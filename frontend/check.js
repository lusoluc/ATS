const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function check() {
  const footer = await prisma.page.findUnique({where: {slug: '_global_footer'}});
  console.log('Footer exists?', !!footer);
  if (footer && !footer.content.includes('/impressum')) {
    console.log('Footer does NOT contain impressum link!');
  } else {
    console.log('Footer contains impressum link or does not exist');
  }

  const impressum = await prisma.page.findUnique({where: {slug: 'impressum'}});
  if (!impressum) {
    console.log('Impressum page missing! Creating...');
    await prisma.page.create({
      data: {
        title: 'Impressum',
        slug: 'impressum',
        status: 'published',
        content: JSON.stringify({
          content: [
            {
              type: "Hero",
              props: { title: "Impressum", subtitle: "Rechtliche Angaben", align: "center", backgroundColor: "#f8fafc", textColor: "#0f172a" }
            },
            {
              type: "TextContent",
              props: {
                content: "Angaben gemäß § 5 TMG:\n\nSecurATS GmbH\nMusterstraße 123\n10115 Berlin\n\nVertreten durch:\nDr. Max Mustermann\n\nKontakt:\nTelefon: +49 (0) 30 12345678\nE-Mail: info@securats.de\n\nRegistereintrag:\nEintragung im Handelsregister.\nRegistergericht: Amtsgericht Charlottenburg (Berlin)\nRegisternummer: HRB 123456 B",
                align: "left"
              }
            }
          ],
          root: {},
          zones: {}
        })
      }
    });
    console.log('Impressum created.');
  } else {
    console.log('Impressum page already exists.');
  }
}
check().finally(() => prisma.$disconnect());
