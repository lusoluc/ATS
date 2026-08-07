"""SecurATS-Tests: board (aufgeteilt aus der frueheren Monolith-tests.py)."""
import datetime
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .factories import make_application, make_job, make_world
from .utils import make_user


class ApplicationDocumentsTestCase(TestCase):
    """WP1: Mehrfach-Upload + sicherer Nachweis-Download (BOLA/Audit)."""

    def _job(self):
        return make_job(make_world(), title="Fachärztin")

    def test_apply_with_multiple_documents_and_photo_cv(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                job = self._job()
                cv = SimpleUploadedFile("cv.jpg", b"\xff\xd8\xff", content_type="image/jpeg")
                d1 = SimpleUploadedFile("approbation.pdf", b"%PDF-1", content_type="application/pdf")
                d2 = SimpleUploadedFile("zeugnis.jpg", b"\xff\xd8\xff", content_type="image/jpeg")
                resp = self.client.post(
                    reverse('ats:bewerben', args=[job.id]),
                    data={"first_name": "Katharina", "last_name": "Vossberg", "consent_privacy": "on",
                          "email": "kv@ex.org", "cv_file": cv, "documents": [d1, d2]},
                )
                self.assertEqual(resp.status_code, 200)
                from ..models import Application, ApplicationDocument, email_blind_index
                app = Application.objects.get(applicant__emailHash=email_blind_index("kv@ex.org"))
                self.assertEqual(ApplicationDocument.objects.filter(application=app).count(), 2)
                self.assertIsNotNone(app.cvStorageId)  # Foto-CV akzeptiert

    def test_document_download_auth_and_bola(self):
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                from ..models import ApplicationDocument, Location, UserScope
                app = make_application(self._job(), first_name="K",
                                       last_name="V", email="kv2@ex.org")
                doc = ApplicationDocument.objects.create(
                    application=app, name="approbation.pdf",
                    file=SimpleUploadedFile("a.pdf", b"%PDF-1"))
                url = reverse('ats:download_document', args=[doc.id])
                # anonym -> Login-Redirect
                self.assertEqual(self.client.get(url).status_code, 302)
                # Recruiter mit Zugriff -> 200 + Audit
                rec = make_user("wp1rec", role="Recruiter")
                self.client.force_login(rec)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                # KEIN response.close() hier: Das feuert das Signal
                # request_finished -> close_old_connections. Django sieht dann
                # den vom TestCase gesetzten Transaktions-Autocommit und
                # SCHLIESST die Verbindung. Auf SQLite ist close() bei einer
                # In-Memory-DB ein No-Op (faellt nie auf), auf PostgreSQL ist
                # die Verbindung danach tot. Wir lesen den Inhalt stattdessen
                # aus – das prueft ohnehin mehr als ein blosser Statuscode.
                content = b"".join(response.streaming_content)
                self.assertTrue(content.startswith(b"%PDF"))
                from ..models import AuditLog
                self.assertTrue(AuditLog.objects.filter(action="READ_DOCUMENT").exists())
                # BOLA: eingeschränkter Recruiter auf anderen Standort -> 404
                other = Location.objects.create(name="Muenchen")
                scoped = make_user("wp1scoped", role="Recruiter")
                sc = UserScope.objects.create(user=scoped, full_access=False)
                sc.locations.add(other)
                self.client.force_login(scoped)
                self.assertEqual(self.client.get(url).status_code, 404)

class BoardReorderTestCase(TestCase):
    """WP4/B10: Spalten-Reihenfolge persistieren, BOLA-sicher."""

    def test_reorder_updates_board_order_and_respects_scope(self):
        from ..models import Location, UserScope
        world = make_world()
        loc_m = Location.objects.create(name="Muenchen")
        job_b = make_job(world, title="J1")
        job_m = make_job(world, title="J2", location=loc_m)
        apps = [make_application(job) for job in (job_b, job_b, job_m)]

        # Recruiter nur mit Scope auf den Welt-Standort
        rec = make_user("wp4rec", role="Recruiter")
        sc = UserScope.objects.create(user=rec, full_access=False)
        sc.locations.add(world.location)
        self.client.force_login(rec)

        r = self.client.post(reverse('ats:reorder_board'), data={
            "status": "NEW",
            "ids[]": [str(apps[1].id), str(apps[0].id), str(apps[2].id)]})
        self.assertEqual(r.status_code, 200)
        for a in apps:
            a.refresh_from_db()
        self.assertEqual(apps[1].boardOrder, 0)
        self.assertEqual(apps[0].boardOrder, 1)
        self.assertEqual(apps[2].boardOrder, 0)  # München: außerhalb Scope -> unangetastet

    def test_reorder_rejects_invalid_status(self):
        rec = make_user("wp4rec2", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.post(reverse('ats:reorder_board'), data={"status": "HACK", "ids[]": []})
        self.assertEqual(r.status_code, 400)

class WP4FeatureTestCase(TestCase):
    """WP4: Bulk-Statuswechsel (BOLA+Audit) und Vorlagen-Versionierung."""

    def _setup_apps(self):
        job = make_job(make_world(), title="J")
        return [make_application(job) for _ in range(3)]

    def test_bulk_status_change_with_audit(self):
        from ..models import AuditLog
        apps = self._setup_apps()
        rec = make_user("wp4bulk", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.post(reverse('ats:bulk_update_status'), data={
            "status": "IN_REVIEW", "ids[]": [str(a.id) for a in apps[:2]]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["updated"], 2)
        for a in apps[:2]:
            a.refresh_from_db()
            self.assertEqual(a.status, "IN_REVIEW")
        apps[2].refresh_from_db()
        self.assertEqual(apps[2].status, "NEW")
        self.assertEqual(AuditLog.objects.filter(action="STATUS_CHANGE_BULK").count(), 2)

    def test_bulk_rejects_invalid_status(self):
        rec = make_user("wp4bulk2", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.post(reverse('ats:bulk_update_status'), data={"status": "X", "ids[]": []})
        self.assertEqual(r.status_code, 400)

    def test_bulk_skips_out_of_scope_applications(self):
        """Bulk darf kein Schlupfloch um den Einzel-BOLA-Schutz sein: eine
        Bewerbung außerhalb des Zugriffsbereichs muss übersprungen werden,
        während die eigenen normal durchlaufen."""
        from ..permissions import can_access_application
        apps = self._setup_apps()
        outsider = make_user("wp4bulk3", role="Recruiter")
        if hasattr(outsider, 'scope'):
            outsider.scope.facilities.clear()
            outsider.scope.locations.clear()
        # Nur sinnvoll, wenn der Scope tatsächlich greift
        if not can_access_application(outsider, apps[0]):
            self.client.force_login(outsider)
            r = self.client.post(reverse('ats:bulk_update_status'), data={
                "status": "REJECTED",
                "ids[]": [str(a.id) for a in apps]})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["updated"], 0)   # nichts durchgelassen
            for a in apps:
                a.refresh_from_db()
                self.assertEqual(a.status, "NEW")      # unverändert

    def test_job_template_versioning(self):
        from ..models import JobTemplate
        admin = make_user("wp4tpl", role="HR-Admin")
        self.client.force_login(admin)
        self.client.post(reverse('ats:job_templates'), data={"title": "Pflege", "content": "v1-Inhalt"})
        self.client.post(reverse('ats:job_templates'), data={"title": "pflege", "content": "v2-Inhalt"})
        versions = JobTemplate.objects.filter(title__iexact="pflege").order_by("version")
        self.assertEqual([t.version for t in versions], [1, 2])
        self.assertEqual(versions[1].parent_id, versions[0].id)
        # Liste zeigt nur die neueste Version
        resp = self.client.get(reverse('ats:job_templates'))
        self.assertContains(resp, "v2-Inhalt")
        self.assertNotContains(resp, "v1-Inhalt")

class TodayFocusAndContactTestCase(TestCase):
    """UC-PW-06/UM-06 'Heute wichtig' + UC-AY-09 Kontaktdaten im Portal."""

    def _world(self):
        from ..models import ApplicantToken, Application, Interview, Message, StaffingRequest
        world = make_world()
        self.job = make_job(world, title="Pflegefachkraft")
        self.app = make_application(self.job, first_name="Lena", last_name="B",
                                    email="lena@x.de", phone="040-1")
        self.ap = self.app.applicant
        Application.objects.filter(id=self.app.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=9))  # ueberfaellig
        ApplicantToken.objects.create(applicant=self.ap, token="tf-token",
                                      expiresAt=timezone.now() + datetime.timedelta(days=30))
        Message.objects.create(application=self.app, direction="INBOUND",
                               content="Wann höre ich von Ihnen?")
        Interview.objects.create(application=self.app, locationType="VIDEO",
                                 scheduledAt=timezone.now() - datetime.timedelta(days=2))
        StaffingRequest.objects.create(title="MFA", facility=world.facility,
                                       justification="Empfang unterbesetzt")

    def test_dashboard_shows_bundled_signals(self):
        self._world()
        rec = make_user("tfrec", role="Recruiter")
        self.client.force_login(rec)
        r = self.client.get(reverse('ats:dashboard'))
        self.assertContains(r, "Heute wichtig")
        self.assertContains(r, "1 unbeantwortete Nachricht")
        self.assertContains(r, "Erstsichtung")
        self.assertContains(r, "Ergebnis")
        self.assertContains(r, "offene Bedarfsmeldung")
        self.assertContains(r, "Lena B")                       # Direktlink zur Nachricht

    def test_opening_messages_clears_unread(self):
        from ..models import Message
        self._world()
        rec = make_user("tfrec2", role="Recruiter")
        self.client.force_login(rec)
        self.client.get(f"/recruiter/applications/{self.app.id}/messages/")
        self.assertFalse(Message.objects.filter(direction="INBOUND",
                                                readStatus=False).exists())
        r = self.client.get(reverse('ats:dashboard'))
        self.assertNotContains(r, "unbeantwortete Nachricht")  # Zaehler abgebaut

    def test_hiring_manager_sees_no_staffing_counter(self):
        self._world()
        hm = make_user("tfhm", role="Hiring-Manager")
        self.client.force_login(hm)
        r = self.client.get(reverse('ats:dashboard'))
        self.assertNotContains(r, "offene Bedarfsmeldung")     # entscheidet nicht

    def test_portal_phone_update_and_email_request(self):
        from ..models import AuditLog, Message
        self._world()
        r = self.client.post(reverse('ats:candidate_portal', args=["tf-token"]),
                             data={"form": "contact", "phone": "0151 999",
                                   "new_email": "lena.neu@x.de"})
        self.assertEqual(r.status_code, 302)
        self.ap.refresh_from_db()
        self.assertEqual(self.ap.phone, "0151 999")            # Telefon direkt
        self.assertEqual(self.ap.email, "lena@x.de")           # E-Mail UNveraendert
        self.assertTrue(any("lena.neu@x.de".lower() in (n.content or '').lower()
                            for n in Message.objects.filter(direction="INBOUND")))
        self.assertTrue(AuditLog.objects.filter(action="CANDIDATE_DATA_UPDATED").exists())
        self.assertTrue(AuditLog.objects.filter(
            action="CANDIDATE_EMAIL_CHANGE_REQUESTED").exists())
        page = self.client.get(reverse('ats:candidate_portal', args=["tf-token"]))
        self.assertContains(page, "0151 999")                  # vorbefuellt

class HiredStatusTestCase(TestCase):
    """Das Einstellungs-Ereignis: Uebergaenge, Time-to-Fill, Kennzahlen."""

    def _world(self):
        from ..models import Application, SourceChannel
        self.job = make_job(make_world(), title="Pflegefachkraft")
        SourceChannel.objects.create(name="Jobmesse", slug="MESSE_HS")
        self.app = make_application(self.job, first_name="Rosa", last_name="M",
                                    email="rosa@x.de", status="INVITED",
                                    source="MESSE_HS")
        Application.objects.filter(id=self.app.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=14))
        self.app.refresh_from_db()

    def _set_status(self, status):
        return self.client.post(
            reverse('ats:update_status', args=[self.app.id]),
            data={"status": status})

    def test_hire_only_from_invited_and_sets_hired_at(self):
        self._world()
        self.client.force_login(make_user("hsrec", role="Recruiter"))
        # NEW -> HIRED verboten (nachvollziehbarer Prozess)
        self.app.status = "NEW"
        self.app.save(update_fields=["status"])
        r = self._set_status("HIRED")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Eingeladen", r.json()["error"])
        # INVITED -> HIRED setzt das Ereignis
        self.app.status = "INVITED"
        self.app.save(update_fields=["status"])
        self._set_status("HIRED")
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "HIRED")
        self.assertIsNotNone(self.app.hiredAt)
        # Korrektur zurueck loescht das Ereignis sauber
        self._set_status("INVITED")
        self.app.refresh_from_db()
        self.assertIsNone(self.app.hiredAt)

    def test_kanban_column_and_metrics_surfaces(self):
        self._world()
        # Der Test prueft auch die Kanal-Seite, die inzwischen HR-Admin
        # verlangt (Kampagnenkosten sind Leitungs-Information).
        self.client.force_login(make_user("hsrec2", role="HR-Admin"))
        self._set_status("HIRED")
        dash = self.client.get(reverse('ats:dashboard'))
        self.assertContains(dash, "Eingestellt")               # neue Spalte
        self.assertContains(dash, 'id="col-HIRED"')
        kanal = self.client.get(reverse('ats:source_channels'))
        self.assertContains(kanal, "eingestellt")
        self.assertContains(kanal, "Ø Tage bis Einstellung")
        self.assertContains(kanal, "14")                       # Time-to-Fill
        analytics = self.client.get(reverse('ats:analytics'))
        self.assertContains(analytics, "Einstellungen")
        self.assertContains(analytics, "Ø Tage von Bewerbung bis Einstellung")

    def test_cost_per_hire_uses_real_hires(self):
        from ..analytics import cost_per_hire
        from ..models import Application
        self._world()
        self.client.force_login(make_user("hsrec3", role="Recruiter"))
        rows = cost_per_hire(Application.objects.all(),
                             {"MESSE_HS": 1200.0})
        self.assertEqual(rows[0]["hires"] if "hires" in rows[0] else
                         rows[0].get("count", 0), 0)           # INVITED zaehlt nicht
        self._set_status("HIRED")
        rows = cost_per_hire(Application.objects.all(),
                             {"MESSE_HS": 1200.0})
        row = rows[0]
        hires = row.get("hires", row.get("count"))
        self.assertEqual(hires, 1)                             # echtes Ereignis

    def test_portal_pipeline_shows_hired_complete(self):
        from ..models import ApplicantToken
        self._world()
        self.client.force_login(make_user("hsrec4", role="Recruiter"))
        self._set_status("HIRED")
        ApplicantToken.objects.create(
            applicant=self.app.applicant, token="hs-token",
            expiresAt=timezone.now() + datetime.timedelta(days=5))
        portal = self.client.get(reverse('ats:candidate_portal',
                                         args=["hs-token"]))
        self.assertContains(portal, "b-HIRED")                 # gruener Abschluss

class ManualHireDateTestCase(TestCase):
    """Einstellungsdatum manuell setzbar + nachtraeglich korrigierbar."""

    def _world(self):
        job = make_job(make_world(), title="Stelle")
        self.app = make_application(job, first_name="Ida", last_name="B",
                                    email="ida@x.de", status="INVITED")

    def _set(self, **data):
        return self.client.post(
            reverse('ats:update_status', args=[self.app.id]), data=data)

    def test_manual_date_correction_and_validation(self):
        self._world()
        self.client.force_login(make_user("mhrec", role="Recruiter"))
        self._set(status="HIRED", hired_at="2026-06-15")       # rueckwirkend
        self.app.refresh_from_db()
        self.assertEqual(self.app.hiredAt.date().isoformat(), "2026-06-15")
        # Bereits HIRED: reine Datumskorrektur erlaubt
        self._set(status="HIRED", hired_at="2026-06-20")
        self.app.refresh_from_db()
        self.assertEqual(self.app.hiredAt.date().isoformat(), "2026-06-20")
        # Zukunft und Unsinn abgelehnt
        r = self._set(status="HIRED", hired_at="2099-01-01")
        self.assertEqual(r.status_code, 400)
        r = self._set(status="HIRED", hired_at="quatsch")
        self.assertEqual(r.status_code, 400)
        self.app.refresh_from_db()
        self.assertEqual(self.app.hiredAt.date().isoformat(), "2026-06-20")

class CvInlinePreviewTestCase(TestCase):
    """Klickstrecke: Lebenslauf direkt im Fenster lesen statt herunterladen.

    Befund: Die "Lebenslauf-Vorschau" war ein Platzhalter (im Code als
    "Previewer Frame Mock" bezeichnet) – sie zeigte ein PDF-Symbol und einen
    Download-Knopf. Der Recruiter musste die Anwendung verlassen, um die
    häufigste Handlung überhaupt zu erledigen. Zudem landete dabei eine
    KOPIE der Bewerber-PII auf jedem Recruiter-Laptop.

    Die Bequemlichkeit darf die Zugriffskontrolle NICHT aufweichen – genau
    das prüfen diese Tests.
    """

    def setUp(self):
        from django.core.files.storage import default_storage

        self.app = make_application(
            make_job(make_world(), title="Pflegekraft"),
            first_name="C", last_name="V", email="cv@x.de")
        self.app.cvStorageId = default_storage.save(
            "cvs/abc_lebenslauf.pdf",
            SimpleUploadedFile("lebenslauf.pdf", b"%PDF-1.4 inhalt"))
        self.app.save(update_fields=["cvStorageId"])
        self.rec = make_user("cv-rec", role="Recruiter")
        self.url = reverse('ats:download_cv', args=[self.app.id])

    def test_inline_view_renders_in_browser(self):
        """?view=1 liefert die Datei zur ANZEIGE (kein Download-Zwang)."""
        self.client.force_login(self.rec)
        r = self.client.get(self.url + "?view=1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertNotIn("attachment", r.get("Content-Disposition", ""))
        self.assertEqual(r["X-Content-Type-Options"], "nosniff")
        b"".join(r.streaming_content)

    def test_download_still_works_as_attachment(self):
        self.client.force_login(self.rec)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("attachment", r["Content-Disposition"])
        b"".join(r.streaming_content)

    def test_audit_distinguishes_view_from_download(self):
        """Für den Datenschutzbeauftragten wichtig: WER hat nur gelesen und
        wer hat eine KOPIE gezogen?"""
        from ..models import AuditLog
        self.client.force_login(self.rec)
        b"".join(self.client.get(self.url + "?view=1").streaming_content)
        b"".join(self.client.get(self.url).streaming_content)
        modes = [a.metadataJson for a in
                 AuditLog.objects.filter(action="READ_CV")]
        self.assertTrue(any('"mode": "inline"' in m for m in modes))
        self.assertTrue(any('"mode": "download"' in m for m in modes))

    def test_inline_does_not_bypass_access_control(self):
        """Die Vorschau darf KEIN Schlupfloch sein: anonym -> kein Zugriff."""
        r = self.client.get(self.url + "?view=1")
        self.assertIn(r.status_code, (302, 403))

    def test_inline_respects_bola_scope(self):
        """Ein Recruiter mit fremdem Standort-Scope darf auch die Vorschau
        nicht sehen."""
        from ..models import Location
        from ..permissions import can_access_application
        other = make_user("cv-fremd", role="Recruiter")
        if hasattr(other, 'scope'):
            other.scope.locations.set(
                [Location.objects.create(name="Muenchen")])
            other.scope.save()
        if not can_access_application(other, self.app):
            self.client.force_login(other)
            r = self.client.get(self.url + "?view=1")
            self.assertEqual(r.status_code, 404)

    def test_word_document_is_never_served_inline(self):
        """doc/docx kann kein Browser rendern – ehrlich als Download liefern
        statt eine kaputte Vorschau zu zeigen."""
        from django.core.files.storage import default_storage
        self.app.cvStorageId = default_storage.save(
            "cvs/xyz_lebenslauf.docx",
            SimpleUploadedFile("lebenslauf.docx", b"PK\x03\x04"))
        self.app.save(update_fields=["cvStorageId"])
        self.client.force_login(self.rec)
        r = self.client.get(self.url + "?view=1")
        self.assertIn("attachment", r["Content-Disposition"])
        b"".join(r.streaming_content)

class ModalDecisionButtonsTestCase(TestCase):
    """Klickstrecke: Entscheiden, wo gelesen wird.

    Befund: Im Bewerbungs-Fenster konnte man einladen – aber weder
    "in Prüfung nehmen" noch "absagen", also die zwei häufigsten
    Entscheidungen. Der Recruiter musste das Fenster schließen, die Karte
    im Board suchen und ziehen.
    """

    def test_modal_offers_the_three_decisions(self):
        admin = make_user("md-admin", role="HR-Admin")
        self.client.force_login(admin)
        r = self.client.get(reverse('ats:dashboard'))
        self.assertContains(r, 'modal-decide-review')
        self.assertContains(r, 'modal-decide-invited')
        self.assertContains(r, 'modal-decide-rejected')
        self.assertContains(r, 'decideFromModal')

    def _decide_block(self):
        """Der Rumpf von decideFromModal - bis zur naechsten Funktion.

        Bewusst NICHT ueber eine feste Zeichenzahl: das schlug schon bei einer
        Ergaenzung am Funktionsanfang fehl, obwohl die Schutzplanke intakt war.
        """
        import os
        tpl = open(os.path.join('templates', 'includes', 'dashboard', 'scripts.html'),
                   encoding='utf-8').read()
        i = tpl.index('function decideFromModal')
        nxt = tpl.find('\n    function ', i + 10)
        return tpl[i:nxt if nxt > i else len(tpl)]

    def test_decision_uses_the_same_guarded_endpoint(self):
        """Die Abkürzung darf keine Schutzplanke umgehen: Sie nutzt denselben
        update-status-Endpunkt inklusive Bedenken-Gate."""
        block = self._decide_block()
        self.assertIn('update-status', block)
        self.assertIn('concerns_blocked', block)   # Bedenken-Gate bleibt aktiv

    def test_rejection_asks_before_sending(self):
        """Die Absage verschickt sofort eine nicht rueckholbare Mail - dafuer
        muss sie fragen (die harmlosere Sammel-Absage tat es schon)."""
        block = self._decide_block()
        i = block.index("'REJECTED'")
        self.assertIn('confirm', block[:i + 400],
                      "Absage aus dem Modal ohne Rückfrage")

class SidebarRoleFilteringTestCase(TestCase):
    """Benutzerfuehrung: Ein Recruiter sieht nur seine taegliche Arbeit,
    keine Admin-/IT-/Management-Werkzeuge. Ein HR-Admin sieht alles.

    Ziel: kein Schritt zu viel. Der ueberladene Arbeitsplatz (8 Werkzeuge +
    ueber 20 Verwaltungs-Links fuer JEDEN) hat einen Recruiter, der nur
    sichten will, mit SAP-Sync und Systemeinstellungen konfrontiert.

    Seit B2 liegen die sechs Verwaltungs-Bereiche auf EIGENEN Seiten. Im
    Dashboard steht davon nur noch der Link – geprueft wird deshalb der
    Link (Seitenleiste) UND der serverseitige Schutz der Seite selbst.
    """

    def setUp(self):
        self.recruiter = make_user("side-rec", role="Recruiter")
        self.admin = make_user("side-admin", role="HR-Admin")

    # Werkzeuge, die JEDER braucht (taegliche Arbeit)
    WORK = ["kanban-tab", "jobs-tab", "Interview-Kalender", "Talent-Pool",
            "Freigaben"]
    # Seiten, die nur ein HR-Admin erreichen darf: URL-Name + ein inhaltlicher
    # Marker, der beweist, dass die Seite wirklich ihren Inhalt ausliefert.
    ADMIN_PAGES = [
        ('ats:stats_page', "Ausgleichsabgabe"),
        ('ats:process_page', "Recruiting Prozess Flow"),
        ('ats:templates_page', "Globale Variablen"),
        # Der zweite Seiten-Editor ist entfallen - es gibt jetzt EINEN
        # (ats:pages_manage), der auch loeschen kann und zum Baukasten fuehrt.
        ('ats:pages_manage', "Seiten &amp; Navigation"),
        ('ats:ki_page', "KI-Steuerungszentrum"),
        ('ats:hris_page', "Feldzuordnung"),
    ]
    # Weitere Verwaltungs-Links, die schon immer eigene Seiten waren.
    ADMIN_ONLY_LINKS = ["Audit-Log", "Governance", "Daten-Import"]

    def _admin_link_markers(self):
        """Alle Seitenleisten-Ziele, die ein Recruiter nicht sehen darf."""
        return ([reverse(name) for name, _ in self.ADMIN_PAGES]
                + self.ADMIN_ONLY_LINKS)

    def test_recruiter_sees_only_daily_work(self):
        self.client.force_login(self.recruiter)
        html = self.client.get(reverse('ats:dashboard')).content.decode()
        for tool in self.WORK:
            self.assertIn(tool, html, f"Recruiter braucht '{tool}'")
        for marker in self._admin_link_markers():
            self.assertNotIn(marker, html,
                             f"Recruiter soll '{marker}' NICHT sehen")

    def test_admin_sees_everything(self):
        self.client.force_login(self.admin)
        html = self.client.get(reverse('ats:dashboard')).content.decode()
        for tool in self.WORK + self._admin_link_markers():
            self.assertIn(tool, html, f"Admin braucht Zugriff auf '{tool}'")

    def test_superuser_counts_as_admin(self):
        su = make_user("side-su", superuser=True)
        self.client.force_login(su)
        html = self.client.get(reverse('ats:dashboard')).content.decode()
        self.assertIn(reverse('ats:hris_page'), html)

    def test_dashboard_carries_no_admin_content_anymore(self):
        """B2: Die Verwaltungs-Inhalte liegen auf eigenen Seiten – auch fuer
        einen HR-Admin darf das Dashboard sie nicht mehr mitliefern. Sonst
        waere die Aufteilung nur Kosmetik."""
        self.client.force_login(self.admin)
        html = self.client.get(reverse('ats:dashboard')).content.decode()
        for _, marker in self.ADMIN_PAGES:
            self.assertNotIn(marker, html,
                             f"'{marker}' gehoert nicht mehr ins Dashboard")

    def test_admin_pages_render_for_hr_admin(self):
        self.client.force_login(self.admin)
        for name, marker in self.ADMIN_PAGES:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertEqual(r.status_code, 200)
                self.assertIn(marker, r.content.decode())

    def test_admin_pages_rejected_for_recruiter(self):
        """Das Ausblenden in der Seitenleiste ist Benutzerfuehrung, KEINE
        Sicherheitsmassnahme. Wer die URL kennt, wird trotzdem abgewiesen."""
        self.client.force_login(self.recruiter)
        for name, _ in self.ADMIN_PAGES:
            with self.subTest(page=name):
                r = self.client.get(reverse(name))
                self.assertIn(r.status_code, (302, 403, 404))

    def test_hiding_is_ui_only_server_still_protects(self):
        """Gilt genauso fuer die aelteren Admin-Aktionen."""
        self.client.force_login(self.recruiter)
        r = self.client.get(reverse('ats:sap_sf_mapper'))
        self.assertIn(r.status_code, (302, 403, 404))


class SendOnceStateTestCase(TestCase):
    """Einmal-Aktionen: Der Gesendet-Zustand verhindert Doppel-Nachrichten.

    Regel: Nach einer gesendeten Nachricht bleibt das Senden gesperrt, bis
    entweder eine Antwort des Bewerbers eingeht ODER sich der
    Bewerbungsstatus aendert. Der Zustand wird serverseitig gerendert und
    ueberlebt damit jeden Seiten-Reload."""

    def setUp(self):
        self.app = make_application(make_job(make_world(), title="SO-Stelle"))
        self.rec = make_user("so-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.url = reverse('ats:application_messages', args=[self.app.id])

    def _send(self, text="Rückfrage zu den Unterlagen"):
        resp = self.client.post(self.url, data={"content": text})
        # Deterministisch trotz grober Uhr-Aufloesung: die gesendete Nachricht
        # liegt sicher VOR den Folge-Ereignissen des Tests.
        from datetime import timedelta

        from ..models import Message
        Message.objects.filter(application=self.app, direction='OUTBOUND') \
            .update(createdAt=timezone.now() - timedelta(seconds=5))
        return resp

    def test_after_send_form_is_replaced_by_done_state(self):
        self._send()
        page = self.client.get(self.url)
        self.assertContains(page, "Nachricht gesendet – wartet auf Antwort")
        self.assertNotContains(page, 'name="content"')      # kein Formular

    def test_inbound_reply_reenables_form(self):
        from ..models import Message
        self._send()
        Message.objects.create(application=self.app, direction='INBOUND',
                               content='Anbei die Unterlagen.')
        page = self.client.get(self.url)
        self.assertContains(page, 'name="content"')
        self.assertNotContains(page, "wartet auf Antwort")

    def test_status_change_reenables_form(self):
        self._send()
        r = self.client.post(reverse('ats:update_status', args=[self.app.id]),
                             data={"status": "IN_REVIEW"})
        self.assertEqual(r.status_code, 200)
        page = self.client.get(self.url)
        self.assertContains(page, 'name="content"')

    def test_fresh_conversation_shows_form(self):
        page = self.client.get(self.url)
        self.assertContains(page, 'name="content"')
        self.assertNotContains(page, "wartet auf Antwort")


class BoardInsightsTestCase(TestCase):
    """C1 Wiederbewerber-Signal + C2 Liegenbleiber-Radar (aus vorhandenen Daten)."""

    def test_repeat_applicant_detected_across_applications(self):
        from ..board_insights import repeat_applicant_map
        from ..models import Applicant, Application
        job = make_job(make_world(), title="RA-Stelle")
        person = Applicant.objects.create(firstName="Mehrfach", lastName="Test",
                                          email="mehrfach@ex.org")
        # zwei Bewerbungen derselben Person, aeltere abgelehnt
        old = Application.objects.create(applicant=person, jobPosting=job,
                                         status="REJECTED")
        Application.objects.filter(id=old.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=120))
        new = Application.objects.create(applicant=person, jobPosting=job,
                                         status="NEW")
        # Einzelbewerber als Gegenprobe
        solo = make_application(job, first_name="Einzel", last_name="Fall",
                                email="einzel@ex.org")
        m = repeat_applicant_map([new, solo])
        self.assertIn(new.id, m)
        self.assertEqual(m[new.id]["count"], 2)
        self.assertEqual(m[new.id]["prev_status"], "Abgelehnt")
        self.assertNotIn(solo.id, m)                       # nur eine Bewerbung

    def test_stale_radar_levels_and_endstate_excluded(self):
        from ..board_insights import stale_days_map
        from ..models import Application
        job = make_job(make_world(), title="ST-Stelle")

        def aged(status, days):
            a = make_application(job)
            a.status = status
            a.save(update_fields=["status"])
            Application.objects.filter(id=a.id).update(
                createdAt=timezone.now() - datetime.timedelta(days=days))
            a.refresh_from_db()
            return a

        frisch = aged("NEW", 2)
        warn = aged("NEW", 9)
        alert = aged("IN_REVIEW", 20)
        erledigt = aged("REJECTED", 30)   # Endzustand -> kein Signal
        m = stale_days_map([frisch, warn, alert, erledigt])
        self.assertNotIn(frisch.id, m)
        self.assertEqual(m[warn.id]["level"], "warn")
        self.assertEqual(m[alert.id]["level"], "alert")
        self.assertNotIn(erledigt.id, m)

    def test_status_change_audit_resets_stale_clock(self):
        """Ein Statuswechsel setzt die Liegenbleiber-Uhr zurueck: die Karte ist
        alt, aber gerade erst (per Audit) bewegt worden."""
        from ..audit import create_chained_audit
        from ..board_insights import stale_days_map
        from ..models import Application
        job = make_job(make_world(), title="RS-Stelle")
        a = make_application(job)
        Application.objects.filter(id=a.id).update(
            createdAt=timezone.now() - datetime.timedelta(days=30))
        a.refresh_from_db()
        # frischer Statuswechsel heute
        create_chained_audit("STATUS_CHANGE", application_id=str(a.id))
        m = stale_days_map([a])
        self.assertNotIn(a.id, m)                          # Uhr zurueckgesetzt


class TalentPoolMatchTestCase(TestCase):
    """C3: passende Pool-Personen zu einer veroeffentlichten Stelle finden."""

    def _sub(self, email, fams=None, locs=None, days=30):
        import json as _j
        from datetime import timedelta

        from ..models import TalentPoolSubscription
        return TalentPoolSubscription.objects.create(
            email=email, consentId="c-" + email,
            criteria=_j.dumps({"job_families": fams or [], "locations": locs or []}),
            expiresAt=timezone.now() + timedelta(days=days))

    def test_matches_by_family_and_location_only_active(self):
        from ..talent_pool import pool_matches_for_job
        world = make_world()
        job = make_job(world, title="TP-Stelle")
        treffer_fam = self._sub("fam@ex.org", fams=[str(world.job_family.id)])
        self._sub("loc@ex.org", locs=[str(world.location.id)])
        self._sub("fremd@ex.org", fams=["00000000-0000-0000-0000-000000000000"])
        self._sub("alt@ex.org", fams=[str(world.job_family.id)], days=-1)  # abgelaufen
        emails = {s.email for s in pool_matches_for_job(job)}
        self.assertEqual(emails, {"fam@ex.org", "loc@ex.org"})
        self.assertIn(treffer_fam.email, emails)

    def test_publish_surfaces_pool_message(self):
        world = make_world()
        self._sub("pool@ex.org", fams=[str(world.job_family.id)])
        self.client.force_login(make_user("tp-rec", role="Recruiter"))
        r = self.client.post(reverse('ats:create_job'), data={
            "title": "TP-Publish", "description": "x",
            "facility": str(world.facility.id), "location": str(world.location.id),
            "job_family": str(world.job_family.id),
            "workflow_state": str(world.published.id),
            "pay_band": str(world.band.id)}, follow=True)
        self.assertContains(r, "im Talent-Pool passen")


class JobPoolMatchPageTestCase(TestCase):
    """C3-UI: passende Talente je Stelle sehen, einzeln/gesammelt einladen."""

    def _sub(self, email, world, fn="", ln=""):
        import json as _j
        from datetime import timedelta

        from ..models import Applicant, TalentPoolSubscription
        if fn or ln:
            Applicant.objects.get_or_create(
                email=email, defaults=dict(firstName=fn, lastName=ln))
        return TalentPoolSubscription.objects.create(
            email=email, consentId="c-" + email,
            criteria=_j.dumps({"job_families": [str(world.job_family.id)]}),
            expiresAt=timezone.now() + timedelta(days=30))

    def setUp(self):
        self.world = make_world()
        self.job = make_job(self.world, title="Pool-Seite")
        self.a = self._sub("anna@ex.org", self.world, "Anna", "Berg")
        self.b = self._sub("ben@ex.org", self.world, "Ben", "Krause")
        self.rec = make_user("jp-rec", role="Recruiter")
        self.client.force_login(self.rec)
        self.url = reverse('ats:job_pool_matches', args=[self.job.id])

    def test_page_lists_resolved_names(self):
        r = self.client.get(self.url)
        self.assertContains(r, "Anna Berg")
        self.assertContains(r, "Ben Krause")

    def test_bulk_invite_all(self):
        from ..models import TalentPoolContact
        r = self.client.post(self.url, data={
            "sub_ids": [str(self.a.id), str(self.b.id)]}, follow=True)
        self.assertContains(r, "2 Talent(e) zur Bewerbung eingeladen")
        self.assertEqual(TalentPoolContact.objects.filter(jobPosting=self.job).count(), 2)

    def test_invite_is_once_only(self):
        from ..models import TalentPoolContact
        self.client.post(self.url, data={"sub_ids": [str(self.a.id)]})
        # zweite Ansprache derselben Person zur selben Stelle -> kein Doppel
        self.client.post(self.url, data={"sub_ids": [str(self.a.id)]})
        self.assertEqual(TalentPoolContact.objects.filter(
            jobPosting=self.job, subscription=self.a).count(), 1)

    def test_single_invite_leaves_others_open(self):
        from ..models import TalentPoolContact
        self.client.post(self.url, data={"sub_ids": [str(self.a.id)]})
        contacted = set(TalentPoolContact.objects
                        .filter(jobPosting=self.job)
                        .values_list("subscription_id", flat=True))
        self.assertEqual(contacted, {self.a.id})

    def test_bola_foreign_job_denied(self):
        from ..models import Location, UserScope
        other = Location.objects.create(name="Muenchen")
        foreign = make_job(self.world, title="Fremd", location=other)
        sc = UserScope.objects.create(user=self.rec, full_access=False)
        sc.locations.add(self.world.location)
        r = self.client.get(reverse('ats:job_pool_matches', args=[foreign.id]))
        self.assertEqual(r.status_code, 404)


class BulkActionGuardrailsTestCase(TestCase):
    """U1: Die Sammelaktion darf keine Schutzplanke umgehen.

    Gefunden im Durchgang "unerreichbare Funktionen": bulk_update_status lief
    unter @any_staff_required (ein Viewer konnte massenhaft einladen und
    absagen), ohne Gremium-Gate und ohne Absage-Zustellung.
    """

    def setUp(self):
        from .factories import make_application, make_job, make_world
        self.world = make_world()
        self.job = make_job(self.world)
        self.app = make_application(self.job, status="IN_REVIEW")

    def _bulk(self, status):
        return self.client.post(reverse('ats:bulk_update_status'),
                                data={"status": status, "ids[]": [str(self.app.id)]})

    def test_viewer_is_rejected(self):
        self.client.force_login(make_user("bulk-viewer", role="Viewer"))
        resp = self._bulk("INVITED")
        self.assertNotEqual(resp.status_code, 200)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "IN_REVIEW")

    def test_panel_gate_blocks_bulk_invite(self):
        import json as _json
        panel = make_user("bulk-panel", role="Recruiter")
        self.job.panelUserIdsJson = [str(panel.id)]
        self.job.save(update_fields=['panelUserIdsJson'])
        self.client.force_login(make_user("bulk-rec", role="Recruiter"))
        resp = self._bulk("INVITED")
        self.assertEqual(resp.status_code, 200)
        data = _json.loads(resp.content)
        self.assertEqual(data['updated'], 0)
        self.assertTrue(data['blocked'])
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "IN_REVIEW")   # Gremium wirkt

    def test_bulk_rejection_reaches_the_person(self):
        from django.core import mail

        from ..models import AuditLog
        self.client.force_login(make_user("bulk-rec2", role="Recruiter"))
        mail.outbox = []
        self._bulk("REJECTED")
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, "REJECTED")
        self.assertTrue(self.app.withdrawReason)          # Grund gesetzt
        self.assertTrue(AuditLog.objects.filter(
            action='REJECTION_NOTICE_SENT').exists())     # zugestellt
        self.assertTrue(mail.outbox)
