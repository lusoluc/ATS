# Checkliste: Developer Go-Live (Produktionsübergabe)

Diese Checkliste führt den Entwickler / System-Administrator durch alle kritischen Schritte, um die Plattform sicher und hochverfügbar für den "Orga-Leiter" bereitzustellen. 
Sobald alle Punkte abgehakt sind, gilt das System als "Produktionsbereit".

## 1. Infrastruktur & Server-Vorbereitung
- [ ] Node.js (LTS Version) ist auf dem Server installiert.
- [ ] PM2 (Process Manager) ist global installiert (`npm install -g pm2`).
- [ ] Nginx (oder Apache/Caddy) ist als Webserver installiert.
- [ ] Die Dateiberechtigungen für den Ordner `/prisma` sind so gesetzt, dass nur der Node-Benutzer Lese-/Schreibrechte hat.

## 2. Umgebungsvariablen absichern (.env)
- [ ] Das Root `.env` existiert und enthält `NODE_ENV=production`.
- [ ] Ein neues, starkes `JWT_SECRET` wurde generiert (z.B. via `openssl rand -base64 64`) und hinterlegt. Standard-Passwörter wurden entfernt.
- [ ] Die `DATABASE_URL` (in `.env` und `frontend/.env.local`) zeigt auf den korrekten, absoluten Pfad zur `dev.db`.
- [ ] Die SMTP E-Mail-Einstellungen (`SMTP_HOST`, `SMTP_USER`, etc.) wurden mit den echten Werten der IT-Abteilung befüllt.

## 3. Sicherheits-Härtung (Webserver / Reverse Proxy)
- [ ] Eine Domain (z.B. `karriere.landesverein.de`) ist per DNS-A-Record auf die Server-IP gerichtet.
- [ ] Ein SSL-Zertifikat (z.B. Let's Encrypt) wurde installiert und HTTP wird automatisch auf HTTPS umgeleitet.
- [ ] Nginx ist konfiguriert und leitet Traffic von `Location /` an Port `3000` (Frontend) und `/api/v1/` an Port `3001` (Backend) weiter.
- [ ] Nginx **blockiert aktiv** jeglichen externen Zugriff auf sensible Dateien: `.env`, `.env.local` und `*.db` (SQLite Datenbankdateien).

## 4. Build & Deployment
- [ ] Im Root-Ordner wurde `npm install` ausgeführt (Backend Dependencies).
- [ ] Die Datenbank-Struktur wurde erfolgreich angewendet (`npx prisma generate` und `npx prisma db push`).
- [ ] Optionale Init-Daten (Stammdaten-Rahmen) wurden per `node seed.mjs` geladen.
- [ ] Im Frontend-Ordner wurde `npm install` ausgeführt.
- [ ] Im Frontend-Ordner wurde erfolgreich der Produktions-Build erstellt (`npm run build`).

## 5. Systemstart & Persistenz
- [ ] Das Backend wurde über PM2 gestartet (z.B. `pm2 start dist/index.js --name lv-backend`).
- [ ] Das Frontend wurde über PM2 gestartet (z.B. `pm2 start npm --name lv-frontend -- start`).
- [ ] PM2 wurde konfiguriert, sodass die Plattform bei einem Server-Neustart automatisch wieder hochfährt (`pm2 save` und `pm2 startup`).

## 6. End-to-End Verifikation
- [ ] Die Karriereplattform ist unter der echten Domain (HTTPS) fehlerfrei im Browser aufrufbar.
- [ ] Ein Login mit dem initialen Admin-Benutzer funktioniert (Authentifizierung & Token-Erstellung intakt).
- [ ] Eine Test-E-Mail wurde erfolgreich über das System versendet (Prüfung der SMTP-Anbindung).
- [ ] [ZUSATZ] Dem Orga-Leiter wurden die finalen Admin-Zugangsdaten und der Link zum System sicher (z.B. via Passwort-Manager) übergeben.

---
**Status:** [ ] Ausstehend | [ ] In Bearbeitung | [ ] Abgeschlossen & Übergeben
