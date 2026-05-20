import fs from 'fs';
import path from 'path';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const CONTENT_DIR = path.join(process.cwd(), 'content_text');

async function importPages() {
  const files = fs.readdirSync(CONTENT_DIR).filter(f => f.endsWith('.md'));
  let created = 0;
  let updated = 0;

  for (const file of files) {
    const slug = file.replace('.md', '');
    const content = fs.readFileSync(path.join(CONTENT_DIR, file), 'utf8');

    // Versuche den Titel aus der ersten Überschrift (z.B. "# Titel") zu extrahieren
    let title = slug.replace(/_/g, ' ').trim();
    const match = content.match(/^#+\s+(.+)$/m);
    if (match) {
      title = match[1].trim();
    }

    const existing = await prisma.page.findUnique({ where: { slug } });
    if (existing) {
      await prisma.page.update({
        where: { slug },
        data: { content, title }
      });
      updated++;
    } else {
      await prisma.page.create({
        data: {
          slug,
          title,
          content,
          status: 'published',
          navEnabled: false, // Standardmäßig nicht im Menü anzeigen, da es 40 sind
        }
      });
      created++;
    }
  }

  console.log(`Import abgeschlossen! Erstellt: ${created}, Aktualisiert: ${updated}`);
}

importPages()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
