# SecurATS — Funktionsübersicht

**Bewerbermanagement für Pflege & Sozialwirtschaft.** Ein durchgängiges ATS mit
lokaler KI-Assistenz, revisionssicherer Historie und einem klaren Prinzip: der
Mensch entscheidet, das System unterstützt — und lernt mit der Zeit aus echten
Entscheidungen, nie aus Extra-Klicks.

| | |
|---|---|
| **Stand** | 24.07.2026 |
| **Sektor** | Pflege / Sozialwirtschaft |
| **Rahmen** | DSGVO · EU-AI-Act · EU-Entgelttransparenz (RL 2023/970) |
| **KI** | lokal (Gemma), opt-in, erklärbar, fallback-sicher |

Zwei Prinzipien ziehen sich durch die gesamte Lern- und KI-Funktionalität:

1. **Aus Entscheidungen lernen, nicht aus Extra-Klicks.** Recruiter laden
   ohnehin ein, sagen ab, stellen ein — genau das ist das Trainingssignal.
2. **Keine Kennzahl ohne Handlung.** Jede Erkenntnis kommt mit Vorschlag und
   Button. Die Auswertung ist der Auslöser; das Produkt ist der nächste Schritt.

---

## Teil 1 — In dieser Session geschaffen

Jede Funktion mit Tests hinterlegt, live geprüft, in getrennten Commits.
*neu* = Neubau, *Bestand+* = vorhandene Funktion erweitert.

| Funktion | Bereich | Kurzbeschreibung | Status |
|---|---|---|---|
| Aktionsverlauf / Timeline | Nachvollziehbarkeit | Chronologische Historie je Bewerbung und je Stelle — intern & vom Bewerber, an einem Ort. | neu |
| KI-Antwort-Entwurf (C4) | Kommunikation | Höflicher, status-passender Antwort-Vorschlag auf eine einzelne Bewerber-Nachricht. | neu |
| Sammel-Postfach | Kommunikation | Offene Fragen nach Anliegen gebündelt (Stand / Unterlagen / Termin / Ablauf / Rückzug / Sonstiges). | neu |
| Cluster-Antwort | Kommunikation | Eine geprüfte Vorlage, pro Person personalisiert an alle Ausgewählten gesendet. | neu |
| Textbausteine + Auto-Vorschlag | Kommunikation | Gespeicherte Antworten je Anliegen; die zuletzt genutzte wird zum Default-Vorschlag. | neu |
| Auto-Antwort + Governance | Kommunikation | Vollautomatische Antwort nur für sichere Anliegen (Stand/Ablauf), streng begrenzt, auditiert. | neu |
| Lernende Einsortierung | Lernfunktion | Korrigiert HR eine Nachricht in den richtigen Topf, lernt das System daraus (Ehrlichkeits-Gate). | neu |
| L1 · Erkenntnisse & Vorschläge | Lernfunktion | Jede Kennzahl mit konkretem nächstem Schritt (Frage lockern / Kanal prüfen / Engpass). | neu |
| L2 · Bewerber-Steckbrief | Lernfunktion | Faktentreue Kurzzusammenfassung beim Öffnen der Karte — drei Sekunden statt drei Minuten. | neu |
| L4 · Editor-Hinweise | Lernfunktion | Frage- und Anforderungs-Hinweise direkt am Feld im Stellen-Editor. | neu |
| L3 · Gelerntes Scoring | Lernfunktion | Erklärbares A/B/C/D aus echten Entscheidungen, mit Messstrecke & Ehrlichkeits-Schranke, opt-in. | neu |
| Dashboard entrümpelt (B2) | Bedienung | Verwaltungs-Tabs zu eigenen Seiten ausgelagert; das Board zeigt nur die tägliche Arbeit. | Bestand+ |
| Talent-Pool-Werkzeug (C3) | Sourcing | Beim Veröffentlichen passende Pool-Personen anzeigen und mit einem Klick einladen. | Bestand+ |
| Nachrichten-Bar + Wächter-Test | Qualität | Django-Meldungen plattformweit sichtbar; Test gegen mehrzeilige Kommentar-Lecks. | neu |

---

## Teil 2 — Alle Funktionen im Detail

