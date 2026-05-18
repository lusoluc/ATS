export const dynamic = 'force-dynamic';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { PrismaClient } from '@prisma/client';
import ReactMarkdown from 'react-markdown';

const prisma = new PrismaClient();

async function getJob(id: string) {
  try {
    return await prisma.jobPosting.findUnique({
      where: { id },
      include: { 
        facility: { include: { profile: true } }, 
        location: true, 
        jobFamily: true, 
        workflowState: true,
        contactPerson: true,
        benefits: true,
        organization: true
      },
    });
  } catch (e) {
    console.error("PRISMA ERROR IN GETJOB:", e);
    return null;
  }
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const job = await getJob(id);
  if (!job) return { title: 'Job nicht gefunden | Landesverein' };
  return {
    title: `${job.title} | Landesverein Karriere`,
    description: `Stellenangebot: ${job.title} in ${job.location.name}. Jetzt bewerben!`,
  };
}

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const job = await getJob(id);
  if (!job) notFound();

  // Parse JSON arrays, fallback to empty arrays if parsing fails
  let tasks: string[] = [];
  let requirements: string[] = [];
  try { tasks = JSON.parse(job.tasksJson || '[]'); } catch(e){}
  try { requirements = JSON.parse(job.requirementsJson || '[]'); } catch(e){}

  const hasModularContent = tasks.length > 0 || requirements.length > 0;

  // JSON-LD für Google for Jobs
  const jsonLd = {
    "@context": "https://schema.org/",
    "@type": "JobPosting",
    "title": job.title,
    "description": job.description || job.title,
    "identifier": {
      "@type": "PropertyValue",
      "name": job.organization.name,
      "value": job.id
    },
    "datePosted": job.createdAt.toISOString(),
    "validThrough": job.updatedAt ? new Date(job.updatedAt.getTime() + 90 * 24 * 60 * 60 * 1000).toISOString() : undefined, // +90 days roughly
    "employmentType": "FULL_TIME", // Fallback, could be dynamic
    "hiringOrganization": {
      "@type": "Organization",
      "name": job.organization.name,
      "sameAs": "https://www.landesverein.de" // should be dynamic, but good enough for generic Open Source template
    },
    "jobLocation": {
      "@type": "Place",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": job.location.address || "",
        "addressLocality": job.location.city || "",
        "postalCode": job.location.postalCode || "",
        "addressCountry": "DE"
      }
    }
  };

  return (
    <main style={{ minHeight: '100vh', paddingBottom: '6rem', backgroundColor: '#f9f9fb' }}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      
      {/* 1. HERO SECTION */}
      <section style={{ 
        background: 'linear-gradient(135deg, var(--primary) 0%, #4a1542 100%)', 
        color: 'white', 
        padding: '5rem 0 4rem',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Dekoratives Hintergrund-Muster */}
        <div style={{ position: 'absolute', right: '-10%', top: '-20%', width: '500px', height: '500px', background: 'rgba(255,255,255,0.03)', borderRadius: '50%', border: '40px solid rgba(255,255,255,0.05)' }}></div>
        <div style={{ position: 'absolute', left: '-5%', bottom: '-20%', width: '300px', height: '300px', background: 'rgba(255,255,255,0.03)', borderRadius: '50%', border: '20px solid rgba(255,255,255,0.05)' }}></div>

        <div className="container" style={{ position: 'relative', zIndex: 10 }}>
          <Link href="/jobs" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'rgba(255,255,255,0.8)', fontWeight: 600, fontSize: '0.9rem', marginBottom: '2rem', transition: 'color 0.2s' }}>
            ← Zurück zur Stellenübersicht
          </Link>

          <span style={{ display: 'inline-block', padding: '0.4rem 1rem', background: 'rgba(255,255,255,0.15)', borderRadius: '50px', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '1.5rem', backdropFilter: 'blur(10px)' }}>
            {job.jobFamily.name}
          </span>
          
          <h1 style={{ fontSize: 'clamp(2.2rem, 5vw, 3.5rem)', fontFamily: 'var(--font-outfit)', margin: '0 0 2rem', lineHeight: 1.1, maxWidth: '900px' }}>
            {job.title}
          </h1>

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {[
              { icon: '📍', label: job.location.name, desc: 'Standort' },
              { icon: '🏢', label: job.facility.name, desc: 'Einrichtung', link: job.facility.profile?.slug ? `/einrichtungen/${job.facility.profile.slug}` : undefined },
            ].map((b, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1.25rem', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.15)' }}>
                <span style={{ fontSize: '1.5rem' }}>{b.icon}</span>
                <div>
                  <div style={{ fontSize: '0.7rem', opacity: 0.7, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{b.desc}</div>
                  {b.link ? (
                    <Link href={b.link} style={{ fontSize: '0.95rem', fontWeight: 600, color: 'white', textDecoration: 'underline' }}>{b.label}</Link>
                  ) : (
                    <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>{b.label}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 2. MAIN CONTENT & SIDEBAR */}
      <div className="container" style={{ display: 'flex', gap: '3rem', flexWrap: 'wrap', alignItems: 'flex-start', marginTop: '-2rem', position: 'relative', zIndex: 20 }}>
        
        {/* Linke Spalte: Job Description */}
        <div style={{ flex: '1 1 650px', background: 'white', padding: '3rem', borderRadius: '16px', boxShadow: '0 10px 40px rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.05)' }}>
          <style dangerouslySetInnerHTML={{__html: `
            .markdown-content h3 { font-family: var(--font-outfit); font-size: 1.6rem; color: var(--primary); margin: 2.5rem 0 1rem; }
            .markdown-content p { margin-bottom: 1.2rem; line-height: 1.8; color: #4b5563; font-size: 1.05rem; }
            .markdown-content ul { list-style: none; padding-left: 0; margin-bottom: 2rem; }
            .markdown-content li { position: relative; padding-left: 2rem; margin-bottom: 0.8rem; line-height: 1.6; color: #4b5563; font-size: 1.05rem; }
            .markdown-content li::before { content: "✓"; position: absolute; left: 0; top: 2px; color: var(--secondary); font-weight: bold; font-size: 1.2rem; background: rgba(224, 147, 42, 0.15); width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
            .markdown-content strong { color: var(--foreground); font-weight: 700; }
          `}} />
          
          <div className="markdown-content">
            {/* Modular Content */}
            {hasModularContent && (
              <>
                {tasks.length > 0 && (
                  <>
                    <h3>Deine Aufgaben</h3>
                    <ul>
                      {tasks.map((task, i) => <li key={i}>{task}</li>)}
                    </ul>
                  </>
                )}
                {requirements.length > 0 && (
                  <>
                    <h3>Dein Profil</h3>
                    <ul>
                      {requirements.map((req, i) => <li key={i}>{req}</li>)}
                    </ul>
                  </>
                )}
              </>
            )}

            {/* Legacy Markdown Fallback */}
            {job.description && (
              <ReactMarkdown>{job.description}</ReactMarkdown>
            )}
            
            {/* Dynamic Benefits */}
            {job.benefits.length > 0 && (
              <div style={{ marginTop: '3rem' }}>
                <h3>Unsere Benefits</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
                  {job.benefits.map(b => (
                    <div key={b.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', padding: '1rem', background: '#f9fafb', borderRadius: '12px', border: '1px solid #f3f4f6' }}>
                      <span style={{ fontSize: '1.5rem', lineHeight: 1 }}>{b.icon || '✨'}</span>
                      <div>
                        <strong style={{ display: 'block', fontSize: '0.95rem', color: 'var(--foreground)', marginBottom: '0.2rem' }}>{b.name}</strong>
                        {b.description && <span style={{ fontSize: '0.85rem', color: '#6b7280', lineHeight: 1.4 }}>{b.description}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div style={{ marginTop: '4rem', padding: '2rem', background: 'rgba(133,172,55,0.05)', borderRadius: '16px', border: '1px solid rgba(133,172,55,0.2)' }}>
            <h3 style={{ fontSize: '1.4rem', color: 'var(--green-dark)', marginBottom: '1rem', fontFamily: 'var(--font-outfit)' }}>Wir sind klimaneutral auf dem Weg</h3>
            <p style={{ margin: 0, color: '#4b5563', lineHeight: 1.6 }}>Nachhaltigkeit ist uns wichtig. Mit Dienstradleasing, Ökostrom und regionaler Verpflegung setzen wir uns für die Schöpfung ein.</p>
          </div>
        </div>

        {/* Rechte Spalte: Sidebar & CTA */}
        <div style={{ flex: '0 1 380px', position: 'sticky', top: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Bewerbungs-Card */}
          <div style={{ background: 'white', padding: '2rem', borderRadius: '16px', boxShadow: '0 10px 40px rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.05)' }}>
            <h3 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-outfit)', marginBottom: '0.5rem', color: 'var(--primary)' }}>Interesse geweckt?</h3>
            <p style={{ color: '#6b7280', marginBottom: '1.5rem', fontSize: '0.95rem', lineHeight: 1.5 }}>
              Bewirb dich jetzt in weniger als 3 Minuten. Kein langes Anschreiben nötig!
            </p>
            <Link href={`/bewerben?jobId=${job.id}`} className="btn-primary" style={{ display: 'block', textAlign: 'center', fontSize: '1.1rem', padding: '1rem', width: '100%', borderRadius: '8px' }}>
              🚀 Jetzt bewerben
            </Link>
            <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.8rem', color: '#9ca3af' }}>Referenz: {job.id} • Frist: fortlaufend</p>
          </div>

          {/* Ansprechpartner-Card */}
          {job.contactPerson && (
            <div style={{ background: 'white', padding: '2rem', borderRadius: '16px', boxShadow: '0 10px 40px rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.05)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                {job.contactPerson.photoUrl ? (
                  <img src={job.contactPerson.photoUrl} alt={job.contactPerson.firstName} style={{ width: '64px', height: '64px', borderRadius: '50%', border: '2px solid var(--secondary)', objectFit: 'cover' }} />
                ) : (
                  <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: 'bold' }}>
                    {job.contactPerson.firstName[0]}{job.contactPerson.lastName[0]}
                  </div>
                )}
                <div>
                  <h4 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--foreground)' }}>{job.contactPerson.firstName} {job.contactPerson.lastName}</h4>
                  <p style={{ margin: 0, fontSize: '0.85rem', color: '#6b7280' }}>{job.contactPerson.globalJobTitle || 'Ansprechpartner*in'}</p>
                </div>
              </div>
              
              {job.contactPerson.quote && (
                <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px', borderLeft: '4px solid var(--secondary)', marginBottom: '1.5rem', fontStyle: 'italic', fontSize: '0.9rem', color: '#4b5563', lineHeight: 1.5 }}>
                  "{job.contactPerson.quote}"
                </div>
              )}
              
              <p style={{ fontSize: '0.95rem', color: '#4b5563', marginBottom: '1.5rem', lineHeight: 1.5 }}>
                Hast du Fragen zum Bewerbungsprozess oder zur Stelle? Ich helfe dir gerne direkt weiter!
              </p>

              <style dangerouslySetInnerHTML={{__html: `
                .contact-link { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; border-radius: 8px; text-decoration: none; font-size: 0.95rem; transition: background 0.2s; }
                .contact-link.gray { background: #f3f4f6; color: var(--foreground); font-weight: 500; }
                .contact-link.gray:hover { background: #e5e7eb; }
                .contact-link.green { background: rgba(37,211,102,0.1); color: #16a34a; font-weight: 600; }
                .contact-link.green:hover { background: rgba(37,211,102,0.2); }
              `}} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {job.contactPerson.phone && (
                  <a href={`tel:${job.contactPerson.phone.replace(/\\s+/g, '')}`} className="contact-link gray">
                    📞 {job.contactPerson.phone}
                  </a>
                )}
                {job.contactPerson.email && (
                  <a href={`mailto:${job.contactPerson.email}`} className="contact-link gray">
                    ✉️ E-Mail schreiben
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
