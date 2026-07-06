# Muster-Vereinbarung zur Auftragsverarbeitung (AVV) gemäß Art. 28 DSGVO

**Vertragspartner:**
1. **Der Auftraggeber** (Verantwortlicher gemäß Art. 4 Nr. 7 DSGVO, nachfolgend „Auftraggeber“)  
   und
2. **Die SecurATS GmbH** (Auftragsverarbeiter gemäß Art. 4 Nr. 8 DSGVO, nachfolgend „Auftragnehmer“)

---

## 1. Gegenstand, Dauer und Spezifikation der Verarbeitung

### 1.1. Gegenstand und Zweck
Der Auftragnehmer stellt dem Auftraggeber die Software **SecurATS** zur Installation in dessen eigener IT-Infrastruktur bereit. Die Software dient der Digitalisierung des Bewerbungsprozesses (Karriereportal, Job-Manager, Bewerber-Dashboard, Bewertung und Terminvereinbarung).

*Hinweis zum On-Premise-Betrieb:* Da die Software lokal beim Auftraggeber betrieben wird, erfolgt im Normalbetrieb **kein automatischer Datenabfluss** an den Auftragnehmer. Dieser Vertrag tritt in Kraft für Fälle, in denen der Auftragnehmer im Rahmen von Support-Leistungen, Updates, Datenbankwartungen oder Fehlerbehebungen (Remote Access) Zugriff auf personenbezogene Daten der Bewerbenden erhält.

### 1.2. Dauer der Verarbeitung
Die Laufzeit dieses Vertrages richtet sich nach dem zugrundeliegenden Software-Nutzungs- oder Support-Vertrag.

---

## 2. Art der Daten und Kategorien betroffener Personen

### 2.1. Kategorien betroffener Personen
* Bewerberinnen und Bewerber (Kandidaten)
* Beschäftigte des Auftraggebers (Recruiter, Hiring-Manager, Administratoren, Gremienmitglieder)

### 2.2. Arten personenbezogener Daten (Bewerberdaten)
* **Stammdaten:** Name, Vorname, Anschrift, E-Mail-Adresse, Telefonnummer (verschlüsselt at-rest in der Datenbank).
* **Bewerbungsdaten:** Anschreiben, Lebenslauf (CV), Zeugnisse, Zertifikate, Noten, Antworten auf Screening-Fragen (Pflicht- und K.O.-Kriterien).
* **Prozessdaten:** Gesprächsnotizen, Interview-Feedback der Fachbereiche, geplante und gebuchte Termine (Timeslots).
* **KI-Evaluationsdaten:** AI-Scores (A–D), AI-Rationale (Begründungstexte).
* **System- & Loggingdaten:** IP-Adressen (für Brute-Force-Schutz), Audit-Log-Einträge (kryptografisch verkettet, PII-redigiert).

---

## 3. Pflichten des Auftragnehmers (Art. 28 Abs. 3 DSGVO)

Der Auftragnehmer verpflichtet sich, die folgenden Vorgaben einzuhalten:

1. **Weisungsgebundene Verarbeitung:** Die Verarbeitung der Daten erfolgt ausschließlich im Rahmen der getroffenen Vereinbarungen und nach dokumentierten Weisungen des Auftraggebers.
2. **Vertraulichkeit:** Alle Personen, die Zugriff auf die Daten des Auftraggebers haben, sind zur Vertraulichkeit verpflichtet (Verschwiegenheitserklärung).
3. **Technische und Organisatorische Maßnahmen:** Der Auftragnehmer setzt die in der Anlage **TOM** vereinbarten technischen und organisatorischen Maßnahmen um.
4. **Keine externen KI-APIs:** Der Auftragnehmer sichert zu, dass die Software SecurATS im Standard ausschließlich lokale KI-Modelle (über Ollama) anspricht. Bewerberdaten werden zu keinem Zeitpunkt an Drittanbieter-Modelle (z. B. OpenAI, Anthropic) übertragen.
5. **Unterstützungspflichten:** Der Auftragnehmer unterstützt den Auftraggeber bei der Beantwortung von Betroffenenanfragen (Art. 12-22 DSGVO), der Erstellung von Datenschutz-Folgenabschätzungen (DSFA) und bei Meldungen an Aufsichtsbehörden.
6. **Löschung nach Support-Ende:** Nach Abschluss der Support-Arbeiten werden alle temporär übertragenen Datenbestände (z. B. Log-Dateien, Dump-Dateien zur Fehleranalyse) unverzüglich gelöscht.
7. **Kontrollrechte:** Der Auftragnehmer stellt dem Auftraggeber alle erforderlichen Informationen zum Nachweis der Einhaltung dieses Vertrages zur Verfügung und ermöglicht Überprüfungen (Audits).

---

## 4. Pflichten des Auftraggebers

1. Der Auftraggeber ist für die Rechtmäßigkeit der Datenverarbeitung (z. B. Einholung der Einwilligung bei Talent-Pool-Aufnahmen gemäß Art. 6 Abs. 1 lit. a DSGVO) verantwortlich.
2. Der Auftraggeber stellt sicher, dass der kryptografische Schlüssel zur Entschlüsselung der Bewerberdaten (`PII_ENCRYPTION_KEY`) sicher verwahrt wird und dem Auftragnehmer bei Remote-Support-Sitzungen nur im unbedingt erforderlichen Maße zugänglich gemacht wird.
3. Der Auftraggeber konfiguriert den Aufbewahrungs- und Löschzyklus der Bewerberdaten entsprechend den eigenen Löschkonzepten (Nutzung des mitgelieferten Commands `retention_cleanup`).
