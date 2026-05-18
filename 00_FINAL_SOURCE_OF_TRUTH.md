00_FINAL_SOURCE_OF_TRUTH.md
Dokumentstatus

Version: 2.0
Status: verbindlich
Zweck: einzige verbindliche fachlich-technische Quelle für die Umsetzung einer spezialisierten Karriereplattform für den Enterprise
Gültigkeit: ersetzt alle externen Produktvergleiche, Benchmark-Verweise und impliziten Fremdannahmen
Ziel: sichere, kontrollierte und schrittweise Umsetzung einer Enterprise-spezifischen Karriereplattform


1. Verbindlicher Grundsatz
Dieses Dokument ist die einzige verbindliche Quelle für die Umsetzung.
1.1 Enterprise-Only Rule
Die Umsetzung basiert ausschließlich auf:

den fachlichen und strukturellen Anforderungen für den Enterprise,
den verifizierten sichtbaren Elementen der aktuellen Karrierepräsenz,
den explizit definierten Zielentscheidungen dieses Dokuments,
und den vom Auftraggeber/Projektkontext festgelegten Organisations- und Governance-Regeln.

Es dürfen keine externen Produktlogiken nachgebaut oder stillschweigend übernommen werden.
1.2 No External Dependency Rule
Der Senior Developer Agent darf sich nicht auf externe Recruiting-Produkte, externe CMS-Produkte oder generische ATS-Annahmen stützen.
Er darf insbesondere nicht:

externe Recruiting-Plattformen nachbauen,
fehlende Logik aus fremden Produkten ableiten,
Standardverhalten aus generischen ATS-/CMS-Produkten übernehmen,
offene Punkte selbst erfinden.

1.3 Pflicht bei Unklarheit
Wenn Informationen fehlen, muss der Agent:

die Lücke explizit benennen,
das Risiko beschreiben,
eine Entscheidungsvorlage formulieren,
und an der kritischen Stelle stoppen, wenn die Lücke die fachliche oder sicherheitsrelevante Integrität gefährdet.


2. Verifizierter aktueller Enterprise-Kontext
2.1 Aktuelle Karrierepräsenz
Die aktuelle Karrierepräsenz des Enterprises enthält sichtbar mindestens folgende Hauptbereiche:

Arbeitgeber Enterprise,
Beruf und Karriere,
Stellenangebote,
Initiativbewerbung,
Ihr Weg zu uns,
sowie Ansprechpersonen / Ansprechpartner-Kontexte.

Die Plattform enthält außerdem sichtbare Verweise auf Datenschutz und Barrierefreiheit.
2.2 Sichtbare Karrierepfade
Die aktuelle Karrierepräsenz differenziert bereits mehrere Karriere- bzw. Recruiting-Einstiege:

Ausbildung,
Freiwilligendienst: FSJ und BFD,
Praktikum,
Praktisches Jahr und ärztliche Weiterbildung,
Fortbildung und Weiterbildung.

2.3 Sichtbare Jobsuche / Stellenlogik
Die aktuelle Stellenlogik arbeitet bereits mit strukturierten Datenfeldern, darunter:

Referenz,
Einrichtung,
Ort,
Beginn,
Stundenumfang,
Befristung. [dvinci.de]

Zusätzlich ist die Jobsuche mit Berufsfeld-/Kategorielogik verbunden. [dvinci.de]
2.4 Arbeitgeber- und Organisationsbreite
Der Arbeitgeberbereich beschreibt den Enterprise als großen Träger im Gesundheits- und Sozialwesen mit mehreren Einrichtungen, verschiedenen Standorten und vielfältigen Arbeits- und Berufsfeldern. [dvinci.de], [dvinci.de]
Die Seite „Arbeits- und Berufsfelder“ zeigt eine sehr breite Vielfalt fachlicher Felder und Berufe, darunter Pflege, Medizin, Pädagogik/Therapie, Verwaltung, Technik, Küche, Landwirtschaft und weitere Tätigkeitsprofile. [dvinci.de]
2.5 Aktuelle Bewerbungslogik
Die aktuelle Karrierepräsenz beschreibt mindestens folgende Bewerbungswege:

