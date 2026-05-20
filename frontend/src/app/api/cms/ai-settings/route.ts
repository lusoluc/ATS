export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const DEFAULT_AI_SETTINGS = {
  AI_TONE: 'EMPATHETIC',
  AI_LANGUAGE: 'DE_DU',
  AI_AUTO_REJECT_ENABLED: 'false',
  AI_THRESHOLD_D_REJECT: '15',
  AI_THRESHOLD_C_WAITLIST: '50',
  AI_THRESHOLD_A_INVITE: '80',
  AI_CV_LEARNING_MODE: 'true',
  AI_AGG_CHECK_ENABLED: 'true',
  AI_TRANSLATE_EASY_LANGUAGE: 'false'
};

export async function GET() {
  try {
    const settings = await prisma.systemSetting.findMany({
      where: { key: { startsWith: 'AI_' } }
    });

    const result = { ...DEFAULT_AI_SETTINGS };
    settings.forEach(s => {
      if (s.key in result) {
        (result as any)[s.key] = s.value;
      }
    });

    return NextResponse.json(result);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const data = await req.json();

    for (const [key, value] of Object.entries(data)) {
      if (key.startsWith('AI_')) {
        await prisma.systemSetting.upsert({
          where: { key },
          update: { value: String(value) },
          create: { key, value: String(value) }
        });
      }
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
