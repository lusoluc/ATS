"""Sichtungs-Gremium: Team-Entscheidung VOR der Einladung (hoehere Positionen).

Konfiguration je Stelle (JobPosting.panelUserIdsJson). Regel bewusst einfach
und erklaerbar: absolute Mehrheit des Gremiums DAFUER gibt die Einladung
frei. HR-Admin kann mit dokumentierter Verantwortung uebersteuern (Audit).
Kommentare und Fragen des Gremiums landen in den internen Notizen – ein Ort,
alle Beteiligten sehen dasselbe (360-Grad-Prinzip).
"""
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.contrib.auth.models import User

    from .models import Application, JobPosting, RoleDelegation


def _parse_ids(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(i) for i in raw if str(i).strip()]


def resolve_panel(job: "JobPosting") -> tuple[list[str], str]:
    """Gremien-Aufloesung mit Spezifitaets-Leiter (konsistent zu Prozess/Workflow):

        Stelle > Abteilung > Einrichtung > Standort > Jobfamilie > Organisation

    Die SPEZIFISCHSTE besetzte Ebene gewinnt komplett (kein Mischen – klar
    erklaerbar und auditierbar). Sentinel ["NONE"] auf einer Ebene heisst
    „hier bewusst KEIN Gremium" und unterbricht die Vererbung.

    Rueckgabe: (member_ids, quelle) – quelle fuer UI/Audit („geerbt von …").
    """
    ladder = [
        (getattr(job, "panelUserIdsJson", []), "Stelle"),
        (getattr(job.department, "panelUserIdsJson", []) if job.department_id else [], "Abteilung"),
        (getattr(job.facility, "panelUserIdsJson", []) if job.facility_id else [], "Einrichtung"),
        (getattr(job.location, "panelUserIdsJson", []) if job.location_id else [], "Standort"),
        (getattr(job.jobFamily, "panelUserIdsJson", []) if job.jobFamily_id else [], "Jobfamilie"),
        (getattr(job.organization, "panelUserIdsJson", []) if job.organization_id else [], "Organisation"),
    ]
    for raw, source in ladder:
        ids = _parse_ids(raw)
        if not ids:
            continue
        if any(str(i).upper() == "NONE" for i in ids):
            return [], f"{source} (bewusst kein Gremium)"
        return ids, source
    return [], ""


def panel_member_ids(job: "JobPosting") -> list[str]:
    return resolve_panel(job)[0]


def panel_state(app: "Application") -> dict[str, Any]:
    """Zustand des Gremiums fuer eine Bewerbung.

    Rueckgabe-Dict: required, members, votes_for, votes_against, missing,
    allowed (absolute Mehrheit dafuer), summary (fuer Fehlermeldungen/UI).
    """
    members = panel_member_ids(app.jobPosting)
    if not members:
        return {"required": False, "allowed": True, "members": 0,
                "votes_for": 0, "votes_against": 0, "missing": 0, "summary": ""}
    # Sitz-Logik mit Urlaubsvertretung: die eigene Stimme des Mitglieds hat
    # Vorrang; fehlt sie, zaehlt die Stimme einer aktiven Vertretung (im
    # passenden Scope) fuer diesen Sitz. So blockiert Abwesenheit nicht.
    from django.utils import timezone as _tz

    from .models import RoleDelegation
    now = _tz.now()
    seat_of_delegate: dict[str, str] = {}
    for d in RoleDelegation.objects.filter(
            delegator_id__in=[int(m) for m in members if m.isdigit()],
            validFrom__lte=now, validUntil__gt=now):
        from .permissions import delegation_covers
        if delegation_covers(d, app.jobPosting):
            seat_of_delegate.setdefault(str(d.delegatee_id), str(d.delegator_id))
    votes: dict[str, str] = {}
    for v in app.votes.all():
        uid = str(v.user_id)
        if uid in members:
            votes[uid] = v.vote                      # eigene Stimme: Vorrang
        elif uid in seat_of_delegate:
            votes.setdefault(seat_of_delegate[uid], v.vote)
    votes_for = sum(1 for v in votes.values() if v == "FOR")
    votes_against = sum(1 for v in votes.values() if v == "AGAINST")
    # Konfigurierbares Quorum je Stelle (null = absolute Mehrheit);
    # ein Quorum groesser als die Sitzzahl wird ehrlich gekappt.
    quorum = getattr(app.jobPosting, "panelQuorum", None)
    if quorum:
        needed = min(int(quorum), len(members))
        needed_text = f"{needed} von {len(members)} (Quorum)"
    else:
        needed = len(members) // 2 + 1
        needed_text = f"Mehrheit von {len(members)}"
    allowed = votes_for >= needed
    # Abstimmungs-Frist: laeuft ab Bewerbungseingang (bewusst der frueheste
    # belastbare Zeitpunkt – ehrlich dokumentiert), nur solange unentschieden.
    from django.utils import timezone as _tz2
    deadline_days = getattr(app.jobPosting, "panelDeadlineDays", None)
    days_open = (_tz2.now() - app.createdAt).days
    overdue = bool(deadline_days and not allowed
                   and len(votes) < len(members)
                   and days_open > deadline_days)
    _, source = resolve_panel(app.jobPosting)
    summary = (f"Gremium ({source}): {votes_for} dafür / {votes_against} dagegen / "
               f"{len(members) - len(votes)} ausstehend "
               f"(nötig: {needed_text})")
    if overdue:
        summary += (f" – Frist überschritten: {days_open} Tage offen, "
                    f"vereinbart {deadline_days}")
    # Sitz-Liste fuer die visuelle Darstellung (P1: Sitz-Punkte) – je Sitz
    # Name, Stimme und ob sie von einer Vertretung stammt.
    from django.contrib.auth.models import User as _User
    names = {str(u.id): (u.get_full_name() or u.username)
             for u in _User.objects.filter(
                 id__in=[int(m) for m in members if m.isdigit()])}
    delegate_names: dict[str, str] = {}
    if seat_of_delegate:
        for du in _User.objects.filter(
                id__in=[int(d) for d in seat_of_delegate if d.isdigit()]):
            delegate_names[str(du.id)] = du.get_full_name() or du.username
    seat_votes_direct = {str(v.user_id): v.vote for v in app.votes.all()
                         if str(v.user_id) in members}
    seats: list[dict[str, Any]] = []
    for m in members:
        vote = votes.get(m)
        via: str | None = None
        if vote and m not in seat_votes_direct:
            for delegate_id, seat in seat_of_delegate.items():
                if seat == m:
                    via = delegate_names.get(delegate_id, "Vertretung")
                    break
        seats.append({"name": names.get(m, "?"), "vote": vote, "via": via})
    return {"required": True, "allowed": allowed, "members": len(members),
            "votes_for": votes_for, "votes_against": votes_against,
            "missing": len(members) - len(votes), "summary": summary,
            "needed": needed, "overdue": overdue, "days_open": days_open,
            "deadline_days": deadline_days, "seats": seats}


