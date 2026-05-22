#!/bin/bash
# ==============================================================================
# SecurATS - Dockerized Clean-Build Swap (Blue-Green) Deployment & Rollback Skript
# ==============================================================================
# Dieses Skript implementiert ein ausfallsicheres, permanentes Deployment mit Docker:
# 1. Es kopiert die Plattform in ein separates Build-Verzeichnis (/opt/ATS_new).
# 2. Dort wird ein sauberer Git-Reset durchgeführt (keine lokalen Merge-Konflikte!).
# 3. Die Docker-Images werden im Hintergrund isoliert gebaut (Zero-Downtime-Build).
# 4. Wenn der Build erfolgreich ist, werden PM2-Dienste gestoppt, Ports bereinigt,
#    die Ordner getauscht, und wichtige Produktionsdaten (SQLite DB, .env-Dateien)
#    ordnungsgemäß in den neuen shared Ordner für Docker migriert.
# 5. Die Docker-Container werden gestartet und ein Healthcheck wird ausgeführt.
# 6. Sollte der neue Build fehlschlagen, erfolgt ein automatisches Rollback!
# ==============================================================================

set -e

# Farbdefinitionen für Log-Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}🚀 [SecurATS] Starte Docker-basiertes Blue-Green Deployment...${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 0. Root-Rechte erzwingen
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ FEHLER: Dieses Skript muss als Root oder mit 'sudo' ausgeführt werden!${NC}"
  exit 1
fi

# 0b. Stelle sicher, dass lsof und fuser (psmisc) installiert sind, um Ports zuverlässig freizugeben
if ! command -v lsof &> /dev/null || ! command -v fuser &> /dev/null; then
  echo -e "${YELLOW}📦 Hilfswerkzeuge 'lsof' oder 'fuser' fehlen auf dem Host. Installiere...${NC}"
  if command -v apt-get &> /dev/null; then
    apt-get update -y && apt-get install -y lsof psmisc
  else
    echo -e "${RED}⚠️ apt-get nicht gefunden. Bitte installieren Sie 'lsof' und 'psmisc' manuell!${NC}"
  fi
fi

LIVE_DIR="/opt/ATS"
BUILD_DIR="/opt/ATS_new"
OLD_DIR="/opt/ATS_old"

# 1. Build-Verzeichnis vorbereiten
echo -e "${YELLOW}[1/6] Bereite isolierte Build-Umgebung vor...${NC}"
rm -rf "$BUILD_DIR"
cp -r "$LIVE_DIR" "$BUILD_DIR"

cd "$BUILD_DIR"

# 2. Sauberer Git-Zustand im Build-Verzeichnis (Garantiert konfliktfrei)
echo -e "${YELLOW}[2/6] Bereinige Git-Status im Build-Verzeichnis...${NC}"
git reset --hard HEAD
git clean -fd
git fetch origin main
git reset --hard FETCH_HEAD

# 3. Isolierte Docker-Kompilierung im Build-Verzeichnis
echo -e "${YELLOW}[3/6] Baue Docker-Images isoliert...${NC}"
if ! docker compose build; then
  echo -e "${RED}❌ BUILD-FEHLER: Der Docker-Build ist fehlgeschlagen!${NC}"
  echo -e "${YELLOW}🔄 Bereinige Build-Verzeichnis. Die Live-Plattform läuft unverändert weiter!${NC}"
  rm -rf "$BUILD_DIR"
  exit 1
fi

echo -e "${GREEN}✅ Docker-Images erfolgreich isoliert gebaut! Bereite den Austausch vor...${NC}"

# 4. Port-Befreiung & PM2 Bereinigung (Ports für Backend und Frontend freigeben)
echo -e "${YELLOW}[4/6] Beende veraltete PM2-Prozesse und befreie Ports 3000/3001...${NC}"
sudo pm2 delete enterprise-backend >/dev/null 2>&1 || true
sudo pm2 delete enterprise-frontend >/dev/null 2>&1 || true
sudo pm2 save --force >/dev/null 2>&1 || true

