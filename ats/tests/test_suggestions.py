"""L1-Vorschlags-Schicht: Zahl -> Vorschlag + Aktion + Link.

Deckt ab: Durchfall-Regel (Frage prüfen), Kanal-Regel (Budget), Engpass-Regel,
Sortierung nach Wirkung, und - wichtig - keine kontextbezogene Aussage bei zu
duenner Datenlage (Mindestmenge nicht erreicht).
"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..audit import write_audit
from ..models import AuditLog
from ..suggestions import CHANNEL_MIN_APPS, build_suggestions
from .factories import make_application, make_job, make_world
from .utils import make_user


def _advance(app, new_status, when=None):
    old = app.status
    app.status = new_status
    app.save(update_fields=['status'])
    a = write_audit('STATUS_CHANGE', application_id=app.id,
                    oldStatus=old, newStatus=new_status)
    if when is not None:
        AuditLog.objects.filter(id=a.id).update(createdAt=when)


def _decided(job, *, final='REJECTED', reached=(), source='DIRECT',
             answers=None):
    app = make_application(job, status='NEW', source=source,
                           screeningAnswersJson=answers or {})
    for st in reached:
        _advance(app, st)
    if app.status != final:
        _advance(app, final)
    return app


class ScreeningSuggestionTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=[{
            "id": "q1", "type": "YES_NO", "question": "Führerschein Klasse C?",
            "isMandatory": True, "expectedAnswer": "YES"}])

    def test_high_fail_rate_triggers_question_suggestion(self):
        # 6 erfüllt+eingeladen, 16 nicht erfüllt -> 16/22 ~ 73 % Durchfall
        for _ in range(6):
            _decided(self.job, final='INVITED', reached=['IN_REVIEW', 'INVITED'],
                     answers={"Führerschein Klasse C?": "YES"})
        for _ in range(16):
            _decided(self.job, final='REJECTED',
                     answers={"Führerschein Klasse C?": "NO"})
        sugg = build_suggestions(self.job)
        q = next((s for s in sugg if "Führerschein" in s.text), None)
        self.assertIsNotNone(q)
        self.assertEqual(q.action_label, "Frage prüfen")
        self.assertIn("/screening-questions/", q.action_url)
        self.assertGreaterEqual(q.sample_size, 20)

    def test_thin_data_gives_no_context_suggestion(self):
        # nur 5 Vorgaenge -> unter Mindestmenge, keine Frage-Aussage
        for _ in range(5):
            _decided(self.job, final='REJECTED',
                     answers={"Führerschein Klasse C?": "NO"})
        sugg = build_suggestions(self.job)
        self.assertFalse(any("Führerschein" in s.text for s in sugg))


class ChannelSuggestionTestCase(TestCase):
    def test_channel_without_hire_triggers_budget_suggestion(self):
        world = make_world()
        job = make_job(world)
        for _ in range(CHANNEL_MIN_APPS):
            _decided(job, source='PRINT_AD', final='REJECTED',
                     reached=['IN_REVIEW'])
        sugg = build_suggestions(job)
        ch = next((s for s in sugg if "PRINT_AD" in s.text), None)
        self.assertIsNotNone(ch)
        self.assertEqual(ch.action_label, "Kanäle prüfen")
        self.assertIn("/kanaele/", ch.action_url)

    def test_channel_with_hire_no_suggestion(self):
        world = make_world()
        job = make_job(world)
        for _ in range(CHANNEL_MIN_APPS - 1):
            _decided(job, source='PRINT_AD', final='REJECTED')
        _decided(job, source='PRINT_AD', final='HIRED',
                 reached=['IN_REVIEW', 'INVITED', 'HIRED'])
        sugg = build_suggestions(job)
        self.assertFalse(any("PRINT_AD" in s.text and "0 Einstellungen" in s.text
                             for s in sugg))


class BottleneckSuggestionTestCase(TestCase):
    def test_slow_stage_triggers_engpass(self):
        world = make_world()
        job = make_job(world)
        now = timezone.now()
        # mehrere Bewerbungen: NEW->IN_REVIEW schnell (1 Tag),
        # IN_REVIEW->INVITED sehr langsam (20 Tage)
        for _ in range(6):
            app = make_application(job, status='NEW')
            from ..models import Application
            Application.objects.filter(id=app.id).update(
                createdAt=now - timedelta(days=22))
            _advance(app, 'IN_REVIEW', when=now - timedelta(days=21))
            _advance(app, 'INVITED', when=now - timedelta(days=1))
        sugg = build_suggestions(job)
        eng = next((s for s in sugg if "Engpass" in s.reason), None)
        self.assertIsNotNone(eng)
        self.assertIn("/governance/", eng.action_url)


class SortingTestCase(TestCase):
    def test_every_suggestion_has_action(self):
        world = make_world()
        job = make_job(world, screeningQuestionsJson=[{
            "id": "q1", "type": "YES_NO", "question": "Examen?",
            "isMandatory": True, "expectedAnswer": "YES"}])
        for _ in range(22):
            _decided(job, source='PRINT_AD', final='REJECTED',
                     answers={"Examen?": "NO"})
        sugg = build_suggestions(job)
        self.assertTrue(sugg)
        for s in sugg:
            self.assertTrue(s.action_label)
            self.assertTrue(s.action_url)
            self.assertTrue(s.reason)


class AnalyticsBlockTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)
        self.rec = make_user("an-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.url = reverse('ats:analytics')

    def test_empty_state_when_no_data(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Erkenntnisse")
        self.assertContains(r, "Noch keine belastbaren Erkenntnisse")

    def test_shows_channel_suggestion_with_action(self):
        for _ in range(CHANNEL_MIN_APPS):
            _decided(self.job, source='PRINT_AD', final='REJECTED',
                     reached=['IN_REVIEW'])
        r = self.client.get(self.url)
        self.assertContains(r, "PRINT_AD")
        self.assertContains(r, "Kanäle prüfen")
        self.assertContains(r, reverse('ats:source_channels'))

    def test_bola_hides_foreign_data(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Kiel")
        foreign_job = make_job(self.world, title="Fremd", location=other)
        for _ in range(CHANNEL_MIN_APPS):
            _decided(foreign_job, source='PRINT_AD', final='REJECTED')
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.get(self.url)
        # Kanal-Erkenntnis stammt aus fremdem Standort -> nicht sichtbar
        self.assertNotContains(r, "PRINT_AD")
