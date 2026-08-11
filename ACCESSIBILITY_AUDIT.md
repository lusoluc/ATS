# SecurATS – BFSG / WCAG 2.1 AA Audit (WP7)

Stand: Juli 2026. Prüfgegenstand: öffentliche Kandidaten-Strecke
(`/`, `/jobs/`, `/jobs/<id>/`, `/jobs/<id>/bewerben/`, `/bewerber/<token>/`, `/job-alert/`)
sowie Recruiter-Oberfläche. Rechtsrahmen: BFSG (ab 28.06.2025 für B2C-Dienste),
Referenz WCAG 2.1 Stufe AA / EN 301 549.

Legende: ✅ erfüllt · ◐ teilweise · ❌ offen · n/a nicht anwendbar

## 1. Wahrnehmbarkeit

| Kriterium | Status | Umsetzung / Befund |
|---|---|---|
| 1.1.1 Nicht-Text-Inhalte (Alternativtexte) | ✅ | Icons sind dekorativ (FontAwesome, mit Textlabel daneben); Alt-Text beim Medien-Upload Pflicht (HTML `required` + serverseitig erzwungen); Kontaktperson-Fotos mit sprechendem `alt` (Stellendetail, Landingpage, Content-Blöcke) |
| 1.3.1 Info & Beziehungen (Semantik) | ✅ | Überschriftenhierarchie, `<label for>` an Formularfeldern, Tabellen mit `<thead>` |
| 1.4.1 Farbe nicht als einziges Mittel | ✅ | Status zusätzlich als Text-Badge (nicht nur Farbe), Timeline mit Beschriftung |
| 1.4.3 Kontrast (4,5:1) | ✅ | `--text-muted` auf #a6aebc angehoben (WP8); Kandidaten-Portal-Token #94a3b8 auf #0b1220 rechnerisch ~7,3:1 (AA-konform); **Kontrast-Modus** (Panel) bietet zusätzlich AAA |
| 1.4.4 Textvergrößerung 200% | ✅ | rem/relative Größen, responsive Grids (auto-fit) |
| 1.4.10 Reflow (320px) | ✅ | Mobile-stapelnde Formulare (WP1), keine horizontalen Scroller in Kern-Flows |

## 2. Bedienbarkeit

| Kriterium | Status | Umsetzung / Befund |
|---|---|---|
| 2.1.1 Tastatur | ✅ | Formulare/Links/Buttons nativ bedienbar; Kanban vollständig tastaturbedienbar: Karten fokussierbar, Enter/Leertaste öffnet Details, Pfeil hoch/runter sortiert in der Spalte, Pfeil links/rechts wechselt die Spalte (derselbe Server-Pfad wie Drag&Drop, inkl. Einstellungsdatum/Bedenken-Dialog); zusätzlich Hoch/Runter-Buttons an jeder Karte |
| 2.4.1 Blöcke überspringen | ✅ | **Skip-Link „Zum Inhalt springen"** (dieses WP) |
| 2.4.2 Seitentitel | ✅ | `{% block title %}` je Seite gepflegt |
| 2.4.4 Linkzweck | ✅ | Sprechende Link-/Buttontexte, `aria-label` an Icon-Buttons |
| 2.4.7 Fokus sichtbar | ✅ | Einheitlicher globaler `:focus-visible`-Stil (Outline in Akzentfarbe, auch für `[tabindex]`-Elemente wie Kanban-Karten) |
| 2.5.3 Beschriftung im Namen | ✅ | Sichtbare Labels = zugängliche Namen |

## 3. Verständlichkeit

