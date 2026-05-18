import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { requireAuth } from './middlewares/auth.middleware';
import { requireRoles, ROLES } from './middlewares/role.middleware';
import { requireApplicantAccess } from './middlewares/bola.middleware';

const app = express();

// Best-in-Class Security Middlewares
app.use(helmet()); // Setzt HTTP Header gegen XSS, Clickjacking, MIME-Sniffing
app.use(cors());
app.use(express.json());

// Rate Limiter: Verhindert Brute-Force und DoS-Attacken
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 Minuten
  max: 100, // Limit each IP to 100 requests per windowMs
  message: { error: 'Zu viele Anfragen von dieser IP, bitte versuche es später erneut.' }
});
app.use('/api/', apiLimiter);

// Strenger Limiter für Formulare (Anti-Spam)
const formLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 Stunde
  max: 5, // Maximal 5 Bewerbungen pro Stunde pro IP
  message: { error: 'Spam-Schutz: Zu viele Bewerbungen gesendet. Bitte versuche es später erneut.' }
});

// ============================================================================
// 1. PUBLIC APIs (Unprotected / Read-Only / Submission)
// ============================================================================
app.get('/api/v1/public/jobs', (req, res) => {
  res.json({ message: 'List of published jobs' });
});

app.post('/api/v1/public/applications', formLimiter, (req, res) => {
  // Anti-Spam Honeypot Check
  const { bot_check_field, privacy_notice_version_id } = req.body;
  if (bot_check_field) {
    // Bot erkannt! Gib 201 zurück, ohne etwas zu speichern, um ihn in Sicherheit zu wiegen.
    console.warn('[Security] Bot-Versuch über Honeypot abgefangen.');
    return res.status(201).json({ message: 'Application submitted successfully' });
  }

  // Hard Rule: Submission requires privacy_notice_version_id
  if (!privacy_notice_version_id) {
    return res.status(400).json({ error: 'privacy_notice_version_id is required' });
  }
  res.status(201).json({ message: 'Application submitted successfully' });
});

// ============================================================================
// 2. INTERNAL GOVERNANCE APIs (Protected, Central HR Only)
// ============================================================================
app.post('/api/v1/admin/jobs/:id/approve', 
  requireAuth, 
  requireRoles([ROLES.CENTRAL_HR, ROLES.GLOBAL_ADMIN]), 
  (req, res) => {
    res.json({ message: `Job ${req.params.id} approved` });
  }
);

// ============================================================================
// 3. INTERNAL RECRUITING APIs (Protected, Local Editors)
// ============================================================================
app.post('/api/v1/recruiting/jobs', 
  requireAuth, 
  requireRoles([ROLES.LOCAL_EDITOR, ROLES.CENTRAL_HR]), 
  (req, res) => {
    res.status(201).json({ message: 'Draft job created' });
  }
);

// ============================================================================
// 4. SENSITIVE APPLICANT APIs (Protected + BOLA Guard)
// ============================================================================
app.get('/api/v1/recruiting/applications/:id', 
  requireAuth, 
  requireRoles([ROLES.LOCAL_REVIEWER, ROLES.CENTRAL_HR]), 
  requireApplicantAccess, // BOLA Guard enforces Need-to-Know
  (req, res) => {
    res.json({ message: `Sensitive data for application ${req.params.id}` });
  }
);

// WP08: Interview Scheduling API (Protected + BOLA)
app.post('/api/v1/recruiting/applications/:id/interviews',
  requireAuth,
  requireRoles([ROLES.LOCAL_REVIEWER, ROLES.CENTRAL_HR]),
  requireApplicantAccess,
  async (req, res) => {
    const { scheduledAt, locationType, meetingLink } = req.body;
    // Hier würde Prisma den Interview-Eintrag speichern
    console.log(`[Audit] Interview für Bewerbung ${req.params.id} von User ${(req as any).user?.id || 'SYSTEM'} geplant.`);
    res.status(201).json({ 
      message: 'Interview erfolgreich geplant',
      data: { scheduledAt, locationType, meetingLink }
    });
  }
);

// WP08: Message Center API - Senden (Protected + BOLA)
app.post('/api/v1/recruiting/applications/:id/messages',
  requireAuth,
  requireRoles([ROLES.LOCAL_REVIEWER, ROLES.CENTRAL_HR]),
  requireApplicantAccess,
  async (req, res) => {
    const { content } = req.body;
    // Hier würde Prisma die Nachricht speichern
    console.log(`[Audit] Nachricht an Bewerber ${req.params.id} von User ${(req as any).user?.id || 'SYSTEM'} gesendet.`);
    res.status(201).json({ 
      message: 'Nachricht erfolgreich gesendet',
      data: { direction: 'OUTBOUND', content, readStatus: false }
    });
  }
);

// WP08: Message Center API - Lesen (Protected + BOLA)
app.get('/api/v1/recruiting/applications/:id/messages',
  requireAuth,
  requireRoles([ROLES.LOCAL_REVIEWER, ROLES.CENTRAL_HR]),
  requireApplicantAccess,
  async (req, res) => {
    // Hier würde Prisma die Chat-Historie abfragen
    res.json({ 
      message: `Chat-Historie für Bewerbung ${req.params.id}`,
      data: [] // Mock leeres Array
    });
  }
);

const PORT = process.env.PORT || 3000;

// ============================================================================
// 5. WAVE 2: INTEGRATIONS (Multiposter / Job Boards)
// ============================================================================
app.get('/api/v1/integrations/multiposter/feed.xml', (req, res) => {
  // Diese Route wird von Agenturen (StepStone, Arbeitsagentur) periodisch abgerufen.
  // Sie liefert NUR Jobs, deren workflowState auf 'PUBLISHED' steht.
  
  // Wichtig: In Produktion würde hier eine API-Key Validierung stattfinden
  const apiKey = req.headers['x-api-key'];
  if (apiKey !== process.env.MULTIPOSTER_API_KEY && process.env.NODE_ENV === 'production') {
    return res.status(401).json({ error: 'Unauthorized access to Job Feed' });
  }

  // Mock-XML Generierung
  const xmlFeed = `<?xml version="1.0" encoding="UTF-8"?>
<jobs>
  <job id="1">
    <title>Pflegefachkraft (m/w/d) für die Psychiatrie</title>
    <location>Rickling</location>
    <company>Enterprise</company>
    <url>https://karriere.Enterprise.de/jobs/1</url>
  </job>
  <job id="2">
    <title>Assistenzarzt (m/w/d) in Weiterbildung</title>
    <location>Rickling</location>
    <company>Enterprise</company>
    <url>https://karriere.Enterprise.de/jobs/2</url>
  </job>
</jobs>`;

  res.set('Content-Type', 'text/xml');
  res.send(xmlFeed);
});

app.listen(PORT, () => {
  console.log(`[Server] Enterprise Karriereplattform API running on port ${PORT}`);
  console.log(`[Server] Security Baseline: JWT Auth active | RBAC active | BOLA Guards active`);
});
