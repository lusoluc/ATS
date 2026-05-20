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
  if (!job) return { title: 'Job nicht gefunden | Enterprise' };
  return {
    title: `${job.title} | Enterprise Karriere`,
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
      "sameAs": "https://www.Enterprise.de" // should be dynamic, but good enough for generic Open Source template
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
      
      {/* 1. HERO SECTION (Workwise: Authentische Bilder & Mobile First) */}
      <section style={{ 
        position: 'relative',
        background: 'var(--primary)', 
        color: 'white', 
        padding: '6rem 0 4rem',
        overflow: 'hidden'
      }}>
        {/* Authentisches Hintergrundbild (Abgedunkelt) */}
        <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
          <img 
            src="https://images.unsplash.com/photo-1584515979956-d9319b9ce4f9?q=80&w=2000&auto=format&fit=crop" 
            alt="Team Nordicum Health" 
            style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.2 }} 
          />
          <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to right, var(--primary) 0%, rgba(10,37,64,0.8) 100%)' }}></div>
        </div>

        <div className="container" style={{ position: 'relative', zIndex: 10 }}>
          <Link href="/jobs" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'rgba(255,255,255,0.8)', fontWeight: 600, fontSize: '0.95rem', marginBottom: '2.5rem', transition: 'color 0.2s' }}>
            ← Zurück zur Stellenübersicht
          </Link>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <span style={{ display: 'inline-block', padding: '0.4rem 1.2rem', background: 'var(--secondary)', color: 'white', borderRadius: '50px', fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }}>
              {job.jobFamily.name}
            </span>
            {/* Workwise: Arbeitgebermarke / Kununu */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(10px)', padding: '0.35rem 1rem', borderRadius: '50px', fontSize: '0.85rem', fontWeight: 700, border: '1px solid rgba(255,255,255,0.2)' }}>
              <span style={{ color: '#4ade80' }}>★</span> 4.6 (Kununu Top Company)
            </div>
          </div>
          
          <h1 style={{ fontSize: 'clamp(2.5rem, 5vw, 4rem)', fontFamily: 'var(--font-outfit)', margin: '0 0 2.5rem', lineHeight: 1.1, maxWidth: '1000px', fontWeight: 900, textShadow: '0 4px 20px rgba(0,0,0,0.3)' }}>
            {job.title}
          </h1>

          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
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

          <div style={{ marginTop: '4rem', padding: '2.5rem', background: '#f8fafc', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontSize: '1.5rem', color: 'var(--primary)', marginBottom: '1rem', fontFamily: 'var(--font-outfit)' }}>Lerne dein Team kennen</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '1.5rem', alignItems: 'center' }}>
              <div style={{ width: '120px', height: '120px', borderRadius: '50%', overflow: 'hidden', border: '4px solid white', boxShadow: '0 10px 25px rgba(0,0,0,0.1)' }}>
                <img src="https://images.unsplash.com/photo-1559839734-2b71ea197ec2?q=80&w=200&auto=format&fit=crop" alt="Teammitglied" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
              <div>
                <p style={{ margin: 0, color: '#475569', lineHeight: 1.6, fontStyle: 'italic', fontSize: '1.1rem' }}>
                  "Bei uns wird niemand ins kalte Wasser geworfen. Wir haben ein echtes Mentoring-Programm in den ersten 6 Monaten und helfen uns immer gegenseitig. Ich freue mich auf dich!"
                </p>
                <p style={{ margin: '0.5rem 0 0', fontWeight: 700, color: 'var(--text)' }}>— Julian, dein zukünftiger Kollege</p>
              </div>
            </div>
          </div>
        </div>

        <div style={{ flex: '0 1 380px', position: 'sticky', top: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Bewerbungs-Card (Workwise: Klarer CTA & Mobile Friendly) */}
          <div style={{ background: 'white', padding: '2.5rem 2rem', borderRadius: '16px', boxShadow: '0 10px 40px rgba(0,0,0,0.06)', border: '1px solid rgba(0,0,0,0.05)' }}>
            <h3 style={{ fontSize: '1.6rem', fontFamily: 'var(--font-outfit)', marginBottom: '0.5rem', color: 'var(--primary)', fontWeight: 800 }}>Bereit für den Wechsel?</h3>
            <p style={{ color: '#64748b', marginBottom: '2rem', fontSize: '1rem', lineHeight: 1.6 }}>
              Bewirb dich jetzt in unter 2 Minuten. Du brauchst <strong>kein Anschreiben</strong> – ein Lebenslauf (oder Link) reicht völlig!
            </p>
            <Link href={`/bewerben?jobId=${job.id}`} className="btn-primary" style={{ display: 'block', textAlign: 'center', fontSize: '1.15rem', padding: '1.1rem', width: '100%', borderRadius: '8px', boxShadow: '0 8px 20px rgba(0, 80, 255, 0.25)', marginBottom: '1rem' }}>
              🚀 1-Klick Bewerbung
            </Link>
            {/* Workwise: Mobile Recruiting / WhatsApp */}
            <a href="https://wa.me/4912345678?text=Hallo%20Nordicum-Team,%20ich%20interessiere%20mich%20f%C3%BCr%20den%20Job..." target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', width: '100%', padding: '1rem', borderRadius: '8px', background: 'rgba(37,211,102,0.1)', color: '#16a34a', fontWeight: 700, textDecoration: 'none', transition: 'background 0.2s' }}>
              💬 Per WhatsApp bewerben
            </a>
            
            <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.85rem', color: '#94a3b8' }}>Job-ID: {job.id.substring(0,8).toUpperCase()} • Ohne Frist</p>
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
