"""Stellen-Entwurf: aus Bausteinen statt vor dem leeren Feld.

Die Konvertierung einer Bedarfsmeldung erzeugte wörtlich „<Titel> –
Beschreibung folgt.", und im Wizard begann die Beschreibung leer — obwohl
Textbausteine, Benefits und Einrichtungsprofil längst im System liegen.

Die harte Grenze zieht sich durch alle Tests: Der Entwurf nennt nie
Gehaltszahlen. Die Spanne kommt aus dem Entgeltband und nur von dort
(EU-RL 2023/970) — eine KI-Fassung mit Betrag wird komplett verworfen,
nicht repariert.
"""
import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ..job_draft import (
    MAX_ITEMS,
    mentions_money,
    rule_based_draft,
    validate_ai_draft,
)
from ..models import Benefit, FacilityProfile, TextSnippet
from .factories import make_world
from .utils import make_user


class RegelEntwurfTestCase(TestCase):
    def setUp(self):
        self.welt = make_world()

    def test_family_snippet_beats_the_generic_one(self):
        TextSnippet.objects.create(category="INTRO", content="Allgemeiner Einstieg.")
        TextSnippet.objects.create(category="INTRO", jobFamily=self.welt.job_family,
                                   content="Pflege bei uns heißt Zeit für Menschen.")
        entwurf = rule_based_draft("Pflegefachkraft", self.welt.job_family, None)
        self.assertIn("Zeit für Menschen", entwurf["description"])
        self.assertNotIn("Allgemeiner Einstieg", entwurf["description"])

    def test_without_snippets_the_title_still_yields_a_sentence(self):
        entwurf = rule_based_draft("Pflegefachkraft Nachtdienst", None, None)
        self.assertIn("Pflegefachkraft Nachtdienst", entwurf["description"])

    def test_facility_profile_contributes_only_its_first_sentence(self):
        FacilityProfile.objects.create(
            facility=self.welt.facility, slug="klinik",
            description="Haus der Regelversorgung mit 320 Betten. "
                        "Zweiter Satz. Dritter Satz.")
        entwurf = rule_based_draft("Pflegefachkraft", None, self.welt.facility)
        self.assertIn("320 Betten", entwurf["description"])
        self.assertNotIn("Zweiter Satz", entwurf["description"])

    def test_benefits_are_capped_at_four(self):
        namen = [f"Benefit {i}" for i in range(6)]
        entwurf = rule_based_draft("Titel", None, None, benefit_names=namen)
        self.assertIn("Benefit 3", entwurf["description"])
        self.assertNotIn("Benefit 4", entwurf["description"])

    def test_task_snippet_lines_become_list_items(self):
        TextSnippet.objects.create(
            category="TASKS", jobFamily=self.welt.job_family,
            content="- Grundpflege\n- Wunddokumentation\n\n- Übergaben")
        entwurf = rule_based_draft("Titel", self.welt.job_family, None)
        self.assertEqual(entwurf["tasks"],
                         ["Grundpflege", "Wunddokumentation", "Übergaben"])

    def test_the_draft_never_contains_money(self):
        """Konstruktionsbedingt — aber genau deshalb gehört es festgehalten."""
        TextSnippet.objects.create(category="INTRO",
                                   jobFamily=self.welt.job_family,
                                   content="Wir pflegen im Bezugssystem.")
        entwurf = rule_based_draft("Pflegefachkraft", self.welt.job_family,
                                   self.welt.facility)
        self.assertFalse(mentions_money(entwurf["description"]))

    def test_sources_name_what_was_used(self):
        TextSnippet.objects.create(category="INTRO", content="Einstieg.")
        Benefit.objects.create(name="30 Tage Urlaub")
        entwurf = rule_based_draft("Titel", None, None)
        self.assertIn("Einleitungs-Baustein", " ".join(entwurf["quellen"]))
        self.assertIn("Benefits des Hauses", entwurf["quellen"])


