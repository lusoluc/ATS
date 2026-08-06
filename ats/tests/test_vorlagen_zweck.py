"""Vorlagen werden über ihren Zweck gefunden, nicht über den Namen.

Vorher: `EmailTemplate.objects.filter(name__icontains='absage')`. Wer seine
Vorlage „Ablehnung" nannte oder „Absage" in „Rückmeldung nach Sichtung"
umbenannte, bekam keine Fehlermeldung — die Absage fiel still auf einen fest
einprogrammierten Text zurück, den niemand im Haus je freigegeben hatte und
den Bewerbende trotzdem lasen.
"""
from django.test import TestCase
from django.urls import reverse

from ..models import EmailTemplate
from ..templates_registry import guess_purpose, missing_purposes, template_for
from .utils import make_user


class TemplateByPurposeTestCase(TestCase):
    def test_renaming_a_template_does_not_lose_it(self):
        tpl = EmailTemplate.objects.create(
            name="Rückmeldung nach Sichtung", purpose="REJECTION",
            subject="Ihre Bewerbung", htmlContent="<p>Text</p>")
        self.assertEqual(template_for("REJECTION"), tpl)

    def test_a_similarly_named_template_is_not_used_by_accident(self):
        """Früher hätte `icontains='absage'` auch „Absageregeln intern"
        getroffen - eine Vorlage, die nie an Bewerbende gedacht war."""
        EmailTemplate.objects.create(
            name="Absageregeln intern", subject="Intern",
            htmlContent="<p>Nur fürs Team</p>")
        self.assertIsNone(template_for("REJECTION"))

    def test_missing_purpose_is_none_not_a_wrong_guess(self):
        self.assertIsNone(template_for("INVITATION"))
        self.assertIsNone(template_for(""))

    def test_empty_template_does_not_count(self):
        """Eine Vorlage ohne Betreff waere schlimmer als keine."""
        EmailTemplate.objects.create(name="Leer", purpose="REJECTION",
                                     subject="", htmlContent="")
        self.assertIsNone(template_for("REJECTION"))

    def test_missing_purposes_are_listed(self):
        EmailTemplate.objects.create(name="Absagetext", purpose="REJECTION",
                                     subject="X", htmlContent="<p>x</p>")
        offen = missing_purposes()
        self.assertNotIn("Absage", offen)
        self.assertIn("Eingangsbestätigung", offen)
        self.assertIn("Einladung zum Gespräch", offen)


class LegacyNameMappingTestCase(TestCase):
    """Geraten wird nur noch einmal: in der Migration."""

    def test_old_names_map_to_purposes(self):
        self.assertEqual(guess_purpose("Absage"), "REJECTION")
        self.assertEqual(guess_purpose("Ablehnung nach Gespräch"), "REJECTION")
        self.assertEqual(guess_purpose("Einladung zum Interview"), "INVITATION")
        self.assertEqual(guess_purpose("Eingangsbestätigung"), "CONFIRMATION")

    def test_unknown_name_stays_unassigned(self):
        """Eine falsch zugeordnete Vorlage waere schlimmer als eine Luecke -
        sie ginge unbemerkt an Bewerbende."""
        self.assertEqual(guess_purpose("Newsletter Q3"), "")


class TemplatesPageTestCase(TestCase):
    def setUp(self):
        self.client.force_login(make_user("vorlagen-admin", role="HR-Admin"))

    def test_page_names_the_gap_and_its_consequence(self):
        resp = self.client.get(reverse('ats:templates_page'))
        self.assertContains(resp, "keine hinterlegt")
        self.assertContains(resp, "Standardtext")

    def test_saving_assigns_the_purpose(self):
        self.client.post(reverse('ats:save_email_template'), {
            'name': 'Unsere Absage', 'purpose': 'REJECTION',
            'subject': 'Ihre Bewerbung', 'html_content': '<p>Text</p>'})
        tpl = EmailTemplate.objects.get(name='Unsere Absage')
        self.assertEqual(tpl.purpose, 'REJECTION')

    def test_only_one_template_per_purpose(self):
        """Zwei Vorlagen fuer denselben Zweck hiesse wieder raten, welche gilt."""
        self.client.post(reverse('ats:save_email_template'), {
            'name': 'Absage alt', 'purpose': 'REJECTION',
            'subject': 'A', 'html_content': '<p>a</p>'})
        self.client.post(reverse('ats:save_email_template'), {
            'name': 'Absage neu', 'purpose': 'REJECTION',
            'subject': 'B', 'html_content': '<p>b</p>'})
        self.assertEqual(
            EmailTemplate.objects.filter(purpose='REJECTION').count(), 1)
        self.assertEqual(template_for('REJECTION').name, 'Absage neu')

    def test_unknown_purpose_is_treated_as_free_template(self):
        self.client.post(reverse('ats:save_email_template'), {
            'name': 'Kreativ', 'purpose': 'ERFUNDEN',
            'subject': 'X', 'html_content': '<p>x</p>'})
        self.assertEqual(EmailTemplate.objects.get(name='Kreativ').purpose, '')

    def test_hub_reports_missing_purposes_not_a_count(self):
        """Zehn freie Bausteine und keine Absage-Vorlage waeren sonst ein
        gruener Haken."""
        EmailTemplate.objects.create(name="Irgendein Baustein", subject="X",
                                     htmlContent="<p>x</p>")
        resp = self.client.get(reverse('ats:settings_hub'))
        self.assertContains(resp, "ohne Vorlage")
        self.assertContains(resp, "Standardtext")


class RenamedTemplateStillUsedTestCase(TestCase):
    """Die Probe aufs Exempel: Umbenennen darf die Absage nicht kippen."""

    def test_rejection_uses_the_purpose_even_after_renaming(self):
        from django.core import mail

        from ..models import Applicant, ApplicantToken, Application
        from .factories import make_job, make_world
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        applicant = Applicant.objects.create(firstName="Deniz", lastName="K",
                                             email="deniz@example.invalid")
        app = Application.objects.create(applicant=applicant, jobPosting=job,
                                         status="IN_REVIEW")
        ApplicantToken.objects.filter(applicant=applicant).delete()
        # Name ohne jeden Hinweis auf „Absage" — früher hätte die Automatik
        # sie nicht gefunden und einen Ersatztext verschickt.
        EmailTemplate.objects.create(
            name="Rückmeldung nach Sichtung", purpose="REJECTION",
            subject="Ihre Bewerbung als {stelle}", htmlContent="x",
            textContent="Guten Tag {name}, vielen Dank für Ihr Interesse.")

        self.client.force_login(make_user("absage-admin", role="HR-Admin"))
        self.client.post(reverse('ats:update_status', args=[app.id]),
                         {'status': 'REJECTED'})
        self.assertTrue(mail.outbox, "Es wurde nichts verschickt")
        self.assertIn("Ihre Bewerbung als Pflegefachkraft", mail.outbox[0].subject)
        self.assertIn("Guten Tag Deniz", mail.outbox[0].body)
