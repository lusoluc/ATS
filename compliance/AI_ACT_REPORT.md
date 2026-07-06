# AI Act Konformitätsbericht (Technische Dokumentation / Pre-Assessment)

**Produkt:** SecurATS (On-Premise Recruiting-KI)  
**Modell:** Lokales Gemma (via Ollama)  
**Regulatorischer Status:** Hochrisiko-KI-System gemäß Art. 6 & Anhang III (Bereich Beschäftigung/HR) des EU AI Acts  
**Stand:** Juli 2026

---

## 1. Regulatorische Einordnung (EU AI Act)

SecurATS verarbeitet Bewerberdaten (Anschreiben, Lebensläufe) und führt eine KI-gestützte Eignungsbewertung (Scoring A–D) durch. Gemäß **Anhang III, Punkt 4 (Beschäftigung, Personalmanagement und Zugang zur selbstständigen Erwerbstätigkeit)** des EU AI Acts sind solche Systeme als **Hochrisiko-KI-Systeme** klassifiziert.

Als Hochrisiko-System unterliegt die Software strengen Anforderungen, bevor sie in der EU produktiv eingesetzt werden darf. Dieser Bericht dient als technische Vorbereitung für das juristische Konformitätsgutachten (Phase V1, P1.4) und dokumentiert die implementierten Schutzmaßnahmen.

---

## 2. Technische Umsetzung & Schutzmaßnahmen

### 2.1. Risiko-Gating & Opt-in (Default-Off-Prinzip)
* **Die Anforderung:** Keine automatische Ausführung unlizenzierter oder nicht risikogeprüfter KI-Systeme.
* **Die Umsetzung:** 
  * Das KI-Scoring ist standardmäßig deaktiviert. Die Applikationslogik in `ats/views.py` prüft vor jedem Scoring-Durchlauf, ob die Datenbank-Systemeinstellung `AI_SCORING_ENABLED` explizit auf `'1'` gesetzt ist.
  * Ist die Option inaktiv, wird der KI-Prozess übersprungen, `aiScore` bleibt `None`/leer, und die Benutzeroberfläche zeigt eine ehrliche Leerstelle („–“-Badge). Es wird kein künstlicher Platzhalter-Score generiert.

### 2.2. Menschliche Aufsicht (Human-in-the-Loop – Art. 14 AI Act)
* **Die Anforderung:** KI-Systeme dürfen Entscheidungen über Einzelpersonen nicht vollständig automatisieren; eine wirksame menschliche Aufsicht muss gewährleistet sein.
* **Die Umsetzung:**
  * Das System sieht **keine automatischen Zu- oder Absagen** auf Basis des KI-Scores vor. Der KI-Score (A–D) dient ausschließlich als Unterstützung für den menschlichen Recruiter.
  * Automatische Absagen sind im Code hart auf **objektive K.-o.-Kriterien** (wie fehlende gesetzliche Pflichtnachweise oder Mindeststandards, z. B. Führerschein für Fahrer-Rollen in `ats/questions.py`) beschränkt.
  * Die finale Einstufung und alle Statusänderungen (Einladung, Einstellung, Absage) werden immer manuell durch den Recruiter im Dashboard vorgenommen.

### 2.3. Transparenz & Erklärbarkeit (Explainability – Art. 13 AI Act)
* **Die Anforderung:** Hochrisiko-KI-Systeme müssen so konzipiert sein, dass ihre Ergebnisse für den Anwender interpretierbar und erklärbar sind.
* **Die Umsetzung:**
  * Das strukturierte JSON-Ausgabeschema (mittels Ollama-Formatfilter in `ats/ai_safety.py`) zwingt das Modell, zu jedem Score zwingend ein Feld `rationale` mit einer kurzen, prägnanten Begründung in deutscher Sprache (maximal 3 Sätze) zu erzeugen.
  * Diese Begründung wird in der Datenbank (`Application.aiRationale`) gespeichert und dem Recruiter direkt auf der Bewerberkarte und im Detail-Modal angezeigt.

