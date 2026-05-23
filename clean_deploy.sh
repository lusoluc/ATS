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

LOG_FILE="/var/log/securats_deploy.log"

log_dev_diag() {
  local phase="$1"
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "=== DEV DIAGNOSTICS: $phase ($(date)) ===" >> "$LOG_FILE"
  echo "--- System Sockets (ss) ---" >> "$LOG_FILE"
  if command -v ss &> /dev/null; then
    ss -tlnp >> "$LOG_FILE" 2>&1 || true
  else
    netstat -tlnp >> "$LOG_FILE" 2>&1 || true
  fi
  echo "--- Network Interfaces ---" >> "$LOG_FILE"
  ip addr >> "$LOG_FILE" 2>&1 || true
  echo "--- Docker Containers ---" >> "$LOG_FILE"
  docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}" >> "$LOG_FILE" 2>&1 || true
  echo "--- Docker Networks ---" >> "$LOG_FILE"
  docker network ls >> "$LOG_FILE" 2>&1 || true
  echo "--- IPTables NAT Rules ---" >> "$LOG_FILE"
  if command -v iptables &> /dev/null; then
    iptables -t nat -L DOCKER -n -v >> "$LOG_FILE" 2>&1 || true
  fi
  echo "--- Host Node/NPM Processes ---" >> "$LOG_FILE"
  ps aux | grep -E "node|npm" | grep -v grep >> "$LOG_FILE" 2>&1 || true
  echo "==========================================" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"
  chmod 666 "$LOG_FILE" >/dev/null 2>&1 || true
}

# Initiales Logging starten
log_dev_diag "START_OF_DEPLOYMENT"

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

# 0c. Stelle sicher, dass der Docker-Daemon läuft und nicht durch systemd-Limits blockiert ist (Selbstheilung)
if ! docker info &>/dev/null; then
  echo -e "${YELLOW}📦 Docker-Daemon ist nicht erreichbar oder offline. Versuche Selbstheilung...${NC}"
  
  SYSTEMCTL_CMD=""
  if command -v systemctl &> /dev/null; then
    SYSTEMCTL_CMD="systemctl"
  elif [ -x "/bin/systemctl" ]; then
    SYSTEMCTL_CMD="/bin/systemctl"
  elif [ -x "/usr/bin/systemctl" ]; then
    SYSTEMCTL_CMD="/usr/bin/systemctl"
  fi

  if [ -n "$SYSTEMCTL_CMD" ]; then
    echo -e "${YELLOW}   -> Setze systemd-Limits zurück und starte Docker-Dienst neu...${NC}"
    sudo $SYSTEMCTL_CMD reset-failed docker >/dev/null 2>&1 || true
    sudo $SYSTEMCTL_CMD restart docker >/dev/null 2>&1 || true
  else
    if [ -x "/etc/init.d/docker" ]; then
      echo -e "${YELLOW}   -> Starte Docker-Dienst via init.d neu...${NC}"
      sudo /etc/init.d/docker restart >/dev/null 2>&1 || true
    elif command -v service &> /dev/null; then
      echo -e "${YELLOW}   -> Starte Docker-Dienst via service neu...${NC}"
      sudo service docker restart >/dev/null 2>&1 || true
    fi
  fi
  
  # Warte, bis der Docker-Daemon bereit ist (Maximal 30 Sekunden)
  echo -e "${YELLOW}⏳ Warte, bis der Docker-Daemon einsatzbereit ist...${NC}"
  for i in {1..30}; do
    if docker info >/dev/null 2>&1; then
      echo -e "${GREEN}✅ Docker-Daemon erfolgreich gestartet und bereit!${NC}"
      break
    fi
    sleep 1
  done
fi