Jede Funktion mit drei Angaben: **Wie** sie funktioniert, **Warum** sie so
gebaut ist, **Wann** sie im Alltag genutzt wird.

### A — Öffentliches Karriereportal

Die Außenseite: wo Bewerber Stellen finden, sich bewerben und ihren Prozess
selbst begleiten — ohne Konto, aber sicher.

**Stellenportal & Detailseite** · `home` · `job_list` · `job_detail`
- **Wie:** Öffentliche Übersicht aller veröffentlichten Stellen mit Detailseite
  je Anzeige (Aufgaben, Anforderungen, Benefits, **öffentliche Entgeltspanne**,
  Ansprechpartner).
- **Warum:** Erste Anlaufstelle der Bewerber; die Spanne ist Pflicht
  (EU-Entgelttransparenz) und schafft Vertrauen.
- **Wann:** Dauerhaft öffentlich; Ziel jeder Kampagne und jedes Job-Alerts.

**Bewerbungsformular** · `bewerben`
- **Wie:** CV-Upload (Foto genügt), Anschreiben, dynamische Screening-Fragen.
  **K.O.-Kriterien** lehnen automatisch ab, Pflichtfelder werden serverseitig
  geprüft, Honeypot filtert Spam-Bots.
- **Warum:** Niederschwellig für die Zielgruppe, aber sauber validiert — keine
  halbe Bewerbung, kein unvalidierter Upload im Speicher.
- **Wann:** Jede eingehende Bewerbung; K.O.-Fragen sparen die offensichtlichen
  Absagen.

**Kandidatenportal (Magic-Link)** · `candidate_portal`
- **Wie:** Ein tokenbasierter Link ohne Passwort. Bewerber buchen/verschieben/
  sagen Termine ab, schreiben Nachrichten, ziehen zurück oder korrigieren Daten
  — alles auditiert, mit Rate-Limit gegen Missbrauch.
- **Warum:** Self-Service entlastet die HR und gibt Bewerbern Kontrolle, ohne
  Konto-Hürde.
- **Wann:** Nach dem Einladen; der Link steht in der Einladungs-Mail.

**Kampagnen, Landingpages & Kanäle** · `landing_page` · `source_channels` · `job_alert`
- **Wie:** Je Kampagne ein Link + QR-Code (`?src=…`); jede Bewerbung trägt ihre
  Quelle. Einrichtungsprofile, CMS-Seiten und Job-Alerts (Double-Opt-in) runden
  den Außenauftritt ab.
- **Warum:** Beantwortet „war die Jobmesse erfolgreich?" mit Menge *und* Qualität
  (Einladungsquote je Kanal) — Basis der Kanal-Analytik.
- **Wann:** Bei Aushängen, Messen, Anzeigen; die Auswertung steuert das Budget.

### B — Bewerbungs-Management (Kanban-Board)

Das tägliche Arbeitszentrum der HR: Bewerbungen sichten, bewegen, entscheiden —
jeder Klick arbeitsrelevant.

**Kanban-Board & Status** · `dashboard` · `update_status` · `reorder_board` · `bulk_update_status`
- **Wie:** Spalten je Status (Neu → Prüfung → Eingeladen → Eingestellt /
  Abgelehnt), Drag & Drop, Sammel-Statuswechsel. Jeder Wechsel schreibt einen
  verketteten Audit-Eintrag.
- **Warum:** Ein Bild des gesamten Verfahrens; die Statushistorie ist zugleich
  das Lern-Signal für das Scoring (L3).
- **Wann:** Ständig — das Board ist die Startseite der HR.

**Kandidaten-Modal** · `download_cv` · `add_note` · `application_feedback_json`
- **Wie:** Lebenslauf direkt im Fenster (keine Kopie auf den Laptop), interne
  Notizen, Screening-Antworten, Interview-Feedback, **Steckbrief** und die drei
  häufigsten Entscheidungen (Prüfen / Einladen / Absagen) an einem Ort.
- **Warum:** Entscheiden, wo gelesen wird — spart Klicks und streut keine
  Bewerber-PII als Datei-Kopien.
- **Wann:** Bei jeder Sichtung einer einzelnen Bewerbung.

