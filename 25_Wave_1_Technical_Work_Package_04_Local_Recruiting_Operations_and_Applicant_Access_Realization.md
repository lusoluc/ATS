# 25_Wave_1_Technical_Work_Package_04_Local_Recruiting_Operations_and_Applicant_Access_Realization.md

## Dokumentstatus
- Version: 1.0
- Zweck: Viertes konkretes technisches Arbeitspaket für Wave 1
- Fokus: Lokale Recruiting-Ausführung, Bewerberzugriffslogik, Eignungsprüfung, Einladungsvorstufe, privacy-sensitive interne Ansichten
- Zielgruppe:
  - Senior Developer Agent
  - Technical Lead
  - Product Owner
  - Enterprise Architect
  - Security Architect
  - Privacy / Compliance Reviewer
  - Delivery Lead
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, Wave-1-umsetzungsorientiert
- Regel: Wenn dieses Arbeitspaket dem Final Source of Truth widerspricht, gilt immer der Final Source of Truth

---

# 1. Ziel dieses Arbeitspakets

Dieses Arbeitspaket realisiert den ersten belastbaren **internen Recruiting-Operations-Layer** für den Enterprise.

Es soll sicherstellen, dass:
- Bewerbungen nicht nur eingehen, sondern kontrolliert an den richtigen lokalen Kontext gebunden werden,
- lokale Einheiten/Bereiche Bewerber **nur im eigenen zulässigen Scope** sehen,
- eine erste strukturierte **Eignungsprüfung** möglich ist,
- vorbereitende **Einladungs-/Interview-Schritte** kontrolliert abgebildet werden,
- und dabei Datenschutz, Need-to-know-Zugriff und zentrale Governance erhalten bleiben.

Dieses Arbeitspaket ist erfolgreich, wenn danach:
1. applicant-sensitive interne Ansichten kontrolliert realisiert sind,
2. ApplicantAccessAssignment operativ nutzbar ist,
3. lokale Eignungsprüfung strukturiert möglich ist,
4. lokale Einladungs-/Interview-Vorstufen technisch modelliert sind,
5. und keine unzulässige standort- oder bereichsübergreifende Bewerbertransparenz entsteht.

---

# 2. Warum dieses Arbeitspaket jetzt kommt

Nach Work Package 03 ist die öffentliche Karriereerfahrung und die zentrale Job-Governance-Basis realisiert.  
Der nächste logische Schritt ist nun die **interne Recruiting-Ausführung**.

