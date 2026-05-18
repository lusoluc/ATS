'use client';

import { useState } from 'react';

export default function ApplicantDetailClient({ 
  applicationId, 
  initialStatus, 
  initialNotes 
}: { 
  applicationId: string; 
  initialStatus: string; 
  initialNotes: string;
}) {
  const [status, setStatus] = useState(initialStatus);
  const [notes, setNotes] = useState(initialNotes || '');
  const [isUpdating, setIsUpdating] = useState(false);
  const [toast, setToast] = useState('');
  const [useCalendly, setUseCalendly] = useState(false);

  const handleUpdate = async (updateData: any) => {
    setIsUpdating(true);
    try {
      const res = await fetch(`/api/cms/applications/${applicationId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
      });
      if (!res.ok) throw new Error('Fehler beim Speichern');
      
      if (updateData.status) setStatus(updateData.status);
      if (updateData.internalNotes !== undefined) setNotes(updateData.internalNotes);
      
      setToast('✅ Erfolgreich gespeichert');
    } catch (e: any) {
      setToast('❌ Fehler: ' + e.message);
    } finally {
      setIsUpdating(false);
      setTimeout(() => setToast(''), 3000);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem', position: 'sticky', top: '100px' }}>
      {toast && (
        <div style={{ position: 'absolute', top: '-60px', right: '0', background: 'var(--card-bg)', border: '1px solid var(--border)', padding: '1rem', borderRadius: '8px', zIndex: 10, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
          {toast}
        </div>
      )}

      <h3 style={{ fontFamily: 'var(--font-outfit)', marginBottom: '0.5rem' }}>Eignungsprüfung</h3>
      <p style={{ opacity: 0.7, fontSize: '0.9rem', marginBottom: '2rem' }}>
        Aktueller Status: <strong style={{ color: 'var(--primary)' }}>{status}</strong>
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
        <button 
          onClick={() => handleUpdate({ status: 'IN_REVIEW' })}
          disabled={isUpdating || status === 'IN_REVIEW'}
          className="btn-secondary" 
          style={{ width: '100%', opacity: status === 'IN_REVIEW' ? 0.5 : 1 }}
        >
          🔍 In Prüfung nehmen
        </button>
        
        <div style={{ border: '1px solid var(--border)', padding: '1rem', borderRadius: '8px', backgroundColor: 'var(--background)' }}>
          <button 
            onClick={() => handleUpdate({ status: 'INVITED', generateSlots: useCalendly })}
            disabled={isUpdating || status === 'INVITED'}
            className="btn-primary" 
            style={{ backgroundColor: '#10b981', width: '100%', opacity: status === 'INVITED' ? 0.5 : 1, marginBottom: '0.5rem' }}
          >
            ✉️ Einladen
          </button>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={useCalendly} 
              onChange={e => setUseCalendly(e.target.checked)} 
              disabled={status === 'INVITED'}
            />
            Mit Termin-Auswahl (Calendly-Feature)
          </label>
        </div>

        <button 
          onClick={() => handleUpdate({ status: 'REJECTED' })}
          disabled={isUpdating || status === 'REJECTED'}
          className="btn-secondary" 
          style={{ width: '100%', color: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.05)', opacity: status === 'REJECTED' ? 0.5 : 1 }}
        >
          ❌ Absagen (DSGVO-Löschfrist startet)
        </button>
      </div>

      <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--border)' }} />
      
      <h4 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Interne Notizen (HR)</h4>
      <textarea 
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Hinweise für das Interview, Gehaltsvorstellungen etc..."
        style={{ width: '100%', height: '120px', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)', backgroundColor: 'transparent', color: 'var(--foreground)', marginBottom: '1rem', resize: 'vertical' }}
      />
      <button 
        onClick={() => handleUpdate({ internalNotes: notes })}
        disabled={isUpdating || notes === initialNotes}
        className="btn-primary"
        style={{ width: '100%', padding: '0.6rem' }}
      >
        💾 Notizen speichern
      </button>

    </div>
  );
}
