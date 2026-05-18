import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';

const CONTENT_DIR = 'c:/Users/Admin/Desktop/lv/content_text';

// Security: only allow safe slug chars
function isSafeSlug(slug: string) {
  return /^[a-zA-Z0-9_-]+$/.test(slug);
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!isSafeSlug(slug)) return NextResponse.json({ error: 'Invalid slug' }, { status: 400 });

  const filePath = `${CONTENT_DIR}/${slug}.md`;
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return NextResponse.json({ content, slug });
  } catch {
    return NextResponse.json({ error: 'File not found' }, { status: 404 });
  }
}

export async function PUT(req: NextRequest, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!isSafeSlug(slug)) return NextResponse.json({ error: 'Invalid slug' }, { status: 400 });

  const filePath = `${CONTENT_DIR}/${slug}.md`;
  try {
    const { content } = await req.json();
    fs.writeFileSync(filePath, content, 'utf8');
    return NextResponse.json({ success: true, slug });
  } catch {
    return NextResponse.json({ error: 'Could not save file' }, { status: 500 });
  }
}
