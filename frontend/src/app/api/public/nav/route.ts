export const dynamic = 'force-dynamic';
import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// GET /api/public/nav — dynamische Navigation aus DB
export async function GET() {
  try {
    const pages = await prisma.page.findMany({
      where: { status: 'published', navEnabled: true },
      orderBy: [{ navParent: 'asc' }, { navOrder: 'asc' }],
      select: { title: true, slug: true, navLabel: true, navParent: true, navOrder: true },
    });
    return NextResponse.json({ pages });
  } catch (e: any) {
    return NextResponse.json({ pages: [] });
  }
}