Bewerbung auf ausgeschriebene Stellen per in der Anzeige angegebener E-Mail-Adresse,
Bewerbung für Praktikum / FSJ / Bundesfreiwilligendienst per E-Mail,
Kurzbewerbungsformular für Interessierte, die zunächst unverbindlich Kontakt aufnehmen wollen.

Die aktuelle Seite nennt außerdem ausdrücklich:

einen Datenschutzhinweis / Zustimmung im Formular,
sowie den Hinweis, dass Daten nach sechs Monaten gelöscht werden, wenn keine Bewerbung erfolgt oder keine Einwilligung in die Aufnahme in den Kandidat*innen-Pool vorliegt.


3. Zielsystem
3.1 Produktdefinition
Das Zielsystem ist eine spezialisierte Karriereplattform für den Enterprise mit:

mehreren Karrierepfaden,
vielen Berufsfeldern,
verschiedenen Einrichtungen,
mehreren Standorten,
strukturierten Stellenanzeigen,
Initiativbewerbung,
zentraler Governance,
dezentraler operativer Beteiligung,
Anforderungen an Barrierefreiheit,
Anforderungen an Datenschutz,
Anforderungen an Suchmaschinenfreundlichkeit,
und klarer Erweiterbarkeit.

3.2 Systemcharakter
Das Zielsystem ist:

kein Nachbau eines generischen Recruiting-Produkts
kein reines Website-CMS
kein vollständiges ATS in der ersten Version
keine bloße Neuverpackung der aktuellen Seiten

Das Zielsystem ist:

eine modulare Karriereplattform,
mit strukturierten Karriereinhalten,
strukturierten Jobdaten,
klaren Such- und Bewerbungswegen,
Rollen- und Freigabemodell,
Template-Governance,
Datenschutz-/Sicherheitsbasis,
und kontrollierter lokaler Beteiligung.


4. Produktziele
4.1 Hauptziele

Die bestehende Karriere- und Recruiting-Komplexität des Enterprises klar und strukturiert abbilden.
Mehrere Karrierepfade und Berufsfelder gezielt und verständlich darstellen.
Stellen strukturiert, konsistent und suchbar verwalten und ausspielen.
Initiativbewerbung und ausgeschriebene Bewerbungswege sauber unterstützen.
Lokale fachliche Beteiligung ermöglichen, ohne zentrale Governance zu verlieren.
Fehler durch Templates, Pflichtfelder, Freigaben und kontrollierte Prozesse minimieren.
Datenschutz, Barrierefreiheit, Suchmaschinenfreundlichkeit und Auditierbarkeit systemisch einbauen.
Die Lösung so definieren, dass ein Senior Developer Agent sie ohne externe Referenzen umsetzen kann.

4.2 Nicht-Ziele in der ersten Version
Die erste Version soll nicht umfassen:

vollständige Kandidatenakte eines vollwertigen ATS,
Onboarding-Portal,
Messaging-Automation,
Online-Assessments,
generisches CRM,
tiefgreifende Drittsystem-Integrationen, sofern nicht separat freigegeben,
unkontrollierte lokale Eigenprozesse.


5. Betriebsmodell (Operating Model)
5.1 Zentrale HR-Karriere-Abteilung
Die zentrale HR-Karriere-Abteilung ist die zentrale Governance- und Qualitätsinstanz der Plattform.
Verantwortlichkeiten

Definition und Pflege von Stellenanzeigen-Templates
Definition und Pflege von Prozess-Templates
Definition von Pflichtfeldern und Mindestprozessstandards
Prüfung und Freigabe öffentlicher Stellenanzeigen vor Veröffentlichung
zentrale Candidate-Experience-Standards
zentrale Qualitätsstandards
zentrale SEO-, Accessibility- und Privacy-Standards
KPI-/Funnel-/Prozessoptimierung
Koordination und kontinuierliche Verbesserung der Karriereplattform

5.2 Standorte und Bereiche
Standorte und Bereiche sind für die operative Recruiting-Ausführung im eigenen Kontext verantwortlich.
Verantwortlichkeiten

