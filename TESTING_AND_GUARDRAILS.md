# Testen & Sicherheits-Wächter (Guardrails)

Dieses Dokument beschreibt das Sicherheitsnetz von SecurATS: **was geprüft wird,
warum, und wie es automatisch erneut läuft, sobald der Code geändert wird.**
Es ist die Antwort auf die Anforderung: *„Stelle sicher, dass die Tests und
Prüfungen auch in Zukunft durchgeführt werden, wenn ich den Code erweitere,
ergänze oder verändere."*

## TL;DR – so bleibt alles abgesichert

1. **Bei jeder Änderung lokal:** `python manage.py test` — rund tausend
   Testmethoden in etwa einer Minute (Stand 06.08.2026; die genaue Zahl steht
   am Ende jedes Laufs, sie hier zu pflegen hiesse, sie veralten zu lassen).
   Bis zum Laufzeit-Paket waren es 23 Minuten;
   die Zeit ging fast vollständig für Passwort-Hashes beim Anlegen von
   Testbenutzern drauf (siehe `ats/test_runner.py`). Eine Suite, die eine halbe
   Stunde braucht, wird vor dem Commit übersprungen — und schützt dann niemanden.
2. **Automatisch bei jedem Push / Pull Request:** GitHub Actions (`.github/workflows/ci.yml`)
   läuft die volle Suite auf **PostgreSQL** plus einen schnellen Wächter-Vorlauf.
3. **Beim Release-Tag `vX.Y.Z`:** `.github/workflows/release.yml` prüft Version/
   CHANGELOG-Konsistenz, läuft die Tests und baut das Image.

Du musst nichts manuell anstoßen – Erweiterungen und Umbauten werden automatisch
gegen dasselbe Netz geprüft.

## Zwei Arten von Tests

### 1. Normale Tests (prüfen konkretes Verhalten)
Tests über Funktionen, Views, Workflows, DSGVO-Anonymisierung,
Verschlüsselung, Audit-Kette usw. Sie fangen Regressionen in *bestehendem*
Verhalten. Details der Abdeckungs-Arbeit: `TEST_COVERAGE.md`.

### 2. Wächter-Tests / Guardrails (prüfen ganze FehlerKLASSEN)
Das Besondere für die Zukunft: Diese Tests prüfen **nicht einzelne Funktionen**,
sondern scannen die **gesamte Codebasis** bei jedem Lauf – auch Code, der erst
morgen dazukommt. So kann sich ein im Sicherheits-Audit gefundenes Muster nicht
unbemerkt wiederholen. Sie stehen in `ats/tests/test_guardrails.py`.

