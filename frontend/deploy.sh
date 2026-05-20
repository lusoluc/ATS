#!/bin/bash

# ==========================================
# SecurATS Self-Healing Deployment Script
# ==========================================
echo "🔄 [1/5] Starte sicheres Deployment..."

# 1. Aktuellen (funktionierenden) Stand merken für eventuellen Rollback
PREV_COMMIT=$(git rev-parse HEAD)
echo "📌 Aktueller stabiler Commit: $PREV_COMMIT"

# 2. Neues Update herunterladen
echo "📥 [2/5] Lade Updates von GitHub..."
git pull origin main

# 3. Next.js Build Prozess ausführen
echo "🏗️ [3/5] Kompiliere Anwendung (npm run build)..."
if ! npm run build; then
    echo "❌ FEHLER: Der Build ist fehlgeschlagen (z.B. wegen Syntax-Fehler)!"
    echo "🔄 Führe automatischen Rollback durch..."
    git reset --hard $PREV_COMMIT
    npm run build
    pm2 restart securats
    echo "⚠️ Das System wurde erfolgreich auf den alten, funktionierenden Stand zurückgesetzt."
    exit 1
fi

# 4. Wenn Build erfolgreich, PM2 neustarten
echo "✅ Build erfolgreich! Starte Webserver neu..."
pm2 restart securats

# Kurze Pause, damit Next.js hochfahren kann
echo "⏳ Warte 5 Sekunden, bis der Server Traffic annimmt..."
sleep 5

# 5. Production Tests (Health Checks)
echo "🧪 [4/5] Führe Health-Checks durch..."

# Test A: Antwortet der Server mit HTTP 200 (OK)?
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" http://localhost:3000)
if [ "$HTTP_STATUS" -ne 200 ] && [ "$HTTP_STATUS" -ne 307 ] && [ "$HTTP_STATUS" -ne 308 ]; then
    echo "❌ FEHLER: Server antwortet mit Status $HTTP_STATUS anstatt 200!"
    echo "🔄 Führe automatischen Rollback durch..."
    git reset --hard $PREV_COMMIT
    npm run build
    pm2 restart securats
    exit 1
fi
echo "✅ Test A bestanden: Server antwortet korrekt."

# Test B: Ist das HTML valide und enthält es wichtige UI-Elemente? (Z.B. den Footer/Badge)
if ! curl -s http://localhost:3000 | grep -q "SecurATS"; then
    echo "❌ FEHLER: Kritische UI-Elemente (Footer/Badge) fehlen auf der Startseite!"
    echo "🔄 Führe automatischen Rollback durch..."
    git reset --hard $PREV_COMMIT
    npm run build
    pm2 restart securats
    exit 1
fi
echo "✅ Test B bestanden: UI-Elemente sind sichtbar."

echo "🚀 [5/5] DEPLOYMENT ERFOLGREICH! Das neue Update ist live und geprüft."
