"""Aktionsverlauf je Bewerbung und je Stelle - ein Ort fuer die ganze Geschichte.

Der Verlauf erfindet nichts. Er fuehrt zusammen, was schon in den Daten steht:
die verkettete Audit-Historie (interne Entscheidungen, System-Ereignisse), die
Nachrichten (Kommunikation in beide Richtungen), die geplanten Gespraeche und
das Interview-Feedback. Daraus wird EINE chronologische Liste - damit ein
HR-Mensch (auch eine Urlaubsvertretung) auf einen Blick sieht, wer was wann
getan hat, ohne sich durch fuenf Ansichten zu klicken.

Bewusst quellenscharf, damit nichts doppelt erscheint:
- Nachrichten kommen aus dem Message-Modell (mit Inhalt) - die zugehoerigen
  Audit-Eintraege MESSAGE_SENT/CANDIDATE_MESSAGE_SENT werden uebersprungen.
- Feedback kommt aus InterviewFeedback (mit Empfehlung/Bedenken) - der
  Audit-Eintrag INTERVIEW_FEEDBACK_SAVED wird uebersprungen.
- Alles Uebrige (Statuswechsel, Einladung, Absage, Gremium, Gates ...) kommt
  aus dem Audit-Log, das die kanonische, revisionssichere Quelle ist.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from django.utils import timezone

from .board_insights import status_label
from .models import (
    Application,
    AuditLog,
    InterviewFeedback,
    JobPosting,
)

ActorKind = Literal["intern", "bewerber", "system"]


@dataclass
class TimelineEvent:
    """Ein normalisierter Verlaufseintrag - unabhaengig von der Quelle."""
    when: datetime
    actor: str
    actor_kind: ActorKind
    icon: str
    title: str
    detail: str = ""


# Audit-Aktionen, die im Verlauf NICHT auftauchen: entweder durch ein
# Domaenen-Objekt reicher dargestellt (Nachricht, Feedback) oder reines
# Lese-Rauschen (jeder Modal-Aufruf protokolliert einen CV-Zugriff).
_AUDIT_SKIP = {
    "MESSAGE_SENT", "CANDIDATE_MESSAGE_SENT",   # -> Message
    "INTERVIEW_FEEDBACK_SAVED",                 # -> InterviewFeedback
    "READ_CV", "READ_DOCUMENT",                 # Lese-Rauschen
}

# Aktionen, die eine Bewerber-Handlung sind (auch wenn kein interner Nutzer
# eingetragen ist). Bestimmt Zuordnung und Farbe der Spur.
_CANDIDATE_ACTIONS = {
    "WITHDRAWN_BY_CANDIDATE", "CANDIDATE_SLOT_BOOKED",
    "CANDIDATE_APPOINTMENT_CANCELLED", "CANDIDATE_APPOINTMENT_REBOOKED",
    "CANDIDATE_CHANGE_REQUEST", "CANDIDATE_EMAIL_CHANGE_REQUESTED",
    "CANDIDATE_DATA_UPDATED",
}

# Aktionen, die die Automatik/das System ausloest (keine Person am Klick).
_SYSTEM_ACTIONS = {
    "DECISION_REMINDER_SENT", "FEEDBACK_REMINDER_SENT",
    "INTERVIEW_REMINDER_SENT", "REQUISITION_DUE_NOTIFIED",
    "APPLICATION_CONFIRMATION_SENT", "JOB_ALERT_PURGED",
    "TALENT_POOL_PURGED", "ANONYMIZE_DSGVO",
}

# Icon + Klartext-Titel je Aktion. Fehlt eine Aktion hier, wird der
# Aktionsname humanisiert angezeigt (nichts wird stillschweigend verschluckt).
_AUDIT_LABELS: dict[str, tuple[str, str]] = {
    "STATUS_CHANGE": ("fa-arrows-turn-right", "Status geaendert"),
    "STATUS_CHANGE_BULK": ("fa-arrows-turn-right", "Status geaendert (Sammelaktion)"),
    "INVITE_SENT": ("fa-envelope-open-text", "Zum Gespraech eingeladen"),
    "REJECTION_NOTICE_SENT": ("fa-circle-xmark", "Absage versendet"),
    "APPLICATION_CONFIRMATION_SENT": ("fa-circle-check", "Eingangsbestaetigung versendet"),
    "APPLICATION_HIRED": ("fa-user-check", "Eingestellt"),
    "JOB_FILLED": ("fa-flag-checkered", "Stelle besetzt"),
    "HIRED_DATE_CORRECTED": ("fa-calendar-day", "Einstellungsdatum korrigiert"),
    "HIRE_CONCERNS_ACKNOWLEDGED": ("fa-triangle-exclamation", "Bedenken vor Einstellung bestaetigt"),
    "ADD_NOTE": ("fa-comment-medical", "Interne Notiz"),
    "PANEL_VOTE_CAST": ("fa-scale-balanced", "Gremiums-Stimme"),
    "PANEL_COMMENT_ADDED": ("fa-comments", "Gremiums-Kommentar"),
    "PANEL_OVERRIDDEN": ("fa-gavel", "Gremiums-Votum uebersteuert"),
    "FEEDBACK_REQUESTED": ("fa-paper-plane", "Feedback angefragt"),
    "APPROVAL_GATE_OPENED": ("fa-door-open", "Freigabe angestossen"),
    "INTERVIEW_OUTCOME_SET": ("fa-clipboard-check", "Gespraechsergebnis erfasst"),
    "INTERVIEW_ROUND_CHANGED": ("fa-forward-step", "Gespraechsrunde weitergezaehlt"),
    "WITHDRAWN_BY_CANDIDATE": ("fa-person-walking-arrow-right", "Bewerbung zurueckgezogen"),
    "CANDIDATE_SLOT_BOOKED": ("fa-calendar-check", "Termin selbst gebucht"),
    "CANDIDATE_APPOINTMENT_CANCELLED": ("fa-calendar-xmark", "Termin abgesagt"),
    "CANDIDATE_APPOINTMENT_REBOOKED": ("fa-calendar-day", "Termin umgebucht"),
    "CANDIDATE_CHANGE_REQUEST": ("fa-pen", "Aenderung angefragt"),
    "CANDIDATE_EMAIL_CHANGE_REQUESTED": ("fa-at", "E-Mail-Aenderung angefragt"),
    "CANDIDATE_DATA_UPDATED": ("fa-user-pen", "Daten aktualisiert"),
    "DECISION_REMINDER_SENT": ("fa-bell", "Erinnerung: Entscheidung offen"),
    "FEEDBACK_REMINDER_SENT": ("fa-bell", "Erinnerung: Feedback offen"),
    "INTERVIEW_REMINDER_SENT": ("fa-bell", "Termin-Erinnerung versendet"),
    "PAY_HISTORY_QUESTION_BLOCKED": ("fa-ban", "Frage nach Gehaltshistorie geblockt"),
    "ANONYMIZE_DSGVO": ("fa-user-slash", "Daten anonymisiert (DSGVO)"),
}


def _actor_for(action: str, user_id: str | None) -> tuple[str, ActorKind]:
    if action in _CANDIDATE_ACTIONS:
        return ("Bewerber:in", "bewerber")
    if action in _SYSTEM_ACTIONS or not user_id:
        return ("System", "system")
    return (user_id, "intern")


def _humanize(action: str) -> str:
    return action.replace("_", " ").capitalize()


def _status_detail(meta: dict) -> str:
    old = meta.get("oldStatus")
    new = meta.get("newStatus")
    if old and new:
        return f"{status_label(old)} → {status_label(new)}"
    if new:
        return status_label(new)
    return ""


def _audit_detail(action: str, meta: dict) -> str:
    """Ein knapper, menschlicher Zusatztext je Aktion (aus den Metadaten)."""
    if action in ("STATUS_CHANGE", "STATUS_CHANGE_BULK"):
        return _status_detail(meta)
    if action == "APPLICATION_HIRED":
        return str(meta.get("hired_at") or "")
    if action == "INTERVIEW_OUTCOME_SET":
        outcome = meta.get("outcome")
        try:
            from .models.applications import interview_outcome_label
            return interview_outcome_label(outcome) if outcome else ""
        except Exception:
            return str(outcome or "")
    if action == "PANEL_VOTE_CAST":
        vote = {"FOR": "Dafür", "AGAINST": "Dagegen"}.get(
            str(meta.get("vote") or ""), "")
        return (vote + (" (geändert)" if meta.get("changed") else "")).strip()
    if action == "ADD_NOTE":
        note = str(meta.get("note_added") or "")
        return note[:200] + ("…" if len(note) > 200 else "")
    return ""


def _parse_meta(raw: str | None) -> dict:
    import json
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


def _audit_events(application_ids: list[str],
                  with_name: dict[str, str] | None = None) -> list[TimelineEvent]:
    """Verlaufseintraege aus dem Audit-Log fuer die gegebenen Bewerbungen.

    `with_name` (app_id -> Bewerbername) haengt bei mehreren Bewerbungen den
    Namen an den Titel an - noetig fuer den Stellen-Verlauf, wo mehrere
    Personen gemischt erscheinen.
    """
    if not application_ids:
        return []
    events: list[TimelineEvent] = []
    rows = (AuditLog.objects
            .filter(applicationId__in=application_ids)
            .order_by("createdAt"))
    for row in rows:
        if row.action in _AUDIT_SKIP:
            continue
        icon, title = _AUDIT_LABELS.get(
            row.action, ("fa-circle-info", _humanize(row.action)))
        actor, kind = _actor_for(row.action, row.userId)
        meta = _parse_meta(row.metadataJson)
        detail = _audit_detail(row.action, meta)
        if with_name and row.applicationId in with_name:
            title = f"{title} · {with_name[row.applicationId]}"
        events.append(TimelineEvent(
            when=row.createdAt, actor=actor, actor_kind=kind,
            icon=icon, title=title, detail=detail))
    return events


def application_events(app: Application) -> list[TimelineEvent]:
    """Chronologischer Verlauf EINER Bewerbung (aeltestes zuerst).

    Fuehrt Audit, Nachrichten, Gespraeche und Feedback zusammen.
    """
    events: list[TimelineEvent] = []

    # 1. Der Anfang: die Bewerbung selbst (Bewerber-Handlung).
    events.append(TimelineEvent(
        when=app.createdAt, actor="Bewerber:in", actor_kind="bewerber",
        icon="fa-file-arrow-up", title="Bewerbung eingegangen",
        detail=app.jobPosting.title))

    # 2. Kommunikation (mit Inhalt, in beide Richtungen).
    for msg in app.messages.order_by("createdAt"):
        inbound = msg.direction == "INBOUND"
        events.append(TimelineEvent(
            when=msg.createdAt,
            actor="Bewerber:in" if inbound else "Team",
            actor_kind="bewerber" if inbound else "intern",
            icon="fa-comment" if inbound else "fa-comment-dots",
            title="Nachricht erhalten" if inbound else "Nachricht gesendet",
            detail=(msg.content or "")[:200]
            + ("…" if len(msg.content or "") > 200 else "")))

    # 3. Geplante Gespraeche (das Ergebnis liefert separat der Audit-Eintrag).
    for iv in app.interviews.order_by("createdAt"):
        when = iv.scheduledAt.strftime("%d.%m.%Y %H:%M")
        events.append(TimelineEvent(
            when=iv.createdAt, actor="Team", actor_kind="intern",
            icon="fa-calendar-plus", title="Gespraech geplant",
            detail=f"{iv.kind_label} am {when}"))

    # 4. Interview-Feedback (mit Empfehlung und Bedenken).
    for fb in (InterviewFeedback.objects.filter(application=app)
               .select_related("author").order_by("createdAt")):
        who = fb.author.get_full_name() or fb.author.get_username()
        detail = fb.recommendation_label
        if fb.concerns.strip():
            detail += f" · Bedenken: {fb.concerns.strip()[:120]}"
        events.append(TimelineEvent(
            when=fb.createdAt, actor=who, actor_kind="intern",
            icon="fa-comment-dots",
            title=f"Feedback (Runde {fb.round})" if fb.round else "Feedback",
            detail=detail))

    # 5. Alles Uebrige aus dem Audit-Log.
    events.extend(_audit_events([str(app.id)]))

    events.sort(key=lambda e: e.when)
    return events


def job_events(job: JobPosting) -> list[TimelineEvent]:
    """Chronologischer Verlauf EINER Stelle (aeltestes zuerst).

    Hoehere Flughoehe als der Bewerber-Verlauf: Anlage der Stelle, jede
    eingehende Bewerbung und die Meilensteine ueber alle Bewerbungen hinweg
    (Einladung, Absage, Einstellung, Rueckzug ...), jeweils mit Namen.

    Bewusste Grenze: Job-Lebenszyklus-Audits (aktiviert/deaktiviert) tragen
    keine Job-ID im Log und sind daher hier nicht abbildbar - der Verlauf
    zeigt, was den Bewerbungen widerfahren ist, nicht die Schalter an der
    Anzeige. (Siehe LEARNING/AUDIT-Notiz: JOB_ACTIVATED speichert nur den Titel.)
    """
    events: list[TimelineEvent] = []

    events.append(TimelineEvent(
        when=job.createdAt, actor="System", actor_kind="system",
        icon="fa-briefcase", title="Stelle angelegt", detail=job.title))

    apps = list(Application.objects.filter(jobPosting=job)
                .select_related("applicant").order_by("createdAt"))
    names: dict[str, str] = {}
    for a in apps:
        name = f"{a.applicant.firstName} {a.applicant.lastName}".strip() \
            or "Bewerber:in"
        names[str(a.id)] = name
        events.append(TimelineEvent(
            when=a.createdAt, actor="Bewerber:in", actor_kind="bewerber",
            icon="fa-file-arrow-up", title="Neue Bewerbung",
            detail=name))

    events.extend(_audit_events(list(names.keys()), with_name=names))
    events.extend(_approval_events(job))

    events.sort(key=lambda e: e.when)
    return events


#: Entscheidung -> (Symbol, Klartext). Die Rohwerte stehen so in der Datenbank.
_APPROVAL_LABELS = {
    "APPROVED": ("fa-circle-check", "Freigabe erteilt"),
    "REJECTED": ("fa-circle-xmark", "Zustimmung verweigert"),
    "RETURNED": ("fa-rotate-left", "Rückfrage gestellt"),
}


def _approval_events(job: JobPosting) -> list[TimelineEvent]:
    """Entschiedene Freigabe-Stufen dieser Stelle.

    Die Entscheidungen lagen vollstaendig in der Datenbank - Stufe, Zeitpunkt,
    Begruendung, bei § 99 auch die Gruende - aber keine Ansicht zeigte sie.
    Wer wissen wollte, warum eine Stelle online ist, musste das rohe Audit-Log
    durchsuchen. Der Urheber fehlte sogar in den Daten (das Feld zeigte auf ein
    totes Alt-Modell); seit U6 steht er dort und damit auch hier.
    """
    from .models import ApprovalStep
    steps = (ApprovalStep.objects
             .filter(approvalTicket__jobPosting=job)
             .exclude(status="PENDING")
             .exclude(actionTakenAt__isnull=True)
             .select_related("actionTakenBy")
             .order_by("actionTakenAt"))
    out: list[TimelineEvent] = []
    for step in steps:
        when = step.actionTakenAt
        if when is None:                       # vom Filter ausgeschlossen
            continue
        icon, title = _APPROVAL_LABELS.get(
            step.status, ("fa-clipboard-check", f"Freigabe: {step.status}"))
        who = step.actionTakenBy
        # Altbestand aus der Zeit vor U6 hat keinen Urheber - das wird gesagt,
        # nicht mit einem Platzhalternamen ueberdeckt.
        actor = who.get_username() if who is not None else "nicht dokumentiert"
        detail = f"Stufe {step.stepOrder}"
        comment = (step.comments or "").strip()
        if comment:
            detail += f" – {comment}"
        out.append(TimelineEvent(
            when=when, actor=actor, actor_kind="intern",
            icon=icon, title=title, detail=detail))
    return out


def relative_age(when: datetime, now: datetime | None = None) -> str:
    """Kurze, menschliche Altersangabe ("vor 3 Tagen") fuer die Anzeige."""
    now = now or timezone.now()
    secs = max(0, int((now - when).total_seconds()))
    if secs < 90:
        return "gerade eben"
    mins = secs // 60
    if mins < 60:
        return f"vor {mins} Min."
    hours = mins // 60
    if hours < 24:
        return f"vor {hours} Std."
    days = hours // 24
    if days < 31:
        return f"vor {days} Tag{'en' if days != 1 else ''}"
    months = days // 30
    if months < 12:
        return f"vor {months} Monat{'en' if months != 1 else ''}"
    return f"vor {days // 365} Jahr{'en' if days // 365 != 1 else ''}"