| Wächter | Verhindert die Wiederkehr von | Bezug |
|---------|------------------------------|-------|
| `GuardrailAuthDecoratorTestCase` | View ohne Auth-Decorator (jede neue View muss geschützt oder bewusst auf der Allowlist sein) | Audit-Fund 2 (`schedule_interview`) |
| `GuardrailNoCsrfExemptTestCase` | `@csrf_exempt` im Code | Audit (CSRF) |
| `GuardrailNoRawSqlTestCase` | rohes SQL / `.extra()` / `RawSQL` in Views | Audit (SQL-Injection) |
| `GuardrailProductionCacheTestCase` | prozess-lokaler Login-Lockout-Cache | Audit-Fund 6 (LocMemCache) |
| `GuardrailPostgresOnlyInProductionTestCase` | SQLite im Produktivbetrieb | Betriebs-Härtung |
| `GuardrailTemplateCommentTestCase` | mehrzeilige `{# … #}`-Kommentare (lecken als Text an Nutzer) | Portal-Fund N2 (bestätigt) |
| `GuardrailTableScrollTestCase` | Tabellen ohne Scroll-Wrapper (am Phone abgeschnitten) + mehrdeutige Wrapper-Schlüsse | Mobile-Audit M1 |
| `GuardrailPayTransparencyTestCase` (in `test_pay_transparency.py`) | Gehaltshistorien-Fragen in Screening-Fragen (Frageverbot EU-RL 2023/970) | E2 |
| `GuardrailAutocompleteTestCase` | PII-Felder ohne `autocomplete` in öffentlichen Formularen (WCAG 1.3.5 AA) | B2 |
| `GuardrailImgAltTestCase` | `<img>` ohne `alt`-Attribut, in ALLEN Templates (WCAG 1.1.1) | B-Nachtrag |
| `GuardrailFormLabelTestCase` | sichtbare Formularfelder der Bewerberstrecke ohne `label`/`aria-label` (WCAG 3.3.2) | B-Nachtrag |
| `GuardrailStandaloneTemplateTestCase` | Standalone-Templates ohne A11y-Fundament (`lang`, Skip-Link, `:focus-visible`) — die Fehlerklasse, durch die das Portal monatelang ohne Panel/Fokus war | B-Nachtrag |
| `GuardrailConsistentHelpTestCase` | Seiten ohne konsistenten Hilfe-Weg (Barrierefreiheitserklärung, KI-Transparenz) — auch in Standalone-Templates (WCAG 2.2 / 3.2.6) | C2 |
| `GuardrailNoDeadSettingsTestCase` | Bedienelement für eine Einstellung, die niemand liest — ein Versprechen ohne Funktion | U2 |
| `GuardrailNoOrphanRouteTestCase` | fertige Seite, zu der kein Link führt. Die häufigste Fehlerklasse des Projekts: gebaut, geschützt, getestet — und für niemanden erreichbar. Reine Maschinen-Endpunkte (Monitoring, Jobbörsen-Feeds) stehen in einer begründeten Allowlist | U3 |
| `GuardrailNoDeadModelTestCase` | Modell, das ausser im Django-Admin niemand anfasst. Registrierung ist keine Nutzung – dieser Fehlschluss hat sieben leere Prisma-Tabellen jahrelang durchgewunken, darunter das tote `User`-Modell, das den Urheber jeder Freigabe unbefuellbar machte | W1 |
| `GuardrailAdminPageInHubTestCase` | Admin-Seite, die nicht ueber die Einstellungs-Zentrale erreichbar ist. Aktionen/Exporte stehen mit Begruendung auf einer Ausnahmeliste, die selbst auf tote Eintraege geprueft wird | AA |
| `GuardrailIconButtonNameTestCase` | Knopf, der nur aus einem Symbol besteht, ohne `aria-label` - fuer Screenreader ein namenloser Knopf. Ein `title` genuegt nicht. Punkt 3 der Definition of Done stand seit Langem da; der Waechter dazu fehlte, und zehn Knoepfe waren namenlos | AE |
| `GuardrailNoTemplateNameGuessingTestCase` | `name__icontains` auf `EmailTemplate` — Vorlagen über ihren Namen zu suchen hiess: Umbenennen kippt den Versand still auf einen Text zurück, den niemand freigegeben hat. Der Zweck steuert, der Name beschriftet | AF |
| `GuardrailExceptionListsAreCheckedTestCase` | Ausnahmeliste ohne Prüfung auf tote Einträge. Von acht Listen prüften nur zwei, ob ihre Einträge überhaupt noch etwas treffen — eine tote Ausnahme ist eine offene Tür ohne Haus | AV |
| `GuardrailNoWeakHasherInSettingsTestCase` (in `test_laufzeit.py`) | schwacher Passwort-Hasher in `securats/*.py`. Die Abkürzung `if 'test' in sys.argv` würde die Passwortsicherheit der Produktion an eine Zeichenkette in der Kommandozeile hängen; der Test-Hasher gehört in `ats/test_runner.py`, den der Betrieb nie lädt | AH |
| `TransparenteStufeIstMerkmalsblindTestCase` (in `test_agg_golden.py`) | Merkmalsvektor des gelernten Scorings, der auf Name, Geschlecht, Alter, Behinderung, Religion oder Elternzeit-Lücke reagiert. Der Modul-Kopf von `scoring.py` sagt seit Langem zu, nur stellenrelevante Merkmale zu verwenden — geprüft hatte das niemand. Enthält eine Signalprüfung: erst zeigen, dass der Wächter überhaupt unterscheiden kann, dann Gleichheit verlangen | BN |
| `AlleFehlerseitenTestCase` / `FuenfhundertTestCase` (in `test_fehlerseiten.py`) | Fehlerseite ohne Weg zurueck (Sackgasse mit Stil) und eine 500-Seite, die `base.html` erbt, `static` braucht oder die Datenbank anfasst - sie scheitert dann genau in der Lage, fuer die sie gedacht ist. Prueft ausserdem, dass kein englischer Django-Text durchschlaegt | BV |
| `KeineFremdenAdressenInDenVorlagenTestCase` / `DiePolitikSchliesstFremdeQuellenAusTestCase` (in `test_sicherheits_header.py`) | Vorlage, die von einem fremden Server laedt, und jede CSP-Direktive, die eine fremde Herkunft oder `*` erlaubt. Die Air-Gap-Zusage war schon einmal gebrochen (Schriften von cdnjs/Google in `base.html`) - jetzt setzt der Browser sie durch, und der Waechter haelt die Politik eng | BU |
| `WaechterDeckungTestCase` / `LayoutRegelnTestCase` (in `test_mobil.py`) | Oeffentliche Seite, die nicht am Handy geprueft wird, und die vier Layout-Regeln, die den Ueberstand behoben haben. Die Messung selbst braucht einen echten Browser: `manage.py mobil_pruefen` (375 px, Exit-Code 1 bei Ueberstand). Gefunden hat sie u. a., dass „One-Click bewerben" am Telefon nicht anklickbar war | BS |
| `PruefsetIstBrauchbarTestCase` (in `test_agg_golden.py`) | AGG-Prüfset, dessen Varianten nebenbei auch die Qualifikation ändern — dann misst die Strecke Fachlichkeit statt Merkmal und besteht fröhlich weiter. Prüft zusätzlich, dass alle Merkmale nach § 1 AGG vertreten sind | BN |

