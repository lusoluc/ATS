"""Stufe 4: Auto-Antwort auf sichere, eindeutige Anliegen + Governance.

Sicherheitskritisch. Deckt ab: ab Werk an fuer Stand/Ablauf; NIE fuer
Entscheidungs-/Nicht-Kommunikations-Anliegen (Unterlagen/Termin/Rueckzug),
NIE fuer zusammengesetzte Nachrichten, Hauptschalter aus = nichts,
Feineinstellung je Anliegen, harte Filterung nicht-sicherer Anliegen aus der
Einstellung, Transparenz-Hinweis + Audit, und der Governance-Speicherpfad.
"""
from django.test import TestCase
from django.urls import reverse

from ..auto_reply import (
    AUTO_REPLY_ENABLED_KEY,
    AUTO_REPLY_INTENTS_KEY,
    enabled_intents,
    maybe_auto_reply,
)
from ..models import AuditLog, SystemSetting, TextSnippet
from .factories import make_application, make_job, make_world
from .utils import make_user


def _set(key, value):
    SystemSetting.objects.update_or_create(key=key, defaults={'value': value})


class MaybeAutoReplyTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Pflege Station 1")
        self.app = make_application(self.job, first_name="Anna", last_name="Berg",
                                    status="IN_REVIEW")

    def _last_out(self):
        return self.app.messages.filter(direction='OUTBOUND').first()

    def test_default_answers_status(self):
        """Ab Werk: eine saubere Stand-Frage wird automatisch beantwortet."""
        self.assertTrue(maybe_auto_reply(self.app, "Wie ist der Stand?"))
        out = self._last_out()
        self.assertIsNotNone(out)
        self.assertIn("Anna", out.content)
        self.assertIn("automatisch erstellt", out.content)  # Transparenz
        self.assertEqual(
            AuditLog.objects.filter(action='AUTO_REPLY_SENT').count(), 1)

    def test_default_answers_process(self):
        self.assertTrue(maybe_auto_reply(self.app, "Wie geht es weiter?"))

    def test_never_answers_documents(self):
        """Unterlagen ist kein reines Kommunikations-Anliegen -> nie auto."""
        self.assertFalse(maybe_auto_reply(
            self.app, "Sind meine Unterlagen vollständig angekommen?"))
        self.assertIsNone(self._last_out())

    def test_never_answers_scheduling(self):
        self.assertFalse(maybe_auto_reply(
            self.app, "Können wir den Termin verschieben?"))

    def test_never_answers_withdrawal(self):
        self.assertFalse(maybe_auto_reply(
            self.app, "Ich möchte meine Bewerbung zurückziehen."))

    def test_never_answers_compound(self):
        """Stand-Frage + unerkannte Zusatzfrage -> Mensch, nie auto."""
        self.assertFalse(maybe_auto_reply(
            self.app, "Wie ist der Stand? Bieten Sie eine Betriebswohnung an?"))
        self.assertIsNone(self._last_out())

    def test_master_switch_off_blocks_all(self):
        _set(AUTO_REPLY_ENABLED_KEY, '0')
        self.assertFalse(maybe_auto_reply(self.app, "Wie ist der Stand?"))

    def test_per_intent_selection(self):
        _set(AUTO_REPLY_INTENTS_KEY, '["PROCESS"]')
        self.assertFalse(maybe_auto_reply(self.app, "Wie ist der Stand?"))
        self.assertTrue(maybe_auto_reply(self.app, "Wie geht es weiter?"))

    def test_unsafe_intent_in_setting_is_filtered(self):
        """Selbst wenn jemand ein Entscheidungs-Anliegen einstellt, greift es
        nicht - enabled_intents schneidet auf die sicheren zu."""
        _set(AUTO_REPLY_INTENTS_KEY, '["DOCUMENTS", "WITHDRAWAL"]')
        self.assertEqual(enabled_intents(), set())
        self.assertFalse(maybe_auto_reply(
            self.app, "Sind meine Unterlagen angekommen?"))

    def test_uses_saved_snippet_template(self):
        TextSnippet.objects.create(
            category='REPLY_STATUS',
            content='Hausvorlage fuer [[Vorname]] zur Stelle [[Stelle]].')
        maybe_auto_reply(self.app, "Wie ist der Stand?")
        self.assertIn("Hausvorlage fuer Anna", self._last_out().content)


class GovernanceSaveTestCase(TestCase):
    def setUp(self):
        self.admin = make_user("ar-admin", role="HR-Admin")
        self.client.force_login(self.admin)
        self.url = reverse('ats:save_auto_reply_settings')

    def test_saves_and_filters_unsafe(self):
        self.client.post(self.url, data={
            'auto_reply_enabled': '1',
            'auto_reply_intents': ['STATUS', 'DOCUMENTS', 'WITHDRAWAL']})
        import json
        stored = json.loads(SystemSetting.objects.get(
            key=AUTO_REPLY_INTENTS_KEY).value)
        self.assertIn('STATUS', stored)
        self.assertNotIn('DOCUMENTS', stored)   # nicht sicher -> gefiltert
        self.assertNotIn('WITHDRAWAL', stored)

    def test_master_off_persists(self):
        self.client.post(self.url, data={'auto_reply_intents': ['STATUS']})
        self.assertEqual(SystemSetting.objects.get(
            key=AUTO_REPLY_ENABLED_KEY).value, '0')
        self.assertEqual(enabled_intents(), set())

    def test_requires_admin(self):
        self.client.logout()
        rec = make_user("ar-rec", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.post(self.url, data={'auto_reply_enabled': '1'})
        self.assertIn(r.status_code, (302, 403))
        # Recruiter darf die Governance nicht aendern
        self.assertFalse(SystemSetting.objects.filter(
            key=AUTO_REPLY_ENABLED_KEY, value='1').exists())
