# 13_Content_Migration_and_Inventory.md

## Dokumentstatus
- Version: 2.0
- Zweck: Enterprise-spezifische Migrations- und Inventarisierungsgrundlage für Inhalte, Strukturen und Zielobjekte
- Gültigkeit: benchmark-frei, ausschließlich auf Enterprise-Quellen und Zielmodell ausgerichtet
- Regel: Wenn Zielmodell oder Governance-Regeln angepasst werden, muss dieses Migrationsdokument aktualisiert werden

---

# 1. Ziel dieses Dokuments

Dieses Dokument definiert:
- welche Inhalte und Strukturen in der aktuellen Enterprise-Karrierepräsenz sichtbar sind,
- wie diese in Zielobjekte überführt werden,
- welche Inhalte migriert, restrukturiert, neu geschrieben oder stillgelegt werden,
- welche Inhalte zentral gepflegt werden,
- welche Inhalte lokal ergänzt werden dürfen,
- und welche Validierungen vor Go-Live notwendig sind.

Die Migration ist **keine 1:1-Kopie** der aktuellen Seiten, sondern eine **strukturierte Transformation**:
- von aktueller Enterprise-Webstruktur
- in das neue Zielmodell der Karriereplattform.

---

# 2. Migrationsprinzipien

## 2.1 Enterprise ist die einzige Content-Ausgangsquelle
Für aktuelle Inhalte und aktuelle Struktur dient ausschließlich die aktuelle Enterprise-Karrierepräsenz als Ausgangsbasis. Dazu gehören insbesondere:
- Karriere-Startseite,
- Arbeitgeberinhalte,
- Beruf und Karriere,
- Karrierepfade,
- Stellenangebote,
- Initiativbewerbung,
- Ihr Weg zu uns / Bewerbung,
- Ansprechpartner-/Kontaktlogik,
- Datenschutz- und Barrierefreiheitsbezüge. 

## 2.2 Migration nach Zieltyp, nicht nach HTML-Seite
Migriert wird in:
- strukturierte Masterdaten,
- strukturierte Seiten-/Seitentypen,
- strukturierte Jobobjekte,
- strukturierte Formulare,
- wiederverwendbare Module.

## 2.3 Struktur vor Copy & Paste
Wo Inhalte in strukturierte Felder gehören, müssen sie strukturiert migriert werden.
Freitext-Übernahmen ohne strukturelle Überführung sind zu vermeiden.

## 2.4 Ownership ist Pflicht
Jedes Zielobjekt braucht klaren Owner:
- zentrale HR-Karriere-Abteilung,
- lokaler Bereich / Standort,
- Privacy / Compliance,
- technischer System Owner,
- oder anderer explizit definierter Owner.

## 2.5 Nicht alles wird 1:1 übernommen
Mögliche Migrationsaktionen:
- MIGRATE_AS_IS
- MIGRATE_AND_RESTRUCTURE
- REWRITE
- MERGE
- SPLIT
- RETIRE
- POSTPONE

---

# 3. Aktuelle sichtbare Inhaltsbereiche des Enterprises

## 3.1 Karriere-Hauptnavigation / Einstieg
Sichtbar sind unter anderem:
- Arbeitgeber Enterprise,
- Beruf und Karriere,
- Stellenangebote,
- Initiativbewerbung,
- Ihr Weg zu uns. 

## 3.2 Karrierepfad-Inhalte
Die aktuelle Plattform enthält sichtbare Karrierepfad-/Recruiting-Einstiege:
- Ausbildung,
- Freiwilligendienst (FSJ/BFD),
- Praktikum,
- Praktisches Jahr und ärztliche Weiterbildung,
- Fortbildung / Weiterbildung. 

