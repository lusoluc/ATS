"""SecurATS-Tests: audit/dsgvo (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .utils import make_user


class AuditChainTestCase(TestCase):
    """WP2/UC-MB-12: Append-Only-Integrität via Hash-Kette."""

    def test_chain_is_valid_and_detects_tampering(self):
        from ..audit import verify_audit_chain, write_audit
        from ..models import AuditLog
        write_audit("READ_CV", application_id="a1")
        write_audit("STATUS_CHANGE", application_id="a1", to="INVITED")
        write_audit("READ_DOCUMENT", application_id="a2")
        self.assertTrue(verify_audit_chain()["ok"])

        # Manipulation eines bestehenden Eintrags bricht die Kette
        mid = AuditLog.objects.order_by("seq")[1]
        mid.metadataJson = '{"to": "REJECTED"}'
        mid.save(update_fields=["metadataJson"])
        result = verify_audit_chain()
        self.assertFalse(result["ok"])
        self.assertEqual(result["broken_id"], str(mid.id))

    def test_deleting_an_entry_breaks_the_chain(self):
        """Das häufigste Vertuschungsszenario: einen Eintrag LÖSCHEN (statt
        ändern). Der Nachfolger zeigt dann auf einen prevHash, den es nicht
        mehr gibt -> die Kette muss brechen."""
        from ..audit import verify_audit_chain, write_audit
        from ..models import AuditLog
        write_audit("READ_CV", application_id="d1")
        mid = write_audit("STATUS_CHANGE", application_id="d1", to="INVITED")
        write_audit("READ_DOCUMENT", application_id="d2")
        self.assertTrue(verify_audit_chain()["ok"])
        # Mittleren Eintrag entfernen (z.B. um eine Einsicht zu verbergen)
        AuditLog.objects.filter(id=mid.id).delete()
        self.assertFalse(verify_audit_chain()["ok"])

    def test_truncating_the_tail_is_the_one_undetectable_case(self):
        """Ehrliche Grenze der reinen Hash-Kette: Wird das ENDE der Kette
        abgeschnitten (die letzten n Einträge gelöscht), bleibt der Rest in
        sich stimmig – das ist ohne externen Anker (z.B. periodisch
        veröffentlichter Root-Hash) prinzipiell nicht erkennbar. Dieser Test
        HÄLT DIESE ANNAHME FEST, damit sie bewusst bleibt und nicht mit
        falscher Sicherheit verwechselt wird."""
        from ..audit import verify_audit_chain, write_audit
        from ..models import AuditLog
        write_audit("READ_CV", application_id="t1")
        write_audit("READ_CV", application_id="t2")
        last = write_audit("READ_CV", application_id="t3")
        AuditLog.objects.filter(id=last.id).delete()   # Ende gekappt
        # Bekannte Grenze: bleibt gültig. Wenn dieser Test eines Tages
        # fehlschlägt, wurde ein Anker-Mechanismus ergänzt -> Doku anpassen.
        self.assertTrue(verify_audit_chain()["ok"])

    def test_chain_recovers_after_manipulation_is_reverted(self):
        """Wird eine Manipulation rückgängig gemacht, muss die Kette wieder
        als gültig erkannt werden (kein Fehlalarm-Rest)."""
        from ..audit import verify_audit_chain, write_audit
        from ..models import AuditLog
        write_audit("A", application_id="r1")
        mid = write_audit("B", application_id="r1")
        write_audit("C", application_id="r1")
        original = mid.metadataJson
        mid.metadataJson = '{"x": 1}'
        mid.save(update_fields=["metadataJson"])
        self.assertFalse(verify_audit_chain()["ok"])
        # zurücksetzen
        AuditLog.objects.filter(id=mid.id).update(metadataJson=original)
        self.assertTrue(verify_audit_chain()["ok"])

    def test_unchained_legacy_entries_do_not_break_chain(self):
        """Alt-Einträge ohne entryHash (aus der Zeit vor der Kette) dürfen
        die Verifikation nicht scheitern lassen, werden aber gezählt."""
        from ..audit import verify_audit_chain, write_audit
        from ..models import AuditLog
        AuditLog.objects.create(action="LEGACY", metadataJson="{}")  # kein Hash
        write_audit("NEU", application_id="l1")
        result = verify_audit_chain()
        self.assertTrue(result["ok"])
        self.assertEqual(result["unchained"], 1)

    def test_ai_execution_entries_are_chained(self):
        from ..audit import verify_audit_chain, write_audit
        from ..views import log_ai_execution
        write_audit("READ_CV", application_id="a1")
        log_ai_execution("Scoring", "gemma:2b", 1.0, True, False, "", False,
                         prompt_used="Bewerbertext")
        self.assertTrue(verify_audit_chain()["ok"])

    def test_rapid_writes_with_timestamp_ties_stay_verifiable(self):
        """Regression: Bei schnellen Folge-Writes kollidiert createdAt
        (Uhr-Auflösung), und die zufällige UUID würde die Reihenfolge
        kippen. Die Kettenordnung MUSS über die Sequenz laufen – sonst
        meldet die Verifikation falschen Manipulations-Alarm."""
        from ..audit import verify_audit_chain, write_audit
        for i in range(50):
            write_audit(f"RAPID_{i}")
        result = verify_audit_chain()
        self.assertTrue(result["ok"])
        self.assertEqual(result["checked"], 50)

class DsgvoExportTestCase(TestCase):
    """WP2/UC-MB-07: Betroffenenauskunft enthält alle Daten, keine internen Vermerke."""

    def test_export_contains_person_applications_and_audit(self):
        import uuid as _u

        from ..audit import write_audit
        from ..dsgvo import build_applicant_export
        from ..models import (
            Applicant,
            Application,
            ApplicationDocument,
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
        job = JobPosting.objects.create(title="Pflegekraft", organization=org, facility=fac,
                                        location=loc, jobFamily=fam, workflowState=wf)
        ap = Applicant.objects.create(firstName="Aylin", lastName="Yildiz", email="ay@ex.org")
        app = Application.objects.create(applicant=ap, jobPosting=job, status="IN_REVIEW",
                                         coverLetterTxt="Mein Anschreiben",
                                         internalNotes="GEHEIMER interner Vermerk")
        ApplicationDocument.objects.create(application=app, name="zeugnis.pdf")
        write_audit("READ_CV", application_id=str(app.id))

        data = build_applicant_export(ap)
        self.assertEqual(data["betroffene_person"]["email"], "ay@ex.org")
        self.assertEqual(data["betroffene_person"]["vorname"], "Aylin")  # entschlüsselt
        self.assertEqual(len(data["bewerbungen"]), 1)
        self.assertEqual(data["bewerbungen"][0]["anschreiben"], "Mein Anschreiben")
        self.assertIn("zeugnis.pdf", data["bewerbungen"][0]["nachweise"])
        self.assertTrue(any(e["action"] == "READ_CV" for e in data["zugriffsprotokoll"]))
        # interne Vermerke dürfen NICHT im Export erscheinen
        import json as _j
        self.assertNotIn("GEHEIMER", _j.dumps(data, ensure_ascii=False))

class AuditExportTestCase(TestCase):
    """UC-JF-10/MB-08/NS-12: Audit-Nachweis als Datei, mit Integritaets-Kopfzeile."""

    def test_export_with_chain_status_and_filters(self):
        from ..audit import write_audit
        write_audit("STATUS_CHANGE", application_id="x1")
        write_audit("DATA_IMPORT", rows=5)
        admin = make_user("audadmin", role="HR-Admin")
        self.client.force_login(admin)
        r = self.client.get(reverse('ats:audit_export'))
        body = r.content.decode("utf-8")
        self.assertIn("Hash-Kette: INTAKT", body)             # Integritaet in der Datei
        self.assertIn("STATUS_CHANGE", body)
        self.assertIn("DATA_IMPORT", body)
        self.assertIn('filename="securats-audit-', r["Content-Disposition"])
        # Aktions-Filter
        r2 = self.client.get(reverse('ats:audit_export') + "?action=DATA_IMPORT")
        body2 = r2.content.decode("utf-8")
        self.assertIn("DATA_IMPORT", body2)
        self.assertNotIn("STATUS_CHANGE;", body2)
        # Export selbst auditiert
        from ..models import AuditLog
        self.assertTrue(AuditLog.objects.filter(action="AUDIT_EXPORTED").exists())

    def test_export_requires_admin_and_validates_dates(self):
        rec = make_user("audrec", role="Recruiter")
        self.client.force_login(rec)
        self.assertNotEqual(self.client.get(reverse('ats:audit_export')).status_code, 200)
        admin = make_user("audadmin2", role="HR-Admin")
        self.client.force_login(admin)
        r = self.client.get(reverse('ats:audit_export') + "?von=gestern")
        self.assertEqual(r.status_code, 400)

class TalentPoolPurgeAndStatsTestCase(TestCase):
    """Purge-Command (DSGVO) + Wirksamkeits-Kennzahlen."""

    def _sub(self, email, days_expired):
        from ..models import TalentPoolSubscription
        return TalentPoolSubscription.objects.create(
            email=email, consentId="c", criteria="{}",
            expiresAt=timezone.now() - datetime.timedelta(days=days_expired))

    def test_purge_respects_grace_period(self):
        from io import StringIO

        from django.core.management import call_command

        from ..models import AuditLog, TalentPoolSubscription
        self._sub("alt@x.de", days_expired=45)                 # lange abgelaufen
        self._sub("frisch@x.de", days_expired=5)               # in Kulanz
        self._sub("aktiv@x.de", days_expired=-100)     # gueltig
        call_command("purge_talent_pool", stdout=StringIO())
        emails = set(TalentPoolSubscription.objects.values_list("email", flat=True))
        self.assertEqual(emails, {"frisch@x.de", "aktiv@x.de"})
        self.assertTrue(AuditLog.objects.filter(action="TALENT_POOL_PURGED").exists())
        # engere Kulanz raeumt auch den frischen weg
        call_command("purge_talent_pool", "--grace-days", "0", stdout=StringIO())
        emails = set(TalentPoolSubscription.objects.values_list("email", flat=True))
        self.assertEqual(emails, {"aktiv@x.de"})

    def test_stats_count_conversion(self):
        import uuid as _u

        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            TalentPoolContact,
            TalentPoolSubscription,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="Pflegefachkraft neu", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=wf)
        sub = TalentPoolSubscription.objects.create(
            email="timo@x.de", consentId="c", criteria="{}",
            expiresAt=timezone.now() + datetime.timedelta(days=100))
        TalentPoolContact.objects.create(subscription=sub, jobPosting=job)
        # Konversion: nach dem Hinweis kommt die Bewerbung derselben E-Mail
        ap = Applicant.objects.create(firstName="Timo", lastName="V", email="timo@x.de")
        Application.objects.create(applicant=ap, jobPosting=job, status="NEW")
        rec = make_user("statrec", role="Recruiter")
        self.client.force_login(rec)
        page = self.client.get(reverse('ats:talent_pool'))
        self.assertContains(page, "daraus neue Bewerbungen")
        self.assertContains(page, "aktive Einwilligungen")
        # Kennzahl 1 Hinweis / 1 Konversion sichtbar
        self.assertContains(page, "Hinweise versendet")

class DataRetentionAnonymizationTestCase(TestCase):
    """DSGVO-Anonymisierung (`data_retention`) – bisher UNGETESTET, obwohl
    sie Personendaten unwiderruflich verändert und per Cron automatisch läuft.

    Diese Tests sichern beide Fehlerrichtungen ab:
      * zu VIEL löschen (aktive Bewerbungen, Talent-Pool-Einwilligung,
        frische Absagen) -> Datenverlust, Vertrauensbruch
      * zu WENIG löschen (Fristen greifen nicht) -> DSGVO-Verstoß
    """

    def _world(self):
        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="DR-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Pflegefachkraft", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=ws)

    def _application(self, email, status, age_days, consent=False,
                     first="Erika", last="Muster"):
        from ..models import Applicant, Application
        ap = Applicant.objects.create(firstName=first, lastName=last,
                                      email=email, phone="0170-1")
        app = Application.objects.create(
            applicant=ap, jobPosting=self.job, status=status,
            coverLetterTxt="Mein Anschreiben",
            internalNotes="Interner Vermerk",
            consentTalentPool=consent)
        # updatedAt ist auto_now -> per Query zurückdatieren
        Application.objects.filter(id=app.id).update(
            updatedAt=timezone.now() - datetime.timedelta(days=age_days))
        app.refresh_from_db()
        return ap, app

    def _run(self, days=180, dry=False):
        from io import StringIO

        from django.core.management import call_command
        out = StringIO()
        args = ["data_retention", "--days", str(days)]
        if dry:
            args.append("--dry-run")
        call_command(*args, stdout=out)
        return out.getvalue()

    def test_old_rejection_without_consent_is_anonymized(self):
        self._world()
        ap, app = self._application("alt@x.de", "REJECTED", age_days=200)
        self._run()
        app.refresh_from_db()
        ap.refresh_from_db()
        self.assertEqual(app.coverLetterTxt, "ANONYMISIERT")
        self.assertIsNone(app.cvStorageId)
        self.assertEqual(ap.lastName, "Anonymisiert")
        self.assertIsNone(ap.phone)
        self.assertNotEqual(ap.email, "alt@x.de")   # PII ersetzt

    def test_talent_pool_consent_protects_from_anonymization(self):
        """Einwilligung = Aufbewahrungsgrund. Wer zugestimmt hat, bleibt."""
        self._world()
        ap, app = self._application("pool@x.de", "REJECTED", age_days=300,
                                    consent=True)
        self._run()
        app.refresh_from_db()
        ap.refresh_from_db()
        self.assertEqual(app.coverLetterTxt, "Mein Anschreiben")
        self.assertEqual(ap.email, "pool@x.de")     # unangetastet

    def test_recent_rejection_is_not_touched(self):
        self._world()
        ap, app = self._application("frisch@x.de", "REJECTED", age_days=10)
        self._run(days=180)
        ap.refresh_from_db()
        self.assertEqual(ap.email, "frisch@x.de")   # Frist noch nicht um

    def test_active_application_never_anonymized(self):
        self._world()
        ap, app = self._application("aktiv@x.de", "IN_REVIEW", age_days=999)
        self._run()
        app.refresh_from_db()
        ap.refresh_from_db()
        self.assertEqual(app.coverLetterTxt, "Mein Anschreiben")
        self.assertEqual(ap.email, "aktiv@x.de")

    def test_person_with_other_active_application_keeps_identity(self):
        """Der subtilste Fall: alte Absage bei Stelle A, aber die Person
        läuft bei Stelle B noch aktiv mit. Die ALTE Bewerbung wird
        anonymisiert – die PERSON darf es nicht, sonst verliert das
        laufende Verfahren seinen Bewerber."""
        from ..models import Application
        self._world()
        ap, old_app = self._application("beides@x.de", "REJECTED",
                                        age_days=250)
        active = Application.objects.create(
            applicant=ap, jobPosting=self.job, status="INVITED",
            coverLetterTxt="Zweite Bewerbung")
        self._run()
        old_app.refresh_from_db()
        ap.refresh_from_db()
        active.refresh_from_db()
        # Die alte Bewerbung ist anonymisiert ...
        self.assertEqual(old_app.coverLetterTxt, "ANONYMISIERT")
        # ... die Person bleibt aber identifizierbar (laufendes Verfahren!)
        self.assertEqual(ap.email, "beides@x.de")
        self.assertEqual(ap.lastName, "Muster")
        self.assertEqual(active.coverLetterTxt, "Zweite Bewerbung")

    def test_dry_run_changes_nothing(self):
        self._world()
        ap, app = self._application("probe@x.de", "REJECTED", age_days=250)
        out = self._run(dry=True)
        app.refresh_from_db()
        ap.refresh_from_db()
        self.assertIn("DRY-RUN", out)
        self.assertEqual(app.coverLetterTxt, "Mein Anschreiben")
        self.assertEqual(ap.email, "probe@x.de")

    def test_anonymization_is_audited(self):
        from ..models import AuditLog
        self._world()
        ap, app = self._application("audit@x.de", "REJECTED", age_days=250)
        self._run()
        self.assertTrue(AuditLog.objects.filter(
            action="ANONYMIZE_DSGVO", applicationId=str(app.id)).exists())

    def test_withdrawn_is_treated_like_rejected(self):
        self._world()
        ap, app = self._application("zurueck@x.de", "WITHDRAWN",
                                    age_days=250)
        self._run()
        app.refresh_from_db()
        self.assertEqual(app.coverLetterTxt, "ANONYMISIERT")

    def test_cv_file_is_deleted_from_storage(self):
        """Anonymisierung muss auch die HOCHGELADENE DATEI entfernen –
        ein Datenbankfeld zu leeren genügt nicht, die PDF liegt sonst
        weiter im Dateisystem."""

        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage

        from ..models import Application
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                self._world()
                ap, app = self._application("cv@x.de", "REJECTED",
                                            age_days=250)
                path = default_storage.save("cvs/lebenslauf.pdf",
                                            ContentFile(b"%PDF-1.4 fake"))
                Application.objects.filter(id=app.id).update(cvStorageId=path)
                self.assertTrue(default_storage.exists(path))
                self._run()
                app.refresh_from_db()
                self.assertIsNone(app.cvStorageId)
                self.assertFalse(default_storage.exists(path),
                                 "CV-Datei liegt noch im Dateisystem!")
