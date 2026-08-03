"""N1: Interview-Leitfaden je Stelle + Abdeckungs-Checkliste im Feedback.

Voice-Studien-Learning "kontrollierte Varianz": menschliche Interviews
bekommen per Themen-Leitfaden dieselbe Konsistenz, die KI-Interviews in der
Feldstudie ueberlegen machte. Deckt ab: Leitfaden-Normalisierung am Modell,
Wizard-Roundtrip (CSV), Abdeckung wird je Feedback gespeichert (nur echte
Themen, kein Schmuggel), Anzeige n/m auf der Termine-Seite.
"""
from django.test import TestCase
from django.urls import reverse

from ..models import InterviewFeedback
from .factories import make_application, make_job, make_world
from .utils import make_user

_GUIDE = ["Fachliche Erfahrung", "Schichtbereitschaft", "Rückfragen"]


class GuideModelTestCase(TestCase):
    def test_guide_normalized(self):
        world = make_world()
        job = make_job(world, interviewGuideJson=["  Thema A  ", "", 42,
                                                  "x" * 200])
        guide = job.interview_guide
        self.assertIn("Thema A", guide)
        self.assertNotIn("", guide)
        self.assertTrue(all(len(t) <= 80 for t in guide))

    def test_guide_csv(self):
        world = make_world()
        job = make_job(world, interviewGuideJson=_GUIDE)
        self.assertEqual(job.interview_guide_csv,
                         "Fachliche Erfahrung, Schichtbereitschaft, Rückfragen")


class GuideWizardTestCase(TestCase):
    def test_create_job_parses_guide_csv(self):
        world = make_world()
        admin = make_user("gw-admin", role="HR-Admin")
        self.client.force_login(admin)
        self.client.post(reverse('ats:create_job'), data={
            'title': 'Pflegefachkraft Leitfaden',
            'description': 'Text', 'tasks': 'A', 'requirements': 'B',
            'facility': str(world.facility.id),
            'location': str(world.location.id),
            'job_family': str(world.job_family.id),
            'workflow_state': str(world.published.id),
            'interview_guide': ' Fachliche Erfahrung , Schichtbereitschaft ,, Rückfragen ',
        })
        from ..models import JobPosting
        job = JobPosting.objects.get(title='Pflegefachkraft Leitfaden')
        self.assertEqual(job.interview_guide, _GUIDE)


class GuideCoverageTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        # Das Feedback-Formular lebt im Gespraechsrunden-Abschnitt - eine
        # Stelle mit Leitfaden hat realistisch auch Runden definiert.
        self.job = make_job(self.world, interviewGuideJson=_GUIDE,
                            interviewRoundsJson=['Erstgespräch'])
        self.app = make_application(self.job, status='INVITED')
        self.rec = make_user("gc-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.url = reverse('ats:save_interview_feedback', args=[self.app.id])

    def test_coverage_saved(self):
        self.client.post(self.url, data={
            'recommendation': 'YES', 'round': '0', 'strengths': 'Gut',
            'guide_topic': ['Fachliche Erfahrung', 'Rückfragen']})
        fb = InterviewFeedback.objects.get()
        self.assertEqual(sorted(fb.guideCoverageJson),
                         ['Fachliche Erfahrung', 'Rückfragen'])

    def test_smuggled_topics_filtered(self):
        self.client.post(self.url, data={
            'recommendation': 'YES', 'round': '0', 'strengths': 'Gut',
            'guide_topic': ['Fachliche Erfahrung', 'ERFUNDENES THEMA']})
        fb = InterviewFeedback.objects.get()
        self.assertEqual(fb.guideCoverageJson, ['Fachliche Erfahrung'])

    def test_coverage_shown_on_interviews_page(self):
        self.client.post(self.url, data={
            'recommendation': 'YES', 'round': '0', 'strengths': 'Gut',
            'guide_topic': ['Fachliche Erfahrung']})
        r = self.client.get(reverse('ats:interviews'))
        self.assertContains(r, "Leitfaden: 1/3 Themen behandelt")

    def test_checklist_rendered_in_form(self):
        r = self.client.get(reverse('ats:interviews'))
        self.assertContains(r, "Leitfaden – im Gespräch behandelt")
        self.assertContains(r, "Schichtbereitschaft")

    def test_no_guide_no_checklist(self):
        job2 = make_job(self.world, title="Ohne Leitfaden",
                        interviewRoundsJson=['Erstgespräch'])
        make_application(job2, status='INVITED')
        # Seite rendert; fuer Stellen ohne Leitfaden erscheint keine Checkliste
        # in DEREN Formular - grob geprueft ueber die Gesamtseite mit nur
        # dieser Stelle:
        InterviewFeedback.objects.all().delete()
        self.app.delete()
        r = self.client.get(reverse('ats:interviews'))
        self.assertNotContains(r, "Leitfaden – im Gespräch behandelt")
