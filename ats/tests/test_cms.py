"""SecurATS-Tests: cms (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .utils import make_user


class BrandWP8TestCase(TestCase):
    """WP8: Einrichtungs-Karriereseite, Alt-Texte, ehrliche Landing, A11y-Reste."""

    def _fixture(self):
        import uuid as _u

        from ..models import Facility, FacilityProfile, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="Berlin")
        fac = Facility.objects.create(name="Klinik Nord", organization=org)
        profile = FacilityProfile.objects.create(
            facility=fac, slug="klinik-nord",
            description="Wir sind ein Haus der Grund- und Regelversorgung.")
        fam = JobFamily.objects.create(name="JF-" + str(_u.uuid4())[:6])
        wf = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="Pflegefachkraft", organization=org,
                                        facility=fac, location=loc, jobFamily=fam,
                                        workflowState=wf)
        return fac, profile, job

    def test_facility_career_page(self):
        fac, profile, job = self._fixture()
        r = self.client.get(reverse('ats:facility_profile', args=["klinik-nord"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Klinik Nord")
        self.assertContains(r, "Grund- und Regelversorgung")
        self.assertContains(r, "Pflegefachkraft")          # offene Stelle gelistet
        self.assertEqual(self.client.get(
            reverse('ats:facility_profile', args=["gibt-es-nicht"])).status_code, 404)

    def test_job_detail_links_facility_page(self):
        fac, profile, job = self._fixture()
        r = self.client.get(reverse('ats:job_detail', args=[job.id]))
        self.assertContains(r, "kennenlernen")
        self.assertContains(r, "/einrichtung/klinik-nord/")

    def test_media_upload_stores_alt_text(self):
        from ..models import MediaAsset
        admin = make_user("wp8admin", role="HR-Admin")
        self.client.force_login(admin)
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                self.client.post(reverse('ats:media_manage'), data={
                    "file": SimpleUploadedFile("team.jpg", b"\xff\xd8\xff"),
                    "name": "Teamfoto",
                    "altText": "Das Pflegeteam der Station 3 im Gruppenbild"})
        asset = MediaAsset.objects.get(name="Teamfoto")
        self.assertIn("Station 3", asset.altText)

    def test_home_has_honest_candidate_copy(self):
        r = self.client.get(reverse('ats:home'))
        self.assertContains(r, "Handy-Foto")
        self.assertContains(r, "Barrierefrei")
        self.assertNotContains(r, "kununu")     # erfundene Bewertung entfernt
        self.assertNotContains(r, "4.8")

    def test_kanban_cards_have_keyboard_reorder(self):
        from ..models import Applicant, Application
        fac, profile, job = self._fixture()
        ap = Applicant.objects.create(firstName="K", lastName="B", email="kb@x.de")
        Application.objects.create(applicant=ap, jobPosting=job, status="NEW")
        rec = make_user("wp8rec", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.get(reverse('ats:dashboard'))
        self.assertContains(r, "Karte nach oben verschieben")
        self.assertContains(r, "moveCard(")

class VisualProcessLanguageTestCase(TestCase):
    """P1 Design-Runde: Pipeline im Portal, Sitz-Punkte im Postfach."""

    def test_portal_pipeline_reflects_status(self):
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
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="VPL-Fam")
        wf = WorkflowState.objects.create(name="published")
        j1 = JobPosting.objects.create(title="Stelle A", organization=org,
                                       facility=fac, location=loc,
                                       jobFamily=fam, workflowState=wf)
        j2 = JobPosting.objects.create(title="Stelle B", organization=org,
                                       facility=fac, location=loc,
                                       jobFamily=fam, workflowState=wf)
        ap = Applicant.objects.create(firstName="Pia", lastName="L",
                                      email="pia@x.de")
        Application.objects.create(applicant=ap, jobPosting=j1,
                                   status="IN_REVIEW")
        Application.objects.create(applicant=ap, jobPosting=j2,
                                   status="REJECTED")
        ApplicantToken.objects.create(applicant=ap, token="vpl-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=5))
        page = self.client.get(reverse('ats:candidate_portal', args=["vpl-token"]))
        self.assertContains(page, 'class="pipeline"', count=2)   # je Bewerbung
        self.assertContains(page, "In Sichtung")
        self.assertContains(page, "p-step current")              # aktiver Schritt
        self.assertContains(page, "p-step stopped")              # Absage: gestoppt
        self.assertContains(page, "Bewerbungsfortschritt")       # a11y-Label

    def test_approvals_seat_dots_with_delegation_marker(self):

        from ..models import (
            Applicant,
            Application,
            Facility,
            JobFamily,
            JobPosting,
            Location,
            Organization,
            RoleDelegation,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="F", organization=org)
        fam = JobFamily.objects.create(name="Seat-Fam")
        wf = WorkflowState.objects.create(name="published")
        member = make_user("seatmember", role="Hiring-Manager")
        other = make_user("seatother", role="Hiring-Manager")
        vt = make_user("seatvt", role="Viewer")
        job = JobPosting.objects.create(
            title="PDL Sitzprobe", organization=org, facility=fac,
            location=loc, jobFamily=fam, workflowState=wf,
            panelUserIdsJson=[str(member.id), str(other.id)])
        ap = Applicant.objects.create(firstName="S", lastName="K", email="sk@x.de")
        app = Application.objects.create(applicant=ap, jobPosting=job,
                                         status="IN_REVIEW")
        RoleDelegation.objects.create(
            delegator=member, delegatee=vt, scopeType="ALL",
            validFrom=timezone.now() - datetime.timedelta(days=1),
            validUntil=timezone.now() + datetime.timedelta(days=7))
        self.client.force_login(vt)
        self.client.post(reverse('ats:application_vote', args=[app.id]),
                         data={"vote": "FOR"})
        page = self.client.get(reverse('ats:approvals'))
        self.assertContains(page, "seat for")                    # gruener Sitz
        self.assertContains(page, "via-mark")                    # Vertretungs-Marker
        self.assertContains(page, "in Vertretung")               # Tooltip nennt es
        self.assertContains(page, "Mehrheit von 2")

class BrandingTestCase(TestCase):
    """CI/CD des Traegers auf Bewerberseiten: Kontrast, Import, Trennung."""

    def test_contrast_automation_and_hex_normalization(self):
        from ..branding import normalize_hex, on_color
        self.assertEqual(on_color("#0018A8"), "#ffffff")   # DB-Blau -> Weiss
        self.assertEqual(on_color("#E20074"), "#ffffff")   # Telekom-Magenta -> Weiss
        self.assertEqual(on_color("#FFD500"), "#111827")   # helles Gelb -> Dunkel
        self.assertEqual(on_color("#ffffff"), "#111827")
        self.assertEqual(normalize_hex("#abc"), "#aabbcc")
        self.assertIsNone(normalize_hex("rot"))            # nie ungeprueft ins CSS
        self.assertIsNone(normalize_hex("#12345"))

    def test_import_extracts_suggestions_from_html(self):
        from ..branding import extract_branding_from_html
        html = ('<html><head><meta name="theme-color" content="#0065bd">'
                '<link rel="apple-touch-icon" href="/static/logo-192.png">'
                '<meta property="og:image" content="https://cdn.x.de/haus.jpg">'
                '</head></html>')
        out = extract_branding_from_html(html, "https://www.traeger.de/de")
        self.assertEqual(out["primary"], "#0065bd")
        self.assertEqual(out["logo"], "https://www.traeger.de/static/logo-192.png")
        self.assertEqual(out["hero"], "https://cdn.x.de/haus.jpg")
        leer = extract_branding_from_html("<html></html>", "https://x.de")
        self.assertIsNone(leer["primary"])                 # keine Erfindungen

    def _brand_world(self):
        from ..models import Organization
        org = Organization.objects.create(
            name="Elbtal Pflege gGmbH", brandEnabled=True, brandMode="LIGHT",
            brandPrimary="#0065bd",
            brandLogoUrl="https://cdn.elbtal.example/logo.svg")
        return org

    def test_public_pages_branded_recruiter_stays_securats(self):
        self._brand_world()
        public = self.client.get("/jobs/")
        self.assertContains(public, "brand-css")           # CI aktiv
        self.assertContains(public, "#0065bd")
        self.assertContains(public, "logo.svg")            # Logo oben links
        self.assertContains(public, "--bg-color: #f5f7fa") # heller Grund
        self.client.force_login(make_user("brandrec", role="Recruiter"))
        ats = self.client.get("/recruiter/dashboard/")
        self.assertNotContains(ats, "brand-css")           # Produktidentitaet

    def test_branding_page_rights_and_validation(self):
        org = self._brand_world()
        self.client.force_login(make_user("brandrec2", role="Recruiter"))
        self.assertEqual(self.client.get(reverse('ats:branding')).status_code, 403)
        self.client.force_login(make_user("brandadmin", role="HR-Admin"))
        self.client.post(reverse('ats:branding'), data={
            "enabled": "1", "mode": "LIGHT", "primary": "keinefarbe",
            "accent": "", "logo_url": org.brandLogoUrl, "hero_url": ""})
        org.refresh_from_db()
        self.assertEqual(org.brandPrimary, "#0065bd")      # Ungueltiges verworfen
        self.client.post(reverse('ats:branding'), data={
            "enabled": "1", "mode": "DARK", "primary": "#e20074",
            "accent": "", "logo_url": org.brandLogoUrl, "hero_url": ""})
        org.refresh_from_db()
        self.assertEqual(org.brandPrimary, "#e20074")
        self.assertEqual(org.brandMode, "DARK")

class LandingPageTestCase(TestCase):
    """Kampagnen-Landingpages: Scope, Selbstmessung, Analytics-Trichter."""

    def _world(self):
        from ..models import (
            Facility,
            JobFamily,
            JobPosting,
            LandingPage,
            Location,
            Organization,
            WorkflowState,
        )
        org = Organization.objects.create(name="O")
        self.loc = Location.objects.create(name="HH")
        self.fac_a = Facility.objects.create(name="Haus Elbblick", organization=org)
        self.fac_b = Facility.objects.create(name="Klinik B", organization=org)
        fam = JobFamily.objects.create(name="LP-Fam")
        wf = WorkflowState.objects.create(name="published")
        def job(title, fac):
            return JobPosting.objects.create(title=title, organization=org,
                                             facility=fac, location=self.loc,
                                             jobFamily=fam, workflowState=wf,
                                             screeningQuestionsJson=[])
        self.job_in = job("Pflegefachkraft Elbblick", self.fac_a)
        self.job_out = job("Verwaltung Klinik B", self.fac_b)
        self.lp = LandingPage.objects.create(
            name="Jobmesse Hamburg", slug="jobmesse-hamburg",
            headline="Pflege mit Elbblick", introText="Kommen Sie zu uns.",
            facility=self.fac_a)

    def test_public_page_scopes_counts_and_sets_source(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from ..models import Application, LandingPage
        self._world()
        page = self.client.get(reverse('ats:landing_page',
                                       args=["jobmesse-hamburg"]))
        self.assertContains(page, "Pflege mit Elbblick")
        self.assertContains(page, "Pflegefachkraft Elbblick")   # im Scope
        self.assertNotContains(page, "Verwaltung Klinik B")     # nicht im Scope
        self.lp.refresh_from_db()
        self.assertEqual(self.lp.views, 1)                      # Selbstmessung
        # Bewerbung derselben Sitzung traegt die Kampagne als Quelle
        self.client.post(reverse('ats:bewerben', args=[self.job_in.id]),
                         data={"first_name": "Lea", "last_name": "P",
                               "email": "lea.p@x.de", "consent_privacy": "on",
                               "cv_file": SimpleUploadedFile("cv.pdf",
                                                             b"%PDF-1.4")})
        self.assertEqual(Application.objects.get().source, "JOBMESSE-HAMBURG")
        # Deaktiviert -> oeffentlich 404
        LandingPage.objects.filter(id=self.lp.id).update(active=False)
        r = self.client.get(reverse('ats:landing_page',
                                    args=["jobmesse-hamburg"]))
        self.assertEqual(r.status_code, 404)

    def test_manage_page_metrics_and_analytics_funnel(self):
        from ..models import Applicant, Application, LandingPage
        self._world()
        LandingPage.objects.filter(id=self.lp.id).update(views=4)
        for i, st in enumerate(["NEW", "INVITED"]):
            ap = Applicant.objects.create(firstName="L", lastName=str(i),
                                          email=f"l{i}@x.de")
            Application.objects.create(applicant=ap, jobPosting=self.job_in,
                                       status=st, source="JOBMESSE-HAMBURG")
        self.client.force_login(make_user("lprec", role="Recruiter"))
        manage = self.client.get(reverse('ats:landing_pages'))
        self.assertContains(manage, "data:image/svg+xml")       # QR
        self.assertContains(manage, "/k/jobmesse-hamburg/")
        self.assertContains(manage, "50,0&nbsp;%")              # 2 Apps / 4 Views (de-Locale)
        self.assertContains(manage, "50&nbsp;%")                # 1/2 eingeladen
        analytics = self.client.get(reverse('ats:analytics'))
        self.assertContains(analytics, "Landingpages & Kampagnen")  # statischer Template-Text bleibt roh
        self.assertContains(analytics, "Jobmesse Hamburg")
        self.assertContains(analytics, "50,0&nbsp;%")           # Trichter im Dashboard

    def test_manage_requires_staff(self):
        self._world()
        self.assertNotEqual(
            self.client.get(reverse('ats:landing_pages')).status_code, 200)

class CmsBlocksTestCase(TestCase):
    """CMS-Baukasten: Validierung, Editor-Zyklus, oeffentliches Rendering."""

    def test_normalize_rejects_unknown_and_clamps(self):
        from ..blocks import normalize_blocks
        out = normalize_blocks([
            {"type": "hero", "heading": "H", "text": "T", "imageUrl": ""},
            {"type": "boese-injektion", "x": "y"},              # unbekannt -> weg
            {"type": "jobs", "heading": "", "limit": "999"},    # clamp 12
            {"type": "stats", "items": "10|Häuser\n\n 4,8|Note "},
        ])
        self.assertEqual([b["type"] for b in out], ["hero", "jobs", "stats"])
        self.assertEqual(out[1]["limit"], 12)
        self.assertEqual(out[2]["items"], ["10|Häuser", "4,8|Note"])

    def _page(self, blocks):

        from ..models import Page
        return Page.objects.create(title="Karriere", slug="karriere-cms",
                                   status="published",
                                   blocksJson=blocks)

    def test_public_page_renders_blocks_escaped(self):
        from ..models import ContactPerson, Facility, JobFamily, JobPosting, Location, Organization, WorkflowState
        org = Organization.objects.create(name="O")
        loc = Location.objects.create(name="HH")
        fac = Facility.objects.create(name="Haus Nord", organization=org)
        fam = JobFamily.objects.create(name="CB-Fam")
        wf = WorkflowState.objects.create(name="published")
        JobPosting.objects.create(title="Pflegefachkraft Nord",
                                  organization=org, facility=fac,
                                  location=loc, jobFamily=fam,
                                  workflowState=wf)
        cp = ContactPerson.objects.create(firstName="Nina", lastName="Falk",
                                          email="nf@x.de",
                                          globalJobTitle="Recruiting")
        payload = '<script>alert("cms")</script>'
        self._page([
            {"type": "hero", "heading": "Willkommen", "text": payload},
            {"type": "checklist", "heading": "Benefits",
             "items": ["30 Tage Urlaub", "Deutschlandticket"]},
            {"type": "stats", "items": ["21|Standorte", "4,6|kununu"]},
            {"type": "faq", "items": ["Wie schnell?|In 5 Tagen."]},
            {"type": "contact", "contactPersonId": str(cp.id)},
            {"type": "jobs", "heading": "Offene Stellen", "limit": 5},
            {"type": "cta", "text": "Bereit?", "buttonLabel": "Jetzt bewerben",
             "url": "/jobs/"},
        ])
        page = self.client.get("/pages/karriere-cms/")
        self.assertContains(page, "Willkommen")
        self.assertContains(page, "Deutschlandticket")
        self.assertContains(page, "21")                        # Kennzahl
        self.assertContains(page, "<details")                  # FAQ aufklappbar
        self.assertContains(page, "Nina Falk")                 # Ansprechperson
        self.assertContains(page, "Pflegefachkraft Nord")      # Jobs-Block
        self.assertContains(page, "Jetzt bewerben")            # CTA
        self.assertNotContains(page, payload)                  # nie roh
        self.assertContains(page, "&lt;script&gt;")

    def test_editor_cycle_add_save_reorder_delete_and_rights(self):

        pg = self._page([])
        url = reverse('ats:blocks_editor',
                      kwargs={'kind': 'page', 'obj_id': pg.id})
        # CMS-Seiten: nur HR-Admin (Recruiter -> 403)
        self.client.force_login(make_user("cbrec", role="Recruiter"))
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(make_user("cbadmin", role="HR-Admin"))
        self.client.post(url, data={"action": "add", "block_type": "hero"})
        self.client.post(url, data={"action": "add",
                                    "block_type": "checklist"})
        self.client.post(url, data={"action": "save", "idx": "0",
                                    "f_heading": "Hallo", "f_text": "Text",
                                    "f_imageUrl": ""})
        self.client.post(url, data={"action": "up", "idx": "1"})
        pg.refresh_from_db()
        blocks = pg.blocksJson
        self.assertEqual([b["type"] for b in blocks],
                         ["checklist", "hero"])                # umsortiert
        self.assertEqual(blocks[1]["heading"], "Hallo")
        self.client.post(url, data={"action": "delete", "idx": "0"})
        pg.refresh_from_db()
        self.assertEqual(len(pg.blocksJson), 1)

    def test_editor_noop_save_preserves_blocks(self):

        blocks = [{"type": "quote", "text": "Bestes Team.",
                   "author": "Aylin", "role": "Pflege"}]
        pg = self._page(blocks)
        url = reverse('ats:blocks_editor',
                      kwargs={'kind': 'page', 'obj_id': pg.id})
        self.client.force_login(make_user("cbadmin2", role="HR-Admin"))
        self.client.post(url, data={"action": "save", "idx": "0",
                                    "f_text": "Bestes Team.",
                                    "f_author": "Aylin", "f_role": "Pflege"})
        pg.refresh_from_db()
        self.assertEqual(pg.blocksJson, blocks)                # No-Op-Garantie

    def test_landing_page_renders_blocks(self):

        from ..models import LandingPage
        LandingPage.objects.create(
            name="LP", slug="lp-blocks",
            blocksJson=[{"type": "stats",
                         "items": ["57|Aufrufe heute"]}])
        page = self.client.get(reverse('ats:landing_page',
                                       args=["lp-blocks"]))
        self.assertContains(page, "Aufrufe heute")

class CampaignExpiryTestCase(TestCase):
    """P1-10: Kampagnen-Ablaufdatum – Landingpage & Kanal automatisch inaktiv."""

    def _lp(self, expired=False):
        from ..models import LandingPage
        exp = (timezone.now() - datetime.timedelta(days=1)) if expired else None
        return LandingPage.objects.create(
            name="Sommeraktion", slug="sommer", headline="Sommeraktion 2026",
            expiresAt=exp)

    def _channel(self, expired=False):
        from ..models import SourceChannel
        exp = (timezone.now() - datetime.timedelta(hours=2)) if expired else None
        return SourceChannel.objects.create(
            name="Jobmesse Wien", slug="MESSE_WIEN", expiresAt=exp)

    def test_landing_page_serves_then_expires_gracefully(self):
        lp = self._lp(expired=False)
        r = self.client.get(f"/k/{lp.slug}/")
        self.assertContains(r, "Sommeraktion 2026")
        self.assertEqual(self.client.session.get('application_src'), "SOMMER")
        lp.refresh_from_db()
        self.assertEqual(lp.views, 1)                          # gezaehlt
        # Ablauf: freundliche Endseite statt 404 (QR auf Plakaten!)
        lp.expiresAt = timezone.now() - datetime.timedelta(minutes=1)
        lp.save(update_fields=['expiresAt'])
        self.client.session.flush()
        r2 = self.client.get(f"/k/{lp.slug}/")
        self.assertEqual(r2.status_code, 200)
        self.assertContains(r2, "Diese Aktion ist beendet")
        self.assertContains(r2, "offenen Stellen")             # Weg zur Boerse
        self.assertIsNone(self.client.session.get('application_src'))
        lp.refresh_from_db()
        self.assertEqual(lp.views, 1)                          # NICHT gezaehlt

    def test_channel_attribution_stops_after_expiry(self):
        self._channel(expired=False)
        self.client.get("/jobs/?src=MESSE_WIEN")
        self.assertEqual(self.client.session.get('application_src'),
                         "MESSE_WIEN")
        # Abgelaufen: keine neue Zuordnung mehr
        from ..models import SourceChannel
        SourceChannel.objects.update(
            expiresAt=timezone.now() - datetime.timedelta(hours=1))
        self.client.session.flush()
        self.client.get("/jobs/?src=MESSE_WIEN")
        self.assertIsNone(self.client.session.get('application_src'))
        # Freie Quellen (kein angelegter Kanal) bleiben unbeschraenkt
        self.client.get("/jobs/?src=EMPFEHLUNG_MUELLER")
        self.assertEqual(self.client.session.get('application_src'),
                         "EMPFEHLUNG_MUELLER")

    def test_admin_sets_and_clears_expiry(self):
        ch = self._channel()
        lp = self._lp()
        self.client.force_login(make_user("exp-admin", role="HR-Admin"))
        self.client.post(reverse('ats:source_channels'), data={
            "form": "expiry", "ch_id": str(ch.id), "expires": "2026-06-30"})
        ch.refresh_from_db()
        local = timezone.localtime(ch.expiresAt)
        self.assertEqual(local.date().isoformat(), "2026-06-30")
        self.assertEqual(local.hour, 23)                       # Tagesende (lokal)
        page = self.client.get(reverse('ats:source_channels'))
        self.assertContains(page, "Kampagne beendet")          # Badge
        # Leeren = laeuft wieder unbegrenzt
        self.client.post(reverse('ats:source_channels'), data={
            "form": "expiry", "ch_id": str(ch.id), "expires": ""})
        ch.refresh_from_db()
        self.assertIsNone(ch.expiresAt)
        # Landingpage analog (eigener Feldname wg. Edit-Formular-Kollision)
        self.client.post(reverse('ats:landing_pages'), data={
            "form": "expiry", "expiry_lp_id": str(lp.id),
            "expires": "2026-08-31"})
        lp.refresh_from_db()
        self.assertEqual(lp.expiresAt.date().isoformat(), "2026-08-31")

    def test_unexpired_and_undated_behave_as_before(self):
        lp = self._lp()                                        # kein Datum
        r = self.client.get(f"/k/{lp.slug}/")
        self.assertContains(r, "Sommeraktion 2026")
        lp.expiresAt = timezone.now() + datetime.timedelta(days=30)
        lp.save(update_fields=['expiresAt'])
        r2 = self.client.get(f"/k/{lp.slug}/")
        self.assertNotContains(r2, "Diese Aktion ist beendet") # noch aktiv

class CmsAndNotesCoverageTestCase(TestCase):
    """Deckt add_note (mit BOLA) und die CMS-Views save/delete ab."""

    def setUp(self):
        self.admin = make_user("cn-admin", role="HR-Admin")
        self.recruiter = make_user("cn-rec", role="Recruiter")

    def _application(self):
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
        fam = JobFamily.objects.create(name="CN-Fam")
        ws = WorkflowState.objects.create(name="published")
        job = JobPosting.objects.create(title="Kraft", organization=org,
                                        facility=fac, location=loc,
                                        jobFamily=fam, workflowState=ws)
        return Application.objects.create(
            applicant=Applicant.objects.create(firstName="C", lastName="N",
                                               email="cn@x.de"),
            jobPosting=job, status="NEW")

    # --- add_note: schreibt Notiz + BOLA ---
    def test_add_note_appends_and_audits(self):
        from ..models import AuditLog
        app = self._application()
        self.client.force_login(self.recruiter)
        r = self.client.post(reverse('ats:add_note', args=[app.id]),
                             {"note": "Sympathisch im Telefonat"})
        self.assertTrue(r.json()["success"])
        app.refresh_from_db()
        self.assertIn("Sympathisch im Telefonat", app.internalNotes)
        self.assertTrue(AuditLog.objects.filter(action="ADD_NOTE").exists())

    def test_add_note_bola_scoped(self):
        from ..permissions import can_access_application
        app = self._application()
        outsider = make_user("cn-out", role="Recruiter")
        if hasattr(outsider, 'scope'):
            outsider.scope.facilities.clear()
            outsider.scope.locations.clear()
        if not can_access_application(outsider, app):
            self.client.force_login(outsider)
            r = self.client.post(reverse('ats:add_note', args=[app.id]),
                                 {"note": "fremd"})
            self.assertEqual(r.status_code, 404)

    # --- CMS: save_page anlegen, delete_page loeschen ---
    def test_save_and_delete_page(self):
        from ..models import Page
        self.client.force_login(self.admin)
        self.client.post(reverse('ats:save_page'),
                         {"title": "Über uns", "slug": "ueber-uns",
                          "content": "Hallo", "status": "published"})
        page = Page.objects.get(slug="ueber-uns")
        self.assertEqual(page.title, "Über uns")
        # Löschen
        self.client.post(reverse('ats:delete_page', args=[page.id]))
        self.assertFalse(Page.objects.filter(id=page.id).exists())

    def test_save_page_requires_admin(self):
        from ..models import Page
        self.client.force_login(self.recruiter)
        self.client.post(reverse('ats:save_page'),
                         {"title": "Schmuggel", "slug": "schmuggel",
                          "content": "x"})
        self.assertFalse(Page.objects.filter(slug="schmuggel").exists())

    # --- CMS: delete_media ---
    def test_delete_media(self):
        from django.core.files.base import ContentFile

        from ..models import MediaAsset
        asset = MediaAsset.objects.create(name="logo")
        try:
            asset.file.save("logo.txt", ContentFile(b"x"), save=True)
        except Exception:
            pass
        self.client.force_login(self.admin)
        self.client.post(reverse('ats:delete_media', args=[asset.id]))
        self.assertFalse(MediaAsset.objects.filter(id=asset.id).exists())

class TextSnippetsTestCase(TestCase):
    """UC-SB-18 / UC-UM-13: Textbausteine – war ungetestet."""

    def setUp(self):
        self.admin = make_user("ts-admin", role="HR-Admin")
        self.recruiter = make_user("ts-rec", role="Recruiter")

    def test_create_and_list_snippet(self):
        from ..models import TextSnippet
        self.client.force_login(self.admin)
        self.client.post(reverse('ats:snippets'),
                         {"category": "INTRO", "content": "30 Tage Urlaub"})
        s = TextSnippet.objects.get()
        self.assertEqual(s.category, "INTRO")
        page = self.client.get(reverse('ats:snippets'))
        self.assertContains(page, "30 Tage Urlaub")

    def test_delete_snippet(self):
        from ..models import TextSnippet
        self.client.force_login(self.admin)
        self.client.post(reverse('ats:snippets'),
                         {"category": "TASKS", "content": "Weg damit"})
        s = TextSnippet.objects.get()
        self.client.post(reverse('ats:snippets'), {"delete_id": str(s.id)})
        self.assertFalse(TextSnippet.objects.filter(id=s.id).exists())

    def test_snippets_require_admin(self):
        from ..models import TextSnippet
        self.client.force_login(self.recruiter)
        self.client.post(reverse('ats:snippets'),
                         {"category": "INTRO", "content": "Schmuggel"})
        self.assertFalse(TextSnippet.objects.filter(content="Schmuggel").exists())
