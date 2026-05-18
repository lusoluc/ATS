# Developer Installation 1x1 - Das Handbuch für Entwickler

Dieses Handbuch richtet sich an Entwickler (Frontend, Backend oder Fullstack) sowie System-Administratoren, die an der Landesverein Karriereplattform arbeiten oder diese in den Live-Betrieb (Produktion) überführen. 

---

## 1. Architektur & Tech Stack im Überblick

Wir verwenden ein modernes **Monorepo-Setup**:
*   **Backend (Root-Ordner)**: Node.js mit Express. REST-API, Authentifizierung (JWT), Security Middlewares.
*   **Frontend (Ordner `/frontend`)**: Next.js (App Router) mit React und Tailwind CSS. Eigene API-Routen für UI-spezifische Aufgaben (Page Builder Puck).
*   **Datenbank**: SQLite via Prisma ORM (`prisma/dev.db`).

---

## 2. Manuelle Einrichtung (Schritt-für-Schritt Lokal)

Wenn du das Skript `setup.bat` nicht nutzen möchtest (z.B. für WSL, Mac, Linux), folge diesen Schritten:

1. **Abhängigkeiten installieren:**
   ```bash
   npm install         # Backend/Root
   cd frontend && npm install && cd ..  # Frontend
   ```
2. **Umgebungsvariablen (.env) setzen:**
   Root `.env`: `DATABASE_URL="file:./dev.db"`, `JWT_SECRET="lokal-secret"`, `PORT=3001`
   Frontend `.env.local`: `DATABASE_URL="file:c:/absoluter/pfad/zur/dev.db"` (WICHTIG: Absoluter Pfad mit Slashes!)
3. **Datenbank aufbauen:**
   ```bash
   npx prisma generate
   npx prisma db push
   node seed.mjs
   ```

---

## 3. Die Anwendung starten (Entwicklungsmodus)

**Terminal 1 (Backend):** `npm start` (Startet auf Port 3001)
**Terminal 2 (Frontend):** `cd frontend && npm run dev` (Startet auf Port 3000)

---

## 4. Häufige Fehler & Lösungen (Troubleshooting Lokal)

*   `Error: Cannot find module '@prisma/client'`: `npx prisma generate` ausführen.
*   `PrismaClientInitializationError`: Falscher/relativer Datenbankpfad in `frontend/.env.local`. Absoluten Pfad setzen!
*   `EADDRINUSE: address already in use :::3000`: Port 3000 belegt. Laufende `node.exe` Prozesse killen.
*   Next.js lädt ewig: `.next` Ordner löschen (Cache leeren) und neu starten.
*   TypeScript Fehler in `page.tsx`: In VS Code `Strg+Shift+P` -> `TypeScript: Restart TS server`.

---

## 5. PRODUKTION: Konfiguration & Security Baseline

Um Sicherheitslücken durch fehlerhafte Konfigurationen zu vermeiden, darf die Applikation **niemals** über `npm run dev` oder `start.bat` ungeschützt ins Netz gestellt werden. Folgende Checkliste ist für Server (z.B. Linux VPS oder Windows Server) zwingend abzuarbeiten:

### 5.1. Umgebungsvariablen absichern
Die `.env` Datei muss auf dem Produktionsserver zwingend angepasst werden:
```env
NODE_ENV=production
# Generiere einen extrem starken Schlüssel (z.B. via: openssl rand -base64 64)
JWT_SECRET="e9f8a...dein-neues-geheimes-secret...3b1c"
PORT=3001
```

### 5.2. Der Process Manager (PM2)
Nutze nicht `npm start`. Nutze einen Process Manager wie `pm2`, der die Applikation bei Abstürzen automatisch neu startet.
```bash
npm install -g pm2
# Backend starten
pm2 start dist/index.js --name "lv-backend"
# Frontend starten (zuvor: cd frontend && npm run build)
pm2 start npm --name "lv-frontend" -- start
pm2 save
```