**Suche, Wiederbewerber & Liegenbleiber (B1 · C1 · C2)** · `global_search`
- **Wie:** Globale Header-Suche (Name/E-Mail/Stelle) über den verschlüsselten
  Blind-Index; Board-Filter; ein Signal, wenn sich jemand erneut bewirbt, und
  ein Radar für Karten, die zu lange unbewegt liegen.
- **Warum:** Macht sichtbar, was schon in den Daten steht — ohne dass jemand
  danach suchen muss.
- **Wann:** Beim schnellen Finden und bei der täglichen Triage.

### C — Auswahlprozess

Von der Einladung bis zur Entscheidung — strukturiert, dokumentiert, mit klaren
Freigabewegen.

**Gespräche & Slots** · `schedule_interview` · `slot_create` · `interviews_ics` · `interview_outcome`
- **Wie:** Termine direkt oder als frei wählbare Slots (Bewerber bucht selbst),
  mehrere Gesprächsformate (Telefon bis Probearbeit), Team-Einladung,
  ICS-Kalenderexport, No-Show-Erfassung.
- **Warum:** Verteilte Teams stimmen sich ohne Mail-Ping-Pong ab; No-Show-Quoten
  und Format-Vergleiche werden messbar.
- **Wann:** Sobald eine Bewerbung eingeladen wird.

**Interview-Feedback** · `save_interview_feedback`
- **Wie:** Je Runde eine strukturierte Rückmeldung: Empfehlung, Kriterien-Noten,
  Stärken und — als eigenes, nicht übersehbares Feld — **Bedenken**.
- **Warum:** Die zweite Runde und die finale Entscheidung stehen auf
  Dokumentiertem, nicht auf Flurfunk. Keine Sorge geht verloren.
- **Wann:** Direkt nach jedem Gespräch.

**Gremium, Freigaben & Bedarf** · `application_vote` · `approvals_inbox` · `governance_view` · `staffing_requests`
- **Wie:** Sichtungs-Gremien stimmen dafür/dagegen (Quorum, Frist),
  Personalbedarf wird strukturiert gemeldet und freigegeben. Das Gremium löst
  sich über eine **Spezifitäts-Leiter** auf (Abteilung › Einrichtung › Standort
  › Jobfamilie › Organisation).
- **Warum:** Höhere Positionen brauchen einen kontrollierten Mehr-Augen-Weg;
  Einladungen erst nach Mehrheit (Override nur mit Audit).
- **Wann:** Bei Leitungs-/Fachpositionen und wo eine Freigabe vorgeschrieben ist.

**Vertretungen (B8)** · `delegations`
- **Wie:** Zeitlich befristete Delegation von Rechten (ALL / Einrichtung /
  Stelle); das Zeitfenster wird serverseitig geprüft.
- **Warum:** Urlaub und Fluktuation dürfen Verfahren nicht blockieren — aber nur
  im klar begrenzten Rahmen.
- **Wann:** Bei Abwesenheit; zusammen mit dem Aktionsverlauf die Basis jeder
  Urlaubsvertretung.

### D — Sammel-Antworten & Postfach *(neu)*

Ähnliche Bewerber-Fragen gebündelt statt einzeln beantworten — die große
Entlastung, in fünf aufeinander aufbauenden Stufen.

**Anliegen-Erkennung & Sammel-Postfach** · `inbox`
- **Wie:** Eingehende Fragen werden regelbasiert in Anliegen einsortiert (Stand
  / Unterlagen / Termin / Ablauf / Rückzug) und gebündelt angezeigt. Die **ganze
  Nachricht** wird bewertet: eine Standard-Frage *plus* etwas Unerkanntes landet
  in „Sonstiges / individuelle Prüfung".
- **Warum:** 12 Leute fragen dasselbe — das gehört zusammen. Der Catch-all sorgt
  dafür, dass nichts durchs Raster fällt.
- **Wann:** Täglich zur gebündelten Abarbeitung offener Fragen.

**Cluster-Antwort** · `batch_reply`
- **Wie:** Eine Vorlage prüfen, Vorschau je Person, mit einem Klick an alle
  Ausgewählten senden — jede Antwort mit Name, Stelle und Stand personalisiert.
  Senden-einmal verhindert Doppel-Nachrichten.
