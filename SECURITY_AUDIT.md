# SecurATS – Sicherheits-Audit (Pentest & Bug-Hunt)

**Datum:** 2026-07-05 · **Prüfumfang:** Django-Backend (`ats/`), Settings, Templates,
Management-Commands · **Methodik:** manueller Code-Review entlang OWASP-Kategorien,
jeder Fund am echten Code verifiziert, Fixes mit Regressionstests abgesichert.
**Ergebnis:** 4 Funde behoben, 1 Härtungs-Empfehlung. **Teststand danach: 340 grün.**

---

## Zusammenfassung

| # | Fund | Kategorie | Schwere | Status |
|---|------|-----------|---------|--------|
| 1 | Open Redirect über `next`-Parameter | CWE-601 | Mittel | ✅ behoben |
| 2 | `schedule_interview` ohne Auth-Decorator | Broken Access Control | Hoch | ✅ behoben |
| 3 | `toggle_learning_sample` ohne BOLA-Scope | Broken Object Level Auth | Mittel | ✅ behoben |
| 4 | Demo-Seeds legen Backdoor-Konten ohne DEMO_MODE an | Insecure Defaults | Mittel–Hoch | ✅ behoben |
| 5 | Kein Brute-Force-Schutz am Login | Hardening | Niedrig | ⚠ Empfehlung |

---

## Fund 1 — Open Redirect (CWE-601) · Mittel · behoben

**Wo:** `save_interview_feedback`, `advance_interview_round` – beide leiteten mit
`redirect(request.POST['next'])` an einen ungeprüften Wert weiter.

**Risiko:** Eine präparierte Formular-/Link-Konstruktion könnte eine eingeloggte
Person nach `https://phishing.example` umleiten (Phishing/Token-Diebstahl).

**Fix:** Zentraler Helfer `_safe_next_url()` prüft das Ziel mit Djangos
`url_has_allowed_host_and_scheme` gegen den eigenen Host; nicht-lokale Ziele werden
verworfen und auf das interne Fallback geleitet. Regressionstest: externes `next`
wird ignoriert, internes akzeptiert.

## Fund 2 — Fehlender Auth-Decorator (Broken Access Control) · Hoch · behoben

**Wo:** `schedule_interview(request)` hatte KEINEN Decorator. Da es keine globale
Login-Middleware gibt (nur `AuthenticationMiddleware`, die nur `request.user` setzt),
war die View für jeden authentifizierten Nutzer aufrufbar – Interviews auf beliebige
Bewerbungen per ID anlegen, E-Mails auslösen, ohne Einrichtungs-Scope.

**Verifikation:** Vollständiger Scan aller `def view(request…)` bestätigte, dass
`schedule_interview` die EINZIGE eigentlich zu schützende View ohne Decorator war;
alle übrigen decorator-losen Views sind bewusst öffentlich (Jobbörse,
Bewerbungsformular, Kandidatenportal per Token, Health-Checks, Landingpages).

**Fix:** `@recruiter_required` + `can_access_application`-BOLA-Prüfung (404 außerhalb
des Scopes). Regressionstests: unauthentifiziert kein 200; fremder Scope → 404.

## Fund 3 — Fehlender BOLA-Scope (IDOR) · Mittel · behoben

**Wo:** `toggle_learning_sample` hatte `@recruiter_required`, aber keinen
`can_access_application`-Check – ein Recruiter konnte KI-Trainings-Feedback auf
Bewerbungen außerhalb seiner Einrichtung erzeugen (und dabei Anschreiben-Text kopieren).

**Fix:** `can_access_application`-Prüfung ergänzt (404 außerhalb des Scopes),
Regressionstest.

## Fund 4 — Demo-Seeds als Backdoor (Insecure Defaults) · Mittel–Hoch · behoben

**Wo:** `seed_demo` / `seed_demo_bank` legen Staff-Accounts mit festem Passwort
(`securats-demo-2026`) an. Nur `--reset` war durch `DEMO_MODE` geschützt – der
normale Seed-Pfad NICHT. Ein versehentlicher Lauf auf Produktion hätte
bekannte-Passwort-Logins mit Personalzugriff erzeugt.

**Wichtige Entwarnung:** Der Auto-Seed `seed_data_if_empty()` (läuft im Dashboard bei
leerer DB) legt KEINE login-fähigen Konten an – nur Stammdaten. Kein Auto-Backdoor.

**Fix:** Beide Seed-Commands verlangen jetzt am Anfang von `handle()` `DEMO_MODE=1`
(konsistent zum bestehenden `--reset`-Schutz), sonst `CommandError`. Nebenbei ein
`UnboundLocalError` in `seed_demo_bank` behoben (lokaler `settings`-Import nach
Verwendung). Regressionstests: beide Commands ohne DEMO_MODE → CommandError; keine
`demo-`Konten ohne expliziten Seed.

## Fund 5 — Kein Login-Brute-Force-Schutz · Niedrig · Empfehlung

Keine Ratenbegrenzung/Sperre bei wiederholten Fehllogins. Für den regulierten
Betrieb empfohlen: `django-axes` (Konten-/IP-Sperre nach N Fehlversuchen) plus
Reverse-Proxy-Ratelimit. Bewusst NICHT im Code umgesetzt (Paket + Migration +
Betriebsentscheidung); als Betriebs-/Hardening-Aufgabe dokumentiert.

---

## Was zusätzlich geprüft wurde – ohne Befund (gut)

- **SQL-Injection:** kein Raw-SQL, kein `.extra()`/`RawSQL`/`cursor()`. ORM durchgängig.
- **XSS (Server):** kein `|safe`, `mark_safe` oder `autoescape off`; Auto-Escaping aktiv.
  Der eine JSON-in-Modal-Pfad escaped clientseitig.
- **CSRF:** `CsrfViewMiddleware` aktiv, `@csrf_exempt` wird nirgends angewendet.
- **CORS:** aus Env, kein Allow-All, mit Warnkommentar; `CSRF_TRUSTED_ORIGINS` gekoppelt.
- **Secrets:** kein Secret im Repo (`.env.example` nur Platzhalter); Secret-Key- und
  PII-Key-Pflicht in Produktion erzwungen.
- **CV-Download:** `@recruiter_required` + BOLA + Audit-Log + `basename` (kein Traversal).
- **Datei-Upload:** Typ-Whitelist + Größenlimit VOR dem Anlegen; UUID-Präfix +
  Djangos `safe_join` verhindern Pfad-Traversal.
- **Session/Transport:** in Produktion `SESSION/CSRF_COOKIE_SECURE`, HSTS (1 Jahr,
  inkl. Subdomains), `SECURE_CONTENT_TYPE_NOSNIFF`.
- **Clickjacking:** `XFrameOptionsMiddleware` aktiv (Default `DENY`).
- **Passwörter:** MinimumLength- + CommonPassword-Validator aktiv.
- **Gefährliche Primitive:** kein `eval`/`exec`/`pickle`/`subprocess`/`os.system` mit
  Eingaben; `__import__` nur mit festen Modulnamen.
- **Toter Code:** keine verwaisten Modelle/Views; Migrationen konsistent.

---

## Behobene Nebensache

Doppelter `@recruiter_required`-Decorator auf `advance_interview_round` entfernt
(wirkungslos, aber unsauber).
