export const dynamic = 'force-dynamic';
import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

const UPLOAD_DIR = 'c:/Users/Admin/Desktop/lv/frontend/public/uploads';

// GET /api/cms/images — alle hochgeladenen Bilder auflisten
export async function GET() {
  try {
    fs.mkdirSync(UPLOAD_DIR, { recursive: true });
    const files = fs.readdirSync(UPLOAD_DIR)
      .filter(f => /\.(jpe?g|png|gif|webp|svg)$/i.test(f))
      .map(f => ({
        name: f,
        url: `/uploads/${f}`,
        size: fs.statSync(path.join(UPLOAD_DIR, f)).size,
        mtime: fs.statSync(path.join(UPLOAD_DIR, f)).mtime,
      }))
      .sort((a, b) => new Date(b.mtime).getTime() - new Date(a.mtime).getTime());
    return NextResponse.json({ images: files });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// POST /api/cms/images — Bild hochladen (multipart/form-data)
export async function POST(req: NextRequest) {
  try {
    fs.mkdirSync(UPLOAD_DIR, { recursive: true });
    const formData = await req.formData();
    const file = formData.get('file') as File | null;
    if (!file) return NextResponse.json({ error: 'Keine Datei' }, { status: 400 });

    const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'];
    if (!allowed.includes(file.type)) return NextResponse.json({ error: 'Nur Bilder erlaubt (JPG, PNG, GIF, WebP, SVG)' }, { status: 400 });

    const maxSize = 8 * 1024 * 1024; // 8 MB
    if (file.size > maxSize) return NextResponse.json({ error: 'Datei zu groß (max. 8 MB)' }, { status: 400 });

    // Sicherer Dateiname: Timestamp + bereinigter Originalname
    const ext = path.extname(file.name).toLowerCase();
    const baseName = path.basename(file.name, ext).replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const fileName = `${Date.now()}_${baseName}${ext}`;
    const filePath = path.join(UPLOAD_DIR, fileName);

    const buffer = Buffer.from(await file.arrayBuffer());
    fs.writeFileSync(filePath, buffer);

    return NextResponse.json({ url: `/uploads/${fileName}`, name: fileName }, { status: 201 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// DELETE /api/cms/images?name=...
export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const name = searchParams.get('name');
    if (!name) return NextResponse.json({ error: 'Name fehlt' }, { status: 400 });
    // Sicherheit: keine Pfad-Traversal
    const safe = path.basename(name);
    const filePath = path.join(UPLOAD_DIR, safe);
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
    return NextResponse.json({ success: true });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