- **Warum:** Kein Massenversand-Look; es liest sich individuell, kostet aber
  einen Bruchteil der Zeit.
- **Wann:** Sobald sich in einem Anliegen mehrere offene Fragen sammeln.

**Textbausteine, Auto-Vorschlag & Einzel-Entwurf (C4)** · `save_reply_snippet` · `draft_reply`
- **Wie:** Eigene Antworten je Anliegen speichern; die zuletzt genutzte wird zum
  vorausgefüllten Vorschlag. Für einzelne Nachrichten erzeugt „KI-Antwort
  entwerfen" einen status-passenden Entwurf (lokal, fällt auf eine Vorlage
  zurück).
- **Warum:** HR sitzt nie vor dem leeren Feld; die Bibliothek wächst aus echten
  Antworten.
- **Wann:** Bei wiederkehrenden Formulierungen und bei individuellen Antworten.

**Auto-Antwort + Governance** · `save_auto_reply_settings`
- **Wie:** Vollautomatische Antwort **nur** für sichere, eindeutige
  Kommunikations-Anliegen (Stand/Ablauf), nie für Entscheidungen oder
  zusammengesetzte Nachrichten. Jede Auto-Antwort ist als automatisch
  gekennzeichnet, nennt den Weg zum Menschen und wird auditiert. Freischaltung je
  Anliegen in der KI-Zentrale.
- **Warum:** Schnelle Antwort hebt die Bewerber-Zufriedenheit — aber
  Einladung/Absage bleiben menschlich (EU AI Act).
- **Wann:** Ab Werk für Stand + Ablauf aktiv; jederzeit abschaltbar.

**Lernende Einsortierung** · `reclassify_message`
- **Wie:** Verschiebt HR eine falsch einsortierte Nachricht in den richtigen
  Topf, wird das als Signal in der Audit-Kette festgehalten. Ein
  Ehrlichkeits-Gate lernt ein Wort erst, wenn es in mehreren Korrekturen
  eindeutig auf dasselbe Anliegen zeigt; eine Einzel-Korrektur wirkt sofort für
  genau diese Nachricht.
- **Warum:** Das Postfach wird mit der Zeit besser — aus echtem Verhalten, ohne
  Extra-Klicks. Lernen weitet die Auto-Antwort nie aus.
- **Wann:** Immer wenn die Einsortierung danebenlag (arbeitsrelevant + Lernsignal).

### E — Aktionsverlauf / Timeline *(neu)*

**Chronologische Historie je Bewerbung & Stelle** · `application_timeline` · `job_timeline`
- **Wie:** Führt zusammen, was schon in den Daten steht — Audit-Kette (interne
  Entscheidungen), Nachrichten (mit Inhalt), Gespräche, Feedback — zu einer
  Zeitleiste mit drei Spuren: Team, Bewerber:in, System. Quellenscharf, damit
  nichts doppelt erscheint.
- **Warum:** Auf einen Blick sehen, wer was wann getan hat: schneller
  Stand-Überblick, lückenlose Nachvollziehbarkeit, ganze Geschichte bei
  Rückfragen.
- **Wann:** Tägliches HR-Werkzeug — und der schnelle Einstieg jeder
  Urlaubsvertretung.

### F — Talent-Pool

**Pool-Übersicht & Match je Stelle (C3)** · `talent_pool` · `job_pool_matches`
- **Wie:** Beim Veröffentlichen meldet SecurATS passende Pool-Personen (über
  Jobfamilie/Standort aus früheren Bewerbungen, datensparsam). Namen sichtbar,
  alle offenen vorausgewählt, „Ausgewählte einladen" als Ein-Klick-Alltag;
  Ausnahme: Profil vorher ansehen. Doppel-Ansprache ausgeschlossen.
- **Warum:** Aus dem passiven Archiv wird ein aktives Werkzeug — Einwilligung
  heißt gelegentliche, passende Ansprache, nicht Dauerwerbung.
- **Wann:** Bei jeder neuen Ausschreibung mit passendem Pool.

### G — Entgelttransparenz (E1–E4)

Umsetzung der EU-Richtlinie 2023/970 — tarif-nativ und in den Prozess eingebaut,
nicht als Nachtrag.

