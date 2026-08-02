"""P4: Datenaufbewahrung — konfigurierbare Löschfrist + Trockenlauf.

Deckt ab: Frist-Setting mit Leitplanken (Clamp + Audit), Trockenlauf-Vorschau
zählt exakt die Command-Kriterien (eine Wahrheit), der Command nutzt die
konfigurierte Frist als Default, und die Anonymisierung löscht auch die
freiwillige § 164-Angabe (Art.-9-Datum).
"""
import datetime

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import Application, AuditLog, SystemSetting
from ..retention import (
    DEFAULT_RETENTION_DAYS,
    MAX_DAYS,
    MIN_DAYS,
    RETENTION_DAYS_KEY,
    configured_retention_days,
    dry_run_preview,
)
from .factories import make_application, make_job, make_world
from .utils import make_user


def _age(app: Application, days: int) -> None:
    """updatedAt zurückdatieren (auto_now umgehen via QuerySet.update)."""
    Application.objects.filter(id=app.id).update(
        updatedAt=timezone.now() - datetime.timedelta(days=days))


class ConfiguredDaysTestCase(TestCase):
    def test_default_without_setting(self):
        self.assertEqual(configured_retention_days(), DEFAULT_RETENTION_DAYS)

    def test_setting_wins(self):
        SystemSetting.objects.create(key=RETENTION_DAYS_KEY, value="90")
        self.assertEqual(configured_retention_days(), 90)

    def test_out_of_range_values_are_clamped(self):
        SystemSetting.objects.create(key=RETENTION_DAYS_KEY, value="5")
        self.assertEqual(configured_retention_days(), MIN_DAYS)
        SystemSetting.objects.filter(key=RETENTION_DAYS_KEY).update(value="9999")
        self.assertEqual(configured_retention_days(), MAX_DAYS)

    def test_garbage_falls_back_to_default(self):
        SystemSetting.objects.create(key=RETENTION_DAYS_KEY, value="bald")
        self.assertEqual(configured_retention_days(), DEFAULT_RETENTION_DAYS)


class DryRunPreviewTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)

    def test_counts_only_expired_terminal_without_consent(self):
        old_rejected = make_application(self.job, status="REJECTED")
        _age(old_rejected, 200)
        old_withdrawn = make_application(self.job, status="WITHDRAWN")
        _age(old_withdrawn, 200)
        # Gegenproben: frisch, aktiv, Talent-Pool-Einwilligung
        _age(make_application(self.job, status="REJECTED"), 10)
        _age(make_application(self.job, status="IN_REVIEW"), 200)
        pool = make_application(self.job, status="REJECTED",
                                consentTalentPool=True)
        _age(pool, 200)
        preview = dry_run_preview(180)
        self.assertEqual(preview['total'], 2)
        self.assertEqual(preview['rejected'], 1)
        self.assertEqual(preview['withdrawn'], 1)
        self.assertEqual(preview['days'], 180)

    def test_uses_configured_days_when_none(self):
        SystemSetting.objects.create(key=RETENTION_DAYS_KEY, value="30")
        app = make_application(self.job, status="REJECTED")
        _age(app, 40)   # jünger als 180, älter als 30
        self.assertEqual(dry_run_preview()['total'], 1)


class RetentionPageTestCase(TestCase):
    def setUp(self):
        self.admin = make_user("ret-admin", role="HR-Admin")
        self.client.force_login(self.admin)

    def test_requires_hr_admin(self):
        self.client.logout()
        viewer = make_user("ret-viewer", role="Viewer")
        self.client.force_login(viewer)
        resp = self.client.get(reverse('ats:retention'))
        self.assertNotEqual(resp.status_code, 200)

    def test_page_renders_with_preview(self):
        resp = self.client.get(reverse('ats:retention'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Trockenlauf")
        self.assertContains(resp, str(DEFAULT_RETENTION_DAYS))

    def test_save_writes_setting_and_audit(self):
        resp = self.client.post(reverse('ats:retention'), {'days': '365'})
        self.assertEqual(resp.status_code, 302)
        row = SystemSetting.objects.get(key=RETENTION_DAYS_KEY)
        self.assertEqual(row.value, "365")
        audit = AuditLog.objects.filter(action='RETENTION_POLICY_CHANGED').first()
        self.assertIsNotNone(audit)
        self.assertIn('"old_days": 180', audit.metadataJson)
        self.assertIn('"new_days": 365', audit.metadataJson)

    def test_invalid_values_rejected(self):
        for bad in ('7', '5000', 'morgen', ''):
            self.client.post(reverse('ats:retention'), {'days': bad})
        self.assertFalse(
            SystemSetting.objects.filter(key=RETENTION_DAYS_KEY).exists())
        self.assertFalse(
            AuditLog.objects.filter(action='RETENTION_POLICY_CHANGED').exists())


class CommandUsesSettingTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)

    def test_command_default_is_configured_days(self):
        SystemSetting.objects.create(key=RETENTION_DAYS_KEY, value="30")
        app = make_application(self.job, status="REJECTED")
        _age(app, 40)   # unter dem 180er-Default, über der konfigurierten Frist
        call_command('data_retention', verbosity=0)
        app.refresh_from_db()
        self.assertEqual(app.coverLetterTxt, "ANONYMISIERT")

    def test_anonymization_clears_severe_disability(self):
        app = make_application(self.job, status="REJECTED",
                               severeDisability="JA")
        _age(app, 200)
        call_command('data_retention', verbosity=0)
        app.refresh_from_db()
        self.assertEqual(app.severeDisability, "")
        # Bewerberdaten sind ebenfalls anonymisiert
        self.assertEqual(app.applicant.lastName, "Anonymisiert")