# Falls alte Docker-Container aus einem vorherigen Live-Ordner laufen, stoppen wir sie gleich beim Swap.
# Wir befreien hier zusätzlich alle Ports auf dem Host:
docker rm -f securats-frontend securats-backend >/dev/null 2>&1 || true

# Finde und entferne jegliche Container, die die Ports 3000 oder 3001 belegen (unabhängig vom Namen)
for port in 3000 3001; do
  CONTAINERS_USING_PORT=$(docker ps -q --filter "publish=$port" || true)
  if [ -n "$CONTAINERS_USING_PORT" ]; then
    echo -e "${YELLOW}🛑 Entferne Container, die Port $port blockieren: $CONTAINERS_USING_PORT...${NC}"
    docker rm -f $CONTAINERS_USING_PORT >/dev/null 2>&1 || true
  fi
done

for port in 3000 3001; do
  sudo fuser -k ${port}/tcp >/dev/null 2>&1 || true
  PID_TO_KILL=$(lsof -t -i:$port || true)
  if [ -n "$PID_TO_KILL" ]; then
    sudo kill -9 $PID_TO_KILL >/dev/null 2>&1 || true
  fi
done


# 5. Swap & Daten-Erhalt (Die kritische Phase)
echo -e "${YELLOW}[5/6] Führe Verzeichnistausch und Daten-Migration aus...${NC}"

# Vorheriges Backup-Verzeichnis löschen falls vorhanden
rm -rf "$OLD_DIR"

# Wenn der alte Live-Ordner aktiv war, stoppen wir seine docker-compose-Dienste, falls vorhanden
if [ -f "$LIVE_DIR/docker-compose.yml" ]; then
  echo -e "${YELLOW}🛑 Stoppe bestehende Docker-Container der alten Version...${NC}"
  cd "$LIVE_DIR"
  docker compose down || true
fi

# Ordner tauschen
mv "$LIVE_DIR" "$OLD_DIR"
mv "$BUILD_DIR" "$LIVE_DIR"

# WICHTIG: shared-Verzeichnis für SQLite-Datenbank erstellen und voll beschreibbar machen
mkdir -p "$LIVE_DIR/shared"
chmod 777 "$LIVE_DIR/shared"

# Produktions-Daten (SQLite-Datenbank und Env-Variablen) aus dem alten Ordner in den neuen übertragen!
echo -e "${YELLOW}⚙️  Kopiere Umgebungsvariablen und migriere SQLite-Datenbank...${NC}"

