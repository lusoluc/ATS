"""SecurATS-Tests: misc (aufgeteilt aus der frueheren Monolith-tests.py)."""
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ..models import SystemSetting
from .utils import User, make_user


class BacklogFeaturesTestCase(TestCase):
    """B1/B2/B8/B11/B15 – Auth-Schutz und Kernverhalten."""

    def setUp(self):
        self.client = Client()
        make_user("hradmin3", role="HR-Admin")
        make_user("rec3", role="Recruiter")

    # B1 – CV-Download
    def test_cv_download_requires_login(self):
        import uuid as _u
        resp = self.client.get(reverse('ats:download_cv', args=[_u.uuid4()]))
        self.assertEqual(resp.status_code, 302)

    def test_cv_download_recruiter_missing_app_404(self):
        import uuid as _u
        self.client.force_login(User.objects.get(username="rec3"))
        resp = self.client.get(reverse('ats:download_cv', args=[_u.uuid4()]))
        self.assertEqual(resp.status_code, 404)

    def test_write_audit_records_user(self):
        from ..audit import write_audit
        from ..models import AuditLog
        u = User.objects.get(username="rec3")
        u.is_authenticated  # noqa
        # simulate authenticated user object
        class _U:
            is_authenticated = True
            def get_username(self_inner): return "rec3"
        write_audit("READ_CV", user=_U(), application_id=None, storage="x")
        self.assertTrue(AuditLog.objects.filter(action="READ_CV", userId="rec3").exists())

    # B2 – Audit-Viewer
    def test_audit_viewer_hr_admin_ok_recruiter_forbidden(self):
        from ..models import AuditLog
        AuditLog.objects.create(action="READ_CV", userId="x")
        self.client.force_login(User.objects.get(username="rec3"))
        self.assertEqual(self.client.get(reverse('ats:audit_log')).status_code, 403)
        self.client.force_login(User.objects.get(username="hradmin3"))
        resp = self.client.get(reverse('ats:audit_log'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "READ_CV")

    # B11 – Talent-Pool
    def test_talent_pool_view(self):
        from datetime import timedelta

        from ..models import TalentPoolSubscription
        TalentPoolSubscription.objects.create(
            email="pool@example.org", consentId="c1",
            expiresAt=timezone.now() + timedelta(days=30))
        self.client.force_login(User.objects.get(username="rec3"))
        resp = self.client.get(reverse('ats:talent_pool'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "pool@example.org")

    # B15 – Screening-Fragen
    def test_screening_question_add(self):
        from ..models import ScreeningQuestion
        self.client.force_login(User.objects.get(username="hradmin3"))
        resp = self.client.post(reverse('ats:screening_questions'),
                                data={"question": "Führerschein Klasse B?"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(ScreeningQuestion.objects.filter(question="Führerschein Klasse B?").exists())

    # B8 – Delegationen
    def test_delegations_view(self):
        self.client.force_login(User.objects.get(username="hradmin3"))
        self.assertEqual(self.client.get(reverse('ats:delegations')).status_code, 200)

class BacklogP3TestCase(TestCase):
    """B7/B10/B16/B17/B18 – Analytics, Ordering, Seiten, Medien."""

    def _app(self, source="DIRECT"):
        import uuid as _u

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
        loc = Location.objects.create(name="Berlin")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="W-" + str(_u.uuid4())[:6])
        job = JobPosting.objects.create(title="Stelle", organization=org, facility=fac,
                                        location=loc, jobFamily=fam, workflowState=wf)
        ap = Applicant.objects.create(firstName="X", lastName="Y",
                                      email=str(_u.uuid4())[:8] + "@ex.org")
        return Application.objects.create(applicant=ap, jobPosting=job, source=source)

    def setUp(self):
        self.client = Client()
        make_user("hradmin6", role="HR-Admin")
        make_user("rec6", role="Recruiter")

    def test_analytics_view(self):
        self._app(source="STEPSTONE")
        self._app(source="DIRECT")
        self.client.force_login(User.objects.get(username="rec6"))
        resp = self.client.get(reverse('ats:analytics'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Bewerbungen gesamt")
        self.assertContains(resp, "STEPSTONE")

    def test_kanban_order_persisted(self):
        app = self._app()
        self.client.force_login(User.objects.get(username="rec6"))
        resp = self.client.post(reverse('ats:update_status', args=[app.id]),
                                data={"status": "IN_REVIEW", "order": "5"})
        self.assertEqual(resp.status_code, 200)
        from ..models import Application
        self.assertEqual(Application.objects.get(id=app.id).boardOrder, 5)

    def test_page_create_and_public_render(self):
        self.client.force_login(User.objects.get(username="hradmin6"))
        resp = self.client.post(reverse('ats:pages_manage'),
                                data={"title": "Über uns", "slug": "ueber-uns",
                                      "content": "Wir sind SecurATS.", "navEnabled": "on"})
        self.assertEqual(resp.status_code, 302)
        from ..models import Page
        self.assertTrue(Page.objects.filter(slug="ueber-uns").exists())
        # öffentlich abrufbar
        pub = self.client.get(reverse('ats:page_detail', args=["ueber-uns"]))
        self.assertEqual(pub.status_code, 200)
        self.assertContains(pub, "Wir sind SecurATS.")

    def test_page_detail_404_for_unknown(self):
        self.assertEqual(self.client.get(reverse('ats:page_detail', args=["nope"])).status_code, 404)

    def test_media_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                self.client.force_login(User.objects.get(username="hradmin6"))
                from ..models import MediaAsset
                # WP8/WCAG 1.1.1: ohne Alt-Text kein Upload – auch bei
                # direktem POST am (required-)Formular vorbei.
                f = SimpleUploadedFile("logo.txt", b"hello", content_type="text/plain")
                resp = self.client.post(reverse('ats:media_manage'), data={"file": f})
                self.assertEqual(resp.status_code, 302)
                self.assertEqual(MediaAsset.objects.count(), 0)
                f2 = SimpleUploadedFile("logo.txt", b"hello", content_type="text/plain")
                resp = self.client.post(reverse('ats:media_manage'),
                                        data={"file": f2, "altText": "Firmenlogo"})
                self.assertEqual(resp.status_code, 302)
                self.assertEqual(MediaAsset.objects.count(), 1)
                self.assertEqual(MediaAsset.objects.first().altText, "Firmenlogo")

class InlineFormErrorsTestCase(TestCase):
    """WCAG 3.3.1/3.3.2 + Robustheit: serverseitige Inline-Formularfehler."""

    def _job(self):
        import uuid as _u

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="B")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        return JobPosting.objects.create(title="Testjob", organization=org, facility=fac,
                                         location=loc, jobFamily=fam, workflowState=wf)

    def test_empty_post_creates_nothing_and_shows_errors(self):
        from ..models import Applicant, Application
        job = self._job()
        r = self.client.post(reverse('ats:bewerben', args=[job.id]), data={
            "consent_privacy": ""})  # direkter POST ohne Pflichtfelder
        self.assertEqual(r.status_code, 200)
        # Robustheit: KEIN Bewerber mit leerer E-Mail (Blind-Index-Kollision verhindert)
        self.assertEqual(Applicant.objects.count(), 0)
        self.assertEqual(Application.objects.count(), 0)
        # WCAG: Zusammenfassung + Feldfehler mit ARIA
        self.assertContains(r, "Bitte prüfen Sie Ihre Angaben")
        self.assertContains(r, 'role="alert"')
        self.assertContains(r, "Vornamen")
        self.assertContains(r, "Lebenslauf")
        self.assertContains(r, 'aria-invalid="true"')
        self.assertContains(r, 'aria-describedby="err-email"')

    def test_invalid_email_keeps_entered_values(self):
        from ..models import Application
        job = self._job()
        r = self.client.post(reverse('ats:bewerben', args=[job.id]), data={
            "first_name": "Marek", "last_name": "Nowak",
            "email": "keine-mail", "consent_privacy": "on",
            "cover_letter": "Ich möchte gern bei Ihnen arbeiten."})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Application.objects.count(), 0)
        self.assertContains(r, "gültige E-Mail-Adresse")
        # Werte-Erhalt: nichts muss neu getippt werden (WCAG 3.3, Frustvermeidung)
        self.assertContains(r, 'value="Marek"')
        self.assertContains(r, 'value="Nowak"')
        self.assertContains(r, "Ich möchte gern bei Ihnen arbeiten.")

    def test_valid_post_still_succeeds(self):
        from ..models import Application
        job = self._job()
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                r = self.client.post(reverse('ats:bewerben', args=[job.id]), data={
                    "first_name": "Ok", "last_name": "Fall", "email": "ok@x.de",
                    "consent_privacy": "on",
                    "cv_file": SimpleUploadedFile("cv.jpg", b"\xff\xd8\xff")})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Application.objects.count(), 1)   # keine Regression

    def test_job_alert_invalid_email_shows_error_not_success(self):
        from ..models import JobAlertSubscription
        r = self.client.post(reverse('ats:job_alert'), data={"email": "quatsch"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(JobAlertSubscription.objects.count(), 0)
        self.assertContains(r, "gültige E-Mail-Adresse")
        self.assertNotContains(r, "Fast geschafft")        # kein Fake-Erfolg
        self.assertContains(r, 'value="quatsch"')          # Eingabe erhalten

class EditRoundTripPreservationTestCase(TestCase):
    """Bestandserhalt-Netz gegen die Speicherfehler-Klasse „Bearbeiten ohne
    Aenderung loescht Daten": Jede Edit-Funktion wird mit exakt den Feldern
    abgesendet, die ihr (vorbefuelltes) Formular liefert – danach darf sich
    KEIN Modellfeld geaendert haben. Neue Edit-Views bekommen hier ihren Test.
    """

    def _snapshot(self, obj):
        from django.forms.models import model_to_dict
        d = model_to_dict(obj)
        # M2M-Felder als sortierte ID-Listen vergleichbar machen
        # (JSONField-Listen enthalten keine Model-Instanzen und bleiben roh)
        return {k: (sorted(str(x.pk) for x in v)
                    if isinstance(v, list) and all(hasattr(x, "pk") for x in v)
                    else v)
                for k, v in d.items()}

    def _assert_unchanged(self, obj, before, ignore=("updatedAt",)):
        import json as _json
        obj.refresh_from_db()
        after = self._snapshot(obj)
        for k in before:
            if k in ignore:
                continue
            a, b = after.get(k), before.get(k)
            if k.endswith("Json") and isinstance(a, str) and isinstance(b, str):
                # Whitespace-Normalisierung beim Re-Serialisieren ist ok –
                # verglichen wird die SEMANTIK, nicht die Formatierung.
                try:
                    a, b = _json.loads(a or "null"), _json.loads(b or "null")
                except ValueError:
                    pass
            self.assertEqual(a, b,
                             f"Feld '{k}' hat sich beim No-Op-Edit geändert!")

    def test_job_noop_edit_preserves_everything(self):
        import json as _json
        import uuid as _u

        from ..models import (
            Benefit,
            ContactPerson,
            Department,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        dept = Department.objects.create(name="Station 1", facility=fac)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        cp = ContactPerson.objects.create(firstName="P", lastName="W",
                                          email="pw@x.de")
        b1 = Benefit.objects.create(name="Jobrad-" + str(_u.uuid4())[:4])
        b2 = Benefit.objects.create(name="Kita-" + str(_u.uuid4())[:4])
        panel_user = make_user("rtpanel", role="Hiring-Manager")
        from ..models import PayBand
        band = PayBand.objects.create(name="RT-Band", minAmount=3100,
                                      maxAmount=3900)
        job = JobPosting.objects.create(
            title="Pflegefachkraft Nacht", organization=org, facility=fac,
            department=dept, location=loc, jobFamily=fam, workflowState=wf,
            contactPerson=cp, description="Beschreibung bleibt.",
            tasksJson=["Grundpflege"], requirementsJson=["Examen"],
            screeningQuestionsJson=[{"id": "q1", "question": "Examen?",
                                     "type": "YES_NO", "isMandatory": True}],
            panelUserIdsJson=[str(panel_user.id)],
            payBand=band)
        job.benefits.set([b1, b2])
        before = self._snapshot(job)
        self.client.force_login(make_user("rtrec", role="Recruiter"))
        # Exakt die Felder des (vorbefuellten) Job-Formulars – nichts geaendert:
        r = self.client.post(reverse('ats:create_job'), data={
            "job_id": str(job.id), "title": job.title,
            "description": job.description,
            "tasks": "Grundpflege", "requirements": "Examen",
            "screening_questions": _json.dumps(job.screeningQuestionsJson),
            "facility": str(fac.id), "department": str(dept.id),
            "location": str(loc.id), "job_family": str(fam.id),
            "contact_person": str(cp.id), "job_template": "",
            "workflow_state": str(wf.id),
            "pay_band": str(band.id),
            "benefits": [str(b1.id), str(b2.id)],
            "panel_members_present": "1",
            "panel_members": [str(panel_user.id)],
        })
        self.assertIn(r.status_code, (200, 302))
        self._assert_unchanged(job, before)
        self.assertEqual(sorted(str(b.id) for b in job.benefits.all()),
                         sorted([str(b1.id), str(b2.id)]))

    def test_contact_person_noop_edit(self):
        from ..models import ContactPerson
        cp = ContactPerson.objects.create(
            firstName="Petra", lastName="Wolf", email="p.wolf@x.de",
            phone="040-99", globalJobTitle="Leitung Recruiting",
            photoUrl="https://intern/p.jpg", quote="Wir suchen Menschen.")
        before = self._snapshot(cp)
        self.client.force_login(make_user("rtrec2", role="Recruiter"))
        self.client.post(reverse('ats:contacts'), data={
            "cp_id": str(cp.id), "firstName": cp.firstName,
            "lastName": cp.lastName, "email": cp.email, "phone": cp.phone,
            "globalJobTitle": cp.globalJobTitle, "photoUrl": cp.photoUrl,
            "quote": cp.quote})
        self._assert_unchanged(cp, before)

    def test_email_template_noop_edit(self):
        from ..models import EmailTemplate
        tpl = EmailTemplate.objects.create(
            name="Absage Standard", subject="Zu Ihrer Bewerbung: {stelle}",
            htmlContent="<p>Hallo {name}</p>", textContent="Hallo {name}")
        before = self._snapshot(tpl)
        self.client.force_login(make_user("rtrec3", role="Recruiter"))
        self.client.post(reverse('ats:save_email_template'), data={
            "template_id": str(tpl.id), "name": tpl.name,
            "subject": tpl.subject, "html_content": tpl.htmlContent,
            "text_content": tpl.textContent})
        self._assert_unchanged(tpl, before)

    def test_page_noop_edit(self):
        from ..models import Page
        page = Page.objects.create(
            slug="ueber-uns", title="Über uns", content="Wir sind ein Träger.",
            navEnabled=True, navLabel="Über uns", navOrder=3,
            metaDesc="Träger im Norden.")
        before = self._snapshot(page)
        self.client.force_login(make_user("rtadmin", role="HR-Admin"))
        # Formular sendet title/slug/content/navEnabled – Nav-Details und
        # metaDesc sind NICHT im Formular und muessen unangetastet bleiben.
        self.client.post(reverse('ats:pages_manage'), data={
            "page_id": str(page.id), "slug": page.slug,
            "title": page.title, "content": page.content,
            "navEnabled": "on"})
        self._assert_unchanged(page, before)

    def test_landing_page_noop_edit(self):
        from ..models import ContactPerson, Facility, JobFamily, LandingPage, Location, Organization
        org = Organization.objects.create(name="RT-O")
        fac = Facility.objects.create(name="RT-F", organization=org)
        loc = Location.objects.create(name="RT-L")
        fam = JobFamily.objects.create(name="RT-Fam2")
        cp = ContactPerson.objects.create(firstName="R", lastName="T",
                                          email="rt@x.de")
        lp = LandingPage.objects.create(
            name="RT-Kampagne", slug="rt-kampagne", headline="H",
            introText="I", heroUrl="https://x.de/h.jpg", facility=fac,
            location=loc, jobFamily=fam, contactPerson=cp, active=True,
            views=7)
        before = self._snapshot(lp)
        self.client.force_login(make_user("rtlp", role="Recruiter"))
        self.client.post(reverse('ats:landing_pages'), data={
            "lp_id": str(lp.id), "name": lp.name, "headline": lp.headline,
            "intro_text": lp.introText, "hero_url": lp.heroUrl,
            "facility": str(fac.id), "department": "",
            "job_family": str(fam.id), "location": str(loc.id),
            "contact_person": str(cp.id), "active": "1"})
        self._assert_unchanged(lp, before)

    def test_branding_noop_edit(self):
        from ..models import Organization
        org = Organization.objects.create(
            name="RT-Traeger", brandEnabled=True, brandMode="LIGHT",
            brandPrimary="#0065bd", brandAccent="#004a8f",
            brandLogoUrl="https://x.de/logo.svg",
            brandHeroUrl="https://x.de/haus.jpg")
        before = self._snapshot(org)
        self.client.force_login(make_user("rtbrand", role="HR-Admin"))
        self.client.post(reverse('ats:branding'), data={
            "enabled": "1", "mode": org.brandMode, "primary": org.brandPrimary,
            "accent": org.brandAccent, "logo_url": org.brandLogoUrl,
            "hero_url": org.brandHeroUrl})
        self._assert_unchanged(org, before)

    def test_panel_default_and_minimum_standard_noop(self):
        import json as _json
        import uuid as _u

        from ..models import JobFamily
        member = make_user("rtmember", role="Recruiter")
        fam = JobFamily.objects.create(
            name="JF-" + str(_u.uuid4())[:6],
            panelUserIdsJson=[str(member.id)],
            minimumQuestionsJson=[{"id": "min-1", "question": "Examen?",
                                   "type": "YES_NO", "isMandatory": True}])
        before = self._snapshot(fam)
        self.client.force_login(make_user("rtadmin2", role="HR-Admin"))
        self.client.post(reverse('ats:panel_defaults'), data={
            "level": "job_family", "entity_id": str(fam.id),
            "members": [str(member.id)]})
        self.client.post(reverse('ats:screening_questions'), data={
            "form": "minimum", "family_id": str(fam.id),
            "minimum_json": _json.dumps(fam.minimumQuestionsJson)})
        self._assert_unchanged(fam, before)

class SettingsAdminCoverageTestCase(TestCase):
    """Deckt die bisher ungetesteten Admin-/Stammdaten-Views ab –
    Funktion UND Autorisierung (Nicht-Admins müssen abgewiesen werden,
    damit ein künftiger Refactor den Schutz nicht still entfernt)."""

    def setUp(self):
        self.admin = make_user("cov-admin", role="HR-Admin")
        self.recruiter = make_user("cov-rec", role="Recruiter")

    # --- SystemSetting ---
    def test_save_system_setting_creates_and_requires_admin(self):
        # Nicht-Admin wird abgewiesen (Redirect/403, jedenfalls kein Erfolg)
        self.client.force_login(self.recruiter)
        self.client.post(reverse('ats:save_system_setting'),
                         {"key": "firma", "value": "Hack"})
        self.assertFalse(SystemSetting.objects.filter(key="FIRMA").exists())
        # Admin darf – Key wird großgeschrieben gespeichert
        self.client.force_login(self.admin)
        self.client.post(reverse('ats:save_system_setting'),
                         {"key": "firma", "value": "Elbtal"})
        s = SystemSetting.objects.get(key="FIRMA")
        self.assertEqual(s.value, "Elbtal")

    # --- WorkflowState ---
    def test_save_workflow_state_creates(self):
        from ..models import WorkflowState
        self.client.force_login(self.admin)
        self.client.post(reverse('ats:save_workflow_state'),
                         {"name": "Vorauswahl", "description": "Erste Sichtung"})
        self.assertTrue(
            WorkflowState.objects.filter(name="vorauswahl").exists())

    # --- EmailTemplate ---
    def test_save_email_template_creates(self):
        from ..models import EmailTemplate
        self.client.force_login(self.admin)
        self.client.post(reverse('ats:save_email_template'),
                         {"name": "Absage", "subject": "Ihre Bewerbung",
                          "html_content": "<p>Danke</p>",
                          "text_content": "Danke"})
        self.assertTrue(EmailTemplate.objects.filter(name="Absage").exists())

    # --- Kategorien (JobFamily) anlegen + archivieren ---
    def test_category_create_and_archive(self):
        from ..models import JobFamily
        self.client.force_login(self.admin)
        self.client.post(reverse('ats:categories'),
                         {"name": "Pflege", "description": "Pflegeberufe"})
        cat = JobFamily.objects.get(name="Pflege")
        self.assertFalse(cat.archived)
        # Archivieren entfernt sie aus der aktiven Liste
        self.client.post(reverse('ats:archive_category', args=[cat.id]))
        cat.refresh_from_db()
        self.assertTrue(cat.archived)

    def test_category_create_requires_admin(self):
        from ..models import JobFamily
        self.client.force_login(self.recruiter)
        self.client.post(reverse('ats:categories'), {"name": "Schmuggel"})
        self.assertFalse(JobFamily.objects.filter(name="Schmuggel").exists())

    # --- Standorte anlegen + archivieren ---
    def test_location_create_and_archive(self):
        from ..models import Location
        self.client.force_login(self.admin)
        self.client.post(reverse('ats:locations'),
                         {"name": "Hamburg", "city": "Hamburg"})
        loc = Location.objects.get(name="Hamburg")
        self.client.post(reverse('ats:archive_location', args=[loc.id]))
        loc.refresh_from_db()
        self.assertTrue(loc.archived)

    # --- Ansichten laden (GET) ---
    def test_admin_views_render(self):
        self.client.force_login(self.admin)
        for name in ('categories', 'locations', 'contacts'):
            r = self.client.get(reverse(f'ats:{name}'))
            self.assertEqual(r.status_code, 200, f"{name} lädt nicht")


class EmailTemplateRenderingTestCase(TestCase):
    """U2: Vorlagen-Platzhalter kommen NIE roh bei Bewerbenden an.

    Gefunden im Durchgang: Die mitgelieferten Vorlagen schreiben
    [[COMPANY_NAME]]/[[FIRST_NAME]], die Versandpfade ersetzten nur
    {name}/{stelle}/{firma}. Ergebnis war "Bewerbungseingang bei
    [[COMPANY_NAME]]" plus rohes HTML als Klartext.
    """

    def test_both_syntaxes_are_replaced(self):
        from ..mailing import render_template
        out = render_template(
            "Hallo [[FIRST_NAME]] [[LAST_NAME]], Stelle: {stelle} bei [[COMPANY_NAME]].",
            first_name="Ida", last_name="Sund", job_title="Pflegekraft",
            company="Klinik Nord")
        self.assertEqual(
            out, "Hallo Ida Sund, Stelle: Pflegekraft bei Klinik Nord.")

    def test_unknown_placeholders_are_removed_not_sent(self):
        from ..mailing import render_template
        out = render_template("Hallo [[UNBEKANNT]], hier {mystery}!",
                              first_name="Ida")
        self.assertNotIn("[[", out)
        self.assertNotIn("{", out)

    def test_html_becomes_readable_text(self):
        from ..mailing import html_to_text
        out = html_to_text("<h3>Hallo Ida,</h3><p>Punkt eins.<br/>Zeile zwei.</p>")
        self.assertNotIn("<", out)
        self.assertIn("Hallo Ida,", out)
        self.assertIn("Zeile zwei.", out)

    def test_seeded_templates_render_clean(self):
        """Die ausgelieferten Vorlagen selbst - der eigentliche Fund."""
        from ..models import EmailTemplate
        from ..views.common import seed_data_if_empty
        with self.settings(DEMO_MODE=True):
            seed_data_if_empty()
        from ..mailing import render_email
        for tpl in EmailTemplate.objects.all():
            subject, body = render_email(
                tpl, first_name="Ida", last_name="Sund",
                job_title="Pflegekraft", company="Klinik Nord",
                portal_url="https://x/portal")
            for raw in ("[[", "{firma}", "{name}", "<h3", "<p>"):
                self.assertNotIn(raw, subject, f"Betreff von {tpl.name}")
                self.assertNotIn(raw, body, f"Text von {tpl.name}")
