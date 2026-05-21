import { PrismaClient } from '@prisma/client';
import DOMPurify from 'isomorphic-dompurify';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

const prisma = new PrismaClient();

export default async function HomePage() {
  const page = await prisma.page.findUnique({ where: { slug: 'home' } });

  if (!page || !page.content) {
    return (
      <main style={{ padding: '6rem 0', textAlign: 'center' }}>
        <h1>Startseite noch leer</h1>
        <p>Bitte logge dich im Admin-Bereich ein und fülle die Startseite mit Inhalten.</p>
      </main>
    );
  }

  // We check if it is old Puck JSON data (starts with {) or new HTML
  let contentHtml = page.content;
  if (page.content.trim().startsWith('{')) {
    contentHtml = '<div style="text-align: center; padding: 4rem;"><h2>Hinweis</h2><p>Dies ist noch das alte Puck-Layout. Bitte öffne die Seite im Editor und speichere sie einmal als neuen Text ab.</p></div>';
  }

  // Dynamically insert latest published jobs if placeholder exists
  if (contentHtml.includes('{{LIVE_JOBS_LIST}}')) {
    try {
      const liveJobs = await prisma.jobPosting.findMany({
        where: { workflowState: { name: 'published' } },
        take: 4,
        orderBy: { createdAt: 'desc' },
        include: { location: true, jobFamily: true }
      });

      let jobsHtml = '';
      for (const job of liveJobs) {
        const locationName = job.location?.name || 'Campus Hamburg-Mitte';
        const categoryName = job.jobFamily?.name || 'Allgemein';
        const type = 'Vollzeit / Teilzeit';
        const salary = 'KTD Tarif + Zulagen';

        jobsHtml += `
          <a href="/jobs/${job.id}" class="job-list-item animate-fade-in" style="padding: 1.5rem 2rem; background: white; border-radius: 16px; border: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1.5rem; text-decoration: none; margin-bottom: 0.75rem;">
            <div style="flex: 1 1 500px;">
              <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--foreground); margin-bottom: 0.8rem; font-family: var(--font-outfit);">${job.title}</h3>
              <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; color: var(--muted); font-size: 0.9rem;">
                <span style="display: flex; align-items: center; gap: 0.4rem;">📍 <strong>${locationName}</strong></span>
                <span style="display: flex; align-items: center; gap: 0.4rem;">⏱️ ${type}</span>
                <span style="display: flex; align-items: center; gap: 0.4rem;">💶 ${salary}</span>
              </div>
            </div>
            <div style="display: flex; gap: 1rem; align-items: center;">
              <span class="badge" style="background: rgba(99,37,116,0.1); color: var(--primary); font-weight: 600;">${categoryName}</span>
              <span class="btn-primary" style="padding: 0.6rem 1.5rem; font-size: 0.95rem; border-radius: 8px;">Bewerben</span>
            </div>
          </a>
        `;
      }

      if (liveJobs.length === 0) {
        jobsHtml = '<div style="text-align: center; padding: 3rem; opacity: 0.6; border: 1px dashed var(--border); border-radius: 16px;">Derzeit sind keine offenen Stellen ausgeschrieben. Schauen Sie bald wieder vorbei oder senden Sie uns eine Initiativbewerbung!</div>';
      }

      contentHtml = contentHtml.replace('{{LIVE_JOBS_LIST}}', jobsHtml);
    } catch (err) {
      console.error("Error embedding live jobs on homepage:", err);
    }
  }

  const cleanHtml = DOMPurify.sanitize(contentHtml, {
    ADD_ATTR: ['target', 'style']
  });

  return (
    <main>
      <div 
        className="ql-editor prose prose-lg max-w-none" 
        style={{ padding: '0', background: 'var(--background)' }}
        dangerouslySetInnerHTML={{ __html: cleanHtml }} 
      />
    </main>
  );
}