class GeldWaechterTestCase(TestCase):
    """Der Kern der Härte-Prüfung: kein erfundener Betrag im Anzeigentext."""

    def test_money_is_recognized_in_its_common_forms(self):
        for text in ("ab 3.500 € im Monat", "EUR 4000", "Vergütung: 3800",
                     "Gehalt: 3.200", "wir zahlen 45.000 im Jahr"):
            self.assertTrue(mentions_money(text), text)

    def test_ordinary_ad_text_is_not_flagged(self):
        for text in ("30 Tage Urlaub", "Station 3 mit 8 Betten",
                     "im Dreischichtsystem", "seit 1998", ""):
            self.assertFalse(mentions_money(text), text)

    def test_an_ai_draft_with_money_is_dropped_entirely(self):
        fallback = {"description": "Sicherer Text.", "tasks": ["A"],
                    "requirements": ["B"], "quellen": []}
        raw = json.dumps({"description": "Wir zahlen 3.500 € brutto.",
                          "tasks": ["Grundpflege"], "requirements": ["Examen"]})
        entwurf, used_ai = validate_ai_draft(raw, fallback)
        self.assertFalse(used_ai)
        self.assertEqual(entwurf, fallback)

    def test_money_in_a_task_line_also_drops_the_draft(self):
        """Verworfen wird die GANZE Fassung, nicht das eine Feld — wer an
        einem Betrag herumschneidet, lässt den halben Satz stehen."""
        fallback = {"description": "Sicher.", "tasks": [], "requirements": [],
                    "quellen": []}
        raw = json.dumps({"description": "Gute Beschreibung.",
                          "tasks": ["Dokumentation (Zulage 200 €)"],
                          "requirements": []})
        _, used_ai = validate_ai_draft(raw, fallback)
        self.assertFalse(used_ai)


class KiFassungValidierungTestCase(TestCase):
    FALLBACK = {"description": "Regel-Text.", "tasks": ["R1"],
                "requirements": ["R2"], "quellen": ["Baustein"]}

    def test_garbage_falls_back(self):
        for raw in ("", "kein json", "[]", json.dumps({"description": 7}),
                    json.dumps({"description": "x", "tasks": "keine Liste",
                                "requirements": []})):
            entwurf, used_ai = validate_ai_draft(raw, self.FALLBACK)
            self.assertFalse(used_ai, raw)
            self.assertEqual(entwurf, self.FALLBACK, raw)

    def test_a_valid_draft_is_accepted_and_capped(self):
        raw = json.dumps({"description": "Flüssiger Text.",
                          "tasks": [f"Aufgabe {i}" for i in range(12)],
                          "requirements": ["Examen"]})
        entwurf, used_ai = validate_ai_draft(raw, self.FALLBACK)
        self.assertTrue(used_ai)
        self.assertEqual(len(entwurf["tasks"]), MAX_ITEMS)
        self.assertIn("KI-Formulierung", entwurf["quellen"])

    def test_empty_ai_lists_keep_the_rule_based_ones(self):
        raw = json.dumps({"description": "Nur Text.", "tasks": [],
                          "requirements": []})
        entwurf, used_ai = validate_ai_draft(raw, self.FALLBACK)
        self.assertTrue(used_ai)
        self.assertEqual(entwurf["tasks"], ["R1"])
        self.assertEqual(entwurf["requirements"], ["R2"])


