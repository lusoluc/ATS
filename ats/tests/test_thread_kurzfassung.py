"""Verlaufs-Kurzfassung: den Schriftwechsel in Sekunden erfassen.

Wer einen Fall übernimmt — Urlaubsvertretung, Krankheitsfall — las bisher den
ganzen Nachrichtenverlauf von unten nach oben, um drei Fragen zu beantworten:
Wie viel wurde geschrieben, wer ist am Zug, worum ging es zuletzt? Der
Steckbrief beantwortete das für die Bewerbung, nicht für den Schriftwechsel.

Wie beim Steckbrief gilt: Die Fakten sind deterministisch; die KI darf den
Text nur umformulieren, und ohne KI bleibt der deterministische Text.
"""
import datetime
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import Message, SystemSetting
from ..thread_summary import build_verlauf, verlauf_text
from .factories import make_application, make_job, make_world
from .utils import make_user


def _nachricht(app, direction, text="Hallo", vor_tagen=0):
    m = Message.objects.create(application=app, direction=direction,
                               content=text)
    if vor_tagen:
        Message.objects.filter(id=m.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=vor_tagen))
    return m


class FaktenTestCase(TestCase):
    def setUp(self):
        self.app = make_application(make_job(make_world()))

    def test_no_messages_means_no_summary(self):
        self.assertIsNone(build_verlauf(self.app))

    def test_counts_and_directions(self):
        _nachricht(self.app, 'INBOUND', vor_tagen=5)
        _nachricht(self.app, 'OUTBOUND', vor_tagen=4)
        _nachricht(self.app, 'INBOUND', vor_tagen=1)
        f = build_verlauf(self.app)
        self.assertEqual((f.gesamt, f.eingehend, f.ausgehend), (3, 2, 1))
        self.assertEqual(f.letzte_richtung, 'INBOUND')

    def test_an_unanswered_question_counts_its_days(self):
        _nachricht(self.app, 'INBOUND', "Wann höre ich von Ihnen?", vor_tagen=6)
        f = build_verlauf(self.app)
        self.assertEqual(f.wartet_seit_tagen, 6)
        self.assertIn("seit 6 Tagen unbeantwortet", verlauf_text(f))

    def test_after_our_reply_the_applicant_is_at_bat(self):
        _nachricht(self.app, 'INBOUND', vor_tagen=3)
        _nachricht(self.app, 'OUTBOUND', vor_tagen=1)
        f = build_verlauf(self.app)
        self.assertIsNone(f.wartet_seit_tagen)
        self.assertIn("am Zug", verlauf_text(f))

    def test_the_last_intent_is_named(self):
        _nachricht(self.app, 'INBOUND',
                   "Können wir den Termin verschieben? Der Dienstplan kam dazwischen.")
        f = build_verlauf(self.app)
        self.assertEqual(f.letztes_anliegen, "Termin")
        self.assertIn("Anliegen zuletzt: Termin.", verlauf_text(f))

    def test_the_excerpt_is_capped_and_single_line(self):
        _nachricht(self.app, 'INBOUND', "Zeile eins\nZeile zwei  " + "x" * 300)
        f = build_verlauf(self.app)
        self.assertLessEqual(len(f.auszug), 161)
        self.assertNotIn("\n", f.auszug)
        self.assertTrue(f.auszug.endswith("…"))

    def test_the_text_adds_no_information(self):
        """Der Satzbau ist das Einzige, was verlauf_text hinzufügt — jede
        Zahl im Text muss aus den Fakten stammen."""
        _nachricht(self.app, 'INBOUND', vor_tagen=4)
        _nachricht(self.app, 'OUTBOUND', vor_tagen=2)
        f = build_verlauf(self.app)
        text = verlauf_text(f)
        import re
        zahlen = {z for z in re.findall(r"\b\d+\b", text)
                  if len(z) <= 2}          # Datumsteile (2026 etc.) ausnehmen
        erlaubt = {str(f.gesamt), str(f.eingehend), str(f.ausgehend)}
        erlaubt |= {t.lstrip('0') or '0' for f_ in (f.erste_am, f.letzte_am)
                    for t in timezone.localtime(f_).strftime('%d %m').split()}
        erlaubt |= {timezone.localtime(f_).strftime('%d')
                    for f_ in (f.erste_am, f.letzte_am)}
        erlaubt |= {timezone.localtime(f_).strftime('%m')
                    for f_ in (f.erste_am, f.letzte_am)}
        self.assertLessEqual(zahlen, erlaubt,
                             f"Zahl im Text ohne Quelle in den Fakten: {text}")


