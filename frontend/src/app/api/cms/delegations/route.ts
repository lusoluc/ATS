export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET() {
  try {
    // In einer echten App: Hole die User-ID aus dem JWT Token
    // Hier für den Prototyp holen wir einfach alle Delegationen, um sie anzuzeigen.
    const delegations = await prisma.roleDelegation.findMany({
      include: {
        delegator: true,
        delegatee: true,
      },
      orderBy: { createdAt: 'desc' }
    });

    const users = await prisma.user.findMany({ select: { id: true, email: true, role: true } });
    
    return NextResponse.json({ delegations, users });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const data = await req.json();
    
    // Einfache Validierung
    if (!data.delegatorId || !data.delegateeId || !data.scopeType || !data.validFrom || !data.validUntil) {
      return NextResponse.json({ error: 'Fehlende Pflichtfelder' }, { status: 400 });
    }

    if (data.delegatorId === data.delegateeId) {
      return NextResponse.json({ error: 'Man kann sich nicht selbst vertreten' }, { status: 400 });
    }

    const delegation = await prisma.roleDelegation.create({
      data: {
        delegatorId: data.delegatorId,
        delegateeId: data.delegateeId,
        scopeType: data.scopeType,
        scopeId: data.scopeId || null,
        validFrom: new Date(data.validFrom),
        validUntil: new Date(data.validUntil)
      }
    });

    return NextResponse.json({ success: true, delegation });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');

    if (!id) return NextResponse.json({ error: 'ID fehlt' }, { status: 400 });

    await prisma.roleDelegation.delete({ where: { id } });

    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
