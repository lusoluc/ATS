"""Zustell-Jobs: Ein Fehlschlag darf weder verloren gehen noch Versand behaupten.

Alle vier Zustell-Kommandos liefen bereits über `send_notice` — werteten dessen
Rückgabewert aber nicht aus. Drei Folgen, an jedem der vier Wege:

* Einmal-Marker (`lastAlertSentAt`, `reminderSentAt`, `_mark`, Audit-Marker)
  wurden auch bei Fehlschlag gesetzt: Ein vorübergehender Mailserver-Ausfall
  verlor die Benachrichtigung **endgültig** — kein Lauf wiederholte sie je.
* Protokolle (`ALERT_SENT`, `INTERVIEW_REMINDER_SENT`, `FEEDBACK_REMINDER_SENT`)
  behaupteten Versand über Mails, die nie rausgingen — dasselbe Muster wie der
  SBV-Vermerk in Paket AN.
* Die Erfolgsmeldung zählte Versuche statt Zustellungen: „12 Alerts versendet"
  konnte bei totem Mailserver vollständig erlogen sein, und der
  Scheduler-Vermerk blieb grün.

Jetzt: Marker, Protokoll und Zählung nur bei Zustellung. Fehlschläge werden
gezählt und beim nächsten Lauf wiederholt. Schlägt ALLES fehl, endet der Job
mit Fehler (rot auf der Jobs-Seite); Teilfehler bleiben grün, weil eine
einzelne kaputte Adresse den Job nicht dauerhaft röten darf — wiederholt wird
sie trotzdem.
"""
import datetime
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from ..models import AuditLog, Interview, JobAlertLog, JobAlertSubscription, Message


def _kaputter_mailserver():
    return mock.patch("ats.mail_send.send_mail",
                      side_effect=OSError("Connection refused"))


class JobAlertDeliveryTestCase(TestCase):
    def _abo_und_stelle(self):
        from .factories import make_job, make_world
        world = make_world()
        make_job(world, title="Pflegefachkraft Station 3")
        return JobAlertSubscription.objects.create(
            email="hit@example.invalid", status="ACTIVE", keyword="Pflege",
            confirmationToken="c-z1", managementToken="m-z1")

    def test_failure_leaves_no_log_and_no_timestamp(self):
        """Kein ALERT_SENT über eine Mail, die nie rausging — und der
        nächste Lauf muss den Alert wiederholen können."""
        sub = self._abo_und_stelle()
        with _kaputter_mailserver():
            with self.assertRaises(CommandError):
                call_command("send_job_alerts", "--hours", "1",
                             stdout=StringIO())
        self.assertFalse(JobAlertLog.objects.filter(action="ALERT_SENT").exists())
        sub.refresh_from_db()
        self.assertIsNone(sub.lastAlertSentAt)

    def test_the_next_run_actually_retries(self):
        """Der Kern des Fundes: Ausfall heißt aufgeschoben, nicht verloren."""
        self._abo_und_stelle()
        with _kaputter_mailserver():
            with self.assertRaises(CommandError):
                call_command("send_job_alerts", "--hours", "1",
                             stdout=StringIO())
        aus = StringIO()
        call_command("send_job_alerts", "--hours", "1", stdout=aus)
        self.assertIn("1 Alert(s) zugestellt", aus.getvalue())
        self.assertTrue(JobAlertLog.objects.filter(action="ALERT_SENT").exists())

    def test_purge_hash_is_stable_across_processes(self):
        """Pythons hash() ist pro Prozess randomisiert — der Audit-Wert war
        als Nachweis wertlos. Jetzt: gekürzter Blind-Index, deterministisch."""
        from ..models import email_blind_index
        sub = JobAlertSubscription.objects.create(
            email="weg@example.invalid", status="INACTIVE",
            confirmationToken="c-z2", managementToken="m-z2")
        erwartet = email_blind_index("weg@example.invalid")[:16]
        call_command("send_job_alerts", stdout=StringIO())
        eintrag = AuditLog.objects.filter(action="JOB_ALERT_PURGED").latest("createdAt")
        self.assertIn(erwartet, eintrag.metadataJson)
        self.assertFalse(
            JobAlertSubscription.objects.filter(id=sub.id).exists())


class InterviewReminderDeliveryTestCase(TestCase):
    def _faelliges_interview(self):
        from ..models import Applicant, Application
        from .factories import make_job, make_world
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Erin", lastName="N",
                                          email="erin@example.invalid")
        app = Application.objects.create(applicant=person, jobPosting=job,
                                         status="INVITED")
        return Interview.objects.create(
            application=app,
            scheduledAt=timezone.now() + datetime.timedelta(hours=3))

    def test_failure_is_retried_and_leaves_no_trace_of_success(self):
        iv = self._faelliges_interview()
        with _kaputter_mailserver():
            with self.assertRaises(CommandError):
                call_command("send_interview_reminders", stdout=StringIO())
        iv.refresh_from_db()
        self.assertIsNone(iv.reminderSentAt,
                          "Der Marker wurde trotz Fehlschlag gesetzt - die "
                          "Erinnerung wäre endgültig verloren.")
        self.assertFalse(Message.objects.exists(),
                         "Keine Portal-Nachricht über eine Mail, die nie "
                         "rausging - sonst gäbe es beim Wiederholen Doppel.")
        self.assertFalse(AuditLog.objects.filter(
            action="INTERVIEW_REMINDER_SENT").exists())

        aus = StringIO()
        call_command("send_interview_reminders", stdout=aus)
        self.assertIn("1 Erinnerung(en) zugestellt", aus.getvalue())
        iv.refresh_from_db()
        self.assertIsNotNone(iv.reminderSentAt)
        self.assertEqual(Message.objects.count(), 1)


class FeedbackReminderDeliveryTestCase(TestCase):
    def test_failed_reminder_is_not_marked_as_sent(self):
        from django.contrib.auth.models import User

        from ..models import Applicant, Application
        from .factories import make_job, make_world
        from .utils import make_user
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Falk", lastName="B",
                                          email="falk@example.invalid")
        app = Application.objects.create(applicant=person, jobPosting=job,
                                         status="INVITED", interviewRound=1)
        pruefer = make_user("fb-pruefer", role="Hiring-Manager")
        User.objects.filter(pk=pruefer.pk).update(email="pruefer@example.invalid")
        iv = Interview.objects.create(
            application=app, outcome="COMPLETED", locationType="REMOTE",
            scheduledAt=timezone.now() - datetime.timedelta(days=4))
        iv.participants.add(pruefer)

        with _kaputter_mailserver():
            with self.assertRaises(CommandError):
                call_command("send_feedback_requests", stdout=StringIO())
        self.assertFalse(AuditLog.objects.filter(
            action="FEEDBACK_REMINDER_SENT").exists())

        aus = StringIO()
        call_command("send_feedback_requests", stdout=aus)
        self.assertIn("1 Feedback-Erinnerung(en) zugestellt", aus.getvalue())
        self.assertTrue(AuditLog.objects.filter(
            action="FEEDBACK_REMINDER_SENT").exists())