Das passt direkt zum Enterprise-Kontext:
- Die aktuelle Stellenlogik sagt bereits, dass Bewerbungen an die zuständige Fachabteilung oder Einrichtung weitergeleitet werden.  
- Die aktuelle Bewerbungs-/Service-Logik zeigt außerdem, dass unterschiedliche Bewerbungswege existieren.  
Damit ist klar: Die Plattform braucht nach dem öffentlichen Entry jetzt den **kontrollierten internen Bearbeitungsschritt**. [1](https://www.dvinci.de/karrierewebseite/)

Gleichzeitig ist dieser Schritt sicherheits- und datenschutzkritisch:
- Bewerberdaten dürfen nur nach **Need-to-know** sichtbar sein,
- objekt- und kontextbezogene Autorisierung muss greifen,
- und alle sensiblen Zugriffe und Entscheidungen müssen auditierbar sein.  
OWASP fordert für objektbasierte APIs explizite object-level authorization, und geschützte REST-/API-Umgebungen müssen HTTPS-only und endpoint-sicher sein. [2](https://datenschutz-hamburg.de/fileadmin/user_upload/HmbBfDI/Datenschutz/Informationen/240611_Information_Applicant_Data_Protection_and_Recruiting_EN.pdf)[3](https://gdpr-info.eu/art-5-gdpr/)[4](https://gdpr-info.eu/art-6-gdpr/)

---

# 3. Scope dieses Arbeitspakets

## 3.1 In Scope

### 3.1.1 Applicant Access Realisation
- ApplicantAccessAssignment operational realization
- context-bound applicant visibility
- assignment-based applicant list access
- restricted applicant detail access
- expiry and revocation handling baseline

### 3.1.2 Local Recruiting Operations Baseline
- local suitability review baseline
- structured decision-stage updates
- local invite / interview-preparation stage handling baseline
- local role-specific applicant interaction scope

### 3.1.3 Internal Applicant Views
- applicant list view baseline for authorized local reviewers
- applicant detail baseline for authorized local reviewers
- privacy-sensitive response shaping
- document visibility rules baseline
- restricted note / stage visibility baseline

### 3.1.4 Governance and Security Integration
- central vs local access boundaries enforced
- no global broad visibility by default
- role + context + object enforcement
- audit hooks for applicant reads and stage updates
- privileged internal API protection remains intact

### 3.1.5 Privacy / Retention Alignment
- applicant record linked to privacy / retention baseline
- access behavior aligned with need-to-know principle
- no uncontrolled local export model in Wave 1
- no uncontrolled cross-site applicant sharing

---

## 3.2 Out of Scope
Dieses Arbeitspaket enthält noch nicht:
- vollständige Interview-Terminplanung
- komplexe multi-step scheduling engine
- comprehensive candidate communication automation
- talent pool management in full breadth
- advanced recruiter dashboarding
- broad reporting UI
- free-form local process engine
- full document management expansion beyond Wave-1 minimum

---

# 4. Verbindliche Inputs

Der Senior Developer Agent muss dieses Arbeitspaket auf Basis der folgenden Dokumente ausführen:

1. `00_FINAL_SOURCE_OF_TRUTH.md`
2. `08_Entity_Data_Model.md`
3. `09_Roles_Permissions_Workflows.md`
4. `11_API_Contracts_and_Schemas.md`
5. `12_Test_and_Quality_Gates.md`
6. `14_Security_Architecture_and_Certificate_Guide.md`
7. `15_Implementation_Control_Checklist.md`
8. `21_Wave_1_Implementation_Package.md`
9. `22_Wave_1_Technical_Work_Package_01_Core_Model_and_Auth.md`
10. `23_Wave_1_Technical_Work_Package_02_API_and_Workflow_Foundation.md`
11. `24_Wave_1_Technical_Work_Package_03_Public_Experience_and_Job_Governance_Realization.md`

---

# 5. Verbindliche Ziele

## Ziel A – Operational Applicant Access
ApplicantAccessAssignment muss technisch so realisiert werden, dass nur autorisierte lokale oder zentrale Rollen die jeweils relevanten Bewerbungen sehen.

## Ziel B – Local Suitability Review
Lokale Recruiter/Fachverantwortliche müssen innerhalb ihres zulässigen Scopes eine erste strukturierte Eignungsprüfung durchführen können.

## Ziel C – Invitation Stage Baseline
Es muss ein kontrollierter interner Schritt für Einladung / Interviewvorbereitung / nächsten Prozessschritt existieren, ohne schon die gesamte spätere Prozesswelt abzubilden.

## Ziel D – Privacy-Safe Internal Views
Applicant-sensitive interne Ansichten müssen so realisiert werden, dass nur die erforderlichen Daten sichtbar sind und keine breite Offenlegung entsteht.

## Ziel E – Auditability and Security Continuity
Jeder relevante Bewerberzugriff, jede sensible Statusänderung und jede Zuweisungsänderung muss an die bestehende Audit-/Security-Basis anschließen.

---

# 6. Verbindliche Deliverables

## 6.1 Deliverable 1 – Applicant Access Realisation Pack
Enthält:
- applicant list access realization
- applicant detail access realization
- access assignment enforcement
- access revocation / expiry handling baseline
- context visibility rules

## 6.2 Deliverable 2 – Local Recruiting Action Pack
Enthält:
- local suitability review realization
- stage update baseline
- invitation-preparation stage realization
- role-based action restrictions

## 6.3 Deliverable 3 – Internal Applicant View Model Pack
Enthält:
- applicant list view baseline
- applicant detail view baseline
- field visibility classification
- document visibility baseline
- stage/comment visibility baseline

## 6.4 Deliverable 4 – Security and Audit Pack
Enthält:
- applicant read audit hooks
- stage update audit hooks
- access assignment audit hooks
- denied-access behavior
- no-broad-visibility validation rules

## 6.5 Deliverable 5 – Privacy / Retention Alignment Pack
Enthält:
- privacy-linked internal record awareness
- retention-aligned status baseline
- no uncontrolled export rule
- no uncontrolled sharing rule

## 6.6 Deliverable 6 – Technical Risk / Gap List
Enthält:
- offene Risiken
- blocker vor WP05
- privacy/security gaps
- local process boundary conflicts

---

# 7. Konkrete Arbeitsaufgaben

## Task 1 – Realise ApplicantAccessAssignment Enforcement
### Beschreibung
Realisierung der operativen Zugriffskontrolle auf Bewerbungen/Bewerberobjekte anhand von ApplicantAccessAssignment.

### Muss sicherstellen
- kein Zugriff ohne gültige Assignment-Logik
- Kontextbezug je Zugriff
- Ablauf/Entzug von Zugriffen
- keine breite bereichsübergreifende Sichtbarkeit
- keine lokale Sichtbarkeit außerhalb des eigenen Job-/Facility-/Standortkontextes

### Output
- access enforcement realization
- assignment check logic
- invalid-access behavior
- expiry/revocation handling baseline

---

## Task 2 – Realise Local Applicant List View Baseline
### Beschreibung
Realisierung einer internen Bewerberlistenansicht für lokale Rollen innerhalb ihres zulässigen Kontexts.

### Muss enthalten
- nur Bewerbungen aus erlaubtem Scope
- minimale, zweckgebundene Übersichtsdaten
- keine unnötige Datenexposition
- klaren Status-/Stufenbezug

### Muss vermeiden
- globale Bewerberübersichten
- facility-/standortübergreifende Offenlegung
- Anzeige sensibler Daten ohne Bedarf

### Output
- local applicant list realization
- field exposure baseline
- list filtering behavior in allowed scope

---

## Task 3 – Realise Local Applicant Detail View Baseline
### Beschreibung
Realisierung einer internen Bewerberdetailansicht für autorisierte lokale Rollen.

### Muss enthalten
- nur zulässige Detailfelder
- Dokumentzugriff nur im erlaubten Scope
- aktuelle Prozessstufe / decision stage
- privacy-/retention-aware record context
- keine Anzeige irrelevanter fremder Prozessinformationen

### Output
- applicant detail realization
- field visibility map
- document visibility rule set
- negative access behavior

---

## Task 4 – Realise Local Suitability Review Baseline
### Beschreibung
Realisierung eines ersten strukturierten Eignungsprüfungsschritts für lokale Verantwortliche.

### Muss enthalten
- strukturierte decision stage update capability
- definierte zulässige Aktionen
- keine freie, unstrukturierte Gesamtprozesslogik
- Rollen-/Kontextprüfung

### Muss sicherstellen
- nur autorisierte lokale Rollen können prüfen
- Prüfung ist auf den relevanten Bewerberkontext beschränkt
- Stage-Änderung wird geloggt

### Output
- suitability review realization
- stage update action baseline
- role and context checks

---

## Task 5 – Realise Invitation / Interview Preparation Baseline
### Beschreibung
Realisierung einer kontrollierten internen Vorstufe für Einladung bzw. Interviewvorbereitung.

### Muss enthalten
- definierte Decision/Stage für Einladungsvorbereitung oder Einladungsentscheidung
- nur zulässige Rollen
- kein unkontrollierter Kommunikationskanalzwang in Wave 1
- auditierbare Fortschreibung des Status

### Output
- invitation baseline realization
- permitted stage transitions
- denied action behavior

---

## Task 6 – Apply Privacy-Safe Response Shaping
### Beschreibung
Sicherstellen, dass interne applicant-sensitive Views und APIs nur zwecknotwendige Daten liefern.

### Muss prüfen
- Listenansicht zeigt weniger als Detailansicht
- Rollen mit geringerer Berechtigung sehen weniger Daten
- keine unnötige Offenlegung sensibler Informationen
- keine Sichtbarkeit ohne Assignment-Kontext

### Output
- response shaping baseline
- field visibility classification by view/role
- no-overexposure validation summary

OWASP highlights broken object/property level authorization as a critical API risk, which is especially relevant where internal views or APIs might expose more applicant properties than necessary. [2](https://datenschutz-hamburg.de/fileadmin/user_upload/HmbBfDI/Datenschutz/Informationen/240611_Information_Applicant_Data_Protection_and_Recruiting_EN.pdf)[3](https://gdpr-info.eu/art-5-gdpr/)

---

## Task 7 – Wire Applicant Access and Actions into Audit Hooks
### Beschreibung
Alle relevanten internen Bewerberzugriffe und -aktionen an die Audit-Basis anbinden.

### Mindestkandidaten
- restricted applicant record read
- access assignment creation
- access assignment removal
- stage update
- denied access attempt
- invalid context attempt

### Output
- audit hook mapping implementation note
- required event fields
- traceability mapping

NIST log-management guidance emphasizes the importance of logs for detection, investigation and remediation, and this is especially relevant for applicant-data-sensitive operations. [5](https://pages.nist.gov/800-63-3/sp800-63b.html)[6](https://csrc.nist.gov/pubs/sp/800/63/b/upd2/final)

---

## Task 8 – Validate Local Recruiting Realisation Against Governance Rules
### Beschreibung
Prüfen, dass lokale Recruiting-Realisierung nicht gegen zentrale Governance verstößt.

### Muss prüfen
- lokale Reviewer können keine zentrale Freigabelogik umgehen
- lokale Rollen erhalten keine globalen Leserechte
- lokale Prozessschritte bleiben innerhalb genehmigter Stage-Logik
- keine freie lokale Sonderlogik entsteht
- zentrale HR-Governance bleibt übergeordnet

### Output
- governance alignment summary
- blocker list
- rule conflict list

---

# 8. Acceptance Criteria for This Work Package

Dieses Arbeitspaket ist erfolgreich abgeschlossen, wenn:

## 8.1 Applicant Access
- applicant list access ist kontextgebunden realisiert
- applicant detail access ist kontextgebunden realisiert
- kein Zugriff ohne gültiges ApplicantAccessAssignment
- Assignment expiry / invalid context werden korrekt abgefangen

## 8.2 Local Recruiting Operations
- lokale Eignungsprüfung ist möglich
- Stage-Updates sind möglich
- Einladungsvorstufe ist kontrolliert möglich
- unzulässige Rollen oder Kontexte werden blockiert

## 8.3 Privacy / Security
- interne Views exponieren nur erforderliche Daten
- keine bereichs-/standortübergreifende Broad Visibility
- applicant reads und sensitive actions sind auditierbar
- Security-/Authorization-Baseline bleibt konsistent

## 8.4 Governance
- lokale operative Recruiting-Schritte funktionieren
- zentrale Governance-Regeln werden nicht verletzt
- Publish-/Approval-Scope bleibt zentral geschützt

## 8.5 Anschlussfähigkeit
- WP05 kann auf dieser Basis mit erweiterten Privacy/Retention/Compliance-Hardening- oder Rollout-/Migration-Funktionen aufsetzen
- keine kritische applicant-access- oder privacy-Lücke blockiert den nächsten Schritt

---

# 9. Pflicht-Tests / Validierungen

## 9.1 Access-Control Tests
- local reviewer can see assigned application
- local reviewer cannot see unrelated application
- expired assignment blocks access
- missing assignment blocks access
- cross-facility/cross-location access denied where not allowed

## 9.2 Stage/Action Tests
- authorized local review update works
- unauthorized role update fails
- invalid stage transition fails
- invitation baseline action works only for allowed role/stage

## 9.3 Privacy / Response Exposure Tests
- list view exposes less than detail view
- unauthorized field exposure is blocked
- documents are not visible without required permission
- no unnecessary data properties are returned

## 9.4 Audit Tests
- restricted applicant read is logged
- stage update is logged
- denied access attempt is logged
- assignment change is logged

## 9.5 Governance Tests
- local recruiting actions do not unlock publish logic
- local roles cannot perform central approval actions
- local process execution remains within approved boundaries

---

# 10. No-Go Conditions for This Work Package

Dieses Arbeitspaket ist **nicht freigabefähig**, wenn:

1. applicant-sensitive Daten ohne Assignment oder außerhalb des Kontexts sichtbar sind
2. lokale Rollen bereichs-/standortübergreifende Bewerber sehen können
3. Detailansichten zu viele Datenfelder exponieren
4. Stage-Updates ohne Rollen-/Kontextprüfung möglich sind
5. denied access nicht abgefangen oder nicht auditierbar ist
6. lokale Recruiting-Schritte zentrale Governance-Regeln unterlaufen
7. Dokumentzugriffe unkontrolliert sind
8. privacy-/retention-aware handling im internen Modell nicht berücksichtigt ist
9. object-level authorization auf applicant-sensitive APIs/View-Logik nicht wirksam ist
10. die Implementierung implizit freie lokale Recruiting-Prozesse schafft

---

# 11. Verpflichtende Antwortstruktur des Senior Developer Agent

Der Senior Developer Agent muss auf dieses Arbeitspaket mit genau dieser Struktur antworten:

## Section 1 – Read Confirmation
- gelesene bindende Dokumente
- bestätigte Relevanz für WP04

## Section 2 – Applicant Access Realisation Plan
- list access
- detail access
- assignment enforcement
- expiry / revocation handling

## Section 3 – Local Recruiting Operations Plan
- suitability review
- stage updates
- invitation baseline
- local role constraints

## Section 4 – Privacy-Safe Internal View Strategy
- field exposure rules
- document visibility rules
- list vs detail exposure logic
- no-overexposure controls

## Section 5 – Security and Audit Continuity
- object-level authorization behavior
- denied access handling
- audit hook mapping
- governance protection continuity

## Section 6 – Risks and Required Decisions
- privacy risks
- access-scope risks
- role-boundary risks
- blockers before WP05

## Section 7 – Proposed Next Work Package Readiness
- readiness for WP05
- missing prerequisites
- recommended next implementation focus

---

# 12. Empfohlener nächster Schritt nach diesem Arbeitspaket

Nach erfolgreichem Abschluss dieses Arbeitspakets soll direkt folgen:

## `26_Wave_1_Technical_Work_Package_05_Privacy_Retention_Compliance_and_Hardening.md`

Fokus:
- retention/deletion execution baseline
- privacy notice lifecycle hardening
- compliance validation hardening
- certificate / MFA / mTLS hardening in Wave 1 context
- final wave-1 readiness checks for applicant-sensitive operations

---

# 13. Finale Regel

Dieses Arbeitspaket ist nur dann erfolgreich, wenn der Senior Developer Agent:
- lokale Recruiting-Beteiligung funktional ermöglicht,
- dabei aber keine unkontrollierte Datenoffenlegung zulässt,
- und die Enterprise-Zielbalance aus zentraler Governance und lokaler operativer Auswahl strikt einhält.