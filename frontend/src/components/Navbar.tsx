'use client';
import { useState } from 'react';
import Link from 'next/link';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

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
          <div 
            className="dropdown" 
            onClick={() => setDropdownOpen(!dropdownOpen)}
            onMouseEnter={() => setDropdownOpen(true)}
            onMouseLeave={() => setDropdownOpen(false)}
          >
            <span className="dropdown-trigger">Beruf & Karriere ▾</span>
            <div className={`dropdown-content glass-panel ${dropdownOpen ? 'show' : ''}`}>
              <Link href="/info/_de_beruf_und_karriere_ausbildung_" onClick={() => setIsOpen(false)}>Ausbildung</Link>
              <Link href="/info/_de_beruf_und_karriere_praktikum_" onClick={() => setIsOpen(false)}>Praktikum</Link>
              <Link href="/info/_de_beruf_und_karriere_freiwilligendienst_fsj_und_bfd_" onClick={() => setIsOpen(false)}>FSJ & BFD</Link>
              <Link href="/info/_de_beruf_und_karriere_praktisches_jahr_und_aerztliche_weiterbildung_" onClick={() => setIsOpen(false)}>Ärztliche Weiterbildung</Link>
            </div>
          </div>
          
          <Link href="/arbeitgeber" onClick={() => setIsOpen(false)}>Arbeitgeber</Link>
          <Link href="/jobs" onClick={() => setIsOpen(false)}>Stellenangebote</Link>
          <Link href="/job-alert" onClick={() => setIsOpen(false)}>Job-Alert</Link>
          <Link href="/info/_de_initiativbewerbung_" className="btn-primary mobile-btn" onClick={() => setIsOpen(false)}>
            Initiativbewerbung
          </Link>
          <Link href="/login" className="cms-link" onClick={() => setIsOpen(false)}>
            🔒 CMS Login
          </Link>
        </div>
      </div>
    </nav>
  );
}
