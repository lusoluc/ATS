'use client';
import { useState } from 'react';
import Link from 'next/link';

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
  const parents = cmsPages.filter(p => !p.navParent && p.id !== initiativPage?.id);
  const children = cmsPages.filter(p => p.navParent);

  return (
    <nav className="navbar glass-panel">
      <div className="container nav-content">
        <Link href="/" className="nav-logo" onClick={() => setIsOpen(false)}>
          Enterprise
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
                    {myChildren.map(child => (
                      <Link key={child.id} href={`/info/${child.slug}`} onClick={() => setIsOpen(false)}>
                        {child.navLabel || child.title}
                      </Link>
                    ))}
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
          
          <Link href="/jobs" onClick={() => setIsOpen(false)}>Stellenangebote</Link>
          <Link href="/job-alert" onClick={() => setIsOpen(false)}>Job-Alert</Link>
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
