"""SecurATS-Tests: talent/pool (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import SystemSetting
from .utils import make_user


class TalentPoolLifecycleTestCase(TestCase):
    """Talent-Pool: Einwilligung (Portal) -> Matching -> eine Ansprache -> Widerruf."""

    def _world(self):
        import uuid as _u

        from ..models import (
            Applicant,
            ApplicantToken,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        self.loc = Location.objects.create(name="Hamburg")
        fac = Facility.objects.create(name="F", organization=org)
        self.fam = JobFamily.objects.create(name="Pflege-" + str(_u.uuid4())[:4])
        self.wf = WorkflowState.objects.create(name="published")
        old_job = JobPosting.objects.create(title="Pflegefachkraft (besetzt)",
                                            organization=org, facility=fac,
                                            location=self.loc, jobFamily=self.fam,
                                            workflowState=self.wf)
        self.ap = Applicant.objects.create(firstName="Timo", lastName="V",
                                           email="timo@x.de")
        Application.objects.create(applicant=self.ap, jobPosting=old_job,
                                   status="REJECTED")
        ApplicantToken.objects.create(applicant=self.ap, token="tp-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=30))
        self.org, self.fac = org, fac

    def _join(self):
        return self.client.post(reverse('ats:candidate_portal', args=["tp-token"]),
                                data={"form": "talent_pool", "action": "join"})

    def test_portal_join_derives_criteria_and_leave_deletes(self):
        from ..models import AuditLog, TalentPoolSubscription
        self._world()
        self.assertEqual(self._join().status_code, 302)
        import json as _json
        sub = TalentPoolSubscription.objects.get_by_email("timo@x.de")
        crit = _json.loads(sub.criteria)
        self.assertIn(str(self.fam.id), crit["job_families"])   # aus eigener Bewerbung
        self.assertIn(str(self.loc.id), crit["locations"])
        self.assertTrue(AuditLog.objects.filter(action="TALENT_POOL_JOINED").exists())
        page = self.client.get(reverse('ats:candidate_portal', args=["tp-token"]))
        self.assertContains(page, "Sie sind aufgenommen")
        # Widerruf loescht den Eintrag vollstaendig
        self.client.post(reverse('ats:candidate_portal', args=["tp-token"]),
                         data={"form": "talent_pool", "action": "leave"})
        self.assertFalse(TalentPoolSubscription.objects.filter(
            email="timo@x.de").exists())
        self.assertTrue(AuditLog.objects.filter(action="TALENT_POOL_LEFT").exists())

    def test_matching_and_single_contact(self):
        from django.core import mail

        from ..models import AuditLog, JobPosting, TalentPoolContact
        self._world()
        self._join()
        new_job = JobPosting.objects.create(title="Pflegefachkraft Station 3",
                                            organization=self.org, facility=self.fac,
                                            location=self.loc, jobFamily=self.fam,
                                            workflowState=self.wf)
        rec = make_user("tprec", role="Recruiter")
        self.client.force_login(rec)
        page = self.client.get(reverse('ats:talent_pool'))
        self.assertContains(page, "Station 3")                  # Match sichtbar
        self.assertContains(page, "Auf Stelle hinweisen")
        from ..models import TalentPoolSubscription
        sub = TalentPoolSubscription.objects.get_by_email("timo@x.de")
        r = self.client.post(reverse('ats:talent_pool'),
                             data={"contact_sub_id": str(sub.id),
                                   "job_id": str(new_job.id)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("timo@x.de", mail.outbox[0].to)
        self.assertIn("Station 3", mail.outbox[0].subject)
        self.assertIn("austreten", mail.outbox[0].body)         # Widerrufs-Hinweis
        self.assertTrue(AuditLog.objects.filter(action="TALENT_POOL_CONTACTED").exists())
        # Zweite Ansprache auf dieselbe Stelle: blockiert
        self.client.post(reverse('ats:talent_pool'),
                         data={"contact_sub_id": str(sub.id),
                               "job_id": str(new_job.id)})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(TalentPoolContact.objects.count(), 1)
        page = self.client.get(reverse('ats:talent_pool'))
        self.assertContains(page, "hingewiesen am")

    def test_expired_subscription_not_matched(self):
        from ..models import JobPosting, TalentPoolSubscription
        self._world()
        self._join()
        TalentPoolSubscription.objects.filter_by_email("timo@x.de").update(
            expiresAt=timezone.now() - datetime.timedelta(days=1))
        JobPosting.objects.create(title="Pflegefachkraft Station 3",
                                  organization=self.org, facility=self.fac,
                                  location=self.loc, jobFamily=self.fam,
                                  workflowState=self.wf)
        rec = make_user("tprec2", role="Recruiter")
        self.client.force_login(rec)
        page = self.client.get(reverse('ats:talent_pool'))
        self.assertContains(page, "abgelaufen")
        self.assertNotContains(page, "Auf Stelle hinweisen")    # kein Match, kein Button

class ProcessMemoryTestCase(TestCase):
    """Prozess-Gedaechtnis: zuletzt genutzter Prozess als Default (Weg A)."""

    def _world(self):
        import uuid as _u

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        self.fac_a = Facility.objects.create(name="Klinik A", organization=org)
        self.fac_b = Facility.objects.create(name="Klinik B", organization=org)
        self.fam = JobFamily.objects.create(name="Pflege-" + str(_u.uuid4())[:4])
        wf = WorkflowState.objects.create(name="published")
        import datetime

        from django.utils import timezone
        now = timezone.now()
        self.older_same_fac = JobPosting.objects.create(
            title="Pflegefachkraft Station 1", organization=org,
            facility=self.fac_a, location=loc, jobFamily=self.fam,
            workflowState=wf,
            screeningQuestionsJson=[{"id": "q1", "question": "Examen?",
                                     "type": "YES_NO", "isMandatory": True,
                                     "expectedAnswer": "YES"}],
            tasksJson=["Grundpflege"], requirementsJson=["Examen"],
            createdAt=now - datetime.timedelta(hours=2))
        self.newer_other_fac = JobPosting.objects.create(
            title="Pflegefachkraft Klinik B", organization=org,
            facility=self.fac_b, location=loc, jobFamily=self.fam,
            workflowState=wf,
            screeningQuestionsJson=[{"id": "q9", "question": "Nachtdienst?",
                                     "type": "YES_NO", "isMandatory": False}],
            createdAt=now)
        self.org, self.loc, self.wf = org, loc, wf

    def test_endpoint_prefers_same_facility_and_requires_role(self):
        self._world()
        url = (reverse('ats:process_previous')
               + f"?job_family={self.fam.id}&facility={self.fac_a.id}")
        # Rollen-Schutz (Haertung): ohne Login keine Prozessdaten
        self.assertNotEqual(self.client.get(url).status_code, 200)
        self.client.force_login(make_user("pmrec", role="Recruiter"))
        d = self.client.get(url).json()
        self.assertTrue(d["found"])
        self.assertEqual(d["source_title"], "Pflegefachkraft Station 1")  # gleiche Einrichtung schlaegt neuere fremde
        self.assertEqual(d["screening_questions"][0]["question"], "Examen?")
        # Ohne Einrichtungs-Treffer: juengste der Familie
        d2 = self.client.get(reverse('ats:process_previous')
                             + f"?job_family={self.fam.id}").json()
        self.assertEqual(d2["source_title"], "Pflegefachkraft Klinik B")
        # Unbekannte Familie: found=False
        import uuid as _u
        d3 = self.client.get(reverse('ats:process_previous')
                             + f"?job_family={_u.uuid4()}").json()
        self.assertFalse(d3["found"])

    def test_convert_applies_previous_process(self):
        from ..models import JobPosting, StaffingRequest
        self._world()
        SystemSetting.objects.create(key="APPROVAL_CHAIN", value="HR-Admin")
        req = StaffingRequest.objects.create(
            title="Pflegefachkraft Nachtdienst", facility=self.fac_a,
            jobFamily=self.fam, status="ACCEPTED", justification="intern")
        self.client.force_login(make_user("pmrec2", role="Recruiter"))
        self.client.post(reverse('ats:staffing_requests'), data={
            "form": "convert", "request_id": str(req.id),
            "location": str(self.loc.id)})
        job = JobPosting.objects.get(title="Pflegefachkraft Nachtdienst")
        self.assertIn("Examen?", str(job.screeningQuestionsJson))  # bewaehrter Prozess
        self.assertIn("Grundpflege", job.tasksJson)
        self.assertIn("vervollständigen", job.description)     # Geruest bleibt

class ProcessLadderAndStandardsTestCase(TestCase):
    """Spezifitaets-Leiter, Kaltstart-Fallback, Vorstands-Mindeststandards."""

    def _world(self):
        import uuid as _u

        from ..models import Department, Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        self.loc_hh = Location.objects.create(name="Hamburg")
        self.loc_lg = Location.objects.create(name="Lüneburg")
        self.fac_a = Facility.objects.create(name="Klinik A", organization=org)
        self.fac_b = Facility.objects.create(name="Klinik B", organization=org)
        self.dept = Department.objects.create(name="Station 3", facility=self.fac_a)
        self.fam = JobFamily.objects.create(name="Pflege-" + str(_u.uuid4())[:4])
        self.wf = WorkflowState.objects.create(name="published")
        self.org = org

        def mk(title, fac, loc, dept=None, q=None, days_old=0):
            j = JobPosting.objects.create(
                title=title, organization=org, facility=fac, location=loc,
                department=dept, jobFamily=self.fam, workflowState=self.wf,
                screeningQuestionsJson=q or [])
            if days_old:
                JobPosting.objects.filter(id=j.id).update(
                    createdAt=timezone.now() - datetime.timedelta(days=days_old))
            return j
        # aelteste: gleiche Abteilung; mittel: gleiche Einrichtung; neueste: nur Standort
        self.j_dept = mk("Mit Abteilung", self.fac_a, self.loc_hh, self.dept,
                         q=[{"id": "qd", "question": "Abteilungsfrage?",
                             "type": "YES_NO", "isMandatory": True}],
                         days_old=30)
        self.j_fac = mk("Mit Einrichtung", self.fac_a, self.loc_hh, None,
                        q=[{"id": "qf", "question": "Einrichtungsfrage?",
                            "type": "YES_NO", "isMandatory": False}],
                        days_old=15)
        self.j_loc = mk("Nur Standort", self.fac_b, self.loc_hh, None, days_old=1)

    def test_ladder_department_beats_facility_beats_location(self):
        self._world()
        self.client.force_login(make_user("ladrec", role="Recruiter"))
        base = reverse('ats:process_previous') + f"?job_family={self.fam.id}"
        d = self.client.get(base + f"&facility={self.fac_a.id}"
                            f"&department={self.dept.id}&location={self.loc_hh.id}").json()
        self.assertEqual(d["source_title"], "Mit Abteilung")   # trotz aelter
        self.assertEqual(d["scope"], "gleiche Abteilung")
        d = self.client.get(base + f"&facility={self.fac_a.id}&location={self.loc_hh.id}").json()
        self.assertEqual(d["source_title"], "Mit Einrichtung")
        self.assertEqual(d["scope"], "gleiche Einrichtung")
        d = self.client.get(base + f"&location={self.loc_hh.id}").json()
        self.assertEqual(d["source_title"], "Nur Standort")    # juengste am Standort
        self.assertEqual(d["scope"], "gleicher Standort")

    def test_cold_start_falls_back_to_rulebook(self):
        import uuid as _u

        from ..models import JobFamily
        fam = JobFamily.objects.create(name="Pflegefachkraft-" + str(_u.uuid4())[:4])
        self.client.force_login(make_user("coldrec", role="Recruiter"))
        d = self.client.get(reverse('ats:process_previous')
                            + f"?job_family={fam.id}&title=Pflegefachkraft").json()
        self.assertTrue(d["found"])
        self.assertEqual(d["source"], "REGELWERK")
        self.assertIn("Regelwerk", d["scope"])
        self.assertTrue(any("Examen" in q["question"] for q in d["screening_questions"]))

    def test_minimum_standards_enforced_and_not_weakenable(self):
        from ..models import AuditLog, JobPosting
        self._world()
        self.fam.minimumQuestionsJson = [{
            "id": "min-fzg",
            "question": "Liegt ein erweitertes Führungszeugnis vor?",
            "type": "YES_NO", "isMandatory": True,
            "expectedAnswer": "YES"}]
        self.fam.save()
        rec = make_user("stdrec", role="Recruiter")
        self.client.force_login(rec)
        # Stelle OHNE die Pflichtfrage speichern -> Server fuegt sie ein
        self.client.post(reverse('ats:create_job'), data={
            "title": "Erzieher Kita Nord", "description": "x",
            "tasks": "Betreuung", "requirements": "Ausbildung",
            "screening_questions": '[{"id":"q1","question":"Eigene Frage?","type":"YES_NO","isMandatory":false}]',
            "facility": str(self.fac_a.id), "location": str(self.loc_hh.id),
            "job_family": str(self.fam.id), "workflow_state": str(self.wf.id)})
        job = JobPosting.objects.get(title="Erzieher Kita Nord")
        self.assertIn("Führungszeugnis", str(job.screeningQuestionsJson))
        self.assertTrue(AuditLog.objects.filter(action="MINIMUM_STANDARD_APPLIED").exists())
        # Versuch, die Pflichtfrage auf optional abzuschwaechen -> erzwungen True
        import json as _json
        weakened = job.screeningQuestionsJson
        for q in weakened:
            q["isMandatory"] = False
        self.client.post(reverse('ats:create_job'), data={
            "job_id": str(job.id), "title": job.title, "description": "x",
            "tasks": "Betreuung", "requirements": "Ausbildung",
            "screening_questions": _json.dumps(weakened),
            "facility": str(self.fac_a.id), "location": str(self.loc_hh.id),
            "job_family": str(self.fam.id), "workflow_state": str(self.wf.id)})
        job.refresh_from_db()
        fzg = next(q for q in job.screeningQuestionsJson
                   if q["id"] == "min-fzg")
        self.assertTrue(fzg["isMandatory"])                    # nicht abschwaechbar
        # eigene Frage darf optional bleiben
        own = next(q for q in job.screeningQuestionsJson
                   if q["id"] == "q1")
        self.assertFalse(own["isMandatory"])

    def test_standards_management_requires_hr_admin(self):
        self._world()
        self.client.force_login(make_user("stdrec2", role="Recruiter"))
        r = self.client.post(reverse('ats:screening_questions'), data={
            "form": "minimum", "family_id": str(self.fam.id),
            "minimum_json": '[]'})
        self.assertEqual(r.status_code, 403)                   # nur HR-Admin
        self.client.force_login(make_user("stdadmin", role="HR-Admin"))
        r = self.client.post(reverse('ats:screening_questions'), data={
            "form": "minimum", "family_id": str(self.fam.id),
            "minimum_json": 'kein json'})
        self.assertContains(r, "Ungültiges JSON")              # nichts kaputt gespeichert
        self.fam.refresh_from_db()
        self.assertEqual(self.fam.minimumQuestionsJson, [])
