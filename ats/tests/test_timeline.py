"""Aktionsverlauf (Timeline): Zusammenfuehrung aus Audit, Nachrichten,
Gespraechen und Feedback - je Bewerbung und je Stelle.

Deckt ab: interne UND Bewerber-Aktionen erscheinen, chronologische Ordnung,
keine Doppelzaehlung (Message vs. MESSAGE_SENT-Audit), Stellen-Verlauf mit
Namen, sowie BOLA (fremde Bewerbung/Stelle -> 404).
"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..audit import write_audit
from ..timeline import application_events, job_events, relative_age
from .factories import make_application, make_job, make_world
from .utils import make_user


class TimelineAssemblyTestCase(TestCase):
    """Rechenkern: baut der Verlauf die richtigen Eintraege aus den Quellen?"""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Verlaufs-Stelle")
        self.t0 = timezone.now() - timedelta(days=5)
        self.app = make_application(self.job, first_name="Nadia",
                                    last_name="Kaya", createdAt=self.t0)
        self.rec = make_user("tl-rec", role="Recruiter")

    def test_application_starts_with_submission(self):
        events = application_events(self.app)
        self.assertTrue(events)
        first = events[0]
        self.assertEqual(first.title, "Bewerbung eingegangen")
        self.assertEqual(first.actor_kind, "bewerber")
        self.assertEqual(first.when, self.t0)

    def test_internal_and_candidate_actions_both_present(self):
        from ..models import Message
        Message.objects.create(application=self.app, direction="INBOUND",
                               content="Wann hoere ich von Ihnen?",
                               createdAt=self.t0 + timedelta(days=1))
        write_audit("STATUS_CHANGE", user=self.rec, application_id=self.app.id,
                    oldStatus="NEW", newStatus="IN_REVIEW")
        write_audit("WITHDRAWN_BY_CANDIDATE", application_id=self.app.id)

        kinds = {e.actor_kind for e in application_events(self.app)}
        self.assertIn("intern", kinds)      # Statuswechsel durch Recruiter
        self.assertIn("bewerber", kinds)    # Bewerbung + Rueckzug
        titles = [e.title for e in application_events(self.app)]
        self.assertIn("Status geaendert", titles)
        self.assertIn("Bewerbung zurueckgezogen", titles)

    def test_status_change_shows_readable_transition(self):
        write_audit("STATUS_CHANGE", user=self.rec, application_id=self.app.id,
                    oldStatus="NEW", newStatus="INVITED")
        ev = next(e for e in application_events(self.app)
                  if e.title == "Status geaendert")
        self.assertEqual(ev.detail, "Neu → Eingeladen")

    def test_events_are_chronological(self):
        from ..models import Message
        Message.objects.create(application=self.app, direction="OUTBOUND",
                               content="Danke fuer Ihre Bewerbung.",
                               createdAt=self.t0 + timedelta(days=2))
        write_audit("STATUS_CHANGE", user=self.rec, application_id=self.app.id,
                    newStatus="IN_REVIEW")
        events = application_events(self.app)
        times = [e.when for e in events]
        self.assertEqual(times, sorted(times))

    def test_message_not_double_counted_with_audit(self):
        """Nachricht kommt aus dem Message-Objekt; das MESSAGE_SENT-Audit
        darf NICHT zusaetzlich als eigener Eintrag erscheinen."""
        from ..models import Message
        Message.objects.create(application=self.app, direction="OUTBOUND",
                               content="Terminvorschlag anbei.",
                               createdAt=self.t0 + timedelta(days=1))
        write_audit("MESSAGE_SENT", user=self.rec, application_id=self.app.id)
        msg_like = [e for e in application_events(self.app)
                    if "Nachricht" in e.title]
        self.assertEqual(len(msg_like), 1)
        self.assertEqual(msg_like[0].detail[:11], "Terminvorsc")

    def test_interview_and_feedback_appear(self):
        from ..models import Interview, InterviewFeedback
        iv = Interview.objects.create(
            application=self.app, scheduledAt=self.t0 + timedelta(days=3),
            locationType="VIDEO")
        InterviewFeedback.objects.create(
            application=self.app, interview=iv, author=self.rec,
            round=1, recommendation="YES", strengths="Ruhig, klar",
            concerns="Wenig Nachtdienst-Erfahrung")
        titles = [e.title for e in application_events(self.app)]
        self.assertIn("Gespraech geplant", titles)
        self.assertTrue(any(t.startswith("Feedback") for t in titles))
        fb = next(e for e in application_events(self.app)
                  if e.title.startswith("Feedback"))
        self.assertIn("Bedenken", fb.detail)


class JobTimelineTestCase(TestCase):
    """Stellen-Verlauf: Anlage, eingehende Bewerbungen, Meilensteine mit Namen."""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Stellen-Verlauf")
        self.rec = make_user("jt-rec", role="Recruiter")

    def test_job_timeline_lists_creation_and_applications(self):
        make_application(self.job, first_name="Ida", last_name="Sturm")
        make_application(self.job, first_name="Leo", last_name="Vogt")
        events = job_events(self.job)
        titles = [e.title for e in events]
        self.assertEqual(titles[0], "Stelle angelegt")
        details = " ".join(e.detail for e in events)
        self.assertIn("Ida Sturm", details)
        self.assertIn("Leo Vogt", details)

    def test_job_milestone_carries_applicant_name(self):
        app = make_application(self.job, first_name="Ida", last_name="Sturm")
        write_audit("INVITE_SENT", user=self.rec, application_id=str(app.id))
        invite = next(e for e in job_events(self.job)
                      if e.title.startswith("Zum Gespraech eingeladen"))
        self.assertIn("Ida Sturm", invite.title)


class TimelinePageTestCase(TestCase):
    """Views: rendern, Inhalt zeigen, BOLA durchsetzen."""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Seiten-Job")
        self.app = make_application(self.job, first_name="Nadia",
                                    last_name="Kaya")
        self.rec = make_user("tlp-rec", role="Recruiter")
        self.client.force_login(self.rec)

    def test_application_timeline_renders(self):
        write_audit("STATUS_CHANGE", user=self.rec, application_id=self.app.id,
                    oldStatus="NEW", newStatus="IN_REVIEW")
        r = self.client.get(
            reverse('ats:application_timeline', args=[self.app.id]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Aktionsverlauf")
        self.assertContains(r, "Bewerbung eingegangen")
        self.assertContains(r, "Nadia Kaya")

    def test_job_timeline_renders(self):
        r = self.client.get(reverse('ats:job_timeline', args=[self.job.id]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Stelle angelegt")

    def test_bola_foreign_application_denied(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Bremen")
        foreign_job = make_job(self.world, title="Fremd", location=other)
        foreign_app = make_application(foreign_job)
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.get(
            reverse('ats:application_timeline', args=[foreign_app.id]))
        self.assertEqual(r.status_code, 404)

    def test_bola_foreign_job_denied(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Bremen")
        foreign_job = make_job(self.world, title="Fremd", location=other)
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.get(
            reverse('ats:job_timeline', args=[foreign_job.id]))
        self.assertEqual(r.status_code, 404)


class RelativeAgeTestCase(TestCase):
    def test_relative_age_buckets(self):
        now = timezone.now()
        self.assertEqual(relative_age(now, now), "gerade eben")
        self.assertEqual(relative_age(now - timedelta(minutes=5), now), "vor 5 Min.")
        self.assertEqual(relative_age(now - timedelta(hours=3), now), "vor 3 Std.")
        self.assertEqual(relative_age(now - timedelta(days=1), now), "vor 1 Tag")
        self.assertEqual(relative_age(now - timedelta(days=3), now), "vor 3 Tagen")
