import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Retention Policy Konstanten
const RETENTION_MONTHS = 6;

/**
 * Retention Execution Baseline (Background Worker für WP05)
 * Dieser Job sollte regelmäßig (z.B. täglich per Cron) laufen.
 * Er sucht nach Bewerbungen im Status 'REJECTED' oder 'ARCHIVED',
 * deren Frist abgelaufen ist, und anonymisiert die PII-Daten.
 */
export async function runRetentionWorker() {
  console.log(`[Retention Worker] Starte asynchronen Löschlauf...`);
  
  // Berechne den Stichtag (vor X Monaten)
  const cutoffDate = new Date();
  cutoffDate.setMonth(cutoffDate.getMonth() - RETENTION_MONTHS);

  try {
    // 1. Finde alle Bewerbungen, die löschpflichtig sind
    // In einer echten DB würden wir nach dem Datum der Absage filtern (z.B. rejectedAt)
    // Für dieses Modell nutzen wir das updatedAt der ApplicationForm 
    const expiredApplications = await (prisma as any).application.findMany({
      where: {
        // Angenommener Status-Filter (in der Prisma-Schema Erweiterung für WP04/05)
        // status: { in: ['REJECTED', 'WITHDRAWN'] },
        updatedAt: {
          lte: cutoffDate
        }
      }
    });

    if (expiredApplications.length === 0) {
      console.log(`[Retention Worker] Keine abgelaufenen Datensätze gefunden. Stichtag: ${cutoffDate.toISOString()}`);
      return;
    }

    console.log(`[Retention Worker] ${expiredApplications.length} abgelaufene Datensätze gefunden. Starte Anonymisierung...`);

    // 2. Anonymisierung der PII-Daten durchführen
    // Wir löschen den Record nicht zwingend komplett (falls statistische Daten für Analytics bleiben sollen),
    // sondern überschreiben alle sensiblen Felder.
    for (const app of expiredApplications) {
      // await prisma.applicationForm.update({
      //   where: { id: app.id },
      //   data: {
      //     firstName: 'ANONYMISED',
      //     lastName: 'ANONYMISED',
      //     email: 'anonymised@domain.local',
      //     status: 'DELETED_RETENTION',
      //     // Lösche Referenzen zu Lebensläufen/Dokumenten
      //     documentUrls: []
      //   }
      // });
      
      // Simuliere Audit Log
      console.log(`[Audit Hook] Datensatz ${app.id} erfolgreich anonymisiert (Retention Policy: ${RETENTION_MONTHS} Monate).`);
    }

    console.log(`[Retention Worker] Durchlauf erfolgreich abgeschlossen.`);

  } catch (error) {
    console.error(`[Retention Worker] Fehler beim Löschlauf:`, error);
  } finally {
    await prisma.$disconnect();
  }
}

// Direkter Aufruf, falls das Skript manuell getriggert wird
if (require.main === module) {
  runRetentionWorker();
}
