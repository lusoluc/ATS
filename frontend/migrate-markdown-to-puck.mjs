import fs from 'fs';
import path from 'path';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const CONTENT_DIR = path.join(process.cwd(), '../content_text');

function mdToHtml(md) {
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

async function run() {
  if (!fs.existsSync(CONTENT_DIR)) {
    console.log("Ordner ../content_text nicht gefunden. Bitte aus dem Hauptordner ausführen oder prüfen ob er existiert.");
    return;
  }

  const files = fs.readdirSync(CONTENT_DIR).filter(f => f.endsWith('.md'));
  
  for (const file of files) {
    const slug = file.replace('.md', '').replace(/^_de_/, '').replace(/_$/, '').replace(/_/g, '-');
    const rawContent = fs.readFileSync(path.join(CONTENT_DIR, file), 'utf8');
    
    // Extract title
    let title = slug.replace(/-/g, ' ');
    const titleMatch = rawContent.match(/^#+\s+(.+)$/m);
    if (titleMatch) title = titleMatch[1].trim();

    // Convert markdown to HTML for the Puck TextBlock
    const htmlContent = mdToHtml(rawContent);

    const puckJson = {
      content: [
        {
          type: "HeroBlock",
          props: {
            title: title,
            subtitle: "Importiert aus alter Version",
            alignment: "left",
            titleSize: "medium",
            textColor: "dark",
            id: `hero-${Date.now()}`
          }
        },
        {
          type: "TextBlock",
          props: {
            content: htmlContent,
            size: "default",
            color: "default",
            align: "left",
            id: `text-${Date.now()}`
          }
        }
      ],
      root: { props: { title: title } },
      zones: {}
    };

    const existing = await prisma.page.findUnique({ where: { slug } });
    if (existing) {
      await prisma.page.update({
        where: { slug },
        data: { content: JSON.stringify(puckJson) }
      });
      console.log(`[Update] ${slug}`);
    } else {
      await prisma.page.create({
        data: {
          slug,
          title,
          content: JSON.stringify(puckJson),
          status: 'published',
          navEnabled: false
        }
      });
      console.log(`[Erstellt] ${slug}`);
    }
  }
}

run().catch(console.error).finally(() => prisma.$disconnect());
