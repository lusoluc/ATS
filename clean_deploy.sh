#!/bin/bash
# ==============================================================================
# SecurATS - Clean-Build Swap (Blue-Green) Deployment & Rollback Skript
# ==============================================================================
# Dieses Skript implementiert ein hochgradig professionelles Deployment:
# 1. Es kopiert die Plattform in ein separates Build-Verzeichnis (/opt/ATS_new).
# 2. Dort wird ein sauberer Git-Reset durchgeführt (keine lokalen Merge-Konflikte!).
# 3. Das Projekt wird im Hintergrund isoliert gebaut.
# 4. Wenn der Build erfolgreich ist, werden Ports bereinigt, die Ordner getauscht,
#    wichtige Produktionsdaten (SQLite DB, .env-Dateien) übertragen und PM2 neu gestartet.
# 5. Sollte der neue Build fehlschlagen, erfolgt ein automatisches Rollback!
# ==============================================================================

set -e

# Farbdefinitionen für Log-Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}🚀 [SecurATS] Starte Clean-Build Swap Deployment (Blue-Green)...${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 0. Root-Rechte erzwingen
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ FEHLER: Dieses Skript muss als Root oder mit 'sudo' ausgeführt werden!${NC}"
  exit 1
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
git reset --hard origin/main

# 3. Isolierte Kompilierung im Build-Verzeichnis
echo -e "${YELLOW}[3/6] Installiere Abhängigkeiten und baue Anwendung isoliert...${NC}"

# Backend-Build
npm install --legacy-peer-deps
npx prisma generate --schema=frontend/prisma/schema.prisma
npx tsc

# Frontend-Build
cd frontend
npm install --legacy-peer-deps
npx prisma generate --schema=prisma/schema.prisma

echo -e "${YELLOW}🏗️  Starte Next.js Build-Kompilierung...${NC}"
if ! npm run build; then
  echo -e "${RED}❌ BUILD-FEHLER: Die Next.js Kompilierung ist fehlgeschlagen!${NC}"
  echo -e "${YELLOW}🔄 Bereinige Build-Verzeichnis. Die Live-Plattform läuft unverändert weiter!${NC}"
  rm -rf "$BUILD_DIR"
  exit 1
fi

cd .. # Zurück in BUILD_DIR root

echo -e "${GREEN}✅ Build erfolgreich isoliert abgeschlossen! Bereite den Austausch vor...${NC}"

# 4. Port-Befreiung (Ports für Backend und Frontend freigeben)
echo -e "${YELLOW}[4/6] Befreie Ports 3000 und 3001 (Beende verwaiste Prozesse)...${NC}"
for port in 3000 3001; do
  sudo fuser -k ${port}/tcp >/dev/null 2>&1 || true
  PID_TO_KILL=$(lsof -t -i:$port || true)
  if [ -n "$PID_TO_KILL" ]; then
    sudo kill -9 $PID_TO_KILL >/dev/null 2>&1 || true
  fi
done

# 5. Swap & Daten-Erhalt (Die kritische Phase)
echo -e "${YELLOW}[5/6] Führe Verzeichnistausch und Datenübertragung aus...${NC}"

# Vorheriges Backup-Verzeichnis löschen falls vorhanden
rm -rf "$OLD_DIR"

# Ordner tauschen
mv "$LIVE_DIR" "$OLD_DIR"
mv "$BUILD_DIR" "$LIVE_DIR"

# Produktions-Daten (SQLite-Datenbank und Env-Variablen) aus dem alten Ordner in den neuen übertragen!
echo -e "${YELLOW}⚙️  Übertrage Datenbank und Umgebungskonfigurationen...${NC}"
cp "$OLD_DIR/.env" "$LIVE_DIR/.env" || true
cp "$OLD_DIR/frontend/.env.local" "$LIVE_DIR/frontend/.env.local" || true
cp "$OLD_DIR/frontend/.env" "$LIVE_DIR/frontend/.env" || true
cp "$OLD_DIR/frontend/prisma/dev.db" "$LIVE_DIR/frontend/prisma/dev.db" || true

# 6. PM2 Prozesse sauber neu registrieren & starten
echo -e "${YELLOW}[6/6] Starte PM2-Prozesse neu...${NC}"
sudo pm2 delete enterprise-backend >/dev/null 2>&1 || true
sudo pm2 delete enterprise-frontend >/dev/null 2>&1 || true

# Backend auf Port 3001 starten
sudo PORT=3001 pm2 start "$LIVE_DIR/dist/index.js" --name "enterprise-backend" --cwd "$LIVE_DIR"

# Frontend auf Port 3000 starten
sudo PORT=3000 pm2 start npm --name "enterprise-frontend" --cwd "$LIVE_DIR/frontend" -- run start -- -p 3000

# PM2 Konfiguration permanent speichern
sudo pm2 save

echo -e "${YELLOW}⏳ Warte 6 Sekunden, bis die Server initialisiert sind...${NC}"
sleep 6

# 7. Health-Check & Automatisches Rollback bei Fehlern
echo -e "${YELLOW}🧪 Führe Health-Check auf der Live-Plattform durch...${NC}"
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" http://localhost:3000 || echo "000")

if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 307 ] || [ "$HTTP_STATUS" -eq 308 ]; then
  echo -e "${GREEN}======================================================================${NC}"
  echo -e "${GREEN}🎉 SUCCESS! Das neue Update ist vollkommen fehlerfrei live geschaltet!${NC}"
  echo -e "${GREEN}   Status-Code: $HTTP_STATUS${NC}"
  echo -e "${GREEN}======================================================================${NC}"
  rm -rf "$OLD_DIR" # Sicheres Löschen des alten Ordners erst bei Erfolg
  sudo pm2 status
  exit 0
else
  echo -e "${RED}======================================================================${NC}"
  echo -e "${RED}❌ HEALTH-CHECK FEHLGESCHLAGEN: Server antwortet mit Status $HTTP_STATUS!${NC}"
  echo -e "${RED}🔄 FÜHRE AUTOMATISCHES ROLLBACK AUF DEN LETZTEN STABILEN STAND AUS...${NC}"
  echo -e "${RED}======================================================================${NC}"
  
  # Bereinige verpfuschte neue Prozesse
  sudo pm2 delete enterprise-backend >/dev/null 2>&1 || true
  sudo pm2 delete enterprise-frontend >/dev/null 2>&1 || true
  for port in 3000 3001; do
    sudo fuser -k ${port}/tcp >/dev/null 2>&1 || true
  done
  
  # Verzeichnisse zurück-swappen
  rm -rf "$LIVE_DIR"
  mv "$OLD_DIR" "$LIVE_DIR"
  
  # PM2 Prozesse auf Basis des alten, funktionierenden Stands neu starten
  sudo PORT=3001 pm2 start "$LIVE_DIR/dist/index.js" --name "enterprise-backend" --cwd "$LIVE_DIR"
  sudo PORT=3000 pm2 start npm --name "enterprise-frontend" --cwd "$LIVE_DIR/frontend" -- run start -- -p 3000
  sudo pm2 save
  
  echo -e "${GREEN}⚠️ Rollback abgeschlossen! Die vorherige stabile Version ist wieder aktiv.${NC}"
  echo -e "${RED}Bitte prüfen Sie die Crash-Logs der fehlerhaften Version below:${NC}"
  sudo pm2 status
  exit 1
fi