### 5.3. Dateiberechtigungen & SQLite Sicherheit
Da wir SQLite verwenden, ist die Datei `prisma/dev.db` der einzige Ort, an dem Daten liegen.
*   Stelle sicher, dass der Webserver-Benutzer Lese- und Schreibrechte auf diese Datei und den Ordner `/prisma` hat.
*   Stelle über den Webserver (Nginx/Apache) sicher, dass die Datei `/prisma/dev.db` **niemals** direkt über eine URL heruntergeladen werden kann (Blockiere den Pfad im Reverse Proxy).

---

## 6. PRODUKTION: Domain, Reverse Proxy & SSL einrichten

Die direkte Freigabe der Ports 3000/3001 ist eine Sicherheitslücke. Node.js ist nicht dafür gebaut, direkte Internetverbindungen ohne Schutzschicht zu handhaben.

### 6.1. DNS & Domain
Lege im Control Panel deines Domain-Anbieters (z.B. Ionos, Strato, AWS) einen **A-Record** für die Domain (z.B. `karriere.landesverein.de`) an, der auf die IP-Adresse deines Servers zeigt.

### 6.2. Nginx Reverse Proxy konfigurieren
Installiere Nginx. Nginx nimmt Anfragen auf Port 80 (HTTP) und 443 (HTTPS) entgegen und leitet sie intern an Next.js (Port 3000) und das Backend (Port 3001) weiter.

**Beispiel Nginx Konfiguration (`/etc/nginx/sites-available/lv-karriere`):**
```nginx
server {
    server_name karriere.landesverein.de;

    # Weiterleitung Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Weiterleitung Backend API
    location /api/v1/ {
        proxy_pass http://127.0.0.1:3001/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Sicherheitsregel: Zugriff auf DB blockieren
    location ~* \.(db|sqlite|sqlite3)$ {
        deny all;
    }
}
```

### 6.3. SSL-Verschlüsselung (HTTPS) erzwingen
Nutze Certbot (Let's Encrypt), um ein kostenloses SSL-Zertifikat zu installieren und HTTP auf HTTPS umzuleiten:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d karriere.landesverein.de
```

---

## 7. PRODUKTION: E-Mail Service & SMTP Integration

Die Plattform versendet Status-E-Mails (z.B. "Bewerbung eingegangen", "Interview-Einladung"). Um nicht als Spam markiert zu werden, muss ein echter SMTP-Server angebunden werden.

### 7.1. Umgebungsvariablen ergänzen
Ergänze die Root `.env` Datei um die SMTP-Daten deines Mail-Providers (z.B. der Exchange Server des Landesvereins, oder ein Dienst wie SendGrid / Mailgun):

```env
# Mail Konfiguration
SMTP_HOST="smtp.dein-mailserver.de"
SMTP_PORT=587
SMTP_USER="karriere-system@landesverein.de"
SMTP_PASS="DeinSicheresPasswort123!"
MAIL_FROM="Landesverein Karriere <karriere-system@landesverein.de>"
```

### 7.2. Implementierungs-Hinweis im Code
Das Backend (`src/utils/mailer.ts` oder direkt in den Controllern) greift auf diese Variablen zurück. Wir empfehlen die Nutzung der Bibliothek `nodemailer`:
```typescript
// Beispielhafte Integration in Node.js
import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: parseInt(process.env.SMTP_PORT || '587'),
  secure: process.env.SMTP_PORT === '465', // true for 465, false for other ports
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

export const sendMail = async (to: string, subject: string, html: string) => {
  await transporter.sendMail({
    from: process.env.MAIL_FROM,
    to,
    subject,
    html,
  });
};
```
*Achtung:* Stelle sicher, dass die Firewall deines Servers ausgehende Verbindungen auf Port 587 (bzw. 465 / 25) erlaubt, sonst schlagen Mail-Versuche mit einem Timeout fehl!
