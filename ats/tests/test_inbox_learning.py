"""Stufe 5: lernende Optimierung der Einsortierung aus HR-Korrekturen.

Deckt ab: Ehrlichkeits-Gate (>= MIN_EVIDENCE, eindeutig), mehrdeutige Woerter
werden verworfen, gelerntes Wort verbessert analyze(), Sofort-Korrektur je
Nachricht wirkt vor dem Gate, der Reclassify-Endpoint schreibt das Signal +
BOLA, und - Sicherheit - Lernen weitet die Auto-Antwort NIE aus.
"""
from django.test import TestCase
from django.urls import reverse

from ..audit import write_audit
from ..inbox_intents import INTENT_DOCUMENTS, INTENT_STATUS, analyze
from ..inbox_learning import (
    MIN_EVIDENCE,
    RECLASSIFY_ACTION,
    learned_keywords,
    message_overrides,
)
from ..models import AuditLog, Message
from .factories import make_application, make_job, make_world
from .utils import make_user


def _correction(intent, excerpt, message_id="m"):
    write_audit(RECLASSIFY_ACTION, application_id="a",
                message_id=message_id, to_intent=intent, excerpt=excerpt)


class LearnedKeywordsTestCase(TestCase):
    def test_gate_requires_min_evidence(self):
        # zweimal reicht nicht (MIN_EVIDENCE = 3)
        for _ in range(MIN_EVIDENCE - 1):
            _correction(INTENT_DOCUMENTS, "Frage zur Approbationsurkunde")
        self.assertNotIn("approbationsurkunde",
                         learned_keywords().get(INTENT_DOCUMENTS, []))

    def test_learns_after_enough_evidence(self):
        for _ in range(MIN_EVIDENCE):
            _correction(INTENT_DOCUMENTS, "Frage zur Approbationsurkunde")
        self.assertIn("approbationsurkunde",
                      learned_keywords().get(INTENT_DOCUMENTS, []))

    def test_ambiguous_word_is_rejected(self):
        # "hospiz" mal zu DOCUMENTS, mal zu STATUS korrigiert -> mehrdeutig
        for _ in range(MIN_EVIDENCE):
            _correction(INTENT_DOCUMENTS, "Rueckfrage hospiz unterlagen")
        _correction(INTENT_STATUS, "hospiz stand")
        learned = learned_keywords()
        self.assertNotIn("hospiz", learned.get(INTENT_DOCUMENTS, []))
        self.assertNotIn("hospiz", learned.get(INTENT_STATUS, []))

    def test_learned_keyword_improves_analyze(self):
        text = "Wann ist die Approbationsurkunde faellig?"
        # vorher: kein DOCUMENTS-Stichwort -> nicht DOCUMENTS
        self.assertNotEqual(analyze(text).bucket, INTENT_DOCUMENTS)
        for _ in range(MIN_EVIDENCE):
            _correction(INTENT_DOCUMENTS, "Frage zur Approbationsurkunde")
        self.assertEqual(
            analyze(text, extra_keywords=learned_keywords()).bucket,
            INTENT_DOCUMENTS)


class MessageOverrideTestCase(TestCase):
    def test_single_correction_overrides_immediately(self):
        _correction(INTENT_DOCUMENTS, "irgendwas", message_id="msg-1")
        ov = message_overrides(["msg-1", "msg-2"])
        self.assertEqual(ov.get("msg-1"), INTENT_DOCUMENTS)
        self.assertNotIn("msg-2", ov)

    def test_latest_correction_wins(self):
        _correction(INTENT_DOCUMENTS, "x", message_id="msg-1")
        _correction(INTENT_STATUS, "x", message_id="msg-1")
        self.assertEqual(message_overrides(["msg-1"])["msg-1"], INTENT_STATUS)


class ReclassifyViewTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Pflege Station 1")
        self.rec = make_user("rc-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.app = make_application(self.job, first_name="Anna", last_name="Berg")
        self.msg = Message.objects.create(
            application=self.app, direction='INBOUND',
            content="Etwas ganz Ungewöhnliches.")
        self.url = reverse('ats:reclassify_message')

    def test_writes_learning_signal(self):
        self.client.post(self.url, data={
            'message_id': str(self.msg.id), 'to_intent': INTENT_DOCUMENTS})
        self.assertTrue(AuditLog.objects.filter(
            action=RECLASSIFY_ACTION).exists())

    def test_moves_message_in_inbox(self):
        self.client.post(self.url, data={
            'message_id': str(self.msg.id), 'to_intent': INTENT_DOCUMENTS})
        r = self.client.get(reverse('ats:inbox'))
        # Anna erscheint jetzt im Unterlagen-Cluster (Sofort-Korrektur)
        self.assertContains(r, "Anna Berg")
        self.assertContains(r, "Unterlagen")

    def test_bola_foreign_message_denied(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Kiel")
        foreign_job = make_job(self.world, title="Fremd", location=other)
        fapp = make_application(foreign_job)
        fmsg = Message.objects.create(application=fapp, direction='INBOUND',
                                      content="fremd")
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.post(self.url, data={
            'message_id': str(fmsg.id), 'to_intent': INTENT_DOCUMENTS})
        self.assertEqual(r.status_code, 404)

    def test_learning_never_expands_auto_reply(self):
        """Auch massenhaft gelernte Stichwoerter erweitern den auto-sicheren
        Kreis NICHT - er ist eine Konstante."""
        from ..inbox_intents import AUTO_SAFE_INTENTS
        before = set(AUTO_SAFE_INTENTS)
        for _ in range(MIN_EVIDENCE + 2):
            _correction(INTENT_DOCUMENTS, "Approbationsurkunde nachweis")
        learned_keywords()
        self.assertEqual(set(AUTO_SAFE_INTENTS), before)
        # eine gelernte DOCUMENTS-Frage bleibt nicht auto_safe
        a = analyze("Wann ist die Approbationsurkunde faellig?",
                    extra_keywords=learned_keywords())
        self.assertFalse(a.auto_safe)
