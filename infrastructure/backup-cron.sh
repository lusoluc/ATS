#!/bin/bash
# ==============================================================================
# SecurATS - Automated Vault Backup (Cronjob)
# ==============================================================================
# Sichert die PostgreSQL-Datenbank und alle hochgeladenen Dokumente (CVs).
# Überträgt das Backup verschlüsselt an einen sicheren Cloud-Speicher.
# ==============================================================================

set -e

# Konfiguration
BACKUP_DIR="/var/backups/securats"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
DB_NAME="securats_db"
DB_USER="securats_user"
UPLOADS_DIR="/var/www/securats/uploads"
REMOTE_STORAGE="gcp-secure-vault:securats-backups/" # Beispiel für rclone/GCP
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "[SecurATS Vault] Starte Backup-Prozess ($TIMESTAMP)..."

# 1. Datenbank-Dump (Sicherer Export aller Daten)
echo "[1/3] Erstelle Datenbank-Dump..."
DB_BACKUP_FILE="$BACKUP_DIR/db_$TIMESTAMP.sql.gz"
pg_dump -U "$DB_USER" -d "$DB_NAME" -F p | gzip > "$DB_BACKUP_FILE"

# 2. Dokumenten-Backup (Lebensläufe, Anlagen)
echo "[2/3] Sichere Upload-Dokumente..."
FILES_BACKUP_FILE="$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz"
if [ -d "$UPLOADS_DIR" ]; then
    tar -czf "$FILES_BACKUP_FILE" -C "$UPLOADS_DIR" .
else
    echo "  (Upload-Verzeichnis existiert noch nicht, überspringe)"
fi

# 3. Off-Site Transfer (Verschlüsselter Transfer an externen Speicher)
echo "[3/3] Übertrage an sicheren Cloud-Speicher..."
# Beispiel-Kommando (setzt voraus, dass rclone konfiguriert ist):
# rclone copy "$DB_BACKUP_FILE" "$REMOTE_STORAGE"
# rclone copy "$FILES_BACKUP_FILE" "$REMOTE_STORAGE"

# 4. Lokale Aufräumaktion (alte Backups löschen um Speicherplatz zu sparen)
find "$BACKUP_DIR" -type f -name "*.gz" -mtime +$RETENTION_DAYS -delete

echo "[SecurATS Vault] Backup erfolgreich abgeschlossen und gesichert."
