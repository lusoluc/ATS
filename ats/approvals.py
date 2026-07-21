"""Freigabe-Gate für zustimmungspflichtige Ausschreibungen (UC-JF-01).

Prinzip:
- Einrichtungen mit `Facility.requiresApproval` schicken jede neue/erneut
  eingereichte Anzeige automatisch durchs Gate: Status `draft`, ApprovalTicket
  mit Schrittkette aus dem SystemSetting `APPROVAL_CHAIN`
  (kommagetrennte Django-Gruppennamen, Default: "HR-Admin").
- Veröffentlicht wird NICHT manuell, sondern automatisch mit der letzten
  Freigabe (siehe views.approvals_inbox). Rückfrage (RETURNED) öffnet den
  Nachbesserungs-Loop: erneutes Speichern reicht das Ticket neu ein (UC-JF-07).
- Der Schnell-Toggle darf das Gate nicht umgehen (views.toggle_job_active).
"""
from typing import TYPE_CHECKING

from .models import ApprovalStep, ApprovalTicket, SystemSetting, WorkflowState

if TYPE_CHECKING:
    from django.contrib.auth.models import User

    from .models import (
        Department,
        Facility,
        JobFamily,
        JobPosting,
        RequisitionRule,
        RequisitionStep,
        StaffingRequest,
    )


def approval_chain(facility: "Facility | None" = None) -> list[str]:
    """Freigabekette: Einrichtungs-eigene Kette > globale APPROVAL_CHAIN > "HR-Admin".

    Individuell je Einrichtung einstellbar (Facility.approvalChain), ohne dass
    Governance umgehbar wird: eine leere/fehlende Kette fällt auf die globale
    bzw. die HR-Admin-Kette zurück – das Gate selbst (requiresApproval) bleibt
    davon unberührt.
    """
    raw = ""
    if facility is not None:
        raw = (facility.approvalChain or "").strip()
    if not raw:
        setting = SystemSetting.objects.filter(key="APPROVAL_CHAIN").first()
        raw = (setting.value if setting and setting.value else "")
    chain = [part.strip() for part in raw.split(",") if part.strip()]
    return chain or ["HR-Admin"]


def draft_state() -> WorkflowState:
    state, _ = WorkflowState.objects.get_or_create(
        name="draft", defaults={"description": "Deaktiviert / Entwurf"})
    return state


def has_open_gate(job: "JobPosting") -> bool:
    """True, wenn eine Freigabe aussteht oder verweigert wurde (Gate geschlossen)."""
    ticket = getattr(job, "approvalTicket", None)
    return ticket is not None and ticket.status in ("PENDING", "RETURNED", "REJECTED")


def ensure_approval_gate(job: "JobPosting") -> "ApprovalTicket | None":
    """Stellt sicher, dass eine zustimmungspflichtige Anzeige durchs Gate läuft.

    - Neue Anzeige: Ticket + Kette anlegen, Anzeige auf `draft` zwingen.
    - Nach Rückfrage/Ablehnung erneut gespeichert: Ticket + Schritte auf PENDING
      zurücksetzen (Wiedervorlage) und Anzeige `draft` halten.
    Rückgabe: das Ticket oder None (kein Gate nötig).
    """
    if not (job.facility_id and job.facility.requiresApproval):
        return None

    ticket = getattr(job, "approvalTicket", None)
    if ticket is None:
        ticket = ApprovalTicket.objects.create(jobPosting=job, status="PENDING")
        for order, role in enumerate(approval_chain(job.facility), start=1):
            ApprovalStep.objects.create(approvalTicket=ticket, stepOrder=order,
                                        assignedRoleId=role)
    elif ticket.status in ("RETURNED", "REJECTED"):
        # Wiedervorlage nach Nachbesserung (UC-JF-07)
        ticket.status = "PENDING"
        ticket.save(update_fields=["status", "updatedAt"])
        ticket.steps.update(status="PENDING", actionTakenAt=None)
    elif ticket.status == "APPROVED":
        return ticket  # bereits freigegeben – keine erneute Pflicht bei Edit

    if job.workflowState.name != "draft":
        job.workflowState = draft_state()
        job.save(update_fields=["workflowState", "updatedAt"])
    return ticket

def requisition_required() -> bool:
    """Stellenfreigabe aktiv? Optional je Installation – wenn an, dann Pflicht."""
    s = SystemSetting.objects.filter(key="REQUISITION_REQUIRED").first()
    return bool(s and s.value == "1")


