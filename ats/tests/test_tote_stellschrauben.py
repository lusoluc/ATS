"""U5/U6: Stellschrauben ohne Wirkung und Felder ohne Tür.

Zwei verwandte Muster aus dem Durchgang:

* **Ohne Wirkung** – eine Einstellung existiert, wird gelesen oder angelegt,
  ändert aber nichts (oder wird durch einen zweiten, unsichtbaren Pflegeort
  überschrieben).
* **Ohne Tür** – ein Feld wird gebraucht oder sogar als Pflicht erhoben, aber
  kein Formular kann es füllen und keine Ansicht zeigt es.
"""
import datetime
import os
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..blocks import enrich_blocks, normalize_blocks
from ..models import Location, MediaAsset, SystemSetting
from .factories import make_job, make_world
from .utils import make_user


class DeadSettingsTestCase(TestCase):
    """Angelegt, nie gelesen: zwei Pflegeorte, einer davon wirkungslos."""

    def test_seed_no_longer_creates_unread_branding_keys(self):
        from ..views.common import seed_data_if_empty
        seed_data_if_empty()
        for key in ("PRIMARY_COLOR", "FOOTER_TEXT"):
            self.assertFalse(
                SystemSetting.objects.filter(key=key).exists(),
                f"{key} wird von keiner Zeile gelesen – Branding kommt aus "
                "den Feldern der Organisation.")

    def test_settings_that_are_actually_read_still_exist(self):
        from ..views.common import seed_data_if_empty
        seed_data_if_empty()
        self.assertTrue(SystemSetting.objects.filter(key="COMPANY_NAME").exists())
        self.assertTrue(SystemSetting.objects.filter(key="SUPPORT_EMAIL").exists())


class OllamaPortTestCase(TestCase):
    """Die Diagnose riet zu OLLAMA_PORT – gelesen wurde die Variable nie."""

    def _url(self, **env):
        from ..views.ai import get_ollama_url
        with mock.patch.dict(os.environ, env, clear=False):
            return get_ollama_url("api/tags")

    def test_port_variable_is_honoured(self):
        self.assertIn(":11500/", self._url(OLLAMA_HOST="10.0.0.5",
                                           OLLAMA_PORT="11500"))

    def test_host_may_carry_its_own_port(self):
        url = self._url(OLLAMA_HOST="10.0.0.5:11600", OLLAMA_PORT="11500")
        self.assertIn("10.0.0.5:11600/", url)

    def test_nonsense_port_falls_back_to_default(self):
        self.assertIn(":11434/", self._url(OLLAMA_HOST="10.0.0.5",
                                           OLLAMA_PORT="elf"))


class BlockAltTextTestCase(TestCase):
    """WCAG 1.1.1: Die Mediathek erzwang einen Alt-Text und verwarf ihn."""

    def test_image_block_without_caption_is_not_decorative(self):
        blocks = normalize_blocks([{"type": "image", "url": "/media/x.jpg",
                                    "alt": "Team der Station 3"}])
        out = enrich_blocks(blocks)
        self.assertEqual(out[0]["resolved_alt"], "Team der Station 3")

    def test_alt_text_is_inherited_from_the_media_library(self):
        asset = MediaAsset.objects.create(name="team.jpg",
                                          file="uploads/team.jpg",
                                          altText="Pflegeteam im Gruppenbild")
        blocks = normalize_blocks([{"type": "image", "url": asset.file.url}])
        out = enrich_blocks(blocks)
        self.assertEqual(out[0]["resolved_alt"], "Pflegeteam im Gruppenbild")

    def test_own_alt_wins_over_library(self):
        asset = MediaAsset.objects.create(name="team.jpg",
                                          file="uploads/team.jpg",
                                          altText="Aus der Mediathek")
        blocks = normalize_blocks([{"type": "image", "url": asset.file.url,
                                    "alt": "Im Block getippt"}])
        self.assertEqual(enrich_blocks(blocks)[0]["resolved_alt"],
                         "Im Block getippt")

    def test_hero_falls_back_to_heading(self):
        blocks = normalize_blocks([{"type": "hero", "heading": "Willkommen",
                                    "imageUrl": "/media/hero.jpg"}])
        self.assertEqual(enrich_blocks(blocks)[0]["resolved_alt"], "Willkommen")


