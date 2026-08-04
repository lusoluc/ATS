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
- **Pro Kontext gelernt, nicht nur pro Beruf.** „Gut zur Stelle" heißt bei
  Nachtpflege etwas anderes als bei IT — aber auch: Station 3 in Hamburg
  bewertet anders als die Geriatrie in Lüneburg. Jede Abteilung hat eigene
  Schwerpunkte, jeder Standort einen eigenen Arbeitsmarkt. Der Lern-Kontext ist
  deshalb das Tripel **(Jobfamilie, Standort, Abteilung)**, nicht die Jobfamilie
  allein. Nur so stimmt am Ende die Gesamt-Erfolgsquote.

**Spezifitäts-Leiter gegen dünne Daten.** Je enger der Kontext, desto treffender
— aber desto weniger Entscheidungen liegen vor. Deshalb lernt das System auf der
spezifischsten Ebene, die genug Daten hat, und fällt sonst zurück. Dieselbe
Leiter, die SecurATS schon bei Gremien und Freigabe-Regeln nutzt
(`resolve_panel`, `resolve_requisition_rule`) — ein Muster, das die Fachabteilung
bereits kennt:

    Abteilung + Jobfamilie          (am treffendsten)
      ↓ zu wenig Daten
    Einrichtung + Jobfamilie
      ↓
    Standort + Jobfamilie
      ↓
    Jobfamilie
      ↓
    Organisation (Notnagel)

Die genutzte Ebene wird immer mit angezeigt: „gelernt auf Ebene *Abteilung
Station 3 · Pflege*, 34 Entscheidungen" — oder ehrlich „nur auf Ebene
*Jobfamilie Pflege* (Abteilung hat erst 6 Entscheidungen)". Der Recruiter sieht
damit sofort, wie belastbar die Einordnung ist.

**Warum das den Ausschlag gibt:** Dieselbe Bewerberin kann für die IT-Abteilung
in Berlin ein A und für die Verwaltung in Hamburg ein C sein. Wer nur den Beruf
betrachtet, mittelt diese Unterschiede weg und lernt Durchschnitt statt Passung.
Bewertet wird also immer das Paar aus **Person und Kontext** (Beruf + Standort +
Abteilung).

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
3. **Mensch-über-Modell-Quote:** wie oft weicht der Recruiter vom Band ab.
   Etwas Abweichung ist gesund (Mensch steuert); dauerhaft hohe Abweichung =
   das Modell trägt nicht. **Umgesetzt (L5):** `scoring_eval.drift_report`
   zählt im neuesten Prüf-Fenster die Fälle „Note A → trotzdem abgesagt" und
   „Note D → trotzdem eingeladen"; ab 30 % erscheint auf der Messstrecken-Seite
   eine Frühwarnung samt konkretem nächsten Schritt. Das Fairness-Cockpit misst
   dieselbe Idee für das LLM-Score — beides ergänzt sich, keins ersetzt das
   andere.
3b. **Zeitverlauf (L5):** Ein Modell, das den Backtest heute besteht, kann in
   drei Monaten an der Realität vorbeilaufen. Deshalb wird auf den ältesten
   50 % gelernt und auf ZWEI aufeinanderfolgenden Fenstern geprüft; fällt die
   Treffsicherheit um mehr als 10 Punkte, steht „fallend" in der Messstrecke —
   mit der Handlung „Zuschnitt und Pflichtkriterien der Jobfamilie prüfen".
4. **Fairness-Drift:** auch ohne geschützte Merkmale als Eingabe überwachen,
   ob das Score unbeabsichtigt mit einem Näherungsmerkmal korreliert. Zuhause
   im Fairness-Cockpit.

Alle vier Metriken werden **je Kontext-Ebene** geführt (Abteilung/Standort/
Jobfamilie). Nur so lässt sich sagen, wo das Lernen trägt und wo es noch
Durchschnitt produziert — und nur die Ebenen, die den Backtest bestehen, werden
überhaupt angezeigt.

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
- **Wahlfreiheit.** Automatische Kanäle (Auto-Antwort, künftig evtl. Sprache)
  sind Angebote neben dem Weg zum Menschen, nie Ersatz. Gekennzeichnet nach
  Art. 50 EU AI Act; die Transparenz-Seite `/ki-transparenz/` erklärt den Stand.
- **Keine geschützten Merkmale** als Eingabe. Datensparsamkeit bleibt.
- **Erklärbarkeit.** Jede Note nennt ihre Gründe. Kein undurchsichtiger Score.
- **Messbar.** Kein gelerntes Score ohne Backtest, Kalibrierung, Override-Quote.
- **Audit.** Jede automatische Aktion einzeln in der Hash-Kette nachweisbar.
- **Opt-in.** Scoring bleibt standardmäßig aus; ein Träger schaltet es bewusst
  und dokumentiert frei.
- **Rechtsgutachten** vor der Vermarktung als „KI-Feature" und vor dem lokalen
  Modell in L3.
- **Kein Sprachkanal ohne Bias-Eval.** Spracherkennung diskriminiert messbar
  nach Akzent/Zweitsprache; ein Voice-Feature braucht VOR dem Pilot einen
  bestandenen ASR-Bias-Test (AI-Voice-Agent-Studie 2026; ROADMAP Evidenz-Gates).

## Reihenfolge

