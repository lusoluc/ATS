"""Board-Erkenntnisse aus vorhandenen Daten (C1 Wiederbewerber, C2 Liegenbleiber).

Beide Signale kosten je EINE zusaetzliche Abfrage fuers ganze Board (kein
N+1). Sie erfinden nichts, sondern machen sichtbar, was schon in den Daten
steht: dass jemand sich erneut bewirbt (ueber den E-Mail-Blind-Index als
Personen-Identitaet) und dass eine Karte zu lange unbewegt liegt.
"""
from datetime import datetime
from typing import Any

from django.db.models import Max
from django.utils import timezone

from .models import Application, AuditLog

STATUS_LABELS = {
    "NEW": "Neu", "IN_REVIEW": "In Prüfung", "INVITED": "Eingeladen",
    "HIRED": "Eingestellt", "REJECTED": "Abgelehnt", "WITHDRAWN": "Zurückgezogen",
}

# Ab hier gilt eine Karte als liegengeblieben (Tage ohne Statuswechsel).
STALE_WARN_DAYS = 7
STALE_ALERT_DAYS = 14


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def repeat_applicant_map(applications: list[Application]) -> dict[Any, dict]:
    """Je Karte: hat sich diese Person schon frueher beworben?

    Rueckgabe {app_id: {"count", "prev_status", "prev_date"}} NUR fuer
    Bewerbungen von Personen mit mehr als einer Bewerbung. Die Person wird
    ueber applicant_id gefuehrt (ein Applicant je E-Mail-Blind-Index)."""
    applicant_ids = {a.applicant_id for a in applications}
    if not applicant_ids:
        return {}
    # Alle Bewerbungen dieser Personen (auch ausserhalb des aktuellen Boards,
    # z. B. aeltere abgelehnte), knapp gehalten auf die noetigen Felder.
    qs = (Application.objects
          .filter(applicant_id__in=applicant_ids)
          .values_list("id", "applicant_id", "status", "createdAt")
          .order_by("createdAt"))
    by_applicant: dict[Any, list[dict]] = {}
    for app_id, applicant_id, status, created in qs:
        by_applicant.setdefault(applicant_id, []).append(
            {"id": app_id, "status": status, "createdAt": created})

    out: dict[Any, dict] = {}
    for app in applications:
        history = by_applicant.get(app.applicant_id, [])
        if len(history) < 2:
            continue
        # juengste ANDERE Bewerbung als Kontext ("zuletzt … am …")
        others = [h for h in history if h["id"] != app.id]
        prev = others[-1] if others else None
        out[app.id] = {
            "count": len(history),
            "prev_status": status_label(prev["status"]) if prev else "",
            "prev_date": prev["createdAt"] if prev else None,
        }
    return out


def stale_days_map(applications: list[Application],
                   now: datetime | None = None) -> dict[Any, dict]:
    """Je Karte: Tage seit dem Eintritt in den aktuellen Status.

    Quelle ist der letzte STATUS_CHANGE-Audit der Bewerbung; fehlt einer
    (Karte nie bewegt), zaehlt createdAt. Erledigte Endzustaende (eingestellt/
    abgelehnt/zurueckgezogen) liefern KEIN Signal - dort ist Liegenbleiben
    kein Problem."""
    now = now or timezone.now()
    active = [a for a in applications
              if a.status not in ("HIRED", "REJECTED", "WITHDRAWN")]
    if not active:
        return {}
    ids = [str(a.id) for a in active]
    last_change: dict[str, datetime] = {}
    for row in (AuditLog.objects
                .filter(action="STATUS_CHANGE", applicationId__in=ids)
                .values("applicationId")
                .annotate(latest=Max("createdAt"))):
        app_id = row["applicationId"]
        if app_id:
            last_change[app_id] = row["latest"]

    out: dict[Any, dict] = {}
    for app in active:
        since = last_change.get(str(app.id)) or app.createdAt
        days = (now - since).days
        if days >= STALE_ALERT_DAYS:
            out[app.id] = {"days": days, "level": "alert"}
        elif days >= STALE_WARN_DAYS:
            out[app.id] = {"days": days, "level": "warn"}
    return out