**Entgeltbänder, Publish-Gate & öffentliche Spanne** · `pay_bands` · `create_job` · `hr_ba_xml_feed`
- **Wie:** Tarif-native Entgeltbänder (z. B. TVöD-P); ohne Band **keine
  Veröffentlichung** (Gate, nicht umgehbar). Die Spanne erscheint in der Anzeige
  und im BA-XML-Feed für die Arbeitsagentur.
- **Warum:** Art. 5 verlangt die Spanne vor der Bewerbung; das Gate stellt
  Compliance strukturell sicher.
- **Wann:** Bei jeder Veröffentlichung; Bänder pflegt HR-Admin einmalig.

**Frageverbots-Wächter & Konsistenz** · `pay_transparency` · `analytics`
- **Wie:** Screening-Fragen nach der Gehaltshistorie werden erkannt und geblockt
  (auditiert); eine Konsistenz-Analytik prüft die Spannen (Art. 4) und
  dokumentiert Compliance.
- **Warum:** Die Richtlinie verbietet die Frage nach der bisherigen Vergütung —
  das darf nicht versehentlich in einer Stelle landen.
- **Wann:** Beim Anlegen von Fragen und in der laufenden Compliance-Auswertung.

### H — KI-Assistenz (lokal, Gemma)

Alle KI läuft **lokal** (keine Cloud, keine Bewerber-Daten nach außen), ist
opt-in und fällt bei nicht erreichbarer KI immer sauber auf einen regelbasierten
Weg zurück.

**AGG-Check & Leichte Sprache** · `gemma_agg_check` · `gemma_translate_simple_german`
- **Wie:** Der Anzeigentext wird auf AGG-Risiken geprüft (Alter/Geschlecht/
  Herkunft …) mit optimiertem Vorschlag; auf Wunsch Übersetzung in Leichte
  Sprache.
- **Warum:** Diskriminierungsarme, barrierefreie Anzeigen — direkt beim
  Schreiben, nicht im Nachhinein.
- **Wann:** Beim Verfassen/Bearbeiten einer Stelle.

**Prozess-Berater, Ton-Overlay & Feinschliff** · `suggest_process` · `apply_template_tone` · `polish_message`
- **Wie:** Regelbasierte Screening-/Prozess-Vorschläge (immer verfügbar) plus
  optionale KI-Zusatzfragen; Umformulierung in eine Ziel-Tonalität
  (Sie/Du/herzlich/nüchtern) ohne Faktenänderung; Feinschliff von Nachrichten.
- **Warum:** Trennt Inhalt von Tonalität und liefert bewährte Bausteine — der
  Mensch bleibt Autor.
- **Wann:** Beim Aufsetzen von Stellen und beim Verfassen von Nachrichten.

**KI-Zentrale** · `ki_page` · `get_ai_execution_logs` · `validate_ai_prompt`
- **Wie:** Verbindungstest, Regelwerk, Ausführungs-Protokoll (was die KI
  tatsächlich getan hat), Prompt-Validierung — und die Governance-Schalter für
  Auto-Antwort und gelerntes Scoring.
- **Warum:** Nachvollziehbarkeit und ein Ort, an dem HR-Admin die KI kontrolliert.
- **Wann:** Bei Einrichtung, Diagnose und Freischaltung von KI-Funktionen.

### I — Lernfunktion (L1–L4) *(neu)*

Das Herzstück der neuen Arbeit: SecurATS lernt mit der Zeit, welche Bewerber
passen und wie der Prozess besser wird — aus echten Entscheidungen, transparent
und gemessen. (Roadmap: `LEARNING_ROADMAP.md`.)

**L1 · Erkenntnisse & Vorschläge** · `analytics` · `screening_questions`
- **Wie:** Ein Rechenkern (`ats/insights.py`) wertet Trichter, Kanäle,
  Frage-Wirkung und Engpässe je Kontext aus (Spezifitäts-Leiter, Mindestmenge
  20). Die Vorschlags-Schicht (`ats/suggestions.py`) macht daraus konkrete
  Schritte mit Button: „Frage lässt 62 % durchfallen — **prüfen**?", „Kanal 40
  Bewerbungen, 0 Einstellungen — **Budget prüfen**?".
