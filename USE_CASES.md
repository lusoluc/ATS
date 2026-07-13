# SecurATS – Use-Case-Bibliothek (Persona-basiert)

> **Zweck:** Qualitätskontrolle. Jede Persona aus `NORTHSTAR.md` (Abschnitt 2.1)
> erhält 10–15 realistische Use Cases. Sie dienen dazu, **jede Seite, Funktion und
> jeden Click-Flow** der App systematisch dagegen zu prüfen und iterativ zu
> optimieren – damit nichts vergessen wird.
>
> **Spalten:** ID · Use Case (Als … möchte ich … um …) · betroffene Seite(n)/Flow ·
> QA-Prüfkriterium (woran erkennt man, dass es gut gelöst ist).
>
> **ID-Schema:** `UC-<Kürzel>-<Nr>`. Status-Konvention für das spätere Audit:
> ✅ erfüllt · ◐ teilweise · ❌ offen · — nicht anwendbar.
>
> Verweise auf Seiten nutzen die realen Routen (z.B. `/recruiter/analytics/`) bzw.
> Dashboard-Tabs. „(Roadmap)" markiert Use Cases, deren Funktion noch aussteht.
>
> ⚠️ **Validierungsstatus (Premortem Juli 2026):** Alle Personas und Use Cases in
> diesem Dokument sind **synthetisch** – Schreibtischarbeit, Stand heute durch
> **0 Interviews** belegt. Sie bleiben das QA-Instrument (Seiten gegen UCs prüfen),
> aber **kein neues Feature wird allein auf ihrer Basis priorisiert** (siehe
> ROADMAP.md, Prinzip 2). Ab Phase V1 erhält jede Persona einen Evidenz-Status:
> **H** = Hypothese (Default heute) · **V** = durch ≥ 2 Interviews validiert ·
> **†** = durch Interviews widerlegt/gestrichen.

---

## Gruppe A — HR & Recruiting

### A1 · Sandra Berg — zentrale Recruiterin (Konzern, 6 Töchter) [SB]

> **Profil & Alltag:** 38, betreut das Recruiting von sechs Tochtergesellschaften mit ~40 parallel
> offenen Stellen. Schreibt wöchentlich mehrere Anzeigen aus, oft dieselbe Rolle für verschiedene
> Standorte. Ihr Tag ist getaktet – jede Minute, die eine Anzeige länger dauert, fehlt in der
> Bewerberkommunikation. **Schmerzpunkte (vorher):** identische Absätze immer neu getippt,
> Ansprechpartner-Daten in jeder Anzeige einzeln nachgezogen, Deaktivieren nur über das
> Bearbeiten-Modal. **Was SecurATS ihr jetzt gibt:** Stammdaten-Zentrale (Standorte, Kategorien,
> Ansprechpartner, Textbausteine, Vorlagen mit Versionierung) – einmal pflegen, überall aktuell;
> Anzeige aus Vorlage + Bausteinen + Ton-Overlay in unter zwei Minuten; Ein-Klick-Deaktivierung.

