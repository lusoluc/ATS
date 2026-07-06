# Projekt-Richtlinien für SecurATS (Compliance & Sicherheit)

Dieses Dokument legt verbindliche Entwicklungsrichtlinien für alle künftigen Entwickler und KI-Assistenten fest. Jede Änderung der Codebasis MUSS diese Compliance-Regeln einhalten und darf sie NIEMALS umgehen.

## 1. EU AI Act (KI-Gesetz)

SecurATS verarbeitet Bewerbungen und fällt damit im Bereich KI-Scoring unter die Regulierung für **Hochrisiko-KI-Systeme** (Beschäftigung/HR, Annex III).

- **Opt-In-Prinzip:**
  - KI-Scoring MUSS standardmäßig deaktiviert sein. Das Feature darf nur ausgeführt werden, wenn die Konfiguration `AI_SCORING_ENABLED` explizit in der Datenbank (SystemSetting) auf `'1'` gesetzt ist.
  - Wenn das Scoring inaktiv ist, darf der Code keinen künstlichen Platzhalter-Score erfinden. `aiScore` muss `None`/leer bleiben.
- **Menschliche Aufsicht (Human-in-the-Loop):**
  - Die KI darf niemals vollautomatisch Zu- oder Absagen generieren. Automatische Absagen dürfen im Code ausschließlich über fest vorgegebene K.-o.-Kriterien (`expectedAnswer` bei Mindeststandards) realisiert werden.
  - Das KI-Urteil dient ausschließlich als Assistenzsystem.
- **Erklärbarkeit (Explainability):**
  - Jeder KI-Scoring-Durchlauf muss zwingend ein Feld `rationale` mit einer kurzen, für Menschen verständlichen Begründung (in deutscher Sprache) erzeugen und speichern.

## 2. AGG (Diskriminierungsfreiheit)

- Der System-Prompt für die KI MUSS immer die Anweisung enthalten, ausschließlich fachlich und AGG-neutral zu bewerten.
- Merkmale wie Herkunft, Alter, Geschlecht, Religion, Behinderung, sexuelle Identität oder Aussehen dürfen NIEMALS in die Bewertung einfließen oder an das Modell übermittelt werden.

## 3. DSGVO & Datensouveränität (Zero-Data-Transfer)

- **On-Premise-Zwang:**
  - Es dürfen keine Cloud-APIs (wie OpenAI, Claude Cloud, Azure AI) für die Bewerberbewertung angebunden werden. Alle KI-Aufrufe müssen über ein lokal gehostetes Ollama erfolgen.
- **Audit-Logging:**
  - Jede Ausführung der KI muss im revisionssicheren Audit-Log (`create_chained_audit`) erfasst werden.
  - **Kein Klartext ins Log:** Personenbezogene Daten (PII) dürfen niemals im Audit-Log landen. Prompts müssen vor dem Logging über `redact_for_log` (Länge + SHA-256) maskiert werden. Echte UUIDs (z. B. `application_id`) sind im Log erlaubt, um den Audit-Pfad zu erhalten.
- **Daten-Verschlüsselung:**
  - Alle personenbezogenen Daten (PII) müssen in der Datenbank verschlüsselt sein (Fernet, `EncryptedCharField`). Suchen/Vergleiche auf E-Mails dürfen nur über einen deterministischen Blind-Index (`emailHash` via HMAC-SHA256) erfolgen.

## 4. BOLA (Zugriffsschutz)

- Jede Listen- oder Detail-View im Recruiter-Bereich muss durch den Standort-/Einrichtungs-Scope des jeweiligen Benutzers gefiltert sein (`can_access_application` und `scope_applications`). IDs von Bewerbern dürfen niemals ungeprüft geladen werden.
