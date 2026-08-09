# SecurATS – Betriebs-Runbook (WP7)

> **Cache (sicherheitsrelevant):** Der Login-Lockout teilt seine Zähler über einen
> gemeinsamen Cache. In Produktion wird automatisch ein DB-Cache genutzt (die Tabelle
> `securats_cache` legt der Entrypoint via `createcachetable` idempotent an); mit
> gesetzter `REDIS_URL` wird Redis bevorzugt. Reiner Prozess-Cache (LocMemCache) nur
> in Entwicklung – er würde das Lockout-Limit pro Gunicorn-Worker vervielfachen.

Zielgruppe: IT-Admin (Persona Sven Ostermann). Alles läuft on-prem; keine Cloud-Abhängigkeit.

## 1. Komponenten

| Komponente | Zweck | Start |
|---|---|---|
| Django-App | Web/API | Docker-Compose (`docker compose up -d`) oder Gunicorn |
| PostgreSQL | **Produktions-DB** (Entscheidung WP7; SQLite nur Dev) | `POSTGRES_HOST` u.a. in `.env` setzen |
| Ollama | lokale KI | `ollama serve` + `ollama pull <modell>` |
| KI-Worker | Async-Queue (L6) | `python manage.py ai_worker --loop` (systemd/Container) |

## 2. Erst-Einrichtung

> **Standardweg ist Docker:** Installation & Ein-Befehl-Update siehe **INSTALL.md**
> (P0.1). Version der laufenden Instanz: `GET /healthz/` → Feld `version`.
> Der folgende manuelle Weg gilt fuer Entwicklung/Sonderfaelle.

```bash
cp .env.example .env            # Secrets setzen (SECRET_KEY, PII_ENCRYPTION_KEY!)
python manage.py migrate
python manage.py bootstrap_auth # Rollen-Gruppen + Admin (SECURATS_ADMIN_USER/PASSWORD)
python manage.py ai_doctor      # KI-Anbindung diagnostizieren (Erreichbarkeit/Modell/Latenz)
```

## 3. Wiederkehrende Jobs

**Im Docker-Betrieb ist nichts einzurichten.** Der Compose-Stapel enthält den
Dienst `scheduler`; er läuft ohne Profil mit und führt die fälligen Jobs aus.
Prüfen: `docker compose ps scheduler`, Zeitplan ansehen:
`docker compose exec web python manage.py scheduler --list`.

Bis zum Zeitplan-Paket stand hier nur der Cron-Vorschlag unten — und der
ausgelieferte Compose-Stapel enthielt keinen Zeitplan. Wer der
Installationsanleitung folgte, bekam **keinen** dieser Jobs, auch nicht die
Anonymisierung nach Fristablauf, die die Oberfläche als „automatisch" zusagt
(Art. 5 Abs. 1 lit. e DSGVO). Was zuletzt wirklich lief, steht unter
*Einstellungen → Wiederkehrende Jobs*.

### Ohne Docker: Cron-Einträge

