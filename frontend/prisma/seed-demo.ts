import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding Nordicum Health Group Demo Data...');

  // 1. Workflow States
  const statePublished = await prisma.workflowState.upsert({
    where: { name: 'published' },
    update: {},
    create: { name: 'published', description: 'Live auf der Karriereseite' }
  });

  // 2. Organization
  const org = await prisma.organization.create({
    data: { name: 'Nordicum Health Group' }
  });

  // 3. Locations
  const locHH = await prisma.location.create({
    data: { name: 'Campus Hamburg-Mitte', city: 'Hamburg' }
  });
  const locNorderstedt = await prisma.location.create({
    data: { name: 'Klinik Norderstedt', city: 'Norderstedt' }
  });
  const locKiel = await prisma.location.create({
    data: { name: 'Zentrale Kiel', city: 'Kiel' }
  });

  // 4. Facilities & Departments
  const facCampus = await prisma.facility.create({
    data: { name: 'Campus Hamburg-Mitte', organizationId: org.id }
  });
  const depIntensiv = await prisma.department.create({
    data: { name: 'Intensivmedizin', facilityId: facCampus.id }
  });
  const depAusbildung = await prisma.department.create({
    data: { name: 'Pflegeschule', facilityId: facCampus.id }
  });

  const facNorderstedt = await prisma.facility.create({
    data: { name: 'Psychiatrische Klinik Norderstedt', organizationId: org.id }
  });
  const depPsych = await prisma.department.create({
    data: { name: 'Psychiatrie & Psychotherapie', facilityId: facNorderstedt.id }
  });

  const facKiel = await prisma.facility.create({
    data: { name: 'Hauptverwaltung Kiel', organizationId: org.id }
  });
  const depIT = await prisma.department.create({
    data: { name: 'IT & Infrastruktur', facilityId: facKiel.id }
  });

  // 5. Job Families
  const jfPflege = await prisma.jobFamily.create({ data: { name: 'Pflege' } });
  const jfMedizin = await prisma.jobFamily.create({ data: { name: 'Medizin' } });
  const jfIT = await prisma.jobFamily.create({ data: { name: 'IT & Technik' } });
  const jfAusbildung = await prisma.jobFamily.create({ data: { name: 'Ausbildung' } });

  // 6. Contact Person
  const contactAnna = await prisma.contactPerson.create({
    data: {
      firstName: 'Anna',
      lastName: 'Müller',
      email: 'anna.mueller@nordicum.de',
      phone: '040 / 123 456 - 0',
      globalJobTitle: 'Leitung Talent Acquisition'
    }
  });

  // 7. Job Postings
  await prisma.jobPosting.create({
    data: {
      title: 'Gesundheits- und Krankenpfleger (m/w/d) Intensivstation',
      description: 'Verstärke unser Team auf der interdisziplinären Intensivstation im Herzen Hamburgs. Wir bieten KTD Tarif + Intensivzulage und verlässliche Dienstpläne per App.',
      organizationId: org.id,
      facilityId: facCampus.id,
      departmentId: depIntensiv.id,
      locationId: locHH.id,
      jobFamilyId: jfPflege.id,
      workflowStateId: statePublished.id,
      contactPersonId: contactAnna.id,
      tasksJson: JSON.stringify(["Überwachung beatmeter Patienten", "Interdisziplinäre Visiten", "Notfallmanagement"]),
      requirementsJson: JSON.stringify(["Abgeschlossene Ausbildung als Pflegefachkraft", "Idealerweise Fachweiterbildung Intensiv", "Teamfähigkeit"])
    }
  });

  await prisma.jobPosting.create({
    data: {
      title: 'Facharzt (m/w/d) für Psychiatrie und Psychotherapie',
      description: 'Wir suchen einen erfahrenen Facharzt für unsere offene Akutstation. Familiäres Team, flache Hierarchien und Chefarzt-Bonusmodell inklusive.',
      organizationId: org.id,
      facilityId: facNorderstedt.id,
      departmentId: depPsych.id,
      locationId: locNorderstedt.id,
      jobFamilyId: jfMedizin.id,
      workflowStateId: statePublished.id,
      contactPersonId: contactAnna.id,
      tasksJson: JSON.stringify(["Psychiatrische Diagnostik", "Psychotherapeutische Einzelgespräche", "Leitung von Gruppentherapien"]),
      requirementsJson: JSON.stringify(["Facharztanerkennung Psychiatrie", "Hohe Empathie", "Führungserfahrung"])
    }
  });

  await prisma.jobPosting.create({
    data: {
      title: 'Senior IT-Systemadministrator (m/w/d) Infrastruktur',
      description: 'Halte die digitale Herzkammer unseres Klinikums am Laufen! Du verantwortest die Server-Infrastruktur und treibst Cloud-Projekte (Hybrid) voran.',
      organizationId: org.id,
      facilityId: facKiel.id,
      departmentId: depIT.id,
      locationId: locKiel.id,
      jobFamilyId: jfIT.id,
      workflowStateId: statePublished.id,
      contactPersonId: contactAnna.id,
      tasksJson: JSON.stringify(["Administration Windows/Linux Server", "Netzwerkmanagement", "IT-Security Audits"]),
      requirementsJson: JSON.stringify(["Ausbildung Fachinformatiker Systemintegration", "5+ Jahre Berufserfahrung", "Kenntnisse in VMware"])
    }
  });

  await prisma.jobPosting.create({
    data: {
      title: 'Auszubildende (m/w/d) Pflegefachfrau/-mann',
      description: 'Starte deine Karriere in der Medizin! Wir bieten dir eine exzellente Ausbildung mit persönlichem Mentor, Tablet für die Berufsschule und Übernahmegarantie.',
      organizationId: org.id,
      facilityId: facCampus.id,
      departmentId: depAusbildung.id,
      locationId: locHH.id,
      jobFamilyId: jfAusbildung.id,
      workflowStateId: statePublished.id,
      contactPersonId: contactAnna.id,
      tasksJson: JSON.stringify(["Grund- und Behandlungspflege erlernen", "Assistenz bei ärztlichen Maßnahmen", "Dokumentation"]),
      requirementsJson: JSON.stringify(["Mittlerer Schulabschluss", "Freude am Umgang mit Menschen", "Zuverlässigkeit"])
    }
  });

  console.log('Seeding completed successfully!');
}

main()
  .catch(e => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
