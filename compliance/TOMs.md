# Technische und Organisatorische Maßnahmen (TOM) gemäß Art. 32 DSGVO

**Produkt:** SecurATS (On-Premise Recruiting-Plattform)  
**Betriebsmodell:** Self-Hosted / On-Premise (im Rechenzentrum des Betreibers oder dessen MSP)  
**Stand:** Juli 2026

Da SecurATS als On-Premise-Software direkt in der Infrastruktur des Anwenders (z. B. Krankenhausträger, Bank, Versicherung) betrieben wird, teilt sich die Verantwortung für die Sicherheit der Verarbeitung:
* **Infrastrukturelle Sicherheit (Netzwerk, Hardware, OS, Backup):** Verantwortung des Betreibers.
* **Applikationssicherheit & Datenverschlüsselung:** Durch SecurATS systemseitig gewährleistet (nachfolgend dokumentiert).

---

## 1. Vertraulichkeit (Art. 32 Abs. 1 lit. b DSGVO)

### 1.1. Zutrittskontrolle
* **Maßnahme:** Verhinderung des unbefugten Zutritts zu Verarbeitungsanlagen (Server, Rechenzentren).
* **Umsetzung:** Da die Software On-Premise betrieben wird, unterliegt dies der physischen Zutrittskontrolle des Betreibers (z. B. Chipkarten-Systeme, Alarmbandsicherung, Videoüberwachung).

### 1.2. Zugangskontrolle
* **Maßnahme:** Verhinderung der Nutzung von Verarbeitungsystemen durch Unbefugte.
* **Umsetzung:**
  * **Rollenbasierte Rechteverwaltung (RBAC):** Django-basierte Gruppenstruktur (`HR-Admin`, `Recruiter`, `Hiring-Manager`, `Viewer`) trennt Berechtigungen granular ab.
  * **Brute-Force-Schutz (SafeLoginView):** Automatisches Sperren von IP-Adresse und Benutzername für 10 Minuten nach 5 Fehlversuchen über Djangos Caching-System.
  * **Sichere Session-Handhabung:** Nutzung verschlüsselter Session-Cookies mit `HttpOnly`- und `Secure`-Flags.

### 1.3. Zugriffskontrolle
* **Maßnahme:** Gewährleistung, dass Zugriffsberechtigte nur auf die ihrer Zugriffsberechtigung unterliegenden Daten zugreifen können.
* **Umsetzung:**
  * **BOLA-Prävention (Broken Object Level Authorization):** Jede Datenbankabfrage im Recruiter-Bereich wird serverseitig durch den Standort- und Einrichtungs-Scope des jeweiligen Benutzers gefiltert (`can_access_application` und `scope_applications`). Der direkte Zugriff über manipulierte IDs wird blockiert.
  * **Verschlüsselung personenbezogener Daten (PII-Encryption-at-Rest):** Alle hochsensiblen Bewerberdaten (Name, Anschrift, E-Mail-Adresse, Telefonnummer) werden in der PostgreSQL-Datenbank mittels starker symmetrischer Verschlüsselung (Fernet-Verfahren, AES-128 in CBC-Modus) verschlüsselt abgelegt (`EncryptedCharField`).
  * **Deterministischer Blind-Index:** E-Mail-Suchen und -Vergleiche (z. B. zur Duplikatsprüfung beim CSV-Import) erfolgen ausschließlich über einen kryptografischen HMAC-SHA256-Hash (`emailHash`). Die E-Mail-Adresse selbst verbleibt verschlüsselt.

### 1.4. Trennungskontrolle
* **Maßnahme:** Gewährleistung, dass zu unterschiedlichen Zwecken erhobene Daten getrennt verarbeitet werden.
* **Umsetzung:**
  * Logische Datentrennung auf Datenbankebene über Mandanten- und Einrichtungs-Strukturen (`Facility`, `Department`).
  * Strenge Trennung von Demodaten (über den abgesicherten `DEMO_MODE` via `seed_demo`) und echten Bewerberdaten.

