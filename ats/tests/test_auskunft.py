"""U4: Betroffenenrechte und Einwilligungs-Nachweise.

Zwei Funde aus dem Durchgang „unerreichbare Funktionen":

* Die Auskunft nach Art. 15/20 gab es nur als Management-Befehl – erreichbar
  ausschließlich mit Server-Zugang, während Art. 12 Abs. 3 eine Monatsfrist
  setzt. Getestet wird deshalb, dass beide Türen (Portal, HR) offen sind und
  dass der Inhalt vollständig ist.
* `privacyNoticeVersion` existierte als Feld, wurde aber von keiner Bewerbung
  befüllt: Art. 7 Abs. 1 ohne Nachweis.
"""
import datetime
import json

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..dsgvo import active_privacy_notice, build_applicant_export, privacy_notice_status
from ..models import (
    ApplicantToken,
    ApplicationDocument,
    AuditLog,
    Message,
    PrivacyNoticeVersion,
    TalentPoolSubscription,
)
from .factories import make_application, make_job, make_world
from .utils import make_user


class DataExportContentTestCase(TestCase):
    """Was gespeichert ist, muss auch in der Auskunft stehen."""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)
        self.app = make_application(self.job, status="REJECTED")
        self.applicant = self.app.applicant

    def test_address_is_no_longer_invisible(self):
        """Die Anschrift wurde beim Import gespeichert und nie wieder gezeigt."""
        self.applicant.address = "Musterweg 5, 20095 Hamburg"
        self.applicant.save()
        data = build_applicant_export(self.applicant)
        self.assertEqual(data['betroffene_person']['anschrift'],
                         "Musterweg 5, 20095 Hamburg")

    def test_rejection_reason_and_messages_are_included(self):
        self.app.withdrawReason = "Pflichtkriterium Führerschein nicht erfüllt."
        self.app.save()
        Message.objects.create(application=self.app, direction="OUTBOUND",
                               content="Ihre Absage")
        data = build_applicant_export(self.applicant)
        entry = data['bewerbungen'][0]
        self.assertIn("Führerschein", entry['absage_oder_ruecknahme'])
        self.assertEqual(len(entry['nachrichten']), 1)
        self.assertEqual(entry['nachrichten'][0]['richtung'], "an Sie")

    def test_documents_listed_with_upload_date(self):
        ApplicationDocument.objects.create(
            application=self.app, name="Zeugnis.pdf",
            file="application_docs/z.pdf", docType="CERTIFICATE")
        data = build_applicant_export(self.applicant)
        docs = data['bewerbungen'][0]['nachweise']
        self.assertEqual(docs[0]['name'], "Zeugnis.pdf")
        self.assertIn('hochgeladen_am', docs[0])

    def test_talent_pool_consent_id_is_retrievable(self):
        """Die consentId war vergeben, aber nirgends abrufbar."""
        TalentPoolSubscription.objects.create(
            email=self.applicant.email, consentId="portal-abc123",
            criteria='{"locations": ["HH"]}',
            expiresAt=timezone.now() + datetime.timedelta(days=365))
        data = build_applicant_export(self.applicant)
        self.assertEqual(data['talentpool_einwilligung']['einwilligung_id'],
                         "portal-abc123")
        self.assertTrue(data['talentpool_einwilligung']['aktiv'])

    def test_no_pool_subscription_is_explicit_none(self):
        data = build_applicant_export(self.applicant)
        self.assertIsNone(data['talentpool_einwilligung'])

    def test_ai_rating_comes_with_its_meaning(self):
        """Art. 15 Abs. 1 h: die Note allein wäre keine Information."""
        self.app.aiScore = "B"
        self.app.aiRationale = "Erfahrung passt, Schichtbereitschaft offen."
        self.app.save()
        entry = build_applicant_export(self.applicant)['bewerbungen'][0]
        self.assertEqual(entry['ki_score'], "B")
        self.assertIn("keine Entscheidung", entry['ki_hinweis'])

    def test_omissions_are_named(self):
        data = build_applicant_export(self.applicant)
        self.assertIn("Zugangs-Token", data['nicht_enthalten'])
        self.assertIn("Interne Vermerke", data['nicht_enthalten'])

    def test_disclosure_flag_survives_undecryptable_value(self):
        """Roher Ciphertext darf nie als „ja" durchgehen."""
        self.app.severeDisability = "gAAAAABnXwEr_kein_klartext"
        self.app.save()
        entry = build_applicant_export(self.applicant)['bewerbungen'][0]
        self.assertEqual(entry['angabe_schwerbehinderung'], "keine Angabe")


