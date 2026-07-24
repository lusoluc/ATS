"""L1-4: gelernte Frage-Hinweise im Fragen-Baukasten (Brücke zu L4).

Deckt ab: question_hints liefert einen Hinweis bei hoher Durchfallquote,
nichts bei duenner Datenlage; der Endpoint gibt die Hinweise als JSON und
setzt BOLA durch.
"""
from django.test import TestCase
from django.urls import reverse

from ..audit import write_audit
from ..suggestions import question_hints
from .factories import make_application, make_job, make_world
from .utils import make_user


def _advance(app, new_status):
    old = app.status
    app.status = new_status
    app.save(update_fields=['status'])
    write_audit('STATUS_CHANGE', application_id=app.id,
                oldStatus=old, newStatus=new_status)


def _decided(job, *, final='REJECTED', reached=(), answers=None):
    app = make_application(job, status='NEW', screeningAnswersJson=answers or {})
    for st in reached:
        _advance(app, st)
    if app.status != final:
        _advance(app, final)
    return app


class QuestionHintsTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=[{
            "id": "q1", "type": "YES_NO", "question": "Führerschein Klasse C?",
            "isMandatory": True, "expectedAnswer": "YES"}])

    def test_hint_on_high_fail_rate(self):
        for _ in range(6):
            _decided(self.job, final='INVITED', reached=['IN_REVIEW', 'INVITED'],
                     answers={"Führerschein Klasse C?": "YES"})
        for _ in range(16):
            _decided(self.job, final='REJECTED',
                     answers={"Führerschein Klasse C?": "NO"})
        hints = question_hints(self.job)
        self.assertIn("Führerschein Klasse C?", hints)
        self.assertIn("durchfallen", hints["Führerschein Klasse C?"])

    def test_no_hint_on_thin_data(self):
        for _ in range(4):
            _decided(self.job, final='REJECTED',
                     answers={"Führerschein Klasse C?": "NO"})
        self.assertEqual(question_hints(self.job), {})


class QuestionHintsEndpointTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, screeningQuestionsJson=[{
            "id": "q1", "type": "YES_NO", "question": "Examen?",
            "isMandatory": True, "expectedAnswer": "YES"}])
        self.rec = make_user("qh-rec", role="Recruiter")
        self.client.force_login(self.rec)

    def test_endpoint_returns_hints_json(self):
        for _ in range(22):
            _decided(self.job, final='REJECTED', answers={"Examen?": "NO"})
        r = self.client.get(
            reverse('ats:job_question_hints', args=[self.job.id]))
        self.assertEqual(r.status_code, 200)
        self.assertIn("Examen?", r.json()["hints"])

    def test_bola_foreign_job_denied(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Kiel")
        foreign = make_job(self.world, title="Fremd", location=other)
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.get(
            reverse('ats:job_question_hints', args=[foreign.id]))
        self.assertEqual(r.status_code, 404)
