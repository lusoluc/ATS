"""WP7/L6: Minimale, abhängigkeitsfreie Async-Queue für KI-Aufgaben.

Nutzung:
    from ats.queue import enqueue
    enqueue("SCORE_APPLICATION", {"application_id": str(app.id)})

Abarbeitung:
    python manage.py ai_worker --loop     (Betrieb, z.B. Compose-Profil `ki`)
    python manage.py ai_worker --once     (einmalig abarbeiten, z.B. Cron/Tests)

WAS VORHER FEHLTE (dieselbe Frage wie an die Zustell-Jobs — läuft das im
Ausfall wirklich?):

* Ein Fehlschlag setzte den Task sofort wieder auf PENDING — und als ältester
  wurde er sofort wieder geclaimt. Alle Versuche waren in Sekunden verbrannt;
  ein 5-Minuten-KI-Ausfall machte die ganze Queue **endgültig** FAILED.
  Jetzt: Backoff über `nextAttemptAt` — der nächste Versuch wartet, bis die
  Störung realistisch vorbei sein kann.
* Starb der Worker zwischen Claim und Ergebnis (Neustart, Deploy, OOM), blieb
  der Task für immer RUNNING — kein Lauf nahm ihn wieder auf. Jetzt:
  `reclaim_stale()` holt hängige RUNNING-Tasks zurück.
* Der Platzhalter „KI-Analyse läuft im Hintergrund …" blieb bei endgültigem
  Fehlschlag ewig stehen. Jetzt: Bei FAILED bekommt die Bewerbung einen
  ehrlichen Vermerk — sofern niemand den Platzhalter längst ersetzt hat.
"""
from __future__ import annotations

import datetime
import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone

from .models import AiTask

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .models import Application

logger = logging.getLogger(__name__)

#: Wird bei AI_ASYNC als vorläufige Begründung gespeichert (public.py) und
#: hier bei endgültigem Fehlschlag ersetzt. EINE Konstante, damit Schreiber
#: und Ersetzer nie auseinanderlaufen.
PLACEHOLDER_RATIONALE = "KI-Analyse läuft im Hintergrund …"

#: Ehrlicher Vermerk, wenn alle Versuche erschöpft sind. Kein erfundener
#: Score, keine ewige Zusage — die Bewerbung gehört regulär gesichtet.
FAILURE_RATIONALE = ("KI-Analyse nicht möglich (alle Versuche fehlgeschlagen). "
                     "Bitte regulär von Hand sichten.")

#: Wartezeit vor dem naechsten Versuch, je nach Anzahl bisheriger Versuche.
#: Kurz genug, dass ein Neustart der KI die Queue zuegig nachzieht; lang
#: genug, dass ein Ausfall nicht alle Versuche in Sekunden verbrennt.
BACKOFF_MINUTES = (2, 10)

#: Ein RUNNING-Task, der aelter ist, gilt als verwaist (Worker-Abbruch).
#: Grosszuegig bemessen: lokales LLM-Scoring auf CPU darf Minuten dauern.
STALE_MINUTES = 30

#: Aufbewahrung erledigter Tasks. DONE ist reine Historie; FAILED bleibt
#: laenger, damit die Jobs-Seite den Fehler zeigen und ihn jemand erneut
#: einreihen kann, bevor er verschwindet.
DONE_KEEP_DAYS = 30
FAILED_KEEP_DAYS = 90

#: Ab diesem Wartealter des aeltesten PENDING-Tasks meldet die Jobs-Seite
#: ein Problem: Bei laufendem Worker (Poll alle 3 s) ist das unmoeglich —
#: entweder laeuft kein Worker, oder er kommt nicht hinterher.
PENDING_WARN_MINUTES = 30


def enqueue(task_type: str, payload: dict[str, Any]) -> AiTask:
    # Robustheit der frueheren dumps(default=str)-Variante erhalten:
    # nicht-JSON-faehige Werte (UUID, datetime) werden zu Strings.
    return AiTask.objects.create(taskType=task_type,
                                 payloadJson=json.loads(json.dumps(payload, default=str)))


