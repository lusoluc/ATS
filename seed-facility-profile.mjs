import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function seedProfile() {
  const fac = await prisma.facility.findFirst({ where: { name: "Psychiatrisches Krankenhaus Rickling" } });
  
  if (fac) {
    await prisma.facilityProfile.upsert({
      where: { facilityId: fac.id },
      update: { slug: "psychiatrie-rickling", description: "Das Psychiatrische Krankenhaus in Rickling ist eine der modernsten Fachkliniken im Norden." },
      create: {
        facilityId: fac.id,
        slug: "psychiatrie-rickling",
        description: "Das Psychiatrische Krankenhaus in Rickling ist eine der modernsten Fachkliniken im Norden."
      }
    });
    console.log("FacilityProfile für Rickling erstellt! Slug: psychiatrie-rickling");
  } else {
    console.log("Einrichtung nicht gefunden.");
  }
}

seedProfile()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
