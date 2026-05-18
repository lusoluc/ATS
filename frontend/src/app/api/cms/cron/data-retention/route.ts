export const dynamic = 'force-dynamic';
import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { unlink } from 'fs/promises';
import { join } from 'path';

const prisma = new PrismaClient();
const SECURE_STORAGE_PATH = join(process.cwd(), '..', 'storage', 'applicants', 'cv');

export async function GET(req: Request) {
  try {
    // 1. Authentifizierung: Dieser Endpunkt darf nur durch einen internen Cron-Job 
    // (z.B. Vercel Cron, GitHub Actions oder einen lokalen Cron-Daemon) mit einem Secret aufgerufen werden.
    const authHeader = req.headers.get('authorization');
    if (authHeader !== `Bearer ${process.env.CRON_SECRET || 'dev-cron-secret'}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // 2. Wir suchen alle Bewerbungen, die vor > 6 Monaten abgelehnt wurden
    // UND bei denen der Bewerber dem Talent-Pool NICHT zugestimmt hat.
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

    const expiredApplications = await (prisma.application as any).findMany({
      where: {
        status: 'REJECTED',
        updatedAt: { lt: sixMonthsAgo },
        consentTalentPool: false
      },
      include: { applicant: true }
    });

    let deletedCount = 0;

    for (const app of expiredApplications) {
      // 3. Lösche den verschlüsselten Lebenslauf rückstandsfrei von der Festplatte
      if (app.cvStorageId) {
        try {
          await unlink(join(SECURE_STORAGE_PATH, app.cvStorageId));
        } catch (e) {
          console.warn(`[DSGVO] Konnte Datei ${app.cvStorageId} nicht löschen:`, e);
        }
      }

      // 4. Anonymisiere den Bewerber in der Datenbank
      // Wir überschreiben die PII (Personal Identifiable Information), behalten aber die ID für Statistiken
      await prisma.applicant.update({
        where: { id: app.applicantId },
        data: {
          firstName: 'Anonymized',
          lastName: 'Anonymized',
          email: `anonymized_${app.applicantId}@deleted.local`,
          phone: null
        }
      });

      // 5. Lösche die Bewerbung selbst
      await prisma.application.delete({ where: { id: app.id } });
      deletedCount++;

      // 6. Audit Log Eintrag
      await (prisma as any).auditLog.create({
        data: {
          action: 'DSGVO_AUTOMATED_DELETION',
          applicationId: app.id,
          metadataJson: JSON.stringify({ reason: '> 6 months rejected, no talent pool consent' })
        }
      });
    }

    return NextResponse.json({
      success: true,
      message: `DSGVO-Bereinigung abgeschlossen. ${deletedCount} Datensätze vollständig anonymisiert und gelöscht.`
    });

  } catch (error: any) {
    console.error('Data Retention Cron Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
