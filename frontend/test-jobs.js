const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();
async function main() {
  const jobs = await prisma.jobPosting.findMany({ include: { workflowState: true } });
  console.log('Jobs:', jobs.length);
  console.log('States:', jobs.map(j => j.workflowState.name));
}
main().catch(console.error).finally(()=>prisma.$disconnect());
