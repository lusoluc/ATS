"""SecurATS-Tests: Entgelttransparenz E1 (EU-RL 2023/970, Art. 5).

Kern-Garantien:
- Ohne Entgeltband geht keine Stelle online (Publish-Gate, nicht umgehbar
  über Editor ODER Schnell-Toggle).
- Die Spanne samt Tarifhinweis steht öffentlich im Stellendetail.
- Der BA-Syndizierungs-Feed transportiert die Spanne mit.
- Bänder pflegt nur HR-Admin.
"""
from django.test import TestCase
from django.urls import reverse

from ..models import (
    AuditLog,
    Facility,
    JobFamily,
    JobPosting,
    Location,
    Organization,
    PayBand,
    WorkflowState,
)
from .utils import make_user


def _world():
    org = Organization.objects.create(name="PT-Org")
    fac = Facility.objects.create(name="PT-Klinik", organization=org)
    loc = Location.objects.create(name="PT-HH", city="Hamburg")
    fam = JobFamily.objects.create(name="PT-Pflege")
    published, _ = WorkflowState.objects.get_or_create(
        name="published", defaults={"description": "Öffentlich"})
    band = PayBand.objects.create(
        name="TVöD-P 7 (Stufe 2–6)", tariffSystem="TVOED",
        minAmount=3304, maxAmount=4106, period="MONTH",
        collectiveAgreement="TVöD-P, Entgeltgruppe P7",
        note="zzgl. Schichtzulagen")
    return org, fac, loc, fam, published, band


class PayBandModelTestCase(TestCase):
    def test_range_label_formats_german(self):
        band = PayBand.objects.create(
            name="B", minAmount=3304, maxAmount=4106, period="MONTH")
        self.assertEqual(band.range_label, "3.304 – 4.106 € pro Monat")


class PayBandAdminTestCase(TestCase):
    """Stammdaten-Pflege: nur HR-Admin, mit Audit-Eintrag."""

    def test_recruiter_forbidden(self):
        self.client.force_login(make_user("pt-rec", role="Recruiter"))
        self.assertEqual(self.client.get(reverse("ats:pay_bands")).status_code, 403)

    def test_admin_creates_and_archives_band(self):
        self.client.force_login(make_user("pt-admin", role="HR-Admin"))
        resp = self.client.post(reverse("ats:pay_bands"), data={
            "name": "AVR C 7", "tariffSystem": "AVR_CARITAS",
            "minAmount": "3400", "maxAmount": "4200", "period": "MONTH",
            "collectiveAgreement": "AVR Caritas, Anlage 32"})
        self.assertEqual(resp.status_code, 302)
        band = PayBand.objects.get(name="AVR C 7")
        self.assertTrue(AuditLog.objects.filter(action="PAY_BAND_CREATED").exists())
        self.client.post(reverse("ats:archive_pay_band", args=[band.id]))
        band.refresh_from_db()
        self.assertTrue(band.archived)

    def test_invalid_range_rejected(self):
        self.client.force_login(make_user("pt-admin2", role="HR-Admin"))
        self.client.post(reverse("ats:pay_bands"), data={
            "name": "Kaputt", "minAmount": "5000", "maxAmount": "3000"})
        self.assertFalse(PayBand.objects.filter(name="Kaputt").exists())


