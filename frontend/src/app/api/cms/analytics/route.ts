import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(req: NextRequest) {
  try {
    // 1. Globale Metriken
    const totalJobs = await prisma.jobPosting.count({ where: { status: 'PUBLISHED' } });
    const totalApplications = await prisma.application.count();
    
    // 2. Bewerber pro Standort (Top 5)
    const applicantsByFacility = await prisma.application.findMany({
      select: {
        jobPosting: { select: { facility: { select: { name: true } } } }
      }
    });

    const facilityCounts: Record<string, number> = {};
    applicantsByFacility.forEach(app => {
      const name = app.jobPosting?.facility?.name || 'Unbekannt';
      facilityCounts[name] = (facilityCounts[name] || 0) + 1;
    });

    const topFacilities = Object.entries(facilityCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, count]) => ({ name, count }));

    // 3. Bottleneck Analyse (Wie viele Bewerber hängen in welchem Step fest)
    const tickets = await prisma.appTicket.findMany({
      include: { steps: { orderBy: { stepOrder: 'asc' } }, workflow: true }
    });

    const bottlenecks: Record<string, number> = {};
    tickets.forEach(ticket => {
      const currentStepOrder = ticket.steps?.[0]?.stepOrder || 0;
      let stepName = `Schritt ${currentStepOrder + 1}`;
      try {
        const wfSteps = JSON.parse(ticket.workflow?.stepsJson || '[]');
        if (wfSteps[currentStepOrder]) {
          stepName = wfSteps[currentStepOrder].name;
        }
      } catch {}
      bottlenecks[stepName] = (bottlenecks[stepName] || 0) + 1;
    });

    const bottleneckData = Object.entries(bottlenecks)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([step, count]) => ({ step, count }));

    return NextResponse.json({
      metrics: {
        totalJobs,
        totalApplications,
        conversionRate: totalJobs > 0 ? ((totalApplications / (totalJobs * 150)) * 100).toFixed(1) : 0 // Simulierte Views (150 pro Job)
      },
      topFacilities,
      bottlenecks: bottleneckData
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