| Kriterium | Status | Umsetzung / Befund |
|---|---|---|
| 3.1.1 Sprache der Seite | ✅ | `<html lang="de">` |
| 3.1.5 Leseniveau (AAA, freiwillig) | ✅ | **Leichte-Sprache-Umschaltung** am Stellendetail (WP1) |
| 3.2.2 Bei Eingabe (keine Kontextwechsel) | ✅ | Keine Auto-Submits. Der Filter im Audit-Log war die letzte Ausnahme (`onchange="this.form.submit()"` — die Zeile hier nannte ihn „gekennzeichnet", was kein Ersatz für Absenden auf Knopfdruck ist) und hat seit dem Audit-Paket einen expliziten „Auswahl anwenden"-Knopf |
| 3.3.1/3.3.2 Fehler & Beschriftungen | ✅ | Pflichtfelder markiert (*), HTML5- **und serverseitige** Validierung: Fehler-Zusammenfassung (`role="alert"`) + Inline-Feldfehler mit `aria-invalid`/`aria-describedby`, Eingaben bleiben erhalten (bewerben + Job-Alert, getestet) |

## 4. Robustheit

| Kriterium | Status | Umsetzung / Befund |
|---|---|---|
| 4.1.2 Name, Rolle, Wert | ✅ | A11y-Panel-Switches als echte Checkboxen; Kanban-Spalten als `role="list"` (mit `aria-label` je Status), Karten als `role="listitem"` |
| 4.1.3 Statusmeldungen | ✅ | `aria-live="polite"` an allen asynchronen KI-Statusregionen (Tonalität, AGG-/Leichte-Sprache-Prüfung, CV-Training, Einladungs-Politur, Analytics); Kanban-Verschiebungen und Vorlese-Status werden über eigene Live-Regionen angesagt |

## Besondere Stärken (über AA hinaus)

- **Barrierefreiheits-Panel** auf jeder Seite (localStorage-persistent): Legasthenie-Schrift,
  Kontrast-Modus (AAA-Kontraste), ADHS-Fokusmodus (Reizreduktion), Lese-Lineal,
  **Vorlesefunktion** (Web Speech API, de-DE).
- **Leichte Sprache** als Inhaltsvariante, nicht nur als UI-Feature.
- Bewerbung ohne PDF-Zwang (Handy-Foto genügt) – Barrierefreiheit auch im Prozess.

## Offene Punkte → WP8 (priorisiert)

1. ~~Tastatur-Alternative für Kanban.~~ ✅ Karten fokussierbar (`tabindex`), Enter öffnet Details, Pfeiltasten sortieren/wechseln Spalte; Hoch/Runter-Buttons; Live-Region sagt Verschiebungen an.
2. ~~`--text-muted`-Kontrast anheben.~~ ✅ #a6aebc; Portal-Token geprüft (~7,3:1, AA).
3. ~~Einheitlicher `:focus-visible`-Stil; `aria-live` für asynchrone Statusmeldungen.~~ ✅ globaler Stil; `aria-live` an allen KI-/Ton-Statusregionen inkl. Vorlesefunktion.
4. ~~Alt-Text-Pflichtfeld beim Medien-Upload; `alt` an Kontaktperson-Fotos.~~ ✅ Pflicht (HTML + Server, getestet); sprechende `alt`-Texte in Landingpage und Content-Blöcken ergänzt.
5. ~~Serverseitige Formularfehler inline am Feld.~~ ✅ umgesetzt (Nachtrag): Zusammenfassung + Feldfehler mit ARIA, Werte-Erhalt; deckt zugleich eine Robustheitslücke (direkte POSTs ohne Pflichtfelder erzeugten Datensätze mit leerer E-Mail).

### Nachtrag: Handy-Durchgang (Paket BS)

Ein dritter Durchgang, diesmal am 375-px-Bildschirm mit einem echten Browser
(`manage.py mobil_pruefen`). Er fand drei Dinge, die zwei Audits übersehen
hatten — alle unsichtbar, solange man am großen Bildschirm entwickelt:

- **„One-Click bewerben" lag außerhalb des Bildes.** Ein deutsches Kompositum
  schob die Grid-Spalte des Stellendetails auf 410 px. Der wichtigste Knopf
  des Produkts, auf dem Gerät, mit dem sich die Zielgruppe bewirbt.
- **Der Barrierefreiheits-Knopf war unerreichbar.** Die nicht umbrechende
  Footer-Zeile machte das Dokument 529 px breit; der Knopf steht
  `position:fixed; right:30px` und rechnete gegen diese 529 px.
- **„KI-Transparenz" im Footer war abgeschnitten** — der Link, den EU AI Act
  Art. 86 verlangt.
- Dazu: Menü-Knopf 19 × 27 px statt mindestens 24 × 24 (WCAG 2.5.8).

Lehre für künftige Audits: `body { overflow-x: hidden }` verwandelt jeden
Überstand in **unsichtbaren Verlust**. Eine Sichtprüfung am Telefon zeigt
nicht, was fehlt — man sieht ja nur, was da ist. Deshalb misst der Wächter die
Elementkanten gegen die Fensterbreite, statt Bilder zu vergleichen.

> Fazit (aktualisiert 04.08.2026): Die im Erst-Audit katalogisierten Lücken sind
> geschlossen. Eine ZWEITE, tiefere Inventur (Paket B1–B7) fand und behob weitere
> Defekte, die das Erst-Audit übersehen hatte — u. a. Panel-Switches ohne
> zugänglichen Namen, das Kandidatenportal ohne Panel/Skip-Link/Fokus-Stil,
> fehlende autocomplete-Attribute (WCAG 1.3.5), fehlendes prefers-reduced-motion,
> ein ungestylter Absende-Knopf auf /bewerben/ und eine Leichte-Sprache-Funktion
> ohne Befüllungsweg. Konsequenz für künftige Aussagen: Der verbindliche Status
> steht in der COMPLIANCE_MATRIX (BFSG/WCAG: ◐ bis zum externen Vollaudit, WP7);
> dieses Dokument ist das Arbeitsprotokoll, keine Konformitätsbehauptung.
> Öffentliche Erklärung zur Barrierefreiheit: `/barrierefreiheit/` (ehrlich
> „teilweise vereinbar"). Laufende Pflege: Wächter-Tests (autocomplete,
> Auth-Allowlist, Tabellen-Wrapper, Template-Kommentare) + neue Views gegen die
> globalen Fokus-/Live-Region-Muster prüfen.
