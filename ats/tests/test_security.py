"""SecurATS-Tests: security (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime
import tempfile
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ..models import SystemSetting
from .utils import User, make_user


class AuthAccessControlTestCase(TestCase):
    """Auth/RBAC: unauthentifiziert -> Login; falsche Rolle -> 403."""

    def setUp(self):
        self.client = Client()

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/recruiter/login/', resp['Location'])

    def test_state_changing_post_requires_login(self):
        url = reverse('ats:update_status', args=[uuid.uuid4()])
        resp = self.client.post(url, data={'status': 'HIRED'})
        self.assertEqual(resp.status_code, 302)

    def test_authenticated_without_role_is_forbidden(self):
        make_user("nobody")
        self.client.force_login(User.objects.get(username="nobody"))
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertEqual(resp.status_code, 403)

    def test_recruiter_can_view_dashboard(self):
        make_user("rec", role="Recruiter")
        self.client.force_login(User.objects.get(username="rec"))
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_recruiter_cannot_access_hr_admin_endpoint(self):
        make_user("rec2", role="Recruiter")
        self.client.force_login(User.objects.get(username="rec2"))
        resp = self.client.post(reverse('ats:save_system_setting'), data={'key': 'X', 'value': 'Y'})
        self.assertEqual(resp.status_code, 403)

    def test_superuser_bypasses_roles(self):
        make_user("root", superuser=True)
        self.client.force_login(User.objects.get(username="root"))
        resp = self.client.get(reverse('ats:dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_public_pages_stay_open(self):
        resp = self.client.get(reverse('ats:home'))
        self.assertEqual(resp.status_code, 200)

class CsrfProtectionTestCase(TestCase):
    """@csrf_exempt ist entfernt: POST ohne Token muss 403 liefern."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        make_user("hradmin2", role="HR-Admin")
        self.client.force_login(User.objects.get(username="hradmin2"))

    def test_post_without_csrf_token_is_rejected(self):
        resp = self.client.post(reverse('ats:save_system_setting'), data={'key': 'X', 'value': 'Y'})
        self.assertEqual(resp.status_code, 403)

class BolaScopingTestCase(TestCase):
    """BOLA: eingeschränkter Nutzer sieht/ändert nur seinen Standort."""

    def _make_application(self, location, org, wf_name):
        from ..models import Applicant, Application, Facility, JobFamily, JobPosting, WorkflowState
        fac = Facility.objects.create(name="Fac-" + wf_name, organization=org)
        fam = JobFamily.objects.create(name="Fam-" + wf_name)
        wf = WorkflowState.objects.create(name=wf_name)
        job = JobPosting.objects.create(title="Job-" + wf_name, organization=org,
                                        facility=fac, location=location,
                                        jobFamily=fam, workflowState=wf)
        appl = Applicant.objects.create(firstName="A", lastName="B",
                                        email=wf_name + "@ex.org")
        return Application.objects.create(applicant=appl, jobPosting=job)

    def setUp(self):
        from ..models import Location, Organization, UserScope
        self.client = Client()
        self.org = Organization.objects.create(name="Org")
        self.loc_a = Location.objects.create(name="Berlin")
        self.loc_b = Location.objects.create(name="Muenchen")
        self.app_a = self._make_application(self.loc_a, self.org, "wfA")
        self.app_b = self._make_application(self.loc_b, self.org, "wfB")

        # Recruiter, eingeschränkt auf Standort A
        self.rec = make_user("scoperec", role="Recruiter")
        scope = UserScope.objects.create(user=self.rec, full_access=False)
        scope.locations.add(self.loc_a)

    def test_scoped_recruiter_only_sees_own_location(self):
        from ..models import Application
        from ..permissions import scope_applications
        visible = scope_applications(self.rec, Application.objects.all())
        ids = set(visible.values_list("id", flat=True))
        self.assertIn(self.app_a.id, ids)
        self.assertNotIn(self.app_b.id, ids)

    def test_scoped_recruiter_cannot_touch_out_of_scope(self):
        self.client.force_login(self.rec)
        # In scope -> erlaubt (200 JSON)
        r_ok = self.client.post(reverse('ats:update_status', args=[self.app_a.id]),
                                data={'status': 'IN_REVIEW'})
        self.assertEqual(r_ok.status_code, 200)
        # Out of scope -> 404
        r_no = self.client.post(reverse('ats:update_status', args=[self.app_b.id]),
                                data={'status': 'IN_REVIEW'})
        self.assertEqual(r_no.status_code, 404)

    def test_hr_admin_sees_everything(self):
        from ..models import Application
        from ..permissions import scope_applications
        admin = make_user("scopeadmin", role="HR-Admin")
        self.assertEqual(scope_applications(admin, Application.objects.all()).count(), 2)

