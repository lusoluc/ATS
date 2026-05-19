#!/bin/bash
# ==============================================================================
# SecurATS - Zero-Downtime Deployment Script
# ==============================================================================
# Dieses Skript aktualisiert die laufende Plattform auf den neuesten Code,
# baut das Projekt im Hintergrund und tauscht den laufenden Prozess nahtlos aus.
# ==============================================================================

set -e # Skript bricht bei einem Fehler sofort ab

echo "[SecurATS] Starte Zero-Downtime Deployment..."

# 1. Neuesten Code laden
echo "[1/5] Lade neuesten Code von GitHub..."
git fetch origin main
git reset --hard origin/main

# 2. Abhängigkeiten installieren
echo "[2/5] Installiere Abhängigkeiten..."
npm ci

# 3. Datenbank-Migrationen (Rückwärtskompatibel) anwenden
echo "[3/5] Führe sichere Datenbank-Updates durch..."
npx prisma generate
npx prisma migrate deploy

# 4. Neue Version im Hintergrund bauen
echo "[4/5] Baue die neue Plattform-Version (Next.js)..."
npm run build

# 5. Nahtloser Austausch (Zero Downtime)
echo "[5/5] Führe Graceful Reload durch..."
# Prüfen ob PM2 bereits den Prozess "securats" kennt.
# Wenn ja: reload (Downtime = 0). Wenn nein: neu starten.
if pm2 show securats > /dev/null; then
    pm2 reload securats --update-env
else
    pm2 start npm --name "securats" -- start
    pm2 save
fi

echo "[SecurATS] Deployment erfolgreich abgeschlossen! Plattform ist aktuell."