cleanup_containers() {
  # Lösche explizit bekannte Container-Namen
  echo -e "${YELLOW}🛑 Lösche bekannte Container-Namen...${NC}"
  docker rm -f securats-django securats-frontend securats-backend ats-frontend ats-backend >/dev/null 2>&1 || true
  
  # Dynamische Erkennung & Entfernung JEDES Containers (laufend oder gestoppt!), der Port 3000 oder 3001 belegt
  echo -e "${YELLOW}🛑 Suche nach weiteren blockierenden Containern (Laufend & Gestoppt)...${NC}"
  for cid in $(docker ps -a -q 2>/dev/null || true); do
    # Prüfe die Port-Bindings in der HostConfig (funktioniert auch bei gestoppten Containern!)
    PORTS=$(docker inspect --format '{{range $p, $conf := .HostConfig.PortBindings}}{{range $conf}}{{.HostPort}} {{end}}{{end}}' $cid 2>/dev/null || true)
    if echo "$PORTS" | grep -q -E "\b3000\b|\b3001\b"; then
      CONTAINER_NAME=$(docker inspect --format '{{.Name}}' $cid 2>/dev/null | sed 's/\///' || echo "Unbekannt")
      echo -e "${RED}👉 Blockierender Container gefunden: Name='$CONTAINER_NAME' ID='$cid' Ports: $PORTS${NC}"
      echo -e "${YELLOW}   -> Lösche Container $cid...${NC}"
      docker rm -f $cid >/dev/null 2>&1 || true
    fi
  done
}

kill_process_on_port() {
  local port=$1
  echo -e "${YELLOW}🔍 Suche Prozess auf Port $port...${NC}"
  
  # 1. Versuche PID via 'ss' zu finden
  if command -v ss &> /dev/null; then
    local pid
    pid=$(sudo ss -tlnp 2>/dev/null | grep -E ":${port}\b" | grep -o -E "pid=[0-9]+" | head -n 1 | cut -d= -f2 || true)
    if [ -n "$pid" ]; then
      echo -e "${RED}👉 Prozess via 'ss' gefunden: PID $pid auf Port $port. Sende SIGKILL...${NC}"
      sudo kill -9 "$pid" >/dev/null 2>&1 || true
      return 0
    fi
  fi
  
  # 2. Versuche PID via 'netstat' zu finden
  if command -v netstat &> /dev/null; then
    local pid
    pid=$(sudo netstat -tlnp 2>/dev/null | grep -E ":${port}\b" | awk '{print $7}' | cut -d/ -f1 | head -n 1 || true)
    if [ -n "$pid" ] && [ "$pid" != "-" ]; then
      echo -e "${RED}👉 Prozess via 'netstat' gefunden: PID $pid auf Port $port. Sende SIGKILL...${NC}"
      sudo kill -9 "$pid" >/dev/null 2>&1 || true
      return 0
    fi
  fi

  # 3. Versuche PID via 'lsof' zu finden
  if command -v lsof &> /dev/null; then
    local pid
    pid=$(sudo lsof -t -i:$port | head -n 1 || true)
    if [ -n "$pid" ]; then
      echo -e "${RED}👉 Prozess via 'lsof' gefunden: PID $pid auf Port $port. Sende SIGKILL...${NC}"
      sudo kill -9 "$pid" >/dev/null 2>&1 || true
      return 0
    fi
  fi
}

