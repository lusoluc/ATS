# 12_Test_and_Quality_Gates.md

## Dokumentstatus
- Version: 1.0
- Zweck: Test-Richtlinien und Quality Gates für alle Work Packages
- Basis: Abgeleitet aus Governance-Vorgaben und Compliance-Rules

## 1. Test-Strategie (Mindestumfang)

### 1.1 Unit- & Business-Logik Tests
- **State-Maschine**: Alle verbotenen Workflow-Übergänge (z.B. `draft` -> `published`) müssen durch Unit-Tests abgewiesen werden.
- **Referenz-Integrität**: Anlage eines `JobPosting` ohne `Facility` oder `Location` muss im Modell-Layer fehlschlagen.

### 1.2 Security & Integration Tests
- **BOLA Tests (Broken Object Level Authorization)**: Es muss ein automatisierter Testfall existieren, bei dem `LocalHiringReviewer A` versucht, die Application-ID von `LocalHiringReviewer B` (aus einer anderen Facility) per GET-Request abzufragen. Ergebnis MUSS 403/404 sein.
- **API Visibility**: Public API Jobs Endpoint darf unter keinen Umständen Jobs mit Status `draft`, `in_review` oder `archived` ausliefern.

### 1.3 Asynchrone Worker Tests (Privacy)
- **Retention Worker**: Ein Integration-Test muss bestätigen, dass der Background-Worker PII-Felder anonymisiert (oder löscht), wenn das `DataRetentionPolicy`-Limit für einen archivierten Bewerber überschritten ist.

## 2. Hard-Gates für Work Packages

Die Implementierung darf nicht voranschreiten, bevor diese Gates erfüllt sind:

### 2.1 Gate: Core Model Freeze (Ende WP01)
- DDL / ORM-Schemas für alle unter `08` genannten Entitäten sind fehlerfrei migrierbar (Migrations-Scripts existieren).
- BOLA-Skelett (Middleware/Guard) existiert.

### 2.2 Gate: API Contract Freeze (Ende WP02)
- Alle OpenAPI-Spezifikationen der unter `11` gelisteten API-Schnittstellen sind validiert. 
- UI-Code (WP03) darf erst nach diesem Gate beginnen.

### 2.3 Gate: SEO & Accessibility (Während WP03/04)
- Semantisches HTML (Headers) ist korrekt.
- Lighthouse / aXe-core Audits weisen keine kritischen WCAG 2.1 AA Verletzungen auf.

### 2.4 Gate: Release Readiness (WP06)
- Erfolgreicher Dry-Run der programmatischen ETL-Content-Migration.
- Audit-Logs erfassen nachweislich `login`, `job_approved` und `applicant_viewed`.
