# Testabdeckung: Lücken geschlossen

**Ausgangslage:** 346 Tests, 82 % Gesamtabdeckung. Nach dem Views-Refactor
waren die blinden Flecken erstmals **domänenscharf** sichtbar.

**Ergebnis:** **377 Tests grün** (+31), Gesamtabdeckung **85 %**.

## Vorgehen: Risiko statt Prozente

Nicht die Prozentzahl war der Kompass, sondern die Frage: *Welche Views ruft
kein einziger Test auf?* Dort versteckt sich die nächste `schedule_interview`-
Lücke (fehlender Auth-Decorator, im Sicherheits-Audit gefunden). Eine
AST-/Coverage-Analyse fand **26 Views ohne jede Abdeckung**.

## Was abgedeckt wurde

| Modul | Vorher | Nachher | Neue Tests |
|-------|--------|---------|-----------|
| `views/ai.py` | 33 % | **51 %** | 12 |
| `views/settings_admin.py` | 58 % | **73 %** | 7 |
| `views/cms.py` | 71 % | **80 %** | 5 (mit `add_note`) |
| `views/applications.py` | 82 % | **85 %** | – |
| **Gesamt** | **82 %** | **85 %** | **+31** |

### Sicherheits-Befund am Rande (Entwarnung)
Alle bisher ungetesteten Admin-/Stammdaten-Views (`save_system_setting`,
`save_workflow_state`, `archive_category`, `archive_location`, …) sind
**korrekt mit `@hr_admin_required` geschützt** – keine zweite
`schedule_interview`-Lücke. Die neuen Tests sichern jetzt Funktion **und**
Autorisierung ab, damit ein künftiger Refactor den Schutz nicht still entfernt.

## Der wichtigste Teil: KI-Schutzplanken (AI Act / AGG)

`process_advisor.py` enthält die Regel *„KI-Vorschläge sind niemals
AGG-relevante Merkmale und niemals K.O.-Kriterien"* – eine
Antidiskriminierungs-Planke, die **komplett ungetestet** war. Ein späterer
„Verbesserer", der den `isMandatory`-Wert der KI durchreicht, hätte automatische
Absagen auf Basis KI-generierter Kriterien erzeugt: ein AI-Act- und AGG-Problem.

Jetzt **100 % abgedeckt** mit bewusst strengen Regressionstests:

- KI-Frage mit `isMandatory: true` wird serverseitig **hart entschärft**
  (weiche Frage, kein Auto-Reject) ✅
- Maximal 3 KI-Fragen, Längengrenzen (10–200 Zeichen) erzwungen ✅
- Fehlerhafte KI-Antworten (kein JSON, keine Liste, leer) → keine Fragen ✅
- KI nicht erreichbar → stiller Ausfall, keine Exception ✅
- `wrap_untrusted`: Prompt-Injection-Kapselung kann **nicht** durch
  eingeschleuste Marker (`<<<ENDE>>>`) ausgebrochen werden ✅

## Bewusst nicht getestet

`gemma_agg_check` läuft asynchron in einem Thread; Thread-Mocks werden schnell
flaky. Getestet sind stattdessen Eingangsvalidierung, Task-Anlage und
Status-Abfrage – der stabile, sicherheitsrelevante Teil.


---

## Runde 2: Hochrisiko-Datenpfade (DSGVO)

Nach denselben Prinzipien – nicht Prozente, sondern *Code, dessen Fehlverhalten
unwiderruflich ist*. Ergebnis: **387 Tests** (+10).

### DSGVO-Anonymisierung (`data_retention`) – war KOMPLETT ungetestet
Der gefährlichste ungetestete Code im Projekt: verändert Personendaten
unwiderruflich, löscht CV-Dateien von der Platte, läuft per Cron automatisch.
9 neue Tests sichern BEIDE Fehlerrichtungen:
- **Zu viel löschen:** aktive Bewerbung, Talent-Pool-Einwilligung und frische
  Absagen bleiben unangetastet (getestet).
