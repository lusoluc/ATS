"""Paket S: Inklusion/SBV — § 164 SGB IX.

Deckt ab: freiwillige Angabe wird gespeichert (verschluesselt at-rest),
Default ist keine Angabe, SBV wird unterrichtet (Mail + Audit ohne
Gesundheitsdaten), Steckbrief-Chip, Governance-Aggregate mit
Anonymitaets-Schwelle — und der Waechter: die Angabe ist NIE
Scoring-Eingabe.
"""
from django.contrib.auth.models import Group
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from ..models import Application, AuditLog
from .factories import make_application, make_job, make_world
from .utils import make_user


class DisclosureSubmissionTestCase(TestCase):
    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Pflegefachkraft")

    def _apply(self, *, disclose, email="sbv-test@x.de"):
        cv = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test",
                                content_type="application/pdf")
        data = {"first_name": "Erika", "last_name": "Muster", "email": email,
                "cover_letter": "Ich bewerbe mich.",
                "consent_privacy": "on", "cv_file": cv}
        if disclose:
            data["disability_disclosure"] = "on"
        return self.client.post(
            reverse('ats:bewerben', args=[self.job.id]), data)

    def test_disclosure_stored_and_encrypted_at_rest(self):
        self._apply(disclose=True)
        app = Application.objects.get()
        self.assertEqual(app.severeDisability, 'JA')   # entschluesselt lesbar
        # at-rest verschluesselt: der Rohwert in der DB ist NICHT der Klartext
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("SELECT severeDisability FROM ats_application")
            raw = cur.fetchone()[0]
        self.assertNotEqual(raw, 'JA')
        self.assertTrue(raw)   # aber auch nicht leer

    def test_default_is_no_statement(self):
        self._apply(disclose=False)
        app = Application.objects.get()
        self.assertEqual(app.severeDisability, '')

    def test_sbv_notified_with_mail_and_audit(self):
        sbv, _ = Group.objects.get_or_create(name='SBV')
        member = make_user("sbv-frau", role="Recruiter")
        member.email = "sbv@haus.example"
        member.save(update_fields=['email'])
        member.groups.add(sbv)
        mail.outbox = []
        self._apply(disclose=True)
        sbv_mails = [m for m in mail.outbox if "SBV" in m.subject]
        self.assertEqual(len(sbv_mails), 1)
        self.assertEqual(sbv_mails[0].to, ["sbv@haus.example"])
        # Audit traegt das Ereignis, aber KEINE Gesundheitsdaten
        audit = AuditLog.objects.filter(action='SBV_NOTIFIED').first()
        self.assertIsNotNone(audit)
        self.assertNotIn('JA', audit.metadataJson)

    def test_no_disclosure_no_notification(self):
        Group.objects.get_or_create(name='SBV')
        mail.outbox = []
        self._apply(disclose=False)
        self.assertFalse(AuditLog.objects.filter(action='SBV_NOTIFIED').exists())


class SteckbriefChipTestCase(TestCase):
    def test_chip_only_when_disclosed(self):
        from ..profile_summary import build_facts, facts_to_bullets
        world = make_world()
        job = make_job(world)
        with_d = make_application(job, severeDisability='JA')
        without = make_application(job)
        self.assertTrue(any("§ 164" in b for b in
                            facts_to_bullets(build_facts(with_d))))
        self.assertFalse(any("§ 164" in b for b in
                             facts_to_bullets(build_facts(without))))


class ScoringGuardTestCase(TestCase):
    """Waechter: die freiwillige Angabe ist NIE Bewertungs-Eingabe."""

    def test_features_identical_with_and_without_disclosure(self):
        from ..scoring import _features_for_app
        world = make_world()
        job = make_job(world, screeningQuestionsJson=[{
            "id": "q1", "type": "YES_NO", "question": "Examen?",
            "isMandatory": True, "expectedAnswer": "YES"}])
        a = make_application(job, screeningAnswersJson={"Examen?": "YES"},
                             coverLetterTxt="Text", severeDisability='JA')
        b = make_application(job, screeningAnswersJson={"Examen?": "YES"},
                             coverLetterTxt="Text")
        self.assertEqual(_features_for_app(a), _features_for_app(b))

    def test_scoring_source_never_references_field(self):
        import os
        base = os.path.dirname(os.path.dirname(__file__))
        for mod in ("scoring.py", "scoring_eval.py", "insights.py",
                    "profile_summary.py"):
            src = open(os.path.join(base, mod), encoding="utf-8").read()
            if mod == "profile_summary.py":
                continue   # Anzeige-Chip ist erlaubt (keine Bewertung)
            self.assertNotIn("severeDisability", src,
                             f"{mod} darf die freiwillige Angabe nicht nutzen")


