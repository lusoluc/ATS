"""Hochgeladene Dateien tragen den Namen der Person nicht mehr im Dateinamen.

Bis zum Verschlüsselungs-Paket landeten Uploads als `<uuid>_<Originalname>` in
der Ablage. Der Originalname lautet typischerweise
`Lebenslauf_Maria_Schmidt.pdf` — damit stand der Name im Klartext im
Dateisystem und in der Spalte `cvStorageId`, während `firstName`/`lastName`
derselben Person Fernet-verschlüsselt lagen. Ein Verzeichnis-Listing des
Medienordners war eine Namensliste.

Neue Uploads sind bereits namenlos; hier geht es um den Bestand — und um den
Anzeigenamen, der dabei nicht verloren gehen darf.
"""
import tempfile
from io import StringIO
from pathlib import PurePath

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import Applicant, Application, ApplicationDocument
from .factories import make_job, make_world
from .utils import make_user

_MEDIA = tempfile.mkdtemp(prefix="securats-dateinamen-")


@override_settings(MEDIA_ROOT=_MEDIA)
class RenameLegacyUploadsTestCase(TestCase):
    ALT = "cvs/11111111-2222-3333-4444-555555555555_Lebenslauf_Maria_Schmidt.pdf"

    def setUp(self):
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Maria", lastName="Schmidt",
                                          email="maria@example.invalid")
        self.pfad = default_storage.save(self.ALT, ContentFile(b"%PDF-1.4 inhalt"))
        self.app = Application.objects.create(
            applicant=person, jobPosting=job, status="IN_REVIEW",
            cvStorageId=self.pfad)

    def _lauf(self, *args):
        aus = StringIO()
        call_command("anonymize_upload_names", *args, stdout=aus, stderr=aus)
        return aus.getvalue()

    def test_the_file_loses_the_name_but_not_its_content(self):
        self._lauf()
        self.app.refresh_from_db()
        self.assertNotIn("Maria", self.app.cvStorageId)
        self.assertNotIn("Schmidt", self.app.cvStorageId)
        self.assertTrue(self.app.cvStorageId.endswith(".pdf"))
        self.assertTrue(default_storage.exists(self.app.cvStorageId))
        with default_storage.open(self.app.cvStorageId, "rb") as fh:
            self.assertEqual(fh.read(), b"%PDF-1.4 inhalt")
        self.assertFalse(default_storage.exists(self.pfad),
                         "Die alte Datei muss weg sein - sonst steht der Name "
                         "weiterhin im Verzeichnis.")

    def test_the_display_name_is_kept(self):
        """Sonst hiesse der Download hinterher `a1b2c3....pdf`.

        Erwartet wird der Name aus dem TATSAECHLICH gespeicherten Pfad: Django
        haengt beim Speichern einen Eindeutigkeits-Zusatz an, wenn die Datei
        schon existiert. Auf eine feste Zeichenkette zu pruefen hiesse, ein
        Artefakt der Ablage zu pruefen statt des Verhaltens.
        """
        erwartet = PurePath(self.pfad).name.split("_", 1)[1]
        self._lauf()
        self.app.refresh_from_db()
        self.assertEqual(self.app.cvFileName, erwartet)
        self.assertIn("Maria_Schmidt", self.app.cvFileName)

    def test_a_second_run_changes_nothing(self):
        self._lauf()
        self.app.refresh_from_db()
        vorher = self.app.cvStorageId
        ausgabe = self._lauf()
        self.app.refresh_from_db()
        self.assertEqual(self.app.cvStorageId, vorher)
        self.assertIn("1 bereits namenlos", ausgabe)

    def test_dry_run_touches_nothing(self):
        ausgabe = self._lauf("--dry-run")
        self.app.refresh_from_db()
        self.assertEqual(self.app.cvStorageId, self.pfad)
        self.assertTrue(default_storage.exists(self.pfad))
        self.assertIn("Lebenslauf_Maria_Schmidt.pdf", ausgabe)

    def test_a_missing_file_is_reported_not_rewritten(self):
        """Eine nur vorübergehende Speicher-Störung darf die Zuordnung nicht
        zerstören: Ein neuer Pfad wäre unumkehrbar."""
        default_storage.delete(self.pfad)
        ausgabe = self._lauf()
        self.app.refresh_from_db()
        self.assertEqual(self.app.cvStorageId, self.pfad)
        self.assertIn("fehlen", ausgabe)


@override_settings(MEDIA_ROOT=_MEDIA)
class DownloadKeepsAUsefulNameTestCase(TestCase):
    """Regression: Der Anzeigename kommt aus dem Datensatz, nicht aus dem Pfad.

    Mit der namenlosen Ablage lieferte die alte Ableitung („alles nach dem
    ersten Unterstrich") den Dateinamen `a1b2c3-....pdf` an den Browser.
    """

    def setUp(self):
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Timo", lastName="L",
                                          email="timo-dl@example.invalid")
        pfad = default_storage.save("cvs/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.pdf",
                                    ContentFile(b"%PDF-1.4 x"))
        self.app = Application.objects.create(
            applicant=person, jobPosting=job, status="IN_REVIEW",
            cvStorageId=pfad, cvFileName="Lebenslauf.pdf")
        self.client.force_login(make_user("dl-admin", role="HR-Admin"))

    def test_the_browser_gets_the_original_name(self):
        resp = self.client.get(reverse('ats:download_cv', args=[self.app.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Lebenslauf.pdf", resp["Content-Disposition"])

    def test_without_a_stored_name_the_uuid_is_not_shown_as_the_name(self):
        """Altbestand ohne Anzeigenamen: lieber der Pfadname als gar nichts —
        aber die Zeile darf nicht so tun, als sei das der Name der Datei."""
        self.app.cvFileName = ""
        self.app.save(update_fields=["cvFileName"])
        resp = self.client.get(reverse('ats:download_cv', args=[self.app.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(".pdf", resp["Content-Disposition"])


@override_settings(MEDIA_ROOT=_MEDIA)
class DocumentRenameTestCase(TestCase):
    def setUp(self):
        world = make_world()
        job = make_job(world, title="Pflegefachkraft")
        person = Applicant.objects.create(firstName="Nora", lastName="P",
                                          email="nora-dok@example.invalid")
        app = Application.objects.create(applicant=person, jobPosting=job,
                                         status="IN_REVIEW")
        pfad = default_storage.save(
            "application_docs/99999999-8888-7777-6666-555555555555_Zeugnis_Nora.pdf",
            ContentFile(b"zeugnis"))
        self.doc = ApplicationDocument.objects.create(
            application=app, name="Zeugnis_Nora.pdf", file=pfad, docType="OTHER")

    def test_documents_are_renamed_and_keep_their_label(self):
        call_command("anonymize_upload_names", stdout=StringIO())
        self.doc.refresh_from_db()
        self.assertNotIn("Nora", self.doc.file.name)
        self.assertEqual(self.doc.name, "Zeugnis_Nora.pdf")
        self.assertTrue(default_storage.exists(self.doc.file.name))
        self.assertEqual(PurePath(self.doc.file.name).suffix, ".pdf")