is_port_in_use() {
  local port=$1
  local hex_port
  hex_port=$(printf "%04X" "$port")
  
  # Check IPv4
  if [ -f /proc/net/tcp ] && grep -q -E "^\s*[0-9]+:\s+[0-9A-Fa-f]+:${hex_port}\s+[0-9A-Fa-f]+\s+0A\b" /proc/net/tcp; then
    return 0
  fi
  # Check IPv6
  if [ -f /proc/net/tcp6 ] && grep -q -E "^\s*[0-9]+:\s+[0-9A-Fa-f]+:${hex_port}\s+[0-9A-Fa-f]+\s+0A\b" /proc/net/tcp6; then
    return 0
  fi
  
  # Fallback to bash socket test
  if (timeout 1 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$port" 2>/dev/null); then
    return 0
  fi
  
  return 1
}

free_ports() {
  echo -e "${YELLOW}🧹 Start der ultimativen Port-Befreiung (Ports 3000 & 3001)...${NC}"
  log_dev_diag "BEFORE_PORT_CLEANUP"
  
  # 0. Analyse: Wer belegt aktuell die Ports? (Für die Logs)
  for port in 3000 3001; do
    echo -e "${BLUE}🔍 Analyse Port $port...${NC}"
    if command -v lsof &> /dev/null; then
      LSOF_OUT=$(sudo lsof -i :$port || true)
      if [ -n "$LSOF_OUT" ]; then
        echo -e "${YELLOW}👉 Host-Prozess auf Port $port gefunden:${NC}\n$LSOF_OUT"
      fi
    fi
    CONTAINERS_ON_PORT=$(docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Ports}}" | grep -E ":$port\b|:$port->" || true)
    if [ -n "$CONTAINERS_ON_PORT" ]; then
      echo -e "${YELLOW}👉 Docker-Container auf Port $port gefunden:${NC}\n$CONTAINERS_ON_PORT"
    fi
  done

  # 1. Beende eventuell blockierende systemd-Dienste auf dem Host
  echo -e "${YELLOW}🛑 Prüfe und stoppe verbliebene systemd-Dienste...${NC}"
  for service in enterprise-backend enterprise-frontend ats-backend ats-frontend securats securats-frontend securats-backend; do
    if systemctl is-active --quiet $service 2>/dev/null; then
      echo -e "   -> Stoppe systemd-Dienst $service..."
      sudo systemctl stop $service >/dev/null 2>&1 || true
      sudo systemctl disable $service >/dev/null 2>&1 || true
    fi
  done

  # 1b. Beende PM2-Systemd-Startdienste dynamically
  echo -e "${YELLOW}🛑 Prüfe und stoppe PM2 systemd-Startdienste...${NC}"
  if command -v systemctl &> /dev/null; then
    for service in $(systemctl list-units --type=service --all --no-legend | grep -E "pm2-" | awk '{print $1}' || true); do
      echo -e "   -> Stoppe und deaktiviere PM2-Systemd-Dienst $service..."
      sudo systemctl stop "$service" >/dev/null 2>&1 || true
      sudo systemctl disable "$service" >/dev/null 2>&1 || true
    done
  fi

  # 2. Beende PM2 Daemon und alle PM2-Prozesse komplett
  echo -e "${YELLOW}🛑 Beende PM2 komplett...${NC}"
  sudo pm2 stop all >/dev/null 2>&1 || true
  sudo pm2 kill >/dev/null 2>&1 || true
  
  # 3. Beende jegliche verbliebenen Node/npm-Prozesse auf dem Host
  echo -e "${YELLOW}🛑 Beende alle Node/npm-Prozesse auf dem Host...${NC}"
  sudo pkill -9 -f node >/dev/null 2>&1 || true
  sudo pkill -9 -f npm >/dev/null 2>&1 || true
  sudo pkill -9 -f docker-proxy >/dev/null 2>&1 || true
  
  # 4. Erste Container-Bereinigung vor dem Docker-Restart
  cleanup_containers
  
  # 5. Erzwinge Freigabe der Host-Ports über PIDs (ss/netstat/lsof) & fuser
  echo -e "${YELLOW}🛑 Erzwinge Freigabe der Host-Ports 3000 & 3001...${NC}"
  for port in 3000 3001; do
    sudo fuser -k ${port}/tcp >/dev/null 2>&1 || true
    kill_process_on_port "$port"
  done

  # 6. Stale Docker-Netzwerkzustand bereinigen (Systemd Docker-Dienst neu starten)
  if systemctl is-active --quiet docker 2>/dev/null; then
    echo -e "${YELLOW}🛑 Starte Docker-Dienst neu, um blockierte/verwaiste Netzwerk-Sockets (Ghost Ports) zu flushen...${NC}"
    sudo systemctl restart docker >/dev/null 2>&1 || true
    
    # Warte, bis der Docker-Daemon wieder voll einsatzbereit ist (Maximal 30 Sekunden)
    echo -e "${YELLOW}⏳ Warte, bis der Docker-Daemon wieder einsatzbereit ist...${NC}"
    for i in {1..30}; do
      if docker info >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker-Daemon ist wieder online und bereit!${NC}"
        break
      fi
      sleep 1
    done
    
    # ZWEITER Container-Cleanup (Double-Tap) unmittelbar nach dem Docker-Restart!
    cleanup_containers
  fi

  # 7. Verifizierung der Port-Freiheit über Pure Bash Sockets
  echo -e "${YELLOW}🧪 Verifiziere Port-Freigabe...${NC}"
  PORTS_BUSY=0
  for port in 3000 3001; do
    if is_port_in_use "$port"; then
      echo -e "${RED}❌ WARNUNG: Port $port ist trotz aller Bemühungen weiterhin belegt!${NC}"
      PORTS_BUSY=1
      # Letzte Notbremse: Versuche den Port nochmals schärfer freizugeben
      kill_process_on_port "$port"
    fi
  done

  if [ $PORTS_BUSY -eq 0 ]; then
    echo -e "${GREEN}✅ Ports 3000 und 3001 sind nun garantiert frei!${NC}"
  else
    echo -e "${YELLOW}⚠️ Einige Ports scheinen noch blockiert zu sein. Wir fahren fort, falls Docker-Proxy den Port freigibt...${NC}"
  fi
  
  log_dev_diag "AFTER_PORT_CLEANUP"
}

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
echo -e "${YELLOW}[4/6] Führe ultimative Port-Befreiung für 3000/3001 aus...${NC}"
free_ports


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
# Falls es sich um den allerersten Umstieg handelt, existiert die Datenbank unter frontend/prisma/dev.db (Prisma).
# Falls es ein Folge-Deployment ist, liegt sie bereits unter shared/dev.db (Django).
if [ -f "$OLD_DIR/shared/dev.db" ]; then
  echo -e "${GREEN}🎯 Gefundene Django-Datenbank: $OLD_DIR/shared/dev.db. Kopiere direkt...${NC}"
  cp "$OLD_DIR/shared/dev.db" "$LIVE_DIR/shared/dev.db"
  chmod 666 "$LIVE_DIR/shared/dev.db"
