# 08_Entity_Data_Model.md

## Dokumentstatus
- Version: 1.0
- Zweck: Verbindliches Entity-Data-Model für die Enterprise Karriereplattform
- Basis: Abgeleitet aus `00_FINAL_SOURCE_OF_TRUTH.md` und WP-Definitionen.

## 1. Kernentitäten (Core Domain)

### 1.1 Organization Domain
- **Organization**: Die Trägergesellschaft (z.B. Enterprise).
- **Facility**: Eine konkrete organisatorische Einrichtung (z.B. ein Psychiatrisches Zentrum). Darf nicht mit Location vermischt werden.
- **Location**: Ein geografischer Standort.
- **JobFamily**: Ein fachliches Berufsfeld (z.B. Pflege, Medizin, Verwaltung).
- **CareerPath**: Karriereeinstieg / Zielgruppe (z.B. Ausbildung, FSJ, Praktikum).
- **ContactPerson**: Ansprechperson für JobPostings, strukturiert referenziert.

### 1.2 Job Domain
- **JobPosting**: Strukturierte Stellenanzeige.
  - Pflichtfelder: `id`, `title`, `organization_id`, `facility_id`, `location_id`, `job_family_id`, `workflow_state_id`, `application_route_id`.
- **JobTemplate**: Vorlage für JobPostings (steuert z.B. Pflichtfelder).

### 1.3 Application Domain
- **ApplicationForm**: Strukturiertes Bewerbungsformular.
  - Pflichtbeziehung: `privacy_notice_version_id`.
- **ApplicationRoute**: Routing-Pfad einer eingehenden Bewerbung.

### 1.4 Content Domain
- **CareerPage**: Redaktionelle Seite.
- **LandingPage**: Spezifische Kampagnen- oder Zielgruppen-Landingpage.
- **SharedContentModule**: Wiederverwendbare Inhaltsbausteine (z.B. Benefits-Modul).

### 1.5 Governance & Security Domain
- **Role** & **Permission**: RBAC-Steuerung.
- **WorkflowState**: Status einer Entität (z.B. `draft`, `approved`).
- **PrivacyNoticeVersion**: Historisierte Datenschutz-Information.
- **DataRetentionPolicy**: Lösch- und Aufbewahrungsregeln.
- **ApplicantAccessAssignment**: Zwingendes Need-to-Know Berechtigungs-Mapping für PII-Daten.
- **ProcessTemplate**: Zentral verwalteter Recruiting-Prozess.
- **LocalProcessVariant**: Lokale Abweichung (in Wave 1 für Execution blockiert).

## 2. Kritische Beziehungen (Integritätsregeln)
- `JobPosting` -> gehört zu genau einer `Facility`.
- `JobPosting` -> gehört zu genau einer `Location`.
- `JobPosting` -> gehört zu genau einer `JobFamily`.
- `ApplicationForm` -> benötigt zwingend Verweis auf `PrivacyNoticeVersion`.
- `ApplicantAccessAssignment` -> verknüpft `User` + `Application` + `Context` (Facility/Location).
