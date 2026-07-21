"""SecurATS-Tests: import/export (aufgeteilt aus der frueheren Monolith-tests.py)."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import SystemSetting
from .utils import make_user


class FeedTokenTestCase(TestCase):
    """WP2/UC-NS-06: Feeds nur mit gültigem Token, wenn konfiguriert."""

    def test_feed_open_when_no_token_configured(self):
        with override_settings(FEED_ACCESS_TOKEN=""):
            self.assertEqual(self.client.get(reverse('ats:stepstone_feed')).status_code, 200)

    def test_feed_blocked_without_token(self):
        with override_settings(FEED_ACCESS_TOKEN="s3cret"):
            self.assertEqual(self.client.get(reverse('ats:stepstone_feed')).status_code, 403)
            self.assertEqual(self.client.get(reverse('ats:hr_ba_xml_feed')).status_code, 403)

    def test_feed_allowed_with_correct_token(self):
        with override_settings(FEED_ACCESS_TOKEN="s3cret"):
            r = self.client.get(reverse('ats:stepstone_feed') + "?token=s3cret")
            self.assertEqual(r.status_code, 200)
            r2 = self.client.get(reverse('ats:hr_ba_xml_feed'), HTTP_X_FEED_TOKEN="s3cret")
            self.assertEqual(r2.status_code, 200)

class OperationsWP7TestCase(TestCase):
    """WP7: Async-Queue, Gesamt-Health, Feed-XML-Validität."""

    def _job(self, title="Pflege & Betreuung <Nachtdienst>"):
        import uuid as _u

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="Berlin")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        return JobPosting.objects.create(title=title, description="Sonderzeichen: & < > \" '",
                                         organization=org, facility=fac, location=loc,
                                         jobFamily=fam, workflowState=wf)

    def test_queue_scores_application_async(self):
        from unittest.mock import patch

        from ..models import AiTask, Application
        job = self._job("Pflegekraft")
        SystemSetting.objects.create(key="AI_ASYNC", value="1")
        SystemSetting.objects.create(key="AI_SCORING_ENABLED", value="1")  # Opt-in (P0.2)
        resp = self.client.post(reverse('ats:bewerben', args=[job.id]), data={
            "first_name": "Async", "last_name": "Test", "email": "async@x.de",
            "cover_letter": "Ich pflege gern.", "consent_privacy": "on",
            "cv_file": SimpleUploadedFile("cv.pdf", b"%PDF-1")})
        self.assertEqual(resp.status_code, 200)
        from ..models import email_blind_index
        app = Application.objects.get(applicant__emailHash=email_blind_index("async@x.de"))
        self.assertIn("Hintergrund", app.aiRationale)      # noch nicht gescort
        self.assertEqual(AiTask.objects.filter(status="PENDING").count(), 1)
        # Worker verarbeitet (LLM gemockt -> deterministisch, ohne Ollama)
        with patch("ats.views.evaluate_with_local_gemma", return_value=("B", "Passt gut.")):
            from ..queue import run_pending
            self.assertEqual(run_pending(), 1)
        app.refresh_from_db()
        self.assertEqual(app.aiScore, "B")
        self.assertEqual(AiTask.objects.filter(status="DONE").count(), 1)

    def test_queue_retries_then_fails(self):
        from ..models import AiTask
        from ..queue import enqueue, run_pending
        enqueue("SCORE_APPLICATION", {"application_id": "00000000-0000-0000-0000-000000000000"})
        for _ in range(3):
            run_pending()
        task = AiTask.objects.get()
        self.assertEqual(task.status, "FAILED")
        self.assertEqual(task.attempts, 3)
        self.assertTrue(task.error)

    def test_unknown_task_type_fails_gracefully(self):
        from ..queue import enqueue, run_pending
        t = enqueue("DOES_NOT_EXIST", {})
        t.maxAttempts = 1
        t.save(update_fields=["maxAttempts"])
        run_pending()
        t.refresh_from_db()
        self.assertEqual(t.status, "FAILED")
        self.assertIn("Unbekannter taskType", t.error)

    def test_healthz_reports_structure(self):
        import json
        r = self.client.get(reverse('ats:healthz'))
        self.assertEqual(r.status_code, 200)   # DB+Media ok im Test
        body = json.loads(r.content)
        self.assertEqual(body["checks"]["db"], "ok")
        self.assertEqual(body["checks"]["media"], "ok")
        self.assertIn(body["status"], ["ok", "degraded"])  # KI fehlt im Test -> degraded

    def test_feeds_produce_wellformed_xml_with_special_chars(self):
        import xml.etree.ElementTree as ET
        self._job()  # Titel mit & < >
        for name in ["ats:stepstone_feed", "ats:hr_ba_xml_feed"]:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200)
            try:
                root = ET.fromstring(resp.content)
            except ET.ParseError as e:
                self.fail(f"{name} liefert kein wohlgeformtes XML: {e}")
            self.assertTrue(len(list(root.iter())) > 1)

class CsvImportTestCase(TestCase):
    """P0.5: Migrationsbrücke – Testlauf ändert nichts, keine Duplikate, ehrlicher Bericht."""

    def _world(self):
        import uuid as _u

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="B")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(title="Pflegefachkraft Station 3",
                                             organization=org, facility=fac,
                                             location=loc, jobFamily=fam, workflowState=wf)
        return self.job

    CSV_DE = ("\ufeffVorname;Nachname;E-Mail;Stelle;Status;Datum\r\n"
              "Max;Mustermann;max@x.de;Pflegefachkraft Station 3;neu;15.03.2026\r\n"
              "Erika;Beispiel;ERIKA@x.de;Pflegefachkraft Station 3;eingeladen;2026-02-01\r\n"
              "Kaputt;Zeile;keine-mail;Pflegefachkraft Station 3;neu;\r\n"
              "Uwe;Unbekannt;uwe@x.de;Gibt Es Nicht;neu;\r\n")

    def test_dry_run_reports_but_changes_nothing(self):
        from ..importer import parse_csv, run_import
        from ..models import Applicant, Application
        self._world()
        rows, fatal = parse_csv(self.CSV_DE.encode("utf-8"))
        self.assertIsNone(fatal)
        report = run_import(rows, dry_run=True)
        self.assertEqual(report["applications_created"], 2)
        self.assertEqual(report["applicants_new"], 2)
        self.assertEqual(len(report["errors"]), 2)         # kaputte Mail + unbekannte Stelle
        self.assertEqual(Applicant.objects.count(), 0)     # Garantie: NICHTS geändert
        self.assertEqual(Application.objects.count(), 0)

    def test_real_import_creates_and_maps(self):
        from ..importer import parse_csv, run_import
        from ..models import Applicant, Application, email_blind_index
        self._world()
        rows, _ = parse_csv(self.CSV_DE.encode("utf-8"))
        report = run_import(rows, dry_run=False)
        self.assertEqual(report["applications_created"], 2)
        self.assertEqual(Application.objects.count(), 2)
        erika = Applicant.objects.get(emailHash=email_blind_index("erika@x.de"))
        app = Application.objects.get(applicant=erika)
        self.assertEqual(app.status, "INVITED")            # Alias „eingeladen" gemappt
        self.assertEqual(app.source, "IMPORT")
        from django.utils import timezone as tz
        self.assertEqual(tz.localtime(app.createdAt).strftime("%Y-%m-%d"), "2026-02-01")
        fehler_zeilen = [z for z, _ in report["errors"]]
        self.assertEqual(fehler_zeilen, [4, 5])            # exakte Zeilennummern

    def test_reimport_skips_existing_and_reuses_applicant(self):
        from ..importer import parse_csv, run_import
        from ..models import Applicant, Application
        self._world()
        rows, _ = parse_csv(self.CSV_DE.encode("utf-8"))
        run_import(rows, dry_run=False)
        report2 = run_import(rows, dry_run=False)           # derselbe Import nochmal
        self.assertEqual(report2["applications_created"], 0)
        self.assertEqual(report2["skipped_existing"], 2)    # keine Duplikate
        self.assertEqual(Applicant.objects.count(), 2)
        self.assertEqual(Application.objects.count(), 2)

    def test_comma_and_english_headers_work(self):
        from ..importer import parse_csv, run_import
        self._world()
        csv_en = ("first_name,last_name,email,job\r\n"
                  "Jane,Doe,jane@x.de,Pflegefachkraft Station 3\r\n")
        rows, fatal = parse_csv(csv_en.encode("utf-8"))
        self.assertIsNone(fatal)
        report = run_import(rows, dry_run=False)
        self.assertEqual(report["applications_created"], 1)

    def test_default_job_for_rows_without_job_column(self):
        from ..importer import parse_csv, run_import
        job = self._world()
        csv_min = "Vorname;Nachname;E-Mail\r\nOhne;Stelle;ohne@x.de\r\n"
        rows, _ = parse_csv(csv_min.encode("utf-8"))
        self.assertEqual(len(run_import(rows, dry_run=True)["errors"]), 1)   # ohne Default: Fehler
        report = run_import(rows, default_job=job, dry_run=False)
        self.assertEqual(report["applications_created"], 1)

    def test_missing_required_headers_is_fatal(self):
        from ..importer import parse_csv
        rows, fatal = parse_csv(b"Spalte1;Spalte2\r\na;b\r\n")
        self.assertIn("Pflichtspalten fehlen", fatal)

    def test_view_requires_admin_and_audits(self):
        from ..models import AuditLog
        self._world()
        rec = make_user("imprec", role="Recruiter")
        self.client.force_login(rec)
        self.assertNotEqual(self.client.get(reverse('ats:data_import')).status_code, 200)
        admin = make_user("impadmin", role="HR-Admin")
        self.client.force_login(admin)
        r = self.client.post(reverse('ats:data_import'), data={
            "action": "import",
            "csv_file": SimpleUploadedFile("import.csv", self.CSV_DE.encode("utf-8"),
                                           content_type="text/csv")})
        self.assertContains(r, "Import abgeschlossen")
        self.assertContains(r, "Stelle nicht gefunden")     # Fehlerbericht sichtbar
        self.assertTrue(AuditLog.objects.filter(action="DATA_IMPORT").exists())
        # Vorlage-Download
        t = self.client.get(reverse('ats:import_template'))
        self.assertIn("Vorname;Nachname", t.content.decode("utf-8"))

class DemoSeedTestCase(TestCase):
    """P0.4: Demo-Instanz – Seed laeuft, Reset nur mit DEMO_MODE, Banner sichtbar."""

    @override_settings(DEMO_MODE=True)
    def test_seed_creates_consistent_world(self):
        from io import StringIO

        from django.core.management import call_command

        from ..models import Application, ApprovalTicket, Facility, JobAlertSubscription, JobPosting
        out = StringIO()
        call_command("seed_demo", stdout=out)
        self.assertGreaterEqual(JobPosting.objects.count(), 6)
        self.assertGreaterEqual(Application.objects.count(), 30)
        self.assertEqual(ApprovalTicket.objects.filter(status="PENDING").count(), 1)
        self.assertEqual(JobAlertSubscription.objects.count(), 2)
        self.assertTrue(Facility.objects.filter(requiresApproval=True).exists())
        # Idempotent ohne --reset: zweiter Lauf dupliziert nichts
        jobs_before = JobPosting.objects.count()
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(JobPosting.objects.count(), jobs_before)

    def test_reset_refuses_without_demo_mode(self):
        from django.core.management import CommandError, call_command
        with self.assertRaises(CommandError):
            call_command("seed_demo", "--reset")

    @override_settings(DEMO_MODE=True)
    def test_reset_rebuilds_with_demo_mode(self):
        from io import StringIO

        from django.core.management import call_command

        from ..models import Application
        call_command("seed_demo", stdout=StringIO())
        n = Application.objects.count()
        call_command("seed_demo", "--reset", stdout=StringIO())
        self.assertEqual(Application.objects.count(), n)   # deterministisch gleich

    @override_settings(DEMO_MODE=True)
    def test_demo_banner_and_logins(self):
        from io import StringIO

        from django.core.management import call_command
        call_command("seed_demo", stdout=StringIO())
        r = self.client.get(reverse('ats:home'))
        self.assertContains(r, "Demo-Instanz")              # Banner
        self.assertTrue(self.client.login(username="demo-admin",
                                          password="securats-demo-2026"))
        # BOLA-Demo: demo-recruiter sieht nur Hamburg
        self.client.login(username="demo-recruiter", password="securats-demo-2026")
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertEqual(resp.status_code, 200)

class XlsxAndCvImportTestCase(TestCase):
    """Umstiegs-Substanz: Excel-Import + CV-Dateiberg-Zuordnung (ZIP)."""

    def _xlsx(self, rows):
        import io

        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        for r in rows:
            ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def _world(self):
        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="XI-Fam")
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(title="Pflegefachkraft",
                                             organization=org, facility=fac,
                                             location=loc, jobFamily=fam,
                                             workflowState=wf)

    def test_parse_xlsx_maps_german_headers_like_csv(self):
        from ..importer import parse_xlsx
        data = self._xlsx([
            ["Vorname", "Nachname", "E-Mail", "Telefon"],
            ["Maria", "Weber", "maria.weber@web.de", "0171 1"],
            [None, None, None, None],                       # Excel-Leerzeile
            ["Ali", "Kaya", "ali.kaya@gmx.de", ""],
        ])
        rows, fatal = parse_xlsx(data)
        self.assertIsNone(fatal)
        self.assertEqual(len(rows), 2)                      # Leerzeile still weg
        self.assertEqual(rows[0]["first_name"], "Maria")
        self.assertEqual(rows[0]["email"], "maria.weber@web.de")
        self.assertEqual(rows[1]["_line"], 4)               # echte Excel-Zeile
        bad, fatal = parse_xlsx(self._xlsx([["Vorname", "Telefon"], ["x", "1"]]))
        self.assertIn("Pflichtspalten fehlen", fatal)
        self.assertIn("email", fatal)

    def test_import_view_accepts_xlsx_end_to_end(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from ..models import Application
        self._world()
        self.client.force_login(make_user("xladmin", role="HR-Admin"))
        f = SimpleUploadedFile("altsystem.xlsx", self._xlsx([
            ["Vorname", "Nachname", "E-Mail"],
            ["Maria", "Weber", "maria.weber@web.de"]]))
        r = self.client.post(reverse('ats:data_import'), data={
            "csv_file": f, "action": "import",
            "default_job": str(self.job.id)})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Application.objects.count(), 1)    # echt importiert

    def test_cv_zip_matching_dry_and_real(self):
        import io
        import zipfile

        from ..importer import match_cv_files
        from ..models import Applicant, Application, ApplicationDocument
        self._world()
        ap = Applicant.objects.create(firstName="Maria", lastName="Weber",
                                      email="maria.weber@web.de")
        app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                         status="NEW")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("maria.weber@web.de_Lebenslauf.pdf", b"%PDF-1.4 x")
            zf.writestr("unbekannt@x.de_CV.pdf", b"%PDF-1.4 y")
            zf.writestr("ohne-mail.pdf", b"%PDF-1.4 z")
            zf.writestr("../evil/maria.weber@web.de_Zeugnis.exe", b"MZ")
        data = buf.getvalue()
        report = match_cv_files(data, dry_run=True)
        self.assertEqual(len(report["matched"]), 1)
        self.assertEqual(report["matched"][0][3], "CV")     # Typ erkannt
        self.assertEqual(len(report["unmatched"]), 2)
        self.assertEqual(len(report["errors"]), 1)          # .exe abgelehnt
        self.assertEqual(ApplicationDocument.objects.count(), 0)  # Testlauf!
        report = match_cv_files(data, dry_run=False)
        self.assertEqual(report["attached"], 1)
        doc = ApplicationDocument.objects.get()
        self.assertEqual(doc.application_id, app.id)
        self.assertEqual(doc.docType, "CV")
        self.assertNotIn("..", doc.file.name)               # Traversal neutralisiert

@override_settings(DEMO_MODE=True)
class DemoBankWorldTestCase(TestCase):
    """Die Banken-Demo-Welt (BAWAG-Stil) ist klickbar und zeigt alle Features."""

    def setUp(self):
        import os
        from io import StringIO

        from django.core.management import call_command
        os.environ["DEMO_MODE"] = "1"
        call_command("seed_demo_bank", stdout=StringIO())

    def tearDown(self):
        import os
        os.environ.pop("DEMO_MODE", None)

    def test_world_branding_and_category_filter(self):
        from ..models import JobFamily, JobPosting
        self.assertEqual(JobPosting.objects.count(), 3)
        fam_ba = JobFamily.objects.get(name="IT Business Analysis")
        # Kategorien-Filter der Stellenboerse (Bereich > Jobfamilie)
        page = self.client.get(f"/jobs/?family={fam_ba.id}")
        self.assertContains(page, "Senior IT Business Analyst")
        self.assertNotContains(page, "Customer Relationship Manager")
        # Banken-CI: Dunkelrot auf hellem Grund, oeffentlich
        self.assertContains(page, "brand-css")
        self.assertContains(page, "#a0132f")
        self.assertContains(page, "--bg-color: #f5f7fa")

    def test_dynamic_form_and_process_governance(self):

        from ..models import ApplicationVote, JobPosting
        j_ba = JobPosting.objects.get(
            title__startswith="Senior IT Business Analyst")
        form = self.client.get(reverse('ats:bewerben', args=[j_ba.id]))
        self.assertContains(form, "ISO 20022")               # SELECT-Option
        self.assertContains(form, "regulatorisches Projekt") # TEXT-Frage
        self.assertContains(form, "regulierten Umfeld")      # Mindeststandard
        # Tech-Prozess: 2er-Gremium konfiguriert, 1/2 Stimme im Demo-Stand
        self.assertEqual(len(j_ba.panelUserIdsJson), 2)
        self.assertEqual(ApplicationVote.objects.filter(
            application__jobPosting=j_ba).count(), 1)

    def test_career_hub_landing_with_funnel_source(self):
        page = self.client.get(reverse('ats:landing_page',
                                       args=["karriere-banking"]))
        self.assertContains(page, "Arbeiten bei der BAWAG Group (Demo)")
        self.assertContains(page, "13. und 14. Gehalt")
        self.assertContains(page, "Senior IT Business Analyst")
        self.assertContains(page, "Julia Steiner")            # Ansprechperson
        # Kampagnen-Quelle sitzt in der Session (Slug = Quelle)
        self.assertEqual(self.client.session.get("application_src"),
                         "KARRIERE-BANKING")

class ImportMappingAndAddressTestCase(TestCase):
    """P0-5: manuelle Spalten-Zuordnung + Adressfeld."""

    def _world(self):
        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="IM-Fam")
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(title="Stelle",
                                             organization=org, facility=fac,
                                             location=loc, jobFamily=fam,
                                             workflowState=wf)

    def test_address_imported_via_synonym(self):
        from ..importer import parse_csv, run_import
        from ..models import Applicant
        self._world()
        csv = ("Vorname;Nachname;E-Mail;Anschrift\n"
               "Maria;Weber;mw-adr@x.de;Musterweg 5, 20095 Hamburg\n")
        rows, fatal = parse_csv(csv.encode())
        self.assertIsNone(fatal)
        run_import(rows, default_job=self.job, dry_run=False)
        ap = Applicant.objects.get()
        self.assertEqual(ap.address, "Musterweg 5, 20095 Hamburg")

    def test_manual_override_wins_and_ui_shows_mapping(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from ..models import Application
        self._world()
        self.client.force_login(make_user("imadmin", role="HR-Admin"))
        csv = (b"Vorname;Nachname;MailAdr\nIna;Kolb;ina-ov@x.de\n")
        # Ohne Override: E-Mail-Spalte unerkannt -> Pflichtspalten-Fehler
        r = self.client.post(reverse('ats:data_import'), data={
            "csv_file": SimpleUploadedFile("alt.csv", csv),
            "action": "preview"})
        self.assertContains(r, "Pflichtspalten fehlen")
        # Mit manueller Zuordnung MailAdr -> email: Import laeuft
        r = self.client.post(reverse('ats:data_import'), data={
            "csv_file": SimpleUploadedFile("alt.csv", csv),
            "action": "import", "default_job": str(self.job.id),
            "map_email": "MailAdr"})
        self.assertEqual(Application.objects.count(), 1)
        # Zuordnungs-Dialog sichtbar, Override vorausgewaehlt
        self.assertContains(r, "Spalten-Zuordnung prüfen")
        self.assertContains(r, 'value="MailAdr" selected')

class HrisExportHonestyTestCase(TestCase):
    """HRIS-Export: darf NIEMALS Erfolg erfinden.

    Befund: Die frühere Fassung stellte nie eine HTTP-Anfrage, erfand eine
    SAP-ID, schrieb sie in die Bewerberakte und protokollierte
    HRIS_EXPORT_SUCCESS mit "target": "SAP_SF_PRODUCTION" im Audit-Log.
    Das Audit-Log ist der Compliance-Nachweis – es darf nicht lügen.
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
        loc = Location.objects.create(name="HH", city="Hamburg")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="HE-Fam")
        ws = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="Pflegekraft", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=ws)
        self.app = Application.objects.create(
            applicant=Applicant.objects.create(firstName="H", lastName="E",
                                               email="he@x.de"),
            jobPosting=job, status="INVITED")

    def _run(self, **kw):
        from io import StringIO

        from django.core.management import call_command
        out = StringIO()
        call_command("hris_export", stdout=out, **kw)
        return out.getvalue()

    def test_without_endpoint_it_refuses_instead_of_faking(self):
        """Der Kern: Ohne Konfiguration wird abgebrochen – KEIN Erfolg,
        KEIN Audit-Eintrag, KEINE erfundene ID."""
        import os

        from django.core.management.base import CommandError

        from ..models import AuditLog
        os.environ.pop('HRIS_ENDPOINT', None)
        with self.assertRaises(CommandError):
            self._run()
        self.assertFalse(AuditLog.objects.filter(
            action="HRIS_EXPORT_SUCCESS").exists())
        self.app.refresh_from_db()
        self.assertNotIn("SAP-ID", self.app.internalNotes or "")

    def test_no_fabricated_sap_id_anywhere_in_code(self):
        """Regressions-Wache: Die Schein-Antwort darf nicht zurückkehren."""
        import ast
        import inspect

        from ats.management.commands import hris_export
        src = inspect.getsource(hris_export)
        # Nur den CODE pruefen – der Modul-Docstring erklaert bewusst, was
        # frueher falsch war und darf die Begriffe nennen.
        tree = ast.parse(src)
        code = "\n".join(
            ast.unparse(n) for n in tree.body
            if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)))
        self.assertNotIn("mock_response", code)
        self.assertNotIn("SAP_SF_PRODUCTION", code)
        self.assertNotIn("SF-CAND-", code)
        # Und: es MUSS einen echten HTTP-Aufruf geben
        self.assertIn("urlopen", code)

    def test_dry_run_transmits_nothing_and_leaks_no_pii(self):
        from ..models import AuditLog
        out = self._run(dry_run=True)
        self.assertIn("DRY-RUN", out)
        self.assertNotIn("he@x.de", out)          # keine PII im Terminal
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_real_transmission_logs_only_real_values(self):
        """Mit Endpunkt wird wirklich gesendet; protokolliert wird nur, was
        das Zielsystem tatsächlich zurückgab."""
        import json
        import os
        from unittest.mock import patch

        from ..models import AuditLog
        os.environ['HRIS_ENDPOINT'] = 'https://hris.example/api/candidates'
        try:
            with patch.object(
                    __import__('ats.management.commands.hris_export',
                               fromlist=['Command']).Command, '_post',
                    return_value=("SF-REAL-42", 201)):
                self._run()
            entry = AuditLog.objects.get(action="HRIS_EXPORT_SUCCESS")
            meta = json.loads(entry.metadataJson)
            self.assertEqual(meta["remoteId"], "SF-REAL-42")
            self.assertEqual(meta["httpStatus"], 201)
            self.app.refresh_from_db()
            self.assertIn("SF-REAL-42", self.app.internalNotes)
        finally:
            os.environ.pop('HRIS_ENDPOINT', None)

    def test_transmission_failure_is_logged_as_failure(self):
        """Ein Fehler beim Zielsystem wird als FEHLER protokolliert –
        nicht als Erfolg."""
        import os
        from unittest.mock import patch

        from ..models import AuditLog
        os.environ['HRIS_ENDPOINT'] = 'https://hris.example/api/candidates'
        try:
            with patch.object(
                    __import__('ats.management.commands.hris_export',
                               fromlist=['Command']).Command, '_post',
                    side_effect=OSError("Verbindung abgelehnt")):
                self._run()
            self.assertFalse(AuditLog.objects.filter(
                action="HRIS_EXPORT_SUCCESS").exists())
            self.assertTrue(AuditLog.objects.filter(
                action="HRIS_EXPORT_FAILED").exists())
        finally:
            os.environ.pop('HRIS_ENDPOINT', None)