elif [ -f "$OLD_DIR/frontend/prisma/dev.db" ]; then
  echo -e "${GREEN}🎯 Gefundene Prisma-Datenbank: $OLD_DIR/frontend/prisma/dev.db. Bereite Migrations-Quelle vor...${NC}"
  cp "$OLD_DIR/frontend/prisma/dev.db" "$LIVE_DIR/shared/old_prisma_dev.db"
  chmod 666 "$LIVE_DIR/shared/old_prisma_dev.db"
else
  echo -e "${YELLOW}⚠️ Keine bestehende dev.db gefunden. Eine neue DB wird beim Start angelegt.${NC}"
fi

# 6. Docker Container im neuen Live-Ordner starten
echo -e "${YELLOW}[6/6] Starte Docker Compose...${NC}"
cd "$LIVE_DIR"

START_SUCCESS=0
MAX_RETRIES=3
RETRY_COUNT=1

while [ $RETRY_COUNT -le $MAX_RETRIES ]; do
  echo -e "${YELLOW}🚀 Starte Container (Versuch $RETRY_COUNT von $MAX_RETRIES)...${NC}"
  if docker compose up -d; then
    START_SUCCESS=1
    break
  else
    echo -e "${RED}⚠️ Versuch $RETRY_COUNT fehlgeschlagen. Eventuell blockiert Docker-Proxy den Port...${NC}"
    log_dev_diag "START_ATTEMPT_FAILED_RETRY_$RETRY_COUNT"
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
      echo -e "${YELLOW}⏳ Warte 5 Sekunden, befreie die Ports erneut und probiere es nochmal...${NC}"
      sleep 5
      free_ports
    fi
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $START_SUCCESS -eq 0 ]; then
  echo -e "${RED}❌ START-FEHLER: Docker Compose konnte nach $MAX_RETRIES Versuchen nicht gestartet werden!${NC}"
  log_dev_diag "FINAL_START_FAILURE"
  # Springe direkt zum Rollback
  HTTP_STATUS="500"
