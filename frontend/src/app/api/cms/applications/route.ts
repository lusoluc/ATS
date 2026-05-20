export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const search = url.searchParams.get('q') || '';
    const workflowId = url.searchParams.get('workflowId') || '';

    // Wir holen alle Bewerbungen. Für das Kanban-Board brauchen wir die AppTickets und AppSteps.
    const tickets = await prisma.appTicket.findMany({
      where: {
        ...(workflowId ? { workflowId } : {}),
        application: {
          applicant: {
            OR: [
              { firstName: { contains: search } },
              { lastName: { contains: search } },
              { email: { contains: search } }
            ]
          }
        }
      },
      include: {
        workflow: true,
        steps: { orderBy: { stepOrder: 'asc' } },
        application: {
          include: {
            applicant: true,
            jobPosting: {
              include: { location: true, jobFamily: true }
            }
          }
        }
      },
      orderBy: { createdAt: 'desc' }
    });

    return NextResponse.json({ tickets });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
