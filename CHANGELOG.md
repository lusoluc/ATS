# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/de/), Versionierung: [SemVer](https://semver.org/lang/de/).
Update-Pfad: `docker compose pull && docker compose up -d` (Migrationen laufen automatisch, siehe INSTALL.md).

## [Unreleased]

### Hinzugefügt (Benutzerhandbuch Teil 3–6 — und der Wächter, der bisher fehlte)

Das Handbuch ist vollständig: **Teil 3** (Wenn mehrere mitreden: Freigaben mit
§-99-Sonderregeln, Auswahlgremien, Vertretung, Governance-Überblick,
Schwerbehindertenvertretung), **Teil 4** (Einrichten — für die
Personalverwaltung, mit der sinnvollen Reihenfolge beim Aufsetzen), **Teil 5**
(Wenn etwas klemmt: die vier Fälle, die im Betrieb wirklich vorkommen, mit den
Befehlen zum Beheben) und **Teil 6** (Was das System für Sie erledigt:
Löschfristen, Nachweiskette, Auswertung ohne Namen, Bewerbendenrechte — und
ausdrücklich, was das System bewusst *nicht* tut).

15 neue Bilder, alle über `manage.py handbuch_bilder` erzeugt; 26 insgesamt.

**Der Wächter, der bisher fehlte:** Angekündigt war „jede interne Seite kommt
im Handbuch vor oder steht mit Begründung in der Ausnahmeliste" — gebaut war
bislang nur die Totprüfung der Liste. Die eigentliche Prüfung fehlte, das
Handbuch hätte also beliebig unvollständig werden können, ohne dass etwas rot
wird. Jetzt geht der Wächter über alle Routen, blendet Djangos eigene
Oberfläche, Detailseiten und Aktionen aus und verlangt für jeden verbleibenden
Bildschirm entweder eine Kapitelzuordnung oder einen Schuldeintrag. Ein zweiter
Test prüft, dass jedes zugeordnete Kapitel im Handbuch wirklich existiert — eine
Zuordnung auf ein erfundenes Kapitel wäre schlimmer als gar keine.

Gegenprobe: Nimmt man eine Seite aus der Zuordnung, meldet der Wächter genau
diese. 22 Seiten stehen noch als offene Schuld drin (Erscheinungsbild, CMS,
HRIS/SAP, Talent-Pool und weitere) — jede mit dem Grund, warum sie noch fehlt.

### Hinzugefügt (Benutzerhandbuch Teil 1+2 — mit Bildern, in der Anwendung, gegen Verrotten gesichert)

Bisher gab es genau ein Dokument für Endanwender: `Handbuch_HR_Anwender.md`,
145 Zeilen, entstanden zu einer Zeit, als die Plattform aus Dashboard, Stellen
und Stammdaten bestand. Es kannte weder Sammel-Postfach noch Freigaben,
Talent-Pool, Interview-Leitfaden, Datenaufbewahrung, Entgelttransparenz oder
Vertretungen — und verwies auf zwei Bilder unter einem absoluten Pfad des
Entwicklerrechners. Bei inzwischen 129 Routen war das kein Update, sondern ein
Neubau.

Neu ist `HANDBUCH.md` mit **Teil 1** (Die ersten 20 Minuten: anmelden,
zurechtfinden, jemanden suchen) und **Teil 2** (die sechs Wege durch den
Alltag: ausschreiben, ändern, sichten, schreiben, Gespräche, entscheiden) —
aufgabenorientiert statt nach Menüpunkten, mit einem Bild an jedem Schritt und
einem Einstieg nach Rolle. Lesbar auch unter **Hilfe & Handbuch** in der
Anwendung selbst, samt Inhaltsverzeichnis und Druckansicht (Strg+P ergibt ein
sauberes Heft ohne Menü und Schaltflächen — dafür braucht es kein
Zusatzwerkzeug).

**Die Bilder entstehen reproduzierbar:** `manage.py handbuch_bilder` legt eine
eigene Testdatenbank an, befüllt sie mit erfundenen Personen, startet einen
Testserver, meldet sich als die jeweilige Rolle an und schießt die
Screenshots — danach wird die Datenbank wieder entfernt. Die Arbeitsdatenbank
wird nie berührt: Ein Handbuch geht per Mail herum und landet auf
Schulungsrechnern, echte Bewerberdaten haben darin nichts verloren.

**Und es kann nicht still verrotten.** Vier Wächter laufen bei jedem Testlauf:

- Kapitel über eine Seite, die es nicht mehr gibt → rot.
- Ein im Handbuch genannter Knopf, den keine Vorlage kennt → rot. (Fand
  prompt den ersten Fehler: Das Handbuch schrieb „Veröffentlichen“, die
  Schaltfläche heißt „Stellenangebot veröffentlichen“.)
- Ein Screenshot, dessen Vorlage sich seit der Aufnahme geändert hat → rot,
  mit dem Befehl zum Neuerzeugen. Der Vergleich läuft über Vorlagen-Hashes im
  Manifest, nicht über Dateidaten — die setzt Git beim Auschecken neu.
- Bild ohne Alt-Text → rot.

Seiten, die Teil 1+2 noch nicht erklären (Einrichtung, Governance,
Störungsfälle), stehen mit Verweis auf den geplanten Teil in einer
Ausnahmeliste — als Schuld, nicht als Freibrief; tote Einträge darin fallen
ebenfalls auf.

Nebenbei: Die gerenderte Handbuch-Seite läuft durch `nh3` (nur Handbuch-Tags,
keine Ereignis-Attribute, nur http/https). „Nur Entwickler ändern diese Datei“
ist eine Annahme, keine Sicherheitsmaßnahme.

### Behoben (Die Rolle „Viewer" konnte alles, was ein Hiring Manager kann)

Aufgefallen bei der Vorbereitung des Benutzerhandbuchs: `Viewer` und
`Hiring-Manager` waren technisch **identisch** — beide liefen nur über
`any_staff_required`. Ein „Viewer" konnte damit das Board umsortieren,
Aufgaben abhaken, Seiteninhalte und Landingpages bearbeiten und
Personalbedarf melden. Ein Rollenname, der etwas anderes verspricht als er
hält, ist in einer Rechteverwaltung besonders teuer: Danach werden Zugänge
vergeben — „der schaut ja nur" — und niemand prüft nach. Ein Handbuch, das
„Viewer = nur lesen" geschrieben hätte, wäre eine Zusicherung gewesen, die
der Code nicht einlöst.

Jetzt: `Viewer` **sieht** alles in seinem Bereich und **ändert nichts**.
Geprüft wird am Verfahren (POST), nicht an der ganzen Seite — sonst hätte
die Verschärfung dem Viewer genau die Einsicht genommen, für die es die
Rolle gibt.

Zwei Dinge, die bewusst so bleiben:

- **Ausdrückliche Benennungen schlagen die Basisrolle.** Wer namentlich in
  ein Auswahlgremium oder eine Freigabestufe berufen wurde, entscheidet
  genau dort — auch als Viewer. Sonst könnte ein Betriebsratsmitglied mit
  Basisrolle Viewer seine eigene Freigabe nicht mehr erteilen. Dasselbe gilt
  für die eigene Vertretung. Alle vier Ausnahmen stehen mit Begründung im
  Wächter.
- **Vertretung ist keine Rolle.** Die Demo führte die Urlaubsvertretung als
  `Viewer` — was nur funktionierte, solange Viewer faktisch alles durfte.
  Korrigiert: Die vertretende Person trägt die Rolle der vertretenen, die
  Vertretung selbst ist eine Delegation. Dafür gibt es jetzt ein echtes
  Viewer-Demokonto (`demo-einsicht`, Standortleitung).

Dazu die Oberfläche: Ein Knopf, der ins 403 läuft, ist schlimmer als kein
Knopf — er behauptet eine Möglichkeit, die es nicht gibt. Alle Formulare der
betroffenen Seiten erscheinen für den Viewer nicht mehr, samt ihrer Karten
(ein leerer Rahmen verwirrt genauso), und an ihrer Stelle steht, warum.

Der Wächter sichert die Fehlerklasse: Jede interne Seite, die per POST etwas
verändert, muss den Viewer aussperren oder mit Begründung in der Ausnahme-
liste stehen — inklusive Totprüfung und Funktionsprobe. Gegenprobe: Nimmt
man den Schutz an zwei Stellen weg, meldet er genau diese zwei.

### Behoben (nach einem KI-Ausfall lässt sich die Bewertung nachholen)

Aus der Frage, was jemand tut, der nach einer Woche zurückkommt und einen
längeren KI-Ausfall vorfindet. Paket BA deckte die Warteschlange ab — der
Weg **daneben** blieb offen:

- **Im Sofort-Modus entstand gar keine Aufgabe**: War die KI beim
  Bewerbungseingang nicht erreichbar, kam die Bewerbung ohne Einordnung an
  — und es gab **keinen Weg**, das je nachzuholen. Jetzt zählt die Seite
  *Wiederkehrende Jobs* die offenen Bewerbungen ohne Einordnung und reiht
  sie per „Bewertung nachholen" zur Bewertung ein (Audit-Eintrag). Gesucht
  wird am Zustand, nicht an der Ursache — dieselbe Schaltfläche hilft
  also auch, wenn eine gescheiterte Aufgabe nach 90 Tagen weggeräumt wurde
  oder die Vorbewertung erst später eingeschaltet wird. Entschiedene
  Vorgänge bleiben unberührt, und ohne eingeschaltete Vorbewertung
  passiert nichts (die Aktivierung bleibt eine bewusste Entscheidung).
- **Ein Ausfall trat als Ergebnis auf**: War die KI nicht erreichbar, fiel
  das Scoring still auf ein Keyword-Raten zurück — die Liste bestand aus
  `django`, `python`, `react`, `sales` und ähnlichem. Eine
  Pflegefachkraft mit zwölf Jahren Erfahrung bekam damit ein „D — Geringe
  Übereinstimmung mit dem Anforderungsprofil", und im Kandidaten-Modal war
  das von einem echten KI-Urteil nicht zu unterscheiden. Der Fallback ist
  entfernt: Bei nicht erreichbarer KI wird ein Fehler gemeldet, die
  Bewerbung ohne Score angenommen und zur Nachbewertung eingereiht. Kein
  erfundener Score.

Dazu eine Betriebs-Checkliste „Nach einem längeren KI-Ausfall" in
OPERATIONS.md: erkennen, Ursache beheben, gescheiterte Aufgaben neu
einreihen, Bewertung nachholen — alles über die Oberfläche, ohne Shell.

### Behoben (KI-Queue übersteht Ausfälle — und ist sichtbar)

Dieselbe Frage wie an die Zustell-Jobs, diesmal an die KI-Warteschlange
(asynchrone Vorbewertung eingehender Bewerbungen): Was passiert, wenn etwas
schiefgeht? Vorher vier Wege, auf denen Arbeit still verloren ging:

- **Ein Fehlschlag verbrannte alle Versuche in Sekunden**: Der Task kam
  sofort wieder nach vorn und scheiterte sofort erneut — ein
  5-Minuten-Ausfall der lokalen KI machte die gesamte Warteschlange
  **endgültig** kaputt. Jetzt wartet der nächste Versuch (Backoff 2/10
  Minuten), bis die Störung realistisch vorbei sein kann. Der alte Test
  kodierte das Sofort-Wiederholen als Soll und wurde auf die neue Wahrheit
  umgeschrieben.
- **Ein Worker-Absturz verlor den Task für immer**: Zwischen Übernahme und
  Ergebnis gestorben (Neustart, Deploy, OOM) blieb er ewig „in Arbeit",
  kein Lauf nahm ihn wieder auf. Jetzt holt jeder Lauf verwaiste Tasks
  zurück; ohne Restversuche enden sie ehrlich als fehlgeschlagen.