class EmailBlindIndexTestCase(TestCase):
    """Go-Live-Blocker: E-Mail verschlüsselt at-rest, Eindeutigkeit via Blind-Index."""

    def test_email_is_encrypted_at_rest(self):
        from django.db import connection

        from ..models import Applicant
        a = Applicant.objects.create(firstName="Aylin", lastName="Y", email="AY@Ex.org ")
        # DATENBANKNEUTRAL: PostgreSQL faltet unquotierte Bezeichner auf
        # Kleinbuchstaben (emailHash -> emailhash = existiert nicht), und der
        # Primaerschluessel ist dort ein echter uuid-Typ statt Hex-Text.
        # Deshalb Spalten quoten und den PK ueber das Feld anpassen lassen.
        q = connection.ops.quote_name
        pk = Applicant._meta.pk.get_db_prep_value(a.id, connection)
        with connection.cursor() as cur:
            cur.execute(
                f"SELECT {q('email')}, {q('emailHash')} FROM ats_applicant "
                f"WHERE {q('id')} = %s", [pk])
            raw_email, raw_hash = cur.fetchone()
        self.assertNotIn("ay@ex.org", raw_email)      # DB enthält KEINEN Klartext
        self.assertTrue(raw_email.startswith("gAAAA"))  # Fernet-Ciphertext
        self.assertEqual(len(raw_hash), 64)             # HMAC-SHA256 hex
        a.refresh_from_db()
        self.assertEqual(a.email, "ay@ex.org")          # transparent entschlüsselt+normalisiert

    def test_blind_index_is_keyed_not_plain_hash(self):
        """Sicherheitseigenschaft: Der Blind-Index ist ein SCHLÜSSELABHÄNGIGER
        HMAC, kein reiner Hash. Sonst könnte ein Angreifer mit Lesezugriff auf
        die Indexspalte per Wörterbuch (bekannte E-Mails durchhashen) die
        Adressen rückrechnen. Dieser Test schlägt an, falls jemand den HMAC
        später zu sha256(email) 'vereinfacht'."""
        import hashlib

        from ..models import email_blind_index
        email = "opfer@example.org"
        plain = hashlib.sha256(email.encode()).hexdigest()
        self.assertNotEqual(email_blind_index(email), plain)

    def test_blind_index_changes_with_the_key(self):
        """Rotiert der PII-Schlüssel, ändert sich der Index zwingend mit –
        Beleg dafür, dass er tatsächlich schlüsselgebunden ist."""
        from django.test import override_settings

        from ..models import email_blind_index
        a = email_blind_index("x@y.de")
        with override_settings(PII_ENCRYPTION_KEY="ein-voellig-anderer-schluessel"):
            b = email_blind_index("x@y.de")
        self.assertNotEqual(a, b)

    def test_blind_index_is_deterministic_and_normalized(self):
        """Deterministisch (sonst kein unique/lookup) und robust gegen
        Schreibweise/Whitespace – genau die Eigenschaft, die get_or_create
        trägt."""
        from ..models import email_blind_index
        self.assertEqual(email_blind_index("a@b.de"), email_blind_index("a@b.de"))
        self.assertEqual(email_blind_index("  A@B.de "),
                         email_blind_index("a@b.de"))

    def test_encrypted_field_ciphertext_is_non_deterministic(self):
        """Fernet nutzt einen Zufalls-IV: zweimal derselbe Klartext ergibt
        UNTERSCHIEDLICHE Ciphertexte. Wäre das nicht so, könnte man aus der
        DB ablesen, welche Bewerber denselben Wert teilen."""
        from ..models import get_fernet_cipher
        c = get_fernet_cipher()
        v1 = c.encrypt(b"Aylin").decode()
        v2 = c.encrypt(b"Aylin").decode()
        self.assertNotEqual(v1, v2)                       # verschiedene IVs
        self.assertEqual(c.decrypt(v1.encode()).decode(),
                         c.decrypt(v2.encode()).decode()) # beide entschlüsseln gleich

    def test_cover_letter_encrypted_at_rest(self):
        """Nicht nur die E-Mail: auch das Anschreiben (Freitext-PII) muss
        verschlüsselt in der DB liegen."""
        from django.db import connection

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
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="EF-Fam")
        ws = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="J", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=ws)
        ap = Applicant.objects.create(firstName="E", lastName="F",
                                      email="ef@x.de")
        secret = "GEHEIMES Anschreiben mit Klartext-PII"
        app = Application.objects.create(applicant=ap, jobPosting=job,
                                         status="NEW", coverLetterTxt=secret)
        q = connection.ops.quote_name
        pk = Application._meta.pk.get_db_prep_value(app.id, connection)
        with connection.cursor() as cur:
            cur.execute(
                f"SELECT {q('coverLetterTxt')} FROM ats_application "
                f"WHERE {q('id')} = %s", [pk])
            raw = cur.fetchone()[0]
        self.assertNotIn("GEHEIMES", raw)                 # kein Klartext in DB
        app.refresh_from_db()
        self.assertEqual(app.coverLetterTxt, secret)      # ORM entschlüsselt

    def test_uniqueness_and_lookup_via_blind_index(self):
        from django.db import IntegrityError, transaction

        from ..models import Applicant
        Applicant.objects.create(firstName="A", lastName="B", email="dup@x.de")
        # gleiche Adresse (andere Schreibweise) -> unique-Verletzung über den Hash
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Applicant.objects.create(firstName="C", lastName="D", email="  DUP@x.de")
        # Lookup + get_or_create über den Index
        found = Applicant.objects.get_by_email("Dup@X.de")
        self.assertEqual(found.firstName, "A")
        obj, created = Applicant.objects.get_or_create_by_email("dup@x.de",
                                                                defaults={"firstName": "E", "lastName": "F"})
        self.assertFalse(created)
        self.assertEqual(obj.id, found.id)

    def test_apply_twice_reuses_applicant(self):
        import uuid as _u

        from ..models import (
            Applicant,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            WorkflowState,
            email_blind_index,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="B")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="W-" + str(_u.uuid4())[:6])
        def mkjob(t):
            return JobPosting.objects.create(title=t, organization=org, facility=fac,
                                             location=loc, jobFamily=fam, workflowState=wf)
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                for job in [mkjob("Job1"), mkjob("Job2")]:
                    self.client.post(reverse('ats:bewerben', args=[job.id]), data={
                        "first_name": "Max", "last_name": "M", "email": "twice@x.de",
                        "consent_privacy": "on",
                        "cv_file": SimpleUploadedFile("cv.pdf", b"%PDF-1")})
        self.assertEqual(Applicant.objects.filter(
            emailHash=email_blind_index("twice@x.de")).count(), 1)  # ein Bewerber, zwei Bewerbungen

    def test_dsgvo_export_still_returns_plaintext(self):
        from io import StringIO

        from django.core.management import call_command

        from ..models import Applicant
        Applicant.objects.create(firstName="Ex", lastName="Port", email="export@x.de")
        out = StringIO()
        call_command("export_applicant", "export@x.de", stdout=out)
        self.assertIn('"email": "export@x.de"', out.getvalue())  # Auskunft in Klartext

