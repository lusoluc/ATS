const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

const PAGES = [
  { title: 'Beruf & Karriere', slug: 'beruf-karriere', navLabel: 'Beruf & Karriere', navParent: '', navOrder: 0, content: '# Beruf & Karriere beim Landesverein\n\nFinde deinen Platz bei uns — ob Pflege, Medizin, Pädagogik, Verwaltung oder Technik.\n\n## Deine Möglichkeiten\n\n- **Pflege & Betreuung** — Psychiatrische Pflege, Altenpflege\n- **Medizin** — Ärztliche Tätigkeit in unseren Kliniken\n- **Pädagogik & Therapie** — Jugendhilfe, Sozialpädagogik\n- **Verwaltung & IT** — Kaufmännische Berufe\n- **Hauswirtschaft & Technik** — Gebäudemanagement' },
  { title: 'Über uns', slug: 'ueber-uns', navLabel: 'Über uns', navParent: 'beruf-karriere', navOrder: 0, content: '# Über den Landesverein\n\nDer **Landesverein für Innere Mission** ist ein diakonisches Sozialunternehmen mit über 145 Jahren Tradition.\n\n## Was uns ausmacht\n\n- 2.000+ Mitarbeitende aus der Region\n- 10 Einrichtungen in Schleswig-Holstein\n- Psychiatrie, Jugendhilfe, Altenpflege\n- Vergütung nach KTD' },
  { title: 'Benefits & Vorteile', slug: 'benefits', navLabel: 'Benefits', navParent: 'beruf-karriere', navOrder: 1, content: '# Benefits & Vorteile\n\n## Vergütung\n- Kirchlicher Tarifvertrag (KTD)\n- Jahressonderzahlung\n- Betriebliche Altersvorsorge\n\n## Work-Life-Balance\n- 30 Tage Urlaub\n- Flexible Arbeitszeiten\n- Familienfreundlich\n\n## Entwicklung\n- Fort- und Weiterbildung\n- Bezahlte Fortbildungstage' },
  { title: 'Ausbildung', slug: 'ausbildung', navLabel: 'Ausbildung', navParent: 'beruf-karriere', navOrder: 2, content: '# Ausbildung beim Landesverein\n\n## Ausbildungsberufe\n- Pflegefachfrau / Pflegefachmann (3 Jahre)\n- Altenpflegehelfer*in (1 Jahr)\n- Erzieher*in\n- Kauffrau/-mann für Büromanagement\n\n## Was wir bieten\n- Vergütung nach KTD-Ausbildungstarif\n- 30 Tage Urlaub\n- Übernahmegarantie bei guten Leistungen' },
  { title: 'Weiterbildung', slug: 'weiterbildung', navLabel: 'Weiterbildung', navParent: 'beruf-karriere', navOrder: 3, content: '# Fort- und Weiterbildung\n\n## Angebote\n- Fachweiterbildung Psychiatrie\n- Praxisanleiter-Qualifikation\n- Führungskräfte-Entwicklung\n- Deeskalationstraining' },
  { title: 'Arbeitgeber', slug: 'arbeitgeber', navLabel: 'Arbeitgeber', navParent: '', navOrder: 1, content: '# Der Landesverein als Arbeitgeber\n\n## Arbeitgeber mit Charakter\n\nWir sind kein Konzern. Wir sind Gemeinschaft.\n\n## Unsere Werte\n- Menschlichkeit\n- Gemeinschaft\n- Verlässlichkeit\n- Nachhaltigkeit\n\n## Gemeinnützig aus Überzeugung\nAlle Gewinne fließen zurück in unsere Arbeit.' },
  { title: 'FAQ', slug: 'faq', navLabel: 'FAQ', navParent: '', navOrder: 5, content: '# Häufig gestellte Fragen\n\n**Kann ich mich initiativ bewerben?**\nJa! Wir freuen uns über Initiativbewerbungen.\n\n**Welcher Tarifvertrag gilt?**\nKirchlicher Tarifvertrag Diakonie (KTD).\n\n**Sind Teilzeitstellen möglich?**\nJa, viele Stellen sind auch in Teilzeit zu besetzen.\n\n**Gibt es Ausbildungsplätze?**\nJa! In Pflege, Sozialberufen und Verwaltung.' },
  { title: 'Kontakt', slug: 'kontakt', navLabel: 'Kontakt', navParent: '', navOrder: 6, content: '# Kontakt\n\n## Recruiting-Team\n\n**E-Mail:** karriere@landesverein.de\n**Telefon:** 04326 / 500\n**Bürozeiten:** Mo–Fr, 8:30–15:00 Uhr\n\n## Adresse\nLandesverein für Innere Mission\nDaldorfer Straße 2\n24635 Rickling' },
];

async function seed() {
  let created = 0, skipped = 0;
  for (const p of PAGES) {
    const exists = await prisma.page.findUnique({ where: { slug: p.slug } });
    if (exists) { skipped++; continue; }
    await prisma.page.create({
      data: {
        title: p.title, slug: p.slug, content: p.content,
        status: 'published', navEnabled: true,
        navLabel: p.navLabel || null, navParent: p.navParent || null, navOrder: p.navOrder || 0,
      },
    });
    created++;
  }
  console.log(`Done: ${created} created, ${skipped} skipped`);
  await prisma.$disconnect();
}
seed().catch(e => { console.error(e); process.exit(1); });