class PayPublishGateTestCase(TestCase):
    """Art. 5: ohne Entgeltband keine Veröffentlichung — auf allen Pfaden."""

    def setUp(self):
        self.org, self.fac, self.loc, self.fam, self.published, self.band = _world()
        self.client.force_login(make_user("pt-rec-gate", role="Recruiter"))

    def _save_job(self, extra):
        data = {"title": "Pflegefachkraft (m/w/d)",
                "description": "Text",
                "facility": str(self.fac.id), "location": str(self.loc.id),
                "job_family": str(self.fam.id),
                "workflow_state": str(self.published.id)}
        data.update(extra)
        return self.client.post(reverse("ats:create_job"), data=data)

    def test_publish_without_band_demoted_to_draft(self):
        self._save_job({})
        job = JobPosting.objects.get(title="Pflegefachkraft (m/w/d)")
        self.assertNotEqual(job.workflowState.name, "published")
        self.assertTrue(AuditLog.objects.filter(
            action="PAY_TRANSPARENCY_GATE_BLOCKED").exists())

    def test_publish_with_band_stays_published(self):
        self._save_job({"pay_band": str(self.band.id)})
        job = JobPosting.objects.get(title="Pflegefachkraft (m/w/d)")
        self.assertEqual(job.workflowState.name, "published")
        self.assertEqual(job.payBand_id, self.band.id)

    def test_quick_toggle_cannot_bypass_gate(self):
        draft, _ = WorkflowState.objects.get_or_create(
            name="draft", defaults={"description": "Entwurf"})
        job = JobPosting.objects.create(
            title="Ohne Band", organization=self.org, facility=self.fac,
            location=self.loc, jobFamily=self.fam, workflowState=draft)
        resp = self.client.post(reverse("ats:toggle_job_active", args=[job.id]))
        self.assertEqual(resp.status_code, 409)
        self.assertIn("Entgelttransparenz", resp.json()["error"])
        job.refresh_from_db()
        self.assertEqual(job.workflowState.name, "draft")

    def test_quick_toggle_works_with_band(self):
        draft, _ = WorkflowState.objects.get_or_create(
            name="draft", defaults={"description": "Entwurf"})
        job = JobPosting.objects.create(
            title="Mit Band", organization=self.org, facility=self.fac,
            location=self.loc, jobFamily=self.fam, workflowState=draft,
            payBand=self.band)
        resp = self.client.post(reverse("ats:toggle_job_active", args=[job.id]))
        self.assertTrue(resp.json()["success"])
        job.refresh_from_db()
        self.assertEqual(job.workflowState.name, "published")


class PayPublicDisplayTestCase(TestCase):
    """Art. 5 Abs. 1: Spanne + Tarifhinweis öffentlich VOR dem Gespräch."""

    def setUp(self):
        self.org, self.fac, self.loc, self.fam, self.published, self.band = _world()
        self.job = JobPosting.objects.create(
            title="Pflegefachkraft Station 1", organization=self.org,
            facility=self.fac, location=self.loc, jobFamily=self.fam,
            workflowState=self.published, payBand=self.band)

    def test_job_detail_shows_range_and_tariff(self):
        resp = self.client.get(reverse("ats:job_detail", args=[self.job.id]))
        self.assertContains(resp, "3.304 – 4.106 € pro Monat")
        self.assertContains(resp, "TVöD-P, Entgeltgruppe P7")
        self.assertContains(resp, "zzgl. Schichtzulagen")
        self.assertContains(resp, "geschlechtsneutralen Kriterien")

    def test_job_detail_without_band_has_no_pay_block(self):
        self.job.payBand = None
        self.job.save(update_fields=["payBand"])
        resp = self.client.get(reverse("ats:job_detail", args=[self.job.id]))
        self.assertNotContains(resp, "Vergütung</h2>")

    def test_ba_feed_contains_pay_range(self):
        # Ohne konfiguriertes FEED_ACCESS_TOKEN ist der Feed offen (Bestandslogik)
        resp = self.client.get(reverse("ats:hr_ba_xml_feed"))
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode("utf-8")
        self.assertIn("<verguetung>", body)
        self.assertIn("<von>3304.00</von>", body)
        self.assertIn("<bis>4106.00</bis>", body)
        self.assertIn("TVöD-P, Entgeltgruppe P7", body)


class GuardrailPayTransparencyTestCase(TestCase):
    """Wächter: Das Publish-Gate darf nicht stillschweigend entfernt werden.

    Schlägt an, wenn create_job/toggle_job_active den pay_transparency-Hook
    verlieren — die FehlerKLASSE 'Stelle ohne Vergütungsangabe geht online'
    bleibt damit dauerhaft abgesichert (Muster wie die übrigen Guardrails)."""

    def test_job_views_wire_pay_gate(self):
        import inspect

        from ..views import jobs as jobs_module
        src = inspect.getsource(jobs_module.create_job)
        self.assertIn("pay_blocked_reason", src)
        src_toggle = inspect.getsource(jobs_module.toggle_job_active)
        self.assertIn("pay_blocked_reason", src_toggle)

    def test_question_paths_wire_history_guard(self):
        """E2: Alle Wege, auf denen Fragen ins System kommen, prüfen die
        Gehaltshistorie — Editor, Registry/Mindeststandards, KI-Validierung."""
        import inspect

        from .. import process_advisor
        from ..views import jobs as jobs_module
        from ..views import settings_admin
        self.assertIn("strip_salary_history_questions",
                      inspect.getsource(jobs_module.create_job))
        self.assertIn("salary_history_violation",
                      inspect.getsource(settings_admin.screening_questions_view))
        self.assertIn("salary_history_violation",
                      inspect.getsource(process_advisor._validate_ai_questions))


