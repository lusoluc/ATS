"""SecurATS-Tests: analytics (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .utils import make_user


class AnalyticsWP5TestCase(TestCase):
    """WP5: Prognose, Anomalien, Fairness, Benchmark, Export, KI-Analyst-Fallback."""

    def _fixture(self):
        import uuid as _u
        from datetime import timedelta

        from django.utils import timezone as tz

        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        self.loc_b = Location.objects.create(name="Berlin")
        self.loc_m = Location.objects.create(name="Muenchen")
        fac = Facility.objects.create(name="F", organization=org)
        self.fam = JobFamily.objects.create(name="Pflege-" + str(_u.uuid4())[:4])
        wf = WorkflowState.objects.create(name="published")
        self.job_b = JobPosting.objects.create(title="Pflege B", organization=org, facility=fac,
                                               location=self.loc_b, jobFamily=self.fam, workflowState=wf)
        self.job_m = JobPosting.objects.create(title="Pflege M", organization=org, facility=fac,
                                               location=self.loc_m, jobFamily=self.fam, workflowState=wf)
        mk = 0
        def app(job, status, ai=None, days_old=0, src="DIRECT"):
            nonlocal mk
            mk += 1
            ap = Applicant.objects.create(firstName=f"F{mk}", lastName="T", email=f"a{mk}@x.de")
            a = Application.objects.create(applicant=ap, jobPosting=job, status=status,
                                           aiScore=ai, source=src)
            if days_old:
                Application.objects.filter(id=a.id).update(
                    createdAt=tz.now() - timedelta(days=days_old))
                a.refresh_from_db()
            return a
        # Historie: 2 Einladungen in Berlin (schnell), Altfälle NEW (stale)
        app(self.job_b, "INVITED", ai="A")
        app(self.job_b, "INVITED", ai="D")          # Mensch lädt trotz D ein -> Override
        app(self.job_b, "REJECTED", ai="A")         # Absage trotz A -> Override
        app(self.job_b, "NEW", days_old=30)          # stale
        for _i in range(5):
            app(self.job_m, "NEW", src="STEPSTONE")  # Quelle ohne Einladungen
        return Application.objects.all()

    def test_pure_analytics_functions(self):
        from ..analytics import (
            cost_per_hire,
            detect_anomalies,
            fairness_overview,
            location_benchmark,
            time_to_fill_forecast,
        )
        from ..models import JobPosting
        apps = self._fixture()
        fc = time_to_fill_forecast(apps, JobPosting.objects.all())
        self.assertEqual(len(fc['rows']), 2)
        self.assertIsNotNone(fc['global_avg'])

        titles = [f['title'] for f in detect_anomalies(apps)]
        self.assertTrue(any("Erstsichtung" in t for t in titles))          # stale
        self.assertTrue(any("STEPSTONE" in t for t in titles))             # Quelle ohne Qualität

        fair = fairness_overview(apps)
        self.assertEqual(fair['invited_low'], 1)
        self.assertEqual(fair['rejected_high'], 1)
        self.assertIn("geschützte merkmale", fair['note'].lower())

        bench = location_benchmark(apps)
        berlin = next(b for b in bench if b['location'] == "Berlin")
        self.assertEqual(berlin['invited'], 2)

        costs = cost_per_hire(apps, {"STEPSTONE": 1000.0})
        self.assertIsNone(costs[0]['cost_per_hire'])  # keine Einladungen -> ehrlich None

    def test_export_is_scoped_and_audited(self):
        from ..models import AuditLog, UserScope
        self._fixture()
        rec = make_user("wp5rec", role="Recruiter")
        sc = UserScope.objects.create(user=rec, full_access=False)
        sc.locations.add(self.loc_b)
        self.client.force_login(rec)
        r = self.client.get(reverse('ats:analytics_export'))
        self.assertEqual(r.status_code, 200)
        body = r.content.decode('utf-8')
        self.assertIn("Pflege B", body)
        self.assertNotIn("Pflege M", body)  # BOLA: München nicht im Export
        self.assertTrue(AuditLog.objects.filter(action="ANALYTICS_EXPORT").exists())

    def test_ask_fallback_without_ollama(self):
        self._fixture()
        rec = make_user("wp5ask", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.post(reverse('ats:analytics_ask'), data={"question": "Wie läuft es?"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data["used_ai"])            # kein Ollama im Test
        self.assertIn("ai_doctor", data["answer"])   # klare Handlungsanweisung

    def test_analytics_page_renders_wp5_sections(self):
        self._fixture()
        admin = make_user("wp5admin", role="HR-Admin")
        self.client.force_login(admin)
        resp = self.client.get(reverse('ats:analytics'))
        self.assertContains(resp, "Time-to-Fill-Prognose")
        self.assertContains(resp, "Fairness-Cockpit")
        self.assertContains(resp, "Standort-Benchmarking")  # Leitung sieht Benchmark
        self.assertContains(resp, "Frag deine Daten")

class PricingTestCase(TestCase):
    """P0.3: Preisseite nur auf der Demo-Instanz; Zahlen konsistent mit PRICING.md."""

    def test_pricing_hidden_on_customer_instances(self):
        # Kundeninstanz (kein DEMO_MODE): Karriereseite zeigt keine Anbieterpreise
        self.assertEqual(self.client.get('/preise/').status_code, 404)

    @override_settings(DEMO_MODE=True)
    def test_pricing_visible_on_demo_with_consistent_numbers(self):
        r = self.client.get('/preise/')
        self.assertEqual(r.status_code, 200)
        for expected in ["390", "690", "990", "2.900", "je Einrichtung",
                         "Design-Partner", "Open Source"]:
            self.assertContains(r, expected)
        # Konsistenz: dieselben Preispunkte stehen im Hypothesen-Dokument
        with open("PRICING.md", encoding="utf-8") as fh:
            doc = fh.read()
        for n in ["390", "690", "990", "2.900"]:
            self.assertIn(n, doc)

class AppointmentAnalyticsTestCase(TestCase):
    """Termin-Analytik: die Selbstservice-Interaktionen werten sich selbst aus."""

    def _interact(self):
        """Erzeugt Interaktionen ueber die ECHTEN Flows (nicht direkt in die DB)."""
        import uuid as _u

        from ..models import (
            Applicant,
            ApplicantToken,
            Application,
            Facility,
            InterviewSlot,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(title="Pflegefachkraft", organization=org,
                                             facility=fac, location=loc,
                                             jobFamily=fam, workflowState=wf)
        ap = Applicant.objects.create(firstName="Sofia", lastName="R", email="sofia@x.de")
        self.app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                              status="IN_REVIEW")
        ApplicantToken.objects.create(applicant=ap, token="ana-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=30))
        start = timezone.now() + datetime.timedelta(days=3)
        self.slot = InterviewSlot.objects.create(
            jobPosting=self.job, kind="VIDEO", startTime=start,
            endTime=start + datetime.timedelta(minutes=45))
        # Verfallener Slot (Vergangenheit, ungebucht)
        past = timezone.now() - datetime.timedelta(days=5)
        InterviewSlot.objects.create(jobPosting=self.job, startTime=past,
                                     endTime=past + datetime.timedelta(minutes=45))
        rec = make_user("anarec", role="Recruiter")
        self.client.force_login(rec)
        # Einladung "Bewerber:in waehlt" -> Selbstbuchung -> Aenderungswunsch
        self.client.post(reverse('ats:schedule_interview'), data={
            "application_id": str(self.app.id), "slot_id": "CANDIDATE_CHOICE",
            "location_type": "VIDEO", "message_text": "Bitte Termin wählen."})
        self.client.post(reverse('ats:candidate_portal', args=["ana-token"]),
                         data={"book_app_id": str(self.app.id),
                               "book_slot_id": str(self.slot.id)})
        from ..models import Interview
        iv = Interview.objects.get(application=self.app)
        self.client.post(reverse('ats:candidate_portal', args=["ana-token"]),
                         data={"change_request_interview_id": str(iv.id),
                               "reason": "Geht es eine Stunde später?"})
        return rec

    def test_stats_reflect_real_interactions(self):
        from ..analytics import appointment_stats
        from ..models import Application, JobPosting
        self._interact()
        stats = appointment_stats(Application.objects.all(), JobPosting.objects.all())
        self.assertEqual(stats["self_booked"], 1)
        self.assertEqual(stats["self_booking_share"], 100)    # einziger Termin: Portal
        self.assertEqual(stats["change_requests"], 1)
        self.assertEqual(stats["cancelled"], 0)
        self.assertIsNotNone(stats["median_hours_to_choice"])  # Paar Einladung->Wahl
        self.assertLess(stats["median_hours_to_choice"], 1)
        self.assertEqual(stats["slots_expired"], 1)            # verfallener Slot gezaehlt
        self.assertEqual(stats["slots_used"], 0)               # gebuchter liegt in Zukunft
        self.assertEqual(dict(stats["kinds"]).get("Video-Gespräch"), 1)

    def test_hint_on_expired_slots(self):
        import uuid as _u

        from ..analytics import appointment_stats
        from ..models import (
            Application,
            Facility,
            InterviewSlot,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O2")
        loc = Location.objects.create(name="B")
        fac = Facility.objects.create(name="F2", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="MFA", organization=org, facility=fac,
                                        location=loc, jobFamily=fam, workflowState=wf)
        for i in range(6):                                     # 6 verfallene Slots
            past = timezone.now() - datetime.timedelta(days=i + 1)
            InterviewSlot.objects.create(jobPosting=job, startTime=past,
                                         endTime=past + datetime.timedelta(minutes=45))
        stats = appointment_stats(Application.objects.all(), JobPosting.objects.all())
        self.assertEqual(stats["utilization"], 0)
        self.assertTrue(any("ungenutzt" in h for h in stats["hints"]))

    def test_analytics_page_shows_aggregates_without_pii(self):
        self._interact()
        r = self.client.get(reverse('ats:analytics'))
        self.assertContains(r, "Termine &amp; Selbstbuchung")
        self.assertContains(r, "selbst gebucht")
        self.assertContains(r, "Median bis zur Terminwahl")
        self.assertNotContains(r, "Sofia")                     # datensparsam: kein Name

class SourceChannelTestCase(TestCase):
    """Jobmesse-Zyklus: Kanal -> QR-Link -> Bewerbung -> Erfolgs-Auswertung."""

    def _world(self):
        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="SC-Fam")
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(title="Pflegefachkraft",
                                             organization=org, facility=fac,
                                             location=loc, jobFamily=fam,
                                             workflowState=wf,
                                             screeningQuestionsJson=[])

    def _apply(self, email):
        return self.client.post(reverse('ats:bewerben', args=[self.job.id]),
                                data={"first_name": "Mia", "last_name": "K",
                                      "email": email, "consent_privacy": "on",
                                      "cv_file": SimpleUploadedFile("cv.pdf",
                                                                    b"%PDF-1.4")})

    def test_src_survives_list_to_application_via_session(self):
        from ..models import Application
        self._world()
        # Messe-QR fuehrt auf die LISTE – Quelle darf beim Klick nicht verloren gehen
        self.client.get("/jobs/?src=JOBMESSE_HH_2026")
        self.client.get(reverse('ats:job_detail', args=[self.job.id]))  # ohne ?src
        self._apply("mia1@x.de")
        app = Application.objects.get()
        self.assertEqual(app.source, "JOBMESSE_HH_2026")
        # Ohne Kampagne: DIRECT (neue Session)
        self.client.session.flush()
        self._apply("mia2@x.de")
        self.assertEqual(Application.objects.exclude(id=app.id).get().source,
                         "DIRECT")

    def test_channel_page_creates_and_reports(self):
        from ..models import Applicant, Application, SourceChannel
        self._world()
        self.client.force_login(make_user("chanrec", role="Recruiter"))
        self.client.post(reverse('ats:source_channels'),
                         data={"name": "Jobmesse Hamburg 09/2026",
                               "note": "Stand B4, 1.200 € Standkosten"})
        ch = SourceChannel.objects.get()
        self.assertEqual(ch.slug, "JOBMESSE_HAMBURG_092026")
        # 2 Bewerbungen ueber den Kanal, 1 davon eingeladen
        for i, status in enumerate(["NEW", "INVITED"]):
            ap = Applicant.objects.create(firstName="K", lastName=str(i),
                                          email=f"k{i}@x.de")
            Application.objects.create(applicant=ap, jobPosting=self.job,
                                       status=status, source=ch.slug)
        page = self.client.get(reverse('ats:source_channels'))
        self.assertContains(page, "Jobmesse Hamburg 09/2026")
        self.assertContains(page, f"?src={ch.slug}")           # kopierbarer Link
        self.assertContains(page, "data:image/svg+xml")        # QR fuer Aufsteller
        self.assertContains(page, "50&nbsp;%")                 # Einladungsquote
        self.assertContains(page, "Standkosten")
        # Namens-Kollision -> eindeutiger Slug
        self.client.post(reverse('ats:source_channels'),
                         data={"name": "Jobmesse Hamburg 09/2026"})
        self.assertEqual(SourceChannel.objects.count(), 2)
        self.assertTrue(SourceChannel.objects.filter(
            slug="JOBMESSE_HAMBURG_092026_2").exists())

    def test_channel_page_requires_staff(self):
        self._world()
        r = self.client.get(reverse('ats:source_channels'))
        self.assertNotEqual(r.status_code, 200)                # Login noetig

class AnalyticsCoverageTestCase(TestCase):
    """Garantie: Jede NEUE Seite ist automatisch in der Analytics –
    ohne Registrierungs-Schritt, ohne Konfiguration."""

    def test_new_landing_page_appears_automatically(self):
        from ..models import LandingPage
        LandingPage.objects.create(name="Spontane Aktion Pflegetag",
                                   slug="pflegetag", views=3)
        self.client.force_login(make_user("acrec", role="Recruiter"))
        analytics = self.client.get(reverse('ats:analytics'))
        self.assertContains(analytics, "Spontane Aktion Pflegetag")

    def test_new_cms_page_counts_and_appears_automatically(self):
        from ..models import Page
        pg = Page.objects.create(title="Haus Elbblick im Porträt",
                                 slug="haus-elbblick", status="published")
        self.client.get("/pages/haus-elbblick/")
        self.client.get("/pages/haus-elbblick/")
        pg.refresh_from_db()
        self.assertEqual(pg.views, 2)                          # Selbstmessung
        self.client.force_login(make_user("acrec2", role="Recruiter"))
        analytics = self.client.get(reverse('ats:analytics'))
        self.assertContains(analytics, "Haus Elbblick im Porträt")
        self.assertContains(analytics, "/pages/haus-elbblick/")

    def test_cms_page_visit_sets_no_campaign_source(self):

        from ..models import Application, Facility, JobFamily, JobPosting, Location, Organization, Page, WorkflowState
        Page.objects.create(title="Impressum", slug="impressum-ac",
                            status="published")
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="AC-Fam")
        wf = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="Stelle", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=wf,
                                        screeningQuestionsJson=[])
        self.client.get("/pages/impressum-ac/")                # Inhaltsseite
        self.assertIsNone(self.client.session.get("application_src"))
        self.client.post(reverse('ats:bewerben', args=[job.id]),
                         data={"first_name": "N", "last_name": "S",
                               "email": "ns@x.de", "consent_privacy": "on",
                               "cv_file": SimpleUploadedFile("cv.pdf",
                                                             b"%PDF-1.4")})
        self.assertEqual(Application.objects.get().source, "DIRECT")
        # Draft-Seiten zaehlen nicht und erscheinen nicht
        from ..models import Page as _P
        _P.objects.create(title="Entwurf X", slug="entwurf-x",
                          status="draft")
        self.assertEqual(self.client.get("/pages/entwurf-x/").status_code, 404)
        self.client.force_login(make_user("acrec3", role="Recruiter"))
        analytics = self.client.get(reverse('ats:analytics'))
        self.assertNotContains(analytics, "Entwurf X")

class ChannelCostTestCase(TestCase):
    """P0-6: Kampagnenkosten strukturiert am Kanal."""

    def test_cost_set_shown_and_feeds_cost_per_hire(self):
        from ..analytics import cost_per_hire
        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            SourceChannel,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="CC-Fam")
        wf = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="Stelle", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=wf)
        ch = SourceChannel.objects.create(name="Jobmesse", slug="MESSE_CC",
                                          note="Stand B4")
        ap = Applicant.objects.create(firstName="K", lastName="M",
                                      email="km-cc@x.de")
        Application.objects.create(applicant=ap, jobPosting=job,
                                   status="HIRED", source="MESSE_CC",
                                   hiredAt=timezone.now())
        self.client.force_login(make_user("ccrec", role="Recruiter"))
        # Kosten mit deutschem Format setzen; nur costAmount aendert sich
        self.client.post(reverse('ats:source_channels'), data={
            "form": "cost", "ch_id": str(ch.id), "cost": "1.200,00"})
        ch.refresh_from_db()
        self.assertEqual(str(ch.costAmount), "1200.00")
        self.assertEqual(ch.note, "Stand B4")                  # unberuehrt
        page = self.client.get(reverse('ats:source_channels'))
        self.assertContains(page, "Kosten je Einstellung")
        self.assertContains(page, "1200&nbsp;€")               # 1200/1 Hire
        # Analytics-Bruecke: Kanal-Kosten wirken ohne SystemSetting
        rows = cost_per_hire(Application.objects.all(),
                             {"MESSE_CC": float(ch.costAmount)})
        self.assertEqual(rows[0].get("hires", rows[0].get("count")), 1)

class HeadcountTestCase(TestCase):
    """P1-7: Mehrfachbedarf je Stelle + Besetzt-Logik."""

    def _world(self, headcount=2):
        from ..models import Facility, JobFamily, JobPosting, LandingPage, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        self.fac = Facility.objects.create(name="Haus Nord", organization=org)
        fam = JobFamily.objects.create(name="HC-Fam")
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Pflegefachkraft Nord", organization=org,
            facility=self.fac, location=loc, jobFamily=fam,
            workflowState=wf, headcount=headcount,
            screeningQuestionsJson=[])
        LandingPage.objects.create(name="LP", slug="hc-lp",
                                   facility=self.fac)

    def _hire_one(self, email):
        from ..models import Applicant, Application
        ap = Applicant.objects.create(firstName="H", lastName="C",
                                      email=email)
        app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                         status="INVITED")
        return self.client.post(
            reverse('ats:update_status', args=[app.id]),
            data={"status": "HIRED"})

    def test_filled_job_hidden_publicly_but_reachable(self):
        self._world(headcount=2)
        self.client.force_login(make_user("hcrec", role="Recruiter"))
        r1 = self._hire_one("hc1@x.de")
        self.assertIsNone(r1.json().get("notice"))             # 1/2: kein Hinweis
        self.assertContains(self.client.get("/jobs/"),
                            "Pflegefachkraft Nord")            # noch sichtbar
        r2 = self._hire_one("hc2@x.de")
        self.assertIn("besetzt", r2.json()["notice"])          # 2/2: Hinweis
        # Oeffentlich ausgeblendet: Stellenboerse UND Landingpage
        self.assertNotContains(self.client.get("/jobs/"),
                               "Pflegefachkraft Nord")
        self.assertNotContains(
            self.client.get(reverse('ats:landing_page', args=["hc-lp"])),
            "Pflegefachkraft Nord")
        # Direktlink bleibt erreichbar – mit Banner statt Blockade
        detail = self.client.get(reverse('ats:job_detail',
                                         args=[self.job.id]))
        self.assertContains(detail, "bereits besetzt")
        self.assertEqual(
            self.client.get(reverse('ats:bewerben',
                                    args=[self.job.id])).status_code, 200)

    def test_wizard_sets_and_edit_preserves_headcount(self):
        from ..models import JobPosting
        self._world()
        self.client.force_login(make_user("hcadmin", role="HR-Admin"))
        JobPosting.objects.filter(id=self.job.id).update(headcount=3)
        # Edit-POST OHNE headcount-Feld darf den Bestand nicht ueberschreiben
        self.client.post(reverse('ats:create_job'), data={
            "job_id": str(self.job.id), "title": "Pflegefachkraft Nord",
            "description": "x", "tasks": "", "requirements": "",
            "screening_questions": "[]",
            "facility": str(self.job.facility_id),
            "location": str(self.job.location_id),
            "job_family": str(self.job.jobFamily_id)})
        self.job.refresh_from_db()
        self.assertEqual(self.job.headcount, 3)                # Bestand bleibt
        # Mit Feld: geklemmt auf 1..99
        self.client.post(reverse('ats:create_job'), data={
            "job_id": str(self.job.id), "title": "Pflegefachkraft Nord",
            "description": "x", "tasks": "", "requirements": "",
            "screening_questions": "[]", "headcount": "150",
            "facility": str(self.job.facility_id),
            "location": str(self.job.location_id),
            "job_family": str(self.job.jobFamily_id)})
        self.job.refresh_from_db()
        self.assertEqual(self.job.headcount, 99)

class BottleneckTrafficLightTestCase(TestCase):
    """Engpass-Ampel: gruen/gelb/rot je Wartezeit."""

    def _world(self):

        from ..models import Facility, JobFamily, Organization
        org = Organization.objects.create(name="O")
        self.fac = Facility.objects.create(name="Z", organization=org)
        JobFamily.objects.create(name="TL-Fam")
        for role in ("Schnell", "Mittel", "Langsam"):
            Group.objects.get_or_create(name=role)
        self.u = make_user("tl-u", role="Hiring-Manager")

    def _req_with_step(self, role, wait_days):
        from ..models import JobFamily, RequisitionStep, StaffingRequest
        req = StaffingRequest.objects.create(
            title="T", facility=self.fac, jobFamily=JobFamily.objects.get(),
            headcount=1, justification="x", requestedBy=self.u,
            status="IN_APPROVAL")
        StaffingRequest.objects.filter(id=req.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=wait_days + 1))
        req.refresh_from_db()
        st = RequisitionStep.objects.create(request=req, role=role, order=1)
        st.status = "APPROVED"
        st.decidedAt = req.createdAt + datetime.timedelta(days=wait_days)
        st.save()
        return req

    def test_levels_map_to_thresholds(self):
        from ..analytics import requisition_stage_stats
        from ..models import StaffingRequest
        self._world()
        self._req_with_step("Schnell", 2)     # <=3 -> green
        self._req_with_step("Mittel", 5)      # 4-7 -> amber
        self._req_with_step("Langsam", 12)    # >7  -> red
        rows = {r['role']: r['level']
                for r in requisition_stage_stats(StaffingRequest.objects.all())}
        self.assertEqual(rows["Schnell"], "green")
        self.assertEqual(rows["Mittel"], "amber")
        self.assertEqual(rows["Langsam"], "red")
