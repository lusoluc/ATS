"""Anliegen-Erkennung fuers Sammel-Postfach.

Deckt ab: jede Kategorie wird erkannt, Umlaut-Toleranz, Ueberlappung
(termin absagen -> SCHEDULING, bewerbung zurueckziehen -> WITHDRAWAL), der
Catch-all fuer Unerkanntes, und - sicherheitskritisch - die Erkennung
ZUSAMMENGESETZTER Nachrichten (Standard-Frage + Zusatz) als individuelle
Pruefung, die nie auto_safe ist.
"""
from django.test import SimpleTestCase

from ..inbox_intents import (
    INTENT_DOCUMENTS,
    INTENT_OTHER,
    INTENT_PROCESS,
    INTENT_SCHEDULING,
    INTENT_STATUS,
    INTENT_WITHDRAWAL,
    analyze,
    classify_rule_based,
)


class ClassifyTestCase(SimpleTestCase):
    def test_status(self):
        self.assertEqual(classify_rule_based(
            "Guten Tag, bis wann kann ich mit einer Rückmeldung rechnen?"),
            INTENT_STATUS)

    def test_documents(self):
        self.assertEqual(classify_rule_based(
            "Sind meine Unterlagen vollständig bei Ihnen angekommen?"),
            INTENT_DOCUMENTS)

    def test_scheduling(self):
        self.assertEqual(classify_rule_based(
            "Ich muss den Termin leider verschieben."),
            INTENT_SCHEDULING)

    def test_process(self):
        self.assertEqual(classify_rule_based(
            "Wie geht es weiter, was sind die nächsten Schritte?"),
            INTENT_PROCESS)

    def test_withdrawal(self):
        self.assertEqual(classify_rule_based(
            "Ich möchte meine Bewerbung zurückziehen."),
            INTENT_WITHDRAWAL)

    def test_unknown_is_other(self):
        self.assertEqual(classify_rule_based(
            "Ihr Empfangsbereich hat eine wunderschöne Zimmerpflanze!"),
            INTENT_OTHER)

    def test_umlaut_tolerance(self):
        # Ohne Umlaute geschrieben - muss trotzdem greifen.
        self.assertEqual(classify_rule_based(
            "Wann hoere ich von Ihnen, gibt es schon eine Rueckmeldung?"),
            INTENT_STATUS)

    def test_overlap_termin_absagen_is_scheduling(self):
        self.assertEqual(classify_rule_based(
            "Leider muss ich den Termin am Freitag absagen."),
            INTENT_SCHEDULING)

    def test_overlap_bewerbung_zurueck_is_withdrawal(self):
        self.assertEqual(classify_rule_based(
            "Ich ziehe meine Bewerbung zurück, kein Interesse mehr."),
            INTENT_WITHDRAWAL)


class AnalyzeTestCase(SimpleTestCase):
    def test_clean_status_is_auto_safe(self):
        a = analyze("Bis wann bekomme ich Bescheid?")
        self.assertEqual(a.bucket, INTENT_STATUS)
        self.assertFalse(a.compound)
        self.assertTrue(a.auto_safe)

    def test_compound_marker_routes_to_other(self):
        """Standard-Frage + 'außerdem …' -> individuelle Pruefung, nicht auto."""
        a = analyze("Bis wann höre ich von Ihnen? Außerdem: bieten Sie auch "
                    "eine Betriebswohnung an?")
        self.assertEqual(a.bucket, INTENT_OTHER)
        self.assertTrue(a.compound)
        self.assertFalse(a.auto_safe)

    def test_two_distinct_intents_routes_to_other(self):
        a = analyze("Sind meine Unterlagen angekommen und wann ist der Termin?")
        self.assertTrue(a.compound)
        self.assertEqual(a.bucket, INTENT_OTHER)
        self.assertFalse(a.auto_safe)

    def test_multiple_questions_routes_to_other(self):
        a = analyze("Wie ist der Stand? Und noch etwas anderes?")
        self.assertTrue(a.compound)
        self.assertFalse(a.auto_safe)

    def test_very_long_message_routes_to_other(self):
        long_text = "Wie ist der Stand? " + ("x" * 650)
        a = analyze(long_text)
        self.assertTrue(a.compound)
        self.assertFalse(a.auto_safe)

    def test_decision_like_intent_never_auto_safe(self):
        # Rueckzug ist kein reines Kommunikations-Anliegen -> nie auto.
        a = analyze("Ich möchte meine Bewerbung zurückziehen.")
        self.assertEqual(a.bucket, INTENT_WITHDRAWAL)
        self.assertFalse(a.auto_safe)

    def test_unknown_is_other_and_not_auto(self):
        a = analyze("Können Sie mir die Anfahrt mit dem Fahrrad beschreiben?")
        self.assertEqual(a.bucket, INTENT_OTHER)
        self.assertFalse(a.auto_safe)
        self.assertTrue(a.reason)

    def test_ai_hook_only_used_when_rule_finds_nothing(self):
        called = {"n": 0}

        def fake_ai(_text: str):
            called["n"] += 1
            return INTENT_STATUS

        # Klarer Status-Text: Regel greift, KI darf NICHT befragt werden.
        analyze("Bis wann höre ich von Ihnen?", ai_classifier=fake_ai)
        self.assertEqual(called["n"], 0)

    def test_ai_hook_refines_unknown(self):
        def fake_ai(_text: str):
            return INTENT_PROCESS

        a = analyze("Mich würde die weitere Vorgehensweise interessieren.",
                    ai_classifier=fake_ai)
        self.assertEqual(a.primary, INTENT_PROCESS)
        self.assertTrue(a.used_ai)