def requisition_chain(facility: "Facility | None" = None,
                      department: "Department | None" = None,
                      job_family: "JobFamily | None" = None) -> list[str]:
    """Genehmigungskette fuer Personalbedarf:
    Einrichtungs-Kette > globale REQUISITION_CHAIN > Freigabekette der
    Einrichtung (eine Governance-Wahrheit statt zwei Pflegeorte)."""
    rule = resolve_requisition_rule(facility, department, job_family)
    if rule and rule.chain.strip():
        return [p.strip() for p in rule.chain.split(",") if p.strip()]
    raw = ""
    if facility is not None:
        raw = (facility.requisitionChain or "").strip()
    if not raw:
        setting = SystemSetting.objects.filter(key="REQUISITION_CHAIN").first()
        raw = (setting.value if setting and setting.value else "")
    chain = [part.strip() for part in raw.split(",") if part.strip()]
    return chain or approval_chain(facility)


def open_requisition_steps(req: "StaffingRequest") -> None:
    """Erzeugt die Stufen fuer einen Antrag (idempotent). Mehrere Rollen
    mit gleicher order = PARALLELE Stufe: alle muessen genehmigen, bevor
    die naechste order faellig wird."""
    from .models import RequisitionStep
    if req.steps.exists():
        return
    groups = requisition_chain_groups_with_quorum(
        req.facility, req.department, req.jobFamily)
    for order, (roles, quorum) in enumerate(groups, start=1):
        for role in roles:
            RequisitionStep.objects.create(request=req, role=role,
                                           order=order, groupQuorum=quorum)


def requisition_required_for(facility: "Facility | None" = None,
                             department: "Department | None" = None,
                             job_family: "JobFamily | None" = None) -> bool:
    """Pflicht global ODER ueber eine mandatory-Regel im Geltungsbereich."""
    if requisition_required():
        return True
    rule = resolve_requisition_rule(facility, department, job_family)
    return bool(rule and rule.mandatory)


def requisition_blocked_reason(job: "JobPosting") -> str | None:
    """None = Veroeffentlichung frei. Prueft nur, wenn der Prozess fuer den
    Geltungsbereich der Stelle Pflicht ist (global oder per Matrix-Regel).
    Nachweis = ein angenommener/konvertierter Bedarf, der auf diese Stelle
    zeigt. Bestandsschutz: greift nur an den Veroeffentlichungs-Schaltpunkten."""
    if not requisition_required_for(job.facility, job.department,
                                    job.jobFamily):
        return None
    from .models import StaffingRequest
    ok = StaffingRequest.objects.filter(
        convertedJob=job, status__in=["ACCEPTED", "CONVERTED"]).exists()
    if ok:
        return None
    return ("Stellenfreigabe aktiv: Veröffentlichen ist nur mit genehmigtem "
            "Personalbedarf möglich. Bitte zuerst unter „Bedarf“ beantragen "
            "und genehmigen lassen, dann daraus die Ausschreibung erstellen.")

def resolve_requisition_rule(facility: "Facility | None" = None,
                             department: "Department | None" = None,
                             job_family: "JobFamily | None" = None,
                             ) -> "RequisitionRule | None":
    """Spezifischste aktive Regel fuer den Geltungsbereich (None = keine).
    Wildcards: eine nicht gesetzte Dimension der Regel passt auf alles;
    eine GESETZTE Dimension muss exakt passen."""
    from .models import RequisitionRule
    best: RequisitionRule | None = None
    for rule in RequisitionRule.objects.filter(active=True):
        if rule.facility_id and rule.facility_id != getattr(facility, 'id', facility):
            continue
        if rule.department_id and rule.department_id != getattr(department, 'id', department):
            continue
        if rule.jobFamily_id and rule.jobFamily_id != getattr(job_family, 'id', job_family):
            continue
        if (best is None or rule.specificity > best.specificity
                or (rule.specificity == best.specificity
                    and rule.createdAt > best.createdAt)):
            best = rule
    return best

def may_decide_requisition_step(user: "User", step: "RequisitionStep",
                                ) -> "tuple[bool, User | None]":
    """Darf diese Person die Stufe entscheiden? -> (erlaubt, vertritt_wen).

    Erlaubt bei direkter Rollen-Zugehoerigkeit (Gruppe = step.role) oder
    aktiver Vertretung durch ein Mitglied dieser Rolle. Scope: ALL immer,
    FACILITY ueber die Einrichtung des Antrags; stellenscharfe (JOB-)
    Vertretungen decken Personalbedarf bewusst NICHT – ein Bedarf hat noch
    keine Stelle. Zeitfenster prueft active_delegations_to serverseitig."""
    if user.is_superuser or user.groups.filter(name=step.role).exists():
        return True, None
    from .permissions import active_delegations_to
    for d in active_delegations_to(user):
        if not d.delegator.groups.filter(name=step.role).exists():
            continue
        if d.scopeType == 'ALL':
            return True, d.delegator
        if (d.scopeType == 'FACILITY' and step.request.facility_id
                and str(step.request.facility_id) == (d.scopeId or '')):
            return True, d.delegator
    return False, None

