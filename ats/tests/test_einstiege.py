"""U3: Funktionen, die es gab, zu denen aber kein Weg führte.

Jeder Test hier steht für einen Fund aus dem Durchgang „unerreichbare
Funktionen": die Seite/der Endpunkt war fertig und geschützt, nur klickte
sie niemand an, weil kein Link darauf zeigte. Getestet wird deshalb
bewusst die *Verlinkung*, nicht nur die Erreichbarkeit der Route.
"""
from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import ApplicationDocument
from .factories import make_application, make_job, make_world
from .utils import make_user


class ForgottenEntryPointsTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)
        self.admin = make_user("einstieg-admin", role="HR-Admin")

    def test_job_row_links_talent_pool_matches(self):
        """Der Pool-Abgleich je Stelle war nur per getippter URL erreichbar."""
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertContains(
            resp, reverse('ats:job_pool_matches', args=[self.job.id]))

    def test_audit_page_offers_csv_export(self):
        """BR/DSB brauchen den Export – der Knopf fehlte."""
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:audit_log'))
        self.assertContains(resp, reverse('ats:audit_export'))

    def test_job_list_links_job_alert(self):
        """Der Job-Alert hing nur an der Einrichtungsseite."""
        resp = self.client.get(reverse('ats:job_list'))
        self.assertContains(resp, reverse('ats:job_alert'))

    def test_best_performer_deletion_reachable_from_ki_tab(self):
        """Art. 17 DSGVO: Löschen war nur als JSON-Route vorhanden."""
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertContains(resp, 'bp-profiles-list')
        self.assertContains(resp, 'loadBestPerformerProfiles')

    def test_candidate_modal_has_document_container(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertContains(resp, 'modal-documents')


class PricingLinkTestCase(TestCase):
    """Die Preisseite wirft ohne DEMO_MODE 404 – der Link zeigte trotzdem
    auf sie. Auf einer Kundeninstanz also ein garantierter Fehlklick."""

    @override_settings(DEMO_MODE=False)
    def test_no_pricing_link_on_customer_instance(self):
        resp = self.client.get(reverse('ats:home'))
        self.assertNotContains(resp, '/preise/')

    @override_settings(DEMO_MODE=True)
    def test_pricing_link_on_demo_instance(self):
        resp = self.client.get(reverse('ats:home'))
        self.assertContains(resp, '/preise/')


class SummaryDocumentsTestCase(TestCase):
    """Nachgereichte Zeugnisse wurden gespeichert, aber nirgends angezeigt."""

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world)
        self.app = make_application(self.job)
        self.admin = make_user("doc-admin", role="HR-Admin")
        self.client.force_login(self.admin)

    def test_summary_lists_documents_with_download_url(self):
        doc = ApplicationDocument.objects.create(
            application=self.app, name="Approbation.pdf",
            file="application_docs/approbation.pdf", docType="APPROBATION")
        resp = self.client.get(
            reverse('ats:application_summary', args=[self.app.id]))
        self.assertEqual(resp.status_code, 200)
        docs = resp.json().get('documents')
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['name'], "Approbation.pdf")
        self.assertEqual(docs[0]['url'],
                         reverse('ats:download_document', args=[doc.id]))

    def test_summary_without_documents_is_empty_list(self):
        resp = self.client.get(
            reverse('ats:application_summary', args=[self.app.id]))
        self.assertEqual(resp.json().get('documents'), [])
