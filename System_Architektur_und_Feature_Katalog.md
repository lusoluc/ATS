# System-Architektur & Feature-Katalog: SecurATS – Datensouveränes Bewerbermanagementsystem

**Autor & Urheber:** Carlos Lucas  
**Adresse:** Weg am Denkmal 34, 22844 Norderstedt - Deutschland  
**Kontakt:** [LinkedIn - Director IT Development](https://www.linkedin.com/in/director-it-development/)

## 1. Executive Summary
Diese hochmoderne, quelloffene Karriereplattform ist eine vollständig integrierte Enterprise-Lösung. Sie vereint ein leistungsstarkes Content-Management-System (CMS), vollautomatisiertes Job-Multiposting und ein Applicant Tracking System (ATS) in einer einzigen, nahtlosen Umgebung.

Der absolute USP (Unique Selling Proposition) dieser Architektur ist der kompromisslose Fokus auf **Datensouveränität** und **Legal Compliance**. Durch eine Zero-Data-Transfer-Policy, integrierte lokale Sprachmodell-Unterstützung und extrem hohe Verschlüsselungsstandards (AES-256) löst SecurATS die größten Schmerzpunkte heutiger HR-Abteilungen: Den Schutz hochsensibler Personendaten bei gleichzeitiger Sicherstellung höchster Prozessstabilität.

Dieses System ist nicht nur eine Recruiting-Software, sondern ein aktives Risikomanagement- und Compliance-Tool. Durch die extrem hohen Standards an Datensicherheit und Informationsschutz ist diese Plattform out-of-the-box für streng regulierte Branchen konzipiert. Dazu gehören insbesondere:
*   **Krankenhauswesen & Gesundheitssektor:** Sicherer Umgang mit Gesundheitsdaten nach Art. 9 DSGVO.
*   **Kirche & Diakonie:** Erfüllt die verschärften Anforderungen des DSG-EKD und KDG.
*   **Banken & Finanzwesen:** Erfüllt die DORA-Anforderungen zur Minimierung von Drittparteienrisiken.
*   **KRITIS-Betreiber (z.B. Stadtwerke, Wasserwerke, Energieversorger):** Air-Gapped Architektur ermöglicht Betrieb in Hochsicherheitsnetzwerken ohne externe Cloud-Abhängigkeiten.

---

## 2. Erfüllte Normen & Regulatorien (Compliance Readiness)
Die Architektur wurde explizit darauf ausgelegt, die strengsten nationalen und internationalen Regularien out-of-the-box zu erfüllen. Damit ist das System für nahezu alle Branchen und Länder im europäischen und westlichen Raum – insbesondere im hochsensiblen KRITIS-Umfeld – sofort einsetzbar.

### 2.1 Datenschutz & Privatsphäre
*   **EU-DSGVO (Datenschutz-Grundverordnung) / GDPR:**
    *   *Art. 5 (Speicherbegrenzung & Datenminimierung):* Ein automatisierter Cronjob (`data-retention`) löscht abgelehnte Bewerbungen nach Ablauf der Frist (z.B. 6 Monate) rückstandsfrei von der Festplatte und anonymisiert die Datensätze.
    *   *Art. 7 (Einwilligung):* Explizite Opt-In-Verfahren für die Aufnahme in den Talent Pool garantieren Rechtmäßigkeit.
    *   *Art. 32 (Sicherheit der Verarbeitung):* Lebensläufe werden auf der Festplatte via **AES-256-GCM** verschlüsselt (Data-at-rest). Der Transport erfolgt via striktem HTTPS/HSTS (Data-in-transit).
*   **DSG-EKD (Datenschutzgesetz der Evangelischen Kirche in Deutschland) & KDG (Katholischer Datenschutz):**
    *   Durch die Air-Gapped Architektur (keine Cloud-APIs, keine Tracker, keine Google Fonts) und das strikte Audit-Logging erfüllt das System die besonderen Anforderungen kirchlicher und diakonischer Träger an die Datenverarbeitung.
*   **CCPA / CPRA (Kalifornien, USA):** Vollständige Kontrolle über Nutzerdaten und sofortige, rückstandsfreie Löschbarkeit auf Knopfdruck.

### 2.2 Informationssicherheit & Resilienz
*   **ISO/IEC 27001 (Informationssicherheits-Managementsysteme):**
    *   *A.9 Zugangssteuerung:* Garantiert durch kryptografische Magic-Links (Passwortlos), feingranulares Role-Based Access Control (RBAC) und strikte BOLA-Prävention auf API-Ebene.
    *   *A.12 Betriebssicherheit:* Schutz vor DDoS- und Spam-Angriffen durch einen integrierten Token-Bucket **Rate-Limiter**.
    *   *A.14 Systemsicherheit:* OWASP Top 10 konform. Schutz vor XSS durch CSP-Header und serverseitige HTML-Sanitization (`DOMPurify`). Schutz vor SQL-Injection durch das Prisma ORM.
    *   *A.18 Compliance (Audit-Logging):* Ein manipulationssicheres Audit-Log dokumentiert jeden sensiblen Lesezugriff (z.B. Download eines Lebenslaufs) mit Zeitstempel und User-ID.
*   **DORA (Digital Operational Resilience Act - EU-Finanzsektor):**
    *   Minimierung von IKT-Drittparteienrisiken (Supply Chain Risk). Da die Plattform 100% autark läuft und keine SaaS-APIs (kein OpenAI, kein Calendly) zwingend benötigt, wird die Lieferkette massiv verkürzt und die operationelle Resilienz für KRITIS-Betreiber sichergestellt.

### 2.3 Arbeitsrecht & Gleichbehandlung
*   **AGG (Allgemeines Gleichbehandlungsgesetz, Deutschland):**
    *   Ein intelligenter "Legal-Tech-Check" analysiert Stellenanzeigen vor Veröffentlichung in Echtzeit auf Diskriminierungen (Alter, Geschlecht, Herkunft) und erzwingt z.B. das `(m/w/d)`.
    *   Die lokale Sprachmodell-Unterstützung zur Bewerberanalyse ist durch den System-Prompt gezwungen, "farbblind" zu sein. Die Auswertung von Fotos, Ethnie, Religion oder Alter ist technisch untersagt.
*   **ISO 9001 (Qualitätsmanagement):**
    *   Reproduzierbare Prozesse durch den Workflow-Builder und standardisierte K.O.-Fragen-Kataloge stellen sicher, dass Bewerbungen prozesssicher und in gleichbleibender Qualität bearbeitet werden.

---

## 3. Die Sicherheitsarchitektur im Detail

*   **AES-256-GCM Dateiverschlüsselung:** Hochgeladene PDFs werden nicht als Klartext gespeichert. Ein AES-256 Wrapper verschlüsselt die Dateien, bevor sie im Storage landen. Ohne den Master-Key des Servers sind gestohlene Festplatten wertlos.
*   **BOLA-Schutz (Broken Object Level Authorization):** Die API vertraut niemals nur auf IDs. Jede Datenbankabfrage (z.B. "Bewerbung anzeigen") erzwingt einen Abgleich mit den Berechtigungen des Nutzers (`facilityId`).
*   **Zero-Data-Transfer & Lokale Infrastruktur:** Das System integriert die lokale Sprachmodell-Unterstützung direkt im internen Netzwerk. Weder Lebensläufe noch Jobbeschreibungen verlassen die eigene Infrastruktur.
*   **Strict Security Headers:** Das System erzwingt HSTS, blockiert Framing (X-Frame-Options) zur Verhinderung von Clickjacking und implementiert eine strikte Content-Security-Policy (CSP) sowie Permissions-Policys.
*   **Rate-Limiting & XSS-Sanitizer:** Eingebauter Schutz gegen DDoS-Botnetze beim Bewerbungseingang und Bereinigung von potenziell gefährlichem HTML in Stellenanzeigen.

---

## 4. Der Feature-Katalog (Complete List)

### 4.1 Enterprise-Schnittstellen & Ökosystem (Entscheider-Fokus)
Die Plattform ist keine isolierte Insellösung, sondern fügt sich durch standardisierte und hochsichere Schnittstellen nahtlos in bestehende Konzern-Infrastrukturen und externe Recruiting-Kanäle ein. Dies minimiert Reibungsverluste und senkt Prozesskosten erheblich.

**1. SAP SuccessFactors Integration (Core HRIS)**
Eine hochsichere, modulare "Candidate-to-Employee" API-Bridge. Sie eliminiert fehleranfällige manuelle Dateneingaben durch HR und übergibt eingestellte Kandidaten vollautomatisch an das SAP-System.
*   **Dynamisches Daten-Mapping (Custom Fields):** Da keine zwei SAP-Instanzen gleich sind, verfügt das Dashboard über einen visuellen "Field Mapper". Admins können interne ATS-Felder flexibel den exakten OData-JSON-Keys zuweisen. Das umfasst Basisdaten (Kontakt, Adresse, Lebenslauf, Sprachen, Führerschein) sowie **gesundheitsspezifische Compliance-Felder** (Approbation, Facharzturkunden, Masernschutznachweis, Erweitertes Führungszeugnis). Das verhindert Hardcoding-Brüche bei API-Updates.
*   **Modulare Lizenz-Kompatibilität:** Das System skaliert dynamisch mit der vorhandenen SAP-Lizenz des Kunden (z.B. *Pre-Hire Profilanlage* in SAP Recruiting/EC, *Digitale Vertragsunterschrift* mit SAP Onboarding 2.0, *Automatisierte Gehaltsband-Zuweisung* über Employee Central).
*   **Safeguard Testing & Diagnostik:** Im Admin-Dashboard ist eine "Fail-Safe" Konfigurationsoberfläche integriert. Ein strikter Schalter zwischen **Sandbox (Test-Umgebung)** und **Produktion (Live)** garantiert risikofreie Rollouts. Ein integriertes **Ping-Diagnose-Tool** überprüft zudem auf Knopfdruck Firewalls, Base-URLs und Auth-Token.

**2. Bundesagentur für Arbeit (HR-BA-XML)**
*   Vollautomatische Schnittstelle zur Generierung von X.509-konformen XML-Dateien. 
*   Ermöglicht die direkte, massenhafte Einspeisung von Vakanzen in das Portal der Arbeitsagentur ohne manuellen Pflegeaufwand.

**3. Google for Jobs (Schema.org API) & SEO**
*   Automatische Generierung von JSON-LD strukturierten Daten inkl. Geodaten-Übermittlung für organische Top-Rankings in der Google-Suche.
*   **SEO-Optimiertes CMS:** Hierarchisches URL-Routing und dynamisch anpassbare Slugs sorgen für maximale organische Sichtbarkeit und reduzieren Abhängigkeiten von teuren Stellenbörsen.

### 4.2 Job- & Stammdatenverwaltung (Master Data)
*   **Job-Wizard & K.O.-Katalog:** Modulares Erstellen von Stellenangeboten durch Kombination von Textbausteinen. Zuweisung von verpflichtenden Screening-Fragen (Checkboxen) pro Job.
*   **Standort- & Kategorien-Verwaltung:** Flexible Pflege beliebig vieler Einrichtungen, Abteilungen und Arbeitsorte in einer Baumstruktur.
*   **Global Settings & Templates:** Verwaltung von systemweiten E-Mail-Vorlagen inkl. rechtssicherer AGG-Absage-Templates.

### 4.3 Frontend & Bewerbererlebnis
*   **Premium UI/UX:** Barrierearmes, hochmodernes Design mit flüssigen Mikro-Animationen und Responsive Layout.
*   **Intelligente Job-Filterung:** Echtzeit-Suche nach flexiblen Kriterien auf der Karriere-Seite.
*   **60-Sekunden-Bewerbung:** Ein schlankes Formular, das Anschreiben überflüssig macht, dynamisch K.O.-Fragen lädt und optionales Talent-Pool-Opt-In anbietet.
*   **Job-Alerts:** Interessenten können sich bei neuen Vakanzen benachrichtigen lassen.

### 4.4 Applicant Tracking System (ATS)
*   **Kanban-Board:** Interaktive, visuelle Spaltenansicht zur Steuerung von Bewerbern durch anpassbare Phasen.
*   **Workflow Engine:** Anpassbare, mehrstufige Genehmigungsverfahren für interne Abstimmungen vor einer Einstellung.
*   **Interne Kommentare:** Geschützte Notizfunktion für den sicheren, internen Austausch über Kandidaten.
*   **Terminplanung (Interview Slots):** Integrierter Kalender, über den Bewerber eigenständig zugewiesene Termine buchen können (kein Calendly nötig).

### 4.5 IAM, Sicherheit & Audit-Logging
*   **Flexible Urlaubsvertretung (Delegation of Authority):** Hochflexible, auf bestimmte Standorte begrenzte und strikt zeitgesteuerte Übergabe von Rechten an Kollegen.
*   **Role-Based Access Control (RBAC):** Feingranulares Rechtesystem für komplexe Unternehmensstrukturen.
*   **Passwortloser Login (Magic-Link):** Hochsicherer Login-Prozess via E-Mail.
*   **Vollständiges Audit-Logging:** Lückenlose Aufzeichnung aller sicherheitsrelevanten Zugriffe (wer hat welchen Lebenslauf wann heruntergeladen?) zur Erfüllung von ISO 27001.
*   **Automatisierte Lösch-Cronjobs:** Garantierte Einhaltung der DSGVO-Löschfristen durch verschlüsselte Vernichtung und Daten-Anonymisierung.

### 4.6 Lokale Sprachmodell-Unterstützung (Air-Gapped)
*   **Anti-Bias CV-Analyzer:** Das Sprachmodell liest Lebensläufe, extrahiert Kompetenzen und berechnet Matching-Scores völlig diskriminierungsfrei.
*   **Automatisierte "Leichte Sprache" (Default-On):** Jeder neu erstellte Text oder Job wird von der Sprachmodell-Unterstützung standardmäßig und vollautomatisch im Hintergrund in zertifizierte "Leichte Sprache" übersetzt. Der Mensch muss nicht aktiv werden, kann die Übersetzung aber bei Bedarf editieren oder deaktivieren.
*   **AGG-Checker:** Ein "digitaler Anwalt", der Jobtexte vor Veröffentlichung auf Gleichbehandlungsverstöße prüft.
*   **Tone of Voice Enforcement:** Das Modell kommuniziert stets im Einklang mit der festgelegten Corporate Identity.
*   **Prompt-Injection Protection:** Strikte Heuristik-Filter und XML-Sandboxing verhindern böswillige Manipulationen der Analyse-Engine durch Bewerber.

**Installation & Betrieb der Sprachmodell-Unterstützung:**
Das System ist darauf ausgelegt, autark zu laufen. Wir nutzen sichere, quelloffene und lokal lauffähige Sprachmodelle.
1. Installieren Sie die lokale Inferenz-Engine.
2. Das ATS verbindet sich ohne weitere Konfiguration direkt mit dem lokalen Dienst (Port `11434`). 
*Hinweis: Sollte der lokale Dienst (z.B. nach einem Server-Neustart) nicht erreichbar sein, greift SecurATS nahtlos auf einen sicheren Fallback-Mock zurück, sodass der Bewerberprozess niemals blockiert wird.*

**Entwickler-Modus (Developer Mode) & Telemetry:**
Über das Admin-Dashboard lässt sich jederzeit ein "Developer Mode" zuschalten. Ist dieser aktiviert, reichert das Audit-Log alle Events und Klicks (sowie API-Calls an die KI) zusätzlich mit tiefgehenden Performance-Metriken an (z.B. Ladezeiten und JS-Heap Size). So können UI-Lags oder fehlerhafte Agent-Verbindungen frühzeitig erkannt und präventiv gelöst werden.


### 4.7 Barrierefreiheit & Inklusion (Accessibility / WCAG)
*   **Echte Teilhabe (Default Inclusivity):** Durch die vollautomatisierte KI-Übersetzung in "Leichte Sprache" ist die Plattform ab dem ersten Tag für Menschen mit kognitiven Einschränkungen zugänglich.
*   **Accessibility-Widget:** Frontend-Integration für Kontrast-Umschaltung, Schriftvergrößerung und Lesefokus.
*   **Erzwungene Screenreader-Kompatibilität:** Das CMS (Puck-basierter Visual Builder) erzwingt bei Medien-Uploads Alt-Texte (Bildbeschreibungen für Blinde) und setzt semantisches HTML streng durch.
*   **Text-to-Speech:** Native Vorlesefunktion für Jobinserate direkt im Browser.

### 4.8 Hybrides CMS & Visual Page Builder (Puck)
*   **Drag-and-Drop Landingpages:** Ein voll integrierter visueller Editor (basiert auf dem React-Framework Puck) ermöglicht es HR-Mitarbeitern, Landingpages aus über 10 Premium-Komponenten (Hero-Banners, Accordions, Spacer) ohne Code-Kenntnisse zusammenzuklicken.
*   **Kontrollierte Design-Freiheit:** Nutzer können Textgrößen (H1, H2, Standard) und Farben anpassen, sind aber durch Dropdowns auf das strikte Corporate-Design beschränkt (kein "Design-Unfall" möglich).
*   **Recruiting-Spezifische Module:** Eigene dynamische Komponenten für *Ansprechpartner-Karten* (mit Telefon/E-Mail Umschalter), *Standort-Infos* und *Highlight-Jobkarten* mit Direktbewerbungs-Button.
*   **Globale Navigation & Footer:** Der Header und Footer der gesamten Plattform können dynamisch als JSON-Blöcke (Puck) über das CMS gepflegt werden, ohne dass ein Server-Neustart nötig ist.
*   **AI Co-Designer Readiness:** Durch die Speicherung des Layouts als maschinenlesbares JSON kann die lokale KI in Zukunft auf Zuruf komplette Seitenlayouts generieren ("Erstelle mir eine Landingpage für Pflegekräfte").
