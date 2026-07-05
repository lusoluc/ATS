# SecurATS – Discovery-Interview-Leitfaden (P0.6)

> **Zweck:** 30-Minuten-Gespräche mit Pflegedienstleitung, HR-Leitung oder
> IT-Leitung in Gesundheits-/Sozialträgern. **Kein Verkauf** – Lernen. Jedes
> Gespräch prüft die Premortem-Hypothesen und den Preis. Direkt nach dem
> Gespräch: Protokoll (unten) ausfüllen, sonst ist die Hälfte weg.
>
> Faustregeln: 80 % zuhören. Nie das Produkt zuerst zeigen. „Erzählen Sie mir
> vom letzten Mal, als …" schlägt „Würden Sie …?" – Vergangenheit ist Fakt,
> Zukunft ist Höflichkeit.

---

## 0. Öffnung (2 Min)

- Dank + Rahmen: „30 Minuten, ich will nichts verkaufen. Ich baue Software für
  Recruiting im Gesundheitswesen und will verstehen, wie es bei Ihnen wirklich
  läuft – auch was nervt."
- Erlaubnis: „Darf ich mitschreiben?"

## 1. Ist-Zustand (8 Min) — *Persona-Validierung*

1. „Führen Sie mich durch die letzte Besetzung: von ‚Stelle frei' bis Zusage –
   wer macht was, mit welchen Werkzeugen?"
2. „Wie kommen Bewerbungen heute rein? (Portal / E-Mail / Papier / WhatsApp?)"
3. „Wie viele offene Stellen parallel? Wie lange dauert eine Besetzung typisch?"
4. „Wer außer HR ist beteiligt – Hiring-Manager, Betriebsrat, Datenschutz?
   Wo hakt die Zusammenarbeit?"

> *Abgleich (still, nicht vorlesen): Deckt sich das mit Sandra/Tobias/Petra aus
> USE_CASES.md? Zitate wörtlich notieren – sie sind die Evidenz (H→V).*

## 2. Schmerz & bisherige Lösung (7 Min) — *Hypothesen #6/#7*

5. „Was ist am heutigen Ablauf am teuersten – Zeit, Geld oder Nerven? Beispiel?"
6. „Was nutzen Sie heute (ATS/Excel/Outlook)? Was zahlen Sie dafür ungefähr?"
7. „Haben Sie schon mal gewechselt oder einen Wechsel verworfen? Warum?"
   → *Wechselkosten-Hypothese #7: Was war der Blocker? Datenübernahme? Schnittstellen?*
8. „Welche Systeme MÜSSTE ein neues Tool können? (Dienstplan, Lohn, …)"
   → *Integrations-Zählung für P1.2 – Systemnamen wörtlich notieren!*

## 3. Datenschutz & Beschaffung (6 Min) — *Hypothesen #2/#4/#6*

9. „Wo dürfen Bewerberdaten bei Ihnen liegen? Wäre EU-Cloud mit AVV okay, oder
   muss es ins eigene Haus?" → *Kernfrage Hypothese #6 – Antwort wörtlich!*
10. „Wie läuft bei Ihnen ein Software-Einkauf? Wer muss zustimmen, wie lange
    dauert das, gibt es Lieferantenfragebögen?" → *Hypothese #2*
11. „KI im Recruiting – was denkt Ihr Haus darüber? Gibt es Vorgaben von
    Betriebsrat oder Datenschutz?" → *Hypothese #4; NICHT mit Features antworten*

## 4. Preis-Test (3 Min) — *wörtlich so sagen (PRICING.md §4)*

> „Der Kern ist Open Source; Betrieb mit Support kostet je nach Hausgröße
> **390 bis 990 € im Monat**, plus **2.900 € Einführung** mit Datenübernahme
> und Schulung. Ganz ehrlich: Wie klingt das für Sie?"

Reaktion in EINE Kategorie: ☐ zu teuer ☐ ok ☐ zu billig/unseriös ☐ anderes Modell erwartet.
Nachfrage: „Womit vergleichen Sie das gerade?"

## 5. Abschluss (4 Min)

12. „Wenn Sie EINE Sache am Recruiting morgen ändern könnten – welche?"
13. Design-Partner-Angebot (Onepager schicken): „Ich suche 2–3 Häuser, die früh
    einsteigen – Einführung kostenlos, Support 12 Monate zum halben Preis, dafür
    ehrliches Feedback. Wäre das grundsätzlich interessant, oder kennen Sie ein
    Haus, für das das passt?"
14. Empfehlungsfrage: „Mit wem sollte ich unbedingt noch sprechen?" (Ziel: 1–2 Namen)
15. Dank + Zusage: kurze Zusammenfassung per Mail + Demo-Link.

---

## Gesprächsprotokoll (direkt danach, max. 10 Min)

```
Datum/Person/Rolle/Haus (Größe MA):
Heutiger Prozess (3 Sätze):
Heutige Tools + Kosten:
Top-Schmerz (Zitat!):
Wechsel-Blocker (Zitat!):
Genannte Pflicht-Integrationen:            ← P1.2-Zählung
On-Prem-Pflicht?  ☐ ja  ☐ EU-Cloud reicht  ☐ egal      ← Hypothese #6
Beschaffungsweg/Dauer/Fragebogen:                        ← Hypothese #2
KI-Haltung (Zitat!):                                     ← Hypothese #4
Preis-Reaktion:  ☐ zu teuer ☐ ok ☐ zu billig ☐ anderes Modell   (+Zitat)
Design-Partner-Interesse:  ☐ ja ☐ vielleicht ☐ nein
Empfehlungen (Namen):
Persona-Abgleich: bestätigt/korrigiert/widerlegt welche? (IDs)
Nächster Schritt + Datum:
```

**Ablage:** ein Protokoll pro Gespräch unter `research/interviews/YYYY-MM-DD-<haus>.md`
(Ordner ist angelegt). Ab 10 Protokollen: PRICING.md-Review und Persona-Status
in USE_CASES.md aktualisieren (H→V/†).
