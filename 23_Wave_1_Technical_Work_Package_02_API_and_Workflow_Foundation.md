# 23_Wave_1_Technical_Work_Package_02_API_and_Workflow_Foundation.md

## Dokumentstatus
- Version: 1.0
- Zweck: Zweites konkretes technisches Arbeitspaket für Wave 1
- Fokus: API Foundation, Workflow Action Endpoints, Form Submission Baseline, Audit Hook Baseline
- Zielgruppe:
  - Senior Developer Agent
  - Technical Lead
  - Enterprise Architect
  - Security Architect
  - Delivery Lead
- Gültigkeit: Landesverein-spezifisch, benchmark-frei, Wave-1-umsetzungsorientiert
- Regel: Wenn dieses Arbeitspaket dem Final Source of Truth widerspricht, gilt immer der Final Source of Truth

---

# 1. Ziel dieses Arbeitspakets

Dieses Arbeitspaket baut direkt auf Work Package 01 auf.

Es soll die erste technisch belastbare API- und Workflow-Basis herstellen, damit:
- öffentliche Karriere- und Jobdaten kontrolliert ausgeliefert werden können,
- interne Governance- und Job-Workflows technisch angesteuert werden können,
- erste Bewerbungs-/Formular-Submissions sauber modelliert werden,
- und Security / Privacy / Logging bereits auf API-Ebene verankert sind.

Dieses Arbeitspaket ist erfolgreich, wenn danach:
1. die API-Klassen aus Wave 1 als technische Endpoint-Gruppen bestätigt sind,
2. die ersten Public/Internal/Workflow/APIs belastbar definiert oder implementierbar sind,
3. die Job-Governance-Workflows (submit-review, approve, publish) technisch vorbereitet sind,
4. die Form-Submission-Basis steht,
5. und Audit-/Security-Hooks an den richtigen Stellen vorgesehen sind.

---

# 2. Warum dieses Arbeitspaket jetzt kommt