class PortalExportTestCase(TestCase):
    """Selbstbedienung im Bewerberportal statt Bitte per Mail."""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)
        self.app = make_application(self.job)
        self.token = ApplicantToken.objects.create(
            applicant=self.app.applicant, token="tok-auskunft-1",
            expiresAt=timezone.now() + datetime.timedelta(days=7))

    def test_portal_offers_the_download(self):
        resp = self.client.get(
            reverse('ats:candidate_portal', args=[self.token.token]))
        self.assertContains(
            resp, reverse('ats:candidate_data_export', args=[self.token.token]))

    def test_download_returns_own_data_only(self):
        other = make_application(self.job, first_name="Fremd")
        resp = self.client.get(
            reverse('ats:candidate_data_export', args=[self.token.token]))
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(body['bewerbungen']), 1)
        self.assertEqual(body['bewerbungen'][0]['id'], str(self.app.id))
        self.assertNotIn(str(other.id), resp.content.decode('utf-8'))

    def test_expired_token_gets_nothing(self):
        self.token.expiresAt = timezone.now() - datetime.timedelta(days=1)
        self.token.save()
        resp = self.client.get(
            reverse('ats:candidate_data_export', args=[self.token.token]))
        self.assertEqual(resp.status_code, 404)

    def test_unknown_token_gets_nothing(self):
        resp = self.client.get(
            reverse('ats:candidate_data_export', args=["gibt-es-nicht"]))
        self.assertEqual(resp.status_code, 404)

    def test_export_is_audited(self):
        self.client.get(
            reverse('ats:candidate_data_export', args=[self.token.token]))
        self.assertTrue(AuditLog.objects.filter(action='DATA_EXPORT').exists())


class HrExportTestCase(TestCase):
    """Kommt die Anfrage per Brief, braucht HR einen Knopf – keinen Server."""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)
        self.app = make_application(self.job)

    def test_hr_admin_can_export(self):
        self.client.force_login(make_user("dsar-admin", role="HR-Admin"))
        resp = self.client.get(
            reverse('ats:applicant_data_export', args=[self.app.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('attachment', resp['Content-Disposition'])

    def test_recruiter_cannot_export(self):
        """Die Auskunft bündelt mehr, als der Bewerbungs-Zugriff hergibt."""
        self.client.force_login(make_user("dsar-rec", role="Recruiter"))
        resp = self.client.get(
            reverse('ats:applicant_data_export', args=[self.app.id]))
        self.assertNotEqual(resp.status_code, 200)

    def test_button_only_for_hr_admin(self):
        # Auf den Knopf-Text prüfen, nicht auf die id: die id steht auch im
        # immer ausgelieferten Skriptblock.
        label = 'Auskunft (Art. 15 DSGVO)'
        self.client.force_login(make_user("dsar-admin2", role="HR-Admin"))
        self.assertContains(self.client.get(reverse('ats:dashboard')), label)
        self.client.force_login(make_user("dsar-rec2", role="Recruiter"))
        self.assertNotContains(self.client.get(reverse('ats:dashboard')), label)


class PrivacyNoticeEvidenceTestCase(TestCase):
    """Art. 7 Abs. 1: Nachweis, worin eingewilligt wurde."""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)

    def test_no_version_is_reported_openly(self):
        status = privacy_notice_status()
        self.assertTrue(status['missing'])
        self.assertIsNone(status['version'])

    def test_nothing_is_invented_when_no_version_exists(self):
        """Keine Auto-Anlage: ein selbst erzeugter Nachweis wäre keiner."""
        self.assertIsNone(active_privacy_notice())
        self.assertEqual(PrivacyNoticeVersion.objects.count(), 0)

    def test_newest_active_version_wins(self):
        PrivacyNoticeVersion.objects.create(version="1.0", content="alt",
                                            active=False)
        new = PrivacyNoticeVersion.objects.create(version="2.0", content="neu",
                                                  active=True)
        self.assertEqual(active_privacy_notice().id, new.id)

    def test_application_records_the_version_it_was_shown(self):
        PrivacyNoticeVersion.objects.create(version="2.0", content="neu",
                                            active=True)
        from django.core.files.uploadedfile import SimpleUploadedFile
        resp = self.client.post(
            reverse('ats:bewerben', args=[self.job.id]),
            {'first_name': 'Nina', 'last_name': 'Berg',
             'email': 'nina.berg@example.org', 'consent_privacy': 'on',
             'cv_file': SimpleUploadedFile("cv.pdf", b"%PDF-1.4")})
        self.assertIn(resp.status_code, (200, 302))
        app = self.job.applications.first()
        self.assertIsNotNone(app)
        self.assertIsNotNone(app.privacyNoticeVersion)
        self.assertEqual(app.privacyNoticeVersion.version, "2.0")

    def test_governance_names_the_gap(self):
        self.client.force_login(make_user("gov-dsb", role="HR-Admin"))
        resp = self.client.get(reverse('ats:governance'))
        self.assertContains(resp, "keine Fassung gepflegt")

    def test_governance_shows_the_version_when_present(self):
        PrivacyNoticeVersion.objects.create(version="3.1", content="x",
                                            active=True)
        self.client.force_login(make_user("gov-dsb2", role="HR-Admin"))
        resp = self.client.get(reverse('ats:governance'))
        self.assertContains(resp, "Fassung 3.1")