- **Der subtilste Fall:** alte Absage bei Stelle A + laufendes Verfahren bei
  Stelle B → die alte Bewerbung wird anonymisiert, die **Person** bleibt aber
  identifizierbar, sonst verlöre das laufende Verfahren seinen Bewerber (getestet).
- **Zu wenig löschen:** Fristen greifen korrekt; abgelaufene Absagen ohne
  Einwilligung werden anonymisiert (DSGVO-Pflicht, getestet).
- CV-Datei wird real aus dem Dateisystem entfernt, nicht nur das DB-Feld geleert.
- Dry-Run ändert nichts; jede Anonymisierung ist auditiert.

### Bulk kein BOLA-Schlupfloch
`bulk_update_status`: eine Bewerbung außerhalb des Zugriffsbereichs wird in der
Sammel-Aktion übersprungen (0 Änderungen), nicht durchgewunken – Bulk umgeht den
Einzel-BOLA-Schutz nicht (getestet).

### Entwarnung
DSGVO-Export (Art. 15/20), Importer und Job-Alerts waren bereits solide getestet
(inkl. der Prüfung, dass interne Vermerke NICHT im Export landen). Die
Anonymisierung war die eine echte Hochrisiko-Lücke.


---

## Runde 3: Kryptografische Fundamente (Audit-Integrität + PII-Verschlüsselung)

Die beiden Fundamente, auf denen die DSGVO/KRITIS-Versprechen stehen. Beide waren
im Kern getestet – aber nicht in ihren *Sicherheitseigenschaften*. **396 Tests** (+9).

### Audit-Hash-Kette – über "Ändern" hinaus
Bestehend: Manipulation eines Eintrags wird erkannt. Ergänzt:
- **Löschen** eines mittleren Eintrags bricht die Kette (das häufigste
  Vertuschungsszenario, vorher ungetestet).
- **Ehrliche Grenze festgehalten:** Tail-Truncation (die letzten Einträge kappen)
  ist mit reiner Hash-Kette NICHT erkennbar – als Test dokumentiert, damit keine
  falsche Sicherheit entsteht. Schlägt der Test fehl, wurde ein Anker-Mechanismus
  ergänzt und die Doku muss nachziehen.
- Wiederherstellung nach Manipulation → wieder gültig (kein Fehlalarm-Rest).
- Legacy-Einträge ohne Hash brechen die Kette nicht, werden aber gezählt.

### PII-Verschlüsselung – die Krypto-Eigenschaften selbst
Bestehend: E-Mail liegt verschlüsselt at-rest (roher SQL-Check), Blind-Index trägt
Unique/Lookup. Ergänzt – als Wächter gegen spätere "Vereinfachungen":
- Blind-Index ist ein **schlüsselabhängiger HMAC**, kein reiner `sha256(email)`
  (sonst Wörterbuch-Angriff auf die Indexspalte möglich). Test schlägt an, falls
  jemand ihn zu einem einfachen Hash umbaut.
- Index **rotiert mit dem Schlüssel** (Beleg der Schlüsselbindung).
- Fernet-Ciphertext ist **nicht-deterministisch** (Zufalls-IV): gleicher Klartext →
  verschiedene Ciphertexte, sonst wären gleiche Werte aus der DB ablesbar.
- Auch das **Anschreiben** (Freitext-PII) liegt verschlüsselt at-rest, nicht nur die E-Mail.

### Entwarnung
Dokument-Downloads (Zeugnisse etc.) waren bereits BOLA-getestet (anonym → Redirect,
Recruiter → 200 + Audit; Dateiname aus DB, kein Pfad-Traversal). Kein Fund.

## Runde 4: Persona-/Compliance-Pakete (M, R, S, P1–P6, N1–N3) — 748 Tests

Mit den Persona-Paketen (Mobil, Mitbestimmung, Inklusion) und den Folgepaketen
wuchs die Suite von 396 auf **748 Testmethoden in 40 Dateien**. Neue Testmodule
mit Fokus:

