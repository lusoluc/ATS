"""L3-2: Messstrecke - Backtest, Kalibrierung, Ehrlichkeits-Schranke.

Deckt ab: zu wenig Daten -> nicht vertrauenswuerdig (mit Grund); bei klarem
Signal laeuft der Backtest, die A/B-Empfehlung erreicht die Grundlinie und die
Schranke oeffnet; Kalibrierung ordnet A ueber D ein.
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from ..audit import write_audit
from ..insights import resolve_learning_scope
from ..models import Application
from ..scoring_eval import backtest, is_trustworthy
from .factories import make_application, make_job, make_world

_KO = [{"id": "q1", "type": "YES_NO", "question": "Examen?",
        "isMandatory": True, "expectedAnswer": "YES"}]


def _advance(app, new_status):
    old = app.status
    app.status = new_status
    app.save(update_fields=['status'])
    write_audit('STATUS_CHANGE', application_id=app.id,
                oldStatus=old, newStatus=new_status)


def _decided_at(job, *, days_ago, ko=True, invited=False, covered=False):
    """Eine Entscheidung: ko erfuellt?, Anforderung im Anschreiben gedeckt?,
    eingeladen? - mit gesetztem Eingangsdatum fuer den zeitlichen Split."""
    ans = {"Examen?": "YES"} if ko else {"Examen?": "NO"}
    cover = "Ich bringe Django-Erfahrung mit." if covered else ""
    app = make_application(job, status='NEW', screeningAnswersJson=ans,
                           coverLetterTxt=cover)
    if invited:
        _advance(app, 'IN_REVIEW')
        _advance(app, 'INVITED')
    else:
        _advance(app, 'REJECTED')
    now = timezone.now()
    Application.objects.filter(id=app.id).update(
        createdAt=now - timedelta(days=days_ago))
    return app


class BacktestTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=_KO,
                            requirementsJson=["Django"])

    def _seed_signal(self, n=10):
        # ALLE erfuellen K.O. (Grundlinie sagt: alle positiv). Erst die
        # Anforderungs-Deckung trennt eingeladen von abgelehnt -> das gelernte
        # Score kann die Grundlinie schlagen. Abwechselnd ueber die Zeit.
        d = 2 * n
        for _ in range(n):
            _decided_at(self.job, days_ago=d, ko=True, covered=True,
                        invited=True)
            d -= 1
            _decided_at(self.job, days_ago=d, ko=True, covered=False,
                        invited=False)
            d -= 1

    def test_insufficient_data_not_trustworthy(self):
        for _ in range(4):
            _decided_at(self.job, days_ago=5, ko=False, invited=False)
        ok, reason = is_trustworthy(resolve_learning_scope(self.job))
        self.assertFalse(ok)
        self.assertIn("wenig", reason.lower())

    def test_backtest_runs_and_gate_opens_on_clear_signal(self):
        self._seed_signal(10)   # 20 Entscheidungen, gelernt schlaegt Grundlinie
        bt = backtest(resolve_learning_scope(self.job))
        self.assertGreaterEqual(bt.total, 20)
        self.assertGreaterEqual(bt.test_n, 6)
        self.assertIsNotNone(bt.learned_precision)
        self.assertIsNotNone(bt.baseline_precision)
        # Gelernt nutzt die Anforderungs-Deckung, Grundlinie (nur K.O.) nicht.
        self.assertGreater(bt.learned_precision, bt.baseline_precision)
        self.assertTrue(bt.beats_baseline)

    def test_calibration_orders_a_above_d(self):
        self._seed_signal(10)
        bt = backtest(resolve_learning_scope(self.job))
        by = {b.grade: b for b in bt.calibration}
        # A wird haeufiger eingeladen als D (Modell hat etwas gelernt)
        self.assertGreaterEqual(by["A"].invite_rate, by["D"].invite_rate)

    def test_no_signal_does_not_open_gate(self):
        # Label unabhaengig von Merkmalen -> Modell schlaegt Grundlinie nicht
        now = timezone.now()
        for i in range(24):
            app = make_application(self.job, status='NEW',
                                   screeningAnswersJson={"Examen?": "YES"})
            # abwechselnd eingeladen/abgelehnt, OHNE Zusammenhang zu Merkmalen
            _advance(app, 'INVITED' if i % 2 else 'REJECTED')
            Application.objects.filter(id=app.id).update(
                createdAt=now - timedelta(days=30 - i))
        ok, _ = is_trustworthy(resolve_learning_scope(self.job))
        self.assertFalse(ok)


class DriftReportTestCase(TestCase):
    """L5: Frühwarnung — wird das Modell schlechter, entscheidet das Team dagegen?"""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=_KO,
                            requirementsJson=["Django"])

    def _pair(self, day, *, consistent):
        """Ein Paar Entscheidungen. consistent=True: Anforderungs-Deckung fuehrt
        zur Einladung (Modell-Logik trifft zu). consistent=False: umgekehrt -
        das Team entscheidet gegen das Muster."""
        _decided_at(self.job, days_ago=day, ko=True, covered=True,
                    invited=consistent)
        _decided_at(self.job, days_ago=day - 1, ko=True, covered=False,
                    invited=not consistent)

    def test_too_little_history_says_so_and_stays_calm(self):
        from ..scoring_eval import drift_report
        for i in range(3):
            self._pair(20 - 2 * i, consistent=True)
        d = drift_report(resolve_learning_scope(self.job))
        self.assertEqual(d.trend, "unbekannt")
        self.assertIn("wenig", d.verdict.lower())
        self.assertTrue(d.action)          # auch hier: nie eine Aussage ohne Schritt

    def test_stable_history_reports_no_action_needed(self):
        from ..scoring_eval import drift_report
        day = 60
        for _ in range(15):
            self._pair(day, consistent=True)
            day -= 2
        d = drift_report(resolve_learning_scope(self.job))
        self.assertIn(d.trend, ("stabil", "steigend"))
        self.assertIn("kein handlungsbedarf", d.action.lower())

    def test_team_deciding_against_the_grade_is_flagged(self):
        from ..scoring_eval import drift_report
        # Erst konsistente Historie (das Modell lernt das Muster), dann kippt
        # das Team im NEUESTEN Zeitraum die Entscheidungen um.
        day = 90
        for _ in range(12):
            self._pair(day, consistent=True)
            day -= 2
        for _ in range(8):
            self._pair(day, consistent=False)
            day -= 2
        d = drift_report(resolve_learning_scope(self.job))
        self.assertIsNotNone(d.override_rate)
        self.assertGreater(d.override_rate, 0.0)
        self.assertTrue(d.too_optimistic + d.too_pessimistic > 0)
        # Verdikt UND Handlung sind gefuellt (Regel: keine Zahl ohne Schritt)
        self.assertTrue(d.verdict and d.action)

    def test_verdict_always_comes_with_an_action(self):
        """Waechter fuer das Produktprinzip 'keine Kennzahl ohne Handlung'."""
        from ..scoring_eval import drift_report
        for seed in (0, 5, 12):
            day = 80
            for i in range(seed + 3):
                self._pair(day, consistent=(i % 2 == 0))
                day -= 2
            d = drift_report(resolve_learning_scope(self.job))
            self.assertTrue(d.verdict, "Verdikt fehlt")
            self.assertTrue(d.action, "Handlung fehlt")
