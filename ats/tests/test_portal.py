"""SecurATS-Tests: portal (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .utils import make_user


class CandidatePortalTestCase(TestCase):
    """B4 – passwortloses Magic-Link-Statusportal."""

    def setUp(self):
        from datetime import timedelta

        from django.utils import timezone

        from ..models import (
            Applicant,
            ApplicantToken,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        self.client = Client()
        org = Organization.objects.create(name="Org")
        loc = Location.objects.create(name="Berlin")
        fac = Facility.objects.create(name="Fac", organization=org)
        fam = JobFamily.objects.create(name="Pflege")
        wf = WorkflowState.objects.create(name="Draft")
        job = JobPosting.objects.create(title="Pflegekraft", organization=org,
                                        facility=fac, location=loc, jobFamily=fam,
                                        workflowState=wf)
        self.applicant = Applicant.objects.create(firstName="Max", lastName="M",
                                                  email="max@ex.org")
        self.app = Application.objects.create(applicant=self.applicant, jobPosting=job,
                                              status="IN_REVIEW")
        self.tok = ApplicantToken.objects.create(
            token="valid-token-123", applicant=self.applicant,
            expiresAt=timezone.now() + timedelta(days=30))
        self.expired = ApplicantToken.objects.create(
            token="expired-token", applicant=self.applicant,
            expiresAt=timezone.now() - timedelta(days=1))

    def test_valid_token_shows_status(self):
        resp = self.client.get(reverse('ats:candidate_portal', args=["valid-token-123"]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Pflegekraft")
        self.assertContains(resp, "In Prüfung")

    def test_invalid_token_404(self):
        resp = self.client.get(reverse('ats:candidate_portal', args=["nope"]))
        self.assertEqual(resp.status_code, 404)

    def test_expired_token(self):
        resp = self.client.get(reverse('ats:candidate_portal', args=["expired-token"]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "abgelaufen")

    def test_candidate_can_withdraw(self):
        from ..models import Application
        resp = self.client.post(reverse('ats:candidate_portal', args=["valid-token-123"]),
                                data={"withdraw_id": str(self.app.id)})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Application.objects.get(id=self.app.id).status, "WITHDRAWN")

class CandidateFlowWP1TestCase(TestCase):
    """WP1: Portal-Timeline + Leichte-Sprache-Umschaltung."""

    def _job(self, easy=None):
        import uuid as _u

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="Berlin")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="W-" + str(_u.uuid4())[:6])
        return JobPosting.objects.create(
            title="Pflegekraft", description="Standardtext.", descriptionEasy=easy,
            organization=org, facility=fac, location=loc, jobFamily=fam, workflowState=wf)

    def test_portal_shows_timeline(self):
        from datetime import timedelta

        from django.utils import timezone

        from ..models import Applicant, ApplicantToken, Application
        job = self._job()
        ap = Applicant.objects.create(firstName="Max", lastName="M", email="m@ex.org")
        Application.objects.create(applicant=ap, jobPosting=job, status="IN_REVIEW")
        ApplicantToken.objects.create(token="tok-tl", applicant=ap,
                                      expiresAt=timezone.now() + timedelta(days=10))
        resp = self.client.get(reverse('ats:candidate_portal', args=["tok-tl"]))
        self.assertEqual(resp.status_code, 200)
        # Die Status-Pipeline (role="img") ist die eine Fortschritts-Anzeige;
        # die fruehere doppelte Timeline darunter wurde als tote Struktur
        # entfernt (CSS war schon in P4 geloescht).
        self.assertContains(resp, 'role="img"')
        self.assertContains(resp, "Bewerbungsfortschritt: In Prüfung")
        for step in ["Eingegangen", "In Sichtung", "Gespräch", "Entscheidung"]:
            self.assertContains(resp, step)
        self.assertNotContains(resp, "tl-step")

    def test_iphone_heic_photo_is_accepted(self):
        # "Ein Handy-Foto genuegt" muss auch fuer iPhone-Standardformat
        # gelten: accept-Attribut UND Server-Whitelist erlauben .heic.
        from django.core.files.uploadedfile import SimpleUploadedFile

        from ..models import Application
        job = self._job()
        cv = SimpleUploadedFile("lebenslauf.heic", b"ftypheic-testbytes",
                                content_type="image/heic")
        resp = self.client.post(reverse('ats:bewerben', args=[job.id]), {
            "first_name": "Ida", "last_name": "Phone", "email": "heic@x.de",
            "cover_letter": "Hallo.", "consent_privacy": "on", "cv_file": cv})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Application.objects.filter(
            applicant__emailHash__isnull=False).exists())
        app = Application.objects.get()
        self.assertTrue(app.cvStorageId)

    def test_job_detail_easy_language_toggle(self):
        job = self._job(easy="Wir suchen Sie. Die Arbeit ist gut.")
        resp = self.client.get(reverse('ats:job_detail', args=[job.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Leichte Sprache")
        self.assertContains(resp, "descEasy")

    def test_job_detail_without_easy_has_no_toggle(self):
        job = self._job(easy=None)
        resp = self.client.get(reverse('ats:job_detail', args=[job.id]))
        self.assertEqual(resp.status_code, 200)
        # descBtnEasy ist die Kennung des Umschalters seit dem Drei-Fassungen-
        # Umbau (normal/leicht/englisch). Der alte Marker "easyToggle" existiert
        # nicht mehr - ihn zu pruefen hiesse, immer zu bestehen.
        self.assertNotContains(resp, "descBtnEasy")

class PortalMessagesTestCase(TestCase):
    """UC-LK-11/RI-06: Portal zeigt den Nachrichten-Verlauf und erlaubt Rückfragen."""

    def _world(self):
        import uuid as _u

        from ..models import (
            Applicant,
            ApplicantToken,
            Application,
            ContactPerson,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Message,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        cp = ContactPerson.objects.create(firstName="Petra", lastName="Wolf",
                                          email="p.wolf@klinik.example")
        self.job = JobPosting.objects.create(title="Pflegefachkraft", organization=org,
                                             facility=fac, location=loc, jobFamily=fam,
                                             workflowState=wf, contactPerson=cp)
        ap = Applicant.objects.create(firstName="Rima", lastName="H", email="rima@x.de")
        self.app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                              status="IN_REVIEW")
        ApplicantToken.objects.create(applicant=ap, token="msg-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=30))
        Message.objects.create(application=self.app, direction="OUTBOUND",
                               content="Wir laden Sie herzlich zum Gespräch ein.")

    def test_portal_shows_outbound_messages(self):
        self._world()
        r = self.client.get(reverse('ats:candidate_portal', args=["msg-token"]))
        self.assertContains(r, "herzlich zum Gespräch")       # bisher unsichtbar!
        self.assertContains(r, "Recruiting-Team")

    def test_reply_creates_inbound_and_mails_contact_person(self):
        from django.core import mail

        from ..models import AuditLog, Message
        self._world()
        r = self.client.post(reverse('ats:candidate_portal', args=["msg-token"]),
                             data={"reply_app_id": str(self.app.id),
                                   "content": "Kann ich meine Tochter zum Infotag mitbringen?"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(any("Tochter".lower() in (n.content or '').lower()
                            for n in Message.objects.filter(direction="INBOUND")))
        self.assertTrue(AuditLog.objects.filter(action="CANDIDATE_MESSAGE_SENT").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("p.wolf@klinik.example", mail.outbox[0].to)
        self.assertIn("Rückfrage", mail.outbox[0].subject)
        # Verlauf zeigt beide Richtungen
        page = self.client.get(reverse('ats:candidate_portal', args=["msg-token"]))
        self.assertContains(page, "Tochter")

    def test_empty_reply_ignored(self):
        from ..models import Message
        self._world()
        self.client.post(reverse('ats:candidate_portal', args=["msg-token"]),
                         data={"reply_app_id": str(self.app.id), "content": "   "})
        self.assertEqual(Message.objects.filter(direction="INBOUND").count(), 0)

class RejectionNoticeTestCase(TestCase):
    """Wuerdevolle Absage: echte Mail + Portal-Nachricht + Talent-Pool-Bruecke."""

    def _world(self):
        import uuid as _u

        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="Elbtal Pflege")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="Pflegefachkraft", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=wf)
        ap = Applicant.objects.create(firstName="Deniz", lastName="K",
                                      email="deniz@x.de")
        self.app = Application.objects.create(applicant=ap, jobPosting=job,
                                              status="IN_REVIEW")
        self.rec = make_user("rejrec", role="Recruiter")
        self.client.force_login(self.rec)

    def _reject(self):
        return self.client.post(
            reverse('ats:update_status', args=[self.app.id]),
            data={"status": "REJECTED"})

    def test_rejection_sends_mail_with_pool_bridge_once(self):
        from django.core import mail

        from ..models import ApplicantToken, AuditLog, Message
        self._world()
        r = self._reject()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn("Deniz", body)
        self.assertIn("Talent-Pool", body)                     # Bruecke
        self.assertIn("/bewerber/", body)                      # Portal-Link
        self.assertIn("keine Aussage über Ihre Qualifikation", body)
        self.assertTrue(Message.objects.filter(application=self.app,
                                               direction="OUTBOUND").exists())
        self.assertTrue(AuditLog.objects.filter(action="REJECTION_NOTICE_SENT").exists())
        self.assertTrue(ApplicantToken.objects.filter(
            applicant=self.app.applicant).exists())            # Link funktioniert
        # Erneutes Setzen (z.B. Drag zurueck und wieder REJECTED): keine 2. Mail
        self.client.post(reverse('ats:update_status', args=[self.app.id]),
                         data={"status": "IN_REVIEW"})
        self._reject()
        self.assertEqual(len(mail.outbox), 1)

    def test_rejection_uses_custom_template(self):
        from django.core import mail

        from ..models import EmailTemplate
        self._world()
        # Der ZWECK steuert, nicht der Name: Frueher wurde die Vorlage ueber
        # `name__icontains='absage'` gesucht - wer sie umbenannte, bekam still
        # einen fest einprogrammierten Ersatztext.
        EmailTemplate.objects.create(name="Absage Standard",
                                     purpose="REJECTION",
                                     subject="Zu Ihrer Bewerbung: {stelle}",
                                     htmlContent="x",
                                     textContent="Liebe/r {name}, danke für Ihr "
                                                 "Interesse an {firma}.")
        self._reject()
        self.assertIn("Zu Ihrer Bewerbung: Pflegefachkraft", mail.outbox[0].subject)
        self.assertIn("Liebe/r Deniz", mail.outbox[0].body)
        self.assertIn("Elbtal Pflege", mail.outbox[0].body)
        self.assertIn("Talent-Pool", mail.outbox[0].body)      # Bruecke auch hier

class PortalBrandingTestCase(TestCase):
    """P4: Das Portal folgt den Tokens – Traeger-CI schaltet es hell."""

    def test_portal_renders_brand_light_and_logo(self):
        from ..models import (
            Applicant,
            ApplicantToken,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(
            name="Elbtal Pflege gGmbH", brandEnabled=True, brandMode="LIGHT",
            brandPrimary="#0065bd",
            brandLogoUrl="https://cdn.elbtal.example/logo.svg")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="PB-Fam")
        wf = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="Stelle", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=wf)
        ap = Applicant.objects.create(firstName="Nora", lastName="B",
                                      email="nora@x.de")
        Application.objects.create(applicant=ap, jobPosting=job,
                                   status="IN_REVIEW")
        ApplicantToken.objects.create(applicant=ap, token="pb-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=5))
        page = self.client.get(reverse('ats:candidate_portal', args=["pb-token"]))
        self.assertContains(page, "brand-css")                 # Override aktiv
        self.assertContains(page, "#0065bd")                   # Traeger-Primaer
        self.assertContains(page, "--bg-color: #f5f7fa")       # hell geschaltet
        self.assertContains(page, "brand-head")                # Logo-Kopfzeile
        self.assertContains(page, "logo.svg")
        # Ohne Branding: Dark-Default bleibt (Tokens im Portal selbst)
        org.brandEnabled = False
        org.save()
        page = self.client.get(reverse('ats:candidate_portal', args=["pb-token"]))
        self.assertNotContains(page, "brand-css")
        self.assertContains(page, "--bg-color:#0b1220")        # SecurATS-Default

class ApplicationConfirmationMailTestCase(TestCase):
    """Eingangsbestätigung nach Bewerbung.

    Befund, den diese Tests festhalten: Die Erfolgsseite versprach
    „Sie erhalten in Kürze eine Bestätigung per E-Mail" – es wurde KEINE
    verschickt. Schlimmer: Der Magic-Link zum Kandidatenportal stand nur auf
    dieser einen Seite. Wer den Tab schloss, kam nie wieder ins Portal
    (Status, Termine, Rückfragen) – das Feature war praktisch unbenutzbar.
    """

    def setUp(self):
        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="CM-Fam")
        ws = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(
            title="Pflegefachkraft", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=ws)

    def _apply(self, email="bewerber@x.de"):
        cv = SimpleUploadedFile("lebenslauf.pdf", b"%PDF-1.4 test",
                                content_type="application/pdf")
        return self.client.post(
            reverse('ats:bewerben', args=[self.job.id]),
            {"first_name": "Erika", "last_name": "Muster", "email": email,
             "phone": "0170-1", "cover_letter": "Ich bewerbe mich.",
             "consent_privacy": "on",   # DSGVO-Pflichteinwilligung
             "cv_file": cv})            # Lebenslauf ist Pflicht

    def test_confirmation_mail_is_sent(self):
        from django.core import mail
        mail.outbox = []
        self._apply()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["bewerber@x.de"])
        self.assertIn("Pflegefachkraft", mail.outbox[0].subject)

    def test_confirmation_mail_contains_portal_link(self):
        """Der Kern des Fixes: Ohne den Link in der Mail wäre das
        Kandidatenportal nach dem Schließen des Tabs unerreichbar."""
        from django.core import mail

        from ..models import ApplicantToken
        mail.outbox = []
        self._apply()
        token = ApplicantToken.objects.get().token
        self.assertIn(token, mail.outbox[0].body)
        self.assertIn("/bewerber/", mail.outbox[0].body)

    def test_portal_link_from_mail_actually_works(self):
        """Ende-zu-Ende: der Link aus der Mail führt ins Portal."""
        from django.core import mail

        from ..models import ApplicantToken
        mail.outbox = []
        self._apply()
        token = ApplicantToken.objects.get().token
        r = self.client.get(reverse('ats:candidate_portal', args=[token]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Pflegefachkraft")

    def test_confirmation_is_audited(self):
        from ..models import AuditLog
        self._apply()
        self.assertTrue(AuditLog.objects.filter(
            action="APPLICATION_CONFIRMATION_SENT").exists())

    def test_email_template_is_used_when_present(self):
        from django.core import mail

        from ..models import EmailTemplate
        EmailTemplate.objects.create(
            name="Eingangsbestätigung", subject="Danke, {name}!",
            textContent="Hallo {name}, Stelle: {stelle}. Portal: {portal}",
            htmlContent="")
        mail.outbox = []
        self._apply()
        self.assertEqual(mail.outbox[0].subject, "Danke, Erika!")
        self.assertIn("Stelle: Pflegefachkraft", mail.outbox[0].body)
        self.assertIn("/bewerber/", mail.outbox[0].body)   # Platzhalter ersetzt

    def test_mail_failure_never_breaks_the_application(self):
        """Wichtigster Fall: Der Mailversand darf die Bewerbung NIE
        scheitern lassen – die Bewerbung ist bereits gespeichert."""
        from unittest.mock import patch

        from ..models import Application
        with patch("django.core.mail.send_mail",
                   side_effect=OSError("SMTP down")):
            r = self._apply(email="robust@x.de")
        self.assertEqual(r.status_code, 200)               # Erfolgsseite
        self.assertEqual(Application.objects.count(), 1)   # Bewerbung da!


class EasyLanguageBridgeTestCase(TestCase):
    """B5: descriptionEasy ist im Stellen-Editor pfleg- und loeschbar.

    Vorher existierte das Feld nur im Modell - der Umschalter am
    Stellendetail blieb auf Produktivdaten fuer immer leer.
    """

    def _base_post(self, job=None, **extra):
        from .factories import make_world
        world = getattr(self, '_world', None) or make_world()
        self._world = world
        data = {
            "title": "Pflegefachkraft (m/w/d)", "description": "Standardtext.",
            "tasks": "Pflegen", "requirements": "Examen",
            "facility": str(world.facility.id),
            "location": str(world.location.id),
            "job_family": str(world.job_family.id),
            "workflow_state": str(world.published.id),
            "pay_band": str(world.band.id),
        }
        if job is not None:
            data["job_id"] = str(job.id)
        data.update(extra)
        return data

    def test_create_and_update_easy_description(self):
        from django.urls import reverse

        from ..models import JobPosting
        from .utils import make_user
        self.client.force_login(make_user("easy-adm", role="HR-Admin"))
        self.client.post(reverse('ats:create_job'), self._base_post(
            description_easy="Wir suchen Sie. Die Arbeit ist gut."))
        job = JobPosting.objects.get(title="Pflegefachkraft (m/w/d)")
        self.assertEqual(job.descriptionEasy,
                         "Wir suchen Sie. Die Arbeit ist gut.")
        # Update mit geaendertem Text
        self.client.post(reverse('ats:create_job'), self._base_post(
            job=job, description_easy="Neuer einfacher Text."))
        job.refresh_from_db()
        self.assertEqual(job.descriptionEasy, "Neuer einfacher Text.")
        # Leeren = Umschalter verschwindet (None statt Leerstring)
        self.client.post(reverse('ats:create_job'), self._base_post(
            job=job, description_easy=""))
        job.refresh_from_db()
        self.assertIsNone(job.descriptionEasy)

    def test_update_without_field_keeps_existing(self):
        from django.urls import reverse

        from ..models import JobPosting
        from .utils import make_user
        self.client.force_login(make_user("easy-adm2", role="HR-Admin"))
        self.client.post(reverse('ats:create_job'), self._base_post(
            description_easy="Bleibt stehen."))
        job = JobPosting.objects.get(title="Pflegefachkraft (m/w/d)")
        # POST ohne description_easy (z. B. Alt-Client) loescht NICHT
        self.client.post(reverse('ats:create_job'), self._base_post(job=job))
        job.refresh_from_db()
        self.assertEqual(job.descriptionEasy, "Bleibt stehen.")