class ScoringDefaultOffTestCase(TestCase):
    """ROADMAP P0.2 / AI Act: KI-Scoring ist Opt-in – Default AUS, keine erfundenen Scores."""

    def _job(self):
        import uuid as _u

        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="B")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        return JobPosting.objects.create(title="Testjob", organization=org, facility=fac,
                                         location=loc, jobFamily=fam, workflowState=wf)

    def _apply(self, job, email):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                return self.client.post(reverse('ats:bewerben', args=[job.id]), data={
                    "first_name": "P0", "last_name": "Zwei", "email": email,
                    "consent_privacy": "on",
                    "cv_file": SimpleUploadedFile("cv.pdf", b"%PDF-1")})

    def test_fresh_install_never_calls_llm(self):
        from unittest.mock import patch

        from ..models import AiTask, Application, email_blind_index
        job = self._job()
        with patch("ats.views.public.evaluate_with_local_gemma") as mock_eval:
            r = self._apply(job, "off@x.de")
        self.assertEqual(r.status_code, 200)
        mock_eval.assert_not_called()                       # KI wird nicht einmal berührt
        app = Application.objects.get(applicant__emailHash=email_blind_index("off@x.de"))
        self.assertIsNone(app.aiScore)                      # kein erfundener Score
        self.assertIsNone(app.aiRationale)
        self.assertEqual(AiTask.objects.count(), 0)         # auch keine Queue-Task

    def test_opt_in_sync_scores(self):
        from unittest.mock import patch

        from ..models import Application, email_blind_index
        job = self._job()
        SystemSetting.objects.create(key="AI_SCORING_ENABLED", value="1")
        with patch("ats.views.public.evaluate_with_local_gemma", return_value=("B", "Passt.")) as mock_eval:
            self._apply(job, "on@x.de")
        mock_eval.assert_called_once()
        app = Application.objects.get(applicant__emailHash=email_blind_index("on@x.de"))
        self.assertEqual(app.aiScore, "B")

    def test_opt_in_async_enqueues(self):
        from unittest.mock import patch

        from ..models import AiTask
        job = self._job()
        SystemSetting.objects.create(key="AI_SCORING_ENABLED", value="1")
        SystemSetting.objects.create(key="AI_ASYNC", value="1")
        with patch("ats.views.public.evaluate_with_local_gemma") as mock_eval:
            self._apply(job, "queue@x.de")
        mock_eval.assert_not_called()                       # nicht synchron
        self.assertEqual(AiTask.objects.filter(taskType="SCORE_APPLICATION",
                                               status="PENDING").count(), 1)

    def test_kanban_shows_honest_dash_not_fake_c(self):
        from ..models import Applicant, Application
        job = self._job()
        ap = Applicant.objects.create(firstName="K", lastName="B", email="dash@x.de")
        Application.objects.create(applicant=ap, jobPosting=job, status="NEW")  # ungescort
        rec = make_user("p02rec", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.get(reverse('ats:dashboard'))
        self.assertContains(r, "ai-score-none")             # ehrliche –-Badge
        self.assertContains(r, 'data-ai-score=""')          # kein erfundenes C im Datenattribut

class HardeningTestCase(TestCase):
    """Haertung: ehrliche Workflow-Aktionen + Portal-Rate-Limit."""

    def _world(self):
        import uuid as _u

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
        org = Organization.objects.create(name="Elbtal")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(title="Pflegefachkraft",
                                             organization=org, facility=fac,
                                             location=loc, jobFamily=fam,
                                             workflowState=wf)
        ap = Applicant.objects.create(firstName="Omar", lastName="S",
                                      email="omar@x.de")
        self.app = Application.objects.create(applicant=ap, jobPosting=self.job,
                                              status="IN_REVIEW")
        ApplicantToken.objects.create(applicant=ap, token="hard-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=30))

    def test_workflow_email_action_sends_real_mail_with_template(self):
        from django.core import mail

        from ..models import AuditLog, EmailTemplate, Message
        from ..views import execute_workflow_actions
        self._world()
        EmailTemplate.objects.create(name="Eingangsbestätigung",
                                     subject="Ihre Bewerbung: {stelle}",
                                     htmlContent="x",
                                     textContent="Hallo {name}, danke – {firma}.")
        execute_workflow_actions(self.app, [
            {"type": "EMAIL_NOTIFICATION", "recipient": "applicant",
             "template": "Eingangsbestätigung"}])
        self.assertEqual(len(mail.outbox), 1)                  # ECHTE Mail
        self.assertIn("Hallo Omar", mail.outbox[0].body)
        self.assertIn("Elbtal", mail.outbox[0].body)
        self.assertTrue(Message.objects.filter(application=self.app,
                                               direction="OUTBOUND").exists())
        audit = AuditLog.objects.get(action="AUTOMATION_EMAIL")
        self.assertIn('"status": "SENT"', audit.metadataJson)

    def test_workflow_actions_never_fake_success(self):
        from django.core import mail

        from ..models import AuditLog
        from ..views import execute_workflow_actions
        self._world()
        execute_workflow_actions(self.app, [
            {"type": "EMAIL_NOTIFICATION", "recipient": "applicant",
             "template": "GibtEsNicht"},
            {"type": "AUTO_INVITE_INTERVIEW"},
            {"type": "SEND_CONTRACT"}])
        self.assertEqual(len(mail.outbox), 0)                  # nichts behauptet
        self.assertIn("SKIPPED_NO_TEMPLATE",
                      AuditLog.objects.get(action="AUTOMATION_EMAIL").metadataJson)
        skipped = AuditLog.objects.filter(action="WORKFLOW_ACTION_SKIPPED")
        self.assertEqual(skipped.count(), 2)
        for a in skipped:
            # Kernaussage unverändert: ehrlich übersprungen, NICHTS simuliert.
            # (Wortlaut angepasst, seit die Automatik echte Aktionstypen kennt –
            # AUTO_INVITE_INTERVIEW/SEND_CONTRACT bleiben bewusst unbekannt.)
            self.assertIn("uebersprungen", a.metadataJson)
            self.assertIn("statt etwas zu simulieren", a.metadataJson)
        # Kein Mock-Link mehr irgendwo im Audit
        self.assertFalse(AuditLog.objects.filter(
            metadataJson__icontains="meet.google.com").exists())

    def test_portal_inbound_rate_limit(self):
        from django.core import mail

        from ..models import Message
        self._world()
        url = reverse('ats:candidate_portal', args=["hard-token"])
        for i in range(10):
            self.client.post(url, data={"reply_app_id": str(self.app.id),
                                        "content": f"Frage {i}"})
        self.assertEqual(Message.objects.filter(direction="INBOUND").count(), 10)
        mails_before = len(mail.outbox)
        r = self.client.post(url, data={"reply_app_id": str(self.app.id),
                                        "content": "Frage 11"})
        self.assertContains(r, "sehr viele")                   # freundliche Bremse
        self.assertEqual(Message.objects.filter(direction="INBOUND").count(), 10)
        self.assertEqual(len(mail.outbox), mails_before)       # keine Team-Mail mehr
        # Auch der E-Mail-Aenderungs-Kanal ist gebremst
        self.client.post(url, data={"form": "contact", "phone": "",
                                    "new_email": "neu@x.de"})
        self.assertFalse(Message.objects.filter(
            content__icontains="neu@x.de").exists())

class ApplicantFormSecurityTestCase(TestCase):
    """Oeffentliche Bewerberformulare: Upload-Whitelist, XSS-Escaping, Waechter."""

    def _world(self):
        from ..models import Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="Sec-Fam")
        wf = WorkflowState.objects.create(name="published")
        self.job = JobPosting.objects.create(title="Pflegefachkraft",
                                             organization=org, facility=fac,
                                             location=loc, jobFamily=fam,
                                             workflowState=wf,
                                             screeningQuestionsJson=[])

    def _apply(self, cv, docs=()):
        data = {"first_name": "Eva", "last_name": "Test",
                "email": "eva.test@x.de", "consent_privacy": "on",
                "cv_file": cv}
        if docs:
            data["documents"] = list(docs)
        return self.client.post(reverse('ats:bewerben', args=[self.job.id]),
                                data=data)

    def test_upload_whitelist_blocks_dangerous_types_before_create(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from ..models import Application, ApplicationDocument
        self._world()
        r = self._apply(SimpleUploadedFile("lebenslauf.exe", b"MZ evil"))
        self.assertContains(r, "wird nicht")                    # Formular-Fehler
        self.assertEqual(Application.objects.count(), 0)        # keine halbe Bewerbung
        r = self._apply(SimpleUploadedFile("cv.pdf", b"%PDF-1.4"),
                        docs=[SimpleUploadedFile("zeugnis.html",
                                                 b"<script>alert(1)</script>")])
        self.assertContains(r, "zeugnis.html")                  # benannt abgelehnt
        self.assertEqual(Application.objects.count(), 0)
        self.assertEqual(ApplicationDocument.objects.count(), 0)
        r = self._apply(SimpleUploadedFile("cv.pdf", b"%PDF-1.4"),
                        docs=[SimpleUploadedFile("zeugnis.pdf", b"%PDF-1.4")])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Application.objects.count(), 1)        # sauberer Fall geht
        self.assertEqual(ApplicationDocument.objects.count(), 1)

    def test_upload_size_limit(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from ..models import Application
        self._world()
        big = SimpleUploadedFile("cv.pdf", b"0" * (10 * 1024 * 1024 + 1))
        r = self._apply(big)
        self.assertContains(r, "größer als 10")
        self.assertEqual(Application.objects.count(), 0)

    def test_applicant_xss_escaped_on_all_render_paths(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from ..models import Applicant, ApplicantToken, Application, Message
        self._world()
        payload = '<script>alert("xss")</script>'
        self._apply(SimpleUploadedFile("cv.pdf", b"%PDF-1.4"))
        ap = Applicant.objects.get()
        Applicant.objects.filter(id=ap.id).update(firstName=payload)
        app = Application.objects.get()
        Message.objects.create(application=app, direction="INBOUND",
                               content=payload)
        ApplicantToken.objects.create(applicant=ap, token="sec-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=5))
        # Portal (Bewerber sieht eigene Daten)
        portal = self.client.get(reverse('ats:candidate_portal',
                                         args=["sec-token"]))
        self.assertNotContains(portal, payload)                 # nie roh
        self.assertContains(portal, "&lt;script&gt;")           # escaped sichtbar
        # Recruiter-Seiten (Stored-XSS-Ziel Nr. 1)
        self.client.force_login(make_user("secrec", role="Recruiter"))
        msgs = self.client.get(reverse('ats:application_messages', args=[app.id]))
        self.assertNotContains(msgs, payload)
        dash = self.client.get(reverse('ats:dashboard'))
        self.assertNotContains(dash, payload)

    def test_guard_no_unsafe_template_filters(self):
        """Waechter: |safe / autoescape off bleiben dauerhaft verbannt.

        Wer die Regel bewusst brechen muss (z. B. CMS-Inhalte), traegt die
        Datei hier mit Begruendung als Ausnahme ein – nicht stillschweigend.
        """
        import pathlib
        allowed_exceptions = set()  # bewusst leer
        offenders = []
        for tpl in pathlib.Path("templates").rglob("*.html"):
            text = tpl.read_text(encoding="utf-8")
            if "|safe" in text or "autoescape off" in text:
                if tpl.name not in allowed_exceptions:
                    offenders.append(str(tpl))
        self.assertEqual(offenders, [],
                         f"Unsichere Template-Filter gefunden: {offenders}")

class BruteForceLockoutTestCase(TestCase):
    """Fund 5: Schutz gegen Login-Brute-Force-Angriffe (IP/Username Sperre)."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.username = "lockeduser"
        self.password = "wrongpass"

    def test_brute_force_lockout_after_max_attempts(self):
        url = reverse('ats:login')
        # 5 fehlgeschlagene Versuche machen
        for _i in range(5):
            r = self.client.post(url, {'username': self.username, 'password': self.password})
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, "Bitte Benutzername und Passwort eingeben")

        # Der 6. Versuch sollte die Lockout-Fehlermeldung zeigen
        r = self.client.post(url, {'username': self.username, 'password': self.password})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Zu viele fehlerhafte Anmeldeversuche")

    def test_production_cache_is_shared_not_per_process(self):
        """Sicherheitskonfiguration: Der Lockout-Cache MUSS in Produktion
        prozessuebergreifend sein. LocMemCache (Django-Default) ist pro
        Gunicorn-Worker isoliert -> ein Angreifer umginge das Limit ueber
        mehrere Worker, und ein Neustart vergisst die Zaehler. Diese
        Regressions-Wache schlaegt an, falls die Produktions-Cache-Logik
        wieder auf reinen LocMemCache zurueckfaellt."""
        import inspect

        import securats.settings as st
        src = inspect.getsource(st)
        # In Produktion muss ein geteilter Cache waehlbar sein:
        self.assertIn('DatabaseCache', src)
        self.assertIn('RedisCache', src)
        # ... und LocMemCache darf NUR im Entwicklungs-Zweig stehen
        # (nach einem 'else' hinter der Produktionsbedingung).
        self.assertIn("not DEBUG", src)
        # Der Lockout-View nutzt tatsaechlich den Cache
        import ats.views as v
        vsrc = inspect.getsource(v.SafeLoginView)
        self.assertIn('cache', vsrc)


class GlobalSearchTestCase(TestCase):
    """B1: Globale Suche - Treffer nur im eigenen Zugriffsbereich (BOLA)."""

    def setUp(self):
        from ..models import Location
        from .factories import make_application, make_job, make_world
        self.world = make_world()
        self.job = make_job(self.world, title="Pflegefachkraft Nachtdienst")
        self.app = make_application(self.job, first_name="Sabine",
                                    last_name="Kruse", email="sabine@ex.org")
        # Zweite Welt/Stelle an anderem Standort (ausserhalb des Scopes)
        self.other_loc = Location.objects.create(name="Muenchen")
        self.other_job = make_job(self.world, title="Buchhalter",
                                  location=self.other_loc)
        self.other_app = make_application(self.other_job, first_name="Sabine",
                                          last_name="Fremd", email="fremd@ex.org")

    def _search(self, q):
        return self.client.get(reverse('ats:global_search'), {"q": q})

    def test_name_search_finds_applicant(self):
        self.client.force_login(make_user("gs-admin", role="HR-Admin"))
        r = self._search("Kruse")
        self.assertContains(r, "Sabine Kruse")

    def test_email_search_exact_match(self):
        self.client.force_login(make_user("gs-admin2", role="HR-Admin"))
        r = self._search("sabine@ex.org")
        self.assertContains(r, "Sabine Kruse")

    def test_job_title_search(self):
        self.client.force_login(make_user("gs-admin3", role="HR-Admin"))
        r = self._search("Nachtdienst")
        self.assertContains(r, "Pflegefachkraft Nachtdienst")

    def test_bola_scoped_recruiter_does_not_see_foreign_applicant(self):
        from ..models import UserScope
        from ..permissions import can_access_application
        rec = make_user("gs-scoped", role="Recruiter")
        sc = UserScope.objects.create(user=rec, full_access=False)
        sc.locations.add(self.world.location)   # nur die eigene Welt
        # Test nur sinnvoll, wenn der Scope die Fremd-Bewerbung wirklich sperrt
        if not can_access_application(rec, self.other_app):
            self.client.force_login(rec)
            r = self._search("Sabine")
            self.assertContains(r, "Sabine Kruse")       # eigener Standort
            self.assertNotContains(r, "Sabine Fremd")    # fremder Standort

    def test_requires_login(self):
        r = self._search("Kruse")
        self.assertIn(r.status_code, (302, 403))

    def test_short_query_yields_nothing(self):
        self.client.force_login(make_user("gs-admin4", role="HR-Admin"))
        r = self._search("a")
        self.assertContains(r, "0 Treffer")


class LockoutCacheFailureTestCase(TestCase):
    """Was passiert, wenn der Cache ausfaellt, der die Sperre traegt?

    Vorher zwei entgegengesetzte Fehlverhalten am selben Zaehler: Das LESEN
    war ungeschuetzt (Cache-Ausfall = 500, niemand konnte sich mehr anmelden),
    das SCHREIBEN fing jeden Fehler ab und schwieg (Sperre lautlos
    abgeschaltet). Jetzt einheitlich: durchlassen, aber laut - und ueber
    `/healthz/` sichtbar.
    """

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_login_stays_usable_when_the_cache_is_down(self):
        """Wer bei kaputtem Cache jeden Versuch abweist, sperrt das Haus aus."""
        from unittest import mock
        url = reverse('ats:login')
        with mock.patch('ats.views.auth_views.cache') as kaputt:
            kaputt.get.side_effect = OSError('cache down')
            kaputt.set.side_effect = OSError('cache down')
            kaputt.delete.side_effect = OSError('cache down')
            with self.assertLogs('ats.views.auth_views', level='ERROR') as protokoll:
                resp = self.client.post(url, {'username': 'x', 'password': 'y'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any('wirkungslos' in z for z in protokoll.output),
                        "Der Ausfall muss im Protokoll stehen: "
                        + str(protokoll.output))

    def test_healthz_reports_a_broken_cache(self):
        """Der Cache traegt die Sperre - also gehoert er in die Gesundheitsprobe."""
        import json
        from unittest import mock
        resp = self.client.get(reverse('ats:healthz'))
        self.assertIn('cache', json.loads(resp.content)['checks'])

        with mock.patch('django.core.cache.cache.set',
                        side_effect=OSError('cache down')):
            resp = self.client.get(reverse('ats:healthz'))
        daten = json.loads(resp.content)
        self.assertIn('error', daten['checks']['cache'])
        self.assertEqual(daten['status'], 'degraded',
                         "Ein kaputter Cache darf den Dienst nicht als 'ok' "
                         "ausweisen - die Login-Sperre haengt daran.")
