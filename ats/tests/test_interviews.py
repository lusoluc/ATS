"""SecurATS-Tests: interviews (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .utils import User, make_user


class InterviewMessageAlertTestCase(TestCase):
    """B9/B6/B5 – Kalender, Nachrichten, Job-Alert."""

    def _app(self):
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
        loc = Location.objects.create(name="L")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF")
        wf = WorkflowState.objects.create(name="W")
        job = JobPosting.objects.create(title="T", organization=org, facility=fac,
                                        location=loc, jobFamily=fam, workflowState=wf)
        appl = Applicant.objects.create(firstName="X", lastName="Y", email="x@ex.org")
        return Application.objects.create(applicant=appl, jobPosting=job)

    def setUp(self):
        self.client = Client()
        make_user("rec5", role="Recruiter")
        self.client.force_login(User.objects.get(username="rec5"))
        self.app = self._app()

    def test_interviews_view(self):
        from django.utils import timezone

        from ..models import Interview
        Interview.objects.create(application=self.app, scheduledAt=timezone.now(),
                                 locationType="REMOTE")
        resp = self.client.get(reverse('ats:interviews'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "T")

    def test_send_message(self):
        from ..models import Message
        resp = self.client.post(reverse('ats:application_messages', args=[self.app.id]),
                                data={"content": "Hallo, bitte Zeugnis nachreichen."})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Message.objects.filter(application=self.app, direction="OUTBOUND").exists())

    def test_job_alert_public_subscribe(self):
        from ..models import JobAlertSubscription
        c = Client()  # anonymous / public
        resp = c.post(reverse('ats:job_alert'), data={"email": "alert@ex.org", "global": "on"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(JobAlertSubscription.objects.filter(email="alert@ex.org").exists())

class CalendarSlotsTestCase(TestCase):
    """Team-Kalender + Timeslots + Portal-Selbstbuchung (Kollaborations-Paket)."""

    def _world(self):
        import uuid as _u

        from ..models import (
            Applicant,
            ApplicantToken,
            Application,
            Facility,
            InterviewSlot,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        self.loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        self.published = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(title="Pflegefachkraft", organization=org,
                                             facility=fac, location=self.loc,
                                             jobFamily=fam, workflowState=self.published)
        self.other_job = JobPosting.objects.create(title="IT-Admin", organization=org,
                                                   facility=fac, location=self.loc,
                                                   jobFamily=fam, workflowState=self.published)
        self.applicant = Applicant.objects.create(firstName="Aylin", lastName="K",
                                                  email="aylin@x.de")
        self.app = Application.objects.create(applicant=self.applicant,
                                              jobPosting=self.job, status="INVITED")
        self.token = ApplicantToken.objects.create(
            applicant=self.applicant, token="cal-token-1",
            expiresAt=timezone.now() + datetime.timedelta(days=30))
        self.slot = InterviewSlot.objects.create(
            jobPosting=self.job,
            startTime=timezone.now() + datetime.timedelta(days=3),
            endTime=timezone.now() + datetime.timedelta(days=3, minutes=45))
        self.foreign_slot = InterviewSlot.objects.create(
            jobPosting=self.other_job,
            startTime=timezone.now() + datetime.timedelta(days=3),
            endTime=timezone.now() + datetime.timedelta(days=3, minutes=45))

    def test_slot_series_creation_and_calendar_render(self):
        from ..models import InterviewSlot
        self._world()
        rec = make_user("calrec", role="Recruiter")
        self.client.force_login(rec)
        d = (timezone.localdate() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        r = self.client.post(reverse('ats:slot_create'), data={
            "job_id": str(self.job.id), "date": d, "time": "10:00",
            "duration": "45", "repeat": "4"})
        self.assertEqual(r.status_code, 302)
        mine = InterviewSlot.objects.filter(createdBy=rec)
        self.assertEqual(mine.count(), 4)                    # woechentliche Serie
        # Kalender zeigt Slot + Ersteller (Kollaboration)
        month = (timezone.localdate() + datetime.timedelta(days=7)).strftime('%Y-%m')
        page = self.client.get(reverse('ats:interviews') + f"?monat={month}")
        self.assertContains(page, "Slot frei")
        self.assertContains(page, "calrec")

    def test_slot_delete_only_own_unbooked(self):
        from ..models import InterviewSlot
        self._world()
        rec = make_user("calrec2", role="Recruiter")
        other = make_user("calrec3", role="Recruiter")
        self.client.force_login(rec)
        d = (timezone.localdate() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        self.client.post(reverse('ats:slot_create'), data={
            "job_id": str(self.job.id), "date": d, "time": "09:00"})
        slot = InterviewSlot.objects.get(createdBy=rec)
        self.client.force_login(other)                       # fremder Recruiter
        r = self.client.post(reverse('ats:slot_delete', args=[slot.id]))
        self.assertEqual(r.status_code, 404)                 # nicht loeschbar
        self.client.force_login(rec)
        r = self.client.post(reverse('ats:slot_delete', args=[slot.id]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(InterviewSlot.objects.filter(id=slot.id).exists())

    def test_candidate_books_slot_atomically(self):
        from django.core import mail

        from ..models import AuditLog, Interview, Message
        self._world()
        r = self.client.get(reverse('ats:candidate_portal', args=["cal-token-1"]))
        self.assertContains(r, "Bitte wählen Sie Ihren Gesprächstermin")
        r = self.client.post(reverse('ats:candidate_portal', args=["cal-token-1"]),
                             data={"book_app_id": str(self.app.id),
                                   "book_slot_id": str(self.slot.id)})
        self.assertEqual(r.status_code, 302)
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.isBooked)
        self.assertEqual(Interview.objects.filter(application=self.app).count(), 1)
        self.assertTrue(Message.objects.filter(application=self.app,
                                               direction="OUTBOUND").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Terminbestätigung", mail.outbox[0].subject)
        self.assertTrue(AuditLog.objects.filter(action="CANDIDATE_SLOT_BOOKED").exists())
        # Portal zeigt jetzt den bestaetigten Termin (mit Format), keine Auswahl mehr
        page = self.client.get(reverse('ats:candidate_portal', args=["cal-token-1"]))
        self.assertContains(page, "✓ Gespräch vor Ort")
        self.assertNotContains(page, "Bitte wählen Sie Ihren Gesprächstermin")

    def test_double_booking_blocked(self):
        from ..models import Applicant, ApplicantToken, Application, Interview
        self._world()
        # Zweite:r Eingeladene:r auf dieselbe Stelle mit eigenem Token
        a2 = Applicant.objects.create(firstName="Tom", lastName="W", email="tom@x.de")
        app2 = Application.objects.create(applicant=a2, jobPosting=self.job,
                                          status="INVITED")
        ApplicantToken.objects.create(applicant=a2, token="cal-token-2",
                                      expiresAt=timezone.now() + datetime.timedelta(days=30))
        self.client.post(reverse('ats:candidate_portal', args=["cal-token-1"]),
                         data={"book_app_id": str(self.app.id),
                               "book_slot_id": str(self.slot.id)})
        r = self.client.post(reverse('ats:candidate_portal', args=["cal-token-2"]),
                             data={"book_app_id": str(app2.id),
                                   "book_slot_id": str(self.slot.id)})
        self.assertEqual(r.status_code, 200)                 # kein Redirect: Fehlerseite
        self.assertContains(r, "gerade vergeben")
        self.assertEqual(Interview.objects.count(), 1)       # nur EIN Interview

    def test_foreign_slot_not_bookable(self):
        from ..models import Interview
        self._world()
        r = self.client.post(reverse('ats:candidate_portal', args=["cal-token-1"]),
                             data={"book_app_id": str(self.app.id),
                                   "book_slot_id": str(self.foreign_slot.id)})
        self.assertEqual(r.status_code, 200)
        self.foreign_slot.refresh_from_db()
        self.assertFalse(self.foreign_slot.isBooked)          # Slot anderer Stelle: nein
        self.assertEqual(Interview.objects.count(), 0)

    def test_candidate_choice_invite_creates_no_interview(self):
        from ..models import Interview, Message
        self._world()
        self.app.status = "IN_REVIEW"
        self.app.save()
        rec = make_user("calrec4", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.post(reverse('ats:schedule_interview'), data={
            "application_id": str(self.app.id), "slot_id": "CANDIDATE_CHOICE",
            "location_type": "IN_PERSON",
            "message_text": "Wir laden Sie herzlich ein."})
        self.assertEqual(r.status_code, 302)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "INVITED")
        self.assertEqual(Interview.objects.count(), 0)        # Termin waehlt Bewerber:in
        msg = Message.objects.get(application=self.app)
        self.assertIn("Wunschtermin", msg.content)            # Portal-Hinweis angehaengt

    def test_ics_export_scoped(self):
        from ..models import Interview
        self._world()
        Interview.objects.create(application=self.app,
                                 scheduledAt=timezone.now() + datetime.timedelta(days=5),
                                 locationType="REMOTE")
        rec = make_user("calrec5", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.get(reverse('ats:interviews_ics'))
        body = r.content.decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", body)
        self.assertIn("Aylin K", body)
        self.assertIn("Pflegefachkraft", body)
        self.assertIn('attachment; filename="securats-interviews.ics"',
                      r["Content-Disposition"])

class InterviewReminderTestCase(TestCase):
    """Termin-Erinnerungen: einmalig, fenstergenau, inkl. Team-Erinnerung."""

    def _world(self, hours_ahead=5, status="INVITED", with_slot_owner=False):
        import uuid as _u

        from ..models import (
            Applicant,
            Application,
            Facility,
            Interview,
            InterviewSlot,
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
        job = JobPosting.objects.create(title="Pflegefachkraft", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=wf)
        ap = Applicant.objects.create(firstName="Nina", lastName="H", email="nina@x.de")
        app = Application.objects.create(applicant=ap, jobPosting=job, status=status)
        when = timezone.now() + datetime.timedelta(hours=hours_ahead)
        iv = Interview.objects.create(application=app, scheduledAt=when,
                                      locationType="REMOTE",
                                      meetingLink="https://meet.example.de/x")
        if with_slot_owner:
            owner = make_user("slotowner", role="Recruiter")
            owner.email = "petra@klinik.example"
            owner.save()
            InterviewSlot.objects.create(jobPosting=job, startTime=when,
                                         endTime=when + datetime.timedelta(minutes=45),
                                         isBooked=True, application=app,
                                         createdBy=owner)
        return app, iv

    def test_reminder_sent_exactly_once(self):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command

        from ..models import AuditLog, Message
        app, iv = self._world(hours_ahead=5)
        call_command("send_interview_reminders", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Erinnerung", mail.outbox[0].subject)
        self.assertIn("https://meet.example.de/x", mail.outbox[0].body)
        self.assertTrue(Message.objects.filter(application=app,
                                               content__icontains="Erinnerung").exists())
        self.assertTrue(AuditLog.objects.filter(action="INTERVIEW_REMINDER_SENT").exists())
        iv.refresh_from_db()
        self.assertIsNotNone(iv.reminderSentAt)
        # Zweiter Lauf: kein Spam
        call_command("send_interview_reminders", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)

    def test_outside_window_not_reminded(self):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command
        self._world(hours_ahead=60)                          # erst uebermorgen
        call_command("send_interview_reminders", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 0)
        call_command("send_interview_reminders", "--hours", "72", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 1)                # groesseres Fenster greift

    def test_withdrawn_never_reminded(self):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command
        self._world(hours_ahead=5, status="WITHDRAWN")
        call_command("send_interview_reminders", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 0)

    def test_slot_owner_gets_team_reminder(self):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command
        self._world(hours_ahead=5, with_slot_owner=True)
        call_command("send_interview_reminders", stdout=StringIO())
        recipients = [addr for m in mail.outbox for addr in m.to]
        self.assertIn("nina@x.de", recipients)               # Bewerberin
        self.assertIn("petra@klinik.example", recipients)    # Slot-Anbieterin (Team)
        self.assertEqual(len(mail.outbox), 2)

class InterviewFormatsTeamTestCase(TestCase):
    """Flexible Prüfformate + Interview-Team + mehrstufige Runden."""

    def _world(self):
        import uuid as _u

        from ..models import (
            Applicant,
            Application,
            Facility,
            InterviewSlot,
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
        self.job = JobPosting.objects.create(title="Pflegefachkraft", organization=org,
                                             facility=fac, location=loc,
                                             jobFamily=fam, workflowState=wf)
        self.applicant = Applicant.objects.create(firstName="Piotr", lastName="K",
                                                  email="piotr@x.de")
        self.app = Application.objects.create(applicant=self.applicant,
                                              jobPosting=self.job, status="IN_REVIEW")
        self.token = __import__('ats.models', fromlist=['ApplicantToken']).ApplicantToken.objects.create(
            applicant=self.applicant, token="fmt-token",
            expiresAt=timezone.now() + datetime.timedelta(days=30))
        self.slot = InterviewSlot.objects.create(
            jobPosting=self.job, kind="TRIAL_WORK",
            startTime=timezone.now() + datetime.timedelta(days=4),
            endTime=timezone.now() + datetime.timedelta(days=4, hours=4))

    def test_invite_with_format_and_team_notifies_members(self):
        from django.core import mail

        from ..models import Interview
        self._world()
        rec = make_user("fmtrec", role="Recruiter")
        kollege = make_user("fachbereich", role="Recruiter")
        kollege.email = "fach@klinik.example"
        kollege.save()
        self.client.force_login(rec)
        r = self.client.post(reverse('ats:schedule_interview'), data={
            "application_id": str(self.app.id), "slot_id": "",
            "location_type": "TRIAL_WORK",
            "participants": [str(kollege.id)],
            "message_text": "Wir laden Sie zur Probearbeit ein."})
        self.assertEqual(r.status_code, 302)
        iv = Interview.objects.get(application=self.app)
        self.assertEqual(iv.locationType, "TRIAL_WORK")
        self.assertEqual(iv.kind_label, "Probearbeit / Hospitation")
        self.assertIn(kollege, iv.participants.all())
        team_mails = [m for m in mail.outbox if "fach@klinik.example" in m.to]
        self.assertEqual(len(team_mails), 1)                  # Team sofort informiert
        self.assertIn("Probearbeit", team_mails[0].subject)

    def test_portal_shows_slot_format_and_books_it(self):
        from ..models import Interview
        self._world()
        self.app.status = "INVITED"
        self.app.save()
        page = self.client.get(reverse('ats:candidate_portal', args=["fmt-token"]))
        self.assertContains(page, "Probearbeit / Hospitation")   # VOR der Buchung sichtbar
        self.client.post(reverse('ats:candidate_portal', args=["fmt-token"]),
                         data={"book_app_id": str(self.app.id),
                               "book_slot_id": str(self.slot.id)})
        iv = Interview.objects.get(application=self.app)
        self.assertEqual(iv.locationType, "TRIAL_WORK")           # Format uebernommen
        page = self.client.get(reverse('ats:candidate_portal', args=["fmt-token"]))
        self.assertContains(page, "✓ Probearbeit / Hospitation")

    def test_second_round_booking_after_past_interview(self):
        from ..models import Interview
        self._world()
        self.app.status = "INVITED"
        self.app.save()
        # Runde 1 liegt in der Vergangenheit (Telefonat gelaufen)
        Interview.objects.create(application=self.app,
                                 scheduledAt=timezone.now() - datetime.timedelta(days=7),
                                 locationType="PHONE")
        page = self.client.get(reverse('ats:candidate_portal', args=["fmt-token"]))
        self.assertContains(page, "Bitte wählen Sie Ihren Gesprächstermin")  # Runde 2 offen
        self.client.post(reverse('ats:candidate_portal', args=["fmt-token"]),
                         data={"book_app_id": str(self.app.id),
                               "book_slot_id": str(self.slot.id)})
        self.assertEqual(Interview.objects.filter(application=self.app).count(), 2)

    def test_reminder_reaches_whole_team(self):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command

        from ..models import Interview
        self._world()
        self.app.status = "INVITED"
        self.app.save()
        kollege = make_user("fachber2", role="Recruiter")
        kollege.email = "fach2@klinik.example"
        kollege.save()
        iv = Interview.objects.create(application=self.app,
                                      scheduledAt=timezone.now() + datetime.timedelta(hours=6),
                                      locationType="ASSESSMENT")
        iv.participants.add(kollege)
        call_command("send_interview_reminders", stdout=StringIO())
        recipients = [addr for m in mail.outbox for addr in m.to]
        self.assertIn("piotr@x.de", recipients)
        self.assertIn("fach2@klinik.example", recipients)
        team_mail = [m for m in mail.outbox if "fach2@klinik.example" in m.to][0]
        self.assertIn("Assessment", team_mail.subject)

class AppointmentSelfServiceTestCase(TestCase):
    """Bewerbende koennen Termine umbuchen, absagen oder Aenderung anfragen."""

    def _world(self, hours_ahead=72):
        import uuid as _u

        from ..models import (
            Applicant,
            ApplicantToken,
            Application,
            Facility,
            Interview,
            InterviewSlot,
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
        self.job = JobPosting.objects.create(title="Pflegefachkraft", organization=org,
                                             facility=fac, location=loc,
                                             jobFamily=fam, workflowState=wf)
        ap = Applicant.objects.create(firstName="Ewa", lastName="L", email="ewa@x.de")
        self.app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                              status="INVITED")
        ApplicantToken.objects.create(applicant=ap, token="ss-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=30))
        start = timezone.now() + datetime.timedelta(hours=hours_ahead)
        self.old_slot = InterviewSlot.objects.create(
            jobPosting=self.job, startTime=start, kind="VIDEO",
            endTime=start + datetime.timedelta(minutes=45),
            isBooked=True, application=self.app)
        owner = make_user("ssowner", role="Recruiter")
        owner.email = "owner@klinik.example"
        owner.save()
        self.old_slot.createdBy = owner
        self.old_slot.save()
        self.iv = Interview.objects.create(application=self.app, scheduledAt=start,
                                           locationType="VIDEO",
                                           reminderSentAt=timezone.now())
        new_start = timezone.now() + datetime.timedelta(hours=96)
        self.new_slot = InterviewSlot.objects.create(
            jobPosting=self.job, startTime=new_start, kind="ON_SITE",
            endTime=new_start + datetime.timedelta(minutes=45))

    def test_rebook_swaps_slots_and_resets_reminder(self):
        from django.core import mail

        from ..models import AuditLog
        self._world()
        r = self.client.post(reverse('ats:candidate_portal', args=["ss-token"]),
                             data={"rebook_interview_id": str(self.iv.id),
                                   "book_slot_id": str(self.new_slot.id)})
        self.assertEqual(r.status_code, 302)
        self.old_slot.refresh_from_db()
        self.new_slot.refresh_from_db()
        self.iv.refresh_from_db()
        self.assertFalse(self.old_slot.isBooked)              # alter Slot wieder frei
        self.assertTrue(self.new_slot.isBooked)
        self.assertEqual(self.iv.scheduledAt, self.new_slot.startTime)
        self.assertEqual(self.iv.locationType, "ON_SITE")     # Format uebernommen
        self.assertIsNone(self.iv.reminderSentAt)             # Erinnerung neu scharf
        recipients = [a for m in mail.outbox for a in m.to]
        self.assertIn("owner@klinik.example", recipients)     # Team informiert
        self.assertIn("ewa@x.de", recipients)                 # Bestaetigung
        self.assertTrue(AuditLog.objects.filter(
            action="CANDIDATE_APPOINTMENT_REBOOKED").exists())

    def test_cancel_frees_slot_and_reopens_choice(self):
        from django.core import mail

        from ..models import AuditLog, Interview, Message
        self._world()
        r = self.client.post(reverse('ats:candidate_portal', args=["ss-token"]),
                             data={"cancel_interview_id": str(self.iv.id),
                                   "reason": "Schichtplan geändert"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Interview.objects.count(), 0)
        self.old_slot.refresh_from_db()
        self.assertFalse(self.old_slot.isBooked)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "INVITED")          # Bewerbung lebt weiter
        self.assertTrue(Message.objects.filter(direction="INBOUND",
                                               content__icontains="Schichtplan").exists())
        self.assertTrue(AuditLog.objects.filter(
            action="CANDIDATE_APPOINTMENT_CANCELLED").exists())
        team = [m for m in mail.outbox if "owner@klinik.example" in m.to]
        self.assertEqual(len(team), 1)
        # Portal bietet die Terminwahl wieder an (freier neuer Slot existiert)
        page = self.client.get(reverse('ats:candidate_portal', args=["ss-token"]))
        self.assertContains(page, "Bitte wählen Sie Ihren Gesprächstermin")

    def test_within_24h_no_self_service_but_change_request(self):
        from ..models import Interview, Message
        self._world(hours_ahead=6)                            # Termin in 6 h
        page = self.client.get(reverse('ats:candidate_portal', args=["ss-token"]))
        self.assertContains(page, "weniger als 24 Stunden")
        self.assertNotContains(page, "Termin absagen")        # kein Selbstservice
        # Absage-POST wird abgewiesen
        r = self.client.post(reverse('ats:candidate_portal', args=["ss-token"]),
                             data={"cancel_interview_id": str(self.iv.id)})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "nur bis 24 Stunden")
        self.assertEqual(Interview.objects.count(), 1)        # Termin bleibt
        # Aenderungsanfrage funktioniert
        r = self.client.post(reverse('ats:candidate_portal', args=["ss-token"]),
                             data={"change_request_interview_id": str(self.iv.id),
                                   "reason": "Bus fällt aus – geht 30 Min später?"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Message.objects.filter(direction="INBOUND",
                                               content__icontains="Bus fällt aus").exists())

    def test_foreign_interview_untouchable(self):
        from ..models import Applicant, ApplicantToken, Application, Interview
        self._world()
        # Zweite Person mit eigenem Token versucht, den fremden Termin abzusagen
        stranger = Applicant.objects.create(firstName="X", lastName="Y", email="xy@x.de")
        Application.objects.create(applicant=stranger, jobPosting=self.job,
                                   status="INVITED")
        ApplicantToken.objects.create(applicant=stranger, token="stranger-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=30))
        self.client.post(reverse('ats:candidate_portal', args=["stranger-token"]),
                         data={"cancel_interview_id": str(self.iv.id)})
        self.assertEqual(Interview.objects.count(), 1)        # unberuehrt

class InterviewOutcomeTestCase(TestCase):
    """Outcome erfassen + messen: No-Show-Quote wird erst durch Pflege belastbar."""

    def _world(self):
        import uuid as _u

        from ..models import (
            Applicant,
            Application,
            Facility,
            Interview,
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
        self.job = JobPosting.objects.create(title="Pflegefachkraft", organization=org,
                                             facility=fac, location=loc,
                                             jobFamily=fam, workflowState=wf)
        self.ivs = []
        for i in range(6):
            ap = Applicant.objects.create(firstName=f"P{i}", lastName="X",
                                          email=f"p{i}@x.de")
            app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                             status="INVITED")
            self.ivs.append(Interview.objects.create(
                application=app, locationType="VIDEO",
                scheduledAt=timezone.now() - datetime.timedelta(days=i + 1)))
        self.rec = make_user("outrec", role="Recruiter")
        self.client.force_login(self.rec)

    def test_capture_outcome_with_audit_and_future_guard(self):
        from ..models import Applicant, Application, AuditLog, Interview
        self._world()
        r = self.client.post(reverse('ats:interview_outcome', args=[self.ivs[0].id]),
                             data={"outcome": "NO_SHOW"})
        self.assertEqual(r.status_code, 302)
        self.ivs[0].refresh_from_db()
        self.assertEqual(self.ivs[0].outcome, "NO_SHOW")
        self.assertEqual(self.ivs[0].outcome_label, "Nicht erschienen")
        self.assertTrue(AuditLog.objects.filter(action="INTERVIEW_OUTCOME_SET").exists())
        # Korrektur erlaubt, ungueltiger Wert ignoriert
        self.client.post(reverse('ats:interview_outcome', args=[self.ivs[0].id]),
                         data={"outcome": "COMPLETED"})
        self.ivs[0].refresh_from_db()
        self.assertEqual(self.ivs[0].outcome, "COMPLETED")
        self.client.post(reverse('ats:interview_outcome', args=[self.ivs[0].id]),
                         data={"outcome": "QUATSCH"})
        self.ivs[0].refresh_from_db()
        self.assertEqual(self.ivs[0].outcome, "COMPLETED")
        # Zukunftstermin: Erfassung abgelehnt
        ap = Applicant.objects.create(firstName="Z", lastName="Z", email="z@x.de")
        app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                         status="INVITED")
        future = Interview.objects.create(application=app, locationType="VIDEO",
                                          scheduledAt=timezone.now() + datetime.timedelta(days=2))
        r = self.client.post(reverse('ats:interview_outcome', args=[future.id]),
                             data={"outcome": "COMPLETED"})
        self.assertEqual(r.status_code, 404)

    def test_calendar_lists_pending_and_analytics_measures(self):
        from ..analytics import appointment_stats
        from ..models import Application, JobPosting
        self._world()
        page = self.client.get(reverse('ats:interviews'))
        self.assertContains(page, "Ergebnis erfassen (6)")
        # 4 stattgefunden, 2 No-Show erfassen -> Quote 33 %
        for iv in self.ivs[:4]:
            self.client.post(reverse('ats:interview_outcome', args=[iv.id]),
                             data={"outcome": "COMPLETED"})
        for iv in self.ivs[4:]:
            self.client.post(reverse('ats:interview_outcome', args=[iv.id]),
                             data={"outcome": "NO_SHOW"})
        stats = appointment_stats(Application.objects.all(), JobPosting.objects.all())
        self.assertEqual(stats["no_show_rate"], 33)
        self.assertEqual(stats["outcome_pending"], 0)
        self.assertTrue(any("No-Show-Quote" in h for h in stats["hints"]))
        r = self.client.get(reverse('ats:analytics'))
        self.assertContains(r, "No-Show-Quote")

    def test_hint_when_outcomes_unmaintained(self):
        from ..analytics import appointment_stats
        from ..models import Application, JobPosting
        self._world()                                          # 6 offene Ergebnisse
        stats = appointment_stats(Application.objects.all(), JobPosting.objects.all())
        self.assertIsNone(stats["no_show_rate"])               # ehrlich: keine Quote
        self.assertTrue(any("ohne erfasstes Ergebnis" in h for h in stats["hints"]))

class ConfigurableInterviewFormatsTestCase(TestCase):
    """P0-4: Terminformate per Verwaltung statt Code-Liste."""

    def test_add_rename_delete_and_labels_survive(self):
        from ..models import get_interview_kinds, interview_kind_label
        self.assertEqual(len(get_interview_kinds()), 6)        # Code-Default
        self.client.force_login(make_user("ifadmin", role="HR-Admin"))
        url = reverse('ats:interview_formats')
        self.client.post(url, data={"action": "add",
                                    "label": "Assessment-Center-Tag"})
        kinds = dict(get_interview_kinds())
        self.assertIn("ASSESSMENT_CENTER_TAG", kinds)
        # Neues Format sofort im Timeslot-Formular waehlbar
        page = self.client.get(reverse('ats:interviews'))
        self.assertContains(page, "Assessment-Center-Tag")
        # Umbenennen + Entfernen; Label bestehender Werte bleibt lesbar
        self.client.post(url, data={"action": "rename", "code": "PHONE",
                                    "label": "Telefon-Erstkontakt"})
        self.assertEqual(dict(get_interview_kinds())["PHONE"],
                         "Telefon-Erstkontakt")
        self.client.post(url, data={"action": "delete",
                                    "code": "ASSESSMENT_CENTER_TAG"})
        self.assertNotIn("ASSESSMENT_CENTER_TAG",
                         dict(get_interview_kinds()))
        self.assertEqual(interview_kind_label("ASSESSMENT"),
                         "Assessment / Auswahltag")            # Fallback intakt

    def test_only_hr_admin_manages(self):
        self.client.force_login(make_user("ifrec", role="Recruiter"))
        r = self.client.post(reverse('ats:interview_formats'),
                             data={"action": "add", "label": "X"})
        self.assertEqual(r.status_code, 403)

class InterviewRoundsTestCase(TestCase):
    """P1-11: mehrstufige Gespraechsrunden als formale Zustaende."""

    def _world(self, rounds=("Erstgespräch", "Fachgespräch")):
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
        self.loc = Location.objects.create(name="HH")
        self.fac = Facility.objects.create(name="F", organization=org)
        self.fam = JobFamily.objects.create(name="IR-Fam")
        self.published = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Stationsleitung", organization=org, facility=self.fac,
            location=self.loc, jobFamily=self.fam,
            workflowState=self.published, interviewRoundsJson=list(rounds))
        ap = Applicant.objects.create(firstName="R", lastName="K",
                                      email="rk@x.de")
        self.app = Application.objects.create(applicant=ap,
                                              jobPosting=self.job,
                                              status="INVITED")
        self.rec = make_user("ir-rec", role="Recruiter")

    def _hire(self):
        return self.client.post(
            reverse('ats:update_status', args=[self.app.id]),
            data={"status": "HIRED"})

    def _advance(self, op="advance"):
        return self.client.post(
            reverse('ats:advance_interview_round', args=[self.app.id]),
            data={"op": op})

    def test_hire_blocked_until_all_rounds_done_then_allowed(self):
        self._world()
        self.client.force_login(self.rec)
        r = self._hire()
        self.assertFalse(r.json()["success"])
        self.assertTrue(r.json()["rounds_blocked"])
        self.assertIn("runde 1 von 2", r.json()["error"])
        self.assertIn("Erstgespräch", r.json()["error"])
        self._advance()
        r2 = self._hire()
        self.assertIn("runde 2 von 2", r2.json()["error"])      # formal weiter
        self.assertIn("Fachgespräch", r2.json()["error"])
        self._advance()
        r3 = self._hire()
        self.assertTrue(r3.json()["success"])                   # alle Runden ✓
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "HIRED")

    def test_advance_caps_back_corrects_and_audits(self):
        self._world()
        self.client.force_login(self.rec)
        for _ in range(5):
            self._advance()                                     # kappt bei 2
        self.app.refresh_from_db()
        self.assertEqual(self.app.interviewRound, 2)
        self._advance(op="back")                                # Korrektur
        self.app.refresh_from_db()
        self.assertEqual(self.app.interviewRound, 1)
        from ..models import AuditLog
        self.assertTrue(AuditLog.objects.filter(
            action="INTERVIEW_ROUND_CHANGED").exists())

    def test_no_rounds_defined_keeps_legacy_behavior(self):
        self._world(rounds=[])
        self.client.force_login(self.rec)
        r = self._hire()
        self.assertTrue(r.json()["success"])                    # wie bisher
        r2 = self._advance()
        self.assertEqual(r2.status_code, 400)                   # nichts definiert

    def test_wizard_sets_rounds_and_edit_preserves(self):

        self._world(rounds=[])
        self.client.force_login(make_user("ir-admin", role="HR-Admin"))
        base = {"job_id": str(self.job.id), "title": "Stationsleitung",
                "description": "x", "tasks": "", "requirements": "",
                "screening_questions": "[]", "facility": str(self.fac.id),
                "location": str(self.loc.id),
                "job_family": str(self.fam.id)}
        self.client.post(reverse('ats:create_job'), data={
            **base, "interview_rounds":
                "Erstgespräch, Probearbeit , , Zusage-Gespräch"})
        self.job.refresh_from_db()
        self.assertEqual(self.job.interviewRoundsJson,
                         ["Erstgespräch", "Probearbeit", "Zusage-Gespräch"])
        # Edit OHNE das Feld: Bestand bleibt (Lehre aus der Headcount-Runde)
        self.client.post(reverse('ats:create_job'), data=base)
        self.job.refresh_from_db()
        self.assertEqual(len(self.job.interviewRoundsJson), 3)
        # Geleert = Rundenpflicht bewusst entfernt
        self.client.post(reverse('ats:create_job'),
                         data={**base, "interview_rounds": ""})
        self.job.refresh_from_db()
        self.assertEqual(self.job.interviewRoundsJson, [])

    def test_rounds_visible_on_interviews_page(self):
        self._world()
        self.client.force_login(self.rec)
        page = self.client.get(reverse('ats:interviews'))
        self.assertContains(page, "Gesprächsrunden")
        self.assertContains(page, "Erstgespräch")
        self.assertContains(page, "Runde abschließen")

class InterviewRoundCouplingTestCase(TestCase):
    """Interview-Ergebnis 'Stattgefunden' fuehrt die Gespraechsrunde mit."""

    def _world(self, rounds=("Erstgespräch", "Fachgespräch")):
        from ..models import (
            Applicant,
            Application,
            Facility,
            Interview,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="IC-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Pflegefachkraft", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=ws,
            interviewRoundsJson=list(rounds))
        ap = Applicant.objects.create(firstName="I", lastName="C",
                                      email="ic@x.de")
        self.app = Application.objects.create(applicant=ap,
                                              jobPosting=self.job,
                                              status="INVITED")
        self.iv = Interview.objects.create(
            application=self.app,
            scheduledAt=timezone.now() - datetime.timedelta(hours=2),
            locationType="REMOTE")
        self.rec = make_user("ic-rec", role="Recruiter")

    def _set_outcome(self, value):
        self.client.force_login(self.rec)
        return self.client.post(
            reverse('ats:interview_outcome', args=[self.iv.id]),
            data={"outcome": value})

    def test_completed_advances_round_correction_rolls_back(self):
        self._world()
        self.assertEqual(self.app.interviewRound, 0)
        self._set_outcome("COMPLETED")
        self.app.refresh_from_db()
        self.assertEqual(self.app.interviewRound, 1)           # vorgerueckt
        # Erneut COMPLETED speichern (kein Zustandswechsel) -> kein Doppel
        self._set_outcome("COMPLETED")
        self.app.refresh_from_db()
        self.assertEqual(self.app.interviewRound, 1)
        # Korrektur weg von COMPLETED -> Runde zurueck
        self._set_outcome("NO_SHOW")
        self.app.refresh_from_db()
        self.assertEqual(self.app.interviewRound, 0)

    def test_never_advances_beyond_defined_rounds(self):
        self._world(rounds=['Einzelgespräch'])              # nur 1 Runde
        self.app.interviewRound = 1                            # schon fertig
        self.app.save(update_fields=['interviewRound'])
        self._set_outcome("COMPLETED")
        self.app.refresh_from_db()
        self.assertEqual(self.app.interviewRound, 1)           # kein Overflow

    def test_no_rounds_defined_is_noop(self):
        self._world(rounds=[])
        self._set_outcome("COMPLETED")
        self.app.refresh_from_db()
        self.assertEqual(self.app.interviewRound, 0)           # nichts passiert
        # ... und HIRED bleibt ohne Runden frei moeglich (Bestandsverhalten)
        r = self.client.post(reverse('ats:update_status',
                                     args=[self.app.id]),
                             data={"status": "HIRED"})
        self.assertTrue(r.json()["success"])

class InterviewFeedbackTestCase(TestCase):
    """Strukturiertes Interview-Feedback: erfassen, gruppieren, an
    Entscheidungspunkten sichtbar, Bedenken-Warnung an HIRED."""

    def _world(self, rounds=("Erstgespräch", "Fachgespräch")):
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
        fam = JobFamily.objects.create(name="FB-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Teamleitung Pflege", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=ws,
            interviewRoundsJson=list(rounds))
        ap = Applicant.objects.create(firstName="F", lastName="B",
                                      email="fb@x.de")
        self.app = Application.objects.create(applicant=ap,
                                              jobPosting=self.job,
                                              status="INVITED")
        self.rec = make_user("fb-rec", role="Recruiter")
        self.rec2 = make_user("fb-rec2", role="Recruiter")

    def _save(self, user, **data):
        self.client.force_login(user)
        payload = {"recommendation": "YES"}
        payload.update(data)
        return self.client.post(
            reverse('ats:save_interview_feedback', args=[self.app.id]),
            data=payload)

    def test_feedback_saved_and_grouped_by_round(self):
        from ..models import InterviewFeedback, feedback_for_application
        self._world()
        self._save(self.rec, round="0", recommendation="YES",
                   strengths="Souverän", concerns="",
                   **{"rate_Ist fachlich versiert": "80",
                      "rate_Passt ins Team": "60"})
        self._save(self.rec2, round="0", recommendation="NO",
                   concerns="Wenig Führungserfahrung")
        fb = feedback_for_application(self.app)
        self.assertEqual(fb['total'], 2)
        self.assertEqual(fb['open_concerns'], 1)
        f1 = InterviewFeedback.objects.get(author=self.rec, round=0)
        self.assertEqual(f1.ratings["Ist fachlich versiert"], 80)
        self.assertTrue(f1.is_positive)

    def test_resubmitting_updates_own_not_duplicates(self):
        from ..models import InterviewFeedback
        self._world()
        self._save(self.rec, round="0", recommendation="YES")
        self._save(self.rec, round="0", recommendation="STRONG_NO",
                   concerns="Doch Zweifel nach Rücksprache")
        # Immer noch genau EIN Feedback dieser Person fuer die Runde
        qs = InterviewFeedback.objects.filter(author=self.rec, round=0)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().recommendation, "STRONG_NO")

    def test_feedback_visible_on_interviews_page(self):
        self._world()
        self._save(self.rec2, round="0", recommendation="NO",
                   concerns="Team-Fit unklar")
        self.client.force_login(self.rec)
        page = self.client.get(reverse('ats:interviews'))
        self.assertContains(page, "Interview-Feedback")
        self.assertContains(page, "Team-Fit unklar")       # Bedenken sichtbar
        self.assertContains(page, "1 mit Bedenken")

    def test_hire_warns_on_open_concerns_then_allows_with_force(self):
        from ..models import AuditLog
        self._world(rounds=[])   # keine Rundenpflicht, damit HIRED offen
        self._save(self.rec2, round="0", recommendation="NO",
                   concerns="Referenzen ausstehend")
        self.client.force_login(self.rec)
        # Ohne Bestaetigung: Warnung, KEINE Einstellung
        r = self.client.post(reverse('ats:update_status',
                                     args=[self.app.id]),
                             data={"status": "HIRED"})
        body = r.json()
        self.assertFalse(body["success"])
        self.assertTrue(body["concerns_blocked"])
        self.assertIn("Referenzen ausstehend", body["concerns"])
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "INVITED")       # nicht eingestellt
        # Mit bewusster Bestaetigung: Einstellung + Audit-Spur
        r2 = self.client.post(reverse('ats:update_status',
                                      args=[self.app.id]),
                              data={"status": "HIRED", "force": "1"})
        self.assertTrue(r2.json()["success"])
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "HIRED")
        self.assertTrue(AuditLog.objects.filter(
            action="HIRE_CONCERNS_ACKNOWLEDGED").exists())

    def test_hire_unaffected_when_no_concerns(self):
        self._world(rounds=[])
        self._save(self.rec2, round="0", recommendation="YES",
                   strengths="Top", concerns="")   # keine Bedenken
        self.client.force_login(self.rec)
        r = self.client.post(reverse('ats:update_status',
                                     args=[self.app.id]),
                             data={"status": "HIRED"})
        self.assertTrue(r.json()["success"])          # kein Gate

    def test_bola_blocks_feedback_outside_scope(self):
        from ..permissions import can_access_application
        self._world()
        # Recruiter mit eingeschraenktem Scope ohne Zugriff
        outsider = make_user("fb-out", role="Recruiter")
        # Scope kuenstlich leer -> kein Vollzugriff
        if hasattr(outsider, 'scope'):
            outsider.scope.facilities.clear()
            outsider.scope.locations.clear()
        if not can_access_application(outsider, self.app):
            self.client.force_login(outsider)
            r = self.client.post(
                reverse('ats:save_interview_feedback', args=[self.app.id]),
                data={"recommendation": "YES"})
            self.assertEqual(r.status_code, 404)

class InterviewFeedbackPercentTestCase(TestCase):
    """Prozent-Slider + automatisch abgeleitete Empfehlung."""

    def setUp(self):
        self._world()

    def _world(self):
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
        fam = JobFamily.objects.create(name="FP-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Erzieher:in", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=ws,
            interviewRoundsJson=['Erstgespräch'])
        ap = Applicant.objects.create(firstName="F", lastName="P",
                                      email="fp@x.de")
        self.app = Application.objects.create(applicant=ap,
                                              jobPosting=self.job,
                                              status="INVITED")
        self.rec = make_user("fp-rec", role="Recruiter")

    def test_percentages_stored_and_recommendation_derived_high(self):
        from ..models import InterviewFeedback
        self.client.force_login(self.rec)
        # Nur Slider, keine Empfehlung gewaehlt -> aus Schnitt abgeleitet
        self.client.post(
            reverse('ats:save_interview_feedback', args=[self.app.id]),
            data={"round": "0",
                  "rate_Passt ins Team": "90",
                  "rate_Ist motiviert": "90",
                  "rate_Ist fachlich versiert": "80",
                  "rate_Kommuniziert klar": "85"})
        f = InterviewFeedback.objects.get()
        self.assertEqual(f.ratings["Passt ins Team"], 90)
        self.assertEqual(f.overall_score, 86)                  # Schnitt
        self.assertEqual(f.recommendation, "STRONG_YES")       # >=85

    def test_recommendation_derived_low_and_clamped(self):
        from ..models import InterviewFeedback
        self.client.force_login(self.rec)
        self.client.post(
            reverse('ats:save_interview_feedback', args=[self.app.id]),
            data={"round": "0",
                  "rate_Passt ins Team": "10",
                  "rate_Ist fachlich versiert": "150",   # wird auf 100 gekappt
                  "rate_Ist motiviert": "20"})
        f = InterviewFeedback.objects.get()
        self.assertEqual(f.ratings["Ist fachlich versiert"], 100)  # geklemmt
        # Schnitt (10+100+20)/3 = 43 -> NEUTRAL? 43<45 -> NO
        self.assertEqual(f.overall_score, 43)
        self.assertEqual(f.recommendation, "NO")

    def test_explicit_recommendation_overrides_derived(self):
        from ..models import InterviewFeedback
        self.client.force_login(self.rec)
        self.client.post(
            reverse('ats:save_interview_feedback', args=[self.app.id]),
            data={"round": "0", "recommendation": "STRONG_NO",
                  "rate_Passt ins Team": "95"})   # hoher Score, aber Veto
        f = InterviewFeedback.objects.get()
        self.assertEqual(f.recommendation, "STRONG_NO")

    def test_empty_submission_is_ignored(self):
        from ..models import InterviewFeedback
        self.client.force_login(self.rec)
        self.client.post(
            reverse('ats:save_interview_feedback', args=[self.app.id]),
            data={"round": "0"})                    # nichts angegeben
        self.assertEqual(InterviewFeedback.objects.count(), 0)

    def test_sliders_render_on_page(self):
        self.client.force_login(self.rec)
        page = self.client.get(reverse('ats:interviews'))
        self.assertContains(page, 'type="range"')
        self.assertContains(page, "Passt ins Team")
        self.assertContains(page, "Gesamteindruck")

class FeedbackBoardSummaryTestCase(TestCase):
    """Feedback-Zusammenfassung auf dem Kanban-Board (Bulk, kein N+1)."""

    def _world(self):
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
        loc = Location.objects.create(name="HH", city="Hamburg")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="BS-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Sozialpädagoge", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=ws)
        self.app = Application.objects.create(
            applicant=Applicant.objects.create(firstName="B", lastName="S",
                                               email="bs@x.de"),
            jobPosting=self.job, status="IN_REVIEW")
        self.rec = make_user("bs-rec", role="Recruiter")
        self.rec2 = make_user("bs-rec2", role="Recruiter")

    def _fb(self, author, ratings, concerns="", rec="YES", rnd=0):

        from ..models import InterviewFeedback
        InterviewFeedback.objects.create(
            application=self.app, author=author, round=rnd,
            recommendation=rec, ratingsJson=ratings,
            concerns=concerns)

    def test_bulk_summary_averages_and_counts(self):
        from ..models import feedback_summaries
        self._world()
        self._fb(self.rec, {"Passt ins Team": 80, "Ist motiviert": 100})  # 90
        self._fb(self.rec2, {"Passt ins Team": 60, "Ist motiviert": 80},   # 70
                 concerns="Erfahrung dünn", rec="NEUTRAL")
        s = feedback_summaries([self.app.id])[self.app.id]
        self.assertEqual(s['count'], 2)
        self.assertEqual(s['avg_score'], 80)          # (90+70)/2
        self.assertEqual(s['open_concerns'], 1)
        self.assertEqual(s['positive'], 1)            # nur rec YES

    def test_badge_renders_on_board(self):
        self._world()
        self._fb(self.rec, {"Passt ins Team": 90}, concerns="Gehaltswunsch hoch")
        self.client.force_login(self.rec)
        page = self.client.get(reverse('ats:dashboard'))
        self.assertContains(page, "fa-comment-dots")   # Score-Badge
        self.assertContains(page, "fa-triangle-exclamation")  # Bedenken-Badge

    def test_no_feedback_no_badge_data(self):
        from ..models import feedback_summaries
        self._world()
        self.assertEqual(feedback_summaries([self.app.id]), {})

class FeedbackRequestTestCase(TestCase):
    """Bitte um Feedback: Event-Mail bei 'stattgefunden' + Cron-Nachfassen."""

    def _world(self, rounds=()):
        from ..models import (
            Applicant,
            Application,
            Facility,
            Interview,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="FR-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Heilerziehungspfleger", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=ws,
            interviewRoundsJson=list(rounds))
        self.app = Application.objects.create(
            applicant=Applicant.objects.create(firstName="F", lastName="R",
                                               email="fr@x.de"),
            jobPosting=self.job, status="INVITED")
        self.iv = Interview.objects.create(
            application=self.app,
            scheduledAt=timezone.now() - datetime.timedelta(days=3),
            locationType="REMOTE")
        self.rec = make_user("fr-rec", role="Recruiter")
        # Zwei Interviewer als Teilnehmer, einer ohne Mail
        self.p1 = make_user("fr-p1", role="Recruiter")
        self.p1.email = "p1@x.de"
        self.p1.save(update_fields=["email"])
        self.p2 = make_user("fr-p2", role="Recruiter")
        self.p2.email = "p2@x.de"
        self.p2.save(update_fields=["email"])
        self.iv.participants.set([self.p1, self.p2])

    def _complete(self):
        from django.core import mail
        mail.outbox = []
        self.client.force_login(self.rec)
        self.client.post(reverse('ats:interview_outcome', args=[self.iv.id]),
                         data={"outcome": "COMPLETED"})
        return mail.outbox

    def test_completion_requests_feedback_from_all_participants(self):
        self._world()
        box = self._complete()
        rcpts = sorted(m.to[0] for m in box)
        self.assertEqual(rcpts, ["p1@x.de", "p2@x.de"])
        self.assertIn("Bitte um Feedback", box[0].subject)

    def test_participant_who_already_gave_feedback_not_asked(self):
        from ..models import InterviewFeedback
        self._world()
        # p1 hat schon bewertet (Runde 0)
        InterviewFeedback.objects.create(
            application=self.app, author=self.p1, round=0,
            recommendation="YES", ratingsJson={"Passt ins Team": 80})
        box = self._complete()
        rcpts = [m.to[0] for m in box]
        self.assertEqual(rcpts, ["p2@x.de"])         # nur der Offene

    def test_no_double_mail_on_resave(self):
        self._world()
        self._complete()
        # Erneut COMPLETED speichern -> kein Zustandswechsel -> keine Mail
        from django.core import mail
        mail.outbox = []
        self.client.post(reverse('ats:interview_outcome', args=[self.iv.id]),
                         data={"outcome": "COMPLETED"})
        self.assertEqual(len(mail.outbox), 0)

    def test_cron_reminds_stragglers_once(self):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command
        self._world()
        self._complete()          # Erst-Bitte raus
        mail.outbox = []
        call_command("send_feedback_requests", days=2, stdout=StringIO())
        rcpts = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(rcpts, ["p1@x.de", "p2@x.de"])   # beide erinnert
        self.assertIn("steht noch aus", mail.outbox[0].subject)
        # Zweiter Lauf: keine erneute Mail (Einmal-Marker)
        mail.outbox = []
        call_command("send_feedback_requests", days=2, stdout=StringIO())
        self.assertEqual(len(mail.outbox), 0)

    def test_cron_skips_recent_interviews(self):
        from io import StringIO

        from django.core import mail
        from django.core.management import call_command
        self._world()
        self.iv.scheduledAt = timezone.now() - datetime.timedelta(hours=6)
        self.iv.outcome = "COMPLETED"
        self.iv.save()
        mail.outbox = []
        call_command("send_feedback_requests", days=2, stdout=StringIO())
        self.assertEqual(len(mail.outbox), 0)             # zu frisch

class FeedbackModalJsonTestCase(TestCase):
    """Interview-Feedback im Kandidaten-Modal (JSON-Endpoint)."""

    def _world(self):

        from ..models import (
            Applicant,
            Application,
            Facility,
            InterviewFeedback,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="MJ-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Kita-Leitung", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=ws)
        self.app = Application.objects.create(
            applicant=Applicant.objects.create(firstName="M", lastName="J",
                                               email="mj@x.de"),
            jobPosting=self.job, status="IN_REVIEW")
        self.rec = make_user("mj-rec", role="Recruiter")
        self.rec2 = make_user("mj-rec2", role="Recruiter")
        InterviewFeedback.objects.create(
            application=self.app, author=self.rec2, round=0,
            recommendation="NO", ratingsJson={"Passt ins Team": 40},
            concerns="Führung noch unklar", strengths="Fachlich stark")

    def test_json_returns_structured_feedback(self):
        self._world()
        self.client.force_login(self.rec)
        r = self.client.get(
            reverse('ats:application_feedback_json', args=[self.app.id]))
        data = r.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['open_concerns'], 1)
        self.assertEqual(data['rounds'][0]['round'], 1)
        item = data['rounds'][0]['items'][0]
        self.assertEqual(item['concerns'], "Führung noch unklar")
        self.assertEqual(item['ratings']["Passt ins Team"], 40)
        self.assertFalse(item['positive'])

    def test_json_bola_scoped(self):
        from ..permissions import can_access_application
        self._world()
        outsider = make_user("mj-out", role="Recruiter")
        if hasattr(outsider, 'scope'):
            outsider.scope.facilities.clear()
            outsider.scope.locations.clear()
        if not can_access_application(outsider, self.app):
            self.client.force_login(outsider)
            r = self.client.get(
                reverse('ats:application_feedback_json', args=[self.app.id]))
            self.assertEqual(r.status_code, 404)

    def test_modal_has_feedback_container(self):
        self._world()
        self.client.force_login(self.rec)
        page = self.client.get(reverse('ats:dashboard'))
        self.assertContains(page, 'id="modal-feedback"')
        self.assertContains(page, 'loadCandidateFeedback')
