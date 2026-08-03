"""P6: „Mein Bereich"-Block für Standortleiter (Rittmann, UC-HR-02/05).

Deckt ab: der Block erscheint nur für Nicht-Admins mit begrenztem Scope,
nennt den Bereich beim Namen und zählt nur die eigenen Stellen/Verfahren.
HR-Admins und unbegrenzte Nutzer sehen ihn nicht (kein Ballast).
"""
from django.test import TestCase
from django.urls import reverse

from ..models import Location, UserScope
from .factories import make_application, make_job, make_world
from .utils import make_user


class MeinBereichTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.other_loc = Location.objects.create(name="Bremen", city="Bremen")
        self.hm = make_user("rittmann", role="Hiring-Manager")
        scope = UserScope.objects.create(user=self.hm, full_access=False)
        scope.locations.add(self.world.location)   # nur Hamburg

    def _dashboard(self):
        return self.client.get(reverse('ats:dashboard'))

    def test_block_shows_scope_label_and_counts(self):
        job_here = make_job(self.world, title="Pflege Hamburg")
        make_job(self.world, title="Pflege Bremen", location=self.other_loc)
        make_application(job_here)                       # laeuft
        make_application(job_here, status="REJECTED")    # zaehlt nicht
        self.client.force_login(self.hm)
        resp = self._dashboard()
        self.assertContains(resp, "Mein Bereich: Hamburg")
        self.assertContains(resp, "1 veröffentlichte Stelle")
        self.assertContains(resp, "1 Bewerbung im Verfahren")

    def test_only_published_jobs_counted(self):
        from ..models import WorkflowState
        draft, _ = WorkflowState.objects.get_or_create(
            name="draft", defaults={"description": "Entwurf"})
        make_job(self.world, workflowState=draft)
        self.client.force_login(self.hm)
        self.assertContains(self._dashboard(), "0 veröffentlichte Stellen")

    def test_admin_sees_no_block(self):
        admin = make_user("mb-admin", role="HR-Admin")
        self.client.force_login(admin)
        self.assertNotContains(self._dashboard(), "Mein Bereich:")

    def test_unscoped_staff_sees_no_block(self):
        rec = make_user("mb-rec", role="Recruiter")
        self.client.force_login(rec)
        self.assertNotContains(self._dashboard(), "Mein Bereich:")
