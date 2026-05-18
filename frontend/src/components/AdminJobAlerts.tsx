'use client';
import { useState, useEffect } from 'react';

type Subscription = {
  id: string;
  email: string;
  locations: string;
  categories: string;
  status: string;
  createdAt: string;
  _count?: { logs: number };
};

export default function AdminJobAlerts() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [kpis, setKpis] = useState({ total: 0, active: 0, inactive: 0 });
  const [loading, setLoading] = useState(true);

  // Formular-Zustand für Erstellen/Bearbeiten
  const [isEditing, setIsEditing] = useState(false);
  const [formMsg, setFormMsg] = useState('');
  const [form, setForm] = useState({ id: '', email: '', locations: '', categories: '', status: 'ACTIVE' });

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/cms/job-alerts');
      const data = await res.json();
      setSubscriptions(data.subscriptions || []);
      setKpis(data.kpis || { total: 0, active: 0, inactive: 0 });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAlerts(); }, []);

  const openNewForm = () => {
    setForm({ id: '', email: '', locations: '[]', categories: '[]', status: 'ACTIVE' });
    setFormMsg('');
    setIsEditing(true);
  };

  const openEditForm = (sub: Subscription) => {
    setForm({ 
      id: sub.id, 
      email: sub.email, 
      locations: sub.locations || '[]', 
      categories: sub.categories || '[]', 
      status: sub.status 
    });
    setFormMsg('');
    setIsEditing(true);
  };

  const saveEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormMsg('Speichert...');
    try {
      // Wenn das JSON invalid ist, korrigieren wir es auf ein leeres Array
      let parsedLocations = form.locations;
      let parsedCategories = form.categories;
      try { JSON.parse(form.locations); } catch { parsedLocations = '[]'; }
      try { JSON.parse(form.categories); } catch { parsedCategories = '[]'; }

      const body = {
        ...form,
        locations: parsedLocations,
        categories: parsedCategories
      };

      const res = await fetch('/api/cms/job-alerts', {
        method: form.id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      
      if (res.ok) {
        setFormMsg('✅ Erfolgreich gespeichert!');
        setTimeout(() => { setIsEditing(false); fetchAlerts(); }, 800);
      } else {
        setFormMsg(`❌ Fehler: ${data.error}`);
      }
    } catch (err: any) {
      setFormMsg(`❌ Verbindungsfehler.`);
    }
  };

  const updateStatus = async (id: string, newStatus: string) => {
    await fetch('/api/cms/job-alerts', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, status: newStatus })
    });
    fetchAlerts();
  };

  const deleteSub = async (id: string) => {
    if (!confirm('Eintrag wirklich löschen? Dieser Schritt kann nicht rückgängig gemacht werden.')) return;
    await fetch(`/api/cms/job-alerts?id=${id}`, { method: 'DELETE' });
    fetchAlerts();
  };

  const inputStyle = { width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' };

  if (loading) return <p style={{ opacity: 0.6 }}>Lade Job-Alert Daten und KPIs...</p>;

  // EDITOR VIEW
  if (isEditing) {
    return (
      <div>
        <button onClick={() => setIsEditing(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary)', marginBottom: '1rem', padding: 0 }}>← Zurück zur Übersicht</button>
        <h1 style={{ fontSize: '2rem', color: 'var(--primary)', marginBottom: '1.5rem' }}>
          {form.id ? 'Abonnent bearbeiten' : 'Neuen Abonnenten anlegen'}
        </h1>
        <form onSubmit={saveEntry} className="glass-panel" style={{ padding: '2rem', borderRadius: '12px', maxWidth: '600px' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>E-Mail Adresse *</label>
            <input required type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} style={inputStyle} placeholder="nutzer@email.de" />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Status</label>
            <select value={form.status} onChange={e => setForm({...form, status: e.target.value})} style={inputStyle}>
              <option value="ACTIVE">✅ Aktiv</option>
              <option value="INACTIVE">⏸️ Pausiert / Inaktiv</option>
            </select>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Kategorien / Berufsfelder (JSON-Array)</label>
            <input value={form.categories} onChange={e => setForm({...form, categories: e.target.value})} style={inputStyle} placeholder='z.B. ["Pflege", "Verwaltung"]' />
            <p style={{ fontSize: '0.8rem', opacity: 0.6, marginTop: '0.3rem' }}>Format: <code>["Wert 1", "Wert 2"]</code>. Leer für "Alle" = <code>[]</code></p>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Standorte (JSON-Array)</label>
            <input value={form.locations} onChange={e => setForm({...form, locations: e.target.value})} style={inputStyle} placeholder='z.B. ["Kiel", "Lübeck"]' />
            <p style={{ fontSize: '0.8rem', opacity: 0.6, marginTop: '0.3rem' }}>Format: <code>["Ort 1", "Ort 2"]</code>. Leer für "Alle" = <code>[]</code></p>
          </div>

          {formMsg && <p style={{ marginBottom: '1.5rem', color: formMsg.includes('✅') ? 'var(--green-dark)' : 'red' }}>{formMsg}</p>}
          
          <button type="submit" className="btn-primary" style={{ padding: '0.75rem 2rem' }}>💾 Speichern</button>
        </form>
      </div>
    );
  }

  // LIST VIEW
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <h1 style={{ fontSize: '2rem', color: 'var(--primary)' }}>Job-Alert Abonnenten</h1>
        <button onClick={openNewForm} className="btn-primary" style={{ padding: '0.6rem 1.2rem' }}>➕ Neuer Eintrag</button>
      </div>
      
      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2.5rem' }}>
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', textAlign: 'center' }}>
          <h3 style={{ fontSize: '1rem', opacity: 0.7, marginBottom: '0.5rem' }}>Abonnenten Gesamt</h3>
          <p style={{ fontSize: '3rem', fontWeight: 800, color: 'var(--primary)' }}>{kpis.total}</p>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', textAlign: 'center', borderLeft: '4px solid var(--green-dark)' }}>
          <h3 style={{ fontSize: '1rem', opacity: 0.7, marginBottom: '0.5rem' }}>Aktiv (Erhalten Mails)</h3>
          <p style={{ fontSize: '3rem', fontWeight: 800, color: 'var(--green-dark)' }}>{kpis.active}</p>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', textAlign: 'center', borderLeft: '4px solid #e0932a' }}>
          <h3 style={{ fontSize: '1rem', opacity: 0.7, marginBottom: '0.5rem' }}>Inaktiv / Pausiert</h3>
          <p style={{ fontSize: '3rem', fontWeight: 800, color: '#e0932a' }}>{kpis.inactive}</p>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', overflowX: 'auto' }}>
        <table style={{ width: '100%', minWidth: '800px', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid var(--border)', color: 'var(--primary)' }}>
              <th style={{ padding: '0.75rem' }}>E-Mail Adresse</th>
              <th style={{ padding: '0.75rem' }}>Abonnierte Filter</th>
              <th style={{ padding: '0.75rem' }}>Status</th>
              <th style={{ padding: '0.75rem' }}>Versendete Mails</th>
              <th style={{ padding: '0.75rem' }}>Anmeldedatum</th>
              <th style={{ padding: '0.75rem', textAlign: 'right' }}>Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {subscriptions.length === 0 && (
              <tr><td colSpan={6} style={{ padding: '2rem', textAlign: 'center', opacity: 0.6 }}>Noch keine Abonnenten registriert.</td></tr>
            )}
            {subscriptions.map(sub => {
              const isActive = sub.status === 'active' || sub.status === 'ACTIVE';
              return (
                <tr key={sub.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '0.75rem', fontWeight: 600 }}>{sub.email}</td>
                  <td style={{ padding: '0.75rem', opacity: 0.8 }}>
                    <div style={{ fontSize: '0.8rem', marginBottom: '0.2rem' }}><strong>Kat:</strong> {JSON.parse(sub.categories || '[]').join(', ') || 'Alle'}</div>
                    <div style={{ fontSize: '0.8rem' }}><strong>Ort:</strong> {JSON.parse(sub.locations || '[]').join(', ') || 'Alle'}</div>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{ 
                      padding: '0.25rem 0.6rem', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 600,
                      background: isActive ? 'rgba(133,172,55,0.1)' : 'rgba(224,147,42,0.1)',
                      color: isActive ? 'var(--green-dark)' : '#e0932a'
                    }}>
                      {isActive ? '✅ Aktiv' : '⏸️ Pausiert'}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{ fontWeight: 800, color: 'var(--primary)' }}>{sub._count?.logs || 0}</span>
                  </td>
                  <td style={{ padding: '0.75rem', opacity: 0.7 }}>{new Date(sub.createdAt).toLocaleDateString('de-DE')}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '0.4rem' }}>
                      <button onClick={() => openEditForm(sub)} style={{ padding: '0.4rem 0.7rem', cursor: 'pointer', fontSize: '0.8rem', borderRadius: '6px', background: 'var(--primary)', border: 'none', color: 'white' }}>✏️ Bearbeiten</button>
                      
                      {isActive ? (
                        <button onClick={() => updateStatus(sub.id, 'INACTIVE')} style={{ padding: '0.4rem 0.7rem', cursor: 'pointer', fontSize: '0.8rem', borderRadius: '6px', background: 'transparent', border: '1px solid var(--border)', color: 'var(--foreground)' }}>⏸️</button>
                      ) : (
                        <button onClick={() => updateStatus(sub.id, 'ACTIVE')} style={{ padding: '0.4rem 0.7rem', cursor: 'pointer', fontSize: '0.8rem', borderRadius: '6px', background: 'rgba(133,172,55,0.1)', border: '1px solid var(--green)', color: 'var(--green-dark)' }}>▶️</button>
                      )}
                      
                      <button onClick={() => deleteSub(sub.id)} style={{ padding: '0.4rem 0.7rem', cursor: 'pointer', fontSize: '0.8rem', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.05)', borderRadius: '6px' }} title="Endgültig löschen">🗑️</button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
