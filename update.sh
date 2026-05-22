#!/bin/bash
# ==============================================================================
# SecurATS - Permanentes & Selbstheilendes Deployment Master-Skript
# ==============================================================================
# Dieses Skript stellt sicher, dass verwaiste Prozesse auf den Ports 3000 und 3001
# restlos beendet werden, lädt den neuesten Code, installiert Abhängigkeiten,
# generiert Prisma-Clients, baut Backend & Frontend und startet alles sauber in PM2.
# ==============================================================================

# Abbruch bei unvorhergesehenen Fehlern, außer bei kontrollierten Befehlen
set -e

echo "======================================================================"
echo "🔄 [SecurATS] Starte permanentes & selbstheilendes Deployment..."
echo "======================================================================"

# 0. Root-Rechte erzwingen
if [ "$EUID" -ne 0 ]; then
  echo "❌ FEHLER: Dieses Skript muss als Root oder mit 'sudo' ausgeführt werden!"
  exit 1
fi

# Wechsle ins Projektverzeichnis
PROJECT_DIR="/opt/ATS"
if [ -d "$PROJECT_DIR" ]; then
  cd "$PROJECT_DIR"
else
  echo "❌ FEHLER: Projektordner $PROJECT_DIR existiert nicht!"
  exit 1
fi

# 1. Port-Bereinigung (Behebt verwaiste Node-Prozesse)
echo "🧹 [1/7] Analysiere und befreie Ports 3000 (Frontend) & 3001 (Backend)..."

# Verwende lsof und fuser für maximale Redundanz beim Terminieren blockierender Prozesse
for port in 3000 3001; do
  if lsof -t -i:$port >/dev/null 2>&1; then
    echo "⚠️  Port $port ist blockiert. Beende verwaiste Prozesse..."
    sudo fuser -k ${port}/tcp >/dev/null 2>&1 || true
    PID_TO_KILL=$(lsof -t -i:$port)
    if [ -n "$PID_TO_KILL" ]; then
      sudo kill -9 $PID_TO_KILL >/dev/null 2>&1 || true
    fi
  else
    echo "✅ Port $port ist frei."
  fi
done

# 2. Git-Zustand bereinigen & Code ziehen
echo "📥 [2/7] Bereinige Git-Status und lade Updates von GitHub..."
# Eventuelle manuelle Server-Änderungen stashen/resetteln, um Merge-Konflikte zu verhindern
git reset --hard HEAD
git clean -fd
git pull origin main

# 3. Backend (Root) Abhängigkeiten & Prisma-Client
echo "📦 [3/7] Richte Backend & Root-Abhängigkeiten ein..."
npm install --legacy-peer-deps

echo "⚙️  Generiere Prisma Client für das Backend..."
npx prisma generate --schema=frontend/prisma/schema.prisma

# 4. Backend kompilieren
echo "🏗️  [4/7] Kompiliere TypeScript Backend..."
npx tsc

# 5. Frontend Abhängigkeiten & Build
echo "📦 [5/7] Richte Frontend-Abhängigkeiten ein..."
cd frontend
npm install --legacy-peer-deps

echo "⚙️  Generiere Prisma Client für das Frontend..."
npx prisma generate --schema=prisma/schema.prisma

echo "🏗️  Baue Next.js Frontend (Kompilierung)..."
npm run build
cd ..

# 6. PM2 Prozesse sauber neu registrieren
echo "🔄 [6/7] Registriere PM2-Prozesse sauber und konfliktfrei neu..."

# Lösche alte PM2-Instanzen um fehlerhafte Caches komplett auszuschließen
sudo pm2 delete enterprise-backend >/dev/null 2>&1 || true
sudo pm2 delete enterprise-frontend >/dev/null 2>&1 || true

# Backend auf Port 3001 starten
echo "🚀 Starte Backend (enterprise-backend) auf Port 3001..."
sudo PORT=3001 pm2 start dist/index.js --name "enterprise-backend" --cwd "$PROJECT_DIR"

# Frontend auf Port 3000 starten
echo "🚀 Starte Next.js Frontend (enterprise-frontend) auf Port 3000..."
sudo PORT=3000 pm2 start npm --name "enterprise-frontend" --cwd "$PROJECT_DIR/frontend" -- run start -- -p 3000

# Speichere die PM2-Konfiguration für System-Reboots
sudo pm2 save

# Kurze Pause, um den Prozessen Zeit zum Starten zu geben
echo "⏳ Warte 5 Sekunden, bis die Server hochgefahren sind..."
sleep 5

# 7. Automatischer Health-Check & Validierung
echo "🧪 [7/7] Führe automatischen Health-Check durch..."
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" http://localhost:3000)

if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 307 ] || [ "$HTTP_STATUS" -eq 308 ]; then
  echo "======================================================================"
  echo "🎉 DEPLOYMENT ERFOLGREICH! Das neue Update ist live und erreichbar."
  echo "   Status-Code: $HTTP_STATUS"
  echo "======================================================================"
  echo "PM2 Prozess-Status:"
  sudo pm2 status
  exit 0
else
  echo "======================================================================"
  echo "❌ DEPLOYMENT-FEHLER: Der Server antwortet mit Status $HTTP_STATUS!"
  echo "======================================================================"
  echo "--- PM2 PROZESS-STATUS ---"
  sudo pm2 status
  echo "--- BACKEND CRASH-LOGS ---"
  sudo pm2 logs enterprise-backend --lines 25 --no-colors --err || true
  echo "--- FRONTEND CRASH-LOGS ---"
  sudo pm2 logs enterprise-frontend --lines 25 --no-colors --err || true
  exit 1
fi
