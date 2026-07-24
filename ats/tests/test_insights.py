"""L1-Rechenkern: Trichter, Kanal, Frage-Wirkung, Engpass, Kontext-Leiter.

Deckt ab: Spezifitaets-Leiter (spezifisch wenn genug Daten, sonst hochfallen),
Mindestmengen-Schranke (< 20 -> nicht belastbar), Trichter aus echtem
Statusverlauf, Kanal-Quote, K.O.-Frage-Wirkung, Engpass-Stufe.
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from ..audit import write_audit
from ..insights import (
    MIN_SAMPLE,
    channel_effectiveness,
    funnel_by_context,
    resolve_learning_scope,
    screening_question_impact,
    stage_bottlenecks,
)
from ..models import Application, AuditLog, Department
from .factories import make_application, make_job, make_world


def _advance(app, new_status, when=None):
    """Statuswechsel schreiben (Verlauf) und optional den Zeitpunkt setzen."""
    old = app.status
    app.status = new_status
    app.save(update_fields=['status'])
    a = write_audit('STATUS_CHANGE', application_id=app.id,
                    oldStatus=old, newStatus=new_status)
    if when is not None:
        AuditLog.objects.filter(id=a.id).update(createdAt=when)
    return app


def _decided(job, *, final='REJECTED', reached=(), source='DIRECT',
             answers=None):
    """Eine abgeschlossene Bewerbung, die die Stufen in `reached` durchlief."""
    app = make_application(job, status='NEW', source=source,
                           screeningAnswersJson=answers or {})
    for st in reached:
        _advance(app, st)
    if app.status != final:
        _advance(app, final)
    return app


class ResolveScopeTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.dept = Department.objects.create(name="Station 3",
                                              facility=self.world.facility)
        self.job = make_job(self.world, department=self.dept)

    def test_insufficient_data_is_not_sufficient(self):
        for _ in range(5):
            _decided(self.job, final='REJECTED')
        scope = resolve_learning_scope(self.job)
        self.assertFalse(scope.sufficient)
        self.assertLess(scope.sample_size, MIN_SAMPLE)

    def test_specific_level_when_enough_data(self):
        for _ in range(MIN_SAMPLE):
            _decided(self.job, final='REJECTED')
        scope = resolve_learning_scope(self.job)
        self.assertTrue(scope.sufficient)
        # spezifischste Ebene mit Daten: Abteilung + Jobfamilie
        self.assertEqual(scope.level, 'dept_family')
        self.assertGreaterEqual(scope.sample_size, MIN_SAMPLE)

    def test_falls_back_to_family_when_department_thin(self):
        # Zweiter Job in ANDERER Einrichtung UND anderem Standort, gleiche
        # Jobfamilie -> nur die Jobfamilie aggregiert genug Daten.
        from ..models import Facility, Location
        fac2 = Facility.objects.create(name="Haus B",
                                       organization=self.world.org)
        loc2 = Location.objects.create(name="Lüneburg", city="Lüneburg")
        dept2 = Department.objects.create(name="Geriatrie", facility=fac2)
        job2 = make_job(self.world, facility=fac2, location=loc2,
                        department=dept2)
        for _ in range(12):
            _decided(self.job, final='REJECTED')
            _decided(job2, final='REJECTED')
        scope = resolve_learning_scope(self.job)
        # Abteilung/Einrichtung/Standort je 12 (< 20) -> hoch bis Jobfamilie (24)
        self.assertTrue(scope.sufficient)
        self.assertEqual(scope.level, 'family')
        self.assertEqual(scope.sample_size, 24)


class FunnelTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)

    def test_funnel_counts_reached_stages(self):
        # 3 erreichen nur Pruefung (dann abgelehnt), 2 wurden eingeladen,
        # davon 1 eingestellt.
        for _ in range(3):
            _decided(self.job, final='REJECTED', reached=['IN_REVIEW'])
        _decided(self.job, final='INVITED', reached=['IN_REVIEW', 'INVITED'])
        _decided(self.job, final='HIRED',
                 reached=['IN_REVIEW', 'INVITED', 'HIRED'])
        scope = resolve_learning_scope(self.job)
        funnel = funnel_by_context(scope)
        by = {s['status']: s['count'] for s in funnel.stages}
        self.assertEqual(by['NEW'], 5)
        self.assertEqual(by['IN_REVIEW'], 5)
        self.assertEqual(by['INVITED'], 2)
        self.assertEqual(by['HIRED'], 1)
        # Abbruch Pruefung -> Eingeladen = 1 - 2/5 = 0.6
        drop = next(t['drop_rate'] for t in funnel.transitions
                    if t['from'] == 'In Prüfung')
        self.assertAlmostEqual(drop, 0.6, places=2)


class ChannelTestCase(TestCase):
    def test_channel_effectiveness_counts_from_history(self):
        world = make_world()
        job = make_job(world)
        # STEPSTONE: 2 Bewerbungen, 1 eingeladen(-dann-abgelehnt)
        _decided(job, source='STEPSTONE', final='REJECTED',
                 reached=['IN_REVIEW'])
        _decided(job, source='STEPSTONE', final='REJECTED',
                 reached=['IN_REVIEW', 'INVITED'])
        # DIRECT: 1 eingestellt
        _decided(job, source='DIRECT', final='HIRED',
                 reached=['IN_REVIEW', 'INVITED', 'HIRED'])
        stats = {c.source: c for c in channel_effectiveness()}
        self.assertEqual(stats['STEPSTONE'].applications, 2)
        self.assertEqual(stats['STEPSTONE'].invited, 1)   # trotz Absage
        self.assertEqual(stats['STEPSTONE'].hired, 0)
        self.assertEqual(stats['DIRECT'].hired, 1)


class ScreeningImpactTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=[{
            "id": "q1", "type": "YES_NO", "question": "Examen vorhanden?",
            "isMandatory": True, "expectedAnswer": "YES"}])

    def test_impact_fail_rate_and_invite_rates(self):
        # 2 erfuellt (beide eingeladen), 3 nicht erfuellt (keiner eingeladen)
        _decided(self.job, final='INVITED', reached=['IN_REVIEW', 'INVITED'],
                 answers={"Examen vorhanden?": "YES"})
        _decided(self.job, final='INVITED', reached=['IN_REVIEW', 'INVITED'],
                 answers={"Examen vorhanden?": "YES"})
        for _ in range(3):
            _decided(self.job, final='REJECTED',
                     answers={"Examen vorhanden?": "NO"})
        scope = resolve_learning_scope(self.job)
        impacts = screening_question_impact(self.job, scope)
        self.assertEqual(len(impacts), 1)
        imp = impacts[0]
        self.assertEqual(imp.answered, 5)
        self.assertAlmostEqual(imp.fail_rate, 0.6, places=2)     # 3/5
        self.assertAlmostEqual(imp.invite_rate_pass, 1.0, places=2)
        self.assertAlmostEqual(imp.invite_rate_fail, 0.0, places=2)

    def test_non_ko_question_is_ignored(self):
        job = make_job(self.world, screeningQuestionsJson=[{
            "id": "q2", "type": "TEXT", "question": "Motivation?",
            "isMandatory": True}])   # kein expectedAnswer -> kein K.O.
        _decided(job, final='REJECTED', answers={"Motivation?": "text"})
        scope = resolve_learning_scope(job)
        self.assertEqual(screening_question_impact(job, scope), [])


class BottleneckTestCase(TestCase):
    def test_slowest_stage_detected(self):
        world = make_world()
        job = make_job(world)
        now = timezone.now()
        app = make_application(job, status='NEW')
        Application.objects.filter(id=app.id).update(
            createdAt=now - timedelta(days=20))
        app.refresh_from_db()
        # NEW -> IN_REVIEW nach 2 Tagen; IN_REVIEW -> INVITED nach 15 Tagen
        _advance(app, 'IN_REVIEW', when=now - timedelta(days=18))
        _advance(app, 'INVITED', when=now - timedelta(days=3))
        result = stage_bottlenecks()
        self.assertIsNotNone(result.slowest)
        self.assertEqual(result.slowest.status, 'IN_REVIEW')  # 15 Tage
        by = {s.status: s.avg_days for s in result.stages}
        self.assertAlmostEqual(by['IN_REVIEW'], 15.0, delta=0.5)
        self.assertAlmostEqual(by['NEW'], 2.0, delta=0.5)
