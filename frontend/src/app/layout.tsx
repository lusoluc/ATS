import type { Metadata } from 'next';
import { Inter, Outfit } from 'next/font/google';
import './globals.css';
import Link from 'next/link';
import Navbar from '../components/Navbar';
import AccessibilitySwitcher from '../components/AccessibilitySwitcher';
import { PrismaClient } from '@prisma/client';
import DOMPurify from 'isomorphic-dompurify';
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
    if (headerPage) {
      if (headerPage.content.startsWith('{')) headerData = JSON.parse(headerPage.content);
      else headerData = headerPage;
    }
    if (footerPage) {
      if (footerPage.content.startsWith('{')) footerData = JSON.parse(footerPage.content);
      else footerData = footerPage;
    }
    navPages = dbNavPages || [];
  } catch (e) {
    // Ignore parse errors or missing DB in build step
  }

  return (
    <html lang="de">
      <body className={`${inter.variable} ${outfit.variable}`}>
        {headerData && headerData.content ? (
          <div className="ql-editor prose max-w-none" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(headerData.content) }} />
        ) : (
          <Navbar cmsPages={navPages} />
        )}
        
        {children}
        
        {/* Global Footer */}
        {footerData && footerData.content ? (
          <div className="ql-editor prose max-w-none" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(footerData.content) }} />
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

        {/* Floating Powered By Badge for Demo */}
        <a href="https://securats.de" target="_blank" rel="noopener noreferrer" style={{ position: 'fixed', bottom: '20px', right: '20px', background: 'white', padding: '8px 16px', borderRadius: '30px', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', zIndex: 9999, display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: '#334155', textDecoration: 'none', border: '1px solid #e2e8f0', outline: 'none' }} className="hover:-translate-y-1 transition-transform">
          <span style={{ opacity: 0.7 }}>Powered by</span> <strong style={{ color: '#2563eb' }}>SecurATS</strong>
        </a>
        
        {/* Global Inclusion & Accessibility Switcher */}
        <AccessibilitySwitcher />
      </body>
    </html>
  );
}
