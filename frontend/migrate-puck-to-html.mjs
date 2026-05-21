import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function migrate() {
  console.log('Starte Migration von Puck-JSON zu purem HTML...');
  const pages = await prisma.page.findMany();
  
  let migratedCount = 0;

  for (const page of pages) {
    if (!page.content || !page.content.trim().startsWith('{')) {
      continue;
    }

    try {
      const data = JSON.parse(page.content);
      if (!data.content || !Array.isArray(data.content)) {
        continue;
      }

      console.log(`Migriere Seite: ${page.slug} (${page.title})`);
      
      let htmlOutput = '';

      for (const block of data.content) {
        if (!block.props) continue;
        
        switch (block.type) {
          case 'Hero':
          case 'HomeHero':
            if (block.props.title) htmlOutput += `<h1>${block.props.title}</h1>\n`;
            if (block.props.subtitle) htmlOutput += `<p><strong>${block.props.subtitle}</strong></p>\n`;
            break;
            
          case 'FeatureList':
          case 'HomeTargetGroups':
          case 'HomeBenefits':
            if (block.props.title) htmlOutput += `<h2>${block.props.title}</h2>\n`;
            if (block.props.description) htmlOutput += `<p>${block.props.description}</p>\n`;
            if (Array.isArray(block.props.features)) {
              htmlOutput += `<ul>\n`;
              for (const f of block.props.features) {
                htmlOutput += `  <li><strong>${f.title}</strong>: ${f.description}</li>\n`;
              }
              htmlOutput += `</ul>\n`;
            }
            if (Array.isArray(block.props.items)) {
              htmlOutput += `<ul>\n`;
              for (const i of block.props.items) {
                htmlOutput += `  <li><strong>${i.title}</strong>: ${i.desc}</li>\n`;
              }
              htmlOutput += `</ul>\n`;
            }
            break;

          case 'Text':
            if (block.props.text) htmlOutput += `<p>${block.props.text}</p>\n`;
            break;
            
          case 'HomeStatBar':
            htmlOutput += `<h2>Statistiken</h2>\n`;
            if (Array.isArray(block.props.stats)) {
              htmlOutput += `<ul>\n`;
              for (const s of block.props.stats) {
                htmlOutput += `  <li><strong>${s.value}</strong>: ${s.label}</li>\n`;
              }
              htmlOutput += `</ul>\n`;
            }
            break;

          case 'HomeEmployerBranding':
          case 'HomeJobsTeaser':
            if (block.props.title) htmlOutput += `<h2>${block.props.title}</h2>\n`;
            if (block.props.contactText) htmlOutput += `<p>${block.props.contactText}</p>\n`;
            break;

          case 'HomeFAQ':
            if (block.props.title) htmlOutput += `<h2>${block.props.title}</h2>\n`;
            if (Array.isArray(block.props.faqs)) {
              for (const faq of block.props.faqs) {
                htmlOutput += `<h3>${faq.q}</h3>\n<p>${faq.a}</p>\n`;
              }
            }
            break;
            
          default:
            // Generic catch-all for any other blocks with title/text
            if (block.props.title) htmlOutput += `<h2>${block.props.title}</h2>\n`;
            if (block.props.description) htmlOutput += `<p>${block.props.description}</p>\n`;
            if (block.props.text) htmlOutput += `<p>${block.props.text}</p>\n`;
            break;
        }
      }

      if (htmlOutput.trim() === '') {
        console.log(`Überspringe ${page.slug} (Kein extrahierbarer Text gefunden)`);
        continue;
      }

      await prisma.page.update({
        where: { id: page.id },
        data: { content: htmlOutput }
      });
      console.log(`✅ ${page.slug} erfolgreich zu HTML migriert.`);
      migratedCount++;

    } catch (err) {
      console.error(`Fehler bei Seite ${page.slug}:`, err);
    }
  }

  console.log(`\n🎉 Migration abgeschlossen! ${migratedCount} Seiten wurden aktualisiert.`);
}

migrate()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
