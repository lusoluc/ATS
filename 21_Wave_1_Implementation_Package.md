# 21_Wave_1_Implementation_Package.md

## Dokumentstatus
- Version: 1.0
- Zweck: Konkretes Umsetzungs- und Steuerungspaket für Wave 1 der neuen Landesverein-Karriereplattform
- Gültigkeit: Landesverein-spezifisch, benchmark-frei, umsetzungsorientiert
- Ziel: dem Senior Developer Agent einen klaren, kontrollierten und priorisierten Einstieg in die reale Umsetzung geben
- Regel: Wenn dieses Dokument dem Final Source of Truth widerspricht, gilt der Final Source of Truth

---

# 1. Ziel dieses Dokuments

Dieses Dokument definiert den **ersten realen Umsetzungsumfang** (“Wave 1”) für die neue Karriereplattform des Landesvereins.

Wave 1 soll sicherstellen, dass:
- die zentrale Plattformbasis steht,
- die wichtigsten Zielobjekte und Workflows implementierbar sind,
- die erste öffentliche Candidate Experience lauffähig wird,
- zentrale Governance bereits verankert ist,
- und Privacy / Security / Accessibility / SEO nicht nachträglich, sondern von Beginn an mitgebaut werden.

Wave 1 ist **nicht** der vollständige Endzustand.  
Wave 1 ist die **erste produktionsnahe, kontrollierte Lieferwelle**.

---

# 2. Wave-1-Leitidee

Wave 1 soll genau die Elemente liefern, die direkt aus dem aktuellen Landesverein-Kontext und dem Zielmodell abgeleitet werden können:

