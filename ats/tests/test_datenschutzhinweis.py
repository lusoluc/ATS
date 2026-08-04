"""Z1: Fassungen des Datenschutzhinweises im Produkt pflegen.

Art. 7 Abs. 1 DSGVO verlangt den Nachweis, worin eingewilligt wurde. Anlegen
ging bisher nur über die Django-Administration — eine technische Oberfläche,
die in der Personalabteilung niemand öffnet. Die Governance-Sicht benannte die
Lücke, aber der Weg zur Behebung führte aus dem Produkt heraus.

Kernregel dieser Seite: **anfügen statt ändern.** Ein nachträglich geänderter
Text würde den Nachweis zerstören, der er sein soll.
"""
from django.test import TestCase
from django.urls import reverse

from ..models import AuditLog, PrivacyNoticeVersion
from .factories import make_application, make_job, make_world
from .utils import make_user


class PrivacyNoticePageTestCase(TestCase):
    def setUp(self):
        self.admin = make_user("dsgvo-admin", role="HR-Admin")
        self.client.force_login(self.admin)
        self.url = reverse('ats:privacy_notice')

    def test_only_hr_admin(self):
        self.client.force_login(make_user("dsgvo-rec", role="Recruiter"))
        self.assertNotEqual(self.client.get(self.url).status_code, 200)

    def test_create_version_and_make_it_valid(self):
        self.client.post(self.url, {'version': '2026-08',
                                    'content': 'Wir verarbeiten Ihre Daten …'})
        notice = PrivacyNoticeVersion.objects.get(version='2026-08')
        self.assertTrue(notice.active)
        self.assertTrue(AuditLog.objects.filter(
            action='PRIVACY_NOTICE_CREATED').exists())

    def test_new_version_supersedes_the_old_one(self):
        """Genau EINE Fassung ist gültig – sonst wäre unklar, welche eine neue
        Bewerbung gesehen hat."""
        self.client.post(self.url, {'version': '1.0', 'content': 'alt'})
        self.client.post(self.url, {'version': '2.0', 'content': 'neu'})
        self.assertFalse(PrivacyNoticeVersion.objects.get(version='1.0').active)
        self.assertTrue(PrivacyNoticeVersion.objects.get(version='2.0').active)

    def test_existing_version_is_never_overwritten(self):
        self.client.post(self.url, {'version': '1.0', 'content': 'Originaltext'})
        resp = self.client.post(self.url, {'version': '1.0',
                                           'content': 'Heimlich geändert'},
                                follow=True)
        self.assertEqual(PrivacyNoticeVersion.objects.filter(version='1.0').count(), 1)
        self.assertEqual(PrivacyNoticeVersion.objects.get(version='1.0').content,
                         'Originaltext')
        self.assertContains(resp, "gibt es schon")

    def test_incomplete_form_creates_nothing(self):
        self.client.post(self.url, {'version': '', 'content': 'ohne Nummer'})
        self.client.post(self.url, {'version': '3.0', 'content': ''})
        self.assertEqual(PrivacyNoticeVersion.objects.count(), 0)

    def test_reactivating_an_older_version_is_possible_and_audited(self):
        self.client.post(self.url, {'version': '1.0', 'content': 'alt'})
        self.client.post(self.url, {'version': '2.0', 'content': 'neu'})
        old = PrivacyNoticeVersion.objects.get(version='1.0')
        self.client.post(self.url, {'action': 'activate', 'version_id': str(old.id)})
        old.refresh_from_db()
        self.assertTrue(old.active)
        self.assertFalse(PrivacyNoticeVersion.objects.get(version='2.0').active)
        self.assertTrue(AuditLog.objects.filter(
            action='PRIVACY_NOTICE_ACTIVATED').exists())

    def test_page_counts_applications_per_version(self):
        """Sichtbar machen, was an einer Fassung hängt – das ist der Grund,
        warum sie nicht änderbar ist."""
        world = make_world()
        job = make_job(world)
        self.client.post(self.url, {'version': '1.0', 'content': 'Text'})
        notice = PrivacyNoticeVersion.objects.get(version='1.0')
        make_application(job, privacyNoticeVersion=notice)
        make_application(job, privacyNoticeVersion=notice)
        resp = self.client.get(self.url)
        self.assertContains(resp, "Bisherige Fassungen")
        self.assertContains(resp, "1.0")

    def test_governance_links_to_the_page_instead_of_django_admin(self):
        resp = self.client.get(reverse('ats:governance'))
        self.assertContains(resp, reverse('ats:privacy_notice'))
        self.assertNotContains(resp, "Django-Administration")

    def test_sidebar_offers_the_page(self):
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertContains(resp, reverse('ats:privacy_notice'))