L1 zuerst — sofort nützlich, schafft die Datengrundlage und das Vertrauen.
Dann L2 (Steckbrief) und L4 (Editor-Hinweise) parallel. L3 zuletzt und in
Stufen (erst gewichtet-transparent, dann optional lokales Modell), erst wenn
genug Entscheidungen vorliegen und die Messung trägt.

---

# L1 — Umsetzungsplan (implementierungsreif)

Erste Stufe, weil sie sofort Nutzen bringt, kein Risiko trägt und die
Datengrundlage für L3 schafft. Grundsatz aus der Abstimmung: **keine Kennzahl
ohne Vorschlag und Aktion.**

## Bausteine

### 1. Rechenkern `ats/insights.py`

Neues Modul, voll typisiert (mypy-strict-Liste), je Funktion eine Abfrage,
keine N+1. Liefert Rohzahlen — keine Formulierung, keine UI.

| Funktion | Liefert | Quelle |
|---|---|---|
| `funnel_by_context()` | je Kontext (Jobfamilie / Standort / Abteilung): Anzahl je Stufe (Neu → Prüfung → Eingeladen → Eingestellt), Abbruchquote je Übergang | `Application.status` + `STATUS_CHANGE`-Audit |
| `channel_effectiveness()` | je Quelle: Bewerbungen, Einladungen, Einstellungen, Quote | `Application.source` + Status |
| `screening_question_impact(context)` | je Frage im Kontext: Durchfallquote, Einladungsquote bei erfüllt vs. nicht erfüllt | `screeningAnswersJson` gegen `JobPosting.screeningQuestionsJson` |
| `stage_bottlenecks()` | durchschnittliche Liegezeit je Prozessstufe, langsamste Stufe | Zeitstempel der `STATUS_CHANGE`-Kette, Freigabe-/Bedarfs-Schritte |

**Kontext-Ebene:** Jede Funktion nimmt einen Kontext (Jobfamilie, optional
Standort und Abteilung) und liefert neben dem Ergebnis die Ebene, auf der
gerechnet wurde — nach der Spezifitäts-Leiter aus dem L3-Kapitel. Ein
gemeinsamer Helfer `resolve_learning_scope(job)` löst sie auf, damit L1 bis L4
dieselbe Logik nutzen.

**Mindestmenge:** Jede Funktion liefert zusätzlich `sample_size`. Unter 20
abgeschlossenen Vorgängen auf der jeweiligen Ebene gibt es KEINE Aussage,
sondern ehrlich „zu wenig Daten (7 von 20) — nächst breitere Ebene genutzt".
Rauschen als Erkenntnis zu verkaufen wäre derselbe Fehler wie die alten
RAG-Buttons.

### 2. Vorschlags-Schicht `ats/suggestions.py`

Übersetzt Rohzahlen in **Vorschlag + Aktion**. Ein Vorschlag ist:

```
Suggestion(
  text="Screening-Frage „Führerschein Klasse C" lässt 62 % durchfallen.",
  reason="Bei vergleichbaren Stellen ohne diese Frage gab es 2,4× mehr Einladungen.",
  action_label="Frage prüfen",
  action_url="/recruiter/... (Stellen-Editor, Frage markiert)",
  severity="warn",
  sample_size=48,
)
```

Regeln (Schwellen bewusst konservativ, im Code dokumentiert):
- Durchfallquote einer Pflichtfrage > 50 % → „zu streng?" mit Link zum
  Fragen-Baukasten der betroffenen Stellen
- Kanal mit ≥ 20 Bewerbungen und 0 Einstellungen → „Budget prüfen" mit Link
  zu Kanäle & Kampagnen
- Stufe mit Liegezeit > 2× Median → „Engpass" mit Link zur Governance/Frist
- Jobfamilie mit Abbruch > 70 % zwischen zwei Stufen → „Prozess prüfen"

### 3. Anzeige

- **Analytics-Seite:** neuer Block „Erkenntnisse & Vorschläge" ganz oben —
  maximal fünf, nach Wirkung sortiert, jeder mit genau einem Aktions-Button.
  Kein Diagramm-Friedhof.
- **Am Ort der Entscheidung (Vorgriff auf L4):** die Frage-Vorschläge
  erscheinen zusätzlich direkt im Fragen-Baukasten des Stellen-Editors.
- Nichts wird automatisch geändert. Der Vorschlag füllt nur vor.

### 4. Tests

- Rechenkern: Trichter, Kanal, Frage-Wirkung, Engpass je gegen aufgebaute
  Testdaten; Mindestmengen-Schranke (unter 20 → keine Aussage).
- Vorschlags-Schicht: löst die richtige Regel aus, formuliert Aktion + Link.
- Ansicht: Analytics rendert Vorschläge, Recruiter sieht nur Erlaubtes (BOLA).

## Reihenfolge der Umsetzung

1. `ats/insights.py` + Tests (reine Rechnung, keine UI) — isoliert prüfbar.
2. `ats/suggestions.py` + Tests (Regeln und Texte).
3. Analytics-Block mit Aktions-Buttons + Browser-Verifikation.
4. Einhängen im Fragen-Baukasten (Brücke zu L4).

## Danach

L2 (Bewerber-Steckbrief) und L4 (Editor-Hinweise) bauen auf denselben
Rechenkern auf. L3 (gelerntes A/B/C/D-Scoring) braucht zusätzlich die
Merkmals-/Label-Extraktion und die Messstrecke aus dem Kapitel oben — erst
sinnvoll, wenn L1 im Alltag läuft und genug Entscheidungen vorliegen.
