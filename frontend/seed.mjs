import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

const SEED_PAGES = [
  { title: 'Über uns', slug: 'ueber-uns', navLabel: 'Über uns', navParent: 'beruf-karriere', navOrder: 0, content: `# Über den Enterprise\n\nDer **Enterprise** ist ein diakonisches Sozialunternehmen mit über 145 Jahren Tradition.\n\n## Unsere Geschichte\n\nSeit 1876 engagieren wir uns für Menschen in besonderen Lebenslagen. Unsere Einrichtungen sind in der norddeutschen Landschaft verwurzelt — eingebettet in Natur, Gemeinschaft und gelebte Nächstenliebe.\n\n## Was uns ausmacht\n\n- **2.000+ Mitarbeitende** aus der Region\n- **10 Einrichtungen** in Schleswig-Holstein\n- Psychiatrie, Jugendhilfe, Altenpflege und soziale Dienste\n- Vergütung nach kirchlichem Tarifvertrag (KTD)\n- Familiäre Atmosphäre und flache Hierarchien\n\n## Unsere Standorte\n\nUnsere Hauptstandorte befinden sich in **Rickling**, **Bad Segeberg**, **Neumünster** und weiteren Orten in Schleswig-Holstein.\n` },
  { title: 'Benefits & Vorteile', slug: 'benefits', navLabel: 'Benefits', navParent: 'beruf-karriere', navOrder: 1, content: `# Benefits & Vorteile\n\nBeim Enterprise arbeiten heißt: Sinnvoll arbeiten und dabei gut versorgt sein.\n\n## Vergütung & Finanzen\n\n- **Kirchlicher Tarifvertrag (KTD)** — faire, transparente Bezahlung\n- **Jahressonderzahlung** — 13. Monatsgehalt\n- **Betriebliche Altersvorsorge** — wir sichern deine Zukunft\n- **Vermögenswirksame Leistungen**\n\n## Work-Life-Balance\n\n- **30 Tage Urlaub** plus Zusatzurlaub für Schichtarbeit\n- **Flexible Arbeitszeitmodelle** — Voll- und Teilzeit\n- **Familienfreundlich** — betriebliche Kinderbetreuung\n\n## Entwicklung & Bildung\n\n- **Fort- und Weiterbildung** — bezahlte Fortbildungstage\n- **Fachliche Spezialisierung** möglich\n- **Karrierepfade** innerhalb des Unternehmens\n\n## Arbeitsumfeld\n\n- **Ländliche Lage** — kurze Wege, viel Natur\n- **Kollegiales Miteinander** — familiäre Teams\n- **Moderne Ausstattung** in unseren Einrichtungen\n` },
  { title: 'Beruf & Karriere', slug: 'beruf-karriere', navLabel: 'Beruf & Karriere', navParent: '', navOrder: 0, content: `# Beruf & Karriere beim Enterprise\n\nFinde deinen Platz bei uns — ob Pflege, Medizin, Pädagogik, Verwaltung oder Technik.\n\n## Deine Möglichkeiten\n\nDer Enterprise bietet vielfältige Karrierewege in einem sinnstiftenden Arbeitsumfeld:\n\n- **Pflege & Betreuung** — Psychiatrische Pflege, Altenpflege, Behindertenbetreuung\n- **Medizin** — Ärztliche Tätigkeit in unseren Kliniken\n- **Pädagogik & Therapie** — Jugendhilfe, Sozialpädagogik, Ergotherapie\n- **Verwaltung & IT** — Kaufmännische Berufe, Digitalisierung\n- **Hauswirtschaft & Technik** — Gebäudemanagement, Küche, Reinigung\n\n## Dein Weg zu uns\n\n1. **Stellenangebote durchsuchen** — nutze unsere Jobbörse mit Umkreissuche\n2. **Initiativ bewerben** — auch ohne passende Ausschreibung\n3. **Bewerbungsgespräch** — wir melden uns innerhalb von 2 Werktagen\n4. **Willkommen im Team** — strukturierte Einarbeitung\n` },
  { title: 'Arbeitgeber', slug: 'arbeitgeber', navLabel: 'Arbeitgeber', navParent: '', navOrder: 1, content: `# Der Enterprise als Arbeitgeber\n\n## Arbeitgeber mit Charakter\n\nWir sind kein Konzern. Wir sind Gemeinschaft. Unsere Mitarbeitenden kommen aus den umliegenden Dörfern und kehren jeden Tag nach Hause zurück.\n\n## Unsere Werte\n\n- **Menschlichkeit** — Jeder Mensch ist wertvoll\n- **Gemeinschaft** — Wir arbeiten im Team\n- **Verlässlichkeit** — Faire Bezahlung, sichere Arbeitsplätze\n- **Nachhaltigkeit** — Verantwortung für Region und Umwelt\n\n## Unsere Einrichtungen\n\nZum Enterprise gehören psychiatrische Einrichtungen, Jugendhilfe-Angebote, Altenpflegeheime und weitere soziale Dienste — alle eingebettet in die norddeutsche Landschaft.\n\n## Gemeinnützig aus Überzeugung\n\nAls diakonisches Unternehmen sind wir gemeinnützig. Das bedeutet: Alle Gewinne fließen zurück in unsere Arbeit, in unsere Mitarbeitenden und in die Region.\n` },
  { title: 'Ausbildung', slug: 'ausbildung', navLabel: 'Ausbildung', navParent: 'beruf-karriere', navOrder: 2, content: `# Ausbildung beim Enterprise\n\n## Deine Ausbildung bei uns\n\nWir bilden in verschiedenen Berufen aus und begleiten dich auf deinem Weg in einen sinnvollen Beruf.\n\n### Ausbildungsberufe\n\n- **Pflegefachfrau / Pflegefachmann** (3 Jahre)\n- **Altenpflegehelfer*in** (1 Jahr)\n- **Erzieher*in** (schulische Ausbildung mit Praxisphasen)\n- **Kauffrau/-mann für Büromanagement**\n- **Hauswirtschafter*in**\n\n### Was wir bieten\n\n- Vergütung nach KTD-Ausbildungstarif\n- 30 Tage Urlaub\n- Praxisanleitung durch erfahrene Kolleg*innen\n- Übernahmegarantie bei guten Leistungen\n- Azubi-Projekte und Teamevents\n` },
  { title: 'FAQ', slug: 'faq', navLabel: 'FAQ', navParent: '', navOrder: 5, content: `# Häufig gestellte Fragen\n\n## Bewerbung\n\n**Kann ich mich initiativ bewerben?**\nJa, absolut! Wir freuen uns über Initiativbewerbungen. Nutze unser Online-Formular — wir melden uns innerhalb von zwei Werktagen.\n\n**Welche Unterlagen brauche ich?**\nLebenslauf und relevante Zeugnisse genügen für den Anfang. Ein Anschreiben ist willkommen, aber nicht zwingend.\n\n**Wie lange dauert der Bewerbungsprozess?**\nIn der Regel melden wir uns innerhalb von 2 Werktagen. Das Bewerbungsgespräch findet zeitnah statt.\n\n## Arbeiten beim Enterprise\n\n**Welcher Tarifvertrag gilt?**\nWir vergüten nach dem Kirchlichen Tarifvertrag Diakonie (KTD) inklusive Jahressonderzahlung und betrieblicher Altersversorgung.\n\n**Sind Teilzeitstellen möglich?**\nJa. Viele unserer Stellen sind auch in Teilzeit zu besetzen.\n\n**Gibt es Ausbildungsplätze?**\nJa! Wir bilden in verschiedenen Pflege-, Sozial- und Verwaltungsberufen aus.\n\n## Standorte\n\n**Wo befinden sich die Einrichtungen?**\nUnsere Hauptstandorte sind in Rickling, Bad Segeberg und Neumünster — eingebettet in die norddeutsche Natur.\n` },
  { title: 'Weiterbildung', slug: 'weiterbildung', navLabel: 'Weiterbildung', navParent: 'beruf-karriere', navOrder: 3, content: `# Fort- und Weiterbildung\n\n## Wir investieren in dich\n\nDer Enterprise unterstützt deine fachliche und persönliche Entwicklung — mit bezahlten Fortbildungstagen und vielfältigen Angeboten.\n\n### Angebote\n\n- Fachweiterbildung Psychiatrie\n- Praxisanleiter-Qualifikation\n- Führungskräfte-Entwicklung\n- Deeskalationstraining\n- Erste-Hilfe-Auffrischung\n- Digitale Kompetenz-Schulungen\n` },
  { title: 'Kontakt', slug: 'kontakt', navLabel: 'Kontakt', navParent: '', navOrder: 6, navEnabled: true, content: `# Kontakt\n\n## Recruiting-Team\n\nWir freuen uns auf deine Fragen und deine Bewerbung!\n\n**E-Mail:** karriere@Enterprise.de\n**Telefon:** 04326 / 500\n\n**Bürozeiten:** Mo–Fr, 8:30 bis 15:00 Uhr\n\n## Adresse\n\nEnterprise\nDaldorfer Straße 2\n24635 Rickling\n` },
];