Erstellung von Stellenanzeigen-Entwürfen auf Basis genehmigter Templates
fachliche Ergänzung lokaler Stellenspezifika
Prüfung der Eignung von Bewerberinnen und Bewerbern für die eigenen Vakanzen
Entscheidung, ob und wann eingeladen wird
Durchführung lokaler Auswahl- und Interview-Schritte
Ausführung lokaler Prozessschritte innerhalb genehmigter Varianten

5.3 Federiertes Modell
Das Zielbetriebsmodell ist federiert:

zentrale Governance und Standardisierung,
lokale fachliche Verantwortung für Eignungsprüfung und Einladung,
kontrollierte lokale Varianten,
keine völlig freien, unkontrollierten Eigenprozesse.

5.4 Harte Regel
Öffentliche Veröffentlichung von Stellenanzeigen ist nur nach Freigabe durch die zentrale HR-Karriere-Abteilung zulässig.

6. Fachliche Kernbegriffe (Glossar)
Diese Begriffe sind verbindlich und dürfen nicht vermischt werden.
6.1 Organization
Die Gesamtorganisation / der Träger.
6.2 Facility
Eine organisatorische Einheit oder Einrichtung.
6.3 Location
Ein geografischer Ort / Standort.
6.4 JobFamily
Ein Berufsfeld bzw. fachlicher Tätigkeitscluster.
6.5 CareerPath
Ein Karrierepfad bzw. Recruiting-Einstieg.
6.6 CareerPage
Eine redaktionelle Seite im Karrierekontext.
6.7 LandingPage
Eine zielgruppenspezifische oder kampagnenbezogene Seite mit definierter Conversion-Absicht.
6.8 JobPosting
Ein strukturiertes Stellenobjekt.
6.9 ApplicationForm
Ein strukturiertes Bewerbungsformular.
6.10 ApplicationRoute
Die strukturierte Logik, an die Bewerbungen weitergeleitet oder zugeordnet werden.
6.11 ContactPerson
Ein öffentlich sichtbarer Ansprechpartner.
6.12 SharedContentModule
Ein wiederverwendbares Inhaltsmodul.
6.13 JobTemplate
Ein zentral gepflegtes Template für Stellenanzeigen.
6.14 ProcessTemplate
Ein zentral gepflegtes Recruiting-Prozess-Template.
6.15 LocalProcessVariant
Eine kontrollierte lokale Prozessvariante innerhalb genehmigter Grenzen.

7. Harte Modellierungsregeln
7.1 Do-not-merge-Regeln
Die folgenden Konzepte müssen strikt getrennt bleiben:

Facility != Location
JobFamily != CareerPath
CareerPage != JobPosting
LandingPage != CareerPage
ApplicationForm != ApplicationRoute
redaktioneller Inhalt != strukturierte Jobdaten

7.2 Do-not-infer-Regeln
Es darf nicht automatisch angenommen werden:

dass jede Stelle denselben Bewerbungsweg hat,
dass jede Einrichtung nur einen Standort hat,
dass jede Karrierepfadseite dieselben Felder braucht,
dass Ansprechpartner global statt kontextbezogen sind,
dass Jobs als Freitextseiten modelliert werden dürfen.

7.3 Struktur vor Freitext
Wo immer möglich, müssen strukturierte Felder statt unstrukturierter Freitext-Container verwendet werden.

8. Verbindliche Domänen des Systems
8.1 Organization Domain
Verantwortlich für:

Organization
Facility
Location
JobFamily
CareerPath
ContactPerson

8.2 Content Domain
Verantwortlich für:

CareerPage
LandingPage
SharedContentModule
SEOProfile
MediaAsset

8.3 Job Domain
Verantwortlich für:

JobPosting
Job-spezifische Inhalte
Jobstatus
Jobveröffentlichung

8.4 Application Domain
Verantwortlich für:

ApplicationForm
ApplicationRoute
Bewerbungs-CTA
Dokumentlogik
Submission-Mode

8.5 Governance Domain
Verantwortlich für:

WorkflowState
Role
Permission
Freigaben
Ownership
Auditierbarkeit

8.6 Discovery Domain
Verantwortlich für:

Jobsuche
Filter
Listen
Zielgruppeneinstiege

