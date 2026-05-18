export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// GET /api/cms/jobs – alle Jobs aus DB
export async function GET() {
  try {
    await ensureSeedData();
    const jobs = await prisma.jobPosting.findMany({
      include: { facility: true, location: true, jobFamily: true, workflowState: true, benefits: true, contactPerson: true },
      orderBy: { createdAt: 'desc' },
    });
    return NextResponse.json({ jobs });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// POST /api/cms/jobs – neuen Job anlegen
export async function POST(req: NextRequest) {
  try {
    await ensureSeedData();
    const body = await req.json();
    const { title, description, jobFamilyId, locationId, facilityId, departmentId, contactPersonId, workflowState, tasksJson, requirementsJson, screeningQuestionsJson, benefitIds } = body;
    
    if (!title) return NextResponse.json({ error: 'Titel ist erforderlich' }, { status: 400 });

    const org = await prisma.organization.findFirst();
    const facId = facilityId || (await prisma.facility.findFirst())?.id;
    const locId = locationId || (await prisma.location.findFirst())?.id;
    const famId = jobFamilyId || (await prisma.jobFamily.findFirst())?.id;
    const workflowRec = await prisma.workflowState.findFirst({ where: { name: workflowState || 'published' } }) || await prisma.workflowState.findFirst();

    if (!org || !facId || !locId || !famId || !workflowRec) {
      return NextResponse.json({ error: 'Stammdaten fehlen' }, { status: 500 });
    }

    const job = await prisma.jobPosting.create({
      data: { 
        title, 
        description: description || '', 
        tasksJson: tasksJson || '[]',
        requirementsJson: requirementsJson || '[]',
        screeningQuestionsJson: screeningQuestionsJson || '[]',
        organizationId: org.id, 
        facilityId: facId, 
        departmentId: departmentId || null,
        contactPersonId: contactPersonId || null,
        locationId: locId, 
        jobFamilyId: famId, 
        workflowStateId: workflowRec.id,
        benefits: {
          connect: benefitIds ? benefitIds.map((id: string) => ({ id })) : []
        }
      },
      include: { facility: true, location: true, jobFamily: true, workflowState: true, benefits: true },
    });
    return NextResponse.json({ job }, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// PUT /api/cms/jobs?id=... – Job aktualisieren
export async function PUT(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID fehlt' }, { status: 400 });
    
    const body = await req.json();
    const { title, description, jobFamilyId, locationId, facilityId, departmentId, contactPersonId, workflowState, tasksJson, requirementsJson, screeningQuestionsJson, benefitIds } = body;

    const workflowRec = workflowState ? await prisma.workflowState.findFirst({ where: { name: workflowState } }) : undefined;

    const job = await prisma.jobPosting.update({
      where: { id },
      data: {
        ...(title && { title }),
        ...(description !== undefined && { description }),
        ...(tasksJson !== undefined && { tasksJson }),
        ...(requirementsJson !== undefined && { requirementsJson }),
        ...(screeningQuestionsJson !== undefined && { screeningQuestionsJson }),
        ...(jobFamilyId && { jobFamilyId }),
        ...(locationId && { locationId }),
        ...(facilityId !== undefined && { facilityId }),
        ...(departmentId !== undefined && { departmentId: departmentId || null }),
        ...(contactPersonId !== undefined && { contactPersonId: contactPersonId || null }),
        ...(workflowRec && { workflowStateId: workflowRec.id }),
        ...(benefitIds !== undefined && {
          benefits: {
            set: benefitIds.map((bId: string) => ({ id: bId }))
          }
        })
      },
      include: { facility: true, location: true, jobFamily: true, workflowState: true, benefits: true },
    });
    return NextResponse.json({ job });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// DELETE /api/cms/jobs?id=...
export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID fehlt' }, { status: 400 });
    await prisma.jobPosting.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

async function ensureSeedData() {
  let org = await prisma.organization.findFirst();
  if (!org) org = await prisma.organization.create({ data: { name: 'Enterprise' } });
  let facility = await prisma.facility.findFirst();
  if (!facility) await prisma.facility.create({ data: { name: 'Psychiatrisches Zentrum Rickling', organizationId: org.id } });
  for (const name of ['draft', 'in_review', 'published', 'archived']) {
    if (!await prisma.workflowState.findFirst({ where: { name } })) await prisma.workflowState.create({ data: { name } });
  }
}