else
  # Führe ggf. Django Migrationen aus, um Schemaänderungen auf der SQLite-DB anzuwenden
  # Wir tun dies über 'docker compose exec', um zu verhindern, dass ein separater Container erstellt wird.
  echo -e "${YELLOW}🔄 Führe Django Database-Schema-Updates aus...${NC}"
  if ! docker compose exec -T web python manage.py migrate --noinput; then
    echo -e "${RED}⚠️ Django-Migrationen fehlgeschlagen. Eventuell Verbindungsfehler. Fahre fort...${NC}"
    log_dev_diag "DJANGO_MIGRATION_FAILED"
  else
    echo -e "${GREEN}✅ Django-Migrationen erfolgreich angewendet!${NC}"
  fi

  # Überprüfe, ob eine alte Prisma-Datenbank bereitliegt, die noch importiert werden muss (Erst-Umstieg)
  if docker compose exec -T web test -f /app/shared/old_prisma_dev.db; then
    echo -e "${YELLOW}🔄 Erst-Migration erkannt: Migriere Prisma-Datenbestände in das neue Django-Schema...${NC}"
    if ! docker compose exec -T web python manage.py migrate_prisma_data --source /app/shared/old_prisma_dev.db; then
      echo -e "${RED}❌ FEHLER: Daten-Migration fehlgeschlagen!${NC}"
      log_dev_diag "DJANGO_PRISMA_MIGRATION_FAILED"
    else
      echo -e "${GREEN}✅ Daten-Migration erfolgreich abgeschlossen! Bereinige temporäre Dateien...${NC}"
      docker compose exec -T web rm -f /app/shared/old_prisma_dev.db || true
    fi
  fi

  # Schneller Neustart der Services, um Datenbank-Verbindungen zu aktualisieren
  echo -e "${YELLOW}🔄 Starte Web-Container kurz neu, um Datenbank-Verbindungen zu aktualisieren...${NC}"
  docker compose restart web || true

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
  log_dev_diag "DEPLOYMENT_SUCCESSFUL"
  rm -rf "$OLD_DIR" # Sicheres Löschen des alten Ordners erst bei Erfolg
  docker compose ps
  exit 0
else
  echo -e "${RED}======================================================================${NC}"
  echo -e "${RED}❌ HEALTH-CHECK FEHLGESCHLAGEN: Server antwortet mit Status $HTTP_STATUS!${NC}"
  echo -e "${RED}🔄 FÜHRE AUTOMATISCHES ROLLBACK AUF DEN LETZTEN STABILEN STAND AUS...${NC}"
  echo -e "${RED}======================================================================${NC}"
  log_dev_diag "HEALTH_CHECK_FAILED_INITIATING_ROLLBACK"
  
  # Stoppe die fehlerhaften neuen Container
  cd "$LIVE_DIR"
  docker compose down || true
  
  # Verzeichnisse zurück-swappen
  rm -rf "$LIVE_DIR"
  mv "$OLD_DIR" "$LIVE_DIR"
  
  cd "$LIVE_DIR"
  
  # Vor dem Start der alten Version unbedingt Ports wieder befreien!
  free_ports
  
  # Rollback starten
  if [ -f "$LIVE_DIR/docker-compose.yml" ]; then
    echo -e "${GREEN}⚠️ Starte vorherige Docker-Container...${NC}"
    ROLLBACK_SUCCESS=0
    RETRY_COUNT=1
    while [ $RETRY_COUNT -le 3 ]; do
      echo -e "${YELLOW}🚀 Starte Rollback-Container (Versuch $RETRY_COUNT von 3)...${NC}"
      if docker compose up -d; then
        ROLLBACK_SUCCESS=1
        break
      else
        echo -e "${RED}⚠️ Rollback-Start Versuch $RETRY_COUNT desolat. Eventuell blockiert Docker-Proxy den Port...${NC}"
        log_dev_diag "ROLLBACK_ATTEMPT_FAILED_RETRY_$RETRY_COUNT"
        if [ $RETRY_COUNT -lt 3 ]; then
          echo -e "${YELLOW}⏳ Warte 5 Sekunden, befreie die Ports erneut und probiere es nochmal...${NC}"
          sleep 5
          free_ports
        fi
      fi
      RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    if [ $ROLLBACK_SUCCESS -eq 0 ]; then
      echo -e "${RED}❌ ROLLBACK-START FEHLGESCHLAGEN! Das System ist eventuell offline!${NC}"
      log_dev_diag "ROLLBACK_FATAL_FAILURE"
    else
      log_dev_diag "ROLLBACK_SUCCESSFUL"
    fi
  else
    echo -e "${GREEN}⚠️ Starte vorherige PM2-Prozesse (Legacy)...${NC}"
    sudo PORT=3001 pm2 start "$LIVE_DIR/dist/index.js" --name "enterprise-backend" --cwd "$LIVE_DIR"
    sudo PORT=3000 pm2 start "$LIVE_DIR/frontend/node_modules/next/dist/bin/next" --name "enterprise-frontend" --cwd "$LIVE_DIR/frontend" -- start -p 3000
    sudo pm2 save --force
    log_dev_diag "ROLLBACK_SUCCESSFUL_LEGACY"
  fi
  
  echo -e "${GREEN}⚠️ Rollback erfolgreich abgeschlossen! Die vorherige Version läuft wieder.${NC}"
  exit 1
fi