class EndpointTestCase(TestCase):
    def setUp(self):
        self.welt = make_world()
        self.client.force_login(make_user("entwurf-rec", role="Recruiter"))

    def test_get_is_refused(self):
        self.assertEqual(
            self.client.get(reverse('ats:suggest_job_draft')).status_code, 405)

    def test_a_viewer_cannot_reach_it(self):
        self.client.force_login(make_user("entwurf-viewer", role="Viewer"))
        resp = self.client.post(reverse('ats:suggest_job_draft'), {})
        self.assertIn(resp.status_code, (302, 403))

    def test_the_rule_based_draft_needs_no_ai(self):
        TextSnippet.objects.create(category="INTRO",
                                   jobFamily=self.welt.job_family,
                                   content="Pflege mit Zeit.")
        resp = self.client.post(reverse('ats:suggest_job_draft'), {
            'title': 'Pflegefachkraft', 'job_family': self.welt.job_family.id})
        data = resp.json()
        self.assertIn("Pflege mit Zeit", data['description'])
        self.assertFalse(data['used_ai'])
        self.assertTrue(any("Entgeltband" in n for n in data['notes']))

    def test_selected_benefits_reach_the_draft(self):
        b = Benefit.objects.create(name="Deutschlandticket")
        Benefit.objects.create(name="Nicht gewählt")
        resp = self.client.post(reverse('ats:suggest_job_draft'), {
            'title': 'Titel', 'benefits': [str(b.id)]})
        self.assertIn("Deutschlandticket", resp.json()['description'])
        self.assertNotIn("Nicht gewählt", resp.json()['description'])

    @patch('ats.views.ai.make_ollama_request')
    def test_with_ai_uses_the_validated_answer(self, mock_req):
        mock_req.return_value = (True, {"response": json.dumps({
            "description": "KI-formulierter Text.",
            "tasks": ["Grundpflege"], "requirements": ["Examen"]})})
        resp = self.client.post(reverse('ats:suggest_job_draft'), {
            'title': 'Pflegefachkraft', 'with_ai': '1'})
        data = resp.json()
        self.assertTrue(data['used_ai'])
        self.assertEqual(data['description'], "KI-formulierter Text.")

    @patch('ats.views.ai.make_ollama_request')
    def test_an_unreachable_ai_falls_back_silently(self, mock_req):
        mock_req.side_effect = OSError("kein Ollama")
        TextSnippet.objects.create(category="INTRO", content="Regel-Einstieg.")
        resp = self.client.post(reverse('ats:suggest_job_draft'), {
            'title': 'Titel', 'with_ai': '1'})
        data = resp.json()
        self.assertFalse(data['used_ai'])
        self.assertIn("Regel-Einstieg", data['description'])

    @patch('ats.views.ai.make_ollama_request')
    def test_an_ai_answer_with_money_is_rejected(self, mock_req):
        mock_req.return_value = (True, {"response": json.dumps({
            "description": "Wir zahlen 3.500 € im Monat.",
            "tasks": [], "requirements": []})})
        TextSnippet.objects.create(category="INTRO", content="Sicherer Einstieg.")
        resp = self.client.post(reverse('ats:suggest_job_draft'), {
            'title': 'Titel', 'with_ai': '1'})
        data = resp.json()
        self.assertFalse(data['used_ai'])
        self.assertIn("Sicherer Einstieg", data['description'])
        self.assertNotIn("3.500", data['description'])


class KonvertierungTestCase(TestCase):
    """Die zweite Tür: Bedarfsmeldung → Stelle ohne „Beschreibung folgt"."""

    def setUp(self):
        self.welt = make_world()
        self.client.force_login(make_user("konv-admin", role="HR-Admin"))

    def _convert(self):
        from ..models import StaffingRequest
        req = StaffingRequest.objects.create(
            title="Pflegefachkraft Station 3", facility=self.welt.facility,
            jobFamily=self.welt.job_family, headcount=1,
            justification="Team am Limit", status='ACCEPTED')
        self.client.post(reverse('ats:staffing_requests'),
                         {'form': 'convert', 'request_id': str(req.id),
                          'location': str(self.welt.location.id)})
        req.refresh_from_db()
        return req.convertedJob

    def test_the_placeholder_is_gone(self):
        TextSnippet.objects.create(category="INTRO",
                                   jobFamily=self.welt.job_family,
                                   content="Pflege heißt bei uns Zeit haben.")
        job = self._convert()
        self.assertIsNotNone(job)
        self.assertNotIn("Beschreibung folgt", job.description)
        self.assertIn("Zeit haben", job.description)
        # Der Hinweis auf den Entwurfs-Charakter bleibt
        self.assertIn("Entwurf aus Bedarfsmeldung", job.description)

    def test_cold_start_fills_tasks_from_the_family_snippet(self):
        """Ohne Vorgängerstelle kamen bisher zwei leere Listen heraus."""
        TextSnippet.objects.create(
            category="TASKS", jobFamily=self.welt.job_family,
            content="Grundpflege\nWunddokumentation")
        job = self._convert()
        self.assertEqual(job.tasksJson, ["Grundpflege", "Wunddokumentation"])

    def test_a_predecessor_still_wins_over_the_snippet(self):
        """Das Prozess-Gedächtnis bleibt die bessere Quelle — es ist die
        zuletzt real genutzte Stelle, kein generischer Baustein."""
        from .factories import make_job
        make_job(self.welt, tasksJson=["Aufgabe aus Vorgänger"],
                 requirementsJson=["Anforderung aus Vorgänger"])
        TextSnippet.objects.create(category="TASKS",
                                   jobFamily=self.welt.job_family,
                                   content="Baustein-Aufgabe")
        job = self._convert()
        self.assertEqual(job.tasksJson, ["Aufgabe aus Vorgänger"])
