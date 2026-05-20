import type { Metadata } from 'next';
import { Inter, Outfit } from 'next/font/google';
import './globals.css';
import Link from 'next/link';
import Navbar from '../components/Navbar';
import { PrismaClient } from '@prisma/client';
import { PuckRenderer } from './info/[slug]/PuckRenderer';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' });

export const metadata: Metadata = {
  title: 'SecurATS',
  description: 'Datensouveränes Bewerbermanagementsystem für On-Premise Sicherheit.',
};

const prisma = new PrismaClient();

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let headerData = null;
  let footerData = null;
  let navPages = [];
  try {
    const [headerPage, footerPage, dbNavPages] = await Promise.all([
      prisma.page.findUnique({ where: { slug: '_global_header' } }),
      prisma.page.findUnique({ where: { slug: '_global_footer' } }),
      prisma.page.findMany({ 
        where: { status: 'published', navEnabled: true },
        orderBy: { navOrder: 'asc' },
        select: { id: true, slug: true, title: true, navLabel: true, navParent: true }
      })
    ]);
    if (headerPage) headerData = JSON.parse(headerPage.content);
    if (footerPage) footerData = JSON.parse(footerPage.content);
    navPages = dbNavPages || [];
  } catch (e) {
    // Ignore parse errors or missing DB in build step
  }

  return (
    <html lang="de">
      <body className={`${inter.variable} ${outfit.variable}`}>
        {headerData && headerData.content ? (
          <PuckRenderer data={headerData} />
        ) : (
          <Navbar cmsPages={navPages} />
        )}
        
        {children}
        
        {/* Global Footer */}
        {footerData && footerData.content ? (
          <PuckRenderer data={footerData} />
        ) : (
          <footer style={{ backgroundColor: 'var(--card-bg)', borderTop: '1px solid var(--border)', padding: '4rem 0 2rem', marginTop: '4rem' }}>
            <div className="container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem', marginBottom: '2rem' }}>
              <div>
                <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>SecurATS</h4>
                <p style={{ opacity: 0.8, fontSize: '0.9rem' }}>Sicheres, lokales Recruiting. 100% DSGVO & DORA konform.</p>
              </div>
              <div>
                <h4 style={{ marginBottom: '1rem' }}>Über uns</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem', opacity: 0.8 }}>
                  <Link href="/arbeitgeber">Warum wir?</Link>
                  <Link href="/info/ueber-uns">Wer wir sind</Link>
                  <Link href="/info/kultur">Kultur & Werte</Link>
                </div>
              </div>
              <div>
                <h4 style={{ marginBottom: '1rem' }}>Rechtliches</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem', opacity: 0.8 }}>
                  <Link href="/info/impressum">Impressum</Link>
                  <Link href="/info/datenschutz">Datenschutz</Link>
                  <Link href="/info/barrierefreiheit">Barrierefreiheit</Link>
                </div>
              </div>
            </div>
            <div className="container" style={{ textAlign: 'center', opacity: 0.5, fontSize: '0.8rem', borderTop: '1px solid var(--border)', paddingTop: '2rem' }}>
              © {new Date().getFullYear()} SecurATS
            </div>
          </footer>
        )}
      </body>
    </html>
  );
}
