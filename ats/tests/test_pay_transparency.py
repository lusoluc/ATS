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
