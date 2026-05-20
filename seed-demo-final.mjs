import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

const PAGES = [
  { title: 'Wer wir sind', slug: 'ueber-uns', navLabel: 'Über uns', navParent: 'beruf-karriere', navOrder: 0, content: `{"content":[{"type":"HeroBlock","props":{"title":"Wir sind die Nordicum Health Group","subtitle":"Der größte Maximalversorger in Norddeutschland.","alignment":"left","titleSize":"large","textColor":"dark"}}],"root":{"props":{"title":"Über uns"}}}` },
  { title: 'Kultur & Werte', slug: 'kultur', navLabel: 'Kultur & Werte', navParent: 'beruf-karriere', navOrder: 1, content: `{"content":[{"type":"HeroBlock","props":{"title":"Unsere Kultur","subtitle":"Wir arbeiten auf Augenhöhe. Kein Chefarzt-Gehabe, sondern echtes Teamwork.","alignment":"left","titleSize":"large","textColor":"dark"}}],"root":{"props":{"title":"Kultur & Werte"}}}` },
  { title: 'Beruf & Karriere', slug: 'beruf-karriere', navLabel: 'Beruf & Karriere', navParent: '', navOrder: 0, content: `{"content":[{"type":"HeroBlock","props":{"title":"Dein Weg zu uns","subtitle":"Egal ob Pflege, Medizin oder IT – finde deinen Platz bei uns.","alignment":"left","titleSize":"large","textColor":"dark"}}],"root":{"props":{"title":"Beruf & Karriere"}}}` },
  { title: 'Impressum', slug: 'impressum', navLabel: 'Impressum', navParent: null, navEnabled: false, navOrder: 99, content: `{"content":[{"type":"HeroBlock","props":{"title":"Impressum","subtitle":"Angaben gemäß § 5 TMG","alignment":"left","titleSize":"medium","textColor":"dark"}}],"root":{"props":{"title":"Impressum"}}}` },
  { title: 'Datenschutz', slug: 'datenschutz', navLabel: 'Datenschutz', navParent: null, navEnabled: false, navOrder: 99, content: `{"content":[{"type":"HeroBlock","props":{"title":"Datenschutzerklärung","subtitle":"Wir nehmen den Schutz deiner Daten ernst.","alignment":"left","titleSize":"medium","textColor":"dark"}}],"root":{"props":{"title":"Datenschutz"}}}` },
  { title: 'Barrierefreiheit', slug: 'barrierefreiheit', navLabel: 'Barrierefreiheit', navParent: null, navEnabled: false, navOrder: 99, content: `{"content":[{"type":"HeroBlock","props":{"title":"Erklärung zur Barrierefreiheit","subtitle":"Unser Anspruch ist eine inklusive Plattform.","alignment":"left","titleSize":"medium","textColor":"dark"}}],"root":{"props":{"title":"Barrierefreiheit"}}}` }
];

