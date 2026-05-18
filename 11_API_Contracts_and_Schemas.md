# 11_API_Contracts_and_Schemas.md

## Dokumentstatus
- Version: 1.0
- Zweck: API-Schnittstellenverträge und Boundaries
- Basis: Abgeleitet aus System-Architekturvorgaben und Zielmodell

## 1. API Boundaries & Schutzklassen

### 1.1 Public APIs (Read-Only / Submission)
- Frei im Netz verfügbar, aber durch Rate-Limiting und CORS geschützt.
- **Endpoints**:
  - `GET /api/v1/public/jobs` - Job-Listen (nur Jobs mit Status `published`).
  - `GET /api/v1/public/jobs/{id}` - Job-Detaildaten.
  - `GET /api/v1/public/taxonomy/locations` - Orte für Filter.
  - `GET /api/v1/public/taxonomy/job-families` - Berufsfelder für Filter.
  - `POST /api/v1/public/applications` - Einreichen einer Bewerbung.
- **Harte Regel**: Submission erfordert Übermittlung einer validen `privacy_notice_version_id`.

### 1.2 Internal Governance APIs (Protected)
- Zwingend Authentifizierung (JWT/Session). Erlaubt nur für `CentralHRCareerAdmin` etc.
- **Endpoints**:
  - `POST /api/v1/admin/jobs/{id}/approve` - Setzt Freigabestatus.
  - `POST /api/v1/admin/templates/jobs` - Pflege der JobTemplates.

### 1.3 Internal Recruiting APIs (Protected)
- Authentifizierung + Local Context (Facility-bezogen).
- **Endpoints**:
  - `POST /api/v1/recruiting/jobs` - Anlage eines Entwurfs.
  - `PATCH /api/v1/recruiting/jobs/{id}` - Pflege von lokalen Jobdaten.
- **Harte Regel**: LocalEditor darf nur Jobs patchen, die zu seiner Facility gehören.

### 1.4 Sensitive Applicant APIs (Protected + BOLA Guard)
- MFA-geschützt. Zwingende Object-Level Authorization pro Request.
- **Endpoints**:
  - `GET /api/v1/recruiting/applications/{id}` - Abruf Bewerberdaten.
- **Harte Regel**: Request wird abgelehnt (403), wenn für diesen User und diese Application ID kein aktives `ApplicantAccessAssignment` existiert.

## 2. Standardisierte HTTP-Responses
- **200 OK / 201 Created**: Erfolg.
- **400 Bad Request**: Scheitern der Schema-Validierung (fehlende Felder, falsche Datentypen).
- **401 Unauthorized**: Nicht authentifiziert (Token fehlt/ungültig).
- **403 Forbidden**: Authentifiziert, aber Autorisierung (BOLA / RBAC) verweigert Zugriff auf das spezifische Objekt.
- **404 Not Found**: Objekt nicht existent oder aus Sicherheitsgründen maskiert (statt 403, um IDs nicht preiszugeben).
