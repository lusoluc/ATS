# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/de/), Versionierung: [SemVer](https://semver.org/lang/de/).
Update-Pfad: `docker compose pull && docker compose up -d` (Migrationen laufen automatisch, siehe INSTALL.md).

## [Unreleased]

### Hinzugefügt
- **Prozess-Automatik: echte Aktionen statt „nicht implementiert".** Die
  Automatik führte bisher nur Bewerber-Mails aus; alles andere – auch das
  Beispiel im eigenen Konfigurations-Feld – wurde stillschweigend
  übersprungen. Neu wirken:
  - `CREATE_TASK` – **Aufgabe/Erinnerung** an eine *Rolle* (nicht an eine
    Person, damit Urlaub sie nicht verwaisen lässt), optional mit Frist.
    Neue Seite „Aufgaben" mit Überfälligkeits-Markierung, Erledigen und
    Wieder-Öffnen; Badge in der Navigation.
  - `EMAIL_NOTIFICATION` an **interne** Empfänger (feste Adresse und/oder alle
    Mitglieder einer Rolle) – bisher wirkte nur der Bewerber-Fall.
  - `ADD_NOTE` – automatischer, gekennzeichneter Vermerk in den internen Notizen.
  - `AUTO_ADVANCE` – **Status-Autovorlauf** innerhalb der Sichtung.
- **Compliance-Grenze im Autovorlauf (Human-in-the-Loop):** `AUTO_ADVANCE` kann
  ausschließlich nach NEW / IN_REVIEW / INVITED schieben. **Zu- und Absagen sind
  hart gesperrt** – sie bleiben der menschlichen Entscheidung vorbehalten
  (`.agents/AGENTS.md`). Ein blockierter Versuch wird als
  `WORKFLOW_ACTION_BLOCKED` protokolliert. Der Autovorlauf löst außerdem keine
  Folge-Automatik aus (keine Ketten, keine Endlosschleifen) – beides getestet.

- **No-Code-Editor für die Prozess-Automatik.** Das rohe JSON-Textfeld ist durch
  einen Baukasten ersetzt: „Wenn *Phase* → dann *Aktion*" mit Auswahllisten und
  passenden Feldern je Aktionstyp. Das JSON entsteht daraus automatisch; für
  Fortgeschrittene bleibt es aufklappbar sichtbar und von Hand überschreibbar.
  Beim Bearbeiten einer Regel werden die Felder zurückbefüllt.
- Die Human-in-the-Loop-Grenze steht jetzt sichtbar im Formular; der
  Autovorlauf bietet Zusage/Absage gar nicht erst zur Auswahl an.

### Behoben
- **HRIS-Export täuschte Erfolg vor (schwerwiegend).** `hris_export` stellte
  **nie** eine HTTP-Anfrage. Es baute eine Schein-Antwort, schrieb eine **frei
  erfundene SAP-ID** in die Bewerberakte und protokollierte
  `HRIS_EXPORT_SUCCESS` mit `"target": "SAP_SF_PRODUCTION"` im **Audit-Log** –
  dem Compliance-Nachweis, der nicht lügen darf. Betreiber hätten geglaubt,
  Bewerberdaten seien an SAP übertragen worden; übertragen wurde nichts.
  Neu: echte Übertragung (HTTP POST, Timeout, Statusprüfung) bei gesetztem
  `HRIS_ENDPOINT`; **ohne Konfiguration bricht der Befehl ab** statt zu
  simulieren; `--dry-run` zeigt die Struktur ohne PII; protokolliert wird nur
  das *tatsächliche* Ergebnis (echte Referenz oder gar keine). Regressions-Wache
  im Test verhindert die Rückkehr der Schein-Antwort.
- **Eingangsbestätigung fehlte komplett.** Die Erfolgsseite versprach „Sie
  erhalten in Kürze eine Bestätigung per E-Mail" – es wurde **keine** verschickt.
  Gravierender: Der Magic-Link zum Kandidatenportal stand nur auf dieser einen
  Seite. Wer den Tab schloss, kam **nie wieder** ins Portal (Status, Termine,
  Rückfragen) – das Feature war praktisch unbenutzbar. Neu: Bestätigungsmail mit
  Portal-Link (Vorlage „Eingangsbestätigung" mit `{name}`, `{stelle}`, `{firma}`,
  `{portal}` wird genutzt, wenn vorhanden), auditiert. Ein Mailfehler lässt die
  Bewerbung nicht scheitern (getestet).
