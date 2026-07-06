# DORA-Konformitäts-Stellungnahme (IKT-Drittparteienrisiko)

**Produkt:** SecurATS  
**Zielgruppe:** IT-Sicherheitsbeauftragte & Compliance-Officer in Finanzunternehmen (Banken, Versicherungen, Wertpapierfirmen)  
**Regulatorischer Kontext:** Verordnung (EU) 2022/2554 (Digital Operational Resilience Act – DORA)  
**Stand:** Juli 2026

---

## 1. Einleitung & IKT-Drittparteien-Risiko

Der **Digital Operational Resilience Act (DORA)** verpflichtet Finanzunternehmen in der EU ab Januar 2025 zur Sicherstellung einer hohen digitalen operationalen Belastbarkeit. Ein zentraler Pfeiler ist die Überwachung des IKT-Drittparteienrisikos (ICT Third-Party Risk).

SecurATS wurde mit dem Architekturprinzip **On-Premise-First** entwickelt. Im Gegensatz zu typischen SaaS-Recruiting-Plattformen verbleiben alle Daten und Prozesse innerhalb der vom Finanzinstitut kontrollierten Sicherheitsgrenzen (Sicherheitsbereich / Virtual Private Cloud).

---

## 2. DORA-Konformität im Detail

### 2.1. Minimierung des IKT-Konzentrationsrisikos (Art. 28-30 DORA)
* **Die Herausforderung:** Die Nutzung marktbeherrschender Cloud-Anbieter führt zu IKT-Klumpenrisiken.
* **SecurATS-Lösung:** Die Plattform läuft vollständig autark im Rechenzentrum des Instituts (z. B. als Docker-Container-Cluster unter Linux). Es besteht **keinerlei Abhängigkeit** von externen Cloud-Infrastrukturen des Herstellers. Ein Ausfall externer SaaS-Dienste beeinträchtigt die Betriebsstabilität des Recruiting-Prozesses nicht.

### 2.2. Datensouveränität & Vermeidung von Schatten-IT (Informationssicherheit)
* **Die Herausforderung:** Sensible Personal- und Bewerberdaten fließen bei SaaS-Lösungen über globale Schnittstellen ab.
* **SecurATS-Lösung:**
  * **On-Premise-LLM:** Das Bewerber-Scoring läuft über ein lokal gehostetes Ollama/Gemma-Modell im internen Docker-Netzwerk des Instituts. Zu keinem Zeitpunkt werden Daten an externe APIs (z. B. OpenAI) übertragen.
  * **Verschlüsselungshoheit:** Die symmetrische Verschlüsselung (`PII_ENCRYPTION_KEY`) wird über Umgebungsvariablen des Instituts konfiguriert. Die Entschlüsselung erfolgt im RAM der Web-Applikation; der Herstellersupport hat keinen standardmäßigen Zugriff auf die Schlüssel.

### 2.3. Auditierbarkeit & Protokollierung (Art. 30 Abs. 2 lit. e DORA)
* **Die Herausforderung:** Lückenloser Nachweis aller Sicherheitsereignisse gegenüber Aufsichtsbehörden (BaFin, EZB).
* **SecurATS-Lösung:**
  * **Kryptografisch verkettetes Audit-Log (`create_chained_audit`):** Jeder Systemzugriff, Dateidownload (CVs) und jede Statusänderung wird manipulationssicher aufgezeichnet. Da die Einträge via Hash-Chain verkettet sind, können Vorfälle lückenlos und manipulationsgeschützt auditiert werden.
  * **Anbindung an SIEM:** Das Audit-Log schreibt in das standardisierte Django-Logging-System und kann direkt an zentrale Log-Aggregatoren (Splunk, Graylog, ELK) des Instituts weitergeleitet werden.

### 2.4. Resilienz & Notfallvorsorge (Business Continuity / Disaster Recovery)
* **Die Herausforderung:** Gewährleistung der Geschäftskontinuität bei Systemausfällen.
* **SecurATS-Lösung:**
  * **Zustandsloses Anwendungsdesign:** Die Django-Applikation selbst ist zustandslos (stateless) und kann redundant hinter einem Load Balancer betrieben werden.
  * **Ausfallsicheres Caching & Queueing:** Die integrierte Async-Queue (`AiTask`) speichert anstehende KI-Aufgaben transaktionssicher in der PostgreSQL-Datenbank. Nach einem eventuellen Datenbank-Failover setzt der Worker-Prozess die Abarbeitung nahtlos fort.

---

## 3. Vertragliche Anforderungen (Art. 30 DORA)

Zur Unterstützung der vertraglichen Vereinbarungen stellt SecurATS standardmäßig bereit:
1. Eine vollständige **Verzeichnisstruktur der Datenverarbeitung** (siehe [AVV.md](file:///C:/Users/Admin/Downloads/securats/compliance/AVV.md)).
2. Detaillierte Sicherheitsgarantien (siehe [TOMs.md](file:///C:/Users/Admin/Downloads/securats/compliance/TOMs.md)).
3. Ein definiertes **Patch- und Update-Management** via SemVer-Releases und vorkonfigurierten Docker-Compose-Containern zur schnellen Einspielung von Sicherheitsupdates.
