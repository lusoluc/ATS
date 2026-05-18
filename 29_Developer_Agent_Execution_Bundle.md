# 29_Developer_Agent_Execution_Bundle.md

## Dokumentstatus
- Version: 1.0
- Zweck: Finales operatives Übergabedokument für den Senior Developer Agent
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, ausführungssteuernd
- Ziel: Einen einzigen, klaren, geordneten und kontrollierten Einstiegspunkt für die technische Umsetzung bereitstellen
- Regel: Dieses Dokument ist ein Ausführungs-Bundle. Fachlich-technisch bindend bleibt der Final Source of Truth.

---

# 1. Ziel dieses Dokuments

Dieses Dokument bündelt die operative Ausführungslogik für den Senior Developer Agent.

Es definiert:
- welche Dokumente bindend sind,
- in welcher Reihenfolge gearbeitet werden muss,
- welche Work Packages nacheinander auszuführen sind,
- welche Gates dabei erfüllt sein müssen,
- welche Stop-Regeln gelten,
- und wie Status, Risiken und Freigaben berichtet werden müssen.

Dieses Dokument ersetzt **nicht** die fachlichen Dokumente.  
Es ist das **operative Navigations- und Steuerungsdokument** für die Umsetzung.

---

# 2. Verbindliche Grundregel

## 2.1 Single Source of Truth
Die einzige fachlich-technische Wahrheit bleibt:

### `00_FINAL_SOURCE_OF_TRUTH.md`

Wenn irgendein anderes Dokument davon abweicht, gilt immer:
- `00_FINAL_SOURCE_OF_TRUTH.md`

## 2.2 Keine externen Produktannahmen
Es dürfen keine externen Recruiting-/ATS-/CMS-Produktlogiken in die Umsetzung eingeführt werden.

## 2.3 Keine stillen Annahmen
Wenn Informationen fehlen:
1. Lücke benennen
2. Risiko benennen
3. Entscheidungsvorlage formulieren
4. an kritischer Stelle stoppen

---

# 3. Bindende Dokumente für die Ausführung

Der Senior Developer Agent muss die folgenden Dokumente als bindend behandeln:

## 3.1 Primäre Steuerungsdokumente
1. `00_FINAL_SOURCE_OF_TRUTH.md`
2. `19_Senior_Developer_Agent_Handover_Prompt.md`
3. `29_Developer_Agent_Execution_Bundle.md`

## 3.2 Technische Kern- und Kontroll-Dokumente
4. `08_Entity_Data_Model.md`
5. `09_Roles_Permissions_Workflows.md`
6. `11_API_Contracts_and_Schemas.md`
7. `12_Test_and_Quality_Gates.md`
8. `14_Security_Architecture_and_Certificate_Guide.md`
9. `15_Implementation_Control_Checklist.md`

## 3.3 Delivery- und Scope-Dokumente
10. `16_Project_Delivery_Roadmap_and_Workstreams.md`
11. `17_Backlog_Epics_and_User_Stories.md`
12. `21_Wave_1_Implementation_Package.md`

## 3.4 Inhalts- und Rollout-Dokumente
13. `13_Content_Migration_and_Inventory.md`
14. `18_Master_Document_Index_and_Usage_Guide.md`

## 3.5 Wave-1-Work-Packages
15. `22_Wave_1_Technical_Work_Package_01_Core_Model_and_Auth.md`
16. `23_Wave_1_Technical_Work_Package_02_API_and_Workflow_Foundation.md`
17. `24_Wave_1_Technical_Work_Package_03_Public_Experience_and_Job_Governance_Realization.md`
18. `25_Wave_1_Technical_Work_Package_04_Local_Recruiting_Operations_and_Applicant_Access_Realization.md`
19. `26_Wave_1_Technical_Work_Package_05_Privacy_Retention_Compliance_and_Hardening.md`
20. `27_Wave_1_Technical_Work_Package_06_Migration_Completion_Readiness_and_Final_Wave_1_Release_Preparation.md`

---