| ID | Use Case | Seite / Flow | QA-Prüfkriterium || ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-SB-01 | …eine neue Stelle für eine Tochter ausschreiben | Dashboard › Jobs › „Stelle anlegen" | Stelle in ≤ 3 Klicks angelegt; Standort/Kategorie wählbar |
| UC-SB-02 | …dieselbe Stelle per Vorlage in mehreren Töchtern nutzen | `/recruiter/job-templates/` → Job anlegen | Vorlage 1-Klick übernommen; Delta editierbar; Stelle verknüpft die exakte Vorlagen-Version (Master-Hierarchie) |
| UC-SB-03 | …die Tonalität einer Vorlage je Abteilung anpassen | Job-Vorlagen › „Ton anpassen" (KI) | KI-Vorschlag erscheint; Fallback bei KI-Ausfall |
| UC-SB-04 | …eine Stelle mit 1 Klick zu StepStone/BA/Google posten | Dashboard › Jobs › Multiposting | Kanäle auswählbar; Feed-URL erzeugt |
| UC-SB-05 | …das Kanban über alle Standorte überblicken | Dashboard › Kanban | Alle Standorte sichtbar (Full-Access); Spalten klar |
| UC-SB-06 | …eine Bewerbung per Drag&Drop weiterziehen | Kanban → `update_status` | Statuswechsel persistiert; Audit-Eintrag entsteht |
| UC-SB-07 | …einen Lebenslauf sicher herunterladen | Bewerbungsdetail → `…/cv/` | Nur mit Rolle; Download; `READ_CV` im Audit |
| UC-SB-08 | …standortübergreifende KPIs vergleichen | `/recruiter/analytics/` | Standort-Vergleich sichtbar; Zahlen korrekt |
| UC-SB-09 | …die Kanal-Performance (Quellen) auswerten | Analytics › Quellen | Quellen-Verteilung inkl. STEPSTONE/BA sichtbar |
| UC-SB-10 | …zentrale E-Mail-Vorlagen & Variablen pflegen | Dashboard › E-Mail & Variablen | Änderung wirkt global; Vorschau vorhanden |
| UC-SB-11 | …eine neue Kategorie/Jobfamilie anlegen | `/recruiter/categories/` | Anlegen ≤ 2 Klicks; sofort wählbar |
| UC-SB-12 | …einen neuen Standort anlegen | `/recruiter/locations/` | Standort anlegbar; erscheint in Job-Anlage |
| UC-SB-13 | …den Talent-Pool nach passenden Kandidaten sichten | ✅ `/recruiter/talent-pool/` | Je Eintrag: automatisch gematchte offene Stellen (Jobfamilie/Standort, BOLA-Scope) + Ein-Klick-Hinweis; genau eine Ansprache je Person und Stelle (DB-erzwungen, getestet); Ablauf sichtbar, abgelaufene ohne Matching |
| UC-SB-14 | …eine AGG-neutrale Absage versenden | Detail → Nachricht/KI | Absagetext AGG-geprüft; versandt + protokolliert |
| UC-SB-15 | …Ansprechpartner zentral pflegen (Telefon/Foto/Rolle) | `/recruiter/contacts/` | Änderung wirkt sofort auf ALLEN Anzeigen (FK-Prinzip, getestet) |
| UC-SB-16 | …eine Ansprechperson überall ersetzen (Urlaub/Ausscheiden) | Contacts › „Überall ersetzen" | Alle Anzeigen in 1 Schritt umgehängt; `CONTACT_REPLACED` im Audit |
| UC-SB-17 | …eine Anzeige mit einem Klick deaktivieren/reaktivieren | Dashboard › Jobs › Toggle | Sofort aus öffentlicher Liste + Feeds; Audit; ohne Modal |
| UC-SB-18 | …wiederkehrende Absätze als Textbausteine pflegen | `/recruiter/snippets/` | Baustein per Dropdown in die Anzeige einfügbar |
| UC-SB-19 | …eine komplette Anzeige in < 2 Min. erstellen | Vorlage + Bausteine + Ton + Kontakt | End-to-End ohne Freitext-Pflicht möglich |
| UC-SB-20 | …eine:n Bewerber:in in EINEM Schritt einladen (Termin + Nachricht) | Kandidaten-Modal › Einladen | Status INVITED, Portal-Nachricht + E-Mail mit Termin, `INVITE_SENT` im Audit; kein erfundener Meeting-Link |
| UC-SB-21 | …mir passende Screening-Fragen vorschlagen lassen | Job-Anlage › „Prozess vorschlagen" | Regelbasiert sofort; KI-Zusatzfragen optional und nie mit K.O.-Wirkung; Gate-Hinweis sichtbar, nicht abschaltbar |
| UC-SB-22 | …Timeslots anbieten, die das ganze Team und Bewerbende nutzen können | `/recruiter/interviews/` | Slot-Anlage mit wöchentl. Serie, Ersteller sichtbar; löschen nur eigene unbelegte (HR-Admin: alle), `SLOT_CREATED/DELETED` im Audit |
| UC-SB-23 | …alle Gespräche des Teams standortübergreifend in EINEM Kalender sehen | `/recruiter/interviews/` | Monatsraster mit Interviews + freien/belegten Slots, BOLA-gescopt; .ics-Export für Outlook (bewusst Download statt Token-Feed: PII) |
| UC-AY-10 | …meinen Gesprächstermin selbst wählen – abends, vom Handy | Portal (Magic-Link) › Terminwahl | Bei Einladung „Bewerber:in wählt": freie Slots als Ein-Klick-Buttons; Buchung atomar (Doppelbuchung getestet blockiert), sofortige Bestätigung per Portal-Nachricht + E-Mail, `CANDIDATE_SLOT_BOOKED` |
| UC-AY-11 | …VOR der Terminwahl wissen, was mich erwartet (Telefonat? Probearbeit?) | Portal › Terminwahl | Slot-Format steht auf jedem Buchungs-Button; Bestätigung nennt das Format („✓ Probearbeit / Hospitation") |
| UC-AY-12 | …meinen Termin selbst umbuchen oder absagen, wenn die Schicht getauscht wird | Portal › „Termin ändern oder absagen" | Bis 24 h vorher: Umbuchen auf freien Slot in einem Klick (alter Slot wird frei, Erinnerung neu scharf) oder Absage mit optionalem Grund – Bewerbung bleibt bestehen, Terminwahl öffnet sich wieder; Team wird automatisch informiert (getestet) |
| UC-AY-13 | …kurzfristig (< 24 h) einen Änderungswunsch loswerden, ohne anzurufen | Portal › Änderungsanfrage | Freitext-Anfrage landet als INBOUND-Nachricht im Verlauf + Mail ans Interview-Team; `CANDIDATE_CHANGE_REQUEST` im Audit; Selbstservice ist in den letzten 24 h bewusst gesperrt (Raum/Anreise sind organisiert) |
| UC-PW-07 | …dass meine Urlaubsvertretung Freigaben UND Gremien-Stimmen übernehmen kann | `/recruiter/delegations/` (wirkt jetzt überall) | Vertretung wirkt in Freigabe-Postfach + Aktion (Badge „in Vertretung für X", im Kommentar dokumentiert) und im Gremium (Sitz-Logik: eigene Stimme des Mitglieds hat Vorrang, getestet); Scope ALL/FACILITY/JOB serverseitig geprüft; abgelaufene Vertretungen wirken nirgends |
| UC-PW-08 | …an ausstehende Entscheidungen erinnert werden, bevor Prozesse blockieren | `send_decision_reminders` (Cron) | Genau EINE Erinnerung je Person und Vorgang (Marker im Audit, getestet gegen Doppellauf) für offene Freigabe-Schritte (nur wenn an der Reihe) und fehlende Gremien-Stimmen; Vertretungen werden mit erinnert („In Vertretung für …") |
| UC-AR-28 | …in einer Parallelgruppe ein Quorum setzen (2 von 3 genügen), damit ein Abwesender nicht blockiert | Routing-Matrix › Ketten-Syntax „(N)“ | „A + B + C (2)“: sobald zwei zustimmen, werden die restlichen Gruppen-Stufen aufgelöst und die nächste Stufe fällig (getestet); ohne „(N)“ müssen alle genehmigen (getestet); Wiedervorlage belebt übersprungene Stufen (getestet) |
| UC-AR-27 | …in einer Genehmigungskette Stufen parallel schalten (Controlling UND Betriebsrat gleichzeitig) | Routing-Matrix › Ketten-Syntax „+" | Komma = nacheinander, „+" = parallel; alle Rollen der Stufe müssen genehmigen (Reihenfolge frei, getestet), Folgestufe bis dahin gesperrt (getestet), eine Rückgabe stoppt den Antrag (getestet); ohne „+" exakt Bestandsverhalten |
| UC-AR-26 | …als HR ohne Code festlegen, welcher Bereich welches Bedarfsformular bekommt und wer genehmigt | Bedarf › Routing-Matrix | Regel = Geltungsbereich (Wildcards) + Fragen + Kette + Pflicht; spezifischste gewinnt (getestet: exakt > teilweise > Fallback); Pflicht je Regel blockiert Veröffentlichung im Scope auch ohne globalen Schalter (getestet); Fragen-Builder je Regel ohne JSON; Antworten für Entscheider sichtbar |
| UC-AR-24 | …als Teamleitung/Bereichsleitung/Vorstand eine Neuanstellung beantragen, die vor der Ausschreibung mehrstufig genehmigt wird | Bedarf › Antrag + Stufenleiste | Optionaler Prozess (HR-Admin-Schalter), wenn aktiv dann Pflicht: Veröffentlichen ohne genehmigten Bedarf blockiert (Entwurf-Rückfall + 409 am Toggle, getestet); Kette je Einrichtung oder global (Rollen = Gruppen, frei anlegbar), sequenziell erzwungen; Genehmigen/Nachbesserung mit Neustart/endgültig Ablehnen; Mail an Antragsteller; `REQUISITION_*`-Audits |
| UC-AR-25 | …aus dem genehmigten Bedarf mit einem Klick die Ausschreibung starten | Bedarf › „Als Entwurf anlegen" | Übernimmt Titel, Einrichtung, Jobfamilie und jetzt auch Stellen-Anzahl (getestet); Genehmigungs-Nachweis hängt an der Stelle und öffnet die Veröffentlichung |
| UC-AR-23 | …je Stelle festlegen, wie viele Gremium-Stimmen genügen, und eine Abstimmungs-Frist mit Eskalation setzen | Stellen-Wizard (Quorum + Frist) › Freigabe-Postfach | Quorum „N von M" (leer = Mehrheit, Bestand unverändert; gekappt auf Sitzzahl – getestet); Frist ab Bewerbungseingang, überfällig = rotes Badge im Postfach + „Frist überschritten"-Eskalations-Mail einmalig je Sitz (Doppellauf getestet); Edit ohne Felder behält Bestand |
| UC-AR-22 | …„3 Stellen gleicher Art" als eine Ausschreibung führen und beim Vollbesetzen nicht weiter werben | Stellen-Wizard (Anzahl) + automatische Ausblendung | headcount 1–99; bei Erreichen Hinweis + `JOB_FILLED`-Audit; Stellenbörse und Landingpages blenden automatisch aus (getestet); Direktlink zeigt „bereits besetzt"-Banner, Bewerben bleibt möglich (getestet); Edit ohne Feld behält Bestand |
| UC-AR-19 | …unsere eigenen Gesprächsformate definieren (z. B. Assessment-Center-Tag) | Termine › „Gesprächsformate verwalten" | Hinzufügen/Umbenennen/Entfernen ohne Code (nur HR-Admin, getestet); wirkt sofort in Timeslots + Termin-Modal; bestehende Termine behalten ihre Bezeichnung (Fallback getestet) |
| UC-AR-20 | …beim Import selbst bestimmen, welche Spalte welches Feld ist – inkl. Adresse | Daten-Import › „Spalten-Zuordnung prüfen" | Erkennungs-Tabelle mit Selects, manuelle Zuordnung gewinnt (getestet: MailAdr→E-Mail), unerkannte Spalten benannt, „Nicht importieren" je Feld; Adresse verschlüsselt at-rest wie Telefon |
| UC-AR-21 | …Kampagnenkosten am Kanal pflegen und Kosten je Einstellung ablesen | „Kanäle & Kampagnen" | Betrag je Kanal (deutsches Format geparst, getestet), Kennzahl Kosten/Einstellung aus echten HIRED-Ereignissen, speist Analytics automatisch |
| UC-AR-17 | …als HR ohne Technik-Vorwissen Mindeststandards pflegen (auch: Pflicht-Dokumente wie Führerschein verlangen) | Screening-Fragen › Mindeststandards | Formular-Builder statt JSON (Frage/Typ/Optionen/K.O., sortieren, löschen – getestet ohne ein Zeichen JSON); 4. Fragetyp „Pflicht-Dokument": Upload im Bewerbungsformular mit Whitelist, Ablage mit Anforderungs-Label (docType REQUIRED), fehlend = Inline-Fehler statt Absage (getestet inkl. .exe-Negativ) |
| UC-AR-18 | …das Einstellungsdatum rückwirkend erfassen oder korrigieren | Kanban „Eingestellt" (Datum-Abfrage) | `hired_at` JJJJ-MM-TT, Korrektur bei bereits Eingestellten, Zukunft/Unsinn 400 (getestet); `HIRED_DATE_CORRECTED`-Audit |
| UC-AR-16 | …eine Einstellung festhalten und wissen, wie lange die Besetzung gedauert hat und welcher Kanal sie gebracht hat | Kanban „Eingestellt" + Kanäle/Analytics | HIRED nur aus „Eingeladen" (erklärender Fehler sonst, getestet); Korrektur löscht das Ereignis sauber; Ø Tage bis Einstellung je Kanal; Kosten je Einstellung rechnet mit echten Einstellungen statt Einladungs-Näherung (getestet); grüner Abschluss in der Bewerber-Pipeline; `APPLICATION_HIRED`-Audit |
| UC-AR-15 | …ohne HTML-Kenntnisse in Minuten eine schöne, funktionsfähige Seite bauen (Karriere, Einrichtung, Aktion) | Seiten-/Landingpage-Verwaltung › „Baukasten" | 10 Block-Typen (Hero, Text, Benefits, Kennzahlen, Zitat, FAQ, Bild, Ansprechperson, Stellen live, CTA); Editor mit Live-Vorschau, hoch/runter/löschen ohne JS; serverseitige Validierung (unbekannte Typen fliegen, Limits geklemmt – getestet); nur Autoescape + Design-Tokens → Träger-Branding automatisch, XSS-Negativ-Test; CMS-Seiten nur HR-Admin (403 getestet); No-Op-Speichern erhält Blöcke; `CMS_BLOCKS_CHANGED`-Audit |
| UC-AR-14 | …je Stelle rollenspezifische Fragen stellen – Freitext, Auswahl oder Ja/Nein mit K.O. | Stellen-Wizard › Screening-Fragen | Typen TEXT (Werterhalt, 1000 Zeichen) und SELECT (eigene Optionen) neben YES_NO; K.O. nur bei definierter erwarteter Antwort; Pflichtfeld ohne K.O. → Inline-Formular-Fehler, keine automatische Absage (getestet); Antworten im Dashboard escaped sichtbar (XSS-Negativ-Test) |
| UC-AR-13 | …einer Messe, Einrichtung oder Aktion eine eigene Seite mit eigener Ansprache geben – und deren Erfolg messen | „Landingpages" + /k/&lt;name&gt;/ | Eigene Headline/Intro/Bild/Ansprechperson; Stellen-Scope UND-verknüpft über Einrichtung/Abteilung/Jobfamilie/Standort (getestet: fremde Stellen erscheinen nicht); der Slug IST die Quelle → jede Bewerbung trägt die Kampagne (getestet über die volle Kette); Selbstmessung Aufrufe→Bewerbungen→Einladungen mit Quoten auf Verwaltungsseite UND Analytics-Dashboard (getestet, de-Locale); QR + Link je Seite; deaktiviert = öffentlich 404 (getestet); Träger-Branding wirkt automatisch; No-Op-Roundtrip; `LANDING_PAGE_SAVED`-Audit |
| UC-AR-12 | …wissen, ob die Jobmesse (oder ein anderer Kanal) erfolgreich war | „Kanäle & Kampagnen" | Kanal anlegen (10 Sek.) → Link + QR-Code für den Aufsteller; Quelle überlebt die ganze Sitzung (Liste→Detail→Formular, getestet); Auswertung mit Menge UND Qualität: Bewerbungen, in Sichtung+, eingeladen, Einladungsquote seit Kanal-Anlage; freie Quellen (Import/Direkt) in derselben Tabelle; Slug-Kollisionen automatisch aufgelöst (getestet); `SOURCE_CHANNEL_CREATED`-Audit |
| UC-AY-16 | …dass meine Daten und Uploads das System nicht gefährden können (und ich klare Fehlermeldungen bekomme) | Bewerbungsformular + Portal | Upload-Whitelist PDF/DOC(X)/JPG/PNG, 10 MB, max. 5 Nachweise, Prüfung VOR dem Anlegen mit Inline-Fehler (getestet: .exe/.html abgelehnt, 0 Objekte); XSS-Payload in Name/Nachricht überall nur escaped (getestet Portal/Thread/Dashboard); Wächter-Test verbannt `|safe`/`autoescape off` dauerhaft |
| UC-AR-10 | …Bestandsbewerber direkt aus dem Excel-Export des Altsystems übernehmen | Daten-Import (.xlsx) | Gleiches Spalten-Mapping wie CSV (deutsche/englische Köpfe), Excel-Leerzeilen still übersprungen, echte Zeilennummern im Fehlerbericht, 5.000-Zeilen-Limit; Testlauf zuerst (getestet End-to-End inkl. echter Anlage) |
| UC-AR-11 | …den CV-Dateiberg aus dem Altsystem den Bewerbungen zuordnen | Daten-Import › „CV-Dateien (ZIP)" | Konvention: Dateiname beginnt mit E-Mail; Zuordnung über Blind-Index zur jüngsten Bewerbung; Typ-Erkennung (Lebenslauf/CV → CV); Testlauf ändert garantiert nichts (getestet); nur PDF/DOC(X)/JPG/PNG, 10 MB je Datei, Pfad-Traversal neutralisiert (getestet); `CV_IMPORT`-Audit |
| UC-AY-15 | …mich vom Handy aus bequem im Portal bewegen (Termine, Rückfragen, Rückzug) | Bewerberportal (mobil) | Touch-Ziele min. 44px, 15px-Formularschrift (kein iOS-Zoom), unter 480px einspaltig mit voller Button-Breite; Portal vollständig auf Design-Tokens → Träger-CI wirkt auch hier (hell + Logo, getestet) |
| UC-AR-09 | …die CI/CD unseres Trägers auf die Bewerberseiten bringen, ohne Designer zu sein | Stammdaten › „Erscheinungsbild" | Ein-Klick-Import von der Unternehmens-Website (theme-color, Logo-Kandidat, Bildvorschlag – Best Effort, getestet); Kontrast automatisch nach WCAG (Telekom-Magenta → Weiß, helles Gelb → Dunkel, getestet); heller Grundton als Standard (CI-Analyse-Muster); Recruiter-ATS behält bewusst SecurATS-Identität (getestet); Farb-Validierung serverseitig, `BRANDING_CHANGED`-Audit, No-Op-Roundtrip |
| UC-AY-14 | …als Bewerber:in auf einen Blick sehen, wo meine Bewerbung steht | Portal › Pipeline je Bewerbung | 4-Schritte-Anzeige (Eingegangen/Sichtung/Gespräch/Entscheidung), Absage als würdevoller grauer Stopp, Screenreader-Label; getestet je Status |
| UC-MD-03 | …den Gremien-Stand auf einen Blick erfassen statt Zahlensätze zu lesen | Freigaben › Sitz-Punkte | Je Sitz ✓/✗/· mit Namen im Tooltip, Vertretungs-Stimmen mit V-Marker; Zusammenfassung als aria-label; getestet |
| UC-SB-30 | …beim Erstellen einer Stelle SEHEN, welches Gremium wirken wird | Job-Wizard › Live-Vorschau | „Ohne eigene Auswahl wirkt: Organisation – …" aktualisiert sich bei jeder Änderung von Familie/Einrichtung/Abteilung/Standort (`/recruiter/panel/preview/`, Rollen-geschützt, Leiter getestet); auch der Bedarf-Convert-Entwurf erbt das Gremium (Gate getestet); Edit-Modus befüllt die Job-Gremium-Auswahl vor — Fix eines Datenverlust-Bugs: vorher löschte jedes Bearbeiten das Stellen-Gremium stillschweigend |
| UC-SB-31 | …für eine Tochter in Minuten eine eigene Karriere-Landingpage bauen, ohne HTML zu können | Landingpage › „Baukasten" | Hero/Kennzahlen/Zitat/FAQ/Stellen-Block per Klick zusammensetzen, Live-Vorschau, Träger-Branding automatisch (getestet) |
| UC-SB-32 | …für eine Jobmesse in Sekunden einen Kanal mit QR-Code anlegen | „Kanäle & Kampagnen" | Link + QR sofort verfügbar; Bewerbungsquelle bleibt über die ganze Bewerber-Sitzung erhalten (getestet) |
| UC-SB-33 | …die Kosten einer Kampagne eintragen und sehen, was eine Einstellung wirklich gekostet hat | Kanal-Karte › Kosten-Feld | Deutsches Zahlenformat wird geparst; „Kosten je Einstellung" rechnet mit echten HIRED-Ereignissen, nicht mit Einladungen (getestet) |
| UC-SB-34 | …eine Stelle mit „3 gleichen Positionen" statt drei Einzelanzeigen ausschreiben | Job-Wizard › Anzahl | Headcount 1–99; Stelle bleibt offen bis alle besetzt sind, Direktlink bleibt erreichbar (getestet) |
| UC-SB-40 | …schon beim Blick aufs Board sehen, wie das Team einen Bewerber einschätzt | Kanban › Bewerber-Karte | Farbiges Score-Badge (Ø aus allen Rückmeldungen) + Anzahl + rotes Bedenken-Signal direkt auf der Karte; ein Query fürs ganze Board (kein N+1, getestet) |
| UC-SB-39 | …vor einer Einstellung gewarnt werden, wenn aus Interviews dokumentierte Bedenken vorliegen | Kanban › Einstellen | HIRED wird nicht blockiert, aber bei Bedenken erscheint eine Warnung mit den Texten; Einstellen erst nach bewusster Bestätigung, auditiert (getestet); ohne Bedenken kein Gate (getestet) |
| UC-SB-38 | …dass eine Gesprächsrunde automatisch abgeschlossen wird, wenn ich das Interview als „stattgefunden“ markiere | Termine › Ergebnis erfassen | „Stattgefunden“ rückt die Runde vor, Korrektur nimmt sie zurück (getestet); kein Doppelzählen, kein Überlauf über die Rundenzahl (getestet) |
| UC-SB-37 | …je Stelle festlegen, welche Gesprächsrunden ein Kandidat durchlaufen muss, bevor eingestellt werden darf | Job-Wizard › Gesprächsrunden + Termine-Seite | Runden kommasepariert je Stelle (max. 6); Einstellen blockiert mit Klartext-Meldung, solange Runden offen (getestet); Fortschritts-Leiste mit Abschließen + Korrektur-Zurücknahme; ohne Runden Bestandsverhalten (getestet); Wizard-Edit ohne Feld behält Bestand (getestet) |
| UC-SB-36 | …einer Messe-Kampagne ein Enddatum geben, damit der QR danach nicht mehr falsch zählt | Kanäle & Landingpages › „Ablauf speichern" | Nach Ablauf: LP zeigt freundliche Endseite mit Weg zur Stellenbörse (kein 404 – Plakate hängen länger!), Kanal ordnet keine neuen Bewerbungen mehr zu, freie Quellen unbeeinflusst, leeres Datum = unbegrenzt (alles getestet) |
| UC-SB-35 | …historische Bewerberdaten einer neu übernommenen Tochter importieren, auch wenn die Spaltennamen abweichen | Daten-Import › Spalten-Zuordnung | Eigene Spaltennamen (z. B. „MailAdr") manuell zuordenbar; Adresse wird mitübernommen und verschlüsselt gespeichert (getestet) |
| UC-BL-08 | …das Gremium flexibel zusammenstellen: Firmen-Default, dann je Jobfamilie/Standort/Einrichtung/Abteilung oder Einzelstelle | `/recruiter/gremien/` (HR-Admin) + Job-Wizard | Vererbungs-Leiter Stelle > Abteilung > Einrichtung > Standort > Jobfamilie > Organisation; spezifischste Ebene gewinnt komplett (getestet: Org-Default erbt, Abteilung schlägt Org, Stelle schlägt alles); Sentinel „bewusst kein Gremium" unterbricht Vererbung (getestet: Aushilfen-Familie trotz Firmen-Default frei); Quelle in jeder Meldung („Gremium (Organisation): …"); geerbte Mitgliedschaft erscheint in Postfach + „Heute wichtig" (getestet); `PANEL_DEFAULT_CHANGED`-Audit |
| UC-BL-07 | …granular steuern, wer Entscheidungen überstimmen darf | SystemSetting `OVERRIDE_GROUPS` | Kommaliste von Gruppen (Default HR-Admin); z. B. „Geschäftsführung" kann Gremien übersteuern, ohne HR-Admin-Rechte zu bekommen (getestet); jede Übersteuerung einzeln auditiert (`PANEL_OVERRIDDEN`) |
| UC-BL-06 | …bei höheren Positionen ein Gremium VOR der Einladung entscheiden lassen | Job-Wizard › „Sichtungs-Gremium" + Freigaben › Gremium | Je Stelle benennbares Team (jede Rolle stimmberechtigt, auch HM/Viewer); Einladung serverseitig an ALLEN Pfaden gesperrt bis absolute Mehrheit „dafür" (Kanban-Drag + beide Einlade-Wege, getestet); Stimme änderbar (eine je Person, auditiert); Kommentare/Fragen landen in den internen Notizen (360°-Ort); HR-Admin-Override mit `PANEL_OVERRIDDEN`-Audit; „Heute wichtig"-Pill + Postfach-Sektion |
| UC-BL-05 | …als Vorstand Mindeststandards je Berufsbild durchsetzen | Screening-Fragen › „Mindeststandards je Jobfamilie" | Pflege nur HR-Admin (403 getestet); Durchsetzung SERVERSEITIG bei jedem Speichern: fehlende Pflichtfragen wieder eingefügt, `isMandatory` erzwungen – Abschwächen unmöglich (getestet), unabhängig von UI/Übernahme/Import; `MINIMUM_STANDARD_CHANGED/_APPLIED`-Audit |
| UC-SB-29 | …einen schon mal genutzten Prozess bei neuen Stellen einfach wiederverwenden | Job-Wizard › „Bewährten Prozess übernehmen" + Bedarf-Convert | Prozess-Gedächtnis (Weg A) mit Spezifitäts-Leiter: gleiche **Abteilung** > **Einrichtung** > **Standort** > Jobfamilie (getestet: ältere Abteilungs-Stelle schlägt neuere fremde); Herkunft wird angezeigt; Kaltstart-Fallback aufs Regelwerk des Prozess-Beraters (`source=REGELWERK`, getestet); Bedarf→Entwurf automatisch; Weg B hinter Evidenz-Gate |
| UC-SB-27 | …dass Absagen würdevoll und automatisch kommuniziert werden | Kanban › Status REJECTED | Beim Übergang: echte Mail (Vorlage „Absage" mit {name}/{stelle}/{firma} oder würdevoller Standardtext) + Portal-Nachricht + Portal-Link; genau einmal je Bewerbung (getestet); Bulk-Absagen bewusst mail-frei |
| UC-SB-28 | …sehen, ob der Talent-Pool wirklich Stellen füllt | Talent-Pool › Kennzahlen | Aktive Einwilligungen, kürzlich abgelaufene, Hinweise (90 Tage) und **daraus entstandene Bewerbungen** (Konversion: Bewerbung derselben E-Mail auf die hingewiesene Stelle nach dem Hinweis); auch im KI-Analysten |
| UC-MB-09 | …dass abgelaufene Einwilligungen wirklich gelöscht werden | `purge_talent_pool` (Cron) | Löschung inkl. Ansprache-Historie nach 30 Tagen Kulanz (konfigurierbar); `TALENT_POOL_PURGED`-Audit; Kulanzfrist = Sichtbarkeitsfenster „kürzlich abgelaufen" für aktive Verlängerungs-Bitte |
| UC-SB-26 | …sehen, ob Selbstbuchung/Slots funktionieren – und was ich ändern sollte | `/recruiter/analytics/` › „Termine & Selbstbuchung" | Selbstbuchungs-Quote, Median bis Terminwahl, Abend/Wochenend-Anteil, Umbuchungen/Absagen/Änderungswünsche, Slot-Auslastung (genutzt/verfallen/offen), Formate-Verteilung + regelbasierte Handlungsvorschläge; nur Aggregate im BOLA-Scope (PII-frei getestet); Kennzahlen auch im lokalen KI-Analysten abfragbar |
| UC-SB-24 | …je Runde das passende Prüfformat wählen (Telefon, Video, vor Ort, Probearbeit, Assessment, schriftliche Aufgabe) | Einlade-Modal › Gesprächsformat | 6 Formate durchgängig: Modal, Slot-Anlage, Kalender-Badges, Portal, Erinnerung, .ics-Betreff; mehrstufige Runden möglich (vergangenes Gespräch blockiert Runde 2 nicht, getestet) |
| UC-SB-25 | …das Interview-Team zusammenstellen und automatisch informieren | Einlade-Modal › Interview-Team | Mehrfachauswahl interner Teilnehmender; sofortige Team-Mail bei Planung, Team-Erinnerung vor dem Termin an ALLE Beteiligten (getestet) |
| UC-SB-42 | …dass die Automatik echte Arbeit anstoßt (Aufgabe „Referenzen einholen") statt nur Mails zu senden | Einstellungen › Prozess-Automatik + Seite „Aufgaben" | CREATE_TASK legt Aufgabe für eine Rolle an (optional mit Frist), sichtbar nur für Zuständige im Zugriffsbereich (getestet), überfällig markiert, erledigbar |
| UC-SB-43 | …dass die Automatik Bewerbungen vorsortiert, aber NIEMALS selbst zu- oder absagt | Automatik › AUTO_ADVANCE | Autovorlauf nur nach NEW/IN_REVIEW/INVITED; HIRED und REJECTED hart gesperrt und als WORKFLOW_ACTION_BLOCKED protokolliert (getestet); keine Automatik-Ketten (getestet) |
| UC-SB-41 | …die gesamte Versionierungshistorie einer Job-Vorlage sichten, Versionen vergleichen (Diff) und eine alte Version wiederherstellen (Rollback) | `/recruiter/job-templates/` | Historie expandierbar; Änderungen werden als Zeilen-Diff angezeigt; Wiederherstellen erzeugt eine neue Version auf Basis der alten |
| UC-SB-42 | …sehen, welche Stellen mit welcher Version einer Vorlage verknüpft sind, und Stellen mit veralteten Vorlagen per Klick aktualisieren | `/recruiter/job-templates/` & Dashboard (Tab 2) | Liste verknüpfter Stellen pro Version sichtbar; Warn-Badge bei veralteten Vorlagen im Job-Manager; Ein-Klick-Update aktualisiert die Stelle auf die neueste Vorlagenversion |


### A2 · Tobias Klein — dezentraler Recruiter (eine Tochter) [TK]

> **Profil & Alltag:** 29, alleinverantwortlich für das Recruiting EINER Tochter; sieht per
> BOLA-Scope nur die eigenen Standorte. Arbeitet viel unterwegs, braucht schnelle Einzelaktionen
> statt Massenverwaltung. **Was neu für ihn gelöst ist:** eigene Anzeigen per Ein-Klick offline
> nehmen (fremde Standorte bleiben technisch unerreichbar), zentral gepflegte Ansprechpartner
> seiner Einrichtung stehen in der Job-Anlage vorausgewählt bereit.

| ID | Use Case | Seite / Flow | QA-Prüfkriterium || ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-TK-01 | …ausschließlich Bewerbungen meines Standorts sehen | Dashboard (BOLA) | Nur eigener Standort sichtbar |
| UC-TK-02 | …eine fremde Bewerbung NICHT öffnen können | `…/cv/`, `…/update-status/` | Fremdzugriff → 404 |
| UC-TK-03 | …meinen eigenen Standort-Workflow nutzen | Dashboard › Prozesse | Passender Workflow greift automatisch |
| UC-TK-04 | …eine Bewerbung sichten und Notiz ergänzen | Detail → `add-note` | Notiz gespeichert; im Verlauf sichtbar |
| UC-TK-05 | …ein Interview planen | `schedule_interview` / Kalender | Termin angelegt; im Kalender sichtbar |
| UC-TK-06 | …einen Kandidaten einladen | Kanban → Status INVITED | Status gesetzt; ggf. Automail ausgelöst |
| UC-TK-07 | …eine Stelle für meinen Standort anlegen | Jobs › anlegen | Vorbelegung auf eigenen Standort |
| UC-TK-08 | …Screening-Antworten einer Bewerbung prüfen | Bewerbungsdetail | Antworten Ja/Nein klar dargestellt |
| UC-TK-09 | …einen CV herunterladen | `…/cv/` | Nur eigener Standort; Audit-Eintrag |
| UC-TK-10 | …dem Bewerber eine Nachricht senden | `…/messages/` | Nachricht gespeichert (OUTBOUND) |
| UC-TK-11 | …meine Standort-KPIs sehen | `/recruiter/analytics/` (scoped) | Zahlen nur für eigenen Standort |
| UC-TK-12 | …eine Absage aussprechen | Status REJECTED | Grund erfassbar; protokolliert |
| UC-TK-13 | …NUR eigene Anzeigen schnell offline nehmen | Jobs › Toggle (BOLA) | Fremder Standort → 404 (getestet); eigener → sofort draft |

### A3 · Petra Wolf — HR-Sachbearbeitung, geteiltes Team [PW]

> **Profil & Alltag:** 51, teilt sich die Stelle mit einer Kollegin (Jobsharing, wechselnde
> Wochentage); Urlaubs- und Krankheitsvertretungen sind bei ihr Normalfall, nicht Ausnahme.
> **Schmerzpunkt (vorher):** vor jedem Urlaub mussten Ansprechpartner-Angaben in Dutzenden
> Anzeigen einzeln umgestellt werden. **Was neu gelöst ist:** Übergabe = zwei Aktionen –
> Delegation anlegen (Zuständigkeit) + „Überall ersetzen" (öffentliche Ansprechperson), beides
> revisionssicher protokolliert und in Minuten erledigt.

| ID | Use Case | Seite / Flow | QA-Prüfkriterium || ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-PW-01 | …Bewerbungen mit einer Kollegin aufteilen | `/recruiter/delegations/` | Delegation anlegbar; sichtbar |
| UC-PW-02 | …eine Urlaubsvertretung befristet einrichten | Delegationen (validFrom/Until) | Zeitfenster greift |
| UC-PW-03 | …nachvollziehen, wer welche Bewerbung bearbeitet hat | `/recruiter/audit/` | Nutzer + Aktion + Zeit sichtbar |
| UC-PW-04 | …Notizen kollaborativ ergänzen | `add-note` | Mehrere Notizen chronologisch |
| UC-PW-05 | …einen Statuswechsel dokumentiert durchführen | `update_status` + Audit | STATUS_CHANGE mit Nutzer geloggt |
| UC-PW-06 | …offene To-dos/Fristen sehen | ✅ Dashboard › „Heute wichtig" | Gebündelt: unbeantwortete Nachrichten (mit Direktlinks), überfällige Erstsichtungen, wartende Freigaben, heutige Gespräche, nachzutragende Ergebnisse, offene Bedarfe |
| UC-PW-07 | …Bewerber-Nachrichten beantworten | `…/messages/` | Verlauf + Senden funktioniert |
| UC-PW-08 | …fehlende Unterlagen nachfordern | Status MISSING_DOCS + Nachricht | Automatische/halbautomatische Nachforderung |
| UC-PW-09 | …einen CV prüfen | `…/cv/` | Download + Audit |
| UC-PW-10 | …die Screening-Fragen einer Stelle einsehen | Job-Detail | Fragen sichtbar |
| UC-PW-11 | …einen Interviewtermin koordinieren | Kalender | Slot buchbar |
| UC-PW-12 | …eine Übergabe dokumentieren | Delegation + Audit | Nachvollziehbar protokolliert |
| UC-PW-13 | …vor dem Urlaub die Ansprechperson in allen Anzeigen tauschen | Contacts › „Überall ersetzen" + Delegation | Beide Schritte ≤ 5 Min.; Audit vollständig; nach Rückkehr zurücktauschbar |

### A4 · Dr. Anja Reuter — HR-Leiterin & Prozess-Owner (Admin) [AR]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-AR-01 | …einen Workflow je Standort/Kategorie definieren | `save_app_workflow` | Spezifischster Workflow greift |
| UC-AR-02 | …ein Pflicht-Gate „Betriebsrat" erzwingen | Prozess-Engine | Gate blockiert bis Freigabe |
| UC-AR-03 | …den AGG-Check-Prompt zentral konfigurieren | KI-Einstellungen | Prompt gespeichert; wirkt global |
| UC-AR-04 | …KI-Tonalität/Sprache global setzen | `save_ai_settings` | Werte persistiert |
| UC-AR-05 | …Auto-Reject-Schwellen konfigurieren | KI-Einstellungen | Schwellen gespeichert; nur K.-o.-Kriterien |
| UC-AR-06 | …E-Mail-Vorlagen & Variablen pflegen | E-Mail & Variablen | CRUD funktioniert |
| UC-AR-07 | …Rollen je Nutzer zuweisen | Django-Admin › Groups | Rolle wirkt sofort (RBAC) |
| UC-AR-08 | …den BOLA-Scope eines Standortleiters setzen | Admin › UserScope | Scope begrenzt Sicht wie erwartet |
| UC-AR-09 | …System-Settings pflegen | `save_system_setting` | Nur HR-Admin; gespeichert |
| UC-AR-10 | …das Audit-Log auf Auffälligkeiten prüfen | `/recruiter/audit/` | Filter nach Aktion |
| UC-AR-11 | …die Screening-Fragen-Bank pflegen | `/recruiter/screening-questions/` | Anlegen/Archivieren |
| UC-AR-12 | …Job-Vorlagen kuratieren | `/recruiter/job-templates/` | Anlegen/Löschen |
| UC-AR-13 | …die Retention-Richtlinie prüfen | Command/Settings | Löschfrist konfigurierbar (Roadmap UI) |

### A5 · Ulrike Mayr — Ausbildungsleitung / Azubi-Recruiting [UM]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-UM-01 | …einen eigenen Azubi-Workflow anlegen | Prozesse | Workflow speicherbar |
| UC-UM-02 | …hunderte Bewerbungen im Kanban managen | Kanban | Performance/Übersicht bei Masse |
| UC-UM-03 | …ein Kennenlern-Event planen | Kalender/Slots | Event/Slots anlegbar |
| UC-UM-04 | …den Talent-Pool für den nächsten Jahrgang pflegen | ✅ Portal-Opt-in + `/recruiter/talent-pool/` | Bewerbende treten selbst bei (verifizierte Einwilligung via Magic-Link, 12 Monate); Austritt jederzeit; `TALENT_POOL_JOINED/_LEFT/_CONTACTED`-Audit |
| UC-UM-05 | …eine Azubi-Stelle mit eigener Vorlage ausschreiben | Job-Vorlagen | Vorlage nutzbar |
| UC-UM-06 | …Fristen/Erinnerungen im Blick behalten | ✅ Dashboard › „Heute wichtig" | s. UC-PW-06; Zähler bauen sich durch Erledigen ab (Nachricht öffnen = gelesen, getestet) |
| UC-UM-07 | …Screening-Fragen für Azubis definieren | Screening-Fragen | Fragen wiederverwendbar |
| UC-UM-08 | …Sammel-Zu-/Absagen aussprechen | ✅ Kanban-Mehrfachauswahl + Bulk-Aktionen | Umgesetzt (WP4) |
| UC-UM-09 | …zum Infotag einladen | Nachricht | Serien-Nachricht (Roadmap) |
| UC-UM-10 | …die Quellen der Azubi-Bewerbungen auswerten | Analytics › Quellen | Schul-/Kanalquellen sichtbar |
| UC-UM-11 | …CV/Zeugnisse prüfen | `…/cv/` | Download + Audit |
| UC-UM-12 | …die Ausschreibung in Leichte Sprache übertragen | KI › Leichte Sprache | Umformulierung erzeugt |
| UC-UM-13 | …Azubi-spezifische Textbausteine je Kategorie hinterlegen | `/recruiter/snippets/` (jobFamily-gebunden) | Baustein nur mit Kategorie-Kennung gelistet; einfügbar |

### A6 · Fatima El-Amrani — Praktikum & Werkstudierende [FA]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-FA-01 | …einen schlanken Kurz-Workflow nutzen | Prozesse | Kurzprozess definierbar |
| UC-FA-02 | …schnelle Zu-/Absagen aussprechen | Kanban/Status | Wenige Klicks |
| UC-FA-03 | …eine Hochschulmesse als Event managen | Kalender | Event anlegbar |
| UC-FA-04 | …den Talent-Pool für spätere Übernahme pflegen | ✅ s. UC-UM-04 | Kriterien aus bisherigen Bewerbungen – bei neuer passender Stelle schlägt die Seite die Ansprache vor |
| UC-FA-05 | …eine Werkstudenten-Stelle per Vorlage anlegen | Job-Vorlagen | Vorlage nutzbar |
| UC-FA-06 | …Bewerbungen nach Fachbereich filtern | Kanban Filter | Filter greift |
| UC-FA-07 | …Kandidaten für Übernahme markieren | Notiz/Pool | Markierung persistiert |
| UC-FA-08 | …CV prüfen | `…/cv/` | Download + Audit |
| UC-FA-09 | …Nachricht zum Praktikumsstart senden | Nachrichten | Versand ok |
| UC-FA-10 | …die Hochschul-Quellen auswerten | Analytics › Quellen | Quellen sichtbar |
| UC-FA-11 | …Studiennachweis im Screening prüfen | Job-Detail | Screening-Antwort sichtbar |
| UC-FA-12 | …fehlende Immatrikulationsbescheinigung nachfordern | Status MISSING_DOCS | Nachforderung möglich |

---

## Gruppe B — Fachbereich & Hiring

### A7 · Volkan Tas — Urlaubsvertretung / Stellvertretung [VT]

> ⚠️ Persona-Status: aus Anforderung abgeleitet (Vertretung darf Prozesse nie blockieren) — in Discovery-Gesprächen validieren.

Volkan ist Wohnbereichsleitung und vertritt die Pflegedienstleitung drei Wochen im Sommer und bei Krankheit. Er hat selbst nur Viewer-Rechte, soll aber in der Vertretungszeit deren Freigaben und Gremien-Stimmen übernehmen — nicht mehr, nicht länger, und alles nachvollziehbar. **Diese Persona ist bei jeder neuen Entscheidungs-Funktion mitzudenken und mitzutesten.**

| UC | Als Vertretung möchte ich… | Wo | Status/Notiz |
|---|---|---|---|
| UC-VT-01 | …befristet eingesetzt werden (von–bis), ohne dass jemand ans Beenden denken muss | `/recruiter/delegations/` | ✅ Pflicht-Zeitfenster bei Anlage; Ablauf wirkt serverseitig sofort überall (Postfach, Gremium) |
| UC-VT-02 | …vorzeitig deaktiviert werden können (früher zurück aus dem Urlaub) | Delegationen › „Beenden" | ✅ `validUntil=jetzt`, `DELEGATION_END`-Audit; Sofortwirkung getestet (Postfach leer, Sitz-Stimme zählt nicht mehr) |
| UC-VT-03 | …Freigaben der vertretenen Person sehen und entscheiden | Freigabe-Postfach | ✅ Badge „in Vertretung für X"; Entscheidung im Kommentar dokumentiert; Scope ALL/FACILITY/JOB serverseitig |
| UC-VT-04 | …Gremien-Stimmen für den Sitz der vertretenen Person abgeben | Freigaben › Gremium | ✅ Sitz-Logik; eigene Stimme des Mitglieds hat Vorrang bei Rückkehr |
| UC-VT-05 | …an ausstehende Entscheidungen der vertretenen Person erinnert werden | `send_decision_reminders` | ✅ Mail mit Präfix „In Vertretung für …", einmalig je Vorgang |
| UC-VT-06 | …dass meine Vertretungs-Handlungen klar zuordenbar bleiben | Audit | ✅ `for_seat`/Kommentar-Vermerk/`DELEGATION_*`-Audits — nie als die vertretene Person, immer als ich selbst in Vertretung |

### B1 · Prof. Dr. Martin Höfer — Chefarzt (Hiring Manager) [HF]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-HF-01 | …nur die mir zugewiesenen Fälle sehen | Dashboard (BOLA) | Keine fremden Bewerbungen sichtbar |
| UC-HF-02 | …mich für einen seltenen Zugriff schnell anmelden | `/recruiter/login/` | Login in ≤ 15 s, ohne Schulung |
| UC-HF-03 | …eine Bewerbung fachlich bewerten | Detail → `add-note` | Bewertung speicherbar |
| UC-HF-04 | …CV & Zeugnisse ansehen | `…/cv/` | Download nur mit Rolle; Audit |
| UC-HF-05 | …zwei Kandidaten vergleichen | Kanban/Detail | Vergleich ohne Umwege möglich |
| UC-HF-06 | …eine Empfehlung an HR geben | Notiz/Status | Empfehlung dokumentiert |
| UC-HF-07 | …Interview-Feedback erfassen | Interview outcome | Ergebnis speicherbar |
| UC-HF-08 | …mobil auf Bewerbungen zugreifen | Responsive UI | Nutzbar auf Smartphone |
| UC-HF-09 | …NICHT auf Systemkonfiguration zugreifen | RBAC | Konfig-Seiten → 403 |
| UC-HF-10 | …Screening-Antworten prüfen | Detail | Antworten klar |
| UC-HF-11 | …eine Freigabe im Workflow erteilen | Approval-Step | Freigabe wirkt; protokolliert |
| UC-HF-12 | …eine Rückfrage an den Recruiter stellen | Notiz | Recruiter sieht Rückfrage |
| UC-HF-16 | …automatisch per Mail gebeten werden, mein Feedback abzugeben, statt dass es untergeht | E-Mail nach dem Gespräch + Cron-Nachfassen | Bitte sofort bei „stattgefunden“ an alle Teilnehmer ohne Bewertung (getestet); Nachzuegler werden ab 2 Tagen einmalig erinnert (getestet); wer schon bewertet hat, wird nicht gefragt (getestet) |
| UC-HF-15 | …Bewerber in Sekunden per Prozent-Regler bewerten („Passt ins Team 80 %“) ohne Formular-Aufwand | Termine › Interview-Feedback | Slider 0–100 % je Aussage mit Live-Anzeige; Gesamteindruck und Empfehlung automatisch aus dem Schnitt (getestet), optional übersteuerbar; nur Regler ziehen + speichern genügt |
| UC-HF-14 | …mein Interview-Feedback strukturiert festhalten (Empfehlung, Kriterien, Stärken, Bedenken) statt es mündlich weiterzugeben | Termine › Interview-Feedback | Eine Bewertung je Person/Runde (änderbar, kein Duplikat – getestet); Bedenken als eigenes Feld, das bei Folgerunde und finaler Entscheidung sichtbar ist |
| UC-HF-13 | …wissen, ob meine Stimme allein schon reicht oder ob ich auf Kolleg:innen warten muss | Bewerbungsdetail › Gremiums-Status | Klartext „N von M (Quorum)" bzw. „Mehrheit von N"; bei erfülltem Quorum sofort freigegeben, ohne auf alle Stimmen zu warten (getestet) |

### B2 · Melanie Dorn — Pflegedienstleitung [MD]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-MD-01 | …meinen Personalbedarf melden | ✅ `/recruiter/bedarf/` | Strukturierte Meldung (Titel, Einrichtung, Anzahl, Wunschstart, Begründung) statt Zuruf; Recruiter/HR-Admin entscheiden mit Anmerkung, Melder:in wird gemailt; `STAFFING_REQUEST_*`-Audit (getestet inkl. Rollen-Trennung) |
| UC-MD-02 | …dass aus meinem angenommenen Bedarf ohne Umwege eine Ausschreibung wird | ✅ Bedarf › „Als Entwurf anlegen" | Ein Klick + Standortwahl → unveröffentlichter Entwurf mit Titel/Einrichtung/Bereich; interne Begründung bleibt intern (getestet); Freigabe-Gate öffnet bei zustimmungspflichtigen Einrichtungen automatisch; Traceability `convertedJob`; nicht doppelt konvertierbar |
| UC-MD-02 | …den Status meiner offenen Stellen verfolgen | Dashboard (scoped) | Nur eigene Station |
| UC-MD-03 | …eine Pflegekraft-Bewerbung bewerten | Notiz | Bewertung speicherbar |
| UC-MD-04 | …CV prüfen | `…/cv/` | Download + Audit |
| UC-MD-05 | …ein Interview planen | Kalender | Termin anlegbar |
| UC-MD-06 | …einen Kandidaten einladen | Status INVITED | Status gesetzt |
| UC-MD-07 | …eine Rückfrage an HR stellen | Notiz/Nachricht | Sichtbar für HR |
| UC-MD-08 | …nur meine Station sehen | BOLA | Fremdzugriff verwehrt |
| UC-MD-09 | …eine Freigabe erteilen | Workflow | Freigabe wirkt |
| UC-MD-10 | …die KPIs meiner Station sehen | Analytics (scoped) | Zahlen nur Station |
| UC-MD-11 | …Screening prüfen | Detail | Antworten sichtbar |
| UC-MD-12 | …eine Absage anstoßen | Status REJECTED | Protokolliert |
| UC-MD-13 | …Personalbedarf melden und dabei nur die für meinen Bereich wirklich nötigen Zusatzfragen beantworten | Bedarf › Antragsformular | Formular passt sich automatisch an Einrichtung/Abteilung/Kategorie an (Routing-Matrix-Regel); ohne passende Regel Standardformular (getestet) |
| UC-MD-14 | …sehen, in welcher Genehmigungsstufe mein Antrag gerade hängt | Bedarf › „Meine Meldungen" | Stufenleiste zeigt jede Rolle mit Status (ausstehend/genehmigt/zurückgegeben), keine Raterei mehr |
| UC-MD-15 | …bei einer Rückfrage nachbessern, ohne den Antrag neu zu schreiben | Bedarf › „Erneut einreichen" nach Rückgabe | Ursprüngliche Angaben vorausgefüllt; nach Absenden startet die Kette korrekt von vorn (getestet) |
| UC-MD-16 | …per Mail erfahren, sobald über meinen Antrag entschieden wurde | E-Mail-Benachrichtigung | Mail bei Genehmigung/Ablehnung/Rückgabe, inkl. Kommentar der entscheidenden Stelle (getestet) |
| UC-MD-17 | …aus meinem genehmigten Bedarf direkt die Ausschreibung starten, ohne alles neu einzutippen | Bedarf › „Als Entwurf anlegen" | Titel, Einrichtung, Jobfamilie und Stellen-Anzahl werden übernommen (getestet) |

### B3 · Jens Hartmann — IT-Teamlead als Fachgutachter [JH]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-JH-01 | …Coding-Skills mit KI-Kompetenzextraktion bewerten | KI/Detail | Skills extrahiert dargestellt |
| UC-JH-02 | …mehrere Kandidaten vergleichen | Kanban | Vergleich möglich |
| UC-JH-03 | …CV & Zertifikate prüfen | `…/cv/` | Download + Audit |
| UC-JH-04 | …eine technische Bewertung als Notiz erfassen | `add-note` | Notiz speicherbar |
| UC-JH-05 | …Interview-Feedback geben | Interview outcome | Ergebnis speicherbar |
| UC-JH-06 | …nur zugewiesene Fälle sehen | BOLA | Scope greift |
| UC-JH-07 | …eine Empfehlung abgeben | Status/Notiz | Dokumentiert |
| UC-JH-08 | …technische Screening-Fragen prüfen | Detail | Antworten sichtbar |
| UC-JH-09 | …eine Freigabe erteilen | Workflow | Freigabe wirkt |
| UC-JH-10 | …eine Nachricht an den Recruiter senden | Notiz | Sichtbar |
| UC-JH-11 | …auf Desktop und mobil arbeiten | Responsive | Nutzbar |
| UC-JH-12 | …keinen Zugriff auf Settings haben | RBAC | 403 auf Konfig |
| UC-JH-13 | …erinnert werden, wenn eine Abstimmung überfällig ist und dringend meine Stimme fehlt | Freigabe-Postfach › Frist-Badge + Eskalations-Mail | Rotes Badge „Frist überschritten (X/Y Tage)"; Eskalations-Mail einmalig, kein Spam bei mehrfachem Cron-Lauf (getestet) |

---

### B4 · Rasmus Voigt — Bereichsleiter IT (Antragsteller UND erste Genehmiger-Instanz) [RV]

> **Profil & Alltag:** 44, verantwortet den Bereich „IT & Digital Banking" über mehrere
> Abteilungen hinweg. Für sein eigenes Team ist er selbst **Antragsteller** von
> Personalbedarf; für Anträge seiner Teamleitungen ist er die **erste Genehmigungsstufe**
> der Kette, bevor es zur Geschäftsführung weitergeht. **Schmerzpunkte (vorher):**
> Neuanstellungsanfragen kamen per Mail, ohne einheitliche Angaben, ohne Nachverfolgung –
> „wurde das eigentlich schon genehmigt?" war eine Dauerfrage. **Was SecurATS ihm jetzt
> gibt:** strukturierte Anträge mit den für seinen Bereich per Routing-Matrix-Regel
> festgelegten Zusatzfragen (z. B. Tech-Stack, Budget-Herkunft), eine Stufenleiste mit
> genau seiner Rolle als nächstem Schritt, Genehmigen/Rückgabe/Ablehnen mit einem Klick.

| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-RV-01 | …als Bereichsleiter selbst Personalbedarf für mein Team melden | Bedarf › Antrag | Formular inkl. bereichsspezifischer Zusatzfragen (Routing-Matrix-Regel greift automatisch) |
| UC-RV-02 | …bei Anträgen meiner Teamleitungen nur dann entscheiden dürfen, wenn ich wirklich an der Reihe bin | Bedarf › Eingegangene Meldungen | Nur die Rolle der aktuell fälligen Stufe darf entscheiden; vorzeitiger Versuch wirkungslos (getestet) |
| UC-RV-03 | …bei fachlichen Rückfragen den Antrag zur Nachbesserung zurückgeben statt ihn abzulehnen | Stufen-Entscheid › „Zur Nachbesserung" | Antrag geht mit Kommentar zurück an den Antragsteller; Kette startet nach Neueinreichung von vorn (getestet) |
| UC-RV-04 | …auf einen Blick sehen, welche Zusatzangaben der Antragsteller gemacht hat, bevor ich entscheide | Eingegangene Meldungen › „Formular-Angaben" | Antworten des Regel-Formulars aufklappbar sichtbar (z. B. Tech-Stack, Budgetquelle) |
| UC-RV-05 | …einen Antrag endgültig ablehnen, wenn der Bedarf fachlich nicht trägt | Stufen-Entscheid › „Ablehnen" | Bestätigungsdialog; Status endgültig, Antragsteller wird informiert (getestet) |
| UC-RV-06 | …als Genehmiger die fälligen Anträge in der Eingangs-Liste sehen, auch ohne Recruiter-Rolle | Bedarf › Eingegangene Meldungen | Ketten-Rollen sehen Anträge ihrer fälligen Stufe + eigene bereits entschiedene (Nachvollziehbarkeit) – vorher konnten sie formal entscheiden, fanden aber nichts (Lücke geschlossen, getestet) |
| UC-RV-12 | …automatisch erinnert werden, wenn ein Antrag zu lange auf meiner Stufe liegt | Cron send_decision_reminders | Einmalige Erinnerung ab N Tagen Wartezeit (Default 3), Wartezeit fair ab Vorstufen-Abschluss gerechnet (getestet); aktive Vertretungen mit passendem Scope erhalten sie mit „In Vertretung für X“-Hinweis (getestet); kein Doppelversand (Einmal-Marker, getestet) |
| UC-RV-11 | …sofort per Mail erfahren, wenn ein Antrag auf MEINE Stufe wartet | E-Mail „Stellenfreigabe wartet auf Ihre Entscheidung“ | Ereignisgetrieben beim Fälligwerden (Anlage / Vorgruppe komplett / Wiedervorlage); parallele Gruppen: ein Versand je Gruppe, Einzel-Entscheidungen innerhalb der Gruppe lösen keine neue Mail aus (getestet); aktive Vertretungen mit passendem Scope erhalten die Mail mit „als Vertretung von X“-Hinweis (getestet) |
| UC-RV-07 | …dass meine Entscheidung nachvollziehbar protokolliert wird | Audit-Log | `REQUISITION_STEP_DECIDED` mit Rolle, Person, Kommentar |
| UC-RV-08 | …für Standard-Rollen (z. B. Filiale) keine unnötige Mehrstufigkeit erdulden müssen | Routing-Matrix (Admin-Konfiguration) | Regel „Standard" kann 1-stufig oder optional sein – nur der Tech-Bereich hat die volle Kette |
| UC-RV-09 | …nach meiner Genehmigung sofort sehen, dass der Antrag zur nächsten Stufe weitergeht | Stufenleiste | Eigene Stufe zeigt „✓ genehmigt", nächste Rolle erscheint als ausstehend |
| UC-RV-10 | …aus einem vollständig genehmigten Bedarf die Ausschreibung selbst starten können | Bedarf › „Als Entwurf anlegen" | Konvertierung inkl. Stellen-Anzahl aus dem Bedarf übernommen (getestet) |

### B5 · Nina Berger — Teammitglied im Auswahlteam (Interviewerin) [NB]

> **Profil & Alltag:** 34, examinierte Pflegefachkraft und stellvertretende
> Stationsleitung. Sitzt regelmäßig in Bewerbungsgesprächen mit – nicht als
> Recruiterin, sondern als künftige Kollegin, die einschätzt, ob jemand fachlich
> und menschlich ins Team passt. **Schmerzpunkte (vorher):** Nach dem Gespräch
> ging es zurück auf Station, das Feedback wurde „später mal" mündlich
> weitergegeben – und war bei der Entscheidung oft vergessen oder verwässert.
> Bedenken („wirkte gestresst, als es um Nachtdienste ging") verpufften, weil
> niemand sie festhielt. **Was SecurATS ihr jetzt gibt:** eine Mail direkt nach
> dem Gespräch mit der Bitte um Feedback, ein Formular, das in einer Minute per
> Prozent-Regler ausgefüllt ist, und die Gewissheit, dass ihre Einschätzung –
> besonders ihre Bedenken – bei der zweiten Runde und der finalen Entscheidung
> sichtbar ist.

| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-NB-01 | …nach einem Gespräch automatisch gebeten werden, mein Feedback abzugeben | E-Mail „Bitte um Feedback" | Geht bei „stattgefunden" an alle Teilnehmer ohne Bewertung, mit Direktlink (getestet); wer schon bewertet hat, wird nicht gefragt (getestet) |
| UC-NB-02 | …den Bewerber in unter einer Minute strukturiert bewerten, ohne Formular-Frust | Termine › Interview-Feedback | Prozent-Regler je Aussage („Passt ins Team 80 %") mit Live-Anzeige; Gesamteindruck automatisch (getestet) |
| UC-NB-03 | …eine klare Empfehlung abgeben, ohne lange nachzudenken | Feedback › Empfehlung | Wird aus dem Schnitt abgeleitet (getestet), optional übersteuerbar (Veto trotz gutem Score – getestet) |
| UC-NB-04 | …ausdrücklich Bedenken festhalten, die sonst untergehen | Feedback › Bedenken-Feld | Eigenes, hervorgehobenes Feld; erscheint bei Folgerunde und finaler Entscheidung, warnt beim Einstellen (getestet) |
| UC-NB-05 | …zusätzlich frei formulieren, was in kein Kriterium passt | Feedback › Stärken + Anmerkungen (Freitext) | Mehrere Freitextfelder, mehrzeilig |
| UC-NB-06 | …dass mehrere Kolleg:innen unabhängig denselben Bewerber bewerten | Feedback (mehrfach) | Eine Rückmeldung je Person/Runde, alle nebeneinander sichtbar (getestet) |
| UC-NB-07 | …mein bereits abgegebenes Feedback korrigieren, wenn ich mich vertan habe | Feedback erneut speichern | Aktualisiert die eigene Bewertung statt Duplikat (getestet), auditiert |
| UC-NB-08 | …erinnert werden, wenn ich mein Feedback vergessen habe | Cron `send_feedback_requests` | Einmalige Erinnerung ab 2 Tagen nach dem Gespräch (getestet), kein Spam (getestet) |
| UC-NB-09 | …das Feedback der Kolleg:innen aus der ersten Runde sehen, bevor ich in die zweite gehe | Termine › Feedback nach Runde | Nach Runde gruppiert, Bedenken rot hervorgehoben |
| UC-SB-41 | …beim Öffnen eines Kandidaten sofort den Team-Eindruck aus den Interviews sehen | Kanban › Kandidaten-Detail | Modal lädt strukturiertes Feedback (nach Runde, Prozente, Bedenken rot) beim Öffnen; BOLA-gescoped (getestet 404) |
| UC-NB-10 | …auch vom Handy zwischen zwei Diensten bewerten | Responsive | Regler und Felder mobil bedienbar |
| UC-NB-11 | …nur Bewerbungen in meinem Bereich sehen und bewerten können | BOLA | Feedback nur im Zugriffsbereich speicherbar (getestet 404) |

## Gruppe C — Governance & Mitbestimmung

### C1 · Jürgen Faber — Betriebsratsvorsitzender [JF]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-JF-01 | …bei zustimmungspflichtigen Vorgängen eingebunden werden | Workflow-Gate | Gate erscheint automatisch |
| UC-JF-02 | …digital freigeben oder ablehnen | Approval | Entscheidung erfassbar |
| UC-JF-03 | …dass meine Freigabe protokolliert wird | Audit | Eintrag mit Nutzer/Zeit |
| UC-JF-04 | …dass der Prozess bis zur Freigabe blockiert bleibt | Workflow-Enforcement | Kein Fortschritt ohne Freigabe |
| UC-JF-05 | …die Historie eines Vorgangs einsehen | Audit/Verlauf | Nachvollziehbar |
| UC-JF-06 | …sehen, welche Vorgänge auf mich warten | ✅ `/recruiter/approvals/` „wartet auf mich" | Umgesetzt (WP6) |
| UC-JF-07 | …eine Rückfrage/Kommentar hinterlegen | Approval-Kommentar | Kommentar gespeichert |
| UC-JF-08 | …nur mitbestimmungsrelevante Daten sehen | RBAC/Datenminimierung | Kein PII-Vollzugriff |
| UC-JF-09 | …Fristen einhalten | ✅ Approval-Postfach mit SLA-Frist | Umgesetzt (WP6) |
| UC-JF-10 | …einen Mitbestimmungs-Nachweis exportieren | ✅ `/recruiter/audit/export.csv` (HR-Admin erstellt auf Anforderung) | CSV mit Zeitraum-/Aktions-Filter; Integritäts-Kopfzeile (Hash-Kette INTAKT/VERLETZT); Export selbst auditiert |
| UC-JF-11 | …mich sicher anmelden | Login | Auth erforderlich |
| UC-JF-12 | …keine unnötigen Bewerberdaten sehen | Scoping | Nur Notwendiges |

### C2 · Katrin Sommer — Schwerbehindertenvertretung / Inklusion [KS]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-KS-01 | …bei relevanten Bewerbungen automatisch eingebunden werden | Workflow | Gate greift |
| UC-KS-02 | …die Nutzung der Barrierefreiheits-Funktionen sehen | Analytics › Inklusion (Roadmap) | Nutzungszahlen sichtbar |
| UC-KS-03 | …den Ausgleichsabgabe-ROI verfolgen | KPIs › Inklusions-ROI | Ersparnis berechnet |
| UC-KS-04 | …schwerbehinderte Talente gezielt fördern | Kennzeichnung (Roadmap) | Markierung möglich |
| UC-KS-05 | …meine Einbindung nachweisen | Audit | Eintrag vorhanden |
| UC-KS-06 | …eine Leichte-Sprache-Ausschreibung prüfen | KI › Leichte Sprache | Variante erzeugbar |
| UC-KS-07 | …eine Freigabe/Kommentar abgeben | Workflow | Wirkt; protokolliert |
| UC-KS-08 | …den Conversion-Uplift durch Barrierefreiheit sehen | Analytics (Roadmap) | Kennzahl sichtbar |
| UC-KS-09 | …nur relevante Daten sehen | RBAC | Datenminimierung |
| UC-KS-10 | …mich sicher anmelden | Login | Auth |
| UC-KS-11 | …das barrierefreie Bewerberportal testen | Accessibility-Panel | A11y-Funktionen greifen |
| UC-KS-12 | …einen Report zur Schwerbehinderten-Quote erstellen | Analytics-Export (Roadmap) | Export erzeugbar |

### C3 · Michael Braun — Datenschutzbeauftragter (DSB) [MB]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-MB-01 | …jeden CV-Zugriff im Audit-Log prüfen | `/recruiter/audit/` | `READ_CV` mit Nutzer sichtbar |
| UC-MB-02 | …die automatische Löschung nachweisen | `data_retention` | Löschlauf belegbar |
| UC-MB-03 | …die Einwilligungs-Abdeckung prüfen | PrivacyNotice/Consent | Version je Bewerbung |
| UC-MB-04 | …bestätigen, dass keine externen Datenflüsse bestehen | Air-Gap | Kein Cloud-Call im Datenpfad |
| UC-MB-05 | …die Verschlüsselung at-rest prüfen | Encrypted Fields | PII verschlüsselt gespeichert |
| UC-MB-06 | …Löschfristen konfigurieren | Settings | Frist einstellbar (Roadmap UI) |
| UC-MB-07 | …eine Betroffenenauskunft erstellen | ✅ `export_applicant`-Command (DSGVO Art. 15) | Umgesetzt (WP2) |
| UC-MB-08 | …Zugriffsprotokolle exportieren | ✅ `/recruiter/audit/export.csv` | s. UC-JF-10; z. B. `?action=READ_CV&von=…&bis=…` |
| UC-MB-09 | …die Wirksamkeit des BOLA-Scopings prüfen | Scope-Test | Fremdzugriff → 404 |
| UC-MB-10 | …die Datenminimierung prüfen | Felder/Formulare | Nur nötige Felder |
| UC-MB-11 | …mich sicher anmelden | Login | Auth |
| UC-MB-12 | …einen Vorfall nachvollziehen | Audit | Lückenlose Kette |

---

## Gruppe D — IT & Sicherheit

### D1 · Sven Ostermann — IT-Administrator / Betrieb [SO]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-SO-01 | …die App per docker-compose deployen | `infrastructure/deploy.sh` | Ein Befehl; Container läuft |
| UC-SO-02 | …den ersten Admin anlegen | `bootstrap_auth` | Admin + Rollen erstellt |
| UC-SO-03 | …Secrets sicher via .env setzen | `.env` | Kein hartcodiertes Secret |
| UC-SO-04 | …ein Backup einrichten | `backup-cron.sh` | Backup erzeugt |
| UC-SO-05 | …einen Restore testen | `emergency-restore.sh` | Wiederherstellung klappt |
| UC-SO-06 | …den Ollama-/KI-Status prüfen | Dashboard › KI-Zentrale | Status ONLINE/OFFLINE sichtbar |
| UC-SO-07 | …Migrationen anwenden | `manage.py migrate` | Fehlerfrei |
| UC-SO-08 | …Logs auf Fehler prüfen | Logging | Aussagekräftige Logs |
| UC-SO-09 | …den Air-Gap-Betrieb sicherstellen | Netz-Konfig | Keine Außenverbindung nötig |
| UC-SO-10 | …HTTPS/HSTS in Produktion aktivieren | Settings (DEBUG=False) | Sichere Cookies/HSTS aktiv |
| UC-SO-11 | …Nutzer/Rollen verwalten | Django-Admin | CRUD möglich |
| UC-SO-12 | …ein Update ohne langen Ausfall einspielen | Deploy | Rebuild + Recreate |

### D2 · Nadine Schulz — CISO (KRITIS/DORA) [NS]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-NS-01 | …verifizieren, dass keine Daten das Haus verlassen | Air-Gap-Test | Kein externer Call |
| UC-NS-02 | …die Vollständigkeit des Audit-Logs prüfen | Audit | Sensible Aktionen geloggt |
| UC-NS-03 | …die Wirksamkeit von RBAC/BOLA prüfen | Scope/Rollen | 403/404 wie erwartet |
| UC-NS-04 | …das Secrets-Handling prüfen | `.env`/Settings | Keys nur aus Env |
| UC-NS-05 | …CSRF-/Session-Härtung prüfen | Settings | CSRF aktiv; Secure-Cookies |
| UC-NS-06 | …die Angriffsfläche minimieren | ✅ `FEED_ACCESS_TOKEN` erzwungen | Umgesetzt (WP2) |
| UC-NS-07 | …den Backup-Vault prüfen | Backup | Verschlüsselt/off-site |
| UC-NS-08 | …einen DR-Test durchführen | Restore | Wiederanlauf belegbar |
| UC-NS-09 | …das Dependency-Risiko bewerten | Ein-Stack-Architektur | Keine Parallel-Stacks aktiv |
| UC-NS-10 | …einen Zugriffsrollen-Review machen | Admin | Rollen überprüfbar |
| UC-NS-11 | …die Login-Sicherheit prüfen | Auth | Passwort-Policy greift |
| UC-NS-12 | …einen Compliance-Nachweis erzeugen | ✅ `/recruiter/audit/export.csv` + `verify_audit` | Datei-Nachweis mit Ketten-Status |
| UC-NS-13 | …dass das System vor Markteintritt einem Pentest/Bug-Hunt standhält | Sicherheits-Audit (SECURITY_AUDIT.md) | OWASP-Review: Open-Redirect, fehlende Auth/BOLA und Demo-Backdoor behoben und mit Regressionstests fixiert; kein SQL-Injection/XSS/Secret-Fund (dokumentiert) |

---

## Gruppe E — Leitung

### E1 · Christian Vogt — Geschäftsführer [CV]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-CV-01 | …einen Live-Überblick über alle Standorte | `/recruiter/analytics/` | Aggregierte Sicht |
| UC-CV-02 | …die Time-to-Hire je Tochter sehen | Analytics | Kennzahl vorhanden |
| UC-CV-03 | …Funnel-Abbrüche erkennen | Analytics › Funnel | Abbruchpunkte sichtbar |
| UC-CV-04 | …die Zahl offener Stellen sehen | Dashboard | Kennzahl sichtbar |
| UC-CV-05 | …den Kanal-Erfolg bewerten | Analytics › Quellen | Quellen-Vergleich |
| UC-CV-06 | …KPIs exportieren | ✅ `/recruiter/analytics/export.csv` | Umgesetzt (WP5, auditiert) |
| UC-CV-07 | …Standorte vergleichen | Analytics | Vergleich sichtbar |
| UC-CV-08 | …den Inklusions-ROI sehen | KPIs | Ersparnis sichtbar |
| UC-CV-09 | …mich schnell anmelden und alles Wichtige sehen | Login + Dashboard | ≤ 2 Klicks zur Übersicht |
| UC-CV-10 | …keine operative Konfiguration vornehmen müssen | RBAC (Viewer) | Read-fokussiert |
| UC-CV-11 | …Trends über Monate sehen | Analytics › Verlauf | Zeitreihe |
| UC-CV-12 | …einen wöchentlichen Report erhalten | ✅ `weekly_report`-Command (Cron) | Umgesetzt (WP6) |
| UC-CV-13 | …auf einen Blick sehen, wie lange Einstellungen dauern und was sie kosten – über alle Töchter | Analytics › Einstellungen | Karte „Einstellungen" (Anzahl + Ø Tage), Kosten je Einstellung je Kanal/Kampagne, kein Bytes-Abfluss an Cloud-BI |
| UC-CV-15 | …auf einen Blick per Ampel sehen, welche Freigabestufe kritisch langsam ist | Analytics › „Welche Stufe bremst?“ | Farbpunkt je Stufe: grün ≤ 3, gelb 4–7, rot > 7 Tage; bewertet die schlechtere aus Ø-Wartezeit und ältestem offenen Antrag (getestet) |
| UC-CV-14 | …erkennen, ob eine Genehmigungskette Einstellungen konzernweit ausbremst | Analytics › „Welche Stufe bremst?“ | Ø Wartetage je Rolle (fällig → entschieden), Engpass-Badge an der langsamsten Stufe, aktuell fällige offene Anträge mit Alter; parallele Gruppen korrekt (Fälligkeit ab letzter Vorgruppen-Entscheidung, getestet); BOLA-gescoped |

### E2 · Birgit Lang — CFO [BL]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-BL-01 | …den Ausgleichsabgabe-Tracker sehen | KPIs › Inklusions-ROI | Live-Ersparnis |
| UC-BL-02 | …die Kosten pro Einstellung sehen | ✅ Analytics (nur Leitung, `SOURCE_COST_*`) | Umgesetzt (WP5) |
| UC-BL-03 | …bestätigen, dass keine Pro-Sitz-Lizenzkosten anfallen | Open-Source-Modell | Keine Lizenzgebühr |
| UC-BL-04 | …das Equal-Pay-/Haftungsrisiko im Blick haben | Compliance | Nachweise vorhanden |
| UC-BL-05 | …Bußgeld-Vermeidung belegen | Audit/Compliance | Nachweisbar |
| UC-BL-06 | …Effizienz-Kennzahlen sehen | Analytics | Durchlaufzeiten |
| UC-BL-07 | …einen ROI-Report exportieren | Export (Roadmap) | Erzeugbar |
| UC-BL-08 | …mich anmelden und KPIs sehen | Login + KPIs | Schnell |
| UC-BL-09 | …Standort-Kosten vergleichen | Analytics | Vergleich |
| UC-BL-10 | …Trends sehen | Verlauf | Zeitreihe |
| UC-BL-11 | …nur lesend zugreifen | RBAC (Viewer) | Read-only |
| UC-BL-12 | …die Inklusions-Einsparung beziffern | ROI | Betrag sichtbar |

### E3 · Holger Rittmann — Standortleiter (ohne HR-Funktion) [HR]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-HR-01 | …nur meinen Standort sehen | BOLA | Scope greift |
| UC-HR-02 | …die offenen Stellen meines Standorts sehen | Dashboard (scoped) | Nur eigener Standort |
| UC-HR-03 | …den Pipeline-Status verfolgen | Kanban (scoped) | Übersicht |
| UC-HR-04 | …Freigaben erteilen | Workflow | Freigabe wirkt |
| UC-HR-05 | …die App ohne HR-Wissen bedienen | Usability | Ohne Schulung nutzbar |
| UC-HR-06 | …die KPIs meines Standorts sehen | Analytics (scoped) | Nur Standort |
| UC-HR-07 | …mich für den Einmal-Zugriff anmelden | Login | Schnell |
| UC-HR-08 | …keine Systemkonfiguration sehen | RBAC | 403 auf Konfig |
| UC-HR-09 | …Interview-Termine meines Standorts sehen | Kalender (scoped) | Nur Standort |
| UC-HR-10 | …einen CV prüfen | `…/cv/` (scoped) | Download + Audit |
| UC-HR-11 | …eine Rückfrage an HR stellen | Notiz | Sichtbar für HR |
| UC-HR-12 | …dass Pflicht-Gates automatisch greifen | Workflow | Gates erzwungen |

---

### E4 · Dr. Elke Winter — Vorstandsmitglied / Aufsichtsratsmandat (finale Freigabe-Instanz) [EW]

> **Profil & Alltag:** 56, sitzt im Vorstand einer Bankengruppe und in zwei
> Aufsichtsratsmandaten. Entscheidet nur selten, aber bei strategisch wichtigen oder
> besonders kostenintensiven Neueinstellungen (z. B. Führungspositionen, große
> Team-Aufstockungen) als letzte Instanz einer Genehmigungskette – neben ihrem
> eigentlichen Tagesgeschäft, meist mobil zwischen Terminen. **Schmerzpunkte (vorher):**
> Personalanfragen erreichten sie unstrukturiert per Mail-Anhang, ohne Kontext, ohne
> Historie der vorherigen Genehmigungsstufen – Entscheidungen fühlten sich blind an.
> **Was SecurATS ihr jetzt gibt:** eine klare, mobil bedienbare Entscheidungsseite mit
> allen vorherigen Genehmigungen, Kommentaren und der Begründung des Antrags sichtbar,
> bevor sie unterschreibt – in Minuten statt E-Mail-Ketten.

| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-EW-01 | …als letzte Instanz einer mehrstufigen Kette nur entscheiden, wenn alle vorherigen Stufen bereits zugestimmt haben | Bedarf › Stufen-Entscheid | Meine Stufe wird erst „ausstehend", wenn alle vorherigen Rollen genehmigt haben (sequenziell erzwungen, getestet) |
| UC-EW-02 | …vor meiner Entscheidung die Begründung und alle bisherigen Genehmigungen mit Kommentaren sehen | Bedarf › Eingegangene Meldungen | Stufenleiste + Antrags-Begründung + Formular-Angaben vollständig sichtbar |
| UC-EW-03 | …eine Neuanstellung mit einem Klick genehmigen, auch unterwegs vom Smartphone | Stufen-Entscheid (responsive) | Formular funktioniert ohne Zusatz-Software auf mobilen Geräten |
| UC-EW-04 | …bei Unklarheiten den Antrag mit einer klaren Begründung zurückgeben, statt ihn selbst zu recherchieren | „Zur Nachbesserung" + Kommentarfeld | Antragsteller erhält meinen Kommentar direkt per Mail |
| UC-EW-05 | …sicher sein, dass meine Entscheidung nicht durch eine tiefere Ebene nachträglich verändert werden kann | Sequenzielle Kette + Audit-Log | Niedrigere Stufen können eine abgeschlossene höhere Stufe nicht überschreiben |
| UC-EW-06 | …dass jede meiner Entscheidungen unveränderlich protokolliert wird (Beweislast Vorstandspflichten) | Audit-Log | `REQUISITION_STEP_DECIDED` mit Zeitstempel, Rolle, Kommentar – nicht nachträglich editierbar |
| UC-EW-07 | …bei Abwesenheit (Vorstandssitzung, Reise) nicht zum alleinigen Flaschenhals werden | Vertretung/Delegation (aktiv, gleiche Mechanik wie Gremien-Vertretung) | Aktive Vertretung darf die fällige Stufe entscheiden (Zeitfenster + Einrichtungs-Scope serverseitig, getestet); Entscheidung trägt sichtbares „i. V.“-Kennzeichen und Audit mit Vertretenem; abgelaufene oder scope-fremde Vertretung wirkungslos (getestet) |
| UC-EW-10 | …meine Vertretung selbst anlegen und beenden, ohne HR bitten zu müssen | Delegationen (Selbstbedienung) | Jede Rolle verwaltet eigene Vertretungen (Anlage delegator=self erzwungen, fremde nicht beend-/einsehbar, Selbst-Delegation abgelehnt – alles getestet); Assistenz-Fall: HR-Admin legt im Namen an, auditiert als on_behalf, wirkt end-to-end in der Kette (getestet) |
| UC-EW-08 | …nur die Anträge sehen, für die meine Rolle tatsächlich die entscheidende Instanz ist – keine operative Alltagsflut | Bedarf › Eingegangene Meldungen (rollenscharf) | Sichtbarkeit strikt an die Kettenrolle gebunden, kein genereller Admin-Zugriff nötig |
| UC-EW-09 | …darauf vertrauen, dass eine von mir abgelehnte Stelle nicht doch heimlich veröffentlicht wird | Requisition-Gate an allen Veröffentlichungspunkten | Wizard, Schnell-Toggle UND finale Job-Freigabe blockieren ohne genehmigten Bedarf (alle drei getestet) |

## Gruppe F — Bewerbende

### F1 · Leon Krüger — Bewerber mit Legasthenie & ADHS [LK]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-LK-01 | …das Barrierefreiheits-Panel öffnen | Accessibility-Switcher | Panel erreichbar |
| UC-LK-02 | …eine Legasthenie-freundliche Schrift aktivieren | A11y | Schrift wechselt |
| UC-LK-03 | …einen Fokus-/Lesemodus nutzen | A11y | Ablenkung reduziert |
| UC-LK-04 | …mir Texte vorlesen lassen | A11y | Vorlesen funktioniert |
| UC-LK-05 | …eine Ausschreibung in Leichter Sprache lesen | Seite/Job | Variante verfügbar |
| UC-LK-06 | …eine passende Stelle finden | `/jobs/` | Suche/Filter |
| UC-LK-07 | …die Bewerbung ohne Überforderung ausfüllen | `bewerben` | Klar, schrittweise |
| UC-LK-08 | …meinen Lebenslauf hochladen | `bewerben` | Upload funktioniert |
| UC-LK-09 | …meinen Status im Portal prüfen | `/bewerber/<token>/` | Status verständlich |
| UC-LK-10 | …mich passwortlos anmelden | Magic-Link | Kein Passwort nötig |
| UC-LK-11 | …eine Rückfrage beantworten | ✅ Portal › Nachrichten | Thread beider Richtungen sichtbar, Antwort als INBOUND + Mail an Ansprechperson (getestet) |
| UC-LK-12 | …meine Bewerbung zurückziehen | Portal › Zurückziehen | Status WITHDRAWN |

### F2 · Aylin Yıldız — datenschutzbewusste Bewerberin [AY]

> **Profil & Alltag:** 31, Medizinische Fachangestellte; hat nach einem Datenleck bei einem
> früheren Arbeitgeber ein feines Gespür für Datensparsamkeit entwickelt. Liest Datenschutz-
> hinweise wirklich, gibt so wenig wie möglich preis und erwartet Kontrolle ohne Kontozwang.
> **Was neu für sie gelöst ist:** ihre E-Mail liegt verschlüsselt in der Datenbank (Blind-Index –
> nachweisbar kein Klartext); der Job-Alert startet erst nach Double-Opt-in, lässt sich eng
> eingrenzen statt „alles", verfällt automatisch nach 12 Monaten und ist per Link jederzeit
> kündbar – ganz ohne Konto.

| ID | Use Case | Seite / Flow | QA-Prüfkriterium || ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-AY-01 | …die Datenschutzhinweise lesen | Datenschutz-Seite | Erreichbar/aktuell |
| UC-AY-02 | …erkennen, dass meine Daten im Haus bleiben | Info/Seite | Transparente Aussage |
| UC-AY-03 | …eine informierte Einwilligung erteilen | Consent | Version protokolliert |
| UC-AY-04 | …meinen Status transparent verfolgen | Portal | Nachvollziehbar |
| UC-AY-05 | …auf Löschung nach Frist vertrauen | Retention | Automatische Löschung |
| UC-AY-06 | …dem Talent-Pool bewusst zustimmen | Opt-in | Freiwillig |
| UC-AY-07 | …meine Bewerbung einreichen | `bewerben` | Erfolgreich |
| UC-AY-08 | …meinen Magic-Link erhalten | Success-Seite | Link angezeigt |
| UC-AY-09 | …meine Daten aktualisieren | ✅ Portal › „Meine Kontaktdaten" | Telefon direkt änderbar (auditiert); E-Mail-Änderung bewusst nur als Anfrage – die E-Mail ist Identitätsanker (Magic-Link, Blind-Index), Prüfung durchs Team (getestet: E-Mail bleibt unverändert) |
| UC-AY-10 | …meine Bewerbung zurückziehen | Portal | WITHDRAWN |
| UC-AY-11 | …einen Job-Alert abonnieren | `/job-alert/` | Abo angelegt |
| UC-AY-12 | …den Job-Alert jederzeit ohne Konto kündigen | `/job-alert/manage/<token>/` | 1 Klick → INACTIVE; Daten beim nächsten Lauf gelöscht |
| UC-AY-13 | …dass meine E-Mail verschlüsselt gespeichert ist | Blind-Index (Art. 25) | Roh-DB enthält nur Ciphertext + HMAC (per Test nachgewiesen) |
| UC-AY-14 | …dass mein Alarm erst nach Bestätigung aktiv wird | Double-Opt-in `/job-alert/confirm/` | Unbestätigte Abos erhalten KEINE Alarme (getestet) |
| UC-AY-15 | …meinen Alarm eng eingrenzen statt „alles" | Alarm-Scope (Stichwort) | Nur passende Titel lösen Alarm aus; Datenminimierung |
| UC-AY-16 | …dass mein Abo automatisch verfällt | 12-Monats-TTL + Lösch-Lauf | Verfallen → kein Alarm, Löschung mit Audit; Verlängerung per Klick |

### F3 · Robert Itzek — interner Bewerber [RI]
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-RI-01 | …mich intern bewerben, ohne dass mein Vorgesetzter es sieht | Vertraulichkeit/Scope | Keine ungewollte Sichtbarkeit |
| UC-RI-02 | …meine Bewerbung einreichen | `bewerben` | Erfolgreich |
| UC-RI-03 | …meinen Status verfolgen | Portal | Nachvollziehbar |
| UC-RI-04 | …auf gewahrte Vertraulichkeit vertrauen | BOLA/Scoping | Zugriff begrenzt |
| UC-RI-05 | …den Magic-Link nutzen | Portal | Passwortlos |
| UC-RI-06 | …eine Rückfrage stellen | ✅ Portal › Nachrichten | Rückfrage-Formular je Bewerbung; `CANDIDATE_MESSAGE_SENT`-Audit |
| UC-RI-07 | …meine Bewerbung zurückziehen | Portal | WITHDRAWN |
| UC-RI-08 | …eine interne Stelle finden | `/jobs/` | Sichtbar |
| UC-RI-09 | …dem internen Datenschutz vertrauen | Privacy | Transparent |
| UC-RI-10 | …einen Job-Alert für interne Stellen abonnieren | `/job-alert/` | Abo möglich |
| UC-RI-11 | …dass meine Bewerbung sauber dokumentiert ist | Audit | Nachvollziehbar |
| UC-RI-12 | …keine Benachteiligung erfahren | Fairness/AGG | Gleichbehandlung |
| UC-RI-13 | …nur über Stellen MEINER Einrichtung alarmiert werden | Alarm-Scope „Einrichtung" | Nur Facility-Treffer lösen Alarm aus (getestet) |

### F4 · Marek Nowak — Bewerber Niedriglohn (Lagerhelfer/Reinigung), mobil-only, wenig Deutsch [MN]

> **Profil & Alltag:** 42, pendelt mit dem Fahrrad und ÖPNV – der Arbeitsweg entscheidet, ob ein
> Job für ihn überhaupt in Frage kommt. Nutzt ausschließlich das Smartphone, Deutsch auf
> A2/B1-Niveau. **Was neu für ihn gelöst ist:** der **Umkreis-Alarm in Kilometern** um einen
> Standort bildet exakt sein wichtigstes Kriterium ab (Erreichbarkeit); die Suche findet Begriffe
> auch in der Beschreibung, wenn der Titel „fremd" formuliert ist; die Bewerbung bleibt
> Handy-Foto + drei Pflichtfelder.

| ID | Use Case | Seite / Flow | QA-Prüfkriterium |*Verhalten: bewirbt sich in wenigen Minuten vom Smartphone, begrenzte Deutschkenntnisse,
kaum Dokumente, will einen einfachen, schnellen Prozess und rasche Rückmeldung.*
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-MN-01 | …eine einfache Stelle ohne komplizierte Suche finden | `/jobs/` | Wenige, große Filter; mobil bedienbar |
| UC-MN-02 | …die Anzeige in einfacher/Leichter Sprache verstehen | Job-Detail / KI › Leichte Sprache | Verständliche Variante verfügbar |
| UC-MN-03 | …mich komplett vom Smartphone aus bewerben | `bewerben` (responsive) | Formular mobil vollständig nutzbar |
| UC-MN-04 | …mich ohne Anschreiben/lange Formulare bewerben | `bewerben` | Minimalpflichtfelder; kein Zwangs-Anschreiben |
| UC-MN-05 | …ein Handy-Foto meiner Unterlagen statt PDF hochladen | Upload | Bild-Upload akzeptiert |
| UC-MN-06 | …die Bewerbung in wenigen Minuten abschließen | `bewerben` | Kurzer Flow; wenige Schritte |
| UC-MN-07 | …eine sofortige, verständliche Eingangsbestätigung erhalten | Erfolgsseite | Klare Bestätigung + Magic-Link |
| UC-MN-08 | …meinen Status ohne Passwort und einfach prüfen | `/bewerber/<token>/` | Passwortlos; klare Status-Labels |
| UC-MN-09 | …schnell erfahren, ob ich den Job habe | Status/Portal | Zeitnahe, eindeutige Rückmeldung |
| UC-MN-10 | …bei fehlenden Angaben einfach nachbessern | Status MISSING_DOCS + Portal | Einfaches Nachreichen möglich |
| UC-MN-11 | …die Sprache der Oberfläche wechseln | i18n (Roadmap) | Sprachumschaltung |
| UC-MN-12 | …ohne Benachteiligung fair behandelt werden | Fairness/AGG | Gleichbehandlung; keine Blackbox-Absage |
| UC-MN-13 | …nur Jobs im erreichbaren Umkreis gemeldet bekommen | Alarm-Scope „Umkreis km" | Haversine-Distanz; 60 km matcht Nachbarstadt, 20 km nicht (getestet) |
| UC-MN-14 | …auch mit „falschen" Suchwörtern fündig werden | `/jobs/` Volltext (Titel+Beschreibung) | Begriff in Beschreibung → Treffer (getestet) |

### F5 · Dr. med. Katharina Vossberg — Fachärztin für Psychiatrie & Psychotherapie (hochwertige Position) [KV]
*Verhalten: hochqualifiziert, diskret (aktuell angestellt), erwartet einen professionellen,
persönlichen Prozess; viele Nachweise (Approbation, Facharzt-Anerkennung, Zeugnisse);
datenschutzbewusst; erwartet schnelle, verbindliche und wertschätzende Kommunikation.*
| ID | Use Case | Seite / Flow | QA-Prüfkriterium |
|---|---|---|---|
| UC-KV-01 | …mich diskret bewerben, ohne dass mein aktueller Arbeitgeber es erfährt | Portal/Scoping | Keine ungewollte Sichtbarkeit; vertraulich |
| UC-KV-02 | …die Stelle mit anspruchsvollen Details (Aufgaben, Team, Ausstattung) verstehen | `/jobs/<id>/` | Reichhaltiges, seriöses Stellenprofil |
| UC-KV-03 | …meine Approbation & Facharzt-Anerkennung einreichen | `bewerben` (Multi-Upload) | Mehrere Dokumente hochladbar |
| UC-KV-04 | …mehrere Zeugnisse/Zertifikate strukturiert beifügen | Upload | Mehrfach-Upload klar zugeordnet |
| UC-KV-05 | …dass meine Qualifikationen korrekt erfasst/geprüft werden | KI › Kompetenz-Extraktion | Nachweise korrekt ausgelesen |
| UC-KV-06 | …einen professionellen, wertschätzenden Prozess erleben | Gesamt-UX | Seriöse, klare Führung |
| UC-KV-07 | …einen persönlichen Ansprechpartner sehen | Job-Detail › Kontaktperson | Ansprechpartner sichtbar |
| UC-KV-08 | …eine schnelle, verbindliche Rückmeldung erhalten | `…/messages/` | Zeitnahe, individuelle Kommunikation |
| UC-KV-09 | …Status und nächste Schritte transparent verfolgen | Portal (+ Timeline) | Klarer Prozess-Stand |
| UC-KV-10 | …auf höchsten Datenschutz vertrauen (on-prem) | Datenschutz/Info | Zusicherung „Daten im Haus" |
| UC-KV-11 | …Interviewtermine flexibel abstimmen | ✅ Portal-Terminwahl + Umbuchen/Absagen | Umgesetzt (Kalender-Pakete) |
| UC-KV-12 | …gezielt fehlende Nachweise nachreichen | Status MISSING_DOCS | Präzise Nachforderung |
| UC-KV-13 | …sicher sein, dass keine automatische Blackbox-Absage erfolgt | Human-in-the-Loop | Ablehnung nur mit menschlicher Prüfung |
| UC-KV-14 | …die Einrichtung vor der Bewerbung kennenlernen | `/einrichtung/<slug>/` (vom Stellendetail verlinkt) | Profil, Bilder, offene Stellen der Einrichtung sichtbar |
| UC-KV-15 | …über passende Oberarzt-/Facharztstellen alarmiert werden | Alarm-Scope „Stichwort" + Einrichtung | Kombinierter Scope; nur relevante Treffer |

---

## QA-Methode: Seiten gegen Use Cases prüfen

Ziel: **Jede Seite/Route der App** gegen die relevanten Use Cases prüfen und
iterativ optimieren (Funktion, Click-Flow, Klarheit). Vorgehen je Seite:
1. Relevante Use Cases zuordnen.
2. Durchspielen: Ist das Ziel in möglichst wenigen, klaren Klicks erreichbar?
3. Status setzen (✅/◐/❌) + Optimierungsnotiz.
4. Lücken beheben, erneut prüfen.

### Seiten-/Routen-Inventar (Prüfobjekte)

**Öffentlich (Karriereportal):**
- `/` Startseite · `/jobs/` Stellenliste · `/jobs/<id>/` Stellendetail
- `/jobs/<id>/bewerben/` Bewerbungsformular · Erfolgsseite
- `/bewerber/<token>/` Magic-Link-Statusportal
- `/job-alert/` Job-Alert-Abo · `/pages/<slug>/` CMS-Seite

**Authentifizierung:**
- `/recruiter/login/` · `/recruiter/logout/`

**Recruiter-Dashboard (Tabs):**
- Kanban · Jobs · Prozesse · CMS · E-Mail & Variablen · SAP · KI-Zentrale · KPIs/Statistiken

**Recruiter-Verwaltung (Sidebar):**
- `/recruiter/analytics/` · `/recruiter/talent-pool/` · `/recruiter/screening-questions/`
- `/recruiter/delegations/` · `/recruiter/categories/` · `/recruiter/locations/`
- `/recruiter/job-templates/` (+ Ton-Overlay) · `/recruiter/interviews/`
- `/recruiter/pages/` · `/recruiter/media/` · `/recruiter/audit/`

**Aktionen/Endpunkte:**
- `…/cv/` CV-Download · `…/update-status/` · `…/add-note/` · `…/messages/`
- `schedule_interview` · `create_job` · `save_page` · Workflows · E-Mail-Templates
- System-Settings · KI (test/agg-check/simple-german/settings/logs/validate-prompt)
- `sap_sf_mapper`

**Administration:**
- Django-Admin (UserScope/BOLA, Stammdaten)

### Traceability-Matrix (Vorlage – im Audit auszufüllen)

| Seite/Route | Abgedeckte Use Cases | Status | Optimierungsnotiz |
|---|---|---|---|
| `/` Startseite | UC-LK-06, UC-AY-02, UC-MN-02 | ✅ | Suche/Filter über `/jobs/` verlinkt; „Daten bleiben im Haus" auf Startseite UND direkt am Absende-Knopf des Bewerbungsformulars; Leichte Sprache am Job-Detail; A11y-Panel global |
| `/jobs/` Stellenliste | UC-SB-…, UC-LK-06, UC-RI-08, UC-MN-01/14 | ✅ | Flexible Suche: Volltext (Titel+Beschreibung, getestet), Standort-, Abteilungs- und Kategorie-Filter |
| `/jobs/<id>/` Stellendetail | UC-KV-02, UC-KV-07, UC-MN-02 | ✅ | Kontaktperson ✅; Leichte-Sprache-Umschaltung ✅ |
| `/jobs/<id>/bewerben/` | UC-LK-07/08, UC-AY-07, UC-RI-02, UC-MN-03..07, UC-KV-03/04 | ✅ | Multi-Upload + Foto-CV + mobil + Minimalfelder ✅; A11y global ✅; sicherer Nachweis-Download ✅ |
| `/bewerber/<token>/` Portal | UC-LK-09..12, UC-AY-04/10, UC-RI-03/07, UC-MN-08..10, UC-KV-01/09/12 | ✅ | Status-Timeline ✅; passwortlos; Zurückziehen; klare Labels |
| `/job-alert/` (+confirm/manage) | UC-AY-11/12/14/15/16, UC-RI-13, UC-MN-13, UC-KV-15 | ✅ | Scope: Stichwort/Einrichtung/km-Umkreis (Haversine)/global; Double-Opt-in; Verwalten/Abmelden per Token; 12-Monats-Verfall + Lösch-Lauf; **eine Anmeldung je E-Mail** (Update statt Duplikat, getestet) |
| `/einrichtung/<slug>/` | UC-KV-14 | ✅ | Öffentliche Karriereseite je Einrichtung (Profil, Bilder, offene Stellen); vom Stellendetail verlinkt |
| `/recruiter/login/` | UC-HF-02, UC-CV-09, UC-*-Login | ✅ | Django-Login, RBAC-Gruppen |
| Dashboard › Kanban | UC-SB-05/06, UC-TK-*, UC-HR-03 | ✅ | Positionsgenaues Drag&Drop mit persistierter Reihenfolge (B10) ✅; Mehrfachauswahl + Sammel-Statuswechsel (UC-UM-08/09, mit Audit) ✅; sicherer CV-Download + Nachrichten-Button ✅ |
| Dashboard › Jobs | UC-SB-01/04/17/19, UC-TK-07/13 | ✅ | **Ein-Klick-Deaktivierung/Aktivierung** je Anzeige (published↔draft, Audit, BOLA-getestet); Bearbeiten-Modal; Vorlagen + Ton-Overlay + Textbausteine in der Anlage |
| Dashboard › Prozesse | UC-AR-01/02, UC-JF-04 | ❔ | (UC-JF-01 jetzt über automatisches Approval-Gate abgedeckt, s. `/recruiter/approvals/`) |
| Dashboard › KI-Zentrale | UC-AR-03/04/05, UC-SO-06, UC-MN-02, UC-KV-05/13 | ❔ | |
| Dashboard › KPIs | UC-KS-03, UC-BL-01, UC-CV-08 | ❔ | |
| `/recruiter/analytics/` | UC-SB-08/09, UC-CV-01..07, UC-BL-* | ✅ | §4.1 KPIs + §4.3: Time-to-Fill-Prognose, Anomalie-Hinweise mit Handlungsvorschlag, Fairness-Cockpit (datensparsam), Standort-Benchmark + Kosten/Einstellung (nur Leitung), CSV-Export (audit-protokolliert), lokaler KI-Analyst „Frag deine Daten" |
| `/recruiter/talent-pool/` | UC-SB-13, UC-UM-04, UC-FA-04 | ✅ | Kompletter Lebenszyklus: Opt-in im Portal (Kriterien datensparsam aus eigenen Bewerbungen: Jobfamilie + Standort – bewusst KEIN Skill-Profil), Matching auf veröffentlichte Stellen im Scope, Ein-Klick-Hinweis mit Doppel-Ansprache-Sperre + Widerrufs-Hinweis in jeder Mail, Verfall nach 12 Monaten, Austritt jederzeit im Portal (alles getestet) |
| `/recruiter/screening-questions/` | UC-AR-11, UC-UM-07 | ✅ | Fragen-Bank CRUD, Foundation ✅ |
| `/recruiter/delegations/` | UC-PW-01/02/12 | ✅ | Anlegen + vorzeitiges Beenden per UI, mit Audit; auf Django-Auth-User umgestellt |
| `/recruiter/categories/` | UC-SB-11, UC-AR-* | ✅ | CRUD + Archiv, Foundation ✅ |
| `/recruiter/locations/` | UC-SB-12, UC-AR-08 | ✅ | CRUD + Archiv, Foundation ✅ |
| `/recruiter/contacts/` | UC-SB-15/16, UC-PW-13, UC-KV-07 | ✅ | Ansprechpartner-Zentrale: FK-Prinzip (zentral ändern → sofort auf allen Anzeigen, getestet), Zuordnung je Einrichtung/Abteilung, **„Überall ersetzen"** (Urlaub/Ausscheiden, mit Audit), Lösch-Schutz bei Verwendung |
| `/recruiter/snippets/` | UC-SB-18/19, UC-UM-13, UC-AR-12 | ✅ | Textbausteine (Einleitung/Aufgaben/Anforderungen/Benefits, optional je Kategorie), per Dropdown in die Job-Anlage einfügbar |
| `/recruiter/job-templates/` (+Ton) | UC-SB-02/03, UC-AR-12 | ✅ | Versionierung (gleicher Titel → v+1, parent-Kette; Liste zeigt neueste) ✅; Ton-Overlay-UI direkt in der Job-Anlage ✅ |
| `/recruiter/interviews/` | UC-TK-05, UC-MD-05, UC-HR-09 | ✅ | Monatskalender (BOLA), Slots anlegen/löschen, drei Einlade-Wege, Outcome-Erfassung, Selbstservice-Umbuchen/-Absagen, Erinnerungen, `.ics` – vollständig seit den Kalender-Paketen |
| `/recruiter/pages/` | UC-AR-*, CMS | ◐ | Editor + öffentliche Seiten ✅; visueller Builder bewusst on hold hinter Evidenz-Gate (ROADMAP: erst bei ≥3 Interview-Nennungen) |
| `/recruiter/media/` | CMS/Assets | ✅ | Upload/Liste/Löschen, Foundation ✅ |
| `/recruiter/audit/` | UC-PW-03, UC-MB-01/08/12, UC-JF-03 | ✅ | Viewer + Filter, Foundation ✅; Hash-Kette + verify_audit (WP2) |
| `/recruiter/approvals/` | UC-JF-01/02/05/06/07, UC-AR-02 | ✅ |
| `/recruiter/interviews/` (Team-Kalender) | UC-SB-22/23/24/25, UC-AY-10/11/12/13 | ✅ |
| `/recruiter/analytics/` › Termine & Selbstbuchung | UC-SB-26 | ✅ (inkl. No-Show-Quote aus Outcome-Erfassung) |
| Portal › Nachrichten | UC-LK-11, UC-RI-06 | ✅ |
| `/recruiter/bedarf/` | UC-MD-01 | ✅ |
| Dashboard › „Heute wichtig" | UC-PW-06, UC-UM-06 | ✅ |
| Portal › Kontaktdaten | UC-AY-09 | ✅ |
| `/recruiter/audit/export.csv` | UC-JF-10, UC-MB-08, UC-NS-12 | ✅ | „Wartet auf mich"-Postfach: Reihenfolge-Logik, Freigeben/Rückfrage(Pflichtkommentar)/Ablehnen, SLA-Frist + überfällig-Badge, Audit; **automatisches Gate** (`Facility.requiresApproval` → Anzeige startet als draft mit Ticket+Kette aus `APPROVAL_CHAIN`), finale Freigabe **publiziert automatisch**, Toggle blockt bei offenem Gate (409), Wiedervorlage nach Rückfrage – alles getestet |
| `/recruiter/governance/` | UC-JF-08, UC-MB-01/08, UC-KS-* | ✅ | Datenminimiert (nur Aggregate, per Test: keine Namen/E-Mails); Hashketten-Status, Retention-/KI-Log-Zähler, Consent-Abdeckung |
| `…/cv/` CV-Download | UC-SB-07, UC-TK-09, UC-MB-01 | ❔ | |
| `…/update-status/` | UC-SB-06, UC-TK-06/12 | ❔ | |
| `…/messages/` | UC-TK-10, UC-PW-07, UC-FA-09, UC-KV-08 | ❔ | |
| Django-Admin › UserScope | UC-AR-08, UC-MB-09, UC-NS-03 | ❔ | |

> Status-Legende Matrix: ❔ ungeprüft · ✅ erfüllt · ◐ teilweise · ❌ Lücke.

> **Global (alle Seiten):** Barrierefreiheits-Panel in `base.html` deckt UC-LK-01..04 ab – Legasthenie-Schrift, Kontrast-Modus, ADHS-Fokus, Lese-Lineal, **Vorlesen** – persistent via localStorage.

### Nächster Schritt
Nach Fertigstellung dieser Bibliothek: die Matrix Seite für Seite durchgehen,
jede Route real durchklicken, Status + Optimierungsnotiz eintragen und Lücken
beheben. So ist sichergestellt, dass **keine Persona-Anforderung vergessen** wird.
