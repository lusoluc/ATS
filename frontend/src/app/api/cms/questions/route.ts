export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET() {
  try {
    const questions = await prisma.screeningQuestion.findMany({
      orderBy: { createdAt: 'desc' }
    });
    return NextResponse.json({ questions });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const { question } = await req.json();
    if (!question) return NextResponse.json({ error: 'Frage fehlt' }, { status: 400 });

    const q = await prisma.screeningQuestion.create({ data: { question } });
    return NextResponse.json(q);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    const { id, question, archived } = await req.json();
    if (!id) return NextResponse.json({ error: 'ID fehlt' }, { status: 400 });

    const data: any = {};
    if (question !== undefined) data.question = question;
    if (archived !== undefined) data.archived = archived;

    const q = await prisma.screeningQuestion.update({ where: { id }, data });
    return NextResponse.json(q);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID fehlt' }, { status: 400 });

    await prisma.screeningQuestion.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
