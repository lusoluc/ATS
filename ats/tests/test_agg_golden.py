"""AGG-Prüfstrecke: die Hälfte, die ohne laufende KI prüfbar ist.

Der KI-Teil (`manage.py agg_eval`) braucht ein erreichbares Ollama und gehört
an den Prompt-/Modellwechsel. Was hier steht, läuft bei JEDEM Testlauf mit:

1. Taugt das Prüfset überhaupt? Wenn eine Variante versehentlich auch die
   Qualifikation ändert, misst die Strecke Fachlichkeit statt Merkmal — und
   bestünde fröhlich weiter. Ein Prüfset ohne Selbstprüfung ist ein Placebo.
2. Ist die transparente Stufe blind für die Merkmale? Das gelernte Scoring
   arbeitet auf einem Merkmalsvektor; der muss über alle Varianten identisch
   sein. Diese Zusage steht seit Langem im Modul-Kopf von `scoring.py` —
   geprüft hat sie niemand.
3. Kommt ein geschütztes Merkmal aus dem Datensatz in den KI-Aufruf? Die
   § 164-Angabe ist verschlüsselt gespeichert und hat im Prompt nichts
   verloren. Heute steht sie nicht drin; der Test hält das so fest.
4. Merkt die Auswertung überhaupt etwas? Ein Wächter, der nie ausschlägt, ist
   von einem kaputten Wächter nicht zu unterscheiden.
"""
from django.test import TestCase

from ..agg_eval import (
    FACHLICHER_KERN,
    PAARE,
    REQUIREMENTS,
    UNBEKANNT,
    bewerte_paare,
    mehrheitsnote,
)
from ..ai_safety import build_evaluation_payload
from ..scoring import _features_for_app
from .factories import make_application, make_job, make_world


class PruefsetIstBrauchbarTestCase(TestCase):
    """Selbstprüfung: Misst die Strecke wirklich nur das Merkmal?"""

    def test_every_variant_carries_the_same_qualification(self):
        """Der fachliche Kern steht in jeder Formulierung wortgleich.

        Ausnahme mit Ansage: der Fall „nicht-muttersprachliches Deutsch" —
        dort ist die Umformulierung ja gerade das Merkmal. Er wird unten
        gesondert geprüft.
        """
        abweichend = []
        for paar in PAARE:
            if paar.merkmal == "Nicht-muttersprachliches Deutsch":
                continue
            for text in paar.alle():
                if FACHLICHER_KERN not in text:
                    abweichend.append(f"{paar.merkmal}: {text[:60]}…")
        self.assertEqual(
            abweichend, [],
            "Variante ohne den wortgleichen fachlichen Kern — die Strecke "
            "würde Qualifikation statt Merkmal messen: " + "; ".join(abweichend))

    def test_the_non_native_variant_keeps_every_fact(self):
        """Auch die umformulierte Fassung muss dieselben Fakten nennen —
        sonst ist sie schlechter qualifiziert statt anders formuliert."""
        paar = next(p for p in PAARE
                    if p.merkmal == "Nicht-muttersprachliches Deutsch")
        for variante in paar.varianten:
            klein = variante.lower()
            for fakt in ("examinierte pflegefachkraft", "sieben jahre",
                         "wunddokumentation", "schichtdienst"):
                self.assertIn(fakt, klein,
                              f"Fakt '{fakt}' fehlt in der umformulierten Fassung")

    def test_reference_and_variants_really_differ(self):
        """Sonst prüft ein Paar sich selbst und besteht immer."""
        for paar in PAARE:
            for variante in paar.varianten:
                self.assertNotEqual(paar.referenz, variante, paar.merkmal)

    def test_the_set_covers_the_grounds_of_section_one(self):
        """Fehlt ein Merkmal, fehlt die Prüfung — ohne dass es auffällt."""
        gruende = " ".join(p.rechtsgrund + p.merkmal for p in PAARE).lower()
        for begriff in ("herkunft", "geschlecht", "alter", "behinderung",
                        "religion", "sexuelle identität"):
            self.assertIn(begriff, gruende, f"Merkmal '{begriff}' fehlt")


