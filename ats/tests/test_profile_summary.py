"""L2: Bewerber-Steckbrief - faktentreu, deterministisch, KI nur umformulierend.

Deckt ab: K.O.-Kriterien (alle/teilweise + offene), Anforderungs-Erwähnungen
im Anschreiben, Wiederbewerber, Fließtext + Chips, Endpoint mit BOLA, und die
Fail-safe-KI (harte Fakten bleiben, auch wenn die KI umformuliert).
"""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ..models import Application
from ..profile_summary import build_facts, facts_to_bullets, facts_to_text
from .factories import make_application, make_job, make_world
from .utils import make_user

_KO = [
    {"id": "q1", "type": "YES_NO", "question": "Examen?",
     "isMandatory": True, "expectedAnswer": "YES"},
    {"id": "q2", "type": "YES_NO", "question": "Führerschein?",
     "isMandatory": True, "expectedAnswer": "YES"},
]


class BuildFactsTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=_KO,
                            requirementsJson=["Django-Kenntnisse", "PostgreSQL"])

    def test_all_ko_met(self):
        app = make_application(self.job, screeningAnswersJson={
            "Examen?": "YES", "Führerschein?": "YES"})
        f = build_facts(app)
        self.assertEqual((f.ko_total, f.ko_met), (2, 2))
        self.assertEqual(f.ko_missing, [])
        self.assertIn("Erfüllt alle 2 Pflichtkriterien", facts_to_text(f))

    def test_partial_ko_lists_missing(self):
        app = make_application(self.job, screeningAnswersJson={
            "Examen?": "YES", "Führerschein?": "NO"})
        f = build_facts(app)
        self.assertEqual((f.ko_met, f.ko_total), (1, 2))
        self.assertEqual(f.ko_missing, ["Führerschein?"])
        self.assertIn("offen: Führerschein?", facts_to_text(f))

    def test_requirement_mentions_in_cover(self):
        app = make_application(
            self.job, screeningAnswersJson={"Examen?": "YES"},
            coverLetterTxt="Ich bringe Erfahrung mit Django und PostgreSQL mit.")
        f = build_facts(app)
        self.assertEqual(len(f.req_hits), 2)
        self.assertIn("greift 2 von 2 Anforderungen auf", facts_to_text(f))

    def test_no_cover_is_flagged(self):
        app = make_application(self.job, coverLetterTxt="")
        f = build_facts(app)
        self.assertFalse(f.has_cover)
        self.assertIn("Kein Anschreiben", " ".join(facts_to_bullets(f)))

    def test_repeat_applicant_counted(self):
        # Dieselbe Person, zwei Bewerbungen (nicht zwei Bewerber-Datensaetze).
        app1 = make_application(self.job, first_name="Rea", last_name="P")
        app2 = Application.objects.create(
            applicant=app1.applicant, jobPosting=self.job, status='NEW')
        f = build_facts(app2)
        self.assertGreaterEqual(f.repeat_count, 2)
        self.assertIn("Bewirbt sich erneut", " ".join(facts_to_bullets(f)))


class SummaryEndpointTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=_KO,
                            requirementsJson=["Django-Kenntnisse"])
        self.rec = make_user("ps-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.app = make_application(self.job, first_name="Nina", last_name="K",
                                    screeningAnswersJson={"Examen?": "YES",
                                                          "Führerschein?": "YES"})
        self.url = reverse('ats:application_summary', args=[self.app.id])

    def _enable_ai(self):
        from ..models import SystemSetting
        SystemSetting.objects.update_or_create(
            key='AI_SCORING_ENABLED', defaults={'value': '1'})

    def test_returns_deterministic_when_ai_off(self):
        # AI-Opt-in aus (Default) -> sofort deterministisch, kein Ollama-Aufruf
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data['used_ai'])
        self.assertIn("Erfüllt alle 2 Pflichtkriterien", data['text'])
        self.assertTrue(data['bullets'])

    def test_falls_back_when_ai_on_but_unreachable(self):
        self._enable_ai()
        with patch('ats.views.ai.make_ollama_request',
                   side_effect=Exception("no ollama")):
            r = self.client.get(self.url)
        data = r.json()
        self.assertFalse(data['used_ai'])
        self.assertIn("Erfüllt alle 2 Pflichtkriterien", data['text'])

    def test_ai_rephrases_but_facts_chips_remain(self):
        self._enable_ai()
        fake = (True, {"response": "Nina erfüllt alle Kriterien souverän."})
        with patch('ats.views.ai.make_ollama_request', return_value=fake):
            r = self.client.get(self.url)
        data = r.json()
        self.assertTrue(data['used_ai'])
        self.assertIn("souverän", data['text'])
        # Chips bleiben die harten, deterministischen Fakten
        self.assertIn("Erfüllt alle 2 Pflichtkriterien", " ".join(data['bullets']))

    def test_bola_foreign_application_denied(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Kiel")
        fjob = make_job(self.world, title="Fremd", location=other)
        fapp = make_application(fjob)
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.get(
            reverse('ats:application_summary', args=[fapp.id]))
        self.assertEqual(r.status_code, 404)

    def test_no_message_created(self):
        before = Application.objects.count()
        with patch('ats.views.ai.make_ollama_request',
                   side_effect=Exception("x")):
            self.client.get(self.url)
        self.assertEqual(Application.objects.count(), before)