class PortalDisclosureTestCase(TestCase):
    """P1: Widerruf/Abgabe der freiwilligen Angabe im Kandidatenportal
    (Art. 7 Abs. 3 DSGVO: Widerruf so einfach wie Erteilung)."""

    def setUp(self):
        from datetime import timedelta

        from django.utils import timezone

        from ..models import ApplicantToken
        self.world = make_world()
        self.job = make_job(self.world, title="Pflegefachkraft")
        self.app = make_application(self.job, severeDisability='JA',
                                    status='IN_REVIEW')
        self.tok = ApplicantToken.objects.create(
            token="sbv-portal-token", applicant=self.app.applicant,
            expiresAt=timezone.now() + timedelta(days=30))
        self.url = reverse('ats:candidate_portal', args=[self.tok.token])

    def test_portal_shows_revoke_when_disclosed(self):
        r = self.client.get(self.url)
        self.assertContains(r, "Angabe zurücknehmen")

    def test_revoke_clears_field_and_audits_without_health_data(self):
        self.client.post(self.url, data={'form': 'disability',
                                         'action': 'revoke'})
        self.app.refresh_from_db()
        self.assertEqual(self.app.severeDisability, '')
        audit = AuditLog.objects.filter(
            action='SBV_DISCLOSURE_REVOKED').first()
        self.assertIsNotNone(audit)
        self.assertNotIn('JA', audit.metadataJson)

    def test_grant_sets_field_and_notifies_sbv(self):
        # erst widerrufen, dann nachtraeglich wieder abgeben
        self.app.severeDisability = ''
        self.app.save(update_fields=['severeDisability'])
        sbv, _ = Group.objects.get_or_create(name='SBV')
        member = make_user("sbv-p1", role="Recruiter")
        member.email = "sbv-p1@haus.example"
        member.save(update_fields=['email'])
        member.groups.add(sbv)
        mail.outbox = []
        self.client.post(self.url, data={'form': 'disability',
                                         'action': 'grant'})
        self.app.refresh_from_db()
        self.assertEqual(self.app.severeDisability, 'JA')
        self.assertTrue(any("SBV" in m.subject for m in mail.outbox))
        self.assertTrue(AuditLog.objects.filter(
            action='SBV_NOTIFIED').exists())

    def test_grant_skips_closed_applications(self):
        closed = make_application(self.job, status='REJECTED')
        # gleicher Bewerber wie self.app? Nein - eigener. Token gehoert zu
        # self.app.applicant; closed haengt an anderem Bewerber und darf
        # unberuehrt bleiben (BOLA des Portals: nur eigene Bewerbungen).
        self.client.post(self.url, data={'form': 'disability',
                                         'action': 'grant'})
        closed.refresh_from_db()
        self.assertEqual(closed.severeDisability, '')

    def test_own_closed_application_not_granted(self):
        own_closed = Application.objects.create(
            applicant=self.app.applicant, jobPosting=self.job,
            status='REJECTED')
        self.app.severeDisability = ''
        self.app.save(update_fields=['severeDisability'])
        self.client.post(self.url, data={'form': 'disability',
                                         'action': 'grant'})
        own_closed.refresh_from_db()
        self.app.refresh_from_db()
        self.assertEqual(own_closed.severeDisability, '')   # zu bleibt zu
        self.assertEqual(self.app.severeDisability, 'JA')   # aktiv bekommt sie


class GovernanceInclusionTestCase(TestCase):
    def setUp(self):
        self.rec = make_user("gi-rec", role="Recruiter")
        self.client.force_login(self.rec)

    def test_block_renders_with_anonymity_threshold(self):
        world = make_world()
        job = make_job(world)
        make_application(job, severeDisability='JA')   # nur 1 -> keine Quote
        r = self.client.get(reverse('ats:governance'))
        self.assertContains(r, "Inklusion (§ 164 SGB IX)")
        self.assertContains(r, "erst ab 5 Fällen")

    def test_rates_visible_above_threshold(self):
        world = make_world()
        job = make_job(world)
        for _ in range(5):
            make_application(job, severeDisability='JA', status='INVITED')
        for _ in range(5):
            make_application(job, status='REJECTED')
        r = self.client.get(reverse('ats:governance'))
        self.assertContains(r, "Einladungsquote mit Angabe vs. ohne")
        self.assertContains(r, "100 % vs. 0 %")
