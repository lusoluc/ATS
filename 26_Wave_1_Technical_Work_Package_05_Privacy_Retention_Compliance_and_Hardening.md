# 26_Wave_1_Technical_Work_Package_05_Privacy_Retention_Compliance_and_Hardening.md# 26_Wave_1_Technical_Work_Package_05_Privacy_Retention[5](https://pages.nist.gov/800-63-4/sp800-63b.html)[3](https://gdpr-info.eu/art-5-gdpr/)[14](https://eur-lex.europa.eu/eli/reg/2018/1725/oj/eng)[4](https://gdpr-info.eu/art-6-gdpr/)

## Ziel E – Release Readiness for Applicant-Sensitive Processing
Vor applicant-sensitiver produktiver Nutzung müssen Privacy, Security, Logging und Retention so weit belastbar sein, dass keine kritische Go-Live-Lücke mehr offen bleibt. [5](https://pages.nist.gov/800-63-4/sp800-63b.html)[15](https://pages.nist.gov/800-63-3/sp800-63b.html)[16](https://csrc.nist.gov/pubs/sp/800/63/b/upd2/final)

---

# 6. Verbindliche Deliverables

## 6.1 Deliverable 1 – Privacy Notice Lifecycle Pack
Enthält:
- aktive/notwendige PrivacyNoticeVersion-Regeln
- Aktivierungs-/Ablöseregeln
- Zuordnungsvalidierung zu Forms/Flows
- applicant-facing consistency validation
- notice-version traceability baseline

## 6.2 Deliverable 2 – Retention and Deletion Pack
Enthält:
- trigger mapping
- retention timer baseline
- delete/anonymise/restrict baseline
- handling matrix for rejection / withdrawal / hire / consent-expiry
- no-indefinite-storage enforcement note

## 6.3 Deliverable 3 – Compliance Hardening Pack
Enthält:
- need-to-know confirmation logic
- access-scope hardening notes
- export restriction baseline
- cross-site visibility prohibition confirmation
- compliance audit completeness checklist

## 6.4 Deliverable 4 – Security Hardening Pack
Enthält:
- TLS hardening confirmation
- certificate handling readiness note
- MFA enforcement confirmation for privileged roles
- mTLS verification note for selected endpoints/services
- secret/key management readiness note
- denied-access and misconfiguration protections

## 6.5 Deliverable 5 – Wave-1 Applicant-Sensitive Release Readiness Pack
Enthält:
- final blocker review for applicant-sensitive scope
- open risk list
- go/no-go candidate view
- required remediation list before release if any

## 6.6 Deliverable 6 – Technical Risk / Gap List
Enthält:
- unresolved privacy gaps
- unresolved retention gaps
- unresolved certificate/auth hardening gaps
- blocker list before Wave-1 release or next work package

---

# 7. Konkrete Arbeitsaufgaben

## Task 1 – Harden PrivacyNoticeVersion Lifecycle
### Beschreibung
Stelle sicher, dass PrivacyNoticeVersion nicht nur existiert, sondern kontrolliert im Lebenszyklus verwaltet wird.

### Muss prüfen
- nur aktive Notice-Versionen dürfen neu zugewiesen werden
- Form-/Submission-Logik muss auf gültige Notice-Version prüfen
- ersetzte / alte Notice-Versionen müssen historisch nachvollziehbar bleiben
- applicant-facing notice retrieval muss mit interner Zuordnung konsistent sein

### Output
- notice lifecycle rules
- active/inactive behavior summary
- invalid assignment handling
- traceability confirmation

---

## Task 2 – Realise Retention Trigger Resolution
### Beschreibung
Definiere und realisiere die Baseline, wie Retention-Trigger technisch ermittelt werden.

### Mindesttrigger
- rejection
- withdrawal
- process_end
- hire
- consent_expiry

### Muss sicherstellen
- unterschiedliche Trigger können unterschiedlich behandelt werden
- Trigger führen nicht implizit zu unendlicher Speicherung
- Trigger können mit DataRetentionPolicy verbunden werden

### Output
- trigger resolution matrix
- trigger-to-policy baseline
- edge case list

---

## Task 3 – Realise Retention Action Baseline
### Beschreibung
Definiere und realisiere die Baseline für:
- delete
- anonymise
- restrict

### Muss prüfen
- welche applicant-related object types betroffen sind
- welche Aktion je Trigger / Policy zulässig ist
- wie dry-run / preview geprüft werden kann
- wie Auditierung erfolgt

### Output
- retention action baseline
- object-type handling matrix
- audit log mapping for retention actions

Datenschutzgrundsätze verlangen Speicherbegrenzung und zweckbezogene Verarbeitung; Leitfäden zu Bewerberdaten betonen, dass Bewerbungsdaten nicht unbegrenzt gespeichert werden dürfen. [6](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)[1](https://zuplo.com/learning-center/owasp-cheat-sheet-guide)[10](https://developer.uspto.gov/ptab-api/documents/170995518/download)

---

## Task 4 – Validate Applicant Processing Scope Hardening
### Beschreibung
Prüfe und härte die ApplicantAccessAssignment- und internen Applicant-View-Regeln gegen Fehlkonfigurationen.

### Muss prüfen
- keine broad visibility by default
- keine lokalen Rollen mit globalem Einsichtsrecht
- keine Analysten-/Reviewer-Rolle mit unnötiger Datenfülle
- access expiry / revocation funktioniert
- denied access attempts werden erkannt und geloggt

### Output
- applicant processing hardening summary
- misconfiguration scenarios
- protected response shaping confirmation

---

## Task 5 – Confirm No-Uncontrolled-Export and No-Uncontrolled-Sharing Baseline
### Beschreibung
Sicherstellen, dass in Wave 1 keine unkontrollierte Export- oder Sharing-Logik für applicant-sensitive Daten entsteht.

### Muss prüfen
- keine offenen Bulk-Export-Routen
- kein unkontrolliertes Cross-Site-Sharing
- keine stillen Weitergaben außerhalb definierter Rollen-/Kontextgrenzen
- keine öffentliche oder halböffentliche Ableitbarkeit sensitiver Daten

### Output
- export/sharing restriction baseline
- denied scenario list
- control note for later waves

---

## Task 6 – Harden TLS / Certificate / MFA / mTLS Readiness
### Beschreibung
Überprüfe und härte die Wave-1-Sicherheitsbasis für applicant-sensitive und privilegierte Funktionen.

### Muss prüfen
- HTTPS-only exposure
- TLS baseline confirmed
- certificate validity / ownership / renewal visibility
- MFA required for privileged roles
- mTLS enforced where marked mandatory
- no fallback to weaker service access for privileged APIs
- no secrets in code/config that violate readiness

OWASP recommends strong TLS configuration with TLS 1.3 by default and HTTPS-only services, while RFC 8705 provides the basis for mTLS-bound client authentication for privileged machine interactions. [4](https://gdpr-info.eu/art-6-gdpr/)[3](https://gdpr-info.eu/art-5-gdpr/)[14](https://eur-lex.europa.eu/eli/reg/2018/1725/oj/eng)

### Output
- security hardening confirmation
- remaining certificate/auth blockers
- privileged-endpoint hardening note

---

## Task 7 – Confirm Compliance-Sensitive Audit Completeness
### Beschreibung
Prüfe, ob alle compliance-sensitiven Aktionen in Wave 1 auditierbar sind.

### Mindestkandidaten
- restricted applicant read
- denied access attempt
- access assignment create/update/remove
- stage update
- approval/rejection actions
- privacy notice changes
- retention action execution
- auth failure / mTLS failure where relevant

NIST logging guidance emphasizes that logs are essential for security investigation and remediation, and applicant-sensitive operations need traceable audit events. [15](https://pages.nist.gov/800-63-3/sp800-63b.html)[16](https://csrc.nist.gov/pubs/sp/800/63/b/upd2/final)

### Output
- audit completeness checklist
- missing event list
- blocker list for release readiness

---

## Task 8 – Execute Wave-1 Applicant-Sensitive Release Readiness Review
### Beschreibung
Führe einen spezifischen Readiness-Review für applicant-sensitive Wave-1-Funktionen durch.

### Muss prüfen
- forms
- privacy notices
- retention triggers
- access assignments
- internal applicant views
- privileged auth
- protected transport
- logging/audit
- no-go blocker set

### Output
- release readiness summary
- go/no-go candidate statement
- remediation list if required

---

# 8. Acceptance Criteria for This Work Package

Dieses Arbeitspaket ist erfolgreich abgeschlossen, wenn:

## 8.1 Privacy
- PrivacyNoticeVersion-Lifecycle ist belastbar
- Forms/Flows nutzen nur gültige Notice-Versionen
- notice traceability ist sichergestellt

## 8.2 Retention
- Trigger-Matrix ist definiert
- retention actions sind als Baseline definiert
- keine unbefristete Speicherung bleibt unadressiert
- rejection/withdrawal/hire/consent-expiry werden differenziert behandelt

## 8.3 Compliance
- applicant-sensitive Sichtbarkeit ist gegen Fehlkonfiguration gehärtet
- uncontrolled export/sharing ist ausgeschlossen
- need-to-know remains enforced

## 8.4 Security
- TLS/certificate baseline ist bestätigt
- MFA baseline für privilegierte Rollen ist bestätigt
- mTLS-markierte Pfade sind überprüft
- keine kritische Secret-/Key-/Transport-Lücke bleibt ungeklärt

## 8.5 Release Readiness
- applicant-sensitive Wave-1-Funktionen haben keinen kritischen Go-Live-Blocker mehr
- offene Punkte sind dokumentiert und bewertbar

---

# 9. Pflicht-Tests / Validierungen

## 9.1 Privacy Notice Tests
- form with valid notice works
- form with invalid/inactive notice is blocked
- submission stores notice version traceably
- public notice retrieval matches active assigned version

## 9.2 Retention Tests
- rejection trigger resolved correctly
- withdrawal trigger resolved correctly
- consent-expiry path behaves correctly where configured
- retention action dry-run / preview behaves as expected
- undefined retention paths are surfaced as error/blocker

## 9.3 Access / Compliance Tests
- no cross-site broad visibility
- no applicant export route without explicit approval
- expired assignments no longer grant access
- denied access is logged
- field exposure remains minimized

## 9.4 Security Hardening Tests
- protected endpoints HTTPS-only
- deprecated TLS versions disabled
- privileged role MFA enforcement works
- mTLS-required endpoint rejects missing/invalid client certificate
- no privileged endpoint is reachable with downgraded auth path

## 9.5 Audit Completeness Tests
- restricted read logged
- stage update logged
- access assignment change logged
- retention execution logged
- failed privileged access attempt logged

---

# 10. No-Go Conditions for This Work Package

Dieses Arbeitspaket ist **nicht freigabefähig**, wenn:

1. öffentliche Formulare ohne gültige PrivacyNoticeVersion verwendbar bleiben
2. applicant-related data keine definierte RetentionPolicy/Trigger-Logik besitzt
3. unbefristete Speicherung applicant-sensitive Daten implizit bestehen bleibt
4. cross-site oder broad applicant visibility weiterhin möglich ist
5. kontrolllose Export-/Sharing-Pfade bestehen
6. privilegierte Rollen keine MFA-Basis haben
7. TLS-/certificate-Basis unzureichend ist
8. mTLS-markierte privilegierte Pfade ungesichert bleiben
9. compliance-sensitive Audit Events fehlen
10. applicant-sensitive Wave-1-Funktionen trotz kritischer Privacy-/Security-Lücke release-ready erklärt würden

---

# 11. Verpflichtende Antwortstruktur des Senior Developer Agent

Der Senior Developer Agent muss auf dieses Arbeitspaket mit genau dieser Struktur antworten:

## Section 1 – Read Confirmation
- gelesene bindende Dokumente
- bestätigte Relevanz für WP05

## Section 2 – Privacy Notice Hardening Plan
- lifecycle handling
- activation/invalidation rules
- traceability rules
- invalid-assignment handling

## Section 3 – Retention and Deletion Plan
- trigger matrix
- policy linkage
- delete/anonymise/restrict baseline
- edge cases and blocker scenarios

## Section 4 – Compliance Hardening Plan
- applicant visibility hardening
- no-export / no-sharing controls
- access misconfiguration protections
- compliance-sensitive audit plan

## Section 5 – Security Hardening Plan
- TLS/certificate checks
- MFA scope confirmation
- mTLS verification targets
- secret/key readiness
- remaining hardening gaps

## Section 6 – Applicant-Sensitive Release Readiness Review
- current readiness status
- critical blockers
- remediation list
- go/no-go recommendation

## Section 7 – Proposed Next Work Package Readiness
- readiness for WP06 or release-prep package
- missing prerequisites
- recommended next implementation focus

---

# 12. Empfohlener nächster Schritt nach diesem Arbeitspaket

Nach erfolgreichem Abschluss dieses Arbeitspakets soll direkt folgen:

## `27_Wave_1_Technical_Work_Package_06_Migration_Completion_Readiness_and_Final_Wave_1_Release_Preparation.md`

Fokus:
- final content migration completion for Wave 1
- final ownership and publishing readiness
- final accessibility / SEO checks
- final operational runbook/readiness
- final release gate pass for Wave 1

---

# 13. Finale Regel

Dieses Arbeitspaket ist nur dann erfolgreich, wenn der Senior Developer Agent:
- Privacy, Retention und Compliance nicht nur formal referenziert, sondern technisch belastbar macht,
- Security Hardening für applicant-sensitive und privilegierte Funktionen nachvollziehbar absichert,
- und keine kritische Release-Lücke für den Wave-1-Einsatz offen lässt.

## Dokumentstatus
- Version: 1.0
- Zweck: Fünftes konkretes technisches Arbeitspaket für Wave 1
- Fokus: Privacy, Retention, Compliance and Hardening
- Zielgruppe:
  - Senior Developer Agent
  - Security Architect
  - Privacy / Compliance Reviewer
  - Enterprise Architect
  - Technical Lead
  - Delivery Lead
- Gültigkeit: Landesverein-spezifisch, benchmark-frei, Wave-1-Hardening-orientiert
- Regel: Wenn dieses Arbeitspaket dem Final Source of Truth widerspricht, gilt immer der Final Source of Truth

---

# 1. Ziel dieses Arbeitspakets

Dieses Arbeitspaket stellt sicher, dass die in Wave 1 realisierten öffentlichen und internen Recruiting-Funktionen nicht nur funktional arbeiten, sondern auch:
- datenschutzkonform,
- sicherheitstechnisch belastbar,
- auditierbar,
- und für applicant-sensitive Verarbeitung freigabefähig sind.

Es soll die Plattform auf den Punkt bringen, an dem:
1. PrivacyNoticeVersion nicht nur verknüpft, sondern kontrolliert lebenszyklusfähig ist,
2. Retention-/Deletion-Logik technisch belastbar wird,
3. applicant-sensitive Prozesse gegen Fehlkonfigurationen abgesichert werden,
4. MFA/TLS/mTLS/certificate-handling produktionsnah gehärtet werden,
5. und finale Wave-1-Go/No-Go-Kontrollen für applicant-sensitive Verarbeitung vorbereitet werden. [1](https://zuplo.com/learning-center/owasp-cheat-sheet-guide)[2](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)[5](https://pages.nist.gov/800-63-4/sp800-63b.html)[4](https://gdpr-info.eu/art-6-gdpr/)

---

# 2. Warum dieses Arbeitspaket jetzt kommt

Nach den bisherigen Arbeitspaketen existieren:
- öffentliche Karriere- und Jobpfade,
- zentrale Freigabe- und Governance-Pfade,
- lokale Recruiting-Zugriffe,
- applicant-sensitive interne Ansichten,
- und erste Privacy-/Security-Bausteine.

Jetzt muss sichergestellt werden, dass diese Funktionen nicht nur „laufen“, sondern auch regulatorisch und sicherheitstechnisch belastbar sind. Das ist besonders wichtig, weil:
- die aktuelle Landesverein-Bewerbungslogik bereits explizit auf Datenschutz und Löschung nach sechs Monaten hinweist, sofern keine andere zulässige Grundlage vorliegt, 
- Bewerberdaten nach Datenschutzgrundsätzen zweckgebunden, minimiert, sicher und zeitlich begrenzt verarbeitet werden müssen, [6](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)[7](https://www.ietf.org/rfc/rfc8705.pdf)
- und geschützte APIs / applicant-sensitive Funktionen von Anfang an mit korrekter Zugriffskontrolle, Transport Security, Logging und Hardening abgesichert sein müssen. [3](https://gdpr-info.eu/art-5-gdpr/)[4](https://gdpr-info.eu/art-6-gdpr/)[8](https://datenschutz-hamburg.de/fileadmin/user_upload/HmbBfDI/Datenschutz/Informationen/240611_Information_Applicant_Data_Protection_and_Recruiting_EN.pdf)

---

# 3. Scope dieses Arbeitspakets

## 3.1 In Scope

### 3.1.1 Privacy Notice Hardening
- PrivacyNoticeVersion lifecycle baseline
- activation / replacement rules
- linkage validation hardening
- applicant-facing consistency checks
- stored notice-version traceability hardening

### 3.1.2 Retention / Deletion Baseline Realisation
- retention trigger resolution
- retention countdown baseline
- delete / anonymise / restrict action baseline
- rejection / withdrawal / hire / consent-expiry distinction
- no-indefinite-storage enforcement baseline

### 3.1.3 Applicant-Processing Compliance Hardening
- need-to-know applicant access confirmation
- access-scope misconfiguration hardening
- no-uncontrolled-export baseline
- no-cross-site-broad-sharing baseline
- compliance-sensitive audit completeness checks

### 3.1.4 Security Hardening Baseline
- TLS configuration hardening verification
- certificate handling hardening baseline
- MFA baseline verification for privileged roles
- mTLS enforcement verification for selected privileged service calls
- endpoint protection hardening review
- secret/key handling readiness confirmation

### 3.1.5 Wave-1 Release Safety Checks for Applicant-Sensitive Operations
- pre-release privacy readiness validation
- pre-release certificate/auth readiness validation
- final no-go blocker review for applicant-sensitive scope
- alignment with Implementation Control Checklist and Test/Quality Gates

---

## 3.2 Out of Scope
Dieses Arbeitspaket enthält noch nicht:
- vollständige Talent-Pool-Funktion in voller Breite
- tiefgehende Drittlandtransfer-/Subprocessor-Steuerung jenseits des Wave-1-Kerns
- umfassende Notification-/Campaign-Compliance-Logik
- vollständige Records-of-Processing / organisational legal documentation außerhalb der Systemfunktionen
- future-wave integrations beyond current Wave-1 system boundaries

---

# 4. Verbindliche Inputs

Der Senior Developer Agent muss dieses Arbeitspaket auf Basis der folgenden Dokumente ausführen:

1. `00_FINAL_SOURCE_OF_TRUTH.md`
2. `09_Roles_Permissions_Workflows.md`
3. `11_API_Contracts_and_Schemas.md`
4. `12_Test_and_Quality_Gates.md`
5. `14_Security_Architecture_and_Certificate_Guide.md`
6. `15_Implementation_Control_Checklist.md`
7. `21_Wave_1_Implementation_Package.md`
8. `22_Wave_1_Technical_Work_Package_01_Core_Model_and_Auth.md`
9. `23_Wave_1_Technical_Work_Package_02_API_and_Workflow_Foundation.md`
10. `24_Wave_1_Technical_Work_Package_03_Public_Experience_and_Job_Governance_Realization.md`
11. `25_Wave_1_Technical_Work_Package_04_Local_Recruiting_Operations_and_Applicant_Access_Realization.md`

---

# 5. Verbindliche Ziele

## Ziel A – Privacy Notice Lifecycle Control
Die Plattform muss sicherstellen, dass applicant-facing Formulare und Flows immer mit einer gültigen PrivacyNoticeVersion arbeiten und dass diese Zuordnung nachvollziehbar bleibt. Informationspflichten im Bewerbungsverfahren müssen sichtbar und zuordenbar unterstützt werden. [1](https://zuplo.com/learning-center/owasp-cheat-sheet-guide)[9](https://apisecurity.io/owasp-api-security-top-10/)

## Ziel B – Retention / Deletion Enforcement Baseline
Die Plattform muss eine belastbare Baseline dafür schaffen, dass Bewerberdaten nicht unbefristet gespeichert bleiben und dass Trigger wie Ablehnung, Rückzug, Verfahrensende, Einstellung oder Einwilligungsablauf technisch differenziert behandelt werden. In Deutschland wird häufig eine Aufbewahrung von bis zu sechs Monaten nach Verfahrensende zur Verteidigung gegen mögliche AGG-Ansprüche beschrieben; darüber hinausgehende Speicherung braucht regelmäßig eine separate Grundlage. [10](https://developer.uspto.gov/ptab-api/documents/170995518/download)[11](https://auth0.com/docs/get-started/authentication-and-authorization-flow/authenticate-with-mtls)[12](https://dev.to/kanywst/rfc-8705-deep-dive-turning-access-tokens-into-unstealable-tokens-with-mtls-406)

## Ziel C – Applicant Processing Compliance Hardening
Die Plattform muss sicherstellen, dass applicant-sensitive Verarbeitung nicht durch zu breite Sichtbarkeit, fehlerhafte Assignments oder unzureichende Auditierung entgleist. Zugriff auf Bewerberdaten ist auf die am Verfahren Beteiligten zu begrenzen. [1](https://zuplo.com/learning-center/owasp-cheat-sheet-guide)[13](https://www.akamai.com/site/en/documents/brief/2023/owasp-api-top-10.pdf)

## Ziel D – Security Hardening for Wave 1
Die Plattform muss die Security-Basis für applicant-sensitive und privilegierte Bereiche final härten:
- HTTPS/TLS-only,
- privilegierte Rollen mit MFA,
- mTLS auf vorgesehenen privilegierten Service-Pfaden,
- Secret-/Certificate-Lifecycle,
