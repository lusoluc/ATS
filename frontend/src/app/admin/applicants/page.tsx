export const dynamic = 'force-dynamic';

import Link from 'next/link';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export default async function ApplicantListPage() {
  const applications = await prisma.application.findMany({
    include: {
      applicant: true,
      jobPosting: {
        include: { facility: true }
      }
    },
    orderBy: { createdAt: 'desc' }
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'NEW': return { bg: '#e0e7ff', text: '#3730a3' }; // Blue
      case 'IN_REVIEW': return { bg: '#fef3c7', text: '#92400e' }; // Yellow
      case 'INVITED': return { bg: '#dcfce3', text: '#166534' }; // Green
      case 'REJECTED': return { bg: '#fee2e2', text: '#991b1b' }; // Red
      default: return { bg: '#f3f4f6', text: '#374151' }; // Gray
    }
  };

  return (
    <main style={{ minHeight: '100vh', padding: '4rem 2rem', backgroundColor: 'var(--background)' }}>
      <div className="container" style={{ maxWidth: '1200px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontFamily: 'var(--font-outfit)', fontSize: '2.5rem' }}>Bewerbungseingang</h1>
          <span style={{ padding: '0.5rem 1rem', backgroundColor: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '0.9rem' }}>
            ATS Dashboard
          </span>
        </div>

        <div className="glass-panel" style={{ backgroundColor: 'var(--card-bg)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: 'rgba(0,0,0,0.02)', borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '1.5rem', fontWeight: 600 }}>Eingang</th>
                <th style={{ padding: '1.5rem', fontWeight: 600 }}>Bewerber*in</th>
                <th style={{ padding: '1.5rem', fontWeight: 600 }}>Stelle & Standort</th>
                <th style={{ padding: '1.5rem', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '1.5rem', fontWeight: 600 }}>Notizen</th>
                <th style={{ padding: '1.5rem', fontWeight: 600, textAlign: 'right' }}>Aktion</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((app: any) => {
                const colors = getStatusColor(app.status);
                return (
                  <tr key={app.id} style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.2s' }}>
                    <td style={{ padding: '1.5rem', opacity: 0.7, fontSize: '0.9rem' }}>
                      {app.createdAt.toLocaleDateString('de-DE')}
                    </td>
                    <td style={{ padding: '1.5rem' }}>
                      <strong>{app.applicant.firstName} {app.applicant.lastName}</strong>
                      <div style={{ fontSize: '0.8rem', opacity: 0.6 }}>{app.applicant.email}</div>
                    </td>
                    <td style={{ padding: '1.5rem', opacity: 0.9 }}>
                      {app.jobPosting.title}
                      <div style={{ fontSize: '0.8rem', opacity: 0.6 }}>{app.jobPosting.facility.name}</div>
                    </td>
                    <td style={{ padding: '1.5rem' }}>
                      <span style={{ 
                        padding: '0.25rem 0.75rem', 
                        borderRadius: '50px', 
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        backgroundColor: colors.bg,
                        color: colors.text
                      }}>
                        {app.status}
                      </span>
                    </td>
                    <td style={{ padding: '1.5rem', opacity: 0.7, fontSize: '0.9rem', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {app.internalNotes ? app.internalNotes : '-'}
                    </td>
                    <td style={{ padding: '1.5rem', textAlign: 'right' }}>
                      <Link href={`/admin/applicants/${app.id}`} className="btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
                        Details ansehen
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {applications.length === 0 && (
            <div style={{ padding: '3rem', textAlign: 'center', opacity: 0.6 }}>Keine Bewerbungen im System.</div>
          )}
        </div>
      </div>
    </main>
  );
}
