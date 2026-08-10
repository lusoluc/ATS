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

#: TEIL 3 - Wenn mehrere mitreden.
TEIL3: list[Bild] = [
    Bild("70-gremien", "/recruiter/gremien/", "HR-Admin",
         "Auswahlgremien: wer bei welcher Art Stelle mitentscheidet",
         templates=("panel_defaults.html",)),
    Bild("71-vertretung", "/recruiter/delegations/", "Hiring-Manager",
         "Vertretungen: wer wen wie lange vertritt",
         templates=("delegations.html",)),
    Bild("72-governance", "/recruiter/governance/", "Hiring-Manager",
         "Governance-Übersicht: Entscheidungswege und ihre Nachweise",
         templates=("governance.html",)),
]

#: TEIL 4 - Einrichten.
TEIL4: list[Bild] = [
    Bild("80-einstellungen", "/recruiter/einstellungen/", "HR-Admin",
         "Einstellungs-Zentrale: alle Einrichtungsbereiche mit ihrem Zustand",
         templates=("admin_pages/settings_hub.html",)),
    Bild("81-standorte", "/recruiter/locations/", "HR-Admin",
         "Standorte anlegen und pflegen",
         templates=("locations.html",)),
    Bild("82-prozess", "/recruiter/prozess-flow/", "HR-Admin",
         "Prozessablauf: die Schritte, die jede Bewerbung durchläuft",
         templates=("admin_pages/process.html",)),
    Bild("83-fragen", "/recruiter/screening-questions/", "HR-Admin",
         "Fragen-Baukasten: wiederverwendbare Fragen an Bewerbende",
         templates=("screening_questions.html",)),
    Bild("84-entgeltbaender", "/recruiter/pay-bands/", "HR-Admin",
         "Entgeltbänder: Gehaltsspannen je Tätigkeit",
         templates=("pay_bands.html",)),
    Bild("85-mailvorlagen", "/recruiter/email-vorlagen/", "HR-Admin",
         "E-Mail-Vorlagen für wiederkehrende Nachrichten",
         templates=("admin_pages/templates.html",)),
    Bild("86-mailversand", "/recruiter/einstellungen/email/", "HR-Admin",
         "E-Mail-Versand einrichten und die Verbindung prüfen",
         templates=("admin_pages/mail_settings.html",)),
    Bild("87-ki", "/recruiter/ki-zentrale/", "HR-Admin",
         "KI-Zentrale: Vorbewertung ein- oder ausschalten und testen",
         templates=("admin_pages/ki.html",)),
]

#: TEIL 5 - Wenn etwas klemmt.
TEIL5: list[Bild] = [
    Bild("90-jobs", "/recruiter/einstellungen/jobs/", "HR-Admin",
         "Wiederkehrende Jobs: was laufen soll und was wirklich lief",
         templates=("admin_pages/scheduled_jobs.html",)),
]

#: TEIL 6 - Was das System für Sie erledigt.
TEIL6: list[Bild] = [
    Bild("95-aufbewahrung", "/recruiter/datenaufbewahrung/", "HR-Admin",
         "Datenaufbewahrung: Fristen und der Trockenlauf vor dem Löschen",
         templates=("admin_pages/retention.html",)),
    Bild("96-nachweis", "/recruiter/audit/", "HR-Admin",
         "Nachweis-Protokoll: lückenlose Kette aller Entscheidungen",
         templates=("audit_log.html",)),
    Bild("97-auswertung", "/recruiter/analytics/", "Recruiter",
         "Auswertung: Kennzahlen und daraus abgeleitete Hinweise",
         templates=("analytics.html",)),
]

