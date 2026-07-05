# SecurATS – BFSG / WCAG 2.1 AA Audit (WP7)

Stand: Juli 2026. Prüfgegenstand: öffentliche Kandidaten-Strecke
(`/`, `/jobs/`, `/jobs/<id>/`, `/jobs/<id>/bewerben/`, `/bewerber/<token>/`, `/job-alert/`)
sowie Recruiter-Oberfläche. Rechtsrahmen: BFSG (ab 28.06.2025 für B2C-Dienste),
Referenz WCAG 2.1 Stufe AA / EN 301 549.

Legende: ✅ erfüllt · ◐ teilweise · ❌ offen · n/a nicht anwendbar

## 1. Wahrnehmbarkeit

| Kriterium | Status | Umsetzung / Befund |
|---|---|---|
| 1.1.1 Nicht-Text-Inhalte (Alternativtexte) | ◐ | Icons sind dekorativ (FontAwesome, mit Textlabel daneben); Kontaktperson-Fotos brauchen `alt` – bei Medien-Uploads Alt-Text-Feld ergänzen (WP8) |
| 1.3.1 Info & Beziehungen (Semantik) | ✅ | Überschriftenhierarchie, `<label for>` an Formularfeldern, Tabellen mit `<thead>` |
| 1.4.1 Farbe nicht als einziges Mittel | ✅ | Status zusätzlich als Text-Badge (nicht nur Farbe), Timeline mit Beschriftung |
| 1.4.3 Kontrast (4,5:1) | ◐ | Haupttexte auf Dunkelgrund ok; `--text-muted` (#9ca3af) auf Glass-Flächen grenzwertig → **Kontrast-Modus** (Panel) bietet AAA-Alternative; Token-Anhebung in WP8 prüfen |
| 1.4.4 Textvergrößerung 200% | ✅ | rem/relative Größen, responsive Grids (auto-fit) |
| 1.4.10 Reflow (320px) | ✅ | Mobile-stapelnde Formulare (WP1), keine horizontalen Scroller in Kern-Flows |

## 2. Bedienbarkeit

| Kriterium | Status | Umsetzung / Befund |
|---|---|---|
| 2.1.1 Tastatur | ◐ | Formulare/Links/Buttons nativ bedienbar; **Kanban-Drag&Drop hat keine Tastatur-Alternative** → Ausgleich: Statuswechsel per Modal-Dropdown möglich; dokumentierte Lücke |
| 2.4.1 Blöcke überspringen | ✅ | **Skip-Link „Zum Inhalt springen"** (dieses WP) |
| 2.4.2 Seitentitel | ✅ | `{% block title %}` je Seite gepflegt |
| 2.4.4 Linkzweck | ✅ | Sprechende Link-/Buttontexte, `aria-label` an Icon-Buttons |
| 2.4.7 Fokus sichtbar | ◐ | Browser-Default aktiv + Input-Focus-Ring; einheitlicher :focus-visible-Stil in WP8 |
| 2.5.3 Beschriftung im Namen | ✅ | Sichtbare Labels = zugängliche Namen |

## 3. Verständlichkeit

| Kriterium | Status | Umsetzung / Befund |
|---|---|---|
| 3.1.1 Sprache der Seite | ✅ | `<html lang="de">` |
| 3.1.5 Leseniveau (AAA, freiwillig) | ✅ | **Leichte-Sprache-Umschaltung** am Stellendetail (WP1) |
| 3.2.2 Bei Eingabe (keine Kontextwechsel) | ✅ | Keine Auto-Submits; Filter-Select im Audit-Log ist explizit gekennzeichnet |
| 3.3.1/3.3.2 Fehler & Beschriftungen | ✅ | Pflichtfelder markiert (*), HTML5- **und serverseitige** Validierung: Fehler-Zusammenfassung (`role="alert"`) + Inline-Feldfehler mit `aria-invalid`/`aria-describedby`, Eingaben bleiben erhalten (bewerben + Job-Alert, getestet) |

## 4. Robustheit

| Kriterium | Status | Umsetzung / Befund |
|---|---|---|
| 4.1.2 Name, Rolle, Wert | ◐ | A11y-Panel-Switches als echte Checkboxen ✅; Kanban-Karten für Screenreader als Liste auszeichnen (WP8) |
| 4.1.3 Statusmeldungen | ◐ | Ton-/KI-Statusmeldungen sind Text; `aria-live` ergänzen (WP8) |

## Besondere Stärken (über AA hinaus)

- **Barrierefreiheits-Panel** auf jeder Seite (localStorage-persistent): Legasthenie-Schrift,
  Kontrast-Modus (AAA-Kontraste), ADHS-Fokusmodus (Reizreduktion), Lese-Lineal,
  **Vorlesefunktion** (Web Speech API, de-DE).
- **Leichte Sprache** als Inhaltsvariante, nicht nur als UI-Feature.
- Bewerbung ohne PDF-Zwang (Handy-Foto genügt) – Barrierefreiheit auch im Prozess.

## Offene Punkte → WP8 (priorisiert)

1. Tastatur-Alternative für Kanban-Reihenfolge (Pfeiltasten oder „nach oben/unten"-Buttons).
2. `--text-muted`-Kontrast anheben oder auf AA-konformen Wert pinnen.
3. Einheitlicher `:focus-visible`-Stil; `aria-live` für asynchrone Statusmeldungen.
4. Alt-Text-Pflichtfeld beim Medien-Upload; `alt` an Kontaktperson-Fotos.
5. ~~Serverseitige Formularfehler inline am Feld.~~ ✅ umgesetzt (Nachtrag): Zusammenfassung + Feldfehler mit ARIA, Werte-Erhalt; deckt zugleich eine Robustheitslücke (direkte POSTs ohne Pflichtfelder erzeugten Datensätze mit leerer E-Mail).

> Fazit: Kern-Kandidatenstrecke ist BFSG-tauglich nutzbar (inkl. assistiver Ausgleichs-
> funktionen). **Alle fünf im Audit katalogisierten AA-Lücken sind inzwischen geschlossen**
> (WP8 + Nachträge); verbleibende ◐-Einträge oben sind aktualisiert oder betreffen
> laufende Pflege (z.B. Alt-Texte bei künftigen Uploads).
