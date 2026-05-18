export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(req: NextRequest) {
  try {
    const subscriptions = await prisma.jobAlertSubscription.findMany({
      orderBy: { createdAt: 'desc' },
      include: {
        _count: {
          select: { logs: { where: { action: 'ALERT_SENT' } } }
        }
      }
    });
    
    // Quick KPI calculations
    const total = subscriptions.length;
    const active = subscriptions.filter(s => s.status === 'active' || s.status === 'ACTIVE').length;
    const inactive = total - active;

    return NextResponse.json({ subscriptions, kpis: { total, active, inactive } });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, locations, categories, status } = body;
    
    const existing = await prisma.jobAlertSubscription.findUnique({ where: { email } });
    if (existing) return NextResponse.json({ error: 'Diese E-Mail existiert bereits' }, { status: 400 });

    const created = await prisma.jobAlertSubscription.create({
      data: {
        email,
        locations: locations || '[]',
        categories: categories || '[]',
        status: status || 'ACTIVE',
      }
    });
    return NextResponse.json({ success: true, created });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    const body = await req.json();
    const { id, email, locations, categories, status } = body;
    const updated = await prisma.jobAlertSubscription.update({
      where: { id },
      data: { 
        ...(email !== undefined && { email }),
        ...(locations !== undefined && { locations }),
        ...(categories !== undefined && { categories }),
        ...(status !== undefined && { status })
      }
    });
    return NextResponse.json({ success: true, updated });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID is missing' }, { status: 400 });

    await prisma.jobAlertSubscription.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