def _parse_group_quorum(segment: str) -> tuple[list[str], int]:
    """Zieht ein optionales Quorum-Suffix "(N)" aus einem Ketten-Segment.
    Liefert (roles, quorum). Quorum ohne Suffix oder unsinnig = len(roles)
    (alle noetig). Beispiel: "A + B + C (2)" -> (["A","B","C"], 2)."""
    import re
    quorum: int | None = None
    m = re.search(r"\((\d+)\)\s*$", segment)
    if m:
        quorum = int(m.group(1))
        segment = segment[:m.start()]
    roles = [r.strip() for r in segment.split('+') if r.strip()]
    if not quorum or quorum < 1 or quorum > len(roles):
        quorum = len(roles)
    return roles, quorum


def requisition_chain_groups(facility: "Facility | None" = None,
                             department: "Department | None" = None,
                             job_family: "JobFamily | None" = None,
                             ) -> list[list[str]]:
    """Kette als Stufen-GRUPPEN (nur Rollen, Quorum-Suffix entfernt).
    Syntax: Komma trennt sequenzielle Stufen, '+' verbindet parallele
    Rollen, optionales "(N)" am Ende einer Gruppe = Quorum."""
    return [roles for roles, _ in
            requisition_chain_groups_with_quorum(facility, department,
                                                 job_family)]


def requisition_chain_groups_with_quorum(
        facility: "Facility | None" = None,
        department: "Department | None" = None,
        job_family: "JobFamily | None" = None) -> list[tuple[list[str], int]]:
    """Wie requisition_chain_groups, aber list[(roles, quorum)]."""
    out: list[tuple[list[str], int]] = []
    for segment in requisition_chain(facility, department, job_family):
        roles, quorum = _parse_group_quorum(segment)
        if roles:
            out.append((roles, quorum))
    return out

def due_requisition_steps(req: "StaffingRequest") -> "list[RequisitionStep]":
    """Die aktuell FAELLIGEN Stufen (alle PENDING mit der niedrigsten
    offenen order) – bei parallelen Gruppen mehr als eine."""
    pending = req.steps.filter(status='PENDING').order_by('order')
    first = pending.first()
    if not first:
        return []
    return list(pending.filter(order=first.order))

def notify_due_requisition_steps(req: "StaffingRequest") -> int:
    """Benachrichtigt alle Personen, die JETZT entscheiden koennen: die
    Mitglieder der faelligen Rollen-Gruppen plus deren aktive Vertretungen
    (Scope ALL oder passende Einrichtung; stellenscharfe Vertretungen
    decken Bedarf nicht). Ereignisgetrieben beim Faelligwerden einer
    Stufe – kein Cron, kein Doppellauf. Liefert die Empfaengerzahl."""
    from django.contrib.auth.models import Group
    from django.core.mail import send_mail
    from django.utils import timezone as _tz

    from .audit import write_audit
    from .models import RoleDelegation

    due = due_requisition_steps(req)
    if not due:
        return 0
    roles = [st.role for st in due]
    now = _tz.now()
    recipients: dict[str, str | None] = {}  # email -> Vertretungs-Hinweis (oder None)
    for role in roles:
        grp = Group.objects.filter(name=role).first()
        if not grp:
            continue
        for member in grp.user_set.filter(is_active=True):
            if member.email:
                recipients.setdefault(member.email, None)
        deleg = (RoleDelegation.objects
                 .filter(delegator__groups__name=role,
                         validFrom__lte=now, validUntil__gt=now)
                 .select_related('delegator', 'delegatee'))
        for d in deleg:
            covers = (d.scopeType == 'ALL'
                      or (d.scopeType == 'FACILITY' and req.facility_id
                          and str(req.facility_id) == (d.scopeId or '')))
            if covers and d.delegatee.email:
                recipients.setdefault(
                    d.delegatee.email,
                    d.delegator.get_username())
    for email, deputy_for in recipients.items():
        extra = (f"\nSie erhalten diese Nachricht als Vertretung von "
                 f"{deputy_for}." if deputy_for else "")
        send_mail(
            f"Stellenfreigabe wartet auf Ihre Entscheidung: {req.title}",
            (f"Der Personalbedarf \u201e{req.title}\u201c "
             f"({req.facility.name if req.facility else '-'}) wartet auf "
             f"die Stufe {' / '.join(roles)}.\n"
             f"Beantragt von: "
             f"{req.requestedBy.get_username() if req.requestedBy else '-'}\n"
             f"Entscheiden: /recruiter/bedarf/" + extra),
            None, [email], fail_silently=True)
    if recipients:
        write_audit('REQUISITION_DUE_NOTIFIED', request_id=str(req.id),
                    roles=roles, recipients=len(recipients))
    return len(recipients)

