"""L3-1: gelernter, erklaerbarer Scoring-Kern.

Deckt ab: Merkmals-Extraktion (nur stellenrelevant), Lift-Gewichte, Kaltstart
(zu wenig Daten -> kein Modell), Note + Begruendung, und dass ein starker
Bewerber besser eingestuft wird als ein schwacher.
"""
from django.test import TestCase

from ..audit import write_audit
from ..insights import resolve_learning_scope
from ..models import Application
from ..scoring import (
    _features_for_app,
    grade_application,
    learn_context_model,
)
from .factories import make_application, make_job, make_world

_KO = [
    {"id": "q1", "type": "YES_NO", "question": "Examen?",
     "isMandatory": True, "expectedAnswer": "YES"},
    {"id": "q2", "type": "YES_NO", "question": "Schicht?",
     "isMandatory": True, "expectedAnswer": "YES"},
]


def _advance(app, new_status):
    old = app.status
    app.status = new_status
    app.save(update_fields=['status'])
    write_audit('STATUS_CHANGE', application_id=app.id,
                oldStatus=old, newStatus=new_status)


def _decided(job, *, final, reached=(), answers=None, cover=""):
    app = make_application(job, status='NEW', screeningAnswersJson=answers or {},
                           coverLetterTxt=cover)
    for st in reached:
        _advance(app, st)
    if app.status != final:
        _advance(app, final)
    return app


class FeatureTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=_KO,
                            requirementsJson=["Django", "PostgreSQL"])

    def test_strong_application_features(self):
        app = make_application(
            self.job, screeningAnswersJson={"Examen?": "YES", "Schicht?": "YES"},
            coverLetterTxt="Erfahrung mit Django und PostgreSQL.")
        f = _features_for_app(app)
        self.assertEqual(f["ko_all"], 1.0)
        self.assertEqual(f["ko_ratio"], 1.0)
        self.assertEqual(f["req_coverage"], 1.0)
        self.assertEqual(f["has_cover"], 1.0)

    def test_weak_application_features(self):
        app = make_application(
            self.job, screeningAnswersJson={"Examen?": "NO", "Schicht?": "NO"},
            coverLetterTxt="")
        f = _features_for_app(app)
        self.assertEqual(f["ko_all"], 0.0)
        self.assertEqual(f["ko_ratio"], 0.0)
        self.assertEqual(f["has_cover"], 0.0)


class LearningTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=_KO,
                            requirementsJson=["Django"])

    def _seed(self):
        # 12 starke -> eingeladen, 12 schwache -> abgelehnt (klares Signal)
        for _ in range(12):
            _decided(self.job, final='INVITED', reached=['IN_REVIEW', 'INVITED'],
                     answers={"Examen?": "YES", "Schicht?": "YES"},
                     cover="Ich habe Django-Erfahrung.")
        for _ in range(12):
            _decided(self.job, final='REJECTED',
                     answers={"Examen?": "NO", "Schicht?": "NO"}, cover="")

    def test_cold_start_no_model(self):
        # nur 4 Entscheidungen -> unter Mindestmenge
        for _ in range(4):
            _decided(self.job, final='REJECTED', answers={"Examen?": "NO"})
        scope = resolve_learning_scope(self.job)
        self.assertIsNone(learn_context_model(scope))

    def test_learns_positive_weight_for_discriminating_feature(self):
        self._seed()
        model = learn_context_model(resolve_learning_scope(self.job))
        self.assertIsNotNone(model)
        self.assertGreater(model.weights["ko_all"], 0.3)
        self.assertGreaterEqual(model.sample_size, 20)

    def test_strong_beats_weak_grade(self):
        self._seed()
        model = learn_context_model(resolve_learning_scope(self.job))
        strong = make_application(
            self.job, screeningAnswersJson={"Examen?": "YES", "Schicht?": "YES"},
            coverLetterTxt="Django-Profi.")
        weak = make_application(
            self.job, screeningAnswersJson={"Examen?": "NO", "Schicht?": "NO"},
            coverLetterTxt="")
        g_strong, reasons = grade_application(strong, model)
        g_weak, _ = grade_application(weak, model)
        order = "DCBA"   # schlecht -> gut
        # Kernaussage: der starke Bewerber wird strikt besser eingestuft.
        self.assertGreater(order.index(g_strong), order.index(g_weak))
        self.assertIn(g_strong, ("A", "B"))
        self.assertTrue(any("erfüllt" in r.lower() for r in reasons))

    def test_grade_has_rationale(self):
        self._seed()
        model = learn_context_model(resolve_learning_scope(self.job))
        app = make_application(
            self.job, screeningAnswersJson={"Examen?": "YES", "Schicht?": "YES"},
            coverLetterTxt="Django.")
        _, reasons = grade_application(app, model)
        self.assertTrue(reasons)

    def test_label_counts_invited_even_if_later_rejected(self):
        # Eine Bewerbung, die eingeladen und DANN abgelehnt wurde, zaehlt als
        # eingeladen (positives Label) - Verlauf, nicht nur Endstand.
        app = _decided(self.job, final='REJECTED',
                       reached=['IN_REVIEW', 'INVITED'],
                       answers={"Examen?": "YES", "Schicht?": "YES"})
        from ..scoring import _labelled_rows
        rows = _labelled_rows([Application.objects.get(id=app.id)])
        self.assertTrue(rows[0][1])   # invited == True
