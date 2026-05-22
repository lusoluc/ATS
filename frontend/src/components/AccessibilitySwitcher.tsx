'use client';

import React, { useState, useEffect } from 'react';

export default function AccessibilitySwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const [contrastMode, setContrastMode] = useState(false);
  const [dyslexicFont, setDyslexicFont] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const [readingRuler, setReadingRuler] = useState(false);
  const [rulerY, setRulerY] = useState(0);

  // Load initial states from localStorage if available
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedContrast = localStorage.getItem('access-contrast') === 'true';
      const savedDyslexic = localStorage.getItem('access-dyslexic') === 'true';
      const savedFocus = localStorage.getItem('access-focus') === 'true';

      if (savedContrast) {
        setContrastMode(true);
        document.body.classList.add('accessibility-contrast-mode');
      }
      if (savedDyslexic) {
        setDyslexicFont(true);
        document.body.classList.add('font-dyslexic');
      }
      if (savedFocus) {
        setFocusMode(true);
        document.body.classList.add('accessibility-focus-mode');
      }
    }
  }, []);

  // Track mouse movement for reading ruler
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setRulerY(e.clientY);
    };

    if (readingRuler) {
      window.addEventListener('mousemove', handleMouseMove);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, [readingRuler]);

  const toggleContrast = () => {
    const next = !contrastMode;
    setContrastMode(next);
    localStorage.setItem('access-contrast', String(next));
    if (next) {
      document.body.classList.add('accessibility-contrast-mode');
    } else {
      document.body.classList.remove('accessibility-contrast-mode');
    }
  };

  const toggleDyslexic = () => {
    const next = !dyslexicFont;
    setDyslexicFont(next);
    localStorage.setItem('access-dyslexic', String(next));
    if (next) {
      document.body.classList.add('font-dyslexic');
    } else {
      document.body.classList.remove('font-dyslexic');
    }
  };

  const toggleFocus = () => {
    const next = !focusMode;
    setFocusMode(next);
    localStorage.setItem('access-focus', String(next));
    if (next) {
      document.body.classList.add('accessibility-focus-mode');
    } else {
      document.body.classList.remove('accessibility-focus-mode');
    }
  };

  const speakSelectedText = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const selection = window.getSelection()?.toString();
      if (selection) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(selection);
        utterance.lang = 'de-DE';
        window.speechSynthesis.speak(utterance);
      } else {
        // Read main contents
        window.speechSynthesis.cancel();
        const textToRead = document.querySelector('main')?.textContent || document.body.textContent || '';
        const cleanText = textToRead.replace(/\s+/g, ' ').substring(0, 400); // read introduction preview
        const utterance = new SpeechSynthesisUtterance(cleanText + "... Markieren Sie einen Text, um ihn mir vorlesen zu lassen.");
        utterance.lang = 'de-DE';
        window.speechSynthesis.speak(utterance);
      }
    } else {
      alert('Sprachausgabe wird von Ihrem Browser leider nicht unterstützt.');
    }
  };

  const stopSpeaking = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  };

  return (
    <>
      {/* Floating Reading Ruler */}
      {readingRuler && (
        <div 
          style={{
            position: 'fixed',
            left: 0,
            right: 0,
            top: rulerY,
            height: '24px',
            backgroundColor: 'rgba(234, 179, 8, 0.25)',
            borderTop: '2px solid #eab308',
            borderBottom: '2px solid #eab308',
            pointerEvents: 'none',
            zIndex: 99999,
            transform: 'translateY(-12px)',
            backdropFilter: 'invert(0.1)'
          }}
        />
      )}

      {/* Floating Action Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed',
          bottom: '80px',
          right: '20px',
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: '#632574',
          color: '#ffffff',
          boxShadow: '0 8px 24px rgba(99, 37, 116, 0.3)',
          border: '2px solid #ffffff',
          zIndex: 99990,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
        }}
        className="hover:scale-110 active:scale-95"
        aria-label="Barrierefreiheit und Inklusions-Optionen öffnen"
        title="Barrierefreiheit-Toolbar"
      >
        <span style={{ fontSize: '1.8rem', lineHeight: 1 }}>♿</span>
      </button>

      {/* Slide-out Accessibility Drawer */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '150px',
            right: '20px',
            width: '320px',
            backgroundColor: contrastMode ? '#000000' : 'rgba(255, 255, 255, 0.95)',
            color: contrastMode ? '#ffffff' : '#1a0a22',
            border: contrastMode ? '3px solid #ffff00' : '1px solid rgba(99, 37, 116, 0.15)',
            borderRadius: '24px',
            padding: '24px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
            zIndex: 99995,
            backdropFilter: 'blur(10px)',
            fontFamily: dyslexicFont ? '"Comic Sans MS", sans-serif' : 'inherit'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(128,128,128,0.2)', paddingBottom: '8px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>♿ Inklusions-Optionen</h3>
            <button 
              onClick={() => setIsOpen(false)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1.2rem',
                color: contrastMode ? '#ffff00' : '#6b7280',
                padding: '4px'
              }}
            >
              ✕
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Contrast Mode Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <strong style={{ display: 'block', fontSize: '0.9rem' }}>👁️ Kontrast-Modus</strong>
                <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>Maximaler Kontrast für BFSG</span>
              </div>
              <input 
                type="checkbox" 
                checked={contrastMode} 
                onChange={toggleContrast}
                style={{ width: '20px', height: '20px', cursor: 'pointer' }}
              />
            </div>

            {/* Dyslexic Font Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <strong style={{ display: 'block', fontSize: '0.9rem' }}>✍️ Legasthenie-Schrift</strong>
                <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>Optimiertes Lesen & Abstände</span>
              </div>
              <input 
                type="checkbox" 
                checked={dyslexicFont} 
                onChange={toggleDyslexic}
                style={{ width: '20px', height: '20px', cursor: 'pointer' }}
              />
            </div>

            {/* ADHS Focus Mode Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <strong style={{ display: 'block', fontSize: '0.9rem' }}>🧘 Reizreduktion (ADHS)</strong>
                <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>Fokus auf wichtige Formulare</span>
              </div>
              <input 
                type="checkbox" 
                checked={focusMode} 
                onChange={toggleFocus}
                style={{ width: '20px', height: '20px', cursor: 'pointer' }}
              />
            </div>

            {/* Reading Ruler Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <strong style={{ display: 'block', fontSize: '0.9rem' }}>📏 Lese-Lineal</strong>
                <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>Visuelles Lese-Führungshilfe</span>
              </div>
              <input 
                type="checkbox" 
                checked={readingRuler} 
                onChange={() => setReadingRuler(!readingRuler)}
                style={{ width: '20px', height: '20px', cursor: 'pointer' }}
              />
            </div>

            {/* Text to Speech Tool */}
            <div style={{ marginTop: '8px', borderTop: '1px solid rgba(128,128,128,0.2)', paddingTop: '12px' }}>
              <strong style={{ display: 'block', fontSize: '0.9rem', marginBottom: '8px' }}>🔊 Vorlesefunktion</strong>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={speakSelectedText}
                  style={{
                    flex: 1,
                    padding: '8px',
                    borderRadius: '8px',
                    backgroundColor: contrastMode ? '#000000' : '#85AC37',
                    color: contrastMode ? '#ffff00' : '#ffffff',
                    border: contrastMode ? '2px solid #ffff00' : 'none',
                    fontWeight: 'bold',
                    fontSize: '0.8rem',
                    cursor: 'pointer'
                  }}
                >
                  Text vorlesen
                </button>
                <button
                  onClick={stopSpeaking}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    backgroundColor: contrastMode ? '#000000' : '#e11d48',
                    color: contrastMode ? '#ffffff' : '#ffffff',
                    border: contrastMode ? '2px solid #ffffff' : 'none',
                    fontWeight: 'bold',
                    fontSize: '0.8rem',
                    cursor: 'pointer'
                  }}
                  title="Stopp"
                >
                  ■
                </button>
              </div>
              <p style={{ fontSize: '0.7rem', opacity: 0.7, marginTop: '6px', textAlign: 'center' }}>
                Tipp: Text markieren und auf &quot;Text vorlesen&quot; klicken.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
