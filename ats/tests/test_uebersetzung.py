"""Englische Fassung der Stellenanzeige — die Brücke, bis das Deutsch reicht.

Zielgruppe des Hauses sind auch internationale Pflegekräfte. Die Leichte
Sprache hat ihren Pflegeweg seit B5; eine englische Fassung gab es nicht.
Gleiche Mechanik, gleiche Ehrlichkeit: leer = kein Umschalter, der KI-Entwurf
landet im Textfeld zur Prüfung, nie ungesehen auf der Anzeige — und anders
als bei der Leichten Sprache gibt es KEINEN deterministischen Fallback, weil
eine Übersetzung sich nicht durch Satzkürzung ersetzen lässt.
"""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ..models import JobPosting, SystemSetting
from .factories import make_job, make_world
from .utils import make_user


class EditorTestCase(TestCase):
    def setUp(self):
        self.welt = make_world()
        self.client.force_login(make_user("en-rec", role="Recruiter"))

    def _post_job(self, **extra):
        daten = {'title': 'Pflegefachkraft', 'description': 'Beschreibung.',
                 'tasks': 'Aufgabe', 'requirements': 'Anforderung',
                 'facility': self.welt.facility.id,
                 'location': self.welt.location.id,
                 'job_family': self.welt.job_family.id}
        daten.update(extra)
        return self.client.post(reverse('ats:create_job'), daten)

    def test_the_english_version_is_saved(self):
        self._post_job(description_english="We are looking for a nurse.")
        job = JobPosting.objects.get(title='Pflegefachkraft')
        self.assertEqual(job.descriptionEnglish, "We are looking for a nurse.")

    def test_an_empty_field_stays_none_not_empty_string(self):
        self._post_job(description_english="")
        job = JobPosting.objects.get(title='Pflegefachkraft')
        self.assertIsNone(job.descriptionEnglish)

    def test_an_absent_field_keeps_the_existing_version(self):
        """Gleiche Semantik wie die Leichte Sprache: Formulare, die das Feld
        nicht mitsenden (etwa der Schnell-Toggle), löschen nichts."""
        job = make_job(self.welt, descriptionEnglish="Existing version.")
        self.client.post(reverse('ats:create_job'), {
            'job_id': str(job.id), 'title': job.title,
            'description': 'Neu.', 'tasks': 'A', 'requirements': 'B',
            'facility': self.welt.facility.id,
            'location': self.welt.location.id,
            'job_family': self.welt.job_family.id})
        job.refresh_from_db()
        self.assertEqual(job.descriptionEnglish, "Existing version.")


class DetailSeiteTestCase(TestCase):
    def setUp(self):
        self.welt = make_world()

    def test_without_a_version_there_is_no_english_button(self):
        job = make_job(self.welt, description="Text.")
        resp = self.client.get(reverse('ats:job_detail', args=[job.id]))
        self.assertNotContains(resp, "descBtnEnglish")

    def test_the_version_renders_with_a_language_attribute(self):
        """WCAG 3.1.2: Ohne lang="en" liest ein deutscher Screenreader den
        englischen Text mit deutschen Ausspracheregeln vor."""
        job = make_job(self.welt, description="Text.",
                       descriptionEnglish="We are looking for you.")
        resp = self.client.get(reverse('ats:job_detail', args=[job.id]))
        self.assertContains(resp, "descBtnEnglish")
        self.assertContains(resp, 'id="descEnglish" lang="en"')
        self.assertContains(resp, "We are looking for you.")

    def test_both_versions_can_coexist(self):
        job = make_job(self.welt, description="Text.",
                       descriptionEasy="Einfacher Text.",
                       descriptionEnglish="English text.")
        resp = self.client.get(reverse('ats:job_detail', args=[job.id]))
        self.assertContains(resp, "descBtnEasy")
        self.assertContains(resp, "descBtnEnglish")


class UebersetzungsEndpointTestCase(TestCase):
    def setUp(self):
        self.client.force_login(make_user("en-rec2", role="Recruiter"))

    def test_get_is_refused(self):
        resp = self.client.get(reverse('ats:gemma_translate_english'))
        self.assertEqual(resp.status_code, 405)

    def test_a_viewer_cannot_reach_it(self):
        self.client.force_login(make_user("en-viewer", role="Viewer"))
        resp = self.client.post(reverse('ats:gemma_translate_english'),
                                {'text': 'Hallo'})
        self.assertIn(resp.status_code, (302, 403))

    def test_empty_text_is_refused(self):
        resp = self.client.post(reverse('ats:gemma_translate_english'), {})
        self.assertFalse(resp.json()['success'])

    @patch('ats.views.ai.make_ollama_request')
    def test_a_successful_translation_is_returned(self, mock_req):
        mock_req.return_value = (True, {"response": "We are looking for you."})
        resp = self.client.post(reverse('ats:gemma_translate_english'),
                                {'text': 'Wir suchen Sie.'})
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['result'], "We are looking for you.")

    @patch('ats.views.ai.make_ollama_request')
    def test_no_silent_fallback_when_the_ai_is_down(self, mock_req):
        """Der Unterschied zur Leichten Sprache: Es gibt nichts Ehrliches,
        was man ohne KI liefern könnte — also wird das gesagt, statt Deutsch
        als Englisch auszugeben."""
        mock_req.side_effect = OSError("kein Ollama")
        resp = self.client.post(reverse('ats:gemma_translate_english'),
                                {'text': 'Wir suchen Sie.'})
        data = resp.json()
        self.assertFalse(data['success'])
        self.assertIn("unverändert", data['error'])

    @patch('ats.views.ai.make_ollama_request')
    def test_the_maintained_prompt_wins_over_the_default(self, mock_req):
        """Dieselbe Asymmetrie wie einst bei der Leichten Sprache vermeiden:
        Ein pflegbarer Prompt, den das System nie liest, ist ein totes
        Angebot."""
        SystemSetting.objects.create(key='AI_ENGLISH_PROMPT',
                                     value='MEIN EIGENES REGELWERK')
        mock_req.return_value = (True, {"response": "Ok."})
        self.client.post(reverse('ats:gemma_translate_english'),
                         {'text': 'Hallo'})
        payload = mock_req.call_args.args[1]
        self.assertIn('MEIN EIGENES REGELWERK', payload['prompt'])

    @patch('ats.views.ai.make_ollama_request')
    def test_the_call_is_logged_with_its_outcome(self, mock_req):
        from ..models import AuditLog
        mock_req.return_value = (True, {"response": "Fine."})
        self.client.post(reverse('ats:gemma_translate_english'),
                         {'text': 'Hallo'})
        self.assertTrue(AuditLog.objects.filter(
            action='AI_EXECUTION', userId='Englische Fassung').exists())


class KiZentraleTestCase(TestCase):
    """Der Prompt ist pflegbar UND wird gespeichert — kein totes Angebot."""

    def setUp(self):
        self.client.force_login(make_user("en-admin", role="HR-Admin"))

    def test_saving_the_settings_keeps_the_english_prompt(self):
        self.client.post(reverse('ats:save_ai_settings'), {
            'AI_TONE': 'EMPATHETIC',
            'AI_ENGLISH_PROMPT': 'Übersetze knapp und freundlich.'})
        row = SystemSetting.objects.get(key='AI_ENGLISH_PROMPT')
        self.assertEqual(row.value, 'Übersetze knapp und freundlich.')

    def test_the_ki_page_offers_the_field(self):
        resp = self.client.get(reverse('ats:ki_page'))
        self.assertContains(resp, 'AI_ENGLISH_PROMPT')