async function main() {
  let created = 0;
  for (const page of SEED_PAGES) {
    const existing = await prisma.page.findUnique({ where: { slug: page.slug } });
    if (existing) {
      await prisma.page.update({
        where: { slug: page.slug },
        data: { content: page.content }
      });
      console.log(`Updated ${page.slug}`);
    } else {
      await prisma.page.create({
        data: {
          title: page.title,
          slug: page.slug,
          content: page.content,
          status: 'published',
          navEnabled: page.navEnabled !== undefined ? page.navEnabled : true,
          navLabel: page.navLabel || null,
          navParent: page.navParent || null,
          navOrder: page.navOrder || 0,
        },
      });
      created++;
      console.log(`Created ${page.slug}`);
    }
  }

  // Also seed initial System settings and Email Templates
  const settings = [
    { key: 'company_name', value: 'Enterprise' },
    { key: 'primary_color', value: '#e2001a' },
    { key: 'contact_email', value: 'karriere@Enterprise.de' },
    { key: 'contact_address', value: 'Daldorfer Straße 2, 24635 Rickling' },
    { key: 'footer_links', value: JSON.stringify([{ label: 'Impressum', url: '/info/impressum' }, { label: 'Datenschutz', url: '/info/datenschutz' }]) }
  ];

  for(const s of settings) {
    await prisma.systemSetting.upsert({
      where: { key: s.key },
      update: { value: s.value },
      create: { key: s.key, value: s.value }
    });
  }

  await prisma.emailTemplate.upsert({
    where: { name: 'job_alert_daily_digest' },
    update: {},
    create: {
      name: 'job_alert_daily_digest',
      subject: '{{global.company_name}}: Neue Stellenangebote für Sie',
      htmlContent: '<h1>Neue Jobs bei {{global.company_name}}</h1><p>Wir haben {{matchedJobs.length}} neue Jobs für Sie gefunden.</p>',
      textContent: 'Neue Jobs bei {{global.company_name}}'
    }
  });

  console.log(`Finished. Created ${created} new pages.`);
}

main().catch(console.error).finally(() => prisma.$disconnect());