# --- Handler ------------------------------------------------------------------

def _handle_score_application(payload: dict[str, Any]) -> dict[str, Any]:
    """Scort eine Bewerbung asynchron (nutzt die injection-sichere Pipeline)."""
    from .models import Application
    from .views import evaluate_with_local_gemma
    app = Application.objects.get(id=payload["application_id"])
    score, rationale = evaluate_with_local_gemma(
        app.coverLetterTxt or "", app.jobPosting.requirementsJson, application_id=app.id)
    app.aiScore = score
    app.aiRationale = rationale
    app.save(update_fields=["aiScore", "aiRationale", "updatedAt"])
    return {"score": score}


def _score_application_gave_up(payload: dict[str, Any]) -> None:
    """Endgueltiger Fehlschlag: Der Platzhalter darf nicht ewig „läuft" sagen.

    Ueberschrieben wird NUR der Platzhalter (oder Leere) — hat inzwischen
    jemand von Hand eine Begruendung eingetragen, bleibt sie stehen.
    """
    from .models import Application
    app_id = str(payload.get("application_id") or "")
    if not app_id:
        return
    try:
        app = Application.objects.get(id=app_id)
    except Exception:
        return  # Bewerbung geloescht/anonymisiert — nichts zu berichtigen
    if app.aiRationale in (None, "", PLACEHOLDER_RATIONALE):
        app.aiRationale = FAILURE_RATIONALE
        app.save(update_fields=["aiRationale", "updatedAt"])


HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "SCORE_APPLICATION": _handle_score_application,
}

#: Wird gerufen, wenn ein Task ENDGUELTIG scheitert (alle Versuche erschoepft
#: oder verwaist ohne Restversuch) — damit kein Task still eine Zusage
#: hinterlaesst, die nie eingeloest wird.
ON_GAVE_UP: dict[str, Callable[[dict[str, Any]], None]] = {
    "SCORE_APPLICATION": _score_application_gave_up,
}


# --- Worker-Kern ---------------------------------------------------------------

def _gave_up(task: AiTask) -> None:
    hook = ON_GAVE_UP.get(task.taskType)
    if hook is None:
        return
    try:
        hook(task.payloadJson or {})
    except Exception:
        # Der Hook ist Berichtigung, nicht Pflichtprogramm: Sein Fehler darf
        # das Festschreiben des Task-Ergebnisses nicht verhindern.
        logger.exception("Endgueltig-Fehlschlag-Hook fuer %s fehlgeschlagen",
                         task.id)


def reclaim_stale(now: datetime.datetime | None = None) -> int:
    """Holt verwaiste RUNNING-Tasks zurueck (Worker-Abbruch).

    Der Versuch ist beim Claim bereits gezaehlt: Ein Task, der den Worker
    zweimal mit in den Tod reisst, soll nicht ewig wiederkommen. Sind die
    Versuche erschoepft, endet er ehrlich als FAILED.
    """
    now = now or timezone.now()
    grenze = now - datetime.timedelta(minutes=STALE_MINUTES)
    zurueckgeholt = 0
    with transaction.atomic():
        stale = (AiTask.objects.select_for_update(skip_locked=True)
                 .filter(status="RUNNING", startedAt__lt=grenze))
        for task in stale:
            if task.attempts >= task.maxAttempts:
                task.status = "FAILED"
                task.error = (f"Worker-Abbruch: Versuch {task.attempts} wurde "
                              f"nach {STALE_MINUTES} min nicht beendet.")
                task.finishedAt = now
                task.save(update_fields=["status", "error", "finishedAt"])
                _gave_up(task)
            else:
                task.status = "PENDING"
                task.nextAttemptAt = None
                task.save(update_fields=["status", "nextAttemptAt"])
            zurueckgeholt += 1
    if zurueckgeholt:
        logger.warning("%s verwaiste RUNNING-Task(s) zurueckgeholt", zurueckgeholt)
    return zurueckgeholt


