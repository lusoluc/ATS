import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const pageData = {
  slug: 'funktionen/ai-recruiting',
  title: 'KI-gestütztes Recruiting (RAG)',
  navEnabled: true,
  navLabel: 'KI & Automatisierung',
  navParent: 'funktionen',
  status: 'published',
  content: JSON.stringify({
    content: [
      {
        type: "Hero",
        props: {
          title: "Das Recruiting-System, das mitlernt.",
          subtitle: "Kontext-basiertes KI-Scoring mit 4 Effizienz-Kategorien (A bis D).",
          align: "center",
          padding: "120px",
          bgColor: "#111827",
          textColor: "#ffffff"
        }
      },
      {
        type: "FeatureList",
        props: {
          title: "Intelligentes Matching durch Contextual RAG",
          description: "Unsere KI vergleicht neue Bewerber nicht mit einem generischen Modell, sondern mit den Profilen eurer eigenen Top-Performer – gefiltert nach exaktem Standort und Berufsfeld.",
          features: [
            { title: "Kategorie A (>80%)", description: "Der perfekte Match. Das System kann diese Kandidaten vollautomatisch zum Interview einladen.", icon: "⭐" },
            { title: "Kategorie B (50-80%)", description: "Solide Kandidaten. Landen automatisch in der regulären HR-Sichtung.", icon: "👥" },
            { title: "Kategorie C (15-50%)", description: "Grenzfälle oder Quereinsteiger. Werden auf die Waitlist gesetzt und manuell durch HR geprüft.", icon: "⏳" },
            { title: "Kategorie D (<15%)", description: "Fachlich ungeeignet. Das System versendet nach 48 Stunden Verzögerung automatisch eine wertschätzende Absage.", icon: "🛑" }
          ]
        }
      },
      {
        type: "FeatureList",
        props: {
          title: "Micro-Modelle für Standorte",
          description: "Ein Arzt in Hamburg braucht andere Soft-Skills als eine Pflegekraft in Neumünster. Das System bildet hunderte Micro-Modelle, um diese Nuancen anhand historischer Einstellungen zu lernen.",
          features: []
        }
      }
    ],
    root: { props: { title: "KI Recruiting" } },
    zones: {}
  })
};

async function main() {
  await prisma.page.upsert({
    where: { slug: 'funktionen/ai-recruiting' },
    update: pageData,
    create: pageData
  });
  console.log("Marketing Page created!");
}
main().catch(console.error).finally(() => prisma.$disconnect());
