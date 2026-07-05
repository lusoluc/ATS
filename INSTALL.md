# SecurATS – Installation & Update

> Zielgruppe: IT-Admin ohne Vorkenntnisse dieses Projekts. Ziel (ROADMAP P0.1):
> **Installation + erstes Update in unter einem Tag, ohne Rückfragen.**
> Voraussetzungen: Linux-Host mit Docker ≥ 24 und Docker-Compose-Plugin, 4 GB RAM
> (8 GB mit KI-Profil), ausgehender Zugriff auf ghcr.io (oder Image-Datei per Hand).

## 1. Erstinstallation (ca. 15 Minuten)

```bash
git clone https://github.com/lusoluc/ATS.git securats && cd securats
cp .env.example .env
```

`.env` öffnen und **vier Werte** setzen (alles andere hat Defaults):

| Variable | Was |
|---|---|
| `DJANGO_SECRET_KEY` | langer Zufallswert, z. B. `openssl rand -base64 48` |
| `PII_ENCRYPTION_KEY` | langer Zufallswert – **verschlüsselt Bewerberdaten; Verlust = Datenverlust. Getrennt sichern!** |
| `POSTGRES_PASSWORD` | DB-Passwort (nur intern im Compose-Netz) |
| `SECURATS_ADMIN_USER` / `SECURATS_ADMIN_PASSWORD` | Erst-Admin (wird beim Start idempotent angelegt) |

Dann:

```bash
docker compose up -d
```

Das war die Installation. Der Start wartet auf die Datenbank, wendet Migrationen an,
sammelt statische Dateien ein und legt Rollen + Admin an.

**Prüfen:**
```bash
curl -s http://localhost:3000/healthz/
# → {"status": "ok" oder "degraded", "version": "1.0.0", ...}
# "degraded" ohne KI-Profil ist normal (KI nicht erreichbar, Kern läuft).
```
Login: `http://<host>:3000/recruiter/` mit dem Erst-Admin.

## 2. Update (der Ein-Befehl-Pfad)

```bash
docker compose pull && docker compose up -d
```

Migrationen laufen automatisch beim Start. Version prüfen: `curl -s localhost:3000/healthz/`.
Auf eine **feste Version pinnen** statt `latest`: in `.env` z. B. `SECURATS_VERSION=1.0.0`
setzen (empfohlen für Produktion; Update dann = Version hochsetzen + obiger Befehl).

**Vor jedem Update:** Backup (Abschnitt 4). **Rollback:** `SECURATS_VERSION` auf die
vorherige Version zurücksetzen, `docker compose up -d`, ggf. DB-Backup einspielen
(Migrationen sind vorwärtsgerichtet – Rollback braucht das Backup).

## 3. Lokale KI aktivieren (optional)

```bash
docker compose --profile ki up -d
docker exec securats-ollama ollama pull gemma2:9b
python_oder_container> python manage.py ai_doctor   # Diagnose
```
Dann in den SystemSettings `AI_MODEL` setzen. Das automatische Bewerber-Scoring
bleibt auch mit KI-Profil **aus**, bis `AI_SCORING_ENABLED=1` gesetzt wird
(bewusst, siehe OPERATIONS.md → AI Act).

## 4. Backup (Minimum)

```bash
docker exec securats-db pg_dump -U securats securats > backup-$(date +%F).sql
docker run --rm -v securats_media:/m -v $PWD:/out alpine tar czf /out/media-$(date +%F).tgz -C /m .
```
Plus: `.env` **getrennt** sichern (enthält `PII_ENCRYPTION_KEY`).
Details & Cron-Pläne: OPERATIONS.md.

## 5. Demo-Instanz betreiben (optional)

Fuer Interessenten-Gespraeche: eigene Instanz mit fiktiven Daten und
naechtlichem Reset.

```bash
# .env ergaenzen:
DEMO_MODE=1
DEMO_PASSWORD=<gespraechs-passwort>

docker compose up -d
docker compose exec web python manage.py seed_demo

# Naechtlicher Reset (Cron auf dem Host):
10 3 * * * docker compose -f /pfad/zu/securats/docker-compose.yml exec -T web python manage.py seed_demo --reset
```

Sichtbar: Demo-Banner auf jeder Seite; Logins `demo-admin` (Vollzugriff) und
`demo-recruiter` (sieht per BOLA nur Hamburg – gutes Live-Beispiel). Der
`--reset` ist ohne `DEMO_MODE=1` gesperrt und kann eine Produktions-DB nicht
leeren. Alle Demo-Personen sind fiktiv; KI-Scoring bleibt auch in der Demo aus.

## 6. Bestandsdaten uebernehmen

Bewerber aus dem Altsystem/Excel: als CSV exportieren und unter
`/recruiter/import/` einspielen – erst „Pruefen" (Testlauf, aendert nichts),
dann „Importieren". Vorlage und Formatdetails direkt auf der Seite.

## 7. Häufige Fragen

- **Port ändern:** `SECURATS_PORT=8080` in `.env`.
- **Ohne Docker / SQLite:** nur für Entwicklung – siehe README (venv + `manage.py runserver`).
- **„degraded" im Healthz:** KI nicht erreichbar oder Queue-Task fehlgeschlagen – Kern läuft; `ai_doctor` hilft.
- **Feeds absichern:** `FEED_ACCESS_TOKEN` in `.env` setzen.
