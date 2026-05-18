import { PrismaClient } from '@prisma/client';
import https from 'https';
import fs from 'fs';

const prisma = new PrismaClient();

// In Produktion sollten Zertifikate aus einem sicheren Vault geladen werden
const mtlsAgent = new https.Agent({
  // cert: fs.readFileSync('./certs/client-cert.pem'),
  // key: fs.readFileSync('./certs/client-key.pem'),
  // ca: fs.readFileSync('./certs/ca-cert.pem'),
  rejectUnauthorized: true, // Erzwingt Server-Zertifikat Validierung
});

/**
 * HRIS Export Worker (WP10)
 * Sucht nach Bewerbern, die in den Status 'HIRED' gesetzt wurden,
 * und exportiert deren Stammdaten sicher in das Core-HR System (z.B. SAP, LOGA).
 */
export async function runHrisExport() {
  console.log(`[HRIS Export] Starte Export-Lauf für eingestellte Kandidaten...`);

  try {
    // 1. Finde alle ApplicationForms, die auf HIRED stehen und noch nicht exportiert wurden
    // (Simuliert durch eine Query auf Interview Outcome oder einen neuen Status)
    const hiredApplications = [
      { id: 'app-003', firstName: 'Sarah', lastName: 'Müller', email: 's.mueller@example.com', jobPostingId: 'job-1' }
    ];

    if (hiredApplications.length === 0) {
      console.log(`[HRIS Export] Keine neuen Einstellungen zum Exportieren gefunden.`);
      return;
    }

    console.log(`[HRIS Export] ${hiredApplications.length} Kandidaten für den Export gefunden.`);

    // 2. Exportiere jeden Kandidaten sicher via mTLS
    for (const app of hiredApplications) {
      console.log(`[mTLS] Sende Kandidat ${app.id} an das Core-HR System...`);
      
      const payload = JSON.stringify({
        sourceSystem: 'LV_CAREER_PLATFORM',
        candidateId: app.id,
        firstName: app.firstName,
        lastName: app.lastName,
        email: app.email,
        jobReference: app.jobPostingId,
        timestamp: new Date().toISOString()
      });

      /*
      // Tatsächlicher API Request (auskommentiert für Demo)
      const options = {
        hostname: 'hris.Enterprise.local',
        port: 443,
        path: '/api/v1/onboarding/candidate',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload)
        },
        agent: mtlsAgent
      };

      const req = https.request(options, (res) => {
        if (res.statusCode === 201) {
          console.log(`[Audit] Kandidat ${app.id} erfolgreich ins HRIS exportiert.`);
        }
      });
      req.write(payload);
      req.end();
      */

      console.log(`[Audit] Kandidat ${app.id} erfolgreich ins HRIS exportiert (SIMULIERT).`);
      
      // Hier würde Prisma das Flag `hrisExported: true` auf der Application setzen
    }

  } catch (error) {
    console.error(`[HRIS Export] Fehler beim Exportlauf:`, error);
  } finally {
    await prisma.$disconnect();
  }
}

if (require.main === module) {
  runHrisExport();
}