#: TEIL 4 (Fortsetzung) - die restlichen Einrichtungsseiten.
TEIL4B: list[Bild] = [
    Bild("88-ansprechpartner", "/recruiter/contacts/", "HR-Admin",
         "Ansprechpartner, die auf Stellenanzeigen genannt werden",
         templates=("contacts.html",)),
    Bild("89-jobfamilien", "/recruiter/categories/", "HR-Admin",
         "Jobfamilien: die fachliche Gliederung der Stellen",
         templates=("categories.html",)),
    Bild("89b-kanaele", "/recruiter/kanaele/", "HR-Admin",
         "Herkunftskanäle: woher Bewerbungen kommen",
         templates=("source_channels.html",)),
    Bild("89c-vorlagen", "/recruiter/job-templates/", "HR-Admin",
         "Stellen-Vorlagen für wiederkehrende Ausschreibungen",
         templates=("job_templates.html",)),
    Bild("89d-datenschutzhinweis", "/recruiter/datenschutzhinweis/", "HR-Admin",
         "Versionen des Datenschutzhinweises für Bewerbende",
         templates=("admin_pages/privacy_notice.html",)),
    Bild("89e-import", "/recruiter/import/", "HR-Admin",
         "Stammdaten aus einer Tabelle einlesen",
         templates=("import.html",)),
]

#: TEIL 7 - Die eigene Karriereseite.
TEIL7: list[Bild] = [
    Bild("A0-erscheinungsbild", "/recruiter/branding/", "HR-Admin",
         "Erscheinungsbild: Farben, Logo, helle oder dunkle Darstellung",
         templates=("branding.html",)),
    Bild("A1-seiten", "/recruiter/pages/", "HR-Admin",
         "Seiten der Karriereseite bearbeiten",
         templates=("pages_manage.html",)),
    Bild("A2-mediathek", "/recruiter/media/", "HR-Admin",
         "Mediathek: Bilder für Karriereseite und Anzeigen",
         templates=("media_manage.html",)),
    Bild("A3-textbausteine", "/recruiter/snippets/", "HR-Admin",
         "Textbausteine, die auf mehreren Seiten wiederverwendet werden",
         templates=("snippets.html",)),
    Bild("A4-landingpages", "/recruiter/landingpages/", "HR-Admin",
         "Kampagnen-Landingpages für gezielte Ansprache",
         templates=("landing_pages_manage.html",)),
]

#: TEIL 8 - Auswertung und Schnittstellen.
TEIL8: list[Bild] = [
    Bild("B0-kennzahlen", "/recruiter/kpis/", "HR-Admin",
         "Kennzahlen-Übersicht des Recruitings",
         templates=("admin_pages/stats.html",)),
    Bild("B1-talentpool", "/recruiter/talent-pool/", "Recruiter",
         "Talent-Pool: Menschen, die einer späteren Ansprache zugestimmt haben",
         templates=("talent_pool.html",)),
    Bild("B2-lernendes-scoring", "/recruiter/lernendes-scoring/", "HR-Admin",
         "Lernendes Scoring: Messstrecke und Freigabe-Stand",
         templates=("admin_pages/learned_scoring.html",)),
    Bild("B3-hris", "/recruiter/hris/", "HR-Admin",
         "HRIS-Anbindung: Übergabe an das Personalsystem",
         templates=("admin_pages/hris.html",)),
]

#: TEIL 9 - Was Bewerbende sehen.
TEIL9: list[Bild] = [
    Bild("C0-karriereseite", "/", "-",
         "Die öffentliche Startseite der Karriereseite",
         templates=("home.html",)),
    Bild("C1-stellenliste", "/jobs/", "-",
         "Die öffentliche Stellenliste mit Filtern",
         templates=("job_list.html",)),
    Bild("C2-jobalert", "/job-alert/", "-",
         "Anmeldung für Benachrichtigungen über neue Stellen",
         templates=("job_alert.html",)),
]

ALLE: list[Bild] = (TEIL1 + TEIL2 + TEIL3 + TEIL4 + TEIL4B + TEIL5 + TEIL6
                    + TEIL7 + TEIL8 + TEIL9)