class PayRangeAuditAnchorTestCase(TestCase):
    """E3: Jede veröffentlichte Spanne wird in der Audit-HASH-KETTE verankert —
    manipulationssicherer Nachweis, welche Spanne wann öffentlich war."""

    def setUp(self):
        self.org, self.fac, self.loc, self.fam, self.published, self.band = _world()

    def _job(self, state=None, band=None, title="Anker-Stelle"):
        return JobPosting.objects.create(
            title=title, organization=self.org, facility=self.fac,
            location=self.loc, jobFamily=self.fam,
            workflowState=state or self.published, payBand=band)

    def test_publish_creates_chained_entry_with_metadata(self):
        import json as _json

        from ..audit import verify_audit_chain
        self._job(band=self.band)
        entry = AuditLog.objects.get(action="PAY_RANGE_PUBLISHED")
        self.assertTrue(entry.entryHash)                       # Teil der Kette
        meta = _json.loads(entry.metadataJson)
        self.assertEqual(meta["band"], "TVöD-P 7 (Stufe 2–6)")
        self.assertEqual(meta["min"], "3304")
        self.assertEqual(meta["max"], "4106")
        self.assertEqual(meta["event"], "PUBLISHED")
        self.assertTrue(verify_audit_chain()["ok"])

    def test_unrelated_resave_does_not_duplicate(self):
        job = self._job(band=self.band)
        job.title = "Anker-Stelle (geändert)"
        job.save()
        self.assertEqual(
            AuditLog.objects.filter(action="PAY_RANGE_PUBLISHED").count(), 1)

    def test_band_change_while_published_is_anchored_again(self):
        job = self._job(band=self.band)
        other = PayBand.objects.create(name="P8", minAmount=3490, maxAmount=4410)
        job.payBand = other
        job.save()
        events = [e for e in AuditLog.objects.filter(
            action="PAY_RANGE_PUBLISHED").order_by("seq")]
        self.assertEqual(len(events), 2)
        import json as _json
        self.assertEqual(_json.loads(events[1].metadataJson)["event"],
                         "BAND_CHANGED")

    def test_draft_job_is_not_anchored(self):
        draft, _ = WorkflowState.objects.get_or_create(
            name="draft", defaults={"description": "Entwurf"})
        self._job(state=draft, band=self.band)
        self.assertFalse(
            AuditLog.objects.filter(action="PAY_RANGE_PUBLISHED").exists())

    def test_toggle_activation_is_anchored(self):
        draft, _ = WorkflowState.objects.get_or_create(
            name="draft", defaults={"description": "Entwurf"})
        job = self._job(state=draft, band=self.band)
        self.client.force_login(make_user("e3-rec", role="Recruiter"))
        self.client.post(reverse("ats:toggle_job_active", args=[job.id]))
        self.assertTrue(
            AuditLog.objects.filter(action="PAY_RANGE_PUBLISHED").exists())


class PayBandEvaluationTestCase(TestCase):
    """E3 / Art. 4: Tätigkeitsbewertung je Band (vier Kriterien)."""

    def setUp(self):
        _, _, _, _, _, self.band = _world()

    def test_has_evaluation_requires_all_four(self):
        self.assertFalse(self.band.has_evaluation)
        self.band.criteriaSkills = "Examen"
        self.band.criteriaEffort = "Schichtdienst"
        self.band.criteriaResponsibility = "Medikamentengabe"
        self.assertFalse(self.band.has_evaluation)             # 3 von 4
        self.band.criteriaWorkingConditions = "Stationsdienst"
        self.assertTrue(self.band.has_evaluation)

    def test_evaluate_via_view_saves_and_audits(self):
        self.client.force_login(make_user("e3-admin", role="HR-Admin"))
        self.client.post(reverse("ats:pay_bands"), data={
            "action": "evaluate", "band_id": str(self.band.id),
            "criteriaSkills": "3-jähriges Examen",
            "criteriaEffort": "Wechselschicht, Grundpflege",
            "criteriaResponsibility": "Medikamentengabe, Doku",
            "criteriaWorkingConditions": "Station, Patientenkontakt"})
        self.band.refresh_from_db()
        self.assertTrue(self.band.has_evaluation)
        self.assertTrue(AuditLog.objects.filter(
            action="PAY_BAND_EVALUATED").exists())
        page = self.client.get(reverse("ats:pay_bands"))
        self.assertContains(page, "✓ bewertet")


