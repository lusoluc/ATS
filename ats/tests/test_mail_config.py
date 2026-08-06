"""Mailversand: Konfiguration, Ehrlichkeit, Einstellungs-Zentrale.

Vor diesem Paket gab es GAR KEINE Mail-Einstellungen. Django fiel auf seinen
Standard `localhost:25` zurück, und weil an 31 Stellen `fail_silently=True`
steht, verschwanden Absagen, Einladungen und Magic-Links spurlos — die
Oberfläche meldete „verschickt", zugestellt wurde nichts.
"""
import os
from unittest import mock

from django.core import mail as django_mail
from django.test import TestCase
from django.urls import reverse

from ..mail_config import (
    HOST_KEY,
    PASSWORD_KEY,
    has_password,
    is_configured,
    mail_settings,
    mail_status,
    record_result,
    store_password,
)
from ..models import AuditLog, SystemSetting
from .utils import make_user


class MailConfigTestCase(TestCase):
    def setUp(self):
        # Umgebungsvariablen der Entwicklungsmaschine duerfen die Tests nicht
        # verfaelschen - hier gilt ausschliesslich, was der Test setzt.
        patcher = mock.patch.dict(os.environ, {
            "EMAIL_HOST": "", "EMAIL_PORT": "", "EMAIL_HOST_USER": "",
            "EMAIL_HOST_PASSWORD": "", "EMAIL_SECURITY": "",
            "DEFAULT_FROM_EMAIL": ""}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_nothing_configured_is_reported_as_such(self):
        self.assertFalse(is_configured())
        self.assertFalse(mail_status()['configured'])

    def test_settings_from_the_database_are_used(self):
        SystemSetting.objects.create(key=HOST_KEY, value="mail.traeger.de")
        SystemSetting.objects.create(key="MAIL_FROM", value="bewerbung@traeger.de")
        cfg = mail_settings()
        self.assertTrue(cfg.configured)
        self.assertEqual(cfg.host, "mail.traeger.de")
        self.assertEqual(cfg.port, 587)      # STARTTLS-Regelfall
        self.assertTrue(cfg.use_tls)

    def test_environment_beats_the_database(self):
        """Eine Deployment-Entscheidung wiegt schwerer als ein Formular."""
        SystemSetting.objects.create(key=HOST_KEY, value="aus-der-datenbank")
        with mock.patch.dict(os.environ, {"EMAIL_HOST": "aus-der-umgebung"}):
            cfg = mail_settings()
            self.assertEqual(cfg.host, "aus-der-umgebung")
            self.assertIn("host", cfg.from_env)

    def test_ssl_defaults_to_port_465(self):
        SystemSetting.objects.create(key=HOST_KEY, value="mail.traeger.de")
        SystemSetting.objects.create(key="MAIL_SECURITY", value="ssl")
        cfg = mail_settings()
        self.assertEqual(cfg.port, 465)
        self.assertTrue(cfg.use_ssl)
        self.assertFalse(cfg.use_tls)

    def test_password_is_stored_encrypted_and_never_plain(self):
        store_password("geheim123")
        raw = SystemSetting.objects.get(key=PASSWORD_KEY).value
        self.assertNotIn("geheim123", raw)
        self.assertEqual(mail_settings().password, "geheim123")
        self.assertTrue(has_password())

    def test_status_never_reveals_the_password(self):
        store_password("geheim123")
        self.assertNotIn("geheim123", str(mail_status()))
        self.assertTrue(mail_status()['has_password'])

    def test_undecryptable_password_counts_as_missing(self):
        """Nach einem Schluesselwechsel lieber ein ehrliches „fehlt" als ein
        Anmeldeversuch mit Buchstabensalat."""
        SystemSetting.objects.create(key=PASSWORD_KEY, value="kein-gueltiges-token")
        self.assertEqual(mail_settings().password, "")

    def test_last_result_is_remembered(self):
        record_result(False, "Connection refused")
        last = mail_status()['last']
        self.assertFalse(last['ok'])
        self.assertIn("Connection refused", last['detail'])


class MailBackendTestCase(TestCase):
    """Ohne hinterlegten Server wird nichts zugestellt - und das steht danach
    im Zustand, statt nur im Nichts zu verschwinden."""

    def setUp(self):
        patcher = mock.patch.dict(os.environ, {"EMAIL_HOST": ""}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_sending_without_configuration_delivers_nothing_and_says_so(self):
        from ..mail_backend import ConfiguredSmtpBackend
        backend = ConfiguredSmtpBackend()
        message = django_mail.EmailMessage("Betreff", "Text", "a@b.de", ["c@d.de"])
        with self.assertLogs('ats.mail_backend', level='ERROR'):
            sent = backend.send_messages([message])
        self.assertEqual(sent, 0)
        last = mail_status()['last']
        self.assertFalse(last['ok'])
        self.assertIn("Kein Mailserver", last['detail'])


class MailSettingsPageTestCase(TestCase):
    def setUp(self):
        self.admin = make_user("mail-admin", role="HR-Admin")
        self.client.force_login(self.admin)
        self.url = reverse('ats:mail_settings')
        patcher = mock.patch.dict(os.environ, {
            "EMAIL_HOST": "", "EMAIL_HOST_PASSWORD": "",
            "DEFAULT_FROM_EMAIL": ""}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_only_hr_admin(self):
        self.client.force_login(make_user("mail-rec", role="Recruiter"))
        self.assertNotEqual(self.client.get(self.url).status_code, 200)

    def test_page_names_the_gap_when_nothing_is_configured(self):
        self.assertContains(self.client.get(self.url),
                            "es wird nichts zugestellt")

    def test_saving_the_server_and_auditing_it(self):
        self.client.post(self.url, {'host': 'mail.traeger.de', 'port': '587',
                                    'security': 'starttls', 'user': 'ats',
                                    'password': 'geheim',
                                    'from_address': 'bewerbung@traeger.de'})
        cfg = mail_settings()
        self.assertEqual(cfg.host, 'mail.traeger.de')
        self.assertEqual(cfg.password, 'geheim')
        self.assertTrue(AuditLog.objects.filter(
            action='MAIL_SETTINGS_CHANGED').exists())

    def test_empty_password_field_keeps_the_stored_one(self):
        """Sonst löschte jedes Speichern das Passwort — es steht ja nie im
        Formular."""
        store_password('bleibt')
        self.client.post(self.url, {'host': 'mail.traeger.de',
                                    'from_address': 'x@y.de', 'password': ''})
        self.assertEqual(mail_settings().password, 'bleibt')

    def test_password_can_be_removed_deliberately(self):
        store_password('weg damit')
        self.client.post(self.url, {'host': 'mail.traeger.de',
                                    'from_address': 'x@y.de',
                                    'clear_password': '1'})
        self.assertEqual(mail_settings().password, '')

    def test_environment_values_are_locked_not_silently_ignored(self):
        with mock.patch.dict(os.environ, {"EMAIL_HOST": "fix.example"}):
            resp = self.client.get(self.url)
            self.assertContains(resp, "Umgebungsvariablen")
            # Ein Formularwert darf den Umgebungswert nicht ueberschreiben
            self.client.post(self.url, {'host': 'versuch.example',
                                        'from_address': 'x@y.de'})
            self.assertEqual(mail_settings().host, "fix.example")
        self.assertEqual(SystemSetting.objects.filter(key=HOST_KEY).count(), 0)

    def test_test_send_reports_the_real_error(self):
        SystemSetting.objects.create(key=HOST_KEY, value="mail.traeger.de")
        SystemSetting.objects.create(key="MAIL_FROM", value="x@y.de")
        with mock.patch('django.core.mail.send_mail',
                        side_effect=OSError("Connection refused")):
            resp = self.client.post(self.url, {'action': 'test',
                                               'recipient': 'chef@traeger.de'},
                                    follow=True)
        self.assertContains(resp, "Connection refused")
        self.assertTrue(AuditLog.objects.filter(action='MAIL_TEST_SENT').exists())


class SettingsHubTestCase(TestCase):
    def setUp(self):
        self.client.force_login(make_user("hub-admin", role="HR-Admin"))
        self.url = reverse('ats:settings_hub')

    def test_only_hr_admin(self):
        self.client.force_login(make_user("hub-rec", role="Recruiter"))
        self.assertNotEqual(self.client.get(self.url).status_code, 200)

    def test_open_points_are_shown_first(self):
        """Wer neu aufsetzt, soll nicht raten muessen, was noch fehlt."""
        resp = self.client.get(self.url)
        self.assertContains(resp, "Noch einzurichten")
        self.assertContains(resp, "E-Mail-Versand")

    def test_hub_links_the_configuration_pages(self):
        resp = self.client.get(self.url)
        for name in ('ats:mail_settings', 'ats:privacy_notice', 'ats:retention',
                     'ats:locations', 'ats:pay_bands', 'ats:ki_page',
                     'ats:hris_page', 'ats:branding'):
            self.assertContains(resp, reverse(name))

    def test_sidebar_offers_the_hub(self):
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertContains(resp, reverse('ats:settings_hub'))


class AdminOnlyVisibilityTestCase(TestCase):
    """„Nur für den Admin sichtbar" heißt: auch serverseitig geschützt.

    Zwei Seiten liefen auseinander — verlinkt nur im Admin-Block, geöffnet
    werden konnten sie von jeder internen Rolle.
    """

    def test_channel_costs_are_leadership_only(self):
        """Kanalkosten speisen „Kosten je Einstellung", das die Analytik nur
        der Leitung zeigt. Die Pflegeseite stand jeder Rolle offen."""
        self.client.force_login(make_user("kanal-rec", role="Recruiter"))
        self.assertEqual(
            self.client.get(reverse('ats:source_channels')).status_code, 403)
        self.client.force_login(make_user("kanal-admin", role="HR-Admin"))
        self.assertEqual(
            self.client.get(reverse('ats:source_channels')).status_code, 200)

    def test_own_delegation_stays_reachable_for_every_role(self):
        """Gegenprobe: Die Vertretung ist ausdrücklich Selbstbedienung — ein
        Vorstand legt seine Urlaubsvertretung selbst an. Sie darf NICHT auf
        HR-Admin verengt werden."""
        self.client.force_login(make_user("vertret-rec", role="Recruiter"))
        self.assertEqual(
            self.client.get(reverse('ats:delegations')).status_code, 200)

    def test_delegation_link_is_visible_without_admin_rights(self):
        """Der Link stand nur im Admin-Block: Wer keine Admin-Rechte hatte,
        kam an die eigene Vertretung nicht heran."""
        self.client.force_login(make_user("vertret-rec2", role="Recruiter"))
        self.assertContains(self.client.get(reverse('ats:dashboard')),
                            reverse('ats:delegations'))

    def test_settings_hub_is_not_offered_to_non_admins(self):
        self.client.force_login(make_user("hub-nichtadmin", role="Recruiter"))
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertNotContains(resp, reverse('ats:settings_hub'))
