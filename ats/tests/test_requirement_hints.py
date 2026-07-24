"""L4: Anforderungs-Hinweise im Stellen-Editor.

Deckt ab: requirement_impact vergleicht besetzte Stellen gleicher Jobfamilie
mit vs. ohne eine Anforderung (Zeit bis Besetzung); Hinweis nur bei genug
Datenlage je Gruppe und spuerbarem Unterschied; Endpoint liefert die Hinweise
mit BOLA.
"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..insights import REQ_MIN_DAYS, requirement_impact
from ..models import Application
from ..suggestions import requirement_hints
from .factories import make_application, make_job, make_world
from .utils import make_user


def _filled_job(world, *, reqs, created_days_ago, ttf_days, title="Stelle"):
    """Eine besetzte Stelle: angelegt vor X Tagen, erste Einstellung nach
    ttf_days. Gleiche Jobfamilie wie world."""
    job = make_job(world, title=title, requirementsJson=reqs)
    now = timezone.now()
    from ..models import JobPosting
    JobPosting.objects.filter(id=job.id).update(
        createdAt=now - timedelta(days=created_days_ago))
    app = make_application(job, status='HIRED')
    Application.objects.filter(id=app.id).update(
        hiredAt=now - timedelta(days=created_days_ago - ttf_days))
    return job


class RequirementImpactTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        # Ziel-Stelle mit der fraglichen Anforderung
        self.job = make_job(self.world, title="Ziel",
                            requirementsJson=["Führerschein Klasse C",
                                              "Teamfähigkeit"])

    def test_slower_requirement_yields_hint(self):
        # 3 vergleichbare MIT „Führerschein" -> langsam (40 Tage)
        for i in range(3):
            _filled_job(self.world, reqs=["Führerschein Klasse C"],
                        created_days_ago=60, ttf_days=40, title=f"mit{i}")
        # 3 vergleichbare OHNE -> schnell (15 Tage)
        for i in range(3):
            _filled_job(self.world, reqs=["Teamfähigkeit"],
                        created_days_ago=60, ttf_days=15, title=f"ohne{i}")
        impacts = {i.requirement: i for i in requirement_impact(self.job)}
        self.assertIn("Führerschein Klasse C", impacts)
        imp = impacts["Führerschein Klasse C"]
        self.assertEqual((imp.jobs_with, imp.jobs_without), (3, 3))
        self.assertGreaterEqual(imp.days_faster_without, REQ_MIN_DAYS)
        self.assertAlmostEqual(imp.days_faster_without, 25.0, delta=1.0)

    def test_no_hint_without_enough_jobs(self):
        # nur 2 mit / 2 ohne -> unter REQ_MIN_GROUP (3)
        for i in range(2):
            _filled_job(self.world, reqs=["Führerschein Klasse C"],
                        created_days_ago=60, ttf_days=40, title=f"m{i}")
            _filled_job(self.world, reqs=["Teamfähigkeit"],
                        created_days_ago=60, ttf_days=15, title=f"o{i}")
        self.assertEqual(requirement_impact(self.job), [])

    def test_no_hint_when_not_faster(self):
        # gleich schnell mit/ohne -> kein Hinweis
        for i in range(3):
            _filled_job(self.world, reqs=["Führerschein Klasse C"],
                        created_days_ago=60, ttf_days=20, title=f"m{i}")
            _filled_job(self.world, reqs=["Teamfähigkeit"],
                        created_days_ago=60, ttf_days=20, title=f"o{i}")
        self.assertEqual(requirement_impact(self.job), [])

    def test_hint_text_mentions_days(self):
        for i in range(3):
            _filled_job(self.world, reqs=["Führerschein Klasse C"],
                        created_days_ago=60, ttf_days=40, title=f"m{i}")
            _filled_job(self.world, reqs=["Teamfähigkeit"],
                        created_days_ago=60, ttf_days=15, title=f"o{i}")
        hints = requirement_hints(self.job)
        self.assertIn("Führerschein Klasse C", hints)
        self.assertIn("schneller besetzt", hints["Führerschein Klasse C"])


class EndpointTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Ziel",
                            requirementsJson=["Führerschein Klasse C"])
        self.rec = make_user("rq-rec", role="Recruiter")
        self.client.force_login(self.rec)

    def test_endpoint_returns_req_hints(self):
        for i in range(3):
            _filled_job(self.world, reqs=["Führerschein Klasse C"],
                        created_days_ago=60, ttf_days=40, title=f"m{i}")
            _filled_job(self.world, reqs=["Teamfähigkeit"],
                        created_days_ago=60, ttf_days=15, title=f"o{i}")
        r = self.client.get(
            reverse('ats:job_question_hints', args=[self.job.id]))
        self.assertEqual(r.status_code, 200)
        self.assertIn("req_hints", r.json())
        self.assertIn("Führerschein Klasse C", r.json()["req_hints"])

    def test_bola_foreign_job_denied(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Kiel")
        foreign = make_job(self.world, title="Fremd", location=other)
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.get(
            reverse('ats:job_question_hints', args=[foreign.id]))
        self.assertEqual(r.status_code, 404)
