import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(req: NextRequest) {
  try {
    const workflows = await prisma.appWorkflowDef.findMany({
      include: {
        facility: { select: { name: true } }
      },
      orderBy: { createdAt: 'desc' }
    });
    return NextResponse.json({ workflows });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    if (body.id) {
      const updated = await prisma.appWorkflowDef.update({
        where: { id: body.id },
        data: {
          name: body.name,
          locationIdsJson: body.locationIdsJson || '[]',
          stepsJson: body.stepsJson
        }
      });
      return NextResponse.json(updated);
    } else {
      const created = await prisma.appWorkflowDef.create({
        data: {
          name: body.name,
          locationIdsJson: body.locationIdsJson || '[]',
          stepsJson: body.stepsJson
        }
      });
      return NextResponse.json(created);
    }
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const id = url.searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'Missing ID' }, { status: 400 });
    
    // Check if workflow is used by any tickets
    const tickets = await prisma.appTicket.count({ where: { workflowId: id } });
    if (tickets > 0) {
      return NextResponse.json({ error: `Workflow wird von ${tickets} aktiven Bewerbung(en) genutzt und kann nicht gelöscht werden.` }, { status: 400 });
    }

    await prisma.appWorkflowDef.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
