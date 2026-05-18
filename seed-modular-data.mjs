import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function seed() {
  console.log("Starte Seeding für modulare Daten...");

  // 1. Hole Basis-Daten (müssen durch vorherige Seeds existieren)
  let org = await prisma.organization.findFirst();
  let loc = await prisma.location.findFirst({ where: { name: "Rickling" } });
  let fac = await prisma.facility.findFirst({ where: { name: "Psychiatrisches Krankenhaus Rickling" } });
  let fam = await prisma.jobFamily.findFirst({ where: { name: "Medizin" } });
  let state = await prisma.workflowState.findFirst({ where: { name: "published" } });

  if (!org || !loc || !fac || !fam || !state) {
    throw new Error("Basisdaten fehlen. Bitte führe zuerst den ursprünglichen Seed aus.");
  }

  // 2. Erstelle Benefits
  console.log("Erstelle Benefits...");
  const b1 = await prisma.benefit.upsert({ where: { name: "31 Tage Urlaub" }, update: {}, create: { name: "31 Tage Urlaub", icon: "🌴", description: "Viel Zeit für Erholung." }});
  const b2 = await prisma.benefit.upsert({ where: { name: "Tarif AVR DD" }, update: {}, create: { name: "Tarif AVR DD", icon: "💶", description: "Leistungsgerechte kirchliche Vergütung." }});
  const b3 = await prisma.benefit.upsert({ where: { name: "Dienstradleasing" }, update: {}, create: { name: "Dienstradleasing", icon: "🚲", description: "Für den Weg zur Arbeit und privat." }});
  const b4 = await prisma.benefit.upsert({ where: { name: "Betriebliche Altersvorsorge" }, update: {}, create: { name: "Betriebliche Altersvorsorge", icon: "🛡️", description: "Sicher in die Zukunft." }});

  // 3. Erstelle Text-Bausteine
  console.log("Erstelle Textbausteine...");
  await prisma.textSnippet.createMany({
    data: [
      { category: "TASKS", content: "Oberärztliche Leitung einer offen geführten Suchtstation", jobFamilyId: fam.id },
      { category: "TASKS", content: "Sicherstellung einer differenzierten Diagnostik und Therapieplanung", jobFamilyId: fam.id },
      { category: "TASKS", content: "Fachärztliche Anleitung und Supervision der Assistenzärzt*innen", jobFamilyId: fam.id },
      { category: "REQUIREMENTS", content: "Abgeschlossene Facharztausbildung in Psychiatrie und Psychotherapie", jobFamilyId: fam.id },
      { category: "REQUIREMENTS", content: "Empathie, Kommunikationsstärke und Freude an der Arbeit mit Menschen", jobFamilyId: fam.id },
      { category: "REQUIREMENTS", content: "Offenheit für interdisziplinäre Zusammenarbeit", jobFamilyId: fam.id }
    ]
  });

  // 4. Erstelle Ansprechpartner mit Zitat
  console.log("Erstelle Ansprechpartner...");
  const contact = await prisma.contactPerson.create({
    data: {
      firstName: "Dr. Matthias",
      lastName: "Hollmann",
      email: "m.hollmann@landesverein.de",
      phone: "04328 18 279",
      photoUrl: "https://ui-avatars.com/api/?name=Matthias+Hollmann&background=6b2361&color=fff&size=256",
      quote: "Suchtmedizin ist mehr als nur Therapie – es ist die Begleitung von Menschen zurück ins Leben. Ich freue mich auf Ihre Unterstützung in unserem Team!",
      globalJobTitle: "Chefarzt der 2. Klinik",
      facilityLinks: {
        create: { facilityId: fac.id, roleTitle: "Chefarzt" }
      }
    }
  });

  // 5. Erstelle modulares Job Posting (Wir nutzen ID 9999 für diesen Test)
  console.log("Erstelle modulares Job Posting...");
  
  // JSON Arrays für Aufgaben und Anforderungen
  const tasks = JSON.stringify([
    "Oberärztliche Leitung einer offen geführten Suchtstation",
    "Sicherstellung einer differenzierten Diagnostik und Therapieplanung",
    "Fachärztliche Anleitung und Supervision der Assistenzärzt*innen"
  ]);
  
  const requirements = JSON.stringify([
    "Abgeschlossene Facharztausbildung in Psychiatrie und Psychotherapie",
    "Empathie, Kommunikationsstärke und Freude an der Arbeit mit Menschen",
    "Interesse an der stationären Versorgung"
  ]);

  const job = await prisma.jobPosting.create({
    data: {
      id: "9999",
      title: "Oberarzt/Oberärztin Psychiatrie (Modular)",
      // Wir lassen description leer, da wir modular rendern wollen!
      description: null,
      tasksJson: tasks,
      requirementsJson: requirements,
      contactPersonId: contact.id,
      organizationId: org.id,
      facilityId: fac.id,
      locationId: loc.id,
      jobFamilyId: fam.id,
      workflowStateId: state.id,
      benefits: {
        connect: [{ id: b1.id }, { id: b2.id }, { id: b3.id }, { id: b4.id }]
      }
    }
  });

  console.log("Erfolgreich beendet! Neuer modularer Job: 9999");
}

seed()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
