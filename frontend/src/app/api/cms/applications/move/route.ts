import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function POST(req: NextRequest) {
  try {
    const { ticketId, stepIndex } = await req.json();
    if (!ticketId || stepIndex === undefined) return NextResponse.json({ error: 'Missing data' }, { status: 400 });

    // Finde das Ticket
    const ticket = await prisma.appTicket.findUnique({ where: { id: ticketId }, include: { workflow: true, steps: true } });
    if (!ticket) return NextResponse.json({ error: 'Ticket not found' }, { status: 404 });

    // Lösche alle alten Steps
    await prisma.appStep.deleteMany({ where: { appTicketId: ticketId } });

    // Setze den neuen Step (stepOrder = index)
    await prisma.appStep.create({
      data: {
        appTicketId: ticketId,
        stepOrder: stepIndex,
        status: 'PENDING',
        comments: 'Verschoben im Kanban'
      }
    });

    return NextResponse.json({ success: true });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
