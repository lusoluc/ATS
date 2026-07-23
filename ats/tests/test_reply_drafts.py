"""C4: Antwort-Entwuerfe auf Bewerber-Nachrichten.

Deckt ab: regelbasierter Entwurf je Status (immer verfuegbar), der View
liefert bei nicht erreichbarer KI die Grundlage (used_ai=False), ohne
eingehende Nachricht bleibt es bei der Status-Vorlage, es wird NICHTS
automatisch gesendet, und BOLA (fremde Bewerbung -> 404).
"""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ..models import Message
from ..reply_drafts import rule_based_draft, status_line
from .factories import make_application, make_job, make_world
from .utils import make_user


class RuleBasedDraftTestCase(TestCase):
    def test_status_line_differs_per_status(self):
        self.assertNotEqual(status_line("IN_REVIEW"), status_line("INVITED"))
        self.assertIn("prueft", status_line("IN_REVIEW").lower()
                      .replace("ü", "ue"))

    def test_unknown_status_has_safe_default(self):
        self.assertTrue(status_line("SOMETHING_ELSE"))

    def test_draft_contains_greeting_job_and_signoff(self):
        draft = rule_based_draft(status="IN_REVIEW", job_title="Pflegefachkraft")
        self.assertIn("Guten Tag", draft)
        self.assertIn("Pflegefachkraft", draft)
        self.assertIn("Freundliche Gruesse", draft)

    def test_draft_makes_no_binding_promises(self):
        """Kein Entwurf darf eine Zusage/Absage/Termin fest zusichern."""
        for status in ("NEW", "IN_REVIEW", "INVITED", "HIRED", "REJECTED"):
            d = rule_based_draft(status=status, job_title="Stelle").lower()
            self.assertNotIn("zusage", d)
            self.assertNotIn("garantie", d)


class DraftReplyViewTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Pflegefachkraft (m/w/d)")
        self.app = make_application(self.job, status="IN_REVIEW")
        self.rec = make_user("c4-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.url = reverse('ats:draft_reply', args=[self.app.id])

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_without_inbound_returns_status_template(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data['used_ai'])
        self.assertIn("Guten Tag", data['draft'])

    def test_with_inbound_falls_back_when_ai_unreachable(self):
        Message.objects.create(application=self.app, direction='INBOUND',
                               content="Wann darf ich mit Rueckmeldung rechnen?")
        # KI nicht erreichbar -> Regel-Entwurf, aber niemals leer.
        with patch('ats.views.ai.make_ollama_request',
                   side_effect=Exception("no ollama")):
            r = self.client.post(self.url)
        data = r.json()
        self.assertFalse(data['used_ai'])
        self.assertIn("Guten Tag", data['draft'])

    def test_with_inbound_uses_ai_when_available(self):
        Message.objects.create(application=self.app, direction='INBOUND',
                               content="Habe ich alle Unterlagen eingereicht?")
        fake = (True, {"response": "Guten Tag, Ihre Unterlagen sind vollstaendig."})
        with patch('ats.views.ai.make_ollama_request', return_value=fake):
            r = self.client.post(self.url)
        data = r.json()
        self.assertTrue(data['used_ai'])
        self.assertIn("vollstaendig", data['draft'])

    def test_draft_does_not_send_a_message(self):
        """Entwerfen darf keine Nachricht anlegen - senden macht der Mensch."""
        before = self.app.messages.count()
        self.client.post(self.url)
        self.assertEqual(self.app.messages.count(), before)

    def test_bola_foreign_application_denied(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Kiel")
        foreign_job = make_job(self.world, title="Fremd", location=other)
        foreign_app = make_application(foreign_job)
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.post(reverse('ats:draft_reply', args=[foreign_app.id]))
        self.assertEqual(r.status_code, 404)
