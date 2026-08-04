"""Die Freigabe-Seite zeigte ausschliesslich „wartet auf mich".

Zwei Fragen, die im Alltag gestellt werden, konnte sie nicht beantworten:
„Habe ich das schon freigegeben?" und „Was hängt gerade, und bei wem?"
Die Daten lagen die ganze Zeit in der Datenbank — seit U6 samt Urheber.
"""
import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import ApprovalStep, ApprovalTicket
from .factories import make_job, make_world
from .utils import make_user


class ApprovalHistoryTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Pflegedienstleitung")
        self.admin = make_user("kette-admin", role="HR-Admin")
        self.other = make_user("kette-andere", role="HR-Admin")
        self.ticket = ApprovalTicket.objects.create(jobPosting=self.job)

    def _step(self, order=1, status="PENDING", by=None, comment="", role="HR-Admin"):
        return ApprovalStep.objects.create(
            approvalTicket=self.ticket, stepOrder=order, status=status,
            assignedRoleId=role, comments=comment, actionTakenBy=by,
            actionTakenAt=timezone.now() if by else None)

    # --- „Von mir entschieden" ---------------------------------------------

    def test_own_decision_is_visible_after_the_fact(self):
        self._step(order=1, status="APPROVED", by=self.admin,
                   comment="Bedarf ist belegt.")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertContains(resp, "Von mir entschieden")
        self.assertContains(resp, "Bedarf ist belegt.")
        self.assertContains(resp, "freigegeben")

    def test_other_peoples_decisions_are_not_mine(self):
        self._step(order=1, status="APPROVED", by=self.other,
                   comment="Fremde Entscheidung")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertNotContains(resp, "Fremde Entscheidung")

    def test_pending_step_is_not_history(self):
        self._step(order=1, status="PENDING")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertNotContains(resp, "Von mir entschieden")

    def test_refusal_is_named_as_such(self):
        """§ 99: „abgelehnt" und „Zustimmung verweigert" sind nicht dasselbe."""
        self._step(order=1, status="REJECTED", by=self.admin,
                   comment="Widerspruch § 99 Abs. 2")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertContains(resp, "Zustimmung verweigert")

    # --- „Laufende Freigaben" ----------------------------------------------

    def test_running_chain_shows_where_it_hangs(self):
        self._step(order=1, status="APPROVED", by=self.other)
        self._step(order=2, status="PENDING", role="Betriebsrat")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertContains(resp, "Laufende Freigaben")
        self.assertContains(resp, "Pflegedienstleitung")
        self.assertContains(resp, "Stufe 2 · 1 von 2 freigegeben")
        self.assertContains(resp, "Betriebsrat")

    def test_lowest_open_step_is_the_current_one(self):
        """Hoehere Stufen warten auf die niedrigere - sie sind nicht faellig."""
        self._step(order=1, status="PENDING", role="Leitung")
        self._step(order=2, status="PENDING", role="Geschäftsführung")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertContains(resp, "Stufe 1 · 0 von 2 freigegeben")

    def test_parallel_step_names_every_role(self):
        self._step(order=1, status="PENDING", role="Leitung")
        self._step(order=1, status="PENDING", role="Betriebsrat")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertContains(resp, "Leitung, Betriebsrat")

    def test_finished_ticket_disappears_from_the_overview(self):
        self.ticket.status = 'APPROVED'
        self.ticket.save(update_fields=['status'])
        self._step(order=1, status="APPROVED", by=self.other)
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertNotContains(resp, "Laufende Freigaben")

    def test_overdue_chain_is_marked(self):
        self.ticket.createdAt = timezone.now() - datetime.timedelta(days=30)
        self.ticket.save(update_fields=['createdAt'])
        self._step(order=1, status="PENDING", role="Leitung")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertContains(resp, "badge-danger")

    def test_chain_overview_respects_the_access_scope(self):
        """BOLA: Wer die Stelle nicht sehen darf, sieht auch ihre Kette nicht."""
        self._step(order=1, status="PENDING", role="Leitung")
        from ..models import UserScope
        limited = make_user("kette-eng", role="Recruiter")
        scope, _ = UserScope.objects.get_or_create(user=limited)
        scope.full_access = False          # sonst greift die Einschraenkung nie
        scope.save(update_fields=['full_access'])
        scope.locations.clear()
        scope.facilities.set([self.world.org.facilities.create(
            name="Fremde Klinik")])
        self.client.force_login(limited)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertNotContains(resp, "Pflegedienstleitung")

    def test_overview_names_roles_not_people(self):
        """Mitbestimmung braucht Prozess-Transparenz, keine Personendaten."""
        self._step(order=1, status="PENDING", role="Betriebsrat")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:approvals'))
        self.assertNotContains(resp, "kette-andere")
