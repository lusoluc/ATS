"""Fehlgeschlagener Versand darf nicht als Erfolg durchgehen.

An 31 Stellen steht `fail_silently=True`. Das war einmal richtig gedacht — ein
Absturz im nächtlichen Job wäre schlimmer als eine verlorene Mail. Nur meldete
das Kanban danach „Absage verschickt", während der Mailserver sie abgelehnt
hatte. Und das Audit schrieb `"status": "SENT"`, ohne hinzusehen.
"""
import os
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from ..mail_config import HOST_KEY, mail_status
from ..mail_send import send_notice
from ..models import AuditLog, SystemSetting
from .factories import make_application, make_job, make_world
from .utils import make_user

# Im Testlauf ersetzt Django das Backend durch locmem - dann IST ein
# Zustellweg da, und "kein Mailserver" waere die falsche Aussage. Fuer die
# Faelle, die genau den SMTP-Weg pruefen, wird er hier ausdruecklich gesetzt.
SMTP_BACKEND = 'ats.mail_backend.ConfiguredSmtpBackend'


class SendNoticeTestCase(TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {
            "EMAIL_HOST": "", "DEFAULT_FROM_EMAIL": ""}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    @override_settings(EMAIL_BACKEND=SMTP_BACKEND)
    def test_without_a_mailserver_nothing_is_claimed(self):
        self.assertFalse(send_notice("Betreff", "Text", ["a@b.de"]))
        self.assertIn("kein Mailserver", mail_status()['last']['detail'])

    def test_server_error_is_recorded_with_its_reason(self):
        SystemSetting.objects.create(key=HOST_KEY, value="smtp.example.invalid")
        SystemSetting.objects.create(key="MAIL_FROM", value="postfach@example.invalid")
        with mock.patch('ats.mail_send.send_mail',
                        side_effect=OSError("Connection refused")):
            self.assertFalse(send_notice("Betreff", "Text", ["a@b.de"],
                                         context="Absage"))
        last = mail_status()['last']
        self.assertFalse(last['ok'])
        self.assertIn("Connection refused", last['detail'])
        self.assertIn("Absage", last['detail'])

    def test_empty_recipient_list_is_not_an_error_report(self):
        self.assertFalse(send_notice("Betreff", "Text", []))
        self.assertIsNone(mail_status()['last'])

    def test_success_is_recorded(self):
        SystemSetting.objects.create(key=HOST_KEY, value="smtp.example.invalid")
        SystemSetting.objects.create(key="MAIL_FROM", value="postfach@example.invalid")
        with mock.patch('ats.mail_send.send_mail', return_value=1):
            self.assertTrue(send_notice("Betreff", "Text", ["a@b.de"]))
        self.assertTrue(mail_status()['last']['ok'])


class RejectionFeedbackTestCase(TestCase):
    """Eine Absage, die niemanden erreicht, ist die unangenehmste Sorte
    verlorener Nachricht: Die bewerbende Person wartet weiter."""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)
        self.app = make_application(self.job, status="IN_REVIEW")
        self.client.force_login(make_user("absage-rec", role="Recruiter"))
        patcher = mock.patch.dict(os.environ, {"EMAIL_HOST": ""}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    @override_settings(EMAIL_BACKEND=SMTP_BACKEND)
    def test_recruiter_learns_that_the_rejection_did_not_go_out(self):
        resp = self.client.post(
            reverse('ats:update_status', args=[self.app.id]),
            {'status': 'REJECTED'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        entry = AuditLog.objects.filter(action='REJECTION_NOTICE_SENT').first()
        self.assertIsNotNone(entry)
        # Der Audit-Eintrag haelt fest, dass NICHTS zugestellt wurde
        self.assertIn('"delivered": false', entry.metadataJson.lower())


class DashboardMailWarningTestCase(TestCase):
    """Hintergrund-Versand hat kein Publikum. Ein kaputter Mailweg muss
    trotzdem dort auftauchen, wo täglich jemand hinsieht."""

    def setUp(self):
        self.admin = make_user("warn-admin", role="HR-Admin")

    def test_failed_send_is_shown_on_the_board(self):
        from ..mail_config import record_result
        record_result(False, "Connection refused")
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertContains(resp, "nicht")
        self.assertContains(resp, "Connection refused")

    def test_no_warning_when_the_last_send_worked(self):
        from ..mail_config import record_result
        record_result(True, "1 Nachricht(en)")
        self.client.force_login(self.admin)
        self.assertNotContains(self.client.get(reverse('ats:dashboard')),
                               "ging eine Nachricht")

    def test_recruiters_are_not_bothered_with_it(self):
        """Wer den Mailserver nicht einrichten kann, dem hilft die Meldung
        nicht - sie wäre nur Rauschen."""
        from ..mail_config import record_result
        record_result(False, "Connection refused")
        self.client.force_login(make_user("warn-rec", role="Recruiter"))
        self.assertNotContains(self.client.get(reverse('ats:dashboard')),
                               "ging eine Nachricht")


class DeliveryPathTestCase(TestCase):
    """Ein Mailserver ist nur nötig, wenn wirklich per SMTP verschickt wird.

    Wer das Backend bewusst umstellt — Konsole für einen Trockenlauf, Datei für
    eine Abnahme —, hat einen gültigen Weg. Ihn mit „kein Mailserver
    hinterlegt" zu blockieren, wäre eine Bevormundung mit falscher Begründung.
    """

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_console_or_test_backend_needs_no_smtp_host(self):
        from ..mail_config import delivery_possible
        self.assertTrue(delivery_possible())

    @override_settings(EMAIL_BACKEND='ats.mail_backend.ConfiguredSmtpBackend')
    def test_smtp_backend_does_need_one(self):
        from ..mail_config import delivery_possible
        with mock.patch.dict(os.environ, {"EMAIL_HOST": ""}, clear=False):
            self.assertFalse(delivery_possible())
