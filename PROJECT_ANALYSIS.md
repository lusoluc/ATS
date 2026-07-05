# SecurATS – Projektanalyse & Befunde

> Stand: erste vollständige Durchsicht des Repositories `lusoluc/ATS`
> (historische Momentaufnahme aus der Drei-Stack-Aera – Django/Next.js/Express).
> Zweck: dokumentierte Bestandsaufnahme (Architektur, Qualität, Bugs, Sicherheit)
> als Grundlage für den North Star und die schrittweise Weiterentwicklung.
>
> **Hinweis (aktualisiert):** Die hier als offen markierte Kanon-Entscheidung
> ist getroffen (Django, siehe `NORTHSTAR.md` Abschnitt 6) und die
> Drei-Stack-Situation ist aufgelöst (Next.js + Express liegen vollständig in
> `legacy/`). Dieses Dokument bleibt als historischer Befund-Katalog stehen;
> für den aktuellen Stand siehe `NORTHSTAR.md` und `BUILD_PLAN.md`.

---

## 1. Methodik

Das Repository wurde geklont, das Django-Backend lokal lauffähig gemacht
(`manage.py check`, `migrate`, `test` laufen grün), und die kritischen Annahmen
wurden mit echten Reproduktionen belegt (z.B. Ciphertext-Längenmessung,
Lookup-Verhalten der verschlüsselten Felder). Das Next.js-Frontend und die
`src/`-Ebene wurden statisch gelesen (kein Full-Build ausgeführt).

---

## 2. Architektur, wie vorgefunden

Das Repo enthält **drei überlappende Implementierungen desselben Systems**, die
sich (über `DATABASE_URL`) dieselbe SQLite-Datenbank teilen:

| Stack | Ort | Rolle | Auth |
|---|---|---|---|
| **Django 6** | `ats/`, `securats/`, `templates/` | Vollständiges Backend + serverseitige Templates (Career-Portal + Recruiter-Dashboard) | **keine** |
| **Next.js 16 / React 19 + Prisma** | `frontend/` (33 API-Routen, `/admin`, öffentliche Seiten) | Vollständige Full-Stack-App, spricht **direkt per Prisma** auf die DB | zentrale Middleware (`/admin`, `/api/cms`), aber schwach |
| **Express / TypeScript** | `src/` (JWT, bcrypt, Middlewares, Worker) | Dritte Backend-Ebene (auth/bola/role, Retention/HRIS-Worker) | JWT + bcrypt (am ehesten „korrekt") |

Zusätzlich:
- **Prisma-Schema** (`frontend/prisma/schema.prisma`, 41 Modelle) und **Django-Modelle**
  (`ats/models.py`) beschreiben **dieselbe** Datenbank doppelt. Die Django-Felder
  sind 1:1 aus dem Prisma-Schema portiert (camelCase, `createdAt`/`updatedAt`).
- Ein Management-Command `migrate_prisma_data.py` deutet auf Datenmigration
  zwischen den Welten hin.

**Kernproblem der Architektur:** Es gibt keine eindeutige „Source of Truth".
Datenmodell, Auth, Seeding, AI-Anbindung und Retention existieren in mehreren
Stacks parallel und teils widersprüchlich. Die projekteigenen Dokumente
(`AI_DEV_GUIDELINES.md`, `System_Architektur_und_Feature_Katalog.md`) erklären
**Next.js + Prisma** zum kanonischen Stack – der Nutzer bezeichnet jedoch das
**Django-Projekt** als „sein Projekt". Dieser Widerspruch ist die wichtigste
offene Entscheidung (siehe North Star).

---

## 3. Befunde nach Schweregrad

Status-Legende: ✅ behoben · 🟡 empfohlen (Entscheidung/Umbau nötig) · 📝 notiert

### 3.1 Kritisch

| # | Befund | Ort | Status |
|---|---|---|---|
| C1 | **Verschlüsselte Felder sprengen die Spaltenlänge.** Fernet-Ciphertext ist viel länger als der Klartext (5 Zeichen → 100, 50 Zeichen → 164). `firstName/lastName` sind `max_length=100`, `phone` `max_length=50`. SQLite ignoriert das; auf PostgreSQL/MySQL schlägt jedes INSERT mit realistischen Werten fehl → Datenverlust beim Produktionsumzug. | `ats/models.py` | ✅ Spalte jetzt `TEXT` (`get_internal_type`), Klartext-`max_length` bleibt für Formvalidierung. Verifiziert mit 38-Zeichen-Name. |
| C2 | **Keine Authentifizierung auf den Django-Recruiter-Views.** `/recruiter/dashboard/` zeigt alle Bewerber-PII entschlüsselt; alle CRUD-Endpunkte verändern Daten ohne jede Prüfung. | `ats/views.py` (alle Views) | 🟡 Abhängig von Deployment-Topologie; Fix = Auth-Layer (Roadmap). |
| C3 | **Frontend-Login = ein geteiltes Demo-Passwort** (`securats2024`), Cookie speichert nur den Rollen-String (nicht signiert). Middleware prüft nur *Vorhandensein* des Cookies. | `frontend/src/app/api/auth/login/route.ts`, `frontend/src/middleware.ts` | 🟡 Als Platzhalter markiert; echte Auth = Roadmap. |
| C4 | **Öffentlich im Repo stehende Fallback-Krypto-Keys** (`PII_ENCRYPTION_KEY`, `STORAGE_ENCRYPTION_KEY`, `SECRET_KEY`). Wer sie kennt, kann PII entschlüsseln bzw. Sessions fälschen. | `securats/settings.py`, `frontend/src/lib/encryption.ts` | ✅ In Produktion (`DEBUG=False` / `NODE_ENV=production`) werden Keys jetzt erzwungen; dev behält Fallback. |

### 3.2 Hoch

| # | Befund | Ort | Status |
|---|---|---|---|
| H1 | **Suche/Filter auf verschlüsselten Feldern liefert immer 0 Treffer** (Fernet nicht-deterministisch). | `ats/models.py`, Admin-Suche | ✅ Einschränkung dokumentiert; wenn Namenssuche gebraucht wird → verschlüsselter Blind-Index nötig (Roadmap). |
| H2 | **`@csrf_exempt` auf 18 zustandsändernden Django-Endpunkten** – CSRF-Schutz deaktiviert. | `ats/views.py` | 🟡 An echte CSRF-Token / API-Auth koppeln (Roadmap). |
| H3 | **`ALLOWED_HOSTS=['*']` + `CORS_ALLOW_ALL_ORIGINS` + `CORS_ALLOW_CREDENTIALS`** – unsichere Kombination (Browser lehnen sie ohnehin ab). | `securats/settings.py` | ✅ Env-Allowlist, feste CORS-Origins, Secure-Cookies/HSTS in Prod. |
| H4 | **`DEBUG` default `True`.** | `securats/settings.py` | ✅ Env-gesteuert, Prod erzwingt Keys. |
| H5 | **Zwei verschiedene Krypto-Verfahren** (Django Fernet vs. Frontend AES-256-GCM) auf demselben Datenbestand – keine Interop, inkonsistente PII-Strategie. `Applicant.email` ist gar nicht verschlüsselt. | stack-übergreifend | 🟡 Vereinheitlichung = North-Star-Entscheidung. |

### 3.3 Mittel

| # | Befund | Ort | Status |
|---|---|---|---|
| M1 | **`seed_data_if_empty()` läuft bei jedem `home`/`dashboard`-Request** und seedet Mock-Daten in den Request-Pfad. | `ats/views.py` | 📝 Nach Management-Command/Fixture verlagern. |
| M2 | **Ollama-Socket-Check bei jedem Dashboard-Load** (2 s × 2 Hosts → bis 4 s Latenz). | `ats/views.py:dashboard` | 📝 Cachen / asynchron / Health-Endpoint. |
| M3 | **Async-KI über rohe `threading.Thread` + `AuditLog` als Task-Store** – Threads sterben bei Worker-Neustart; AuditLog wird als Queue missbraucht. | `ats/views.py` (agg_check, validate) | 📝 Echte Task-Queue (Celery/RQ) oder synchron mit Timeout. |
| M4 | **CV-Upload ohne Typ-/Größenprüfung**; Dateiname fließt (nach UUID-Prefix) in den Storage-Pfad. | `ats/views.py:bewerben` | 🟡 Content-Type/Größe/Endung validieren. |
| M5 | **Erfundene Kennzahl in der UI:** `honeypot_spam_count = 14` als „High-fidelity metrics fallback". | `ats/views.py:dashboard` | 📝 Entfernen – echte Zahl oder 0 zeigen. |
| M6 | **Doc-vs-Realität-Lücke:** Docs versprechen Magic-Link-Auth, RBAC, BOLA überall, DOMPurify, HSTS, manipulationssicheres Audit-Log. Im Code nur teilweise umgesetzt. | Docs vs. Code | 📝 Im North Star ehrlich als Ist/Soll führen. |

### 3.4 Niedrig

| # | Befund | Ort | Status |
|---|---|---|---|
| L1 | **Stilles `except Exception: pass`** verschluckt Fehler. | `ats/views.py:update_status` | ✅ Durch `logger.exception` ersetzt. |
| L2 | **DOM-XSS-Restfläche:** Screening-Fragen per `innerHTML` mit `${q}` eingefügt (nur Recruiter-Content, niedrig). | `templates/dashboard.html` | ✅ `escapeHtml()` ergänzt. |
| L3 | **Ungenutzte Dependencies:** `djangorestframework` (nicht in `INSTALLED_APPS`), `requests` (bewusst durch `urllib` ersetzt). | `requirements.txt` | 📝 Aufräumen. |
| L4 | **Große Binärartefakte im Repo** (`hr-ba-xml.zip` 610 KB, mehrere PNGs, `e2e-test-report.json`). | Repo-Root | 📝 Nach Bedarf in Releases/LFS auslagern. |

---

## 4. Was bereits umgesetzt & verifiziert ist

Alle risikoarmen, entscheidungsfreien Fixes sind implementiert (siehe Patch
`securats-backend-fixes.patch` plus die Folgeänderungen):

- `ats/models.py`: TEXT-Spalten für verschlüsselte Felder (kein Überlauf mehr).
- `securats/settings.py`: Key-Zwang in Prod, Env-Allowlist, sichere CORS/Cookies/HSTS.
- `ats/views.py`: Fehler-Logging statt `pass`, Logging-Setup.
- `templates/dashboard.html`: HTML-Escaping der Screening-Fragen.
- `frontend/src/lib/encryption.ts`: Key-Zwang in Produktion.

Verifikation: `manage.py check` & Testsuite grün; Prod-Start ohne Keys bricht mit
klarer Meldung ab; Round-Trip langer Namen erfolgreich.

---

## 5. Was bewusst NICHT „einfach gefixt" wurde

Der Auftrag „fixe alle Bugs" lässt sich für dieses Repo nicht verantwortungsvoll
als „alles blind umbauen" umsetzen. Mehrere zentrale Punkte sind **Design-
Entscheidungen**, keine isolierten Bugs:

1. **Drei-Stack-Duplikation auflösen** (Django vs. Next.js vs. Express) – braucht
   die Kanon-Entscheidung aus dem North Star.
2. **Ein echtes Auth-/RBAC-Modell** (statt Demo-Passwort / keiner Auth) – hängt an
   (1) und ist Roadmap-Arbeit.
3. **PII-Krypto vereinheitlichen** – hängt an (1).

Diese Punkte sind im North Star als priorisierte Roadmap abgebildet.