```cron
# DSGVO-Retention: abgelehnte Bewerbungen > Frist anonymisieren (erst --dry-run testen)
15 2 * * *  cd /app && python manage.py data_retention --days 180

# Audit-Integrität prüfen (Hash-Kette) – Alarm bei Bruch
30 2 * * *  cd /app && python manage.py verify_audit

# Job-Alerts: neue Stellen matchen, versenden, verfallene Abos löschen (DSGVO)
0 8 * * *   cd /app && python manage.py send_job_alerts --hours 24
0 7 * * *   python manage.py send_interview_reminders   # Termin-Erinnerungen (24h-Fenster, einmalig je Interview)
30 3 * * *  python manage.py purge_talent_pool               # DSGVO: abgelaufene Pool-Einwilligungen loeschen (30 Tage Kulanz)
0 9 * * *   python manage.py send_feedback_requests            # Interviewer:innen an ausstehendes Interview-Feedback erinnern (einmalig je Gespräch+Person)
0 8 * * *   python manage.py send_decision_reminders          # Offene Freigaben, Gremien-Stimmen UND Stellenfreigabe-Ketten anmahnen (einmalig je Person+Vorgang, inkl. Vertretung)

# Leitungs-KPI-Report (Montag 07:00)
# Ohne --out geht der Bericht per Mail an alle HR-Admins; --out schreibt
# stattdessen eine Datei (eigene Verteilwege). Kann nicht zugestellt
# werden, endet das Kommando mit Fehler - ein Bericht ohne Empfaenger
# ist kein Erfolg.
0 7 * * 1   cd /app && python manage.py weekly_report

# KI-Golden-Set: BEWUSST nicht im scheduler-Dienst - er braucht eine
# erreichbare lokale KI, und ohne KI-Profil stuende der Job jede Woche
# rot. Nach Prompt-/Modellaenderungen von Hand starten; wer das
# KI-Profil produktiv betreibt, kann ihn als Host-Cron ergaenzen:
0 3 * * 0   cd /app && python manage.py ai_eval
```

Queue-Abarbeitung ohne Dauer-Worker (Alternative zu `--loop`):
```cron
*/2 * * * * cd /app && python manage.py ai_worker --once
```

## 4. Monitoring

- `GET /healthz/` – Gesamtstatus: DB, Media, KI-Erreichbarkeit, Queue-Tiefe
  (`200 ok/degraded`, `503 down`). Für Uptime-Checks geeignet.
- `GET /healthz/ai/` – nur KI-Anbindung inkl. „Modell gepullt?".
- Governance-Sicht `/recruiter/governance/` zeigt Hashketten-Status & Datenschutz-Kennzahlen.

## 5. Sicherheit & Compliance im Betrieb

- **Feeds**: `FEED_ACCESS_TOKEN` setzen → Stepstone/BA-Feeds verlangen Token (WP2).
- **Audit-Log**: append-only mit Hash-Kette; niemals Einträge editieren – `verify_audit`
  erkennt jede Manipulation.
- **Betroffenenauskunft**: `python manage.py export_applicant <email> --out auskunft.json`.
- **Vor Go-Live offen**: E-Mail-Blind-Index (deterministischer HMAC) für verschlüsselte
  E-Mail-Spalte – siehe COMPLIANCE_MATRIX.md.

## 6. KI-Betrieb (Ollama)

