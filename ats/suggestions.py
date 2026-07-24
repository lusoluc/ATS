"""L1-Vorschlags-Schicht: aus Zahlen wird Vorschlag + Aktion + Link.

Grundsatz aus der Abstimmung: keine Kennzahl ohne Handlungsempfehlung. Der
Rechenkern (insights) liefert die Zahlen, hier werden sie - nur wenn die
Datenlage traegt - in einen konkreten naechsten Schritt mit Button uebersetzt.
Nichts wird automatisch geaendert; der Vorschlag fuellt spaeter nur vor.

Die Schwellen sind bewusst konservativ und hier dokumentiert, damit ein
Vorschlag Gewicht hat, wenn er erscheint.
"""
from dataclasses import dataclass

from django.db.models import QuerySet
from django.urls import reverse

from .insights import (
    channel_effectiveness,
    funnel_by_context,
    resolve_learning_scope,
    screening_question_impact,
    stage_bottlenecks,
)
from .models import Application, JobPosting

# Schwellen (konservativ; Aenderung heisst: bewusst hier anfassen).
FAIL_THRESHOLD = 0.5          # Pflichtfrage laesst > 50 % durchfallen
MIN_ANSWERED = 10            # ... auf mind. so vielen beantworteten Vorgaengen
CHANNEL_MIN_APPS = 20        # Kanal mit >= 20 Bewerbungen ...
FUNNEL_DROP = 0.7           # Abbruch > 70 % zwischen zwei Stufen
BOTTLENECK_FACTOR = 2.0      # Stufe > 2x Median-Liegezeit
BOTTLENECK_MIN_SAMPLES = 5   # ... auf mind. so vielen Beobachtungen

_SEVERITY_RANK = {"alert": 0, "warn": 1, "info": 2}


@dataclass
class Suggestion:
    text: str            # was auffiel (die Zahl in Worten)
    reason: str          # warum das eine Handlung nahelegt
    action_label: str    # Button-Text
    action_url: str      # wohin der Button fuehrt
    severity: str        # "alert" | "warn" | "info"
    sample_size: int     # worauf die Aussage beruht


def _pct(x: float) -> int:
    return round(x * 100)


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    mid = len(s) // 2
    if len(s) % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def build_suggestions(job: JobPosting,
                      base: "QuerySet[Application] | None" = None) -> list[Suggestion]:
    """Erkenntnisse mit Handlung fuer eine Stelle (Kontext ueber die Leiter).

    `base` erlaubt eine BOLA-Vorfilterung der Bewerbungen. Ergebnis nach
    Wirkung sortiert; die Anzeige kappt auf die wichtigsten.
    """
    out = job_suggestions(job, base) + global_suggestions(base)
    out.sort(key=lambda s: (_SEVERITY_RANK.get(s.severity, 3),
                            -s.sample_size))
    return out


def job_suggestions(job: JobPosting,
                    base: "QuerySet[Application] | None" = None) -> list[Suggestion]:
    """Kontextbezogene Vorschlaege (Frage-Durchfall, Prozess-Abbruch) - NUR bei
    belastbarer Datenlage (Leiter + Mindestmenge)."""
    out: list[Suggestion] = []
    scope = resolve_learning_scope(job, base)
    if not scope.sufficient:
        return out

    for imp in screening_question_impact(job, scope):
        if imp.fail_rate > FAIL_THRESHOLD and imp.answered >= MIN_ANSWERED:
            gap = imp.invite_rate_pass - imp.invite_rate_fail
            reason = ("Eine Pflichtfrage, die mehr als die Hälfte "
                      "ausschließt, ist oft zu streng.")
            if gap > 0.2:
                reason += (" Wer sie erfüllte, wurde deutlich häufiger "
                           "eingeladen – das Kriterium trennt, aber es "
                           "engt den Zulauf stark ein.")
            out.append(Suggestion(
                text=(f"Screening-Frage „{imp.question}“ lässt "
                      f"{_pct(imp.fail_rate)} % durchfallen."),
                reason=reason, action_label="Frage prüfen",
                action_url=reverse('ats:screening_questions'),
                severity="warn", sample_size=imp.answered))

    funnel = funnel_by_context(scope)
    for i, t in enumerate(funnel.transitions):
        prev_count = funnel.stages[i]["count"]
        if t["drop_rate"] > FUNNEL_DROP and prev_count >= MIN_ANSWERED:
            out.append(Suggestion(
                text=(f"Zwischen „{t['from']}“ und „{t['to']}“ brechen "
                      f"{_pct(t['drop_rate'])} % ab."),
                reason="Ein so hoher Abbruch an einer Stufe deutet auf "
                       "einen Prozess- oder Anforderungs-Engpass.",
                action_label="Prozess ansehen",
                action_url=reverse('ats:analytics'),
                severity="warn", sample_size=prev_count))
    return out


