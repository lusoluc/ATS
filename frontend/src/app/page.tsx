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

  const cleanHtml = DOMPurify.sanitize(contentHtml);

  return (
    <main>
      <div 
        className="ql-editor prose prose-lg max-w-none container" 
        style={{ padding: '4rem 1rem', background: 'var(--background)' }}
        dangerouslySetInnerHTML={{ __html: cleanHtml }} 
      />
    </main>
  );
}