#: Seite (URL-Name) -> Kapitel, das sie erklaert. Der Waechter prueft, dass
#: das genannte Kapitel im Handbuch wirklich existiert - eine Zuordnung auf
#: ein erfundenes Kapitel waere schlimmer als gar keine.
ERKLAERT_IN = {
    "login": "1.1 Anmelden",
    "dashboard": "1.2 Was Sie jetzt sehen",
    "global_search": "1.4 Jemanden suchen",
    "hilfe": "1.3 Das Menü",
    "inbox": "Weg 4",
    "interviews": "Weg 5",
    "approvals": "Weg 6",
    "staffing_requests": "Weg 6",
    "panel_defaults": "3.2 Auswahlgremien",
    "delegations": "3.3 Vertretung",
    "governance": "3.4 Der Überblick",
    "settings_hub": "4.1 Die Einstellungs-Zentrale",
    "locations": "4.2 Standorte und Einrichtungen",
    "process_page": "4.3 Der Prozessablauf",
    "screening_questions": "4.4 Fragen an Bewerbende",
    "pay_bands": "4.5 Entgeltbänder",
    "templates_page": "4.6 E-Mail-Vorlagen",
    "mail_settings": "4.7 E-Mail-Versand",
    "ki_page": "4.8 KI ein- oder ausschalten",
    "scheduled_jobs": "5.1 Der zentrale Blick",
    "healthz": "5.5 Wenn gar nichts geht",
    "retention": "6.1 Löschfristen",
    "audit_log": "6.2 Jede Entscheidung ist belegbar",
    "analytics": "6.3 Auswertung ohne Namen",
    "ai_transparency": "6.4 Was Bewerbende sehen dürfen",
    "accessibility_statement": "6.4 Was Bewerbende sehen dürfen",
    "candidate_portal": "6.4 Was Bewerbende sehen dürfen",
    "tasks": "4.3 Der Prozessablauf",
    "contacts": "4.9 Ansprechpartner",
    "categories": "4.10 Jobfamilien",
    "source_channels": "4.11 Herkunftskanäle",
    "job_templates": "4.12 Stellen-Vorlagen",
    "interview_formats": "4.13 Gesprächsformate",
    "privacy_notice": "4.14 Datenschutzhinweis",
    "data_import": "4.15 Stammdaten einlesen",
    "branding": "7.1 Erscheinungsbild",
    "pages_manage": "7.2 Seiten",
    "media_manage": "7.3 Mediathek",
    "snippets": "7.4 Textbausteine",
    "landing_pages": "7.5 Kampagnen-Landingpages",
    "stats_page": "8.1 Kennzahlen",
    "talent_pool": "8.2 Talent-Pool",
    "learned_scoring": "8.3 Lernendes Scoring",
    "best_performer_profiles": "8.4 Vergleichsprofile",
    "ingest_best_performers": "8.4 Vergleichsprofile",
    "hris_page": "Teil 9 — Anbindung an andere Systeme",
    "sap_sf_mapper": "Teil 9 — Anbindung an andere Systeme",
    "stepstone_feed": "Teil 9 — Anbindung an andere Systeme",
    "hr_ba_xml_feed": "Teil 9 — Anbindung an andere Systeme",
    "home": "Teil 10 — Was Bewerbende sehen",
    "job_list": "Teil 10 — Was Bewerbende sehen",
    "job_alert": "Teil 10 — Was Bewerbende sehen",
}


def _repo() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def template_hash(namen: tuple[str, ...]) -> str:
    """Ein Hash über alle Vorlagen eines Bildes.

    Fehlt eine Vorlage, fliesst das als Marke ein - dann faellt auch eine
    UMBENANNTE Vorlage auf, statt still durchzurutschen.

    ZEILENENDEN werden vorher vereinheitlicht. Ohne das haengt der Hash am
    Betriebssystem: Git checkt auf Windows mit CRLF aus, auf dem Linux-Runner
    mit LF - derselbe Inhalt, andere Bytes. Der Waechter meldete daraufhin in
    der CI ALLE Bilder als veraltet, waehrend lokal keins auffiel. Ein
    Waechter, der je nach Rechner etwas anderes sagt, ist wertlos.
    """
    h = hashlib.sha256()
    wurzel = _repo() / "templates"
    for name in sorted(namen):
        datei = wurzel / name
        h.update(name.encode())
        if datei.exists():
            inhalt = datei.read_bytes().replace(b"\r\n", b"\n")
        else:
            inhalt = b"<fehlt>"
        h.update(inhalt)
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
