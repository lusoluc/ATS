#!/bin/sh
# SecurATS Entrypoint (P0.1): macht `docker compose pull && up -d` zum
# Ein-Befehl-Update – Migrationen laufen automatisch beim Start.
set -e

if [ -n "$POSTGRES_HOST" ]; then
  echo "Warte auf PostgreSQL ($POSTGRES_HOST) ..."
  python - << 'PYEOF'
import os, socket, time, sys
host, port = os.environ["POSTGRES_HOST"], int(os.environ.get("POSTGRES_PORT", "5432"))
for i in range(60):
    try:
        socket.create_connection((host, port), timeout=2).close()
        sys.exit(0)
    except OSError:
        time.sleep(2)
print("PostgreSQL nicht erreichbar – Abbruch.", file=sys.stderr)
sys.exit(1)
PYEOF
fi

echo "Migrationen anwenden ..."
python manage.py migrate --noinput

echo "Statische Dateien einsammeln ..."
python manage.py collectstatic --noinput

# Erststart-Komfort: Rollen + Admin anlegen (idempotent), wenn Env gesetzt
if [ -n "$SECURATS_ADMIN_USER" ]; then
  python manage.py bootstrap_auth || true
fi

exec "$@"
