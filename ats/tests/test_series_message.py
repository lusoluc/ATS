"""P3: Serien-Nachricht an aktive Bewerber einer Stelle (UC-UM-09).

Deckt ab: Personalisierung je Person, Portal-Nachricht + E-Mail + Audit,
abgeschlossene Bewerbungen nie angeschrieben, Teilauswahl, BOLA.
"""
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from ..models import AuditLog
from .factories import make_application, make_job, make_world
from .utils import make_user


class SeriesMessageTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Ausbildung Pflege 2027")
        self.rec = make_user("sm-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.a = make_application(self.job, first_name="Ulrike-Test",
                                  last_name="Eins", status="NEW")
        self.b = make_application(self.job, first_name="Zwei",
                                  last_name="Test", status="IN_REVIEW")
        self.closed = make_application(self.job, first_name="Drei",
                                       last_name="Zu", status="REJECTED")
        self.url = reverse('ats:job_series_message', args=[self.job.id])

    def test_page_lists_only_active(self):
        r = self.client.get(self.url)
        self.assertContains(r, "Ulrike-Test Eins")
        self.assertContains(r, "Zwei Test")
        self.assertNotContains(r, "Drei Zu")

    def test_send_personalized_with_mail_and_audit(self):
        mail.outbox = []
        r = self.client.post(self.url, data={
            'template': "Hallo [[Vorname]], Infotag zur Stelle [[Stelle]]!",
            'app_ids': [str(self.a.id), str(self.b.id)]}, follow=True)
        self.assertContains(r, "2 Person(en) gesendet")
        out_a = self.a.messages.filter(direction='OUTBOUND').first()
        self.assertIn("Ulrike-Test", out_a.content)
        self.assertIn("Ausbildung Pflege 2027", out_a.content)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            AuditLog.objects.filter(action='SERIES_MESSAGE_SENT').count(), 2)

    def test_closed_never_receives_even_if_posted(self):
        self.client.post(self.url, data={
            'template': "Hallo [[Vorname]]",
            'app_ids': [str(self.closed.id)]})
        self.assertFalse(self.closed.messages.filter(
            direction='OUTBOUND').exists())

    def test_partial_selection(self):
        self.client.post(self.url, data={
            'template': "Hallo [[Vorname]]", 'app_ids': [str(self.a.id)]})
        self.assertTrue(self.a.messages.filter(direction='OUTBOUND').exists())
        self.assertFalse(self.b.messages.filter(direction='OUTBOUND').exists())

    def test_bola_foreign_job_denied(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Kiel")
        foreign = make_job(self.world, title="Fremd", location=other)
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.get(
            reverse('ats:job_series_message', args=[foreign.id]))
        self.assertEqual(r.status_code, 404)
