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
  
  if (!profile) return { title: 'Einrichtung nicht gefunden | Landesverein Karriere' };

  return {
    title: `${profile.facility.name} | Landesverein Karriere`,
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
      
      {/* Hero Section (Facility Specific) */}
      <section className="hero-section" style={{ minHeight: '50vh', borderBottom: '1px solid var(--border)', backgroundColor: 'var(--primary)', color: 'white' }}>
        <div className="container" style={{ position: 'relative', zIndex: 10, paddingTop: '4rem' }}>
          <Link href="/jobs" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'rgba(255,255,255,0.8)', fontWeight: 600, marginBottom: '2rem' }}>
            ← Zurück zu den Jobs
          </Link>
          <h1 className="hero-title animate-fade-in opacity-0" style={{ fontSize: 'clamp(2.5rem, 5vw, 4rem)', textAlign: 'left', marginBottom: '1rem', fontFamily: 'var(--font-outfit)' }}>
            {fac.name}
          </h1>
          <p className="hero-subtitle animate-fade-in delay-100 opacity-0" style={{ textAlign: 'left', margin: '0', maxWidth: '800px', fontSize: '1.2rem', opacity: 0.9 }}>
            Entdecke deine Karrierechancen an diesem Standort.
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
              {mainContact.email && (
                <a href={`mailto:${mainContact.email}`} className="btn-secondary" style={{ width: '100%', display: 'block', textAlign: 'center', padding: '0.8rem' }}>
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
