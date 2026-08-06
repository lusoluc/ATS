# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/de/), Versionierung: [SemVer](https://semver.org/lang/de/).
Update-Pfad: `docker compose pull && docker compose up -d` (Migrationen laufen automatisch, siehe INSTALL.md).

## [Unreleased]

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