**Wenn ein Wächter fehlschlägt:** Das ist ein *Feature*, kein Ärgernis. Nicht die
Whitelist blind erweitern – erst prüfen, ob der neue Code wirklich so sein soll:
- Auth-Wächter rot → fehlt ein `@recruiter_required` / `@hr_admin_required` /
  `@any_staff_required`? Ergänzen. Nur wenn die View **wirklich öffentlich** sein
  soll (wie die Stellenbörse), den Namen zur `PUBLIC_ALLOWLIST` hinzufügen.
- CSRF-/SQL-Wächter rot → fast immer ein echter Fehler.

Die Wächter beweisen sich **bei jedem Lauf** selbst: Alle Datei-Scans laufen
über zentrale Helfer (`projekt_dateien()` / `projekt_templates()`), die
anschlagen, wenn sie ins Leere sehen — ein Scan über null Dateien wäre grün
und wertlos. `GuardrailScansProveThemselvesTestCase` führt zusätzlich die
Funktionsprobe: Ein absichtlich leerer Baum löst den Alarm aus, ein
absichtlich kaputter Baum wird gefunden. (Früher stand hier ein einmaliger
Handnachweis aus der Entwicklung — der lief genau einmal.)

## Was in den drei Audit-/Test-Runden abgesichert wurde

- **Sicherheits-Audit:** 6 Funde behoben (Open Redirect, fehlender Auth-Decorator,
  fehlende BOLA-Checks, Demo-Seed-Backdoor, Login-Lockout, geteilter Lockout-Cache).
  Details: `SECURITY_AUDIT.md`. Jeder Fund hat einen Regressionstest **und**, wo
  sinnvoll, einen Wächter gegen die ganze Klasse.
- **Hochrisiko-Datenpfade:** DSGVO-Anonymisierung (unwiderruflich, per Cron) voll
  getestet – inkl. des subtilen Falls „Person mit laufender Zweitbewerbung bleibt
  identifizierbar". Bulk-Status ist kein BOLA-Schlupfloch.
- **KI-Schutzplanken (AI Act / AGG):** KI-Vorschläge werden nie zu K.O.-Kriterien;
  Prompt-Injection-Kapselung ist ausbruchsicher. 100 % abgedeckt.
- **Kryptografische Fundamente:** Audit-Hash-Kette erkennt Ändern und Löschen
  (Tail-Truncation als bewusste Grenze dokumentiert); Blind-Index ist ein
  schlüsselabhängiger HMAC; Fernet-Ciphertext ist nicht-deterministisch; PII
  liegt verschlüsselt at-rest.
- **Runde 4 – Persona-/Compliance-Pakete (M/R/S/P/N):** Mitbestimmung (§ 99
  BetrVG: Katalog-Grund-Pflicht, Wochenfrist, BetrVG-Gate am gelernten Scoring),
  Inklusion (§ 164 SGB IX: verschlüsselte Angabe, Widerruf, SBV-Mail ohne
  Gesundheitsdaten im Audit, Ciphertext-Altwert-Wächter `disability_value_disclosed`),
  Datenaufbewahrung (Frist-Leitplanken, Trockenlauf, § 164-Löschung),
  ROI-Export (nur Leitung, keine Namen), K.O.-Absage-Gründe (nie Ermessens-
  Begründungen), KI-Transparenz (dynamisch nach aktiven Funktionen),
  Interview-Leitfaden, Serien-Nachricht, „Mein Bereich" (Scope-Anzeige).

