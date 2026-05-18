export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { action, applicationId, metadata } = body;
    
    if (!action) {
      return NextResponse.json({ error: 'Action is required' }, { status: 400 });
    }

    // Identifiziere den Nutzer aus dem Header (wird via Middleware/Auth gesetzt)
    const userId = req.headers.get('x-user-id') || 'UNKNOWN_OR_GUEST_USER';
    
    // Erfasse Umgebungsvariablen für Troubleshooting
    const ip = req.headers.get('x-forwarded-for') || '127.0.0.1';
    const userAgent = req.headers.get('user-agent') || 'Unknown';
    const url = req.headers.get('referer') || req.url;

    const finalMetadata = {
      ...metadata,
      ip,
      userAgent,
      url,
      timestamp: new Date().toISOString()
    };

    // (prisma as any) wegen Type-Generierungs Problemen im Build
    await (prisma as any).auditLog.create({
      data: {
        action,
        userId,
        applicationId: applicationId || null,
        metadataJson: JSON.stringify(finalMetadata)
      }
    });

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error('Audit Log Error:', error);
    return NextResponse.json({ error: 'Failed to create audit log' }, { status: 500 });
  }
}
