"""L3-3: Governance + gated Anzeige des gelernten Scorings.

Deckt ab: learned_grade liefert None wenn AUS; None wenn AN aber Kontext nicht
vertrauenswuerdig; Note wenn AN + vertrauenswuerdig. Governance-Toggle nur mit
bestaetigtem Rechtsgutachten und nur fuer Admin. Steckbrief zeigt „learned"
nur im freigeschalteten, belastbaren Fall.
"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..audit import write_audit
from ..models import Application, SystemSetting
from ..scoring_eval import LEARNED_SCORING_ENABLED_KEY, learned_grade
from .factories import make_application, make_job, make_world
from .utils import make_user

_KO = [{"id": "q1", "type": "YES_NO", "question": "Examen?",
        "isMandatory": True, "expectedAnswer": "YES"}]


def _enable():
    SystemSetting.objects.update_or_create(
        key=LEARNED_SCORING_ENABLED_KEY, defaults={'value': '1'})


def _advance(app, s):
    old = app.status
    app.status = s
    app.save(update_fields=['status'])
    write_audit('STATUS_CHANGE', application_id=app.id, oldStatus=old, newStatus=s)


def _trustworthy_seed(job, n=10):
    """ALLE erfuellen K.O.; die Anforderungs-Deckung trennt eingeladen von
    abgelehnt -> Backtest schlaegt die Grundlinie (vertrauenswuerdig)."""
    now = timezone.now()
    d = 2 * n
    for _ in range(n):
        for covered, invited in ((True, True), (False, False)):
            app = make_application(
                job, status='NEW', screeningAnswersJson={"Examen?": "YES"},
                coverLetterTxt="Django-Erfahrung." if covered else "")
            if invited:
                _advance(app, 'IN_REVIEW')
                _advance(app, 'INVITED')
            else:
                _advance(app, 'REJECTED')
            Application.objects.filter(id=app.id).update(
                createdAt=now - timedelta(days=d))
            d -= 1


class LearnedGradeGateTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=_KO,
                            requirementsJson=["Django"])
        self.app = make_application(
            self.job, screeningAnswersJson={"Examen?": "YES"},
            coverLetterTxt="Django-Erfahrung.")

    def test_none_when_disabled(self):
        _trustworthy_seed(self.job)
        self.assertIsNone(learned_grade(self.app))   # Default AUS

    def test_none_when_enabled_but_untrustworthy(self):
        _enable()
        # nur 4 Entscheidungen -> nicht belastbar
        for _ in range(4):
            a = make_application(self.job,
                                 screeningAnswersJson={"Examen?": "NO"})
            _advance(a, 'REJECTED')
        self.assertIsNone(learned_grade(self.app))

    def test_grade_when_enabled_and_trustworthy(self):
        _enable()
        _trustworthy_seed(self.job)
        lg = learned_grade(self.app)
        self.assertIsNotNone(lg)
        grade, reasons, ctx = lg
        self.assertIn(grade, ("A", "B", "C", "D"))
        self.assertTrue(reasons)
        self.assertTrue(ctx)


class GovernanceToggleTestCase(TestCase):
    def setUp(self):
        self.admin = make_user("ls-admin", role="HR-Admin")
        self.client.force_login(self.admin)
        self.url = reverse('ats:save_learned_scoring')

    def test_enable_requires_legal_confirmation(self):
        self.client.post(self.url, data={'enable': '1'})   # ohne Bestaetigung
        self.assertFalse(SystemSetting.objects.filter(
            key=LEARNED_SCORING_ENABLED_KEY, value='1').exists())

    def test_enable_with_confirmation(self):
        self.client.post(self.url, data={'enable': '1', 'legal_confirmed': '1'})
        self.assertTrue(SystemSetting.objects.filter(
            key=LEARNED_SCORING_ENABLED_KEY, value='1').exists())

    def test_disable(self):
        SystemSetting.objects.update_or_create(
            key=LEARNED_SCORING_ENABLED_KEY, defaults={'value': '1'})
        self.client.post(self.url, data={})   # enable nicht gesetzt -> aus
        self.assertEqual(SystemSetting.objects.get(
            key=LEARNED_SCORING_ENABLED_KEY).value, '0')

    def test_page_renders_with_governance_notice(self):
        r = self.client.get(reverse('ats:learned_scoring'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Hochrisiko")
        self.assertContains(r, "Messstrecke")

    def test_recruiter_cannot_toggle(self):
        self.client.logout()
        rec = make_user("ls-rec", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.post(self.url, data={'enable': '1', 'legal_confirmed': '1'})
        self.assertIn(r.status_code, (302, 403))
        self.assertFalse(SystemSetting.objects.filter(
            key=LEARNED_SCORING_ENABLED_KEY, value='1').exists())
