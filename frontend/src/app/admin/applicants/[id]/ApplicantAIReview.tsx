'use client';
import { useState } from 'react';

export default function ApplicantAIReview({ applicationId }: { applicationId: string }) {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [error, setError] = useState('');

  const analyzeCV = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/cms/ai/analyze-cv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ applicationId })
      });
      const data = await res.json();
      if (res.ok) {
        setAnalysis(data);
      } else {
        setError(data.error || 'Ein Fehler ist aufgetreten');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '2rem', padding: '2rem', background: 'var(--card-bg)', borderRadius: '12px', border: '1px solid var(--border)', boxShadow: '0 4px 20px rgba(0,0,0,0.05)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', fontFamily: 'var(--font-outfit)', color: 'var(--primary)' }}>
            ✨ KI-Lebenslauf-Analyse
          </h3>
          <p style={{ margin: '0.2rem 0 0', fontSize: '0.85rem', opacity: 0.7 }}>
            Läuft zu 100% lokal. Keine Daten verlassen die Server des Enterprises.
          </p>
        </div>
        {!analysis && !loading && (
          <button onClick={analyzeCV} className="btn-primary" style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)', border: 'none' }}>
            <span>🧠</span> Dokument scannen
          </button>
        )}
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '2rem', background: 'rgba(99, 102, 241, 0.05)', borderRadius: '8px', border: '1px dashed rgba(99, 102, 241, 0.3)' }}>
          <div className="spinner" style={{ margin: '0 auto 1rem', width: '30px', height: '30px', border: '3px solid rgba(99,102,241,0.2)', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          <style dangerouslySetInnerHTML={{__html: `@keyframes spin { to { transform: rotate(360deg); } }`}} />
          <p style={{ margin: 0, fontWeight: 600, color: '#6366f1' }}>Gemma liest das Dokument und extrahiert Kernkompetenzen...</p>
        </div>
      )}

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '8px', fontWeight: 600 }}>
          ❌ {error}
        </div>
      )}

      {analysis && !loading && (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(168,85,247,0.1) 100%)', borderRadius: '8px', border: '1px solid rgba(99,102,241,0.2)' }}>
            <div style={{ background: 'white', width: '60px', height: '60px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: 700, color: '#6366f1', boxShadow: '0 4px 10px rgba(0,0,0,0.1)' }}>
              {analysis.matchScore}%
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: '1.1rem', color: '#4f46e5' }}>Match-Score</h4>
              <p style={{ margin: 0, fontSize: '0.85rem', opacity: 0.8 }}>Übereinstimmung mit dem Anforderungsprofil</p>
            </div>
          </div>

          <div>
            <h4 style={{ marginBottom: '0.5rem', color: 'var(--foreground)' }}>📝 Zusammenfassung</h4>
            <p style={{ margin: 0, lineHeight: 1.6, opacity: 0.8, fontSize: '0.95rem' }}>{analysis.summary}</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div>
              <h4 style={{ marginBottom: '0.5rem', color: 'var(--secondary)' }}>✅ Erkannte Skills</h4>
              <ul style={{ margin: 0, paddingLeft: '1.2rem', lineHeight: 1.6, fontSize: '0.9rem', color: '#4b5563' }}>
                {analysis.skills.map((s: string, i: number) => <li key={i}>{s}</li>)}
              </ul>
            </div>
            <div>
              <h4 style={{ marginBottom: '0.5rem', color: '#ef4444' }}>⚠️ Red Flags / Hinweise</h4>
              <ul style={{ margin: 0, paddingLeft: '1.2rem', lineHeight: 1.6, fontSize: '0.9rem', color: '#4b5563' }}>
                {analysis.redFlags.map((s: string, i: number) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          </div>

          <div style={{ fontSize: '0.75rem', opacity: 0.5, textAlign: 'right', marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
            Generiert von {analysis.aiModel} • Die Ergebnisse sind maschinell erzeugt und bedürfen der manuellen Prüfung.
          </div>
        </div>
      )}
    </div>
  );
}