class TransparencyOverviewTestCase(TestCase):
    """E4: Kennzahlen — Abdeckung, unbewertete Bänder, Familien-Ampel."""

    def setUp(self):
        self.org, self.fac, self.loc, self.fam, self.published, self.band = _world()

    def _job(self, title, band, fam=None):
        return JobPosting.objects.create(
            title=title, organization=self.org, facility=self.fac,
            location=self.loc, jobFamily=fam or self.fam,
            workflowState=self.published, payBand=band)

    def test_counts_and_conflicts(self):
        from ..pay_transparency import transparency_overview
        other_band = PayBand.objects.create(name="P8", minAmount=3490,
                                            maxAmount=4410)
        other_fam = JobFamily.objects.create(name="PT-Verwaltung")
        self._job("Stelle A", self.band)
        self._job("Stelle B", other_band)                       # gleiche Familie, anderes Band
        self._job("Stelle C", self.band, fam=other_fam)         # eigene Familie, ein Band
        # Altbestand ohne Band (am Gate vorbei per ORM, wie Bestandsdaten)
        JobPosting.objects.create(
            title="Altbestand", organization=self.org, facility=self.fac,
            location=self.loc, jobFamily=other_fam,
            workflowState=self.published)
        o = transparency_overview()
        self.assertEqual(o["published"], 4)
        self.assertEqual(o["with_band"], 3)
        self.assertEqual(o["without_band"], 1)
        self.assertEqual(len(o["family_conflicts"]), 1)
        conflict = o["family_conflicts"][0]
        self.assertEqual(conflict["family"], "PT-Pflege")
        self.assertEqual([b["band"] for b in conflict["bands"]],
                         ["P8", "TVöD-P 7 (Stufe 2–6)"])
        # beide Bänder unbewertet (keine Art.-4-Kriterien gesetzt)
        self.assertIn("P8", o["unevaluated_bands"])

    def test_evaluated_band_not_listed(self):
        from ..pay_transparency import transparency_overview
        self.band.criteriaSkills = "Examen"
        self.band.criteriaEffort = "Schicht"
        self.band.criteriaResponsibility = "Medikamente"
        self.band.criteriaWorkingConditions = "Station"
        self.band.save()
        self.assertNotIn(self.band.name,
                         transparency_overview()["unevaluated_bands"])

    def test_analytics_page_shows_cockpit(self):
        self._job("Stelle A", self.band)
        self.client.force_login(make_user("e4-admin", role="HR-Admin"))
        page = self.client.get(reverse("ats:analytics"))
        self.assertContains(page, "Entgelttransparenz")
        self.assertContains(page, "veröffentlichte Stellen mit Entgeltband")


class SalaryHistoryDetectionTestCase(TestCase):
    """E2/Art. 5 Abs. 2: Erkennung — Historie verboten, Vorstellung erlaubt."""

    def test_detects_history_questions(self):
        from ..pay_transparency import salary_history_violation
        verboten = [
            "Was war Ihr letztes Gehalt?",
            "Wie hoch ist Ihre aktuelle Vergütung?",
            "Bitte nennen Sie Ihren derzeitigen Verdienst.",
            "Reichen Sie Ihre letzten drei Gehaltsabrechnungen ein.",
            "Bitte fügen Sie einen Gehaltsnachweis bei.",
            "Ihr bisheriges Bruttojahresgehalt?",
            "Was verdienen Sie momentan?",
            "What is your current salary?",
            "Please provide your salary history.",
        ]
        for frage in verboten:
            self.assertIsNotNone(salary_history_violation(frage),
                                 f"Nicht erkannt: {frage}")

    def test_allows_salary_expectation(self):
        from ..pay_transparency import salary_history_violation
        erlaubt = [
            "Was ist Ihre Gehaltsvorstellung?",
            "Welches Wunschgehalt schwebt Ihnen vor?",
            "Ab wann können Sie anfangen?",
            "Wir zahlen faire Vergütung nach Tarif.",
            "Die Gehaltsspanne finden Sie in der Anzeige.",
        ]
        for frage in erlaubt:
            self.assertIsNone(salary_history_violation(frage),
                              f"Fälschlich blockiert: {frage}")