class NachrichtenSeiteTestCase(TestCase):
    """Tür 1: die Antworten-Seite aus dem Postfach."""

    def setUp(self):
        self.app = make_application(make_job(make_world()))
        self.client.force_login(make_user("verlauf-rec", role="Recruiter"))

    def test_the_thread_page_shows_the_summary(self):
        _nachricht(self.app, 'INBOUND', "Wann gibt es Neuigkeiten?", vor_tagen=3)
        resp = self.client.get(
            reverse('ats:application_messages', args=[self.app.id]))
        self.assertContains(resp, "Kurzfassung")
        self.assertContains(resp, "unbeantwortet")
        self.assertContains(resp, "Wann gibt es Neuigkeiten?")

    def test_without_messages_there_is_no_summary_box(self):
        resp = self.client.get(
            reverse('ats:application_messages', args=[self.app.id]))
        self.assertNotContains(resp, "Kurzfassung")


class SteckbriefTestCase(TestCase):
    """Tür 2: die Karte im Board (application_summary)."""

    def setUp(self):
        self.app = make_application(make_job(make_world()))
        self.client.force_login(make_user("verlauf-adm", role="HR-Admin"))

    def _summary(self):
        return self.client.get(reverse('ats:application_summary',
                                       args=[self.app.id])).json()

    def test_the_summary_carries_the_thread_facts(self):
        _nachricht(self.app, 'INBOUND', "Ich habe eine Frage.", vor_tagen=2)
        data = self._summary()
        self.assertIn('verlauf', data)
        self.assertEqual(data['verlauf']['wartet_seit_tagen'], 2)
        self.assertFalse(data['verlauf']['used_ai'])

    def test_without_messages_the_key_is_absent(self):
        self.assertNotIn('verlauf', self._summary())

    def test_ai_off_means_no_ollama_contact_at_all(self):
        """Das Opt-in-Versprechen: ohne Freischaltung kein Verbindungsversuch."""
        _nachricht(self.app, 'INBOUND', "Frage.")
        with patch('ats.views.ai.make_ollama_request') as mock_req:
            data = self._summary()
        mock_req.assert_not_called()
        self.assertFalse(data['verlauf']['used_ai'])

    def test_with_ai_the_text_is_rephrased_but_the_excerpt_is_verbatim(self):
        SystemSetting.objects.create(key='AI_SCORING_ENABLED', value='1')
        _nachricht(self.app, 'INBOUND', "Originaler Wortlaut der Frage.")
        with patch('ats.views.ai.make_ollama_request',
                   return_value=(True, {"response": "Umformulierter Text."})):
            data = self._summary()
        self.assertTrue(data['verlauf']['used_ai'])
        self.assertEqual(data['verlauf']['text'], "Umformulierter Text.")
        # Der Auszug ist Zitat, kein KI-Material
        self.assertIn("Originaler Wortlaut", data['verlauf']['auszug'])

    def test_a_failing_ai_keeps_the_deterministic_text(self):
        SystemSetting.objects.create(key='AI_SCORING_ENABLED', value='1')
        _nachricht(self.app, 'INBOUND', "Frage.", vor_tagen=1)
        with patch('ats.views.ai.make_ollama_request',
                   side_effect=OSError("kein Ollama")):
            data = self._summary()
        self.assertFalse(data['verlauf']['used_ai'])
        self.assertIn("unbeantwortet", data['verlauf']['text'])


class ZugriffTestCase(TestCase):
    def test_the_thread_page_is_scoped(self):
        """BOLA: fremder Bereich -> 404, wie ueberall."""
        from ..models import UserScope
        welt = make_world()
        app = make_application(make_job(welt))
        fremd = make_user("verlauf-fremd", role="Recruiter")
        scope, _ = UserScope.objects.get_or_create(user=fremd)
        scope.full_access = False
        scope.save()
        self.client.force_login(fremd)
        resp = self.client.get(
            reverse('ats:application_messages', args=[app.id]))
        self.assertEqual(resp.status_code, 404)
