# 22_Wave_1_Technical_Work_Package_01_Core_Model_and_Auth.md

## Dokumentstatus
- Version: 1.0
- Zweck: Erstes konkretes technisches Arbeitspaket für Wave 1
- Fokus: Core Model, AuthN/AuthZ Baseline, Workflow-State Baseline, technische Schutzmechanismen
- Zielgruppe:
  - Senior Developer Agent
  - Technical Lead
  - Enterprise Architect
  - Security Architect
  - Delivery Lead
- Gültigkeit: Landesverein-spezifisch, benchmark-frei, Wave-1-startfähig
- Regel: Wenn dieses Arbeitspaket dem Final Source of Truth widerspricht, gilt immer der Final Source of Truth

---

# 1. Ziel dieses Arbeitspakets

Dieses Arbeitspaket ist der **erste konkrete technische Einstieg** in die Umsetzung der neuen Landesverein-Karriereplattform.

Es soll die Grundlage schaffen für:
- stabile Zielentitäten,
- stabile Referenzbeziehungen,
- stabile Rollen- und Berechtigungslogik,
- stabile Workflowstatus,
- und eine sichere technische Basis für alle weiteren Arbeitspakete.

Dieses Arbeitspaket ist erfolgreich, wenn danach:
1. das Core Model technisch bestätigt ist,
2. die Kernobjekte implementierbar beschrieben sind,
3. die erste AuthN/AuthZ-/TLS-Basis technisch geplant und teilweise implementierbar ist,
4. und spätere Work Packages nicht mehr auf unscharfen Modellannahmen beruhen.

---

# 2. Warum dieses Arbeitspaket zuerst kommt