- **Irreführende Standard-Vorbelegung entfernt.** Wurde eine Automatik-Regel ohne
  eigene Aktionen angelegt, erzeugte SecurATS Aktionen, die es **nie gab**
  (`AUTO_INVITE_INTERVIEW`, `TRIGGER_PROCESS` mit „CALENDAR_SYNC"/„ZOOM_ROOM_CREATE",
  `SEND_CONTRACT`). Ein Admin sah „Vertrag senden" in seiner Pipeline – ausgeführt
  wurde nichts. Die Vorbelegung nutzt jetzt ausschließlich Aktionen, die
  tatsächlich wirken (Vermerk, Aufgabe, Absage-Mail); zwei Tests verhindern
  einen Rückfall.
- Werbetext „ausgereifte Standard-Automatisierungen … Vertragsentwürfe" entfernt –
  er versprach Funktionen, die nicht existierten.

### Geändert
- Migration `0042` (Modell `WorkflowTask`).
- Unbekannte Aktionstypen werden weiterhin **ehrlich übersprungen** statt
  Erfolg zu simulieren – nur der Audit-Wortlaut wurde präzisiert.

## [1.7.0] – 2026-07-05

Reife-Release der Stellenfreigabe: Vertretung, parallele Stufen,
Genehmiger-Sichtbarkeit und die Engpass-Kennzahl machen den Prozess
alltagstauglich für echte Organisationen – vom Teamleiter bis zum
Aufsichtsrat, auch im Urlaubsfall.
Update: `docker compose pull && docker compose up -d` (Migration 0039).

