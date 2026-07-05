# SecurATS – Compliance-Matrix (Norm → Feature → Nachweis)

Stand: WP2. Verknüpft regulatorische Anforderungen mit implementierten Funktionen
und ihren automatisierten Tests. Legende Status: ✅ umgesetzt · ◐ teilweise · ❌ offen.

| Norm / Anforderung | Feature in SecurATS | Ort im Code | Test / Nachweis | Status |
|---|---|---|---|---|
| **DSGVO Art. 15/20** – Auskunft & Datenübertragbarkeit | Betroffenenauskunft als JSON-Export (ohne interne Vermerke) | `dsgvo.build_applicant_export`, `manage.py export_applicant` | `DsgvoExportTestCase` | ✅ |
| **DSGVO Art. 17** – Recht auf Löschung | Automatische Anonymisierung abgelehnter Bewerbungen > Frist, ohne Talentpool-Consent | `management/commands/data_retention.py` (`--days`, `--dry-run`) | manuell/Dry-Run | ✅ |
| **DSGVO Art. 25** – Datenschutz durch Technikgestaltung | ALLE Bewerber-PII-Felder verschlüsselt (Fernet), **inkl. E-Mail** via deterministischem Blind-Index (HMAC-SHA256, unique, Lookup-fähig); keine PII in KI-Logs | `email_blind_index`, `ApplicantManager.get_by_email`, `ai_safety.redact_for_log` | `EmailBlindIndexTestCase` (Ciphertext-Nachweis, Unique via Hash, Export-Klartext) | ✅ |
| **DSGVO Art. 30/32** – Verzeichnis & Integrität der Verarbeitung | Revisionssicheres Audit-Log mit Hash-Kette (Manipulationserkennung) | `audit.create_chained_audit`, `verify_audit_chain`, `manage.py verify_audit` | `AuditChainTestCase` | ✅ |
| **DSGVO Art. 32** – Zugriffskontrolle (Vertraulichkeit) | Rollen (RBAC) + objektbezogene Zugriffsgrenzen (BOLA) | `permissions.role_required`, `can_access_application` | `ApplicationDocumentsTestCase` (BOLA 404) | ✅ |
| **EU AI Act** – Hochrisiko-Bereich Beschäftigung (Anhang III) | **Scoring per Default deaktiviert** (`AI_SCORING_ENABLED`, Opt-in mit dokumentierter Risikoprüfung); ohne Opt-in keine automatische Bewertung, keine Platzhalter-Scores; Auto-Reject nur objektive K.-o.-Kriterien; Human-in-the-Loop bleibt bei Opt-in Pflichtprinzip. **Anbieter-Konformitätsbewertung für das Opt-in-Modul steht aus → Rechtsgutachten P1.4 (ROADMAP)** | `bewerben` (gated), `ScoringDefaultOffTestCase` | Default-Off + keine LLM-Berührung per Test nachgewiesen | ◐ (Risiko entschärft, Gutachten offen) |
| **EU AI Act** – Robustheit gegen Manipulation | Prompt-Injection-Abwehr: Bewerber-Inhalt als gekapselte Daten, System-Guardrail, Output-Validierung | `ai_safety.build_evaluation_payload`, `coerce_score` | `AISafetyTestCase` | ✅ |
| **AGG** – Diskriminierungsfreiheit | KI-System-Prompt auf AGG-Neutralität; keine sensiblen Merkmale im Matching | `ai_safety.AI_SYSTEM_GUARD` | Golden-Set (geplant, L5) | ◐ |
| **BFSG / WCAG** – Barrierefreiheit | A11y-Panel (Legasthenie-Schrift, Kontrast, Fokus, Lese-Lineal, Vorlesen), Leichte Sprache | `templates/base.html`, `job_detail.html` | manuell; WCAG-Audit (WP7) | ◐ |
| **KRITIS** – Betriebssicherheit / Monitoring | AI-Health-Endpoint, Diagnose-Command, abgesicherte Feeds (Token) | `healthz_ai`, `ai_doctor`, `feed_token_required` | `HealthzAiTestCase`, `FeedTokenTestCase` | ✅ |
| **On-Premise / Souveränität** | Vollständig lokaler Betrieb, lokale LLM (Ollama), keine Cloud-Abhängigkeit | Docker-Compose (nur Django), `get_ollama_url` | NORTHSTAR §1 | ✅ |

## Offene Punkte (dokumentiert, terminiert)

- ~~**E-Mail-Verschlüsselung (Art. 25/32)**~~ → **umgesetzt** (Migration 0014 inkl.
  Bestandsdaten-Rückfüllung): `Applicant.email` verschlüsselt, Eindeutigkeit/Lookup über
  `emailHash = HMAC-SHA256(lower(email))`. **Betriebshinweis:** Rotation des
  `PII_ENCRYPTION_KEY` erfordert Neuberechnung aller Blind-Indizes (siehe OPERATIONS.md).
- **AGG-Fairness-Golden-Set (L5):** Eval-Tests fürs Matching stehen in WP4/§3.5 an.
- **WCAG-Vollaudit:** in WP7 (Betrieb & Reife).
