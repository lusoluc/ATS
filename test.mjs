import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

async function run() {
  try {
    const job = await prisma.jobPosting.findUnique({
      where: { id: "9999" },
      include: { 
        facility: { include: { profile: true } }, 
        location: true, 
        jobFamily: true, 
        workflowState: true,
        contactPerson: true,
        benefits: true
      },
    });
    console.log("JOB:", job);
  } catch (e) {
    console.error("ERROR:", e);
  } finally {
    await prisma.$disconnect();
  }
}
run();
