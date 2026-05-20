import Link from 'next/link';
import { notFound } from 'next/navigation';
import { PrismaClient } from '@prisma/client';
import { PuckRenderer } from '../../info/[slug]/PuckRenderer';

const prisma = new PrismaClient();

async function getFacilityProfile(slug: string) {
  try {
    return await prisma.facilityProfile.findUnique({
      where: { slug },
      include: {
        facility: {
          include: {
            jobPostings: {
              where: { workflowState: { name: 'published' } },
              include: { jobFamily: true, location: true }
            },
            contacts: {
              include: { contactPerson: true }
            }
          }
        }
      }
    });
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const profile = await getFacilityProfile(slug);
  
  if (!profile) return { title: 'Einrichtung nicht gefunden | Enterprise Karriere' };

  return {
    title: `${profile.facility.name} | Enterprise Karriere`,
    description: profile.description || `Karriere in der Einrichtung ${profile.facility.name}. Erfahre mehr über uns und unsere offenen Stellen.`
  };
}

export default async function FacilityDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const profile = await getFacilityProfile(slug);

  if (!profile) notFound();

  const fac = profile.facility;
  const activeJobs = fac.jobPostings;
  // Wir nehmen den ersten Kontakt für das Profil, falls vorhanden
  const mainContactLink = fac.contacts[0];
  const mainContact = mainContactLink?.contactPerson;

  return (
    <main style={{ minHeight: '100vh', backgroundColor: 'var(--background)', paddingBottom: '6rem' }}>
      
      {/* Hero Section (Workwise: Authentische Bilder & Local Branding) */}
      <section className="hero-section" style={{ minHeight: '55vh', backgroundColor: 'var(--primary)', color: 'white', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
          <img 
            src="/hospital_exterior.png" 
            alt={`Standort ${fac.name}`} 
            style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.3 }} 
          />
          <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, var(--primary) 0%, transparent 100%)' }}></div>
        </div>

        <div className="container" style={{ position: 'relative', zIndex: 10, paddingTop: '6rem', paddingBottom: '3rem', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', height: '100%' }}>
          <Link href="/jobs" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'rgba(255,255,255,0.9)', fontWeight: 600, marginBottom: '2rem', transition: 'color 0.2s' }}>
            ← Zurück zu allen Jobs
          </Link>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <span style={{ display: 'inline-block', padding: '0.4rem 1.2rem', background: 'var(--secondary)', color: 'white', borderRadius: '50px', fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }}>
              📍 {fac.name}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(10px)', padding: '0.35rem 1rem', borderRadius: '50px', fontSize: '0.85rem', fontWeight: 700, border: '1px solid rgba(255,255,255,0.2)' }}>
              <span style={{ color: '#4ade80' }}>★</span> 4.8 (Mitarbeiterbewertung)
            </div>
          </div>

          <h1 className="hero-title animate-fade-in opacity-0" style={{ fontSize: 'clamp(2.5rem, 5vw, 4.5rem)', textAlign: 'left', marginBottom: '1rem', fontFamily: 'var(--font-outfit)', textShadow: '0 4px 20px rgba(0,0,0,0.3)', fontWeight: 900 }}>
            {fac.name}
          </h1>
          <p className="hero-subtitle animate-fade-in delay-100 opacity-0" style={{ textAlign: 'left', margin: '0', maxWidth: '800px', fontSize: '1.25rem', opacity: 0.9, lineHeight: 1.6 }}>
            Modernste Ausstattung, ein kollegiales Team vor Ort und echte Karrierechancen. Entdecke, was unseren Standort besonders macht.
          </p>
        </div>
      </section>

      <div className="container" style={{ marginTop: '4rem', display: 'flex', gap: '4rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
        
        {/* Main Content (Left) */}
        <div style={{ flex: '2 1 600px' }} className="animate-fade-in delay-200 opacity-0">
          <h2 style={{ fontSize: '2rem', fontFamily: 'var(--font-outfit)', marginBottom: '1.5rem', color: 'var(--primary)' }}>Über diese Einrichtung</h2>
          <div style={{ opacity: 0.9, fontSize: '1.1rem', lineHeight: 1.8, marginBottom: '3rem', color: 'var(--foreground)' }}>
            {(() => {
              try {
                const data = JSON.parse(profile.description || '{}');
                if (data.content) {
                  return <PuckRenderer data={data} />;
                }
              } catch (e) {}
              return <p>{profile.description || "Hier entsteht die neue Informationsseite für diese Einrichtung."}</p>;
            })()}
          </div>

          <h2 style={{ fontSize: '2rem', fontFamily: 'var(--font-outfit)', marginBottom: '1.5rem', color: 'var(--primary)' }}>Offene Stellen hier ({activeJobs.length})</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {activeJobs.length === 0 && (
              <div style={{ padding: '2rem', background: 'var(--card-bg)', borderRadius: '12px', opacity: 0.7 }}>
                Zurzeit gibt es hier keine offenen Stellenangebote.
              </div>
            )}
            {activeJobs.map((job) => (
              <div key={job.id} className="card" style={{ padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ flex: '1 1 250px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--primary)', textTransform: 'uppercase', fontWeight: 600 }}>{job.jobFamily.name}</span>
                  <h3 style={{ fontSize: '1.2rem', marginTop: '0.2rem', color: 'var(--foreground)', marginBottom: '0.2rem' }}>{job.title}</h3>
                  <p style={{ fontSize: '0.85rem', color: '#6b7280', margin: '0' }}>📍 {job.location.name}</p>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <Link href={`/jobs/${job.id}`} className="btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
                    Details ansehen
                  </Link>
                  <Link href={`/bewerben?jobId=${job.id}`} className="btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
                    🚀 Direkt bewerben
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar (Right) */}
        <div style={{ flex: '1 1 350px', position: 'sticky', top: '100px' }} className="animate-fade-in delay-300 opacity-0">
          
          {mainContact ? (
            <div className="glass-panel" style={{ padding: '2rem', backgroundColor: 'var(--card-bg)', marginBottom: '2rem' }}>
              <h3 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-outfit)', marginBottom: '1rem', color: 'var(--primary)' }}>Ansprechpartner*in vor Ort</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                {mainContact.photoUrl ? (
                  <img src={mainContact.photoUrl} alt={mainContact.firstName} style={{ width: '60px', height: '60px', borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--secondary)' }} />
                ) : (
                  <div style={{ width: '60px', height: '60px', borderRadius: '50%', backgroundColor: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>
                    {mainContact.firstName[0]}{mainContact.lastName[0]}
                  </div>
                )}
                <div>
                  <strong style={{ display: 'block', fontSize: '1.1rem', color: 'var(--foreground)' }}>{mainContact.firstName} {mainContact.lastName}</strong>
                  <span style={{ opacity: 0.7, fontSize: '0.9rem' }}>{mainContactLink.roleTitle || mainContact.globalJobTitle}</span>
                </div>
              </div>
              {mainContact.phone && (
                <a href={`tel:${mainContact.phone.replace(/\\s+/g, '')}`} className="btn-secondary" style={{ width: '100%', display: 'block', textAlign: 'center', padding: '0.8rem', marginBottom: '0.5rem' }}>
                  📞 Anrufen
                </a>
              )}
              {/* Workwise: WhatsApp Integration */}
              <a href="https://wa.me/4912345678" target="_blank" rel="noreferrer" style={{ width: '100%', display: 'block', textAlign: 'center', padding: '0.8rem', marginBottom: '0.5rem', backgroundColor: 'rgba(37,211,102,0.1)', color: '#16a34a', borderRadius: '8px', fontWeight: 600, textDecoration: 'none', transition: 'background 0.2s' }}>
                💬 Per WhatsApp schreiben
              </a>
              {mainContact.email && (
                <a href={`mailto:${mainContact.email}`} className="btn-outline" style={{ width: '100%', display: 'block', textAlign: 'center', padding: '0.8rem' }}>
                  ✉️ Nachricht senden
                </a>
              )}
            </div>
          ) : (
            <div className="glass-panel" style={{ padding: '2rem', backgroundColor: 'var(--card-bg)', marginBottom: '2rem' }}>
              <h3 style={{ fontSize: '1.2rem', fontFamily: 'var(--font-outfit)', marginBottom: '1rem' }}>Initiativbewerbung</h3>
              <p style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '1rem' }}>Kein passender Job dabei? Wir freuen uns immer über motivierte Talente.</p>
              <Link href="/bewerben" className="btn-primary" style={{ width: '100%', display: 'block', textAlign: 'center', padding: '0.8rem' }}>
                Jetzt initiativ bewerben
              </Link>
            </div>
          )}

          {/* Geo Map Placeholder */}
          <div className="glass-panel" style={{ padding: '1rem', backgroundColor: 'var(--card-bg)' }}>
            <div style={{ width: '100%', height: '200px', backgroundColor: 'var(--border)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundImage: 'linear-gradient(45deg, rgba(37, 99, 235, 0.1) 0%, rgba(167, 243, 208, 0.2) 100%)' }}>
               <span style={{ opacity: 0.6, fontWeight: 500 }}>📍 Einrichtung auf Karte</span>
            </div>
          </div>

        </div>

      </div>
    </main>
  );
}
