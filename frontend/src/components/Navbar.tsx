'use client';
import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

type NavPage = {
  id: string;
  slug: string;
  title: string;
  navLabel: string | null;
  navParent: string | null;
};

export default function Navbar({ cmsPages = [] }: { cmsPages?: NavPage[] }) {
  const [isOpen, setIsOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState<string | null>(null);

  const initiativPage = cmsPages.find(p => p.slug.includes('initiativbewerbung'));
  const jobsPage = cmsPages.find(p => p.slug.includes('stellenangebote') || p.slug === 'jobs');
  const alertPage = cmsPages.find(p => p.slug.includes('job-alert') || p.slug.includes('job_alert'));

  const specialIds = [initiativPage?.id, jobsPage?.id, alertPage?.id].filter(Boolean);
  const parents = cmsPages.filter(p => !p.navParent && !specialIds.includes(p.id));
  const children = cmsPages.filter(p => p.navParent);

  return (
    <nav className="navbar glass-panel">
      <div className="container nav-content">
        <Link href="/" className="nav-logo" onClick={() => setIsOpen(false)} style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <Image src="/logo.png" alt="SecurATS Logo" width={32} height={32} style={{ borderRadius: '6px' }} />
          SecurATS
        </Link>
        
        {/* Mobile Toggle Button */}
        <button 
          className="mobile-toggle"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Toggle Menu"
        >
          {isOpen ? '✕' : '☰'}
        </button>

        <div className={`nav-links ${isOpen ? 'active' : ''}`}>
          {parents.map(parent => {
            const myChildren = children.filter(c => c.navParent === parent.slug);
            if (myChildren.length > 0) {
              return (
                <div 
                  key={parent.id}
                  className="dropdown" 
                  onClick={() => setDropdownOpen(dropdownOpen === parent.id ? null : parent.id)}
                  onMouseEnter={() => setDropdownOpen(parent.id)}
                  onMouseLeave={() => setDropdownOpen(null)}
                >
                  <span className="dropdown-trigger">{parent.navLabel || parent.title} ▾</span>
                  <div className={`dropdown-content glass-panel ${dropdownOpen === parent.id ? 'show' : ''}`}>
                    {myChildren.map(child => {
                      const subChildren = children.filter(c => c.navParent === child.slug);
                      if (subChildren.length > 0) {
                        return (
                          <div key={child.id} className="nested-dropdown">
                            <span className="nested-dropdown-trigger" style={{ padding: '0.65rem 1.2rem', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600 }}>
                              {child.navLabel || child.title} <span className="nested-indicator">❯</span>
                            </span>
                            <div className="nested-dropdown-content glass-panel">
                              {subChildren.map(sub => (
                                <Link key={sub.id} href={`/info/${sub.slug}`} onClick={() => setIsOpen(false)}>
                                  {sub.navLabel || sub.title}
                                </Link>
                              ))}
                            </div>
                          </div>
                        );
                      }
                      return (
                        <Link key={child.id} href={`/info/${child.slug}`} onClick={() => setIsOpen(false)}>
                          {child.navLabel || child.title}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              );
            }
            return (
              <Link key={parent.id} href={`/info/${parent.slug}`} onClick={() => setIsOpen(false)}>
                {parent.navLabel || parent.title}
              </Link>
            );
          })}
          {jobsPage && (
            <Link href="/jobs" onClick={() => setIsOpen(false)}>
              {jobsPage.navLabel || jobsPage.title}
            </Link>
          )}
          {alertPage && (
            <Link href="/job-alert" onClick={() => setIsOpen(false)}>
              {alertPage.navLabel || alertPage.title}
            </Link>
          )}
          {initiativPage && (
            <Link href={`/info/${initiativPage.slug}`} className="btn-primary mobile-btn" onClick={() => setIsOpen(false)}>
              {initiativPage.navLabel || initiativPage.title}
            </Link>
          )}
          <Link href="/login" className="cms-link" onClick={() => setIsOpen(false)}>
            🔒 CMS Login
          </Link>
        </div>
      </div>
    </nav>
  );
}
