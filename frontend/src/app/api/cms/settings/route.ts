export const dynamic = 'force-dynamic';
import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET() {
  try {
    const settings = await prisma.systemSetting.findMany({ orderBy: { key: 'asc' } });
    const templates = await prisma.emailTemplate.findMany({ orderBy: { name: 'asc' } });
    
    return NextResponse.json({ settings, templates });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { type, data } = body; // type = 'setting' | 'template'

    if (type === 'setting') {
      const { key, value } = data;
      await prisma.systemSetting.upsert({
        where: { key },
        update: { value },
        create: { key, value }
      });
      return NextResponse.json({ success: true });
    }

    if (type === 'template') {
      const { id, name, subject, htmlContent, textContent } = data;
      if (id) {
        await prisma.emailTemplate.update({
          where: { id },
          data: { name, subject, htmlContent, textContent }
        });
      } else {
        await prisma.emailTemplate.create({
          data: { name, subject, htmlContent, textContent }
        });
      }
      return NextResponse.json({ success: true });
    }

    return NextResponse.json({ error: 'Invalid type' }, { status: 400 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