class LocationCoordinatesTestCase(TestCase):
    """Ohne Koordinaten fällt die Umkreissuche still auf Ortsgleichheit."""

    def setUp(self):
        self.client.force_login(make_user("geo-admin", role="HR-Admin"))

    def test_coordinates_can_be_entered(self):
        self.client.post(reverse('ats:locations'),
                         {'name': 'Hamburg', 'city': 'Hamburg',
                          'lat': '53.5511', 'lng': '9.9937'})
        loc = Location.objects.get(name='Hamburg')
        self.assertAlmostEqual(loc.lat, 53.5511)
        self.assertAlmostEqual(loc.lng, 9.9937)

    def test_german_comma_is_accepted(self):
        self.client.post(reverse('ats:locations'),
                         {'name': 'Lüneburg', 'lat': '53,2464', 'lng': '10,4115'})
        loc = Location.objects.get(name='Lüneburg')
        self.assertAlmostEqual(loc.lat, 53.2464)

    def test_impossible_values_are_dropped_not_stored(self):
        """Eine Koordinate, die auf keinen Punkt der Erde zeigt, wäre
        schlimmer als gar keine – die Umkreissuche rechnete mit Unfug."""
        self.client.post(reverse('ats:locations'),
                         {'name': 'Unfug', 'lat': '999', 'lng': 'abc'})
        loc = Location.objects.get(name='Unfug')
        self.assertIsNone(loc.lat)
        self.assertIsNone(loc.lng)

    def test_page_says_when_radius_search_will_not_work(self):
        Location.objects.create(name="Ohne Koordinaten", city="Kiel")
        resp = self.client.get(reverse('ats:locations'))
        self.assertContains(resp, "ohne Koordinaten")


class ApprovalAuthorTestCase(TestCase):
    """Freigaben hatten einen Zeitpunkt, aber keinen Urheber – und keine
    Ansicht, die die Entscheidung überhaupt zeigte."""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)
        self.approver = make_user("freigeber", role="HR-Admin")

    def _ticket_with_step(self, status="PENDING"):
        from ..models import ApprovalStep, ApprovalTicket
        ticket = ApprovalTicket.objects.create(jobPosting=self.job)
        return ApprovalStep.objects.create(
            approvalTicket=ticket, stepOrder=1, status=status,
            assignedRoleId="HR-Admin")

    def test_author_field_accepts_the_login_user(self):
        """Vorher zeigte das Feld auf ein totes Alt-Modell."""
        step = self._ticket_with_step()
        step.actionTakenBy = self.approver
        step.actionTakenAt = timezone.now()
        step.status = "APPROVED"
        step.save()
        step.refresh_from_db()
        self.assertEqual(step.actionTakenBy, self.approver)

    def test_decision_shows_up_in_the_job_timeline(self):
        from ..timeline import job_events
        step = self._ticket_with_step()
        step.status = "APPROVED"
        step.actionTakenBy = self.approver
        step.actionTakenAt = timezone.now()
        step.comments = "Bedarf belegt."
        step.save()
        titles = [e.title for e in job_events(self.job)]
        self.assertIn("Freigabe erteilt", titles)
        event = next(e for e in job_events(self.job)
                     if e.title == "Freigabe erteilt")
        self.assertEqual(event.actor, "freigeber")
        self.assertIn("Bedarf belegt.", event.detail)

    def test_pending_steps_are_not_history(self):
        from ..timeline import job_events
        self._ticket_with_step()
        self.assertNotIn("Freigabe erteilt",
                         [e.title for e in job_events(self.job)])

    def test_old_decision_without_author_says_so(self):
        from ..timeline import job_events
        step = self._ticket_with_step()
        step.status = "REJECTED"
        step.actionTakenAt = timezone.now() - datetime.timedelta(days=3)
        step.save()
        event = next(e for e in job_events(self.job)
                     if e.title == "Zustimmung verweigert")
        self.assertEqual(event.actor, "nicht dokumentiert")


class RequisitionChainTestCase(TestCase):
    """Der dritte Pfad der Freigabekette war von keinem Formular erreichbar."""

    def test_chain_comes_from_rule_or_global_setting_only(self):
        from ..approvals import requisition_chain
        world = make_world()
        SystemSetting.objects.create(key="REQUISITION_CHAIN",
                                     value="Leitung, Geschäftsführung")
        # Der frühere Zwischenschritt (Facility.requisitionChain) ist entfallen;
        # ein gesetzter Wert dort darf die globale Kette nicht mehr verdrängen.
        world.facility.requisitionChain = "Wird ignoriert"
        world.facility.save()
        self.assertEqual(requisition_chain(world.facility, None, None),
                         ["Leitung", "Geschäftsführung"])