## Zusätzliche automatische Prüfungen in der CI

Über die Tests hinaus prüft `ci.yml` bei jedem Push/PR:
- **`makemigrations --check`** – schlägt fehl, wenn ein Modell geändert wurde, aber
  die Migration fehlt (verhindert „vergessene Migration" im Merge).
- **`check --deploy`** – Djangos Sicherheits-Checkliste für den Produktivbetrieb.
- **Volle Suite auf PostgreSQL** – dem Produktions-DB-Backend, damit die
  at-rest-Verschlüsselungs-Tests realistisch laufen.

## Barrierefreiheit bei JEDER Weiterentwicklung (Definition of Done)

Die Wächter oben fangen die statisch prüfbaren Fehlerklassen automatisch —
bei jedem Testlauf und in der CI. Was ein Scanner nicht sehen kann, ist
Pflicht-Checkliste für jedes neue Feature mit Oberfläche:

1. **Tastatur-Durchlauf:** Der neue Ablauf ist komplett ohne Maus bedienbar
   (Tab-Reihenfolge sinnvoll, Fokus sichtbar, kein Fokus-Gefängnis).
2. **Ansagen:** Asynchrone Zustandswechsel (Laden, Erfolg, Fehler, Zähler)
   haben eine `aria-live`-/`role="status"`-Region.
3. **Namen:** Icon-Buttons tragen `aria-label`; Umschalter `aria-pressed`
   bzw. `aria-expanded`; Deko-Icons `aria-hidden`.
4. **Kontrast:** Neue Farben gegen die Kontrast-Regeln prüfen (Text ≥ 4,5:1);
   KEINE seitenlokalen Überschreibungen zentral korrigierter Button-Farben.
5. **Zielgrößen:** Interaktive Elemente ≥ 24 px (WCAG 2.2), am Phone ≥ 44 px;
   Eingaben ≥ 16 px Schrift.
6. **Erklärung aktuell halten:** Ändert ein Feature den Stand der
   Barrierefreiheit, `templates/accessibility_statement.html` (bekannte
   Einschränkungen) und die BFSG-Zeile der `COMPLIANCE_MATRIX.md` nachziehen.

Maßstab: WCAG 2.1 AA heute, WCAG 2.2 AA mit EN 301 549 V4 (erwartet 2026/27) —
Details und Rechtslage in der Bewerberstrecken-Checkliste (Session-Artefakt)
und `ACCESSIBILITY_AUDIT.md`.

**WCAG-2.2-Stand (vorgezogen, damit EN 301 549 V4 kein Nachrüst-Projekt wird):**

| Kriterium | Umsetzung |
|---|---|
| 2.4.11 Focus Not Obscured | `scroll-padding-top` gegen den Sticky-Header; Sprungziele mit `scroll-margin-top` |
| 2.5.7 Dragging Movements | Datei-Upload und Kanban haben immer eine Klick-/Tastatur-Alternative zum Ziehen |
| 2.5.8 Target Size | Icon-Knöpfe und Karten-Verschieben ≥ 24×24 px überall (44 px am Phone), Checkboxen im Bewerbungsformular 24 px |
| 3.2.6 Consistent Help | Barrierefreiheit + KI-Transparenz in gleicher Reihenfolge im Footer **und** in beiden Standalone-Templates (Wächter) |
| 3.3.7 Redundant Entry | Formularwerte bleiben nach Fehlern erhalten; `autocomplete` an allen PII-Feldern |
| 3.3.8 Accessible Authentication | Kandidatenportal per Magic-Link ohne Passwort/Rätsel |
| 2.2.2 Pause, Stop, Hide | Vorlesen mit Pause/Weiter/Stopp; Animationen respektieren `prefers-reduced-motion` |

## Eine neue Prüfung ergänzen

Kommt eine neue FehlerKLASSE dazu, die dauerhaft ferngehalten werden soll:
1. In `ats/tests/test_guardrails.py` eine `Guardrail…TestCase` ergänzen,
   die die Codebasis scannt (Muster: die bestehenden Wächter kopieren).
2. In `ci.yml` im Job `guardrails` die Klasse zur Liste hinzufügen (optional –
   die volle Suite führt sie ohnehin aus).
3. Hier in der Tabelle dokumentieren.