Der aktuelle Landesverein-Kontext zeigt bereits:
- mehrere Karrierepfade,
- strukturierte Jobfelder,
- unterschiedliche Einrichtungen und Orte,
- sowie eine bestehende Bewerbungs- und Kontaktlogik. [1](https://www.dvinci.de/karrierewebseite/)

Wenn der Senior Developer Agent **vor** einer stabilen Modell- und Sicherheitsbasis mit UI oder Prozesslogik startet, entstehen typische Risiken:
- Facility und Location werden vermischt,
- JobFamily und CareerPath werden falsch zusammengezogen,
- Bewerberzugriffe werden zu breit,
- Approval-Logik wird zu spät eingebaut,
- oder Security/Privacy werden als “spätere Ergänzung” behandelt.  
Gerade APIs müssen aber von Anfang an **HTTPS-only**, **authentifiziert**, **autorisiert** und für objektbasierte Ressourcen gegen **Broken Object Level Authorization** abgesichert werden. [7](https://datenschutz-hamburg.de/fileadmin/user_upload/HmbBfDI/Datenschutz/Informationen/240611_Information_Applicant_Data_Protection_and_Recruiting_EN.pdf)[4](https://gdpr-info.eu/art-5-gdpr/)[6](https://gdpr-info.eu/art-6-gdpr/)

---

# 3. Scope dieses Arbeitspakets

## 3.1 In Scope

### 3.1.1 Kernentitäten
- Organization
- Facility
- Location
- JobFamily
- CareerPath
- ContactPerson
- JobPosting
- ApplicationForm
- ApplicationRoute
- WorkflowState
- Role
- Permission
- PrivacyNoticeVersion
- DataRetentionPolicy
- ApplicantAccessAssignment
- JobTemplate
- ProcessTemplate

### 3.1.2 Kernbeziehungen
- Organization -> Facility
- Facility -> JobPosting
- Location -> JobPosting
- JobFamily -> JobPosting
- CareerPath -> JobPosting (optional where applicable)
- ApplicationForm -> JobPosting / initiative flow
- Role -> Permission
- ApplicantAccessAssignment -> application context
- JobTemplate -> JobPosting
- ProcessTemplate -> workflow / local process use

### 3.1.3 Technische Sicherheitsbasis
- protected endpoint classification
- authentication boundary definition
- MFA scope definition for privileged roles
- object-level authorization model
- TLS/certificate baseline definition
- mTLS requirement classification for privileged service calls
- audit event baseline definition

---

## 3.2 Out of Scope
Dieses Arbeitspaket enthält **noch nicht**:
- öffentliche Homepage-/UI-Implementierung
- Joblist-/Jobdetail-Rendering
- öffentliche Form-UI
- tiefere Content-Migration
- vollständige Candidate-Flow-UI
- facility/location public pages
- SEO-/Accessibility-UI-Feinarbeit
- fortgeschrittene Analytics-Visualisierung

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

Ohne diese Inputs darf dieses Arbeitspaket nicht gestartet werden.

---

# 5. Verbindliche Ziele des Arbeitspakets

## Ziel A – Core Model Confirmation
Der Agent muss eine finalisierte, für Wave 1 bestätigte technische Kernmodell-Sicht erzeugen.

## Ziel B – Relationship Integrity
Der Agent muss sicherstellen, dass alle kritischen Beziehungen technisch konsistent und validierbar sind.

## Ziel C – Authorization Skeleton
Der Agent muss die erste belastbare AuthN/AuthZ-Basis definieren, insbesondere für:
- interne Rollen
- geschützte APIs
- objektbezogenen Zugriff
- applicant-sensitive Kontexte

## Ziel D – Workflow Skeleton
Der Agent muss die minimalen Workflow-States und Workflow-Übergänge für Wave 1 technisch bestätigbar machen.

## Ziel E – Security Baseline Readiness
Der Agent muss die technische Grundlage schaffen, damit spätere Public- und Applicant-Flows nicht auf unsicherem Fundament entstehen.

---

# 6. Verbindliche Deliverables

Der Senior Developer Agent muss als Output dieses Arbeitspakets mindestens folgende Artefakte liefern:

## 6.1 Deliverable 1 – Wave-1 Technical Domain Confirmation
Enthält:
- bestätigte Liste der Wave-1-Entitäten
- bestätigte Pflichtfelder
- bestätigte Typgrenzen
- bestätigte kritische Beziehungen
- markierte offene Modellfragen

## 6.2 Deliverable 2 – Relationship and Integrity Matrix
Enthält:
- 1:N, M:N und optionale Beziehungen
- Pflicht-/Optionalbeziehungen
- Integritätsregeln
- Sperrregeln gegen Modellvermischung

## 6.3 Deliverable 3 – Authorization Boundary Draft
Enthält:
- Public vs Internal vs Sensitive API boundaries
- Rollenbezug
- Objektbezug
- Kontextbezug
- MFA scope
- mTLS classification where relevant

## 6.4 Deliverable 4 – Workflow-State Baseline
Enthält:
- gültige Workflow-States pro Objekttyp
- erlaubte Übergänge
- verbotene Übergänge
- Rollenbezug pro Übergang

## 6.5 Deliverable 5 – Security Control Mapping
Enthält:
- TLS baseline requirements
- auth requirements per API class
- privileged-role security requirements
- logging baseline
- certificate handling baseline

## 6.6 Deliverable 6 – Technical Risk and Gap List
Enthält:
- offene Risiken
- Blocker
- Unklarheiten
- notwendige Entscheidungen vor Work Package 02

---

# 7. Konkrete Arbeitsaufgaben

## Task 1 – Confirm Wave-1 Entity Boundary
### Beschreibung
Bestätige die für Wave 1 relevanten Entitäten und stelle sicher, dass keine zentrale Typgrenze verletzt wird.

### Muss prüfen
- Facility != Location
- JobFamily != CareerPath
- JobPosting != CareerPage
- ApplicationForm != ApplicationRoute
- PrivacyNoticeVersion != DataRetentionPolicy
- ApplicantAccessAssignment != allgemeine Rollenlogik

### Output
- bestätigte Entitätenliste
- markierte Modellgrenzen
- offene Punkte

---

## Task 2 – Confirm Mandatory Fields and Constraints
### Beschreibung
Prüfe und bestätige Pflichtfelder für alle Wave-1-Kernobjekte.

### Fokusobjekte
- JobPosting
- ApplicationForm
- WorkflowState
- Role
- Permission
- JobTemplate
- ProcessTemplate
- PrivacyNoticeVersion
- ApplicantAccessAssignment

### Output
- Feldliste pro Objekt
- Pflichtfeldregeln
- Validierungsregeln
- Konfliktpunkte

---

## Task 3 – Define Relationship Integrity Rules
### Beschreibung
Lege technische Referenz- und Integritätsregeln fest.

### Beispiele
- JobPosting darf nicht ohne Facility, Location und JobFamily bestehen
- public ContactPerson braucht Kontext
- ApplicationForm braucht PrivacyNoticeVersion
- JobTemplate muss aktiv sein, bevor JobDraft es nutzen darf
- LocalProcessVariant darf zentrale Pflichtschritte nicht entfernen

### Output
- Relationship Matrix
- Integrity Rules
- Negative Cases

---

## Task 4 – Define Protected API Classes
### Beschreibung
Klassifiziere alle relevanten API-Gruppen nach Schutzbedarf.

### Klassen
- Public read APIs
- internal governance APIs
- internal recruiting APIs
- sensitive applicant APIs
- workflow APIs
- privacy/compliance APIs
- privileged service-to-service APIs

### Output
- API class list
- required authentication per class
- required authorization per class
- logging requirement per class
- mTLS candidate list

---

## Task 5 – Define Human Authentication Baseline
### Beschreibung
Lege die Baseline für interne User-Authentifizierung fest.

### Muss definieren
- welche Rollen privilegiert sind
- welche Rollen MFA benötigen
- welche Session-Sicherheitsregeln gelten
- welche Reauthentication-sensitive Aktionen existieren

### Output
- privileged role list
- MFA scope
- session baseline
- reauth-sensitive action list

---

## Task 6 – Define Object-Level Authorization Skeleton
### Beschreibung
Lege fest, wie object-level authorization technisch durchgesetzt wird.

### Muss prüfen
- JobPosting access
- applicant access
- workflow transition rights
- local vs central access
- analyst read restrictions
- publisher constraints

### Output
- object-level rule list
- role + context + object access skeleton
- BOLA prevention outline

OWASP identifies object-level authorization failures as the most common API issue and requires authorization checks for every endpoint that acts on an object ID. [7](https://datenschutz-hamburg.de/fileadmin/user_upload/HmbBfDI/Datenschutz/Informationen/240611_Information_Applicant_Data_Protection_and_Recruiting_EN.pdf)[4](https://gdpr-info.eu/art-5-gdpr/)

---

## Task 7 – Define TLS / Certificate Baseline
### Beschreibung
Bestätige den technischen Mindeststandard für Transport Security.

### Muss prüfen
- HTTPS only
- TLS 1.3 default
- TLS 1.2 compatibility only if needed
- certificate lifecycle baseline
- public vs internal certificate separation
- privileged mTLS candidates

OWASP’s TLS guidance recommends TLS 1.3 by default and allows TLS 1.2 only where needed, while insecure legacy protocol versions must be disabled. [6](https://gdpr-info.eu/art-6-gdpr/)[4](https://gdpr-info.eu/art-5-gdpr/)

### Output
- transport security baseline
- certificate handling baseline
- mTLS classification note

---

## Task 8 – Define Audit Event Baseline
### Beschreibung
Lege fest, welche Events schon in Wave 1 zwingend auditierbar sein müssen.

### Mindestkandidaten
- auth success/failure internal roles
- job create/update
- job submit-review
- central approval/rejection
- publication
- applicant access assignment create/remove
- restricted applicant read
- privacy notice changes
- workflow denial
- mTLS failure where applicable

### Output
- audit event list
- minimal log fields
- mandatory traceability rules

NIST log-management guidance emphasizes that logs are essential for investigation and remediation, and centralized visibility is a critical control objective. [8](https://pages.nist.gov/800-63-3/sp800-63b.html)[9](https://csrc.nist.gov/pubs/sp/800/63/b/upd2/final)

---

# 8. Acceptance Criteria for This Work Package

Dieses Arbeitspaket gilt nur dann als erfolgreich abgeschlossen, wenn:

## 8.1 Modell
- alle Wave-1-Entitäten bestätigt sind
- alle Pflichtfelder bestätigt sind
- alle kritischen Beziehungen bestätigt sind
- keine Kernmodellgrenze unklar bleibt

## 8.2 Governance
- zentrale und lokale Rollenabgrenzung technisch bestätigbar ist
- zentrale Freigabelogik technisch modellierbar ist
- lokale Scope-Grenzen technisch modellierbar sind

## 8.3 Security
- API-Klassen klar klassifiziert sind
- geschützte APIs klar von öffentlichen APIs getrennt sind
- MFA-Scope für privilegierte Rollen definiert ist
- object-level authorization skeleton steht
- TLS/certificate baseline bestätigt ist
- mTLS-Kandidaten identifiziert sind

## 8.4 Operative Anschlussfähigkeit
- Work Package 02 kann ohne Kernmodell-Neuerfindung starten
- keine kritische Sicherheits- oder Privacy-Lücke blockiert die nächste Welle

---

# 9. Pflicht-Tests / Validierungen

## 9.1 Modellvalidierung
- check mandatory fields per entity
- check disallowed entity merging
- check required relationship presence
- check invalid reference scenarios

## 9.2 Rollen-/Permissions-Validierung
- privileged role identification review
- central vs local access boundary review
- applicant-sensitive role restriction review

## 9.3 Security-Validierung
- protected API classification review
- TLS baseline review
- MFA scope review
- mTLS classification review
- audit event coverage review

---

# 10. No-Go Conditions for This Work Package

Dieses Arbeitspaket ist **nicht freigabefähig**, wenn eine der folgenden Bedingungen zutrifft:

1. Facility und Location sind nicht sauber getrennt
2. JobFamily und CareerPath sind nicht sauber getrennt
3. JobPosting-Pflichtfelder bleiben unklar
4. ApplicationForm / PrivacyNoticeVersion Beziehung ist unklar
5. zentrale Approval-Logik ist nicht technisch verankert
6. object-level authorization ist nicht konzipiert
7. MFA-Scope privilegierter Rollen ist unklar
8. TLS-/Zertifikatsbaseline ist nicht definiert
9. Audit Event Baseline ist nicht definiert
10. offene Lücken werden als implizite Annahmen stehen gelassen

---

# 11. Verpflichtende Antwortstruktur des Senior Developer Agent

Der Senior Developer Agent muss auf dieses Arbeitspaket mit genau dieser Struktur antworten:

## Section 1 – Read Confirmation
- gelesene bindende Dokumente
- bestätigte Relevanz für Wave 1

## Section 2 – Confirmed Wave-1 Entity Set
- finale Entitätenliste
- offene Fragen
- Konfliktpunkte

## Section 3 – Relationship and Constraint Summary
- Hauptbeziehungen
- Pflicht-/Optionalbeziehungen
- zentrale Integritätsregeln

## Section 4 – Security and Access Skeleton
- API classes
- auth requirements
- MFA scope
- object-level authorization skeleton
- TLS baseline
- mTLS candidate endpoints/services

## Section 5 – Workflow Baseline
- states
- transitions
- protected transitions
- central vs local constraints

## Section 6 – Risks and Required Decisions
- kritische Risiken
- Blocker
- Entscheidungen vor nächstem Arbeitspaket

## Section 7 – Proposed Next Work Package Readiness
- readiness for WP02
- missing prerequisites
- recommended next technical focus

---

# 12. Empfohlener nächster Schritt nach diesem Arbeitspaket

Nach erfolgreichem Abschluss dieses Arbeitspakets soll direkt folgen:

## `23_Wave_1_Technical_Work_Package_02_API_and_Workflow_Foundation.md`

Fokus:
- API contract final confirmation
- protected/internal/public endpoint realization plan
- submit-review / approve / publish workflow APIs
- ApplicationForm submission flow
- initial access-assignment flow
- initial audit hook integration

---

# 13. Finale Regel

Dieses Arbeitspaket darf nicht „oberflächlich beantwortet“ werden.

Es ist nur dann erfolgreich, wenn der Senior Developer Agent:
- das Kernmodell stabilisiert,
- die Sicherheitsbasis explizit macht,
- Governance technisch vorbereitbar macht,
- und keine kritische Modell- oder Security-Lücke ungeklärt lässt.