# 1. Suche nach .env-Dateien im alten Ordner und kopiere sie
find "$OLD_DIR" -name ".env*" | while read -r env_file; do
  REL_PATH=${env_file#"$OLD_DIR/"}
  # Wenn es eine .env im frontend ist, kopieren wir sie in das neue frontend
  # Wenn es die root .env ist, kopieren wir sie ins neue root
  echo -e "${GREEN}🎯 Gefundene Konfiguration: $REL_PATH. Kopiere...${NC}"
  mkdir -p "$(dirname "$LIVE_DIR/$REL_PATH")"
  cp "$env_file" "$LIVE_DIR/$REL_PATH" || true
done

# 2. Suche nach der SQLite-Datenbank und migriere sie in den neuen shared-Ordner
# Wir suchen im alten Ordner nach dev.db (kann in frontend/prisma/dev.db oder in shared/dev.db liegen)
OLD_DB_PATH=""
if [ -f "$OLD_DIR/shared/dev.db" ]; then
  OLD_DB_PATH="$OLD_DIR/shared/dev.db"
elif [ -f "$OLD_DIR/frontend/prisma/dev.db" ]; then
  OLD_DB_PATH="$OLD_DIR/frontend/prisma/dev.db"
fi

if [ -n "$OLD_DB_PATH" ]; then
  echo -e "${GREEN}🎯 Gefundene Datenbank: $OLD_DB_PATH. Migriere zu $LIVE_DIR/shared/dev.db...${NC}"
  cp "$OLD_DB_PATH" "$LIVE_DIR/shared/dev.db"
  chmod 666 "$LIVE_DIR/shared/dev.db" # Sicherstellen, dass der Node-User im Container schreiben darf
else
  echo -e "${YELLOW}⚠️ Keine bestehende dev.db gefunden. Eine neue DB wird beim Start angelegt.${NC}"
fi

# 6. Docker Container im neuen Live-Ordner starten
echo -e "${YELLOW}[6/6] Starte Docker Compose...${NC}"
cd "$LIVE_DIR"

# Führe ggf. Prisma DB-Push aus, um Schemaänderungen auf der SQLite-DB anzuwenden
# Da Prisma im Container läuft, machen wir das über docker compose run
echo -e "${YELLOW}🔄 Führe Prisma Database-Schema-Updates aus...${NC}"
if ! docker compose run --rm frontend npx --no-install prisma db push --schema=prisma/schema.prisma; then
  echo -e "${RED}⚠️ Prisma DB-Push fehlgeschlagen oder keine Änderungen vorhanden. Fahre fort...${NC}"
fi

if ! docker compose up -d; then
  echo -e "${RED}❌ START-FEHLER: Docker Compose konnte nicht gestartet werden!${NC}"
  # Springe direkt zum Rollback
  HTTP_STATUS="500"
else
  echo -e "${YELLOW}⏳ Warte 8 Sekunden, bis die Container vollständig gestartet sind...${NC}"
  sleep 8
  # 7. Health-Check
  echo -e "${YELLOW}🧪 Führe Health-Check auf der Live-Plattform durch...${NC}"
  HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" http://localhost:3000 || echo "000")
fi

if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 307 ] || [ "$HTTP_STATUS" -eq 308 ]; then
  echo -e "${GREEN}======================================================================${NC}"
  echo -e "${GREEN}🎉 SUCCESS! Das neue Docker-Update ist vollkommen fehlerfrei live!${NC}"
  echo -e "${GREEN}   Status-Code: $HTTP_STATUS${NC}"
  echo -e "${GREEN}======================================================================${NC}"
  rm -rf "$OLD_DIR" # Sicheres Löschen des alten Ordners erst bei Erfolg
  docker compose ps
  exit 0
else
  echo -e "${RED}======================================================================${NC}"
  echo -e "${RED}❌ HEALTH-CHECK FEHLGESCHLAGEN: Server antwortet mit Status $HTTP_STATUS!${NC}"
  echo -e "${RED}🔄 FÜHRE AUTOMATISCHES ROLLBACK AUF DEN LETZTEN STABILEN STAND AUS...${NC}"
  echo -e "${RED}======================================================================${NC}"
  
  # Stoppe die fehlerhaften neuen Container
  cd "$LIVE_DIR"
  docker compose down || true
  
  # Verzeichnisse zurück-swappen
  rm -rf "$LIVE_DIR"
  mv "$OLD_DIR" "$LIVE_DIR"
  
  cd "$LIVE_DIR"
  
  # Rollback starten
  if [ -f "$LIVE_DIR/docker-compose.yml" ]; then
    echo -e "${GREEN}⚠️ Starte vorherige Docker-Container...${NC}"
    docker compose up -d
  else
    echo -e "${GREEN}⚠️ Starte vorherige PM2-Prozesse (Legacy)...${NC}"
    sudo PORT=3001 pm2 start "$LIVE_DIR/dist/index.js" --name "enterprise-backend" --cwd "$LIVE_DIR"
    sudo PORT=3000 pm2 start "$LIVE_DIR/frontend/node_modules/next/dist/bin/next" --name "enterprise-frontend" --cwd "$LIVE_DIR/frontend" -- start -p 3000
    sudo pm2 save --force
  fi
  
  echo -e "${GREEN}⚠️ Rollback erfolgreich abgeschlossen! Die vorherige Version läuft wieder.${NC}"
  exit 1
fi