| Setting (SystemSetting) | Wirkung |
|---|---|
| `AI_SCORING_ENABLED` | **Automatisches Bewerber-Scoring (A–D) – Default AUS.** Opt-in-Modul; vor Aktivierung AI-Act-Einordnung prüfen (Hochrisiko-Bereich Beschäftigung). Ohne Aktivierung bleibt `aiScore` leer (ehrliche „–"-Anzeige, kein Platzhalter) |
| `AI_MODEL` | Modellwahl (z.B. `gemma2:9b` statt `gemma:2b` für mehr Denktiefe) |
| `AI_ASYNC` = `1` | Scoring über Queue statt synchron (nur relevant, wenn `AI_SCORING_ENABLED=1`) |
| `AI_TONE` | Tonalitäts-Overlay (SIE/DU/HERZLICH/NUECHTERN) – Guardrails unantastbar |
| `AI_TEMPERATURE`/`AI_NUM_CTX`/`AI_NUM_PREDICT` | Reasoning-Parameter (L5) |
| `SOURCE_COST_<KANAL>` | Kanalkosten → Kosten pro Einstellung in Analytics |
| `APPROVAL_SLA_DAYS` | Freigabe-Frist im Approval-Postfach |
| `APPROVAL_CHAIN` | Freigabekette für zustimmungspflichtige Einrichtungen (kommagetrennte Gruppennamen, Default „HR-Admin"); Gate aktivieren je Einrichtung via Admin-Checkbox `requiresApproval` |

Umgebung: `OLLAMA_HOST`, `OLLAMA_PORT`. Diagnose immer zuerst: `ai_doctor`.

## 7. Backup & Restore (PostgreSQL)

Die vorhandenen Skripte `infrastructure/backup-cron.sh` / `emergency-restore.sh`
setzen PostgreSQL voraus – mit der DB-Entscheidung (WP7) sind sie jetzt der
offizielle Weg. Zusätzlich sichern: `media/` (CVs/Nachweise) und `.env`
(insb. `PII_ENCRYPTION_KEY` – **ohne diesen Schlüssel sind PII-Spalten
unwiederbringlich verloren**; Schlüssel getrennt vom DB-Backup aufbewahren). **Schlüsselrotation:** Der
`PII_ENCRYPTION_KEY` dient auch als HMAC-Key des E-Mail-Blind-Index – bei Rotation
müssen alle `emailHash`-Werte neu berechnet werden (alle Applicants re-saven),
sonst schlagen E-Mail-Lookups fehl.


## HRIS-Export (optional)

`python manage.py hris_export` überträgt Bewerbungen im Status *Eingeladen* an ein
HRIS (z. B. SAP SuccessFactors).

- **Erfordert `HRIS_ENDPOINT`** (und optional `HRIS_TOKEN`). Ohne Endpunkt bricht der
  Befehl ab – er täuscht **keinen** Erfolg vor.
- `--dry-run` zeigt, welche Bewerbungen und welche Felder übertragen würden (ohne PII).
- `--all` überträgt auch bereits übertragene erneut (sonst überspringt er sie).
- **Datenschutz:** Der Export sendet personenbezogene Daten an ein Drittsystem.
  Auftragsverarbeitung klären, bevor der Endpunkt gesetzt wird.


## Datenbank: PostgreSQL – überall

**Entscheidung:** SecurATS läuft in Produktion **ausschließlich auf PostgreSQL**.
Ein Start mit SQLite bei `DEBUG=False` wird **hart abgelehnt** (verständliche
Fehlermeldung statt stiller Fehlfunktion).

**Warum so streng – aus Schaden gelernt:**

* Die Kluft „lokal SQLite / produktiv PostgreSQL" hat echte Fehler versteckt, die
  erst die CI auf PostgreSQL aufdeckte:
  * Hintergrund-Threads (KI-Prüfung) schlossen ihre DB-Verbindung nicht → unter
    PostgreSQL läuft der Verbindungspool leer (`too many clients`). SQLite verzeiht
    das klaglos – der Fehler wäre erst nach Wochen im Betrieb aufgefallen.
  * Roh-SQL mit camelCase-Spalten funktioniert nur auf SQLite (PostgreSQL faltet
    unquotierte Bezeichner auf Kleinbuchstaben).
  * Ein geschlossener Response schließt unter PostgreSQL die Verbindung – auf einer
    SQLite-In-Memory-DB ist `close()` ein No-Op.
* **SQLite sperrt bei parallelen Schreibzugriffen die gesamte Datei**
  (`database is locked`). Im Zielbetrieb (mehrere Recruiter + `ai_worker` + Cron
  gleichzeitig) ist das untragbar.
* Backups (`pg_dump`) und der Nebenläufigkeits-Schutz (`select_for_update`) setzen
  PostgreSQL voraus.

### Lokal auf PostgreSQL entwickeln (empfohlen)

Damit Entwicklung, Tests und Produktion **dieselbe** Datenbank nutzen:

```bash
# 1. PostgreSQL starten (nur lokal erreichbar)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db

# 2. Umgebung setzen (einmal pro Terminal)
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=securats
export POSTGRES_USER=securats
export POSTGRES_PASSWORD=securats

# 3. Wie gewohnt arbeiten – jetzt auf derselben DB wie die CI
python manage.py migrate
python manage.py test
python manage.py runserver
```

### SQLite

Nur noch für schnelle lokale Experimente mit `DEBUG=True`. In Produktion
verweigert SecurATS den Start; nur eine bewusste Ausnahme (`ALLOW_SQLITE=1`)
umgeht das – davon wird abgeraten.