def claim_next(now: datetime.datetime | None = None) -> AiTask | None:
    """Nimmt atomar den ältesten fälligen PENDING-Task (kein Doppel-Claim)."""
    from django.db.models import Q
    now = now or timezone.now()
    with transaction.atomic():
        task = (AiTask.objects.select_for_update(skip_locked=True)
                .filter(status="PENDING")
                .filter(Q(nextAttemptAt__isnull=True) | Q(nextAttemptAt__lte=now))
                .order_by("createdAt").first())
        if not task:
            return None
        task.status = "RUNNING"
        task.startedAt = now
        task.attempts += 1
        task.save(update_fields=["status", "startedAt", "attempts"])
        return task


def process(task: AiTask) -> None:
    handler = HANDLERS.get(task.taskType)
    try:
        if handler is None:
            raise ValueError(f"Unbekannter taskType: {task.taskType}")
        result = handler(task.payloadJson or {})
        task.status = "DONE"
        task.resultJson = json.loads(json.dumps(result or {}, default=str))
        task.error = None
        task.nextAttemptAt = None
    except Exception as e:
        logger.exception("AiTask %s fehlgeschlagen (Versuch %s/%s)",
                         task.id, task.attempts, task.maxAttempts)
        task.error = str(e)[:1000]
        if task.attempts >= task.maxAttempts:
            task.status = "FAILED"
        else:
            # Zurueck in die Warteschlange - aber NICHT sofort: Der naechste
            # Versuch wartet, bis die Stoerung (KI-Neustart, Netz) realistisch
            # vorbei sein kann, statt alle Versuche in Sekunden zu verbrennen.
            minuten = BACKOFF_MINUTES[min(task.attempts, len(BACKOFF_MINUTES)) - 1]
            task.status = "PENDING"
            task.nextAttemptAt = timezone.now() + datetime.timedelta(minutes=minuten)
    task.finishedAt = timezone.now()
    task.save(update_fields=["status", "resultJson", "error", "finishedAt",
                             "nextAttemptAt"])
    if task.status == "FAILED":
        _gave_up(task)


def run_pending(limit: int = 50) -> int:
    """Arbeitet bis zu `limit` fällige Tasks ab; Rückgabe: Anzahl verarbeitet."""
    reclaim_stale()
    n = 0
    while n < limit:
        task = claim_next()
        if not task:
            break
        process(task)
        n += 1
    return n


def requeue_failed() -> int:
    """Reiht alle FAILED-Tasks neu ein (Jobs-Seite: „erneut versuchen").

    Mit vollen Versuchen: Wer den Knopf drueckt, hat die Ursache (typisch:
    KI nicht erreichbar) behoben — ein Rest-Versuchskonto von 0 waere ein
    Knopf ohne Wirkung.
    """
    geaendert = 0
    with transaction.atomic():
        for task in (AiTask.objects.select_for_update()
                     .filter(status="FAILED")):
            task.status = "PENDING"
            task.attempts = 0
            task.nextAttemptAt = None
            task.finishedAt = None
            task.save(update_fields=["status", "attempts", "nextAttemptAt",
                                     "finishedAt"])
            geaendert += 1
    return geaendert


def trim_finished(now: datetime.datetime | None = None) -> tuple[int, int]:
    """Loescht alte erledigte Tasks (Datensparsamkeit statt ewiger Tabelle).

    Rueckgabe: (geloeschte DONE, geloeschte FAILED).
    """
    now = now or timezone.now()
    done, _ = (AiTask.objects.filter(
        status="DONE",
        finishedAt__lt=now - datetime.timedelta(days=DONE_KEEP_DAYS)).delete())
    failed, _ = (AiTask.objects.filter(
        status="FAILED",
        finishedAt__lt=now - datetime.timedelta(days=FAILED_KEEP_DAYS)).delete())
    return done, failed


