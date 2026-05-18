# 17_Backlog_Epics_and_User_Stories.md

## Dokumentstatus
- Version: 1.0
- Zweck: Umsetzungsnaher Backlog-Rahmen mit Epics, Features, User Stories und Akzeptanzkriterien für die neue Enterprise-Karriereplattform
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, Zielmodell-konform
- Regel: Stories dürfen den Final Source of Truth nicht widersprechen

---

# 1. Ziel dieses Dokuments

Dieses Dokument übersetzt das Zielmodell in:
- Epics
- Features
- User Stories
- Akzeptanzkriterien

Die Stories sind so formuliert, dass sie:
- für Product / Architecture / Delivery nutzbar sind,
- vom Senior Developer Agent in Umsetzungspakete zerlegt werden können,
- und gleichzeitig Enterprise-spezifisch bleiben.

---

# 2. Epic-Struktur

## EPIC 1 – Career Experience Foundation
## EPIC 2 – Structured Job Platform
## EPIC 3 – Career Paths and Job Families
## EPIC 4 – Initiative Application and Applicant Entry
## EPIC 5 – Central Governance and Template Control
## EPIC 6 – Local Recruiting Operations
## EPIC 7 – Privacy, Retention and Applicant Access Control
## EPIC 8 – Security, Authentication and Certificates
## EPIC 9 – Accessibility and SEO
## EPIC 10 – Content Migration and Rollout
## EPIC 11 – Analytics, Auditability and Reporting

---

# 3. EPIC 1 – Career Experience Foundation

## Feature 1.1 – Career Homepage
### Story 1.1.1
As an interested visitor,  
I want a clear career homepage,  
so that I can quickly understand what career opportunities and entry paths exist.

#### Acceptance Criteria
- homepage contains clear primary entry points
- jobs search entry is visible
- career path entry is visible
- employer entry is visible
- initiative application entry is visible
- service/contact access is visible

### Story 1.1.2
As a mobile user,  
I want the career homepage to be usable on mobile devices,  
so that I can access relevant information without usability barriers.

#### Acceptance Criteria
- homepage works on mobile viewport
- key CTAs remain visible and usable
- no navigation dead ends on mobile

---

## Feature 1.2 – Employer Area
### Story 1.2.1
As a candidate,  
I want to understand who the Enterprise is as an employer,  
so that I can assess fit and relevance.

#### Acceptance Criteria
- employer page exists
- employer context is structured and readable
- page links to relevant career paths, job families or jobs

---

# 4. EPIC 2 – Structured Job Platform

## Feature 2.1 – JobPosting Model
### Story 2.1.1
As the platform,  
I must store jobs as structured JobPosting objects,  
so that search, filters, governance and templates can work reliably.

#### Acceptance Criteria
- JobPosting requires title, reference, facility, location, job family
- job cannot be published without required fields
- job model supports employment info and application target

## Feature 2.2 – Job List
### Story 2.2.1
As a candidate,  
I want to browse published jobs in a structured job list,  
so that I can discover relevant opportunities.

#### Acceptance Criteria
- public job list exists
- list uses structured job objects
- list supports filters

## Feature 2.3 – Job Detail
### Story 2.3.1
As a candidate,  
I want a detailed job page with all relevant job information,  
so that I can decide whether to apply.

#### Acceptance Criteria
- job detail page exists
- title, reference, facility, location, job family are visible
- application CTA exists
- job description sections are visible

---

# 5. EPIC 3 – Career Paths and Job Families

## Feature 3.1 – CareerPath Entities
### Story 3.1.1
As the platform,  
I must support CareerPath as a first-class concept,  
so that Enterprise-specific entry paths such as Ausbildung or FSJ/BFD can be represented clearly.

#### Acceptance Criteria
- CareerPath entity exists
- career path page type exists
- jobs and/or forms can be linked to career paths

## Feature 3.2 – CareerPath Pages
### Story 3.2.1
As a prospective trainee or volunteer,  
I want dedicated pages for my entry path,  
so that I can understand the context, requirements and next steps.

#### Acceptance Criteria
- dedicated page exists for Ausbildung
- dedicated page exists for FSJ/BFD
- additional career path pages can be added through template logic

## Feature 3.3 – JobFamily Model
### Story 3.3.1
As the platform,  
I must support JobFamily separately from CareerPath,  
so that professional fields and recruiting entry paths do not get mixed.

#### Acceptance Criteria
- JobFamily entity exists
- JobFamily can be referenced by jobs and pages
- JobFamily is not modelled as plain free text

---

# 6. EPIC 4 – Initiative Application and Applicant Entry

