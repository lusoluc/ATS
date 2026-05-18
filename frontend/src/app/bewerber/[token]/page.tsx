import { PrismaClient } from '@prisma/client';
import { notFound } from 'next/navigation';
import { revalidatePath } from 'next/cache';

const prisma = new PrismaClient();

export default async function ApplicantPortal({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;

  const appToken = await prisma.applicantToken.findUnique({
    where: { token },
    include: {
      applicant: {
        include: {
          applications: {
            orderBy: { createdAt: 'desc' },
            take: 1,
            include: { jobPosting: true, interviewSlot: true }
          }
        }
      }
    }
  });

  if (!appToken || appToken.expiresAt < new Date()) {
    return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--background)' }}>
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', backgroundColor: 'var(--card-bg)' }}>
          <h1 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Link abgelaufen oder ungültig</h1>
          <p>Bitte fordere einen neuen Link an oder wende dich an HR.</p>
        </div>
      </main>
    );
  }

  const applicant = appToken.applicant;
  const application = applicant.applications[0];

  if (!application) {
    return <div>Keine aktive Bewerbung gefunden.</div>;
  }

  let availableSlots: any[] = [];
  if (application.status === 'INVITED' && !application.interviewSlot) {
    availableSlots = await prisma.interviewSlot.findMany({
      where: {
        jobPostingId: application.jobPostingId,
        isBooked: false,
        startTime: { gt: new Date() }
      },
      orderBy: { startTime: 'asc' }
    });
  }

  async function bookSlot(formData: FormData) {
    'use server';
    const slotId = formData.get('slotId') as string;
    if (!slotId) return;

    await prisma.interviewSlot.update({
      where: { id: slotId },
      data: { isBooked: true, applicationId: application.id }
    });

    const slot = await prisma.interviewSlot.findUnique({ where: { id: slotId }});
    if (slot) {
      await prisma.interview.create({
        data: {
          applicationId: application.id,
          scheduledAt: slot.startTime,
          locationType: 'IN_PERSON' // Placeholder, could be REMOTE
        }
      });
    }

    revalidatePath(`/bewerber/${token}`);
  }

  return (
    <main style={{ minHeight: '100vh', padding: '4rem 2rem', backgroundColor: 'var(--background)' }}>
      <div className="container" style={{ maxWidth: '800px' }}>
        
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1 style={{ fontFamily: 'var(--font-outfit)', fontSize: '2.5rem', color: 'var(--primary)' }}>
            Hallo {applicant.firstName}!
          </h1>
          <p style={{ fontSize: '1.1rem', opacity: 0.8 }}>Willkommen in deinem Bewerber-Portal.</p>
        </div>

        <div className="glass-panel" style={{ padding: '2rem', backgroundColor: 'var(--card-bg)', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
            Dein aktueller Status für: {application.jobPosting.title}
          </h2>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.5rem', backgroundColor: 'rgba(59, 130, 246, 0.05)', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem' }}>
              {application.status === 'NEW' && '📬'}
              {application.status === 'IN_REVIEW' && '🔍'}
              {application.status === 'INVITED' && '🎉'}
              {application.status === 'REJECTED' && '😔'}
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--primary)' }}>
                {application.status === 'NEW' && 'Bewerbung eingegangen'}
                {application.status === 'IN_REVIEW' && 'Wird aktuell vom Fachbereich geprüft'}
                {application.status === 'INVITED' && 'Du bist eingeladen!'}
                {application.status === 'REJECTED' && 'Absage'}
              </div>
              <div style={{ fontSize: '0.9rem', opacity: 0.7, marginTop: '0.2rem' }}>
                Zuletzt aktualisiert am {application.updatedAt.toLocaleDateString('de-DE')}
              </div>
            </div>
          </div>
        </div>

        {/* --- OPTIONALES CALENDLY FEATURE --- */}
        {application.status === 'INVITED' && (
          <div className="glass-panel" style={{ padding: '2rem', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0' }}>
            
            {application.interviewSlot ? (
              <div style={{ textAlign: 'center' }}>
                <h3 style={{ color: '#166534', marginBottom: '1rem' }}>✅ Termin bestätigt!</h3>
                <p>Wir freuen uns auf dich am:</p>
                <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#166534', margin: '1rem 0' }}>
                  {application.interviewSlot.startTime.toLocaleString('de-DE', { dateStyle: 'full', timeStyle: 'short' })} Uhr
                </div>
                <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>Weitere Details senden wir dir in Kürze per E-Mail.</p>
              </div>
            ) : (
              <div>
                <h3 style={{ color: '#166534', marginBottom: '1rem' }}>Bitte wähle einen Termin</h3>
                
                {availableSlots.length > 0 ? (
                  <div style={{ display: 'grid', gap: '1rem' }}>
                    {availableSlots.map(slot => (
                      <form action={bookSlot} key={slot.id}>
                        <input type="hidden" name="slotId" value={slot.id} />
                        <button type="submit" style={{ width: '100%', padding: '1rem', backgroundColor: 'white', border: '1px solid #bbf7d0', borderRadius: '8px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', transition: 'all 0.2s', fontWeight: 600, color: '#166534' }}>
                          <span>📅 {slot.startTime.toLocaleDateString('de-DE', { weekday: 'long', day: '2-digit', month: 'long' })}</span>
                          <span>⏰ {slot.startTime.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })} Uhr</span>
                        </button>
                      </form>
                    ))}
                  </div>
                ) : (
                  <p style={{ opacity: 0.7 }}>
                    Wir melden uns telefonisch bei dir für die Terminabsprache!
                  </p>
                )}
              </div>
            )}
            
          </div>
        )}

      </div>
    </main>
  );
}
