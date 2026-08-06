# SecurATS – Produkt-Roadmap 2026–2029

> **Revision Juli 2026 nach Premortem.** Diese Roadmap ersetzt die reine
> Feature-Steuerung (BUILD_PLAN.md, WP0–WP8 ✅ abgeschlossen) durch eine
> **validierungsgetriebene Steuerung**: Jede Phase hat ein Markt-Gate, das
> erreicht sein muss, bevor die nächste Ausbaustufe startet. Ziel bleibt:
> **50 produktive, zahlende Einrichtungen bis Mitte 2029.**

---

## 0. Kurswechsel – was diese Roadmap anders macht

Das Premortem (Juli 2026) hat sieben Scheiter-Gründe identifiziert. Der zentrale
Befund: **Alle sieben sind marktseitig, keiner ist featureseitig.** Das Produkt
war nie das Risiko – das Risiko sind Vertrieb, Beschaffungsfähigkeit, Betrieb
beim Kunden, AI-Act-Konformität, Geschäftsmodell, Marktgröße und Wechselkosten.

Daraus folgen vier verbindliche Prinzipien:

1. **Validierungs-Gates statt Feature-Gates.** Kein Ausbau-Paket startet, bevor
   das Markt-Gate der laufenden Phase erreicht ist. Feature-Arbeit ohne
   Gate-Bezug ist ab sofort die Ausnahme, nicht der Default.
2. **Personas sind Hypothesen.** Alle 22 Personas / 285 Use Cases sind
   Schreibtischarbeit (synthetisch). Sie steuern QA, aber **kein neues Feature
   wird mehr allein auf ihrer Basis priorisiert** – erst Interview-Evidenz
   (siehe USE_CASES.md, Validierungsstatus).
3. **Verkaufbarkeit schlägt Vollständigkeit.** Die nächsten Produkt-Investitionen
   sind die, die Verkaufsgespräche ermöglichen oder Deal-Killer entschärfen –
   nicht die, die die Compliance-Matrix noch grüner machen.
4. **Ehrliche Stopp-Regeln.** Die Kill-Kriterien (Abschnitt 6) sind Teil der
   Roadmap und werden nicht stillschweigend verschoben.

---

## 1. Phase V0 – „Beweis der Nachfrage" (Gespraechs-Teil auf 2027 verschoben)

**Gate für V1: 10 geführte Discovery-Gespräche mit echten Zielrollen**
(Pflegedienstleitung, HR-Leitung, IT-Leitung in Gesundheits-/Sozialträgern).

Produktarbeit in V0 ist strikt auf das beschränkt, was Gespräche ermöglicht
oder bekannte Deal-Killer entschärft:

| # | Paket | Premortem-Grund | Definition of Done |
|---|---|---|---|
| P0.1 ✅ | **Release- & Update-Pfad** – umgesetzt: SemVer (`securats/version.py` 1.0.0, im `/healthz/` sichtbar), CHANGELOG (Keep-a-Changelog), Produktions-Compose (Postgres, Healthchecks, optionales KI-Profil mit Ollama+Worker), Entrypoint mit Auto-Migration = Ein-Befehl-Update (`docker compose pull && up -d`), Release-Workflow (Tag → ghcr.io-Image + Konsistenz-Check + Tests), INSTALL.md fuer Fremd-Admins inkl. Rollback | #3 On-Prem-Betriebsfalle | ◐ DoD-Rest: realer Fremd-Admin-Test - **eingeplant fuer 2027** (Entscheidung Carlos, 05.08.2026) |
| P0.2 ✅ | **KI-Scoring per Default AUS** – umgesetzt: `AI_SCORING_ENABLED` (Default AUS), keine Platzhalter-Scores mehr (ehrliche „–"-Badges in Kanban & Modal), README/OPERATIONS/Matrix repositioniert auf „Assistenz, keine automatische Bewertung" | #4 AI-Act-Hypothek | ✅ erfüllt: frische Installation berührt die KI nachweislich nicht (`ScoringDefaultOffTestCase`) |
| P0.3 ✅ | **Preismodell-Hypothese + Preisseite** – umgesetzt: PRICING.md (Modell mit Begruendung, 50er-Ziel-Rechnung ~320 T€ ARR, Test-Protokoll mit Revisionsregel „≥ 4 gleichgerichtete Signale nach 10 Reaktionen"); Modell: Open-Source-Kern frei, Support-Abo je Einrichtung 390/690/990 €/Monat nach Hausgroesse + 2.900 € Einfuehrung, Design-Partner-Konditionen; oeffentliche Seite `/preise/` NUR auf der Demo-Instanz (Kunden-Karriereseiten zeigen keine Anbieterpreise – getestet: 404 ohne DEMO_MODE) | #5 Geschaeftsmodell | ◐ DoD-Rest: Preis in Gespraechen nennen + Reaktionen protokollieren (P0.6, dein Part) |
| P0.4 ✅ | **Demo-Instanz** – umgesetzt: `seed_demo`-Command (deterministische, fiktive Gesundheits-Demo: 7 Stellen inkl. Leichte-Sprache- und K.O.-Frage-Beispiel, 32 Bewerbungen ueber 90 Tage mit Anomalie-/Prognose-Material, offenes Freigabe-Gate, 2 Job-Alerts, BOLA-Demo-Logins), naechtlicher `--reset` NUR mit `DEMO_MODE=1` (Produktionsschutz, getestet), Demo-Banner auf jeder Seite, Betriebsanleitung in INSTALL.md | #1 kein Vertrieb | ◐ DoD-Rest: oeffentliches Hosting (Server + Domain) - **bewusst zurueckgestellt** (Entscheidung Carlos, 05.08.2026: nicht der aktuelle Fokus), Anleitung liegt bei |
| P0.5 ✅ | **CSV-Bewerberdaten-Import** – umgesetzt: `/recruiter/import/` mit Pflicht-Testlauf-Option (Dry-Run per Transaktions-Rollback garantiert aenderungsfrei), Duplikat-Erkennung ueber den E-Mail-Blind-Index, Zeilen-genauer Fehlerbericht, deutsche+englische Spaltenkoepfe, Komma/Semikolon/BOM (Excel-direkt), Status-Aliasse, Standard-Stelle fuer Zeilen ohne Stellenangabe, Vorlagen-Download, `DATA_IMPORT`-Audit | #7 Wechselkosten | ✅ erfuellt (`CsvImportTestCase`, 7 Tests) |
| P0.6 ◐ | **Interview-Programm** – Materialien fertig: INTERVIEW_LEITFADEN.md (30-Min-Struktur, Premortem-Hypothesen #2/#4/#6/#7 als Pruef-Fragen, woertlicher Preis-Test, Protokoll-Vorlage, Ablage `research/interviews/`) + versandfertiger Design-Partner-Onepager (PDF, 1 Seite). **Offen: die Gespraeche selbst** – 25 Kaltkontakte, 10 Gespraeche. **Termin auf 2027 verschoben** (Entscheidung Carlos, 05.08.2026): Bis dahin liegt der Fokus auf dem Produkt, nicht auf Vertrieb. Kill-Kriterium #1 bleibt, nur der Stichtag wandert | #1, Gegen-Check | Gate haengt jetzt ausschliesslich an gefuehrten Gespraechen |

**Explizit NICHT in V0** (on hold, siehe Abschnitt 5): i18n, visueller
Seiten-Builder (B16), OData, weitere Analytics-/Governance-Ausbauten.

---

## 2. Phase V1 – „Design-Partner" (Monat 3–9, bis Apr 2027)

**Gate für V2: 1–3 unterschriebene Design-Partner-Vereinbarungen**
(kostenlose begleitete Einführung gegen Referenz, Logo, monatliches Feedback).

| # | Paket | Premortem-Grund | Kern |
|---|---|---|---|
| P1.1 | **Persona-Validierung**: 15 strukturierte Interviews; jede Persona wird auf Basis von Zitaten bestätigt, korrigiert oder gestrichen; USE_CASES.md bekommt Evidenz-Spalte | Gegen-Check | Personas wechseln von „H" (Hypothese) auf „V" (validiert) oder fliegen |
| P1.2 | **Integrations-Shortlist AUS Interviews** – nicht aus Annahmen. Erwartete Kandidaten: Dienstplanung (Vivendi …), DATEV-/Lohn-Export, softgarden-/rexx-Import – aber gebaut wird erst nach V1-Evidenz | #7 | Priorisierte Liste mit Nennungs-Zählung je System |
| P1.3 | **Lieferanten-Readiness-Paket**: Rechtsform-Entscheidung (UG/GmbH oder Partner-Konstrukt), AVV-Muster, TOMs-Dokument, Supportvertrag mit SLA-Stufen, Antwortkatalog für Lieferantenfragebögen | #2 Einkauf | Ein vollständiger Lieferantenfragebogen eines Trägers ist beantwortbar |
| P1.4 | **AI-Act-Rechtsgutachten** (spezialisierte Kanzlei, Anhang-III-Einstufung des Scorings); danach Entscheid: Scoring als getrennt zertifizierbares Add-on weiterentwickeln oder dauerhaft entfernen | #4 | Schriftliche Ersteinschätzung liegt vor; Entscheidung dokumentiert |
| P1.5 | **Betriebsvarianten testen**: Self-hosted vs. „Managed On-Prem" über Partner-Systemhaus/MSP; in Design-Partner-Projekten beide Wege real durchspielen | #3, #6 | Aufwand je Variante gemessen (Stunden bis produktiv) |

---

## 3. Phase V2 – „Wiederholbarkeit" (Monat 9–18, bis Jan 2028)

**Gate für V3: 3 produktive Referenzinstallationen UND erster bezahlter Vertrag.**

| # | Paket | Kern |
|---|---|---|
| P2.1 | **Onboarding-Playbook** aus den Design-Partner-Einführungen (Checkliste, Zeitplan, Rollen) – Einführung wird von Projekt zu Produktprozess |
| P2.2 | **Top-2-Integrationen bauen** – ausschließlich die aus P1.2-Evidenz |
| P2.3 | **Zertifizierungs-Roadmap starten** (je nach Käufer-Feedback: ISO-27001-Vorbereitung oder BSI-orientierte Selbsterklärung mit Audit-Option) – Antwort auf „Testate statt Selbstauskunft" |
| P2.4 | **Referenzmaterial**: 2 Case Studies mit Zahlen (Time-to-Fill vorher/nachher), Zitate der Design-Partner |
| P2.5 | **Support-Betrieb formalisieren**: Ticketkanal, Reaktionszeiten, Update-Kadenz (monatlich), Security-Advisory-Prozess |

---

## 4. Phase V3 – „Skalierung Richtung 50" (Monat 18–36, bis Jul 2029)

**Ziel-Gate: 50 produktive, zahlende Einrichtungen.**

| # | Paket | Kern |
|---|---|---|
| P3.1 | **Partner-Vertrieb**: Systemhäuser und kirchliche/kommunale IT-Dienstleister als Multiplikatoren (löst Solo-Vertriebs-Engpass strukturell) |
| P3.2 | **EU-Cloud-Managed-Variante** – NUR falls V1/V2 zeigt, dass der harte On-Prem-Kern zu klein ist (#6). Architektur ist vorbereitet (Docker, Postgres, Env-Konfiguration); Positionierung bleibt „Daten in DEUTSCHER Infrastruktur, wahlweise bei Ihnen" |
| P3.3 | **Kür-Features nach Evidenz**: i18n, Builder, OData etc. – jedes nur mit Interview-/Kundennachfrage-Beleg |
| P3.4 | **Fachmessen-Präsenz** (Altenpflege, DMEA, ConSozial) ab verfügbarem Referenzmaterial |

---

## 5. Feature-Backlog – neu sortiert

| Item | Alter Status | Neuer Status | Gate zur Aufnahme |
|---|---|---|---|
| Release-/Update-Pfad (P0.1) | – (fehlte!) | **P0, sofort** | – |
| KI-Scoring Default-Off (P0.2) | Scoring an | **P0, sofort** | – |
| Preisseite/-modell (P0.3) | – (fehlte!) | **P0, sofort** | – |
| Demo-Instanz (P0.4) | – | **P0** | – |
| CSV-Import (P0.5) | – | **P0** | – |
| Integrationen (Dienstplan/Lohn/ATS-Import) | nicht geplant | **V2** | ≥ 3 Interview-Nennungen desselben Systems (P1.2) |
| i18n / Sprachumschaltung (UC-MN-11) | „Kür, als Nächstes" | **on hold → V3** | ≥ 3 Interviews/Kunden fordern es explizit |
| B16 visueller Seiten-Builder | „Kür" | **on hold → V3** | zahlender Kunde fordert es |
| OData-Endpoint | „Kür" | **on hold → V3** | Kunde mit konkreter BI-Anforderung (CSV-Export existiert) |
| Weitere Analytics-/Governance-Tiefe | laufend | **eingefroren** | Design-Partner-Feedback |
| Voice-Agent / telefonisches Vorscreening | – | **on hold → V3** | ≥ 3 Design-Partner-Nennungen UND bestandener ASR-Bias-Test (Akzent/Dialekt/L2; AGG) – Learning aus der AI-Voice-Agent-Studie 2026 |
| Compliance-Matrix-Pflege | laufend | läuft weiter (geringer Aufwand) | – |

**Begründung des Einfrierens:** Nicht, weil diese Features schlecht wären –
sondern weil jede Woche darin eine Woche ist, die keines der sieben realen
Risiken reduziert.

---

## 6. Kill-Kriterien (verbindlich, aus dem Premortem übernommen)

| Frist | Signal fehlt | Konsequenz |
|---|---|---|
| **2027** (verschoben von Okt 2026) | keine 10 Discovery-Gespräche mit Zielrollen | Feature-Stopp komplett; 100 % Zeit auf Zugang (Verbände, Messen, Partner) |
| **Jan 2027** (+6 Mon) | kein unterschriebener Design-Partner | Vertriebsmodell-Pivot: Vertrieb über Systemhaus/MSP statt direkt, oder Segmentwechsel |
| **Jul 2027** (+12 Mon) | < 3 produktive Referenzen ODER kein bezahlter Vertrag | 50er-Ziel beerdigen; SecurATS bewusst als Open-Source-Referenzprojekt weiterführen |

---

## 7. Messgrößen je Phase (Marktsignale statt Testanzahl)

- **V0:** geführte Gespräche (Ziel 10), Antwortquote Kaltkontakt, Demo-Aufrufe,
  Preisreaktionen („zu teuer/ok/zu billig"-Zählung).
- **V1:** unterschriebene Design-Partner (1–3), validierte Personas (Anteil),
  Integrations-Nennungen je System, beantwortbare Lieferantenfragebögen.
- **V2:** produktive Referenzen (3), erster Umsatz, Time-to-Productive je
  Einführung (Trend ↓), Update-Adoption der Bestandskunden (≤ 1 Release Rückstand).
- **V3:** zahlende Einrichtungen (kumuliert Richtung 50), Anteil Partner-Deals,
  Churn (Ziel 0 in dieser Größenordnung).

---

## 8. Verhältnis zu den übrigen Dokumenten

- **BUILD_PLAN.md**: historisches Bauprotokoll WP0–WP8 + Nachträge (abgeschlossen);
  neue technische Pakete werden künftig HIER (Roadmap) priorisiert und dort nur
  noch protokolliert.
- **USE_CASES.md**: QA-Instrument; Validierungsstatus der Personas siehe dortiges
  Banner. Ab V1 mit Evidenz-Verweisen je Persona.
- **NORTHSTAR.md**: Vision unverändert; offene Fragen #4/#5 sind mit dieser
  Revision entschieden (Deployment: Django direkt; Scope: EIN Segment zuerst –
  Pflege-/Sozialträger 300–2.000 MA in DACH).
- **OPERATIONS.md / COMPLIANCE_MATRIX.md / ACCESSIBILITY_AUDIT.md**: unverändert
  gültig; werden Verkaufsunterlagen-tauglich gepflegt (P1.3).

## Lücken-Backlog aus dem Prozess-Review (2026-07-04, priorisiert)

Quelle: Schritt-für-Schritt-Review Stelle→Kampagne→Bewerbung→Gremium→
Einladung→Einstellung mit Rückfragen. Reihenfolge = Nutzen für "schnell
besetzen" pro Aufwand.

**P0 – Bedienbarkeit & unmittelbare Prozess-Lücken**
1. ✅ Mindeststandard-Builder ohne JSON (Formular-Karten, alle 4 Fragetypen)
2. ✅ Fragetyp "Pflicht-Dokument" (Führerschein/Impfnachweis/Zertifikat) end-to-end
3. ✅ Einstellungsdatum manuell setzbar + nachträglich korrigierbar
4. ✅ Terminformate konfigurierbar (Verwaltungsseite statt Code-Liste)
5. ✅ Import: manuelle Spalten-Zuordnung (Vorschau "Spalte X → Feld Y",
   korrigierbar) + Adressfeld im Bewerber-Datensatz
6. ✅ Kanal-Kosten strukturiert am Kanal (Betrag + Zeitraum statt
   Freitext-Notiz/SystemSetting) → speist Kosten je Einstellung direkt

**P1 – Prozess-Tiefe (je ein sauberes Paket)**
7. ✅ Headcount je Stelle ("3 Stellen gleicher Art") + Auto-Hinweis/optionale
   Schließung bei erreichter Besetzung
8. ✅ Gremium: konfigurierbares Quorum (n von m) + Abstimmungs-Deadline
   (Erinnerung existiert; Deadline mit Eskalation fehlt)
9. ✅ Genehmigungspflicht VOR Veröffentlichung – umgesetzt als optionaler Stellenfreigabe-Prozess (Bedarf → mehrstufige Genehmigungskette → Ausschreibung; wenn aktiv, dann Pflicht)
10. ✅ Kampagnen-Ablaufdatum – Landingpage zeigt nach Ablauf eine freundliche Endseite (QR-tauglich), Kanal ordnet keine neuen Bewerbungen mehr zu; Pflege je Kanal/Landingpage
11. ✅ Mehrstufige Gesprächsrunden als formale Zustände – je Stelle definierbar, Einstellen erst nach Abschluss aller Runden, Fortschritts-Leiste + Korrektur auf der Termine-Seite

**Evidenz-Gates (erst mit Design-Partner-Bestätigung)**
- Frei konfigurierbare Status-Pipelines je Jobkategorie + Automatisierungs-
  Trigger ("bei Status X Mail Y") – größtes Paket, braucht echte Prozesse
  als Referenz
- CV-Parsing (Felder aus Lebenslauf), 1-Klick-Bewerbung LinkedIn/Xing
  (OAuth + DSGVO on-prem), Mehrfachbewerbung in einem Schritt
- A/B-Test zwischen Landingpage-Varianten
- Offboarding/Vertrags-Track nach Einstellung (bewusst außerhalb des
  ATS-Kerns)
- Voice-Agent / telefonisches Vorscreening: Die AI-Voice-Agent-Studie 2026
  zeigt, dass der Nutzen aus der STRUKTUR kommt (fester Leitfaden, kontrollierte
  Varianz) – die haben wir ohne Stimme umgesetzt (Interview-Leitfaden N1).
  Ein Sprachkanal kommt erst mit Design-Partner-Evidenz UND bestandenem
  ASR-Bias-Test: Spracherkennung diskriminiert messbar nach Akzent/Dialekt/
  Zweitsprache – für unsere Zielgruppe (internationale Pflegekräfte) ein
  AGG-Risiko, das vor jedem Pilot ausgeschlossen sein muss. Zusätzlich gilt
  Wahlfreiheit: ein Sprachkanal ist immer ein ANGEBOT neben Formular/Text,
  nie der einzige Weg.