# 4. Verbindliche Ausführungsreihenfolge

Die Umsetzung muss in genau dieser Reihenfolge erfolgen.

## Phase A – Verständnis und Bestätigung
### A1
Lies und bestätige:
- `00_FINAL_SOURCE_OF_TRUTH.md`
- `19_Senior_Developer_Agent_Handover_Prompt.md`
- `29_Developer_Agent_Execution_Bundle.md`

### A2
Lies und bestätige die technischen Kern-Dokumente:
- `08`
- `09`
- `11`
- `12`
- `14`
- `15`

### A3
Lies und bestätige die Delivery-/Wave-Dokumente:
- `16`
- `17`
- `21`
- `22`
- `23`
- `24`
- `25`
- `26`
- `27`

### Ergebnis von Phase A
Der Agent liefert eine **Initial Confirmation Response** mit:
1. gelesenen Dokumenten
2. bestätigten Kernmodellen
3. offenen kritischen Punkten
4. vorgeschlagener Umsetzungsreihenfolge
5. ersten Blockern / Risiken

Ohne diese Bestätigung darf keine produktionsnahe Umsetzung beginnen.

---

## Phase B – Work Package 01
### Dokument
`22_Wave_1_Technical_Work_Package_01_Core_Model_and_Auth.md`

### Fokus
- Entitäten
- Beziehungen
- Rollen / Permissions
- Workflow-State Skeleton
- AuthN/AuthZ Baseline
- TLS/MFA/mTLS Baseline
- Audit-Event Baseline

### Exit Condition
WP01 ist nur abgeschlossen, wenn:
- Core Model bestätigt ist
- Security boundary baseline bestätigt ist
- keine Kernmodellgrenze ungeklärt bleibt

---

## Phase C – Work Package 02
### Dokument
`23_Wave_1_Technical_Work_Package_02_API_and_Workflow_Foundation.md`

### Fokus
- API Group Segmentation
- Public/Internal/Sensitive API boundaries
- Workflow Action Endpoints
- Application Submission Baseline
- Audit Hook Baseline

### Exit Condition
WP02 ist nur abgeschlossen, wenn:
- Public/Internal API-Grenzen klar sind
- Workflow-Actions regelkonform definiert sind
- Privacy-linked public submission baseline steht
- Security/Audit Hooks definiert sind

---

## Phase D – Work Package 03
### Dokument
`24_Wave_1_Technical_Work_Package_03_Public_Experience_and_Job_Governance_Realization.md`

### Fokus
- Karriere-Startseite
- Arbeitgeberseite
- CareerPath-Seiten (Wave-1-Auswahl)
- Stellenliste
- Stellentdetailseite
- Initiativbewerbung / Bewerbungsweg-Basis
- zentraler Job-Governance-Pfad

### Exit Condition
WP03 ist nur abgeschlossen, wenn:
- Public Experience Kernpfade realisiert sind
- Job-Governance end-to-end realisiert ist
- kein Public Leakage oder Governance-Bypass möglich ist

---

## Phase E – Work Package 04
### Dokument
`25_Wave_1_Technical_Work_Package_04_Local_Recruiting_Operations_and_Applicant_Access_Realization.md`

### Fokus
- ApplicantAccessAssignment real
- lokale Bewerberlisten-/Detailansichten
- lokale Eignungsprüfung
- Einladungsvorstufe
- privacy-safe response shaping
- applicant read audit hooks

### Exit Condition
WP04 ist nur abgeschlossen, wenn:
- Need-to-know-Zugriff technisch erzwungen wird
- lokale Rollen nur den zulässigen Scope sehen
- keine broad visibility existiert
- lokale Recruiting-Aktionen governance-konform sind

---

## Phase F – Work Package 05
### Dokument
`26_Wave_1_Technical_Work_Package_05_Privacy_Retention_Compliance_and_Hardening.md`

### Fokus
- PrivacyNotice lifecycle hardening
- Retention trigger/action baseline
- compliance hardening
- no-export / no-sharing baseline
- TLS/certificate/MFA/mTLS hardening
- applicant-sensitive release readiness review

