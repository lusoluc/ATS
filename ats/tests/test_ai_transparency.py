"""N3: KI-Transparenz-Seite (Art. 86 EU AI Act).

Deckt ab: öffentlich erreichbar, beschreibt nur aktive Funktionen
(dynamisch nach Konfiguration), verlinkt aus Formular und Portal.
"""
import datetime
import secrets

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import ApplicantToken, SystemSetting
from ..scoring_eval import LEARNED_SCORING_ENABLED_KEY
from .factories import make_application, make_job, make_world
from .utils import make_user  # noqa: F401  (Muster-Import fuer Erweiterungen)


class TransparencyPageTestCase(TestCase):
    URL = reverse('ats:ai_transparency')

    def test_public_no_login_required(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Menschen entscheiden")
        self.assertContains(resp, "Art. 86 EU AI Act")
        # Pflichtkriterien-Abschnitt ist immer da (Mechanik existiert immer)
        self.assertContains(resp, "Pflichtkriterien")

    def test_auto_reply_topics_from_factory_default(self):
        # Auto-Antwort ist ab Werk fuer Stand+Ablauf an -> beide Themen stehen da
        resp = self.client.get(self.URL)
        self.assertContains(resp, "Automatische Antworten")
        self.assertContains(resp, "Stand des Verfahrens")
        self.assertContains(resp, "Ablauf")

    def test_auto_reply_section_hidden_when_off(self):
        SystemSetting.objects.create(key="AUTO_REPLY_ENABLED", value="0")
        resp = self.client.get(self.URL)
        self.assertNotContains(resp, "Automatische Antworten auf Standardfragen")

    def test_scoring_sections_follow_settings(self):
        resp = self.client.get(self.URL)
        self.assertNotContains(resp, "KI-Vorbewertung")
        self.assertNotContains(resp, "Gelernte Einordnung")
        SystemSetting.objects.create(key="AI_SCORING_ENABLED", value="1")
        SystemSetting.objects.create(key=LEARNED_SCORING_ENABLED_KEY, value="1")
        resp = self.client.get(self.URL)
        self.assertContains(resp, "KI-Vorbewertung")
        self.assertContains(resp, "Gelernte Einordnung")


class TransparencyLinksTestCase(TestCase):
    def test_linked_from_application_form(self):
        world = make_world()
        job = make_job(world)
        resp = self.client.get(reverse('ats:bewerben', args=[job.id]))
        self.assertContains(resp, reverse('ats:ai_transparency'))

    def test_linked_from_candidate_portal(self):
        world = make_world()
        app = make_application(make_job(world))
        tok = ApplicantToken.objects.create(
            applicant=app.applicant, token=secrets.token_urlsafe(16),
            expiresAt=timezone.now() + datetime.timedelta(days=1))
        resp = self.client.get(
            reverse('ats:candidate_portal', args=[tok.token]))
        self.assertContains(resp, reverse('ats:ai_transparency'))


class AccessibilityStatementTestCase(TestCase):
    """B7: Erklaerung zur Barrierefreiheit (BFSG) - oeffentlich + verlinkt."""

    def test_public_and_honest(self):
        resp = self.client.get(reverse('ats:accessibility_statement'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "teilweise")          # ehrlicher Stand
        self.assertContains(resp, "Barriere melden")    # Feedback-Weg
        self.assertContains(resp, "WCAG")

    def test_linked_from_footer(self):
        resp = self.client.get(reverse('ats:job_list'))
        self.assertContains(resp, reverse('ats:accessibility_statement'))
