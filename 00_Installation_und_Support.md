# Landesverein Karriereplattform - Installations- und Support-Handbuch

Dieses Dokument richtet sich an Administratoren, HR-Mitarbeiter und den IT-Support. Es beschreibt die einfache und sichere Installation der Plattform sowie Schritte zur Fehlerbehebung.

## 1. Übersicht der Lösung

Die Plattform ist als sogenanntes "Monorepo" strukturiert, das bedeutet, Backend und Frontend befinden sich im selben Hauptordner:
- **Backend (Root-Ordner)**: Ein Node.js/Express Server, der für die Sicherheit (Authentifizierung, Autorisierung) und die API-Schnittstellen zuständig ist.
- **Frontend (`/frontend`)**: Eine moderne Next.js Applikation, welche die Benutzeroberfläche bereitstellt.
- **Datenbank**: Eine lokale SQLite-Datenbank (`/prisma/dev.db`), die ohne aufwändigen Datenbankserver (wie MySQL oder PostgreSQL) auskommt und somit perfekt für einfache Installationen und lokale Tests ist.

Um die Hürden bei der Installation komplett zu beseitigen, wurden drei Werkzeuge (Batch-Skripte) entwickelt:
1. `setup.bat` - Automatisierte Installation und Konfiguration.
2. `start.bat` - Automatischer Start aller Dienste (für Entwicklung / Tests).
3. `doctor.bat` - Ein automatisiertes Diagnosewerkzeug für den Supportfall.

---

## 2. Systemvoraussetzungen

Bevor Sie beginnen, muss **Node.js** auf Ihrem Windows-System installiert sein.
- **Download**: [https://nodejs.org/](https://nodejs.org/) (Bitte laden Sie die "LTS" Version herunter)
- Achten Sie bei der Installation darauf, dass der Haken bei "Add to PATH" (zu Umgebungsvariablen hinzufügen) gesetzt bleibt (dies ist meistens Standard).

---

## 3. Die 1-Klick Installation (`setup.bat`)

Um die Plattform für Tests betriebsbereit zu machen, müssen Sie lediglich die Datei `setup.bat` im Hauptordner (`lv`) per Doppelklick ausführen.

**Was macht `setup.bat` im Hintergrund?**
1. **Prüfung**: Es prüft, ob Node.js installiert ist.
2. **Konfiguration**: Es generiert automatisch die Konfigurationsdateien (`.env` im Hauptordner und `frontend/.env.local`). Dabei ermittelt das Skript automatisch den korrekten absoluten Pfad zur Datenbank auf Ihrem spezifischen PC und trägt diesen ein. 
3. **Abhängigkeiten**: Es lädt alle benötigten Softwarepakete herunter.
4. **Datenbank**: Es erstellt die lokale SQLite Datenbank und füllt sie mit ersten Grunddaten.

---

## 4. Die Plattform starten (`start.bat`)

Nach erfolgreicher Installation können Sie die Plattform jederzeit über `start.bat` starten.

1. Doppelklick auf `start.bat`.
2. Es öffnen sich zwei weitere schwarze Fenster im Hintergrund.
3. Nach wenigen Sekunden ist die Plattform erreichbar:
   - **Frontend (Benutzeroberfläche)**: `http://localhost:3000`
   - **Backend (API)**: `http://localhost:3001`

**Beenden:** Schließen Sie einfach die beiden neu geöffneten schwarzen Fenster.

---

## 5. Live-Betrieb, Sicherheit, E-Mail und Domain (Produktion)

> **WICHTIG:** Das Starten über `start.bat` und die Standard-Einstellungen (wie das vorausgefüllte Passwort in der `.env`) sind **nur für lokale Tests und die Entwicklung** gedacht. 

Um die Plattform sicher im Internet (Live-Betrieb) zur Verfügung zu stellen, müssen zwingend folgende Schritte von der IT durchgeführt werden, um Sicherheitslücken zu vermeiden:

1. **Sichere Umgebungsvariablen:** Die kryptografischen Schlüssel (z.B. `JWT_SECRET`) in der `.env` Datei müssen durch starke, zufällige Passwörter ersetzt werden.
2. **Server-Absicherung (Reverse Proxy):** Die Node.js Applikation darf niemals direkt ans Internet gehängt werden. Es muss ein sogenannter "Reverse Proxy" (Nginx oder IIS) davor geschaltet werden, der als sicherer Türsteher fungiert.
3. **SSL/HTTPS Verschlüsselung:** Der Reverse Proxy muss mit einem gültigen SSL-Zertifikat (z.B. Let's Encrypt) ausgestattet werden, damit alle Bewerberdaten abhörsicher übertragen werden.
4. **Domain Integration:** In den DNS-Einstellungen Ihrer Domain (z.B. `karriere.landesverein.de`) muss ein A-Record auf die IP-Adresse des Servers zeigen.
5. **E-Mail Service anbinden:** Damit automatische E-Mails (Bewerbungseingang, Passwort vergessen) versendet werden können, müssen die SMTP-Daten Ihres Mailservers (Host, Port, User, Passwort) in die `.env` Datei eingetragen werden.

**Die genauen technischen Schritte, Befehle und Checklisten für diese Produktions-Einrichtung (Sicherheit, Domain, Mail) finden Sie im beiliegenden `00_Developer_Installation_1x1.md` Handbuch ab Kapitel 6.**

---

## 6. Hilfe bei Fehlern (`doctor.bat`)

Sollte bei der lokalen Einrichtung etwas klemmen:
1. Führen Sie `doctor.bat` per Doppelklick aus.
2. Das Skript prüft 7 kritische Systemzustände (Node-Version, fehlende Dateien, blockierte Ports).
3. Das Ergebnis wird im Terminal angezeigt. 

**Häufige Fehler:**
- **Node.js nicht gefunden:** Node installieren und den PC neustarten.
- **Port 3000 / 3001 belegt:** Es läuft bereits ein Server. Suchen Sie im Taskmanager nach `node.exe` und beenden Sie den Prozess.
- **Datenbank nicht gefunden:** Führen Sie `setup.bat` erneut aus. Stellen Sie sicher, dass der Ordner nicht schreibgeschützt ist.
