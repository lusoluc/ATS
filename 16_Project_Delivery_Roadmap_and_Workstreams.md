# 16_Project_Delivery_Roadmap_and_Workstreams.md

## Dokumentstatus
- Version: 1.0
- Zweck: Projektliefermodell, Workstreams, Meilensteine, Abhängigkeiten, Governance und Rollout-Logik für die neue Karriereplattform des Enterprises
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, umsetzungsorientiert
- Regel: Wenn dieses Dokument mit Final Source of Truth oder Sicherheits-/Privacy-Regeln kollidiert, gelten die dort definierten harten Regeln

---

# 1. Ziel dieses Dokuments

Dieses Dokument definiert:
- die Projektstruktur,
- die zentralen Workstreams,
- die Lieferreihenfolge,
- die Meilensteine,
- die Abhängigkeiten,
- die Governance- und Entscheidungswege,
- und die empfohlene Rollout-Reihenfolge für die neue Karriereplattform des Enterprises.

Das Ziel ist, die Plattform nicht als unstrukturierten Big-Bang umzusetzen, sondern als kontrolliertes, mehrstufiges Delivery-Programm.

---

# 2. Projektziel

Die neue Karriereplattform soll den aktuellen Enterprise-Kontext in eine strukturierte Zielarchitektur überführen:
- mehrere Karrierepfade,
- strukturierte Stellenanzeigen,
- zentrale HR-Karriere-Governance,
- lokale fachliche Recruiting-Beteiligung,
- datenschutz- und sicherheitsfähige Bewerbungslogik,
- barrierefreie und suchmaschinenfreundliche öffentliche Karriereerfahrung. [1](https://www.dvinci.de/karrierewebseite/)[2](https://www.dvinci.de/bewerbermanagement-software/)[3](https://www.dvinci.de/features/)

---

# 3. Delivery-Prinzipien

## 3.1 Kein Big Bang
Die Plattform soll phasenweise geliefert werden.

## 3.2 Erst Modell, dann Implementierung
Vor Umsetzung müssen Zielmodell, Rollen, Workflows, Templates, Privacy-/Retention-Basis und Sicherheitsarchitektur festgelegt und freigegeben sein.

## 3.3 Zentrale Governance, kontrollierte lokale Aktivierung
Zentrale HR-Karriere-Standards und Freigaben müssen zuerst funktionsfähig sein, bevor lokale Einheiten produktiv arbeiten.

## 3.4 Produktionsnahe Qualität vor öffentlichem Go-Live
Es darf kein öffentliches Go-Live geben, bevor Privacy, Security, Accessibility, Template-Governance und zentrale Freigabeflows produktionsreif sind.

---

# 4. Projekt-Workstreams

## 4.1 Workstream A – Business & Operating Model
### Ziel
Festlegung des Zielbetriebsmodells für zentrale HR-Karriere-Governance und lokale Recruiting-Ausführung.

### Inhalte
- Rollenmodell
- zentrale vs. lokale Verantwortlichkeiten
- Bewerberprozess-Operating-Model
- zentrale Freigabe von Stellenanzeigen
- lokale Eignungs- und Einladungslogik
- kontrollierte lokale Prozessvarianten

### Hauptowner
- Product Owner
- Central HR Career Department
- Enterprise Architect

---

## 4.2 Workstream B – Domain & Data Model
### Ziel
Finalisierung des Enterprise-spezifischen Zielmodells.

### Inhalte
- Organization
- Facility
- Location
- JobFamily
- CareerPath
- ContactPerson
- JobPosting
- ApplicationForm
- PrivacyNoticeVersion
- DataRetentionPolicy
- ApplicantAccessAssignment
- Templates und Prozessmodelle

### Hauptowner
- Enterprise Architect
- CMS Architect
- Senior Developer Agent

---

## 4.3 Workstream C – Content Model & CMS
### Ziel
Aufbau des redaktionellen Zielmodells für Karriereinhalte und Seitentypen.

### Inhalte
- Seitentypen
- Inhaltsmodule
- CareerPath-Seiten
- JobFamily-Seiten
- Employer-Bereich
- Initiative Application Page
- Service-/FAQ-/Privacy-/Accessibility-Seiten
- Content Ownership und Freigabelogik

### Hauptowner
- CMS Architect
- UX Architect
- Central HR Career Department

---

## 4.4 Workstream D – Job & Recruiting Workflow Platform
### Ziel
Aufbau der strukturierten Stellen- und Recruitinglogik.

### Inhalte
- JobTemplates
- ProcessTemplates
- JobPosting-Struktur
- Review-/Approval-Flow
- lokaler Recruiting-Flow
- Routing-Logik
- Initiativbewerbungslogik
- Entscheidungsstufen

### Hauptowner
- Product Owner
- Enterprise Architect
- Senior Developer Agent
- Central HR Career Department

---

## 4.5 Workstream E – Privacy, Security & Compliance
### Ziel
Aufbau der Datenschutz-, Sicherheits- und Audit-Basis.

### Inhalte
- PrivacyNoticeVersion
- Retention-/Deletion-Logik
- ApplicantAccessAssignment
- TLS / Zertifikate / mTLS
- MFA / AuthN / AuthZ
- Audit Logging
- Secrets / Key Management
- Access Control
- Need-to-know-Prinzip

### Hauptowner
- Security Architect / Security Lead
- Privacy / Compliance Reviewer
- Senior Developer Agent

---

## 4.6 Workstream F – Public Experience / UX / Discovery
### Ziel
Aufbau der Candidate Experience.

### Inhalte
- Karriere-Startseite
- Jobsuche
- Jobdetailseiten
- CareerPath-Discovery
- JobFamily-Discovery
- Bewerbungs-CTAs
- Mobil-/Accessibility-Qualität
- interne Verlinkung / Conversion-Flows

### Hauptowner
- UX Architect
- Product Owner
- Senior Developer Agent

---

## 4.7 Workstream G – Migration & Content Preparation
### Ziel
Überführung der aktuellen Enterprise-Karriereinhalte in die Zielstruktur.

### Inhalte
- Content Inventory
- Mapping Alt -> Neu
- Content Rewrite
- Facility/Location/JobFamily-Strukturierung
- Kontakt-Normalisierung
- Redirect-/URL-Plan
- Go-Live-Inhaltsprüfung

### Hauptowner
- CMS Architect
- Content Lead / HR Career
- Migration Lead

---

## 4.8 Workstream H – QA, Readiness & Rollout
### Ziel
End-to-end Qualitätssicherung und kontrollierter Rollout.

### Inhalte
- Teststrategie
- Security-/Privacy-Gates
- Accessibility-/SEO-QA
- Workflow-QA
- UAT
- Pilot-Rollout
- Public Go-Live
- Hypercare

### Hauptowner
- QA Lead
- Delivery Lead
- Product Owner
- Security / Privacy Reviewer

---

# 5. Delivery-Phasen

## Phase 0 – Alignment & Freeze
### Ziel
Fachliche und architektonische Klarheit schaffen.

### Deliverables
- Final Source of Truth
- Enterprise-clean Master Concept
- Rollen-/Operating-Model
- Security baseline
- Migration baseline
- Delivery model

### Exit Criteria
- keine offenen Kernbegriffe mehr
- zentrale und lokale Rollen geklärt
- Zielsystem-Scope bestätigt

---

## Phase 1 – Core Modelling & Governance Foundation
### Ziel
Kernmodell und Governance-Layer technisch/fachlich stabilisieren.

### Deliverables
- Domain model final
- Entity model final
- role model final
- workflow model final
- job/process template model
- privacy/security target controls
- API contract baseline

### Exit Criteria
- Zielentitäten freigegeben
- zentrale Approval-Logik freigegeben
- Privacy-/Retention-Modell freigegeben
- Sicherheitsbasis freigegeben

---

## Phase 2 – Foundation Build
### Ziel
Technische Plattformbasis und erste Kernbausteine aufbauen.

### Deliverables
- core schemas
- content model implementation
- job object implementation
- form model implementation
- auth/authz baseline
- certificate/TLS baseline
- audit logging baseline

### Exit Criteria
- technische Kernobjekte implementiert
- AuthN/AuthZ-Grundlagen vorhanden
- zentrale technische Workflows lauffähig

---

## Phase 3 – MVP Candidate Experience
### Ziel
Erste nutzbare Karriereplattform erzeugen.

### Deliverables
- homepage
- employer area
- selected career path pages
- selected job family pages
- job list
- job detail
- initiative application page
- contact modules
- basic privacy/service pages

### Exit Criteria
- candidate core flows funktionieren
- public content basis verfügbar
- structured job rendering produktionsnah

---

## Phase 4 – Controlled Recruiting Operations
### Ziel
Zentrale Governance und lokale Recruiting-Prozesse aktivierbar machen.

### Deliverables
- job template enforcement
- process template enforcement
- local job drafting
- central approval workflow
- local suitability review flow
- invitation decision flow
- applicant access assignment
- privacy notice linkage
- retention policy linkage

### Exit Criteria
- lokale Draft-Erstellung funktioniert
- zentrale Prüfung/Freigabe funktioniert
- Need-to-know-Zugriffe funktionieren

---

## Phase 5 – Hardening & Compliance Readiness
### Ziel
Produktionsreife Sicherheit, Privacy, Accessibility und SEO herstellen.

### Deliverables
- MFA / privileged auth final
- mTLS where required
- retention automation
- audit event completeness
- accessibility QA pass
- SEO readiness
- rate limiting / abuse controls
- operational runbooks

### Exit Criteria
- Test & Quality Gates bestanden
- keine kritischen Sicherheits-/Privacy-Blocker
- Produktionsfreigabe möglich

---

## Phase 6 – Migration & Rollout
### Ziel
Inhalte migrieren und kontrolliert live gehen.

### Deliverables
- content migration wave 1
- URL/redirect setup
- owner assignments final
- final QA and UAT
- pilot / soft launch
- public go-live
- hypercare

### Exit Criteria
- kritische Inhalte live
- Prozesse stabil
- Hypercare aktiv

---

# 6. Meilensteine

## M1 – Concept Freeze
- Final Source of Truth freigegeben
- Enterprise-clean Master Concept freigegeben
- Operating Model freigegeben

## M2 – Architecture & Security Freeze
- Domain/Entity/API/Security-Design freigegeben
- zentrale Approval- und Privacy-Logik freigegeben

## M3 – Foundation Complete
- Kernobjekte und Kern-APIs umgesetzt
- AuthN/AuthZ/TLS/Audit Basis vorhanden

## M4 – MVP Experience Ready
- öffentliche Kernseiten und Jobsuche lauffähig
- erste Bewerbungslogik lauffähig

## M5 – Governance Ready
- zentrale HR-Freigabe aktiv
- lokale Recruiting-Akteure steuerbar
- Need-to-know Access wirksam

## M6 – Compliance & Security Ready
- Test- und Quality-Gates bestanden
- Privacy / Security / Accessibility / SEO freigegeben

## M7 – Public Go-Live
- Inhalte migriert
- Pilot erfolgreich
- öffentlicher Rollout erfolgt

---

# 7. Abhängigkeiten

## 7.1 Kritische fachliche Abhängigkeiten
- kein Content Model ohne finalen Domain Split
- kein Jobmodell ohne Facility/Location/JobFamily-Klärung
- kein lokaler Recruiting-Flow ohne Rollen-/Zugriffsmodell
- keine öffentlichen Formulare ohne PrivacyNoticeVersion und RetentionPolicy
- kein Publish-Flow ohne zentrale Approval-Definition

## 7.2 Kritische technische Abhängigkeiten
- keine produktive API ohne AuthN/AuthZ/TLS Baseline
- keine applicant-sensitive API ohne Access Assignment
- kein Rollout ohne Audit Logging
- keine Public Go-Live-Freigabe ohne SEO/Accessibility Basis

## 7.3 Kritische Migrationsabhängigkeiten
- keine Migration ohne finalen Zieltyp-Mapping
- keine Redirect-Planung ohne Ziel-URL-Struktur
- keine kontaktbezogene Migration ohne Owner-/Freigabeklarheit

---

# 8. Governance-Struktur

## 8.1 Steering / Decision Layer
### Teilnehmer
- Product Owner
- Central HR Career Lead
- Enterprise Architect
- Security / Privacy Lead
- Delivery Lead

### Aufgaben
- Scope-Entscheidungen
- Konfliktentscheidungen
- Go/No-Go zu Meilensteinen
- Priorisierung von MVP vs. späteren Wellen

## 8.2 Design Authority
### Teilnehmer
- Enterprise Architect
- CMS Architect
- UX Architect
- Security Architect
- Senior Developer Agent (reviewed output)

### Aufgaben
- Modellintegrität
- Architekturentscheidungen
- API-/Template-/Workflow-Freigaben

## 8.3 Operational Content & Process Board
### Teilnehmer
- Central HR Career Department
- ausgewählte lokale Vertreter
- CMS / UX / Product

### Aufgaben
- Content Priorisierung
- Template-Freigaben
- CareerPath-/JobFamily-Seitenpriorität
- Bewerbungsprozess-Textlogik

---

# 9. Rollout-Strategie

## 9.1 Empfohlene Reihenfolge
### Wave 1
- Homepage
- Employer area
- core career paths
- job list / job detail
- initiative application
- privacy / accessibility / core service pages

### Wave 2
- selected job family pages
- structured facility/location usage
- contact normalisation
- enhanced service/FAQ pages

### Wave 3
- additional landing pages
- extended local/facility pages
- advanced analytics
- further process variants where justified

## 9.2 Pilot-Logik
Empfohlen wird ein kontrollierter Pilot:
- begrenzter Inhaltsscope
- begrenzte interne Usergruppe
- begrenzte lokale Recruiting-Beteiligung
- enge Hypercare

---

# 10. Delivery Risks

## 10.1 Model Risk
Wenn Facility, Location, JobFamily und CareerPath nicht stabil bleiben, entsteht Rework in Jobsuche, Seitenmodell, Routing und Local Access.

## 10.2 Governance Risk
Wenn zentrale HR-Freigabe oder lokale Prozessgrenzen zu spät eingebaut werden, entstehen Fehler, Inkonsistenz und Datenschutzrisiken.

## 10.3 Migration Risk
Wenn alte Inhalte ungeprüft kopiert werden, werden Legacy-Strukturen und Widersprüche ins Zielsystem übernommen.

## 10.4 Security / Privacy Risk
Wenn Applicant Access, Retention, Privacy Notice, MFA oder TLS zu spät kommen, ist die Plattform fachlich oder regulatorisch nicht freigabefähig.

## 10.5 Scope Risk
Wenn MVP und spätere Wellen nicht klar getrennt werden, verzögert sich die produktive Nutzbarkeit.

---

# 11. Success Criteria

## 11.1 Business / Experience
- klare CareerPath-Einstiege
- nutzbare Jobsuche
- strukturierte Jobdetailseiten
- funktionierende Initiative Application
- verständliche Contact/Process guidance

## 11.2 Governance / Operations
- lokale Draft-Erstellung möglich
- zentrale Stellenfreigabe funktioniert
- lokale Eignungsprüfung funktioniert
- unzulässige Sichtbarkeit ist ausgeschlossen

## 11.3 Security / Privacy / Compliance
- PrivacyNoticeVersion aktiv
- RetentionPolicy aktiv
- ApplicantAccessAssignment aktiv
- MFA/TLS/AuthZ wirksam
- Audit Logging vollständig

---

# 12. Final Rule

Das Projekt gilt nicht als erfolgreich, wenn nur eine schöne Oberfläche live ist.

Es gilt erst dann als erfolgreich, wenn:
- Candidate Experience funktioniert,
- Governance funktioniert,
- lokale Recruiting-Beteiligung kontrolliert funktioniert,
- Datenschutz/Sicherheit funktioniert,
- Inhalte korrekt migriert sind,
- und die Plattform im Enterprise-Betriebsmodell stabil nutzbar ist.