8.7 Privacy / Security / Analytics Domain
Verantwortlich für:

PrivacyNoticeVersion
DataRetentionPolicy
ApplicantAccessAssignment
Audit-Events
Sicherheits- und Monitoringlogik
Analytics Events


9. Verbindliches Page- und Navigation-Modell
9.1 Hauptnavigation im Zielsystem
Die Zielplattform muss mindestens folgende Hauptbereiche unterstützen:

Arbeitgeber
Beruf & Karriere
Stellenangebote
Initiativbewerbung
Ihr Weg zu uns / Bewerbung
Ansprechpartner / Kontakt
Service-/Recht-/Datenschutz-/Barrierefreiheitsseiten

Diese Struktur ist direkt anschlussfähig an die sichtbare aktuelle Karrierepräsenz.
9.2 Verbindliche Seitentypen

Karriere-Startseite
Arbeitgeberseite
Berufsfeldseite
Karrierepfadseite
Standortseite
Einrichtungsseite
LandingPage
Stellenliste
Stellentdetailseite
Initiativbewerbungsseite
Kontakt-/Ansprechpartnerseite
FAQ-/Service-Seite
Datenschutz-/Barrierefreiheits-/rechtliche Seite

9.3 Pflicht-Einstiege auf der Karriere-Startseite
Die Karriere-Startseite muss mindestens folgende Einstiegspfade ermöglichen:

Jobsuche,
Karrierepfade,
Berufsfelder oder Arbeitgeberbereich,
Initiativbewerbung.

Diese Anforderung passt zur sichtbaren Enterprise-Startlogik mit mehreren Karrierepfaden und Jobsucheinstieg.

10. Verbindliches Entitätenmodell
10.1 Mindestentitäten
Die Plattform muss mindestens die folgenden Entitäten unterstützen:

Organization
Facility
Location
JobFamily
CareerPath
ContactPerson
CareerPage
LandingPage
JobPosting
ApplicationForm
ApplicationRoute
WorkflowState
Role
Permission
SEOProfile
MediaAsset
SharedContentModule
JobTemplate
ProcessTemplate
LocalProcessVariant
PrivacyNoticeVersion
DataRetentionPolicy
ApplicantAccessAssignment
HiringDecisionStage
AnalyticsEventDefinition

10.2 Harte Mindestbeziehungen

JobPosting gehört mindestens zu:

einer Organization,
einer Facility,
einer Location,
einer JobFamily


CareerPage kann kontextbezogen auf JobFamily, CareerPath, Facility oder Location referenzieren
ApplicationForm muss mit PrivacyNoticeVersion verknüpft werden
ApplicantAccessAssignment muss einen klaren Rollen- und Kontextbezug haben


11. Such- und Discovery-Modell
11.1 Mindestfilter
Die Jobsuche muss mindestens folgende strukturierte Filter unterstützen:

JobFamily / Berufsfeld
Location / Ort
Facility / Einrichtung
Beschäftigungsart oder Stundenumfang
CareerPath, sofern fachlich passend

Die aktuelle Seite zeigt bereits Berufsfeld-/Kategorielogik sowie die Felder Einrichtung, Ort, Stundenumfang und weitere Jobmerkmale. [dvinci.de]
11.2 Harte Discovery-Regeln

Filter müssen kombinierbar sein.
Trefferlisten müssen verständlich und mobil nutzbar sein.
Es darf nicht nur eine generische Volltextsuche ohne strukturierte Filter geben.
Leere Trefferlisten müssen sinnvolle nächste Schritte anbieten.


12. Bewerbungsmodell
12.1 Mindest-Bewerbungsarten
Die Plattform muss mindestens folgende Arten unterstützen:

Bewerbung auf konkrete Stelle
Initiativbewerbung
karrierepfadbezogene Bewerbung, sofern explizit freigegeben

12.2 Aktueller Enterprise-Bezug
Die aktuelle Plattform unterstützt heute bereits:

Bewerbung auf ausgeschriebene Stellen,
Bewerbung für Praktikum / FSJ / BFD,
sowie eine Kurzbewerbungs-/Interessenlogik.

12.3 Harte Zielregeln