## Feature 4.1 – Initiative Application Page
### Story 4.1.1
As an interested person without a concrete vacancy,  
I want a dedicated initiative application path,  
so that I can still express interest in working for the Enterprise.

#### Acceptance Criteria
- initiative application page exists
- page explains purpose and next step
- page links to or contains valid application form logic

## Feature 4.2 – Public Application Forms
### Story 4.2.1
As an applicant,  
I want a clear and structured application form,  
so that I can submit my information reliably.

#### Acceptance Criteria
- public form endpoint exists
- required fields are validated
- privacy notice is linked
- submission returns controlled response

---

# 7. EPIC 5 – Central Governance and Template Control

## Feature 5.1 – JobTemplate
### Story 5.1.1
As the Central HR Career Department,  
I want job ads to follow approved templates,  
so that wording, structure and required fields remain consistent and errors are reduced.

#### Acceptance Criteria
- JobTemplate entity exists
- required template fields are enforceable
- jobs can be linked to templates
- jobs cannot be submitted without mandatory template data

## Feature 5.2 – Central Review
### Story 5.2.1
As Central HR Career Department,  
I want to review and approve public job ads before publication,  
so that quality and governance standards are enforced.

#### Acceptance Criteria
- local units can submit jobs for review
- central role can approve or reject
- publish is blocked until approval exists

## Feature 5.3 – ProcessTemplate
### Story 5.3.1
As Central HR Career Department,  
I want standard recruiting process templates,  
so that minimum process quality and comparability are ensured.

#### Acceptance Criteria
- ProcessTemplate exists
- mandatory stage keys exist
- local process variants can reference the template

---

# 8. EPIC 6 – Local Recruiting Operations

## Feature 6.1 – Local Job Drafting
### Story 6.1.1
As a local department or site,  
I want to create job drafts within approved templates,  
so that I can describe local vacancies while still following central standards.

#### Acceptance Criteria
- local role can create draft
- local role cannot bypass required fields
- local role cannot publish directly

## Feature 6.2 – Local Suitability Review
### Story 6.2.1
As a local hiring reviewer,  
I want to assess applicants only for my relevant jobs,  
so that local suitability decisions remain within my operational scope.

#### Acceptance Criteria
- reviewer sees only assigned applicants/jobs
- reviewer can record structured stage decisions
- reviewer cannot access unrelated applicants

## Feature 6.3 – Local Invitation Handling
### Story 6.3.1
As a local interview coordinator,  
I want to update invitation or interview stages,  
so that local process progress is reflected in a structured way.

#### Acceptance Criteria
- authorized role can update allowed decision stages
- stage update is logged
- stage update fails if role/context is invalid

## Feature 6.4 – Local Process Variants
### Story 6.4.1
As the platform,  
I must allow only controlled local recruiting variants,  
so that local differences can exist without breaking central minimum process standards.

#### Acceptance Criteria
- LocalProcessVariant entity exists
- central approval is required for productive use
- central mandatory stages cannot be removed

---

# 9. EPIC 7 – Privacy, Retention and Applicant Access Control

## Feature 7.1 – PrivacyNoticeVersion
### Story 7.1.1
As the platform,  
I must show and store the correct privacy notice version for public forms,  
so that applicant-facing privacy communication is traceable.

#### Acceptance Criteria
- form cannot be public without privacy notice linkage
- submission stores privacy notice version
- active notice version can be retrieved publicly

## Feature 7.2 – Retention Policies
### Story 7.2.1
As the platform,  
I must apply retention rules to applicant-related data,  
so that applicant data is not stored indefinitely.

#### Acceptance Criteria
- retention policies exist
- trigger events exist
- deletion/anonymisation/restrict actions can be executed
- applicant-related data does not remain without policy path

## Feature 7.3 – Applicant Access Assignment
### Story 7.3.1
As the platform,  
I must grant applicant access through explicit access assignments,  
so that need-to-know principles are enforced.

#### Acceptance Criteria
- ApplicantAccessAssignment exists
- access is context-bound
- access can expire
- applicant reads are role-/context-checked

---

# 10. EPIC 8 – Security, Authentication and Certificates

## Feature 8.1 – TLS and Certificates
### Story 8.1.1
As the platform,  
I must protect all public and internal endpoints with secure transport,  
so that data in transit is protected.

#### Acceptance Criteria
- HTTPS only
- valid certificates
- deprecated TLS versions disabled
- certificate monitoring exists

## Feature 8.2 – MFA for Privileged Roles
### Story 8.2.1
As a privileged internal user,  
I must authenticate with MFA,  
so that privileged access has stronger protection.

