"""N2: K.O.-Absage nennt objektive Gründe.

Deckt ab: der Snapshot der verfehlten Pflichtkriterien bei Einreichung,
die Anzeige im Kandidatenportal, die Absage-Mail — und den Wächter:
Ermessens-Absagen bekommen NIE eine automatisch formulierte Begründung.
"""
import datetime
import secrets

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import ApplicantToken, Application
from ..questions import KO_REASON_PREFIX, format_ko_reason, ko_grounds
from .factories import make_application, make_job, make_world
from .utils import make_user

KO_QUESTION = "Führerschein Klasse B vorhanden?"


def _ko_job(world):
    return make_job(world, screeningQuestionsJson=[{
        "id": "q-ko1", "type": "YES_NO", "question": KO_QUESTION,
        "isMandatory": True, "expectedAnswer": "YES"}])


class KoGroundsHelperTestCase(TestCase):
    def test_roundtrip(self):
        reason = format_ko_reason([KO_QUESTION, "3-Schicht-System möglich?"])
        self.assertEqual(ko_grounds(reason),
                         [KO_QUESTION, "3-Schicht-System möglich?"])

    def test_discretionary_reasons_yield_nothing(self):
        for reason in ("", None, "Wir haben uns anders entschieden.",
                       "Vom Bewerber über das Portal zurückgezogen."):
            self.assertEqual(ko_grounds(reason), [])


class KoSubmissionTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = _ko_job(self.world)

    def _apply(self, answer):
        cv = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test",
                                content_type="application/pdf")
        return self.client.post(reverse('ats:bewerben', args=[self.job.id]), {
            "first_name": "Kim", "last_name": "Muster",
            "email": "ko-test@x.de", "cover_letter": "Hallo.",
            "consent_privacy": "on", "cv_file": cv,
            "question_q-ko1": answer})

    def test_failed_ko_snapshots_criterion(self):
        self._apply("NO")
        app = Application.objects.get()
        self.assertEqual(app.status, 'REJECTED')
        self.assertTrue(app.withdrawReason.startswith(KO_REASON_PREFIX))
        self.assertEqual(ko_grounds(app.withdrawReason), [KO_QUESTION])

    def test_passed_ko_stays_new(self):
        self._apply("YES")
        app = Application.objects.get()
        self.assertEqual(app.status, 'NEW')
        self.assertFalse(app.withdrawReason)


class KoPortalTestCase(TestCase):
    def setUp(self):
        self.world = make_world()

    def _portal(self, app):
        tok = ApplicantToken.objects.create(
            applicant=app.applicant, token=secrets.token_urlsafe(16),
            expiresAt=timezone.now() + datetime.timedelta(days=1))
        return self.client.get(
            reverse('ats:candidate_portal', args=[tok.token]))

    def test_ko_rejection_shows_grounds(self):
        app = make_application(_ko_job(self.world), status="REJECTED",
                               withdrawReason=format_ko_reason([KO_QUESTION]))
        resp = self._portal(app)
        self.assertContains(resp, "Warum hat es nicht gepasst?")
        self.assertContains(resp, KO_QUESTION)

    def test_discretionary_rejection_shows_no_grounds(self):
        app = make_application(
            make_job(self.world), status="REJECTED",
            withdrawReason="Interne Entscheidung für andere Person.")
        resp = self._portal(app)
        self.assertNotContains(resp, "Warum hat es nicht gepasst?")
        self.assertNotContains(resp, "Interne Entscheidung")   # nie durchreichen


class KoRejectionMailTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.admin = make_user("ko-admin", role="HR-Admin")
        self.client.force_login(self.admin)

    def _notice_body(self, app):
        from django.core import mail
        mail.outbox = []
        from ..views.applications import _send_rejection_notice

        class _Req:
            user = self.admin

            @staticmethod
            def build_absolute_uri(path):
                return f"http://testserver{path}"
        _send_rejection_notice(_Req, app)
        return mail.outbox[0].body if mail.outbox else ""

    def test_ko_mail_names_criterion(self):
        app = make_application(_ko_job(self.world), status="REJECTED",
                               withdrawReason=format_ko_reason([KO_QUESTION]))
        body = self._notice_body(app)
        self.assertIn(KO_QUESTION, body)
        self.assertIn("laut Ausschreibung", body)

    def test_discretionary_mail_has_no_auto_reason(self):
        app = make_application(
            make_job(self.world), status="REJECTED",
            withdrawReason="Wir haben uns anders entschieden.")
        body = self._notice_body(app)
        self.assertNotIn("laut Ausschreibung", body)
        self.assertNotIn("anders entschieden", body)
