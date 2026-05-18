export const dynamic = 'force-dynamic';

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export default async function AdminCalendarPage() {
  // Holt alle ausstehenden Interviews (Gebucht)
  const interviews = await prisma.interview.findMany({
    include: {
      application: {
        include: { applicant: true, jobPosting: true }
      }
    },
    orderBy: { scheduledAt: 'asc' },
    where: { scheduledAt: { gte: new Date() } }
  });

  // Holt alle offenen Slots, die noch nicht gebucht wurden
  const openSlots = await prisma.interviewSlot.findMany({
    where: { isBooked: false, startTime: { gte: new Date() } },
    include: { jobPosting: true },
    orderBy: { startTime: 'asc' }
  });

  return (
    <main style={{ minHeight: '100vh', padding: '4rem 2rem', backgroundColor: 'var(--background)' }}>
      <div className="container" style={{ maxWidth: '1200px' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <div>
            <h1 style={{ fontFamily: 'var(--font-outfit)', fontSize: '2.5rem' }}>HR Kalender</h1>
            <p style={{ opacity: 0.8 }}>Zentrale Verwaltung für Interviews und freie Slots.</p>
          </div>
          <button className="btn-primary" style={{ padding: '0.8rem 1.5rem' }}>
            + Regel erstellen / Slots generieren
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
          
          {/* Feste, gebuchte Termine */}
          <div className="glass-panel" style={{ padding: '2rem', backgroundColor: 'var(--card-bg)' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', color: '#166534', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
              📅 Bevorstehende Interviews (Gebucht)
            </h2>
            
            {interviews.length > 0 ? (
              <div style={{ display: 'grid', gap: '1rem' }}>
                {interviews.map(inv => (
                  <div key={inv.id} style={{ padding: '1.5rem', border: '1px solid #bbf7d0', backgroundColor: '#f0fdf4', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <strong style={{ fontSize: '1.1rem', color: '#166534' }}>
                        {inv.scheduledAt.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit' })} • {inv.scheduledAt.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })} Uhr
                      </strong>
                      <span style={{ fontSize: '0.85rem', padding: '0.2rem 0.5rem', backgroundColor: '#166534', color: 'white', borderRadius: '4px' }}>
                        {inv.locationType}
                      </span>
                    </div>
                    <div style={{ fontWeight: 600 }}>{inv.application.applicant.firstName} {inv.application.applicant.lastName}</div>
                    <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>Für: {inv.application.jobPosting.title}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ opacity: 0.6 }}>Keine anstehenden Interviews gebucht.</p>
            )}
          </div>

          {/* Offene Slots */}
          <div className="glass-panel" style={{ padding: '2rem', backgroundColor: 'var(--card-bg)' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', color: '#b45309', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
              ⏳ Offene Verfügbarkeiten (Ungebucht)
            </h2>
            
            {openSlots.length > 0 ? (
              <div style={{ display: 'grid', gap: '1rem' }}>
                {openSlots.map(slot => (
                  <div key={slot.id} style={{ padding: '1rem', border: '1px dashed #fcd34d', backgroundColor: '#fffbeb', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong style={{ display: 'block', color: '#b45309' }}>
                        {slot.startTime.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit' })} • {slot.startTime.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })} Uhr
                      </strong>
                      <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>Für Job: {slot.jobPosting.title}</span>
                    </div>
                    <button style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1.2rem' }} title="Slot löschen">
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ opacity: 0.6 }}>Keine offenen Slots vorhanden. Bewerber können aktuell keine Termine selbst wählen.</p>
            )}
            
            <div style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: 'rgba(59, 130, 246, 0.05)', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.1)' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Regeln (Demnächst)</h3>
              <p style={{ fontSize: '0.85rem', opacity: 0.8 }}>Hier kannst du später Regeln definieren wie: "Immer Dienstags 10:00 - 14:00 Uhr". Das System füllt die offenen Slots dann automatisch auf.</p>
            </div>
          </div>

        </div>
      </div>
    </main>
  );
}
