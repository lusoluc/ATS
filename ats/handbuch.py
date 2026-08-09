"""Das Benutzerhandbuch — und der Nachweis, dass es die Wahrheit zeigt.

Ein Handbuch verrottet aus demselben Grund, aus dem Code lügt: Niemand merkt
es. Deshalb steht hier die Bildliste als DATEN — jedes Bild kennt die Seite,
die es zeigt, die Rolle, die es sieht, und die Vorlagen, aus denen es
entstanden ist. Daraus ergibt sich beides:

* `manage.py handbuch_bilder` kann die Bilder jederzeit neu schießen.
* Ein Wächter prüft, ob eine Vorlage sich seit dem letzten Schuss geändert
  hat (Hash im Manifest) — dann ist das Bild veraltet und der Testlauf rot.
  Das Dateidatum taugt dafür nicht: Git setzt es beim Auschecken neu.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass, field

#: Wohin die Bilder gehoeren (relativ zum Repo).
BILDER_ORDNER = "docs/handbuch"

#: Manifest mit den Vorlagen-Hashes je Bild.
MANIFEST = f"{BILDER_ORDNER}/bilder.json"

#: Breite/Hoehe der Aufnahmen. Desktop, weil das Handbuch gedruckt und am
#: Rechner gelesen wird; mobile Ansichten haben eigene Bilder (siehe `mobil`).
BREITE, HOEHE = 1280, 860


@dataclass(frozen=True)
class Bild:
    """Ein Screenshot: was er zeigt und wer ihn sieht."""

    name: str                       # Dateiname ohne Endung
    pfad: str                       # URL-Pfad in der Anwendung
    rolle: str                      # HR-Admin | Recruiter | Hiring-Manager | Viewer | -
    beschreibung: str               # Alt-Text im Handbuch (Barrierefreiheit!)
    #: Vorlagen, aus denen die Seite entsteht. Aendert sich eine, ist das
    #: Bild veraltet - genau das prueft der Waechter.
    templates: tuple[str, ...] = ()
    #: Optionaler CSS-Selektor: nur diesen Ausschnitt aufnehmen statt der
    #: ganzen Seite (fuer Detailbilder eines einzelnen Bedienelements).
    ausschnitt: str | None = None
    mobil: bool = False
    #: Vor der Aufnahme auszufuehrende Klicks (CSS-Selektoren).
    klicks: tuple[str, ...] = field(default_factory=tuple)

    @property
    def datei(self) -> str:
        return f"{BILDER_ORDNER}/{self.name}.png"


#: Der Menuepunkt „Stellen" ist kein eigener Bildschirm, sondern ein Reiter
#: der Startseite - deshalb ein Klick statt einer eigenen Adresse.
KLICK_STELLEN = ("[onclick*=\"jobs-tab\"]",)

#: TEIL 1 - Die ersten 20 Minuten.
TEIL1: list[Bild] = [
    Bild("01-anmeldung", "/recruiter/login/", "-",
         "Anmeldeseite von SecurATS mit den Feldern Benutzername und Passwort",
         templates=("registration/login.html",)),
    Bild("02-startseite", "/recruiter/dashboard/", "Recruiter",
         "Startseite nach der Anmeldung: oben die Suche, links das Menü, "
         "in der Mitte das Board mit den Bewerbungen",
         templates=("dashboard.html", "base.html")),
    Bild("03-suche", "/recruiter/dashboard/", "Recruiter",
         "Das Suchfeld oben im Kopfbereich, mit dem sich Personen, "
         "E-Mail-Adressen und Stellen finden lassen",
         templates=("base.html",), ausschnitt="header"),
    Bild("04-menue", "/recruiter/dashboard/", "Recruiter",
         "Das Menü am linken Rand mit allen Bereichen",
         templates=("dashboard.html",), ausschnitt=".dashboard-sidebar"),
    Bild("05-startseite-mobil", "/recruiter/dashboard/", "Recruiter",
         "Dieselbe Startseite auf dem Mobiltelefon",
         templates=("dashboard.html", "base.html"), mobil=True),
]

#: TEIL 2 - Die sechs Wege durch den Alltag.
TEIL2: list[Bild] = [
    # Weg 1+2: Stelle anlegen, aendern, veroeffentlichen
    Bild("10-stellen-liste", "/recruiter/dashboard/", "Recruiter",
         "Übersicht aller Stellen mit Status und Bewerbungszahl",
         templates=("includes/dashboard/tab_jobs.html",), klicks=KLICK_STELLEN),
    # Weg 3: Bewerbungen sichten
    Bild("30-board", "/recruiter/dashboard/", "Recruiter",
         "Das Board: jede Spalte ein Schritt im Verfahren, jede Karte eine "
         "Bewerbung",
         templates=("includes/dashboard/tab_kanban.html",)),
    # Weg 4: Kommunikation
    Bild("40-postfach", "/recruiter/postfach/", "Recruiter",
         "Sammel-Postfach: offene Fragen der Bewerbenden nach Thema gruppiert",
         templates=("inbox.html",)),
    # Weg 5: Gespraeche
    Bild("50-termine", "/recruiter/interviews/", "Recruiter",
         "Terminübersicht mit den geplanten Gesprächen",
         templates=("interviews.html",)),
    # Weg 6: Entscheiden
    Bild("60-freigaben", "/recruiter/approvals/", "Hiring-Manager",
         "Freigabe-Postfach: Vorgänge, die auf eine Entscheidung warten",
         templates=("approvals.html",)),
    Bild("61-bedarf", "/recruiter/bedarf/", "Hiring-Manager",
         "Personalbedarf melden und den Stand der eigenen Meldungen sehen",
         templates=("staffing_requests.html",)),
]

ALLE: list[Bild] = TEIL1 + TEIL2


def _repo() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def template_hash(namen: tuple[str, ...]) -> str:
    """Ein Hash über alle Vorlagen eines Bildes.

    Fehlt eine Vorlage, fliesst das als Marke ein - dann faellt auch eine
    UMBENANNTE Vorlage auf, statt still durchzurutschen.
    """
    h = hashlib.sha256()
    wurzel = _repo() / "templates"
    for name in sorted(namen):
        datei = wurzel / name
        h.update(name.encode())
        h.update(datei.read_bytes() if datei.exists() else b"<fehlt>")
    return h.hexdigest()[:16]


def manifest_lesen() -> dict[str, str]:
    pfad = _repo() / MANIFEST
    if not pfad.exists():
        return {}
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in daten.items()}


def manifest_schreiben(eintraege: dict[str, str]) -> None:
    pfad = _repo() / MANIFEST
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(
        json.dumps(eintraege, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8")


def veraltete_bilder() -> list[str]:
    """Bilder, deren Vorlage sich seit der Aufnahme geändert hat."""
    manifest = manifest_lesen()
    veraltet = []
    for bild in ALLE:
        if not bild.templates:
            continue
        if manifest.get(bild.name) != template_hash(bild.templates):
            veraltet.append(bild.name)
    return veraltet
