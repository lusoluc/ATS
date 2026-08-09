"""Hochgeladene Dateien namenlos ablegen — auch den Altbestand.

Bis zum Verschluesselungs-Paket landeten Uploads als `<uuid>_<Originalname>`
in der Ablage. Der Originalname lautet typischerweise
`Lebenslauf_Maria_Schmidt.pdf`: Damit stand der Name der bewerbenden Person im
Klartext im Dateisystem und in der Spalte `cvStorageId` - waehrend
`firstName`/`lastName` derselben Person Fernet-verschluesselt lagen. Ein
Verzeichnis-Listing des Medienordners war eine Namensliste.

Neue Uploads sind bereits namenlos. Dieses Kommando zieht den Bestand nach.

WICHTIG: Der Anzeigename geht nicht verloren. Er wird VOR dem Umbenennen aus
dem alten Pfad gelesen und verschluesselt im Datensatz abgelegt
(`Application.cvFileName`, `ApplicationDocument.name`) - sonst hiesse der
Download hinterher `a1b2c3....pdf`.
"""
from pathlib import PurePath
from uuid import UUID, uuid4

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from ats.models import Application, ApplicationDocument


def _ist_schon_namenlos(pfad: str) -> bool:
    """Heisst die Datei bereits `<uuid><endung>`?"""
    stamm = PurePath(pfad).stem
    try:
        UUID(stamm)
    except (ValueError, AttributeError):
        return False
    return True


def _anzeigename(pfad: str) -> str:
    """Der Originalname aus `<uuid>_<Originalname>` - oder der Dateiname."""
    name = PurePath(pfad).name
    return name.split("_", 1)[1] if "_" in name else name


def _neuer_pfad(pfad: str) -> str:
    p = PurePath(pfad)
    endung = p.suffix.lower()[:10]
    if not endung.replace(".", "").isalnum():
        endung = ""
    return str(PurePath(p.parent) / f"{uuid4()}{endung}").replace("\\", "/")


class Command(BaseCommand):
    help = ("Benennt bereits hochgeladene Dateien in `<uuid><endung>` um und "
            "sichert den Anzeigenamen verschluesselt im Datensatz.")

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Nur zeigen, was passieren wuerde - nichts aendern.")

    def _umbenennen(self, alt: str) -> str | None:
        """Kopieren, pruefen, altes loeschen. Gibt den neuen Pfad zurueck.

        Bewusst kopieren statt `os.rename`: Ein Fremd-Storage (S3, MinIO) kennt
        kein Umbenennen im Dateisystem. Geloescht wird erst, wenn die Kopie
        nachweislich liegt - ein abgebrochener Lauf darf keine Datei verlieren.
        """
        neu = _neuer_pfad(alt)
        with default_storage.open(alt, "rb") as fh:
            gespeichert = default_storage.save(neu, ContentFile(fh.read()))
        if not default_storage.exists(gespeichert):
            return None
        default_storage.delete(alt)
        return gespeichert

    def handle(self, *args, **options):
        trocken = options["dry_run"]
        umbenannt = fehler = uebersprungen = ohne_datei = 0
        fehlend: list[str] = []

        def bearbeiten(objekt, pfad_feld: str, namen_feld: str):
            nonlocal umbenannt, fehler, uebersprungen, ohne_datei
            alt = getattr(objekt, pfad_feld)
            alt = getattr(alt, "name", alt)          # FileField oder CharField
            if not alt:
                ohne_datei += 1
                return
            if _ist_schon_namenlos(alt):
                uebersprungen += 1
                return
            if not default_storage.exists(alt):
                # Bewusst NICHT umschreiben: Waere der Speicher nur
                # voruebergehend nicht erreichbar, wuerde ein neuer Pfad die
                # Zuordnung zur Datei endgueltig zerstoeren. Lieber melden und
                # beim naechsten Lauf erneut versuchen.
                fehlend.append(alt)
                return
            name = getattr(objekt, namen_feld, "") or _anzeigename(alt)
            if trocken:
                self.stdout.write(f"  {alt} -> <uuid>{PurePath(alt).suffix} "
                                  f"(Anzeigename: {name})")
                umbenannt += 1
                return
            try:
                neu = self._umbenennen(alt)
                if neu is None:
                    raise OSError("Kopie nicht auffindbar")
                setattr(objekt, namen_feld, name[:255])
                setattr(objekt, pfad_feld, neu)
                objekt.save(update_fields=[pfad_feld, namen_feld])
                umbenannt += 1
            except Exception as exc:            # noqa: BLE001 - je Datei weiter
                fehler += 1
                self.stdout.write(self.style.ERROR(f"  {alt}: {exc}"))

        self.stdout.write("Lebenslaeufe ...")
        # `exclude(feld__in=["", None])` laesst NULL-Zeilen durch: In SQL ist
        # `NOT IN (..., NULL)` fuer NULL selbst wieder NULL, also nicht wahr -
        # die Zeile wird nicht ausgeschlossen. Deshalb ausdruecklich beides.
        for app in (Application.objects
                    .exclude(cvStorageId__isnull=True).exclude(cvStorageId="")
                    .iterator(chunk_size=200)):
            bearbeiten(app, "cvStorageId", "cvFileName")

        self.stdout.write("Nachweise ...")
        for doc in ApplicationDocument.objects.all().iterator(chunk_size=200):
            bearbeiten(doc, "file", "name")

        art = "waeren umzubenennen" if trocken else "umbenannt"
        self.stdout.write(self.style.SUCCESS(
            f"{umbenannt} {art}, {uebersprungen} bereits namenlos, "
            f"{ohne_datei} ohne hinterlegte Datei, {fehler} fehlgeschlagen."))
        if fehlend:
            self.stdout.write(self.style.WARNING(
                f"{len(fehlend)} Datensaetze verweisen auf Dateien, die in der "
                f"Ablage fehlen - unveraendert gelassen, damit eine nur "
                f"voruebergehende Speicher-Stoerung die Zuordnung nicht "
                f"zerstoert:"))
            for pfad in fehlend[:20]:
                self.stdout.write(f"  {pfad}")
        if fehler:
            self.stdout.write(self.style.WARNING(
                "Fehlgeschlagene Dateien behalten ihren alten Namen - ein "
                "erneuter Lauf nimmt sie wieder mit."))
