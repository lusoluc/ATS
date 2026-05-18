# 09_Roles_Permissions_Workflows.md

## Dokumentstatus
- Version: 1.0
- Zweck: Verbindliches Rollen-, Berechtigungs- und Workflow-Modell
- Basis: Abgeleitet aus `00_FINAL_SOURCE_OF_TRUTH.md`

## 1. Rollenmodell

### 1.1 Zentrale Governance (Privilegiert)
- **GlobalAdmin**: Technische Systemverwaltung und Infrastruktur. (MFA-Pflicht)
- **CMSOwner**: Globale Content-Hoheit für redaktionelle Inhalte.
- **CentralHRCareerAdmin**: Globale HR-Hoheit, Template-Pflege, zentrale Steuerung, *finale Job-Freigaben*. (MFA-Pflicht)

### 1.2 Spezialisierte QA & Compliance
- **SEOQAReviewer**: Prüfung von SEO-Metadaten und URLs.
- **PrivacyComplianceReviewer**: Verwaltung der `PrivacyNoticeVersion` und der `DataRetentionPolicy`.
- **Publisher**: Darf fachlich freigegebene Inhalte (`approved`) technisch in `published` überführen.
- **Analyst**: Zugriff auf aggregierte Daten (kein Zugriff auf operative Bewerber-PII ohne Sonderrecht).

### 1.3 Lokale Operationen (Recruiting)
- **LocalEditor**: Erstellt `JobDrafts` basierend auf Templates für eigene Facilities/Locations.
- **LocalHiringReviewer**: Sichtet Bewerberunterlagen im Rahmen des `ApplicantAccessAssignment` (striktes Need-to-Know). (MFA-Pflicht)
- **LocalInterviewCoordinator**: Koordiniert lokale Termine und operative Recruiting-Schritte der Prozess-Templates.
- **JobEditor**: Globale oder standortübergreifende Unterstützung bei der Stellenerstellung.

## 2. Workflow-Modell

### 2.1 Standard Workflow-States (Jobs & Pages)
1. `draft`: Lokaler Entwurf, noch nicht bereit zur Freigabe.
2. `in_review`: Von lokalem Editor zur zentralen Prüfung eingereicht. (Lokal read-only).
3. `approved`: Von `CentralHRCareerAdmin` fachlich geprüft und freigegeben.
4. `published`: Veröffentlicht und in den Public APIs ausspielbar.
5. `archived`: Zurückgezogen, offline, aber als Historie erhalten.
6. `rejected`: Von `CentralHRCareerAdmin` im Review-Schritt abgelehnt (geht zurück an LocalEditor).

### 2.2 Harte Workflow-Regeln
- **Kein Bypass**: Niemand darf einen Job direkt von `draft` auf `published` setzen (Trennung von Editor und Approver).
- **Review Zwang**: Nur der `CentralHRCareerAdmin` darf Jobs von `in_review` nach `approved` schieben.
- **Retention Auslöser**: Ein Bewerber-Status auf `Archived/Rejected` löst den Timer für die asynchrone Lösch-Routine der `DataRetentionPolicy` aus.
