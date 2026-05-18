export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { decryptBuffer } from '../../../../../../lib/encryption';

const prisma = new PrismaClient();
const SECURE_STORAGE_PATH = join(process.cwd(), '..', 'storage', 'applicants', 'cv');

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const userFacilityId = req.headers.get('x-user-facility-id');

    if (!userFacilityId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const application = await prisma.application.findUnique({
      where: { 
        id,
        jobPosting: { facilityId: userFacilityId } // BOLA Protection
      },
      include: { applicant: true }
    });

    if (!application || !application.cvStorageId) {
      return NextResponse.json({ error: 'Not found' }, { status: 404 });
    }

    // 1. DSGVO Audit Log: Wer hat wann diesen CV gelesen?
    await (prisma as any).auditLog.create({
      data: {
        action: 'READ_CV',
        userId: req.headers.get('x-user-id') || 'UNKNOWN_HR_USER',
        applicationId: application.id,
        metadataJson: JSON.stringify({ 
          ip: req.headers.get('x-forwarded-for') || '127.0.0.1',
          applicantEmail: application.applicant.email 
        })
      }
    });

    // 2. Lese die verschlüsselte Datei
    const filepath = join(SECURE_STORAGE_PATH, application.cvStorageId);
    const encryptedBuffer = await readFile(filepath);

    // 3. Entschlüsseln (AES-256-GCM)
    const decryptedBuffer = decryptBuffer(encryptedBuffer);

    // 4. Als PDF ausliefern
    return new NextResponse(new Uint8Array(decryptedBuffer), {
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'inline; filename="Lebenslauf.pdf"', // Inline = Ansicht im Browser
        'Cache-Control': 'no-store, max-age=0' // Lebensläufe dürfen niemals im Browser-Cache landen!
      }
    });

  } catch (error: any) {
    console.error('CV Read Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
