"""Entscheidungs-Erinnerungen: offene Freigaben und Gremien-Stimmen anmahnen.

Betrieb (Cron, siehe OPERATIONS.md):
    0 8 * * *  python manage.py send_decision_reminders

Philosophie (konsistent zur Termin-Erinnerung): genau EINE Erinnerung je
Person und Vorgang (Audit-Marker DECISION_REMINDER_SENT) – wer danach nicht
reagiert, wird ueber Urlaubsvertretung oder dokumentiertes Uebersteuern
geloest, nicht ueber Mail-Bombardement. Erinnert wird ab --days (Default 3)
Tagen Wartezeit. Vertretungen werden mit erinnert: die Mail geht auch an
aktive Vertreter:innen der saeumigen Person. Deckt drei Vorgangsarten ab:
Freigabe-Schritte, Gremien-Stimmen und Stellenfreigabe-Ketten (jeweils
eigener Marker, damit keine Vermischung).
"""
import datetime
import json

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from ats.audit import write_audit
from ats.models import (Application, ApplicationVote, ApprovalStep, AuditLog,
                        RoleDelegation)
from ats.panel import panel_member_ids


class Command(BaseCommand):
    help = "Erinnert einmalig an offene Freigabe-Schritte und Gremien-Stimmen."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=3,
                            help="Erinnern ab N Tagen Wartezeit (Default 3).")

    def _already(self, kind, ref, user_id):
        marker = f'"marker": "{kind}:{ref}:{user_id}"'
        return AuditLog.objects.filter(action="DECISION_REMINDER_SENT",
                                       metadataJson__contains=marker).exists()

    def _mark(self, kind, ref, user_id):
        # Achtung: KEIN user=-Kwarg (kollidiert mit write_audit-Signatur) –
        # ein einzelner marker-Schluessel macht die Einmaligkeit robust pruefbar.
        write_audit("DECISION_REMINDER_SENT", marker=f"{kind}:{ref}:{user_id}")

    def _delegates_of(self, user_ids):
        now = timezone.now()
        out = {}
        for d in (RoleDelegation.objects
                  .filter(delegator_id__in=user_ids,
                          validFrom__lte=now, validUntil__gte=now)
                  .select_related("delegatee")):
            out.setdefault(d.delegator_id, []).append(d.delegatee)
        return out

    def handle(self, *args, **options):
        cutoff = timezone.now() - datetime.timedelta(days=max(1, options["days"]))
        sent = 0

        # 1) Freigabe-Schritte: PENDING, an der Reihe, Ticket aelter als cutoff
        steps = (ApprovalStep.objects
                 .filter(status="PENDING", approvalTicket__status="PENDING",
                         approvalTicket__createdAt__lte=cutoff)
                 .select_related("approvalTicket__jobPosting"))
        for step in steps:
            prior = step.approvalTicket.steps.filter(stepOrder__lt=step.stepOrder)
            if prior.exclude(status="APPROVED").exists():
                continue  # noch nicht an der Reihe -> keine Mahnung
            if step.assignedUserId:
                holders = list(User.objects.filter(username=step.assignedUserId,
                                                   is_active=True))
            else:
                holders = list(User.objects.filter(groups__name=step.assignedRoleId,
                                                   is_active=True))
            delegates = self._delegates_of([h.id for h in holders])
            job = step.approvalTicket.jobPosting
            days = (timezone.now() - step.approvalTicket.createdAt).days
            for holder in holders:
                recipients = [holder] + delegates.get(holder.id, [])
                for person in recipients:
                    if not person.email or self._already("APPROVAL", step.id, person.id):
                        continue
                    prefix = ("" if person == holder
                              else f"(In Vertretung für {holder.get_full_name() or holder.username}) ")
                    send_mail(
                        f"Erinnerung: Freigabe wartet seit {days} Tagen – {job.title}",
                        (f"{prefix}Die Freigabe '{job.title}' wartet seit {days} Tagen "
                         f"auf die Rolle {step.assignedRoleId or step.assignedUserId}.\n"
                         "Entscheiden: /recruiter/approvals/"),
                        None, [person.email], fail_silently=True)
                    self._mark("APPROVAL", step.id, person.id)
                    sent += 1

        # 2) Gremien-Stimmen: Sitz ohne Stimme, Bewerbung aelter als cutoff
        apps = (Application.objects
                .filter(status__in=["NEW", "IN_REVIEW"], createdAt__lte=cutoff)
                .select_related("jobPosting__department", "jobPosting__facility",
                                "jobPosting__location", "jobPosting__jobFamily",
                                "jobPosting__organization", "applicant"))
        for app in apps:
            members = [int(m) for m in panel_member_ids(app.jobPosting) if m.isdigit()]
            voted = set(ApplicationVote.objects.filter(application=app)
                        .values_list("user_id", flat=True))
            missing = [m for m in members if m not in voted]
            delegates = self._delegates_of(missing)
            days = (timezone.now() - app.createdAt).days
            for uid in missing:
                member = User.objects.filter(id=uid, is_active=True).first()
                if member is None:
                    continue
                for person in [member] + delegates.get(uid, []):
                    if not person.email or self._already("PANEL", f"{app.id}:{uid}",
                                                         person.id):
                        continue
                    prefix = ("" if person == member
                              else f"(In Vertretung für {member.get_full_name() or member.username}) ")
                    send_mail(
                        f"Erinnerung: Gremium wartet – {app.jobPosting.title}",
                        (f"{prefix}Ihre Stimme zur Bewerbung auf '{app.jobPosting.title}' "
                         f"steht seit {days} Tagen aus – ohne Mehrheit kann nicht "
                         "eingeladen werden.\nAbstimmen: /recruiter/approvals/"),
                        None, [person.email], fail_silently=True)
                    self._mark("PANEL", f"{app.id}:{uid}", person.id)
                    sent += 1
            # Eskalation bei ueberschrittener Abstimmungs-Frist: einmalig,
            # unabhaengig von der normalen Erinnerung (eigener Marker).
            from ats.panel import panel_state
            state = panel_state(app)
            if state.get("overdue"):
                for uid in missing:
                    member = User.objects.filter(id=uid,
                                                 is_active=True).first()
                    if (member is None or not member.email
                            or self._already("PANEL_OVERDUE",
                                             f"{app.id}:{uid}", member.id)):
                        continue
                    send_mail(
                        f"Frist überschritten: Gremium blockiert – "
                        f"{app.jobPosting.title}",
                        (f"Die vereinbarte Abstimmungs-Frist "
                         f"({state['deadline_days']} Tage) ist überschritten "
                         f"– die Bewerbung ist seit {state['days_open']} "
                         f"Tagen offen und kann ohne Ihre Stimme nicht "
                         "weitergehen.\nJetzt abstimmen: /recruiter/approvals/"),
                        None, [member.email], fail_silently=True)
                    self._mark("PANEL_OVERDUE", f"{app.id}:{uid}", member.id)
                    sent += 1

        # 3) Stellenfreigabe-Ketten: faellige Stufe zu lange offen. Faellig-ab
        #    ist der Abschluss der Vorstufe (nicht Antragseingang), damit die
        #    Wartezeit fair je Stufe zaehlt und nicht die ganze Kette bestraft.
        from ats.models import StaffingRequest
        from ats.approvals import (due_requisition_steps,
                                    may_decide_requisition_step)
        for req in (StaffingRequest.objects.filter(status="IN_APPROVAL")
                    .select_related("facility", "requestedBy")
                    .prefetch_related("steps")):
            due = due_requisition_steps(req)
            if not due:
                continue
            # faellig-ab = spaeteste Entscheidung der direkt vorausgehenden
            # order-Gruppe; fuer die erste Stufe der Antragseingang.
            min_order = due[0].order
            prior_ends = [st.decidedAt for st in req.steps.all()
                          if st.decidedAt and st.order < min_order]
            due_since = max(prior_ends) if prior_ends else req.createdAt
            if due_since > cutoff:
                continue  # noch nicht lange genug faellig
            days = (timezone.now() - due_since).days
            roles = " / ".join(sorted({st.role for st in due}))
            # Empfaenger: Gruppenmitglieder der faelligen Rollen + aktive
            # Vertretungen, die den Antrag entscheiden duerfen.
            role_names = {st.role for st in due}
            holders = list(User.objects.filter(
                groups__name__in=role_names, is_active=True).distinct())
            delegates = self._delegates_of([h.id for h in holders])
            # Nur Vertretungen behalten, die diesen Antrag wirklich decken
            covering = {}
            for st in due:
                for holder in holders:
                    if not holder.groups.filter(name=st.role).exists():
                        continue
                    for dep in delegates.get(holder.id, []):
                        # may_decide prueft Scope/Zeitfenster fuer die Stufe
                        if may_decide_requisition_step(dep, st)[0]:
                            covering.setdefault(holder.id, {})[dep.id] = dep
            for holder in holders:
                recipients = [holder] + list(
                    covering.get(holder.id, {}).values())
                for person in recipients:
                    ref = f"{req.id}:{holder.id}"
                    if not person.email or self._already("REQUISITION", ref,
                                                         person.id):
                        continue
                    prefix = ("" if person == holder
                              else f"(In Vertretung für "
                                   f"{holder.get_full_name() or holder.username}) ")
                    fac = req.facility.name if req.facility else "-"
                    send_mail(
                        f"Erinnerung: Stellenfreigabe wartet seit {days} "
                        f"Tagen – {req.title}",
                        (f"{prefix}Der Personalbedarf '{req.title}' ({fac}) "
                         f"wartet seit {days} Tagen auf die Stufe {roles}.\n"
                         "Entscheiden: /recruiter/bedarf/"),
                        None, [person.email], fail_silently=True)
                    self._mark("REQUISITION", ref, person.id)
                    sent += 1

        self.stdout.write(self.style.SUCCESS(
            f"{sent} Entscheidungs-Erinnerung(en) verschickt (ab {options['days']} Tagen)."))