async function main() {
  console.log('--- STARTING DEMO SEED ---');

  // 1. Pages
  for (const page of PAGES) {
    await prisma.page.upsert({
      where: { slug: page.slug },
      update: { title: page.title, content: page.content, navLabel: page.navLabel, navParent: page.navParent, navEnabled: page.navEnabled ?? true, navOrder: page.navOrder, status: 'published' },
      create: { title: page.title, slug: page.slug, content: page.content, navLabel: page.navLabel, navParent: page.navParent, navEnabled: page.navEnabled ?? true, navOrder: page.navOrder, status: 'published' }
    });
    console.log(`Upserted page: ${page.slug}`);
  }

  // 2. Setup Base Data (Workflow States)
  let draftState = await prisma.workflowState.findUnique({ where: { name: 'draft' } });
  if (!draftState) draftState = await prisma.workflowState.create({ data: { name: 'draft', description: 'Entwurf' } });
  
  let publishedState = await prisma.workflowState.findUnique({ where: { name: 'published' } });
  if (!publishedState) publishedState = await prisma.workflowState.create({ data: { name: 'published', description: 'Veröffentlicht' } });

  // 3. Job Families
  const families = ['Pflege & Betreuung', 'Medizin & Ärzte', 'IT & Technik', 'Verwaltung'];
  const familyIds = {};
  for (const name of families) {
    const f = await prisma.jobFamily.upsert({
      where: { name },
      update: {},
      create: { name }
    });
    familyIds[name] = f.id;
  }
  
  // 4. Locations & Facilities
  const locations = [
    { name: 'Hamburg-Mitte', lat: 53.551, lng: 9.993 },
    { name: 'Kiel-Campus', lat: 54.323, lng: 10.122 },
    { name: 'Lübeck', lat: 53.865, lng: 10.686 }
  ];
  const locIds = {};
  for (const l of locations) {
    const loc = await prisma.location.upsert({
      where: { name: l.name },
      update: { lat: l.lat, lng: l.lng },
      create: { name: l.name, lat: l.lat, lng: l.lng }
    });
    locIds[l.name] = loc.id;
    
    // Create Facility
    const facName = `Klinikum ${l.name}`;
    const fac = await prisma.facility.upsert({
      where: { name: facName },
      update: { locationId: loc.id },
      create: { name: facName, locationId: loc.id, address: `Hauptstraße 1, ${l.name}` }
    });
    
    // Create Facility Profile so /einrichtungen/[slug] works!
    const slug = facName.toLowerCase().replace(/[^a-z0-9]/g, '-');
    await prisma.facilityProfile.upsert({
      where: { slug },
      update: { facilityId: fac.id },
      create: { slug, facilityId: fac.id, description: JSON.stringify({ content: [{ type: 'HeroBlock', props: { title: facName, subtitle: 'Ein moderner Standort der Nordicum Health Group.', alignment: 'left', titleSize: 'medium', textColor: 'dark' } }], root: { props: { title: facName } } }) }
    });
  }

  // 5. Active Jobs
  const jobs = [
    { title: 'Gesundheits- und Krankenpfleger (m/w/d)', family: 'Pflege & Betreuung', loc: 'Hamburg-Mitte' },
    { title: 'Fachkrankenpfleger Intensivpflege (m/w/d)', family: 'Pflege & Betreuung', loc: 'Kiel-Campus' },
    { title: 'Assistenzarzt Kardiologie (m/w/d)', family: 'Medizin & Ärzte', loc: 'Lübeck' },
    { title: 'Oberarzt Neurologie (m/w/d)', family: 'Medizin & Ärzte', loc: 'Hamburg-Mitte' },
    { title: 'IT-Systemadministrator Kliniksysteme (m/w/d)', family: 'IT & Technik', loc: 'Kiel-Campus' },
    { title: 'HR Generalist (m/w/d)', family: 'Verwaltung', loc: 'Hamburg-Mitte' },
  ];

  for (const [index, j] of jobs.entries()) {
    const facName = `Klinikum ${j.loc}`;
    const fac = await prisma.facility.findUnique({ where: { name: facName } });
    
    // Ensure unique external ID to avoid collision
    const externalId = `DEMO-JOB-${index + 1}`;
    
    await prisma.jobPosting.upsert({
      where: { externalId },
      update: { title: j.title, workflowStateId: publishedState.id },
      create: {
        externalId,
        title: j.title,
        description: `Wir suchen eine engagierte Fachkraft für den Bereich ${j.title}. Bewirb dich jetzt in unter 60 Sekunden!`,
        jobFamilyId: familyIds[j.family],
        locationId: locIds[j.loc],
        facilityId: fac.id,
        workflowStateId: publishedState.id,
        workModel: 'Vollzeit',
        employmentType: 'Unbefristet',
        screeningQuestionsJson: JSON.stringify(['Haben Sie eine abgeschlossene Ausbildung?', 'Ab wann sind Sie verfügbar?'])
      }
    });
  }
  
  console.log('--- DEMO SEED COMPLETED ---');
}

main().catch(e => { console.error(e); process.exit(1); }).finally(() => prisma.$disconnect());
