"""L1-Rechenkern: Einblicke aus vorhandenen Daten (keine UI, keine Formulierung).

Reine Zahlen aus dem, was das Team ohnehin erzeugt: Statusverlauf (Audit-Kette),
Herkunftskanal, Screening-Antworten, Zeitstempel. Jede Funktion macht wenige
Abfragen (kein N+1) und liefert neben dem Ergebnis IMMER die Kontext-Ebene und
die Stichprobengroesse - denn Rauschen als Erkenntnis zu verkaufen waere der
Fehler der alten RAG-Buttons.

Kontext zaehlt: "gut zur Stelle" heisst bei der Nachtpflege in Hamburg etwas
anderes als in der Geriatrie in Lueneburg. Deshalb loest resolve_learning_scope
die spezifischste Ebene auf, die genug Entscheidungen hat, und faellt sonst die
Leiter hinauf - dasselbe Muster wie bei Gremien und Freigabe-Regeln.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime

from django.db.models import QuerySet

from .board_insights import status_label
from .models import Application, AuditLog, JobPosting

# Status-Welt
NEW, IN_REVIEW, INVITED, HIRED, REJECTED, WITHDRAWN = (
    "NEW", "IN_REVIEW", "INVITED", "HIRED", "REJECTED", "WITHDRAWN")

# Positiver Trichter (Reihenfolge der Stufen, die eine Bewerbung durchlaeuft).
STAGE_ORDER = [NEW, IN_REVIEW, INVITED, HIRED]
# Ein Vorgang gilt als abgeschlossen, sobald eine Entscheidung fiel.
DECIDED_STATUSES = {INVITED, HIRED, REJECTED, WITHDRAWN}
POSITIVE_STATUSES = {INVITED, HIRED}

# Unter so vielen abgeschlossenen Vorgaengen auf einer Ebene gibt es KEINE
# Aussage - lieber ehrlich "zu wenig Daten" als Zufall als Muster.
MIN_SAMPLE = 20


@dataclass
class LearningScope:
    """Die Ebene, auf der gerechnet wurde, samt Belastbarkeit."""
    level: str                     # Schluessel der Ebene
    label: str                     # menschlich, z. B. "Abteilung Station 3 · Pflege"
    applications: "QuerySet[Application]"
    sample_size: int               # abgeschlossene Vorgaenge auf dieser Ebene
    sufficient: bool               # >= MIN_SAMPLE erreicht?


def _decided_count(qs: "QuerySet[Application]") -> int:
    return qs.filter(status__in=DECIDED_STATUSES).count()


def resolve_learning_scope(
        job: JobPosting,
        base: "QuerySet[Application] | None" = None) -> LearningScope:
    """Spezifischste Kontext-Ebene mit genug Entscheidungen (sonst hoch fallen).

    Leiter: Abteilung+Jobfamilie → Einrichtung+Jobfamilie → Standort+Jobfamilie
    → Jobfamilie → Organisation. `base` erlaubt eine Vorfilterung (z. B. BOLA).
    """
    apps = Application.objects.all() if base is None else base
    jf = job.jobFamily_id
    ladder: list[tuple[str, str, dict]] = []
    if job.department_id:
        ladder.append((
            "dept_family",
            f"Abteilung {getattr(job.department, 'name', '')} · "
            f"{getattr(job.jobFamily, 'name', '')}",
            {"jobPosting__department_id": job.department_id,
             "jobPosting__jobFamily_id": jf}))
    if job.facility_id:
        ladder.append((
            "facility_family",
            f"Einrichtung {getattr(job.facility, 'name', '')} · "
            f"{getattr(job.jobFamily, 'name', '')}",
            {"jobPosting__facility_id": job.facility_id,
             "jobPosting__jobFamily_id": jf}))
    if job.location_id:
        ladder.append((
            "location_family",
            f"Standort {getattr(job.location, 'name', '')} · "
            f"{getattr(job.jobFamily, 'name', '')}",
            {"jobPosting__location_id": job.location_id,
             "jobPosting__jobFamily_id": jf}))
    ladder.append((
        "family", f"Jobfamilie {getattr(job.jobFamily, 'name', '')}",
        {"jobPosting__jobFamily_id": jf}))
    ladder.append((
        "organization", "Gesamte Organisation",
        {"jobPosting__organization_id": job.organization_id}
        if job.organization_id else {}))

    broadest: LearningScope | None = None
    for level, label, flt in ladder:
        scoped = apps.filter(**flt)
        n = _decided_count(scoped)
        scope = LearningScope(level=level, label=label, applications=scoped,
                              sample_size=n, sufficient=n >= MIN_SAMPLE)
        if scope.sufficient:
            return scope
        broadest = scope        # merke die breiteste (letzte) Ebene
    assert broadest is not None
    return broadest


# --- Statusverlauf (eine Abfrage, wiederverwendet) --------------------------
def _status_events(app_ids: list[str]) -> dict[str, list[tuple[str, datetime]]]:
    """Je Bewerbung die Statuswechsel (newStatus, Zeitpunkt) in Reihenfolge.

    Aus STATUS_CHANGE(_BULK)-Audits, geordnet nach der Kettensequenz. EINE
    Abfrage fuer alle Bewerbungen.
    """
    import json
    out: dict[str, list[tuple[str, datetime]]] = {}
    if not app_ids:
        return out
    rows = (AuditLog.objects
            .filter(action__in=("STATUS_CHANGE", "STATUS_CHANGE_BULK"),
                    applicationId__in=[str(i) for i in app_ids])
            .order_by("seq", "createdAt")
            .values_list("applicationId", "metadataJson", "createdAt"))
    for app_id, meta_json, created in rows:
        try:
            meta = json.loads(meta_json or "{}")
        except (ValueError, TypeError):
            meta = {}
        new_status = meta.get("newStatus")
        if app_id and new_status:
            out.setdefault(app_id, []).append((str(new_status), created))
    return out


def _reached(app_id: str, current: str,
             events: dict[str, list[tuple[str, datetime]]]) -> set[str]:
    reached = {NEW, current}
    for status, _ in events.get(app_id, []):
        reached.add(status)
    return reached


@dataclass
class FunnelResult:
    scope: LearningScope
    stages: list[dict] = field(default_factory=list)        # {status,label,count}
    transitions: list[dict] = field(default_factory=list)   # {from,to,drop_rate}


def funnel_by_context(scope: LearningScope) -> FunnelResult:
    """Trichter je Kontext: wie viele Bewerbungen erreichten jede Stufe, und
    wie hoch ist die Abbruchquote je Uebergang. „Erreicht" aus dem echten
    Statusverlauf (nicht nur dem aktuellen Stand)."""
    rows = list(scope.applications.values_list("id", "status"))
    events = _status_events([str(r[0]) for r in rows])
    reached_all = [_reached(str(aid), st, events) for aid, st in rows]

    stages: list[dict] = []
    for stage in STAGE_ORDER:
        count = sum(1 for r in reached_all if stage in r)
        stages.append({"status": stage, "label": status_label(stage),
                       "count": count})
    transitions: list[dict] = []
    for i in range(len(stages) - 1):
        prev, nxt = stages[i], stages[i + 1]
        drop = (1 - nxt["count"] / prev["count"]) if prev["count"] else 0.0
        transitions.append({
            "from": prev["label"], "to": nxt["label"],
            "drop_rate": round(drop, 3)})
    return FunnelResult(scope=scope, stages=stages, transitions=transitions)


@dataclass
class ChannelStat:
    source: str
    applications: int
    invited: int
    hired: int
    invite_rate: float


def channel_effectiveness(
        applications: "QuerySet[Application] | None" = None) -> list[ChannelStat]:
    """Je Herkunftskanal: Bewerbungen, Einladungen, Einstellungen, Quote.
    Einladung/Einstellung aus dem echten Verlauf (invited-dann-abgelehnt zaehlt
    trotzdem als Einladung)."""
    qs = Application.objects.all() if applications is None else applications
    rows = list(qs.values_list("id", "status", "source"))
    events = _status_events([str(r[0]) for r in rows])
    acc: dict[str, dict[str, int]] = {}
    for aid, status, source in rows:
        src = source or "DIRECT"
        a = acc.setdefault(src, {"apps": 0, "invited": 0, "hired": 0})
        a["apps"] += 1
        reached = _reached(str(aid), status, events)
        if reached & POSITIVE_STATUSES:
            a["invited"] += 1
        if HIRED in reached:
            a["hired"] += 1
    out = []
    for src, a in acc.items():
        rate = a["invited"] / a["apps"] if a["apps"] else 0.0
        out.append(ChannelStat(source=src, applications=a["apps"],
                               invited=a["invited"], hired=a["hired"],
                               invite_rate=round(rate, 3)))
    out.sort(key=lambda c: c.applications, reverse=True)
    return out


@dataclass
class QuestionImpact:
    question: str
    answered: int              # abgeschlossene Vorgaenge mit Antwort
    fail_rate: float           # Anteil, der die erwartete Antwort NICHT traf
    invite_rate_pass: float    # Einladungsquote bei erfuellt
    invite_rate_fail: float    # Einladungsquote bei nicht erfuellt


def screening_question_impact(job: JobPosting,
                              scope: LearningScope) -> list[QuestionImpact]:
    """Je K.O.-Frage der Stelle: Durchfallquote und Einladungsquote bei
    erfuellt vs. nicht erfuellt. Nur Fragen mit erwarteter Antwort (K.O.);
    nur abgeschlossene Vorgaenge (eine Entscheidung liegt vor)."""
    questions = [q for q in (job.screeningQuestionsJson or [])
                 if q.get("expectedAnswer")]
    if not questions:
        return []
    decided = scope.applications.filter(status__in=DECIDED_STATUSES)
    rows = list(decided.values_list("id", "status", "screeningAnswersJson"))
    events = _status_events([str(r[0]) for r in rows])

    out: list[QuestionImpact] = []
    for q in questions:
        text = q.get("question", "")
        expected = q.get("expectedAnswer")
        answered = pass_n = pass_inv = fail_n = fail_inv = 0
        for aid, status, answers in rows:
            ans_map: dict[str, str] = answers if isinstance(answers, dict) else {}
            if text not in ans_map:
                continue
            answered += 1
            invited = bool(_reached(str(aid), status, events)
                           & POSITIVE_STATUSES)
            if ans_map.get(text) == expected:
                pass_n += 1
                pass_inv += 1 if invited else 0
            else:
                fail_n += 1
                fail_inv += 1 if invited else 0
        if answered == 0:
            continue
        out.append(QuestionImpact(
            question=text, answered=answered,
            fail_rate=round(fail_n / answered, 3),
            invite_rate_pass=round(pass_inv / pass_n, 3) if pass_n else 0.0,
            invite_rate_fail=round(fail_inv / fail_n, 3) if fail_n else 0.0))
    return out


# Fuellwoerter fuers Anforderungs-Matching (Wort steckt in mehreren Anforderungen).
_REQ_STOP = {
    "und", "oder", "mit", "von", "der", "die", "das", "den", "dem", "ein",
    "eine", "fuer", "sowie", "sehr", "gute", "guter", "jahre", "jahren",
    "mind", "mindestens", "idealerweise", "kenntnisse", "erfahrung",
    "erfahrungen", "abgeschlossene", "abgeschlossenes",
}

# Schwellen fuer die Anforderungs-Wirkung (konservativ).
REQ_MIN_GROUP = 3      # je Gruppe (mit/ohne) mind. so viele besetzte Stellen
REQ_MIN_DAYS = 5       # ... und mind. so viel schneller ohne die Anforderung


def _req_tokens(text: str) -> set[str]:
    t = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return {w for w in re.split(r"[^a-z0-9]+", t)
            if len(w) >= 4 and w not in _REQ_STOP}


def _job_has_requirement(req_lines: list[str], needle_tokens: set[str]) -> bool:
    if not needle_tokens:
        return False
    hay = _req_tokens(" ".join(str(r) for r in (req_lines or [])))
    return bool(needle_tokens & hay)


@dataclass
class RequirementImpact:
    requirement: str
    jobs_with: int
    jobs_without: int
    avg_ttf_with: float
    avg_ttf_without: float
    days_faster_without: float


def requirement_impact(job: JobPosting) -> list[RequirementImpact]:
    """Je Anforderung der Stelle: hatten vergleichbare Stellen (gleiche
    Jobfamilie) sie, und wurden die OHNE sie schneller besetzt?

    Vergleicht die Zeit bis zur Besetzung (erster Einstellungs-Zeitpunkt minus
    Stellen-Anlage) besetzter vergleichbarer Stellen mit vs. ohne die
    Anforderung. Nur bei genug Datenlage je Gruppe und spuerbarem Unterschied.
    """
    from django.db.models import Min

    reqs = [str(r).strip() for r in (job.requirementsJson or [])
            if str(r).strip()]
    if not reqs or not job.jobFamily_id:
        return []

    comparable = list(JobPosting.objects
                      .filter(jobFamily_id=job.jobFamily_id)
                      .exclude(id=job.id)
                      .values_list("id", "createdAt", "requirementsJson"))
    if not comparable:
        return []

    # Erst-Einstellung je vergleichbarer Stelle in EINER Abfrage.
    job_ids = [c[0] for c in comparable]
    first_hire: dict = {}
    for row in (Application.objects
                .filter(jobPosting_id__in=job_ids, status="HIRED",
                        hiredAt__isnull=False)
                .values("jobPosting_id").annotate(fh=Min("hiredAt"))):
        first_hire[row["jobPosting_id"]] = row["fh"]

    # Zeit bis Besetzung je besetzter Stelle (Tage) + deren Anforderungen.
    filled: list[tuple[float, list]] = []
    for jid, created, req_json in comparable:
        fh = first_hire.get(jid)
        if fh is None:
            continue
        ttf = max(0.0, (fh - created).total_seconds() / 86400.0)
        filled.append((ttf, req_json or []))

    out: list[RequirementImpact] = []
    for req in reqs:
        toks = _req_tokens(req)
        with_ttf = [ttf for ttf, rj in filled
                    if _job_has_requirement(rj, toks)]
        without_ttf = [ttf for ttf, rj in filled
                       if not _job_has_requirement(rj, toks)]
        if len(with_ttf) < REQ_MIN_GROUP or len(without_ttf) < REQ_MIN_GROUP:
            continue
        avg_with = sum(with_ttf) / len(with_ttf)
        avg_without = sum(without_ttf) / len(without_ttf)
        faster = avg_with - avg_without
        if faster >= REQ_MIN_DAYS:
            out.append(RequirementImpact(
                requirement=req, jobs_with=len(with_ttf),
                jobs_without=len(without_ttf),
                avg_ttf_with=round(avg_with, 1),
                avg_ttf_without=round(avg_without, 1),
                days_faster_without=round(faster, 1)))
    out.sort(key=lambda i: i.days_faster_without, reverse=True)
    return out


@dataclass
class StageDwell:
    status: str
    label: str
    avg_days: float
    samples: int


@dataclass
class BottleneckResult:
    stages: list[StageDwell] = field(default_factory=list)
    slowest: "StageDwell | None" = None


def stage_bottlenecks(
        applications: "QuerySet[Application] | None" = None) -> BottleneckResult:
    """Durchschnittliche Liegezeit je Stufe (Tage) und die langsamste Stufe.
    Aus den Zeitstempeln der Statuswechsel; die Startstufe zaehlt ab
    Bewerbungseingang."""
    qs = Application.objects.all() if applications is None else applications
    rows = list(qs.values_list("id", "status", "createdAt"))
    events = _status_events([str(r[0]) for r in rows])

    # je Stufe: Summe Tage + Zahl der Beobachtungen
    acc: dict[str, list[float]] = {}
    for aid, _status, created in rows:
        timeline = [(NEW, created)] + events.get(str(aid), [])
        for i in range(len(timeline) - 1):
            status, when = timeline[i]
            _, nxt_when = timeline[i + 1]
            days = max(0.0, (nxt_when - when).total_seconds() / 86400.0)
            acc.setdefault(status, []).append(days)

    stages: list[StageDwell] = []
    for status, vals in acc.items():
        avg = sum(vals) / len(vals) if vals else 0.0
        stages.append(StageDwell(status=status, label=status_label(status),
                                 avg_days=round(avg, 1), samples=len(vals)))
    stages.sort(key=lambda s: s.avg_days, reverse=True)
    return BottleneckResult(stages=stages, slowest=stages[0] if stages else None)
