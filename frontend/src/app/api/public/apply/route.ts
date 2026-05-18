export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { randomBytes } from 'crypto';
import { encryptBuffer } from '../../../../lib/encryption';
import { applyRateLimit } from '../../../../lib/rate-limit';

const prisma = new PrismaClient();

// Wir simulieren hier den Secure Object Storage (MinIO/S3).
// Der Ordner liegt bewusst AUSSERHALB von frontend/public,
// sodass die Dateien nicht über eine normale URL erreichbar sind!
const SECURE_STORAGE_PATH = join(process.cwd(), '..', 'storage', 'applicants', 'cv');

export async function POST(req: NextRequest) {
  try {
    // 0. Rate Limiting (Schutz vor DDoS / Spam-Bewerbungen)
    const ip = req.headers.get('x-forwarded-for') || '127.0.0.1';
    // Max 3 Bewerbungen pro 60 Sekunden pro IP
    const rateLimit = applyRateLimit(`apply_${ip}`, { interval: 60000, uniqueTokenPerInterval: 3 });
    if (!rateLimit.success) {
      return NextResponse.json({ error: 'Zu viele Anfragen. Bitte versuche es in einer Minute erneut.' }, { status: 429 });
    }

    const formData = await req.formData();
    
    const jobId = formData.get('jobId') as string;
    const firstName = formData.get('firstName') as string;
    const lastName = formData.get('lastName') as string;
    const email = formData.get('email') as string;
    const phone = formData.get('phone') as string;
    const consentTalentPool = formData.get('consentTalentPool') === 'true'; // DSGVO Opt-In
    const screeningAnswersJson = formData.get('screeningAnswers') as string || '{}';
    const file = formData.get('cvFile') as File;

    // 1. Grundlegende Validierung
    if (!jobId || !firstName || !lastName || !email) {
      return NextResponse.json({ error: 'Pflichtfelder fehlen.' }, { status: 400 });
    }

    // 2. Sicherheits-Check für die Datei (Mini-Version eines Magic Byte Checks)
    let cvStorageId = null;
    if (file && file.size > 0) {
      if (file.type !== 'application/pdf') {
        return NextResponse.json({ error: 'Aus Sicherheitsgründen sind nur PDF-Dateien erlaubt.' }, { status: 400 });
      }
      if (file.size > 5 * 1024 * 1024) {
        return NextResponse.json({ error: 'Datei zu groß (Max 5MB).' }, { status: 400 });
      }

      // Speichere die Datei sicher ab
      await mkdir(SECURE_STORAGE_PATH, { recursive: true });
      const bytes = await file.arrayBuffer();
      const buffer = Buffer.from(bytes);
      
      // Datei AES-256-GCM verschlüsseln
      const encryptedBuffer = encryptBuffer(buffer);
      
      // Eindeutiger, kryptografisch sicherer Dateiname
      const safeFilename = randomBytes(16).toString('hex') + '.enc';
      const filepath = join(SECURE_STORAGE_PATH, safeFilename);
      
      await writeFile(filepath, encryptedBuffer);
      cvStorageId = safeFilename; // In Produktion wäre das z.B. die S3 Object-ID
    }

    // 3. Datenbank-Transaktion: Bewerber anlegen & Workflow starten
    const result = await prisma.$transaction(async (tx) => {
      // 3a. Bewerber anlegen oder updaten (Upsert)
      const applicant = await tx.applicant.upsert({
        where: { email: email.toLowerCase() },
        update: { firstName, lastName, phone },
        create: { firstName, lastName, email: email.toLowerCase(), phone }
      });

      // 3b. Application erstellen
      const application = await (tx as any).application.create({
        data: {
          applicantId: applicant.id,
          jobPostingId: jobId,
          cvStorageId: cvStorageId,
          screeningAnswersJson: screeningAnswersJson,
          consentTalentPool: consentTalentPool, // DSGVO
          status: 'NEW',
          // Hier würde später das lokale LLM asynchron den aiScore eintragen
        }
      });

      // 3c. Magic-Link Token generieren (Gültig für 30 Tage)
      const tokenString = randomBytes(32).toString('hex');
      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + 30);
      
      const token = await tx.applicantToken.create({
        data: {
          applicantId: applicant.id,
          token: tokenString,
          expiresAt
        }
      });

      // 3d. Workflow Engine triggern (Falls der Job / Standort einen definierten Flow hat)
      // Für diesen Prototyp erstellen wir ein Dummy-Ticket, das HR zugewiesen wird.
      const job = await tx.jobPosting.findUnique({ where: { id: jobId }, include: { facility: true }});
      if (job) {
        // Wir suchen nach einem AppWorkflowDef für diese Einrichtung (Fallback: erster verfügbarer)
        let workflow = await tx.appWorkflowDef.findFirst({ where: { facilityId: job.facilityId } });
        if (!workflow) workflow = await tx.appWorkflowDef.findFirst();

        if (workflow) {
          const ticket = await tx.appTicket.create({
            data: {
              applicationId: application.id,
              workflowId: workflow.id,
              status: 'IN_PROGRESS'
            }
          });
          
          // Erster Step: HR Review
          await tx.appStep.create({
            data: {
              appTicketId: ticket.id,
              stepOrder: 1,
              status: 'PENDING',
              comments: 'Automatisch durch System zugewiesen'
            }
          });
        }
      }

      return { application, token };
    });

    // 4. E-Mail Versand simulieren
    const magicLink = `http://localhost:3000/bewerber/${result.token.token}`;
    console.log(`\n\n[MAIL-SIMULATION] An: ${email}\nBetreff: Eingangsbestätigung deiner Bewerbung\n\nHallo ${firstName},\nvielen Dank für deine Bewerbung! Du kannst den aktuellen Status deiner Bewerbung jederzeit unter folgendem, sicheren Link einsehen:\n👉 ${magicLink}\n\nDein Enterprise Team\n\n`);

    return NextResponse.json({ 
      success: true, 
      message: 'Bewerbung erfolgreich empfangen.',
      // Nur fürs Prototyping geben wir den Link in der Response zurück, 
      // in Produktion wird er NUR per Mail verschickt!
      dev_magicLink: magicLink 
    });

  } catch (error: any) {
    console.error('Apply Error:', error);
    return NextResponse.json({ error: 'Interner Server-Fehler bei der Verarbeitung.' }, { status: 500 });
  }
}
