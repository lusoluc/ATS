# SecurATS – North Star

> **Status: v0.3 – Fundament + Governance-Kern produktiv, Kanon-Fragen entschieden.**
> Dieses Dokument ist die eine Quelle der Wahrheit für *Wohin* und *Warum*.
> Es beschreibt Vision, Prinzipien, Zielarchitektur, den Qualitätsanspruch und
> eine priorisierte Roadmap. Die **taktische Detail-Historie** (jedes Release,
> jeder Migrationsschritt, jeder gefangene Bug) steht in `BUILD_PLAN.md`; der
> aktuelle **Lücken-Backlog** in `ROADMAP.md`. Alle fünf Kanon-Fragen aus
> Abschnitt 11 sind inzwischen entschieden. Offene *Produkt*-Entscheidungen
> (nicht Architektur) sind weiterhin markiert (🔶).

---

## 1. Vision & Why

**Vision (ein Satz):**
> **SecurATS ist das erste Enterprise-Bewerbermanagement mit integrierter lokaler KI,
> das den *gesamten* Recruiting-Prozess für *alle* Beteiligten – über beliebig viele
> Standorte und Tochtergesellschaften hinweg – vollständig on-premise / air-gapped
> abbildet: flexibel je Einheit und trotzdem verbindlich governed. So wird aus
> gesetzlichem Zwang (Datenschutz, Barrierefreiheit, Fairness) ein messbarer
> Wettbewerbsvorteil.
> Bewerbermanagement, vollständig in eigener Hand.**

*Drei Wertebenen, die die Vision zusammenhält:*
1. **Souveränität** – die Daten bleiben zu 100 % im Haus (on-prem, air-gap, lokale KI).
2. **Operative Exzellenz** – Effizienz, einfache Kommunikation und 360°-Überblick auf dem Niveau etablierter Cloud-ATS.
3. **Gelebte Governance** – ein System für viele Einheiten, jede mit eigenen Abläufen, alle unter denselben unumgehbaren Leitplanken.

**Das Warum (der Schmerz):**
Für hochregulierte Organisationen ist Cloud-Recruiting ein **dreifaches Risiko**:
- **Rechtsrisiko** – DSGVO-Bußgelder, Schrems II / US-Cloud-Abhängigkeit, kirchlicher Datenschutz.
- **Haftungsrisiko** – BFSG-Abmahnungen, AGG-Klagen, Equal-Pay-Klagen, HR-Pflichten des EU AI Act.
- **Souveränitätsverlust** – Schatten-IT, Abhängigkeit von SaaS-Abos, Datenabfluss.

SecurATS **dreht diesen Zwang um**: Wer Datensouveränität, Barrierefreiheit und
Fairness technisch garantiert, senkt Strafzahlungen gegen null, erschließt einen
größeren Talentpool und schützt sich vor Klagen – statt nur Kosten und Risiken zu
verwalten. Aus Compliance-Pflicht wird Rendite und Fachkräftesicherung.

**Warum jetzt (Regulierungswelle 2025–2026):**
- **BFSG** (seit 28.06.2025): barrierefreie Bewerbungsprozesse sind Pflicht (WCAG 2.1); Bußgelder bis 10.000 € plus Abmahnungen.
- **SGB IX § 154 (Ausgleichsabgabe):** bis 720 €/Monat je unbesetztem Pflichtplatz bei Nullbeschäftigung (Unternehmen ab 20 MA).
- **EU AI Act:** Human-in-the-Loop-Pflicht für HR-KI; keine intransparente Voll-Automatisierung von Personalentscheidungen.
- **Entgelttransparenz / Equal Pay (ab Juni 2026):** Gehaltsband-Überwachung gegen Lohnklagen.
- **DSGVO / Schrems II, DSG-EKD / KDG, DORA:** kein Datenabfluss, keine US-Cloud, minimierte Lieferketten-Risiken.

### 1.1 Was SecurATS ist – Funktionsumfang im Überblick

Damit der Umfang unmissverständlich ist (Ziel-Scope; der Bau-Status wird in der
Roadmap, Abschnitt 10, nachgehalten):

