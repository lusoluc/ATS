import { notFound } from 'next/navigation';
import Link from 'next/link';
import * as fs from 'fs';
import * as path from 'path';
import { PrismaClient } from '@prisma/client';
import DOMPurify from 'isomorphic-dompurify';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

const prisma = new PrismaClient();
const CONTENT_DIR = 'c:/Users/Admin/Desktop/lv/content_texte';

async function getPage(slug: string) {
  // 1. DB zuerst
  try {
    const page = await prisma.page.findUnique({ where: { slug } });
    if (page && page.status === 'published') return { title: page.title, content: page.content, metaDesc: page.metaDesc, source: 'db' as const };
  } catch { /* ignore */ }

  // 2. Fallback: Markdown-Datei
  try {
    const safeName = slug.replace(/[^a-zA-Z0-9_\-]/g, '');
    const filePath = path.join(CONTENT_DIR, `${safeName}.md`);
    if (fs.existsSync(filePath)) {
      const raw = fs.readFileSync(filePath, 'utf-8');
      const title = raw.match(/^#\s+(.+)/m)?.[1] || slug;
      return { title, content: raw, metaDesc: null, source: 'file' as const };
    }
  } catch { /* ignore */ }

  return null;
}

// Minimal Markdown → HTML (ohne externe Deps)
function mdToHtml(md: string): string {
  return md
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%;border-radius:8px;margin:1rem 0;" />')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" style="color:var(--primary);text-decoration:underline;">$1</a>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]*<\/li>)/, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[h|u|l|p])/gm, '<p>')
    .replace(/<p><\/p>/g, '');
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = await getPage(slug);
  if (!page) return { title: 'Seite nicht gefunden | Enterprise' };
  return {
    title: `${page.title} | Enterprise Karriere`,
    description: page.metaDesc || `${page.title} – Enterprise Schleswig-Holstein`,
  };
}

import { PuckRenderer } from './PuckRenderer';

export default async function InfoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = await getPage(slug);
  if (!page) notFound();

  let isPuck = false;
  let puckData = null;

  try {
    puckData = JSON.parse(page.content);
    if (puckData && puckData.content) {
      isPuck = true;
    }
  } catch (e) {
    // Es ist kein JSON, also normales Markdown
  }

  if (isPuck) {
    return (
      <main style={{ minHeight: '100vh', paddingBottom: '5rem', background: '#f9fafb' }}>
        <PuckRenderer data={puckData} />
      </main>
    );
  }

  const rawHtml = mdToHtml(page.content);
  // XSS Protection
  const html = DOMPurify.sanitize(rawHtml);

  return (
    <main style={{ minHeight: '100vh', paddingBottom: '5rem' }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)', color: 'white', padding: '3.5rem 0 4rem' }}>
        <div className="container animate-fade-in opacity-0">
          <Link href="/" style={{ fontSize: '0.85rem', opacity: 0.7, display: 'inline-block', marginBottom: '1rem' }}>← Startseite</Link>
          <h1 style={{ fontFamily: 'var(--font-outfit)', fontSize: 'clamp(1.8rem,4vw,2.8rem)', fontWeight: 900, lineHeight: 1.15, color: 'white' }}>
            {page.title}
          </h1>
        </div>
      </div>

      {/* Content */}
      <div className="container animate-fade-in delay-100 opacity-0" style={{ maxWidth: '780px', paddingTop: '3rem', marginTop: '-2rem' }}>
        <div style={{ background: 'var(--surface)', borderRadius: '16px', padding: 'clamp(1.5rem,4vw,3rem)', boxShadow: 'var(--shadow)' }}>
          <article
            className="markdown-content"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        </div>
      </div>
    </main>
  );
}
