export const dynamic = 'force-dynamic';
import { NextResponse } from 'next/server';
import fs from 'fs';

const CONTENT_DIR = 'c:/Users/Admin/Desktop/lv/content_text';

export async function GET() {
  try {
    const files = fs.readdirSync(CONTENT_DIR)
      .filter(f => f.endsWith('.md'))
      .map(filename => {
        const slug = filename.replace('.md', '');
        const raw = fs.readFileSync(`${CONTENT_DIR}/${filename}`, 'utf8');
        // Extract a readable title from filename
        const title = slug
          .replace(/^_de_/, '')
          .replace(/_/g, ' ')
          .replace(/\b\w/g, l => l.toUpperCase());
        return { slug, title, size: raw.length };
      });
    return NextResponse.json({ files });
  } catch (e) {
    return NextResponse.json({ error: 'Could not read content directory' }, { status: 500 });
  }
}
