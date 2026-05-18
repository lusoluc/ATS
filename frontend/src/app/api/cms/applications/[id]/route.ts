export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const body = await req.json();
    
    // BOLA-Check: Welche Facility darf dieser User sehen?
    // In Produktion kommt dies aus der Session (z.B. JWT Token oder NextAuth session)
    const userFacilityId = req.headers.get('x-user-facility-id'); 
    
    if (!userFacilityId) {
       return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const updateData: any = {};
    if (body.status !== undefined) updateData.status = body.status;
    if (body.internalNotes !== undefined) updateData.internalNotes = body.internalNotes;

    // STRICKTER BOLA CHECK: Update nur, wenn die Application zu einem Job gehört,
    // der in der Facility des eingeloggten Users liegt.
    const application = await prisma.application.update({
      where: { 
        id: id,
        // Prisma Relation Filter: Die Bewerbung muss an eine Facility gehen, 
        // für die der User Berechtigungen hat.
        jobPosting: {
           facilityId: userFacilityId
        }
      },
      data: updateData,
      include: {
        applicant: true
      }
    });

    if (body.status === 'INVITED' && body.generateSlots) {
      // Generate 3 dummy slots for tomorrow, the day after, and 3 days from now
      for (let i = 1; i <= 3; i++) {
        const d = new Date();
        d.setDate(d.getDate() + i);
        d.setHours(10 + i, 0, 0, 0); // e.g. 11:00, 12:00, 13:00

        const endD = new Date(d);
        endD.setHours(endD.getHours() + 1);

        await prisma.interviewSlot.create({
          data: {
            jobPostingId: application.jobPostingId,
            startTime: d,
            endTime: endD,
          }
        });
      }
      
      console.log(`[MAIL] An: ${application.applicant.email}\nBetreff: Einladung zum Kennenlernen!\nBitte wähle hier deinen Wunschtermin: http://localhost:3000/bewerber/termin`);
    } else if (body.status === 'INVITED') {
      console.log(`[MAIL] An: ${application.applicant.email}\nBetreff: Einladung zum Kennenlernen!\nWir werden dich zeitnah für eine Terminabsprache anrufen.`);
    }

    return NextResponse.json({ success: true, application });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
