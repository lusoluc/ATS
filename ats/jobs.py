"""Wiederkehrende Jobs — und der ehrliche Nachweis, dass sie laufen.

WAS VORHER WAR: Neun Kommandos, die regelmäßig laufen müssen — allen voran
`data_retention` (Anonymisierung nach Fristablauf) und `purge_talent_pool`
(abgelaufene Einwilligungen löschen). `OPERATIONS.md` schlug dafür einen
Cron-Eintrag vor. Der ausgelieferte `docker-compose.yml` enthielt **keinen
Zeitplan**: Wer der Installationsanleitung folgt und `docker compose up -d`
fährt, bekommt `db`, `web`, KI und den KI-Worker — und keinen einzigen dieser
Jobs.

Die Seite „Datenaufbewahrung" sagte derweil zu HR-Admins, Bewerbungen würden
„nach Ablauf der Frist **automatisch** anonymisiert (DSGVO-Datenminimierung)".
Ein Satz, den die Auslieferung nicht einlöste — bei einer Pflicht aus Art. 5
Abs. 1 lit. e DSGVO, für die die Leitung geradesteht.

WIE ES JETZT LÄUFT: Jeder Lauf hinterlässt einen Vermerk. Damit kann die
Oberfläche sagen, wann ein Job zuletzt lief — und schweigen ist keine Option
mehr: Ein Job, der nie lief, steht als solcher da. Dazu bringt der
Compose-Stapel einen `scheduler`-Dienst mit, der die fälligen Jobs ausführt.

Bewusst KEIN Fremdsystem (Celery, Redis-Beat): Der Träger betreibt das Haus
selbst, oft ohne eigenes Betriebsteam. Ein Dienst mehr im selben Image, der
alle paar Minuten nachsieht, ist zu verstehen und zu reparieren; eine
verteilte Warteschlange wäre es für dieses Publikum nicht.
"""
from __future__ import annotations

import datetime
import json
import logging
from dataclasses import dataclass, field

from django.core import management
from django.utils import timezone

logger = logging.getLogger(__name__)

#: Prefix der SystemSetting-Schluessel, unter denen Laeufe vermerkt werden.
RUN_KEY = "JOB_LAST_RUN_"


@dataclass(frozen=True)
class JobSpec:
    """Ein wiederkehrender Job: was er heisst, wann er faellig ist, was er wiegt."""

    name: str                     # Management-Kommando
    label: str                    # Klartext fuer die Oberflaeche
    hour: int                     # Uhrzeit der Faelligkeit (lokale Zeit)
    minute: int = 0
    weekday: int | None = None    # None = taeglich, sonst 0=Montag
    args: list[str] = field(default_factory=list)
    #: Pflicht heisst: Ein Ausbleiben ist ein Rechtsproblem, kein Komfortverlust.
    pflicht: bool = False
    warum: str = ""


#: Der Zeitplan. Die Zeiten sind aus dem Cron-Vorschlag in OPERATIONS.md
#: uebernommen, damit bestehende Installationen dasselbe Verhalten sehen.
JOBS: list[JobSpec] = [
    JobSpec("data_retention", "Aufbewahrungsfristen anwenden", 2, 15,
            pflicht=True,
            warum="Ohne diesen Lauf bleiben abgelehnte Bewerbungen unbegrenzt "
                  "gespeichert – entgegen Art. 5 Abs. 1 lit. e DSGVO und "
                  "entgegen dem, was die Seite Datenaufbewahrung zusagt."),
    JobSpec("purge_talent_pool", "Abgelaufene Talent-Pool-Einwilligungen löschen",
            3, 30, pflicht=True,
            warum="Eine Einwilligung, die abgelaufen ist, trägt die Speicherung "
                  "nicht mehr."),
    JobSpec("verify_audit", "Integrität der Audit-Kette prüfen", 2, 30,
            warum="Eine Manipulation faellt sonst erst auf, wenn jemand den "
                  "Nachweis braucht."),
    JobSpec("send_job_alerts", "Job-Alerts versenden", 8, 0,
            args=["--hours", "24"],
            warum="Abonnentinnen und Abonnenten warten sonst vergeblich."),
    JobSpec("send_interview_reminders", "Termin-Erinnerungen", 7, 0,
            warum="Erinnerungen, die nie rausgehen, kosten Termine."),
    JobSpec("send_feedback_requests", "Feedback-Erinnerungen an Interviewende", 9, 0),
    JobSpec("send_decision_reminders", "Erinnerungen an offene Freigaben", 8, 0),
    JobSpec("weekly_report", "Wochenbericht für die Leitung", 7, 0, weekday=0),
]