Jede veröffentlichte Stelle muss ein Bewerbungsziel haben.
Initiativbewerbung muss als eigener sauber modellierter Flow existieren.
Bewerbungswege dürfen nicht nur informell in Freitext beschrieben sein.
Routing / Zuordnung muss strukturierbar sein.


13. Rollenmodell
13.1 Mindestrollen
Die Plattform muss mindestens folgende Rollen unterstützen:

GlobalAdmin
CMSOwner
CentralHRCareerAdmin
JobEditor
LocalEditor
LocalHiringReviewer
LocalInterviewCoordinator
SEOQAReviewer
PrivacyComplianceReviewer
Publisher
Analyst

13.2 Zentrale Rollenlogik

Zentrale HR-Karriere steuert Templates, Standards, Prüfung und Freigabe.
Lokale Einheiten prüfen fachlich Eignung und führen Auswahl-/Einladungsschritte aus.
Veröffentlichung erfolgt nicht direkt lokal ohne zentrale Freigabe.
Analysten sehen keine operativen Bewerberdetails ohne separate Berechtigung.


14. Workflowregeln
14.1 Standardstatus

draft
in_review
approved
published
archived
rejected

14.2 Seitenworkflow

anlegen
bearbeiten
submit_for_review
QA/SEO Review
approve
publish

14.3 Jobworkflow

Job anlegen
Pflichtfelder vervollständigen
Bewerbungslogik zuordnen
zur Prüfung einreichen
zentrale HR prüft
approve / reject
publish
deactivate / archive

14.4 Bewerberworkflow

Bewerbung eingehen
Kontextbezogene Zuordnung
Access Assignment
lokale Eignungsprüfung
Einladung / weiterer Prozessschritt
Ergebnis / Ausgang
Retention-/Löschlogik auslösen

14.5 Harte Workflow-Regeln

Keine Veröffentlichung ohne Review.
Keine Veröffentlichung ohne Owner.
Kein veröffentlichter Job ohne Bewerbungsziel.
Keine öffentliche Stellenanzeige ohne zentrale Freigabe.
Keine lokale Prozessvariante ohne zentrale Genehmigung.
Keine öffentliche Bewerbungslogik ohne Privacy-/Retention-Basis.


15. Template- und Prozessgovernance
15.1 JobTemplates
Stellenanzeigen müssen template-basiert erstellt werden, wenn für den jeweiligen Bereich / Karrierepfad / Jobkontext ein Template definiert ist.
Mindestzweck

Pflichtfelder erzwingen
Fehlerrisiko reduzieren
Wortlautqualität verbessern
Konsistenz sichern
Freigabe erleichtern

15.2 ProcessTemplates
Recruiting-Prozesse müssen über zentrale ProcessTemplates definiert werden.
Mindestzweck

Mindestprozess sichern
lokale Unterschiede kontrollieren
KPI-Vergleichbarkeit erhalten
Fehler und Compliance-Risiken reduzieren

15.3 LocalProcessVariant
Lokale Unterschiede dürfen nur als kontrollierte Varianten existieren:

innerhalb definierter Grenzen,
zentral genehmigt,
auditiert,
nicht frei erfunden.


16. Datenschutz- und Bewerberdatenschutzregeln
16.1 Aktueller Enterprise-Bezug
Die aktuelle Plattform zeigt bereits:

Datenschutzzustimmung im Kurzbewerbungsformular,
Kandidat*innen-Pool-Bezug,
sowie Löschung nach sechs Monaten, wenn keine Bewerbung oder keine Einwilligung in den Pool vorliegt.

16.2 Zielregeln
Die Plattform muss Bewerberdatenschutz by design and by default unterstützen.
Mindestprinzipien

Zweckbindung
Datenminimierung
Speicherbegrenzung
Integrität und Vertraulichkeit
Nachvollziehbarkeit / Accountability
Need-to-know Zugriff

16.3 Pflichtobjekte

PrivacyNoticeVersion
DataRetentionPolicy
ApplicantAccessAssignment

16.4 Harte Regeln

Kein öffentliches Formular ohne gültige PrivacyNoticeVersion
Kein Bewerberzugriff ohne Rollen- und Kontextbezug
Keine unbegrenzte Speicherung von Bewerberdaten
Keine breite standortübergreifende Einsicht in Bewerberdaten ohne ausdrückliche Legitimation


