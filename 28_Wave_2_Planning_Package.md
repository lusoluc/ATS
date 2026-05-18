# 28_Wave_2_Planning_Package.md

## Dokumentstatus
- **Version:** 1.0
- **Zweck:** Architektur- und Umsetzungsplanung für Wave 2 (Skalierung, tiefe Integration & fortgeschrittene Prozesse)
- **Fokus:** Erweiterung der in Wave 1 gebauten Basis um fortgeschrittene Funktionen.
- **Zielgruppe:**
  - Product Owner
  - Enterprise Architect
  - Senior Developer Agent
  - Central HR Career Department
- **Gültigkeit:** Landesverein-spezifisch, setzt zwingend auf dem Code- und Datenmodell aus Wave 1 auf.

---

# 1. Ziel von Wave 2 (Skalierung & Tiefe)

Nachdem in Wave 1 das MVP (Minimum Viable Product) mit funktionierender Governance, BOLA-Guards und Privacy-Metriken live gegangen ist, konzentriert sich Wave 2 auf die **funktionale Tiefe und externe Vernetzung**. 

Die Plattform wird von einem sicheren Job-Portal zu einem echten **Bewerbermanagement-Ökosystem (ATS-Erweiterung)** ausgebaut.

## Kernthemen:
1. **Tiefe im Bewerbungsprozess:** Echte Interview-Planung und Kalender-Integration statt manueller Einladungs-Status.
2. **Daten-Anreicherung:** Detailseiten für Facilities (Einrichtungen) und noch spezifischere Karrierepfade.
3. **Analytics & Reporting:** Dashboards für Central HR zur Messung von "Time-to-Hire" und "Bewerber-Drop-Off".
4. **HRIS-Integration:** Anbindung an das finale Personalverwaltungssystem (z.B. SAP SuccessFactors, LOGA oder Workday) zur nahtlosen Personalübernahme (`HIRED`-Trigger).

---

# 2. Scope von Wave 2

## 2.1 In Scope

### 2.1.1 Advanced Local Recruiting Operations
- **Interview Scheduling Engine:** Interaktive Kalender zur Terminfindung zwischen LocalHiringReviewer und Bewerber.
- **Message Center:** Bidirektionale In-App-Kommunikation mit dem Bewerber (inkl. E-Mail-Notifikationen), voll DSGVO-konform und zentral im System auditiert.
- **Custom Local Workflows:** Einrichtungen (`Facilities`) können spezifische Sub-Steps im Recruiting-Prozess definieren (z.B. "Probearbeitstag in der Pflege").

### 2.1.2 Erweiterte Public Experience (Frontend)
- **Facility Detail Pages (`/einrichtungen/[slug]`):** Eigene Landingpages für die verschiedenen Zentren und Kliniken des Landesvereins, inkl. lokaler Benefits und Ansprechpartner.
- **Erweiterte Job-Suchen:** Geodaten-basierte Umkreissuche ("Jobs im Umkreis von 20km um Rickling").
- **Talent Pool / Job Alert:** User können sich für Benachrichtigungen registrieren, wenn passende Jobs online gehen (erfordert Consent-Management-Update).

### 2.1.3 Analytics & Central HR Governance
- **Central HR Dashboard:** Metriken zu offenen Vakanzen, durchschnittlicher Besetzungsdauer und Engpass-Berufen.
- **Diversity & Bias Monitoring:** Anonymisierte Auswertungen (wo rechtlich zulässig), um Diskriminierung im Prozess zu erkennen.

### 2.1.4 Integrations (APIs)
- **Job-Board Multiposting:** API-Anbindung an StepStone, Indeed, oder Agentur für Arbeit zur automatisierten Veröffentlichung von `PUBLISHED` Jobs.
- **Core HR System (HRIS):** REST/SOAP-Push von eingestellten Kandidaten (`HIRED`) in das führende Personalverwaltungssystem zur Vertragserstellung.

---

## 2.2 Out of Scope (Verschoben auf Wave 3)
- KI-gestütztes automatisches Lebenslauf-Screening (zu hohes rechtliches / betriebsrätliches Risiko in Wave 2).
- Vollständiges internes Mitarbeiter-Portal (Fokus bleibt auf externen Bewerbern).
- Komplexe Gehaltsverhandlungs-Tools im UI.

---

# 3. Architektur- & Datenmodell-Erweiterungen (Prisma)

Für Wave 2 muss das `08_Entity_Data_Model.md` (und das `schema.prisma`) um folgende Kernelemente erweitert werden:

1. **`Interview` Entity:**
   - Verknüpft mit `ApplicationForm` und `User` (LocalHiringReviewer).
   - Felder: `scheduledAt`, `locationType` (Remote, In-Person), `meetingLink`, `outcome`.

2. **`Message` Entity:**
   - Speichert die Kommunikation.
   - Felder: `direction` (Inbound, Outbound), `content`, `readStatus`.

3. **`TalentPoolSubscription` Entity:**
   - Für den Job Alert.
   - Felder: `email`, `criteria` (JSON), `consentId`, `expiresAt`.

4. **`FacilityProfile` Entity:**
   - Reichhaltigere Daten für die `/einrichtungen` Landingpages.
   - Felder: `description`, `images`, `contactPersonId`.

---

# 4. Security & Compliance Implikationen (Wave 2)

Die Erweiterungen bringen neue Herausforderungen:
- **Message Center Privacy:** Die Nachrichten zwischen Recruiter und Bewerber enthalten hochgradig PII (Personal Identifiable Information). Der Retention-Worker aus WP05 muss so aktualisiert werden, dass auch die `Message` Entity nach 6 Monaten anonymisiert wird.
- **API Multiposting:** Externe Job-Boards benötigen Zugriff. Eine neue M2M (Machine-to-Machine) Auth-Strategie mit streng limitierten OAuth2 Scopes (`read:jobs_public`) muss etabliert werden.
- **HRIS Integration:** Der Export von eingestellten Kandidaten in das Core HR System erfordert mTLS (Mutual TLS), wie im Security Guide (`14_`) spezifiziert.

---

# 5. Roadmap & Nächste Schritte

Um Wave 2 technisch zu starten, müssen folgende Developer-Aufgaben ausgeführt werden:

1. **WP07 - Data Model Expansion:** Update des Prisma-Schemas mit `Interview`, `Message`, und `TalentPoolSubscription`. Durchführung der DB-Migration.
2. **WP08 - Interview & Message API:** Entwicklung der sicheren Endpunkte unter Wahrung der bestehenden BOLA-Guards.
3. **WP09 - Advanced Frontend Features:** Bau der Facility-Seiten und Integration der Map/Geodaten-Suche.
4. **WP10 - System Integration:** Anbindung des Multiposters (z.B. via XML-Feed) und des HRIS-Export-Workers.

---

**Freigabestatus Wave 2 Planning:**
Entwurf bereit zur Review durch den Product Owner und Enterprise Architect.
