"""P5: ROI-/Inklusions-Export (CSV) für die Leitung (CFO Braun).

Deckt ab: Zugriff nur Leitung (BR/SBV sehen Governance ohne Knopf),
CSV-Grundform (BOM, Semikolon), Kennzahlen-Inhalt, Anonymitäts-Schwelle
der Inklusions-Quote, Audit-Eintrag.
"""
from django.test import TestCase
from django.urls import reverse

from ..models import AuditLog, SourceChannel
from .factories import make_application, make_job, make_world
from .utils import make_user


class RoiExportAccessTestCase(TestCase):
    def test_only_hr_admin(self):
        viewer = make_user("roi-viewer", role="Viewer")
        self.client.force_login(viewer)
        resp = self.client.get(reverse('ats:roi_export'))
        self.assertNotEqual(resp.status_code, 200)

    def test_button_only_for_leadership(self):
        admin = make_user("roi-admin", role="HR-Admin")
        viewer = make_user("roi-viewer2", role="Viewer")
        self.client.force_login(admin)
        self.assertContains(self.client.get(reverse('ats:governance')),
                            'roi-export.csv')
        self.client.force_login(viewer)
        self.assertNotContains(self.client.get(reverse('ats:governance')),
                               'roi-export.csv')


class RoiExportContentTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)
        self.admin = make_user("roi-cfo", role="HR-Admin")
        self.client.force_login(self.admin)

    def _csv(self) -> str:
        resp = self.client.get(reverse('ats:roi_export'))
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode('utf-8')

    def test_csv_form_and_core_rows(self):
        make_application(self.job, status="HIRED")
        make_application(self.job, status="NEW")
        SourceChannel.objects.create(name="Jobmesse", slug="messe",
                                     costAmount=1200)
        body = self._csv()
        self.assertTrue(body.startswith('\ufeff'))       # BOM für Excel
        self.assertIn('Bereich;Kennzahl;Wert', body)      # Semikolon
        self.assertIn('Besetzung;Einstellungen;1;', body)
        self.assertIn('Besetzung;Bewerbungen eingegangen;2;', body)
        self.assertIn('Kanalkosten;Kampagnenkosten gesamt;1200', body)
        self.assertIn('Kosten je Einstellung;1200.0', body)
        # Aggregate ohne Namen: kein Bewerbername im Export
        self.assertNotIn('Mira', body)

    def test_inclusion_threshold_hides_rates(self):
        make_application(self.job, status="INVITED", severeDisability="JA")
        body = self._csv()
        self.assertIn('Bewerbungen mit § 164-Angabe;1;', body)
        self.assertIn('unter Anonymitätsschwelle', body)

    def test_inclusion_rates_above_threshold(self):
        for i in range(5):
            make_application(self.job, status="INVITED" if i < 4 else "NEW",
                             severeDisability="JA")
            make_application(self.job, status="INVITED" if i < 2 else "NEW")
        body = self._csv()
        self.assertIn('Einladungsquote mit/ohne Angabe;80 % / 40 %;', body)

    def test_export_is_audited(self):
        self._csv()
        audit = AuditLog.objects.filter(action='ROI_EXPORT').first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.userId, self.admin.get_username())