### Hinzugefügt
- **Vertretung in der Freigabekette („i. V.")**: Aktive Vertretungen
  (bestehende Delegations-Mechanik) dürfen die fällige Stufe entscheiden;
  Zeitfenster und Einrichtungs-Scope serverseitig geprüft, stellenscharfe
  Vertretungen decken Bedarf bewusst nicht; jede Vertretungs-Entscheidung
  sichtbar gekennzeichnet und im Audit mit dem Vertretenen protokolliert.
- **Vertretungs-Selbstbedienung**: Jede interne Rolle legt ihre eigene
  Vertretung selbst an und beendet sie (vorher nur HR-Admin); Nicht-Admins
  sehen nur eigene erteilte/erhaltene Vertretungen; HR-Admin kann im
  Assistenz-Fall im Namen einer anderen Person anlegen (auditiert).
- **Parallele Genehmigungsstufen**: Ketten-Syntax „+" schaltet Rollen
  einer Stufe parallel („Controlling + Betriebsrat"); alle müssen
  genehmigen (Reihenfolge frei), eine Rückgabe stoppt den Antrag; ohne
  „+" exakt das bisherige sequenzielle Verhalten.
- **Engpass-Kennzahl je Freigabestufe**: Analytics-Karte „Welche Stufe
  bremst?" mit Ø Wartetagen je Rolle (fällig → entschieden), aktuell
  fälligen offenen Anträgen und Engpass-Badge; parallele Gruppen korrekt
  berücksichtigt (Fälligkeit ab letzter Vorgruppen-Entscheidung).

### Behoben
- **Genehmiger-Sichtbarkeit**: Ketten-Rollen (Bereichsleitung, Vorstand …)
  ohne Recruiter-Rolle sahen die Eingangs-Liste nicht, obwohl sie
  entscheiden durften; jetzt sehen sie ihre fälligen und selbst
  entschiedenen Anträge.
- **Assistenz-Anlage von Vertretungen**: Die Anlage durch HR-Admin erzeugte
  bisher eine Vertretung, die vom Admin selbst ausging (funktional falsch
  für Ketten-Rollen); der Vertretene ist jetzt wählbar.

## [1.6.0] – 2026-07-05

Governance-Release: Der komplette Weg VOR der Ausschreibung ist jetzt
abbildbar – vom beantragten Personalbedarf über konfigurierbare
Genehmigungsketten bis zur formalen Gesprächsrunden-Pflicht vor der
Einstellung. Optional je Installation, aber wenn aktiviert, verbindlich.
Update: `docker compose pull && docker compose up -d` (Migrationen 0034–0038).

### Hinzugefügt
- **Stellenfreigabe (vorgeschalteter Genehmigungsprozess)**: Teamleitung bis
  Aufsichtsrat beantragen Personalbedarf; sequenzielle, je Einrichtung oder
  global konfigurierbare Genehmigungskette (Rollen = frei anlegbare Gruppen);
  drei Ausgänge je Stufe (Genehmigen / Zur Nachbesserung mit Neustart /
  endgültig Ablehnen); Mail an Antragsteller; Stufenleiste am Antrag;
  optional per Schalter – wenn aktiv, ist Veröffentlichen ohne genehmigten
  Bedarf an allen drei Schaltpunkten blockiert (Wizard, Schnell-Toggle,
  finale Job-Freigabe).
- **No-Code Routing-Matrix**: Regeln verknüpfen Geltungsbereich (Einrichtung ×
  Abteilung × Job-Kategorie, Wildcards möglich) mit eigenem Bedarfsformular
  (dynamische Zusatzfragen: Freitext/Auswahl/Ja-Nein) und eigener
  Genehmigungskette; spezifischste Regel gewinnt (exakt > teilweise >
  Fallback); Pflicht je Regel wirkt auch ohne globalen Schalter; Antworten
  für Entscheider sichtbar; Pflege komplett ohne Code oder JSON.
- **Gremium: Quorum & Abstimmungs-Frist**: je Stelle konfigurierbares Quorum
  („N von M" statt starrer Mehrheit, ehrlich auf Sitzzahl gekappt) und
  Frist in Tagen mit rotem Überfälligkeits-Badge im Freigabe-Postfach und
  einmaliger Eskalations-Mail an ausstehende Mitglieder.
- **Kampagnen-Ablaufdatum**: Landingpages zeigen nach Ablauf eine freundliche
  Endseite mit Weg zur Stellenbörse (kein 404 – QR-Plakate hängen länger als
  Kampagnen laufen); abgelaufene Kanäle ordnen keine neuen Bewerbungen mehr
  zu, freie Quellen bleiben unbeschränkt; Pflege je Kanal/Landingpage,
  leer = unbegrenzt.
- **Gesprächsrunden als formale Zustände**: je Stelle definierbare Runden
  (z. B. Erstgespräch → Fachgespräch → Probearbeit); Einstellen erst möglich,
  wenn alle Runden abgeschlossen sind (klare Meldung nennt die offene Runde);
  Abschließen und Zurücknehmen (Korrektur) auf der Termine-Seite mit
  Fortschritts-Leiste; ohne definierte Runden bleibt alles wie bisher.

### Behoben
- **Freigabe-Bypass**: Die finale Job-Freigabe publizierte am
  Stellenfreigabe-Gate vorbei – jetzt bleibt die Stelle Entwurf, mit
  Warnung und Audit-Eintrag.
- **Wizard-Datenverlust**: Das Bearbeiten einer Stelle über die Oberfläche
  löschte gesetzte Quorum-/Frist-Werte stillschweigend (Felder wurden nie
  vorbefüllt); Edit befüllt jetzt alle Governance-Felder vor.

### Geändert
- Bedarf-Konvertierung übernimmt die Stellen-Anzahl (Headcount) aus dem
  genehmigten Antrag.
- Demo-Welt Banking enthält drei Routing-Matrix-Beispielregeln
  (Tech-Gremienprozess, Standard Filiale, globaler Fallback).

## [1.5.0] – 2026-07-04

Flexibilität & Bedienbarkeit: Das Einstellungs-Ereignis macht Erfolg messbar,
der CMS-Baukasten macht Seiten in Minuten baubar, und die Konfiguration
(Fragen, Formate, Import, Kosten) braucht kein Technik-Vorwissen mehr.
Update: `docker compose pull && docker compose up -d` (Migrationen 0029–0032).

### Hinzugefügt
- **Status „Eingestellt" mit Time-to-Fill**: nur aus „Eingeladen" setzbar,
  Einstellungsdatum automatisch oder manuell (rückwirkend, korrigierbar);
  grüne Kanban-Spalte; je Kanal/Landingpage „eingestellt" und „Ø Tage bis
  Einstellung"; Kosten je Einstellung rechnet mit echten Einstellungen.
- **CMS-Baukasten**: Seiten und Landingpages aus 10 Block-Typen zusammensetzen
  (Hero, Benefits, Kennzahlen, Zitat, FAQ, Bild, Ansprechperson, Stellen live,
  CTA) – Editor mit Live-Vorschau, ohne HTML, Träger-Branding automatisch.
- **Fragen-Builder ohne JSON**: Mindeststandards je Jobfamilie per Formular
  pflegen (Frage, Typ, Optionen, K.O.-Antwort, sortieren) – kein Technik-Vorwissen.
- **Fragetyp „Pflicht-Dokument"**: Führerschein, Impfnachweis oder Zertifikat
  je Stelle/Jobfamilie verlangen; Upload mit Whitelist, Ablage mit
  Anforderungs-Label; fehlend = Formular-Fehler, nie automatische Absage.
- **Gesprächsformate konfigurierbar**: eigene Formate anlegen/umbenennen/
  entfernen (HR-Admin) – bestehende Termine behalten ihre Bezeichnung.
- **Import: manuelle Spalten-Zuordnung** („Ihre Spalte → unser Feld", Automatik
  übersteuerbar, unerkannte Spalten benannt) und **Adressfeld** (verschlüsselt).
- **Kampagnenkosten am Kanal**: Betrag je Kanal, Kennzahl „Kosten je
  Einstellung" direkt auf der Kanal-Seite und in der Analytics.
- **Analytics-Vollständigkeit**: jede neue Landingpage UND jede neue
  Inhaltsseite erscheint automatisch (Aufruf-Zähler für CMS-Seiten;
  Inhaltsseiten setzen bewusst keine Kampagnenquelle).

### Migrationen
- 0029 CMS-Blöcke, 0030 Seiten-Aufrufe, 0031 Einstellungsdatum,
  0032 Adresse + Kanal-Kosten

## [1.4.0] – 2026-07-04

Kampagnen, Umstieg & Sicherheit: Der Erfolg von Maßnahmen wird messbar, der
Wechsel von Bestandssystemen praktikabel, die öffentlichen Formulare gehärtet.
Update: `docker compose pull && docker compose up -d` (Migrationen 0027–0028
automatisch; neue Abhängigkeiten openpyxl, segno via requirements).

### Hinzugefügt
- **Kanäle & Kampagnen**: Recruiting-Kanal in 10 Sekunden anlegen → Link +
  druckfertiger QR-Code; je Kanal Bewerbungen, „in Sichtung+", Einladungen und
  Einladungsquote. Kampagnen-Quelle überlebt jetzt die ganze Sitzung
  (Liste → Stelle → Formular) statt beim ersten Klick verloren zu gehen.
- **Kampagnen-Landingpages** unter `/k/<name>/`: eigene Ansprache (Überschrift,
  Text, Bild, Ansprechperson), Stellen-Scope über Einrichtung/Abteilung/
  Jobfamilie/Standort, Träger-Branding automatisch. Der Seiten-Name ist die
  Quelle – der volle Trichter Aufrufe → Bewerbungen → Einladungen erscheint auf
  der Verwaltungsseite und im Analytics-Dashboard.
- **Excel-Import (.xlsx)** mit demselben Spalten-Mapping wie CSV, echten
  Zeilennummern im Fehlerbericht und Testlauf zuerst.
- **CV-Dateien aus dem Altsystem (ZIP)**: Zuordnung über E-Mail-Dateinamen zur
  jüngsten Bewerbung, Typ-Erkennung, Testlauf-Garantie, Typ-Whitelist und
  Größenlimits.
- **Rollenspezifische Fragetypen** im Bewerbungsformular: Freitext und Auswahl
  neben Ja/Nein; K.O.-Logik nur bei definierter erwarteter Antwort, Pflichtfelder
  mit Inline-Fehler statt automatischer Absage.
- **Zweite Demo-Welt „Banking"** (`seed_demo_bank`): Großunternehmens-Szenario
  mit Kategorien-Hierarchie, drei Prozess-Profilen (Standard/Tech/Executive)
  und Karriere-Hub – dasselbe Produkt, andere Konfiguration.

### Sicherheit
- **Upload-Härtung am Bewerbungsformular**: Typ-Whitelist (PDF, Word, JPG,
  PNG), 10 MB je Datei, max. 5 Nachweise, Prüfung vor dem Anlegen.
- **XSS-Absicherung testfixiert**: End-to-End-Test über Portal, Nachrichten und
  Dashboard; Wächter-Test verbannt unsichere Template-Filter dauerhaft.

### Migrationen
- 0027 Recruiting-Kanäle, 0028 Landingpages

## [1.3.0] – 2026-07-03

Design & Träger-Identität: Die Software erklärt sich selbst – und trägt auf allen
Bewerberseiten die CI des Trägers statt der Produkt-Optik.
Update: `docker compose pull && docker compose up -d` (Migration 0026 automatisch).

### Hinzugefügt
- **Träger-Branding auf allen Bewerberseiten** (Stellenbörse, Bewerbungsstrecke,
  Portal, Inhaltsseiten): Primär-/Akzentfarbe, Logo, heller oder dunkler Grundton –
  Pflege unter „Erscheinungsbild" (HR-Admin). **Ein-Klick-Import von der
  Unternehmens-Website** (theme-color, Logo-Kandidat, Bildvorschlag; Best Effort mit
  manueller Bestätigung). **Kontrast-Automatik nach WCAG**: Textfarbe auf der
  Primärfarbe wird berechnet, nicht geraten. Das Recruiter-ATS behält bewusst die
  SecurATS-Identität (zentrale Pfad-Trennung, getestet). Live-Vorschau, Audit,
  serverseitige Farb-Validierung. Grundlage: CI-Muster-Analyse
  (Klinik-, Banken- und Telko-Websites) – dokumentiert im Bauplan.
- **Bewerbungs-Pipeline im Portal**: 4-Schritte-Anzeige (Eingegangen → Sichtung →
  Gespräch → Entscheidung) je Bewerbung; Absage als würdevoller grauer Stopp;
  Screenreader-Label.
- **Gremium-Sitz-Punkte im Freigabe-Postfach**: ✓/✗/· je Sitz mit Namen im Tooltip,
  Vertretungs-Stimmen mit V-Marker – der Stand ist auf einen Blick erfassbar.
- **Sidebar in fünf benannten Gruppen** (Arbeitsbereich / Entscheiden / Termine &
  Menschen / Stammdaten & Inhalte / System & Nachweis) mit sinnvoller Umsortierung.

### Geändert
- **Bewerberportal vollständig auf Design-Tokens** umgestellt: Träger-CI wirkt auch
  dort (hell + Logo), ohne Branding bleibt die gewohnte Optik; einheitliche
  Status-Farbsprache (NEU=Violett, SICHTUNG=Bernstein, EINGELADEN=Teal, ABSAGE=Grau)
  auf hellem und dunklem Grund lesbar; tote Alt-Timeline entfernt.
- **Mobil-Feinschliff im Portal**: Touch-Ziele min. 44 px, 15-px-Formularschrift
  (kein iOS-Zoom), einspaltiges Layout unter 480 px.

### Migrationen
- 0026 Branding-Felder an der Organisation

## [1.2.0] – 2026-07-03

Prozess-Individualisierung & Governance: Das System merkt sich bewährte Prozesse,
Gremien entscheiden vor der Einladung, Vertretungen blockieren nichts mehr – und
das Audit-Log behauptet nur noch, was wirklich passiert ist.
Update: `docker compose pull && docker compose up -d` (Migrationen 0022–0025 automatisch).

### Hinzugefügt
- **Prozess-Gedächtnis** (Job-Wizard „Bewährten Prozess übernehmen" + automatisch beim
  Bedarf-Convert): Spezifitäts-Leiter Abteilung > Einrichtung > Standort > Jobfamilie;
  Kaltstart-Fallback aufs Regelwerk des Prozess-Beraters; Herkunft wird angezeigt.
- **Vorstands-Mindeststandards** je Jobfamilie (Pflege nur HR-Admin): serverseitig bei
  jedem Speichern durchgesetzt – fehlende Pflichtfragen werden wieder eingefügt,
  `isMandatory` ist nicht abschwächbar; vollständig auditiert.
- **Sichtungs-Gremium vor der Einladung** (höhere Positionen): je Struktur konfigurierbar
  über die Vererbungs-Leiter Stelle > Abteilung > Einrichtung > Standort > Jobfamilie >
  Organisation (Pflegeseite `/recruiter/gremien/`, Sentinel „bewusst kein Gremium");
  absolute Mehrheit gibt frei, serverseitig an allen Einladungs-Pfaden; Stimmen änderbar
  und auditiert, Kommentare in den internen Notizen; Live-Vorschau des wirksamen Gremiums
  im Job-Wizard; Override granular über `OVERRIDE_GROUPS` (auditiert).
- **Urlaubsvertretung wirkt** (vorher Karteileiche): in Freigaben (Badge + Kommentar-Vermerk)
  und Gremien (Sitz-Logik, eigene Stimme hat Vorrang); Scope ALL/FACILITY/JOB serverseitig;
  vorzeitiges Beenden wirkt sofort überall; eigene Persona [VT] mit UC-VT-01…06 verankert.
- **Entscheidungs-Erinnerungen** (`send_decision_reminders`, Cron): offene Freigaben (nur
  wer an der Reihe ist) und fehlende Gremien-Stimmen; genau eine Erinnerung je Person und
  Vorgang; Vertretungen werden mit erinnert.
- **Talent-Pool-Lebenszyklus** (vorher Karteileiche): Opt-in im Portal (Kriterien
  datensparsam aus eigenen Bewerbungen), Matching auf offene Stellen, Ein-Klick-Hinweis
  mit Doppel-Ansprache-Sperre, Austritt jederzeit, Wirksamkeits-Kennzahlen inkl.
  Konversion, `purge_talent_pool` (DSGVO-Löschung nach Kulanzfrist).
- **Würdevolle Absage-Kommunikation**: echte Mail + Portal-Nachricht beim REJECTED-Übergang
  (einmalig, Vorlage „Absage" mit Platzhaltern), mit Portal-Link und Talent-Pool-Einladung.
- **Bestandserhalt-Testnetz**: No-Op-Roundtrip-Tests für alle sechs Edit-Pfade –
  verbindliche Regel für jede künftige Edit-View.

### Geändert
- **Workflow-Aktionen ehrlich**: `EMAIL_NOTIFICATION` versendet jetzt echte Mails aus
  Vorlagen (oder auditiert `SKIPPED_NO_TEMPLATE`); alle nicht implementierten Aktionen
  werden als `WORKFLOW_ACTION_SKIPPED` auditiert statt Versand zu simulieren; Mock-Links entfernt.

### Sicherheit
- Portal-Rate-Limit: max. 10 eingehende Vorgänge je Stunde und Person (Rückfragen,
  Änderungswünsche, E-Mail-Änderungs-Anfragen) – freundliche Bremse statt Team-Flutung.
- Datenverlust-Bug behoben: Bearbeiten einer Stelle löschte deren Gremium stillschweigend
  (Edit-Vorbefüllung + Testnetz verhindern die gesamte Bug-Klasse).
- Audit-Integrität: keine „SENT"-Behauptungen mehr ohne tatsächlichen Versand.

### Migrationen
- 0022 `TalentPoolContact` · 0023 `JobFamily.minimumQuestionsJson`
  · 0024 `JobPosting.panelUserIdsJson` + `ApplicationVote` · 0025 Gremien-Defaults auf
  Organisation/Standort/Einrichtung/Abteilung/Jobfamilie

## [1.1.0] – 2026-07-03

Terminmanagement komplett: vom Bedarf über die Einladung bis zum gemessenen Ergebnis.
Update wie gewohnt: `docker compose pull && docker compose up -d` (Migrationen 0016–0021 laufen automatisch).

### Hinzugefügt
- **Team-Kalender** (`/recruiter/interviews/`): Monatsraster über alle Standorte (BOLA-gescopt),
  Interviews + angebotene/belegte Timeslots inkl. Ersteller, `.ics`-Download (bewusst kein
  Abo-Feed: PII). Slot-Anlage einzeln oder als Wochen-Serie, mit Gesprächsformat.
- **Sechs Gesprächsformate durchgängig** (Telefonat, Video, vor Ort, Probearbeit/Hospitation,
  Assessment/Auswahltag, schriftliche Aufgabe): im Einlade-Modal, am Slot, als Kalender-Badge,
  im Portal **vor** der Buchung, im Erinnerungs-Betreff und im `.ics`-Export.
- **Interview-Team:** Teilnehmende beim Einladen zuordnen; sofortige Team-Mail bei Planung,
  Team-Erinnerung an alle Beteiligten, Info bei jeder Bewerber-Aktion (Umbuchung/Absage/Wunsch).
- **Selbstbuchung & Selbstservice im Portal:** Terminwahl per Ein-Klick (atomar, Doppelbuchung
  ausgeschlossen), Umbuchen und Absagen bis 24 h vorher (serverseitig erzwungen), jederzeit
  Änderungsanfrage; mehrstufige Runden (Telefonat → Probearbeit → vor Ort) je Runde neu buchbar.
- **Termin-Erinnerungen** (`send_interview_reminders`, Cron): genau einmal je Interview,
  an Bewerbende (Mail + Portal) und das gesamte Interview-Team; Umbuchung schärft die
  Erinnerung neu.
- **Ergebnis-Erfassung:** „Ergebnis erfassen" im Kalender (stattgefunden / No-Show /
  kurzfristig abgesagt), Ein-Klick, auditiert mit Vorwert; Zusage/Absage bleibt im Kanban.
- **Termin-Analytik** (Analytics › „Termine & Selbstbuchung"): Selbstbuchungs-Quote, Median
  bis zur Terminwahl, Abend/Wochenend-Anteil, Umbuchungen/Absagen/Änderungswünsche,
  Slot-Auslastung, Formate-Verteilung, **No-Show-Quote** (nur über erfasste Ergebnisse) –
  mit regelbasierten Handlungsvorschlägen; Kennzahlen auch im lokalen KI-Analysten.
- **Portal-Nachrichten:** Verlauf beider Richtungen je Bewerbung sichtbar + Rückfrage-Formular
  (Mail an die Ansprechperson der Stelle); Kontaktdaten: Telefon direkt änderbar, E-Mail-Änderung
  bewusst nur als geprüfte Anfrage (Identitätsanker).
- **Personalbedarf** (`/recruiter/bedarf/`): strukturierte Meldung statt Zuruf; Entscheidung mit
  Anmerkung + Mail an Melder:in; **Ein-Klick-Überführung** in einen unveröffentlichten
  Ausschreibungs-Entwurf (interne Begründung bleibt intern, Freigabe-Gate greift automatisch).
- **„Heute wichtig"** im Dashboard: unbeantwortete Nachrichten (mit Direktlinks), überfällige
  Erstsichtungen, wartende Freigaben, heutige Gespräche, offene Ergebnisse, offene Bedarfe.
- **Audit-Export** (`/recruiter/audit/export.csv`, HR-Admin): CSV mit Zeitraum-/Aktions-Filter,
  Integritäts-Kopfzeile (Hash-Ketten-Status) und `entryHash` je Zeile; Export selbst auditiert.
- **Prozess-Berater** am Stellen-Formular: berufsspezifische K.-o.-Frage-Vorschläge (Examen,
  Approbation, Führungszeugnis …), KI-Zusatzfragen stets optional; Freigabekette je Einrichtung
  konfigurierbar (`Facility.approvalChain`, nie leer).
- **Einladungs-Nachricht** im Modal (aus Vorlage vorbefüllt, lokale KI-Politur optional),
  echte Zustellung als Portal-Nachricht + E-Mail statt Mock-Links.

### Geändert
- Portal-Terminwahl prüft auf **anstehende** statt irgendwelche Gespräche (mehrstufige Prozesse).
- Demo-Seed: Slots mit gemischten Formaten (inkl. 4-h-Probearbeit).
- Use-Case-Matrix: 9 veraltete „(Roadmap)"-Zeilen auf ✅ korrigiert; 12 UCs neu erfüllt
  (UC-SB-20…26, UC-AY-10…13, UC-MD-01/02, UC-JF-10, UC-MB-08, UC-NS-12, UC-LK-11, UC-RI-06,
  UC-PW-06, UC-UM-06).

### Sicherheit
- Selbstservice-Grenzen serverseitig erzwungen (24-h-Regel, fremde Tokens wirkungslos).
- E-Mail-Änderung im Portal nur als geprüfte Anfrage (Schutz des Magic-Link-Identitätsankers).
- Interne Bedarfs-Begründungen erscheinen nie in öffentlichen Ausschreibungen (getestet).

### Migrationen
- 0016 `Facility.approvalChain` · 0017 `InterviewSlot.createdBy` · 0018 `Interview.reminderSentAt`
  · 0019 `Interview.participants` + `InterviewSlot.kind` · 0020 `StaffingRequest`
  · 0021 `StaffingRequest.convertedJob`

## [1.0.0] – 2026-07-02

Erste versionierte Release. Konsolidiert den kompletten Ausbau WP0–WP8 plus Nachträge.

### Hinzugefügt
- **Kandidaten-Strecke:** Bewerbung ohne Konto (Handy-Foto statt PDF genügt), Mehrfach-Dokumente,
  Magic-Link-Portal mit 4-Stufen-Status-Timeline, Leichte Sprache je Stelle, Vorlesefunktion,
  Barrierefreiheits-Panel (Legasthenie-Schrift, Kontrast, Fokusmodus, Lese-Lineal).
- **Job-Alerts mit Scope:** Stichwort / Einrichtung / km-Umkreis (Haversine) / global;
  Double-Opt-in, Verwalten & Abmelden per Token, automatischer 12-Monats-Verfall,
  genau ein Abo je E-Mail (Update statt Duplikat). Versand-Command `send_job_alerts`.
- **Stellensuche:** Volltext (Titel + Beschreibung), Standort-/Abteilungs-/Kategorie-Filter;
  öffentliche Einrichtungs-Karriereseiten `/einrichtung/<slug>/`.
- **Recruiter:** Kanban mit positionalem Drag&Drop **und** Tastatur-Alternative, Mehrfachauswahl,
  Stammdaten-Zentrale (Ansprechpartner inkl. „Überall ersetzen", Textbausteine, Vorlagen mit
  Versionierung + Tonalitäts-Overlay), Ein-Klick-(De)Aktivierung von Anzeigen.
- **Governance:** Freigabe-Postfach „wartet auf mich" mit SLA-Frist; **automatisches
  Approval-Gate** (`Facility.requiresApproval` + `APPROVAL_CHAIN`), finale Freigabe
  publiziert automatisch; datenminimiertes Governance-Cockpit für BR/SBV/DSB;
  GF-Wochenreport (`weekly_report`).
- **Analytics:** Time-to-Fill-Prognose, Anomalie-Hinweise mit Handlungsvorschlag,
  Fairness-Cockpit (datensparsam), Standort-Benchmark & Kosten/Einstellung (Leitung),
  CSV-Export (auditiert), lokaler KI-Analyst auf aggregierten Daten.
- **Sicherheit/Compliance:** PII-Verschlüsselung inkl. **E-Mail via Blind-Index** (HMAC),
  Audit-Log mit Hash-Kette + `verify_audit`, DSGVO-Export `export_applicant`,
  Prompt-Injection-Guardrails (`ai_safety`), Feed-Token, BOLA-Scoping durchgängig,
  serverseitige Inline-Formularfehler (WCAG 3.3.1 – alle AA-Lücken geschlossen).
- **Betrieb:** DB-Queue + `ai_worker`, `/healthz/` (inkl. Version), `ai_doctor`,
  PostgreSQL-Produktionsprofil, Runbook (OPERATIONS.md), Docker-Compose-Stack
  (Postgres, optionales KI-Profil), Release-Workflow (ghcr.io).

### Geändert
- **KI-Scoring ist Opt-in (Default AUS)** – `AI_SCORING_ENABLED`; keine Platzhalter-Scores
  mehr, ehrliche „–"-Anzeige. Positionierung: „KI-Assistenz, keine automatische Bewertung".
- Landing bewerber-zentriert; erfundene Bewertungs-Badge entfernt.

### Sicherheit
- CV-Downloads nur über autorisierte Endpoints (BOLA + Audit), kein /media/-Direktzugriff.