---

## 2. Integrität (Art. 32 Abs. 1 lit. b DSGVO)

### 2.1. Weitergabekontrolle
* **Maßnahme:** Gewährleistung, dass personenbezogene Daten bei der Übertragung oder Speicherung nicht unbefugt gelesen, kopiert oder verändert werden können.
* **Umsetzung:**
  * **Zero-Data-Transfer-KI (On-Premise-LLM):** Alle KI-Aufrufe (z. B. für das Bewerbungs-Scoring oder Tonalitätsanalysen) gehen ausschließlich an die lokale **Ollama-Instanz** im selben Docker-Netzwerk. Es erfolgt kein Transfer von Bewerberdaten an externe Cloud-APIs (wie OpenAI, Claude Cloud).
  * **Datei-Upload-Sanitizing:** Hochgeladene Nachweise und Lebensläufe werden gegen eine strenge Dateitypen-Whitelist (PDF, DOCX, JPG, PNG) und ein Größenlimit (max. 10 MB) geprüft. Pfad-Traversal-Angriffe bei der Speicherung sind technisch ausgeschlossen.
  * **Geschützter CV-Download:** Lebensläufe sind nicht direkt über das Dateisystem abrufbar (`media/`-Ordner geschützt), sondern werden über einen autorisierten Django-Endpunkt ausgeliefert, der Berechtigungen prüft und den Zugriff protokolliert.

### 2.2. Eingabekontrolle
* **Maßnahme:** Gewährleistung, dass nachträglich überprüft werden kann, ob und von wem personenbezogene Daten eingegeben, verändert oder entfernt worden sind.
* **Umsetzung:**
  * **Revisionssicheres Chained Audit-Log:** Jede sicherheits- oder prozessrelevante Aktion (z. B. CV-Download, Statusänderung, Freigabe, KI-Scoring) wird über die Funktion `create_chained_audit` protokolliert.
  * **Manipulationserkennung:** Das Audit-Log verkettet Einträge kryptografisch (Hash-Chain), sodass nachträgliche Manipulationen an den Protokollen sofort auffallen.
  * **DSGVO-Konformes Logging:** Im Audit-Log werden keine PII (Klartext-Bewerberdaten) gespeichert. Prompts werden vor dem Logging über `redact_for_log` in Länge und einen SHA-256-Hash maskiert.

---

## 3. Verfügbarkeit und Belastbarkeit (Art. 32 Abs. 1 lit. b DSGVO)

### 3.1. Verfügbarkeit & Rasche Wiederherstellbarkeit
* **Maßnahme:** Gewährleistung, dass das System bei einem physischen oder technischen Zwischenfall rasch wiederhergestellt werden kann.
* **Umsetzung:**
  * **Docker-Container-Architektur:** Schnelle Bereitstellung und Updates über Docker Compose (`docker compose up -d`). Automatisierte Healthchecks überwachen die Container (Django-App, PostgreSQL-DB, Ollama-Service).
  * **Async Queue-Architektur (AiTask):** Schwere KI-Analysen blockieren nicht den Web-Traffic des Hauptthreads, sondern laufen asynchron über eine datenbankgestützte Warteschlange. Dadurch wird das Risiko von Denial-of-Service-Zuständen durch Lastspitzen minimiert.

---

## 4. Verfahren zur regelmäßigen Überprüfung und Bewertung (Art. 32 Abs. 1 lit. d DSGVO)

* **Kontinuierliche Testsuite:** Über 340 automatisierte Regressionstests prüfen kontinuierlich die Einhaltung der Sicherheitsfunktionen (z. B. CSRF-Schutz, BOLA-Sperren, Verschlüsselung, Brute-Force-Sperren).
* **No-Code-Prozessrichtlinien:** Sicherheitsrelevante K.O.-Kriterien und Mindeststandards für Stellen werden serverseitig erzwungen (`ensure_minimum_standards`), um Fehler durch Anwender auszuschließen.
