export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { revalidatePath } from 'next/cache';
import * as fs from 'fs';
import * as path from 'path';

const prisma = new PrismaClient();
const CONTENT_DIR = 'c:/Users/Admin/Desktop/lv/content_text';

function toSlug(title: string) {
  return title
    .toLowerCase()
    .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

// GET /api/cms/pages  — alle Seiten (DB + Markdown-Dateien als Import-Kandidaten)
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const includeFiles = searchParams.get('includeFiles') === 'true';

    const pages = await prisma.page.findMany({ orderBy: [{ navOrder: 'asc' }, { createdAt: 'asc' }] });

    let fileSuggestions: { slug: string; title: string; source: 'file' }[] = [];
    if (includeFiles) {
      try {
        const files = fs.readdirSync(CONTENT_DIR).filter(f => f.endsWith('.md'));
        const existingSlugs = new Set(pages.map(p => p.slug));
        fileSuggestions = files
          .map(f => ({ slug: f.replace('.md', ''), title: f.replace('.md', '').replace(/_/g, ' '), source: 'file' as const }))
          .filter(f => !existingSlugs.has(f.slug));
      } catch { /* ignore */ }
    }

    return NextResponse.json({ pages, fileSuggestions });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// POST /api/cms/pages — neue Seite anlegen
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { title, slug: rawSlug, content, status, navEnabled, navLabel, navParent, navOrder, metaDesc, importFromFile } = body;
    if (!title) return NextResponse.json({ error: 'Titel ist erforderlich' }, { status: 400 });

    const slug = rawSlug ? rawSlug.trim() : toSlug(title);

    // Prüfen ob Slug schon existiert
    const existing = await prisma.page.findUnique({ where: { slug } });
    if (existing) return NextResponse.json({ error: `Slug "${slug}" existiert bereits.` }, { status: 409 });

    let pageContent = content || '';

    // Optional: Inhalt aus Markdown-Datei importieren
    if (importFromFile) {
      try {
        const filePath = path.join(CONTENT_DIR, `${slug}.md`);
        if (fs.existsSync(filePath)) pageContent = fs.readFileSync(filePath, 'utf-8');
      } catch { /* ignore */ }
    }

    const page = await prisma.page.create({
      data: {
        title,
        slug,
        content: pageContent,
        status: status || 'published',
        navEnabled: navEnabled !== false,
        navLabel: navLabel || null,
        navParent: navParent || null,
        navOrder: navOrder || 0,
        metaDesc: metaDesc || null,
      },
    });
    revalidatePath('/', 'layout');
    return NextResponse.json({ page }, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// PUT /api/cms/pages?id=...  — Seite aktualisieren
export async function PUT(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID fehlt' }, { status: 400 });

    const body = await req.json();
    const { title, slug: rawSlug, content, status, navEnabled, navLabel, navParent, navOrder, metaDesc } = body;

    // Slug-Kollision prüfen (außer mit sich selbst)
    if (rawSlug) {
      const collision = await prisma.page.findFirst({ where: { slug: rawSlug, NOT: { id } } });
      if (collision) return NextResponse.json({ error: `Slug "${rawSlug}" ist bereits von "${collision.title}" belegt.` }, { status: 409 });
    }

    const page = await prisma.page.update({
      where: { id },
      data: {
        ...(title !== undefined && { title }),
        ...(rawSlug !== undefined && { slug: rawSlug }),
        ...(content !== undefined && { content }),
        ...(status !== undefined && { status }),
        ...(navEnabled !== undefined && { navEnabled }),
        ...(navLabel !== undefined && { navLabel: navLabel || null }),
        ...(navParent !== undefined && { navParent: navParent || null }),
        ...(navOrder !== undefined && { navOrder }),
        ...(metaDesc !== undefined && { metaDesc: metaDesc || null }),
      },
    });
    revalidatePath('/', 'layout');
    return NextResponse.json({ page });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// DELETE /api/cms/pages?id=...
export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID fehlt' }, { status: 400 });
    await prisma.page.delete({ where: { id } });
    revalidatePath('/', 'layout');
    return NextResponse.json({ success: true });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
