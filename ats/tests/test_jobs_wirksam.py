"""Ein Job, der läuft, muss auch wirken — sonst ist der grüne Haken gelogen.

Zwei Funde derselben Klasse im Zeitplan:

* `verify_audit` meldete einen **Integritätsbruch** der Audit-Kette nur als
  Text und endete mit Exit-Code 0. Der Zeitplan-Dienst vermerkte den Lauf als
  „in Ordnung" — ausgerechnet der Job, der Manipulation erkennen soll, hätte
  sie grün abgehakt. Cron und Monitoring reagieren auf Exit-Codes, nicht auf
  Textfarben.
* `weekly_report` schrieb ohne `--out` nach stdout — im Zeitplan-Dienst also
  ins Docker-Log, das niemand liest. Der Job stand grün im Vermerk, die
  Leitung bekam nie einen Bericht. Der Docstring vertröstete auf „Versand
  folgt mit WP7"; die Versand-Schicht existierte längst.
"""
from io import StringIO
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from ..audit import write_audit
from ..jobs import JOBS_BY_NAME, last_run, run_job
from ..models import AuditLog
from .utils import make_user


def _admin_mit_adresse(name="wr-admin", adresse="leitung@example.invalid"):
    from django.contrib.auth.models import User
    u = make_user(name, role="HR-Admin")
    User.objects.filter(pk=u.pk).update(email=adresse)
    return u


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class VerifyAuditFailsLoudlyTestCase(TestCase):
    def _bruch(self):
        write_audit("READ_CV", application_id="x")
        opfer = write_audit("READ_CV", application_id="y")
        AuditLog.objects.filter(id=opfer.id).update(action="MANIPULIERT")

    def test_intact_chain_exits_cleanly(self):
        write_audit("READ_CV", application_id="x")
        aus = StringIO()
        call_command("verify_audit", stdout=aus)
        self.assertIn("intakt", aus.getvalue())

    def test_a_broken_chain_is_an_error_not_a_message(self):
        """Der Kern: Exit-Code statt Textfarbe."""
        self._bruch()
        with self.assertRaises(CommandError):
            call_command("verify_audit", stdout=StringIO())

    def test_the_scheduler_records_the_break_as_failure(self):
        """Vorher stand hier „in Ordnung" — über einem Integritätsbruch."""
        self._bruch()
        ok = run_job(JOBS_BY_NAME["verify_audit"])
        self.assertFalse(ok)
        vermerk = last_run("verify_audit")
        self.assertFalse(vermerk["ok"])
        self.assertIn("INTEGRIT", vermerk["detail"].upper())

    def test_admins_are_alerted_by_mail(self):
        _admin_mit_adresse()
        self._bruch()
        with self.assertRaises(CommandError):
            call_command("verify_audit", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Integritätsbruch", mail.outbox[0].subject)
        self.assertIn("leitung@example.invalid", mail.outbox[0].to)

    def test_a_failing_alert_mail_does_not_hide_the_break(self):
        """Der Versand ist Beigabe — der Fehler ist die Meldung."""
        _admin_mit_adresse()
        self._bruch()
        with mock.patch("ats.mail_send.send_mail",
                        side_effect=OSError("Mailserver weg")):
            with self.assertRaises(CommandError):
                call_command("verify_audit", stdout=StringIO())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class WeeklyReportReachesSomeoneTestCase(TestCase):
    def test_the_report_is_mailed_to_admins(self):
        _admin_mit_adresse()
        aus = StringIO()
        call_command("weekly_report", stdout=aus)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Wochenreport", mail.outbox[0].subject)
        self.assertIn("Pipeline", mail.outbox[0].body)
        self.assertIn("versandt", aus.getvalue())

    def test_without_recipients_the_job_fails_instead_of_green(self):
        """Ein Bericht, der niemanden erreicht, ist kein Erfolg."""
        with self.assertRaises(CommandError):
            call_command("weekly_report", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 0)

    def test_the_scheduler_records_the_undelivered_report_as_failure(self):
        ok = run_job(JOBS_BY_NAME["weekly_report"])
        self.assertFalse(ok)
        vermerk = last_run("weekly_report")
        self.assertFalse(vermerk["ok"])

    def test_out_still_writes_a_file_without_mailing(self):
        import tempfile
        from pathlib import Path
        _admin_mit_adresse()
        with tempfile.TemporaryDirectory() as d:
            ziel = Path(d) / "kpi.md"
            call_command("weekly_report", out=str(ziel), stdout=StringIO())
            self.assertIn("Wochenreport", ziel.read_text(encoding="utf-8"))
        self.assertEqual(len(mail.outbox), 0,
                         "Mit --out darf NICHT zusaetzlich versandt werden.")
