# SecurATS – Datensouveränes Bewerbermanagementsystem

Eine voll integrierte, quelloffene Enterprise-Recruiting-Plattform mit höchsten
Ansprüchen an Datensicherheit, DSGVO-/KRITIS-Compliance und lokale KI.

> **Kosten:** Der Kern ist Open Source (Selbstbetrieb kostenlos). Betrieb mit Support und Einfuehrung: siehe [PRICING.md](PRICING.md).

## Autor & Urheber
**Carlos Lucas – Hamburg / Germany**
* [LinkedIn – Director IT Development](https://www.linkedin.com/in/director-it-development/)

## Stack (kanonisch)
SecurATS ist auf **einen** Stack konsolidiert:

- **Backend & UI:** Django 6 (App `ats`, Projekt `securats`, serverseitige Templates)
- **Datenbank:** SQLite (nur Entwicklung); PostgreSQL als zwingend erforderliche Produktions-Datenbank (siehe OPERATIONS.md)
- **Lokale KI:** Ollama / Gemma (Zero-Data-Transfer)
- **Betrieb:** Docker + docker-compose

Die früheren Parallel-Stacks **Next.js + Prisma** und **Express** wurden entfernt;
der Code liegt vollständig in der Git-History (Stand vor der Stack-Konsolidierung).
Hintergrund und Zielbild stehen in **`NORTHSTAR.md`**, die vollständige
Bestandsaufnahme in **`PROJECT_ANALYSIS.md`**.

## Projektstruktur
```
ats/            Django-App (Models, Views, Admin, Management-Commands)
securats/       Django-Projekt (Settings, URLs)
templates/      Serverseitige Templates (Career-Portal + Recruiter-Dashboard)
static/         Statische Assets
infrastructure/ Deploy-/Backup-/Restore-Skripte
NORTHSTAR.md    Vision, Personas, Funktionsumfang, Roadmap
PROJECT_ANALYSIS.md  Analyse & Befunde
```

## Schnellstart

### Mit Docker (empfohlen)
```bash
cp .env.example .env      # DJANGO_SECRET_KEY und PII_ENCRYPTION_KEY setzen
docker compose up -d --build
# Career-Portal: http://localhost:3000
```

### Lokal (Entwicklung)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Im Entwicklungsmodus (`DEBUG=True`) werden Dev-Fallback-Schlüssel genutzt; in
Produktion (`DEBUG=False`) sind `DJANGO_SECRET_KEY` und `PII_ENCRYPTION_KEY` Pflicht.

## Anmeldung & Rollen (RBAC)
Der Recruiter-/Admin-Bereich (`/recruiter/...`) erfordert Login. Rollen sind als
Django-Groups abgebildet: **HR-Admin**, **Recruiter**, **Hiring-Manager**, **Viewer**.
Ersten Admin und die Rollen anlegen:

```bash
SECURATS_ADMIN_USER=admin SECURATS_ADMIN_PASSWORD='<sicheres-passwort>' \
  python manage.py bootstrap_auth
```
Danach unter `/recruiter/login/` anmelden. Weitere Nutzer im Django-Admin anlegen
und der passenden Rollen-Group zuweisen. Das öffentliche Karriereportal bleibt frei
zugänglich.

## Features
- **Zero-Data-Transfer-KI (Assistenz, keine automatische Bewertung):** lokale KI via Ollama/Gemma unterstützt beim Formulieren (Tonalität, Leichte Sprache) und in der Datenanalyse – alles on-prem. Ein automatisches Bewerber-Scoring (A–D) existiert als **Opt-in-Modul** (`AI_SCORING_ENABLED`, Default AUS) und ist mit Human-in-the-Loop, Injection-Guardrails und Fairness-Monitoring abgesichert; vor Aktivierung EU-AI-Act-Einordnung prüfen (Hochrisiko-Bereich Beschäftigung).
- **Compliance:** DSGVO-Auto-Deletion (Cronjob), AGG-Checker, air-gap-fähig, PII-Verschlüsselung at-rest.
- **SAP-Integration:** SuccessFactors „Candidate-to-Employee"-Bridge mit visuellem Field-Mapper.
- **BA-XML-Export:** automatische Vakanzen-Einspeisung an die Arbeitsagentur.
- **CMS:** editierbare Seiteninhalte. *(Der frühere Puck-Drag-&-Drop-Builder war Teil des Next.js-Frontends und liegt in der Git-History; ein Nachbau in Django ist im Roadmap-Backlog.)*

## Automatische Löschung (Retention)
DSGVO-konforme Löschung/Anonymisierung läuft über das Management-Command:
```bash
python manage.py data_retention
```
Für den Produktivbetrieb per Cron einplanen, z.B. täglich:
```
0 3 * * * cd /app && python manage.py data_retention >> /var/log/securats-retention.log 2>&1
```

## Weiterentwicklung
Ziele, Personas, Funktionsumfang und die priorisierte Roadmap sind in
**`NORTHSTAR.md`** dokumentiert.
