"""Cluster-Antwort: eine Vorlage, pro Person personalisiert an alle gesendet.

Deckt ab: Personalisierung der Platzhalter, je Person eine OUTBOUND-Nachricht
+ Audit, Senden-einmal (bereits beantwortete Frage wird uebersprungen),
Teilauswahl, und BOLA (fremde Bewerbung wird uebersprungen).
"""
from django.test import TestCase
from django.urls import reverse

from ..models import AuditLog, Message
from ..reply_drafts import batch_template, personalize
from .factories import make_application, make_job, make_world
from .utils import make_user


class PersonalizeTestCase(TestCase):
    def test_placeholders_replaced(self):
        tpl = "Guten Tag [[Vorname]], Ihre Bewerbung als [[Stelle]] " \
              "(Stand: [[Stand]])."
        out = personalize(tpl, first_name="Anna", job_title="Pflegekraft",
                          status="IN_REVIEW")
        self.assertIn("Anna", out)
        self.assertIn("Pflegekraft", out)
        self.assertIn("In Prüfung", out)
        self.assertNotIn("[[", out)

    def test_status_batch_template_exists(self):
        self.assertIn("[[Vorname]]", batch_template("STATUS"))

    def test_other_has_no_batch_template(self):
        self.assertEqual(batch_template("OTHER"), "")


def _inbound(app, text):
    return Message.objects.create(application=app, direction='INBOUND',
                                  content=text)


class BatchReplyViewTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Pflege Station 1")
        self.rec = make_user("br-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.url = reverse('ats:batch_reply')
        self.a = make_application(self.job, first_name="Anna", last_name="Berg",
                                  status="IN_REVIEW")
        self.b = make_application(self.job, first_name="Ben", last_name="Krause",
                                  status="IN_REVIEW")
        _inbound(self.a, "Wie ist der Stand?")
        _inbound(self.b, "Gibt es Neuigkeiten?")

    def _post(self, ids, template="Guten Tag [[Vorname]], Stand: [[Stand]]."):
        return self.client.post(self.url, data={
            'intent': 'STATUS', 'template': template,
            'app_ids': ids}, follow=True)

    def test_sends_personalized_to_all(self):
        r = self._post([str(self.a.id), str(self.b.id)])
        self.assertContains(r, "2 Antwort(en) gesendet")
        out_a = self.a.messages.filter(direction='OUTBOUND').first()
        out_b = self.b.messages.filter(direction='OUTBOUND').first()
        self.assertIn("Anna", out_a.content)
        self.assertIn("Ben", out_b.content)
        self.assertNotIn("[[", out_a.content)

    def test_writes_audit_per_person(self):
        self._post([str(self.a.id), str(self.b.id)])
        self.assertEqual(AuditLog.objects.filter(action='BATCH_REPLY_SENT').count(), 2)

    def test_partial_selection(self):
        self._post([str(self.a.id)])
        self.assertTrue(self.a.messages.filter(direction='OUTBOUND').exists())
        self.assertFalse(self.b.messages.filter(direction='OUTBOUND').exists())

    def test_send_once_skips_already_answered(self):
        # b bereits beantwortet -> letzte Nachricht OUTBOUND
        Message.objects.create(application=self.b, direction='OUTBOUND',
                               content="Schon beantwortet.")
        r = self._post([str(self.a.id), str(self.b.id)])
        self.assertContains(r, "1 Antwort(en) gesendet")
        # b bekommt keine zweite Sammel-Antwort
        self.assertEqual(self.b.messages.filter(direction='OUTBOUND').count(), 1)

    def test_bola_foreign_application_skipped(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Kiel")
        foreign_job = make_job(self.world, title="Fremd", location=other)
        fa = make_application(foreign_job, first_name="Zoe", last_name="Fremd")
        _inbound(fa, "Wie ist der Stand?")
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        self._post([str(fa.id)])
        self.assertFalse(fa.messages.filter(direction='OUTBOUND').exists())