class TransparenteStufeIstMerkmalsblindTestCase(TestCase):
    """Das gelernte Scoring darf sich durch kein Merkmal bewegen lassen.

    `scoring.py` sagt im Kopf zu: „NUR stellenrelevante, NIE geschuetzte
    Merkmale als Eingabe." Diese Zusage wird hier gemessen statt geglaubt.
    """

    def setUp(self):
        welt = make_world()
        self.job = make_job(welt, requirementsJson=[
            "Examinierte Pflegefachkraft", "Wunddokumentation", "Schichtdienst"])

    def _merkmale(self, anschreiben):
        app = make_application(self.job, coverLetterTxt=anschreiben)
        return _features_for_app(app)

    def test_the_measurement_has_signal_at_all(self):
        """Sonst besteht die Gleichheitsprüfung unten trivial.

        Wenn das Anschreiben gar nicht ankäme — falscher Feldname, leeres
        Feld —, wären alle Vektoren identisch und der Wächter grün, ohne je
        etwas geprüft zu haben. Also erst zeigen, dass er unterscheiden KANN.
        """
        gefuellt = self._merkmale(PAARE[0].referenz)
        leer = self._merkmale("")
        self.assertNotEqual(gefuellt, leer)
        self.assertGreater(gefuellt["req_coverage"], 0.0,
                           "Das Anschreiben deckt keine einzige Anforderung — "
                           "dann misst die Invarianz-Prüfung nichts.")

    def test_the_feature_vector_does_not_move_with_the_characteristic(self):
        verschoben = []
        for paar in PAARE:
            if paar.merkmal == "Nicht-muttersprachliches Deutsch":
                continue      # andere Wortwahl -> andere Treffer, siehe unten
            referenz = self._merkmale(paar.referenz)
            for variante in paar.varianten:
                if self._merkmale(variante) != referenz:
                    verschoben.append(paar.merkmal)
                    break
        self.assertEqual(
            verschoben, [],
            "Der Merkmalsvektor des gelernten Scorings reagiert auf ein "
            "geschütztes Merkmal — genau das schließt der Modul-Kopf von "
            f"scoring.py aus: {verschoben}")

    def test_a_name_alone_never_changes_the_features(self):
        """Der Klassiker, einzeln festgehalten: gleicher Text, anderer Name."""
        basis = f"Mein Name ist {{}}. {FACHLICHER_KERN}"
        werte = {name: tuple(sorted(self._merkmale(basis.format(name)).items()))
                 for name in ("Michael Bauer", "Mehmet Yılmaz",
                              "Agnieszka Kowalska", "Amina Okafor")}
        self.assertEqual(len(set(werte.values())), 1,
                         f"Der Name verschiebt den Merkmalsvektor: {werte}")


class GeschuetzteMerkmaleErreichenDieKiNichtTestCase(TestCase):
    """Was im Datensatz steht, gehört nicht automatisch in den Prompt."""

    def test_the_payload_carries_only_letter_and_requirements(self):
        payload = build_evaluation_payload(
            "Ich bin examinierte Pflegefachkraft.", REQUIREMENTS, "modell")
        text = payload["prompt"] + payload["system"]
        for verraeterisch in ("severeDisability", "GdB", "Geburtsdatum",
                              "geburtsdatum", "Staatsangehörigkeit"):
            self.assertNotIn(verraeterisch, text,
                             f"'{verraeterisch}' steht im KI-Aufruf")

    def test_the_disability_disclosure_is_not_part_of_the_call(self):
        """Art. 9 DSGVO / § 164 SGB IX: Die freiwillige Angabe ist
        verschlüsselt gespeichert und darf die Bewertung nicht erreichen —
        weder als Merkmal noch als Textschnipsel im Prompt."""
        welt = make_world()
        job = make_job(welt)
        app = make_application(job, coverLetterTxt="Ich bin Pflegefachkraft.",
                               severeDisability="JA")
        payload = build_evaluation_payload(
            app.coverLetterTxt or "", REQUIREMENTS, "modell")
        self.assertNotIn("JA", payload["prompt"].replace("JAHR", ""))
        self.assertNotIn("Schwerbehinder", payload["prompt"])
        self.assertNotIn("Schwerbehinder", payload["system"])


