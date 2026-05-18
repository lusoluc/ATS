# Enterprise Karriereplattform – Finales Master-Dokumentenpaket (aktuellste Version)

> Stand: 2026-05-13  
> Zweck: Sammeldokument mit den **letzten / neuesten Versionen** aller final relevanten Dokumente aus dem bisherigen Konzept- und Umsetzungsprozess für die neue Karriereplattform des Enterprises.

---

# Inhaltsverzeichnis

1. [00_FINAL_SOURCE_OF_TRUTH.md](#00_final_source_of_truthmd)
2. [06_Consolidated_Master_Concept.md](#06_consolidated_master_conceptmd)
3. [13_Content_Migration_and_Inventory.md](#13_content_migration_and_inventorymd)
4. [14_Security_Architecture_and_Certificate_Guide.md](#14_security_architecture_and_certificate_guidemd)
5. [15_Implementation_Control_Checklist.md](#15_implementation_control_checklistmd)
6. [16_Project_Delivery_Roadmap_and_Workstreams.md](#16_project_delivery_roadmap_and_workstreamsmd)
7. [17_Backlog_Epics_and_User_Stories.md](#17_backlog_epics_and_user_storiesmd)
8. [18_Master_Document_Index_and_Usage_Guide.md](#18_master_document_index_and_usage_guidemd)
9. [19_Senior_Developer_Agent_Handover_Prompt.md](#19_senior_developer_agent_handover_promptmd)
10. [21_Wave_1_Implementation_Package.md](#21_wave_1_implementation_packagemd)
11. [22_Wave_1_Technical_Work_Package_01_Core_Model_and_Auth.md](#22_wave_1_technical_work_package_01_core_model_and_authmd)
12. [23_Wave_1_Technical_Work_Package_02_API_and_Workflow_Foundation.md](#23_wave_1_technical_work_package_02_api_and_workflow_foundationmd)
13. [24_Wave_1_Technical_Work_Package_03_Public_Experience_and_Job_Governance_Realization.md](#24_wave_1_technical_work_package_03_public_experience_and_job_governance_realizationmd)
14. [25_Wave_1_Technical_Work_Package_04_Local_Recruiting_Operations_and_Applicant_Access_Realization.md](#25_wave_1_technical_work_package_04_local_recruiting_operations_and_applicant_access_realizationmd)
15. [26_Wave_1_Technical_Work_Package_05_Privacy_Retention_Compliance_and_Hardening.md](#26_wave_1_technical_work_package_05_privacy_retention_compliance_and_hardeningmd)
16. [27_Wave_1_Technical_Work_Package_06_Migration_Completion_Readiness_and_Final_Wave_1_Release_Preparation.md](#27_wave_1_technical_work_package_06_migration_completion_readiness_and_final_wave_1_release_preparationmd)
17. [29_Developer_Agent_Execution_Bundle.md](#29_developer_agent_execution_bundlemd)

---

# 00_FINAL_SOURCE_OF_TRUTH.md

## Dokumentstatus
- Version: 2.0
- Status: verbindlich
- Zweck: einzige verbindliche fachlich-technische Quelle für die Umsetzung einer spezialisierten Karriereplattform für den Enterprise
- Gültigkeit: ersetzt alle externen Produktvergleiche, Benchmark-Verweise und impliziten Fremdannahmen
- Ziel: sichere, kontrollierte und schrittweise Umsetzung einer Enterprise-spezifischen Karriereplattform

---

## 1. Verbindlicher Grundsatz

Dieses Dokument ist die einzige verbindliche Quelle für die Umsetzung.

### 1.1 Enterprise-Only Rule
Die Umsetzung basiert ausschließlich auf:
- den fachlichen und strukturellen Anforderungen für den Enterprise,
- den verifizierten sichtbaren Elementen der aktuellen Karrierepräsenz,
- den explizit definierten Zielentscheidungen dieses Dokuments,
- und den vom Auftraggeber/Projektkontext festgelegten Organisations- und Governance-Regeln.

Es dürfen **keine externen Produktlogiken** nachgebaut oder stillschweigend übernommen werden.

### 1.2 No External Dependency Rule
Der Senior Developer Agent darf sich **nicht** auf externe Recruiting-Produkte, externe CMS-Produkte oder generische ATS-Annahmen stützen.

Er darf insbesondere nicht:
- externe Recruiting-Plattformen nachbauen,
- fehlende Logik aus fremden Produkten ableiten,
- Standardverhalten aus generischen ATS-/CMS-Produkten übernehmen,
- offene Punkte selbst erfinden.

### 1.3 Pflicht bei Unklarheit
Wenn Informationen fehlen, muss der Agent:
1. die Lücke explizit benennen,
2. das Risiko beschreiben,
3. eine Entscheidungsvorlage formulieren,
4. und an der kritischen Stelle stoppen, wenn die Lücke die fachliche oder sicherheitsrelevante Integrität gefährdet.

---

## 2. Verifizierter aktueller Enterprise-Kontext

### 2.1 Aktuelle Karrierepräsenz
Die aktuelle Karrierepräsenz des Enterprises enthält sichtbar mindestens folgende Hauptbereiche:
- Arbeitgeber Enterprise,
- Beruf und Karriere,
- Stellenangebote,
- Initiativbewerbung,
- Ihr Weg zu uns,
- sowie Ansprechpersonen / Ansprechpartner-Kontexte.

Die Plattform enthält außerdem sichtbare Verweise auf Datenschutz und Barrierefreiheit.

### 2.2 Sichtbare Karrierepfade
Die aktuelle Karrierepräsenz differenziert bereits mehrere Karriere- bzw. Recruiting-Einstiege:
- Ausbildung,
- Freiwilligendienst: FSJ und BFD,
- Praktikum,
- Praktisches Jahr und ärztliche Weiterbildung,
- Fortbildung und Weiterbildung.

### 2.3 Sichtbare Jobsuche / Stellenlogik
Die aktuelle Stellenlogik arbeitet bereits mit strukturierten Datenfeldern, darunter:
- Referenz,
- Einrichtung,
- Ort,
- Beginn,
- Stundenumfang,
- Befristung.

Zusätzlich ist die Jobsuche mit Berufsfeld-/Kategorielogik verbunden.

### 2.4 Arbeitgeber- und Organisationsbreite
Der Arbeitgeberbereich beschreibt den Enterprise als großen Träger im Gesundheits- und Sozialwesen mit mehreren Einrichtungen, verschiedenen Standorten und vielfältigen Arbeits- und Berufsfeldern.

Die Seite „Arbeits- und Berufsfelder“ zeigt eine sehr breite Vielfalt fachlicher Felder und Berufe, darunter Pflege, Medizin, Pädagogik/Therapie, Verwaltung, Technik, Küche, Landwirtschaft und weitere Tätigkeitsprofile.

### 2.5 Aktuelle Bewerbungslogik
Die aktuelle Karrierepräsenz beschreibt mindestens folgende Bewerbungswege:
- Bewerbung auf ausgeschriebene Stellen per in der Anzeige angegebener E-Mail-Adresse,
- Bewerbung für Praktikum / FSJ / Bundesfreiiwilligendienst per E-Mail,
- ein Kurzbewerbungsformular für Interessierte, die zunächst unverbindlich Kontakt aufnehmen wollen.

Die aktuelle Seite nennt außerdem ausdrücklich:
- einen Datenschutzhinweis / Zustimmung im Formular,
- sowie den Hinweis, dass Daten nach sechs Monaten gelöscht werden, wenn keine Bewerbung oder keine Einwilligung in die Aufnahme in den Kandidat*innen-Pool vorliegt.

---

## 3. Zielsystem

### 3.1 Produktdefinition
Das Zielsystem ist eine spezialisierte Karriereplattform für den Enterprise mit:
- mehreren Karrierepfaden,
- vielen Berufsfeldern,
- verschiedenen Einrichtungen,
- mehreren Standorten,
- strukturierten Stellenanzeigen,
- Initiativbewerbung,
- zentraler Governance,
- dezentraler operativer Beteiligung,
- Anforderungen an Barrierefreiheit,
- Anforderungen an Datenschutz,
- Anforderungen an Suchmaschinenfreundlichkeit,
- und klarer Erweiterbarkeit.

### 3.2 Systemcharakter
Das Zielsystem ist:
- **kein Nachbau eines generischen Recruiting-Produkts**
- **kein reines Website-CMS**
- **kein vollständiges ATS in der ersten Version**
- **keine bloße Neuverpackung der aktuellen Seiten**

Das Zielsystem ist:
- eine modulare Karriereplattform,
- mit strukturierten Karriereinhalten,
- strukturierten Jobdaten,
- klaren Such- und Bewerbungswegen,
- Rollen- und Freigabemodell,
- Template-Governance,
- Datenschutz-/Sicherheitsbasis,
- und kontrollierter lokaler Beteiligung.

---

## 4. Produktziele

### 4.1 Hauptziele
1. Die bestehende Karriere- und Recruiting-Komplexität des Enterprises klar und strukturiert abbilden.
2. Mehrere Karrierepfade und Berufsfelder gezielt und verständlich darstellen.
3. Stellen strukturiert, konsistent und suchbar verwalten und ausspielen.
4. Initiativbewerbung und ausgeschriebene Bewerbungswege sauber unterstützen.
5. Lokale fachliche Beteiligung ermöglichen, ohne zentrale Governance zu verlieren.
6. Fehler durch Templates, Pflichtfelder, Freigaben und kontrollierte Prozesse minimieren.
7. Datenschutz, Barrierefreiheit, Suchmaschinenfreundlichkeit und Auditierbarkeit systemisch einbauen.
8. Die Lösung so definieren, dass ein Senior Developer Agent sie ohne externe Referenzen umsetzen kann.

### 4.2 Nicht-Ziele in der ersten Version
Die erste Version soll **nicht** umfassen:
- vollständige Kandidatenakte eines vollwertigen ATS,
- Onboarding-Portal,
- Messaging-Automation,
- Online-Assessments,
- generisches CRM,
- tiefgreifende Drittsystem-Integrationen, sofern nicht separat freigegeben,
- unkontrollierte lokale Eigenprozesse.

---

## 5. Betriebsmodell (Operating Model)

### 5.1 Zentrale HR-Karriere-Abteilung
Die zentrale HR-Karriere-Abteilung ist die zentrale Governance- und Qualitätsinstanz der Plattform.

#### Verantwortlichkeiten
- Definition und Pflege von Stellenanzeigen-Templates
- Definition und Pflege von Recruiting-Prozess-Templates
- Definition von Pflichtfeldern und Mindestprozessstandards
- Prüfung und Freigabe öffentlicher Stellenanzeigen vor Veröffentlichung
- zentrale Candidate-Experience-Standards
- zentrale Qualitätsstandards
- zentrale SEO-, Accessibility- und Privacy-Standards
- KPI-/Funnel-/Prozessoptimierung
- Koordination und kontinuierliche Verbesserung der Karriereplattform

### 5.2 Standorte und Bereiche
Standorte und Bereiche sind für die operative Recruiting-Ausführung im eigenen Kontext verantwortlich.

#### Verantwortlichkeiten
- Erstellung von Stellenanzeigen-Entwürfen auf Basis genehmigter Templates
- fachliche Ergänzung lokaler Stellenspezifika
- Prüfung der Eignung von Bewerberinnen und Bewerbern für die eigenen Vakanzen
- Entscheidung, ob und wann eingeladen wird
- Durchführung lokaler Auswahl- und Interview-Schritte
- Ausführung lokaler Prozessschritte innerhalb genehmigter Varianten

### 5.3 Federiertes Modell
Das Zielbetriebsmodell ist **federiert**:
- zentrale Governance und Standardisierung,
- lokale fachliche Verantwortung für Eignungsprüfung und Einladung,
- kontrollierte lokale Varianten,
- keine völlig freien, unkontrollierten Eigenprozesse.

### 5.4 Harte Regel
Öffentliche Veröffentlichung von Stellenanzeigen ist **nur nach Freigabe durch die zentrale HR-Karriere-Abteilung** zulässig.

---

## 6. Fachliche Kernbegriffe (Glossar)

Diese Begriffe sind verbindlich und dürfen nicht vermischt werden.

### 6.1 Organization
Die Gesamtorganisation / der Träger.

### 6.2 Facility
Eine organisatorische Einheit oder Einrichtung.

### 6.3 Location
Ein geografischer Ort / Standort.

### 6.4 JobFamily
Ein Berufsfeld bzw. fachlicher Tätigkeitscluster.

### 6.5 CareerPath
Ein Karrierepfad bzw. Recruiting-Einstieg.

### 6.6 CareerPage
Eine redaktionelle Seite im Karrierekontext.

### 6.7 LandingPage
Eine zielgruppenspezifische oder kampagnenbezogene Seite mit definierter Conversion-Absicht.

### 6.8 JobPosting
Ein strukturiertes Stellenobjekt.

### 6.9 ApplicationForm
Ein strukturiertes Bewerbungsformular.

### 6.10 ApplicationRoute
Die strukturierte Logik, an die Bewerbungen weitergeleitet oder zugeordnet werden.

### 6.11 ContactPerson
Ein öffentlich sichtbarer Ansprechpartner.

### 6.12 SharedContentModule
Ein wiederverwendbares Inhaltsmodul.

### 6.13 JobTemplate
Ein zentral gepflegtes Template für Stellenanzeigen.

### 6.14 ProcessTemplate
Ein zentral gepflegtes Recruiting-Prozess-Template.

### 6.15 LocalProcessVariant
Eine kontrollierte lokale Prozessvariante innerhalb genehmigter Grenzen.

---

## 7. Harte Modellierungsregeln

### 7.1 Do-not-merge-Regeln
Die folgenden Konzepte müssen strikt getrennt bleiben:
- Facility != Location
- JobFamily != CareerPath
- CareerPage != JobPosting
- LandingPage != CareerPage
- ApplicationForm != ApplicationRoute
- redaktioneller Inhalt != strukturierte Jobdaten

### 7.2 Do-not-infer-Regeln
Es darf nicht automatisch angenommen werden:
- dass jede Stelle denselben Bewerbungsweg hat,
- dass jede Einrichtung nur einen Standort hat,
- dass jede Karrierepfadseite dieselben Felder braucht,
- dass Ansprechpartner global statt kontextbezogen sind,
- dass Jobs als Freitextseiten modelliert werden dürfen.

### 7.3 Struktur vor Freitext
Wo immer möglich, müssen strukturierte Felder statt unstrukturierter Freitext-Container verwendet werden.

---

## 8. Verbindliche Domänen des Systems

### 8.1 Organization Domain
Verantwortlich für:
- Organization
- Facility
- Location
- JobFamily
- CareerPath
- ContactPerson

### 8.2 Content Domain
Verantwortlich für:
- CareerPage
- LandingPage
- SharedContentModule
- SEOProfile
- MediaAsset

### 8.3 Job Domain
Verantwortlich für:
- JobPosting
- Job-spezifische Inhalte
- Jobstatus
- Jobveröffentlichung

### 8.4 Application Domain
Verantwortlich für:
- ApplicationForm
- ApplicationRoute
- Bewerbungs-CTA
- Dokumentlogik
- Submission-Mode

### 8.5 Governance Domain
Verantwortlich für:
- WorkflowState
- Role
- Permission
- Freigaben
- Ownership
- Auditierbarkeit

### 8.6 Discovery Domain
Verantwortlich für:
- Jobsuche
- Filter
- Listen
- Zielgruppeneinstiege

### 8.7 Privacy / Security / Analytics Domain
Verantwortlich für:
- PrivacyNoticeVersion
- DataRetentionPolicy
- ApplicantAccessAssignment
- Audit-Events
- Sicherheits- und Monitoringlogik
- Analytics Events

---

## 9. Verbindliches Page- und Navigation-Modell

### 9.1 Hauptnavigation im Zielsystem
Die Zielplattform muss mindestens folgende Hauptbereiche unterstützen:
- Arbeitgeber
- Beruf & Karriere
- Stellenangebote
- Initiativbewerbung
- Ihr Weg zu uns / Bewerbung
- Ansprechpartner / Kontakt
- Service-/Recht-/Datenschutz-/Barrierefreiheitsseiten

### 9.2 Verbindliche Seitentypen
- Karriere-Startseite
- Arbeitgeberseite
- Berufsfeldseite
- Karrierepfadseite
- Standortseite
- Einrichtungsseite
- LandingPage
- Stellenliste
- Stellentdetailseite
- Initiativbewerbungsseite
- Kontakt-/Ansprechpartnerseite
- FAQ-/Service-Seite
- Datenschutz-/Barrierefreiheits-/rechtliche Seite

### 9.3 Pflicht-Einstiege auf der Karriere-Startseite
Die Karriere-Startseite muss mindestens folgende Einstiegspfade ermöglichen:
- Jobsuche,
- Karrierepfade,
- Berufsfelder oder Arbeitgeberbereich,
- Initiativbewerbung.

---

## 10. Verbindliches Entitätenmodell

### 10.1 Mindestentitäten
Die Plattform muss mindestens die folgenden Entitäten unterstützen:
- Organization
- Facility
- Location
- JobFamily
- CareerPath
- ContactPerson
- CareerPage
- LandingPage
- JobPosting
- ApplicationForm
- ApplicationRoute
- WorkflowState
- Role
- Permission
- SEOProfile
- MediaAsset
- SharedContentModule
- JobTemplate
- ProcessTemplate
- LocalProcessVariant
- PrivacyNoticeVersion
- DataRetentionPolicy
- ApplicantAccessAssignment
- HiringDecisionStage
- AnalyticsEventDefinition

### 10.2 Harte Mindestbeziehungen
- JobPosting gehört mindestens zu:
  - einer Organization,
  - einer Facility,
  - einer Location,
  - einer JobFamily
- CareerPage kann kontextbezogen auf JobFamily, CareerPath, Facility oder Location referenzieren
- ApplicationForm muss mit PrivacyNoticeVersion verknüpft werden
- ApplicantAccessAssignment muss einen klaren Rollen- und Kontextbezug haben

---

## 11. Such- und Discovery-Modell

### 11.1 Mindestfilter
Die Jobsuche muss mindestens folgende strukturierte Filter unterstützen:
- JobFamily / Berufsfeld
- Location / Ort
- Facility / Einrichtung
- Beschäftigungsart oder Stundenumfang
- CareerPath, sofern fachlich passend

### 11.2 Harte Discovery-Regeln
- Filter müssen kombinierbar sein.
- Trefferlisten müssen verständlich und mobil nutzbar sein.
- Es darf nicht nur eine generische Volltextsuche ohne strukturierte Filter geben.
- Leere Trefferlisten müssen sinnvolle nächste Schritte anbieten.

---

## 12. Bewerbungsmodell

### 12.1 Mindest-Bewerbungsarten
Die Plattform muss mindestens folgende Arten unterstützen:
- Bewerbung auf konkrete Stelle
- Initiativbewerbung
- karrierepfadbezogene Bewerbung, sofern explizit freigegeben

### 12.2 Aktueller Enterprise-Bezug
Die aktuelle Plattform unterstützt heute bereits:
- Bewerbung auf ausgeschriebene Stellen,
- Bewerbung für Praktikum / FSJ / BFD,
- sowie eine Kurzbewerbungs-/Interessenlogik.

### 12.3 Harte Zielregeln
- Jede veröffentlichte Stelle muss ein Bewerbungsziel haben.
- Initiativbewerbung muss als eigener sauber modellierter Flow existieren.
- Bewerbungswege dürfen nicht nur informell in Freitext beschrieben sein.
- Routing / Zuordnung muss strukturierbar sein.

---

## 13. Rollenmodell

### 13.1 Mindestrollen
Die Plattform muss mindestens folgende Rollen unterstützen:
- GlobalAdmin
- CMSOwner
- CentralHRCareerAdmin
- JobEditor
- LocalEditor
- LocalHiringReviewer
- LocalInterviewCoordinator
- SEOQAReviewer
- PrivacyComplianceReviewer
- Publisher
- Analyst

### 13.2 Zentrale Rollenlogik
- Zentrale HR-Karriere steuert Templates, Standards, Prüfung und Freigabe.
- Lokale Einheiten prüfen fachlich Eignung und führen Auswahl-/Einladungsschritte aus.
- Veröffentlichung erfolgt nicht direkt lokal ohne zentrale Freigabe.
- Analysten sehen keine operativen Bewerberdetails ohne separate Berechtigung.

---

## 14. Workflowregeln

### 14.1 Standardstatus
- draft
- in_review
- approved
- published
- archived
- rejected

### 14.2 Seitenworkflow
1. anlegen
2. bearbeiten
3. submit_for_review
4. QA/SEO Review
5. approve
6. publish

### 14.3 Jobworkflow
1. Job anlegen
2. Pflichtfelder vervollständigen
3. Bewerbungslogik zuordnen
4. zur Prüfung einreichen
5. zentrale HR prüft
6. approve / reject
7. publish
8. deactivate / archive

### 14.4 Bewerberworkflow
1. Bewerbung eingehen
2. Kontextbezogene Zuordnung
3. Access Assignment
4. lokale Eignungsprüfung
5. Einladung / weiterer Prozessschritt
6. Ergebnis / Ausgang
7. Retention-/Löschlogik auslösen

### 14.5 Harte Workflow-Regeln
- Keine Veröffentlichung ohne Review.
- Keine Veröffentlichung ohne Owner.
- Kein veröffentlichter Job ohne Bewerbungsziel.
- Keine öffentliche Stellenanzeige ohne zentrale Freigabe.
- Keine lokale Prozessvariante ohne zentrale Genehmigung.
- Keine öffentliche Bewerbungslogik ohne Privacy-/Retention-Basis.

---

## 15. Template- und Prozessgovernance

### 15.1 JobTemplates
Stellenanzeigen müssen template-basiert erstellt werden, wenn für den jeweiligen Bereich / Karrierepfad / Jobkontext ein Template definiert ist.

#### Mindestzweck
- Pflichtfelder erzwingen
- Fehlerrisiko reduzieren
- Wortlautqualität verbessern
- Konsistenz sichern
- Freigabe erleichtern

### 15.2 ProcessTemplates
Recruiting-Prozesse müssen über zentrale ProcessTemplates definiert werden.

#### Mindestzweck
- Mindestprozess sichern
- lokale Unterschiede kontrollieren
- KPI-Vergleichbarkeit erhalten
- Fehler und Compliance-Risiken reduzieren

### 15.3 LocalProcessVariant
Lokale Unterschiede dürfen nur als **kontrollierte Varianten** existieren:
- innerhalb definierter Grenzen,
- zentral genehmigt,
- auditiert,
- nicht frei erfunden.

---

## 16. Datenschutz- und Bewerberdatenschutzregeln

### 16.1 Aktueller Enterprise-Bezug
Die aktuelle Plattform zeigt bereits:
- Datenschutzzustimmung im Kurzbewerbungsformular,
- Kandidat*innen-Pool-Bezug,
- sowie Löschung nach sechs Monaten, wenn keine Bewerbung oder keine Einwilligung in den Pool vorliegt.

### 16.2 Zielregeln
Die Plattform muss Bewerberdatenschutz **by design and by default** unterstützen.

#### Mindestprinzipien
- Zweckbindung
- Datenminimierung
- Speicherbegrenzung
- Integrität und Vertraulichkeit
- Nachvollziehbarkeit / Accountability
- Need-to-know Zugriff

### 16.3 Pflichtobjekte
- PrivacyNoticeVersion
- DataRetentionPolicy
- ApplicantAccessAssignment

### 16.4 Harte Regeln
- Kein öffentliches Formular ohne gültige PrivacyNoticeVersion
- Kein Bewerberzugriff ohne Rollen- und Kontextbezug
- Keine unbegrenzte Speicherung von Bewerberdaten
- Keine breite standortübergreifende Einsicht in Bewerberdaten ohne ausdrückliche Legitimation

---

## 17. Sicherheitsregeln

### 17.1 Mindestanforderungen
Die Plattform muss mindestens unterstützen:
- HTTPS-only
- starke Authentifizierung für interne Rollen
- MFA für privilegierte Rollen
- objektbezogene Autorisierung
- kontextgebundene Bewerberzugriffe
- Audit Logging
- Zertifikats- und Secret-Management
- mTLS für privilegierte interne Service-zu-Service-Kommunikation, sofern dafür vorgesehen

### 17.2 Harte Regeln
- Kein geschützter interner Endpunkt anonym
- keine Veröffentlichung ohne Autorisierung
- keine sensible Bewerberdaten-Einsicht ohne Rollen- und Kontextprüfung
- keine produktive Nutzung ohne gültige Zertifikate und TLS-Baseline
- keine Secrets oder privaten Schlüssel hart im Code

---

## 18. Accessibility- und SEO-Regeln

### 18.1 Accessibility
Die Plattform muss Barrierefreiheit als Kernanforderung behandeln.

#### Mindestanforderungen
- semantische Struktur
- Tastaturbedienbarkeit
- sinnvolle Labels
- verständliche Fehlermeldungen
- Fokuszustände
- verständliche Linktexte

### 18.2 SEO
Die Plattform muss suchmaschinenfreundliche Karriere- und Jobinhalte unterstützen.

#### Mindestanforderungen
- sprechende URLs
- page-level title / description
- canonical handling
- strukturierte Jobdaten
- indexierbare Jobdetailseiten
- sinnvolle interne Verlinkung

---

## 19. Migration-Grundsatz

### 19.1 Enterprise als Content-Quelle
Für Inhalte und aktuelle Struktur ist die aktuelle Enterprise-Karriereseite die Ausgangsbasis.

Das betrifft insbesondere:
- Karriere-Startlogik,
- Karrierepfade,
- Arbeitgeberinhalte,
- Berufsfelder,
- Stellenlogik,
- Bewerbungs-/Kontakt-/Service-Inhalte.

### 19.2 Harte Migrationsregel
Inhalte gelten nicht als migriert, nur weil sie visuell kopiert wurden.

Inhalte gelten erst dann als migriert, wenn:
- sie dem richtigen Zieltyp zugeordnet sind,
- strukturierte Felder korrekt befüllt sind,
- Ownership definiert ist,
- Workflow und Governance korrekt greifen,
- Privacy-/Accessibility-/SEO-Prüfungen erfolgt sind,
- und die Inhalte das neue Betriebsmodell unterstützen.

---

## 20. Implementierungsregeln für den Senior Developer Agent

### 20.1 Vor jeder großen Umsetzungsphase liefern
Der Agent muss vor jedem größeren Schritt liefern:
1. Ziel
2. Inputs
3. Annahmen
4. Risiken
5. Output-Artefakte
6. Test-/Abnahmekriterien

### 20.2 Stop-and-Escalate-Regeln
Der Agent muss stoppen und eskalieren bei:
- unklarer Trennung zwischen Facility und Location,
- unklarer Trennung zwischen JobFamily und CareerPath,
- fehlendem Bewerbungsziel,
- unklarer zentraler vs. lokaler Zuständigkeit,
- fehlender Privacy-/Retention-Basis,
- fehlendem Kontext für öffentliche Ansprechpartner.

### 20.3 Verbotene Abkürzungen
Der Agent darf nicht:
- JobPosting als unstrukturierte CMS-Seite behandeln,
- JobFamily oder CareerPath als Freitextfeld modellieren,
- zentrale Freigabeprozesse überspringen,
- lokale Eigenprozesse unkontrolliert öffnen,
- Datenschutz-/Security-/Accessibility-Themen auf „später“ verschieben,
- externe Produktlogiken stillschweigend übernehmen.

---

## 21. Letzte verbindliche Regel

Wenn dieses Dokument und ein anderes älteres Dokument widersprüchlich sind, gilt **immer dieses Dokument**.

Wenn dieses Dokument an einer Stelle unvollständig ist, muss der Agent **nicht raten**, sondern die Lücke explizit melden.

---

# 06_Consolidated_Master_Concept.md

## Dokumentstatus
- Version: 2.0
- Zweck: Konsolidierte Gesamtversion für das Zielbild der neuen Karriereplattform des Enterprises
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, implementierungsnah
- Regel: Wenn dieses Dokument anderen älteren Zwischenständen widerspricht, gilt dieses Dokument

---

## 1. Executive Summary

Der Enterprise verfügt bereits heute über eine Karrierepräsenz mit mehreren klar sichtbaren Bereichen wie Arbeitgeber, Beruf und Karriere, Stellenangebote, Initiativbewerbung und „Ihr Weg zu uns“. Zusätzlich sind Ansprechpartner-/Kontaktbezüge, Datenschutz und Barrierefreiheit sichtbar eingebunden.

Die Karriereplattform unterscheidet bereits mehrere Recruiting- und Karriereeinstiege, darunter Ausbildung, Freiwilligendienst (FSJ/BFD), Praktikum, Praktisches Jahr / ärztliche Weiterbildung sowie Fortbildung und Weiterbildung.

Die Stellenlogik ist bereits strukturiert und enthält Felder wie Referenz, Einrichtung, Ort, Beginn, Stundenumfang und Befristung.

Daraus folgt:  
Das Zielsystem darf nicht als einfache Karriereseite oder bloße Jobliste gedacht werden, sondern als **strukturierte Karriereplattform** mit:
- redaktionellen Karriereinhalten,
- strukturierten Jobdaten,
- zentraler Governance,
- lokaler operativer Recruiting-Ausführung,
- Datenschutz- und Sicherheitslogik,
- Barrierefreiheit,
- und suchmaschinenfreundlicher Job-/Karriereausspielung.

---

## 2. Verifizierter Enterprise-Ausgangszustand

### 2.1 Sichtbare Hauptbereiche
Die aktuelle Karrierepräsenz enthält sichtbar:
- Arbeitgeber Enterprise,
- Beruf und Karriere,
- Stellenangebote,
- Initiativbewerbung,
- Ihr Weg zu uns,
- Kontakt-/Ansprechpersonen-Kontexte,
- Datenschutz,
- Barrierefreiheit.

### 2.2 Sichtbare Karrierepfade
Aktuell sichtbar sind mindestens:
- Ausbildung,
- Freiwilligendienst: FSJ und BFD,
- Praktikum,
- Praktisches Jahr und ärztliche Weiterbildung,
- Fortbildung und Weiterbildung.

### 2.3 Sichtbare Job- und Suchlogik
Die aktuelle Stellenliste arbeitet bereits mit strukturierten Attributen wie:
- Referenz,
- Einrichtung,
- Ort,
- Beginn,
- Stundenumfang,
- Befristung.

Zusätzlich ist eine Berufsfeld-/Kategorielogik erkennbar.

### 2.4 Sichtbare organisatorische Breite
Die Arbeitgeber- und Berufsfeldseiten zeigen, dass der Enterprise ein großer Träger mit mehreren Einrichtungen, Standorten und sehr unterschiedlichen Arbeits- und Berufsfeldern ist. Sichtbar sind Tätigkeiten unter anderem in Suchthilfe, psychiatrischer Hilfe, Behindertenhilfe, Altenhilfe sowie in Küche, Technik, Handwerk, Verwaltung und weiteren Bereichen.

### 2.5 Sichtbare Bewerbungslogik
Die aktuelle Karrierepräsenz beschreibt:
- Bewerbung auf ausgeschriebene Stellen per E-Mail an die in der Anzeige genannte Adresse,
- Bewerbung für Praktikum / FSJ / BFD per E-Mail,
- ein Kurzbewerbungsformular für unverbindliches Interesse oder schnellen Erstkontakt.

Im Kurzbewerbungsformular ist ein Datenschutzbezug sichtbar, und es wird ausdrücklich darauf hingewiesen, dass Daten nach sechs Monaten gelöscht werden, sofern keine Bewerbung oder keine Einwilligung in einen Kandidat*innen-Pool vorliegt.

---

## 3. Zielbild

### 3.1 Zielsystem
Das Zielsystem ist eine spezialisierte Karriereplattform für den Enterprise mit:
- mehreren Karrierepfaden,
- vielen Berufsfeldern,
- verschiedenen Einrichtungen,
- mehreren Standorten,
- strukturierten Stellenanzeigen,
- Initiativbewerbung,
- zentraler Governance,
- lokaler fachlicher Recruiting-Beteiligung,
- Datenschutz-/Sicherheitsbasis,
- Barrierefreiheit,
- SEO-/Discoverability-Fähigkeit,
- und klarer Erweiterbarkeit.

### 3.2 Kein Ziel
Das Zielsystem ist **nicht**:
- ein generisches Standard-ATS für beliebige Unternehmen,
- ein bloßer Relaunch der aktuellen Website,
- ein reines Content-CMS ohne strukturierte Recruiting-Logik,
- ein vollständiges Enterprise-ATS in der ersten Version.

### 3.3 Kernprinzip
Die Plattform muss gleichzeitig zwei Dinge leisten:
1. **Candidate Experience / Career Experience**  
   klare Einstiege, klare Wege, passende Inhalte, klare Bewerbungspfade
2. **Governed Recruiting Operations**  
   Templates, Freigaben, Rollen, strukturierte Prozesse, kontrollierte lokale Varianten

---

## 4. Operating Model

### 4.1 Zentrale HR-Karriere-Abteilung
Die zentrale HR-Karriere-Abteilung koordiniert, standardisiert und optimiert die Karriereplattform.

#### Verantwortlichkeiten
- Definition und Pflege von Stellenanzeigen-Templates
- Definition und Pflege von Recruiting-Prozess-Templates
- Definition von Pflichtfeldern und Qualitätsstandards
- Prüfung und Freigabe öffentlicher Stellenanzeigen
- zentrale Candidate-Experience-Standards
- zentrale SEO-, Accessibility- und Privacy-Standards
- KPI-/Funnel-/Prozessoptimierung

### 4.2 Standorte und Bereiche
Standorte und Bereiche führen operative Recruiting-Aufgaben im eigenen Kontext aus.

#### Verantwortlichkeiten
- Erstellen von Stellenanzeigen-Entwürfen auf Basis von Templates
- lokale fachliche Ergänzungen
- fachliche Prüfung der Eignung von Bewerberinnen und Bewerbern
- Entscheidung über Einladung / Interview / nächsten Schritt
- Ausführung lokaler Recruiting-Schritte innerhalb genehmigter Grenzen

### 4.3 Zielmodell
Das Zielmodell ist **federiert**:
- zentrale Governance,
- lokale operative Recruiting-Verantwortung,
- kontrollierte lokale Varianten,
- keine freien, unkontrollierten Sonderprozesse.

### 4.4 Harte Regel
Öffentliche Stellenanzeigen dürfen nur nach zentraler Freigabe veröffentlicht werden.

---

## 5. Design Drivers

### 5.1 Multi-Karrierepfad-Fähigkeit
Die Plattform muss mehrere Karrierepfade nativ unterstützen, weil diese bereits heute sichtbar und inhaltlich unterschiedlich ausgeprägt sind.

### 5.2 Strukturierte Joblogik
Jobs müssen als strukturierte Objekte modelliert werden, weil die aktuelle Seite bereits eindeutig strukturierte Stellenattribute nutzt.

### 5.3 Trennung von Einrichtung, Ort, Berufsfeld und Karrierepfad
Diese Konzepte sind in der aktuellen Plattform sichtbar unterschiedlich und müssen deshalb im Zielmodell getrennt bleiben.

### 5.4 Dezentrale operative Beteiligung bei zentraler Governance
Die neue Lösung muss lokale Recruiting-Beteiligung erlauben, aber zentrale Qualitäts- und Freigabekontrolle sicherstellen.

### 5.5 Datenschutz und Need-to-Know-Zugriffe
Da die Plattform Bewerberdaten verarbeitet und der Enterprise bereits heute Datenschutzinformationen und Löschhinweise im Bewerbungszusammenhang ausweist, muss das Zielsystem Datenschutz by design unterstützen.

### 5.6 Barrierefreiheit und Servicequalität
Da Barrierefreiheit auf der aktuellen Seite sichtbar verankert ist, muss Accessibility im Zielsystem eine Kernanforderung sein.

---

## 6. Domain Model (konsolidiert)

### 6.1 Kernentitäten
- Organization
- Facility
- Location
- JobFamily
- CareerPath
- ContactPerson
- CareerPage
- LandingPage
- JobPosting
- ApplicationForm
- ApplicationRoute
- WorkflowState
- Role
- Permission
- SEOProfile
- MediaAsset
- SharedContentModule
- JobTemplate
- ProcessTemplate
- LocalProcessVariant
- PrivacyNoticeVersion
- DataRetentionPolicy
- ApplicantAccessAssignment
- HiringDecisionStage
- AnalyticsEventDefinition

### 6.2 Kritische Beziehungen
- JobPosting muss mindestens zu Facility, Location und JobFamily gehören.
- CareerPage kann kontextbezogen auf JobFamily, CareerPath, Facility oder Location verweisen.
- ApplicationForm muss an PrivacyNoticeVersion gebunden sein.
- ApplicantAccessAssignment muss eine klare Rollen- und Kontextzuordnung besitzen.
- LocalProcessVariant darf zentrale Pflichtschritte nicht entfernen.

---

## 7. Informationsarchitektur

### 7.1 Hauptnavigation im Zielsystem
Die Zielplattform muss mindestens diese Hauptbereiche unterstützen:
- Arbeitgeber
- Beruf & Karriere
- Stellenangebote
- Initiativbewerbung
- Ihr Weg zu uns / Bewerbung
- Ansprechpartner / Kontakt
- Service / FAQ / Datenschutz / Barrierefreiheit / rechtliche Seiten

### 7.2 Verbindliche Seitentypen
- Karriere-Startseite
- Arbeitgeberseite
- Berufsfeldseite
- Karrierepfadseite
- Standortseite
- Einrichtungsseite
- Landingpage
- Stellenliste
- Stellentdetailseite
- Initiativbewerbung
- Ansprechpartnerseite
- FAQ-/Service-Seiten

---

## 8. Content Model

### 8.1 Grundsatz
Die Plattform muss redaktionelle Inhalte und strukturierte Jobdaten sauber trennen.

### 8.2 Strukturierte Content-Typen
- Shared modules
- employer content
- job family pages
- career path pages
- service pages
- contact content
- privacy/legal/service content
- landing pages
- structured jobs

### 8.3 Wiederverwendung
Wiederkehrende Inhalte sollen in SharedContentModules oder anderen strukturierten Zielobjekten wiederverwendbar gemacht werden, statt redundante Einzelseiten zu pflegen.

---

## 9. Workflowmodell

### 9.1 Seitenworkflow
1. Draft
2. Bearbeitung
3. Review
4. QA / SEO / Accessibility Review
5. Approval
6. Publish

### 9.2 Jobworkflow
1. lokaler Jobentwurf
2. Pflichtfelder / Struktur vervollständigen
3. Bewerbungslogik und Routing zuweisen
4. zentrale Review-Einreichung
5. zentrale HR-Prüfung
6. Approve / Reject
7. Publish
8. Archive / Deactivate

### 9.3 Bewerberworkflow
1. Eingang
2. Privacy-/Retention-Kontext
3. kontextgebundene Zuweisung
4. lokale Eignungsprüfung
5. Einladung / nächster Schritt
6. Entscheidung / Ausgang
7. Retention- / Löschlogik

---

## 10. Rollenmodell

### 10.1 Mindestrollen
- GlobalAdmin
- CMSOwner
- CentralHRCareerAdmin
- JobEditor
- LocalEditor
- LocalHiringReviewer
- LocalInterviewCoordinator
- SEOQAReviewer
- PrivacyComplianceReviewer
- Publisher
- Analyst

### 10.2 Kernlogik
- CentralHRCareerAdmin: Governance, Templates, Standards, Freigaben
- JobEditor / LocalEditor: Entwürfe und Bearbeitung im zulässigen Scope
- LocalHiringReviewer / LocalInterviewCoordinator: lokale fachliche Recruiting-Schritte
- Publisher: Veröffentlichung nur bei gültigem Freigabestatus
- Analyst: nur Reporting, keine operativen Bewerberdaten ohne Zusatzfreigabe

---

## 11. Privacy / Security / Compliance Konzept

### 11.1 Privacy-Basis
Die Plattform muss Bewerberdatenschutz systemisch unterstützen.

#### Mindestobjekte
- PrivacyNoticeVersion
- DataRetentionPolicy
- ApplicantAccessAssignment

### 11.2 Harte Regeln
- Kein öffentliches Formular ohne verknüpfte PrivacyNoticeVersion
- Kein Bewerberzugriff ohne Rollen- und Kontextbezug
- Keine unbegrenzte Speicherung von Bewerberdaten
- Keine breite bereichs- oder standortübergreifende Einsicht in Bewerberdaten ohne explizite Legitimation

### 11.3 Sicherheitsbasis
- HTTPS-only
- MFA für privilegierte Rollen
- objektbezogene Autorisierung
- Audit Logging
- Zertifikats- und Secret-Management
- mTLS für privilegierte interne Service-Kommunikation, wo vorgesehen

---

## 12. Accessibility- und SEO-Konzept

### 12.1 Accessibility
Die Plattform muss Barrierefreiheit als Kernanforderung behandeln.

#### Mindestanforderungen
- semantische Struktur
- Tastaturbedienbarkeit
- verständliche Labels
- verständliche Fehlermeldungen
- Fokuszustände
- verständliche Linktexte

### 12.2 SEO
Die Plattform muss suchmaschinenfreundliche Job- und Karriereinhalte unterstützen.

#### Mindestanforderungen
- sprechende URLs
- page-level metadata
- canonical handling
- strukturierte Jobdaten
- indexierbare Jobdetailseiten
- sinnvolle interne Verlinkung

---

## 13. MVP-Umfang

### 13.1 MVP muss enthalten
- Karriere-Startseite
- Arbeitgeberbereich
- mehrere CareerPath-/JobFamily-Seiten
- Stellenliste
- Stellentdetailseite
- Initiativbewerbungsseite
- Ansprechpartner-/Kontaktlogik
- Grundrollenmodell
- Grundworkflow
- Privacy-/Retention-Basis
- Accessibility-Basis
- SEO-Basis

### 13.2 Nicht zwingend im MVP
- tiefes ATS
- umfangreiche Kampagnenautomatisierung
- Onboarding
- komplexe Mehrsprachigkeit
- tiefe externe Integrationen
- unkontrollierte lokale Spezialprozesse

---

## 14. Delivery-Prinzip

### 14.1 Erst Modell, dann Umsetzung
Vor UI-/Produktivumsetzung müssen vorliegen:
- finale Entitäten,
- Beziehungen,
- Rollen,
- Workflows,
- Template-Regeln,
- Privacy-/Retention-Regeln,
- Security-Basis.

### 14.2 Harte Stop-Regel
Wenn zentrale Modellgrenzen unklar sind (z. B. Facility vs. Location, JobFamily vs. CareerPath, Bewerbungsziel, Ownership, Privacy-Basis), darf der Developer Agent nicht raten, sondern muss eskalieren.

---

## 15. Letzte Regel

Dieses Dokument ist die konsolidierte Enterprise-spezifische Zielbeschreibung.  
Externe Produktlogiken oder Benchmark-Verweise sind für die Umsetzung nicht maßgeblich.

---

# 13_Content_Migration_and_Inventory.md

## Dokumentstatus
- Version: 2.0
- Zweck: Enterprise-spezifische Migrations- und Inventarisierungsgrundlage für Inhalte, Strukturen und Zielobjekte
- Gültigkeit: benchmark-frei, ausschließlich auf Enterprise-Quellen und Zielmodell ausgerichtet
- Regel: Wenn Zielmodell oder Governance-Regeln angepasst werden, muss dieses Migrationsdokument aktualisiert werden

---

## 1. Ziel dieses Dokuments

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

## 2. Migrationsprinzipien

### 2.1 Enterprise ist die einzige Content-Ausgangsquelle
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

### 2.2 Migration nach Zieltyp, nicht nach HTML-Seite
Migriert wird in:
- strukturierte Masterdaten,
- strukturierte Seiten-/Seitentypen,
- strukturierte Jobobjekte,
- strukturierte Formulare,
- wiederverwendbare Module.

### 2.3 Struktur vor Copy & Paste
Wo Inhalte in strukturierte Felder gehören, müssen sie strukturiert migriert werden.
Freitext-Übernahmen ohne strukturelle Überführung sind zu vermeiden.

### 2.4 Ownership ist Pflicht
Jedes Zielobjekt braucht klaren Owner:
- zentrale HR-Karriere-Abteilung,
- lokaler Bereich / Standort,
- Privacy / Compliance,
- technischer System Owner,
- oder anderer explizit definierter Owner.

### 2.5 Nicht alles wird 1:1 übernommen
Mögliche Migrationsaktionen:
- MIGRATE_AS_IS
- MIGRATE_AND_RESTRUCTURE
- REWRITE
- MERGE
- SPLIT
- RETIRE
- POSTPONE

---

## 3. Aktuelle sichtbare Inhaltsbereiche des Enterprises

### 3.1 Karriere-Hauptnavigation / Einstieg
Sichtbar sind unter anderem:
- Arbeitgeber Enterprise,
- Beruf und Karriere,
- Stellenangebote,
- Initiativbewerbung,
- Ihr Weg zu uns.

### 3.2 Karrierepfad-Inhalte
Die aktuelle Plattform enthält sichtbare Karrierepfad-/Recruiting-Einstiege:
- Ausbildung,
- Freiwilligendienst (FSJ/BFD),
- Praktikum,
- Praktisches Jahr und ärztliche Weiterbildung,
- Fortbildung / Weiterbildung.

### 3.3 Arbeitgeber- und Berufsfeldinhalte
Sichtbar sind:
- Arbeitgeber-Überblick,
- Arbeits- und Berufsfelder,
- inhaltliche Einblicke in Tätigkeitsfelder und Berufe.

### 3.4 Stellenlogik
Sichtbar sind:
- Stellenliste,
- strukturierte Stellenattribute,
- einzelne Jobdetailseiten,
- Kategorie-/Berufsfeldbezug.

### 3.5 Bewerbungs- und Serviceinhalte
Sichtbar sind:
- Ihr Weg zu uns,
- Ihre Bewerbung,
- Kurzbewerbungsformular,
- Datenschutzhinweis und Löschhinweis,
- Ansprechpersonen-Kontexte.

---

## 4. Ziel-Migrationsdomänen

Alle Quellinhalte werden einer der folgenden Ziel-Domänen zugeordnet.

### 4.1 Domain A – Strukturierte Stammdaten
- Organization
- Facility
- Location
- JobFamily
- CareerPath
- ContactPerson

### 4.2 Domain B – Redaktionelle Karriere-Seiten
- homepage
- employer page
- job family page
- career path page
- location page
- facility page
- service / FAQ page
- initiative page

### 4.3 Domain C – Landing Pages
- zielgruppenspezifische Seiten
- kampagnenbezogene Seiten
- standortfokussierte Seiten
- berufsfeldspezifische Einstiegsseiten

### 4.4 Domain D – Job Objects
- JobPosting
- strukturierte Jobattribute
- Bewerbungs-CTA-Logik

### 4.5 Domain E – Bewerbungs-/Service-/Privacy-Inhalte
- ApplicationForm
- PrivacyNoticeVersion
- Datenschutzhinweise
- Bewerbungsprozessinhalte
- Zugangs-/Servicehinweise

### 4.6 Domain F – Shared Modules
- CTA Banner
- FAQ Listen
- Benefits Blöcke
- Contact Cards
- Intro-/Teaser-Module
- Bild/Text-Module

---

## 5. Migrationsaktionen

### 5.1 MIGRATE_AS_IS
Nur verwenden, wenn Inhalt und Struktur bereits direkt zum Zieltyp passen.

### 5.2 MIGRATE_AND_RESTRUCTURE
Verwenden, wenn Inhalt relevant bleibt, aber in strukturierte Felder / Module / Zieltypen überführt werden muss.

### 5.3 REWRITE
Verwenden, wenn Inhalt relevant bleibt, aber sprachlich, strukturell oder inhaltlich neu gefasst werden muss.

### 5.4 MERGE
Verwenden, wenn mehrere Quellinhalte zu einem Zielobjekt zusammengeführt werden.

### 5.5 SPLIT
Verwenden, wenn eine Quelle mehrere Zielobjekte enthält.

### 5.6 RETIRE
Verwenden, wenn Inhalt veraltet, redundant oder im Zielmodell nicht benötigt wird.

### 5.7 POSTPONE
Verwenden, wenn Inhalt bekannt, aber nicht MVP-relevant ist.

---

## 6. Standardfelder für das Migrationsinventar

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

## 7. Enterprise-spezifische Startinventarisierung

### 7.1 Karriere-Startseite
- `target_domain`: Editorial Career Pages
- `target_type`: homepage
- `migration_action`: MIGRATE_AND_RESTRUCTURE
- `central_owner`: Central HR Career Department

### 7.2 Arbeitgeberbereich
- `target_domain`: Editorial Career Pages
- `target_type`: employer
- `migration_action`: MIGRATE_AND_RESTRUCTURE
- `central_owner`: Central HR Career Department

### 7.3 Arbeits- und Berufsfelder
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: JobFamily + job_family page
- `migration_action`: SPLIT
- `central_owner`: Central HR Career Department
- `template`: job family page template required

### 7.4 Ausbildung
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: CareerPath + career_path page
- `migration_action`: MIGRATE_AND_RESTRUCTURE
- `central_owner`: Central HR Career Department

### 7.5 Freiwilligendienst: FSJ und BFD
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: CareerPath + career_path page
- `migration_action`: MIGRATE_AND_RESTRUCTURE
- `central_owner`: Central HR Career Department

### 7.6 Praktikum
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: CareerPath + career_path page
- `migration_action`: REWRITE

### 7.7 Praktisches Jahr / Ärztliche Weiterbildung
- `target_domain`: Structural Master Data + Editorial Career Pages
- `target_type`: CareerPath + career_path page
- `migration_action`: MIGRATE_AND_RESTRUCTURE

### 7.8 Fortbildung / Weiterbildung
- `target_domain`: Editorial Career Pages
- `target_type`: service page oder career_path page
- `migration_action`: MIGRATE_AND_RESTRUCTURE

### 7.9 Stellenliste
- `target_domain`: Job Objects
- `target_type`: JobPosting
- `migration_action`: MIGRATE_AND_RESTRUCTURE
- `central_owner`: Central HR Career Department
- `local_owner`: lokale Bereiche/Facilities für Draft-/Fachinhalte
- `publication governance`: central only
- `template`: mandatory JobTemplate mapping required

### 7.10 Jobdetailseiten
- `target_domain`: Job Objects
- `target_type`: JobPosting
- `migration_action`: MIGRATE_AND_RESTRUCTURE

### 7.11 Einrichtungen und Orte aus Stellen
- `target_domain`: Structural Master Data
- `target_type`: Facility / Location
- `migration_action`: SPLIT

### 7.12 Ihr Weg zu uns / Ihre Bewerbung
- `target_domain`: Editorial Career Pages + Application Domain + Privacy / Service
- `target_type`: service page + initiative page + ApplicationForm
- `migration_action`: SPLIT
- `central_owner`: Central HR Career Department
- `privacy_review_required`: yes

### 7.13 Kontaktpersonen / Ansprechpersonen
- `target_domain`: Structural Master Data + Shared Modules
- `target_type`: ContactPerson + contact_cards module
- `migration_action`: MIGRATE_AND_RESTRUCTURE

### 7.14 Datenschutz / Barrierefreiheit / Recht
- `target_domain`: Privacy / Legal / Service
- `target_type`: privacy page / accessibility page / legal page / privacy notice
- `migration_action`: REWRITE + MIGRATE_AND_RESTRUCTURE
- `central_owner`: Privacy / Compliance + Central HR Career Department

---

## 8. Ownership-Modell für Migration

### 8.1 Zentrale HR-Karriere-Abteilung besitzt dauerhaft
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

### 8.2 Lokale Einheiten dürfen beitragen zu
- lokalen Stelleninhalten innerhalb von Templates
- fachlichen Ergänzungen bei JobDrafts
- lokalen Facility-/Location-Kontexten, wenn im Zielmodell vorgesehen
- kontextbezogenen Ansprechpartnern
- kontrollierten Prozessvarianten innerhalb definierter Grenzen

### 8.3 Privacy / Compliance besitzt oder prüft
- PrivacyNoticeVersionen
- Datenschutzseiten
- Retention-Texte
- Bewerberrechte-Kommunikation
- Lösch- und Kandidat*innen-Pool-Logik

### 8.4 Technische / System-Owner besitzen
- Migrationstooling
- Importvalidierung
- Statusverfolgung
- Referenzintegrität
- technische Datenqualität

---

## 9. Migrationsvalidierung

### 9.1 Strukturvalidierung
Jedes Zielobjekt muss geprüft werden auf:
- korrekten Zieltyp
- Pflichtfelder
- gültige Referenzen
- gültige Slugs / Zielstruktur
- korrekte Zuordnung von Facility, Location, JobFamily, CareerPath

### 9.2 Templatevalidierung
- Seite nutzt den richtigen Seitentyp / das richtige Template
- Job nutzt korrektes JobTemplate
- Pflichtsektionen sind vorhanden
- keine unzulässige Freiform-Struktur, wo Template-Pflicht besteht

### 9.3 Governancevalidierung
- zentraler Owner vorhanden
- lokaler Owner vorhanden, falls nötig
- Workflowstatus korrekt
- Freigabe-/Publikationspfad korrekt

### 9.4 Privacy-/Compliance-Validierung
- Bewerbungsseiten / Formulare sind an PrivacyNoticeVersion gebunden
- keine öffentlichen Kontaktobjekte ohne Kontext
- keine Zieltexte, die dem neuen Privacy-/Retention-Modell widersprechen

### 9.5 Accessibility-Validierung
- Inhalte sind template-kompatibel barrierefrei integrierbar
- Überschriftenstruktur passend
- Formular- und CTA-Inhalte verständlich
- Bild-/Medieninhalte mit Alt-Text-/Kontextprüfung

### 9.6 SEO-Validierung
- Ziel-URL-/Slug-Strategie definiert
- Metadaten vorbereitet
- Canonical-Strategie geklärt
- keine ungewollten Doppelseiten

---

## 10. Migrationsphasen

### Phase 1 – Discovery Inventory
- alle aktuell sichtbaren Enterprise-Karriereinhalte erfassen
- Kategorien zuordnen
- Dopplungen und Überschneidungen identifizieren
- strukturrelevante Daten in Texten identifizieren

### Phase 2 – Mapping
- Zieldomäne zuordnen
- Zieltyp zuordnen
- Migrationsaktion zuordnen
- Ownership und Template zuordnen

### Phase 3 – Content Preparation
- Inhalte restrukturieren
- Wiederholungen normalisieren
- Stammdaten vorbereiten
- Rewrites erstellen, wo nötig

### Phase 4 – Controlled Import / Entry
- strukturierte Stammdaten laden
- Zielseiten anlegen
- Jobs als strukturierte JobPosting-Objekte einbringen
- Workflows / Ownership setzen

### Phase 5 – QA and Sign-Off
- Content QA
- Governance QA
- Privacy / Compliance QA
- Accessibility QA
- SEO QA

### Phase 6 – Go-Live Readiness
- finale Linkprüfung
- finale Ownership-Prüfung
- finale Freigaben
- Redirect-/Korrektur-/Rollback-Plan

---

## 11. Empfohlene Migrationspriorität

### Priorität 1
- Karriere-Startseite
- Arbeitgeberbereich
- Stellenliste / Jobdetailmodell
- Initiativbewerbung / Ihre Bewerbung
- Privacy-/Barrierefreiheitsbasis
- zentrale CareerPath-Seiten

### Priorität 2
- JobFamily-Seiten
- strukturierte Facilities / Locations
- Ansprechpartner-Normalisierung
- FAQ-/Service-/Bewerbungsweg-Inhalte

### Priorität 3
- zusätzliche LandingPages
- vertiefte Standort-/Einrichtungsseiten
- kampagnenbezogene Inhalte
- spätere Erweiterungsinhalte

---

## 12. Offene Migrationsfragen

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

## 13. Harte Migrationsregel

Ein Inhalt gilt **nicht** als migriert, nur weil er im Zielsystem sichtbar ist.

Ein Inhalt gilt erst dann als migriert, wenn:
- der korrekte Zieltyp gesetzt ist,
- strukturierte Felder befüllt sind,
- Owner und Workflow korrekt gesetzt sind,
- Privacy-/Accessibility-/SEO-Prüfungen erfolgt sind,
- und der Inhalt das neue Enterprise-Betriebsmodell unterstützt.

---

# 14_Security_Architecture_and_Certificate_Guide.md

## Document Status
- Version: 0.1
- Purpose: Define the binding security architecture, certificate model, authentication model, API protection controls, secret management rules and operational hardening baseline
- Scope: Public platform traffic, internal user traffic, internal service-to-service APIs, recruiting administration APIs, workflow APIs, privacy/compliance APIs
- Binding level: Derived from `00_FINAL_SOURCE_OF_TRUTH.md`, `11_API_Contracts_and_Schemas.md`, and `12_Test_and_Quality_Gates.md`
- Rule: If this document conflicts with the Final Source of Truth, the Final Source of Truth wins

---

## 1. Goal of This Document

This document defines the security architecture baseline that must be implemented before the platform can be considered production-ready.

The security architecture must ensure:
- secure transport for all public and internal traffic
- strong authentication for users and machine clients
- strict authorization at endpoint, function and object level
- least-privilege access for all actors
- auditable access to sensitive applicant data
- strong certificate and secret lifecycle management
- secure-by-default platform configuration
- ability to detect, investigate and remediate misuse

The platform must not rely on “security later” assumptions.
Security controls must be present by default and verified before release.

---

## 2. Security Design Principles

### 2.1 Secure by Design and Secure by Default
Security must be built into the platform design and not added as an optional add-on at the end.

### 2.2 Defense in Depth
Authorization and access control must not be enforced only at one layer.

### 2.3 Least Privilege
All human users, applications, background jobs and service identities must receive only the minimum permissions required to perform their intended tasks.

### 2.4 Explicit Trust Boundaries
The platform must distinguish clearly between:
- public anonymous traffic
- authenticated internal user traffic
- privileged administration traffic
- service-to-service traffic
- applicant-data-sensitive traffic

Every boundary must have explicit security controls.

### 2.5 Auditability
Sensitive operations must be attributable to:
- actor
- time
- object
- action
- outcome

---

## 3. Security Zones and Trust Boundaries

### 3.1 Zone A – Public Internet / Anonymous Access
Contains:
- public career pages
- public job lists
- public job detail pages
- public application forms
- public privacy notices

Security characteristics:
- HTTPS only
- no applicant data
- no internal workflow data
- strict input validation
- abuse/rate-limiting protections
- no trust in client input by default

### 3.2 Zone B – Authenticated Internal User Zone
Contains:
- Central HR Career Department UI/API
- local editors
- local hiring reviewers
- local interview coordinators
- privacy/compliance reviewers
- publishers
- analysts

Security characteristics:
- authenticated access only
- MFA for privileged roles
- session controls
- role-based access control
- context-based applicant access
- full audit logging

### 3.3 Zone C – Privileged Internal API Zone
Contains:
- workflow APIs
- sensitive applicant APIs
- access-assignment APIs
- privacy/compliance configuration APIs
- publication/approval APIs

Security characteristics:
- authenticated and authorized only
- strong token validation
- object-level authorization
- enhanced logging
- optional mTLS for especially privileged APIs

### 3.4 Zone D – Service-to-Service Zone
Contains:
- internal API-to-API calls
- background workers
- search/index services
- retention job execution
- analytics ingestion
- notification/invitation services if added later

Security characteristics:
- service identity required
- mutual authentication strongly preferred
- no anonymous east-west traffic
- certificate or equivalent strong client authentication
- narrow scopes
- environment separation

---

## 4. Transport Security and Certificates

### 4.1 TLS Baseline
All public and internal API traffic must use TLS.

#### Mandatory rules
- HTTPS only for all endpoints
- TLS 1.3 enabled by default
- TLS 1.2 permitted only for controlled compatibility
- TLS 1.0 disabled
- TLS 1.1 disabled
- SSLv2 and SSLv3 disabled
- weak ciphers disabled
- downgrade protections enabled where applicable

### 4.2 Certificate Requirements
The platform must use valid X.509 certificates for public and internal endpoints. Certificates must be lifecycle-managed.

#### Mandatory certificate controls
- proper subject alternative names (SANs)
- certificate expiration monitoring
- defined renewal window
- revocation handling process
- production and non-production separation
- no self-signed public production certificates
- internal PKI or managed trust model for internal-only services

### 4.3 HSTS and HTTPS Enforcement
Public browser-facing services should enforce HTTPS and prevent downgrade to insecure transport.

### 4.4 Certificate Lifecycle
Certificate lifecycle must include:
- issuance
- validation
- deployment
- rotation
- expiration alerting
- revocation / replacement
- emergency replacement for compromise

#### Hard rule
No production API may go live without:
- valid certificate
- expiry monitoring
- defined renewal process
- documented ownership

---

## 5. Mutual TLS (mTLS)

### 5.1 Why mTLS is Required for High-Privilege Internal Communication
For highly privileged web services, mutually authenticated client-side certificates are recommended.

### 5.2 Where mTLS Must Be Used
mTLS must be strongly considered mandatory for:
- privileged internal service-to-service APIs
- approval/publication services
- applicant-sensitive internal API gateways
- compliance / retention execution services
- secrets-management or key-management service calls if applicable

### 5.3 mTLS Modes
The architecture may support:
- PKI-based mutual TLS
- self-signed certificate mutual TLS only in tightly controlled internal environments
- certificate-bound access tokens for selected OAuth-protected machine clients

### 5.4 Mandatory mTLS Rules
- client certificate must be validated against trusted authority or trust store
- expired certificates must be rejected
- revoked certificates must be rejected where revocation support exists
- service identity must map to certificate identity
- certificate mismatch must block access
- mTLS failures must be logged
- privileged internal APIs must not silently fall back to anonymous or weak client auth

#### Hard rule
If an endpoint is marked as `requires_mtls = true`, the call must fail without a valid client certificate.

---

## 6. Authentication Architecture

### 6.1 Human User Authentication
Authenticated internal users must not rely on weak or shared access mechanisms.

#### Minimum model
- centralized identity provider or equivalent
- unique named accounts only
- MFA mandatory for privileged roles
- no shared admin credentials
- no long-lived local password bypass accounts unless explicitly controlled for emergency use

### 6.2 Privileged Role Authentication
The following roles require MFA:
- GlobalAdmin
- Central HR Career Admin
- CMSOwner
- Publisher
- Privacy / Compliance Reviewer
- any role with unrestricted internal audit visibility

### 6.3 Machine Authentication
Service identities must use strong authentication.
Preferred order:
1. mTLS with service certificate
2. OAuth2 client authentication using mTLS
3. another documented strong machine identity pattern approved explicitly

#### Hard rule
Shared generic API secrets alone are not sufficient for highly privileged service-to-service traffic.

---

## 7. Authorization Architecture

### 7.1 Authorization Layers
Authorization must exist at:
- edge / gateway level
- service level
- object level
- workflow state transition level

### 7.2 Role-Based Access Control (RBAC)
The platform uses explicit roles:
- GlobalAdmin
- CMSOwner
- CentralHRCareerAdmin
- JobEditor
- LocalEditor
- LocalHiringReviewer
- LocalInterviewCoordinator
- SEOQAReviewer
- PrivacyComplianceReviewer
- Publisher
- Analyst

### 7.3 Context-Based Authorization
Role alone is not sufficient for applicant data or local recruiting operations.
Authorization decisions must also consider:
- facility
- location
- job
- process stage
- access assignment
- workflow status

### 7.4 Object-Level Authorization
A caller must be checked against the specific object they want to access.

#### Mandatory examples
- LocalHiringReviewer may access only assigned applications/jobs
- LocalEditor may edit only assigned content scopes
- Publisher may publish only approved objects
- CentralHRCareerAdmin may approve job ads but does not automatically gain unrestricted applicant detail access
- Analyst may see analytics but not applicant documents

### 7.5 Workflow-Aware Authorization
Authorization must also check whether the requested action is valid for the current workflow state.
Examples:
- no publish before approval
- no central approval by non-central role
- no retention action without valid trigger/policy
- no access assignment by unauthorized user

---

## 8. Token and Session Security

### 8.1 Token Principles
If bearer or access tokens are used:
- they must be short-lived
- bound to audience
- scope-restricted
- never transmitted in URLs
- never logged in plain text

### 8.2 Sender-Constrained Tokens
For highly sensitive machine-to-machine APIs, prefer sender-constrained access tokens or certificate-bound tokens where feasible.

### 8.3 Session Management
Authenticated sessions must be controlled using session secrets and clear expiration handling.

#### Mandatory session rules
- inactivity timeout for internal UI sessions
- explicit logout support
- reauthentication for highly privileged actions
- no insecure “remember me” shortcut for privileged contexts
- session invalidation on logout

### 8.4 Reauthentication for Sensitive Actions
The system should require stronger confirmation or fresh session assurance for:
- changing role assignments
- changing access assignments
- approving publication
- modifying privacy notices
- modifying retention policies
- rotating certificates/secrets

---

## 9. API Gateway and Service Protection

### 9.1 Gateway Responsibilities
The API gateway or equivalent edge component should handle:
- TLS termination where appropriate
- basic request filtering
- coarse authentication enforcement
- rate limiting
- abuse detection
- request correlation IDs

### 9.2 Service Responsibilities
Services must still enforce:
- authorization
- object-level checks
- workflow rules
- field-level restrictions where needed
- privacy-sensitive response shaping

### 9.3 API Inventory and Exposure Control
Every endpoint must have:
- owner
- documentation status
- intended audience (public/internal/privileged/internal service-only)
- authentication requirement
- authorization requirement
- data classification

---

## 10. Secrets and Key Management

### 10.1 General Rule
Secrets must never be hard-coded in source code or static deployment artifacts.

### 10.2 Secret Types
This applies to:
- client secrets
- certificate private keys
- signing keys
- encryption keys
- webhook secrets
- environment secrets
- API integration credentials

### 10.3 Mandatory Secret Controls
- secret storage in secret-management system or equivalent
- separate secrets per environment
- access control on secret retrieval
- rotation capability
- revocation capability
- audit logging of secret access where feasible

### 10.4 Key Rotation
Signing keys, client secrets and certificates must support rotation.
Rotation must not require application redesign.

### 10.5 Emergency Revocation
A compromised credential/certificate/key must support emergency revocation and replacement.

#### Hard rule
If production credentials cannot be rotated or revoked, the design is not acceptable.

---

## 11. Applicant Data Protection and Access Hardening

### 11.1 Need-to-Know Access
Applicant data must only be visible to users directly involved in the relevant recruitment process.

### 11.2 Access Assignment
Applicant access must be granted through explicit assignment with:
- actor
- context
- role
- scope
- validity period
- auditability

### 11.3 Segregation by Context
The following must not be broadly visible by default across unrelated sites or departments:
- applicant profile data
- uploaded documents
- review notes
- invitation history
- decision progression

### 11.4 Central vs Local Access Principle
- Central HR Career Department may access process-governance-relevant information and approved operational scope
- Local sites/departments may access only the applicants for their own relevant jobs/processes
- Full unrestricted candidate detail access must not be the default for central governance users

---

## 12. Logging, Audit and Monitoring

### 12.1 Mandatory Audit Events
The following must be audit logged:
- authentication success/failure for internal roles
- mTLS handshake failures for protected services
- role changes
- access assignment create/update/remove
- applicant record read in restricted APIs
- job creation/update/review/approval/publish/archive
- privacy notice creation/update/activation
- retention policy creation/update
- retention execution actions
- workflow transition failures
- repeated authorization failures

### 12.2 Log Content Requirements
Every critical log should contain:
- timestamp
- actor id / service identity
- source IP / service context where appropriate
- object type
- object id
- action
- outcome
- reason / error code
- correlation id / trace id

### 12.3 Monitoring and Detection
At minimum, monitoring should exist for:
- repeated failed login attempts
- repeated failed mTLS handshakes
- repeated access scope violations
- abnormal applicant access volume
- certificate expiration windows
- failed retention execution
- repeated workflow bypass attempts
- unusual API volume/resource exhaustion patterns

---

## 13. Secure Configuration and Hardening Rules

### 13.1 Default Deny
All non-public endpoints are deny-by-default unless explicitly exposed.

### 13.2 No Weak Defaults
The platform must not ship with:
- default admin passwords
- anonymous internal access
- weak TLS versions
- disabled logging
- optional MFA for privileged roles
- open CORS policies without justification
- unrestricted debug endpoints in production

### 13.3 Rate Limiting and Abuse Controls
Sensitive public flows should include rate limiting and abuse controls, especially:
- form submissions
- search/listing abuse
- login endpoints
- password reset or equivalent account flows if introduced later

### 13.4 Error Handling
Errors must:
- avoid leaking secrets or internal stack details
- provide structured machine-readable error codes
- preserve traceability via correlation IDs
- avoid disclosing sensitive authorization logic

---

## 14. Security Architecture for Central vs Local Operating Model

### 14.1 Central HR Career Department
Security implications:
- privileged governance role
- MFA mandatory
- approval actions auditable
- no automatic unrestricted applicant access
- access to central templates and process standards
- limited operational visibility according to need-to-know

### 14.2 Local Sites / Departments
Security implications:
- access only to assigned job and applicant scope
- invitation and suitability decisions restricted to approved context
- no cross-site applicant visibility by default
- no ability to publish jobs directly without central approval

### 14.3 Controlled Variants
Local process variations must remain:
- template-based
- centrally approved
- auditable
- security-equivalent to central mandatory baseline

---

## 15. Security Requirements per API Class

### 15.1 Public Content APIs
Requirements:
- HTTPS only
- no authentication required unless explicitly protected
- no internal data leakage
- rate limiting for abuse-prone endpoints
- structured input validation

### 15.2 Public Form Submission APIs
Requirements:
- HTTPS only
- privacy notice linkage required
- anti-abuse protection
- strict validation
- upload protection
- submission auditability
- retention policy linkage

### 15.3 Internal Governance APIs
Requirements:
- authenticated only
- MFA for privileged users
- role and state-based authorization
- full audit logging
- no publish without approval
- optional privileged mTLS depending on architecture

### 15.4 Sensitive Applicant APIs
Requirements:
- authenticated only
- role + context + object authorization
- access-assignment check
- audit event on read
- response minimisation
- no bulk unrestricted export by default

### 15.5 Service-to-Service APIs
Requirements:
- TLS mandatory
- strong machine identity
- mTLS strongly preferred / mandatory for privileged flows
- narrow scopes
- service inventory ownership
- certificate/key rotation support

---

## 16. Certificate and Authentication Deployment Model

### 16.1 Recommended Public Endpoint Model
- public certificate for internet-facing domain
- HTTPS-only redirect handling if needed
- TLS 1.3 preferred
- secure cipher configuration
- certificate renewal automation or managed process

### 16.2 Recommended Internal Service Model
- internal PKI or trusted internal CA
- service certificate per service identity
- certificate validation at trust boundary
- separate certificate sets per environment
- mTLS between critical internal services

### 16.3 Recommended User Authentication Model
- central identity provider
- SSO for internal users where feasible
- MFA for privileged roles
- short-lived session model
- session reauthentication for critical actions

### 16.4 Recommended Machine Authentication Model
- OAuth2 with mTLS client authentication for service clients where possible
- certificate-bound tokens for especially sensitive machine clients where practical
- fallback strong service identity only if approved explicitly

---

## 17. Incident and Compromise Response Hooks

### 17.1 Certificate Compromise
Must support:
- certificate revocation / trust removal
- reissue
- redeploy
- incident logging
- dependent service impact analysis

### 17.2 Secret Compromise
Must support:
- immediate secret invalidation
- replacement
- dependency tracing
- post-incident audit review

### 17.3 Account Compromise
Must support:
- forced logout/session invalidation
- MFA reset workflow
- role review
- access-assignment review
- applicant-access audit review

### 17.4 API Abuse / Data Exposure Incident
Must support:
- log retrieval
- actor traceability
- object scope traceability
- exposure-window estimation
- remediation status tracking

---

## 18. Hard Security Go / No-Go Rules

The platform must not go live if any of the following are true:

1. Any protected internal API is accessible anonymously.
2. Any public or internal API supports insecure transport.
3. Deprecated TLS versions remain enabled on production endpoints.
4. Privileged roles do not require MFA.
5. Sensitive internal machine APIs intended for mTLS do not validate client certificates.
6. Applicant data is accessible without role + context + object-level authorization.
7. Job publication can occur without required central approval.
8. Secrets or private keys are hard-coded or non-rotatable.
9. Critical audit events are missing.
10. Certificate expiration or revocation handling is undefined.
11. Retention and deletion controls for applicant data are undefined.
12. Unknown or undocumented privileged endpoints exist in production.

---

## 19. Mandatory Developer Agent Outputs Before Security Sign-Off

Before implementation is considered security-ready, the Senior Developer Agent must provide:

### 19.1 Security Topology
- public zones
- internal zones
- service-to-service boundaries
- trust boundaries
- TLS/mTLS boundaries

### 19.2 Certificate Plan
- certificate owners
- endpoint classification
- public vs internal certificate model
- renewal/rotation plan
- revocation handling plan

### 19.3 Authentication Plan
- user authentication method
- MFA scope
- service authentication method
- token model
- reauthentication model

### 19.4 Authorization Plan
- role matrix
- object-level authorization rules
- access-assignment enforcement model
- workflow authorization rules

### 19.5 Logging and Detection Plan
- audit event catalog
- security monitoring events
- alerting thresholds
- traceability model

### 19.6 Hardening Checklist
- TLS configuration
- secret handling
- endpoint exposure review
- error handling
- rate limiting
- inventory validation

---

## 20. Final Binding Rule

No implementation may treat certificates, transport security, MFA, mTLS, authorization, logging, privacy or key rotation as “future enhancement”.
They are part of the minimum security architecture and must be designed in from the start.

---

# 15_Implementation_Control_Checklist.md

## Document Status
- Version: 0.1
- Purpose: Final execution control checklist for implementation, deployment, security sign-off, privacy readiness and public go-live
- Scope: Entire career platform, including public pages, job delivery, application processing, internal workflows, governance APIs, applicant-data-sensitive APIs, templates, privacy controls and security controls
- Audience:
  - Senior Developer Agent
  - Technical Lead
  - Enterprise Architect
  - Security Architect
  - Product Owner
  - Delivery / Release Manager
  - Privacy / Compliance Reviewer
- Binding level: Derived from the Final Source of Truth and all implementation documents
- Rule: If this checklist conflicts with the Final Source of Truth, the Final Source of Truth wins

---

## 1. Goal of This Checklist

This checklist is the final control layer that ensures:
- no critical implementation area is forgotten
- no feature is considered “done” without security, privacy and governance readiness
- no public or internal release happens with unresolved critical control gaps
- the Developer Agent works in a controlled, verifiable and auditable way

This checklist must be used:
- before implementation starts
- during implementation
- before integration testing
- before enabling applicant processing
- before enabling local sites/departments
- before public go-live

---

## 2. Usage Instructions

### 2.1 Control Status Values
Each control item must have one of the following states:
- `NOT_STARTED`
- `IN_PROGRESS`
- `DONE`
- `BLOCKED`
- `NOT_APPLICABLE`

### 2.2 Evidence Requirement
A control item is only considered `DONE` if evidence exists.
Accepted evidence types:
- approved design artifact
- implemented configuration
- test result
- audit log proof
- screenshot / environment proof
- code/config review result
- documented sign-off

### 2.3 Hard Rule
“Planned later” is not an acceptable substitute for `DONE` if the control is defined as mandatory for the current milestone.

---

## 3. Global Milestone Gates

### 3.1 Milestone Types
The checklist is structured around these milestone gates:
1. Pre-Implementation Gate
2. Pre-Development Gate
3. Pre-Integration Gate
4. Pre-Applicant-Data Gate
5. Pre-Local-Unit-Activation Gate
6. Pre-Public-Go-Live Gate
7. Post-Go-Live Hardening Gate

### 3.2 Critical Release Rule
If any mandatory control in the active milestone gate is:
- `NOT_STARTED`
- `BLOCKED`
- or failed in testing

then the milestone must be treated as **No-Go**.

---

## 4. Pre-Implementation Gate

### 4.1 Concept and Model Controls
- PI-001: Final Source of Truth exists and is approved
- PI-002: Domain model exists with all core entities
- PI-003: Facility, Location, JobFamily and CareerPath are explicitly separated in the model
- PI-004: Roles and permissions model exists
- PI-005: Workflow model exists for pages, jobs, forms and applicant processing
- PI-006: Central vs local operating model is explicitly documented
- PI-007: Template governance model exists for job ads and process templates
- PI-008: Privacy / retention / notice model is explicitly documented

---

## 5. Pre-Development Gate

### 5.1 API and Data Contract Controls
- PD-001: Public API contract set exists
- PD-002: Internal governance API contract set exists
- PD-003: Sensitive applicant API contract set exists
- PD-004: Error model is defined and standardized
- PD-005: Validation rules are defined for required fields, enums, references and workflow transitions

### 5.2 Security Architecture Controls
- PD-006: Security architecture guide exists and is approved
- PD-007: TLS baseline is defined
- PD-008: mTLS usage is explicitly defined for privileged service-to-service flows
- PD-009: Human authentication model is defined
- PD-010: MFA scope for privileged roles is explicitly defined
- PD-011: Secret and key management approach is defined
- PD-012: Logging and audit event catalog is defined

---

## 6. Pre-Integration Gate

### 6.1 Functional Implementation Controls
- PGI-001: Core entity schemas are implemented
- PGI-002: Workflow state enforcement is implemented
- PGI-003: Template conformity enforcement is implemented
- PGI-004: Public job list/detail APIs function according to contract
- PGI-005: Internal job governance APIs function according to contract
- PGI-006: Application form retrieval/submission APIs function correctly
- PGI-007: Applicant access assignment logic is implemented

### 6.2 Security Integration Controls
- PGI-008: All protected internal endpoints reject unauthenticated access
- PGI-009: Object-level authorization is implemented for all object-ID-based operations
- PGI-010: Local users cannot access unrelated jobs/applications
- PGI-011: Central approval requirement for job publication is enforced technically
- PGI-012: mTLS-protected services reject calls without valid client certificate where required

---

## 7. Pre-Applicant-Data Gate

### 7.1 Privacy and Data Protection Controls
- PAD-001: Every public ApplicationForm links to an active PrivacyNoticeVersion
- PAD-002: Submitted applications persist the shown privacy notice version
- PAD-003: DataRetentionPolicy exists for applicant-related objects
- PAD-004: Rejected, withdrawn, hired and optional talent-pool cases are distinguished
- PAD-005: Applicant access is strictly need-to-know and assignment-based
- PAD-006: Public applicant submission does not expose internal routing targets
- PAD-007: Sensitive applicant reads are audit logged
- PAD-008: Applicant uploads are protected and validated

### 7.2 Security Controls Before Applicant Data Processing
- PAD-009: HTTPS/TLS is enabled and validated on all applicant-facing endpoints
- PAD-010: Rate limiting / anti-abuse controls exist for public form submission
- PAD-011: Applicant-sensitive internal APIs require authentication + authorization + context checks
- PAD-012: No applicant data is visible through public APIs

---

## 8. Pre-Local-Unit-Activation Gate

### 8.1 Central vs Local Governance Controls
- PLA-001: Local units can create job drafts only through approved templates
- PLA-002: Local units cannot publish job ads directly without central approval
- PLA-003: Local suitability review is restricted to assigned local scope
- PLA-004: Local invitation handling is restricted to authorized roles/stages
- PLA-005: Controlled local process variants are centrally approved before use
- PLA-006: Local process variants cannot remove centrally mandatory stages
- PLA-007: Local access does not expand automatically to other sites/departments

---

## 9. Pre-Public-Go-Live Gate

### 9.1 Public Experience Controls
- PGL-001: Career homepage exists and is complete
- PGL-002: Job list and job detail pages are fully functional
- PGL-003: Initiative application page is reachable and functional
- PGL-004: Contact / contact-person logic is correct and context-bound

### 9.2 Accessibility and SEO Controls
- PGL-005: Core pages and forms are keyboard operable
- PGL-006: Labels, errors and semantics on public forms are adequate
- PGL-007: SEO title / meta description / canonical handling is configured
- PGL-008: Job detail pages can provide structured job data

### 9.3 Production Security Controls
- PGL-009: Public endpoints are HTTPS only
- PGL-010: Deprecated TLS versions are disabled in production
- PGL-011: Production certificates are valid and monitored
- PGL-012: No debug/admin/test endpoints are publicly exposed
- PGL-013: Public APIs and pages are rate-limited or otherwise protected against abuse where needed

---

## 10. Post-Go-Live Hardening Gate

### 10.1 Operational Security Controls
- PGG-001: Audit logs are centrally retrievable
- PGG-002: Alerts exist for repeated failed authentication
- PGG-003: Alerts exist for repeated access scope violations
- PGG-004: Alerts exist for certificate expiration windows
- PGG-005: Alerts exist for failed retention execution
- PGG-006: API inventory is maintained and owned

### 10.2 Operational Readiness Controls
- PGG-007: Secret rotation procedure exists and is tested
- PGG-008: Certificate renewal / replacement procedure exists and is tested
- PGG-009: Incident response hooks exist for credential/certificate compromise
- PGG-010: Applicant access audit review process exists

---

## 11. Critical Security Checklist

### 11.1 Must Be True Before Any Production Use
- HTTPS only is enforced
- valid certificates are in place
- deprecated TLS versions are disabled
- privileged roles require MFA
- internal protected APIs require authentication
- object-level authorization is implemented
- applicant access is context-bound
- no public endpoint leaks applicant data
- privacy notice is linked to public forms
- retention policy exists for applicant data
- job publication requires central approval
- audit logging covers restricted access and approvals
- no hard-coded secrets exist in production deployment path
- certificate and key rotation are possible

If any of these are false, production use is blocked.

---

## 12. Developer Agent Delivery Checklist

### 12.1 Before coding
- affected domains
- affected APIs
- affected security controls
- expected workflow impact
- expected privacy impact
- expected access-control impact

### 12.2 Before merge / integration
- unit/integration test result
- security test result
- validation result
- workflow test result
- negative test result
- unresolved risks

### 12.3 Before release candidate
- control checklist delta
- known limitations
- no-go blockers
- environment-specific readiness
- final sign-off dependencies

---

## 13. No-Go Conditions

Release or activation must be blocked if any of the following is true:
- protected internal endpoint accessible without authentication
- applicant data visible outside assigned context
- object-level authorization missing on object-based API
- job can be published without central approval
- public form lacks valid privacy notice
- applicant retention policy missing or undefined
- production certificate invalid, missing or unmanaged
- TLS misconfiguration present
- MFA missing for privileged roles
- secrets/private keys hard-coded
- audit logging missing for approvals or applicant access
- local unit receives broader access than approved scope
- controlled local process variant bypasses mandatory central stages

---

## 14. Final Sign-Off Matrix

Before production sign-off, all of the following stakeholders must explicitly confirm their relevant areas:
- Enterprise / Architecture Sign-Off
- Product / Process Sign-Off
- Security Sign-Off
- Privacy / Compliance Sign-Off
- Delivery / Operations Sign-Off

---

## 15. Final Rule

A feature is not complete because the code works.
A feature is complete only when:
- the functional requirement works,
- the security controls work,
- the workflow controls work,
- the privacy controls work,
- the relevant checklist items are marked DONE with evidence,
- and no active no-go condition remains.

---

# 16_Project_Delivery_Roadmap_and_Workstreams.md

## Dokumentstatus
- Version: 1.0
- Zweck: Projektliefermodell, Workstreams, Meilensteine, Abhängigkeiten, Governance und Rollout-Logik für die neue Karriereplattform des Enterprises
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, umsetzungsorientiert
- Regel: Wenn dieses Dokument mit Final Source of Truth oder Sicherheits-/Privacy-Regeln kollidiert, gelten die dort definierten harten Regeln

---

## 1. Ziel dieses Dokuments

Dieses Dokument definiert:
- die Projektstruktur,
- die zentralen Workstreams,
- die Lieferreihenfolge,
- die Meilensteine,
- die Abhängigkeiten,
- die Governance- und Entscheidungswege,
- und die empfohlene Rollout-Reihenfolge für die neue Karriereplattform des Enterprises.

---

## 2. Projektziel

Die neue Karriereplattform soll den aktuellen Enterprise-Kontext in eine strukturierte Zielarchitektur überführen:
- mehrere Karrierepfade,
- strukturierte Stellenanzeigen,
- zentrale HR-Karriere-Governance,
- lokale fachliche Recruiting-Beteiligung,
- datenschutz- und sicherheitsfähige Bewerbungslogik,
- barrierefreie und suchmaschinenfreundliche öffentliche Karriereerfahrung.

---

## 3. Delivery-Prinzipien

- Kein Big Bang
- Erst Modell, dann Implementierung
- Zentrale Governance, kontrollierte lokale Aktivierung
- Produktionsnahe Qualität vor öffentlichem Go-Live

---

## 4. Projekt-Workstreams

### 4.1 Workstream A – Business & Operating Model
Inhalte:
- Rollenmodell
- zentrale vs. lokale Verantwortlichkeiten
- Bewerberprozess-Operating-Model
- zentrale Freigabe von Stellenanzeigen
- lokale Eignungs- und Einladungslogik
- kontrollierte lokale Prozessvarianten

### 4.2 Workstream B – Domain & Data Model
Inhalte:
- Organization
- Facility
- Location
- JobFamily
- CareerPath
- ContactPerson
- JobPosting
- ApplicationForm
- PrivacyNoticeVersion
- DataRetentionPolicy
- ApplicantAccessAssignment
- Templates und Prozessmodelle

### 4.3 Workstream C – Content Model & CMS
Inhalte:
- Seitentypen
- Inhaltsmodule
- CareerPath-Seiten
- JobFamily-Seiten
- Employer-Bereich
- Initiative Application Page
- Service-/FAQ-/Privacy-/Accessibility-Seiten
- Content Ownership und Freigabelogik

### 4.4 Workstream D – Job & Recruiting Workflow Platform
Inhalte:
- JobTemplates
- ProcessTemplates
- JobPosting-Struktur
- Review-/Approval-Flow
- lokaler Recruiting-Flow
- Routing-Logik
- Initiativbewerbungslogik
- Entscheidungsstufen

### 4.5 Workstream E – Privacy, Security & Compliance
Inhalte:
- PrivacyNoticeVersion
- Retention-/Deletion-Logik
- ApplicantAccessAssignment
- TLS / Zertifikate / mTLS
- MFA / AuthN / AuthZ
- Audit Logging
- Secrets / Key Management
- Access Control
- Need-to-know-Prinzip

### 4.6 Workstream F – Public Experience / UX / Discovery
Inhalte:
- Karriere-Startseite
- Jobsuche
- Jobdetailseiten
- CareerPath-Discovery
- JobFamily-Discovery
- Bewerbungs-CTAs
- Mobil-/Accessibility-Qualität
- interne Verlinkung / Conversion-Flows

### 4.7 Workstream G – Migration & Content Preparation
Inhalte:
- Content Inventory
- Mapping Alt -> Neu
- Content Rewrite
- Facility/Location/JobFamily-Strukturierung
- Kontakt-Normalisierung
- Redirect-/URL-Plan
- Go-Live-Inhaltsprüfung

### 4.8 Workstream H – QA, Readiness & Rollout
Inhalte:
- Teststrategie
- Security-/Privacy-Gates
- Accessibility-/SEO-QA
- Workflow-QA
- UAT
- Pilot-Rollout
- Public Go-Live
- Hypercare

---

## 5. Delivery-Phasen

### Phase 0 – Alignment & Freeze
Deliverables:
- Final Source of Truth
- Enterprise-clean Master Concept
- Rollen-/Operating-Model
- Security baseline
- Migration baseline
- Delivery model

### Phase 1 – Core Modelling & Governance Foundation
Deliverables:
- Domain model final
- Entity model final
- role model final
- workflow model final
- job/process template model
- privacy/security target controls
- API contract baseline

### Phase 2 – Foundation Build
Deliverables:
- core schemas
- content model implementation
- job object implementation
- form model implementation
- auth/authz baseline
- certificate/TLS baseline
- audit logging baseline

### Phase 3 – MVP Candidate Experience
Deliverables:
- homepage
- employer area
- selected career path pages
- selected job family pages
- job list
- job detail
- initiative application page
- contact modules
- basic privacy/service pages

### Phase 4 – Controlled Recruiting Operations
Deliverables:
- job template enforcement
- process template enforcement
- local job drafting
- central approval workflow
- local suitability review flow
- invitation decision flow
- applicant access assignment
- privacy notice linkage
- retention policy linkage

### Phase 5 – Hardening & Compliance Readiness
Deliverables:
- MFA / privileged auth final
- mTLS where required
- retention automation
- audit event completeness
- accessibility QA pass
- SEO readiness
- rate limiting / abuse controls
- operational runbooks

### Phase 6 – Migration & Rollout
Deliverables:
- content migration wave 1
- URL/redirect setup
- owner assignments final
- final QA and UAT
- pilot / soft launch
- public go-live
- hypercare

---

## 6. Meilensteine

- M1 – Concept Freeze
- M2 – Architecture & Security Freeze
- M3 – Foundation Complete
- M4 – MVP Experience Ready
- M5 – Governance Ready
- M6 – Compliance & Security Ready
- M7 – Public Go-Live

---

## 7. Abhängigkeiten

### 7.1 Kritische fachliche Abhängigkeiten
- kein Content Model ohne finalen Domain Split
- kein Jobmodell ohne Facility/Location/JobFamily-Klärung
- kein lokaler Recruiting-Flow ohne Rollen-/Zugriffsmodell
- keine öffentlichen Formulare ohne PrivacyNoticeVersion und RetentionPolicy
- kein Publish-Flow ohne zentrale Approval-Definition

### 7.2 Kritische technische Abhängigkeiten
- keine produktive API ohne AuthN/AuthZ/TLS Baseline
- keine applicant-sensitive API ohne Access Assignment
- kein Rollout ohne Audit Logging
- keine Public Go-Live-Freigabe ohne SEO/Accessibility Basis

### 7.3 Kritische Migrationsabhängigkeiten
- keine Migration ohne finalen Zieltyp-Mapping
- keine Redirect-Planung ohne Ziel-URL-Struktur
- keine kontaktbezogene Migration ohne Owner-/Freigabeklarheit

---

## 8. Governance-Struktur

- Steering / Decision Layer
- Design Authority
- Operational Content & Process Board

---

## 9. Rollout-Strategie

### 9.1 Empfohlene Reihenfolge
Wave 1:
- Homepage
- Employer area
- core career paths
- job list / job detail
- initiative application
- privacy / accessibility / core service pages

Wave 2:
- selected job family pages
- structured facility/location usage
- contact normalisation
- enhanced service/FAQ pages

Wave 3:
- additional landing pages
- extended local/facility pages
- advanced analytics
- further process variants where justified

### 9.2 Pilot-Logik
Empfohlen wird ein kontrollierter Pilot:
- begrenzter Inhaltsscope
- begrenzte interne Usergruppe
- begrenzte lokale Recruiting-Beteiligung
- enge Hypercare

---

## 10. Delivery Risks

- Model Risk
- Governance Risk
- Migration Risk
- Security / Privacy Risk
- Scope Risk

---

## 11. Success Criteria

### 11.1 Business / Experience
- klare CareerPath-Einstiege
- nutzbare Jobsuche
- strukturierte Jobdetailseiten
- funktionierende Initiative Application
- verständliche Contact/Process guidance

### 11.2 Governance / Operations
- lokale Draft-Erstellung möglich
- zentrale Stellenfreigabe funktioniert
- lokale Eignungsprüfung funktioniert
- unzulässige Sichtbarkeit ist ausgeschlossen

### 11.3 Security / Privacy / Compliance
- PrivacyNoticeVersion aktiv
- RetentionPolicy aktiv
- ApplicantAccessAssignment aktiv
- MFA/TLS/AuthZ wirksam
- Audit Logging vollständig

---

## 12. Final Rule

Das Projekt gilt nicht als erfolgreich, wenn nur eine schöne Oberfläche live ist.

Es gilt erst dann als erfolgreich, wenn:
- Candidate Experience funktioniert,
- Governance funktioniert,
- lokale Recruiting-Beteiligung kontrolliert funktioniert,
- Datenschutz/Sicherheit funktioniert,
- Inhalte korrekt migriert sind,
- und die Plattform im Enterprise-Betriebsmodell stabil nutzbar ist.

---

# 17_Backlog_Epics_and_User_Stories.md

## Dokumentstatus
- Version: 1.0
- Zweck: Umsetzungsnaher Backlog-Rahmen mit Epics, Features, User Stories und Akzeptanzkriterien für die neue Enterprise-Karriereplattform
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, Zielmodell-konform
- Regel: Stories dürfen den Final Source of Truth nicht widersprechen

---

## 1. Ziel dieses Dokuments

Dieses Dokument übersetzt das Zielmodell in:
- Epics
- Features
- User Stories
- Akzeptanzkriterien

Die Stories sind so formuliert, dass sie:
- für Product / Architecture / Delivery nutzbar sind,
- vom Senior Developer Agent in Umsetzungspakete zerlegt werden können,
- und gleichzeitig Enterprise-spezifisch bleiben.

---

## 2. Epic-Struktur

- EPIC 1 – Career Experience Foundation
- EPIC 2 – Structured Job Platform
- EPIC 3 – Career Paths and Job Families
- EPIC 4 – Initiative Application and Applicant Entry
- EPIC 5 – Central Governance and Template Control
- EPIC 6 – Local Recruiting Operations
- EPIC 7 – Privacy, Retention and Applicant Access Control
- EPIC 8 – Security, Authentication and Certificates
- EPIC 9 – Accessibility and SEO
- EPIC 10 – Content Migration and Rollout
- EPIC 11 – Analytics, Auditability and Reporting

---

## 3. Beispielhafte Kern-Stories (Auszug der finalen Version)

### EPIC 1 – Career Experience Foundation
- Story 1.1.1: klare Karriere-Startseite mit Einstiegen
- Story 1.1.2: mobile Nutzbarkeit der Karriere-Startseite
- Story 1.2.1: Arbeitgeberbereich verständlich darstellen

### EPIC 2 – Structured Job Platform
- Story 2.1.1: JobPosting als strukturiertes Objekt
- Story 2.2.1: strukturierte öffentliche Stellenliste
- Story 2.3.1: strukturierte Stellentdetailseite

### EPIC 3 – Career Paths and Job Families
- Story 3.1.1: CareerPath als First-Class Concept
- Story 3.2.1: dedizierte CareerPath-Seiten für Ausbildung / FSJ/BFD etc.
- Story 3.3.1: JobFamily getrennt von CareerPath modellieren

### EPIC 4 – Initiative Application and Applicant Entry
- Story 4.1.1: Initiativbewerbungsseite
- Story 4.2.1: strukturierte öffentliche Bewerbungsformulare

### EPIC 5 – Central Governance and Template Control
- Story 5.1.1: JobTemplates erzwingen Konsistenz
- Story 5.2.1: zentrale HR-Freigabe vor Veröffentlichung
- Story 5.3.1: ProcessTemplates definieren Mindestprozess

### EPIC 6 – Local Recruiting Operations
- Story 6.1.1: lokale Stellenentwürfe innerhalb Templates
- Story 6.2.1: lokale Eignungsprüfung im eigenen Scope
- Story 6.3.1: lokale Einladungs-/Interview-Stufen
- Story 6.4.1: kontrollierte LocalProcessVariants

### EPIC 7 – Privacy, Retention and Applicant Access Control
- Story 7.1.1: PrivacyNoticeVersion sichtbar und speicherbar
- Story 7.2.1: Retention-Regeln für Bewerberdaten
- Story 7.3.1: ApplicantAccessAssignment erzwingt Need-to-Know

### EPIC 8 – Security, Authentication and Certificates
- Story 8.1.1: HTTPS / TLS / Zertifikate
- Story 8.2.1: MFA für privilegierte Rollen
- Story 8.3.1: mTLS für privilegierte Service-Kommunikation
- Story 8.4.1: object-level authorization

### EPIC 9 – Accessibility and SEO
- Story 9.1.1: Accessibility Baseline
- Story 9.2.1: SEO / structured jobs baseline

### EPIC 10 – Content Migration and Rollout
- Story 10.1.1: Content Inventory
- Story 10.2.1: strukturierte Migration
- Story 10.3.1: Redirect- und Go-Live-Vorbereitung

### EPIC 11 – Analytics, Auditability and Reporting
- Story 11.1.1: Analytics Events
- Story 11.2.1: Audit Logging

---

## 4. Story Priorisation Recommendation

### MVP Must-Have
- EPIC 1 core pages
- EPIC 2 structured jobs
- EPIC 3 selected CareerPaths / JobFamilies
- EPIC 4 initiative application
- EPIC 5 central governance
- EPIC 6 local recruiting basics
- EPIC 7 privacy/retention/access basics
- EPIC 8 auth/authz/TLS basics
- EPIC 9 accessibility/SEO basics
- EPIC 10 migration wave 1
- EPIC 11 core analytics/audit

### Later Wave
- extended landing pages
- broader facility/location page model
- deeper local variants
- advanced analytics
- non-MVP integrations

---

## 5. Hard Story Rules

1. No story is done if it works functionally but fails privacy/security controls.
2. No story involving applicant data is done without context-based access checks.
3. No publication-related story is done without central approval enforcement.
4. No public form story is done without privacy notice and retention linkage.
5. No content migration story is done if the target type and owner are unclear.
6. No internal privileged story is done without authentication and auditability.

---

## 6. Final Rule

These Epics and Stories are Enterprise-specific implementation backlog framing.  
They are not a generic recruiting software backlog and must always remain aligned with:
- the Enterprise operating model,
- the Final Source of Truth,
- and the mandatory privacy/security/governance controls.

---

# 18_Master_Document_Index_and_Usage_Guide.md

## Dokumentstatus
- Version: 1.0
- Zweck: Master-Index und Nutzungsleitfaden für das gesamte Enterprise-Karriereplattform-Paket
- Gültigkeit: Enterprise-spezifisch, benchmark-frei
- Regel: Dieses Dokument erklärt, welches Dokument für welchen Zweck maßgeblich ist. Fachlich-technisch verbindlich bleibt der Final Source of Truth.

---

## 1. Ziel dieses Dokuments

Dieses Dokument definiert:
- welche Dokumente im Gesamtpaket existieren,
- welchen Zweck jedes Dokument erfüllt,
- welche Zielgruppe welches Dokument nutzen soll,
- in welcher Reihenfolge die Dokumente gelesen oder verwendet werden,
- und welches Minimalset für die Übergabe an den Senior Developer Agent erforderlich ist.

---

## 2. Grundregel des Dokumentensets

### 2.1 Single Source of Truth
Das wichtigste Dokument des Gesamtpakets ist:

#### `00_FINAL_SOURCE_OF_TRUTH.md`

Dieses Dokument ist die **einzige verbindliche fachlich-technische Zielquelle** für die neue Enterprise-Karriereplattform.

### 2.2 Unterstützende Dokumente
Alle anderen Dokumente sind:
- vorbereitend,
- spezifizierend,
- operationalisierend,
- oder ausführungsleitend.

Sie konkretisieren den Final Source of Truth, ersetzen ihn aber nicht.

---

## 3. Gesamtübersicht der Dokumente

(Dieser Abschnitt listet die Dokumente 01–19 mit Zweck und Zielgruppen; maßgeblich ist die im Chat zuletzt definierte Fassung.)

---

## 4. Empfohlene Lesereihenfolge nach Zielgruppe

### Für Senior Developer Agent (Pflichtreihenfolge)
1. `00_FINAL_SOURCE_OF_TRUTH.md`
2. `08_Entity_Data_Model.md`
3. `09_Roles_Permissions_Workflows.md`
4. `11_API_Contracts_and_Schemas.md`
5. `12_Test_and_Quality_Gates.md`
6. `14_Security_Architecture_and_Certificate_Guide.md`
7. `15_Implementation_Control_Checklist.md`
8. `16_Project_Delivery_Roadmap_and_Workstreams.md`
9. `17_Backlog_Epics_and_User_Stories.md`
10. `19_Senior_Developer_Agent_Handover_Prompt.md`

---

## 5. Minimaler Handover-Satz für den Senior Developer Agent

Mindestens:
1. `00_FINAL_SOURCE_OF_TRUTH.md`
2. `08_Entity_Data_Model.md`
3. `09_Roles_Permissions_Workflows.md`
4. `11_API_Contracts_and_Schemas.md`
5. `12_Test_and_Quality_Gates.md`
6. `14_Security_Architecture_and_Certificate_Guide.md`
7. `15_Implementation_Control_Checklist.md`
8. `19_Senior_Developer_Agent_Handover_Prompt.md`

---

## 6. Dokument-Priorität bei Konflikten

1. `00_FINAL_SOURCE_OF_TRUTH.md`
2. `14_Security_Architecture_and_Certificate_Guide.md`
3. `12_Test_and_Quality_Gates.md`
4. `15_Implementation_Control_Checklist.md`
5. `08_Entity_Data_Model.md`
6. `09_Roles_Permissions_Workflows.md`
7. `11_API_Contracts_and_Schemas.md`
8. `16_Project_Delivery_Roadmap_and_Workstreams.md`
9. `17_Backlog_Epics_and_User_Stories.md`
10. übrige Hintergrunddokumente

---

## 7. Verwendungsregeln

### 7.1 Was NICHT getan werden darf
- ältere Zwischenstände als neue Wahrheit verwenden
- externe Benchmark-Logik wieder einführen
- technische Annahmen außerhalb des Final Source of Truth erfinden
- Security/Privacy/Template-Gates überspringen
- Content Migration ohne Zieltyp-/Ownership-Mapping starten

### 7.2 Was der Senior Developer Agent immer tun muss
- zuerst den Final Source of Truth lesen
- bei Unklarheit eskalieren
- keine stillen Annahmen treffen
- vor jedem größeren Schritt Ziel, Inputs, Risiken und Tests ausgeben
- Security, Privacy und Governance nicht als “später” behandeln

---

## 8. Finale Regel

Das Dokumentenset ist nur dann korrekt genutzt, wenn:
- `00_FINAL_SOURCE_OF_TRUTH.md` als primäre Wahrheit dient,
- Security / Privacy / Governance nicht optional behandelt werden,
- und der Senior Developer Agent nicht frei interpretiert, sondern kontrolliert arbeitet.

---

# 19_Senior_Developer_Agent_Handover_Prompt.md

## Dokumentstatus
- Version: 1.0
- Zweck: finale, kontrollierte Übergabeinstruktion für den Senior Developer Agent
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, umsetzungssteuernd
- Regel: Der Agent darf nur innerhalb der hier definierten Grenzen arbeiten

---

## 1. Rolle und Mission

Du agierst als **Senior Developer Agent** für die neue Karriereplattform des Enterprises.

Du entwickelst **nicht**:
- ein generisches Bewerbermanagementsystem,
- keinen Nachbau eines externen Produkts,
- keine beliebige Karriereseite.

Du entwickelst:
- eine **spezialisierte Karriereplattform für den Enterprise**,
- auf Basis des dokumentierten Zielmodells,
- mit zentraler HR-Karriere-Governance,
- lokaler fachlicher Recruiting-Beteiligung,
- strukturierten Stellenanzeigen,
- Initiativbewerbungslogik,
- Datenschutz-/Sicherheitsbasis,
- Barrierefreiheit,
- und kontrollierter Erweiterbarkeit.

---

## 2. Verbindliche Dokumente, die du zuerst lesen musst

1. `00_FINAL_SOURCE_OF_TRUTH.md`
2. `08_Entity_Data_Model.md`
3. `09_Roles_Permissions_Workflows.md`
4. `11_API_Contracts_and_Schemas.md`
5. `12_Test_and_Quality_Gates.md`
6. `14_Security_Architecture_and_Certificate_Guide.md`
7. `15_Implementation_Control_Checklist.md`
8. `16_Project_Delivery_Roadmap_and_Workstreams.md`
9. `17_Backlog_Epics_and_User_Stories.md`

Erst danach darfst du in konkrete Implementierungsplanung oder Umsetzung gehen.

---

## 3. Verbindliche Arbeitsregeln

- Keine stillen Annahmen
- Keine externen Produktannahmen
- Erst Modell, dann Implementierung
- Keine Umgehung von Governance
- Security / Privacy / Accessibility sind Kernanforderungen

---

## 4. Was du bauen sollst

- Karriere-Startseite
- Arbeitgeberbereich
- CareerPath-Seiten
- JobFamily-Seiten
- strukturierte Stellenanzeigen
- Stellenliste und Stellentdetailseite
- Initiativbewerbungslogik
- Bewerbungsformulare
- Contact-/Ansprechpartnerlogik
- zentrale HR-Freigabelogik
- lokale Eignungs- und Einladungslogik
- Privacy-/Retention-/Applicant-Access-Logik
- AuthN/AuthZ/TLS/mTLS/Audit-Basis

---

## 5. Was du nicht bauen darfst

Du darfst nicht:
- JobPosting als unstrukturierte CMS-Seite behandeln
- Facility und Location vermischen
- JobFamily und CareerPath vermischen
- Applicant Data breit zugänglich machen
- zentrale Approval-Logik optional behandeln
- lokale freie Prozessmodellierung erlauben
- öffentliche Formulare ohne PrivacyNoticeVersion zulassen
- unendliche Speicherung von Bewerberdaten erlauben
- privilegierte Rollen ohne MFA behandeln
- geschützte interne APIs ohne sichere AuthN/AuthZ/TLS-Basis bereitstellen

---

## 6. Zentrale Modellgrenzen

- Facility != Location
- JobFamily != CareerPath
- CareerPage != JobPosting
- LandingPage != CareerPage
- ApplicationForm != ApplicationRoute
- redaktioneller Content != strukturierte Jobdaten

---

## 7. Technische Mindestverantwortung

- Struktur
- APIs
- Governance
- Security
- Privacy

---

## 8. Arbeitsreihenfolge

1. Technical Confirmation
2. API and Contract Layer
3. Core Platform Implementation Planning
4. Governance and Security Layer Planning
5. MVP Execution Plan

---

## 9. Pflichtausgabe vor jedem größeren Umsetzungsschritt

1. Ziel
2. betroffene Domänen
3. Inputs / vorausgesetzte Dokumente
4. Annahmen
5. Risiken
6. zu erzeugende Artefakte
7. relevante Security-/Privacy-/Governance-Kontrollen
8. relevante Tests / Acceptance Criteria

---

## 10. Hard Stop / Escalation Rules

Stopp bei:
- unklarer Trennung Facility vs. Location
- unklarer Trennung JobFamily vs. CareerPath
- fehlendem Bewerbungsziel für JobPosting
- fehlender zentraler Freigabelogik
- fehlender PrivacyNoticeVersion für öffentliche Formulare
- fehlender RetentionPolicy für applicant-related data
- unklarer ApplicantAccessAssignment-Logik
- fehlender MFA-/AuthN-/TLS-/mTLS-Basis bei privilegierten Bereichen
- unklarer Ownership
- Dokumentenkonflikten

---

## 11. Qualitätsregeln

- Done bedeutet nicht nur „läuft“
- Keine impliziten Abkürzungen
- Testpflicht

---

## 12. No-Go Bedingungen

Keine produktionsnahe Freigabe bei:
- geschützte interne APIs anonym
- object-level authorization fehlt
- applicant data außerhalb erlaubten Kontexts sichtbar
- Job ohne zentrale Freigabe veröffentlichbar
- public form ohne PrivacyNoticeVersion
- fehlende RetentionLogik
- TLS-/Zertifikatsbasis unzureichend
- MFA für privilegierte Rollen fehlt
- Secrets/Keys hart codiert
- Audit Logging fehlt

---

## 13. Deine erste Pflichtantwort nach Übergabe

1. bestätigte Liste der gelesenen bindenden Dokumente
2. konsolidierte technische Sicht auf:
   - Entitäten
   - Beziehungen
   - Rollen
   - Workflows
   - Security Boundaries
3. Liste aller offenen kritischen Punkte
4. Vorschlag für die konkrete Umsetzungsreihenfolge Phase 1 bis 3
5. Liste der ersten technischen Deliverables
6. Liste der ersten Test-/Gate-Prüfungen

---

## 14. Letzte verbindliche Regel

Du bist nicht beauftragt, kreativ zu improvisieren.  
Du bist beauftragt, das dokumentierte Enterprise-Zielsystem **präzise, sicher, kontrolliert und nachvollziehbar** umzusetzen.

---

# 21_Wave_1_Implementation_Package.md

## Dokumentstatus
- Version: 1.0
- Zweck: Konkretes Umsetzungs- und Steuerungspaket für Wave 1 der neuen Enterprise-Karriereplattform
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, umsetzungsorientiert
- Ziel: dem Senior Developer Agent einen klaren, kontrollierten und priorisierten Einstieg in die reale Umsetzung geben
- Regel: Wenn dieses Dokument dem Final Source of Truth widerspricht, gilt immer der Final Source of Truth

---

## 1. Ziel dieses Dokuments

Wave 1 ist die **erste kontrollierte Enterprise-fähige Lieferwelle**.

Es soll sicherstellen, dass:
- die zentrale Plattformbasis steht,
- die wichtigsten Zielobjekte und Workflows implementierbar sind,
- die erste öffentliche Candidate Experience lauffähig wird,
- zentrale Governance bereits verankert ist,
- und Privacy / Security / Accessibility / SEO nicht nachträglich, sondern von Beginn an mitgebaut werden.

---

## 2. Wave-1-Leitidee

Wave 1 fokussiert auf:
- Karriere-Startlogik mit mehreren Einstiegen
- strukturierte Stellenplattform
- Initiativbewerbungs-/Bewerbungsweg-Basis
- Arbeitgeber- und CareerPath-Basisbereich
- Governance-/Privacy-/Security-Basis

---

## 3. Wave-1-Zielbild

Wave 1 ist erfolgreich, wenn mindestens vorhanden sind:
1. strukturierte Kernentitäten und Kernbeziehungen
2. Basis-APIs für öffentliche Inhalte und Jobs
3. Karriere-Startseite
4. Arbeitgeberbereich
5. ausgewählte CareerPath-Seiten
6. Stellenliste und Stellentdetailseite
7. Initiativbewerbungsseite / Bewerbungsweg-Basis
8. zentrale JobTemplate- und Approval-Logik
9. lokale Draft-Erstellung im erlaubten Rahmen
10. PrivacyNoticeVersion / Retention-Basis
11. AuthN/AuthZ/TLS/MFA-Basis
12. Audit Logging Baseline
13. Accessibility- und SEO-Basis
14. erste Migrationswelle für Kerninhalte

---

## 4. Scope von Wave 1

### In Scope
- Struktur- und Domänenbasis
- Öffentliche Candidate-Experience-Basis
- Recruiting-/Governance-Basis
- Privacy / Security / Compliance Basis
- Migrationsbasis

### Out of Scope
- vollständiges ATS
- umfassende Interview-/Terminplanung
- umfangreiche Facility-/Location-Detailseiten
- tiefe Mehrsprachigkeit
- breite Landingpage-Fabrik
- Onboarding
- Messaging-/Notification-Automation
- komplexe Integrationen
- freie lokale Prozessmodellierung

---

## 5. Wave-1-Arbeitsstränge

- Workstream 1 – Core Model Build
- Workstream 2 – Public Career Experience Build
- Workstream 3 – Job Governance Build
- Workstream 4 – Applicant Entry & Privacy Build
- Workstream 5 – Security Baseline Build
- Workstream 6 – Migration Wave 1

---

## 6. Priorisierte Wave-1-Features

### P0 – Unverzichtbar
- Core entity implementation
- role/permission baseline
- workflow baseline
- public homepage
- employer page
- job list
- job detail
- ApplicationForm + privacy linkage
- central approval enforcement
- TLS/auth/authz baseline
- audit logging baseline
- retention policy baseline

### P1 – Sehr wichtig
- selected CareerPath pages
- initiative application page
- contact module logic
- service/application guidance page
- selected JobFamily support where needed for MVP

### P2 – Nur wenn Kapazität vorhanden
- deeper service FAQ
- richer module reuse
- early local process variant support beyond minimum
- extended analytics views

---

## 7. Deliverables von Wave 1

- Fachlich / Modell
- Technisch
- Öffentlich sichtbare Oberfläche
- Governance
- Compliance / Quality

---

## 8. Abhängigkeiten innerhalb von Wave 1

- vor öffentlicher Candidate Experience: Entitäten, Rollen, Workflows, APIs, PrivacyNoticeVersion, TLS/Auth/AuthZ
- vor Applicant Data Processing: Form Validation, Privacy, Retention, Applicant Access, Audit Logging
- vor lokalem Recruiting-Einsatz: Templates, Draft Scope, zentrale Review-Flow, Access Scope Controls, MFA

---

## 9. Wave-1-Implementierungsreihenfolge

1. Technical Confirmation Pack
2. Core Schema & Validation Layer
3. Auth / AuthZ / TLS / Audit Baseline
4. Public Experience Core
5. Job Governance
6. Applicant Entry
7. Migration Wave 1 Content Load
8. Hardening & Gate Review

---

## 10. Test- und Gate-Pflichten

- Funktionale Mindesttests
- Sicherheits-Mindesttests
- Privacy-/Compliance-Mindesttests
- Accessibility-/SEO-Mindesttests

---

## 11. Wave-1-Akzeptanzkriterien

- Candidate kann Karriereeinstieg verstehen
- Candidate kann Stellen finden und im Detail sehen
- lokaler Draft ist möglich
- zentrale HR-Freigabe funktioniert
- Bewerberzugriffe sind need-to-know-basiert
- Audit Logging ist aktiv
- Kernseiten sind barrierefrei nutzbar
- keine kritischen Go-Live-Blocker offen

---

## 12. Wave-1-No-Go-Kriterien

Keine Release-Readiness bei:
- Jobs ohne zentrale Freigabe publizierbar
- applicant data ohne Kontextzugriff sichtbar
- öffentliche Formulare ohne PrivacyNoticeVersion
- RetentionPolicy fehlt
- geschützte interne APIs anonym
- object-level authorization fehlt
- kritische Audit Events fehlen
- TLS-/Zertifikatsbasis unzureichend
- MFA-Basis fehlt

---

## 13. Verpflichtende erste Antwort des Senior Developer Agent für Wave 1

1. gelesene Dokumente
2. bestätigte Entitäten/Beziehungen
3. Rollen und Workflowzustände
4. offene kritische Punkte
5. technische Umsetzungsreihenfolge Step 1–4
6. erste Deliverables
7. erste Gate-/Security-/Privacy-Checks

---

## 14. Finale Regel

Wave 1 ist keine “schnelle erste Version”.  
Wave 1 ist die **erste kontrollierte Enterprise-fähige Lieferwelle**.

---

# 22_WP01 bis 27_WP06 – Ausführungspakete (Kurzüberblick)

## 22_Wave_1_Technical_Work_Package_01_Core_Model_and_Auth.md
Fokus:
- Core Model
- Pflichtfelder
- Relationship Integrity
- AuthN/AuthZ Skeleton
- TLS/MFA/mTLS Baseline
- Audit Event Baseline

## 23_Wave_1_Technical_Work_Package_02_API_and_Workflow_Foundation.md
Fokus:
- API Group Segmentation
- Public/Internal/Workflow/APIs
- Workflow Action Endpoints
- Form Submission Baseline
- Audit Hook Map

## 24_Wave_1_Technical_Work_Package_03_Public_Experience_and_Job_Governance_Realization.md
Fokus:
- Homepage
- Employer Page
- CareerPath Pages
- Job List / Job Detail
- Initiative / Application Guidance
- Job Governance Path Realization

## 25_Wave_1_Technical_Work_Package_04_Local_Recruiting_Operations_and_Applicant_Access_Realization.md
Fokus:
- ApplicantAccessAssignment Realisierung
- lokale Bewerberlisten/-detailansichten
- lokale Eignungsprüfung
- Einladungsvorstufe
- privacy-safe internal views

## 26_Wave_1_Technical_Work_Package_05_Privacy_Retention_Compliance_and_Hardening.md
Fokus:
- PrivacyNotice Lifecycle
- Retention Trigger / Actions
- Compliance Hardening
- no-export/no-sharing baseline
- TLS/certificate/MFA/mTLS hardening
- applicant-sensitive release readiness

## 27_Wave_1_Technical_Work_Package_06_Migration_Completion_Readiness_and_Final_Wave_1_Release_Preparation.md
Fokus:
- vollständige Wave-1-Content-Migration
- Ownership / Publish Readiness
- Accessibility-/SEO-Finalisierung
- Release Runbook
- Hypercare / Monitoring
- finaler Go/No-Go-Stand

---

# 29_Developer_Agent_Execution_Bundle.md

## Dokumentstatus
- Version: 1.0
- Zweck: Finales operatives Übergabedokument für den Senior Developer Agent
- Gültigkeit: Enterprise-spezifisch, benchmark-frei, ausführungssteuernd
- Ziel: Einen einzigen, klaren, geordneten und kontrollierten Einstiegspunkt für die technische Umsetzung bereitstellen
- Regel: Dieses Dokument ist ein Ausführungs-Bundle. Fachlich-technisch bindend bleibt der Final Source of Truth.

---

## 1. Ziel dieses Dokuments

Dieses Dokument bündelt die operative Ausführungslogik für den Senior Developer Agent.

Es definiert:
- welche Dokumente bindend sind,
- in welcher Reihenfolge gearbeitet werden muss,
- welche Work Packages nacheinander auszuführen sind,
- welche Gates dabei erfüllt sein müssen,
- welche Stop-Regeln gelten,
- und wie Status, Risiken und Freigaben berichtet werden müssen.

---

## 2. Verbindliche Grundregel

### 2.1 Single Source of Truth
Die einzige fachlich-technische Wahrheit bleibt:

#### `00_FINAL_SOURCE_OF_TRUTH.md`

### 2.2 Keine externen Produktannahmen
Es dürfen keine externen Recruiting-/ATS-/CMS-Produktlogiken in die Umsetzung eingeführt werden.

### 2.3 Keine stillen Annahmen
Wenn Informationen fehlen:
1. Lücke benennen
2. Risiko benennen
3. Entscheidungsvorlage formulieren
4. an kritischer Stelle stoppen

---

## 3. Bindende Dokumente für die Ausführung

### Primäre Steuerungsdokumente
1. `00_FINAL_SOURCE_OF_TRUTH.md`
2. `19_Senior_Developer_Agent_Handover_Prompt.md`
3. `29_Developer_Agent_Execution_Bundle.md`

### Technische Kern- und Kontroll-Dokumente
4. `08_Entity_Data_Model.md`
5. `09_Roles_Permissions_Workflows.md`
6. `11_API_Contracts_and_Schemas.md`
7. `12_Test_and_Quality_Gates.md`
8. `14_Security_Architecture_and_Certificate_Guide.md`
9. `15_Implementation_Control_Checklist.md`

### Delivery- und Scope-Dokumente
10. `16_Project_Delivery_Roadmap_and_Workstreams.md`
11. `17_Backlog_Epics_and_User_Stories.md`
12. `21_Wave_1_Implementation_Package.md`

### Inhalts- und Rollout-Dokumente
13. `13_Content_Migration_and_Inventory.md`
14. `18_Master_Document_Index_and_Usage_Guide.md`

### Wave-1-Work-Packages
15. `22...WP01`
16. `23...WP02`
17. `24...WP03`
18. `25...WP04`
19. `26...WP05`
20. `27...WP06`

---

## 4. Verbindliche Ausführungsreihenfolge

### Phase A – Verständnis und Bestätigung
A1–A3: Lesen und bestätigen aller bindenden Dokumente.

### Phase B – Work Package 01
Core Model & Auth

### Phase C – Work Package 02
API & Workflow Foundation

### Phase D – Work Package 03
Public Experience & Job Governance

### Phase E – Work Package 04
Local Recruiting Operations & Applicant Access

### Phase F – Work Package 05
Privacy / Retention / Compliance / Hardening

### Phase G – Work Package 06
Migration Completion / Release Preparation

---

## 5. Verbindliche Antwortstruktur pro Work Package

1. Read Confirmation
2. Scope Confirmation
3. Planned Deliverables
4. Security / Privacy / Governance Controls
5. Risks and Blockers
6. Gate Readiness
7. Next-Step Readiness

---

## 6. Harte Ausführungsregeln

- Kein Überspringen von Work Packages
- Kein UI vor stabiler Basis
- Keine Security-/Privacy-/Governance-Verschiebung
- Keine lokalen Freiheiten außerhalb des Zielmodells

---

## 7. Harter Gate-Mechanismus

Jedes Work Package muss die Gates aus `12` und `15` erfüllen.  
No-Go, wenn eine Pflichtbedingung offen bleibt.

---

## 8. Harte Stop-and-Escalate-Regeln

Stop bei:
- unklarer Trennung Facility vs. Location
- unklarer Trennung JobFamily vs. CareerPath
- fehlendem Bewerbungsziel
- fehlender zentraler Freigabe
- fehlender PrivacyNoticeVersion / RetentionLogik
- unklarer ApplicantAccessAssignment-Logik
- fehlender MFA-/TLS-/mTLS-Basis
- unklarer Ownership
- Konflikten zwischen zentraler und lokaler Logik

---

## 9. Reporting-Format

Nach jedem Work Package: WP Status Report mit:
1. WP Name
2. Status
3. Deliverables completed
4. Open blockers
5. Security/privacy/governance status
6. Gate status
7. Next-step recommendation

---

## 10. Finaler Wave-1-Abschluss

Wave 1 ist nur abgeschlossen, wenn:
- WP01–WP06 vollständig durchlaufen wurden,
- keine kritische No-Go-Bedingung mehr offen ist,
- und der finale Go/No-Go-Stand positiv ist.

---

## 11. Minimaler Betriebsmodus des Senior Developer Agent

- präzise
- phasenbasiert
- kontrolliert
- auditierbar
- nicht improvisierend

Verboten:
- schnell bauen und später korrigieren
- Annahmen ohne Kennzeichnung
- Security/Privacy/Governance später behandeln
- Work Packages vermischen
- lokale Sonderlogik stillschweigend einführen

---

## 12. Abschlussregel

Dieses Dokument ist das operative Ausführungs-Bundle für den Senior Developer Agent.
Es stellt sicher, dass die Enterprise-Karriereplattform:
- in der richtigen Reihenfolge,
- mit der richtigen Governance,
- mit der richtigen Security-/Privacy-Basis,
- und mit kontrollierten Freigabeschritten
umgesetzt wird.
