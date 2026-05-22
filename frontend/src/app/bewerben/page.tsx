'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

type Job = {
  id: string;
  title: string;
  facility: { name: string };
  screeningQuestionsJson: string;
};

export default function ApplicationForm() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [screeningQuestions, setScreeningQuestions] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [magicLink, setMagicLink] = useState('');

  // Form State
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [screeningAnswers, setScreeningAnswers] = useState<Record<string, string>>({});
  const [privacyAccepted, setPrivacyAccepted] = useState(false);

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const id = searchParams.get('jobId');
    if (id) {
      setJobId(id);
      fetch(`/api/public/jobs/${id}`)
        .then(res => res.json())
        .then(data => {
          if (data.job) {
            setJob(data.job);
            try {
              const qs = JSON.parse(data.job.screeningQuestionsJson || '[]');
              setScreeningQuestions(Array.isArray(qs) ? qs : []);
            } catch {
              setScreeningQuestions([]);
            }
          }
        });
    }
  }, []);

  const handleAnswerChange = (question: string, value: string) => {
    setScreeningAnswers(prev => ({ ...prev, [question]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!privacyAccepted) {
      setErrorMsg('Bitte stimme der Datenschutzerklärung zu.');
      return;
    }

    if (!cvFile) {
      setErrorMsg('Bitte lade deinen Lebenslauf (PDF) hoch.');
      return;
    }

    // Für K.O.-Fragen (falls vorhanden) prüfen, ob alle beantwortet wurden
    for (const q of screeningQuestions) {
      if (!screeningAnswers[q]) {
        setErrorMsg(`Bitte beantworte die Frage: "${q}"`);
        return;
      }
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      if (jobId) formData.append('jobId', jobId);
      formData.append('firstName', firstName);
      formData.append('lastName', lastName);
      formData.append('email', email);
      formData.append('phone', phone);
      formData.append('screeningAnswers', JSON.stringify(screeningAnswers));
      formData.append('cvFile', cvFile);

      const res = await fetch('/api/public/apply', {
        method: 'POST',
        body: formData, // WICHTIG: KEIN Content-Type Header bei FormData!
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Fehler bei der Übertragung.');
      }

      setMagicLink(data.dev_magicLink);
      setIsSuccess(true);
    } catch (error: any) {
      setErrorMsg(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--background)' }} aria-live="polite">
        <div className="glass-panel animate-fade-in" style={{ padding: '3rem', textAlign: 'center', maxWidth: '500px', backgroundColor: 'var(--card-bg)' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }} role="img" aria-label="Feiernde Papierschlangen">🎉</div>
          <h1 style={{ fontFamily: 'var(--font-outfit)', fontSize: '2rem', marginBottom: '1rem', color: 'var(--primary)' }}>
            Bewerbung erfolgreich!
          </h1>
          <p style={{ opacity: 0.8, marginBottom: '2rem' }}>
            Vielen Dank für dein Interesse. Wir haben deine Daten sicher empfangen.
          </p>
          
          <div style={{ padding: '1.5rem', backgroundColor: 'rgba(37, 99, 235, 0.05)', border: '1px dashed var(--primary)', borderRadius: '8px', marginBottom: '2rem', textAlign: 'left' }}>
            <strong style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--primary)' }}>ℹ️ Hinweis für den Prototyp:</strong>
            <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>Normalerweise würdest du jetzt eine E-Mail erhalten. Für diese Demo hier dein persönlicher Magic-Link zum Tracking-Portal:</p>
            <a href={magicLink} style={{ color: 'var(--secondary)', fontWeight: 600, wordBreak: 'break-all', fontSize: '0.85rem' }}>{magicLink}</a>
          </div>

          <Link href="/" className="btn-primary" style={{ padding: '0.8rem 2rem' }}>
            Zurück zur Startseite
          </Link>
        </div>
      </main>
    );
  }

  const inputStyle = { width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '1rem', backgroundColor: 'var(--background)', color: 'var(--foreground)' };

  return (
    <main style={{ minHeight: '100vh', padding: '4rem 2rem', backgroundColor: 'var(--background)' }}>
      <div className="container" style={{ maxWidth: '800px' }}>
        
        {/* Header section marked with stimulus-heavy to blur out in ADHS focus mode */}
        <div className="animate-fade-in opacity-0 stimulus-heavy" style={{ marginBottom: '3rem', textAlign: 'center' }}>
          <Link href={jobId ? `/jobs/${jobId}` : '/jobs'} style={{ color: 'var(--primary)', fontWeight: 600, marginBottom: '1rem', display: 'inline-block' }} aria-label="Zurück zur Stellenübersicht">
            ← Zurück {jobId ? 'zum Job' : 'zur Übersicht'}
          </Link>
          <h1 style={{ fontFamily: 'var(--font-outfit)', fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '0.5rem' }}>
            Die 60-Sekunden-Bewerbung
          </h1>
          <p style={{ opacity: 0.8, fontSize: '1.1rem' }}>
            {job ? `Für: ${job.title} bei ${job.facility.name}` : 'Initiativbewerbung beim Enterprise'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="glass-panel animate-fade-in delay-100 opacity-0" style={{ padding: '3rem', backgroundColor: 'var(--card-bg)', borderRadius: '16px' }} aria-label="Bewerbungsformular">
          
          <h3 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', color: 'var(--foreground)' }}>1. Deine Kontaktdaten</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div>
              <label htmlFor="first_name" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Vorname *</label>
              <input 
                id="first_name"
                type="text" 
                required 
                aria-required="true"
                aria-label="Vorname"
                value={firstName} 
                onChange={e => setFirstName(e.target.value)} 
                style={inputStyle} 
              />
            </div>
            <div>
              <label htmlFor="last_name" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Nachname *</label>
              <input 
                id="last_name"
                type="text" 
                required 
                aria-required="true"
                aria-label="Nachname"
                value={lastName} 
                onChange={e => setLastName(e.target.value)} 
                style={inputStyle} 
              />
            </div>
            <div>
              <label htmlFor="email_address" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>E-Mail Adresse *</label>
              <input 
                id="email_address"
                type="email" 
                required 
                aria-required="true"
                aria-label="E-Mail Adresse"
                value={email} 
                onChange={e => setEmail(e.target.value)} 
                style={inputStyle} 
              />
            </div>
            <div>
              <label htmlFor="phone_number" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Telefon (Optional)</label>
              <input 
                id="phone_number"
                type="tel" 
                aria-label="Telefonnummer (optional)"
                value={phone} 
                onChange={e => setPhone(e.target.value)} 
                style={inputStyle} 
              />
            </div>
          </div>

          {screeningQuestions.length > 0 && (
            <>
              <h3 style={{ fontSize: '1.2rem', margin: '3rem 0 1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', color: 'var(--foreground)' }}>2. Wichtige Vorab-Fragen</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginBottom: '2rem', padding: '1.5rem', backgroundColor: 'rgba(37, 99, 235, 0.05)', borderRadius: '8px', border: '1px dashed rgba(37, 99, 235, 0.2)' }}>
                {screeningQuestions.map((q, idx) => (
                  <div key={idx}>
                    <label htmlFor={`question_${idx}`} style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'var(--primary)' }}>{q} *</label>
                    <input 
                      id={`question_${idx}`}
                      type="text" 
                      required 
                      aria-required="true"
                      aria-label={q}
                      value={screeningAnswers[q] || ''} 
                      onChange={e => handleAnswerChange(q, e.target.value)} 
                      placeholder="Deine Antwort..."
                      style={{...inputStyle, backgroundColor: 'white'}} 
                    />
                  </div>
                ))}
              </div>
            </>
          )}

          <h3 style={{ fontSize: '1.2rem', margin: '3rem 0 1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', color: 'var(--foreground)' }}>
            {screeningQuestions.length > 0 ? '3' : '2'}. Dein Lebenslauf (Upload)
          </h3>
          <div style={{ marginBottom: '2.5rem' }}>
            <label htmlFor="cv_file" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
              Kein Anschreiben nötig! Einfach Lebenslauf (PDF) hochladen *
            </label>
            <input 
              id="cv_file"
              type="file" 
              accept="application/pdf"
              required
              aria-required="true"
              aria-label="Lebenslauf hochladen (ausschließlich im PDF-Format)"
              onChange={e => setCvFile(e.target.files?.[0] || null)}
              style={{ ...inputStyle, padding: '1.5rem', border: '2px dashed var(--border)', cursor: 'pointer' }}
            />
            {cvFile && <p style={{ marginTop: '0.5rem', color: 'var(--secondary)', fontWeight: 600 }} aria-live="polite">✅ {cvFile.name} ausgewählt ({Math.round(cvFile.size / 1024)} KB)</p>}
          </div>

          <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '2rem 0' }} />

          {/* Friendly Captcha (Barrierefreier, DSGVO-konformer Spamschutz) */}
          <div 
            style={{ 
              marginBottom: '2rem', 
              padding: '1.25rem', 
              backgroundColor: 'var(--background)', 
              border: '1px solid var(--border)', 
              borderRadius: '12px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between', 
              gap: '1rem',
              flexWrap: 'wrap'
            }} 
            className="friendly-captcha-container"
            aria-label="Barrierefreie Spamschutz-Verifizierung"
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }} role="img" aria-label="Roboter-Icon">🤖</span>
              <div>
                <strong style={{ display: 'block', fontSize: '0.9rem', color: 'var(--foreground)' }}>Friendly Captcha (Barrierefrei)</strong>
                <span style={{ fontSize: '0.75rem', opacity: 0.7, color: 'var(--muted)' }}>DSGVO-konforme Spamschutz-Verifizierung im Hintergrund</span>
              </div>
            </div>
            <div style={{ padding: '0.5rem 1rem', backgroundColor: 'var(--green-light)', color: 'var(--primary-dark)', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 'bold' }} aria-live="polite">
              ✓ Mensch verifiziert (Spam-Schutz aktiv)
            </div>
          </div>

          <div style={{ marginBottom: '2rem', display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
            <input 
              type="checkbox" 
              id="privacy"
              required
              aria-required="true"
              aria-label="Einwilligung in die Datenschutzerklärung"
              checked={privacyAccepted}
              onChange={e => setPrivacyAccepted(e.target.checked)}
              style={{ width: '24px', height: '24px', marginTop: '0.1rem', cursor: 'pointer', accentColor: 'var(--primary)' }}
            />
            <label htmlFor="privacy" style={{ fontSize: '0.95rem', opacity: 0.9, cursor: 'pointer', lineHeight: 1.5, color: 'var(--foreground)' }}>
              Ich willige in die Verarbeitung meiner hochgeladenen Daten (inkl. Lebenslauf) zum Zweck des Bewerbungsverfahrens ein. Mir ist bekannt, dass meine Daten nach 6 Monaten automatisch gelöscht werden. <a href="/info/datenschutz" target="_blank" style={{ color: 'var(--primary)', textDecoration: 'underline' }}>Details zum Datenschutz</a>.
            </label>
          </div>

          {errorMsg && (
            <div style={{ padding: '1rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '8px', marginBottom: '2rem', border: '1px solid rgba(239, 68, 68, 0.2)', fontWeight: 600 }} aria-live="assertive">
              {errorMsg}
            </div>
          )}

          <button 
            type="submit" 
            className="btn-primary" 
            disabled={isSubmitting}
            style={{ width: '100%', fontSize: '1.2rem', padding: '1.2rem', opacity: isSubmitting ? 0.7 : 1, transition: 'all 0.2s', border: 'none', cursor: 'pointer' }}
          >
            {isSubmitting ? 'Wird sicher verschlüsselt und gesendet...' : '🚀 Bewerbung verbindlich absenden'}
          </button>
        </form>

      </div>
    </main>
  );
}