- eine Karriere-Startlogik mit mehreren Einstiegen, da die aktuelle Seite bereits unterschiedliche Karrierepfade und Hauptnavigationsbereiche sichtbar macht, 
- eine strukturierte Stellenplattform, weil die aktuelle Stellenliste bereits mit Feldern wie Referenz, Einrichtung, Ort, Beginn, Stundenumfang und Befristung arbeitet, [1](https://www.dvinci.de/karrierewebseite/)
- eine Initiativbewerbungs-/Bewerbungsweg-Basis, weil „Initiativbewerbung“, „Ihr Weg zu uns“ und „Ihre Bewerbung“ bereits sichtbar vorhanden sind, 
- einen Arbeitgeber- und CareerPath-Basisbereich, weil der Landesverein bereits Arbeitgeberinhalte, Arbeits- und Berufsfelder sowie Karrierepfade sichtbar ausspielt, [3](https://www.dvinci.de/bewerbermanagement-software/)[2](https://www.dvinci.de/features/)
- und eine Governance-/Privacy-/Security-Basis, weil die aktuelle Plattform bereits Datenschutz- und Löschhinweise im Bewerbungsumfeld sowie Barrierefreiheitsbezug sichtbar macht. 

---

# 3. Wave-1-Zielbild

Wave 1 ist erfolgreich, wenn am Ende mindestens Folgendes vorhanden ist:

1. strukturierte Kernentitäten und Kernbeziehungen  
2. Basis-APIs für öffentliche Inhalte und Jobs  
3. Karriere-Startseite  
4. Arbeitgeberbereich  
5. ausgewählte CareerPath-Seiten  
6. Stellenliste und Stellentdetailseite  
7. Initiativbewerbungsseite / Bewerbungsweg-Basis  
8. zentrale JobTemplate- und Approval-Logik  
9. lokale Draft-Erstellung im erlaubten Rahmen  
10. PrivacyNoticeVersion / Retention-Basis  
11. AuthN/AuthZ/TLS/MFA-Basis  
12. Audit Logging Baseline  
13. Accessibility- und SEO-Basis  
14. erste Migrationswelle für Kerninhalte

---

# 4. Scope von Wave 1

## 4.1 In Scope

### 4.1.1 Struktur- und Domänenbasis
- Organization
- Facility
- Location
- JobFamily
- CareerPath
- ContactPerson
- CareerPage
- JobPosting
- ApplicationForm
- ApplicationRoute
- WorkflowState
- Role
- Permission
- SEOProfile
- SharedContentModule
- JobTemplate
- ProcessTemplate
- PrivacyNoticeVersion
- DataRetentionPolicy
- ApplicantAccessAssignment

## 4.1.2 Öffentliche Candidate-Experience-Basis
- Karriere-Startseite
- Arbeitgeberseite
- mindestens ausgewählte CareerPath-Seiten
- Stellenliste
- Stellentdetailseite
- Initiativbewerbungsseite
- grundlegende Service-/Bewerbungsweg-Seite

## 4.1.3 Recruiting-/Governance-Basis
- lokale Jobentwürfe
- zentrale Prüfung/Freigabe
- Veröffentlichung nur nach zentraler Freigabe
- Basis-Applicant-Entry via Form-Modell
- Need-to-know-Access-Basis für Bewerberdaten

## 4.1.4 Privacy / Security / Compliance Basis
- PrivacyNoticeVersion-Linking
- RetentionPolicy-Basis
- TLS/Zertifikatsbasis
- privilegierte Rollen mit MFA-Pflicht
- object-level authorization
- applicant access logging
- zentrale Audit-Events
- barrierefreie Mindestumsetzung öffentlicher Kernpfade

## 4.1.5 Migrationsbasis
- Migration der Startseite
- Migration des Arbeitgeberbereichs
- Migration ausgewählter CareerPath-Inhalte
- Migration der strukturierten Jobfelder
- Migration der Initiativbewerbungs-/Bewerbungsweg-Inhalte
- Migration Privacy-/Accessibility-Grundseiten

---

## 4.2 Out of Scope für Wave 1

Folgende Themen gehören **nicht** in Wave 1:
- vollständiges ATS mit tiefer Kandidatenakte
- umfassende Interview-/Terminplanung
- umfangreiche Facility-/Location-Detailseiten
- tiefe Mehrsprachigkeit
- weitreichende Kampagnen-/Landingpage-Library
- Onboarding-Funktionalitäten
- Messaging-/Notification-Automation jenseits zwingender technischer Notwendigkeit
- komplexe externe Integrationen, sofern nicht explizit freigegeben
- freie lokale Prozessmodellierung

---

# 5. Wave-1-Arbeitsstränge

## Workstream 1 – Core Model Build
### Ziel
Implementierung der Kernentitäten, Beziehungen und Statusmodelle.

### Deliverables
- entity schemas
- relationship constraints
- workflow states
- role/permission baseline
- validation rules

### Exit Criteria
- alle Kernentitäten aus Wave-1-Scope implementiert
- Pflichtfelder validierbar
- Modellgrenzen stabil

---

## Workstream 2 – Public Career Experience Build
### Ziel
Erste funktionsfähige öffentliche Karriereplattform.

### Deliverables
- homepage
- employer page
- selected career path pages
- job list
- job detail
- initiative application page
- service/application guidance page

### Exit Criteria
- Kernpfade für Candidate Experience funktionieren
- Hauptnavigation vorhanden
- Jobsuch-/Jobdetailfluss nutzbar

---

## Workstream 3 – Job Governance Build
### Ziel
Zentrale und lokale Rollenlogik für Stellenanzeigen umsetzen.

### Deliverables
- JobTemplate support
- draft creation
- validation
- submit for review
- central approval / rejection
- publish block until approval

### Exit Criteria
- lokaler Draft möglich
- zentrale Freigabe nötig
- Publish ohne Approval technisch ausgeschlossen

---

## Workstream 4 – Applicant Entry & Privacy Build
### Ziel
Sichere Bewerbungsbasis herstellen.

### Deliverables
- ApplicationForm retrieval
- public form submission
- privacy notice linkage
- retention policy linkage
- applicant access assignment baseline
- applicant-sensitive logging baseline

### Exit Criteria
- public form submission funktioniert
- Form ohne PrivacyNoticeVersion nicht zulässig
- applicant access kontextgebunden

---

## Workstream 5 – Security Baseline Build
### Ziel
Technische Sicherheitsmindestbasis herstellen.

### Deliverables
- HTTPS-only baseline
- TLS config baseline
- internal auth baseline
- MFA baseline for privileged roles
- authorization baseline
- object-level authorization
- audit logging baseline

### Exit Criteria
- kein geschützter Endpunkt anonym
- privilegierte Rollen MFA-fähig
- object-level authorization nachweisbar
- kritische Audit Events vorhanden

---

## Workstream 6 – Migration Wave 1
### Ziel
Erste Landesverein-Inhalte in die Zielstruktur überführen.

### Deliverables
- mapped homepage content
- mapped employer content
- mapped selected career path content
- structured job field migration
- mapped initiative application/service content
- privacy/accessibility baseline content

### Exit Criteria
- Zielobjekte korrekt befüllt
- zentrale Ownership gesetzt
- keine kritischen Migrationsblocker mehr in Scope-1-Inhalten

---

# 6. Priorisierte Wave-1-Features

## 6.1 P0 – Unverzichtbar
- Core entity implementation
- role/permission baseline
- workflow baseline
- public homepage
- employer page
- job list
- job detail
- ApplicationForm + privacy linkage
- central approval enforcement
- TLS/auth/authz baseline
- audit logging baseline
- retention policy baseline

## 6.2 P1 – Sehr wichtig
- selected CareerPath pages
- initiative application page
- contact module logic
- service/application guidance page
- selected JobFamily support where needed for MVP

## 6.3 P2 – Nur wenn Kapazität vorhanden
- deeper service FAQ
- richer module reuse
- early local process variant support beyond minimum
- extended analytics views

---

# 7. Konkrete Deliverables von Wave 1

## 7.1 Fachlich / Modell
- bestätigte Wave-1-Entitätenliste
- bestätigte Wave-1-Beziehungen
- bestätigtes Rollen-/Permissions-Minimum
- bestätigter Wave-1-Workflowkatalog
- bestätigte Zielseitentypen in Scope

## 7.2 Technisch
- Kernschemas
- API endpoints für Public / Internal / Workflow / Privacy
- Auth/AuthZ-Baseline
- TLS/certificate config baseline
- logging hooks

## 7.3 Öffentlich sichtbare Oberfläche
- Karriere-Startseite
- Arbeitgeberseite
- CareerPath-Seiten in MVP-Auswahl
- Stellenliste
- Stellentdetailseite
- Initiativbewerbungsseite
- Service-/Bewerbungsweg-Basis

## 7.4 Governance
- JobTemplate enforcement
- submit-review flow
- central approve / reject
- publish enforcement
- applicant access assignment minimum

## 7.5 Compliance / Quality
- privacy notice assignment
- retention policy assignment
- accessibility baseline pass on public MVP paths
- SEO metadata baseline
- Go/No-Go readiness view

---

# 8. Abhängigkeiten innerhalb von Wave 1

## 8.1 Zwingende Vorbedingungen
Vor öffentlicher Candidate Experience müssen fertig sein:
- Entitäten
- Rollen
- Workflows
- API baseline
- PrivacyNoticeVersion
- TLS/auth/authz baseline

## 8.2 Zwingende Vorbedingungen vor Applicant Data Processing
Vor jeglicher echter Bewerberdatenverarbeitung müssen fertig sein:
- public form validation
- privacy notice linkage
- retention baseline
- applicant access control
- audit logging
- protected internal API enforcement

## 8.3 Zwingende Vorbedingungen vor lokalem Recruiting-Einsatz
Vor Aktivierung lokaler Bereiche müssen fertig sein:
- JobTemplate baseline
- local draft scope
- central review flow
- applicant access scope controls
- role mapping
- MFA for privileged roles

---

# 9. Wave-1-Implementierungsreihenfolge

## Step 1 – Technical Confirmation Pack
Der Senior Developer Agent liefert zuerst:
- bestätigte Wave-1-Entitäten
- bestätigte Beziehungen
- bestätigte Rollen
- bestätigte Workflows
- bestätigte Security Boundaries
- offene kritische Punkte

## Step 2 – Core Schema & Validation Layer
Dann:
- entity implementation
- reference integrity
- workflow-state handling
- validation rules
- error model

## Step 3 – Auth / AuthZ / TLS / Audit Baseline
Dann:
- protected endpoint model
- role enforcement
- object-level authorization
- MFA scope implementation plan
- TLS/certificate baseline
- audit logging baseline

## Step 4 – Public Experience Core
Dann:
- homepage
- employer page
- job list
- job detail
- service/application guidance page

## Step 5 – Job Governance
Dann:
- JobTemplate
- local draft creation
- submit-review
- central approval
- publish gate

## Step 6 – Applicant Entry
Dann:
- ApplicationForm public flow
- privacy notice linkage
- retention policy linkage
- initiative application page
- access assignment baseline

## Step 7 – Migration Wave 1 Content Load
Dann:
- load mapped homepage
- employer content
- selected career path content
- initiative/service content
- privacy/accessibility content baseline

## Step 8 – Hardening & Gate Review
Dann:
- quality gates
- security gates
- accessibility/SEO review
- release blocker review

---

# 10. Wave-1-Test- und Gate-Pflichten

## 10.1 Funktionale Mindesttests
- homepage loads correctly
- employer page loads correctly
- job list returns structured jobs
- job detail returns correct data
- local draft can be created
- central approval is required
- publish fails without approval
- form submission works with valid privacy notice
- form submission fails without required privacy conditions

## 10.2 Sicherheits-Mindesttests
- protected internal endpoints reject anonymous access
- privileged roles require configured stronger auth path
- object-level authorization blocks unrelated object access
- unrelated local applicant access is blocked
- TLS baseline is validated
- mTLS-required service endpoints reject invalid client certs where applicable

## 10.3 Privacy-/Compliance-Mindesttests
- PrivacyNoticeVersion visible and linked
- retention policy attached
- applicant access logged
- applicant access without assignment blocked
- no public applicant data leakage

## 10.4 Accessibility-/SEO-Mindesttests
- keyboard navigation for core public pages/forms
- labels and errors on forms
- metadata baseline present
- structured job data possible on detail pages

---

# 11. Wave-1-Akzeptanzkriterien

Wave 1 gilt nur dann als erfolgreich, wenn:

## 11.1 Fachlich
- Candidate kann Karriereeinstieg verstehen
- Candidate kann Stellen finden
- Candidate kann Stellen im Detail sehen
- Candidate kann Initiative / Bewerbungsweg nachvollziehen

## 11.2 Operativ
- lokaler Draft ist möglich
- zentrale HR-Freigabe funktioniert
- Veröffentlichung ist korrekt kontrolliert

## 11.3 Datenschutz / Sicherheit
- Bewerbungs-/Formularlogik ist privacy-linked
- Bewerberzugriffe sind need-to-know-basiert
- Audit Logging ist aktiv
- TLS/Auth/AuthZ sind wirksam

## 11.4 Qualität
- Kernseiten sind barrierefrei nutzbar
- SEO-Basis ist vorhanden
- keine kritischen Go-Live-Blocker offen

---

# 12. Wave-1-No-Go-Kriterien

Wave 1 darf nicht als release-ready betrachtet werden, wenn:
- Jobs ohne zentrale Freigabe publizierbar sind
- applicant data ohne korrekten Kontextzugriff sichtbar ist
- öffentliche Formulare ohne PrivacyNoticeVersion funktionieren
- RetentionPolicy nicht existiert
- geschützte interne APIs anonym erreichbar sind
- object-level authorization nicht funktioniert
- kritische Audit Events fehlen
- TLS-/Zertifikatsbasis unzureichend ist
- MFA-/privileged access baseline fehlt
- Accessibility-/Privacy-/Security-Kernpfade nicht bestehen

---

# 13. Verpflichtende erste Antwort des Senior Developer Agent für Wave 1

Die erste Antwort des Agenten auf Wave 1 muss enthalten:

1. bestätigte Liste der für Wave 1 relevanten Dokumente  
2. bestätigte Wave-1-Entitäten und Beziehungen  
3. bestätigte Wave-1-Rollen und Workflowzustände  
4. Liste der offenen kritischen Punkte  
5. vorgeschlagene technische Umsetzungsreihenfolge Step 1–4  
6. Liste der ersten konkreten Deliverables  
7. Liste der ersten Security-/Privacy-/Gate-Checks  

Ohne diese Struktur darf Wave 1 nicht gestartet werden.

---

# 14. Finale Regel

Wave 1 ist keine “schnelle erste Version”.

Wave 1 ist die **erste kontrollierte Landesverein-fähige Lieferwelle** und muss deshalb:
- fachlich korrekt,
- governance-konform,
- datenschutzkonform,
- sicher,
- auditierbar
- und technisch belastbar sein.