Nach dem stabilisierten Kernmodell muss als nächstes die **API- und Workflow-Schicht** festgezogen werden, weil:
- die aktuelle Landesverein-Zielrealität bereits eine klar strukturierte Jobsuche und Stellenanzeigendarstellung zeigt, [1](https://www.dvinci.de/karrierewebseite/)
- öffentliche Karriere- und Jobfunktionen ohne saubere Public/Internal-Trennung riskant wären, [2](https://gdpr-info.eu/art-5-gdpr/)[4](https://gdpr-info.eu/art-6-gdpr/)
- und die zukünftige Landesverein-Plattform zwingend zentrale Jobfreigaben und lokale Recruiting-Beteiligung technisch kontrollieren muss. [1](https://www.dvinci.de/karrierewebseite/)[5](https://www.dvinci.de/bewerbermanagement-software/)

Sobald APIs für Jobs, Workflow-Transitions und Bewerbungen existieren, steigt auch das Risiko für:
- fehlende Endpoint-Autorisierung,
- fehlende Objektprüfung,
- unsaubere Workflow-Transitions,
- oder ungewollte Datenoffenlegung.  
Genau deshalb fordert OWASP Zugriffskontrolle auf jeder API-Ebene und object-level authorization für objektbasierte APIs. [2](https://gdpr-info.eu/art-5-gdpr/)[3](https://datenschutz-hamburg.de/fileadmin/user_upload/HmbBfDI/Datenschutz/Informationen/240611_Information_Applicant_Data_Protection_and_Recruiting_EN.pdf)

---

# 3. Scope dieses Arbeitspakets

## 3.1 In Scope

### 3.1.1 Public API Foundation
- navigation / discovery read baseline
- career page read baseline
- job list read baseline
- job detail read baseline
- public form retrieval baseline
- public privacy notice retrieval baseline

### 3.1.2 Internal Governance API Foundation
- internal job list / job detail baseline
- job draft create/update baseline
- job template usage baseline
- process template lookup baseline
- local process variant lookup/create baseline (minimum)

### 3.1.3 Workflow Action API Foundation
- submit-review for jobs
- central approve / reject for jobs
- publish for jobs
- minimal workflow state validation

### 3.1.4 Applicant Entry Baseline
- ApplicationForm submission contract
- privacy notice linkage validation
- applicant submission acceptance baseline
- no internal routing exposure in public responses

### 3.1.5 Security / Audit Hooks
- endpoint class security mapping
- required auth requirement per endpoint group
- initial audit event trigger mapping
- rejection/error model baseline
- access-denied behavior baseline

---

## 3.2 Out of Scope
Dieses Arbeitspaket enthält noch nicht:
- vollständige Public UI-Implementierung
- vollständige applicant review UI
- komplette analytics implementation
- tiefere local process variant engine
- full retention execution logic
- advanced bulk operations
- full notification or invitation delivery workflows

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

---

# 5. Verbindliche Ziele

## Ziel A – Public API Baseline
Die erste öffentliche API-Fläche für Karriere- und Jobdaten muss stabil und klar abgegrenzt sein.

## Ziel B – Internal Governance API Baseline
Die erste interne API-Fläche für Jobs, Templates und Governance muss belastbar und geschützt sein.

## Ziel C – Workflow Action Baseline
Jobbezogene Workflow-Aktionen müssen technisch steuerbar und regelgebunden sein.

## Ziel D – Application Submission Baseline
Bewerbungs-/Formular-Submissions müssen strukturiert, privacy-linked und kontrolliert entgegengenommen werden können.

## Ziel E – API Security Baseline
Alle API-Klassen müssen korrekt nach Public/Internal/Sensitive klassifiziert und mit AuthN/AuthZ/TLS-/Audit-Erwartungen versehen sein.

---

# 6. Verbindliche Deliverables

## 6.1 Deliverable 1 – Wave-1 API Group Confirmation
Enthält:
- finale Liste der API-Gruppen in Scope
- Public / Internal / Workflow / Sensitive classification
- required auth level per group
- required audit level per group

## 6.2 Deliverable 2 – Public API Baseline Pack
Enthält:
- navigation read contract confirmation
- page read contract confirmation
- jobs list contract confirmation
- job detail contract confirmation
- public form read contract confirmation
- public privacy notice read contract confirmation

## 6.3 Deliverable 3 – Internal Job/Governance API Pack
Enthält:
- internal jobs list contract
- job draft create contract
- job update contract
- template lookup contract
- process template / local process variant baseline contract

## 6.4 Deliverable 4 – Workflow Action API Pack
Enthält:
- submit-review endpoint rules
- approve/reject endpoint rules
- publish endpoint rules
- workflow validation baseline
- invalid transition behavior

## 6.5 Deliverable 5 – Application Submission Pack
Enthält:
- public submission request model
- privacy notice validation behavior
- error scenarios
- minimal accepted response model
- routing secrecy baseline

## 6.6 Deliverable 6 – Audit and Access Hook Map
Enthält:
- which endpoint triggers which audit event
- authentication failure hooks
- authorization denial hooks
- workflow action logging hooks
- applicant submission logging baseline

---

# 7. Konkrete Arbeitsaufgaben

## Task 1 – Confirm Final API Group Segmentation
### Beschreibung
Bestätige die API-Klassen für Wave 1 endgültig.

### Erwartete Gruppen
- Public Experience APIs
- Internal Governance APIs
- Workflow Action APIs
- Applicant Entry APIs
- Sensitive Applicant APIs (baseline only, limited in Wave 1)
- Privacy / Compliance APIs (minimum baseline)

### Output
- API group matrix
- auth requirement per group
- logging requirement per group
- access sensitivity rating per group

---

## Task 2 – Confirm Public API Baseline Contracts
### Beschreibung
Bestätige oder konkretisiere die minimalen Public Read APIs.

### Fokus
- navigation
- pages
- jobs list
- job detail
- form retrieval
- privacy notice retrieval

### Muss sicherstellen
- keine applicant data leakage
- keine internal workflow leakage
- public response contains only allowed data
- stable error model
- public endpoints are HTTPS-only by design

OWASP’s REST security guidance requires secure REST services to expose HTTPS-only endpoints and to separate public exposure from protected internal logic. [2](https://gdpr-info.eu/art-5-gdpr/)[4](https://gdpr-info.eu/art-6-gdpr/)

### Output
- public contract confirmation
- field allowlist for public objects
- public error behaviors

---

## Task 3 – Confirm Internal Job and Governance Contracts
### Beschreibung
Bestätige oder konkretisiere die internen Job- und Governance-Kontrakte.

### Fokus
- internal jobs list
- create draft
- update draft
- read internal job state
- template lookup
- process template lookup

### Muss sicherstellen
- no anonymous access
- role-based access required
- object-level and workflow-state constraints considered
- create/update payloads match Wave-1 entity rules

### Output
- internal governance contract pack
- required permissions per operation
- negative test expectations

---

## Task 4 – Define Workflow Action Endpoint Rules
### Beschreibung
Lege die exakten Regeln für Job-Workflow-Actions fest.

### Fokusaktionen
- submit-review
- central approve
- central reject
- publish

### Muss prüfen
- who may call the endpoint
- from which workflow state
- with which required fields
- with which side effects
- with which audit event
- what denial/error behavior must happen

OWASP’s API guidance emphasizes that each protected endpoint needs explicit access control, and workflow actions on controlled objects are especially sensitive to broken function/object authorization. [2](https://gdpr-info.eu/art-5-gdpr/)[3](https://datenschutz-hamburg.de/fileadmin/user_upload/HmbBfDI/Datenschutz/Informationen/240611_Information_Applicant_Data_Protection_and_Recruiting_EN.pdf)

### Output
- workflow action matrix
- allowed transitions
- forbidden transitions
- permission mapping
- audit mapping

---

## Task 5 – Confirm Public Application Submission Baseline
### Beschreibung
Definiere die Baseline für öffentliche Formular-/Bewerbungssubmission.

### Fokus
- form retrieval
- submission payload
- required privacy notice reference
- required consent acknowledgement where configured
- minimal response object
- no routing detail exposure
- validation failures

### Muss sicherstellen
- no public submission without privacy linkage
- no hidden internal routing leak
- submission is structured
- failure behavior is deterministic

### Output
- submission contract confirmation
- validation rule set
- rejection/error cases
- minimal persistence assumptions

---

## Task 6 – Define API-Level Security Requirements
### Beschreibung
Ordne jeder API-Klasse verbindliche Sicherheitsanforderungen zu.

### Muss definieren
- public vs internal auth requirements
- MFA-relevant endpoints
- mTLS candidate endpoint groups
- object-level auth requirement groups
- no-token / invalid-token / expired-token behavior
- correlation/audit requirement

### Output
- API security matrix
- required auth/authz model per group
- security-relevant negative test set

---

## Task 7 – Define Audit Hook Baseline per Endpoint Group
### Beschreibung
Lege fest, welche Endpoint-Aktionen Wave-1-auditierbar sein müssen.

### Mindestkandidaten
- protected endpoint auth failure
- job create
- job update
- submit-review
- approve/reject
- publish
- public form submit
- privacy notice mismatch
- authorization denial
- access scope denial

NIST log-management guidance stresses that logging is essential for investigation and remediation, and centralized visibility is a critical security capability. [6](https://pages.nist.gov/800-63-3/sp800-63b.html)[7](https://csrc.nist.gov/pubs/sp/800/63/b/upd2/final)

### Output
- audit hook map
- minimal event field model
- traceability requirement list

---

## Task 8 – Validate API Foundation Against Wave-1 Gates
### Beschreibung
Prüfe die definierte API- und Workflow-Basis gegen die bestehenden Quality-/Security-/Privacy-Gates.

### Muss prüfen
- Test and Quality Gates compatibility
- Security Architecture compatibility
- Implementation Checklist alignment
- no No-Go condition already present in the design

### Output
- gate compatibility summary
- identified blockers
- gate risks to resolve before WP03

---

# 8. Acceptance Criteria for This Work Package

Dieses Arbeitspaket ist erfolgreich abgeschlossen, wenn:

## 8.1 API Foundation
- API-Gruppen final bestätigt sind
- Public APIs klar abgegrenzt sind
- Internal Governance APIs klar abgegrenzt sind
- Workflow APIs regelbasiert definiert sind

## 8.2 Workflow Foundation
- submit-review / approve / publish Logik technisch beschreibbar und validierbar ist
- ungültige Übergänge erkannt und abgewiesen werden können

## 8.3 Applicant Entry Foundation
- public form retrieval and submission baseline bestätigt ist
- privacy notice linkage technisch verankert ist
- keine interne Routinglogik öffentlich sichtbar wird

## 8.4 Security Foundation
- required auth per endpoint group definiert ist
- object-level authorization expectation klar definiert ist
- MFA-relevante Endpoint-Gruppen identifiziert sind
- mTLS candidates identifiziert sind
- TLS baseline berücksichtigt ist
- Audit hooks definiert sind

## 8.5 Anschlussfähigkeit
- Work Package 03 kann auf dieser Basis direkt mit UI/service realization oder workflow/service realization weitermachen
- keine kritische API-/Workflow-/Security-Lücke ungeklärt bleibt

---

# 9. Pflicht-Tests / Validierungen

## 9.1 API Contract Validation
- required request fields validated
- forbidden fields rejected where necessary
- invalid enum values rejected
- pagination/meta format stable
- error model consistent

## 9.2 Public Exposure Validation
- public jobs endpoint leaks no internal fields
- public pages endpoint leaks no internal workflow states
- public forms endpoint leaks no internal routing detail

## 9.3 Workflow Validation
- submit-review fails without required state or data
- approve fails for unauthorized actor
- publish fails without approval
- invalid state transition is rejected predictably

## 9.4 Security Validation
- internal endpoints require auth
- sensitive groups require correct permission model
- object-based actions require object-level check
- no auth bypass path exists in contract logic
- protected endpoints align with TLS-only requirement

---

# 10. No-Go Conditions for This Work Package

Dieses Arbeitspaket ist **nicht freigabefähig**, wenn:

1. Public und Internal API-Klassen nicht sauber getrennt sind
2. Public responses interne oder sensitive Felder enthalten
3. Workflow-Actions ohne klare Rollen-/Statuslogik definiert werden
4. Form submission ohne PrivacyNoticeVersion-Bezug möglich bleibt
5. protected internal endpoints keine klare Auth-Pflicht haben
6. object-level authorization für objektbasierte APIs unklar bleibt
7. zentrale Freigabelogik technisch nicht enforcebar ist
8. Audit hooks für Approval/Publish/Submissions fehlen
9. TLS-only / protected transport baseline in der API-Logik nicht berücksichtigt ist
10. kritische Lücken als implizite Annahmen stehen bleiben

---

# 11. Verpflichtende Antwortstruktur des Senior Developer Agent

Der Senior Developer Agent muss auf dieses Arbeitspaket mit genau dieser Struktur antworten:

## Section 1 – Read Confirmation
- gelesene bindende Dokumente
- bestätigte Relevanz für WP02

## Section 2 – Confirmed API Group Matrix
- API groups
- sensitivity class
- auth requirement
- audit requirement

## Section 3 – Public API Baseline
- confirmed endpoints
- allowed fields
- denied fields
- error behavior

## Section 4 – Internal Governance and Workflow API Baseline
- confirmed endpoints
- permission model
- transition model
- invalid transition behavior

## Section 5 – Applicant Entry Baseline
- form retrieval rules
- submission rules
- privacy linkage rules
- rejection behavior

## Section 6 – Security and Audit Hooks
- object-level authorization skeleton on API layer
- MFA relevant endpoints
- mTLS candidates
- audit trigger map

## Section 7 – Risks and Required Decisions
- critical risks
- blockers
- required decisions before WP03

## Section 8 – Proposed Next Work Package Readiness
- readiness for WP03
- missing prerequisites
- recommended next implementation focus

---

# 12. Empfohlener nächster Schritt nach diesem Arbeitspaket

Nach erfolgreichem Abschluss dieses Arbeitspakets soll direkt folgen:

## `24_Wave_1_Technical_Work_Package_03_Public_Experience_and_Job_Governance_Realization.md`

Fokus:
- realization of homepage/employer/jobs public experience
- realization of job draft to publish workflow path
- selected career path page realization
- first initiative application page realization
- first UI/service-layer integration using approved APIs and workflow actions

---

# 13. Finale Regel

Dieses Arbeitspaket ist nur dann erfolgreich, wenn der Senior Developer Agent:
- die API- und Workflow-Basis explizit stabilisiert,
- Public/Internal/Sensitive Grenzen sauber trennt,
- Privacy und Security bereits auf Endpoint-Ebene mitdenkt,
- und keine kritische Access-/Workflow-/Submission-Lücke ungeklärt lässt.