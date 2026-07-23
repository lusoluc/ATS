"""SecurATS-Tests: jobs (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .utils import User, make_user


class CategoriesLocationsTestCase(TestCase):
    """B13/B14 – Kategorien & Standorte (HR-Admin)."""

    def setUp(self):
        self.client = Client()
        make_user("hradmin4", role="HR-Admin")
        make_user("rec4", role="Recruiter")
        self.client.force_login(User.objects.get(username="hradmin4"))

    def test_category_add_and_recruiter_forbidden(self):
        from ..models import JobFamily
        resp = self.client.post(reverse('ats:categories'), data={"name": "Pflege"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(JobFamily.objects.filter(name="Pflege").exists())
        # Recruiter darf nicht
        self.client.force_login(User.objects.get(username="rec4"))
        self.assertEqual(self.client.get(reverse('ats:categories')).status_code, 403)

    def test_location_add(self):
        from ..models import Location
        resp = self.client.post(reverse('ats:locations'),
                                data={"name": "Klinik Berlin", "city": "Berlin", "postalCode": "10115"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Location.objects.filter(name="Klinik Berlin").exists())

class JobTemplateTestCase(TestCase):
    """B12 – Job-Vorlagen-Bibliothek (Kern)."""

    def setUp(self):
        self.client = Client()
        make_user("hradmin5", role="HR-Admin")
        self.client.force_login(User.objects.get(username="hradmin5"))

    def test_create_template(self):
        from ..models import JobTemplate
        resp = self.client.post(reverse('ats:job_templates'),
                                data={"title": "Stationsleitung", "content": "Aufgaben: …"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(JobTemplate.objects.filter(title="Stationsleitung").exists())

class JobAlertScopeTestCase(TestCase):
    """Job-Alert mit Scope (Stichwort/Firma/Umkreis), Unique-E-Mail, DSGVO-Verfall."""

    def _world(self):
        import uuid as _u

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        # Hamburg und Lüneburg (~46 km), München (~600 km)
        self.hh = Location.objects.create(name="Hamburg", lat=53.5511, lng=9.9937)
        self.lg = Location.objects.create(name="Lueneburg", lat=53.2464, lng=10.4115)
        self.muc = Location.objects.create(name="Muenchen", lat=48.1351, lng=11.5820)
        self.fac_a = Facility.objects.create(name="Klinik A", organization=org)
        self.fac_b = Facility.objects.create(name="Klinik B", organization=org)
        fam = JobFamily.objects.create(name="Pflege-" + str(_u.uuid4())[:4])
        wf = WorkflowState.objects.create(name="published")
        def job(title, loc, fac):
            return JobPosting.objects.create(title=title, organization=org, facility=fac,
                                             location=loc, jobFamily=fam, workflowState=wf)
        return job

    def _sub(self, email, **kw):
        import json as _j

        from ..models import JobAlertSubscription
        defaults = dict(status="ACTIVE", confirmationToken=email + "-c",
                        managementToken=email + "-m")
        defaults.update(kw)
        if "locations" in defaults and isinstance(defaults["locations"], list):
            defaults["locations"] = _j.dumps([str(x) for x in defaults["locations"]])
        return JobAlertSubscription.objects.create(email=email, **defaults)

    def test_unique_email_updates_instead_of_duplicating(self):
        from ..models import JobAlertSubscription
        self._world()
        r1 = self.client.post(reverse('ats:job_alert'), data={
            "email": "Ay@Ex.org", "keyword": "Pflege"})
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post(reverse('ats:job_alert'), data={
            "email": "ay@ex.org", "keyword": "Leitung", "radius": "30",
            "location": str(self.hh.id)})
        self.assertEqual(JobAlertSubscription.objects.count(), 1)   # KEIN Duplikat
        sub = JobAlertSubscription.objects.get()
        self.assertEqual(sub.keyword, "Leitung")                    # aktualisiert
        self.assertEqual(sub.radiusKm, 30)
        self.assertContains(r2, "aktualisiert")

    def test_scope_matching_keyword_facility_radius_global(self):
        from ..job_alerts import match_subscribers_for_job
        job = self._world()
        j_pflege_lg = job("Pflegefachkraft Nachtdienst", self.lg, self.fac_a)
        j_it_muc = job("IT-Administrator", self.muc, self.fac_b)

        self._sub("kw@x.de", keyword="pflege")                       # Stichwort
        self._sub("fac@x.de", facility=self.fac_b)                  # Firma
        self._sub("rad@x.de", locations=[self.hh.id], radiusKm=60)  # 60km um HH
        self._sub("rad2@x.de", locations=[self.hh.id], radiusKm=20)
        self._sub("glob@x.de", globalAlert=True)
        self._sub("pend@x.de", globalAlert=True, status="PENDING")

        m1 = {s.email for s in match_subscribers_for_job(j_pflege_lg)}
        # Stichwort ✓, 60km-Umkreis (HH→Lüneburg ~46km) ✓, global ✓;
        # 20km ✗, Firma B ✗, unbestätigt ✗
        self.assertEqual(m1, {"kw@x.de", "rad@x.de", "glob@x.de"})

        m2 = {s.email for s in match_subscribers_for_job(j_it_muc)}
        self.assertEqual(m2, {"fac@x.de", "glob@x.de"})

    def test_expired_subscription_is_excluded_and_purged(self):
        from datetime import timedelta
        from io import StringIO

        from django.core.management import call_command
        from django.utils import timezone as tz

        from ..job_alerts import match_subscribers_for_job
        from ..models import AuditLog, JobAlertSubscription
        job = self._world()
        j = job("Pflegehelfer", self.hh, self.fac_a)
        old = self._sub("old@x.de", globalAlert=True)
        JobAlertSubscription.objects.filter(id=old.id).update(
            lastConfirmedAt=tz.now() - timedelta(days=400))
        old.refresh_from_db()
        self.assertEqual(match_subscribers_for_job(j), [])  # verfallen -> kein Alarm
        out = StringIO()
        call_command("send_job_alerts", stdout=out)
        self.assertEqual(JobAlertSubscription.objects.count(), 0)  # gelöscht
        self.assertTrue(AuditLog.objects.filter(action="JOB_ALERT_PURGED").exists())

    def test_confirm_and_unsubscribe_flow(self):
        from ..models import JobAlertSubscription
        self._world()
        self.client.post(reverse('ats:job_alert'), data={"email": "flow@x.de", "global": "1"})
        sub = JobAlertSubscription.objects.get(email="flow@x.de")
        self.assertEqual(sub.status, "PENDING")   # Double-Opt-in: erst bestätigen
        r = self.client.get(reverse('ats:job_alert_confirm', args=[sub.confirmationToken]))
        sub.refresh_from_db()
        self.assertEqual(sub.status, "ACTIVE")
        self.assertContains(r, "aktiv")
        r2 = self.client.post(reverse('ats:job_alert_manage', args=[sub.managementToken]),
                              data={"action": "unsubscribe"})
        sub.refresh_from_db()
        self.assertEqual(sub.status, "INACTIVE")
        self.assertContains(r2, "abgemeldet")

    def test_send_command_logs_alert_for_matching_job(self):
        from io import StringIO

        from django.core.management import call_command

        from ..models import JobAlertLog
        job = self._world()
        self._sub("hit@x.de", keyword="Pflege")
        job("Pflegefachkraft Station 3", self.hh, self.fac_a)
        out = StringIO()
        call_command("send_job_alerts", "--hours", "1", stdout=out)
        self.assertIn("1 Alert(s) versendet", out.getvalue())
        log = JobAlertLog.objects.get(action="ALERT_SENT")
        self.assertIn("Pflegefachkraft", log.metadata)

    def test_job_list_flexible_search(self):
        job = self._world()
        job("Stationsleitung", self.hh, self.fac_a)
        j2 = job("Springer", self.muc, self.fac_b)
        j2.description = "Unterstützung im Pflegedienst"
        j2.save(update_fields=["description"])
        # Suche findet Treffer auch in der Beschreibung
        r = self.client.get(reverse('ats:job_list') + "?q=Pflegedienst")
        self.assertContains(r, "Springer")
        self.assertNotContains(r, "Stationsleitung")
        # Kategorie-Filter vorhanden
        r2 = self.client.get(reverse('ats:job_list'))
        self.assertContains(r2, "Alle Kategorien")

class MasterDataTestCase(TestCase):
    """Stammdaten-Zentrale: Ansprechpartner (zentral wirkt überall, Ersetzen,
    Lösch-Schutz), Job-Schnell-Toggle, Textbausteine."""

    def _world(self):
        import uuid as _u

        from ..models import ContactPerson, Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="Berlin")
        self.fac = Facility.objects.create(name="Klinik A", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        self.published = WorkflowState.objects.create(name="published")
        self.cp_a = ContactPerson.objects.create(firstName="Petra", lastName="Wolf",
                                                 email="pw@x.de", phone="030-1")
        self.cp_b = ContactPerson.objects.create(firstName="Tobias", lastName="Klein",
                                                 email="tk@x.de")
        from ..models import PayBand
        band = PayBand.objects.create(name="MD-Band", minAmount=3000,
                                      maxAmount=3800)
        self.jobs = [JobPosting.objects.create(
            title=f"Stelle {i}", organization=org, facility=self.fac, location=loc,
            jobFamily=fam, workflowState=self.published, contactPerson=self.cp_a,
            payBand=band)
            for i in range(3)]

    def test_central_edit_reflects_on_job_detail(self):
        self._world()
        admin = make_user("mdadmin", role="HR-Admin")
        self.client.force_login(admin)
        # Telefon zentral ändern -> Stellendetail zeigt sofort die neue Nummer
        self.client.post(reverse('ats:contacts'), data={
            "action": "save", "cp_id": str(self.cp_a.id),
            "firstName": "Petra", "lastName": "Wolf", "email": "pw@x.de",
            "phone": "030-999999"})
        r = self.client.get(reverse('ats:job_detail', args=[self.jobs[0].id]))
        self.assertContains(r, "030-999999")

    def test_replace_everywhere_swaps_all_jobs_with_audit(self):
        from ..models import AuditLog, JobPosting
        self._world()
        admin = make_user("mdadmin2", role="HR-Admin")
        self.client.force_login(admin)
        self.client.post(reverse('ats:contacts'), data={
            "action": "replace_everywhere",
            "old_id": str(self.cp_a.id), "new_id": str(self.cp_b.id)})
        self.assertEqual(JobPosting.objects.filter(contactPerson=self.cp_b).count(), 3)
        self.assertEqual(JobPosting.objects.filter(contactPerson=self.cp_a).count(), 0)
        audit = AuditLog.objects.get(action="CONTACT_REPLACED")
        self.assertIn('"jobs_updated": 3', audit.metadataJson)

    def test_contact_in_use_cannot_be_deleted(self):
        from ..models import ContactPerson
        self._world()
        admin = make_user("mdadmin3", role="HR-Admin")
        self.client.force_login(admin)
        self.client.post(reverse('ats:contacts'), data={
            "action": "delete", "cp_id": str(self.cp_a.id)})
        self.assertTrue(ContactPerson.objects.filter(id=self.cp_a.id).exists())  # geschützt
        self.client.post(reverse('ats:contacts'), data={
            "action": "delete", "cp_id": str(self.cp_b.id)})
        self.assertFalse(ContactPerson.objects.filter(id=self.cp_b.id).exists())  # unbenutzt -> weg

    def test_quick_toggle_deactivates_and_reactivates(self):
        from ..models import AuditLog
        self._world()
        rec = make_user("mdrec", role="Recruiter")
        self.client.force_login(rec)
        job = self.jobs[0]
        r = self.client.post(reverse('ats:toggle_job_active', args=[job.id]))
        self.assertFalse(r.json()["active"])
        job.refresh_from_db()
        self.assertEqual(job.workflowState.name, "draft")
        # deaktiviert -> nicht mehr öffentlich gelistet
        self.assertNotContains(self.client.get(reverse('ats:job_list')), job.title)
        self.assertTrue(AuditLog.objects.filter(action="JOB_DEACTIVATED").exists())
        r2 = self.client.post(reverse('ats:toggle_job_active', args=[job.id]))
        self.assertTrue(r2.json()["active"])
        job.refresh_from_db()
        self.assertEqual(job.workflowState.name, "published")

    def test_toggle_respects_bola_scope(self):
        from ..models import Location, UserScope
        self._world()
        other = Location.objects.create(name="Muenchen")
        scoped = make_user("mdscoped", role="Recruiter")
        sc = UserScope.objects.create(user=scoped, full_access=False)
        sc.locations.add(other)  # kein Zugriff auf Berlin
        self.client.force_login(scoped)
        r = self.client.post(reverse('ats:toggle_job_active', args=[self.jobs[0].id]))
        self.assertEqual(r.status_code, 404)

    def test_snippets_crud_and_available_in_job_form(self):
        from ..models import TextSnippet
        self._world()
        admin = make_user("mdadmin4", role="HR-Admin")
        self.client.force_login(admin)
        self.client.post(reverse('ats:snippets'), data={
            "category": "BENEFITS", "content": "30 Tage Urlaub und Jobticket."})
        self.assertEqual(TextSnippet.objects.count(), 1)
        # Baustein-Dropdown erscheint in der Job-Anlage (Dashboard)
        r = self.client.get(reverse('ats:dashboard'))
        self.assertContains(r, "Textbaustein einfügen")
        self.assertContains(r, "30 Tage Urlaub")

class ScreeningQuestionTypesTestCase(TestCase):
    """Dynamisches Bewerbungsformular: TEXT/SELECT/YES_NO je Stelle."""

    def _world(self, screening):

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="Wien")
        fac = Facility.objects.create(name="Zentrale", organization=org)
        fam = JobFamily.objects.create(name="QT-Fam")
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Senior IT Business Analyst", organization=org,
            facility=fac, location=loc, jobFamily=fam, workflowState=wf,
            screeningQuestionsJson=screening)

    QUESTIONS = [
        {"id": "pay", "type": "SELECT", "isMandatory": True,
         "question": "Mit welchen Payment-Standards haben Sie gearbeitet?",
         "options": ["SEPA", "SWIFT MT", "ISO 20022", "Noch keine"]},
        {"id": "reg", "type": "TEXT", "isMandatory": True,
         "question": "Kurz: ein regulatorisches Projekt (DORA/MaRisk/PSD2)?"},
        {"id": "exp", "type": "YES_NO", "isMandatory": True,
         "question": "Mind. 3 Jahre Core-Banking-Erfahrung?",
         "expectedAnswer": "YES"},
    ]

    def _apply(self, **answers):
        data = {"first_name": "Ivo", "last_name": "K", "email": "ivo@x.de",
                "consent_privacy": "on",
                "cv_file": SimpleUploadedFile("cv.pdf", b"%PDF-1.4")}
        data.update({f"question_{k}": v for k, v in answers.items()})
        return self.client.post(reverse('ats:bewerben', args=[self.job.id]),
                                data=data)

    def test_form_renders_all_types(self):
        self._world(self.QUESTIONS)
        page = self.client.get(reverse('ats:bewerben', args=[self.job.id]))
        self.assertContains(page, "ISO 20022")                 # SELECT-Option
        self.assertContains(page, "<textarea", count=2)        # TEXT + Anschreiben
        self.assertContains(page, "DORA/MaRisk/PSD2")

    def test_answers_saved_and_ko_only_with_expected(self):

        from ..models import Application
        self._world(self.QUESTIONS)
        self._apply(pay="ISO 20022", reg="DORA-Testkonzept begleitet.",
                    exp="YES")
        app = Application.objects.get()
        self.assertEqual(app.status, "NEW")                    # kein K.O.
        answers = app.screeningAnswersJson
        self.assertEqual(
            answers["Mit welchen Payment-Standards haben Sie gearbeitet?"],
            "ISO 20022")
        self.assertIn("DORA-Testkonzept",
                      answers["Kurz: ein regulatorisches Projekt (DORA/MaRisk/PSD2)?"])
        # K.O. weiterhin nur ueber expectedAnswer
        self._apply(pay="SEPA", reg="MaRisk.", exp="NO")
        self.assertEqual(Application.objects.exclude(id=app.id).get().status,
                         "REJECTED")

    def test_mandatory_text_empty_is_form_error_not_rejection(self):
        from ..models import Application
        self._world(self.QUESTIONS)
        r = self._apply(pay="SEPA", reg="", exp="YES")
        self.assertContains(r, "Bitte beantworten Sie diese Frage.")
        self.assertEqual(Application.objects.count(), 0)       # nichts angelegt
        self.assertContains(r, 'value="SEPA" selected')        # Werterhalt

    def test_text_answer_xss_stays_escaped(self):

        from ..models import Application
        self._world(self.QUESTIONS)
        payload = '<script>alert("qx")</script>'
        self._apply(pay="SEPA", reg=payload, exp="YES")
        app = Application.objects.get()
        answers = app.screeningAnswersJson
        self.assertEqual(
            answers["Kurz: ein regulatorisches Projekt (DORA/MaRisk/PSD2)?"],
            payload)                                           # roh gespeichert
        self.client.force_login(make_user("qtrec", role="Recruiter"))
        dash = self.client.get(reverse('ats:dashboard'))
        self.assertNotContains(dash, payload)                  # nie roh gerendert

class QuestionBuilderAndFileTypeTestCase(TestCase):
    """Mindeststandard-Builder ohne JSON + Pflicht-Dokument-Fragetyp."""

    def _world(self, screening=None):

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        self.fam = JobFamily.objects.create(name="QB-Fam")
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Pflegefachkraft", organization=org, facility=fac,
            location=loc, jobFamily=self.fam, workflowState=wf,
            screeningQuestionsJson=screening or [])

    def test_builder_add_edit_reorder_delete_without_json(self):
        self._world()
        self.client.force_login(make_user("qbadmin", role="HR-Admin"))
        url = reverse('ats:screening_questions')
        base = {"form": "minimum_builder", "family_id": str(self.fam.id)}
        self.client.post(url, data={**base, "action": "add",
                                    "q_type": "YES_NO",
                                    "q_question": "Liegt ein Examen vor?",
                                    "q_expected": "YES"})
        self.client.post(url, data={**base, "action": "add",
                                    "q_type": "FILE",
                                    "q_question": "Führerschein Klasse B"})
        self.fam.refresh_from_db()
        qs = self.fam.minimumQuestionsJson
        self.assertEqual([q["type"] for q in qs], ["YES_NO", "FILE"])
        self.assertEqual(qs[0]["expectedAnswer"], "YES")       # K.O. gesetzt
        self.assertTrue(all(q["isMandatory"] for q in qs))     # immer Pflicht
        self.assertNotIn("expectedAnswer", qs[1])              # FILE nie K.O.
        self.client.post(url, data={**base, "action": "up", "idx": "1"})
        self.client.post(url, data={**base, "action": "save", "idx": "1",
                                    "q_type": "YES_NO",
                                    "q_question": "Liegt ein Pflege-Examen vor?",
                                    "q_expected": "YES"})
        self.client.post(url, data={**base, "action": "delete", "idx": "0"})
        self.fam.refresh_from_db()
        qs = self.fam.minimumQuestionsJson
        self.assertEqual(len(qs), 1)
        self.assertIn("Pflege-Examen", qs[0]["question"])
        # Die Seite selbst zeigt Formularfelder, kein JSON-Feld mehr
        page = self.client.get(url)
        self.assertNotContains(page, "minimum_json")
        self.assertContains(page, "Pflicht-Dokument (Upload)")

    def test_file_question_end_to_end_with_negatives(self):

        from ..models import Application, ApplicationDocument
        self._world(screening=[
            {"id": "fs", "type": "FILE", "isMandatory": True,
             "question": "Führerschein Klasse B"}])
        form = self.client.get(reverse('ats:bewerben', args=[self.job.id]))
        self.assertContains(form, "Führerschein Klasse B")
        self.assertContains(form, 'type="file" id="question_fs"')
        def apply(**extra):
            data = {"first_name": "Ute", "last_name": "F",
                    "email": "ute@x.de", "consent_privacy": "on",
                    "cv_file": SimpleUploadedFile("cv.pdf", b"%PDF-1.4")}
            data.update(extra)
            return self.client.post(
                reverse('ats:bewerben', args=[self.job.id]), data=data)
        # Pflicht fehlt -> Formular-Fehler, nichts angelegt
        r = apply()
        self.assertContains(r, "Bitte laden Sie dieses Dokument hoch.")
        self.assertEqual(Application.objects.count(), 0)
        # Gefaehrlicher Typ -> abgelehnt (Formular-Sicherheitsregel)
        r = apply(question_fs=SimpleUploadedFile("schein.exe", b"MZ"))
        self.assertEqual(Application.objects.count(), 0)
        # Sauberer Fall: Dokument mit Anforderungs-Label abgelegt
        apply(question_fs=SimpleUploadedFile("schein.pdf", b"%PDF-1.4"))
        app = Application.objects.get()
        doc = ApplicationDocument.objects.get(docType="REQUIRED")
        self.assertIn("Führerschein Klasse B", doc.name)
        self.assertIn("schein.pdf",
                      str(app.screeningAnswersJson))          # Antwort = Dateiname
        self.assertEqual(app.status, "NEW")                    # FILE nie K.O.

class JobTemplateHierarchyTestCase(TestCase):
    """B12: Versionierung, Diff und Master-Hierarchie für Job-Vorlagen."""

    def setUp(self):
        from django.contrib.auth.models import User

        from ats.models import Facility, JobFamily, JobPosting, JobTemplate, Location, Organization, WorkflowState
        self.user = User.objects.create_user(username="recruiter2", password="password")
        g, _ = Group.objects.get_or_create(name="Recruiter")
        self.user.groups.add(g)
        self.client.force_login(self.user)

        self.org = Organization.objects.create(name="SecurATS")
        self.fac = Facility.objects.create(name="Einrichtung A", organization=self.org)
        self.loc = Location.objects.create(name="Standort A", city="City A")
        self.fam = JobFamily.objects.create(name="Pflege")
        self.state = WorkflowState.objects.create(name="published")

        # Create template version 1
        self.tpl_v1 = JobTemplate.objects.create(
            title="Pflege-Vorlage",
            content="Wir suchen Pflegekräfte.\nAnforderungen: Deutsch.",
            version=1
        )
        # Create template version 2 (same title)
        self.tpl_v2 = JobTemplate.objects.create(
            title="Pflege-Vorlage",
            content="Wir suchen Pflegekräfte.\nAnforderungen: Deutsch.\nNeu: Führerschein.",
            version=2,
            parent=self.tpl_v1
        )

        # Create job using v1 (outdated)
        self.job = JobPosting.objects.create(
            title="Altenpfleger:in",
            organization=self.org,
            facility=self.fac,
            location=self.loc,
            jobFamily=self.fam,
            workflowState=self.state,
            jobTemplate=self.tpl_v1
        )

    def test_template_version_creation_and_outdated_property(self):
        # Verify setup
        self.assertEqual(self.tpl_v1.version, 1)
        self.assertEqual(self.tpl_v2.version, 2)
        self.assertEqual(self.tpl_v2.parent, self.tpl_v1)

        # Verify job is linked to v1 and is detected as outdated
        self.assertEqual(self.job.jobTemplate, self.tpl_v1)
        self.assertTrue(self.job.is_template_outdated)

    def test_job_template_detail_view(self):
        url = reverse('ats:job_template_detail', args=[self.tpl_v1.id])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['title'], "Pflege-Vorlage")
        self.assertEqual(data['latest_version'], 2)

        # Check history list
        self.assertEqual(len(data['history']), 2)
        v1_data = next(x for x in data['history'] if x['version'] == 1)
        v2_data = next(x for x in data['history'] if x['version'] == 2)

        self.assertFalse(v1_data['is_latest'])
        self.assertTrue(v2_data['is_latest'])

        # Verify active jobs are returned for v1
        self.assertEqual(v1_data['active_jobs_count'], 1)
        self.assertEqual(v1_data['active_jobs'][0]['title'], "Altenpfleger:in")

        # Verify diff is generated for v1 (outdated)
        self.assertIn("Führerschein", v1_data['diff_html'])

    def test_restore_template_version(self):
        # Restore v1 as new version v3
        url = reverse('ats:restore_job_template', args=[self.tpl_v1.id])
        r = self.client.post(url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['new_version'], 3)

        from ats.models import AuditLog, JobTemplate
        new_tpl = JobTemplate.objects.get(id=data['new_tpl_id'])
        self.assertEqual(new_tpl.version, 3)
        self.assertEqual(new_tpl.title, "Pflege-Vorlage")
        self.assertEqual(new_tpl.content, self.tpl_v1.content) # Content from v1 restored
        self.assertEqual(new_tpl.parent, self.tpl_v2) # Parent is the previous latest (v2)

        # Audit log verification
        self.assertTrue(AuditLog.objects.filter(action="RESTORE_TEMPLATE").exists())

    def test_update_job_posting_template_version(self):
        # Update job to use latest template version (v2)
        url = reverse('ats:update_job_posting_template', args=[self.job.id])
        r = self.client.post(url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['new_version'], 2)

        self.job.refresh_from_db()
        self.assertEqual(self.job.jobTemplate, self.tpl_v2)
        self.assertFalse(self.job.is_template_outdated)

        # Audit log verification
        from ats.models import AuditLog
        self.assertTrue(AuditLog.objects.filter(action="UPDATE_JOB_TEMPLATE_VERSION").exists())

class WorkflowActionsTestCase(TestCase):
    """Prozess-Automatik: echte Aktionen statt 'nicht implementiert'.

    Kern: AUTO_ADVANCE darf NIEMALS zu HIRED/REJECTED führen –
    Zu-/Absagen bleiben dem Menschen vorbehalten (.agents/AGENTS.md,
    Human-in-the-Loop). Dieser Test ist die Compliance-Wache dafür.
    """

    def setUp(self):
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
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="WA-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Pflegefachkraft", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=ws)
        self.app = Application.objects.create(
            applicant=Applicant.objects.create(firstName="W", lastName="A",
                                               email="wa@x.de"),
            jobPosting=self.job, status="IN_REVIEW")
        self.rec = make_user("wa-rec", role="Recruiter")

    def _run(self, actions):
        from ..views import execute_workflow_actions
        execute_workflow_actions(self.app, actions)
        self.app.refresh_from_db()

    # --- AUTO_ADVANCE: die Compliance-Grenze ---
    def test_auto_advance_moves_within_screening(self):
        from ..models import AuditLog
        self._run([{"type": "AUTO_ADVANCE", "to": "INVITED"}])
        self.assertEqual(self.app.status, "INVITED")
        self.assertTrue(AuditLog.objects.filter(
            action="AUTOMATION_AUTO_ADVANCE").exists())

    def test_auto_advance_never_hires(self):
        """Automatische ZUSAGE ist verboten (Human-in-the-Loop)."""
        from ..models import AuditLog
        self._run([{"type": "AUTO_ADVANCE", "to": "HIRED"}])
        self.assertEqual(self.app.status, "IN_REVIEW")     # unverändert!
        blocked = AuditLog.objects.filter(
            action="WORKFLOW_ACTION_BLOCKED").first()
        self.assertIsNotNone(blocked)
        self.assertIn("Human-in-the", blocked.metadataJson)

    def test_auto_advance_never_rejects(self):
        """Automatische ABSAGE ist verboten (Human-in-the-Loop)."""
        self._run([{"type": "AUTO_ADVANCE", "to": "REJECTED"}])
        self.assertEqual(self.app.status, "IN_REVIEW")     # unverändert!

    def test_auto_advance_does_not_chain(self):
        """Der Autovorlauf löst KEINE weitere Automatik aus – sonst wären
        Endlosschleifen möglich."""

        from ..models import AppWorkflowDef, AuditLog
        # Regel: bei INVITED nochmal weiterschieben (würde eine Kette bilden)
        AppWorkflowDef.objects.create(
            name="Kette", jobIdsJson=[str(self.job.id)],
            stepsJson=[{"state": "INVITED", "actions": [
                {"type": "AUTO_ADVANCE", "to": "NEW"}]}])
        self._run([{"type": "AUTO_ADVANCE", "to": "INVITED"}])
        self.assertEqual(self.app.status, "INVITED")   # NICHT weiter zu NEW
        self.assertEqual(AuditLog.objects.filter(
            action="AUTOMATION_AUTO_ADVANCE").count(), 1)

    # --- Interne Benachrichtigung (der vorher tote Fall) ---
    def test_internal_email_to_address_and_role(self):
        from django.core import mail
        member = make_user("wa-bl", role="Recruiter")
        member.email = "leitung@x.de"
        member.save(update_fields=["email"])
        Group.objects.get_or_create(name="Bereichsleitung")[0].user_set.add(member)
        mail.outbox = []
        self._run([{"type": "EMAIL_NOTIFICATION",
                    "recipient": "gremium@securats.de",
                    "role": "Bereichsleitung"}])
        # Eine Mail an alle internen Empfänger (Adresse + Rollen-Mitglieder)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(sorted(mail.outbox[0].to),
                         ["gremium@securats.de", "leitung@x.de"])

    def test_internal_email_without_recipient_is_skipped_honestly(self):
        from django.core import mail

        from ..models import AuditLog
        mail.outbox = []
        self._run([{"type": "EMAIL_NOTIFICATION", "recipient": ""}])
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(AuditLog.objects.filter(
            action="WORKFLOW_ACTION_SKIPPED").exists())

    # --- ADD_NOTE ---
    def test_add_note_action_appends_note(self):
        self._run([{"type": "ADD_NOTE", "text": "Unterlagen angefordert"}])
        self.assertIn("Unterlagen angefordert", self.app.internalNotes)
        self.assertIn("(Automatik)", self.app.internalNotes)

    # --- CREATE_TASK ---
    def test_create_task_with_role_and_due_date(self):
        from ..models import WorkflowTask
        self._run([{"type": "CREATE_TASK", "title": "Referenzen einholen",
                    "role": "Recruiter", "due_days": "3"}])
        task = WorkflowTask.objects.get()
        self.assertEqual(task.title, "Referenzen einholen")
        self.assertEqual(task.role, "Recruiter")
        self.assertIsNotNone(task.dueAt)
        self.assertEqual(task.status, "OPEN")
        self.assertFalse(task.overdue)

    def test_task_overdue_flag(self):
        from ..models import WorkflowTask
        self._run([{"type": "CREATE_TASK", "title": "Fristsache"}])
        t = WorkflowTask.objects.get()
        t.dueAt = timezone.now() - datetime.timedelta(days=1)
        t.save(update_fields=["dueAt"])
        self.assertTrue(t.overdue)

    # --- Aufgaben-Ansicht ---
    def test_tasks_page_shows_and_completes_task(self):
        from ..models import WorkflowTask
        self._run([{"type": "CREATE_TASK", "title": "Zeugnis prüfen",
                    "role": "Recruiter"}])
        task = WorkflowTask.objects.get()
        self.client.force_login(self.rec)
        page = self.client.get(reverse('ats:tasks'))
        self.assertContains(page, "Zeugnis prüfen")
        # Erledigen
        self.client.post(reverse('ats:tasks'), {"task_id": str(task.id)})
        task.refresh_from_db()
        self.assertEqual(task.status, "DONE")
        self.assertEqual(task.doneBy, self.rec)

    def test_task_only_visible_to_responsible_role(self):
        self._run([{"type": "CREATE_TASK", "title": "Nur für Vorstand",
                    "role": "Vorstand"}])
        self.client.force_login(self.rec)          # Recruiter, nicht Vorstand
        page = self.client.get(reverse('ats:tasks'))
        self.assertNotContains(page, "Nur für Vorstand")

    def test_task_bola_scoped(self):
        from ..models import WorkflowTask
        from ..permissions import can_access_application
        self._run([{"type": "CREATE_TASK", "title": "Fremd"}])
        task = WorkflowTask.objects.get()
        outsider = make_user("wa-out", role="Recruiter")
        if hasattr(outsider, 'scope'):
            outsider.scope.facilities.clear()
            outsider.scope.locations.clear()
        if not can_access_application(outsider, self.app):
            self.client.force_login(outsider)
            r = self.client.post(reverse('ats:tasks'),
                                 {"task_id": str(task.id)})
            self.assertEqual(r.status_code, 404)
            task.refresh_from_db()
            self.assertEqual(task.status, "OPEN")   # unverändert

    def test_unknown_action_still_skipped_honestly(self):
        from ..models import AuditLog
        self._run([{"type": "SEND_SMS_TO_MARS"}])
        skip = AuditLog.objects.filter(action="WORKFLOW_ACTION_SKIPPED").first()
        self.assertIsNotNone(skip)
        self.assertIn("Unbekannter Aktionstyp", skip.metadataJson)

class AutomationFormEditorTestCase(TestCase):
    """No-Code-Editor für die Prozess-Automatik + Aufräumen der irreführenden
    Standard-Vorbelegungen.

    Kern-Befund, den diese Tests festhalten: Die frühere Vorbelegung erzeugte
    Aktionen, die es NIE gab (AUTO_INVITE_INTERVIEW, TRIGGER_PROCESS,
    SEND_CONTRACT). Ein Admin sah "Vertrag senden" in der Pipeline – und es
    passierte nichts. Vorbelegt wird jetzt nur, was wirklich ausgeführt wird.
    """

    def setUp(self):
        from ..models import WorkflowState
        self.admin = make_user("af-admin", role="HR-Admin")
        for s in ("NEW", "IN_REVIEW", "INVITED", "REJECTED"):
            WorkflowState.objects.get_or_create(name=s)
        self.client.force_login(self.admin)

    def _saved_steps(self):
        from ..models import AppWorkflowDef
        return AppWorkflowDef.objects.get().stepsJson

    def test_defaults_contain_no_phantom_actions(self):
        """Die Vorbelegung darf KEINE Aktionstypen mehr erzeugen, die der
        Ausführer nicht kennt – sonst führt das UI den Admin in die Irre."""
        from ..views import execute_workflow_actions  # noqa: F401
        self.client.post(reverse('ats:save_app_workflow'), {
            "name": "Standard", "steps": ["NEW", "IN_REVIEW", "INVITED",
                                          "REJECTED"]})
        phantom = {"AUTO_INVITE_INTERVIEW", "TRIGGER_PROCESS", "SEND_CONTRACT"}
        for step in self._saved_steps():
            for a in step["actions"]:
                self.assertNotIn(a.get("type"), phantom,
                                 f"Phantom-Aktion {a.get('type')} in "
                                 f"{step['state']} – wird nie ausgeführt!")

    def test_defaults_only_use_implemented_action_types(self):
        """Jede vorbelegte Aktion muss ein Typ sein, den execute_workflow_actions
        tatsächlich behandelt."""
        implemented = {"EMAIL_NOTIFICATION", "ADD_NOTE", "CREATE_TASK",
                       "AUTO_ADVANCE", "APPROVAL_COMMITTEE"}
        self.client.post(reverse('ats:save_app_workflow'), {
            "name": "Standard", "steps": ["NEW", "IN_REVIEW", "INVITED",
                                          "REJECTED"]})
        for step in self._saved_steps():
            for a in step["actions"]:
                self.assertIn(a.get("type"), implemented)

    def test_defaults_are_actually_executed(self):
        """Beweis, dass die Vorbelegung wirkt: INVITED legt eine Aufgabe an."""
        from ..models import (
            Applicant,
            Application,
            AppWorkflowDef,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
            WorkflowTask,
        )
        from ..views import execute_workflow_actions
        self.client.post(reverse('ats:save_app_workflow'), {
            "name": "Standard", "steps": ["INVITED"]})
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="AF-Fam")
        ws = WorkflowState.objects.get(name="INVITED")
        job = JobPosting.objects.create(title="J", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=ws)
        app = Application.objects.create(
            applicant=Applicant.objects.create(firstName="A", lastName="F",
                                               email="af@x.de"),
            jobPosting=job, status="INVITED")
        steps = AppWorkflowDef.objects.get().stepsJson
        execute_workflow_actions(app, steps[0]["actions"])
        self.assertEqual(WorkflowTask.objects.count(), 1)   # Aufgabe entstand

    def test_form_editor_json_is_accepted(self):
        """Das JSON, das der Baukasten erzeugt, muss der Server unverändert
        übernehmen (Format-Vertrag zwischen Editor und save_app_workflow)."""
        import json
        built = [{"step": "IN_REVIEW", "actions": [
            {"type": "CREATE_TASK", "title": "Referenzen einholen",
             "role": "Recruiter", "due_days": 3},
            {"type": "AUTO_ADVANCE", "to": "INVITED"}]}]
        self.client.post(reverse('ats:save_app_workflow'), {
            "name": "Baukasten", "steps": ["IN_REVIEW"],
            "custom_actions_json": json.dumps(built)})
        steps = self._saved_steps()
        actions = steps[0]["actions"]
        self.assertEqual(actions[0]["title"], "Referenzen einholen")
        self.assertEqual(actions[0]["due_days"], 3)
        self.assertEqual(actions[1]["to"], "INVITED")

    def test_editor_is_rendered_instead_of_raw_json_field(self):
        """Der Baukasten ist da – und der Hinweis auf die Human-in-the-Loop-
        Grenze steht sichtbar im Formular.

        Seit B2 liegt der Baukasten auf der eigenen Seite „Prozess Flow
        Manager" statt in einem versteckten Dashboard-Tab."""
        r = self.client.get(reverse('ats:process_page'))
        self.assertContains(r, 'id="automation-rows"')
        self.assertContains(r, 'automation-add')
        self.assertContains(r, "Zusagen und Absagen trifft immer ein Mensch")
        # Die alte irreführende Werbung ist weg
        self.assertNotContains(r, "Vertragsentwürfe")

    def test_roles_are_offered_to_the_editor(self):
        r = self.client.get(reverse('ats:process_page'))
        self.assertContains(r, 'automation-roles-data')
        self.assertContains(r, 'Recruiter')