def scoring_aktiv() -> bool:
    """Ist die KI-Vorbewertung eingeschaltet? (EU-AI-Act-Opt-in)"""
    from .models import SystemSetting
    return SystemSetting.objects.filter(
        key="AI_SCORING_ENABLED", value="1").exists()


def unscored_applications() -> QuerySet[Application]:
    """Bewerbungen, die trotz aktivem Scoring keine Einordnung tragen.

    Der Anlass ist der lange KI-Ausfall: Im Sofort-Modus (AI_ASYNC aus)
    entstand frueher gar keine Aufgabe - die Bewerbung kam ohne Score an, und
    es gab **keinen Weg**, sie je nachbewerten zu lassen. Dieselbe Lage
    entsteht, wenn eine gescheiterte Aufgabe nach 90 Tagen weggeraeumt wurde
    oder jemand das Scoring erst spaeter einschaltet.

    Gesucht wird deshalb am ZUSTAND, nicht an der Ursache: kein Score, offener
    Vorgang, keine Aufgabe in Arbeit. Entschiedene Vorgaenge bleiben aussen
    vor - eine Einordnung fuer eine laengst abgelehnte oder eingestellte
    Bewerbung waere Rechnen ohne Zweck.
    """
    from django.db.models import Q

    from .models import Application
    # Aufgaben, die noch laufen oder warten - deren Bewerbungen brauchen
    # keinen zweiten Eintrag.
    laufend = [i for i in (
        AiTask.objects.filter(taskType="SCORE_APPLICATION",
                              status__in=["PENDING", "RUNNING"])
        .values_list("payloadJson__application_id", flat=True)) if i]
    # `aiScore` ist NULL ODER leer - in SQL zwei verschiedene Dinge, hier
    # dieselbe Bedeutung: keine Einordnung.
    return (Application.objects
            .filter(status__in=["NEW", "IN_REVIEW"])
            .filter(Q(aiScore__isnull=True) | Q(aiScore=""))
            .exclude(id__in=laufend))


def enqueue_unscored() -> int:
    """Reiht alle unbewerteten offenen Bewerbungen zur Bewertung ein."""
    anzahl = 0
    for app in unscored_applications().iterator(chunk_size=200):
        enqueue("SCORE_APPLICATION", {"application_id": str(app.id)})
        anzahl += 1
    return anzahl


def queue_depth() -> dict[str, int]:
    from django.db.models import Count
    rows = AiTask.objects.values("status").annotate(c=Count("id"))
    return {str(r["status"]): int(r["c"]) for r in rows}


def queue_overview(now: datetime.datetime | None = None) -> dict[str, Any]:
    """Zustand der Queue fuer die Jobs-Seite — Zahlen plus die eine Frage:
    Wartet hier etwas laenger, als es bei laufendem Worker koennte?"""
    now = now or timezone.now()
    depth = queue_depth()
    aeltester = (AiTask.objects.filter(status="PENDING")
                 .order_by("createdAt").first())
    warte_minuten = None
    if aeltester:
        warte_minuten = int((now - aeltester.createdAt).total_seconds() // 60)
    letzter_fehler = (AiTask.objects.filter(status="FAILED")
                      .order_by("-finishedAt").first())
    return {
        "pending": depth.get("PENDING", 0),
        "running": depth.get("RUNNING", 0),
        "failed": depth.get("FAILED", 0),
        "done": depth.get("DONE", 0),
        "warte_minuten": warte_minuten,
        "haengt": (warte_minuten is not None
                   and warte_minuten >= PENDING_WARN_MINUTES),
        "letzter_fehler": (letzter_fehler.error or "") if letzter_fehler else "",
        # Bewerbungen, die trotz aktivem Scoring keine Einordnung tragen und
        # auf die auch keine Aufgabe wartet - der Rest, den ein Ausfall
        # hinterlaesst. Nur zaehlen, wenn Scoring ueberhaupt an ist: sonst
        # waere JEDE Bewerbung "unbewertet", was schlicht der Normalzustand
        # ohne KI ist.
        "unbewertet": (unscored_applications().count()
                       if scoring_aktiv() else 0),
    }
