# Testen & Sicherheits-Wächter (Guardrails)

Dieses Dokument beschreibt das Sicherheitsnetz von SecurATS: **was geprüft wird,
warum, und wie es automatisch erneut läuft, sobald der Code geändert wird.**
Es ist die Antwort auf die Anforderung: *„Stelle sicher, dass die Tests und
Prüfungen auch in Zukunft durchgeführt werden, wenn ich den Code erweitere,
ergänze oder verändere."*

## TL;DR – so bleibt alles abgesichert

1. **Bei jeder Änderung lokal:** `python manage.py test` (≈ 6–7 Min, 396+ Tests).
2. **Automatisch bei jedem Push / Pull Request:** GitHub Actions (`.github/workflows/ci.yml`)
   läuft die volle Suite auf **PostgreSQL** plus einen schnellen Wächter-Vorlauf.
3. **Beim Release-Tag `vX.Y.Z`:** `.github/workflows/release.yml` prüft Version/
   CHANGELOG-Konsistenz, läuft die Tests und baut das Image.

Du musst nichts manuell anstoßen – Erweiterungen und Umbauten werden automatisch
gegen dasselbe Netz geprüft.

## Zwei Arten von Tests

### 1. Normale Tests (prüfen konkretes Verhalten)
396+ Tests über Funktionen, Views, Workflows, DSGVO-Anonymisierung,
Verschlüsselung, Audit-Kette usw. Sie fangen Regressionen in *bestehendem*
Verhalten. Details der Abdeckungs-Arbeit: `TEST_COVERAGE.md`.

### 2. Wächter-Tests / Guardrails (prüfen ganze FehlerKLASSEN)
Das Besondere für die Zukunft: Diese Tests prüfen **nicht einzelne Funktionen**,
sondern scannen die **gesamte Codebasis** bei jedem Lauf – auch Code, der erst
morgen dazukommt. So kann sich ein im Sicherheits-Audit gefundenes Muster nicht
unbemerkt wiederholen. Sie stehen in `ats/tests.py` (Abschnitt „WÄCHTER-TESTS").

| Wächter | Verhindert die Wiederkehr von | Bezug |
|---------|------------------------------|-------|
| `GuardrailAuthDecoratorTestCase` | View ohne Auth-Decorator (jede neue View muss geschützt oder bewusst auf der Allowlist sein) | Audit-Fund 2 (`schedule_interview`) |
| `GuardrailNoCsrfExemptTestCase` | `@csrf_exempt` im Code | Audit (CSRF) |
| `GuardrailNoRawSqlTestCase` | rohes SQL / `.extra()` / `RawSQL` in Views | Audit (SQL-Injection) |
| `GuardrailProductionCacheTestCase` | prozess-lokaler Login-Lockout-Cache | Audit-Fund 6 (LocMemCache) |

**Wenn ein Wächter fehlschlägt:** Das ist ein *Feature*, kein Ärgernis. Nicht die
Whitelist blind erweitern – erst prüfen, ob der neue Code wirklich so sein soll:
- Auth-Wächter rot → fehlt ein `@recruiter_required` / `@hr_admin_required` /
  `@any_staff_required`? Ergänzen. Nur wenn die View **wirklich öffentlich** sein
  soll (wie die Stellenbörse), den Namen zur `PUBLIC_ALLOWLIST` hinzufügen.
- CSRF-/SQL-Wächter rot → fast immer ein echter Fehler.

Die Wächter sind **selbst getestet**: In der Entwicklung wurde bewiesen, dass der
Auth-Wächter eine absichtlich ungeschützte View sofort meldet.

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

## Zusätzliche automatische Prüfungen in der CI

Über die Tests hinaus prüft `ci.yml` bei jedem Push/PR:
- **`makemigrations --check`** – schlägt fehl, wenn ein Modell geändert wurde, aber
  die Migration fehlt (verhindert „vergessene Migration" im Merge).
- **`check --deploy`** – Djangos Sicherheits-Checkliste für den Produktivbetrieb.
- **Volle Suite auf PostgreSQL** – dem Produktions-DB-Backend, damit die
  at-rest-Verschlüsselungs-Tests realistisch laufen.

## Eine neue Prüfung ergänzen

Kommt eine neue FehlerKLASSE dazu, die dauerhaft ferngehalten werden soll:
1. In `ats/tests.py` unter „WÄCHTER-TESTS" eine `Guardrail…TestCase` ergänzen,
   die die Codebasis scannt (Muster: die bestehenden Wächter kopieren).
2. In `ci.yml` im Job `guardrails` die Klasse zur Liste hinzufügen (optional –
   die volle Suite führt sie ohnehin aus).
3. Hier in der Tabelle dokumentieren.
