import { PrismaClient } from '@prisma/client';
import { notFound } from 'next/navigation';
import { ClientEditor } from './ClientEditor';

const prisma = new PrismaClient();

export default async function EditorPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  
  const page = await prisma.page.findUnique({
    where: { slug }
  });

  if (!page) {
    notFound();
  }

  let initialData = { content: [], root: {}, zones: {} };
  
  try {
    const parsed = JSON.parse(page.content);
    if (parsed && parsed.content) {
      initialData = parsed;
    }
  } catch (e) {
    // Falls Markdown vorliegt, nehmen wir das als TextBlock. Falls leer, ein schönes Default-Layout.
    initialData = {
      content: [
        {
          type: "HeroBlock",
          props: { title: page.title, subtitle: "Füge hier deinen Slogan ein", alignment: "center", titleSize: "large", textColor: "white", id: "default-hero" }
        },
        {
          type: "Spacer",
          props: { size: "medium", id: "default-spacer-1" }
        },
        {
          type: "TextBlock",
          props: { content: page.content || "Füge hier den Hauptinhalt deiner Seite ein. Du kannst diesen Text löschen oder bearbeiten.", size: "default", color: "default", align: "left", id: "legacy-content" }
        }
      ],
      root: {},
      zones: {}
    } as any;
  }

  return (
    <div style={{ height: '100vh', width: '100vw' }}>
      <ClientEditor initialData={initialData} slug={slug} />
    </div>
  );
}