## 3.3 Arbeitgeber- und Berufsfeldinhalte
Sichtbar sind:
- Arbeitgeber-Überblick,
- Arbeits- und Berufsfelder,
- inhaltliche Einblicke in Tätigkeitsfelder und Berufe. [2](https://www.dvinci.de/bewerbermanagement-software/)[3](https://www.dvinci.de/features/)

## 3.4 Stellenlogik
Sichtbar sind:
- Stellenliste,
- strukturierte Stellenattribute,
- einzelne Jobdetailseiten,
- Kategorie-/Berufsfeldbezug. [1](https://www.dvinci.de/karrierewebseite/)

## 3.5 Bewerbungs- und Serviceinhalte
Sichtbar sind:
- Ihr Weg zu uns,
- Ihre Bewerbung,
- Kurzbewerbungsformular,
- Datenschutzhinweis und Löschhinweis,
- Ansprechpersonen-Kontexte. 

---

# 4. Ziel-Migrationsdomänen

Alle Quellinhalte werden einer der folgenden Ziel-Domänen zugeordnet.

## 4.1 Domain A – Strukturierte Stammdaten
- Organization
- Facility
- Location
- JobFamily
- CareerPath
- ContactPerson

## 4.2 Domain B – Redaktionelle Karriere-Seiten
- homepage
- employer page
- job family page
- career path page
- location page
- facility page
- service / FAQ page
- initiative page

## 4.3 Domain C – Landing Pages
- zielgruppenspezifische Seiten
- kampagnenbezogene Seiten
- standortfokussierte Seiten
- berufsfeldspezifische Einstiegsseiten

## 4.4 Domain D – Job Objects
- JobPosting
- strukturierte Jobattribute
- Bewerbungs-CTA-Logik

## 4.5 Domain E – Bewerbungs-/Service-/Privacy-Inhalte
- ApplicationForm
- PrivacyNoticeVersion
- Datenschutzhinweise
- Bewerbungsprozessinhalte
- Zugangs-/Servicehinweise

## 4.6 Domain F – Shared Modules
- CTA Banner
- FAQ Listen
- Benefits Blöcke
- Contact Cards
- Intro-/Teaser-Module
- Bild/Text-Module

---

# 5. Migrationsaktionen

## 5.1 MIGRATE_AS_IS
Nur verwenden, wenn Inhalt und Struktur bereits direkt zum Zieltyp passen.

## 5.2 MIGRATE_AND_RESTRUCTURE
Verwenden, wenn Inhalt relevant bleibt, aber in strukturierte Felder / Module / Zieltypen überführt werden muss.

## 5.3 REWRITE
Verwenden, wenn Inhalt relevant bleibt, aber sprachlich, strukturell oder inhaltlich neu gefasst werden muss.

## 5.4 MERGE
Verwenden, wenn mehrere Quellinhalte zu einem Zielobjekt zusammengeführt werden.

## 5.5 SPLIT
Verwenden, wenn eine Quelle mehrere Zielobjekte enthält.

## 5.6 RETIRE
Verwenden, wenn Inhalt veraltet, redundant oder im Zielmodell nicht benötigt wird.

## 5.7 POSTPONE
Verwenden, wenn Inhalt bekannt, aber nicht MVP-relevant ist.

---

# 6. Standardfelder für das Migrationsinventar

Jeder Quellinhalt muss im Migrationsinventar mindestens folgende Felder besitzen:

- source_id
- source_url
- source_title
- source_category
- target_domain
- target_type
- migration_action
- template_name
- central_owner
- local_owner
- required_structuring
- privacy_review_required
- seo_review_required
- accessibility_review_required
- status
- notes

---

# 7. Enterprise-spezifische Startinventarisierung

---

# 7.1 Karriere-Startseite

## Quelle
- aktuelle Karriere-Startseite / Haupteinstieg des Karriereportals 

## Sichtbare Quellmerkmale
Die Seite enthält u. a.:
- Arbeitgebereinstieg,
- Beruf und Karriere,
- Stellenangebote,
- Initiativbewerbung,
- Ihr Weg zu uns,
- Einstiegspunkte wie Ausbildung und FSJ/BFD,
- Jobsucheinstieg,
- Ansprechpartner-/Servicebezug,
- Datenschutz und Barrierefreiheit. 

## Zielabbildung
- `target_domain`: Editorial Career Pages
- `target_type`: homepage
- `migration_action`: MIGRATE_AND_RESTRUCTURE

## Begründung
Die Seite soll nicht 1:1 kopiert werden.  
Sie soll zur strukturierten Karriere-Startseite werden mit:
- primären Einstiegen,
- Karrierepfad-Teasern,
- Job-CTA,
- Initiativbewerbungs-CTA,
- Service-/Kontaktzugang.

## Ownership
- central_owner: Central HR Career Department

---

# 7.2 Arbeitgeberbereich

## Quelle
- Arbeitgeber Enterprise / Arbeitgeberübersicht [2](https://www.dvinci.de/bewerbermanagement-software/)

## Sichtbare Quellmerkmale
Die Seite beschreibt den Enterprise als großen Träger im Gesundheits- und Sozialwesen mit mehreren Arbeitsfeldern, Standorten und vielfältigen beruflichen Möglichkeiten. [2](https://www.dvinci.de/bewerbermanagement-software/)[3](https://www.dvinci.de/features/)

## Zielabbildung
- `target_domain`: Editorial Career Pages
- `target_type`: employer
- `migration_action`: MIGRATE_AND_RESTRUCTURE

## Begründung
Die Inhalte sollen in einen strukturierten Arbeitgeberbereich überführt werden, ggf. mit wiederverwendbaren Modulen für Unterseiten wie Berufsfelder oder Karrierepfade.

## Ownership
- central_owner: Central HR Career Department

---

# 7.3 Arbeits- und Berufsfelder

## Quelle
- Arbeits- und Berufsfelder [3](https://www.dvinci.de/features/)

## Sichtbare Quellmerkmale
Die Seite enthält:
- breite Arbeitsfeldbeschreibung,
- viele Berufsbezeichnungen,
- Querschnitt über fachliche Bereiche des Enterprises. [3](https://www.dvinci.de/features/)

## Zielabbildung
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: JobFamily + job_family page
- `migration_action`: SPLIT

## Begründung
Diese Quelle muss in mindestens zwei Ebenen überführt werden:
1. strukturierte JobFamily-Stammdaten
2. job-family-orientierte Zielseiten

## Ownership
- central_owner: Central HR Career Department

## Template
- job family page template required

---

# 7.4 Ausbildung

## Quelle
- Ausbildung 

## Sichtbare Quellmerkmale
Die Seite enthält:
- Ausbildungskontext,
- Mengenhinweis zu Ausbildungsplätzen,
- Verweise auf Praktikum / FSJ / BFD,
- Förderhinweise,
- Bewerbungsbezug. 

## Zielabbildung
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: CareerPath + career_path page
- `migration_action`: MIGRATE_AND_RESTRUCTURE

## Begründung
Die Seite soll zu einer strukturierten CareerPath-Instanz „Ausbildung“ plus Zielseite werden.

## Ownership
- central_owner: Central HR Career Department

---

# 7.5 Freiwilligendienst: FSJ und BFD

## Quelle
- FSJ / BFD Seite 

## Sichtbare Quellmerkmale
Die Seite enthält:
- Beschreibung von FSJ/BFD,
- Zielgruppenbezug,
- Einsatzfelder,
- Dauer,
- Rahmenbedingungen,
- Vergütungshinweise. 

## Zielabbildung
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: CareerPath + career_path page
- `migration_action`: MIGRATE_AND_RESTRUCTURE

## Begründung
Die Quelle wird als eigener CareerPath im Zielmodell geführt.

## Ownership
- central_owner: Central HR Career Department

---

# 7.6 Praktikum

## Quelle
- Praktikum ist aktuell als Karrierepfad/Kategorie sichtbar im Bereich Beruf und Karriere. 

## Zielabbildung
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: CareerPath + career_path page
- `migration_action`: REWRITE

## Begründung
Die Zielstruktur bleibt relevant, der Zielinhalt muss aber wahrscheinlich eigenständig ausformuliert und an das Zielmodell angepasst werden.

---

# 7.7 Praktisches Jahr / Ärztliche Weiterbildung

## Quelle
- Praktisches Jahr und ärztliche Weiterbildung sind aktuell sichtbar. 

## Zielabbildung
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: CareerPath + career_path page
- `migration_action`: MIGRATE_AND_RESTRUCTURE

## Begründung
Die Quelle soll als spezialisierter Karrierepfad mit zielgruppengerechter Zielseite abgebildet werden.

---

# 7.8 Fortbildung / Weiterbildung

## Quelle
- Fortbildung und Weiterbildung sind aktuell sichtbar. 

## Zielabbildung
- `target_domain`: Editorial Career Pages
- `target_type`: service page oder career_path page
- `migration_action`: MIGRATE_AND_RESTRUCTURE

## Begründung
Die genaue Klassifizierung wird im Zielmodell festgelegt, die Sichtbarkeit und Relevanz des Themenfelds ist jedoch aktuell bestätigt. 

---

# 7.9 Stellenliste

## Quelle
- Stellenangebote / Stellenliste [1](https://www.dvinci.de/karrierewebseite/)

## Sichtbare Quellmerkmale
Die Stellenliste enthält:
- Titel,
- Referenz,
- Einrichtung,
- Ort,
- Beginn,
- Stundenumfang,
- Befristung,
- Kategorie-/Berufsfeldbezug,
- Verweis auf Weiterleitung an Fachabteilung oder Einrichtung. [1](https://www.dvinci.de/karrierewebseite/)

## Zielabbildung
- `target_domain`: Job Objects
- `target_type`: JobPosting
- `migration_action`: MIGRATE_AND_RESTRUCTURE

## Begründung
Die Stellenliste ist der zentrale strukturierte Migrationsbereich.  
Jobs müssen in Zielobjekte überführt werden mit:
- Pflichtfeldern,
- Facility-/Location-/JobFamily-Referenzen,
- Bewerbungsziel,
- Template-Governance,
- Ownership,
- Workflowstatus.

## Ownership
- central_owner: Central HR Career Department
- local_owner: lokale Bereiche/Facilities für Draft-/Fachinhalte
- publication governance: central only

## Template
- mandatory JobTemplate mapping required

---

# 7.10 Jobdetailseiten

## Quelle
- einzelne Jobdetailseiten, z. B. Serviceassistent (m/w/d) 

## Sichtbare Quellmerkmale
Jobdetailseiten enthalten:
- detailliertere Aufgaben,
- Anforderungen,
- Benefits,
- Einrichtungs-/Standortkontext,
- Beschäftigungsinformationen. 

## Zielabbildung
- `target_domain`: Job Objects
- `target_type`: JobPosting
- `migration_action`: MIGRATE_AND_RESTRUCTURE

## Begründung
Die Inhalte werden in strukturierte JobPosting-Felder und ggf. template-konforme Inhaltsblöcke überführt.

---

# 7.11 Einrichtungen und Orte aus Stellen

## Quelle
- Einrichtungs- und Ortsangaben in der Stellenliste, z. B. Gärtnerei Erlenhof / Aukrug-Innien, Psychiatrisches Krankenhaus / Rickling usw. [1](https://www.dvinci.de/karrierewebseite/)

## Zielabbildung
- `target_domain`: Structural Master Data
- `target_type`: Facility / Location
- `migration_action`: SPLIT

## Begründung
Diese Werte dürfen nicht nur in Jobtexten verbleiben.  
Sie müssen als strukturierte Stammdaten nutzbar sein für:
- Jobs,
- Filter,
- Seiten,
- Kontaktzuordnung,
- spätere Standort-/Einrichtungsseiten.

---

# 7.12 Ihr Weg zu uns / Ihre Bewerbung

## Quelle
- Ihr Weg zu uns,
- Ihre Bewerbung. 

## Sichtbare Quellmerkmale
Die Seiten enthalten:
- Bewerbungsweg-Erklärung,
- Verweis auf E-Mail-Bewerbungen,
- Verweis auf Kurzbewerbungsformular,
- Kontakt-/Ansprechpersonenlogik,
- Datenschutz-/Löschhinweise im Bewerbungsumfeld. 

## Zielabbildung
- `target_domain`: Editorial Career Pages + Application Domain + Privacy / Service
- `target_type`: service page + initiative page + ApplicationForm
- `migration_action`: SPLIT

## Begründung
Diese Quelle muss in mehrere Zielobjekte überführt werden:
1. Service-/Bewerbungsweg-Seite
2. Initiativbewerbungsseite
3. strukturiertes ApplicationForm
4. PrivacyNotice-Verknüpfung
5. Prozess-/FAQ-Module

## Ownership
- central_owner: Central HR Career Department
- privacy_review_required: yes

---

# 7.13 Kontaktpersonen / Ansprechpersonen

## Quelle
- Ihre Ansprechpartner / Ansprechpersonen-Kontexte auf der Plattform 

## Zielabbildung
- `target_domain`: Structural Master Data + Shared Modules
- `target_type`: ContactPerson + contact_cards module
- `migration_action`: MIGRATE_AND_RESTRUCTURE

## Begründung
Ansprechpartner dürfen nicht nur als lose Textbestandteile migriert werden, sondern müssen zu:
- strukturierten ContactPerson-Objekten,
- kontextbezogenen Zuweisungen,
- wiederverwendbaren Contact-Modulen
werden.

## Harte Regel
Kein öffentlicher Ansprechpartner wird migriert ohne:
- Kontextzuordnung,
- Owner-Freigabe,
- ggf. Privacy-/Freigabeprüfung.

---

# 7.14 Datenschutz / Barrierefreiheit / Recht

## Quelle
- sichtbare Datenschutz- und Barrierefreiheitsverweise auf der aktuellen Plattform sowie datenschutzbezogene Texte im Kurzbewerbungsformular. 

## Zielabbildung
- `target_domain`: Privacy / Legal / Service
- `target_type`: privacy page / accessibility page / legal page / privacy notice
- `migration_action`: REWRITE + MIGRATE_AND_RESTRUCTURE

## Begründung
Diese Inhalte müssen auf die neue Architektur, neue Formulare, neue Bewerbungslogik und neue Datenschutz-/Retention-Struktur angepasst werden.

## Ownership
- central_owner: Privacy / Compliance + Central HR Career Department

---

# 8. Ownership-Modell für Migration

## 8.1 Zentrale HR-Karriere-Abteilung besitzt dauerhaft
- Karriere-Startseite
- Arbeitgeberseiten
- CareerPath-Seiten
- JobTemplates
- ProcessTemplates
- Initiativbewerbungsseite
- Bewerbungsweg-/FAQ-Basis
- Jobveröffentlichungs-Governance
- zentrale CTA-Logik
- zentrale SEO- und Quality-Leitlinien

## 8.2 Lokale Einheiten dürfen beitragen zu
- lokalen Stelleninhalten innerhalb von Templates
- fachlichen Ergänzungen bei JobDrafts
- lokalen Facility-/Location-Kontexten, wenn im Zielmodell vorgesehen
- kontextbezogenen Ansprechpartnern
- kontrollierten Prozessvarianten innerhalb definierter Grenzen

## 8.3 Privacy / Compliance besitzt oder prüft
- PrivacyNoticeVersionen
- Datenschutzseiten
- Retention-Texte
- Bewerberrechte-Kommunikation
- Lösch- und Kandidat*innen-Pool-Logik

## 8.4 Technische / System-Owner besitzen
- Migrationstooling
- Importvalidierung
- Statusverfolgung
- Referenzintegrität
- technische Datenqualität

---

# 9. Migrationsvalidierung

## 9.1 Strukturvalidierung
Jedes Zielobjekt muss geprüft werden auf:
- korrekten Zieltyp
- Pflichtfelder
- gültige Referenzen
- gültige Slugs / Zielstruktur
- korrekte Zuordnung von Facility, Location, JobFamily, CareerPath

## 9.2 Templatevalidierung
- Seite nutzt den richtigen Seitentyp / das richtige Template
- Job nutzt korrektes JobTemplate
- Pflichtsektionen sind vorhanden
- keine unzulässige Freiform-Struktur, wo Template-Pflicht besteht

## 9.3 Governancevalidierung
- zentraler Owner vorhanden
- lokaler Owner vorhanden, falls nötig
- Workflowstatus korrekt
- Freigabe-/Publikationspfad korrekt

## 9.4 Privacy-/Compliance-Validierung
- Bewerbungsseiten / Formulare sind an PrivacyNoticeVersion gebunden
- keine öffentlichen Kontaktobjekte ohne Kontext
- keine Zieltexte, die dem neuen Privacy-/Retention-Modell widersprechen

## 9.5 Accessibility-Validierung
- Inhalte sind template-kompatibel barrierefrei integrierbar
- Überschriftenstruktur passend
- Formular- und CTA-Inhalte verständlich
- Bild-/Medieninhalte mit Alt-Text-/Kontextprüfung

## 9.6 SEO-Validierung
- Ziel-URL-/Slug-Strategie definiert
- Metadaten vorbereitet
- Canonical-Strategie geklärt
- keine ungewollten Doppelseiten

---

# 10. Migrationsphasen

## Phase 1 – Discovery Inventory
- alle aktuell sichtbaren Enterprise-Karriereinhalte erfassen
- Kategorien zuordnen
- Dopplungen und Überschneidungen identifizieren
- strukturrelevante Daten in Texten identifizieren

## Phase 2 – Mapping
- Zieldomäne zuordnen
- Zieltyp zuordnen
- Migrationsaktion zuordnen
- Ownership und Template zuordnen

## Phase 3 – Content Preparation
- Inhalte restrukturieren
- Wiederholungen normalisieren
- Stammdaten vorbereiten
- Rewrites erstellen, wo nötig

## Phase 4 – Controlled Import / Entry
- strukturierte Stammdaten laden
- Zielseiten anlegen
- Jobs als strukturierte JobPosting-Objekte einbringen
- Workflows / Ownership setzen

## Phase 5 – QA and Sign-Off
- Content QA
- Governance QA
- Privacy / Compliance QA
- Accessibility QA
- SEO QA

## Phase 6 – Go-Live Readiness
- finale Linkprüfung
- finale Ownership-Prüfung
- finale Freigaben
- Redirect-/Korrektur-/Rollback-Plan

---

# 11. Empfohlene Migrationspriorität

## Priorität 1
- Karriere-Startseite
- Arbeitgeberbereich
- Stellenliste / Jobdetailmodell
- Initiativbewerbung / Ihre Bewerbung
- Privacy-/Barrierefreiheitsbasis
- zentrale CareerPath-Seiten

## Priorität 2
- JobFamily-Seiten
- strukturierte Facilities / Locations
- Ansprechpartner-Normalisierung
- FAQ-/Service-/Bewerbungsweg-Inhalte

## Priorität 3
- zusätzliche LandingPages
- vertiefte Standort-/Einrichtungsseiten
- kampagnenbezogene Inhalte
- spätere Erweiterungsinhalte

---

# 12. Offene Migrationsfragen

Vor der vollständigen Migration müssen diese Fragen beantwortet werden:

1. Welche aktuellen Inhalte sind autoritativ, welche redundant?
2. Welche Texte werden wiederverwendet, welche neu geschrieben?
3. Welche JobFamily-Seiten sind MVP-pflichtig?
4. Welche Facility-/Location-Seiten sind MVP-pflichtig?
5. Welche Ansprechpartner sind für die neue Plattform öffentlich freigegeben?
6. Welche aktuellen Datenschutz-/Rechtstexte können übernommen werden?
7. Welche URLs müssen erhalten oder sauber weitergeleitet werden?
8. Welche Inhalte bleiben dauerhaft zentral gepflegt und welche können später kontrolliert lokal ergänzt werden?

---

# 13. Harte Migrationsregel

Ein Inhalt gilt **nicht** als migriert, nur weil er im Zielsystem sichtbar ist.

Ein Inhalt gilt erst dann als migriert, wenn:
- der korrekte Zieltyp gesetzt ist,
- strukturierte Felder befüllt sind,
- Owner und Workflow korrekt gesetzt sind,
- Privacy-/Accessibility-/SEO-Prüfungen erfolgt sind,
- und der Inhalt das neue Enterprise-Betriebsmodell unterstützt.