- **Warum:** Eine Zahl ohne Handlung ist Deko. Unter belastbarer Datenlage:
  ehrlich „zu wenig Daten".
- **Wann:** Ganz oben auf der Analytics-Seite; die Frage-/Anforderungs-Hinweise
  zusätzlich im Editor.

**L2 · Bewerber-Steckbrief** · `application_summary`
- **Wie:** Beim Öffnen einer Karte eine **faktentreue** Kurzzusammenfassung
  (`ats/profile_summary.py`): erfüllte Pflichtkriterien, Anforderungs-Erwähnungen
  im Anschreiben, Vollständigkeit, Wiederbewerber. Harte Fakten als Chips; die
  lokale KI darf nur umformulieren, nichts erfinden.
- **Warum:** Drei Sekunden statt drei Minuten Lesen — ein schnelles Bild, keine
  Rangliste.
- **Wann:** Bei jeder Sichtung einer Bewerbung im Modal.

**L4 · Editor-Hinweise** · `job_question_hints`
- **Wie:** Direkt am Feld im Stellen-Editor: „Diese Frage ließ 60 % durchfallen —
  lockern?" und „N vergleichbare Stellen ohne diese Anforderung wurden X Tage
  schneller besetzt — streichen?". „Streichen" entfernt die Zeile; wirksam wird
  erst das Speichern.
- **Warum:** Die Hilfe sitzt am Ort der Entstehung — nicht in einem Report, den
  keiner öffnet.
- **Wann:** Beim Bearbeiten einer Stelle.

**L3 · Gelerntes A/B/C/D-Scoring** · `learned_scoring`
- **Wie:** Ein transparentes, gewichtetes Modell (`ats/scoring.py`) lernt je
  Kontext (Jobfamilie/Standort/Abteilung), welche stellenrelevanten Merkmale mit
  einer Einladung zusammenhängen — Label ist die reale Entscheidung. Eine
  **Messstrecke** (`ats/scoring_eval.py`: Backtest gegen die regelbasierte
  Grundlinie, Kalibrierung) entscheidet: angezeigt wird das gelernte Score nur,
  wenn es die Regel *schlägt* (Ehrlichkeits-Schranke). Jede Note ist begründet.
- **Warum:** Das bestehende Score wird besser statt eines zweiten Rankings; keine
  Black Box, keine geschützten Merkmale.
- **Wann:** Standardmäßig **aus**. Aktivierung ist eine bewusste, auditierte
  Entscheidung des Trägers — nach Rechtsgutachten (EU AI Act, Hochrisiko).

### J — Analytics & Steuerung

**Erfolgs-Dashboard** · `analytics` · `analytics_export` · `analytics_ask`
- **Wie:** Lokal berechnet (keine Cloud-BI), im Sichtbereich des Nutzers:
  Trichter, Quellen, Score-Verteilung, Standort-Vergleich, Zeitreihen, Kosten je
  Einstellung, Time-to-Fill-Prognose, Anomalien — plus eine Freitext-Frage an die
  Daten. Ganz oben die L1-Erkenntnisse.
- **Warum:** Steuern mit Zahlen, die im Haus bleiben; Leitung sieht mehr
  (Benchmark/Kosten) als eine Standort-Recruiterin.
- **Wann:** Für Reporting, Budget- und Prozess-Entscheidungen.

**Fairness-Cockpit** · `analytics (fairness)`
- **Wie:** Überwacht Mensch-über-Modell-Quote (Overrides) und Fairness-Drift —
  auch ohne geschützte Merkmale als Eingabe.
- **Warum:** Vertrauen ins System braucht sichtbare Kontrolle, dass es nicht
  unbeabsichtigt verzerrt.
- **Wann:** Begleitend, besonders wenn gelerntes Scoring aktiv ist.

### K — Verwaltung & Stammdaten

**Stammdaten & Vorlagen** · `locations` · `categories` · `contacts` · `snippets` · `job_templates` · `screening_questions`
- **Wie:** Standorte, Kategorien, Ansprechpartner, Textbausteine, Stellen-Vorlagen
  (mit Versionierung), Screening-Fragen-Registry, Benefits, Gremien-Defaults — als
  eigene, HR-Admin-geschützte Seiten (seit B2 aus dem Board ausgelagert).