class SapMapperHonestyTestCase(TestCase):
    """SAP-Feldzuordnung: war ein Blender, ist jetzt ein echtes Werkzeug.

    Befund: Der POST tat NICHTS, meldete aber „Synchronisation erfolgreich",
    zählte „exportierte Bewerbersätze" und die Oberfläche gab einen frei
    erfundenen „SAP Response-Code: 201 Created" aus. Die Zielsystem-Auswahl bot
    „SAP SF Production (Echtes HRIS)" an – der Wert hieß intern MOCK_SAP_PROD.
    In einer Demo hätte ein Interessent geglaubt, die Anbindung funktioniere.
    """

    def setUp(self):
        self.admin = make_user("sap-admin", role="HR-Admin")
        self.client.force_login(self.admin)

    def test_saving_mapping_never_claims_a_transfer(self):
        import json
        r = self.client.post(reverse('ats:sap_sf_mapper'), {
            "mapping_data": json.dumps({"email": "sf_email",
                                        "lastName": "sf_last_name"})})
        body = r.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["saved_fields"], 2)
        # Kein Erfolgs-Theater mehr:
        self.assertNotIn("records_exported", body)
        self.assertIn("KEINE Daten übertragen", body["message"])

    def test_mapping_is_persisted(self):
        import json

        self.client.post(reverse('ats:sap_sf_mapper'), {
            "mapping_data": json.dumps({"email": "sf_email"})})
        saved = SystemSetting.objects.get(key="HRIS_FIELD_MAPPING")
        self.assertEqual(json.loads(saved.value), {"email": "sf_email"})

    def test_invalid_mapping_is_rejected(self):
        r = self.client.post(reverse('ats:sap_sf_mapper'),
                             {"mapping_data": "kein json"})
        self.assertEqual(r.status_code, 400)

    def test_ui_no_longer_fabricates_a_sap_response_code(self):
        """Regressions-Wache gegen das erfundene „201 Created"."""
        import os
        tpl = os.path.join('templates', 'sap_sf_mapper.html')
        src = open(tpl, encoding='utf-8').read()
        self.assertNotIn("201 Created", src)
        self.assertNotIn("MOCK_SAP_PROD", src)
        self.assertNotIn("mTLS Verbindung", src)
        self.assertIn("KEINE Daten übertragen", src)

    def test_export_actually_uses_the_saved_mapping(self):
        """Der Kreis schließt sich: Die gespeicherte Zuordnung wird vom
        echten Export tatsächlich angewendet – der Mapper ist kein
        Schaufenster mehr."""
        import json

        from ats.management.commands.hris_export import Command

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
        SystemSetting.objects.create(
            key="HRIS_FIELD_MAPPING",
            value=json.dumps({"email": "sf_email", "lastName": "sf_last_name"}))
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH", city="Hamburg")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="SM-Fam")
        ws = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="J", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=ws)
        app = Application.objects.create(
            applicant=Applicant.objects.create(firstName="S", lastName="Meier",
                                               email="sm@x.de"),
            jobPosting=job, status="INVITED")
        payload = Command()._payload(app)
        self.assertEqual(payload["candidate"],
                         {"sf_email": "sm@x.de", "sf_last_name": "Meier"})