def global_suggestions(
        base: "QuerySet[Application] | None" = None) -> list[Suggestion]:
    """Kontext-unabhaengige Vorschlaege (Kanal-Budget, Prozess-Engpass) im
    gegebenen (BOLA-)Rahmen."""
    out: list[Suggestion] = []
    for ch in channel_effectiveness(base):
        if ch.applications >= CHANNEL_MIN_APPS and ch.hired == 0:
            out.append(Suggestion(
                text=f"Kanal {ch.source}: {ch.applications} Bewerbungen, "
                     f"0 Einstellungen.",
                reason="Viel Zulauf ohne Ergebnis – das Budget bringt hier "
                       "keine Besetzung.",
                action_label="Kanäle prüfen",
                action_url=reverse('ats:source_channels'),
                severity="warn", sample_size=ch.applications))

    bott = stage_bottlenecks(base)
    if bott.slowest and bott.slowest.samples >= BOTTLENECK_MIN_SAMPLES:
        # Median der UEBRIGEN Stufen (ohne die langsamste) als Vergleich -
        # sonst zieht der Engpass seinen eigenen Vergleichswert hoch.
        med = _median([s.avg_days for s in bott.stages[1:]])
        if med > 0 and bott.slowest.avg_days > BOTTLENECK_FACTOR * med:
            out.append(Suggestion(
                text=(f"Stufe „{bott.slowest.label}“ dauert im Schnitt "
                      f"{bott.slowest.avg_days:.0f} Tage."),
                reason="Diese Stufe ist der Engpass – deutlich langsamer als "
                       "der Rest des Prozesses.",
                action_label="Fristen ansehen",
                action_url=reverse('ats:governance'),
                severity="info", sample_size=bott.slowest.samples))
    return out


def aggregate_suggestions(
        jobs: "list[JobPosting]",
        base: "QuerySet[Application] | None" = None,
        limit: int = 5, max_jobs: int = 40) -> "tuple[list[Suggestion], bool]":
    """Vorschlaege fuers Dashboard: globale einmal + kontextbezogene je Stelle,
    dedupliziert und nach Wirkung gekappt.

    `max_jobs` deckelt die Rechenlast; ist die Stellenzahl groesser, sagt das
    zweite Rueckgabe-Flag ehrlich, dass nicht alle geprueft wurden (kein
    stilles Abschneiden).
    """
    import re
    truncated = len(jobs) > max_jobs
    collected = list(global_suggestions(base))
    for job in jobs[:max_jobs]:
        collected.extend(job_suggestions(job, base))
    collected.sort(key=lambda s: (_SEVERITY_RANK.get(s.severity, 3),
                                  -s.sample_size))
    # Gleichartige Erkenntnisse (gleiche Aktion, gleicher Satz bis auf die
    # Zahl) zu EINER zusammenfassen - die wirksamste (zuerst sortierte) bleibt.
    out: list[Suggestion] = []
    seen: set[tuple[str, str]] = set()
    for s in collected:
        key = (s.action_label, re.sub(r"\d+", "#", s.text))
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out[:limit], truncated