#### Acceptance Criteria
- MFA required for privileged roles
- privileged endpoint access blocked without required auth level

## Feature 8.3 – mTLS for Privileged Service Calls
### Story 8.3.1
As the platform,  
I must support mTLS for privileged service-to-service communication where required,  
so that highly privileged internal APIs are strongly protected.

#### Acceptance Criteria
- mTLS-required endpoints reject missing/invalid client certs
- certificate identity is validated
- failures are logged

## Feature 8.4 – Object-Level Authorization
### Story 8.4.1
As the platform,  
I must enforce object-level authorization on all protected object-based APIs,  
so that users cannot access objects outside their allowed scope.

#### Acceptance Criteria
- BOLA-like access attempts fail
- unrelated object access is blocked
- access violations are logged

---

# 11. EPIC 9 – Accessibility and SEO

## Feature 9.1 – Accessibility Baseline
### Story 9.1.1
As a user,  
I want public pages and forms to be accessible,  
so that I can use the platform regardless of assistive or non-mouse interaction needs.

#### Acceptance Criteria
- keyboard navigation works on core pages/forms
- labels and errors are understandable
- headings are semantic
- no critical accessibility blocker on MVP paths

## Feature 9.2 – SEO Baseline
### Story 9.2.1
As the organisation,  
I want public jobs and career pages to be discoverable,  
so that relevant opportunities can be found through search engines.

#### Acceptance Criteria
- SEO metadata exists
- canonical handling exists
- job detail pages can expose structured job data
- target URLs are stable and meaningful

---

# 12. EPIC 10 – Content Migration and Rollout

## Feature 10.1 – Content Inventory
### Story 10.1.1
As the migration team,  
I want all current Enterprise career content to be inventoried and classified,  
so that nothing important is migrated blindly or lost.

#### Acceptance Criteria
- inventory exists
- source pages mapped to target domains/types
- ownership and action type assigned

## Feature 10.2 – Structured Migration
### Story 10.2.1
As the migration team,  
I want current content to be transformed into target page types and structured objects,  
so that the new platform follows the new model and not the old HTML structure.

#### Acceptance Criteria
- jobs mapped to JobPosting
- career path pages mapped correctly
- contact entries normalized
- privacy/service pages reviewed

## Feature 10.3 – Redirect and Go-Live Preparation
### Story 10.3.1
As the rollout team,  
I want final content validation and redirect readiness,  
so that the transition to the new platform is controlled.

#### Acceptance Criteria
- target URLs defined
- old/new mapping exists
- final QA passed
- no unresolved critical migration blocker remains

---

# 13. EPIC 11 – Analytics, Auditability and Reporting

## Feature 11.1 – Analytics Events
### Story 11.1.1
As the organisation,  
I want key public and process events tracked,  
so that we can understand usage and optimise the platform.

#### Acceptance Criteria
- page_view tracked
- job_view tracked
- filter_use tracked
- form_start tracked
- form_submit tracked
- contact_click tracked

## Feature 11.2 – Audit Logging
### Story 11.2.1
As the organisation,  
I want critical governance and access actions audit logged,  
so that approvals, applicant access and compliance-sensitive changes are traceable.

#### Acceptance Criteria
- applicant access reads are logged
- approval actions are logged
- privacy/retention changes are logged
- workflow-sensitive actions are logged

---

# 14. Story Priorisation Recommendation

## MVP Must-Have
- EPIC 1 core pages
- EPIC 2 structured jobs
- EPIC 3 selected CareerPaths / JobFamilies
- EPIC 4 initiative application
- EPIC 5 central governance
- EPIC 6 local recruiting basics
- EPIC 7 privacy/retention/access basics
- EPIC 8 auth/authz/TLS basics
- EPIC 9 accessibility/SEO basics
- EPIC 10 migration wave 1
- EPIC 11 core analytics/audit

## Later Wave
- extended landing pages
- broader facility/location page model
- deeper local variants
- advanced analytics
- non-MVP integrations

---

# 15. Hard Story Rules

1. No story is done if it works functionally but fails privacy/security controls.
2. No story involving applicant data is done without context-based access checks.
3. No publication-related story is done without central approval enforcement.
4. No public form story is done without privacy notice and retention linkage.
5. No content migration story is done if the target type and owner are unclear.
6. No internal privileged story is done without authentication and auditability.

---

# 16. Final Rule

These Epics and Stories are Enterprise-specific implementation backlog framing.  
They are not a generic recruiting software backlog and must always remain aligned with:
- the Enterprise operating model,
- the Final Source of Truth,
- and the mandatory privacy/security/governance controls.