# BEWUSST NICHT im Zeitplan (Entscheidung, keine Auslassung):
#
# * `ai_eval` (KI-Golden-Set): braucht eine erreichbare lokale KI. Auf
#   Installationen ohne KI-Profil - dem Normalfall - stuende der Job jede
#   Woche rot, und ein Job, der bei fehlender KI still uebersprungen wuerde,
#   waere wieder ein gruener Nichtstuer. Er gehoert zur KI-Pflege und wird
#   nach Prompt-/Modellaenderungen von Hand gestartet (OPERATIONS.md).
# * `seed_demo --reset` (naechtlicher Demo-Reset): nur fuer Demo-Instanzen
#   (DEMO_MODE=1) und dort als Host-Cron dokumentiert (INSTALL.md). In den
#   Standard-Zeitplan gehoert kein Kommando, das eine Datenbank leert.

JOBS_BY_NAME = {j.name: j for j in JOBS}


def _setting(name: str):
    from .models import SystemSetting
    return SystemSetting.objects.filter(key=f"{RUN_KEY}{name}").first()


def record_job_run(name: str, ok: bool, detail: str = "") -> None:
    """Vermerkt, dass ein Job gelaufen ist — mit Ergebnis."""
    from .models import SystemSetting
    SystemSetting.objects.update_or_create(
        key=f"{RUN_KEY}{name}",
        defaults={"value": json.dumps({
            "when": timezone.now().isoformat(),
            "ok": bool(ok),
            "detail": (detail or "")[:300],
        })},
    )


def last_run(name: str) -> dict | None:
    """Letzter Lauf eines Jobs — oder None, wenn er noch nie lief."""
    setting = _setting(name)
    if not setting or not setting.value:
        return None
    try:
        daten = json.loads(setting.value)
        daten["when_dt"] = datetime.datetime.fromisoformat(daten["when"])
        return daten
    except (ValueError, TypeError, KeyError):
        logger.exception("Job-Vermerk fuer %s ist unlesbar", name)
        return None


def _due_at(spec: JobSpec, now: datetime.datetime) -> datetime.datetime:
    """Der letzte Zeitpunkt, zu dem dieser Job faellig war."""
    lokal = timezone.localtime(now)
    faellig = lokal.replace(hour=spec.hour, minute=spec.minute,
                            second=0, microsecond=0)
    if spec.weekday is None:
        if faellig > lokal:
            faellig -= datetime.timedelta(days=1)
        return faellig
    # Wochenjob: zurueck auf den letzten passenden Wochentag
    versatz = (lokal.weekday() - spec.weekday) % 7
    faellig -= datetime.timedelta(days=versatz)
    if faellig > lokal:
        faellig -= datetime.timedelta(days=7)
    return faellig


def is_due(spec: JobSpec, now: datetime.datetime | None = None) -> bool:
    """Steht dieser Job an? Ein Lauf je Faelligkeit, nicht je Aufruf."""
    now = now or timezone.now()
    faellig = _due_at(spec, now)
    letzter = last_run(spec.name)
    if letzter is None:
        return True
    return letzter["when_dt"] < faellig


def run_job(spec: JobSpec) -> bool:
    """Fuehrt einen Job aus und vermerkt das Ergebnis.

    Ein Fehler bricht den Zeitplan nicht ab: Sonst haette ein kaputter
    Wochenbericht die Aufbewahrungsfristen mit lahmgelegt.
    """
    try:
        management.call_command(spec.name, *spec.args)
    except Exception as exc:            # noqa: BLE001 - Grund gehoert vermerkt
        logger.exception("Job %s fehlgeschlagen", spec.name)
        record_job_run(spec.name, False, f"{type(exc).__name__}: {exc}")
        return False
    record_job_run(spec.name, True)
    return True


def due_jobs(now: datetime.datetime | None = None) -> list[JobSpec]:
    now = now or timezone.now()
    return [j for j in JOBS if is_due(j, now)]


def job_overview(now: datetime.datetime | None = None) -> list[dict]:
    """Je Job: wann zuletzt, wie lange her, und ob das ein Problem ist."""
    now = now or timezone.now()
    zeilen = []
    for spec in JOBS:
        letzter = last_run(spec.name)
        tage = None
        if letzter:
            tage = (now - letzter["when_dt"]).days
        zeilen.append({
            "name": spec.name,
            "label": spec.label,
            "pflicht": spec.pflicht,
            "warum": spec.warum,
            "nie_gelaufen": letzter is None,
            "when": letzter["when_dt"] if letzter else None,
            "ok": letzter["ok"] if letzter else None,
            "detail": letzter.get("detail", "") if letzter else "",
            "tage_her": tage,
            # Ein Tagesjob, der seit mehr als zwei Tagen nicht lief, ist
            # ueberfaellig - ein Tag Toleranz fuer Neustarts und Zeitzonen.
            "ueberfaellig": letzter is None or (tage is not None and tage > (
                8 if spec.weekday is not None else 2)),
        })
    return zeilen


def open_problems(now: datetime.datetime | None = None) -> list[dict]:
    """Nur die Zeilen, die jemand sehen MUSS."""
    return [z for z in job_overview(now) if z["ueberfaellig"]]
