export const dynamic = 'force-dynamic';

import { PrismaClient } from '@prisma/client';
import Link from 'next/link';
import ApplicantDetailClient from './ApplicantDetailClient';
import ApplicantAIReview from './ApplicantAIReview';

const prisma = new PrismaClient();

export default async function ApplicantSuitabilityReview({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  const application = await prisma.application.findUnique({
    where: { id },
    include: {
      applicant: true,
      jobPosting: {
        include: { facility: true }
      }
    }
  });

  if (!application) {
    return <div style={{ padding: '4rem', textAlign: 'center' }}>Bewerbung nicht gefunden.</div>;
  }

  // Für Screening-Antworten aus dem JSON
  let screeningAnswers: Record<string, string> = {};
  try {
    if (application.screeningAnswersJson) {
      screeningAnswers = JSON.parse(application.screeningAnswersJson);
    }
  } catch (e) {}

  return (
    <main style={{ minHeight: '100vh', paddingBottom: '6rem', backgroundColor: 'var(--background)' }}>
      <div className="container" style={{ paddingTop: '2rem', paddingBottom: '2rem' }}>
        <Link href="/admin/applicants" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary)', fontWeight: 600 }}>
          <span>←</span> Zurück zur Übersicht
        </Link>
      </div>

      <div className="container" style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        
        {/* Applicant Details */}
        <div style={{ flex: '2 1 500px' }}>
          <div className="glass-panel">
            <div style={{ padding: '2rem', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary)', textTransform: 'uppercase' }}>
                Bewerbung für: {application.jobPosting.title} ({application.jobPosting.facility.name})
              </span>
              <h1 style={{ fontSize: '2rem', fontFamily: 'var(--font-outfit)', marginTop: '0.5rem' }}>
                {application.applicant.firstName} {application.applicant.lastName}
              </h1>
              <div style={{ display: 'flex', gap: '2rem', marginTop: '1rem', opacity: 0.8, fontSize: '0.9rem' }}>
                <span>📧 {application.applicant.email}</span>
                {application.applicant.phone && <span>📞 {application.applicant.phone}</span>}
                <span>📅 {application.createdAt.toLocaleDateString('de-DE')}</span>
              </div>
            </div>
            
            <div style={{ padding: '2rem', borderBottom: '1px solid var(--border)' }}>
              <h3 style={{ marginBottom: '1rem', fontFamily: 'var(--font-outfit)' }}>K.O.-Fragen (Screening)</h3>
              {Object.keys(screeningAnswers).length > 0 ? (
                <div style={{ display: 'grid', gap: '1rem' }}>
                  {Object.entries(screeningAnswers).map(([q, a], idx) => (
                    <div key={idx} style={{ padding: '1rem', backgroundColor: 'rgba(37, 99, 235, 0.05)', borderRadius: '8px' }}>
                      <strong style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.2rem', color: 'var(--primary)' }}>{q}</strong>
                      <span>{a as string}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ opacity: 0.6 }}>Keine spezifischen Screening-Fragen beantwortet.</p>
              )}
            </div>

            <div style={{ padding: '2rem' }}>
              <h3 style={{ marginBottom: '1rem', fontFamily: 'var(--font-outfit)' }}>Dokumente</h3>
              <div style={{ padding: '1rem', border: '1px solid var(--border)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1.2rem' }}>📄</span>
                  <strong>{application.cvStorageId || 'Lebenslauf.pdf'}</strong>
                </div>
                {/* Da wir MinIO hier mocken, zeigen wir nur einen Button ohne echte Funktion an */}
                <button className="btn-secondary" style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }} onClick={() => console.log('Mock: Download PDF')}>PDF Ansehen (Sicherer Link)</button>
              </div>
            </div>

            {/* AI Review Integration */}
            <ApplicantAIReview applicationId={application.id} />
          </div>
        </div>

        {/* Client-Side Controls (Status & Notizen) */}
        <div style={{ flex: '1 1 300px' }}>
          <ApplicantDetailClient 
            applicationId={application.id} 
            initialStatus={application.status} 
            initialNotes={application.internalNotes} 
          />
        </div>

      </div>
    </main>
  );
}
