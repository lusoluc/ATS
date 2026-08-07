"""SecurATS-Tests: governance (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime

from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ..models import SystemSetting
from .utils import make_user


class DelegationsWP3TestCase(TestCase):
    """WP3/UC-PW-01/02: Delegation anlegen und vorzeitig beenden (mit Audit)."""

    def test_create_and_end_delegation(self):
        from django.contrib.auth.models import User as AuthUser

        from ..models import AuditLog, RoleDelegation
        boss = make_user("wp3boss", role="HR-Admin")
        stand_in = AuthUser.objects.create_user("wp3vertretung", "v@x.de", "pw")
        self.client.force_login(boss)
        r = self.client.post(reverse('ats:delegations'), data={
            "delegatee": "wp3vertretung", "scopeType": "ALL",
            "validFrom": "2026-07-01", "validUntil": "2026-07-21"})
        self.assertEqual(r.status_code, 302)
        d = RoleDelegation.objects.get(delegator=boss)
        self.assertEqual(d.delegatee, stand_in)
        self.assertTrue(AuditLog.objects.filter(action="DELEGATION_CREATE").exists())
        # vorzeitig beenden
        r2 = self.client.post(reverse('ats:delegations'), data={"end_id": str(d.id)})
        self.assertEqual(r2.status_code, 302)
        d.refresh_from_db()
        from django.utils import timezone as tz
        self.assertLessEqual(d.validUntil, tz.now())
        self.assertTrue(AuditLog.objects.filter(action="DELEGATION_END").exists())

class GovernanceWP6TestCase(TestCase):
    """WP6: Approval-Inbox (wartet auf mich, Kommentar, Frist), Governance-Sicht,
    Wochenreport."""

    def _job(self):
        import uuid as _u

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="Berlin")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        return JobPosting.objects.create(title="Stationsleitung", organization=org,
                                         facility=fac, location=loc, jobFamily=fam,
                                         workflowState=wf)

    def _ticket(self, job):
        from ..models import ApprovalStep, ApprovalTicket
        t = ApprovalTicket.objects.create(jobPosting=job, status="PENDING")
        s1 = ApprovalStep.objects.create(approvalTicket=t, stepOrder=1,
                                         assignedRoleId="Hiring-Manager")
        s2 = ApprovalStep.objects.create(approvalTicket=t, stepOrder=2,
                                         assignedRoleId="HR-Admin")
        return t, s1, s2

    def test_waiting_list_respects_order_and_role(self):
        job = self._job()
        t, s1, s2 = self._ticket(job)
        hm = make_user("wp6hm", role="Hiring-Manager")
        hr = make_user("wp6hr", role="HR-Admin")
        # HM ist mit Schritt 1 dran; HR mit Schritt 2 noch NICHT (Vorgaenger offen).
        #
        # Geprueft wird die Entscheidungs-Moeglichkeit (das Formular zum
        # Schritt), nicht mehr der blosse Stellentitel irgendwo auf der Seite:
        # Seit Y1 fuehrt dieselbe Seite eine Uebersicht der LAUFENDEN Ketten,
        # in der die Stelle auftaucht, ohne dass man an der Reihe waere. Das
        # ist gewollt - "wartet auf mich" und "was laeuft gerade" sind zwei
        # verschiedene Fragen.
        self.client.force_login(hm)
        self.assertContains(self.client.get(reverse('ats:approvals')), str(s1.id))
        self.client.force_login(hr)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertNotContains(resp, str(s2.id))
        self.assertContains(resp, "Laufende Freigaben")

    def test_approve_advances_and_completes_ticket(self):
        from ..models import AuditLog
        job = self._job()
        t, s1, s2 = self._ticket(job)
        hm = make_user("wp6hm2", role="Hiring-Manager")
        hr = make_user("wp6hr2", role="HR-Admin")
        self.client.force_login(hm)
        self.client.post(reverse('ats:approvals'), data={"step_id": str(s1.id), "action": "approve"})
        # jetzt ist HR an der Reihe
        self.client.force_login(hr)
        self.assertContains(self.client.get(reverse('ats:approvals')), "Stationsleitung")
        self.client.post(reverse('ats:approvals'), data={"step_id": str(s2.id), "action": "approve"})
        t.refresh_from_db()
        self.assertEqual(t.status, "APPROVED")
        self.assertTrue(AuditLog.objects.filter(action="APPROVAL_APPROVED").exists())

    def test_return_requires_comment(self):
        job = self._job()
        t, s1, _ = self._ticket(job)
        hm = make_user("wp6hm3", role="Hiring-Manager")
        self.client.force_login(hm)
        # ohne Kommentar -> bleibt PENDING
        self.client.post(reverse('ats:approvals'), data={"step_id": str(s1.id), "action": "return"})
        s1.refresh_from_db()
        self.assertEqual(s1.status, "PENDING")
        # mit Kommentar -> RETURNED + Ticket RETURNED
        self.client.post(reverse('ats:approvals'), data={"step_id": str(s1.id),
                                                         "action": "return",
                                                         "comment": "Budget unklar?"})
        s1.refresh_from_db()
        t.refresh_from_db()
        self.assertEqual(s1.status, "RETURNED")
        self.assertEqual(t.status, "RETURNED")
        self.assertIn("Budget", s1.comments)

    def test_foreign_user_cannot_action_step(self):
        job = self._job()
        t, s1, _ = self._ticket(job)
        rec = make_user("wp6rec", role="Recruiter")  # nicht zugewiesen
        self.client.force_login(rec)
        r = self.client.post(reverse('ats:approvals'), data={"step_id": str(s1.id), "action": "approve"})
        self.assertEqual(r.status_code, 404)
        s1.refresh_from_db()
        self.assertEqual(s1.status, "PENDING")

    def test_governance_view_is_data_minimized(self):
        from ..models import Applicant, Application
        job = self._job()
        ap = Applicant.objects.create(firstName="Vertraulich", lastName="Nachname",
                                      email="v@x.de")
        Application.objects.create(applicant=ap, jobPosting=job, status="IN_REVIEW")
        viewer = make_user("wp6viewer", role="Viewer")
        self.client.force_login(viewer)
        resp = self.client.get(reverse('ats:governance'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Audit-Hashkette")
        self.assertNotContains(resp, "Vertraulich")   # keine Namen
        self.assertNotContains(resp, "v@x.de")        # keine E-Mails

    def test_weekly_report_runs(self):
        from io import StringIO

        from django.core.management import call_command
        self._job()
        out = StringIO()
        call_command("weekly_report", stdout=out)
        text = out.getvalue()
        self.assertIn("Wochenreport", text)
        self.assertIn("Besetzungs-Prognose", text)

class ApprovalGateTestCase(TestCase):
    """UC-JF-01: automatisches Freigabe-Gate für zustimmungspflichtige Einrichtungen."""

    def _world(self, requires=True):
        import uuid as _u

        from ..models import Facility, JobFamily, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        self.loc = Location.objects.create(name="Berlin")
        self.fac = Facility.objects.create(name="Klinik Mitbestimmt", organization=org,
                                           requiresApproval=requires)
        self.fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        self.published = WorkflowState.objects.create(name="published")
        # Entgelttransparenz-Gate erfuellen — hier geht es um das Freigabe-Gate
        from ..models import PayBand
        self.band = PayBand.objects.create(
            name="Gate-Band", minAmount=3000, maxAmount=3800)

    def _create_job(self, title="Stationsleitung OP"):
        rec = make_user("gate-" + title[:6].lower().replace(" ", ""), role="HR-Admin")
        self.client.force_login(rec)
        return self.client.post(reverse('ats:create_job'), data={
            "title": title, "description": "Text",
            "facility": str(self.fac.id), "location": str(self.loc.id),
            "job_family": str(self.fam.id), "workflow_state": str(self.published.id),
            "pay_band": str(self.band.id),
        })

    def test_job_for_approval_facility_starts_gated(self):
        from ..models import ApprovalTicket, JobPosting
        self._world(requires=True)
        self._create_job()
        job = JobPosting.objects.get(title="Stationsleitung OP")
        self.assertEqual(job.workflowState.name, "draft")          # trotz "published"-Wunsch
        ticket = ApprovalTicket.objects.get(jobPosting=job)
        self.assertEqual(ticket.status, "PENDING")
        self.assertEqual(ticket.steps.count(), 1)                   # Default-Kette: HR-Admin
        # nicht öffentlich sichtbar
        self.assertNotContains(self.client.get(reverse('ats:job_list')), "Stationsleitung OP")

    def test_final_approval_publishes_automatically(self):
        from ..models import AuditLog, JobPosting
        self._world(requires=True)
        SystemSetting.objects.create(key="APPROVAL_CHAIN", value="Hiring-Manager,HR-Admin")
        self._create_job(title="Pflegeleitung")
        job = JobPosting.objects.get(title="Pflegeleitung")
        ticket = job.approvalTicket
        self.assertEqual(ticket.steps.count(), 2)
        hm = make_user("gatehm", role="Hiring-Manager")
        hr = make_user("gatehr", role="HR-Admin")
        s1, s2 = ticket.steps.order_by("stepOrder")
        self.client.force_login(hm)
        self.client.post(reverse('ats:approvals'), data={"step_id": str(s1.id), "action": "approve"})
        job.refresh_from_db()
        self.assertEqual(job.workflowState.name, "draft")           # noch nicht final
        self.client.force_login(hr)
        self.client.post(reverse('ats:approvals'), data={"step_id": str(s2.id), "action": "approve"})
        job.refresh_from_db()
        self.assertEqual(job.workflowState.name, "published")       # automatisch online
        self.assertContains(self.client.get(reverse('ats:job_list')), "Pflegeleitung")
        self.assertTrue(AuditLog.objects.filter(action="APPROVAL_GATE_OPENED").exists())

    def test_toggle_cannot_bypass_open_gate(self):
        from ..models import JobPosting
        self._world(requires=True)
        self._create_job(title="Gate-Test")
        job = JobPosting.objects.get(title="Gate-Test")
        rec = make_user("gaterec", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.post(reverse('ats:toggle_job_active', args=[job.id]))
        self.assertEqual(r.status_code, 409)                         # Gate blockiert Toggle
        job.refresh_from_db()
        self.assertEqual(job.workflowState.name, "draft")

    def test_resubmission_after_return_resets_chain(self):
        from ..models import JobPosting
        self._world(requires=True)
        self._create_job(title="Rueckfrage-Fall")
        job = JobPosting.objects.get(title="Rueckfrage-Fall")
        s1 = job.approvalTicket.steps.get()
        hr = make_user("gatehr2", role="HR-Admin")
        self.client.force_login(hr)
        self.client.post(reverse('ats:approvals'), data={
            "step_id": str(s1.id), "action": "return", "comment": "Budget?"})
        job.approvalTicket.refresh_from_db()
        self.assertEqual(job.approvalTicket.status, "RETURNED")
        # Nachbesserung: erneutes Speichern reicht neu ein
        self.client.post(reverse('ats:create_job'), data={
            "job_id": str(job.id), "title": "Rueckfrage-Fall", "description": "Mit Budget",
            "facility": str(self.fac.id), "location": str(self.loc.id),
            "job_family": str(self.fam.id), "workflow_state": str(self.published.id)})
        job.approvalTicket.refresh_from_db()
        self.assertEqual(job.approvalTicket.status, "PENDING")       # Wiedervorlage
        self.assertEqual(job.approvalTicket.steps.filter(status="PENDING").count(), 1)

    def test_facility_without_flag_publishes_directly(self):
        from ..models import ApprovalTicket, JobPosting
        self._world(requires=False)
        self._create_job(title="Ohne Gate")
        job = JobPosting.objects.get(title="Ohne Gate")
        self.assertEqual(job.workflowState.name, "published")        # keine Regression
        self.assertFalse(ApprovalTicket.objects.filter(jobPosting=job).exists())

class StaffingRequestTestCase(TestCase):
    """UC-MD-01: Personalbedarf melden, entscheiden, Melder informieren."""

    def _world(self):
        import uuid as _u

        from ..models import Facility, JobFamily, Organization
        org = Organization.objects.create(name="O")
        self.fac = Facility.objects.create(name="Klinik A", organization=org)
        self.fam = JobFamily.objects.create(name="Pflege-" + str(_u.uuid4())[:4])

    def test_hiring_manager_reports_need(self):
        from ..models import AuditLog, StaffingRequest
        self._world()
        hm = make_user("hmuser", role="Hiring-Manager")
        self.client.force_login(hm)
        r = self.client.post(reverse('ats:staffing_requests'), data={
            "form": "create", "title": "Pflegefachkraft Nachtdienst",
            "facility": str(self.fac.id), "job_family": str(self.fam.id),
            "headcount": "2", "desired_start": "2026-09-01",
            "justification": "Nachtdienste nur mit Leasing abgedeckt."})
        self.assertEqual(r.status_code, 302)
        req = StaffingRequest.objects.get()
        self.assertEqual(req.headcount, 2)
        self.assertEqual(req.requestedBy, hm)
        self.assertEqual(req.status, "OPEN")
        self.assertTrue(AuditLog.objects.filter(action="STAFFING_REQUEST_CREATED").exists())
        page = self.client.get(reverse('ats:staffing_requests'))
        self.assertContains(page, "Nachtdienst")
        self.assertNotContains(page, "Eingegangene Meldungen")  # HM entscheidet nicht

    def test_recruiter_decides_and_reporter_is_mailed(self):
        from django.core import mail

        from ..models import AuditLog, StaffingRequest
        self._world()
        hm = make_user("hmuser2", role="Hiring-Manager")
        hm.email = "hm@klinik.example"
        hm.save()
        req = StaffingRequest.objects.create(
            title="MFA Empfang", facility=self.fac, headcount=1,
            justification="Empfang unterbesetzt.", requestedBy=hm)
        rec = make_user("bedrec", role="Recruiter")
        self.client.force_login(rec)
        page = self.client.get(reverse('ats:staffing_requests'))
        self.assertContains(page, "Eingegangene Meldungen")
        r = self.client.post(reverse('ats:staffing_requests'), data={
            "form": "decide", "request_id": str(req.id),
            "decision": "ACCEPTED", "note": "Budget da – Ausschreibung folgt."})
        self.assertEqual(r.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")
        self.assertEqual(req.decidedBy, rec)
        self.assertIsNotNone(req.decidedAt)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("hm@klinik.example", mail.outbox[0].to)
        self.assertIn("angenommen", mail.outbox[0].subject)
        self.assertTrue(AuditLog.objects.filter(action="STAFFING_REQUEST_DECIDED").exists())
        # Entschiedene Meldung nicht erneut entscheidbar
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "decide", "request_id": str(req.id), "decision": "DECLINED"})
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")

    def test_hiring_manager_cannot_decide(self):
        from ..models import StaffingRequest
        self._world()
        req = StaffingRequest.objects.create(title="X", facility=self.fac,
                                             justification="y")
        hm = make_user("hmuser3", role="Hiring-Manager")
        self.client.force_login(hm)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "decide", "request_id": str(req.id), "decision": "ACCEPTED"})
        req.refresh_from_db()
        self.assertEqual(req.status, "OPEN")                   # unveraendert

class StaffingConvertTestCase(TestCase):
    """Feinschliff: angenommener Bedarf -> Ausschreibungs-Entwurf in einem Klick."""

    def _world(self, requires_approval=False):
        import uuid as _u

        from ..models import Facility, JobFamily, Location, Organization, StaffingRequest
        org = Organization.objects.create(name="O")
        self.loc = Location.objects.create(name="Hamburg")
        self.fac = Facility.objects.create(name="Klinik A", organization=org,
                                           requiresApproval=requires_approval)
        SystemSetting.objects.create(key="APPROVAL_CHAIN", value="HR-Admin")
        self.fam = JobFamily.objects.create(name="Pflege-" + str(_u.uuid4())[:4])
        self.req = StaffingRequest.objects.create(
            title="Pflegefachkraft Nachtdienst", facility=self.fac,
            jobFamily=self.fam, headcount=2, status="ACCEPTED",
            justification="Leasingkosten 8 T€/Monat – Team am Limit.")
        self.rec = make_user("convrec", role="Recruiter")
        self.client.force_login(self.rec)

    def _convert(self):
        return self.client.post(reverse('ats:staffing_requests'), data={
            "form": "convert", "request_id": str(self.req.id),
            "location": str(self.loc.id)})

    def test_convert_creates_draft_and_keeps_justification_internal(self):
        from ..models import AuditLog, JobPosting
        self._world()
        r = self._convert()
        self.assertEqual(r.status_code, 302)
        job = JobPosting.objects.get(title="Pflegefachkraft Nachtdienst")
        self.assertEqual(job.workflowState.name, "draft")      # unveroeffentlicht
        self.assertEqual(job.facility, self.fac)
        self.assertEqual(job.jobFamily, self.fam)
        self.assertEqual(job.location, self.loc)
        self.assertNotIn("Leasing", job.description)           # intern bleibt intern!
        self.assertIn("vervollständigen", job.description)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, "CONVERTED")
        self.assertEqual(self.req.convertedJob, job)           # Traceability
        self.assertTrue(AuditLog.objects.filter(
            action="STAFFING_REQUEST_CONVERTED").exists())
        # Nicht doppelt konvertierbar
        self._convert()
        self.assertEqual(JobPosting.objects.filter(
            title="Pflegefachkraft Nachtdienst").count(), 1)

    def test_convert_opens_gate_for_approval_facility(self):
        from ..models import ApprovalTicket, JobPosting
        self._world(requires_approval=True)
        self._convert()
        job = JobPosting.objects.get(title="Pflegefachkraft Nachtdienst")
        self.assertTrue(ApprovalTicket.objects.filter(jobPosting=job,
                                                      status="PENDING").exists())

    def test_open_request_and_hiring_manager_cannot_convert(self):
        from ..models import JobPosting, StaffingRequest
        self._world()
        # Offener (nicht angenommener) Bedarf
        open_req = StaffingRequest.objects.create(
            title="MFA Empfang", facility=self.fac, justification="x")
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "convert", "request_id": str(open_req.id),
            "location": str(self.loc.id)})
        self.assertFalse(JobPosting.objects.filter(title="MFA Empfang").exists())
        # Hiring-Manager darf nicht konvertieren
        hm = make_user("convhm", role="Hiring-Manager")
        self.client.force_login(hm)
        self._convert()
        self.assertFalse(JobPosting.objects.filter(
            title="Pflegefachkraft Nachtdienst").exists())

class ReviewPanelTestCase(TestCase):
    """Sichtungs-Gremium: Team stimmt VOR der Einladung (hoehere Positionen)."""

    def _world(self):
        import uuid as _u

        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        self.m1 = make_user("panel1", role="Hiring-Manager")
        self.m2 = make_user("panel2", role="Recruiter")
        self.m3 = make_user("panel3", role="Viewer")
        self.job = JobPosting.objects.create(
            title="Pflegedienstleitung", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=wf,
            panelUserIdsJson=[str(self.m1.id), str(self.m2.id),
                              str(self.m3.id)])
        ap = Applicant.objects.create(firstName="Vera", lastName="M",
                                      email="vera@x.de")
        self.app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                              status="IN_REVIEW")
        self.rec = make_user("panrec", role="Recruiter")

    def _vote(self, user, vote, comment=""):
        self.client.force_login(user)
        return self.client.post(reverse('ats:application_vote', args=[self.app.id]),
                                data={"vote": vote, "comment": comment})

    def test_invite_blocked_until_majority_then_allowed(self):
        self._world()
        self.client.force_login(self.rec)
        r = self.client.post(reverse('ats:update_status', args=[self.app.id]),
                             data={"status": "INVITED"}).json()
        self.assertFalse(r["success"])
        self.assertTrue(r["panel_blocked"])
        self.assertIn("ausstehend", r["error"])
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "IN_REVIEW")         # unveraendert
        # 1 dafuer reicht nicht (1 von 3), 2 dafuer = absolute Mehrheit
        self._vote(self.m1, "FOR")
        self.client.force_login(self.rec)
        r = self.client.post(reverse('ats:update_status', args=[self.app.id]),
                             data={"status": "INVITED"}).json()
        self.assertFalse(r["success"])
        self._vote(self.m2, "FOR", comment="Starke Berufserfahrung, gerne einladen.")
        self.client.force_login(self.rec)
        r = self.client.post(reverse('ats:update_status', args=[self.app.id]),
                             data={"status": "INVITED"}).json()
        self.assertTrue(r["success"])
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "INVITED")
        self.assertIn("Gremium panel2: Starke Berufserfahrung",
                      self.app.internalNotes)                  # Kommentar am 360-Grad-Ort

    def test_schedule_interview_also_gated(self):
        from ..models import Interview
        self._world()
        self.client.force_login(self.rec)
        r = self.client.post(reverse('ats:schedule_interview'), data={
            "application_id": str(self.app.id), "slot_id": "CANDIDATE_CHOICE",
            "location_type": "VIDEO", "message_text": "x"})
        self.assertEqual(r.status_code, 302)
        self.assertIn("gremium=", r["Location"])               # abgewiesen mit Grund
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "IN_REVIEW")
        self.assertEqual(Interview.objects.count(), 0)

    def test_hr_admin_override_with_audit_recruiter_cannot(self):
        from ..models import AuditLog
        self._world()
        self.client.force_login(self.rec)
        r = self.client.post(reverse('ats:update_status', args=[self.app.id]),
                             data={"status": "INVITED", "force": "1"}).json()
        self.assertFalse(r["success"])                         # Recruiter: kein Override
        admin = make_user("panadmin", role="HR-Admin")
        self.client.force_login(admin)
        r = self.client.post(reverse('ats:update_status', args=[self.app.id]),
                             data={"status": "INVITED", "force": "1"}).json()
        self.assertTrue(r["success"])
        self.assertTrue(AuditLog.objects.filter(action="PANEL_OVERRIDDEN").exists())

    def test_only_panel_members_vote_and_vote_is_changeable(self):
        from ..models import ApplicationVote, AuditLog
        self._world()
        outsider = make_user("outsider", role="Recruiter")
        self.client.force_login(outsider)
        r = self.client.post(reverse('ats:application_vote', args=[self.app.id]),
                             data={"vote": "FOR"})
        self.assertEqual(r.status_code, 403)                   # kein Stimmrecht
        self.assertEqual(ApplicationVote.objects.count(), 0)
        self._vote(self.m3, "AGAINST")
        self._vote(self.m3, "FOR")                             # Meinung geaendert
        self.assertEqual(ApplicationVote.objects.count(), 1)   # eine Stimme je Person
        self.assertEqual(ApplicationVote.objects.get().vote, "FOR")
        self.assertEqual(AuditLog.objects.filter(action="PANEL_VOTE_CAST").count(), 2)
        # Postfach zeigt die Gremiums-Sektion
        page = self.client.get(reverse('ats:approvals'))
        self.assertContains(page, "Sichtungs-Gremium")
        self.assertContains(page, "Pflegedienstleitung")

class DelegationOverrideRemindersTestCase(TestCase):
    """Vertretung wirkt (Freigaben + Gremium), granulares Override, Mahnungen."""

    def _world(self):
        import uuid as _u

        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            RoleDelegation,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        self.fac = Facility.objects.create(name="Klinik A", organization=org,
                                           requiresApproval=True,
                                           approvalChain="Hiring-Manager")
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        self.hm = make_user("hmchef", role="Hiring-Manager")     # im Urlaub
        self.hm.email = "chef@klinik.example"
        self.hm.save()
        self.vertretung = make_user("stellvertreter", role="Viewer")
        self.vertretung.email = "vertreter@klinik.example"
        self.vertretung.save()
        RoleDelegation.objects.create(
            delegator=self.hm, delegatee=self.vertretung,
            scopeType="ALL", scopeId=None,
            validFrom=timezone.now() - datetime.timedelta(days=1),
            validUntil=timezone.now() + datetime.timedelta(days=14))
        self.job = JobPosting.objects.create(
            title="Pflegedienstleitung", organization=org, facility=self.fac,
            location=loc, jobFamily=fam, workflowState=wf,
            panelUserIdsJson=[str(self.hm.id)])
        ap = Applicant.objects.create(firstName="Ines", lastName="T",
                                      email="ines@x.de")
        self.app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                              status="IN_REVIEW")
        self.org, self.loc, self.wf, self.fam = org, loc, wf, fam

    def test_delegation_unblocks_approval_step(self):
        from ..approvals import ensure_approval_gate
        from ..models import ApprovalStep
        self._world()
        ensure_approval_gate(self.job)                          # Kette: Hiring-Manager
        self.client.force_login(self.vertretung)                # Viewer, aber Vertretung
        page = self.client.get(reverse('ats:approvals'))
        self.assertContains(page, "Pflegedienstleitung")
        self.assertContains(page, "in Vertretung für")
        step = ApprovalStep.objects.get()
        r = self.client.post(reverse('ats:approvals'),
                             data={"step_id": str(step.id), "action": "approve"})
        self.assertEqual(r.status_code, 302)
        step.refresh_from_db()
        self.assertEqual(step.status, "APPROVED")
        self.assertIn("In Vertretung für", step.comments)       # dokumentiert

    def test_delegate_vote_fills_seat_member_vote_wins(self):
        from ..models import ApplicationVote
        from ..panel import panel_state
        self._world()
        # Vertretung stimmt fuer den Sitz des abwesenden Mitglieds
        self.client.force_login(self.vertretung)
        r = self.client.post(reverse('ats:application_vote', args=[self.app.id]),
                             data={"vote": "FOR"})
        self.assertEqual(r.status_code, 302)
        state = panel_state(self.app)
        self.assertTrue(state["allowed"])                       # 1/1-Sitz gefuellt
        # Mitglied kommt zurueck und stimmt selbst DAGEGEN -> eigene Stimme siegt
        self.client.force_login(self.hm)
        self.client.post(reverse('ats:application_vote', args=[self.app.id]),
                         data={"vote": "AGAINST"})
        state = panel_state(self.app)
        self.assertFalse(state["allowed"])
        self.assertEqual(ApplicationVote.objects.count(), 2)    # beide Stimmen erhalten

    def test_override_groups_setting_is_granular(self):

        from ..models import AuditLog, SystemSetting
        self._world()
        SystemSetting.objects.create(key="OVERRIDE_GROUPS",
                                     value="HR-Admin, Geschäftsführung")
        gf = make_user("gfuser", role="Recruiter")
        gf.groups.add(Group.objects.get_or_create(name="Geschäftsführung")[0])
        self.client.force_login(gf)
        r = self.client.post(reverse('ats:update_status', args=[self.app.id]),
                             data={"status": "INVITED", "force": "1"}).json()
        self.assertTrue(r["success"])                           # granular erlaubt
        self.assertTrue(AuditLog.objects.filter(action="PANEL_OVERRIDDEN").exists())
        plain = make_user("plainrec", role="Recruiter")
        self.app.status = "IN_REVIEW"
        self.app.save()
        self.client.force_login(plain)
        r = self.client.post(reverse('ats:update_status', args=[self.app.id]),
                             data={"status": "INVITED", "force": "1"}).json()
        self.assertFalse(r["success"])                          # ohne Gruppe: nein

    def test_decision_reminders_once_including_delegates(self):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command

        from ..approvals import ensure_approval_gate
        from ..models import Application
        self._world()
        ensure_approval_gate(self.job)
        # Vorgaenge kuenstlich altern lassen
        Application.objects.filter(id=self.app.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=5))
        from ..models import ApprovalTicket
        ApprovalTicket.objects.update(
            createdAt=timezone.now() - datetime.timedelta(days=5))
        call_command("send_decision_reminders", stdout=StringIO())
        recipients = [a for m in mail.outbox for a in m.to]
        self.assertIn("chef@klinik.example", recipients)        # Inhaber (2x: Freigabe+Gremium)
        self.assertIn("vertreter@klinik.example", recipients)   # Vertretung mit erinnert
        vertreter_mail = [m for m in mail.outbox
                          if "vertreter@klinik.example" in m.to][0]
        self.assertIn("In Vertretung für", vertreter_mail.body)
        count_first = len(mail.outbox)
        call_command("send_decision_reminders", stdout=StringIO())
        self.assertEqual(len(mail.outbox), count_first)         # einmalig je Vorgang

class DelegationLifecycleAndPanelDefaultsTestCase(TestCase):
    """UC-VT-02 (Sofort-Deaktivierung) + flexible Gremien-Defaults (Leiter)."""

    def _world(self):
        import uuid as _u

        from ..models import (
            Department,
            Facility,
            JobFamily,
            Location,
            Organization,
            WorkflowState,
        )
        self.org = Organization.objects.create(
            name="Traeger", panelUserIdsJson=[])
        self.loc = Location.objects.create(name="HH")
        self.fac = Facility.objects.create(name="Klinik A", organization=self.org)
        self.dept = Department.objects.create(name="Station 3", facility=self.fac)
        self.fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        self.fam_aushilfe = JobFamily.objects.create(
            name="Aushilfe-" + str(_u.uuid4())[:4],
            panelUserIdsJson=["NONE"])
        self.wf = WorkflowState.objects.create(name="published")
        self.gremium_user = make_user("orggremium", role="Hiring-Manager")
        self.org.panelUserIdsJson = [str(self.gremium_user.id)]
        self.org.save()

    def _job(self, **kw):
        from ..models import JobPosting
        base = dict(title="Stelle", organization=self.org, facility=self.fac,
                    location=self.loc, jobFamily=self.fam, workflowState=self.wf)
        base.update(kw)
        return JobPosting.objects.create(**base)

    def _app(self, job):
        import uuid as _u

        from ..models import Applicant, Application
        ap = Applicant.objects.create(firstName="K", lastName=str(_u.uuid4())[:4],
                                      email=f"{_u.uuid4()}@x.de")
        return Application.objects.create(applicant=ap, jobPosting=job,
                                          status="IN_REVIEW")

    def test_panel_inheritance_ladder_and_none_sentinel(self):

        from ..panel import resolve_panel
        self._world()
        # 1) Firmen-Default erbt auf normale Stelle
        job = self._job(title="Pflegefachkraft")
        members, source = resolve_panel(job)
        self.assertEqual(members, [str(self.gremium_user.id)])
        self.assertEqual(source, "Organisation")
        # 2) Abteilungs-Default schlaegt Firmen-Default
        dept_user = make_user("deptgremium", role="Recruiter")
        self.dept.panelUserIdsJson = [str(dept_user.id)]
        self.dept.save()
        job_dept = self._job(title="Stationsleitung", department=self.dept)
        members, source = resolve_panel(job_dept)
        self.assertEqual(members, [str(dept_user.id)])
        self.assertEqual(source, "Abteilung")
        # 3) Stellen-Ebene schlaegt alles
        job_own = self._job(title="PDL", department=self.dept,
                            panelUserIdsJson=[str(self.gremium_user.id),
                                              str(dept_user.id)])
        members, source = resolve_panel(job_own)
        self.assertEqual(source, "Stelle")
        self.assertEqual(len(members), 2)
        # 4) Sentinel NONE unterbricht Vererbung trotz Firmen-Default
        job_aushilfe = self._job(title="Aushilfe Küche",
                                 jobFamily=self.fam_aushilfe)
        members, source = resolve_panel(job_aushilfe)
        self.assertEqual(members, [])
        self.assertIn("bewusst kein Gremium", source)
        # Gate: geerbtes Gremium blockiert, Aushilfe nicht
        rec = make_user("ladrec2", role="Recruiter")
        self.client.force_login(rec)
        app = self._app(job)
        r = self.client.post(reverse('ats:update_status', args=[app.id]),
                             data={"status": "INVITED"}).json()
        self.assertFalse(r["success"])
        self.assertIn("Organisation", r["error"])              # Quelle erklaert
        app2 = self._app(job_aushilfe)
        r = self.client.post(reverse('ats:update_status', args=[app2.id]),
                             data={"status": "INVITED"}).json()
        self.assertTrue(r["success"])

    def test_inherited_membership_shows_in_inbox_and_focus(self):
        self._world()
        self._app(self._job(title="Pflegefachkraft Nacht"))
        self.client.force_login(self.gremium_user)             # nur via Org-Default
        page = self.client.get(reverse('ats:approvals'))
        self.assertContains(page, "Pflegefachkraft Nacht")
        dash = self.client.get(reverse('ats:dashboard'))
        self.assertContains(dash, "Gremium-Stimme")            # Heute-wichtig-Pill

    def test_delegation_early_end_takes_effect_immediately(self):
        """UC-VT-02: vorzeitiges Beenden wirkt sofort in Postfach UND Gremium."""

        from ..approvals import ensure_approval_gate
        from ..models import RoleDelegation
        from ..panel import panel_state
        self._world()
        self.fac.requiresApproval = True
        self.fac.approvalChain = "Hiring-Manager"
        self.fac.save()
        vt = make_user("volkan", role="Viewer")
        d = RoleDelegation.objects.create(
            delegator=self.gremium_user, delegatee=vt, scopeType="ALL",
            validFrom=timezone.now() - datetime.timedelta(days=1),
            validUntil=timezone.now() + datetime.timedelta(days=14))
        job = self._job(title="PDL-Stelle")
        ensure_approval_gate(job)
        app = self._app(job)
        self.client.force_login(vt)
        # Wirkt: Postfach zeigt Schritt, Stimme fuellt Sitz
        self.assertContains(self.client.get(reverse('ats:approvals')), "PDL-Stelle")
        self.client.post(reverse('ats:application_vote', args=[app.id]),
                         data={"vote": "FOR"})
        self.assertTrue(panel_state(app)["allowed"])
        # HR-Admin beendet vorzeitig -> Sofortwirkung ueberall
        admin = make_user("endadmin", role="HR-Admin")
        self.client.force_login(admin)
        self.client.post(reverse('ats:delegations'), data={"end_id": str(d.id)})
        d.refresh_from_db()
        self.assertLessEqual(d.validUntil, timezone.now())
        self.client.force_login(vt)
        page = self.client.get(reverse('ats:approvals'))
        self.assertNotContains(page, "in Vertretung für")      # Postfach: weg
        self.assertFalse(panel_state(app)["allowed"])          # Sitz-Stimme zaehlt nicht mehr
        r = self.client.post(reverse('ats:application_vote', args=[app.id]),
                             data={"vote": "FOR"})
        self.assertEqual(r.status_code, 403)                   # Stimmrecht weg

    def test_defaults_page_requires_hr_admin_and_saves(self):
        self._world()
        self.client.force_login(make_user("defrec", role="Recruiter"))
        self.assertEqual(self.client.get(reverse('ats:panel_defaults')).status_code, 403)
        admin = make_user("defadmin", role="HR-Admin")
        self.client.force_login(admin)
        member = make_user("neuling", role="Recruiter")
        r = self.client.post(reverse('ats:panel_defaults'), data={
            "level": "job_family", "entity_id": str(self.fam.id),
            "members": [str(member.id)]})
        self.assertEqual(r.status_code, 302)
        self.fam.refresh_from_db()
        self.assertIn(str(member.id), self.fam.panelUserIdsJson)
        # "Bewusst kein Gremium"
        self.client.post(reverse('ats:panel_defaults'), data={
            "level": "job_family", "entity_id": str(self.fam.id), "no_panel": "1"})
        self.fam.refresh_from_db()
        self.assertIn("NONE", self.fam.panelUserIdsJson)

class PanelPreviewAndConvertInheritanceTestCase(TestCase):
    """Gremium-Flexibilitaet auch beim Prozess-ERSTELLEN: Vorschau + Vererbung."""

    def _world(self):
        import uuid as _u

        from ..models import Department, Facility, JobFamily, Location, Organization, WorkflowState
        self.gremium_user = make_user("prevgremium", role="Hiring-Manager")
        self.org = Organization.objects.create(
            name="Traeger", panelUserIdsJson=[str(self.gremium_user.id)])
        self.loc = Location.objects.create(name="HH")
        self.fac = Facility.objects.create(name="Klinik A", organization=self.org)
        self.dept = Department.objects.create(name="Station 3", facility=self.fac)
        self.fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        self.wf = WorkflowState.objects.create(name="published")
        SystemSetting.objects.create(key="APPROVAL_CHAIN", value="HR-Admin")

    def test_preview_resolves_ladder_and_requires_role(self):
        self._world()
        url = (reverse('ats:panel_preview')
               + f"?facility={self.fac.id}&job_family={self.fam.id}")
        self.assertNotEqual(self.client.get(url).status_code, 200)  # ohne Login nix
        self.client.force_login(make_user("prevrec", role="Recruiter"))
        d = self.client.get(url).json()
        self.assertEqual(d["source"], "Organisation")           # Firmen-Default
        self.assertIn("prevgremium", d["members"])
        # Abteilungs-Default schlaegt Organisation – Vorschau folgt der Leiter
        dept_user = make_user("prevdept", role="Recruiter")
        self.dept.panelUserIdsJson = [str(dept_user.id)]
        self.dept.save()
        d = self.client.get(url + f"&department={self.dept.id}").json()
        self.assertEqual(d["source"], "Abteilung")
        self.assertEqual(d["members"], ["prevdept"])

    def test_converted_draft_inherits_org_panel_gate(self):
        from ..models import Applicant, Application, JobPosting, StaffingRequest
        self._world()
        req = StaffingRequest.objects.create(
            title="Pflegedienstleitung neu", facility=self.fac,
            jobFamily=self.fam, status="ACCEPTED", justification="intern")
        rec = make_user("prevrec2", role="Recruiter")
        self.client.force_login(rec)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "convert", "request_id": str(req.id),
            "location": str(self.loc.id)})
        job = JobPosting.objects.get(title="Pflegedienstleitung neu")
        self.assertEqual(job.panelUserIdsJson, [])              # erbt, kein Eigen-Panel
        ap = Applicant.objects.create(firstName="N", lastName="P", email="np@x.de")
        app = Application.objects.create(applicant=ap, jobPosting=job,
                                         status="IN_REVIEW")
        r = self.client.post(reverse('ats:update_status', args=[app.id]),
                             data={"status": "INVITED"}).json()
        self.assertFalse(r["success"])                          # Org-Gremium greift
        self.assertIn("Organisation", r["error"])

@override_settings(DEMO_MODE=True)
class DemoGovernanceWorldTestCase(TestCase):
    """Die Governance-Demo-Welt ist klickbar: Gremium, Vertretung, Standards, Pool."""

    def setUp(self):
        import os
        from io import StringIO

        from django.core.management import call_command
        os.environ["DEMO_MODE"] = "1"
        call_command("seed_demo", stdout=StringIO())

    def tearDown(self):
        import os
        os.environ.pop("DEMO_MODE", None)

    def test_gremium_case_is_demonstrable(self):
        from ..models import Application, JobPosting
        from ..panel import panel_state
        job = JobPosting.objects.get(title__startswith="Pflegedienstleitung")
        app = Application.objects.get(jobPosting=job)
        state = panel_state(app)
        self.assertTrue(state["required"])
        self.assertEqual(state["members"], 3)
        self.assertEqual(state["votes_for"], 1)                # 1/3: Gate greift
        self.assertFalse(state["allowed"])
        # demo-recruiter kann die Einladung NICHT durchziehen (Live-Demo-Moment)
        from django.contrib.auth.models import User
        self.client.force_login(User.objects.get(username="demo-admin"))
        r = self.client.post(reverse('ats:update_status', args=[app.id]),
                             data={"status": "INVITED"}).json()
        self.assertFalse(r["success"])
        self.assertIn("Gremium", r["error"])

    def test_vertretung_and_pending_signals_visible(self):
        from django.contrib.auth.models import User
        vt = User.objects.get(username="demo-vertretung")
        self.client.force_login(vt)
        page = self.client.get(reverse('ats:approvals'))
        self.assertContains(page, "Sichtungs-Gremium")         # Sitz via Vertretung
        self.assertContains(page, "Pflegedienstleitung")
        hm = User.objects.get(username="demo-hm")
        self.client.force_login(hm)
        dash = self.client.get(reverse('ats:dashboard'))
        self.assertContains(dash, "Gremium-Stimme")            # Heute-wichtig-Pill

    def test_minimum_standard_and_pool_match_seeded(self):
        from django.contrib.auth.models import User

        from ..models import JobFamily, TalentPoolSubscription
        fam = JobFamily.objects.get(name="Pflege")
        self.assertIn("Examen", str(fam.minimumQuestionsJson))
        self.assertEqual(TalentPoolSubscription.objects.count(), 2)
        self.client.force_login(User.objects.get(username="demo-admin"))
        page = self.client.get(reverse('ats:talent_pool'))
        self.assertContains(page, "jonas.weber@beispiel-demo.de")
        self.assertContains(page, "Auf Stelle hinweisen")      # aktiver Treffer
        self.assertContains(page, "abgelaufen")                # Kulanz sichtbar
        bedarf = self.client.get(reverse('ats:staffing_requests'))
        self.assertContains(bedarf, "Leasingkräften")          # offene Meldung

class PanelQuorumDeadlineTestCase(TestCase):
    """P1-8: konfigurierbares Quorum + Abstimmungs-Frist mit Eskalation."""

    def _world(self, quorum=None, deadline=None, seats=3):

        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        self.fac = Facility.objects.create(name="F", organization=org)
        self.fam = JobFamily.objects.create(name="PQ-Fam")
        self.published = WorkflowState.objects.create(name="published")
        self.members = [make_user(f"pq-m{i}", role="Hiring-Manager")
                        for i in range(seats)]
        for i, m in enumerate(self.members):
            m.email = f"pq-m{i}@x.de"
            m.save(update_fields=["email"])
        self.job = JobPosting.objects.create(
            title="Leitung Wohnbereich", organization=org, facility=self.fac,
            location=loc, jobFamily=self.fam, workflowState=self.published,
            panelQuorum=quorum, panelDeadlineDays=deadline,
            panelUserIdsJson=[str(m.id) for m in self.members])
        ap = Applicant.objects.create(firstName="P", lastName="Q",
                                      email="pq@x.de")
        self.app = Application.objects.create(applicant=ap,
                                              jobPosting=self.job,
                                              status="IN_REVIEW")

    def _vote(self, user, vote="FOR"):
        from ..models import ApplicationVote
        ApplicationVote.objects.create(application=self.app, user=user,
                                       vote=vote)

    def _invite(self):
        return self.client.post(
            reverse('ats:update_status', args=[self.app.id]),
            data={"status": "INVITED"})

    def test_quorum_one_vote_suffices_where_majority_would_block(self):
        self._world(quorum=1)
        self.client.force_login(make_user("pqrec", role="Recruiter"))
        self._vote(self.members[0])                            # 1 von 3
        r = self._invite()
        self.assertTrue(r.json()["success"])                   # Quorum erfuellt
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "INVITED")

    def test_default_majority_still_blocks_single_vote(self):
        self._world(quorum=None)
        self.client.force_login(make_user("pqrec2", role="Recruiter"))
        self._vote(self.members[0])
        r = self._invite()
        self.assertFalse(r.json()["success"])                  # blockiert
        self.assertTrue(r.json()["panel_blocked"])
        self.assertIn("Mehrheit von 3", r.json()["error"])

    def test_quorum_larger_than_seats_is_capped(self):
        from ..panel import panel_state
        self._world(quorum=5, seats=3)
        self.assertEqual(panel_state(self.app)["needed"], 3)   # ehrlich gekappt
        self._vote(self.members[0])
        self._vote(self.members[1])
        self.client.force_login(make_user("pqrec3", role="Recruiter"))
        r = self._invite()
        self.assertFalse(r.json()["success"])                  # 2 < 3
        self.assertIn("3 von 3 (Quorum)", r.json()["error"])
        self._vote(self.members[2])
        self.assertTrue(self._invite().json()["success"])      # 3 von 3

    def test_deadline_overdue_badge_and_single_escalation(self):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command

        from ..models import Application
        from ..panel import panel_state
        self._world(deadline=7)
        Application.objects.filter(id=self.app.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=10))
        self.app.refresh_from_db()
        state = panel_state(self.app)
        self.assertTrue(state["overdue"])                      # 10 > 7 Tage
        self.assertIn("Frist überschritten", state["summary"])
        # Freigabe-Postfach zeigt das Badge
        self.client.force_login(self.members[0])
        page = self.client.get(reverse('ats:approvals'))
        self.assertContains(page, "Frist überschritten")
        # Eskalations-Mail einmalig, auch bei Doppellauf
        call_command("send_decision_reminders", "--days", "3",
                     stdout=StringIO())
        first = len([m for m in mail.outbox
                     if "Frist überschritten" in m.subject])
        self.assertEqual(first, 3)                             # je Sitz einmal
        call_command("send_decision_reminders", "--days", "3",
                     stdout=StringIO())
        again = len([m for m in mail.outbox
                     if "Frist überschritten" in m.subject])
        self.assertEqual(again, 3)                             # kein Doppelversand

    def test_wizard_sets_and_edit_preserves(self):
        self._world()
        self.client.force_login(make_user("pqadmin", role="HR-Admin"))
        base = {"job_id": str(self.job.id), "title": "Leitung Wohnbereich",
                "description": "x", "tasks": "", "requirements": "",
                "screening_questions": "[]",
                "facility": str(self.fac.id),
                "location": str(self.job.location_id),
                "job_family": str(self.fam.id)}
        self.client.post(reverse('ats:create_job'),
                         data={**base, "panel_quorum": "2",
                               "panel_deadline_days": "70"})
        self.job.refresh_from_db()
        self.assertEqual(self.job.panelQuorum, 2)
        self.assertEqual(self.job.panelDeadlineDays, 60)       # geklemmt
        # Edit OHNE die Felder: Bestand bleibt (Lehre aus Headcount-Runde)
        self.client.post(reverse('ats:create_job'), data=base)
        self.job.refresh_from_db()
        self.assertEqual(self.job.panelQuorum, 2)
        self.assertEqual(self.job.panelDeadlineDays, 60)

class RequisitionProcessTestCase(TestCase):
    """Stellenfreigabe: optional, aber wenn aktiv, dann Pflicht."""

    def _world(self, active=True, chain="Bereichsleitung, Geschäftsführung"):

        from ..models import Facility, JobFamily, Location, Organization, SystemSetting, WorkflowState
        org = Organization.objects.create(name="O")
        self.loc = Location.objects.create(name="HH")
        self.fac = Facility.objects.create(name="Haus Nord", organization=org)
        self.fam = JobFamily.objects.create(name="RQ-Fam")
        self.published = WorkflowState.objects.create(name="published")
        WorkflowState.objects.create(name="draft")
        from ..models import PayBand
        self.band = PayBand.objects.create(
            name="RQ-Band", minAmount=3000, maxAmount=3800)
        if active:
            SystemSetting.objects.create(key="REQUISITION_REQUIRED",
                                         value="1")
            SystemSetting.objects.create(key="REQUISITION_CHAIN",
                                         value=chain)
        self.bl = make_user("rq-bl", role="Hiring-Manager")
        Group.objects.get_or_create(name="Bereichsleitung")[0].user_set.add(
            self.bl)
        self.gf = make_user("rq-gf", role="Hiring-Manager")
        Group.objects.get_or_create(name="Geschäftsführung")[0].user_set.add(
            self.gf)
        self.requester = make_user("rq-tl", role="Hiring-Manager")
        self.requester.email = "tl@x.de"
        self.requester.save(update_fields=["email"])

    def _request_need(self):
        from ..models import StaffingRequest
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "create", "facility": str(self.fac.id),
            "title": "Pflegefachkraft Nachtdienst", "headcount": "2",
            "job_family": str(self.fam.id),
            "justification": "Nachtdienst unterbesetzt."})
        return StaffingRequest.objects.get()

    def _decide(self, user, req, decision, comment=""):
        step = req.steps.filter(status='PENDING').order_by('order').first()
        self.client.force_login(user)
        return self.client.post(reverse('ats:staffing_requests'), data={
            "form": "step_decide", "step_id": str(step.id),
            "decision": decision, "comment": comment})

    def test_publish_blocked_without_approved_need(self):
        from ..models import JobPosting
        self._world(active=True)
        self.client.force_login(make_user("rq-admin", role="HR-Admin"))
        self.client.post(reverse('ats:create_job'), data={
            "title": "Direkt-Versuch", "description": "x", "tasks": "",
            "requirements": "", "screening_questions": "[]",
            "facility": str(self.fac.id), "location": str(self.loc.id),
            "job_family": str(self.fam.id),
            "workflow_state": str(self.published.id),
            "pay_band": str(self.band.id)})
        job = JobPosting.objects.get(title="Direkt-Versuch")
        self.assertEqual(job.workflowState.name, "draft")      # blockiert
        # Schnell-Toggle umgeht das Gate nicht
        r = self.client.post(reverse('ats:toggle_job_active', args=[job.id]))
        self.assertEqual(r.status_code, 409)
        self.assertIn("Stellenfreigabe", r.json()["error"])

    def test_sequential_chain_then_convert_carries_headcount(self):
        self._world(active=True)
        req = self._request_need()
        self.assertEqual(req.status, "IN_APPROVAL")
        self.assertEqual(req.steps.count(), 2)                 # zwei Stufen
        # GF darf Stufe 1 (Bereichsleitung) nicht entscheiden
        self._decide(self.gf, req, "approve")
        req.refresh_from_db()
        self.assertEqual(req.steps.filter(status='APPROVED').count(), 0)
        # Reihenfolge eingehalten: BL, dann GF
        self._decide(self.bl, req, "approve")
        self._decide(self.gf, req, "approve")
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")
        # Konvertieren erzeugt die Ausschreibung MIT headcount aus dem Bedarf
        self.client.force_login(make_user("rq-rec", role="Recruiter"))
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "convert", "request_id": str(req.id),
            "location": str(self.loc.id)})
        req.refresh_from_db()
        self.assertEqual(req.status, "CONVERTED")
        job = req.convertedJob
        self.assertEqual(job.headcount, 2)                     # uebernommen
        # Der Nachweis oeffnet die Veroeffentlichung (Toggle nicht mehr 409
        # wegen Requisition; das Job-Freigabe-Gate ist ein anderes Thema)
        r = self.client.post(reverse('ats:toggle_job_active', args=[job.id]))
        self.assertNotIn("Stellenfreigabe", (r.json().get("error") or ""))

    def test_return_and_resubmit_restart_chain(self):
        from django.core import mail
        self._world(active=True)
        req = self._request_need()
        self._decide(self.bl, req, "return", comment="Budget unklar.")
        req.refresh_from_db()
        self.assertEqual(req.status, "RETURNED")
        self.assertTrue(any("Nachbesserung" in m.subject for m in mail.outbox))
        # Nur Antragsteller reicht neu ein; Kette startet von vorn
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "resubmit", "request_id": str(req.id),
            "justification": "Budget bestätigt durch Controlling."})
        req.refresh_from_db()
        self.assertEqual(req.status, "IN_APPROVAL")
        self.assertEqual(req.steps.filter(status='PENDING').count(), 2)
        self.assertIn("Controlling", req.justification)

    def test_inactive_process_changes_nothing(self):
        from ..models import JobPosting
        self._world(active=False)
        self.client.force_login(make_user("rq-admin2", role="HR-Admin"))
        self.client.post(reverse('ats:create_job'), data={
            "title": "Ohne Prozess", "description": "x", "tasks": "",
            "requirements": "", "screening_questions": "[]",
            "facility": str(self.fac.id), "location": str(self.loc.id),
            "job_family": str(self.fam.id),
            "workflow_state": str(self.published.id),
            "pay_band": str(self.band.id)})
        self.assertEqual(JobPosting.objects.get().workflowState.name,
                         "published")                          # wie bisher
        req = self._request_need()
        self.assertEqual(req.status, "OPEN")                   # keine Kette
        self.assertEqual(req.steps.count(), 0)

    def test_direct_decide_disabled_while_chain_runs(self):
        self._world(active=True)
        req = self._request_need()
        self.client.force_login(make_user("rq-rec2", role="Recruiter"))
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "decide", "request_id": str(req.id),
            "decision": "ACCEPTED"})
        req.refresh_from_db()
        self.assertEqual(req.status, "IN_APPROVAL")            # Kette gilt

class RequisitionRoutingTestCase(TestCase):
    """No-Code Routing-Matrix: Scope-Regeln, Spezifität, Formular, Pflicht."""

    def _world(self):

        from ..models import Department, Facility, JobFamily, Location, Organization, RequisitionRule, WorkflowState
        org = Organization.objects.create(name="O")
        self.loc = Location.objects.create(name="Wien")
        self.fac = Facility.objects.create(name="Headquarter",
                                           organization=org)
        self.dep_it = Department.objects.create(name="IT", facility=self.fac)
        self.dep_sales = Department.objects.create(name="Vertrieb",
                                                   facility=self.fac)
        self.fam_core = JobFamily.objects.create(name="Core Banking")
        self.fam_admin = JobFamily.objects.create(name="Administration")
        self.published = WorkflowState.objects.create(name="published")
        WorkflowState.objects.create(name="draft")
        for role in ("Bereichsleitung", "Risikomanagement",
                     "Geschäftsführung", "Filialleitung"):
            Group.objects.get_or_create(name=role)
        # Drei Regeln wie im Anforderungs-Prompt
        self.r_tech = RequisitionRule.objects.create(
            name="Tech-Prozess Core Banking", facility=self.fac,
            department=self.dep_it, jobFamily=self.fam_core,
            chain="Bereichsleitung, Risikomanagement, Geschäftsführung",
            mandatory=True,
            formQuestionsJson=[{"id": "stack", "type": "TEXT",
                               "isMandatory": True,
                               "question": "Welcher Tech-Stack wird betreut?"}])
        self.r_std = RequisitionRule.objects.create(
            name="Standard Vertrieb", facility=self.fac,
            department=self.dep_sales, chain="Filialleitung",
            mandatory=False)
        self.r_fallback = RequisitionRule.objects.create(
            name="Fallback", chain="Geschäftsführung", mandatory=False)
        from ..models import PayBand
        self.band = PayBand.objects.create(
            name="RT-Band", minAmount=3200, maxAmount=4400)
        self.requester = make_user("rt-tl", role="Hiring-Manager")

    def test_resolver_specific_beats_general(self):
        from ..approvals import requisition_chain, resolve_requisition_rule
        self._world()
        self.assertEqual(
            resolve_requisition_rule(self.fac, self.dep_it, self.fam_core),
            self.r_tech)                                       # exakter Match
        self.assertEqual(
            resolve_requisition_rule(self.fac, self.dep_sales,
                                     self.fam_admin),
            self.r_std)                                        # Teil-Match
        self.assertEqual(
            resolve_requisition_rule(None, None, self.fam_admin),
            self.r_fallback)                                   # Fallback
        self.assertEqual(
            requisition_chain(self.fac, self.dep_it, self.fam_core),
            ["Bereichsleitung", "Risikomanagement", "Geschäftsführung"])

    def test_rule_mandatory_blocks_publish_without_global_switch(self):
        from ..models import JobPosting
        self._world()                                          # KEIN globaler Schalter
        self.client.force_login(make_user("rt-admin", role="HR-Admin"))
        self.client.post(reverse('ats:create_job'), data={
            "title": "Core-Banking-Architekt", "description": "x",
            "tasks": "", "requirements": "", "screening_questions": "[]",
            "facility": str(self.fac.id), "department": str(self.dep_it.id),
            "location": str(self.loc.id),
            "job_family": str(self.fam_core.id),
            "workflow_state": str(self.published.id),
            "pay_band": str(self.band.id)})
        job = JobPosting.objects.get(title="Core-Banking-Architekt")
        self.assertEqual(job.workflowState.name, "draft")      # Regel-Pflicht
        # Vertrieb (Regel optional) publiziert frei
        self.client.post(reverse('ats:create_job'), data={
            "title": "Vertriebsassistenz", "description": "x",
            "tasks": "", "requirements": "", "screening_questions": "[]",
            "facility": str(self.fac.id),
            "department": str(self.dep_sales.id),
            "location": str(self.loc.id),
            "job_family": str(self.fam_admin.id),
            "workflow_state": str(self.published.id),
            "pay_band": str(self.band.id)})
        self.assertEqual(JobPosting.objects.get(
            title="Vertriebsassistenz").workflowState.name, "published")

    def test_dynamic_form_questions_enforced_and_stored(self):

        from ..models import StaffingRequest
        self._world()
        self.client.force_login(self.requester)
        # GET mit Geltungsbereich zeigt die Regel-Frage
        page = self.client.get(
            reverse('ats:staffing_requests')
            + f"?facility={self.fac.id}&department={self.dep_it.id}"
              f"&job_family={self.fam_core.id}")
        self.assertContains(page, "Welcher Tech-Stack wird betreut?")
        base = {"form": "create", "facility": str(self.fac.id),
                "department": str(self.dep_it.id),
                "job_family": str(self.fam_core.id),
                "title": "Senior Architekt", "headcount": "1",
                "justification": "Regulatorik-Programm."}
        # Pflichtfrage fehlt -> kein Antrag
        self.client.post(reverse('ats:staffing_requests'), data=base)
        self.assertEqual(StaffingRequest.objects.count(), 0)
        # Mit Antwort: Antrag + Kette aus der Regel + Antwort gespeichert
        self.client.post(reverse('ats:staffing_requests'),
                         data={**base, "rq_stack": "Kernbank T24, ISO 20022"})
        req = StaffingRequest.objects.get()
        self.assertEqual(req.status, "IN_APPROVAL")
        self.assertEqual([st.role for st in req.steps.all()],
                         ["Bereichsleitung", "Risikomanagement",
                          "Geschäftsführung"])
        answers = req.answersJson
        self.assertEqual(answers["Welcher Tech-Stack wird betreut?"],
                         "Kernbank T24, ISO 20022")
        # Entscheider sieht die Angaben
        gf = make_user("rt-gf", role="Recruiter")
        self.client.force_login(gf)
        inbox = self.client.get(reverse('ats:staffing_requests'))
        self.assertContains(inbox, "Kernbank T24")

    def test_final_job_approval_cannot_bypass_requisition(self):
        from ..models import JobPosting
        self._world()
        SystemSetting.objects.create(key="REQUISITION_REQUIRED", value="1")
        self.fac.requiresApproval = True
        self.fac.approvalChain = "HR-Admin"
        self.fac.save(update_fields=["requiresApproval", "approvalChain"])
        admin = make_user("rt-admin2", role="HR-Admin")
        self.client.force_login(admin)
        self.client.post(reverse('ats:create_job'), data={
            "title": "Bypass-Versuch", "description": "x", "tasks": "",
            "requirements": "", "screening_questions": "[]",
            "facility": str(self.fac.id), "location": str(self.loc.id),
            "job_family": str(self.fam_admin.id),
            "workflow_state": str(self.published.id)})
        job = JobPosting.objects.get(title="Bypass-Versuch")
        step = job.approvalTicket.steps.get()
        # Finale Job-Freigabe: publiziert NICHT ohne genehmigten Bedarf
        self.client.post(reverse('ats:approvals'), data={
            "step_id": str(step.id), "action": "approve"})
        job.refresh_from_db()
        self.assertEqual(job.approvalTicket.status, "APPROVED")
        self.assertEqual(job.workflowState.name, "draft")      # Gate hält

class RequisitionDelegationTestCase(TestCase):
    """Vertretung in der Stellenfreigabe-Kette (UC-EW-07) + Sichtbarkeit
    der Eingangs-Liste fuer Ketten-Genehmiger ohne Recruiter-Rolle."""

    def _world(self):

        from ..models import Facility, JobFamily, Organization, SystemSetting, WorkflowState
        org = Organization.objects.create(name="O")
        self.fac = Facility.objects.create(name="Zentrale", organization=org)
        self.fac2 = Facility.objects.create(name="Filiale Sued",
                                            organization=org)
        JobFamily.objects.create(name="DL-Fam")
        WorkflowState.objects.create(name="published")
        SystemSetting.objects.create(key="REQUISITION_REQUIRED", value="1")
        SystemSetting.objects.create(key="REQUISITION_CHAIN",
                                     value="Vorstand")
        self.vorstand = make_user("dl-vorstand", role="Hiring-Manager")
        Group.objects.get_or_create(name="Vorstand")[0].user_set.add(
            self.vorstand)
        self.deputy = make_user("dl-vertretung", role="Hiring-Manager")
        self.requester = make_user("dl-tl", role="Hiring-Manager")

    def _request_need(self, fac=None):
        from ..models import JobFamily, StaffingRequest
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "create", "facility": str((fac or self.fac).id),
            "title": "Leitung Treasury", "headcount": "1",
            "job_family": str(JobFamily.objects.get().id),
            "justification": "Nachfolge."})
        return StaffingRequest.objects.latest('createdAt')

    def _delegate(self, scope_type="FACILITY", scope_id=None, expired=False):
        from ..models import RoleDelegation
        now = timezone.now()
        return RoleDelegation.objects.create(
            delegator=self.vorstand, delegatee=self.deputy,
            scopeType=scope_type,
            scopeId=scope_id if scope_id is not None else str(self.fac.id),
            validFrom=now - datetime.timedelta(days=10),
            validUntil=(now - datetime.timedelta(days=1) if expired
                        else now + datetime.timedelta(days=5)))

    def _decide(self, user, req):
        step = req.steps.filter(status='PENDING').order_by('order').first()
        self.client.force_login(user)
        return self.client.post(reverse('ats:staffing_requests'), data={
            "form": "step_decide", "step_id": str(step.id),
            "decision": "approve"})

    def test_deputy_sees_and_decides_marked_as_delegation(self):
        from ..models import AuditLog
        self._world()
        req = self._request_need()
        self._delegate()
        # Vertretung sieht den Antrag in der Eingangs-Liste (ohne Recruiter-Rolle)
        self.client.force_login(self.deputy)
        page = self.client.get(reverse('ats:staffing_requests'))
        self.assertContains(page, "Leitung Treasury")
        self.assertContains(page, "step_decide")               # Formular da
        # ... und darf entscheiden – gekennzeichnet als i. V.
        self._decide(self.deputy, req)
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")
        step = req.steps.get()
        self.assertTrue(step.viaDelegation)
        self.assertEqual(step.decidedBy, self.deputy)
        page2 = self.client.get(reverse('ats:staffing_requests'))
        self.assertContains(page2, "i. V.")
        audit = AuditLog.objects.filter(
            action="REQUISITION_STEP_DECIDED").latest('createdAt')
        self.assertIn("dl-vorstand", audit.metadataJson)       # vertritt wen

    def test_expired_or_wrong_scope_delegation_is_powerless(self):
        self._world()
        req = self._request_need()
        self._delegate(expired=True)
        self._decide(self.deputy, req)
        req.refresh_from_db()
        self.assertEqual(req.status, "IN_APPROVAL")            # wirkungslos
        # Falsche Einrichtung im Scope: ebenso wirkungslos + unsichtbar
        from ..models import RoleDelegation
        RoleDelegation.objects.all().delete()
        self._delegate(scope_id=str(self.fac2.id))
        self.client.force_login(self.deputy)
        page = self.client.get(reverse('ats:staffing_requests'))
        self.assertNotContains(page, "Leitung Treasury")
        self._decide(self.deputy, req)
        req.refresh_from_db()
        self.assertEqual(req.status, "IN_APPROVAL")
        # Stellenscharfe (JOB-)Vertretung deckt Bedarf bewusst nicht
        RoleDelegation.objects.all().delete()
        self._delegate(scope_type="JOB", scope_id="egal")
        self._decide(self.deputy, req)
        req.refresh_from_db()
        self.assertEqual(req.status, "IN_APPROVAL")

    def test_chain_role_without_recruiter_sees_inbox(self):
        self._world()
        req = self._request_need()
        # Der Vorstand selbst (reine Ketten-Gruppe, kein Recruiter/HR-Admin)
        # sieht den faelligen Antrag – vorher war die Liste fuer ihn leer.
        self.client.force_login(self.vorstand)
        page = self.client.get(reverse('ats:staffing_requests'))
        self.assertContains(page, "Leitung Treasury")
        self._decide(self.vorstand, req)
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")
        self.assertFalse(req.steps.get().viaDelegation)        # direkt, kein i. V.

class ParallelApprovalTestCase(TestCase):
    """Parallele Genehmigungsstufen: 'A, B + C, D' – B und C gleichzeitig."""

    def _world(self):

        from ..models import Facility, JobFamily, Organization, SystemSetting, WorkflowState
        org = Organization.objects.create(name="O")
        self.fac = Facility.objects.create(name="Zentrale", organization=org)
        JobFamily.objects.create(name="PA-Fam")
        WorkflowState.objects.create(name="published")
        SystemSetting.objects.create(key="REQUISITION_REQUIRED", value="1")
        SystemSetting.objects.create(
            key="REQUISITION_CHAIN",
            value="Bereichsleitung, Controlling + Betriebsrat, Geschäftsführung")
        self.users = {}
        for role in ("Bereichsleitung", "Controlling", "Betriebsrat",
                     "Geschäftsführung"):
            u = make_user(f"pa-{role[:6].lower()}", role="Hiring-Manager")
            Group.objects.get_or_create(name=role)[0].user_set.add(u)
            self.users[role] = u
        self.requester = make_user("pa-tl", role="Hiring-Manager")

    def _request_need(self):
        from ..models import JobFamily, StaffingRequest
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "create", "facility": str(self.fac.id),
            "title": "Compliance-Analyst", "headcount": "1",
            "job_family": str(JobFamily.objects.get().id),
            "justification": "MaRisk-Programm."})
        return StaffingRequest.objects.get()

    def _decide(self, role, req, decision="approve"):
        step = req.steps.get(role=role)
        self.client.force_login(self.users[role])
        return self.client.post(reverse('ats:staffing_requests'), data={
            "form": "step_decide", "step_id": str(step.id),
            "decision": decision})

    def test_parallel_group_both_must_approve_any_order(self):
        self._world()
        req = self._request_need()
        # Struktur: 4 Steps, Controlling+Betriebsrat teilen sich order 2
        orders = {st.role: st.order for st in req.steps.all()}
        self.assertEqual(orders, {"Bereichsleitung": 1, "Controlling": 2,
                                  "Betriebsrat": 2, "Geschäftsführung": 3})
        # GF darf nicht vor der Gruppe; Gruppe nicht vor Stufe 1
        self._decide("Geschäftsführung", req)
        self.assertEqual(req.steps.filter(status='APPROVED').count(), 0)
        self._decide("Betriebsrat", req)
        self.assertEqual(req.steps.filter(status='APPROVED').count(), 0)
        self._decide("Bereichsleitung", req)
        # Beide Gruppen-Mitglieder sind jetzt gleichzeitig faellig und
        # entscheiden in BELIEBIGER Reihenfolge (Betriebsrat zuerst)
        self._decide("Betriebsrat", req)
        req.refresh_from_db()
        self.assertEqual(req.status, "IN_APPROVAL")            # noch nicht
        # GF weiterhin gesperrt, solange Controlling fehlt
        self._decide("Geschäftsführung", req)
        self.assertEqual(req.steps.filter(role="Geschäftsführung",
                                          status='APPROVED').count(), 0)
        self._decide("Controlling", req)
        self._decide("Geschäftsführung", req)
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")               # komplett

    def test_return_from_group_member_stops_whole_request(self):
        self._world()
        req = self._request_need()
        self._decide("Bereichsleitung", req)
        self._decide("Controlling", req)
        self._decide("Betriebsrat", req, decision="return")
        req.refresh_from_db()
        self.assertEqual(req.status, "RETURNED")               # eine Stimme reicht
        # Wiedervorlage: ALLE vier Stufen starten von vorn
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "resubmit", "request_id": str(req.id),
            "justification": "Budget nachgereicht."})
        req.refresh_from_db()
        self.assertEqual(req.status, "IN_APPROVAL")
        self.assertEqual(req.steps.filter(status='PENDING').count(), 4)

    def test_both_group_members_see_their_form_simultaneously(self):
        self._world()
        req = self._request_need()
        self._decide("Bereichsleitung", req)
        for role in ("Controlling", "Betriebsrat"):
            self.client.force_login(self.users[role])
            page = self.client.get(reverse('ats:staffing_requests'))
            self.assertContains(page, "Compliance-Analyst")
            self.assertContains(page, "step_decide")
            self.assertContains(page, "2 parallel fällig")

class RequisitionBottleneckTestCase(TestCase):
    """UC-CV-14: Engpass-Kennzahl je Freigabestufe."""

    def _world(self):

        from ..models import Facility, JobFamily, Organization
        org = Organization.objects.create(name="O")
        self.fac = Facility.objects.create(name="Z", organization=org)
        JobFamily.objects.create(name="BN-Fam")
        for role in ("Bereichsleitung", "Controlling", "Betriebsrat",
                     "Geschäftsführung"):
            Group.objects.get_or_create(name=role)
        self.gf_user = make_user("bn-gf", role="Hiring-Manager")

    def _req(self, days_ago):
        from ..models import JobFamily, StaffingRequest
        req = StaffingRequest.objects.create(
            title="T", facility=self.fac,
            jobFamily=JobFamily.objects.get(), headcount=1,
            justification="x", requestedBy=self.gf_user,
            status="IN_APPROVAL")
        StaffingRequest.objects.filter(id=req.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=days_ago))
        req.refresh_from_db()
        return req

    def _step(self, req, role, order, decided_days_ago=None):
        from ..models import RequisitionStep
        st = RequisitionStep.objects.create(request=req, role=role,
                                            order=order)
        if decided_days_ago is not None:
            st.status = 'APPROVED'
            st.decidedAt = timezone.now() - datetime.timedelta(
                days=decided_days_ago)
            st.save()
        return st

    def test_average_wait_and_open_bottleneck(self):
        from ..analytics import requisition_stage_stats
        from ..models import StaffingRequest
        self._world()
        # Antrag 1 (vor 10 Tagen): BL entschied nach 2 Tagen (Tag -8),
        # GF nach weiteren 6 Tagen (Tag -2) -> BL Ø 2.0, GF Ø 6.0
        r1 = self._req(days_ago=10)
        self._step(r1, "Bereichsleitung", 1, decided_days_ago=8)
        self._step(r1, "Geschäftsführung", 2, decided_days_ago=2)
        # Antrag 2 (vor 5 Tagen): BL sofort faellig, noch OFFEN (5 Tage alt)
        r2 = self._req(days_ago=5)
        self._step(r2, "Bereichsleitung", 1)
        rows = {r['role']: r
                for r in requisition_stage_stats(StaffingRequest.objects.all())}
        self.assertEqual(rows["Bereichsleitung"]["decided"], 1)
        self.assertAlmostEqual(rows["Bereichsleitung"]["avg_days"], 2.0,
                               delta=0.1)
        self.assertAlmostEqual(rows["Geschäftsführung"]["avg_days"], 6.0,
                               delta=0.1)
        self.assertEqual(rows["Bereichsleitung"]["open_now"], 1)
        self.assertAlmostEqual(rows["Bereichsleitung"]["oldest_open_days"],
                               5.0, delta=0.1)
        # Engpass = hoechster Durchschnitt steht oben
        ordered = requisition_stage_stats(StaffingRequest.objects.all())
        self.assertEqual(ordered[0]["role"], "Geschäftsführung")

    def test_parallel_group_due_from_previous_group_end(self):
        from ..analytics import requisition_stage_stats
        from ..models import StaffingRequest
        self._world()
        # Vor 9 Tagen: BL entschied Tag -6 (3 Tage Wartezeit). Danach
        # parallel: Controlling Tag -5 (1 Tag), Betriebsrat Tag -2 (4 Tage).
        # GF faellig erst ab Tag -2 (LETZTE Gruppen-Entscheidung) und
        # entschied Tag -1 -> 1 Tag, NICHT 4.
        r = self._req(days_ago=9)
        self._step(r, "Bereichsleitung", 1, decided_days_ago=6)
        self._step(r, "Controlling", 2, decided_days_ago=5)
        self._step(r, "Betriebsrat", 2, decided_days_ago=2)
        self._step(r, "Geschäftsführung", 3, decided_days_ago=1)
        rows = {x['role']: x
                for x in requisition_stage_stats(StaffingRequest.objects.all())}
        self.assertAlmostEqual(rows["Controlling"]["avg_days"], 1.0, delta=0.1)
        self.assertAlmostEqual(rows["Betriebsrat"]["avg_days"], 4.0, delta=0.1)
        self.assertAlmostEqual(rows["Geschäftsführung"]["avg_days"], 1.0,
                               delta=0.1)

    def test_card_renders_on_analytics_page(self):
        self._world()
        r = self._req(days_ago=3)
        self._step(r, "Bereichsleitung", 1, decided_days_ago=1)
        self.client.force_login(make_user("bn-admin", role="HR-Admin"))
        page = self.client.get(reverse('ats:analytics'))
        self.assertContains(page, "Welche Stufe bremst?")
        self.assertContains(page, "Bereichsleitung")
        self.assertContains(page, "Engpass")

class DelegationSelfServiceTestCase(TestCase):
    """Vertretungs-Pflege: Selbstbedienung fuer jede Rolle + Assistenz-Fall."""

    def _world(self):

        from ..models import Facility, JobFamily, Organization, SystemSetting
        org = Organization.objects.create(name="O")
        self.fac = Facility.objects.create(name="Z", organization=org)
        JobFamily.objects.create(name="DS-Fam")
        SystemSetting.objects.create(key="REQUISITION_REQUIRED", value="1")
        SystemSetting.objects.create(key="REQUISITION_CHAIN", value="Vorstand")
        self.vorstand = make_user("ds-vorstand", role="Hiring-Manager")
        Group.objects.get_or_create(name="Vorstand")[0].user_set.add(
            self.vorstand)
        self.deputy = make_user("ds-deputy", role="Hiring-Manager")
        self.stranger = make_user("ds-stranger", role="Hiring-Manager")
        self.admin = make_user("ds-admin", role="HR-Admin")

    def _create(self, as_user, delegatee, delegator=None, days=5):
        from django.utils import timezone as _tz
        self.client.force_login(as_user)
        data = {"delegatee": delegatee.username,
                "scopeType": "ALL",
                "validFrom": _tz.now().date().isoformat(),
                "validUntil": (_tz.now()
                               + datetime.timedelta(days=days)).date().isoformat()}
        if delegator is not None:
            data["delegator"] = delegator.username
        return self.client.post(reverse('ats:delegations'), data=data)

    def test_any_role_creates_own_delegation_delegator_enforced(self):
        from ..models import RoleDelegation
        self._world()
        # Vorstand (kein HR-Admin!) legt eigene Vertretung an – und selbst
        # ein manipulierter delegator-POST wird fuer Nicht-Admins ignoriert
        self._create(self.vorstand, self.deputy, delegator=self.stranger)
        d = RoleDelegation.objects.get()
        self.assertEqual(d.delegator, self.vorstand)           # erzwungen self
        self.assertEqual(d.delegatee, self.deputy)
        # Sichtbarkeit: Beteiligte sehen den Eintrag in der Tabelle,
        # Unbeteiligte sehen eine LEERE Tabelle (der Name im Empfaenger-
        # Dropdown zaehlt nicht als Sichtbarkeit)
        self.client.force_login(self.deputy)
        self.assertNotContains(self.client.get(reverse('ats:delegations')),
                               "Keine aktiven Delegationen")
        self.client.force_login(self.stranger)
        self.assertContains(self.client.get(reverse('ats:delegations')),
                            "Keine aktiven Delegationen")

    def test_only_own_delegation_can_be_ended(self):
        from ..models import RoleDelegation
        self._world()
        self._create(self.vorstand, self.deputy)
        d = RoleDelegation.objects.get()
        # Fremder kann sie nicht beenden
        self.client.force_login(self.stranger)
        self.client.post(reverse('ats:delegations'),
                         data={"end_id": str(d.id)})
        d.refresh_from_db()
        self.assertGreater(d.validUntil, timezone.now())       # laeuft weiter
        # Der Vertretene selbst schon
        self.client.force_login(self.vorstand)
        self.client.post(reverse('ats:delegations'),
                         data={"end_id": str(d.id)})
        d.refresh_from_db()
        self.assertLessEqual(d.validUntil, timezone.now())     # beendet

    def test_admin_creates_on_behalf_and_it_works_in_chain(self):
        from ..models import AuditLog, JobFamily, RoleDelegation, StaffingRequest
        self._world()
        # Assistenz-Fall: HR-Admin legt die Vertretung FUER den Vorstand an
        self._create(self.admin, self.deputy, delegator=self.vorstand)
        d = RoleDelegation.objects.get()
        self.assertEqual(d.delegator, self.vorstand)           # nicht der Admin!
        audit = AuditLog.objects.filter(action="DELEGATION_CREATE").latest(
            'createdAt')
        self.assertIn("ds-vorstand", audit.metadataJson)       # on_behalf
        # End-to-End: die Vertretung entscheidet die Vorstands-Stufe
        requester = make_user("ds-tl", role="Hiring-Manager")
        self.client.force_login(requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "create", "facility": str(self.fac.id),
            "title": "CFO-Assistenz", "headcount": "1",
            "job_family": str(JobFamily.objects.get().id),
            "justification": "Nachfolge."})
        req = StaffingRequest.objects.get()
        step = req.steps.get()
        self.client.force_login(self.deputy)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "step_decide", "step_id": str(step.id),
            "decision": "approve"})
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")
        self.assertTrue(req.steps.get().viaDelegation)         # i. V.

    def test_self_delegation_rejected(self):
        from ..models import RoleDelegation
        self._world()
        self._create(self.vorstand, self.vorstand)             # an sich selbst
        self.assertEqual(RoleDelegation.objects.count(), 0)

class RequisitionNotificationTestCase(TestCase):
    """Faelligkeits-Mails: wer JETZT entscheiden kann, erfaehrt es sofort."""

    def _world(self):

        from ..models import Facility, JobFamily, Organization, RoleDelegation, SystemSetting
        org = Organization.objects.create(name="O")
        self.fac = Facility.objects.create(name="Z", organization=org)
        self.fac2 = Facility.objects.create(name="Sued", organization=org)
        JobFamily.objects.create(name="NT-Fam")
        SystemSetting.objects.create(key="REQUISITION_REQUIRED", value="1")
        SystemSetting.objects.create(
            key="REQUISITION_CHAIN",
            value="Bereichsleitung, Controlling + Betriebsrat")
        def u(name, role, email=True):
            usr = make_user(name, role="Hiring-Manager")
            usr.email = f"{name}@x.de" if email else ""
            usr.save(update_fields=["email"])
            Group.objects.get_or_create(name=role)[0].user_set.add(usr)
            return usr
        self.bl = u("nt-bl", "Bereichsleitung")
        self.bl_no_mail = u("nt-bl2", "Bereichsleitung", email=False)
        self.co = u("nt-co", "Controlling")
        self.br = u("nt-br", "Betriebsrat")
        # Vertretung fuer BL: eine passende, eine mit fremder Einrichtung
        self.deputy_ok = make_user("nt-dep-ok", role="Hiring-Manager")
        self.deputy_ok.email = "dep-ok@x.de"
        self.deputy_ok.save(update_fields=["email"])
        self.deputy_wrong = make_user("nt-dep-w", role="Hiring-Manager")
        self.deputy_wrong.email = "dep-w@x.de"
        self.deputy_wrong.save(update_fields=["email"])
        now = timezone.now()
        RoleDelegation.objects.create(
            delegator=self.bl, delegatee=self.deputy_ok,
            scopeType="FACILITY", scopeId=str(self.fac.id),
            validFrom=now - datetime.timedelta(days=1),
            validUntil=now + datetime.timedelta(days=5))
        RoleDelegation.objects.create(
            delegator=self.bl, delegatee=self.deputy_wrong,
            scopeType="FACILITY", scopeId=str(self.fac2.id),
            validFrom=now - datetime.timedelta(days=1),
            validUntil=now + datetime.timedelta(days=5))
        self.requester = make_user("nt-tl", role="Hiring-Manager")

    def _request_need(self):
        from django.core import mail

        from ..models import JobFamily, StaffingRequest
        mail.outbox = []
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "create", "facility": str(self.fac.id),
            "title": "Data Engineer", "headcount": "1",
            "job_family": str(JobFamily.objects.get().id),
            "justification": "x"})
        return StaffingRequest.objects.get()

    def _decide(self, user, req, role, decision="approve"):
        step = req.steps.get(role=role)
        self.client.force_login(user)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "step_decide", "step_id": str(step.id),
            "decision": decision})

    def test_creation_notifies_first_stage_and_covering_deputy(self):
        from django.core import mail
        self._world()
        self._request_need()
        rcpts = sorted(m.to[0] for m in mail.outbox)
        # BL-Mitglied + passende Vertretung; ohne E-Mail und mit fremdem
        # Einrichtungs-Scope faellt raus
        self.assertEqual(rcpts, ["dep-ok@x.de", "nt-bl@x.de"])
        self.assertIn("wartet auf Ihre Entscheidung", mail.outbox[0].subject)
        deputy_mail = next(m for m in mail.outbox
                           if m.to == ["dep-ok@x.de"])
        self.assertIn("als Vertretung von nt-bl", deputy_mail.body)

    def test_group_completion_triggers_next_stage_once(self):
        from django.core import mail
        self._world()
        req = self._request_need()
        mail.outbox = []
        self._decide(self.bl, req, "Bereichsleitung")
        # Parallele Gruppe faellig: Controlling UND Betriebsrat, EIN Versand
        rcpts = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(rcpts, ["nt-br@x.de", "nt-co@x.de"])
        mail.outbox = []
        self._decide(self.co, req, "Controlling")
        # Gruppe noch offen -> KEINE neue Mail
        self.assertEqual(len(mail.outbox), 0)
        self._decide(self.br, req, "Betriebsrat")
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")
        # Finale Stufe: nur Antragsteller-Bestandsmail, keine Faelligkeits-Mail
        self.assertEqual([m.to[0] for m in mail.outbox], [])  # requester ohne mail

    def test_resubmit_notifies_stage_one_again(self):
        from django.core import mail
        self._world()
        req = self._request_need()
        self._decide(self.bl, req, "Bereichsleitung", decision="return")
        mail.outbox = []
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "resubmit", "request_id": str(req.id),
            "justification": "nachgebessert"})
        rcpts = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(rcpts, ["dep-ok@x.de", "nt-bl@x.de"])

class RequisitionReminderTestCase(TestCase):
    """Liegenbleiben-Erinnerung fuer Stellenfreigabe-Ketten (einmalig)."""

    def _world(self):

        from ..models import Facility, JobFamily, Organization, RoleDelegation, SystemSetting
        org = Organization.objects.create(name="O")
        self.fac = Facility.objects.create(name="Z", organization=org)
        self.fac2 = Facility.objects.create(name="S", organization=org)
        JobFamily.objects.create(name="RM-Fam")
        SystemSetting.objects.create(key="REQUISITION_REQUIRED", value="1")
        SystemSetting.objects.create(
            key="REQUISITION_CHAIN", value="Bereichsleitung, Vorstand")
        def u(name, role):
            usr = make_user(name, role="Hiring-Manager")
            usr.email = f"{name}@x.de"
            usr.save(update_fields=["email"])
            Group.objects.get_or_create(name=role)[0].user_set.add(usr)
            return usr
        self.bl = u("rm-bl", "Bereichsleitung")
        self.vs = u("rm-vs", "Vorstand")
        self.deputy = make_user("rm-dep", role="Hiring-Manager")
        self.deputy.email = "rm-dep@x.de"
        self.deputy.save(update_fields=["email"])
        now = timezone.now()
        RoleDelegation.objects.create(
            delegator=self.vs, delegatee=self.deputy,
            scopeType="ALL", scopeId=None,
            validFrom=now - datetime.timedelta(days=1),
            validUntil=now + datetime.timedelta(days=9))
        self.requester = make_user("rm-tl", role="Hiring-Manager")

    def _make_request(self, age_days):
        from ..models import JobFamily, StaffingRequest
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "create", "facility": str(self.fac.id),
            "title": "Risk Manager", "headcount": "1",
            "job_family": str(JobFamily.objects.get().id),
            "justification": "MaRisk."})
        req = StaffingRequest.objects.get()
        StaffingRequest.objects.filter(id=req.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=age_days))
        return req

    def _run(self, days=3):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command
        mail.outbox = []
        call_command("send_decision_reminders", days=days, stdout=StringIO())
        return mail.outbox

    def test_fresh_request_not_reminded(self):
        self._world()
        self._make_request(age_days=1)
        self.assertEqual(len(self._run(days=3)), 0)   # unter Schwelle

    def test_stale_stage_reminds_holder_once(self):
        self._world()
        self._make_request(age_days=5)
        # Erste faellige Stufe = Bereichsleitung; Vorstand noch nicht dran
        box = self._run(days=3)
        rcpts = sorted(m.to[0] for m in box)
        self.assertEqual(rcpts, ["rm-bl@x.de"])       # nur die faellige Rolle
        self.assertIn("seit 5 Tagen", box[0].subject)
        # Zweiter Lauf: keine erneute Mail (Einmal-Marker)
        self.assertEqual(len(self._run(days=3)), 0)

    def test_due_since_counts_from_previous_stage_end(self):
        self._world()
        req = self._make_request(age_days=10)
        # Bereichsleitung entschied vor 1 Tag -> Vorstand erst seit 1 Tag
        # faellig, also NICHT ueber der 3-Tage-Schwelle trotz 10 Tage alt.
        bl_step = req.steps.get(role="Bereichsleitung")
        bl_step.status = "APPROVED"
        bl_step.decidedBy = self.bl
        bl_step.decidedAt = timezone.now() - datetime.timedelta(days=1)
        bl_step.save()
        self.assertEqual(len(self._run(days=3)), 0)   # Vorstand erst 1 Tag
        # Ruecke die BL-Entscheidung auf vor 4 Tage -> Vorstand faellig
        bl_step.decidedAt = timezone.now() - datetime.timedelta(days=4)
        bl_step.save()
        box = self._run(days=3)
        rcpts = sorted(m.to[0] for m in box)
        # Vorstand + dessen aktive Vertretung (ALL-Scope deckt Kette)
        self.assertEqual(rcpts, ["rm-dep@x.de", "rm-vs@x.de"])
        dep = next(m for m in box if m.to == ["rm-dep@x.de"])
        self.assertIn("In Vertretung für", dep.body)

class ParallelQuorumTestCase(TestCase):
    """Quorum innerhalb einer Parallelgruppe: '2 von 3 genuegen'."""

    def _world(self, chain):

        from ..models import Facility, JobFamily, Organization, SystemSetting
        org = Organization.objects.create(name="O")
        self.fac = Facility.objects.create(name="Z", organization=org)
        JobFamily.objects.create(name="PQ-Fam")
        SystemSetting.objects.create(key="REQUISITION_REQUIRED", value="1")
        SystemSetting.objects.create(key="REQUISITION_CHAIN", value=chain)
        self.users = {}
        import re
        for role in re.findall(r"[A-Za-zÄÖÜäöü]+", chain):
            u = make_user(f"pq-{role[:5].lower()}", role="Hiring-Manager")
            Group.objects.get_or_create(name=role)[0].user_set.add(u)
            self.users[role] = u
        self.requester = make_user("pq-tl", role="Hiring-Manager")

    def _create(self):
        from ..models import JobFamily, StaffingRequest
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "create", "facility": str(self.fac.id),
            "title": "Prüfer", "headcount": "1",
            "job_family": str(JobFamily.objects.get().id),
            "justification": "x"})
        return StaffingRequest.objects.get()

    def _decide(self, role, req, decision="approve"):
        step = req.steps.get(role=role)
        self.client.force_login(self.users[role])
        return self.client.post(reverse('ats:staffing_requests'), data={
            "form": "step_decide", "step_id": str(step.id),
            "decision": decision})

    def test_quorum_two_of_three_completes_group(self):
        self._world("Leitung, A + B + C (2), Vorstand")
        req = self._create()
        # Quorum je Gruppen-Step gespeichert
        self.assertEqual(req.steps.get(role="A").groupQuorum, 2)
        self.assertEqual(req.steps.get(role="Vorstand").groupQuorum, 1)
        self._decide("Leitung", req)
        # Zwei von drei genuegen -> dritte Stufe wird SKIPPED, Vorstand faellig
        self._decide("A", req)
        req.refresh_from_db()
        self.assertEqual(req.status, "IN_APPROVAL")
        self._decide("B", req)
        # C wurde nie gebraucht
        req.refresh_from_db()
        self.assertEqual(req.steps.get(role="C").status, "SKIPPED")
        # Vorstand ist jetzt faellig und schliesst ab
        self._decide("Vorstand", req)
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")

    def test_without_quorum_all_still_required(self):
        self._world("A + B + C, Vorstand")                    # kein (N)
        req = self._create()
        self.assertEqual(req.steps.get(role="A").groupQuorum, 3)
        self._decide("A", req)
        self._decide("B", req)
        # Vorstand noch NICHT faellig, C fehlt
        self.assertEqual(req.steps.filter(role="Vorstand",
                                          status="APPROVED").count(), 0)
        self._decide("C", req)
        self._decide("Vorstand", req)
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")
        self.assertEqual(req.steps.filter(status="SKIPPED").count(), 0)

    def test_resubmit_revives_skipped_steps(self):
        self._world("A + B + C (2)")
        req = self._create()
        self._decide("A", req)
        self._decide("B", req)                                # C -> SKIPPED
        req.refresh_from_db()
        self.assertEqual(req.status, "ACCEPTED")              # 2/2 reicht, 1 Gruppe
        # kuenstlich zurueckgeben, um Resubmit zu testen
        from ..models import StaffingRequest
        StaffingRequest.objects.filter(id=req.id).update(status="RETURNED")
        self.client.force_login(self.requester)
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "resubmit", "request_id": str(req.id),
            "justification": "nochmal"})
        req.refresh_from_db()
        # ALLE drei wieder offen – auch das zuvor uebersprungene C
        self.assertEqual(req.steps.filter(status="PENDING").count(), 3)

class PanelVoteByDeputyTestCase(TestCase):
    """UC-VT-06: Vertretung im Sichtungs-Gremium – war KOMPLETT ungetestet.

    Warum das wichtig ist: An dieser Logik hängen Einstellungsentscheidungen.
    Zählt die Stimme einer Urlaubsvertretung nicht mit, blockiert Abwesenheit
    das Verfahren. Zählt sie doppelt (Mitglied UND Vertretung), entstünde eine
    Mehrheit, die es nie gab. Und für Betriebsrat/Audit muss nachvollziehbar
    bleiben, FÜR WESSEN Sitz jemand gestimmt hat.
    """

    def setUp(self):

        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        self.m1 = make_user("pv-m1", role="Hiring-Manager")
        self.m2 = make_user("pv-m2", role="Hiring-Manager")
        self.m3 = make_user("pv-m3", role="Hiring-Manager")
        self.deputy = make_user("pv-vertretung", role="Hiring-Manager")
        self.stranger = make_user("pv-fremd", role="Hiring-Manager")

        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        self.fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="PV-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Pflegefachkraft", organization=org, facility=self.fac,
            location=loc, jobFamily=fam, workflowState=ws,
            panelUserIdsJson=[str(self.m1.id), str(self.m2.id),
                              str(self.m3.id)])
        self.app = Application.objects.create(
            applicant=Applicant.objects.create(firstName="P", lastName="V",
                                               email="pv@x.de"),
            jobPosting=self.job, status="IN_REVIEW")

    def _delegate(self, frm, to, days=7, scope="ALL", scope_id=None):
        from ..models import RoleDelegation
        now = timezone.now()
        return RoleDelegation.objects.create(
            delegator=frm, delegatee=to, scopeType=scope, scopeId=scope_id,
            validFrom=now - datetime.timedelta(days=1),
            validUntil=now + datetime.timedelta(days=days))

    def _vote(self, user, vote="FOR"):
        self.client.force_login(user)
        return self.client.post(reverse('ats:application_vote',
                                        args=[self.app.id]), {"vote": vote})

    def _state(self):
        from ..panel import panel_state
        self.app.refresh_from_db()
        return panel_state(self.app)

    # --- Grundfall ---
    def test_member_can_vote(self):
        self._vote(self.m1)
        self.assertEqual(self._state()["votes_for"], 1)

    def test_stranger_without_delegation_is_rejected(self):
        r = self._vote(self.stranger)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self._state()["votes_for"], 0)

    # --- Vertretung ---
    def test_deputy_vote_counts_for_the_absent_members_seat(self):
        """Kern: Die Vertretung stimmt für den Sitz des abwesenden Mitglieds –
        sonst würde Urlaub das Verfahren blockieren."""
        self._delegate(self.m1, self.deputy)
        r = self._vote(self.deputy)
        self.assertNotEqual(r.status_code, 403)
        self.assertEqual(self._state()["votes_for"], 1)

    def test_deputy_vote_is_attributable_in_audit(self):
        """Für Betriebsrat/Audit muss erkennbar sein, FÜR WEN gestimmt wurde."""
        from ..models import AuditLog
        self._delegate(self.m1, self.deputy)
        self._vote(self.deputy)
        entry = AuditLog.objects.filter(action="PANEL_VOTE_CAST").first()
        self.assertIsNotNone(entry)
        self.assertIn("for_seat", entry.metadataJson)
        self.assertIn(self.m1.username, entry.metadataJson)

    def test_member_vote_has_no_for_seat_marker(self):
        from ..models import AuditLog
        self._vote(self.m1)
        entry = AuditLog.objects.filter(action="PANEL_VOTE_CAST").first()
        self.assertNotIn("for_seat", entry.metadataJson)

    def test_members_own_vote_wins_over_deputy(self):
        """Ein Sitz = EINE Stimme. Stimmen Mitglied und Vertretung, darf der
        Sitz nicht doppelt zählen – die eigene Stimme des Mitglieds gewinnt."""
        self._delegate(self.m1, self.deputy)
        self._vote(self.deputy, "AGAINST")     # Vertretung: dagegen
        self._vote(self.m1, "FOR")             # Mitglied selbst: dafür
        st = self._state()
        self.assertEqual(st["votes_for"], 1)
        self.assertEqual(st["votes_against"], 0)   # NICHT doppelt gezählt

    def test_expired_delegation_cannot_vote(self):
        from ..models import RoleDelegation
        now = timezone.now()
        RoleDelegation.objects.create(
            delegator=self.m1, delegatee=self.deputy, scopeType="ALL",
            validFrom=now - datetime.timedelta(days=30),
            validUntil=now - datetime.timedelta(days=1))   # abgelaufen
        r = self._vote(self.deputy)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self._state()["votes_for"], 0)

    def test_delegation_outside_scope_cannot_vote(self):
        """Eine Vertretung nur für Einrichtung X darf nicht bei Stellen aus
        Einrichtung Y mitentscheiden."""
        from ..models import Facility, Organization
        other = Facility.objects.create(
            name="Andere", organization=Organization.objects.first())
        self._delegate(self.m1, self.deputy, scope="FACILITY",
                       scope_id=str(other.id))
        r = self._vote(self.deputy)
        self.assertEqual(r.status_code, 403)

    def test_majority_reached_via_deputy_allows_decision(self):
        """Ende-zu-Ende: 2 Mitglieder + 1 Vertretung ergeben die Mehrheit –
        die Entscheidung wird dadurch möglich."""
        self._delegate(self.m3, self.deputy)
        self._vote(self.m1)
        self.assertFalse(self._state()["allowed"])   # 1 von 3: zu wenig
        self._vote(self.m2)
        st = self._state()
        self.assertTrue(st["allowed"])               # 2 von 3: Mehrheit
        # Vertretung liefert die dritte Stimme
        self._vote(self.deputy)
        self.assertEqual(self._state()["votes_for"], 3)


class VoteOnceStateTestCase(TestCase):
    """Einmal-Aktion Gremium: die abgegebene Stimme ist am Button sichtbar;
    nur das Aendern auf die Gegenstimme bleibt anklickbar (auditiert)."""

    def _panel_world(self):
        from .factories import make_application, make_job, make_world
        from .utils import make_user
        world = make_world()
        member = make_user("vo-member", role="Hiring-Manager")
        job = make_job(world, title="VO-Stelle",
                       panelUserIdsJson=[str(member.id)])
        app = make_application(job)
        return member, app

    def test_vote_state_rendered_after_voting(self):
        member, app = self._panel_world()
        self.client.force_login(member)
        page = self.client.get(reverse('ats:approvals'))
        self.assertContains(page, 'value="FOR"')               # beide Buttons aktiv
        self.client.post(reverse('ats:application_vote', args=[app.id]),
                         data={"vote": "FOR"})
        page = self.client.get(reverse('ats:approvals'))
        self.assertContains(page, "Dafür gestimmt")            # Erledigt-Zustand
        self.assertContains(page, "Ändern: Dagegen")           # Gegenstimme bleibt
        self.assertNotContains(page, 'data-done-label="Dafür gestimmt"')


class ApprovalGatePayBandTestCase(TestCase):
    """V1: Das Entgelt-Gate gilt an ALLEN drei Veroeffentlichungs-Wegen.

    Anlegen und Schnell-Toggle blockten eine Stelle ohne Entgeltband schon
    immer; die automatische Veroeffentlichung nach der letzten Freigabe
    pruefte nur den Personalbedarf - eine Stelle ohne Verguetungsangabe ging
    darueber online (EU-RL 2023/970 Art. 5).
    """

    def _job_without_band(self):
        import uuid as _u

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="Klinik Freigabe", organization=org,
                                      requiresApproval=True)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        WorkflowState.objects.get_or_create(name="published")
        draft, _ = WorkflowState.objects.get_or_create(name="draft")
        return JobPosting.objects.create(
            title="Ohne Band", organization=org, facility=fac, location=loc,
            jobFamily=fam, workflowState=draft, payBand=None)

    def test_final_approval_does_not_publish_without_pay_band(self):
        from ..approvals import ensure_approval_gate
        from ..models import AuditLog
        job = self._job_without_band()
        ensure_approval_gate(job)
        step = job.approvalTicket.steps.order_by("stepOrder").first()
        self.client.force_login(make_user("paygate-hr", role="HR-Admin"))
        self.client.post(reverse('ats:approvals'),
                         data={"step_id": str(step.id), "action": "approve"})
        job.refresh_from_db()
        self.assertEqual(job.workflowState.name, "draft")   # bleibt Entwurf
        self.assertTrue(AuditLog.objects.filter(action="PAY_GATE_BLOCKED").exists())
        self.assertNotContains(self.client.get(reverse('ats:job_list')), "Ohne Band")

    def test_final_approval_publishes_with_pay_band(self):
        from ..approvals import ensure_approval_gate
        from ..models import PayBand
        job = self._job_without_band()
        job.payBand = PayBand.objects.create(name="B", minAmount=3000,
                                             maxAmount=3600)
        job.save(update_fields=["payBand"])
        ensure_approval_gate(job)
        step = job.approvalTicket.steps.order_by("stepOrder").first()
        self.client.force_login(make_user("paygate-hr2", role="HR-Admin"))
        self.client.post(reverse('ats:approvals'),
                         data={"step_id": str(step.id), "action": "approve"})
        job.refresh_from_db()
        self.assertEqual(job.workflowState.name, "published")


class PanelVotesSurviveManyOpenApplicationsTestCase(TestCase):
    """Gekappt wird das Ergebnis, nicht die Eingabe.

    Vorher holte die Freigaben-Seite die 200 ÄLTESTEN offenen Bewerbungen der
    ganzen Organisation und prüfte ERST DANACH, wer in welchem Gremium sitzt.
    In einem Haus mit mehr als 200 offenen Bewerbungen konnten die 200
    ältesten sämtlich aus fremden Einrichtungen stammen — dann blieb die
    Liste leer, obwohl die eigene Stimme ausstand. Eine ausbleibende
    Gremiums-Stimme blockiert die Einladung; niemand hätte den Grund gesehen.
    """

    def test_my_pending_vote_shows_up_behind_200_foreign_applications(self):
        import uuid as _u

        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        mitglied = make_user("gremium-mitglied", role="Hiring-Manager")

        # 210 aeltere Bewerbungen auf einer Stelle OHNE dieses Gremium.
        fremd = JobPosting.objects.create(
            title="Fremde Stelle", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=wf,
            panelUserIdsJson=[])
        bewerbende = Applicant.objects.bulk_create([
            Applicant(firstName=f"A{i}", lastName="X",
                      email=f"a{i}@example.invalid") for i in range(210)])
        alt = timezone.now() - datetime.timedelta(days=30)
        Application.objects.bulk_create([
            Application(applicant=b, jobPosting=fremd, status="IN_REVIEW",
                        createdAt=alt) for b in bewerbende])

        # Eine NEUERE Bewerbung auf einer Stelle MIT diesem Gremium.
        meine_stelle = JobPosting.objects.create(
            title="Pflegedienstleitung", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=wf,
            panelUserIdsJson=[str(mitglied.id)])
        wer = Applicant.objects.create(firstName="Vera", lastName="M",
                                       email="vera-gremium@example.invalid")
        meine = Application.objects.create(applicant=wer,
                                           jobPosting=meine_stelle,
                                           status="IN_REVIEW")

        self.client.force_login(mitglied)
        resp = self.client.get(reverse('ats:approvals'))
        gezeigt = [r['app'].id for r in resp.context['panel_rows']]
        self.assertIn(meine.id, gezeigt,
                      "Die eigene ausstehende Stimme war hinter 210 fremden "
                      "Bewerbungen verschwunden – genau die Kappung vor dem "
                      "Filtern.")