- **Ausschreibung & Reichweite:** Stellen-Editor mit zentralen Variablen, wiederverwendbare **Job-Vorlagen** (siehe Abschnitt 3.7), **Headcount je Stelle** (Mehrfachbedarf als eine Ausschreibung, automatische Ausblendung bei Vollbesetzung mit Banner statt Blockade), 1-Klick-Multiposting (StepStone, BA-XML/Arbeitsagentur, Google for Jobs), eigene Karriereseiten/Landingpages je Standort mit **Kampagnen-Trichter** (Aufrufe → Bewerbungen → Einladungen → Einstellungen).
- **CMS-Baukasten (Kern-Differenzierer):** Seiten und Landingpages werden aus zehn Block-Typen zusammengesetzt (Hero, Text, Checkliste/Benefits, Kennzahlen-Reihe, Zitat, aufklappbares FAQ, Bild, Ansprechperson, „Aktuelle Stellen" live, CTA) – Editor mit Live-Vorschau, kein HTML-Wissen nötig, Träger-Branding wirkt automatisch. Jede neue Seite zählt sich selbst und erscheint automatisch in der Analytics.
- **Recruiting-Kanäle & Kampagnen:** Kanal in Sekunden anlegen (Link + druckfertiger QR-Code), Kampagnenquelle überlebt die ganze Bewerbersitzung, **strukturierte Kampagnenkosten je Kanal** speisen direkt die Kennzahl „Kosten je Einstellung".
- **Bewerbermanagement:** digitale Bewerberakte, Kanban-Pipeline inkl. **Status „Eingestellt" mit Time-to-Fill** (Einstellungsdatum automatisch oder rückwirkend manuell, Korrektur ohne Datenverlust), ABC-/Scoring, Volltextsuche über Bewerbung & Anhänge, Talent-Pool, Sammel-Zu-/Absage.
- **Dynamische Bewerbungsformulare & Mindeststandards:** vier Fragetypen (Ja/Nein, Auswahl, Freitext, **Pflicht-Dokument** – z. B. Führerschein, Impfnachweis, Zertifikat) je Stelle oder als vererbter Mindeststandard je Jobfamilie; K.O.-Logik ausschließlich bei objektiv definierter erwarteter Antwort, sonst Formular-Fehler statt automatischer Absage. Pflege **per Formular-Builder ohne Technik-Vorwissen**, nicht per JSON.
- **Sichtungs-Gremium:** Personen-Liste mit sechsstufiger Vererbungsleiter (Stelle > Abteilung > Einrichtung > Standort > Jobfamilie > Organisation), Vertretung im Urlaubsfall greift automatisch, **konfigurierbares Quorum** (statt starrer absoluter Mehrheit) und **Abstimmungs-Frist mit Eskalations-Mail** bei Überschreitung.
- **Vorgeschalteter Stellenfreigabe-Prozess (optional, dann verbindlich) mit No-Code Routing-Matrix:** siehe eigener Abschnitt 3.9 – vom Personalbedarf über eine mehrstufige, konfigurierbare Genehmigungskette bis zur Freigabe der Ausschreibung, bevor überhaupt eine Anzeige online gehen darf.
- **Konfigurierbare Terminformate:** Gesprächsformate (Telefon, Video, vor Ort, Probearbeit, Assessment, eigene Formate) werden von HR selbst verwaltet, nicht im Code definiert; bestehende Termine behalten ihre Bezeichnung auch nach Änderungen.
- **Import mit manueller Spalten-Zuordnung:** CSV/XLSX-Import zeigt „Unsere Felder → Ihre Spalten" nach jedem Testlauf, Automatik-Erkennung ist korrigierbar, unerkannte Spalten werden benannt statt stillschweigend verworfen; Adressfeld verschlüsselt at-rest.
- **Kommunikation:** E-Mail-Vorlagen mit eigenen Absendern direkt aus dem System, verschlüsselte interne Kommentare, passwortloses Magic-Link-Kandidatenportal, Terminplanung – ohne externen Cloud-Zwang.
- **Lokale KI (Zero-Data-Transfer):** CV-/Kompetenz-Parsing, Vorsortierung/Scoring, AGG-Check, „Leichte Sprache", Formulierungs- und Antwortvorschläge – stets Human-in-the-Loop.
- **Automatisiertes Auslesen, Bewerten & Matching:** Lebensläufe, Anschreiben und Zeugnisse werden automatisch ausgelesen und gegen das **Stellenprofil** (Muss-/Kann-Kriterien) abgeglichen; nachvollziehbarer Score mit Begründung (was erfüllt, was fehlt).
- **Konfigurierbare Prozess-Automatisierung (je Stelle, sehr individuell):** Vorqualifizierung/Priorisierung für den Recruiter, automatische Nachforderung fehlender Dokumente/Zertifikate/Angaben, automatische Absage **nur** bei objektiven K.-o.-Kriterien – alles regel-/schwellenbasiert, protokolliert, pro Stelle abschaltbar.
- **Bedienung/UX:** intuitiv für Gelegenheitsnutzer, Profi-Werkzeuge (Shortcuts, Bulk-Aktionen, Split-Screen-Vergleich, gespeicherte Ansichten, Workflow-Designer) für Vielnutzer; rollen-adaptive Oberfläche.
- **Prozess & Governance:** frei definierbare Workflows je Standort/Kategorie/Einrichtung, erzwungene Pflicht-Gates (Betriebsrat, AGG, DSGVO-Einwilligung, Stellenfreigabe), revisionssicheres Audit-Log, automatische Retention/Löschung, Equal-Pay-Gehaltsband.
- **Barrierefreiheit:** BFSG/WCAG-Panel (Legasthenie-Schrift, Kontrast, Fokusmodus, Lese-Lineal, Vorlesefunktion) plus „Leichte Sprache".
- **Rollen, Rechte & Multi-Standort:** RBAC + BOLA-Silos, Delegationen, Mandanten/Töchter – zentral steuern *und* lokal anpassen.
- **Reporting & KPIs:** Erfolgs-/Insight-Dashboard (siehe Abschnitt 4) – Time-to-Hire, **Time-to-Fill & Kosten je Einstellung**, Funnel-Abbrüche, Quellen(-qualität), Standort-Vergleich, KI-Analyst & Prognosen, Fairness-/Inklusions-/Compliance-Cockpits, Export nach Excel/BI.
- **Schnittstellen:** SAP-SuccessFactors-Bridge, HR-BA-XML, StepStone; OData/Excel-Export.
- **Betrieb & Sicherheit:** 100 % on-prem / air-gapped (Docker), PII-Verschlüsselung at-rest, TLS/HSTS, Backup-Vault, Disaster Recovery – Open Source.

> **Zwei vollständige Demo-Welten** belegen die Mandantenfähigkeit anhand
> desselben Codes: eine Pflege-/Sozialträger-Welt und eine Banking-Welt
> (Corporate-Design, Kategorien-Hierarchie, drei Prozess-Profile
> Standard/Tech/Executive, eigene Routing-Matrix-Regeln) – identisches
> Produkt, nur andere Konfiguration.

---

## 2. Für wen – und wer konkret profitiert

**Zielbranchen** (Cloud-ATS ist ein K.O.-Kriterium): Gesundheits- & Sozialwesen
(Art. 9 DSGVO, DSG-EKD/KDG), öffentlicher Sektor / Landesnetze (Schrems II),
KRITIS & Finanzsektor (DORA) – sowie **jedes Unternehmen ab 20 MA** mit
BFSG- und Ausgleichsabgabe-Pflicht.

**Leitprinzip: Jede einzelne Rolle im Bewerbungsprozess gewinnt – und dadurch am
Ende das Unternehmen.** SecurATS ist kein reines HR-Tool, sondern verbessert das
Erlebnis und senkt das Risiko für *alle* Beteiligten:

| Beteiligte:r | Konkreter Nutzen |
|---|---|
| **Bewerber:in** (inkl. Menschen mit Behinderung / Neurodiversität) | Barrierefreies Bewerben (Legasthenie-Schrift, Kontrastmodus, ADHS-Fokusmodus, Lese-Lineal, Text-to-Speech); bias-freie, „farbblinde" KI-Bewertung; die eigenen Daten verlassen nie das Haus + automatische Löschung; Magic-Link-Statusportal ohne Passworthürde → **würdevoller, fairer, zugänglicher Prozess**. |
| **Recruiter:in / HR-Sachbearbeitung** | Ein Klick veröffentlicht zu StepStone, BA-XML (Arbeitsagentur) und Google for Jobs; zentrale Variablen statt Template-Pflege in hunderten Vorlagen; Kanban + status-gekoppelte Automatisierung; AGG-Checker & „Leichte Sprache" verhindern Abmahnungen → **weniger Handarbeit, weniger Rechtsrisiko, kürzere Time-to-Hire**. |
| **Fachabteilung / Hiring Manager** | Sicherer Einmal-Passwort-Zugriff auf genau die eigenen Akten (BOLA-Standort-/Abteilungssilos), interne Kommentare & Freigaben direkt im Board → **schnelle, sichere Mitbeurteilung ohne E-Mail-Anhänge und Schatten-IT**. |
| **Bereichsleitung / Geschäftsführung / Vorstand & Aufsichtsrat** | Personalbedarf strukturiert statt per Mail; No-Code Routing-Matrix stellt automatisch die passende Genehmigungskette und Zusatzfragen bereit; nur die jeweils fällige Rolle entscheidet, alles unveränderlich protokolliert → **Neueinstellungen nachvollziehbar und verbindlich genehmigt, ohne jede Organisation ins selbe starre Korsett zu zwingen**. |
| **Betriebsrat / Mitbestimmung** | Die Prozess-Engine erzwingt z.B. die Betriebsratsanhörung als Workflow-Gate mit digitaler Freigabe, bevor es weitergeht → **Mitbestimmungsrechte technisch garantiert und revisionssicher dokumentiert**. |
| **Schwerbehindertenvertretung / Inklusionsbeauftragte** | Barrierefreiheit steigert die Bewerbungs-Conversion nachweislich um +37 % und erreicht mehr qualifizierte schwerbehinderte Talente → **gesetzliche Quote wird erfüllbar und messbar**. |
| **Datenschutz / Compliance / Legal** | Air-Gap, PII-Verschlüsselung at-rest, revisionssicheres Audit-Log jedes sensiblen Zugriffs, automatische Retention/Löschung, Human-in-the-Loop, Equal-Pay-Gehaltsband → **nachweisbare Compliance statt bloßer Behauptung**. |
| **IT / CISO / KRITIS-Betrieb** | 100 % on-prem / air-gapped, Zero-Downtime-Deployments, Backup-Vault, Disaster Recovery mit RTO < 5 Min, keine SaaS-Lieferkette → **Souveränität, Resilienz und minimiertes Drittparteienrisiko (DORA)**. |
| **Geschäftsführung / CFO – das Unternehmen** | Ausgleichsabgabe gegen null (bis ~43.200 €/Jahr bei 140 MA), +37 % qualifizierte Bewerbungen, Haftungsschutz Equal Pay, keine DSGVO-/BFSG-Bußgelder, kein SaaS-Abo → **aus Pflicht wird Rendite und Fachkräftesicherung**. |

> Diese Nutzen-Kette ist bewusst als *gemeinsamer* Gewinn formuliert: Der Vorteil
> für die schwächste Partei (z.B. eine Bewerberin mit Sehbehinderung) ist zugleich
> der wirtschaftliche Vorteil des Unternehmens (mehr Bewerbungen, weniger Abgabe).

### 2.1 Personas – so findet sich jede:r wieder

Die Tabelle oben ist die Kurzreferenz. Damit sich **jede reale Rolle** im System
wiedererkennt, hier die konkreten Personas (Namen fiktiv, Situationen realistisch
für regulierte Mehr-Standort-Organisationen). Jede ist an tatsächliche System-
Fähigkeiten geknüpft: Rollen-/Rechte-Silos (BOLA), Delegationen, Workflow-Gates,
Magic-Link-Portal, Audit-Log, KPIs, lokale KI.

**HR & Recruiting**
- **Sandra Berg – zentrale Recruiterin** *(Konzern-HR einer Diakonie mit 6 Töchtern: Kliniken, Pflegeheime, Kita).* **Schmerz:** jongliert Stellen für alle Standorte mit je eigenen Anforderungen – kein Bock auf 6 Systeme und Excel-Wildwuchs. **→ SecurATS:** eine Oberfläche, standortspezifische Workflows & Variablen, 1-Klick-Multiposting je Tochter, zentrale Vorlagen, Karriereseiten aus dem CMS-Baukasten ohne HTML, Recruiting-Kanäle mit QR-Code und Kosten-Tracking je Kampagne, Mehrfachbedarf als eine Ausschreibung (Headcount). **Gewinn:** steuert alles zentral, *ohne* lokale Eigenheiten platt zu machen – und sieht live, welcher Kanal welche Einstellung zu welchem Preis gebracht hat.
- **Tobias Klein – dezentraler Recruiter** *(nur eine Tochtergesellschaft).* **Schmerz:** will ausschließlich *seine* Bewerber sehen und seinen eigenen Ablauf. **→ SecurATS:** BOLA-Silo zeigt exakt seinen Standort; eigener Workflow – doch Konzern-Pflichtschritte greifen automatisch. **Gewinn:** volle Autonomie im erlaubten Rahmen.
- **Petra Wolf – HR-Sachbearbeitung im geteilten Team.** **Schmerz:** Wer bearbeitet welche Bewerbung? Keine Doppelarbeit, saubere Vertretung im Urlaub. **→ SecurATS:** Delegationen, Rollen/Views, Aufgaben & To-dos, interne Kommentare – jede Aktion landet im Audit-Log. **Gewinn:** klare Arbeitsteilung, lückenlos und rechtssicher dokumentiert.
- **Dr. Anja Reuter – HR-Leiterin & Prozess-Owner (Admin).** **Schmerz:** will konzernweit standardisieren, aber lokale Freiheit lassen und Compliance *erzwingen*. **→ SecurATS:** Workflow-Designer, zentrale Variablen, KI-Leitplanken, nicht abschaltbare Pflicht-Gates, **No-Code Routing-Matrix für die vorgeschaltete Stellenfreigabe** (welcher Bereich braucht welches Formular und welche Kette), konfigurierbares Gremien-Quorum mit Frist, Fragen-Builder ohne JSON. **Gewinn:** „Flexibel, aber governed" liegt in ihrer Hand – bis auf die Ebene einzelner Abteilungen, ohne einen Entwickler zu brauchen.
- **Ulrike Mayr – Ausbildungsleitung / Azubi-Recruiting.** **Schmerz:** hunderte Schülerbewerbungen, Kennenlern-Events, Fristen. **→ SecurATS:** eigener Azubi-Workflow, Event-Planung, Talent-Pool, automatische Erinnerungen. **Gewinn:** Überblick über den ganzen Jahrgang, nichts fällt durchs Raster.
- **Fatima El-Amrani – Koordinatorin Praktikum & Werkstudierende** *(Hochschul-Kooperationen, mehrere Fachbereiche).* **Schmerz:** viele kurzfristige, saisonale Stellen mit schnellem Durchlauf – der volle Recruiting-Prozess ist dafür zu schwerfällig, und gute Kräfte sollen später übernommen werden. **→ SecurATS:** schlanker Kurz-Workflow für Praktika/Werkstudierende, Hochschulmessen als Events, Talent-Pool für die spätere Festeinstellung, schnelle Zu-/Absagen. **Gewinn:** viele kurze Prozesse souverän gesteuert – und der Nachwuchs-Pool wächst systematisch.

**Fachbereich & Hiring**
- **Prof. Dr. Martin Höfer – Chefarzt (Hiring Manager).** **Schmerz:** keine Zeit fürs Tool, will nur „seine" Fälle, hasst PDF-Anhänge per Mail. **→ SecurATS:** sicherer Einmal-Zugriff auf genau seine Akten (BOLA), Bewertung & Kommentar direkt im Board, mobil. **Gewinn:** schnelle Mitbeurteilung ohne Schatten-IT.
- **Melanie Dorn – Pflegedienstleitung.** **Schmerz:** meldet Personalbedarf per Zettel/Mail → Verzug, Rückfragen verpuffen; bei mehrstufiger Genehmigung verliert sie den Überblick, wo der Antrag gerade hängt. **→ SecurATS:** digitaler Personalbedarf mit dynamischem Formular je Bereich, sichtbarer Stufenleiste (wer hat schon entschieden, wer fehlt), automatischer Mail bei jeder Entscheidung und einfacher Nachbesserung bei Rückgabe. **Gewinn:** offene Stellen schneller besetzt, nie wieder „wurde das eigentlich schon genehmigt?".
- **Jens Hartmann – IT-Teamlead als Fachgutachter.** **Schmerz:** soll Coding-Skills bewerten, bekommt aber nur Papierlebensläufe. **→ SecurATS:** KI-gestützte Kompetenz-Extraktion + strukturierte Bewertungsfelder, Vergleich mehrerer Kandidaten. **Gewinn:** fundierte fachliche Einschätzung in Minuten.
- **Nina Berger – Teammitglied im Auswahlteam (Interviewerin).** **Schmerz:** sitzt in Gesprächen mit, gibt Feedback aber mündlich „später mal" weiter – bei der Entscheidung ist es dann vergessen oder verwässert, Bedenken verpuffen. **→ SecurATS:** automatische Bitte um Feedback direkt nach dem Gespräch, Bewertung in unter einer Minute per Prozent-Regler, eigenes Bedenken-Feld, das bei Folgerunde und finaler Entscheidung sichtbar ist und beim Einstellen warnt. **Gewinn:** jede Einschätzung zählt – Entscheidungen stehen auf dokumentiertem Feedback statt auf Flurfunk.

**Fachbereich & Hiring (Stellenfreigabe)**
- **Rasmus Voigt – Bereichsleiter IT** *(Antragsteller UND erste Genehmiger-Instanz).* **Schmerz:** Neuanstellungsanfragen kamen per Mail ohne einheitliche Angaben, ohne Nachverfolgung – „wurde das eigentlich schon genehmigt?" war Dauerfrage. **→ SecurATS:** No-Code Routing-Matrix stellt automatisch die passenden Zusatzfragen (Tech-Stack, Budgetherkunft) und die richtige Genehmigungskette bereit; er entscheidet nur, wenn seine Stufe wirklich fällig ist. **Gewinn:** strukturierte Anträge statt E-Mail-Chaos, klare Verantwortung je Kettenstufe.

**Governance & Mitbestimmung**
- **Jürgen Faber – Betriebsratsvorsitzender.** **Schmerz:** wird spät/informell eingebunden (§ 99 BetrVG), nichts ist sauber dokumentiert. **→ SecurATS:** Anhörung als **blockierendes** Workflow-Gate mit digitaler Freigabe, alles im Audit-Log. **Gewinn:** Mitbestimmung technisch garantiert und jederzeit belegbar.
- **Katrin Sommer – Schwerbehindertenvertretung / Inklusionsbeauftragte.** **Schmerz:** erfährt zu spät von einschlägigen Bewerbungen (§ 164 SGB IX); klassische Formulare schrecken ab. **→ SecurATS:** automatische Einbindung, barrierefreier Prozess erhöht Bewerbungen, Nachweisführung. **Gewinn:** gesetzlicher Auftrag wird erfüllbar – und die Ausgleichsabgabe sinkt.
- **Michael Braun – Datenschutzbeauftragter (DSB).** **Schmerz:** Cloud-Tools = Schrems-II-Risiko, keine belastbaren Löschnachweise, kirchlicher Datenschutz (DSG-EKD/KDG). **→ SecurATS:** Air-Gap, PII-Verschlüsselung, automatische Retention/Löschung, revisionssicheres Audit. **Gewinn:** nachweisbare Compliance statt Bauchgefühl.

**IT & Sicherheit**
- **Sven Ostermann – IT-Administrator / Betrieb.** **Schmerz:** SaaS entzieht Kontrolle, Update-Überraschungen, unklare Backups. **→ SecurATS:** On-Prem-Deploy (Docker), air-gap-fähig, Backup-Vault, Disaster Recovery (RTO < 5 Min). **Gewinn:** volle Kontrolle, planbarer Betrieb.
- **Nadine Schulz – CISO (KRITIS/DORA).** **Schmerz:** jede Drittpartei ist Angriffsfläche und Lieferkettenrisiko. **→ SecurATS:** keine SaaS-Kette, alles im eigenen Netz, vollständiges Audit. **Gewinn:** Drittparteienrisiko und Angriffsfläche minimiert.

**Leitung**
- **Christian Vogt – Geschäftsführer.** **Schmerz:** kein Durchblick über Töchter und Standorte; Reports dauern Tage. **→ SecurATS:** Live-Dashboard über alle Einheiten – Time-to-Hire, **Time-to-Fill und Kosten je Einstellung aus echten Einstellungsereignissen**, Funnel, Kanal-Erfolg, offene Stellen; Export auf Knopfdruck. **Gewinn:** Entscheidungen auf Basis aktueller Zahlen, in Minuten statt Wochen.
- **Birgit Lang – CFO.** **Schmerz:** Pro-Kopf-SaaS-Abos, drohende Ausgleichsabgabe, Bußgeldrisiko. **→ SecurATS:** keine Pro-Sitz-Kosten, sinkende Abgabe, Haftungsschutz (Equal Pay/BFSG). **Gewinn:** aus Compliance-Pflicht wird ein Rendite-Hebel.
- **Holger Rittmann – Standortleiter (ohne HR-Funktion)** *(führt eine Einrichtung/ein Werk, kein HR-Personal vor Ort).* **Schmerz:** verantwortlich für die Besetzung seines Standorts, wird aber bisher nur per Mail aus der Zentrale informiert – will steuern, ohne HR-Experte werden zu müssen. **→ SecurATS:** standort-gescoptes Dashboard (BOLA) mit offenen Stellen, Pipeline-Status und genau seinen Freigaben – ohne HR-Fachwissen bedienbar; die Pflicht-Gates greifen trotzdem automatisch. **Gewinn:** bleibt jederzeit im Bild und steuert sein Standort-Recruiting mit, ohne HR-Arbeit zu übernehmen.
- **Dr. Elke Winter – Vorstandsmitglied / Aufsichtsratsmandat** *(finale Freigabe-Instanz bei strategisch wichtigen Neueinstellungen).* **Schmerz:** Personalanfragen erreichten sie unstrukturiert per Mail-Anhang, ohne Kontext der vorherigen Genehmigungsstufen – Entscheidungen fühlten sich blind an. **→ SecurATS:** mobil bedienbare Entscheidungsseite mit allen vorherigen Genehmigungen, Kommentaren und der Begründung sichtbar, bevor sie unterschreibt; unveränderliches Audit-Log für ihre Sorgfaltspflicht. **Gewinn:** fundierte Entscheidung in Minuten statt E-Mail-Ketten – überall dort, wo die Sitzung gerade tagt.

**Bewerbende**
- **Leon Krüger – Bewerber mit Legasthenie & ADHS.** **Schmerz:** Standard-Bewerbungsformulare sind eine echte Hürde. **→ SecurATS:** Barrierefreiheits-Panel (Legasthenie-Schrift, Fokusmodus, Lese-Lineal, Vorlesefunktion), Leichte Sprache, passwortloses Magic-Link-Statusportal. **Gewinn:** kann sich überhaupt fair und eigenständig bewerben.
- **Aylin Yıldız – datenschutzbewusste Bewerberin.** **Schmerz:** „Was passiert eigentlich mit meinen Daten?" **→ SecurATS:** Daten verlassen nie das Haus, automatische Löschung nach Frist, jederzeit transparenter Status. **Gewinn:** Vertrauen – und ein würdevoller Prozess.
- **Robert Itzek – interner Bewerber.** **Schmerz:** möchte sich intern bewerben, ohne dass die aktuelle Führungskraft es vorzeitig erfährt. **→ SecurATS:** Vertraulichkeits-Silo (BOLA) trennt die interne Bewerbung von der Fachabteilung. **Gewinn:** interne Weiterentwicklung ohne Angst vor Nachteilen.
- **Marek Nowak – Bewerber für einen Niedriglohn-Job (Lagerhelfer/Reinigung), mobil-only, wenig Deutsch.** **Schmerz:** lange Formulare, PDF-Zwang und komplizierte Portale sind eine Hürde. **→ SecurATS:** ultrakurzer, mobiler Bewerbungsflow, Foto-Upload statt PDF, Leichte Sprache, passwortloses Status-Portal, schnelle Rückmeldung. **Gewinn:** kann sich in Minuten fair bewerben.
- **Dr. med. Katharina Vossberg – Fachärztin für Psychiatrie & Psychotherapie (hochwertige Position).** **Schmerz:** erwartet einen diskreten, professionellen Prozess und muss viele Nachweise (Approbation, Facharzt-Anerkennung, Zeugnisse) einreichen. **→ SecurATS:** vertrauliche Bewerbung (kein Leak zum aktuellen Arbeitgeber), Multi-Nachweis-Upload, KI-gestützte Qualifikations­erfassung, persönlicher Ansprechpartner, transparenter Status, Human-in-the-Loop statt Blackbox-Absage. **Gewinn:** ein Prozess auf Augenhöhe mit dem Anspruch der Position.

> **Prinzip dahinter:** Jede Persona sieht **genau ihren** Ausschnitt, arbeitet in
> **ihrem** Ablauf – und trotzdem greifen für alle dieselben verbindlichen Leitplanken.
> Das ist der Kern von „Flexibel, aber governed" (Prinzip 8), gelebt pro Rolle.

---

## 3. Warum eine Plattform – operativer Nutzen (jenseits der Regularien)

Compliance ist der **Eintrittspreis** für regulierte Branchen – aber nicht der
Grund, warum ein Team die Software jeden Tag gerne benutzt. Der tägliche Wert ist
operativ. Hier muss SecurATS mit etablierten ATS (Benchmark: **dVinci** – Cloud-SaaS,
ISO 27001, RZ Hamburg, Testsieger, ab ~257 €/Monat) mindestens gleichziehen und
durch **lokale KI + Datensouveränität** überholen.

### 3.1 Effizienzgewinn – aus Tagen werden Minuten
- Stelle **einmal** schreiben → 1-Klick-Multiposting (StepStone, BA-XML, Google for Jobs).
- **Zentrale Variablen:** eine Änderung wirkt sofort in allen Anzeigen, E-Mails und Landingpages.
- Digitale Bewerberakte, Kanban, status-gekoppelte Automatisierung, Fristen/To-do-Erinnerungen.
- Sammel-Aktion „einen einstellen, Rest absagen" inkl. Talent-Pool.
- **Lokale KI:** Anti-Bias-CV-Parsing extrahiert Kompetenzen automatisch, Vorsortierung/Scoring,
  AGG-Check vor Veröffentlichung, „Leichte Sprache" auf Knopfdruck – **ohne dass ein Byte das Haus verlässt**.
  → HR gewinnt Zeit für die *Auswahl* statt für Verwaltung.

### 3.2 Einfache Kommunikation – mit Bewerbern und intern
- Eigene Absenderadressen + Korrespondenz-Vorlagen direkt aus dem System (Schluss mit dem E-Mail-Postfach-Chaos).
- Verschlüsselte interne Kommentare; Fachbereichs-Freigaben direkt im Board.
- **Magic-Link-Kandidatenportal:** transparenter Status, Terminwahl, Rückfragen – passwortlos und barrierefrei.
- **Ohne externe Abhängigkeit:** kein Zwang zu Microsoft Teams/Calendly/Cloud – Kommunikation und
  Terminplanung laufen lokal (air-gap-fähig).
- **Lokale KI als Assistenz:** Vorschläge für Antwort-/Absagetexte, Übersetzung in Leichte Sprache,
  AGG-neutrale Formulierungen – der Mensch entscheidet (EU-AI-Act Human-in-the-Loop).

### 3.3 360°-Blick – der ganze Prozess in einer Ansicht
- Durchgehende Akte von **Personalbedarf** (Fachbereich meldet digital) → Multiposting → Screening →
  Interview → Freigabe → Einstellung/SAP-Export.
- Rollen-/Rechte-Silos (BOLA): jede:r sieht genau den eigenen Ausschnitt.
- Reporting/KPIs: Kanal-Erfolg, Time-to-Hire, Funnel-Abbrüche; Export für BI/Excel.
- Revisionssicheres Audit-Log über den gesamten Verlauf.
- **Lokale KI als Kopilot über den 360°-Daten:** erkennt Muster (z.B. wo Kandidaten abspringen)
  und macht Vorschläge – vollständig auf den eigenen Servern.

### 3.4 Flexibilität ohne Kontrollverlust – zentral steuern, lokal anpassen
Der vielleicht eigentliche USP: SecurATS ist **hochflexibel, ohne die Prozess-
sicherheit aufzugeben**. Starre Standard-ATS pressen alle Standorte in ein Korsett;
rein „flexible" Tools lassen dafür die Governance schleifen. SecurATS verbindet beides:
- **Lokale Individualität:** Jeder Standort / jede Einrichtung bildet eigene Recruiting-
  Phasen, Workflows, Rollen, Variablen und sogar eigene Landingpages ab. Die Prozess-Engine
  löst automatisch den **spezifischsten** Workflow je Job / Standort / Kategorie / Einrichtung auf.
- **Verbindliche Governance:** Gleichzeitig bleiben Pflicht-Schritte **systemseitig erzwungen** –
  z.B. Betriebsratsanhörung als blockierendes Gate, AGG-Check vor Veröffentlichung,
  DSGVO-Einwilligung, revisionssichere Freigaben. Diese lassen sich lokal **nicht wegkonfigurieren**.
- **Zentral + lokal zugleich:** Globale Vorgaben/Variablen (und KI-Leitplanken wie AGG-Prompt,
  Tonalität, Schwellenwerte) werden einmal zentral gesetzt und wirken überall; lokale Overrides
  bleiben möglich, **wo sie erlaubt sind**.
- **Ergebnis:** Konzern-Konsistenz und Rechtssicherheit **und** Respekt für die realen
  Gegebenheiten vor Ort – kein Entweder-oder.

> Anders gesagt: Die Klinik in Berlin, das Pflegeheim auf dem Land und die Zentrale arbeiten im
> **selben** System nach ihren je **eigenen** Regeln – aber niemand kann eine gesetzlich oder
> betrieblich vorgeschriebene Station überspringen.

### 3.5 KI-Matching & konfigurierbare Automatisierung – individuell pro Stelle
Der Kern-Effizienzhebel: Bewerbungen werden **automatisch ausgelesen, bewertet und
gegen das Stellenprofil abgeglichen** – und daran lassen sich pro Stelle Prozesse
knüpfen, so individuell wie nötig.
- **Auslesen:** Lebenslauf, Anschreiben und Zeugnisse werden lokal geparst –
  Kompetenzen, Abschlüsse, Zertifikate, Berufserfahrung, Sprachen.
- **Matching gegen das Stellenprofil:** Abgleich mit den definierten **Muss-/Kann-Kriterien**;
  Ergebnis ist ein **nachvollziehbarer Score mit Begründung** (welche Anforderung erfüllt,
  welche offen ist) – keine Blackbox.
- **Hinterlegbare Automatisierungen (bei Bedarf, regelbasiert):**
  - **Vorqualifizierung für den Recruiter** – automatische Priorisierung/Markierung der
    besten Treffer inkl. KI-Begründung; der Mensch entscheidet.
  - **Automatische Rückfrage bei Lücken** – fehlt ein Pflichtdokument, ein Zertifikat oder
    eine Pflichtangabe, versendet das System automatisch eine barrierefreie Nachforderung
    über das Kandidatenportal.
  - **Automatische Absage – ausschließlich bei objektiven K.-o.-Kriterien** (z.B. zwingend
    erforderliche Berufszulassung/Fahrerlaubnis fehlt), fair formuliert und protokolliert.
- **Guardrails (Prinzip 8 + EU AI Act):** Die KI **bewertet und assistiert**, aber ablehnende
  Entscheidungen auf Basis *subjektiver* Scores bleiben **Human-in-the-Loop**; AGG-„Farben-
  blindheit" gilt durchgängig; jede automatische Aktion ist im Audit-Log nachvollziehbar und
  **pro Stelle abschaltbar**. Automatisierung spart Zeit, ohne Fairness oder Rechtssicherheit
  aufzugeben.

### 3.6 Bedienung: intuitiv für alle, mächtig für Profis
- **Intuitiv als Standard:** aufgeräumte Oberfläche, sinnvolle Voreinstellungen, geführte
  Abläufe – auch Gelegenheitsnutzer (Chefarzt, Standortleiter) kommen **ohne Schulung** zurecht.
- **Profi-Werkzeuge, wo sie gebraucht werden** (progressive disclosure): Tastatur-Shortcuts,
  Bulk-/Serien-Aktionen, Split-Screen-Dokumentenvergleich, Volltext- & Filtersuche, gespeicherte
  Ansichten, Vorlagen-/Variablen-Bibliothek, Drag-&-Drop-Kanban, Workflow-Designer.
- **Rollen-adaptiv:** jede Persona sieht genau die Werkzeuge ihres Jobs – der Recruiter das volle
  Cockpit, der Fachexperte nur Bewertung & Kommentar. Weniger Ballast, weniger Klicks.
- **Verschlankung an jeder Station:** kontextnahe Helfer, die den konkreten Schritt kürzen –
  KI-Textvorschlag beim Absagen, Ein-Klick-Nachforderung, Sammel-Statuswechsel, Terminvorschlag.
- **Anspruch:** Bedienkomfort auf dem Niveau der etablierten Marktführer (siehe 3.8) – Usability
  ist Teil der **Definition of Done**, nicht Kür.

### 3.7 Job-Vorlagen – nie wieder bei null anfangen
Wiederkehrende Stellen (z.B. „Krankenpfleger:in – Stationsleitung") sollen beim 2., 10.
oder 100. Mal – und auch in einer anderen Tochter – von einem starken Startpunkt ausgehen
statt vom leeren Blatt. Die Kunst dabei: **Wiederverwendung ohne Verlust der lokalen Stimme.**

**Der Kniff – Inhalt und Tonalität trennen:**
- **Vorlage = strukturierter Kern:** Aufgaben, Anforderungen (Muss/Kann), Screening-Fragen,
  Benefits-Bausteine – das, was über Abteilungen und Töchter hinweg wiederverwendbar ist.
- **Tonalität & lokale Variablen = automatisches Overlay:** Abteilungs-/Kategorie-Tonalität,
  Standort-Daten (Ansprechpartner, Adresse, CI) und rechtliche Textbausteine greifen **beim Verwenden** –
  nicht in der Vorlage eingebacken. So bleibt „Stationsleitung" inhaltlich konsistent, klingt aber in
  Tochter A anders als in Tochter B.
- **Lokale KI als Veredler:** re-formuliert den Kern automatisch in die Ziel-Tonalität der
  Abteilung/Kategorie (z.B. „Du" vs. „Sie", nüchtern vs. herzlich) – inkl. optionalem AGG-Check und
  Leichte-Sprache-Variante. Der Mensch feilt nur noch am Delta.

**Der Prozess – schlau, aber kinderleicht (wenige Klicks):**
1. **Vorschlag statt leeres Blatt:** Beim Anlegen schlägt das System passende Vorlagen vor
   (nach Jobkategorie/Titel-Ähnlichkeit), inkl. „zuletzt in deiner Tochter genutzt" und –
   via Analytics (Abschnitt 4) – „**beste Performer**".
2. **1-Klick-Vorbefüllung:** Kern übernommen, Tonalität + Standort-Variablen automatisch angewandt.
3. **Nur das Delta anpassen.**
4. **Veröffentlichen & optional als Vorlage sichern:** Verbesserungen fließen zurück in die Bibliothek.

**Governance & Qualität (Prinzip 8):**
- **Drei Ebenen:** persönliche Entwürfe · Abteilungs-/Standort-Vorlagen · konzernweite **Master-Vorlagen**
  (kuratiert/freigegeben) – Sichtbarkeit über Rollen/BOLA, damit die Bibliothek nicht wuchert.
- **Versionierung:** Änderungen bleiben nachvollziehbar; Master-Updates können abgeleiteten Stellen
  als Vorschlag angeboten werden.
- **Selbstlernend:** Die KI erkennt, welche Formulierungen mehr qualifizierte Bewerbungen bringen,
  und schlägt Vorlagen-Verbesserungen vor – Best Practice einer Tochter wird für alle nutzbar.

> Ergebnis: Konzernweiter Wissenstransfer bei jeder Ausschreibung – schneller Start, konsistente
> Qualität und trotzdem die je eigene Stimme jeder Abteilung.

### 3.8 Der Unterschied zu etablierten Cloud-ATS
Anbieter wie dVinci liefern Effizienz, Kommunikation und Reporting bereits stark – aber als
**Cloud-SaaS** (Pro-Kopf-Abo, Rechenzentrum beim Anbieter, KI extern bzw. limitiert). SecurATS
liefert denselben operativen Komfort **on-premise / air-gapped, mit aktiver lokaler KI und als
Open Source** – kein Datenabfluss, kein Vendor-Lock-in, keine Pro-Sitz-Kosten.

> **Die Pointe:** Regularien sagen „du *darfst* keine Cloud". SecurATS sagt: „du *brauchst* auch
> keine – um komfortabel, schnell und vernetzt zu recruiten." Genau die regulierten Kunden, die
> Cloud-ATS eigentlich nicht nutzen dürften (Diakonie, Kliniken, KRITIS – teils sogar heutige
> dVinci-Referenzen), bekommen so erstmals vollen Komfort **ohne** den Compliance-Bruch.

**Ehrliche Einordnung:** Etablierte Wettbewerber punkten mit jahrelang gereiftem Bedienkomfort,
Support und Ökosystem (Job-Board-Integrationen, Onboarding-Module). Das ist der Maßstab, den
SecurATS im Bedienerlebnis erreichen muss – der Hebel, mit dem SecurATS gewinnt, ist die
Kombination aus **Souveränität + lokaler KI + Open Source + planbaren Kosten**.

### 3.9 Vorgeschalteter Stellenfreigabe-Prozess & No-Code Routing-Matrix

Bevor eine Stelle überhaupt beworben werden darf, braucht sie in vielen
Organisationen eine **interne Genehmigung des Bedarfs** – von der
Teamleitung über Bereichsleitung und Geschäftsführung bis zum Aufsichtsrat.
Weil SecurATS eine Plattform für **verschiedenste Unternehmensorganisationen**
ist, ist dieser Prozess **optional je Installation, aber wenn aktiviert
verbindlich** – kein Sonderfall, sondern dieselbe Governance-Haltung wie bei
jedem anderen Pflicht-Gate (Prinzip 8).

- **Antrag statt Zuruf:** Jede interne Rolle meldet Personalbedarf strukturiert
  (Titel, Anzahl, Einrichtung/Abteilung/Kategorie, Begründung) statt per Mail
  oder Zettel.
- **No-Code Routing-Matrix (HR-Admin, ohne Programmieraufwand):** Regeln
  verknüpfen einen Geltungsbereich (Einrichtung × Abteilung × Job-Kategorie,
  mit Wildcards für „alle") mit einem **dynamischen Bedarfsformular**
  (frei definierbare Zusatzfragen) und einer **Genehmigungskette**. Kollidieren
  Regeln, gewinnt die spezifischste (exakter Match vor Teil-Match vor
  globalem Fallback) – nach demselben Vererbungsprinzip wie das
  Sichtungs-Gremium (Abschnitt 4 der Architektur-Muster, siehe auch
  `AI_DEV_GUIDELINES.md`).
- **Pflicht je Regel:** Eine Regel kann für ihren Geltungsbereich verbindlich
  sein, **auch ohne globalen Schalter** – ein Konzern kann den Prozess für die
  IT-Abteilung verpflichtend machen und für die Filiale optional lassen.
- **Sequenzielle Kette mit Nachbesserung:** Nur die Rolle der jeweils fälligen
  Stufe entscheidet; drei Ausgänge (Genehmigen, Zur Nachbesserung mit
  Neustart der Kette, endgültig Ablehnen); Antragsteller wird bei jedem
  finalen Schritt informiert.
- **Verbindlich heißt verbindlich – an allen drei Schaltpunkten:** Der
  Stellen-Wizard, der Schnell-Toggle **und die finale Job-Freigabe selbst**
  verweigern die Veröffentlichung ohne genehmigten Bedarf. Ein genehmigter
  Bedarf lässt sich mit einem Klick in eine Ausschreibung überführen
  (Titel, Kategorie, Stellen-Anzahl werden übernommen).

> Damit lässt sich sowohl die schlanke 1-Stufen-Freigabe einer Filiale als
> auch der 4-stufige Gremien-Prozess einer Bank-IT-Abteilung abbilden –
> **inklusive paralleler Stufen** („Controlling + Betriebsrat": alle Rollen
> einer Stufe müssen genehmigen, eine Rückgabe stoppt den Antrag) –
> ohne dass die eine Organisation die Konfiguration der anderen sieht oder
> einschränkt.

### 3.10 Gesprächsrunden & strukturiertes Interview-Feedback

Damit die zweite Runde und die finale Einstellung auf dokumentiertem Feedback
stehen – nicht auf Flurfunk – bildet SecurATS den Gesprächsprozess als formale
Kette ab und sammelt Feedback dort ein, wo es entsteht.

- **Gesprächsrunden als Zustände:** Je Stelle definierbar (z. B. Erstgespräch →
  Fachgespräch → Probearbeit). Eine Einstellung ist erst möglich, wenn alle
  Runden abgeschlossen sind. Setzt eine Interviewer:in das Gespräch auf
  „stattgefunden", rückt die Runde automatisch vor (Korrektur nimmt sie zurück).
- **Bitte um Feedback – ohne dass jemand daran denkt:** Genau bei „stattgefunden"
  erhalten die Teilnehmer:innen, die noch nicht bewertet haben, automatisch eine
  Mail mit Direktlink; ein täglicher Cron mahnt Nachzügler genau einmal.
- **Erfassen in unter einer Minute:** Prozent-Regler zu klaren Aussagen („Passt
  ins Team 80 %", „Ist motiviert 90 %") mit Live-Gesamteindruck; die Empfehlung
  wird aus dem Schnitt abgeleitet, ist aber übersteuerbar. Dazu Stärken, ein
  eigenes, hervorgehobenes **Bedenken-Feld** und freie Anmerkungen.
- **Mehrere Stimmen, ein Bild:** Jede:r Interviewer:in gibt unabhängig eine
  Bewertung je Runde ab; alle erscheinen nebeneinander.
- **Sichtbar, wo entschieden wird:** Auf der Bewerber-Karte im Board zeigt ein
  farbiges Badge den kollektiven Durchschnitt und ein Warnsignal bei Bedenken;
  beim Einstellen mit offenen Bedenken verlangt das System eine bewusste,
  protokollierte Bestätigung. So geht keine Sorge verloren, nur weil niemand
  daran dachte, sie weiterzugeben.

---

## 4. Erfolgs- & Insight-Dashboard (Analytics)

> „Nur mit Zahlen erkennen wir langfristig, wo unsere Stärken und Schwächen liegen
> und wo wir besser werden können." – genau dafür ist dieses Modul da.

Recruiting-Analytics ist kein Nachgedanke, sondern ein Kern-Baustein. Der
**Unterschied zu Cloud-ATS**: Weil alle Daten on-prem liegen und die KI **lokal**
rechnet, kann SecurATS tiefer, historisch unbegrenzt und **datenschutzkonform**
auswerten – ohne dass ein Byte an einen Analytics-Cloud-Dienst geht. Deine Daten,
deine Auswertung.

### 4.1 Kern-Kennzahlen (das solide Fundament)
- **Geschwindigkeit:** Time-to-Hire, Time-to-Fill, **Verweildauer je Phase** (wo hakt es?), SLA-Überschreitungen.
- **Volumen:** Bewerbungen gesamt / je Stelle / je Standort / im Zeitverlauf; offene vs. besetzte Stellen; Pipeline-Alter.
- **Quellen:** Herkunft der Bewerbungen (StepStone, BA, Google for Jobs, Karriereseite, Empfehlung) – **inkl. Quellen-Qualität**, nicht nur -Menge.
- **Funnel & Conversion:** Übergangsquoten je Stufe (Eingang → Sichtung → Interview → Angebot → Einstellung), **Abbruch-Analyse**.
- **Ergebnis:** Angebots-Annahmequote, Absage-/Absprunggründe, Kosten pro Einstellung (perspektivisch je Quelle).

### 4.2 Rollen-adaptive Sichten (jede:r sieht das Richtige – im BOLA-Rahmen)
- **Geschäftsführung:** strategische Kacheln über alle Töchter/Standorte, Trends, Ampeln – Antworten in Sekunden.
- **HR-Leitung:** operative Steuerung, Engpässe, Recruiter-Auslastung, Prozess-Qualität.
- **Recruiter:in:** persönliches Cockpit (meine Stellen, meine To-dos, meine Durchlaufzeiten).
- **Standort/Tochter:** nur die eigenen Zahlen – Leitung sieht den aggregierten Vergleich.

### 4.3 Was es innovativ & zukunftsweisend macht
- **Lokaler KI-Analyst – „Frag deine Daten":** Fragen in normaler Sprache stellen
  („Warum dauert die Besetzung in der Pflege länger als in der Verwaltung?") und Antwort +
  Diagramm erhalten – vollständig on-prem, ohne Cloud-BI.
- **Prognosen (Predictive):** Time-to-Fill-Vorhersage je Stelle, erwartetes Bewerbungsaufkommen
  je Kanal/Saison, Wahrscheinlichkeit einer erfolgreichen Besetzung – als Planungshilfe für die Personalbedarfe.
- **Engpass- & Anomalie-Erkennung:** automatische Hinweise („Angebots-Annahmequote im Standort X seit
  6 Wochen fallend") plus konkrete Handlungsvorschläge – das Dashboard sagt nicht nur *was*, sondern *was tun*.
- **Candidate-Experience-Analytics:** wo brechen Bewerber im Formular ab, Time-to-First-Response,
  Feedback-/Zufriedenheitswerte – der Blick aus Bewerbersicht.
- **Fairness-/Bias-Frühwarnung (AGG-Cockpit, optional & datensparsam):** überwacht die **eigenen
  automatischen Entscheidungen** des Systems auf auffällige Muster (adverse impact), rein aggregiert,
  ohne Profiling geschützter Merkmale – Fairness wird *messbar*, nicht nur behauptet.
- **Inklusions-/BFSG-ROI-Cockpit:** Nutzung der Barrierefreiheits-Funktionen, Conversion-Uplift,
  **Ausgleichsabgabe-Tracker** (gesparte € live) – der wirtschaftliche Nachweis der Inklusion.
- **Compliance-Cockpit:** Retention-/Löschläufe, durchschnittliche Datenhaltedauer vs. Richtlinie,
  Einwilligungs-Abdeckung, Audit-Vollständigkeit – Datenschutz als Kennzahl.
- **Multi-Standort-Benchmarking:** Töchter/Standorte fair nebeneinander (gleiche Definitionen),
  Best-Practice-Standorte werden sichtbar und übertragbar.
- **Closed-Loop „Quality-of-Hire" (Zukunftsausbau):** Quelle → Einstellung → Frühfluktuation/Bewährung
  verknüpfen – so zeigt sich, welche Kanäle nicht nur *viele*, sondern *langfristig erfolgreiche* Mitarbeitende bringen.

### 4.4 Bedienung, Export & Betrieb
- **Individuell:** KPI-/Dashboard-Builder, gespeicherte Ansichten je Rolle, Schwellen-Alerts,
  geplante Report-Versände (z.B. wöchentlicher GF-Report).
- **Offen:** Export nach Excel und Anbindung an eigene BI-Tools (OData) – die Rohdaten bleiben deine.
- **Guardrails:** Analytics respektieren BOLA-Silos und Datensparsamkeit (Aggregation/k-Anonymität,
  keine Auswertung geschützter Merkmale); passt zu Prinzip 8 und „Fairness by Design".

> Kurz: Ein Dashboard, das nicht nur rückblickend zählt, sondern **vorausschaut, erklärt und zum
> Handeln führt** – und das, weil lokal gerechnet wird, ohne den Datenschutz-Kompromiss der Cloud-BI.

---

## 5. Produktprinzipien (nicht verhandelbar)

1. **Datensouveränität zuerst.** 100 % on-premise betreibbar, air-gap-fähig,
   keine zwingenden externen APIs/CDNs/Tracker/Fonts.
2. **Zero-Data-Transfer-KI.** Nur lokale Modelle (Ollama/Gemma). Nie Bewerberdaten
   an Cloud-LLMs.
3. **Privacy & Security by Design.** PII verschlüsselt at-rest, TLS/HSTS in-transit,
   Datenminimierung, automatische Löschung, manipulationssicheres Audit-Log.
4. **Compliance ist beweisbar, nicht behauptet.** Jede Compliance-Aussage ist an
   ein konkretes, testbares Feature gekoppelt (siehe „Definition of Done").
5. **Fairness/AGG by Design.** KI ist „farbblind"; Alter/Geschlecht/Herkunft/
   Religion/Aussehen fließen nie in Bewertungen ein; AGG-Check vor Veröffentlichung.
6. **Barrierefreiheit.** BFSG/WCAG-konform, inkl. „Leichte Sprache".
7. **Eine Quelle der Wahrheit.** Ein kanonischer Stack, ein Datenmodell, ein
   Auth-Modell. Keine parallelen Reimplementierungen.
8. **Flexibel, aber governed.** Lokale Anpassung (Workflows, Rollen, Variablen,
   Seiten je Standort/Einrichtung) ist erwünscht – Pflicht-Schritte (Freigaben,
   Betriebsrat, AGG-Check, DSGVO-Einwilligung) bleiben systemseitig erzwingbar und
   sind lokal **nicht** abschaltbar. Konfigurierbarkeit endet dort, wo Rechtssicherheit beginnt.
9. **Wahlfreiheit Mensch/KI.** Automatische Interaktion mit Bewerbenden ist immer
   ein Angebot neben dem Weg zum Menschen, nie der einzige Kanal – gekennzeichnet
   (Art. 50 EU AI Act) und öffentlich erklärt (`/ki-transparenz/`, Art. 86).

---

## 6. ✅ Entschieden: Django ist der kanonische Stack

**Entscheidung (getroffen):** Der Zielstack ist **Django**. Gründe: Es ist das real
laufende, deploybare System (die `docker-compose.yml` fährt bereits ausschließlich
Django), es ist „dein Projekt", und Backend/ORM/Migrations/Admin sowie die
Python-KI-Anbindung sind stark. **Next.js wird nach `legacy/` gezogen**; die wenigen
Features, die dort reicher sind (Analytics, Delegations, Magic-Link-Kandidatenportal,
Kalender, Audit-Viewer), werden gezielt in Django nachgebaut.

Von ursprünglich **drei** Stacks bleibt damit **einer**: die Express-Ebene ist bereits
in `legacy/express-api/`, Next.js folgt.

<details>
<summary>Für die Historie: die verglichenen Optionen</summary>

| Option | Pro | Contra |
|---|---|---|
| **Django** (gewählt) | Bereits laufendes Deployment; Admin/ORM/Migrations; natürliche Python-KI-Anbindung; battery-included Auth/RBAC | Template-UI weniger reich; einige Frontend-Features nachzubauen |
| **Next.js + Prisma** | Funktional Superset; Build verifiziert; ein TS-Sprachraum | Auth nur Platzhalter; Deployment-Rückbau nötig; Django würde Legacy |

</details>

---

## 7. Zielarchitektur (Django, umgesetzt)

```
[Bewerber-Browser] ──TLS──▶ [Öffentliches Career-Portal]
                                     │
[HR-Browser] ──TLS──▶ [Recruiter-App] ──▶ [Auth/RBAC/BOLA]
                                     │
                             [Kanonische App-/API-Schicht]
                                     │
                    ┌────────────────┼───────────────┐
              [Datenbank]      [Lokale KI]      [Datei-Storage]
             (PII verschl.)   (Ollama/Gemma)   (CV verschl.)
                                     │
                             [Audit-Log (append-only)]
```

Querschnitt: Retention-Cronjob, HR-BA-XML/StepStone-Feeds, SAP-SuccessFactors-Bridge.

**Modul-Zuordnung in der Codebasis** (Details & Konventionen:
`AI_DEV_GUIDELINES.md`): `ats/panel.py` (Sichtungs-Gremium-Auflösung),
`ats/approvals.py` (Freigabeketten inkl. Stellenfreigabe-Routing-Matrix),
`ats/blocks.py` (CMS-Baukasten), `ats/questions.py` (Fragen-Registry),
`ats/importer.py` (CSV/XLSX-Import), `ats/analytics.py` (Kennzahlen),
`ats/audit.py` (Audit-Kette), `ats/permissions.py` (BOLA-Scope +
Delegationen).

---

## 8. Definition of Done (Qualitäts-/Sicherheitsanspruch)

Ein Feature gilt erst als fertig, wenn:

- [ ] Auth **und** Autorisierung (RBAC + BOLA-Scope) greifen – keine ID-only-Query.
- [ ] PII, die gespeichert wird, ist verschlüsselt at-rest; Keys nur aus Env.
- [ ] Zustandsändernde Requests sind CSRF-/Token-geschützt.
- [ ] Sensible Zugriffe (CV-Download, Statuswechsel, Löschung) erzeugen ein Audit-Log.
- [ ] Keine externen Netzwerkaufrufe im Datenpfad (air-gap-Test bestanden).
- [ ] Automatisierter Test deckt Happy-Path + einen Missbrauchsfall ab.
- [ ] Keine erfundenen/gemockten Kennzahlen in der Produktions-UI.
- [ ] **Usability:** Kernaufgabe in möglichst wenigen Klicks; von Gelegenheitsrollen ohne Schulung bedienbar; Profi-Kürzel vorhanden, wo sinnvoll.
- [ ] **KI/Automatisierung:** jede automatische Aktion ist begründet, im Audit-Log, pro Stelle abschaltbar; automatische Absagen nur bei objektiven K.-o.-Kriterien (sonst Human-in-the-Loop).

---

## 9. Erfolgskriterien (messbar)

- **Sicherheit:** 0 unauthentifizierte Pfade zu PII; alle Krypto-Keys env-basiert;
  `manage.py check --deploy` bzw. `next build` ohne Sicherheitswarnungen.
- **Compliance-Nachweis:** Für jede beworbene Norm (DSGVO Art. 5/7/32, AGG, ISO
  27001 A.9/A.12/A.14/A.18) existiert ein verlinktes Feature **und** ein Test.
- **Air-Gap:** Vollständiger Bewerbungs- + Screening-Flow ohne Internetzugang.
- **Ein Stack:** Nur noch ein Deployable pro Rolle; kein doppeltes Datenmodell.
- **DX:** `README` → lokaler Start in < 10 Minuten, ein Befehl.
- **Usability:** neue:r Recruiter:in ohne Schulung produktiv; definierte Kernaufgaben (Stelle anlegen, Bewerbung sichten, Status wechseln, absagen) je unter einer Ziel-Klickzahl.
- **Automatisierung mit Augenmaß:** messbare Zeitersparnis (z.B. Vorqualifizierungs-Quote, Anteil automatisch nachgeforderter Lücken) bei 0 unbegründeten oder nicht protokollierten Auto-Absagen.

---

## 10. Roadmap (priorisiert)

> Die **taktische Umsetzungsreihenfolge** (Arbeitspakete, Releases, jede
> Migration, jeder gefangene Bug) steht in **`BUILD_PLAN.md`**. Der aktuelle,
> nach dem Schritt-für-Schritt-Prozess-Review priorisierte **Lücken-Backlog**
> steht in **`ROADMAP.md`**. Diese Phasen hier sind die strategische Sicht –
> sie werden nicht mehr Zeile für Zeile nachgeführt, sobald eine Phase
> inhaltlich abgeschlossen ist (siehe Statuszeile je Phase).

### Phase 0 – Stabilisieren ✅ abgeschlossen
Krypto-Feld-Überlauf behoben, Settings gehärtet (Key-Zwang, CORS, HSTS,
ALLOWED_HOSTS), Fehler-Logging statt `pass`, DOM-XSS-Escaping, erfundene
Metriken entfernt.

### Phase 1 – „Make it one" ✅ abgeschlossen
Kanon-Entscheidung **Django** getroffen und vollständig umgesetzt: Express-
Ebene (`src/`) und Next.js/Prisma-Frontend liegen komplett in `legacy/` und
werden nicht mehr ausgeliefert (siehe Abschnitt 6). Feature-Gap Next.js →
Django vollständig abgearbeitet (`FEATURE_BACKLOG.md`, 18/18 Punkte).

### Phase 2 – „Make it safe" ✅ Kern abgeschlossen
RBAC-Auth (Django-Groups HR-Admin/Recruiter/Hiring-Manager/Viewer + beliebige
Freigabeketten-Rollen), CSRF konsistent (globaler Token-Wrapper), BOLA-Scoping
(`UserScope`, `scope_*`/`can_access_*`-Muster, siehe `AI_DEV_GUIDELINES.md`),
sicherer CV-Download mit Audit-Log. Offen: PII-Krypto-Strategie für `email`
vereinheitlichen; externe Feeds (StepStone/HR-BA-XML) token-/IP-absichern.

### Phase 3 – „Make it provable" (Compliance nachweisbar) – Kern erledigt, Härtung offen
Audit-Log-Viewer mit benutzerattribuierten Zugriffen steht und wird von jedem
neuen Governance-Feature aktiv genutzt (Stellenfreigabe, Quorum, CMS-Änderungen
etc.). Offen: Audit-Log append-only + Integritätssicherung, Retention-Job
produktiv geplant (Scheduling/Dry-Run), Compliance-Matrix (Norm → Feature →
Test) im Repo, Air-Gap-Integrationstest in CI.

### Phase 4 – „Make it sellable" (Reife) – laufend
Erfolgs-/Insight-Dashboard (Kern-KPIs, Funnel, Quellen, **Time-to-Fill &
Kosten je Einstellung**, Standort-Vergleich) und Job-Vorlagen-Bibliothek sind
umgesetzt. KI-Analyst/Prognosen/Fairness-Cockpit, Vorlagen-Master-
Versionierung, UX-Parität mit Marktführern und vollständige Feed-/Bridge-
Validierung bleiben Ausbaustufen.

### Phase 5 – Prozess-Tiefe & Governance-Reife (aktuell, seit Prozess-Review Juli 2026)
Ausgangspunkt war ein Schritt-für-Schritt-Review der ganzen Kette
**Stelle → Kampagne → Bewerbung → Gremium → Einladung → Einstellung**, der
konkrete Bedienbarkeits- und Flexibilitätslücken aufdeckte (voller,
priorisierter Katalog: `ROADMAP.md`). Erledigt aus diesem Katalog:

- [x] Fragen-Builder ohne JSON-Vorwissen; Fragetyp „Pflicht-Dokument".
- [x] Einstellungsdatum manuell setz- und korrigierbar.
- [x] Terminformate konfigurierbar (Verwaltungsseite statt Code-Liste).
- [x] Import: manuelle Spalten-Zuordnung + Adressfeld.
- [x] Kampagnenkosten strukturiert am Kanal (speist Kosten je Einstellung).
- [x] Status „Eingestellt" mit Time-to-Fill (statt INVITED-Näherung).
- [x] CMS-Baukasten (10 Block-Typen, Editor mit Live-Vorschau).
- [x] Analytics-Vollständigkeits-Garantie (jede neue Seite zählt automatisch).
- [x] Headcount je Stelle + automatische Ausblendung bei Vollbesetzung.
- [x] Gremium: konfigurierbares Quorum + Abstimmungs-Frist mit Eskalation.
- [x] **Vorgeschalteter Stellenfreigabe-Prozess mit No-Code Routing-Matrix**
      (Abschnitt 3.9) – erfüllt zugleich „Genehmigungspflicht vor
      Veröffentlichung" in stärkerer Form als ursprünglich geplant.

Offen aus demselben Katalog (Details/Priorität: `ROADMAP.md`):
- [x] Kampagnen-Ablaufdatum (Landingpage/Kanal automatisch inaktiv).
- [x] Mehrstufige Gesprächsrunden als formale Zustände (inkl. automatischer Kopplung ans Interview-Ergebnis).
- [x] Parallele Genehmigungsstufen in der Routing-Matrix – inkl. Quorum je
      Gruppe („2 von 3 genügen") und Vertretung in der Kette („i. V.").
- [ ] Frei konfigurierbare Status-Pipelines je Jobkategorie + Automatisierungs-
      Trigger (größtes Einzelpaket; Evidenz-Gate, siehe unten).

### Evidenz-Gates (bewusst zurückgestellt bis Design-Partner-Bestätigung)
CV-Parsing-Feldbefüllung, 1-Klick-Bewerbung via LinkedIn/Xing (OAuth +
DSGVO-Abwägung on-prem), Mehrfachbewerbung in einem Schritt, A/B-Test
zwischen Landingpage-Varianten, Offboarding/Vertrags-Track nach Einstellung.
Diese Punkte sind kein Versäumnis, sondern warten bewusst auf echte
Nutzungsevidenz aus Discovery-Gesprächen, bevor Aufwand hineinfließt.

---

## 11. Kanon-Fragen – alle fünf entschieden

1. ~~**Kanonischer Stack**~~ → **entschieden: Django** (Express + Next.js → `legacy/`).
2. ~~**Auth-Modell**~~ → **entschieden (WP1/WP2, de facto):** intern klassische Django-Sessions + RBAC-Gruppen; Bewerbende passwortlos via Magic-Link-Portal. JWT nicht nötig.
3. ~~**Ziel-Datenbank in Produktion**~~ → **entschieden (WP7): PostgreSQL in Produktion, SQLite nur Entwicklung/Evaluation.** Begründung: Nebenläufigkeit Web + `ai_worker` (Queue nutzt `select_for_update(skip_locked)`), robuste Backups (`pg_dump`, vorhandene Skripte), Skalierung. Aktivierung rein per Env (`POSTGRES_HOST` …), kein Code-Unterschied.
4. ~~**Deployment-Realität**~~ → **entschieden (de facto seit Stack-Konsolidierung):
   Django ist direkt erreichbar**; das Next.js-Frontend liegt in `legacy/` und wird
   nicht mehr ausgeliefert. C2/H2 gelten damit in voller Dringlichkeit für Django
   (umgesetzt in WP2).
5. ~~**Scope jetzt**~~ → **entschieden (Premortem-Revision Juli 2026): EIN Segment
   zuerst** – Pflege-/Sozialträger mit ca. 300–2.000 Mitarbeitenden in DACH.
   Begründung und Validierungs-Gates: siehe ROADMAP.md. Breite über weitere
   Branchen erst ab Phase V3 mit Evidenz.

---

*Architektur- und Kanon-Fragen sind geklärt; die Arbeit läuft in Phase 5
(Abschnitt 10) entlang des priorisierten Lücken-Backlogs in `ROADMAP.md`.
Neue offene Fragen sind ausschließlich Produkt-Priorisierung, nicht mehr
Architektur – sie entstehen laufend aus Prozess-Reviews und werden dort
🔶 markiert, sobald sie auftreten.*
