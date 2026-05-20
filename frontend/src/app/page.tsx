import { PrismaClient } from '@prisma/client';
import { PuckRenderer } from './info/[slug]/PuckRenderer';
import Link from 'next/link';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

const prisma = new PrismaClient();

export default async function HomePage() {
  let isPuck = false;
  let puckData: any = null;

  try {
    const page = await prisma.page.findUnique({ where: { slug: 'home' } });
    if (page && page.content) {
      const parsed = JSON.parse(page.content);
      if (parsed && parsed.content) {
        isPuck = true;
        puckData = parsed;
      }
    }
  } catch(e) {
    console.error("Error parsing homepage puck data:", e);
  }

  if (isPuck && puckData) {
    return <PuckRenderer data={puckData} />;
  }

  return (
    <main style={{ padding: '6rem 0', textAlign: 'center' }}>
      <h1>Bitte migriere die Startseite in den Editor.</h1>
      <p>Führe das Migration-Skript aus, um das Layout in den Puck-Editor zu laden.</p>
    </main>
  );
}
