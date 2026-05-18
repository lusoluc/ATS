export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

// GET /api/cms/categories – alle Kategorien
// POST /api/cms/categories – neue Kategorie anlegen
export async function GET() {
  try {
    const categories = await prisma.jobFamily.findMany({ orderBy: { name: 'asc' } });
    return NextResponse.json({ categories });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const { name, description } = await req.json();
    if (!name) return NextResponse.json({ error: 'Name erforderlich' }, { status: 400 });
    const existing = await prisma.jobFamily.findFirst({ where: { name } });
    if (existing) return NextResponse.json({ error: 'Kategorie existiert bereits' }, { status: 409 });
    const category = await prisma.jobFamily.create({ data: { name, description: description || '' } });
    return NextResponse.json({ category }, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    const { id, name, archived } = await req.json();
    if (!id) return NextResponse.json({ error: 'ID erforderlich' }, { status: 400 });
    
    const updateData: any = {};
    if (name !== undefined) updateData.name = name;
    if (archived !== undefined) updateData.archived = archived;
    
    const category = await prisma.jobFamily.update({ where: { id }, data: updateData });
    return NextResponse.json({ category });
  } catch (e: any) {
    if (e.code === 'P2025') return NextResponse.json({ error: 'Kategorie nicht gefunden' }, { status: 404 });
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID fehlt' }, { status: 400 });
    await prisma.jobFamily.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch (e: any) {
    if (e.code === 'P2003') {
      return NextResponse.json({ error: 'Kann nicht gelöscht werden: Es existieren noch Stellenangebote mit diesem Berufsfeld.' }, { status: 409 });
    }
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