### 2.4. Protokollierung & Rückverfolgbarkeit (Traceability – Art. 12 AI Act)
* **Die Anforderung:** Automatische Aufzeichnung von Systemereignissen über die gesamte Lebensdauer.
* **Die Umsetzung:**
  * Jeder KI-Durchlauf ruft die Funktion `log_ai_execution` auf, die ein detailliertes Protokoll im revisionssicheren Audit-Log (`create_chained_audit`) erzeugt.
  * Das Protokoll erfasst das verwendete Modell, die Latenzzeit, den Status (Erfolg/Fehlgeschlagen), das verwendete Tonalitäts-Overlay, eventuelle Reparatur-Retries (`repaired=True`) sowie die unverschlüsselte `application_id` (UUID), um den Audit-Pfad zur Bewerbung zu erhalten.
  * Zur Wahrung des Datenschutzes werden die tatsächlichen Bewerbertexte im Log über `redact_for_log` (Maskierung durch Länge + SHA-256-Hash) unkenntlich gemacht.

### 2.5. Integrität, Robustheit & Prompt-Injection-Schutz (Art. 15 AI Act)
* **Die Anforderung:** Schutz vor Manipulationen und Missbrauch durch Dritte.
* **Die Umsetzung:**
  * In `ats/ai_safety.py` kapselt der Helper `wrap_untrusted` alle Bewerberinhalte in eindeutige Marker (`<<<BEWERBER_INHALT>>>` und `<<<ENDE>>>`).
  * Der unveränderliche System-Prompt (`AI_SYSTEM_GUARD`) weist die KI explizit an, jegliche Anweisungen innerhalb dieser Marker als reine Nutzdaten (nicht als Systeminstruktionen) zu behandeln. Dies blockiert Versuche von Bewerbenden, ihren Score durch versteckte Prompts im Anschreiben zu manipulieren.

### 2.6. AGG-Neutralität & Bias-Prävention (Diskriminierungsfreiheit)
* **Die Anforderung:** Vermeidung von Benachteiligungen aufgrund geschützter Merkmale.
* **Die Umsetzung:**
  * Der System-Prompt enthält die strikte Anweisung: *"Du bewertest ausschließlich fachlich, AGG-neutral und ohne Diskriminierung."*
  * Personenbezogene Merkmale (wie Alter, Geschlecht, Religion, sexuelle Identität, Aussehen, Herkunft) werden zu keinem Zeitpunkt an das Modell übermittelt.

---

## 3. Konformitäts-Checkliste für die Rechtsberatung (Art. 9–15 AI Act)

| AI Act Artikel | Anforderung | Status in SecurATS | Technische Referenz |
|---|---|---|---|
| **Art. 9** | Risikomanagementsystem | **Vorbereitet** | SystemSetting-Gating (`AI_SCORING_ENABLED=0`), lokaler Betrieb (kein externer API-Ausfall möglich) |
| **Art. 10** | Daten & Daten-Governance | **Konform** | Datenverbleib On-Premise; PII-Verschlüsselung (`EncryptedCharField`); keine Nutzung von PII im KI-Pfad |
| **Art. 11** | Technische Dokumentation | **Vorbereitet** | Dieser Bericht, `AI_DEV_GUIDELINES.md`, `COMPLIANCE_MATRIX.md` |
| **Art. 12** | Protokollierung (Logging) | **Konform** | Chained Audit-Log via `log_ai_execution` mit UUID-Verknüpfung |
| **Art. 13** | Transparenz (Erklärbarkeit) | **Konform** | Erzwungene `rationale`-Generierung (Deutsch, max. 3 Sätze) |
| **Art. 14** | Menschliche Aufsicht | **Konform** | Kein Auto-Reject durch KI; rein unterstützendes Vorschlags-Scoring |
| **Art. 15** | Genauigkeit, Robustheit, Sicherheit | **Konform** | Prompt-Injection-Marker (`wrap_untrusted`), Reparatur-Retries für JSON-Validität |