def invitation_blocked_reason(app: "Application") -> str | None:
    """None = Einladung frei; sonst die erklaerende Meldung."""
    state = panel_state(app)
    if state["required"] and not state["allowed"]:
        return state["summary"]
    return None


def resolve_panel_preview(job_family_id: str | None = None,
                          facility_id: str | None = None,
                          department_id: str | None = None,
                          location_id: str | None = None) -> tuple[list[str], str]:
    """Vorschau fuer den Stellen-Wizard: welches Gremium WUERDE ohne eigene
    Auswahl wirken? Gleiche Leiter wie resolve_panel, nur ohne Stellen-Ebene
    (die Stelle existiert ja noch nicht). Organisation wird ueber die
    Einrichtung aufgeloest (on-prem typischerweise Ein-Traeger-Installation:
    Fallback erste Organisation)."""
    from .models import Department, Facility, JobFamily, Location, Organization
    facility = Facility.objects.filter(id=facility_id).first() if facility_id else None
    org = facility.organization if facility else Organization.objects.first()
    ladder = [
        (Department.objects.filter(id=department_id).first() if department_id else None, "Abteilung"),
        (facility, "Einrichtung"),
        (Location.objects.filter(id=location_id).first() if location_id else None, "Standort"),
        (JobFamily.objects.filter(id=job_family_id).first() if job_family_id else None, "Jobfamilie"),
        (org, "Organisation"),
    ]
    for obj, source in ladder:
        if obj is None:
            continue
        ids = _parse_ids(getattr(obj, "panelUserIdsJson", []))
        if not ids:
            continue
        if any(str(i).upper() == "NONE" for i in ids):
            return [], f"{source} (bewusst kein Gremium)"
        return ids, source
    return [], ""


def sits_on_panel(user: "User", job: "JobPosting",
                  delegations: "list[RoleDelegation] | None" = None) -> bool:
    """Sitzt diese Person im Gremium dieser Stelle – selbst ODER als aktive
    Vertretung eines Mitglieds (UC-VT-04)? Fuer Listen/Zaehler, damit
    Vertretungen ihre ausstehenden Sitze auch SEHEN, nicht nur stimmen duerfen.
    `delegations` kann fuer Schleifen vorgeladen werden (active_delegations_to).
    """
    from .permissions import active_delegations_to, delegation_covers
    members = panel_member_ids(job)
    if not members:
        return False
    if str(user.id) in members:
        return True
    if delegations is None:
        delegations = active_delegations_to(user)
    return any(str(d.delegator_id) in members and delegation_covers(d, job)
               for d in delegations)
