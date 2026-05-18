export const dynamic = 'force-dynamic';
import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET() {
  try {
    const [facilities, departments, contacts, benefits, snippets] = await Promise.all([
      prisma.facility.findMany({ select: { id: true, name: true } }),
      prisma.department.findMany({ select: { id: true, name: true, facilityId: true } }),
      prisma.contactPerson.findMany({ select: { id: true, firstName: true, lastName: true, globalJobTitle: true } }),
      prisma.benefit.findMany({ select: { id: true, name: true, icon: true } }),
      prisma.textSnippet.findMany({ select: { id: true, category: true, content: true, jobFamilyId: true } }),
    ]);

    return NextResponse.json({
      facilities,
      departments,
      contacts,
      benefits,
      snippets
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
