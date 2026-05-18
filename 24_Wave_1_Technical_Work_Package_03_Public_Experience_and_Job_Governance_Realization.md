# 24_Wave_1_Technical_Work_Package_03_Public_Experience_and_Job_Governance_Realization.md

## Dokumentstatus
- Version: 1.0
- Zweck: Drittes konkretes technisches Arbeitspaket für Wave 1
- Fokus: Public Experience Realisierung + Job Governance Realisierung
- Zielgruppe:
  - Senior Developer Agent
  - Technical Lead
  - Product Owner
  - UX Architect
  - CMS Architect
  - Enterprise Architect
  - Delivery Lead
- Gültigkeit: Landesverein-spezifisch, benchmark-frei, Wave-1-umsetzungsorientiert
- Regel: Wenn dieses Arbeitspaket dem Final Source of Truth widerspricht, gilt immer der Final Source of Truth

---

# 1. Ziel dieses Arbeitspakets

Dieses Arbeitspaket realisiert die erste **sichtbare und nutzbare Produktoberfläche** der neuen Landesverein-Karriereplattform.

Es soll sicherstellen, dass:
- die öffentliche Karriere- und Jobsuche erstmals nutzbar wird,
- zentrale Inhalte nicht nur modelliert, sondern sichtbar ausspielbar sind,
- die strukturierte Joblogik im UI / Service Layer korrekt erscheint,
- die erste Job-Governance-Kette (Draft → Review → Approval → Publish) end-to-end realisierbar wird,
- und die sichtbaren Kernpfade des aktuellen Landesverein-Karriereportals kontrolliert in das Zielsystem überführt werden. [3](https://www.dvinci.de/karrierewebseite/)

Dieses Arbeitspaket ist erfolgreich, wenn danach:
1. die Karriere-Startseite realisiert ist,
2. der Arbeitgeberbereich realisiert ist,
3. die Stellenliste und Stellentdetailseite realisiert sind,
4. mindestens ausgewählte CareerPath-Seiten realisiert sind,
5. die Initiativbewerbungs- / Bewerbungsweg-Basis realisiert ist,
6. und der zentrale Job-Governance-Pfad technisch durchgehbar ist. [1](https://www.dvinci.de/bewerbermanagement-software/)[3](https://www.dvinci.de/karrierewebseite/)

---

# 2. Warum dieses Arbeitspaket jetzt kommt

Nach Work Package 01 (Core Model & Auth Baseline) und Work Package 02 (API & Workflow Foundation) ist nun die erste Realisierungsschicht sinnvoll, weil:
- das aktuelle Landesverein-Portal bereits eine öffentliche Karriereerfahrung besitzt, die ersetzt bzw. modernisiert werden muss, 
- Jobs nicht nur intern strukturiert sein dürfen, sondern öffentlich such- und lesbar sein müssen, [3](https://www.dvinci.de/karrierewebseite/)
- und zentrale Governance nur dann sinnvoll wirksam wird, wenn der Weg vom lokalen Entwurf bis zur Veröffentlichung technisch end-to-end funktioniert. [3](https://www.dvinci.de/karrierewebseite/)

Gleichzeitig darf diese Realisierung nicht “blind UI-first” erfolgen.  
OWASP betont für APIs und service-basierte Systeme, dass geschützte Funktionen und objektbasierte Ressourcen auf jeder Ebene autorisiert werden müssen; deshalb muss auch die sichtbare Produktrealisierung sauber auf den zuvor definierten AuthN/AuthZ-/Workflow-/API-Regeln aufsetzen. [4](https://gdpr-info.eu/art-5-gdpr/)[5](https://datenschutz-hamburg.de/fileadmin/user_upload/HmbBfDI/Datenschutz/Informationen/240611_Information_Applicant_Data_Protection_and_Recruiting_EN.pdf)

---

# 3. Scope dieses Arbeitspakets

## 3.1 In Scope

### 3.1.1 Public Experience Realisation
- Karriere-Startseite
- Arbeitgeberseite
- Stellenliste
- Stellentdetailseite
- ausgewählte CareerPath-Seiten
- Initiativbewerbungsseite
- Bewerbungsweg-/Service-Basis-Seite
- Kontakt-/Ansprechpartner-Modulbasis

### 3.1.2 Public Experience Service Integration
- navigation integration
- public page data retrieval
- public jobs listing integration
- public job detail integration
- form retrieval integration
- public privacy notice access where relevant

### 3.1.3 Job Governance Realisation
- lokaler Jobentwurf real nutzbar
- submit-review path real nutzbar
- zentrale Approve/Reject-Logik real nutzbar
- Publish nur mit Approval real nutzbar
- Basisausspielung veröffentlichter Jobs in public listing/detail

### 3.1.4 UX / Content Template Realisation
- homepage template realization
- employer page template realization
- career path page template realization
- job list template realization
- job detail template realization
- initiative/service page template realization

### 3.1.5 Baseline Compliance in Public Realisation
- privacy-linked form usage
- no applicant data leakage
- public pages accessible at baseline level
- public job pages SEO-baseline capable
- public job pages HTTPS-only exposed

---

## 3.2 Out of Scope
Dieses Arbeitspaket enthält noch nicht:
- vollständige lokale Reviewer UI für Bewerberprüfung
- vollständige Interview-/Invitation-UI
- breite Facility-/Location-Detailseiten
- tiefe JobFamily-Library in voller Breite
- komplexe Candidate status UI beyond submission baseline
- advanced campaign/landing-page factory
- full analytics dashboards
- later-wave automation flows

---

# 4. Verbindliche Inputs

Der Senior Developer Agent muss dieses Arbeitspaket auf Basis der folgenden Dokumente ausführen:

1. `00_FINAL_SOURCE_OF_TRUTH.md`
2. `11_API_Contracts_and_Schemas.md`
3. `12_Test_and_Quality_Gates.md`
4. `13_Content_Migration_and_Inventory.md`
5. `14_Security_Architecture_and_Certificate_Guide.md`
6. `15_Implementation_Control_Checklist.md`
7. `16_Project_Delivery_Roadmap_and_Workstreams.md`
8. `17_Backlog_Epics_and_User_Stories.md`
9. `21_Wave_1_Implementation_Package.md`
10. `22_Wave_1_Technical_Work_Package_01_Core_Model_and_Auth.md`
11. `23_Wave_1_Technical_Work_Package_02_API_and_Workflow_Foundation.md`

---

# 5. Verbindliche Ziele

## Ziel A – Public Homepage and Entry Logic
Die neue Plattform muss eine Karriere-Startseite realisieren, die den Landesverein-Kontext mit mehreren Einstiegen verständlich abbildet.  
Die aktuelle Seite zeigt bereits Einstiege in Arbeitgeberkontext, Karrierepfade und Jobsuche. 

## Ziel B – Employer and CareerPath Realisation
Der Arbeitgeberbereich und ausgewählte CareerPath-Seiten müssen produktionsnah realisiert werden, da diese auf der aktuellen Plattform bereits sichtbare Kernorientierungspunkte sind. [1](https://www.dvinci.de/bewerbermanagement-software/)

## Ziel C – Public Jobs Realisation
Die strukturierte Landesverein-Stellenlogik muss als Stellenliste und Stellentdetail realisiert werden, basierend auf den bereits sichtbaren Jobfeldern und Detailinformationen. [3](https://www.dvinci.de/karrierewebseite/)

## Ziel D – Initiative/Application Guidance Realisation
Die Plattform muss einen klaren Initiativbewerbungs- und Bewerbungsweg-Einstieg realisieren, da diese Logik auf der aktuellen Seite bereits sichtbar vorhanden ist. 

## Ziel E – Job Governance End-to-End Path
Der Pfad lokaler Jobentwurf → zentrale Prüfung → zentrale Freigabe → Veröffentlichung muss real und überprüfbar funktionieren.

---

# 6. Verbindliche Deliverables

## 6.1 Deliverable 1 – Public Experience Realisation Pack
Enthält:
- realisierte Karriere-Startseite
- realisierte Arbeitgeberseite
- realisierte Stellenliste
- realisierte Stellentdetailseite
- realisierte ausgewählte CareerPath-Seiten
- realisierte Initiativbewerbungsseite
- realisierte Service-/Bewerbungsweg-Seite

## 6.2 Deliverable 2 – Public Page Template Realisation Pack
Enthält:
- homepage template realization
- employer template realization
- career path template realization
- job list template realization
- job detail template realization
- initiative/service page template realization

## 6.3 Deliverable 3 – Job Governance Realisation Pack
Enthält:
- local draft handling realization
- submit-review realization
- central approve/reject realization
- publish enforcement realization
- published/public visibility linkage

## 6.4 Deliverable 4 – Public Form / Privacy Integration Pack
Enthält:
- public form retrieval in UI/service
- privacy notice linkage in UI/service
- initiative/application CTA handling
- no-routing-leak behaviour
- baseline submission-ready integration path

## 6.5 Deliverable 5 – Accessibility / SEO Baseline Pack
Enthält:
- semantic structure baseline
- keyboard-usable core pages/forms
- metadata baseline
- structured job data readiness
- internal link baseline

## 6.6 Deliverable 6 – Technical Risk / Gap List
Enthält:
- offene technische Lücken
- blocker vor WP04
- UI/service-layer conflicts
- migration-dependent gaps

---

# 7. Konkrete Arbeitsaufgaben

## Task 1 – Realise Career Homepage
### Beschreibung
Realisierung der neuen Karriere-Startseite basierend auf dem Zielmodell.

### Muss enthalten
- Arbeitgeber-Einstieg
- Jobsuche-Einstieg
- CareerPath-Einstiege
- Initiativbewerbungs-Einstieg
- Service-/Kontaktbezug
- klare CTA-Struktur

Die aktuelle Landesverein-Startseite zeigt bereits mehrere Karrierepfad-Teaser sowie den Jobsucheinstieg. 

### Output
- homepage realization
- content/module mapping
- CTA flow mapping
- accessibility baseline notes

---

## Task 2 – Realise Employer Page
### Beschreibung
Realisierung einer strukturierten Arbeitgeberseite.

### Muss enthalten
- Arbeitgeberkontext
- Arbeitgeberbeschreibung
- Anschluss an Berufsfelder, CareerPaths oder Jobs
- saubere Seitenstruktur
- modulare Wiederverwendbarkeit

Die aktuelle Arbeitgeberseite und die Arbeits-/Berufsfeld-Seite zeigen, dass dieser Bereich ein zentraler Orientierungsbaustein des Landesvereins ist. [1](https://www.dvinci.de/bewerbermanagement-software/)[2](https://www.dvinci.de/features/)

### Output
- employer page realization
- reusable employer modules
- internal linking concept

---

## Task 3 – Realise Selected CareerPath Pages
### Beschreibung
Realisierung ausgewählter CareerPath-Seiten für Wave 1.

### Mindestempfehlung für Wave 1
- Ausbildung
- FSJ/BFD
- ggf. Praktisches Jahr / ärztliche Weiterbildung oder weitere priorisierte Pfade

Die aktuelle Karrierepräsenz macht diese Karrierepfade bereits sichtbar und teils inhaltlich eigenständig. 

### Muss enthalten
- zielgruppenspezifischer Intro-Kontext
- Beschreibung des Karrierepfads
- Bewerbungs- oder Job-CTA
- Anschluss an relevante Jobs / Form / Kontakt

### Output
- selected career path page realization set
- content-to-CTA mapping
- template usage confirmation

---

## Task 4 – Realise Job List
### Beschreibung
Realisierung der öffentlichen Stellenliste auf Basis strukturierter JobPosting-Daten.

### Muss enthalten
- strukturierte Trefferliste
- Anzeige von mindestens:
  - Titel
  - Referenz
  - Einrichtung
  - Ort
  - Beginn
  - Stundenumfang
  - Befristung, sofern vorhanden
- Filterlogik
- Übergang zur Stellentdetailseite

Die aktuelle Landesverein-Stellenliste zeigt diese Daten bereits sichtbar. [3](https://www.dvinci.de/karrierewebseite/)

### Output
- job list realization
- filter wiring
- public-safe field mapping
- empty-state behaviour

---

## Task 5 – Realise Job Detail Page
### Beschreibung
Realisierung der öffentlichen Stellentdetailseite.

### Muss enthalten
- Titel
- Referenz
- Facility / Einrichtung
- Location / Ort
- JobFamily / Kategorie, sofern im Ziel öffentlich relevant
- Aufgaben
- Anforderungen
- Benefits / Angebotsabschnitte, soweit vorhanden
- Bewerbungs-CTA
- Ansprechpartner oder klarer Alternativkontakt

Die aktuelle Detailseitenlogik zeigt bereits reichhaltige Stelleninhalte inkl. Aufgaben, Anforderungen und Angebotsabschnitten. 

### Output
- job detail realization
- structured-to-UI mapping
- CTA placement
- SEO/structured data readiness note

---

## Task 6 – Realise Initiative Application and Service Guidance
### Beschreibung
Realisierung des Initiativbewerbungs- und Service-/Bewerbungsweg-Bereichs.

### Muss enthalten
- Initiativbewerbungsseite
- grundlegende Erklärung des Bewerbungswegs
- Form-/Kontakt-CTA
- Privacy-/Datenschutzbezug im Bewerbungszusammenhang
- erwartbares Next-Step-Framing

Die aktuelle Seitenlogik „Ihr Weg zu uns“ und „Ihre Bewerbung“ macht diesen Service-/Application-Kontext bereits sichtbar. 

### Output
- initiative page realization
- application guidance page realization
- public form integration baseline
- privacy-linked CTA flow

---

## Task 7 – Realise Job Governance Path
### Beschreibung
Realisierung des technischen Pfades:
local draft → submit review → central approve/reject → publish → public visibility

### Muss prüfen
- lokaler Jobdraft erzeugbar
- submit-review action möglich
- zentrale Review/Approval action möglich
- publish ohne approval blockiert
- veröffentlichter Job erscheint öffentlich
- abgelehnter Job erscheint nicht öffentlich

### Output
- end-to-end governance flow confirmation
- negative publish test evidence
- status transition realization note

Die zukünftige Landesverein-Plattform benötigt genau diese zentrale Prüf- und Freigabelogik, weil lokale Einheiten Inhalte beitragen sollen, die zentrale HR-Karriere-Abteilung aber prüfen und freigeben muss. [3](https://www.dvinci.de/karrierewebseite/)

---

## Task 8 – Apply Public Security / Privacy Baseline to Realised Flows
### Beschreibung
Stelle sicher, dass die realisierten öffentlichen Flows nicht nur funktional, sondern auch korrekt abgesichert sind.

### Muss prüfen
- public endpoints remain public-safe
- no applicant data leakage
- no internal workflow exposure
- no form without privacy linkage
- no HTTP-only exposure
- no missing auth on internal governance actions
- object-level protection remains intact for protected operations

OWASP requires HTTPS-only protected transport and access control at each protected endpoint, including object-level checks for object-driven APIs. [4](https://gdpr-info.eu/art-5-gdpr/)[5](https://datenschutz-hamburg.de/fileadmin/user_upload/HmbBfDI/Datenschutz/Informationen/240611_Information_Applicant_Data_Protection_and_Recruiting_EN.pdf)[6](https://gdpr-info.eu/art-6-gdpr/)

### Output
- public security/privacy check summary
- endpoint exposure check
- no-leakage validation summary

---

# 8. Acceptance Criteria for This Work Package

Dieses Arbeitspaket ist erfolgreich abgeschlossen, wenn:

## 8.1 Public Experience
- Karriere-Startseite funktioniert
- Arbeitgeberseite funktioniert
- ausgewählte CareerPath-Seiten funktionieren
- Stellenliste funktioniert
- Stellentdetailseite funktioniert
- Initiativbewerbungs-/Bewerbungsweg-Basis funktioniert

## 8.2 Governance
- lokaler Jobentwurf ist nutzbar
- submit-review ist nutzbar
- zentrale Approve/Reject-Logik ist nutzbar
- Publish ohne Approval ist ausgeschlossen
- veröffentlichte Jobs werden öffentlich sichtbar
- nicht freigegebene Jobs bleiben intern

## 8.3 Privacy / Security
- public form usage is privacy-linked
- no applicant data leakage in public flows
- governance actions are protected
- object-level rules remain intact
- TLS/HTTPS assumptions are respected
- audit-relevant transitions are loggable

## 8.4 Accessibility / SEO Baseline
- core public pages are keyboard-usable at baseline level
- forms have labels and understandable errors
- metadata baseline exists
- job detail has structured-data readiness

## 8.5 Anschlussfähigkeit
- WP04 kann auf dieser Basis mit Applicant Review / Local Operations Realisation oder expanded content/governance work fortsetzen
- keine kritische UX-/Workflow-/Exposure-Lücke blockiert den nächsten Schritt

---

# 9. Pflicht-Tests / Validierungen

## 9.1 Public Experience Tests
- homepage renders correctly
- employer page renders correctly
- selected career path pages render correctly
- job list returns valid items
- job detail resolves correctly
- initiative page reachable and linked correctly

## 9.2 Governance Tests
- local draft create works
- submit-review works with valid input
- submit-review fails with invalid state/data
- approve/reject restricted correctly
- publish fails without approval
- approved and published jobs become publicly visible only in correct state

## 9.3 Privacy / Security Tests
- public form without privacy linkage is blocked
- no applicant data appears in public response models
- no internal state leaks on public pages
- protected governance actions reject unauthorized actor
- audit hook present for governance actions

## 9.4 Accessibility / SEO Tests
- keyboard access to homepage / job list / job detail / initiative page
- labels on visible form controls
- metadata existence
- stable public slugs
- structured job data capability check

---

# 10. No-Go Conditions for This Work Package

Dieses Arbeitspaket ist **nicht freigabefähig**, wenn:

1. Karriere-Startseite oder Stellenbasis nur teilweise oder inkonsistent realisiert ist
2. öffentliche Jobseiten interne oder sensitive Daten leaken
3. Initiativbewerbungs-/Bewerbungsweg-Basis keine Privacy-Verknüpfung hat
4. lokaler Jobentwurf ohne zentrale Approval-Blockierung direkt publizierbar ist
5. nicht freigegebene Jobs öffentlich sichtbar werden können
6. öffentliche Seiten/Formulare Accessibility-Baseline klar verfehlen
7. öffentliche Jobseiten keine SEO-/Structured-Data-Basis unterstützen
8. Governance Actions nicht geschützt / auditierbar sind
9. das Arbeitspaket stillschweigend zusätzliche Freiheiten für lokale Prozesse einführt
10. öffentliche Flows auf unsicheren oder ungeklärten API-/Security-Annahmen beruhen

---

# 11. Verpflichtende Antwortstruktur des Senior Developer Agent

Der Senior Developer Agent muss auf dieses Arbeitspaket mit genau dieser Struktur antworten:

## Section 1 – Read Confirmation
- gelesene bindende Dokumente
- bestätigte Relevanz für WP03

## Section 2 – Public Experience Realisation Plan
- homepage
- employer page
- selected career path pages
- job list
- job detail
- initiative/application guidance

## Section 3 – Template and Content Mapping
- verwendete Seitentypen
- Modulzuordnung
- CTA-Flows
- notwendige Migrationsinputs

## Section 4 – Governance Realisation Plan
- local draft realization
- review/approval/publish realization
- state visibility rules
- public visibility linkage

## Section 5 – Privacy / Security / Accessibility / SEO Baseline
- privacy-linked public flows
- no-leakage controls
- protected governance actions
- accessibility baseline
- SEO baseline

## Section 6 – Risks and Required Decisions
- UX risks
- workflow risks
- migration/content risks
- blocker before WP04

## Section 7 – Proposed Next Work Package Readiness
- readiness for WP04
- missing prerequisites
- recommended next implementation focus

---

# 12. Empfohlener nächster Schritt nach diesem Arbeitspaket

Nach erfolgreichem Abschluss dieses Arbeitspakets soll direkt folgen:

## `25_Wave_1_Technical_Work_Package_04_Local_Recruiting_Operations_and_Applicant_Access_Realization.md`

Fokus:
- local suitability review realization
- applicant access assignment operational realization
- local interview/invitation stage handling baseline
- privacy-sensitive internal applicant views
- controlled local process execution baseline

---

# 13. Finale Regel

Dieses Arbeitspaket ist nur dann erfolgreich, wenn der Senior Developer Agent:
- die sichtbare Karriereplattform belastbar realisiert,
- die Job-Governance-Kette technisch erzwingbar macht,
- und Public Experience niemals auf Kosten von Privacy, Security oder Governance implementiert.
``