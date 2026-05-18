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
  title: 'Enterprise Karriere',
  description: 'Karriereplattform des Enterprises. Finde Jobs, Ausbildungsplätze und Karrierewege.',
};

const prisma = new PrismaClient();

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let headerData = null;
  let footerData = null;
  try {
    const [headerPage, footerPage] = await Promise.all([
      prisma.page.findUnique({ where: { slug: '_global_header' } }),
      prisma.page.findUnique({ where: { slug: '_global_footer' } })
    ]);
    if (headerPage) headerData = JSON.parse(headerPage.content);
    if (footerPage) footerData = JSON.parse(footerPage.content);
  } catch (e) {
    // Ignore parse errors or missing DB in build step
  }

  return (
    <html lang="de">
      <body className={`${inter.variable} ${outfit.variable}`}>
        {headerData && headerData.content ? (
          <PuckRenderer data={headerData} />
        ) : (
          <Navbar />
        )}
        
        {children}
        
        {/* Global Footer */}
        {footerData && footerData.content ? (
          <PuckRenderer data={footerData} />
        ) : (
          <footer style={{ backgroundColor: 'var(--card-bg)', borderTop: '1px solid var(--border)', padding: '4rem 0 2rem', marginTop: '4rem' }}>
            <div className="container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem', marginBottom: '2rem' }}>
              <div>
                <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Enterprise Karriere</h4>
                <p style={{ opacity: 0.8, fontSize: '0.9rem' }}>Ihr Platz mit Sinn im Herzen Holsteins. Wirken. Helfen. Wachsen.</p>
              </div>
              <div>
                <h4 style={{ marginBottom: '1rem' }}>Über uns</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem', opacity: 0.8 }}>
                  <Link href="/arbeitgeber">Warum wir?</Link>
                  <Link href="/info/_de_arbeitgeber_Enterprise_wer_wir_sind_">Wer wir sind</Link>
                  <Link href="/info/_de_arbeitgeber_Enterprise_was_uns_auszeichnet_">Was uns auszeichnet</Link>
                </div>
              </div>
              <div>
                <h4 style={{ marginBottom: '1rem' }}>Rechtliches</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem', opacity: 0.8 }}>
                  <Link href="/info/_de_impressum_">Impressum</Link>
                  <Link href="/info/_de_datenschutz_">Datenschutz</Link>
                  <Link href="/info/_de_barrierefreiheit_">Barrierefreiheit</Link>
                </div>
              </div>
            </div>
            <div className="container" style={{ textAlign: 'center', opacity: 0.5, fontSize: '0.8rem', borderTop: '1px solid var(--border)', paddingTop: '2rem' }}>
              © {new Date().getFullYear()} Enterprise
            </div>
          </footer>
        )}
      </body>
    </html>
  );
}
