"""Paket R: Mitbestimmung — § 99-Widerspruch + BetrVG-Gate am Scoring.

Deckt ab: Betriebsrats-Stufe kann nicht formlos ablehnen (Grund + Begruendung
Pflicht), strukturierter Widerspruch landet in Kommentar + Audit, Nicht-BR-
Stufen bleiben unveraendert, BR-Stufen laufen auf der gesetzlichen Wochenfrist,
und das gelernte Scoring aktiviert nur mit Rechtsgutachten UND
Betriebsrats-Zustimmung (§ 87 Abs. 1 Nr. 6 BetrVG).
"""
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from ..models import ApprovalStep, ApprovalTicket, AuditLog, SystemSetting
from ..scoring_eval import LEARNED_SCORING_ENABLED_KEY
from .factories import make_job, make_world
from .utils import make_user


def _ticket_with_step(job, role):
    ticket = ApprovalTicket.objects.create(jobPosting=job, status='PENDING')
    step = ApprovalStep.objects.create(
        approvalTicket=ticket, stepOrder=1, assignedRoleId=role,
        status='PENDING')
    return ticket, step


class W99WiderspruchTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Stationsleitung")
        self.br = make_user("br-jf", role="Recruiter")   # Basis-Zugriff
        group, _ = Group.objects.get_or_create(name="Betriebsrat")
        self.br.groups.add(group)
        self.client.force_login(self.br)
        self.url = reverse('ats:approvals')

    def test_br_reject_without_grounds_blocked(self):
        _, step = _ticket_with_step(self.job, "Betriebsrat")
        self.client.post(self.url, data={
            'step_id': str(step.id), 'action': 'reject',
            'comment': 'Passt nicht.'})   # Begruendung, aber kein Grund
        step.refresh_from_db()
        self.assertEqual(step.status, 'PENDING')   # nicht durchgegangen

    def test_br_reject_without_comment_blocked(self):
        _, step = _ticket_with_step(self.job, "Betriebsrat")
        self.client.post(self.url, data={
            'step_id': str(step.id), 'action': 'reject',
            'w99_grounds': ['1']})   # Grund, aber keine Begruendung
        step.refresh_from_db()
        self.assertEqual(step.status, 'PENDING')

    def test_br_structured_widerspruch_recorded(self):
        ticket, step = _ticket_with_step(self.job, "Betriebsrat")
        self.client.post(self.url, data={
            'step_id': str(step.id), 'action': 'reject',
            'w99_grounds': ['1', '5'],
            'comment': 'Interne Ausschreibung fehlte.'})
        step.refresh_from_db()
        ticket.refresh_from_db()
        self.assertEqual(step.status, 'REJECTED')
        self.assertEqual(ticket.status, 'REJECTED')
        self.assertIn('§ 99 Abs. 2 BetrVG', step.comments)
        self.assertIn('Nr. 5', step.comments)
        audit = AuditLog.objects.filter(action='APPROVAL_REJECTED').first()
        self.assertIn('w99_grounds', audit.metadataJson)

    def test_non_br_reject_needs_no_grounds(self):
        _, step = _ticket_with_step(self.job, "Geschäftsführung")
        gf, _ = Group.objects.get_or_create(name="Geschäftsführung")
        self.br.groups.add(gf)
        self.client.post(self.url, data={
            'step_id': str(step.id), 'action': 'reject', 'comment': ''})
        step.refresh_from_db()
        self.assertEqual(step.status, 'REJECTED')

    def test_br_step_uses_week_deadline(self):
        """BR-Stufen laufen auf der gesetzlichen Wochenfrist (§ 99 Abs. 3),
        auch wenn das Haus-SLA laenger ist."""
        from datetime import timedelta

        from django.utils import timezone
        SystemSetting.objects.update_or_create(
            key='APPROVAL_SLA_DAYS', defaults={'value': '14'})
        ticket, _ = _ticket_with_step(self.job, "Betriebsrat")
        ApprovalTicket.objects.filter(id=ticket.id).update(
            createdAt=timezone.now() - timedelta(days=8))
        r = self.client.get(self.url)
        self.assertContains(r, 'überfällig')          # 8 > 7 (Wochenfrist)
        self.assertContains(r, '§ 99')

    def test_widerspruch_form_only_for_br_steps(self):
        _, _step = _ticket_with_step(self.job, "Betriebsrat")
        r = self.client.get(self.url)
        self.assertContains(r, 'Zustimmung verweigern (§ 99 Abs. 2 BetrVG)')
        self.assertContains(r, 'Auswahlrichtlinie')   # Grund Nr. 2 im Formular


class ScoringBetrVGGateTestCase(TestCase):
    def setUp(self):
        self.admin = make_user("br-admin", role="HR-Admin")
        self.client.force_login(self.admin)
        self.url = reverse('ats:save_learned_scoring')

    def _enabled(self):
        row = SystemSetting.objects.filter(
            key=LEARNED_SCORING_ENABLED_KEY).first()
        return bool(row and row.value == '1')

    def test_legal_alone_not_enough(self):
        self.client.post(self.url, data={
            'enable': '1', 'legal_confirmed': '1'})
        self.assertFalse(self._enabled())

    def test_br_alone_not_enough(self):
        self.client.post(self.url, data={
            'enable': '1', 'br_confirmed': '1'})
        self.assertFalse(self._enabled())

    def test_both_confirmations_enable(self):
        self.client.post(self.url, data={
            'enable': '1', 'legal_confirmed': '1', 'br_confirmed': '1'})
        self.assertTrue(self._enabled())
        audit = AuditLog.objects.filter(
            action='LEARNED_SCORING_TOGGLED').first()
        self.assertIn('br_confirmed', audit.metadataJson)

    def test_disable_needs_no_confirmation(self):
        SystemSetting.objects.update_or_create(
            key=LEARNED_SCORING_ENABLED_KEY, defaults={'value': '1'})
        self.client.post(self.url, data={})
        self.assertFalse(self._enabled())
