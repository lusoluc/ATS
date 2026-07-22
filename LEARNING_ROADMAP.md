# Lernende Bewerber-Passung — Roadmap

Ziel: SecurATS lernt mit der Zeit, welche Bewerber zu einer Stelle passen und
welche nicht. Recruiter konzentrieren sich auf die relevanten Personen,
Stellenanzeigen werden besser, die Fachabteilung wird fundierter beraten.
Fernziel: Einladungen und Absagen stärker automatisieren — ohne die
menschliche Entscheidung zu ersetzen.

Zwei Grundregeln ziehen sich durch alles:

1. **Aus Entscheidungen lernen, nicht aus Extra-Klicks.** Recruiter laden
   ohnehin ein, sagen ab, stellen ein. Genau das ist das Trainingssignal. Kein
   Klick, der nicht sowieso Arbeit wäre. (Deshalb wurden die alten
   „Positiv/Negativ (RAG)"-Buttons entfernt — sie lernten nichts.)
2. **Jede Erkenntnis kommt mit Vorschlag und Aktion.** Eine Zahl ohne
   Handlungsempfehlung ist Deko und wird ignoriert. Die Auswertung ist nur der
   Auslöser; das Produkt ist der konkrete nächste Schritt mit einem Button.

## Welche Datenpunkte wir schon haben

Ohne ein einziges neues Feld:

- **Entscheidungen (die Wahrheit):** Statusverlauf jeder Bewerbung
  (NEU → Prüfung → Eingeladen → Eingestellt / Abgelehnt), mit Zeitstempel in der
  Audit-Kette (`STATUS_CHANGE`).
- **Interview-Feedback:** Empfehlung, Kriterien-Bewertungen, Stärken, Bedenken.
- **Gremium:** Stimmen dafür/dagegen.
- **Screening:** Antworten je Bewerbung gegen die K.O.-/Pflichtfragen der Stelle.
- **Herkunft:** Kanal jeder Bewerbung.
- **Zeit:** Eingang, Zeit bis Einladung, Zeit bis Einstellung.
- **Text:** Anschreiben, Lebenslauf (lokal, verschlüsselt).

Bewusst NICHT und nie: geschützte Merkmale (Alter, Geschlecht, Herkunft, …).

## Die Stufen

### L1 — Einblicke, die zu einer Handlung führen

Auswertung vorhandener Daten, null Risiko — aber **nie nur eine Zahl.** Jede
Erkenntnis trägt einen Vorschlag und einen Button:

- Statt „an Frage X scheitern 60 %" → „Frage X lässt 60 % durchfallen,
  vermutlich zu streng. **Frage lockern / entfernen?**"
- Statt „Kanal Y liefert kaum Einstellungen" → „Kanal Y: 40 Bewerbungen, 0
  Einstellungen. **Budget auf Kanal Z verschieben?**"
- Statt „Zeit bis Besetzung: 34 Tage" → „Engpass war die Freigabestufe
  Geschäftsführung (18 Tage). **Frist setzen / eskalieren?**"

Nutzen: Recruiter und Fachabteilung sehen nicht nur Muster, sondern kriegen den
nächsten Schritt gleich mitgeliefert.

### L2 — Bewerber-Steckbrief (schnelles Bild, schnellere Entscheidung)

Keine Rangliste, kein Bewerber gegen Bewerber. Beim Öffnen einer Karte eine
**kurze Zusammenfassung**, damit der Prüfer in Sekunden ein Bild hat:

> „Examinierte Pflegefachkraft, 6 Jahre Nachtdienst. Erfüllt alle vier
> K.O.-Kriterien. Anschreiben betont Teamarbeit und Bezugspflege."

Drei Sekunden statt drei Minuten Lesen. Lokal erzeugt, faktentreu aus den
vorhandenen Feldern (Screening-Antworten, Anschreiben, CV); die KI formuliert
nur, sie erfindet nichts. Das ist die sichtbare Hilfe für den Menschen — die
gelernte Einordnung steckt in L3.

### L3 — Das A/B/C/D-Scoring lernt aus echten Ergebnissen

Kein zweites Ranking neben dem Score. Das **bestehende A/B/C/D-Score selbst**
wird besser: aus dem Gesamtbild aller Datenpunkte plus den tatsächlichen
Entscheidungen lernt das System, Bewerber treffsicherer einzuordnen. (Damit
fällt das frühere „L5" weg — es war dasselbe Ziel.)

**Woher kommen die Daten / was ist relevant?**

- **Das Label (was wir vorhersagen):** die reale Screening-Entscheidung je
  vergangener Bewerbung — eingeladen vs. abgelehnt, verfeinert um „eingestellt"
  als stärkstes Positiv-Signal. Quelle: `STATUS_CHANGE`-Verlauf in der
  Audit-Kette. Das ist die Wahrheit, die das Team selbst geschaffen hat.
- **Die Merkmale (was vorhersagt) — nur stellenrelevant, nie geschützt:**
  - erfüllte K.O./Pflichtkriterien der Stelle (aus Screening-Antworten) — das
    stärkste, objektivste Signal
  - aus CV/Anschreiben abgeleitete Fachsignale: geforderte Qualifikation
    vorhanden? einschlägige Jahre? Treffer auf die Anforderungen der Stelle
  - Vollständigkeit der Bewerbung, Herkunftskanal (schwach)
  - Interview-Feedback fließt NUR als Label-Verfeinerung ein (liegt erst nach
    dem Gespräch vor), nie als Vorfilter-Merkmal
- **Pro Jobfamilie gelernt.** „Gut zur Stelle" heißt bei Nachtpflege etwas
  anderes als bei IT. Global lernen wäre wertlos.

**Wie lernen wir?** In zwei Stufen, transparent zuerst:

1. **Gewichtetes, erklärbares Scoring (Start):** Pro Jobfamilie wird aus der
   Historie gemessen, welche Merkmale mit einer Einladung zusammenhängen (Lift
   je Kriterium: „wer Schichtbereitschaft erfüllte, wurde 2,3× häufiger
   eingeladen"). Das Score ist eine gewichtete Summe erfüllter Kriterien,
   kalibriert auf die Bänder A/B/C/D. Keine Black Box — jede Note kommt mit
   ihrer Begründung.
2. **Lokales, inspizierbares Modell (später, opt-in):** ein einfaches Modell
   (z. B. logistische Regression) auf denselben Merkmalen, lokal trainiert,
   weiterhin über Merkmalsbeiträge erklärbar. Erst bei genug Daten und
   rechtlichem Grünlicht.

**Kaltstart:** Ohne Historie greift das heutige regelbasierte Screening
(K.O.-Kriterien). Das System sagt ehrlich „noch zu wenig Entscheidungen für
gelerntes Scoring in dieser Jobfamilie (12 von ~50)".

**Wie messen wir?** Ohne Messung ist Lernen wertlos. Vier Metriken, sichtbar
gehalten:

1. **Backtest:** auf älteren Entscheidungen trainieren, auf neueren prüfen. Wie
   oft traf die A/B-Empfehlung die reale Einladungs-Entscheidung? (Präzision/
   Trefferquote auf „eingeladen".)
2. **Kalibrierung:** Werden A-Bewerber tatsächlich häufiger eingeladen als
   C-Bewerber? Einladungsquote je Band anzeigen. Gleiche Quote in A und C =
   das Modell hat nichts gelernt — das wird ehrlich gezeigt.
3. **Mensch-über-Modell-Quote:** wie oft weicht der Recruiter vom Band ab
   (steckt schon im Fairness-Cockpit). Etwas Abweichung ist gesund (Mensch
   steuert); ein sinkender Trend = das Modell lernt die echten Präferenzen des
   Teams. Dauerhaft hohe Abweichung = Rauschen, dann nicht vertrauen.
4. **Fairness-Drift:** auch ohne geschützte Merkmale als Eingabe überwachen,
   ob das Score unbeabsichtigt mit einem Näherungsmerkmal korreliert. Zuhause
   im Fairness-Cockpit.

**Die Ehrlichkeits-Schranke:** Das gelernte Score wird nur angezeigt, wenn es
im Backtest die naive Grundlinie (rein regelbasiert) schlägt. Schlägt es sie
nicht, bleibt es aus — das Anti-Blender-Prinzip, angewandt auf ML.

### L4 — Stellenanzeigen dort optimieren, wo sie entstehen

Nicht in einem separaten Report, den keiner öffnet, sondern **im Editor selbst.**
Beim Bearbeiten einer Stelle erscheint der Lern-Hinweis direkt am Feld:

> „Diese Anforderung hatten 8 vergleichbare Stellen — die ohne sie wurden
> 12 Tage schneller besetzt. **Streichen?**"

> „Screening-Frage Z ließ 60 % durchfallen; ähnliche Stellen ohne diese Frage
> bekamen mehr qualifizierte Bewerbungen. **Zur optionalen Frage machen?**"

Die Hilfe sitzt am Ort der Entscheidung — im Fragen-Baukasten (A1) und im
Stellen-Editor. Vorschläge füllen nur vor; wirksam wird nichts ohne Speichern.

## Governance — nicht verhandelbar

Bewerber-Bewertung im Beschäftigungskontext ist nach EU AI Act (Anhang III)
**Hochrisiko.** Der bestehende Kurs gilt für jede Stufe:

- **Mensch entscheidet.** Gelernte Signale sind Empfehlung; automatisch wirken
  nur objektive K.O.-Kriterien.
- **Keine geschützten Merkmale** als Eingabe. Datensparsamkeit bleibt.
- **Erklärbarkeit.** Jede Note nennt ihre Gründe. Kein undurchsichtiger Score.
- **Messbar.** Kein gelerntes Score ohne Backtest, Kalibrierung, Override-Quote.
- **Audit.** Jede automatische Aktion einzeln in der Hash-Kette nachweisbar.
- **Opt-in.** Scoring bleibt standardmäßig aus; ein Träger schaltet es bewusst
  und dokumentiert frei.
- **Rechtsgutachten** vor der Vermarktung als „KI-Feature" und vor dem lokalen
  Modell in L3.

## Reihenfolge

L1 zuerst — sofort nützlich, schafft die Datengrundlage und das Vertrauen.
Dann L2 (Steckbrief) und L4 (Editor-Hinweise) parallel. L3 zuletzt und in
Stufen (erst gewichtet-transparent, dann optional lokales Modell), erst wenn
genug Entscheidungen vorliegen und die Messung trägt.