class SalaryHistoryEnforcementTestCase(TestCase):
    """E2: Durchsetzung an allen vier Eingangswegen."""

    def setUp(self):
        self.org, self.fac, self.loc, self.fam, self.published, self.band = _world()

    def test_create_job_strips_history_question_keeps_legit(self):
        import json as _json
        self.client.force_login(make_user("e2-rec", role="Recruiter"))
        self.client.post(reverse("ats:create_job"), data={
            "title": "E2-Stelle", "description": "Text",
            "facility": str(self.fac.id), "location": str(self.loc.id),
            "job_family": str(self.fam.id),
            "workflow_state": str(self.published.id),
            "pay_band": str(self.band.id),
            "screening_questions": _json.dumps([
                {"id": "q1", "question": "Was war Ihr letztes Gehalt?",
                 "type": "TEXT", "isMandatory": False},
                {"id": "q2", "question": "Haben Sie ein Examen?",
                 "type": "YES_NO", "isMandatory": True,
                 "expectedAnswer": "YES"},
                {"id": "q3", "question": "Was ist Ihre Gehaltsvorstellung?",
                 "type": "TEXT", "isMandatory": False},
            ])})
        job = JobPosting.objects.get(title="E2-Stelle")
        fragen = [q["question"] for q in job.screeningQuestionsJson]
        self.assertNotIn("Was war Ihr letztes Gehalt?", fragen)
        self.assertIn("Haben Sie ein Examen?", fragen)          # bleibt
        self.assertIn("Was ist Ihre Gehaltsvorstellung?", fragen)  # zulässig
        self.assertTrue(AuditLog.objects.filter(
            action="PAY_HISTORY_QUESTION_BLOCKED").exists())

    def test_registry_rejects_history_question(self):
        from ..models import ScreeningQuestion
        self.client.force_login(make_user("e2-admin", role="HR-Admin"))
        self.client.post(reverse("ats:screening_questions"), data={
            "question": "Bitte nennen Sie Ihr aktuelles Gehalt."})
        self.assertFalse(ScreeningQuestion.objects.filter(
            question__icontains="Gehalt").exists())
        self.assertTrue(AuditLog.objects.filter(
            action="PAY_HISTORY_QUESTION_BLOCKED").exists())
        # Zulässige Frage geht weiterhin durch
        self.client.post(reverse("ats:screening_questions"), data={
            "question": "Was ist Ihre Gehaltsvorstellung?"})
        self.assertTrue(ScreeningQuestion.objects.filter(
            question="Was ist Ihre Gehaltsvorstellung?").exists())

    def test_minimum_standards_filtered(self):
        import json as _json
        self.client.force_login(make_user("e2-admin2", role="HR-Admin"))
        self.client.post(reverse("ats:screening_questions"), data={
            "form": "minimum", "family_id": str(self.fam.id),
            "minimum_json": _json.dumps([
                {"id": "m1", "question": "Was haben Sie zuletzt verdient?",
                 "type": "TEXT", "isMandatory": True},
                {"id": "m2", "question": "Führerschein Klasse B?",
                 "type": "YES_NO", "isMandatory": True},
            ])})
        self.fam.refresh_from_db()
        fragen = [q["question"] for q in self.fam.minimumQuestionsJson]
        self.assertEqual(fragen, ["Führerschein Klasse B?"])

    def test_ai_validator_filters_history_question(self):
        import json as _json

        from ..process_advisor import _validate_ai_questions
        raw = _json.dumps([
            {"question": "Wie hoch war Ihr bisheriges Gehalt im letzten Job?"},
            {"question": "Mit welchen Dokumentationssystemen haben Sie gearbeitet?"},
        ])
        out = _validate_ai_questions(raw, set())
        texte = [q["question"] for q in out]
        self.assertEqual(
            texte, ["Mit welchen Dokumentationssystemen haben Sie gearbeitet?"])