- **„KI-Analyse läuft im Hintergrund …" log für immer**: Der Platzhalter
  blieb auch stehen, wenn die Analyse endgültig gescheitert war — oder nie
  ein Worker lief. Jetzt ersetzt ihn bei endgültigem Fehlschlag ein
  ehrlicher Vermerk („bitte regulär von Hand sichten"); eine von Hand
  eingetragene Begründung wird nie überschrieben. Formular und Worker
  teilen sich die Konstante, ein Test erzwingt das.
- **Fehlgeschlagen war eine unsichtbare Endstation**: Kein Bildschirm
  zeigte die Queue, neu anstoßen ging nur per Datenbank-Shell. Jetzt zeigt
  die Seite *Wiederkehrende Jobs* den Queue-Zustand (samt Alarm, wenn die
  älteste wartende Aufgabe länger liegt, als ein laufender Worker erklären
  könnte — dann läuft schlicht keiner) und bietet „Fehlgeschlagene erneut
  einreihen" mit Audit-Eintrag. Auf Installationen ohne KI erscheint der
  Block nicht.

Dazu: `AI_ASYNC` (Vorbewertung im Hintergrund statt während des
Bewerbungs-Requests) war nur per Shell schaltbar — das L6-Versprechen „die
Bewerbungsseite wartet nie auf die KI" war im Produkt nicht aktivierbar.
Der Schalter steht jetzt neben der Vorbewertung auf der KI-Seite, mit
Hinweis auf den nötigen Worker. Und `data_retention` räumt die
Task-Historie auf (erledigt: 30 Tage, gescheitert: 90).

Gegenprobe: Die neue Testdatei läuft gegen den alten Queue-Code rot.

### Behoben (Nachschärfung: Selbst-Audit der elf Pakete AN–AY)

Ein Durchgang durch alle elf Pakete mit einer Frage: Wo wurde eine Abkürzung
genommen oder etwas nur teilweise gelöst? Vier Funde, alle behoben:

- **Screening-Antworten lagen im Klartext** (Lücke aus dem
  Verschlüsselungs-Paket): `Application.screeningAnswersJson` trägt die
  Antworten der bewerbenden Person auf die Screening-Fragen — bei
  Freitext-Fragen ihre eigenen Worte, dieselbe Kategorie wie das
  Anschreiben, das eine Zeile drüber längst verschlüsselt war. Der Wächter
  prüfte nur Char-/Textfelder, und ein JSONField ist keins von beiden —
  genau durch diese Lücke rutschte das Feld. Jetzt: `EncryptedJSONField`
  (Fernet at-rest, Lesen liefert weiter das dict, auch über
  `values_list`), Migration im Vier-Schritt (neue TEXT-Spalte, Daten
  verschlüsselt kopieren, jsonb-Spalte entfernen, umbenennen — ein
  direktes `AlterField` bräuchte auf PostgreSQL `USING` und bräche dort),
  und der Wächter prüft JSONFelder mit. Gegenprobe: Feld testweise auf
  JSONField zurückgedreht → Wächter meldet exakt dieses Feld.
- **Das Job-Alert-Suchwort lag im Klartext**: `keyword` ist von der Person
  frei getippt („Teilzeit Nachtdienst") — anders als die ID-Listen
  `categories`/`locations` echter Freitext, der etwas über sie aussagt.
  Die E-Mail derselben Zeile war verschlüsselt, das Suchwort nicht.
  Verschlüsselbar, weil das Matching in Python läuft, nie per DB-Filter.
  Der Feld-Wächter deckt jetzt auch `JobAlertSubscription` ab; die
  strukturierten JSON-Felder (`ratingsJson`, `guideCoverageJson`,
  ID-Listen) stehen mit Begründung in der Ausnahmeliste.
- **`ai_eval` fehlte unbegründet im Zeitplan**: Die Auslassung war eine
  Entscheidung (der Job braucht eine erreichbare lokale KI und stünde ohne
  KI-Profil jede Woche rot), stand aber nirgends. Jetzt dokumentiert —
  im Zeitplan-Modul und in OPERATIONS.md.
- **Drei veraltete Kommentare** behaupteten noch `fail_silently`-Verhalten,
  das seit Paket AW nicht mehr existiert; dazu eine Alt-Verrenkung beim
  `--dry-run`-Lesen. Bereinigt.

### Behoben (Zustell-Jobs verloren Fehlschläge endgültig — und behaupteten Versand)

Fortsetzung von Paket AX, dieselbe Frage an die vier Zustell-Jobs
(Job-Alerts, Termin-, Entscheidungs- und Feedback-Erinnerungen). Alle liefen
bereits über `send_notice` — werteten dessen Rückgabewert aber nicht aus.
Drei Folgen, an jedem der vier Wege:

- **Einmal-Marker wurden auch bei Fehlschlag gesetzt** (`lastAlertSentAt`,
  `reminderSentAt`, Erinnerungs-Marker). Ein vorübergehender
  Mailserver-Ausfall verlor die Benachrichtigung **endgültig** — kein
  späterer Lauf wiederholte sie. Bei einer Termin-Erinnerung heißt das: Die
  Person erscheint unvorbereitet oder gar nicht, und niemand weiß warum.
- **Protokolle behaupteten Versand** (`ALERT_SENT`,
  `INTERVIEW_REMINDER_SENT`, `FEEDBACK_REMINDER_SENT` entstanden vor bzw.
  unabhängig vom Ergebnis) — dasselbe Muster wie der SBV-Vermerk in Paket AN.
- **Die Erfolgsmeldung zählte Versuche statt Zustellungen**: „12 Alerts
  versendet" konnte bei totem Mailserver vollständig erlogen sein, der
  Scheduler-Vermerk blieb grün.

Jetzt: Marker, Protokoll und Zählung **nur bei Zustellung**. Fehlschläge
werden gezählt und beim nächsten Lauf wiederholt — auch die Portal-Nachricht
der Termin-Erinnerung entsteht erst mit der Mail, sonst gäbe es beim
Wiederholen Doppel. Schlägt **alles** fehl, endet der Job mit Fehler und
steht rot auf der Jobs-Seite; Teilfehler bleiben grün, weil eine einzelne
kaputte Adresse den Job nicht dauerhaft röten darf — wiederholt wird sie
trotzdem. Scheitert nur die Team-Mail einer Termin-Erinnerung, zählt das als
Fehlschlag, verhindert den Marker aber nicht: Die bewerbende Person deshalb
doppelt zu erinnern wäre der falsche Preis.

Nebenfund: Das Lösch-Protokoll der Job-Alerts nutzte Pythons `hash()` —
der ist pro Prozess randomisiert, der Wert war als Nachweis wertlos. Jetzt:
gekürzter Blind-Index, deterministisch.

### Behoben (Jobs, die liefen — aber nichts bewirkten)

Zwei Funde derselben Klasse im Zeitplan, beide vom neuen Scheduler erst
sichtbar gemacht:

**`verify_audit` hakte einen Integritätsbruch grün ab.** Das Kommando meldete
den Bruch der Audit-Hash-Kette nur als roten Text und endete mit Exit-Code 0.
Cron und der Zeitplan-Dienst reagieren auf Exit-Codes, nicht auf Textfarben —
der Lauf stand als „in Ordnung" im Vermerk, ausgerechnet beim Job, der
Manipulation erkennen soll. Jetzt: Ein Bruch ist ein `CommandError`
(Exit 1), der Scheduler vermerkt „fehlgeschlagen" mit dem Befund, und alle
HR-Admins mit hinterlegter Adresse werden benachrichtigt. Der Versand ist
Beigabe: Scheitert die Alarm-Mail, bleibt der Fehler trotzdem die Meldung.

**Der Wochenbericht erreichte niemanden.** Ohne `--out` ging er nach stdout —
im Zeitplan-Dienst also ins Docker-Log, das niemand liest. Der Job stand grün
im Vermerk, die Leitung bekam nie einen Bericht. Der Docstring vertröstete
seit WP6 auf „Versand folgt mit der Betriebs-Infrastruktur in WP7" — die
Versand-Schicht existierte längst. Jetzt: Ohne `--out` geht der Bericht per
Mail an alle HR-Admins. Kann nicht zugestellt werden (kein Mailserver, keine
Adressen), endet das Kommando mit Fehler statt mit grünem Haken — ein
Bericht ohne Empfänger ist kein Erfolg. `--out` schreibt weiterhin eine
Datei, dann ohne Versand.

Ein bestehender Test kodierte das alte Verhalten (Bericht ins Leere =
Erfolg); er prüft denselben Inhalt jetzt am Ort, an dem er ankommt.

### Geändert (Wächter beweisen bei jedem Lauf, dass sie etwas sehen)

Die Doku sagte: „Die Wächter sind selbst getestet: In der Entwicklung wurde
bewiesen, dass der Auth-Wächter eine ungeschützte View meldet." Das war ein
Handnachweis, der genau einmal lief. Von 20 scannenden Wächtern prüften nur
drei, ob ihr Scan überhaupt etwas gesehen hatte — verschiebt jemand ein
Verzeichnis oder ändert eine Struktur, laufen die übrigen ins Leere: grün und
wertlos, ohne dass es auffällt.

- **Alle Datei-Scans laufen jetzt über zwei zentrale Helfer**
  (`projekt_dateien()` / `projekt_templates()`), die bei jedem Aufruf eine
  plausible Mindestmenge verlangen und sonst laut fehlschlagen. 17 Wächter
  umgestellt, keine Reste — die drei verbliebenen Roh-Scans sind die Helfer
  selbst und der Meta-Wächter über die Testdateien, der seinen eigenen
  Selbstnachweis trägt.
- **Funktionsprobe statt Behauptung**: `GuardrailScansProveThemselvesTestCase`
  lässt die Helfer gegen einen absichtlich leeren Baum laufen (muss
  anschlagen) und die Schlucker-Suche gegen einen absichtlich kaputten (muss
  fündig werden) — bei jedem Testlauf, nicht einmal in der Entwicklung.
- Die Scans in `test_kontrast.py`, `test_laufzeit.py` und `test_zeitplan.py`
  tragen denselben Selbstnachweis.

### Behoben (Wächter, die eine Liste prüften statt einer Regel)

Ein Durchgang durch die eigenen Sicherungen — mit derselben Frage, die sonst
dem Produktcode gilt: Prüft der Wächter die Regel, oder nur die Fälle, die
jemand einmal aufgeschrieben hat?

**Erwartungslisten.** Der Autocomplete-Wächter (WCAG 1.3.5) sah in genau zwei
Templates nach — und behauptete im Docstring, neue Bewerber-Formulare fielen
„automatisch" darunter. Das stimmte nicht. Der Label-Wächter führte eine
zweite, ähnliche Liste mit sechs Einträgen.

Beide leiten die öffentlichen Templates jetzt aus der `PUBLIC_ALLOWLIST` des
Auth-Wächters ab — der einzigen Liste dieser Art, die selbst auf tote Einträge
geprüft wird — und folgen `extends`/`include`, weil ein Feld auch in einem
Baustein stecken kann. Statt 2 bzw. 6 werden jetzt 18 Templates geprüft.

Und der breitere Blick fand sofort etwas: Im **Kandidatenportal** trug das
Telefonfeld kein `autocomplete="tel"` — die eigene Nummer der bewerbenden
Person, also genau der Fall, den WCAG 1.3.5 meint. Dasselbe beim Feld für die
neue E-Mail-Adresse. Beide ergänzt.

Damit die Ableitung nicht still leerläuft (ein Wächter über null Dateien wäre
grün und wertlos), prüft sie sich selbst: Das Bewerbungsformular **muss**
enthalten sein.

**Ausnahmelisten.** Von acht führten nur zwei eine Prüfung auf tote Einträge.
Eine Ausnahme, die ins Leere zeigt, ist eine offene Tür ohne Haus: Sie fällt
niemandem auf, und legt jemand später etwas Gleichnamiges an, lässt der
Wächter es wortlos durch. Alle sechs haben die Prüfung jetzt — auch die
derzeit leere, sonst fiele der erste Eintrag sofort aus jeder Kontrolle.

Neuer Wächter `GuardrailExceptionListsAreCheckedTestCase` über die Wächter:
Wer eine Ausnahmeliste führt, muss sie prüfen.

### Behoben (mein eigener Wächter prüfte eine Liste statt der Fehlerklasse)

Das Verschlüsselungs-Paket nahm sechs Modelle mit — und der Wächter dazu prüfte
genau diese sechs namentlich. Er kodierte damit die Fälle, die gefunden worden
waren, nicht die Regel dahinter. Prompt übersehen:
**`JobAlertSubscription.email`**, die private Adresse einer Person, die sich für
Stellen interessiert. Dieselbe Art Angabe wie im Talent-Pool, nur ein Modell
weiter.

- Die Adresse ist jetzt verschlüsselt, mit demselben Blind-Index wie
  `Applicant` und `TalentPoolSubscription`. Die Zusage „genau ein Abo je
  E-Mail" hängt damit am Index statt an der Spalte — inklusive Test, dass
  Groß-/Kleinschreibung kein zweites Abo anlegt (sonst wäre das Double-Opt-in
  umgangen).
- **Der Wächter läuft jetzt über jedes Modell** und erkennt Felder am Namen
  (E-Mail, Telefon, Vor-/Nachname, Anschrift). Gegen den alten Stand geprüft:
  Er meldet die übersehene Stelle.

Geprüft und bewusst **nicht** verschlüsselt, mit Begründung im Wächter:

- `ContactPerson` (Name, E-Mail, Telefon) — steht auf jeder Stellenanzeige im
  Klartext, wird also absichtlich veröffentlicht. Eine Verschlüsselung schützte
  nichts, was nicht ohnehin öffentlich ist, kostete aber die alphabetische
  Sortierung der Kontaktliste: `order_by('lastName')` würde Ciphertext
  sortieren — lautlos falsch, ohne Fehlermeldung.
- `Location.address` — Anschrift einer Einrichtung, kein Personendatum.

### Behoben (halbe Seite Bereichszahlen, halbe Seite Gesamtzahlen)

Die Auswertungs-Seite trägt im Code den Vermerk „BOLA-gescopt", und ihre
Funnel-Zahlen waren es auch. Zwei Blöcke nicht: die Kampagnen- und
Landingpage-Quoten und **Einstellungen gesamt**. Eine Standortleitung las
damit ihre eigenen Bewerbungszahlen direkt neben Kennzahlen der ganzen
Organisation — ohne dass die Seite den Unterschied markiert hätte.

Gemessen im Test: Eine Recruiterin mit Zugriff nur auf Hamburg sah **3 statt 1**
Kampagnen-Bewerbungen und **2 statt 1** Einstellungen.

Das ist schlimmer als eine durchgehende Entscheidung in die eine oder andere
Richtung: Wer eine Quote liest, muss wissen, worauf sie sich bezieht. Dass es
ein Versehen war und kein Entwurf, zeigt der Block unmittelbar daneben — dort
ist das Scoping ausdrücklich kommentiert.

- Beide Blöcke leiten jetzt aus dem bereits gescopten Bestand ab.
- Geprüft und in Ordnung befunden statt angenommen: Die Quellen-Kanäle und die
  Landingpage-Verwaltung sind ebenfalls ungescopt, aber ausschließlich für
  HR-Admins erreichbar — und die haben ohnehin Vollzugriff.

Neuer Wächter `GuardrailAnalyticsIsScopedTestCase`: In diesem Modul muss jeder
Zugriff auf `Application.objects` Argument von `scope_applications` sein. Wie
zuletzt wurden Test und Wächter gegen den alten Stand geprüft und schlagen
dort fehl.

### Behoben (Altbestand der Uploads trug weiter den Namen — und der Download verlor ihn)

Nachtrag zum Verschlüsselungs-Paket. Zwei Enden desselben Fadens:

**Der Bestand.** Neue Uploads landen namenlos in der Ablage, die vorhandenen
Dateien hießen weiterhin `<zufall>_Lebenslauf_Maria_Schmidt.pdf`. Ein
Verzeichnis-Listing des Medienordners blieb damit eine Namensliste — obwohl
dieselben Namen in der Datenbank verschlüsselt liegen. Neu:
`manage.py anonymize_upload_names` (mit `--dry-run`), wiederholbar.

- Kopieren statt Umbenennen im Dateisystem, gelöscht wird erst, wenn die Kopie
  nachweislich liegt: Ein abgebrochener Lauf darf keine Datei verlieren, und
  Fremd-Speicher (S3, MinIO) kennen kein `rename`.
- Datensätze, deren Datei in der Ablage **fehlt**, bleiben unangetastet und
  werden gemeldet. Wäre der Speicher nur vorübergehend nicht erreichbar, würde
  ein neuer Pfad die Zuordnung endgültig zerstören.
- Beim Umbenennen wird der Anzeigename aus dem alten Pfad gerettet und
  verschlüsselt im Datensatz abgelegt.

**Der Download.** `download_cv` leitete den Dateinamen aus dem Ablagepfad ab —
„alles nach dem ersten Unterstrich". Mit der namenlosen Ablage gibt es keinen
Unterstrich mehr, der Browser bekam also `a1b2c3-....pdf` als Dateinamen. Das
war eine Nebenwirkung des Verschlüsselungs-Pakets, die dort niemandem auffiel.
Neu: `Application.cvFileName` (verschlüsselt) trägt den Anzeigenamen; die alte
Ableitung bleibt als Rückfall, bis das Umbenennungs-Kommando gelaufen ist.

Nebenbei korrigiert: `exclude(feld__in=["", None])` schließt NULL-Zeilen
**nicht** aus — in SQL ist `NOT IN (…, NULL)` für NULL selbst wieder NULL. Die
erste Fassung des Kommandos zählte deshalb 84 Bewerbungen ohne Lebenslauf als
„bereits namenlos".

### Behoben (verschlüsselt war die Person, nicht das, was über sie geschrieben stand)

Name, Anschrift und E-Mail der bewerbenden Person lagen längst Fernet-
verschlüsselt. Die Sätze **über** sie nicht:

- **interne Notizen** — oft die heikelsten Sätze im ganzen System,
- der **gesamte Schriftwechsel** (`Message.content`),
- die drei Freitextfelder des **Interview-Feedbacks** (Stärken, Bedenken,
  Kommentar),
- **KI-Begründung** und **Rücktrittsgrund**,
- die **Talent-Pool-Adresse** — dieselbe Angabe derselben Person wie
  `Applicant.email`, nur ohne Schutz,
- der **Dateiname des Lebenslaufs**: Uploads hießen `<uuid>_<Originalname>`,
  und der lautet typischerweise `Lebenslauf_Maria_Schmidt.pdf`. Ein
  Verzeichnis-Listing des Medienordners war damit eine Namensliste.

Das war kein Versäumnis an einer Stelle, sondern acht Felder, die über Jahre
einzeln dazukamen, ohne dass jemand die Frage stellte.

- Alle acht sind jetzt verschlüsselt (Migrationen `0009`/`0010`, Bestandsdaten
  werden nachgezogen; die Datenmigration ist idempotent).
- Die Talent-Pool-Adresse bekommt denselben **Blind-Index** wie
  `Applicant.email` — sonst wäre sie zwar geschützt, aber unauffindbar. Neu:
  `TalentPoolSubscription.objects.get_by_email()`; ein `filter(email=...)`
  liefert auf einer Fernet-Spalte still **null** Treffer statt eines Fehlers.
  Genau diese Falle ist beim Umstellen an acht Stellen zugeschnappt, zwei davon
  im Produkt (Portal-Beitritt und Mitgliedschafts-Anzeige).
- Neue Uploads landen **namenlos** in der Ablage (`<uuid><endung>`), der
  Anzeigename bleibt — verschlüsselt — erhalten. Der Altbestand trägt seine
  alten Namen weiter; das Umbenennen ist eine eigene Aufgabe.

**Bewusste Folge:** Auf verschlüsselten Feldern gibt es keine Volltextsuche
mehr. Im Produkt suchte nichts danach; in sechs Tests schon — die prüfen jetzt
in Python. Einer davon war ein `assertFalse` und wäre sonst **scheinbar grün**
gewesen, ohne noch irgendetwas zu belegen.

Neuer Wächter `GuardrailPersonalFieldsEncryptedTestCase`: An personenbezogenen
Modellen muss jedes Textfeld verschlüsselt sein oder mit Begründung auf einer
Liste stehen. Dazu Tests, die über rohes SQL prüfen, was **wirklich in der
Datenbank steht** — wer ein Backup verliert, darf die Sätze nicht lesen können.

### Behoben (ausstehende Gremiums-Stimmen konnten unsichtbar bleiben)

Die Freigaben-Seite holte die **200 ältesten** offenen Bewerbungen der ganzen
Organisation und prüfte **erst danach**, wer in welchem Sichtungs-Gremium
sitzt. In einem Haus mit mehr als 200 offenen Bewerbungen konnten diese 200
sämtlich aus fremden Einrichtungen stammen — dann blieb die Liste der eigenen
ausstehenden Stimmen leer.

Die Folge ist kein Schönheitsfehler: Eine ausbleibende Gremiums-Stimme
blockiert die Einladung. Der Ablauf stünde still, und niemand hätte den Grund
gesehen — weder die Person mit der offenen Stimme noch die Recruiterin, die
auf die Freigabe wartet.

- Gekappt wird jetzt das **Ergebnis**, nicht die Eingabe: Die Seite geht die
  offenen Bewerbungen durch, bis sie 50 gefunden hat, in denen die eigene
  Stimme aussteht.
- Bewusst **kein** BOLA-Scoping davor: Gremiums-Mitgliedschaft entsteht auch
  aus Vorgaben höherer Ebenen und folgt nicht dem Einrichtungs-Zugriffsbereich.
  Wer hier scopte, versteckte Pflichten statt Daten — die Mitgliedschaft selbst
  ist die Zugriffsprüfung.

Neuer Wächter `GuardrailNoCapBeforeFilterTestCase` gegen diese Form. Beide —
der Regressionstest und der Wächter — wurden gegen den alten Stand geprüft und
schlagen dort fehl; ein Test, der auch ohne den Fix grün ist, beweist nichts.

### Behoben (neun Jobs im Zeitplan — und keiner, der sie startet)

`OPERATIONS.md` schlug für neun Kommandos einen Cron-Eintrag vor. Der
ausgelieferte `docker-compose.yml` enthielt **keinen Zeitplan**: Wer der
Installationsanleitung folgt und `docker compose up -d` fährt, bekam
Datenbank, Anwendung, KI und KI-Worker — und keinen einzigen dieser Jobs.

Betroffen war unter anderem `data_retention`. Die Seite „Datenaufbewahrung"
sagte HR-Admins derweil zu, Bewerbungen würden „nach Ablauf der Frist
**automatisch** anonymisiert (DSGVO-Datenminimierung)". Ein Satz, den die
Auslieferung nicht einlöste — bei einer Pflicht aus Art. 5 Abs. 1 lit. e
DSGVO, für die die Leitung geradesteht. Dasselbe gilt für
`purge_talent_pool`: abgelaufene Einwilligungen wurden nie gelöscht.

- **Neuer Dienst `scheduler` im Compose-Stapel.** Ohne Profil, er läuft immer
  mit — ein Zeitplan, den man erst einschalten muss, wäre derselbe Fehler noch
  einmal. Bewusst kein Celery/Redis-Beat: ein Dienst im selben Image, den ein
  Träger ohne eigenes Betriebsteam lesen und reparieren kann.
- **Jeder Lauf hinterlässt einen Vermerk** (`ats/jobs.py`). Damit kann die
  Oberfläche sagen, was zuletzt lief — und Schweigen ist keine Option mehr.
- **Neue Seite *Einstellungen → Wiederkehrende Jobs***: je Job letzter Lauf,
  Ergebnis und, bei überfälligen Pflicht-Jobs, die Folge im Klartext.
- Die Seite „Datenaufbewahrung" behauptet nicht mehr „automatisch", sondern
  zeigt den letzten Lauf — oder warnt, dass noch nie anonymisiert wurde.
- Ein fehlgeschlagener Job bricht den Zeitplan nicht ab: Sonst hätte ein
  kaputter Wochenbericht die Aufbewahrungsfristen mit lahmgelegt.
- `INSTALL.md` und `OPERATIONS.md` sagen jetzt, dass der Docker-Weg das
  mitbringt; die Cron-Liste gilt für Installationen ohne Docker.

Wächter `GuardrailScheduleIsRealTestCase`: Jeder Zeitplan-Eintrag muss als
Kommando existieren, und der Compose-Stapel muss den Dienst enthalten — ohne
Profil. Damit hängt die Zusage der Oberfläche an einem Test, nicht an einem
Absatz in der Betriebsdoku.

### Behoben (verschluckte Fehler — vor allem einer, der den Login-Schutz betraf)

Acht Stellen fingen eine Ausnahme ab und taten nichts damit. Die teuerste sitzt
in der **Brute-Force-Sperre**: Der Zähler fing Cache-Fehler ab und schwieg.
Fällt der Cache aus, zählt niemand mehr Fehlversuche mit — der Login steht
ungebremst offen, ohne dass es irgendwo auffiele. Ein Schutz, der lautlos
verschwindet, ist gefährlicher als gar keiner, weil man sich auf ihn verlässt.

Dazu kam ein zweites, entgegengesetztes Verhalten am selben Zähler: Das *Lesen*
war ungeschützt. Ein Cache-Ausfall legte damit den Login komplett lahm (500),
während derselbe Ausfall die Sperre lautlos abschaltete.

- Beide Richtungen laufen jetzt gleich: **durchlassen, aber laut**. Wer bei
  kaputtem Cache jeden Anmeldeversuch abweist, sperrt das ganze Haus aus.
- **`/healthz/` prüft den Cache jetzt aktiv** (schreiben, lesen, aufräumen).
  Er trug die Login-Sperre, wurde aber als einziger Baustein nicht überwacht.
  Ein Ausfall meldet `degraded`, kein 503 — der Dienst bleibt benutzbar, nur
  ungebremst.
- Analytics-Berichte ließen bei einem Fehler ganze Abschnitte **verschwinden**.
  Jetzt steht dort „nicht berechenbar" — wer den Abschnitt nicht kennt, hielte
  den Bericht sonst für vollständig.
- KI-Frage-Vorschläge, Modell-Auswahl und die Terminformat-Liste protokollieren
  ihren Rückfall, statt ihn zu verschweigen.

Neuer Wächter `GuardrailNoSilentSwallowTestCase`. Er verlangt nicht, dass jeder
Fehler protokolliert wird — manchmal ist ein Fehlschlag der Normalfall, etwa
wenn ein Sprachmodell kein gültiges JSON liefert. Er verlangt, dass jemand
**hingesehen** hat: ein Log-Aufruf oder ein Kommentar, der die Entscheidung
begründet. Er fand prompt eine achte Stelle, die meine eigene Textsuche
übersehen hatte (`ats/models/` lag nicht im Suchpfad).

### Behoben (dreizehn Mail-Aufrufe gingen am Fehler-Vermerk vorbei)

`ats/mail_send.py` wurde gebaut, damit ein fehlgeschlagener Versand sichtbar
wird — im Zustand, in der Board-Warnung, notfalls als Meldung auf dem
Bildschirm. Der Modul-Docstring nannte selbst „31 Stellen mit
`fail_silently=True`". **Dreizehn davon riefen `send_mail` weiterhin direkt
auf** und umgingen die Schicht vollständig: Gesprächseinladungen,
Terminbestätigungen, Umbuchungen, Rückfragen an die Kontaktperson,
Freigabe- und Bedarfs-Entscheidungen, die Job-Alert-Bestätigung — und die
Unterrichtung der Schwerbehindertenvertretung.

Alle dreizehn laufen jetzt über `send_notice`. Zwei davon hatten
`send_mail as _send` importiert; ein erstes Inventar per Textsuche hat sie
übersehen, die AST-Auswertung nicht.

**Schwerer wiegt der Vermerk daneben.** Bei der SBV-Unterrichtung lief
`write_audit('SBV_NOTIFIED', …)` bedingungslos hinter dem Versand — auch wenn
die Mail still gescheitert war oder die Gruppe „SBV" gar keine Adresse
hinterlegt hatte. Im Protokoll stand damit ein Nachweis über eine Pflicht nach
§ 164/§ 178 Abs. 2 SGB IX, den niemand hätte einlösen können.

- Der Eintrag trägt jetzt `delivered`, und die Kennzahl auf der
  Inklusions-Seite zählt nur noch zugestellte Unterrichtungen.
- Drei Tests halten das fest: gescheiterter Versand, erfolgreicher Versand,
  und der Fall ohne jede hinterlegte Adresse.
- Neuer Wächter `GuardrailNoDirectMailTestCase` sperrt direkten Mail-Versand
  außerhalb von `ats/mail_*.py`. Er arbeitet über den Syntaxbaum, nicht über
  Textsuche — sonst hätte er dieselben zwei Alias-Stellen übersehen wie ich.

### Behoben (der eigene CI-Umbau hat den Testlauf lahmgelegt)

Der Deploy-Check sollte gegen eine produktionsnahe Umgebung laufen — dafür
standen `SECURE_SSL_REDIRECT` und `SECURE_HSTS_PRELOAD` in der Umgebung des
**ganzen** Jobs statt nur bei diesem einen Schritt. Damit beantwortete Django
jede Anfrage des Test-Clients mit einer 301 auf https; die Views liefen nie.
Ergebnis: rund 40 Fehler, keiner mit erkennbarem Bezug zur Ursache
(„Content-Type ist text/html, nicht application/json", „Application matching
query does not exist"). Lokal war nichts zu sehen, weil dort `DEBUG=True` gilt
und der ganze Zweig nicht greift.

- Die beiden Schalter gelten jetzt nur noch beim Deploy-Check.
- Der Test-Runner setzt `SECURE_SSL_REDIRECT` im Testlauf hart auf aus. Der
  Test-Client spricht http; eine https-Umleitung ist dort nie gewollt, und
  dass die Einstellung im Betrieb wirkt, prüft der Deploy-Check ohnehin.
- Zwei Tests halten das fest — einer auf die Einstellung, einer auf die
  Wirkung (kommt eine Antwort an?).

### Geändert (der Backlog las sich wie eine To-do-Liste, war aber ein Foto von damals)

`FEATURE_BACKLOG.md` trug eine Spalte „Django-Ist" mit 15 ❌-Zeilen — für Dinge,
die längst laufen. Die Spalte hält den Stand **bei der Analyse** fest, nicht den
heutigen; der steht in der ersten Spalte. Wer sie als offene Punkte liest, baut
etwas ein zweites Mal oder übersieht einen echten Fund.

- Spalte heißt jetzt „Ausgangslage bei der Analyse", mit einem Absatz davor, der
  den Unterschied benennt.
- Stichprobe an der Zeile, die sicherheitsrelevant klang: B1 („CV wird
  ungeschützt ausgeliefert") ist erledigt — `download_cv` prüft Auth und Rolle,
  `/media/` wird nur unter `DEBUG` von Django ausgeliefert, und in der
  Produktions-Compose liegt es als Volume ohne eigene Route. Kein Befund.
- Feste Testzahlen aus `FEATURE_BACKLOG.md` und `TESTING_AND_GUARDRAILS.md`
  entfernt. „748 Testmethoden" stand dort, während es tausend waren — eine Zahl
  von Hand zu pflegen heißt, sie veralten zu lassen.

### Behoben (weitere Listen schnitten still ab)

Nachdem dieselbe Fehlerklasse an einem Tag zweimal auftrat — `logs[:500]` im
Audit-Log, `assets[:200]` in der Mediathek — ein Durchgang durch alle
Listen-Abfragen. Bewusste Top-N-Listen („die zehn häufigsten Kanäle", „die
nächsten acht Termine") bleiben, wie sie sind. Vier Stellen waren dagegen
stille Grenzen:

- **Die Nachweise einer Bewerbung im Steckbrief** endeten bei 20 — ausgerechnet
  dort, wo der Kommentar daneben erklärt, dass diese Dateien vorher gar
  niemand zu Gesicht bekam.
- **Der eigene Schriftwechsel im Bewerberportal** endete bei 20. Es sind die
  eigenen Nachrichten der bewerbenden Person; die ältesten wegzulassen hiesse,
  ihr den Anfang ihrer Unterhaltung vorzuenthalten.
- **Jobfamilien in der Messstrecke** (40) und **Textbausteine im
  Antwort-Modal** (50) — beides Stammdaten. Wer einen Baustein anlegt und ihn
  nicht wiederfindet, sucht den Fehler bei sich.
- **Eigene Personalbedarfs-Meldungen** endeten bei 20; wer seine Meldung von
  vor einem halben Jahr nicht findet, meldet sie ein zweites Mal.

Wo ein Deckel bleibt, weil die Menge über Jahre wächst — die eigenen
**entschiedenen** Personalbedarfe —, nennt die Seite ihn jetzt samt Gesamtzahl
und verweist auf das Audit-Log. Offene Anträge stehen vollständig da.

Geprüft und in Ordnung befunden statt angenommen: Der Auskunfts-Rechenkern für
Art. 15 DSGVO (`ats/dsgvo.py`) kappt nichts.

### Behoben (Farbverläufe trugen nur an einem Ende)

Systematischer Durchgang durch alle öffentlichen Seiten im hellen
Träger-Modus — mit einem Prüfer, der für jedes sichtbare Textelement den
tatsächlich wirksamen Hintergrund berechnet, Verlaufs-Stopps eingeschlossen.
Ein Fund, dreimal dieselbe Ursache:

- **Der Absende-Knopf des Bewerbungsformulars** stand auf
  `linear-gradient(#0f766e → #0d9488)`, direkt darüber der Vermerk „dunkleres
  Teal: weiße Schrift erreicht AA-Kontrast". Abgedunkelt worden war aber nur
  der **erste** Stopp. Am hellen Ende blieben **3,74:1** bei 16 px fett — fett
  zählt erst ab 18,66 px als große Schrift, gefordert sind also 4,5:1. Rund die
  halbe Fläche des wichtigsten Knopfes der Bewerberstrecke fiel durch, unter
  einem Kommentar, der das Gegenteil behauptete. Jetzt 5,47:1 bis 4,82:1.
- **Beim Überfahren wurde es schlechter statt besser** (bis 2,49:1) — der Knopf
  hellte auf. Er wird jetzt dunkler; Rückmeldung geben ohnehin Anheben und
  Schatten.
- **Ausgerechnet der Knopf für die Barrierefreiheits-Hilfen** lag bei 2,49:1 an
  seinem hellen Ende. Für das Symbol darin fordert WCAG 1.4.11 mindestens 3:1.

Neuer Wächter `GuardrailGradientContrastTestCase`: Steht in einer CSS-Regel ein
Verlauf **und** eine Schriftfarbe, muss jeder Stopp die Schrift tragen. Dazu
eine Gegenprobe mit den historischen Werten — ein Wächter, der immer grün ist,
beweist nichts.

Alle übrigen öffentlichen Seiten (Start, Stellenliste, Stellendetail,
Bewerbungsformular, Job-Alert, Kandidatenportal, Barrierefreiheitserklärung,
KI-Transparenz) sind im hellen Modus ohne Befund.

### Geändert (CI: abgekündigte Actions, ein Check ohne Wirkung, ein halber Wächter-Vorlauf)

Ausgelöst durch einen Tag, an dem CI mehrfach rot war, ohne dass am Code etwas
fehlte — GitHub teilte den Jobs keinen Runner zu. Beim Nachsehen fanden sich
drei Dinge, die schon länger schieflagen:

- **`actions/checkout@v4` und `actions/setup-python@v5` liefen auf
  abgekündigtem Node 20** (aktuell ist v7). Alle Workflows sind nachgezogen,
  auch die Docker-Actions im Release-Lauf.
- **Der Schritt „Django System-Check (Deploy-Modus)" konnte nicht
  fehlschlagen.** Er endete auf `|| python manage.py check` — jede
  Sicherheitswarnung fiel auf den harmlosen Normal-Check zurück. Jetzt läuft
  er streng, und die CI-Umgebung setzt das, was `INSTALL.md` für Produktion
  verlangt. Damit ist die Prüfung eine Aussage statt einer Geste.
- **Der „Sicherheits-Wächter isoliert"-Job prüfte vier handverlesene Klassen**,
  während das Projekt über zwanzig Wächter hat. Er versprach „ein klares
  Ja/Nein zu den abgesicherten FehlerKLASSEN" und deckte keine Viertel davon
  ab. Jetzt laufen alle 50 Wächter-Tests, in knapp zehn Sekunden.

Dazu zwei Kleinigkeiten mit Wirkung: Der Ruff-Job war als einziger ohne
pip-Cache, und alle Jobs haben jetzt ein Zeitlimit — ein Job, dem GitHub
keinen Runner zuteilt, hing sonst bis zum Sechs-Stunden-Limit.

Neu in den Einstellungen: `SECURE_SSL_REDIRECT` und `SECURE_HSTS_PRELOAD`,
beide aus Vorsicht **aus**. Django darf nur dann selbst auf HTTPS umleiten,
wenn ein vorgelagerter Proxy die TLS-Terminierung meldet — sonst
Endlosschleife; und HSTS-Preload ist eine Einbahnstraße, die dem Träger
gehört, nicht der Voreinstellung. `INSTALL.md` erklärt beide.

### Behoben (helle Träger-Palette ließ die Eingabefelder aus)

Aufgefallen an einem grauen Kasten in der Medien-Verwaltung, dahinter lag
Größeres. `branding_css.html` stellt im LIGHT-Modus Karten, Titel, Tabs, Kopf-
und Fußbereich um — die **Formularfelder standen nicht auf der Liste**. Sie
behielten die dunklen Werte aus `base.html` (`rgba(11,13,25,0.5)` mit weißer
Schrift). Über weißem Grund ergibt das einen grauen Kasten mit weißer Schrift:
rund **3,6:1** für den Text, etwa **2,3:1** für den Platzhalter, gefordert sind
4,5:1. Betroffen war das Bewerbungsformular — der eine Bildschirm, an dem
Bewerbende ihre Daten eintippen, bei jedem Träger mit heller Corporate
Identity.

- Felder, Textbereiche, Auswahllisten, Platzhalter und die Lebenslauf-Dropzone
  gehören jetzt zu den hellen Regeln. Gemessen: Text **14,7:1**, Platzhalter
  **7,6:1**.
- **Native Datei-Knöpfe** waren projektweit ungestylt — ein weißer Systemknopf
  mit schwarzer Schrift mitten im dunklen Panel, auch im Bewerbungsformular.
  Sie folgen jetzt dem Feld, in dem sie sitzen: Farben aus `currentColor`
  statt fester Tokens, damit sie auf heller wie dunkler Palette sitzen. Der
  Kasten bleibt Sache der bestehenden Klassen.
- Wächter `GuardrailDarkOnlyControlsTestCase`: Jede Regel in `base.html`, die
  Hintergrund **und** Schriftfarbe hart auf dunkel/weiß setzt, braucht ein
  helles Gegenstück — sonst ist sie auf einer gebrandeten Seite ein
  Kontrastloch. Genau so ist das Bewerbungsformular durchgerutscht.

Zwei bestehende Wächter haben dabei eigene Fehler von mir gefangen: Ein
CSS-Kommentar nannte einen Menüpunkt, den ein Recruiter nicht sehen darf
(Kommentare stehen im ausgelieferten HTML), und ein mehrzeiliger
`{# … #}`-Kommentar war gesperrt, weil er als Text durchschlägt.

### Behoben (Mediathek endete bei den jüngsten 200 Dateien)

Die Medien-Verwaltung lud `MediaAsset.objects.order_by('-createdAt')[:200]` und
sagte darüber nichts. Wer ein Bild aus dem Vorjahr in eine Inhaltsseite einbinden
wollte, fand es nicht — und hatte keinen Anlass zu vermuten, dass es trotzdem
noch da ist. Die naheliegende Reaktion ist, dieselbe Datei erneut hochzuladen:
zweites Mal auf der Platte, neuer Name, neuer Alt-Text, und die 200er-Grenze
rückt für alle anderen ein Stück näher. Dieselbe Fehlerklasse wie im Audit-Log
(`logs[:500]`), nur mit einem Bestand, in dem selten gelöscht wird.

- **Blätterung statt Kappung**: 50 Zeilen je Seite, mit Bereich und Gesamtzahl
  („51–100 von 312"). Auch die älteste Datei ist erreichbar.
- **Suche über Anzeigename und Dateinamen.** Blättern allein genügt nicht: bei
  300 Dateien liegt die gesuchte auf Seite 4, und dorthin blättert niemand.
  Beide Felder, weil sie auseinanderlaufen, sobald jemand den Anzeigenamen
  pflegt — die Datei heißt danach weiter `IMG_2831.jpg`.
- Eine Suche ohne Treffer nennt den Bestand („im Bestand liegen 312 Dateien").
  Ohne diesen Zusatz sehen „nichts gefunden" und „hier ist nichts" gleich aus.
- Nach dem Löschen bleiben Seite und Suche stehen. Bisher landete man nach jedem
  Aufräumen wieder ganz oben — bei einer Liste ohne Seiten fiel das nicht auf.
  Die Zieladresse wird aus `reverse` und zwei bekannten Parametern gebaut, nie
  aus einer mitgeschickten URL.
- **Sortierung mit eindeutiger Zweitstelle** (`-createdAt`, `-id`). Bei gleichem
  Zeitstempel garantiert LIMIT/OFFSET keine Reihenfolge: dieselbe Datei stünde
  auf zwei Seiten, eine andere auf keiner. Gleichstände sind hier kein Randfall,
  sondern der Normalfall — die Uhr tickt grob genug für Massen-Uploads. Genau
  die stille Lücke, gegen die dieses Paket antritt, nur schwerer zu bemerken.
- Tests in `ats/tests/test_mediathek.py` nach dem Muster des Audit-Logs: jeder
  Eintrag erreichbar, absurde Seitenzahl ohne Absturz, Suche über beide Felder.
  SQLite gibt Gleichstände stabil zurück, PostgreSQL nicht — der Test prüft
  deshalb die Sortierung selbst und nicht nur einen glücklichen Durchlauf.

### Geändert (Testlauf: von ~23 Minuten auf wenige)

Gemessen statt vermutet: 970 Tests brauchten 1.374 Sekunden — im Schnitt
1,4 Sekunden je Test. Genau so lange dauert auf dieser Maschine **ein**
Passwort-Hash. Django hängt an jedes `create_user()` den Produktions-Hasher
(PBKDF2, 1,2 Mio. Iterationen), und die Testhilfe `make_user()` steht an über
300 Stellen, die meisten davon in `setUp` — also einmal pro Testmethode. Die
langsamsten Fälle waren folgerichtig die Gremien-Tests mit vier bis sechs
Beteiligten: rund sieben Sekunden, fast alles davon Hashen. Dieselbe Klasse
läuft jetzt in 0,36 Sekunden.

- Neuer `TEST_RUNNER` (`ats/test_runner.py`) setzt einen schnellen Hasher —
  **nur** während eines Testlaufs. Die naheliegende Abkürzung
  `if 'test' in sys.argv` in den Einstellungen hätte die Passwortsicherheit der
  Produktion an eine Zeichenkette in der Kommandozeile gehängt.
- Wächter `GuardrailNoWeakHasherInSettingsTestCase` verhindert genau diese
  Abkürzung. Dazu Tests, dass Anmeldung und `check_password` unverändert
  funktionieren — ein schnellerer Hasher darf nichts am Verhalten ändern.
- Nachgetragen: Der Wächter aus dem Vorlagen-Paket
  (`GuardrailNoTemplateNameGuessingTestCase`) fehlte in der Wächter-Tabelle in
  `TESTING_AND_GUARDRAILS.md`.

Eine Suite, die eine halbe Stunde braucht, wird vor dem Commit übersprungen —
und dann schützt sie niemanden mehr. Das ist der eigentliche Grund für dieses
Paket, nicht die Wartezeit.

### Behoben (Audit-Log endete bei den jüngsten 500 Einträgen)

Das Protokoll ist der Nachweis gegenüber Betriebsrat, Datenschutzbeauftragten
und bei Auskunftsersuchen nach Art. 15 DSGVO. Die Ansicht schnitt bei
`logs[:500]` ab und schrieb die eigene Grenze als Merkmal auf die Seite
(„max. 500 Einträge"). Zu einem Vorgang von vor drei Monaten war der Eintrag
damit schlicht nicht auffindbar — auf einer Installation im Betrieb sind 500
Zeilen wenige Tage.

- **Blätterung statt Kappung**: 100 Zeilen je Seite, die Seite nennt Bereich
  und Gesamtzahl („101–200 von 3.412"). Auch der älteste Eintrag ist erreichbar.
- **Filter, die den Zweck treffen**: Zeitraum, Aktion, Person und Bewerbung
  (die Tabelle kürzt die ID — der Filter nimmt deshalb auch den Anfang).
- **Eine Auswahl-Logik für Ansicht und Export.** Vorher hatten beide ihre
  eigene: Die Seite kannte nur `action`, der Export zusätzlich `von`/`bis`. Der
  Knopf versprach „aktuelle Auswahl als CSV" und lieferte etwas anderes als der
  Bildschirm zeigte. Bei einem Nachweis ist das keine Kleinigkeit.
- **Integrität der Hash-Kette steht jetzt auf der Seite**, nicht nur in der
  Kopfzeile der CSV-Datei. Auf Anforderung, nicht bei jedem Aufruf: die Prüfung
  liest und hasht jeden Eintrag, und ein Dashboard, das auf so etwas wartet,
  hatten wir schon einmal.
- **§ 87 Abs. 1 Nr. 6 BetrVG**: Die Suche nach einer einzelnen Person wird
  ihrerseits protokolliert, und die Seite sagt das dazu. Ohne dieses
  Gegengewicht wäre der Filter ein Werkzeug zur Verhaltenskontrolle, mit dem
  jemand unbemerkt nachsehen könnte, was eine Kollegin den ganzen Tag getan hat.
  Entprellt auf 15 Minuten — zwanzig Einträge fürs Blättern wären vollständig,
  aber unlesbar.
- Ein verdrehter Zeitraum wird benannt statt als „keine Treffer" ausgegeben;
  ein ungültiges Datum im Export liefert 400 statt stillschweigend alles.
- Index auf `AuditLog.userId` — ohne ihn wäre der Personen-Filter ein Full Scan
  über die größte Tabelle im System.
- Das Filter-Select löste bisher `onchange` ein Auto-Submit aus (WCAG 3.2.2).
  Jetzt: expliziter Knopf „Auswahl anwenden". Die Zeile in
  `ACCESSIBILITY_AUDIT.md` behauptete „Keine Auto-Submits" und nannte im selben
  Satz diese Ausnahme — sie ist korrigiert.

### Behoben (E-Mail-Vorlagen wurden über ihren Namen gesucht)

Die Automatik fand ihre Vorlage bisher per Namenssuche:
`EmailTemplate.objects.filter(name__icontains='absage')`. Wer die Vorlage
„Ablehnung" nannte oder „Absage" in „Rückmeldung nach Sichtung" umbenannte,
bekam **keine** Fehlermeldung — der Versand fiel still auf einen fest
einprogrammierten Text zurück. Den hatte niemand im Haus je gesehen oder
freigegeben, Bewerbende lasen ihn trotzdem. Dasselbe auf jeder Installation,
die per Datenimport statt per Seed startet: dort existiert gar keine Vorlage,
und auch das fiel nicht auf, weil der Ersatztext ja griff.

- Jede Vorlage trägt jetzt einen **Zweck** (Eingangsbestätigung, Einladung zum
  Gespräch, Absage, oder freier Baustein). Der Name ist wieder das, was er sein
  sollte: Beschriftung, keine Steuerung.
- Fehlt für einen Zweck eine Vorlage, sagen Vorlagenseite und Einstellungs-Hub
  das offen — mitsamt der Folge („Bewerbende lesen Wortlaut, den niemand bei
  Ihnen freigegeben hat"), statt den Ersatztext als Normalfall auszugeben.
- Je Zweck gilt genau eine Vorlage. Beim Speichern wird der Zweck den anderen
  entzogen, sonst hinge die Auswahl wieder an einer Sortierung.
- Migration `0007` ordnet bestehende Vorlagen einmalig zu. Geraten wird nur
  dort, mit knappen eindeutigen Stichworten und nur für die jeweils erste
  Treffer-Vorlage — ein Fehlgriff wäre schlimmer als eine offene Lücke, weil er
  unbemerkt an Bewerbende ginge. Nicht Zuordenbares bleibt leer und wird
  nachgefragt.
- Neuer Wächter `GuardrailNoTemplateNameGuessingTestCase`: `name__icontains`
  auf `EmailTemplate` ist projektweit gesperrt, damit die Abkürzung nicht
  zurückkehrt.

### Behoben (namenlose Icon-Knöpfe, vorgelesene Deko-Symbole)

Nachträgliche Barrierefreiheits-Abnahme der Bildschirme, die zuletzt entstanden
sind — die Definition of Done im `TESTING_AND_GUARDRAILS.md` war bei fünf Seiten
am Stück übersprungen worden.

- **Zehn Icon-Knöpfe im ganzen Projekt hatten keinen Namen** (Löschen,
  Archivieren, Bearbeiten in Kategorien, Kontakten, Vertretungen, Vorlagen,
  Standorten, Entgeltbändern, Screening-Fragen, Mediathek, Textbausteinen). Ein
  Screenreader las dort nur „Schaltfläche". Ein `title` genügt dafür nicht. Alle
  tragen jetzt einen Namen samt betroffenem Eintrag — sonst hört man in der
  Elementliste zehnmal „Löschen" ohne Bezug.
- 30 Deko-Symbole wurden mitgelesen und sind jetzt `aria-hidden`.
- Der Wechsel in den Bearbeiten-Modus der Seitenverwaltung war für
  Screenreader unsichtbar; die Überschrift sagt ihn jetzt an (`role="status"`).
- Neuer Wächter `GuardrailIconButtonNameTestCase`: Punkt 3 der Definition of Done
  stand seit Langem da, und zehn Knöpfe waren trotzdem namenlos. Eine Regel, die
  nur auf Disziplin baut, hält nicht.

Geprüft und in Ordnung befunden statt angenommen: Zielgrößen (27 px Desktop,
44 px Phone) und die Rückmeldungen nach dem Speichern (zentrale Meldungsleiste
mit `role="status"`).

### Behoben (nächtliche Versandfehler blieben unsichtbar)

Nachtrag zum Paket davor — die dort gebaute Warnung deckte den wahrscheinlichsten
Ausfall **nicht** ab. Djangos SMTP-Backend gibt bei `fail_silently=True` und
nicht erreichbarem Server schlicht `0` zurück, **ohne Ausnahme**. Der
Zustands-Vermerk lief nur über „wurde etwas verschickt?", also wurde in genau
diesem Fall gar nichts notiert: Der nächtliche Job schwieg, die Board-Warnung
erschien nie.

- Ein Versand, der nichts zugestellt hat, gilt jetzt als Fehlschlag — auch ohne
  Ausnahme.
- Die sechs Hintergrund-Wege (Entscheidungs- und Termin-Erinnerungen,
  Feedback-Anfragen, Job-Alerts, Talent-Pool, Freigabe-Fälligkeiten) laufen über
  die Versand-Schicht und liefern Kontext mit: „Termin-Erinnerung nicht
  zugestellt" statt einer nackten Zahl.
- Neuer Wächter gegen direkte `send_mail`-Aufrufe an der Schicht vorbei.
- `send_notice` folgt jetzt der Argument-Reihenfolge von `send_mail`
  (Betreff, Text, Absender, Empfänger). Beim Umstellen war genau hier ein Fehler
  entstanden — eine Signatur, die von der gewohnten abweicht, lädt dazu ein.

### Vereinfacht (ein Seiten-Editor statt zwei halben)

Es gab **zwei** Editoren für Inhaltsseiten, und beide waren unvollständig — und
zwar gegenläufig. „Seiten & Navigation" konnte löschen und führte zum
Block-Baukasten, kannte aber nur vier Felder. Der „CMS Seiten-Editor" hatte
Navigations-Beschriftung, Position, SEO-Text und Sichtbarkeit, dafür weder
Löschen noch Baukasten. Wer eine Seite anlegte **und** veröffentlichte, brauchte
beide Bildschirme.

Geblieben ist **„Seiten & Navigation"** mit allen acht Feldern; gespeichert wird
über den vorhandenen, auditierten Endpunkt, dessen Feldsatz ohnehin vollständig
war. Die zweite, ärmere Speicher-Logik ist ersatzlos entfallen. Der echte
Baukasten sitzt weiterhin pro Seite in der Liste — die richtige Stelle: erst
existiert die Seite, dann füllt man sie.

Nebenbei: Der Slug ist jetzt Pflichtfeld statt still aus dem Titel erzeugt. Die
Adresse einer öffentlichen Seite sollte man sehen, bevor man sie festlegt.

### Behoben (fehlgeschlagener Versand ging als Erfolg durch)

`fail_silently=True` an 31 Stellen war einmal richtig gedacht — ein Absturz im
nächtlichen Job wäre schlimmer als eine verlorene Mail. Nur meldete das Kanban
danach „Absage verschickt", während der Mailserver sie abgelehnt hatte.

- **Wartet ein Mensch** (Absagen, Einladen, Senden): Der Fehler steht sofort auf
  dem Bildschirm, im Klartext des Mailservers.
- **Wartet niemand** (Cron, Job-Alerts): kein Absturz, aber der Fehlschlag landet
  im Zustand und erscheint als Warnung auf dem Board — nur für HR-Admins, denn
  wer den Mailserver nicht einrichten kann, dem hilft die Meldung nicht.
- Zwei Unehrlichkeiten in den **Daten** mit behoben: Der Automatik-Versand schrieb
  im Audit unbesehen `"status": "SENT"`; die Serien-Nachricht meldete „an N
  Personen gesendet", wobei N nur die Schleifendurchläufe zählte.
- Ein Mailserver wird nur verlangt, wenn wirklich per SMTP verschickt wird. Wer
  das Backend bewusst umstellt (Konsole für einen Trockenlauf, Datei für eine
  Abnahme), hat einen gültigen Weg — ihn mit „kein Mailserver hinterlegt" zu
  blockieren wäre eine Bevormundung mit falscher Begründung.
- Platzhalter in `.env.example` und Test-Zugangsdaten sind jetzt unmissverständlich
  künstlich (`smtp.example.invalid`, `NICHT-ECHT-nur-Test`): Ein Geheimnis-Scanner,
  der grundlos anschlägt, wird irgendwann weggeklickt — und dann geht der echte
  Fund mit unter.

### Behoben (E-Mail-Versand war überhaupt nicht konfigurierbar)

Es gab **keine einzige Mail-Einstellung**. Django fiel auf seinen Standard
`localhost:25` zurück, und weil an 31 Stellen `fail_silently=True` steht (ein
Absturz im Hintergrund-Job wäre schlimmer), verschwanden Absagen, Einladungen und
die Zugangslinks zum Bewerberportal spurlos. Die Oberfläche meldete „verschickt",
zugestellt wurde nichts.

- Neue Seite **Einstellungen → E-Mail-Versand**: Mailserver des Trägers,
  Verbindungsart, Absenderadresse. Das Passwort liegt verschlüsselt (dieselbe
  Fernet-Schicht wie die Bewerber-PII) und wird nie zurück ins Formular
  geschrieben; ein leeres Feld heißt „unverändert", nicht „löschen".
- **Umgebungsvariablen haben Vorrang** und sind im Formular gesperrt, statt
  stillschweigend wirkungslos zu sein.
- **Testversand** zeigt die Klartext-Meldung des Mailservers — nicht „irgendwas
  ging schief". Der letzte Versand samt Ergebnis steht im Zustand.
- Ohne hinterlegten Server wird das protokolliert und angezeigt, statt in einen
  toten Standard zu laufen.

### Ergänzt (Einstellungs-Zentrale)

Die Konfigurations-Seiten sind über Jahre einzeln entstanden und lagen verstreut
in der Seitenleiste, zwischen Tagesgeschäft. Wer SecurATS neu aufsetzt, musste
raten, was einzurichten ist.

Neue Seite **Einstellungen** mit 25 Bereichen in fünf Gruppen — je Eintrag der
**Zustand**, nicht nur ein Link, und offene Punkte zuoberst. Ein Wächter
(`GuardrailAdminPageInHubTestCase`) verlangt, dass jede Admin-Seite dort verlinkt
ist; Aktionen und Exporte stehen mit Begründung auf einer Ausnahmeliste, die
selbst auf tote Einträge geprüft wird.

**Zwei Rechte-Funde dabei:**

- **Kanäle & Kosten** stand jeder internen Rolle offen (`any_staff_required`),
  obwohl nur im Admin-Block verlinkt und die Kosten-Auswertung der Leitung
  vorbehalten ist. Sichtbarkeit und Schutz passen jetzt zusammen.
- Umgekehrt war die **Vertretungs-Seite** — ausdrücklich Selbstbedienung für jede
  Rolle, ein Vorstand legt seine Urlaubsvertretung selbst an — nur im Admin-Block
  verlinkt. Ohne Admin-Rechte kam niemand an die eigene Vertretung. Sie steht
  jetzt unter „Termine & Menschen"; ein Test hält fest, dass sie **nicht** auf
  HR-Admin verengt werden darf.

### Ergänzt (Umkreissuche funktioniert ohne Handarbeit)

Standort-Koordinaten ließen sich zwar eintragen, aber niemand kennt sie auswendig.
Blieben sie leer, fiel der Job-Alert still auf „exakt derselbe Standort" zurück —
50 km eingestellt, ein Ort getroffen.

Neu: eine **mitgelieferte Postleitzahlen-Tabelle** (10.813 Einträge, 238 KB;
GeoNames, CC BY 4.0 — Nachweis in `README.md`). Beim Anlegen eines Standorts werden
die Koordinaten daraus ergänzt; von Hand eingetragene Werte haben Vorrang. Für
Bestandsstandorte gibt es einen Knopf zum Nachtragen, der vorhandene Koordinaten
nie überschreibt und nur erscheint, wenn es etwas zu tun gibt.

**Bewusst kein Geocoding-Dienst:** Der wäre bequemer und hausnummerngenau, doch
jede Standortanlage schickte dann eine Trägeradresse an einen fremden Anbieter.
Die Tabelle funktioniert offline, auch in einer Installation ohne Internetzugang.
Genauigkeit auf Ortsebene — für „im Umkreis von X km" reichlich, für
Wegbeschreibungen ungeeignet.

### Ergänzt (Datenschutzhinweis im Produkt pflegbar)

Art. 7 Abs. 1 DSGVO verlangt den Nachweis, **worin** eingewilligt wurde. Fassungen
anlegen ging bisher nur über die Django-Administration — eine technische Oberfläche,
die in der Personalabteilung niemand öffnet. Die Governance-Seite benannte die Lücke
zwar, schickte zur Behebung aber aus dem Produkt heraus.

Neue Seite „Datenschutzhinweis" (HR-Admin, in der Seitenleiste neben der
Datenaufbewahrung, verlinkt aus dem Governance-Hinweis). Zentrale Regel:
**anfügen statt ändern.** Eine bestehende Fassung lässt sich nicht überschreiben —
sonst zeigen die Bewerbungen, die daran hängen, auf einen Text, den es so nie gab.
Die Tabelle zeigt je Fassung, wie viele Personen genau sie gesehen haben; genau
eine Fassung ist gültig, ältere lassen sich wieder aktivieren (auditiert).

### Ergänzt (Freigaben: Rückblick und Überblick)

Die Freigabe-Seite zeigte ausschließlich „wartet auf mich". Zwei Fragen, die im
Alltag gestellt werden, konnte sie nicht beantworten — obwohl die Daten die ganze
Zeit vorlagen:

- **„Habe ich das schon freigegeben?"** Ein entschiedener Schritt verschwand
  spurlos aus der Liste. Jetzt ein eingeklappter Rückblick auf die eigenen
  Entscheidungen mit Datum und Begründung. § 99 wird dabei sprachlich
  auseinandergehalten: „Zustimmung verweigert" ist nicht „abgelehnt".
- **„Was hängt gerade, und bei wem?"** Neue Übersicht der laufenden Ketten mit
  Fortschritt, fälliger Stufe und Alter. Die Engpass-Kennzahl in der Analytik
  beantwortet „welche Stufe bremst im Schnitt" — nicht, welche Stelle jetzt
  steht. Nennt Rollen statt Namen (Prozess-Transparenz, keine Personendaten)
  und respektiert den Zugriffsbereich.

### Behoben (Tempo & Wahrheit der KI-Anzeige)

- **Das Dashboard blockierte bis zu vier Sekunden pro Aufruf.** Das KI-Abzeichen
  probierte bei JEDEM Seitenaufruf zwei Verbindungen mit je zwei Sekunden
  Zeitlimit. Bei einer Installation ohne KI-Profil — dem Normalfall beim Kunden —
  war damit die meistgeöffnete Seite des Produkts dauerhaft träge, ohne
  erkennbaren Grund. Die Antwort gilt jetzt 20 Sekunden nach: kurz genug, dass
  eine nachträglich gestartete KI von selbst gefunden wird.
- **Das Abzeichen log bei abweichendem Port.** Es prüfte fest 11434, während die
  echten KI-Aufrufe `OLLAMA_HOST`/`OLLAMA_PORT` folgen — wer den Port umstellte,
  sah OFFLINE über einer laufenden KI. Anzeige und Funktion kommen jetzt aus
  derselben Quelle.
- Die Adress-Suche (zwei TCP-Verbindungen plus Namensauflösung) lief vor jedem
  einzelnen KI-Aufruf neu, auch mitten in einer Schleife über dutzende
  Bewerbungen. Jetzt einmal je Minute. `ai_doctor` setzt beide Puffer zurück,
  damit eine Diagnose den Jetzt-Zustand zeigt und nicht eine alte Erkenntnis.
- Nebenwirkung: Die Testsuite läuft von 1103 auf 830 Sekunden.

### Behoben (Durchgang „unerreichbare Funktionen")

Ein systematischer Durchgang durch alle 122 Routen, Einstellungen und Modellfelder
mit einer einzigen Frage: *Kommt jemand da hin, und bewirkt es etwas?* Das Muster
kam so oft vor, dass es jetzt einen Wächter hat (`GuardrailNoOrphanRouteTestCase`):
eine View ist gebaut, geschützt und getestet – aber kein Link zeigt darauf, also
existiert sie für niemanden.

- **Auskunft nach Art. 15/20 DSGVO gab es nur auf der Kommandozeile.** Sie war
  implementiert, getestet und in der Compliance-Matrix als erledigt geführt –
  erreichbar aber nur mit Server-Zugang, während Art. 12 Abs. 3 eine Frist von
  einem Monat setzt. Jetzt Selbstbedienung im Bewerberportal und ein Knopf für
  HR-Admins. Der Export war zudem unvollständig (Anschrift, Absagegrund,
  Nachrichten, Talent-Pool-Einwilligung samt consentId fehlten).
- **Einwilligungs-Nachweis (Art. 7 Abs. 1) wurde nie geschrieben.** Das Feld für
  die Fassung des Datenschutzhinweises existierte seit der ersten Migration und
  blieb bei jeder Bewerbung leer.
- **Vier fertige Seiten ohne Verlinkung:** Talent-Pool-Abgleich je Stelle,
  Audit-CSV-Export, Löschansicht für Best-Performer-Profile (ohne sie war Art. 17
  nur per Hand-Request bedienbar) und der Job-Alert. Hochgeladene Zeugnisse wurden
  gespeichert und von keiner Seite angezeigt.
- **Pflichtfeld ohne Wirkung:** Die Mediathek verlangt beim Hochladen einen
  Alt-Text und verwarf ihn beim Rendern; ohne Bildunterschrift stand `alt=""` im
  Markup – für Screenreader die Ansage „reine Deko" (WCAG 1.1.1).
- **Umkreissuche degradierte still:** `Location.lat/lng` brauchte der Job-Alert,
  pflegen konnte die Werte niemand. Wer 50 km einstellte, bekam nur den exakt
  gleichen Ort.
- **Freigaben ohne Urheber:** Das Feld zeigte auf ein totes Alt-Modell, mit dem
  sich niemand anmeldet. Jede Zustimmung hatte einen Zeitpunkt, aber nie einen
  Namen – und tauchte in gar keiner Ansicht auf.
- **Konfiguration, die nichts tat oder falsch beriet:** `PRIMARY_COLOR`/
  `FOOTER_TEXT` (nie gelesen), `SOURCE_COST_*` (unsichtbarer zweiter Pflegeort),
  `OLLAMA_PORT` (empfohlen, aber nicht ausgewertet), `DATABASE_URL` (fiel ohne
  `file:`-Präfix kommentarlos auf die lokale Datei zurück), ein dritter
  Freigabeketten-Pfad ohne Formular, die Preisseite verlinkt auf Instanzen, die
  sie mit 404 beantworten.

### Behoben (Prüfung abgeschlossen)
- **OData-Sync-Tab war ein weiterer Blender.** Eine "Konsole" gab beim Laden
  "Port 443 verschlüsselt mit zertifizierten Partner-Keys" aus und auf Knopfdruck
  ein erfundenes mTLS/OAuth2-Protokoll samt "Revisionssicher übertragen: X Profile".
  Der Aufruf ging an denselben Endpunkt wie der (ehrliche) Feld-Mapper, der KEINE
  Daten überträgt – die Konsole log also. Ersetzt durch eine ehrliche Erklärung des
  echten Wegs (Zuordnung speichern -> `hris_export`); tote JS-Funktionen entfernt.
- Abschluss-Scan der Wizard-Knöpfe: `testGemmaConnection` (echter Ollama-Test) und
  das Status-Polling asynchroner KI-Aufgaben sind echt – keine weiteren Blender.

### Behoben (schwerwiegend – Schein-Funktion durch echte ersetzt)
- **CV-Ingestion / "Vektordatenbank" war reine Animation.** Im Job-Wizard zaehlte ein
  Fortschrittsbalken 0->100 % mit Texten wie "Generiere Vektor-Embeddings" und meldete
  dann "erfolgreich in die Vektordatenbank eingespeist. Die lokale Gemma-KI wurde auf
  Ihre Unternehmenskultur ausgerichtet!" – **es gab kein Backend**: keine Embeddings,
  keine Speicherung, die hochgeladenen Lebenslaeufe wurden weggeworfen. Ein Kunde haette
  in der Demo eine KI-Kernfunktion fuer echt gehalten.
  **Jetzt echt gebaut:** Der Upload erzeugt ueber die lokale KI (Ollama) **echte
  Embeddings** und speichert sie als `BestPerformerProfile` (Migration 0043). Ist Ollama
  nicht erreichbar, wird **NICHTS** gespeichert und der Nutzer klar informiert (HTTP 503,
  ehrliche Meldung) – kein Schein-Erfolg mehr. Datenschutz: Der **Roh-Lebenslauf wird
  nicht gespeichert**, nur der nicht rueckrechenbare Vektor; jede Einspeisung wird
  auditiert. Regressions-Wache im Test verhindert die Rueckkehr der Animation.
- **`pypdf` fehlte in `requirements.txt`**, obwohl der Code es nutzt – in einer
  Minimal-/CI-Installation waere der Import abgestuerzt. Ergaenzt und der Import
  zusaetzlich gegen Fehlen abgesichert.

### Verbessert (Klickstrecke)
- **Lebenslauf direkt im Fenster lesen** statt herunterladen zu muessen. Die
  "Lebenslauf-Vorschau" war bisher ein Platzhalter (im Code als "Previewer Frame
  Mock" bezeichnet): ein PDF-Symbol mit Download-Knopf. Fuer die **haeufigste
  Handlung im Recruiting** musste der Recruiter die Anwendung verlassen, die Datei
  im PDF-Programm oeffnen und zurueckwechseln. Nebenwirkung: Jeder gelesene
  Lebenslauf hinterliess eine **PII-Kopie auf dem Laptop** - in einem Produkt, das
  mit Datensouveraenitaet wirbt, ein Eigentor. Jetzt: echte Inline-Ansicht
  (PDF/Bild) ohne Kopie; Download bleibt fuer die Faelle, die ihn brauchen.
  Das Audit **unterscheidet jetzt Ansicht und Download**, damit der
  Datenschutzbeauftragte sieht, wer eine Kopie gezogen hat.
- **Entscheiden, wo gelesen wird.** Im Bewerbungs-Fenster konnte man zwar einladen,
  aber weder "in Pruefung nehmen" noch "absagen" - die zwei haeufigsten
  Entscheidungen. Man musste das Fenster schliessen, die Karte im Board suchen und
  ziehen. Jetzt: Entscheidungsleiste direkt neben dem Lebenslauf; der aktuelle
  Status ist ausgegraut. Nutzt denselben Endpunkt und dieselben Schutzplanken wie
  Drag&Drop - das Bedenken-Gate vor einer Einstellung bleibt aktiv (getestet).
- Sicherheitsnachweis: Die Inline-Vorschau oeffnet **kein** Schlupfloch -
  Zugriffskontrolle, BOLA-Scope und Audit gelten unveraendert (getestet);
  Word-Dokumente werden ehrlich als Download geliefert statt als kaputte Vorschau.

### Behoben (Anforderungsdokument)
- **23 doppelt vergebene Use-Case-IDs bereinigt.** UC-AR-09, UC-AY-11, UC-SB-42 u. a.
  bezeichneten jeweils ZWEI verschiedene Anforderungen. Fuer ein Dokument, das im
  Vergabeprozess als Nachweis dient ("UC-AR-09 ist erfuellt"), ist das unbrauchbar.
  Alle 401 IDs sind jetzt eindeutig; Inhalte unveraendert.

### Hinzugefuegt (Testluecken aus dem Use-Case-Abgleich)
- **UC-VT-06 – Vertretung im Sichtungs-Gremium (war KOMPLETT ungetestet).** An dieser
  Logik haengen Einstellungsentscheidungen. Jetzt abgesichert: Die Stimme der
  Urlaubsvertretung zaehlt fuer den Sitz des Abwesenden (Abwesenheit blockiert das
  Verfahren nicht); stimmen Mitglied UND Vertretung, zaehlt der Sitz **nicht doppelt**
  (die eigene Stimme gewinnt) - sonst entstuenden Mehrheiten, die es nie gab;
  abgelaufene oder scope-fremde Vertretungen werden abgewiesen; das Audit haelt fest,
  FUER WESSEN Sitz gestimmt wurde (Betriebsrat/Nachvollziehbarkeit).
- **UC-SB-18 / UC-UM-13 – Textbausteine** (Anlegen, Loeschen, nur HR-Admin).

### Geaendert (Grundsatzentscheidung)
- **PostgreSQL ist die einzige unterstuetzte Produktions-Datenbank.** Ein Start mit
  SQLite bei `DEBUG=False` wird **hart abgelehnt** (verstaendliche Meldung statt
  stiller Fehlfunktion). Grund: Die Kluft "lokal SQLite / produktiv PostgreSQL" hat
  echte Fehler versteckt, die erst die CI aufdeckte - u. a. ein **Verbindungsleck**
  durch Hintergrund-Threads (`too many clients`), das SQLite klaglos verzeiht.
  Zudem sperrt SQLite bei parallelen Schreibzugriffen die **ganze Datei**
  (`database is locked`) - im Mehrbenutzerbetrieb eines Traegers untragbar.
- **Lokal auf PostgreSQL entwickeln:** neue `docker-compose.dev.yml` startet die
  Datenbank mit einem Befehl; Entwicklung, Tests und Produktion nutzen damit
  dieselbe Datenbank wie die CI. SQLite bleibt nur fuer schnelle Experimente mit
  `DEBUG=True` (Ausnahme: `ALLOW_SQLITE=1`).
- Drei Waechter-Tests sichern die Entscheidung ab.

### Hinzugefügt
- **Prozess-Automatik: echte Aktionen statt „nicht implementiert".** Die
  Automatik führte bisher nur Bewerber-Mails aus; alles andere – auch das
  Beispiel im eigenen Konfigurations-Feld – wurde stillschweigend
  übersprungen. Neu wirken:
  - `CREATE_TASK` – **Aufgabe/Erinnerung** an eine *Rolle* (nicht an eine
    Person, damit Urlaub sie nicht verwaisen lässt), optional mit Frist.
    Neue Seite „Aufgaben" mit Überfälligkeits-Markierung, Erledigen und
    Wieder-Öffnen; Badge in der Navigation.
  - `EMAIL_NOTIFICATION` an **interne** Empfänger (feste Adresse und/oder alle
    Mitglieder einer Rolle) – bisher wirkte nur der Bewerber-Fall.
  - `ADD_NOTE` – automatischer, gekennzeichneter Vermerk in den internen Notizen.
  - `AUTO_ADVANCE` – **Status-Autovorlauf** innerhalb der Sichtung.
- **Compliance-Grenze im Autovorlauf (Human-in-the-Loop):** `AUTO_ADVANCE` kann
  ausschließlich nach NEW / IN_REVIEW / INVITED schieben. **Zu- und Absagen sind
  hart gesperrt** – sie bleiben der menschlichen Entscheidung vorbehalten
  (`.agents/AGENTS.md`). Ein blockierter Versuch wird als
  `WORKFLOW_ACTION_BLOCKED` protokolliert. Der Autovorlauf löst außerdem keine
  Folge-Automatik aus (keine Ketten, keine Endlosschleifen) – beides getestet.

- **No-Code-Editor für die Prozess-Automatik.** Das rohe JSON-Textfeld ist durch
  einen Baukasten ersetzt: „Wenn *Phase* → dann *Aktion*" mit Auswahllisten und
  passenden Feldern je Aktionstyp. Das JSON entsteht daraus automatisch; für
  Fortgeschrittene bleibt es aufklappbar sichtbar und von Hand überschreibbar.
  Beim Bearbeiten einer Regel werden die Felder zurückbefüllt.
- Die Human-in-the-Loop-Grenze steht jetzt sichtbar im Formular; der
  Autovorlauf bietet Zusage/Absage gar nicht erst zur Auswahl an.

### Behoben
- **Frische Produktiv-Installation füllte sich selbst mit erfundenen Bewerbern
  (schwerwiegend).** `seed_data_if_empty()` lief im Dashboard **und auf der
  öffentlichen Startseite** – ohne jeden Schutz. Der erste Seitenaufruf einer
  leeren Installation (auch der eines **anonymen Besuchers**) legte
  Phantasie-Stellen, erfundene Bewerber:innen samt Anschreiben, **fabrizierte
  KI-Bewertungen** und einen Fake-Meeting-Link an; die öffentliche Stellenbörse
  zeigte dem Kunden erfundene Stellen. Für ein DSGVO-Produkt im regulierten
  Markt inakzeptabel. Demo-Daten entstehen jetzt nur noch bewusst
  (`DEMO_MODE=1`, Entwicklung, oder `manage.py seed_demo`); nötige
  Grundeinstellungen werden weiterhin angelegt.
- **SAP-Feldzuordnung war ein Blender.** Der „Sync jetzt ausführen"-Knopf übertrug
  **nichts**, meldete aber „Synchronisation abgeschlossen", zählte „Exportierte
  Bewerbersätze" und die Konsole gab einen **frei erfundenen** „SAP Response-Code:
  201 Created" aus (hartkodiert im Frontend). Die Zielsystem-Auswahl bot „SAP SF
  Production (Echtes HRIS)" an – intern hieß der Wert `MOCK_SAP_PROD`. Jetzt ist
  die Seite ein echtes Werkzeug: Sie **speichert die Feldzuordnung**, sagt klar,
  dass **keine Daten übertragen** werden, zeigt an, ob ein Endpunkt konfiguriert
  ist – und die Zuordnung wird vom (echten) `hris_export` **tatsächlich
  angewendet**.
- **HRIS-Export täuschte Erfolg vor (schwerwiegend).** `hris_export` stellte
  **nie** eine HTTP-Anfrage. Es baute eine Schein-Antwort, schrieb eine **frei
  erfundene SAP-ID** in die Bewerberakte und protokollierte
  `HRIS_EXPORT_SUCCESS` mit `"target": "SAP_SF_PRODUCTION"` im **Audit-Log** –
  dem Compliance-Nachweis, der nicht lügen darf. Betreiber hätten geglaubt,
  Bewerberdaten seien an SAP übertragen worden; übertragen wurde nichts.
  Neu: echte Übertragung (HTTP POST, Timeout, Statusprüfung) bei gesetztem
  `HRIS_ENDPOINT`; **ohne Konfiguration bricht der Befehl ab** statt zu
  simulieren; `--dry-run` zeigt die Struktur ohne PII; protokolliert wird nur
  das *tatsächliche* Ergebnis (echte Referenz oder gar keine). Regressions-Wache
  im Test verhindert die Rückkehr der Schein-Antwort.
- **Eingangsbestätigung fehlte komplett.** Die Erfolgsseite versprach „Sie
  erhalten in Kürze eine Bestätigung per E-Mail" – es wurde **keine** verschickt.
  Gravierender: Der Magic-Link zum Kandidatenportal stand nur auf dieser einen
  Seite. Wer den Tab schloss, kam **nie wieder** ins Portal (Status, Termine,
  Rückfragen) – das Feature war praktisch unbenutzbar. Neu: Bestätigungsmail mit
  Portal-Link (Vorlage „Eingangsbestätigung" mit `{name}`, `{stelle}`, `{firma}`,
  `{portal}` wird genutzt, wenn vorhanden), auditiert. Ein Mailfehler lässt die
  Bewerbung nicht scheitern (getestet).
- **Irreführende Standard-Vorbelegung entfernt.** Wurde eine Automatik-Regel ohne
  eigene Aktionen angelegt, erzeugte SecurATS Aktionen, die es **nie gab**
  (`AUTO_INVITE_INTERVIEW`, `TRIGGER_PROCESS` mit „CALENDAR_SYNC"/„ZOOM_ROOM_CREATE",
  `SEND_CONTRACT`). Ein Admin sah „Vertrag senden" in seiner Pipeline – ausgeführt
  wurde nichts. Die Vorbelegung nutzt jetzt ausschließlich Aktionen, die
  tatsächlich wirken (Vermerk, Aufgabe, Absage-Mail); zwei Tests verhindern
  einen Rückfall.
- Werbetext „ausgereifte Standard-Automatisierungen … Vertragsentwürfe" entfernt –
  er versprach Funktionen, die nicht existierten.

### Geändert
- Migration `0042` (Modell `WorkflowTask`).
- Unbekannte Aktionstypen werden weiterhin **ehrlich übersprungen** statt
  Erfolg zu simulieren – nur der Audit-Wortlaut wurde präzisiert.

## [1.7.0] – 2026-07-05

Reife-Release der Stellenfreigabe: Vertretung, parallele Stufen,
Genehmiger-Sichtbarkeit und die Engpass-Kennzahl machen den Prozess
alltagstauglich für echte Organisationen – vom Teamleiter bis zum
Aufsichtsrat, auch im Urlaubsfall.
Update: `docker compose pull && docker compose up -d` (Migration 0039).

### Hinzugefügt
- **Vertretung in der Freigabekette („i. V.")**: Aktive Vertretungen
  (bestehende Delegations-Mechanik) dürfen die fällige Stufe entscheiden;
  Zeitfenster und Einrichtungs-Scope serverseitig geprüft, stellenscharfe
  Vertretungen decken Bedarf bewusst nicht; jede Vertretungs-Entscheidung
  sichtbar gekennzeichnet und im Audit mit dem Vertretenen protokolliert.
- **Vertretungs-Selbstbedienung**: Jede interne Rolle legt ihre eigene
  Vertretung selbst an und beendet sie (vorher nur HR-Admin); Nicht-Admins
  sehen nur eigene erteilte/erhaltene Vertretungen; HR-Admin kann im
  Assistenz-Fall im Namen einer anderen Person anlegen (auditiert).
- **Parallele Genehmigungsstufen**: Ketten-Syntax „+" schaltet Rollen
  einer Stufe parallel („Controlling + Betriebsrat"); alle müssen
  genehmigen (Reihenfolge frei), eine Rückgabe stoppt den Antrag; ohne
  „+" exakt das bisherige sequenzielle Verhalten.
- **Engpass-Kennzahl je Freigabestufe**: Analytics-Karte „Welche Stufe
  bremst?" mit Ø Wartetagen je Rolle (fällig → entschieden), aktuell
  fälligen offenen Anträgen und Engpass-Badge; parallele Gruppen korrekt
  berücksichtigt (Fälligkeit ab letzter Vorgruppen-Entscheidung).

### Behoben
- **Genehmiger-Sichtbarkeit**: Ketten-Rollen (Bereichsleitung, Vorstand …)
  ohne Recruiter-Rolle sahen die Eingangs-Liste nicht, obwohl sie
  entscheiden durften; jetzt sehen sie ihre fälligen und selbst
  entschiedenen Anträge.
- **Assistenz-Anlage von Vertretungen**: Die Anlage durch HR-Admin erzeugte
  bisher eine Vertretung, die vom Admin selbst ausging (funktional falsch
  für Ketten-Rollen); der Vertretene ist jetzt wählbar.

## [1.6.0] – 2026-07-05

Governance-Release: Der komplette Weg VOR der Ausschreibung ist jetzt
abbildbar – vom beantragten Personalbedarf über konfigurierbare
Genehmigungsketten bis zur formalen Gesprächsrunden-Pflicht vor der
Einstellung. Optional je Installation, aber wenn aktiviert, verbindlich.
Update: `docker compose pull && docker compose up -d` (Migrationen 0034–0038).

### Hinzugefügt
- **Stellenfreigabe (vorgeschalteter Genehmigungsprozess)**: Teamleitung bis
  Aufsichtsrat beantragen Personalbedarf; sequenzielle, je Einrichtung oder
  global konfigurierbare Genehmigungskette (Rollen = frei anlegbare Gruppen);
  drei Ausgänge je Stufe (Genehmigen / Zur Nachbesserung mit Neustart /
  endgültig Ablehnen); Mail an Antragsteller; Stufenleiste am Antrag;
  optional per Schalter – wenn aktiv, ist Veröffentlichen ohne genehmigten
  Bedarf an allen drei Schaltpunkten blockiert (Wizard, Schnell-Toggle,
  finale Job-Freigabe).
- **No-Code Routing-Matrix**: Regeln verknüpfen Geltungsbereich (Einrichtung ×
  Abteilung × Job-Kategorie, Wildcards möglich) mit eigenem Bedarfsformular
  (dynamische Zusatzfragen: Freitext/Auswahl/Ja-Nein) und eigener
  Genehmigungskette; spezifischste Regel gewinnt (exakt > teilweise >
  Fallback); Pflicht je Regel wirkt auch ohne globalen Schalter; Antworten
  für Entscheider sichtbar; Pflege komplett ohne Code oder JSON.
- **Gremium: Quorum & Abstimmungs-Frist**: je Stelle konfigurierbares Quorum
  („N von M" statt starrer Mehrheit, ehrlich auf Sitzzahl gekappt) und
  Frist in Tagen mit rotem Überfälligkeits-Badge im Freigabe-Postfach und
  einmaliger Eskalations-Mail an ausstehende Mitglieder.
- **Kampagnen-Ablaufdatum**: Landingpages zeigen nach Ablauf eine freundliche
  Endseite mit Weg zur Stellenbörse (kein 404 – QR-Plakate hängen länger als
  Kampagnen laufen); abgelaufene Kanäle ordnen keine neuen Bewerbungen mehr
  zu, freie Quellen bleiben unbeschränkt; Pflege je Kanal/Landingpage,
  leer = unbegrenzt.
- **Gesprächsrunden als formale Zustände**: je Stelle definierbare Runden
  (z. B. Erstgespräch → Fachgespräch → Probearbeit); Einstellen erst möglich,
  wenn alle Runden abgeschlossen sind (klare Meldung nennt die offene Runde);
  Abschließen und Zurücknehmen (Korrektur) auf der Termine-Seite mit
  Fortschritts-Leiste; ohne definierte Runden bleibt alles wie bisher.

### Behoben
- **Freigabe-Bypass**: Die finale Job-Freigabe publizierte am
  Stellenfreigabe-Gate vorbei – jetzt bleibt die Stelle Entwurf, mit
  Warnung und Audit-Eintrag.
- **Wizard-Datenverlust**: Das Bearbeiten einer Stelle über die Oberfläche
  löschte gesetzte Quorum-/Frist-Werte stillschweigend (Felder wurden nie
  vorbefüllt); Edit befüllt jetzt alle Governance-Felder vor.

### Geändert
- Bedarf-Konvertierung übernimmt die Stellen-Anzahl (Headcount) aus dem
  genehmigten Antrag.
- Demo-Welt Banking enthält drei Routing-Matrix-Beispielregeln
  (Tech-Gremienprozess, Standard Filiale, globaler Fallback).

## [1.5.0] – 2026-07-04

Flexibilität & Bedienbarkeit: Das Einstellungs-Ereignis macht Erfolg messbar,
der CMS-Baukasten macht Seiten in Minuten baubar, und die Konfiguration
(Fragen, Formate, Import, Kosten) braucht kein Technik-Vorwissen mehr.
Update: `docker compose pull && docker compose up -d` (Migrationen 0029–0032).

### Hinzugefügt
- **Status „Eingestellt" mit Time-to-Fill**: nur aus „Eingeladen" setzbar,
  Einstellungsdatum automatisch oder manuell (rückwirkend, korrigierbar);
  grüne Kanban-Spalte; je Kanal/Landingpage „eingestellt" und „Ø Tage bis
  Einstellung"; Kosten je Einstellung rechnet mit echten Einstellungen.
- **CMS-Baukasten**: Seiten und Landingpages aus 10 Block-Typen zusammensetzen
  (Hero, Benefits, Kennzahlen, Zitat, FAQ, Bild, Ansprechperson, Stellen live,
  CTA) – Editor mit Live-Vorschau, ohne HTML, Träger-Branding automatisch.
- **Fragen-Builder ohne JSON**: Mindeststandards je Jobfamilie per Formular
  pflegen (Frage, Typ, Optionen, K.O.-Antwort, sortieren) – kein Technik-Vorwissen.
- **Fragetyp „Pflicht-Dokument"**: Führerschein, Impfnachweis oder Zertifikat
  je Stelle/Jobfamilie verlangen; Upload mit Whitelist, Ablage mit
  Anforderungs-Label; fehlend = Formular-Fehler, nie automatische Absage.
- **Gesprächsformate konfigurierbar**: eigene Formate anlegen/umbenennen/
  entfernen (HR-Admin) – bestehende Termine behalten ihre Bezeichnung.
- **Import: manuelle Spalten-Zuordnung** („Ihre Spalte → unser Feld", Automatik
  übersteuerbar, unerkannte Spalten benannt) und **Adressfeld** (verschlüsselt).
- **Kampagnenkosten am Kanal**: Betrag je Kanal, Kennzahl „Kosten je
  Einstellung" direkt auf der Kanal-Seite und in der Analytics.
- **Analytics-Vollständigkeit**: jede neue Landingpage UND jede neue
  Inhaltsseite erscheint automatisch (Aufruf-Zähler für CMS-Seiten;
  Inhaltsseiten setzen bewusst keine Kampagnenquelle).

### Migrationen
- 0029 CMS-Blöcke, 0030 Seiten-Aufrufe, 0031 Einstellungsdatum,
  0032 Adresse + Kanal-Kosten

## [1.4.0] – 2026-07-04

Kampagnen, Umstieg & Sicherheit: Der Erfolg von Maßnahmen wird messbar, der
Wechsel von Bestandssystemen praktikabel, die öffentlichen Formulare gehärtet.
Update: `docker compose pull && docker compose up -d` (Migrationen 0027–0028
automatisch; neue Abhängigkeiten openpyxl, segno via requirements).

### Hinzugefügt
- **Kanäle & Kampagnen**: Recruiting-Kanal in 10 Sekunden anlegen → Link +
  druckfertiger QR-Code; je Kanal Bewerbungen, „in Sichtung+", Einladungen und
  Einladungsquote. Kampagnen-Quelle überlebt jetzt die ganze Sitzung
  (Liste → Stelle → Formular) statt beim ersten Klick verloren zu gehen.
- **Kampagnen-Landingpages** unter `/k/<name>/`: eigene Ansprache (Überschrift,
  Text, Bild, Ansprechperson), Stellen-Scope über Einrichtung/Abteilung/
  Jobfamilie/Standort, Träger-Branding automatisch. Der Seiten-Name ist die
  Quelle – der volle Trichter Aufrufe → Bewerbungen → Einladungen erscheint auf
  der Verwaltungsseite und im Analytics-Dashboard.
- **Excel-Import (.xlsx)** mit demselben Spalten-Mapping wie CSV, echten
  Zeilennummern im Fehlerbericht und Testlauf zuerst.
- **CV-Dateien aus dem Altsystem (ZIP)**: Zuordnung über E-Mail-Dateinamen zur
  jüngsten Bewerbung, Typ-Erkennung, Testlauf-Garantie, Typ-Whitelist und
  Größenlimits.
- **Rollenspezifische Fragetypen** im Bewerbungsformular: Freitext und Auswahl
  neben Ja/Nein; K.O.-Logik nur bei definierter erwarteter Antwort, Pflichtfelder
  mit Inline-Fehler statt automatischer Absage.
- **Zweite Demo-Welt „Banking"** (`seed_demo_bank`): Großunternehmens-Szenario
  mit Kategorien-Hierarchie, drei Prozess-Profilen (Standard/Tech/Executive)
  und Karriere-Hub – dasselbe Produkt, andere Konfiguration.

### Sicherheit
- **Upload-Härtung am Bewerbungsformular**: Typ-Whitelist (PDF, Word, JPG,
  PNG), 10 MB je Datei, max. 5 Nachweise, Prüfung vor dem Anlegen.
- **XSS-Absicherung testfixiert**: End-to-End-Test über Portal, Nachrichten und
  Dashboard; Wächter-Test verbannt unsichere Template-Filter dauerhaft.

### Migrationen
- 0027 Recruiting-Kanäle, 0028 Landingpages

## [1.3.0] – 2026-07-03

Design & Träger-Identität: Die Software erklärt sich selbst – und trägt auf allen
Bewerberseiten die CI des Trägers statt der Produkt-Optik.
Update: `docker compose pull && docker compose up -d` (Migration 0026 automatisch).

### Hinzugefügt
- **Träger-Branding auf allen Bewerberseiten** (Stellenbörse, Bewerbungsstrecke,
  Portal, Inhaltsseiten): Primär-/Akzentfarbe, Logo, heller oder dunkler Grundton –
  Pflege unter „Erscheinungsbild" (HR-Admin). **Ein-Klick-Import von der
  Unternehmens-Website** (theme-color, Logo-Kandidat, Bildvorschlag; Best Effort mit
  manueller Bestätigung). **Kontrast-Automatik nach WCAG**: Textfarbe auf der
  Primärfarbe wird berechnet, nicht geraten. Das Recruiter-ATS behält bewusst die
  SecurATS-Identität (zentrale Pfad-Trennung, getestet). Live-Vorschau, Audit,
  serverseitige Farb-Validierung. Grundlage: CI-Muster-Analyse
  (Klinik-, Banken- und Telko-Websites) – dokumentiert im Bauplan.
- **Bewerbungs-Pipeline im Portal**: 4-Schritte-Anzeige (Eingegangen → Sichtung →
  Gespräch → Entscheidung) je Bewerbung; Absage als würdevoller grauer Stopp;
  Screenreader-Label.
- **Gremium-Sitz-Punkte im Freigabe-Postfach**: ✓/✗/· je Sitz mit Namen im Tooltip,
  Vertretungs-Stimmen mit V-Marker – der Stand ist auf einen Blick erfassbar.
- **Sidebar in fünf benannten Gruppen** (Arbeitsbereich / Entscheiden / Termine &
  Menschen / Stammdaten & Inhalte / System & Nachweis) mit sinnvoller Umsortierung.

### Geändert
- **Bewerberportal vollständig auf Design-Tokens** umgestellt: Träger-CI wirkt auch
  dort (hell + Logo), ohne Branding bleibt die gewohnte Optik; einheitliche
  Status-Farbsprache (NEU=Violett, SICHTUNG=Bernstein, EINGELADEN=Teal, ABSAGE=Grau)
  auf hellem und dunklem Grund lesbar; tote Alt-Timeline entfernt.
- **Mobil-Feinschliff im Portal**: Touch-Ziele min. 44 px, 15-px-Formularschrift
  (kein iOS-Zoom), einspaltiges Layout unter 480 px.

### Migrationen
- 0026 Branding-Felder an der Organisation

## [1.2.0] – 2026-07-03

Prozess-Individualisierung & Governance: Das System merkt sich bewährte Prozesse,
Gremien entscheiden vor der Einladung, Vertretungen blockieren nichts mehr – und
das Audit-Log behauptet nur noch, was wirklich passiert ist.
Update: `docker compose pull && docker compose up -d` (Migrationen 0022–0025 automatisch).

### Hinzugefügt
- **Prozess-Gedächtnis** (Job-Wizard „Bewährten Prozess übernehmen" + automatisch beim
  Bedarf-Convert): Spezifitäts-Leiter Abteilung > Einrichtung > Standort > Jobfamilie;
  Kaltstart-Fallback aufs Regelwerk des Prozess-Beraters; Herkunft wird angezeigt.
- **Vorstands-Mindeststandards** je Jobfamilie (Pflege nur HR-Admin): serverseitig bei
  jedem Speichern durchgesetzt – fehlende Pflichtfragen werden wieder eingefügt,
  `isMandatory` ist nicht abschwächbar; vollständig auditiert.
- **Sichtungs-Gremium vor der Einladung** (höhere Positionen): je Struktur konfigurierbar
  über die Vererbungs-Leiter Stelle > Abteilung > Einrichtung > Standort > Jobfamilie >
  Organisation (Pflegeseite `/recruiter/gremien/`, Sentinel „bewusst kein Gremium");
  absolute Mehrheit gibt frei, serverseitig an allen Einladungs-Pfaden; Stimmen änderbar
  und auditiert, Kommentare in den internen Notizen; Live-Vorschau des wirksamen Gremiums
  im Job-Wizard; Override granular über `OVERRIDE_GROUPS` (auditiert).
- **Urlaubsvertretung wirkt** (vorher Karteileiche): in Freigaben (Badge + Kommentar-Vermerk)
  und Gremien (Sitz-Logik, eigene Stimme hat Vorrang); Scope ALL/FACILITY/JOB serverseitig;
  vorzeitiges Beenden wirkt sofort überall; eigene Persona [VT] mit UC-VT-01…06 verankert.
- **Entscheidungs-Erinnerungen** (`send_decision_reminders`, Cron): offene Freigaben (nur
  wer an der Reihe ist) und fehlende Gremien-Stimmen; genau eine Erinnerung je Person und
  Vorgang; Vertretungen werden mit erinnert.
- **Talent-Pool-Lebenszyklus** (vorher Karteileiche): Opt-in im Portal (Kriterien
  datensparsam aus eigenen Bewerbungen), Matching auf offene Stellen, Ein-Klick-Hinweis
  mit Doppel-Ansprache-Sperre, Austritt jederzeit, Wirksamkeits-Kennzahlen inkl.
  Konversion, `purge_talent_pool` (DSGVO-Löschung nach Kulanzfrist).
- **Würdevolle Absage-Kommunikation**: echte Mail + Portal-Nachricht beim REJECTED-Übergang
  (einmalig, Vorlage „Absage" mit Platzhaltern), mit Portal-Link und Talent-Pool-Einladung.
- **Bestandserhalt-Testnetz**: No-Op-Roundtrip-Tests für alle sechs Edit-Pfade –
  verbindliche Regel für jede künftige Edit-View.

### Geändert
- **Workflow-Aktionen ehrlich**: `EMAIL_NOTIFICATION` versendet jetzt echte Mails aus
  Vorlagen (oder auditiert `SKIPPED_NO_TEMPLATE`); alle nicht implementierten Aktionen
  werden als `WORKFLOW_ACTION_SKIPPED` auditiert statt Versand zu simulieren; Mock-Links entfernt.

### Sicherheit
- Portal-Rate-Limit: max. 10 eingehende Vorgänge je Stunde und Person (Rückfragen,
  Änderungswünsche, E-Mail-Änderungs-Anfragen) – freundliche Bremse statt Team-Flutung.
- Datenverlust-Bug behoben: Bearbeiten einer Stelle löschte deren Gremium stillschweigend
  (Edit-Vorbefüllung + Testnetz verhindern die gesamte Bug-Klasse).
- Audit-Integrität: keine „SENT"-Behauptungen mehr ohne tatsächlichen Versand.

### Migrationen
- 0022 `TalentPoolContact` · 0023 `JobFamily.minimumQuestionsJson`
  · 0024 `JobPosting.panelUserIdsJson` + `ApplicationVote` · 0025 Gremien-Defaults auf
  Organisation/Standort/Einrichtung/Abteilung/Jobfamilie

## [1.1.0] – 2026-07-03

Terminmanagement komplett: vom Bedarf über die Einladung bis zum gemessenen Ergebnis.
Update wie gewohnt: `docker compose pull && docker compose up -d` (Migrationen 0016–0021 laufen automatisch).

### Hinzugefügt
- **Team-Kalender** (`/recruiter/interviews/`): Monatsraster über alle Standorte (BOLA-gescopt),
  Interviews + angebotene/belegte Timeslots inkl. Ersteller, `.ics`-Download (bewusst kein
  Abo-Feed: PII). Slot-Anlage einzeln oder als Wochen-Serie, mit Gesprächsformat.
- **Sechs Gesprächsformate durchgängig** (Telefonat, Video, vor Ort, Probearbeit/Hospitation,
  Assessment/Auswahltag, schriftliche Aufgabe): im Einlade-Modal, am Slot, als Kalender-Badge,
  im Portal **vor** der Buchung, im Erinnerungs-Betreff und im `.ics`-Export.
- **Interview-Team:** Teilnehmende beim Einladen zuordnen; sofortige Team-Mail bei Planung,
  Team-Erinnerung an alle Beteiligten, Info bei jeder Bewerber-Aktion (Umbuchung/Absage/Wunsch).
- **Selbstbuchung & Selbstservice im Portal:** Terminwahl per Ein-Klick (atomar, Doppelbuchung
  ausgeschlossen), Umbuchen und Absagen bis 24 h vorher (serverseitig erzwungen), jederzeit
  Änderungsanfrage; mehrstufige Runden (Telefonat → Probearbeit → vor Ort) je Runde neu buchbar.
- **Termin-Erinnerungen** (`send_interview_reminders`, Cron): genau einmal je Interview,
  an Bewerbende (Mail + Portal) und das gesamte Interview-Team; Umbuchung schärft die
  Erinnerung neu.
- **Ergebnis-Erfassung:** „Ergebnis erfassen" im Kalender (stattgefunden / No-Show /
  kurzfristig abgesagt), Ein-Klick, auditiert mit Vorwert; Zusage/Absage bleibt im Kanban.
- **Termin-Analytik** (Analytics › „Termine & Selbstbuchung"): Selbstbuchungs-Quote, Median
  bis zur Terminwahl, Abend/Wochenend-Anteil, Umbuchungen/Absagen/Änderungswünsche,
  Slot-Auslastung, Formate-Verteilung, **No-Show-Quote** (nur über erfasste Ergebnisse) –
  mit regelbasierten Handlungsvorschlägen; Kennzahlen auch im lokalen KI-Analysten.
- **Portal-Nachrichten:** Verlauf beider Richtungen je Bewerbung sichtbar + Rückfrage-Formular
  (Mail an die Ansprechperson der Stelle); Kontaktdaten: Telefon direkt änderbar, E-Mail-Änderung
  bewusst nur als geprüfte Anfrage (Identitätsanker).
- **Personalbedarf** (`/recruiter/bedarf/`): strukturierte Meldung statt Zuruf; Entscheidung mit
  Anmerkung + Mail an Melder:in; **Ein-Klick-Überführung** in einen unveröffentlichten
  Ausschreibungs-Entwurf (interne Begründung bleibt intern, Freigabe-Gate greift automatisch).
- **„Heute wichtig"** im Dashboard: unbeantwortete Nachrichten (mit Direktlinks), überfällige
  Erstsichtungen, wartende Freigaben, heutige Gespräche, offene Ergebnisse, offene Bedarfe.
- **Audit-Export** (`/recruiter/audit/export.csv`, HR-Admin): CSV mit Zeitraum-/Aktions-Filter,
  Integritäts-Kopfzeile (Hash-Ketten-Status) und `entryHash` je Zeile; Export selbst auditiert.
- **Prozess-Berater** am Stellen-Formular: berufsspezifische K.-o.-Frage-Vorschläge (Examen,
  Approbation, Führungszeugnis …), KI-Zusatzfragen stets optional; Freigabekette je Einrichtung
  konfigurierbar (`Facility.approvalChain`, nie leer).
- **Einladungs-Nachricht** im Modal (aus Vorlage vorbefüllt, lokale KI-Politur optional),
  echte Zustellung als Portal-Nachricht + E-Mail statt Mock-Links.

### Geändert
- Portal-Terminwahl prüft auf **anstehende** statt irgendwelche Gespräche (mehrstufige Prozesse).
- Demo-Seed: Slots mit gemischten Formaten (inkl. 4-h-Probearbeit).
- Use-Case-Matrix: 9 veraltete „(Roadmap)"-Zeilen auf ✅ korrigiert; 12 UCs neu erfüllt
  (UC-SB-20…26, UC-AY-10…13, UC-MD-01/02, UC-JF-10, UC-MB-08, UC-NS-12, UC-LK-11, UC-RI-06,
  UC-PW-06, UC-UM-06).

### Sicherheit
- Selbstservice-Grenzen serverseitig erzwungen (24-h-Regel, fremde Tokens wirkungslos).
- E-Mail-Änderung im Portal nur als geprüfte Anfrage (Schutz des Magic-Link-Identitätsankers).
- Interne Bedarfs-Begründungen erscheinen nie in öffentlichen Ausschreibungen (getestet).

### Migrationen
- 0016 `Facility.approvalChain` · 0017 `InterviewSlot.createdBy` · 0018 `Interview.reminderSentAt`
  · 0019 `Interview.participants` + `InterviewSlot.kind` · 0020 `StaffingRequest`
  · 0021 `StaffingRequest.convertedJob`

## [1.0.0] – 2026-07-02

Erste versionierte Release. Konsolidiert den kompletten Ausbau WP0–WP8 plus Nachträge.

### Hinzugefügt
- **Kandidaten-Strecke:** Bewerbung ohne Konto (Handy-Foto statt PDF genügt), Mehrfach-Dokumente,
  Magic-Link-Portal mit 4-Stufen-Status-Timeline, Leichte Sprache je Stelle, Vorlesefunktion,
  Barrierefreiheits-Panel (Legasthenie-Schrift, Kontrast, Fokusmodus, Lese-Lineal).
- **Job-Alerts mit Scope:** Stichwort / Einrichtung / km-Umkreis (Haversine) / global;
  Double-Opt-in, Verwalten & Abmelden per Token, automatischer 12-Monats-Verfall,
  genau ein Abo je E-Mail (Update statt Duplikat). Versand-Command `send_job_alerts`.
- **Stellensuche:** Volltext (Titel + Beschreibung), Standort-/Abteilungs-/Kategorie-Filter;
  öffentliche Einrichtungs-Karriereseiten `/einrichtung/<slug>/`.
- **Recruiter:** Kanban mit positionalem Drag&Drop **und** Tastatur-Alternative, Mehrfachauswahl,
  Stammdaten-Zentrale (Ansprechpartner inkl. „Überall ersetzen", Textbausteine, Vorlagen mit
  Versionierung + Tonalitäts-Overlay), Ein-Klick-(De)Aktivierung von Anzeigen.
- **Governance:** Freigabe-Postfach „wartet auf mich" mit SLA-Frist; **automatisches
  Approval-Gate** (`Facility.requiresApproval` + `APPROVAL_CHAIN`), finale Freigabe
  publiziert automatisch; datenminimiertes Governance-Cockpit für BR/SBV/DSB;
  GF-Wochenreport (`weekly_report`).
- **Analytics:** Time-to-Fill-Prognose, Anomalie-Hinweise mit Handlungsvorschlag,
  Fairness-Cockpit (datensparsam), Standort-Benchmark & Kosten/Einstellung (Leitung),
  CSV-Export (auditiert), lokaler KI-Analyst auf aggregierten Daten.
- **Sicherheit/Compliance:** PII-Verschlüsselung inkl. **E-Mail via Blind-Index** (HMAC),
  Audit-Log mit Hash-Kette + `verify_audit`, DSGVO-Export `export_applicant`,
  Prompt-Injection-Guardrails (`ai_safety`), Feed-Token, BOLA-Scoping durchgängig,
  serverseitige Inline-Formularfehler (WCAG 3.3.1 – alle AA-Lücken geschlossen).
- **Betrieb:** DB-Queue + `ai_worker`, `/healthz/` (inkl. Version), `ai_doctor`,
  PostgreSQL-Produktionsprofil, Runbook (OPERATIONS.md), Docker-Compose-Stack
  (Postgres, optionales KI-Profil), Release-Workflow (ghcr.io).

### Geändert
- **KI-Scoring ist Opt-in (Default AUS)** – `AI_SCORING_ENABLED`; keine Platzhalter-Scores
  mehr, ehrliche „–"-Anzeige. Positionierung: „KI-Assistenz, keine automatische Bewertung".
- Landing bewerber-zentriert; erfundene Bewertungs-Badge entfernt.

### Sicherheit
- CV-Downloads nur über autorisierte Endpoints (BOLA + Audit), kein /media/-Direktzugriff.