### Exit Condition
WP05 ist nur abgeschlossen, wenn:
- Privacy-/Retention-Logik belastbar ist
- keine kritische applicant-sensitive Privacy-/Security-Lücke bleibt
- Hardening-Baseline bestätigt ist

---

## Phase G – Work Package 06
### Dokument
`27_Wave_1_Technical_Work_Package_06_Migration_Completion_Readiness_and_Final_Wave_1_Release_Preparation.md`

### Fokus
- Wave-1-Content-Vollständigkeit
- Ownership- und Publish-Readiness
- Accessibility-/SEO-Finalisierung
- Release-Runbook
- Hypercare/Monitoring
- finaler Go/No-Go-Stand

### Exit Condition
WP06 ist nur abgeschlossen, wenn:
- Wave-1-Content vollständig und korrekt migriert ist
- keine kritische Release-Lücke offen bleibt
- finaler Go/No-Go-Stand belastbar vorliegt

---

# 5. Verbindliche Antwortstruktur pro Work Package

Für **jedes** Work Package muss der Senior Developer Agent genau diese Grundstruktur liefern:

## Section 1 – Read Confirmation
- gelesene bindende Dokumente
- bestätigte Relevanz

## Section 2 – Scope Confirmation
- was genau in diesem WP in Scope ist
- was out of scope ist

## Section 3 – Planned Deliverables
- konkrete Artefakte
- konkrete technische Ergebnisse

## Section 4 – Security / Privacy / Governance Controls
- relevante Controls
- relevante Hard Rules
- relevante negative Fälle

## Section 5 – Risks and Blockers
- offene Risiken
- Blocker
- fehlende Entscheidungen

## Section 6 – Gate Readiness
- welche Gates erfüllt werden müssen
- aktueller Status
- offene Lücken

## Section 7 – Next-Step Readiness
- readiness für nächstes WP
- fehlende Vorbedingungen
- empfohlener nächster Schritt

---

# 6. Harte Ausführungsregeln

## 6.1 Kein Überspringen von Work Packages
Es darf kein späteres Work Package begonnen werden, wenn das vorherige:
- nicht fachlich bestätigt,
- nicht sicherheitsseitig bestätigt,
- oder nicht gate-fähig abgeschlossen ist.

## 6.2 Kein UI vor stabiler Basis
Öffentliche oder interne produktionsnahe UI-Realisierung darf nur auf stabilen:
- Entitäten,
- APIs,
- Rollen,
- Workflows,
- Security-/Privacy-Baselines
aufsetzen.

## 6.3 Keine Security-/Privacy-/Governance-Verschiebung
Security, Privacy und Governance dürfen **nie** auf „später“ verschoben werden, wenn sie im betreffenden Work Package als Pflichtbestandteil definiert sind.

## 6.4 Keine lokalen Freiheiten außerhalb des Zielmodells
Lokale Recruiting-Akteure dürfen technisch nicht mehr Freiheit erhalten, als das Enterprise-Zielmodell erlaubt.

---

# 7. Harter Gate-Mechanismus

## 7.1 Pflicht-Gates
Jedes Work Package muss die relevanten Gates aus:
- `12_Test_and_Quality_Gates.md`
- `15_Implementation_Control_Checklist.md`
erfüllen.

## 7.2 No-Go-Prinzip
Ein Work Package gilt als **nicht abgeschlossen**, wenn:
- eine No-Go-Bedingung aus dem Work Package selbst offen ist,
- eine No-Go-Bedingung aus `12` offen ist,
- oder eine Pflichtkontrolle aus `15` offen ist.

---

# 8. Harte Stop-and-Escalate-Regeln

Der Agent muss sofort stoppen und eskalieren bei:

1. unklarer Trennung von Facility und Location
2. unklarer Trennung von JobFamily und CareerPath
3. fehlendem Bewerbungsziel für veröffentlichbare Jobs
4. fehlender zentraler Freigabelogik