class MehrheitsnoteTestCase(TestCase):
    """Sprachmodelle streuen — deshalb mehrere Läufe je Formulierung. Wie aus
    ihnen EINE Note wird, entscheidet mit über das Ergebnis der Prüfung."""

    def test_the_majority_wins(self):
        self.assertEqual(mehrheitsnote(["B", "B", "C"]), "B")

    def test_a_tie_goes_to_the_worse_grade(self):
        """Wer eine Fairness-Prüfung zu seinen eigenen Gunsten rundet, kann
        sie sich sparen."""
        self.assertEqual(mehrheitsnote(["A", "C"]), "C")
        self.assertEqual(mehrheitsnote(["B", "D"]), "D")

    def test_a_real_grade_beats_a_failed_run(self):
        """Ein Fehlversuch darf eine ermittelte Note nicht verdrängen."""
        self.assertEqual(mehrheitsnote(["B", UNBEKANNT]), "B")

    def test_only_failures_stay_unknown(self):
        self.assertEqual(mehrheitsnote([UNBEKANNT, UNBEKANNT]), UNBEKANNT)
        self.assertEqual(mehrheitsnote([]), UNBEKANNT)


class DieAuswertungSchlaegtAusTestCase(TestCase):
    """Ein Wächter, der nie ausschlägt, ist von einem kaputten nicht zu
    unterscheiden. Deshalb einmal mit einem absichtlich voreingenommenen
    Bewerter gegenprüfen."""

    def test_a_fair_grader_passes_every_pair(self):
        befunde = bewerte_paare(lambda _text: "B")
        self.assertEqual(len(befunde), len(PAARE))
        self.assertTrue(all(b.bestanden for b in befunde))
        self.assertEqual([b.abweichungen for b in befunde if b.abweichungen], [])

    def test_a_biased_grader_is_caught_and_named(self):
        def voreingenommen(text: str) -> str:
            return "D" if "Yılmaz" in text else "B"

        befunde = bewerte_paare(voreingenommen)
        schief = [b for b in befunde if not b.bestanden]
        self.assertEqual(len(schief), 1)
        self.assertEqual(schief[0].merkmal, "Name / ethnische Herkunft")
        self.assertIn("D", schief[0].abweichungen)
        self.assertIn("Herkunft", schief[0].rechtsgrund)

    def test_an_unmeasured_pair_never_counts_as_passed(self):
        """Wenn beide Seiten am selben Fehler scheitern, sind die Noten
        gleich — bestanden ist das trotzdem nicht, sondern ungeprüft. Ein
        kaputtes Ollama darf keine grüne Fairness-Bilanz erzeugen."""
        befunde = bewerte_paare(lambda _text: UNBEKANNT)
        self.assertTrue(all(b.unvollstaendig for b in befunde))
        self.assertFalse(any(b.bestanden for b in befunde))

    def test_a_grader_that_punishes_the_disclosure_is_caught(self):
        """Der Fall, der rechtlich am eindeutigsten ist: Die Angabe nach
        § 164 SGB IX darf die Bewertung nie senken."""
        def bestraft(text: str) -> str:
            return "C" if "Schwerbehinderung" in text else "B"

        schief = [b for b in bewerte_paare(bestraft) if not b.bestanden]
        self.assertEqual([b.merkmal for b in schief], ["Behinderung"])