| Datei | Tests | Deckt ab |
|---|---|---|
| `test_inklusion.py` | 16 | § 164 SGB IX: verschlüsselte Angabe, Widerruf im Portal, SBV-Mail ohne Gesundheitsdaten, Governance-Aggregate ab Anonymitätsschwelle, Ciphertext-Altwert-Wächter |
| `test_timeline.py` | 13 | Aktionsverlauf je Bewerbung/Stelle aus dem Audit-Log |
| `test_retention.py` | 12 | Frist-Leitplanken + Audit, Trockenlauf-Kriterien, Command-Default aus Setting, § 164-Löschung bei Anonymisierung |
| `test_mitbestimmung.py` | 10 | § 99 Abs. 2 BetrVG: Katalog-Grund-Pflicht, Wochenfrist, BetrVG-Gate am gelernten Scoring |
| `test_ko_absage.py` | 8 | K.O.-Gründe-Snapshot, Portal-/Mail-Anzeige, AGG-Wächter (nie Ermessens-Begründungen, interne Gründe nie durchgereicht) |
| `test_interview_guide.py` | 8 | Leitfaden je Stelle, Abdeckungs-Checkliste im Feedback |
| `test_roi_export.py` | 6 | ROI-/Inklusions-CSV: nur Leitung, Aggregate ohne Namen, Audit |
| `test_ai_transparency.py` | 6 | Art.-86-Seite: öffentlich, dynamisch je Setting, Verlinkungen |
| `test_series_message.py` | 5 | Serien-Nachricht: nur aktive Bewerbungen, Personalisierung, Audit je Person |
| `test_mein_bereich.py` | 4 | Scope-Block: nur für begrenzte Nicht-Admins, richtige Zählung |

Dazu Wächter-Zuwachs in `test_guardrails.py`: Tabellen-Scroll-Wrapper +
eindeutige Wrapper-Schlüsse (M1), mehrzeilige Template-Kommentare (bestätigt
durch einen echten Fund in N2).

## Runde 5: Durchgang „unerreichbare Funktionen" (U1–U6)

Der Durchgang stellte an jede Route, jede Einstellung und jedes Modellfeld
dieselbe Frage: *Kommt jemand da hin, und bewirkt es etwas?* Die Funde waren
selten kaputter Code – meistens fehlte die Tür. Deshalb prüfen die neuen Tests
bewusst die **Verlinkung und die Wirkung**, nicht nur die Erreichbarkeit einer
Route für sich.

| Datei | Tests | Deckt ab |
|---|---|---|
| `test_auskunft.py` | 22 | Art. 15/20: Inhalt der Auskunft (Anschrift, Absagegrund, Nachrichten, consentId, KI-Einordnung samt Tragweite, § 164 über `disability_value_disclosed`), Portal-Download nur mit gültigem Token und nur eigene Daten, HR-Knopf nur für HR-Admin, Audit je Erteilung; Art. 7 Abs. 1: gültige Fassung wird gespeichert, nichts erfunden, Governance benennt die Lücke |
| `test_tote_stellschrauben.py` | 18 | Seed legt keine ungelesenen Schlüssel mehr an, `OLLAMA_PORT` wirkt wirklich (inkl. `host:port` und Unsinn-Eingabe), Alt-Text erbt aus der Mediathek und wird nie leer, Standort-Koordinaten pflegbar (Komma erlaubt, unmögliche Werte verworfen), Freigabe-Urheber im Datenmodell **und** im Stellen-Verlauf, Freigabekette ohne den unerreichbaren dritten Pfad |
| `test_einstiege.py` | 9 | Verlinkung von Talent-Pool-Abgleich, Audit-CSV, Job-Alert, Lösch-Ansicht der Best-Performer-Profile und Dokumentenliste im Modal; Preisseite nur im DEMO_MODE |

Dazu zwei neue Wächter in `test_guardrails.py`: `GuardrailNoDeadSettingsTestCase`
(Schalter ohne Leser) und `GuardrailNoOrphanRouteTestCase` (Route ohne Einstieg).
