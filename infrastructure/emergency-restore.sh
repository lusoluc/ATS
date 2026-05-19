#!/bin/bash
# ==============================================================================
# SecurATS - EMERGENCY DISASTER RECOVERY
# ==============================================================================
# WARNUNG: Dieses Skript löscht die aktuelle lokale Datenbank und 
# stellt den Stand aus dem letzten Backup wieder her.
# NUR IM NOTFALL (TOTALAUSFALL) AUSFÜHREN!
# ==============================================================================

set -e

BACKUP_DIR="/var/backups/securats"
DB_NAME="securats_db"
DB_USER="securats_user"
UPLOADS_DIR="/var/www/securats/uploads"

echo "============================================================"
echo "🚨 SecurATS DISASTER RECOVERY INITIATING 🚨"
echo "============================================================"
read -p "Soll die Wiederherstellung wirklich gestartet werden? Dies überschreibt bestehende Daten! (y/n): " confirm
if [[ "$confirm" != "y" ]]; then
    echo "Abbruch."
    exit 1
fi

# Finde die aktuellsten Backups
LATEST_DB_BACKUP=$(ls -t "$BACKUP_DIR"/db_*.sql.gz | head -1)
LATEST_FILES_BACKUP=$(ls -t "$BACKUP_DIR"/uploads_*.tar.gz | head -1)

if [ -z "$LATEST_DB_BACKUP" ]; then
    echo "Fehler: Kein Datenbank-Backup gefunden!"
    exit 1
fi

echo "[1/3] Stoppe die laufende Plattform um Konflikte zu vermeiden..."
pm2 stop securats || true

echo "[2/3] Stelle Datenbank wieder her aus: $LATEST_DB_BACKUP"
# Wir löschen die existierende DB und erzeugen sie neu (sauberer Zustand)
dropdb -U "$DB_USER" "$DB_NAME" --if-exists || true
createdb -U "$DB_USER" "$DB_NAME"
zcat "$LATEST_DB_BACKUP" | psql -U "$DB_USER" -d "$DB_NAME"

echo "[3/3] Stelle Dokumente (Uploads) wieder her..."
if [ -f "$LATEST_FILES_BACKUP" ]; then
    mkdir -p "$UPLOADS_DIR"
    tar -xzf "$LATEST_FILES_BACKUP" -C "$UPLOADS_DIR"
fi

echo "[4/4] Starte Plattform neu..."
bash ./infrastructure/deploy.sh

echo "============================================================"
echo "✅ DISASTER RECOVERY ERFOLGREICH ABGESCHLOSSEN."
echo "Die Plattform ist wieder online mit dem Stand von: $LATEST_DB_BACKUP"
echo "============================================================"