17. Sicherheitsregeln
17.1 Mindestanforderungen
Die Plattform muss mindestens unterstützen:

HTTPS-only
starke Authentifizierung für interne Rollen
MFA für privilegierte Rollen
objektbezogene Autorisierung
kontextgebundene Bewerberzugriffe
Audit Logging
Zertifikats- und Secret-Management
mTLS für privilegierte interne Service-zu-Service-Kommunikation, sofern dafür vorgesehen

17.2 Harte Regeln

Kein geschützter interner Endpunkt anonym
keine Veröffentlichung ohne Autorisierung
keine sensible Bewerberdaten-Einsicht ohne Rollen- und Kontextprüfung
keine produktive Nutzung ohne gültige Zertifikate und TLS-Baseline
keine Secrets oder privaten Schlüssel hart im Code


18. Accessibility- und SEO-Regeln
18.1 Accessibility
Die Plattform muss Barrierefreiheit als Kernanforderung behandeln.
Die aktuelle Enterprise-Karriereseite verweist bereits sichtbar auf Barrierefreiheit.
Mindestanforderungen

semantische Struktur
Tastaturbedienbarkeit
sinnvolle Labels
verständliche Fehlermeldungen
Fokuszustände
verständliche Linktexte

18.2 SEO
Die Plattform muss suchmaschinenfreundliche Karriere- und Jobinhalte unterstützen.
Mindestanforderungen

sprechende URLs
page-level title / description
canonical handling
strukturierte Jobdaten
indexierbare Jobdetailseiten
sinnvolle interne Verlinkung


19. Migration-Grundsatz
19.1 Enterprise als Content-Quelle
Für Inhalte und aktuelle Struktur ist die aktuelle Enterprise-Karriereseite die Ausgangsbasis.
Das betrifft insbesondere:

Karriere-Startlogik,
Karrierepfade,
Arbeitgeberinhalte,
Berufsfelder,
Stellenlogik,
Bewerbungs-/Kontakt-/Service-Inhalte. [dvinci.de], [dvinci.de], [dvinci.de]

19.2 Harte Migrationsregel
Inhalte gelten nicht als migriert, nur weil sie visuell kopiert wurden.
Inhalte gelten erst dann als migriert, wenn:

sie dem richtigen Zieltyp zugeordnet sind,
strukturierte Felder korrekt befüllt sind,
Ownership definiert ist,
Workflow und Governance korrekt greifen,
Privacy-/Accessibility-/SEO-Prüfungen erfolgt sind,
und die Inhalte das neue Betriebsmodell unterstützen.


20. Implementierungsregeln für den Senior Developer Agent
20.1 Vor jeder großen Umsetzungsphase liefern
Der Agent muss vor jedem größeren Schritt liefern:

Ziel
Inputs
Annahmen
Risiken
Output-Artefakte
Test-/Abnahmekriterien

20.2 Stop-and-Escalate-Regeln
Der Agent muss stoppen und eskalieren bei:

unklarer Trennung zwischen Facility und Location,
unklarer Trennung zwischen JobFamily und CareerPath,
fehlendem Bewerbungsziel,
unklarer zentraler vs. lokaler Zuständigkeit,
fehlender Privacy-/Retention-Basis,
fehlendem Kontext für öffentliche Ansprechpartner.

20.3 Verbotene Abkürzungen
Der Agent darf nicht:

JobPosting als unstrukturierte CMS-Seite behandeln,
JobFamily oder CareerPath als Freitextfeld modellieren,
zentrale Freigabeprozesse überspringen,
lokale Eigenprozesse unkontrolliert öffnen,
Datenschutz-/Security-/Accessibility-Themen auf „später“ verschieben,
externe Produktlogiken stillschweigend übernehmen.


21. Letzte verbindliche Regel
Wenn dieses Dokument und ein anderes älteres Dokument widersprüchlich sind, gilt immer dieses Dokument.
Wenn dieses Dokument an einer Stelle unvollständig ist, muss der Agent nicht raten, sondern die Lücke explizit melden.