- **Warum:** Das Board bleibt schlank; Verwaltung stört den täglichen
  Bewerber-Workflow nicht.
- **Wann:** Bei Einrichtung und Pflege — selten, aber zentral.

**CMS, Medien & E-Mail-Vorlagen** · `pages_manage` · `media_manage` · `templates_page`
- **Wie:** Inhaltsseiten (Baukasten), Medien-Bibliothek und E-Mail-Vorlagen mit
  Variablen — für Karriereportal und Kommunikation.
- **Warum:** Außenauftritt und Standard-Kommunikation ohne Entwickler pflegbar.
- **Wann:** Bei Portal-Änderungen und wiederkehrenden Mails.

### L — Sicherheit, Compliance & Governance

Kein aufgesetztes Feature, sondern die Grundlage, auf der alles andere steht.

**Revisionssichere Audit-Kette** · `audit_log` · `audit_export`
- **Wie:** Jede relevante Aktion schreibt einen Audit-Eintrag, der seinen
  Vorgänger hasht (Hash-Kette in fester Sequenz-Ordnung). Nachträgliche Änderung/
  Löschung bricht die Kette und ist per Prüfung erkennbar. CSV-Export je
  Bewerbung.
- **Warum:** Manipulationssicherer Nachweis — Pflicht für ein Verfahren, das
  Menschen bewertet.
- **Wann:** Automatisch bei jeder Aktion; für Audits und DSGVO-Auskünfte.

**Zugriffsschutz & PII-Verschlüsselung** · BOLA-Scoping · Blind-Index
- **Wie:** Jede Recruiterin sieht nur ihren Bereich (Standorte/Einrichtungen);
  jede View trägt ihren eigenen Auth-Decorator (keine globale Login-Middleware als
  Single Point of Failure). Bewerber-PII (Name, E-Mail, Telefon, Anschreiben) ist
  at-rest verschlüsselt; Lookups laufen über einen deterministischen Blind-Index.
- **Warum:** Datensparsamkeit und Zugriffsbeschränkung nach DSGVO — auch bei
  einem Datenbank-Leck bleiben die Klartext-Daten geschützt.
- **Wann:** Durchgängig, unsichtbar.

**EU-AI-Act-Haltung** · durchgängig
- **Wie:** Bewerber-Bewertung gilt als Hochrisiko (Anhang III). Deshalb: Mensch
  entscheidet, gelernte Signale sind Empfehlung; automatisch wirken nur objektive
  K.O.-Kriterien; Erklärbarkeit, Messbarkeit, Audit, Opt-in — und Rechtsgutachten
  vor dem Livegang gelernter Bewertung.
- **Warum:** Rechtssicherheit und Fairness sind nicht verhandelbar.
- **Wann:** Bei jeder KI-/Lernfunktion, besonders L3.

### M — Integrationen & Import

**Multiposting & HRIS** · `stepstone_feed` · `hr_ba_xml_feed` · `sap_sf_mapper`
- **Wie:** Feeds für StepStone und die Bundesagentur (BA-XML, inkl.
  Entgeltspanne); ein Feld-Mapper für SAP SuccessFactors / HRIS (zeigt die
  Zuordnung; die Übertragung macht ein Befehl bei gesetztem Endpoint).
- **Warum:** Reichweite ohne Doppelpflege; saubere Übergabe an nachgelagerte
  HR-Systeme.
- **Wann:** Bei Veröffentlichung (Multiposting) und Einstellung (HRIS-Übergabe).

**Datenimport & Betriebsüberwachung** · `data_import` · `healthz` · `healthz_ai`
- **Wie:** CSV-Import mit Vorlage für den Umzug bestehender Daten; Health-
  Endpunkte für System und KI-Verfügbarkeit.
- **Warum:** Schneller Start ohne manuelles Nacherfassen; Betrieb bleibt
  beobachtbar.
- **Wann:** Beim Onboarding und im laufenden Betrieb (Monitoring).

---

*SecurATS · Funktionsübersicht · Stand 24.07.2026 — lokal berechnet,
Mensch-im-Loop, revisionssicher.*
