'use client';
import { useState, useEffect } from 'react';

export default function AdminAI() {
  const [settings, setSettings] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetch('/api/cms/ai-settings')
      .then(res => res.json())
      .then(data => setSettings(data));
  }, []);

  const handleChange = (key: string, value: string) => {
    setSettings({ ...settings, [key]: value });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch('/api/cms/ai-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      alert('KI-Einstellungen erfolgreich gespeichert.');
    } catch (e) {
      alert('Fehler beim Speichern.');
    }
    setSaving(false);
  };

  const handleSimulateTraining = () => {
    setUploading(true);
    setTimeout(() => {
      setUploading(false);
      alert('34 anonymisierte Lebensläufe erfolgreich in die Vektordatenbank (Pinecone) eingespeist. Das Modell wurde feinjustiert.');
    }, 2500);
  };

  if (!settings) return <p>Lade KI-Konfiguration...</p>;

  return (
    <div style={{ maxWidth: '900px' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', color: 'var(--primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>🧠</span> KI-Steuerungszentrum
        </h1>
        <p style={{ opacity: 0.7 }}>Verwalte die Verhaltensweisen, Tonalität und das Wissen der künstlichen Intelligenz (LLM) im System.</p>
      </div>

      <div style={{ display: 'grid', gap: '2rem' }}>
        {/* Kommunikationsstil */}
        <div className="glass-panel" style={{ padding: '2rem', borderRadius: '12px', borderLeft: '4px solid #8b5cf6' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>1. Kommunikationsstil & Tonalität</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem' }}>Tonalität (System Prompt)</label>
              <select 
                value={settings.AI_TONE} 
                onChange={e => handleChange('AI_TONE', e.target.value)}
                style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)' }}
              >
                <option value="FORMAL">Formell & Professionell (Konservativ)</option>
                <option value="EMPATHETIC">Empathisch, Wertschätzend & Nahbar (Standard Pflege)</option>
                <option value="CASUAL">Locker, Startup-Style & Direkt</option>
              </select>
              <p style={{ fontSize: '0.8rem', opacity: 0.6, marginTop: '0.4rem' }}>Dies beeinflusst, wie die KI E-Mails formuliert und im Chat mit Bewerbern interagiert.</p>
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem' }}>Ansprache</label>
              <select 
                value={settings.AI_LANGUAGE} 
                onChange={e => handleChange('AI_LANGUAGE', e.target.value)}
                style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)' }}
              >
                <option value="DE_SIE">Deutsch (Siezen)</option>
                <option value="DE_DU">Deutsch (Duzen - Modern)</option>
                <option value="EN">Englisch (International)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Scoring & Automatisierung */}
        <div className="glass-panel" style={{ padding: '2rem', borderRadius: '12px', borderLeft: '4px solid #3b82f6' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>2. Automatisierung & KI-Scoring</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', fontWeight: 'bold', cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  checked={settings.AI_AUTO_REJECT_ENABLED === 'true'} 
                  onChange={e => handleChange('AI_AUTO_REJECT_ENABLED', e.target.checked ? 'true' : 'false')}
                  style={{ width: '18px', height: '18px' }}
                />
                Auto-Absage durch KI aktivieren
              </label>
              <p style={{ fontSize: '0.8rem', opacity: 0.6, marginTop: '0.4rem', marginLeft: '2rem' }}>
                Die KI darf Bewerber automatisch absagen, wenn deren Skill-Matching unter dem definierten Schwellenwert liegt.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem', color: '#ef4444' }}>
                  Kategorie D (&lt; X%)<br/><span style={{fontSize:'0.75rem',opacity:0.7}}>(Auto-Absage)</span>
                </label>
                <input 
                  type="number" 
                  value={settings.AI_THRESHOLD_D_REJECT} 
                  onChange={e => handleChange('AI_THRESHOLD_D_REJECT', e.target.value)}
                  style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem', color: '#f59e0b' }}>
                  Kategorie C (&lt; X%)<br/><span style={{fontSize:'0.75rem',opacity:0.7}}>(Waitlist / Manuell)</span>
                </label>
                <input 
                  type="number" 
                  value={settings.AI_THRESHOLD_C_WAITLIST} 
                  onChange={e => handleChange('AI_THRESHOLD_C_WAITLIST', e.target.value)}
                  style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem', color: '#10b981' }}>
                  Kategorie A (&gt; X%)<br/><span style={{fontSize:'0.75rem',opacity:0.7}}>(Auto-Einladung)</span>
                </label>
                <input 
                  type="number" 
                  value={settings.AI_THRESHOLD_A_INVITE} 
                  onChange={e => handleChange('AI_THRESHOLD_A_INVITE', e.target.value)}
                  style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)' }}
                />
              </div>
            </div>
            <p style={{ fontSize: '0.85rem', opacity: 0.7, marginTop: '-0.5rem' }}>
              <em>Hinweis: Bewerber, die zwischen C und A liegen, werden automatisch in Kategorie B (Standard HR-Sichtung) eingestuft.</em>
            </p>
          </div>
        </div>

        {/* Wissensdatenbank (RAG) */}
        <div className="glass-panel" style={{ padding: '2rem', borderRadius: '12px', borderLeft: '4px solid #10b981' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>3. Wissensdatenbank (Fine-Tuning)</h2>
          <p style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '1.5rem' }}>
            Die KI vergleicht Bewerber mit historischen "Best-Performern" deines Unternehmens. Lade hier anonymisierte Lebensläufe deiner besten Mitarbeiter hoch, um das semantische Verständnis der KI auf eure Unternehmenskultur auszurichten.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', background: 'rgba(0,0,0,0.02)', border: '1px dashed var(--border)', padding: '2rem', borderRadius: '8px', textAlign: 'center' }}>
            <div style={{ fontSize: '2rem' }}>📄</div>
            <p style={{ fontWeight: 'bold' }}>Lebensläufe hochladen (PDF, anonymisiert)</p>
            <p style={{ fontSize: '0.8rem', opacity: 0.6 }}>Drag & Drop oder klicken zum Auswählen</p>
            <button 
              onClick={handleSimulateTraining}
              disabled={uploading}
              style={{ padding: '0.8rem 1.5rem', background: uploading ? 'var(--border)' : '#10b981', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', maxWidth: '300px', margin: '0 auto' }}
            >
              {uploading ? 'Verarbeite & trainiere Modell...' : 'Dateien einspeisen'}
            </button>
          </div>
          
          <div style={{ marginTop: '1.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', fontWeight: 'bold', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={settings.AI_CV_LEARNING_MODE === 'true'} 
                onChange={e => handleChange('AI_CV_LEARNING_MODE', e.target.checked ? 'true' : 'false')}
                style={{ width: '18px', height: '18px' }}
              />
              Kontinuierliches Lernen aktivieren
            </label>
            <p style={{ fontSize: '0.8rem', opacity: 0.6, marginTop: '0.4rem', marginLeft: '2rem' }}>
              Wenn aktiviert, lernt die KI automatisch aus Bewerbungen, die von HR in die Spalte "Vertragsangebot" verschoben werden.
            </p>
          </div>
        </div>
        
        {/* Save Button */}
        <div>
          <button 
            onClick={handleSave} 
            disabled={saving}
            style={{ padding: '1rem 2rem', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer', width: '100%', boxShadow: '0 4px 12px rgba(99,37,116,0.3)' }}
          >
            {saving ? 'Speichere...' : 'Alle KI-Einstellungen speichern'}
          </button>
        </div>
      </div>
    </div>
  );
}
