'use client';
import { useState, useEffect } from 'react';

type Item = { id: string; name: string; lat?: number | null; lng?: number | null; archived?: boolean };

export default function AdminMasterData() {
  const [locations, setLocations] = useState<Item[]>([]);
  const [categories, setCategories] = useState<Item[]>([]);
  const [questions, setQuestions] = useState<any[]>([]);
  const [newLocation, setNewLocation] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [newQuestion, setNewQuestion] = useState('');
  const [msg, setMsg] = useState('');

  const load = async () => {
    const [l, c, q] = await Promise.all([
      fetch('/api/cms/locations'), 
      fetch('/api/cms/categories'),
      fetch('/api/cms/questions')
    ]);
    const [ld, cd, qd] = await Promise.all([l.json(), c.json(), q.json()]);
    setLocations(ld.locations || []);
    setCategories(cd.categories || []);
    setQuestions(qd.questions || []);
  };

  useEffect(() => { load(); }, []);

  const addLocation = async () => {
    if (!newLocation.trim()) return;
    const res = await fetch('/api/cms/locations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newLocation.trim() }) });
    const d = await res.json();
    if (res.ok) {
      const geocoded = d.geocoded ? ' (📍 Koordinaten automatisch gesetzt)' : ' (⚠️ Keine Koordinaten gefunden – Umkreissuche eingeschränkt)';
      setMsg(`✅ Standort hinzugefügt${geocoded}`);
      setNewLocation('');
      load();
    } else setMsg(`❌ ${d.error}`);
  };

  const addCategory = async () => {
    if (!newCategory.trim()) return;
    const res = await fetch('/api/cms/categories', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newCategory.trim() }) });
    const d = await res.json();
    if (res.ok) { setMsg('✅ Kategorie hinzugefügt'); setNewCategory(''); load(); }
    else setMsg(`❌ ${d.error}`);
  };

  const addQuestion = async () => {
    if (!newQuestion.trim()) return;
    const res = await fetch('/api/cms/questions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: newQuestion.trim() }) });
    const d = await res.json();
    if (res.ok) { setMsg('✅ K.O.-Frage hinzugefügt'); setNewQuestion(''); load(); }
    else setMsg(`❌ ${d.error}`);
  };

  const editItem = async (type: 'locations' | 'categories' | 'questions', item: any) => {
    const fieldName = type === 'questions' ? 'question' : 'name';
    const newName = window.prompt(`Neu eingeben:`, item[fieldName]);
    if (!newName || newName.trim() === item[fieldName]) return;
    if (!newName || newName.trim() === item.name) return;
    
    const res = await fetch(`/api/cms/${type}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: item.id, [fieldName]: newName.trim() })
    });
    const d = await res.json();
    if (res.ok) {
      setMsg(`✅ Erfolgreich in "${newName.trim()}" umbenannt`);
      load();
    } else {
      setMsg(`❌ Fehler beim Umbenennen: ${d.error}`);
    }
  };

  const archiveItem = async (type: 'locations' | 'categories' | 'questions', item: any) => {
    const isArchiving = !item.archived;
    const res = await fetch(`/api/cms/${type}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: item.id, archived: isArchiving })
    });
    const d = await res.json();
    if (res.ok) {
      setMsg(`✅ Erfolgreich ${isArchiving ? 'archiviert' : 'wiederhergestellt'}`);
      load();
    } else {
      setMsg(`❌ Fehler beim Archivieren: ${d.error}`);
    }
  };

  const deleteItem = async (type: 'locations' | 'categories' | 'questions', item: any) => {
    if (!window.confirm(`Wirklich löschen?`)) return;
    const res = await fetch(`/api/cms/${type}?id=${item.id}`, { method: 'DELETE' });
    const d = await res.json();
    if (res.ok) {
      setMsg(`✅ Erfolgreich gelöscht`);
      load();
    } else {
      setMsg(`❌ Fehler: ${d.error}`);
    }
  };

  const inputStyle = { padding: '0.65rem 1rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)', fontSize: '0.95rem', flex: 1 } as const;
  const getTagStyle = (archived: boolean) => ({ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.4rem 0.8rem', background: archived ? 'var(--background)' : 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '6px', fontSize: '0.88rem', opacity: archived ? 0.6 : 1, filter: archived ? 'grayscale(1)' : 'none' } as const);

  return (
    <div>
      <h1 style={{ fontSize: '2rem', color: 'var(--primary)', marginBottom: '0.5rem' }}>Stammdaten</h1>
      <p style={{ opacity: 0.7, marginBottom: '2rem' }}>Verwalte Standorte und Berufsfelder für Stellenangebote.</p>
      {msg && <div style={{ marginBottom: '1.5rem', padding: '0.75rem 1rem', borderRadius: '8px', background: msg.startsWith('✅') ? 'rgba(133,172,55,0.15)' : 'rgba(239,68,68,0.1)', color: msg.startsWith('✅') ? 'var(--secondary)' : '#ef4444', fontWeight: 500, lineHeight: 1.4 }}>{msg}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
        {/* Standorte */}
        <div className="glass-panel" style={{ padding: '2rem', borderRadius: '16px' }}>
          <h2 style={{ marginBottom: '1.5rem', fontSize: '1.3rem' }}>📍 Standorte ({locations.length})</h2>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <input value={newLocation} onChange={e => setNewLocation(e.target.value)} onKeyDown={e => e.key === 'Enter' && addLocation()} placeholder="z.B. Neumünster" style={inputStyle} />
            <button className="btn-primary" style={{ padding: '0.65rem 1rem', flexShrink: 0 }} onClick={addLocation}>+ Hinzufügen</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {locations.map(l => (
              <div key={l.id} style={getTagStyle(!!l.archived)}>
                <span style={{ fontWeight: 500, textDecoration: l.archived ? 'line-through' : 'none' }}>{l.name}</span>
                <span style={{ fontSize: '0.7rem', opacity: 0.5 }} title={l.lat ? `${l.lat.toFixed(4)}, ${l.lng?.toFixed(4)}` : 'Keine Koordinaten'}>
                  {l.lat ? '📍' : '⚠️'}
                </span>
                <button onClick={() => archiveItem('locations', l)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.9rem', lineHeight: 1, padding: '0 0.2rem' }} title={l.archived ? "Wiederherstellen" : "Archivieren"}>{l.archived ? '🔄' : '📦'}</button>
                <button onClick={() => editItem('locations', l)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary)', fontSize: '0.9rem', lineHeight: 1, padding: '0 0.2rem' }} title="Umbenennen">✏️</button>
                <button onClick={() => deleteItem('locations', l)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', fontSize: '0.9rem', lineHeight: 1, padding: '0 0.2rem' }} title="Löschen">✕</button>
              </div>
            ))}
            {locations.length === 0 && <p style={{ opacity: 0.5, fontSize: '0.9rem' }}>Noch keine Standorte angelegt.</p>}
          </div>
        </div>

        {/* Berufsfelder */}
        <div className="glass-panel" style={{ padding: '2rem', borderRadius: '16px' }}>
          <h2 style={{ marginBottom: '1.5rem', fontSize: '1.3rem' }}>🏷️ Berufsfelder ({categories.length})</h2>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <input value={newCategory} onChange={e => setNewCategory(e.target.value)} onKeyDown={e => e.key === 'Enter' && addCategory()} placeholder="z.B. Hauswirtschaft" style={inputStyle} />
            <button className="btn-primary" style={{ padding: '0.65rem 1rem', flexShrink: 0 }} onClick={addCategory}>+ Hinzufügen</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {categories.map(c => (
              <div key={c.id} style={getTagStyle(!!c.archived)}>
                <span style={{ fontWeight: 500, textDecoration: c.archived ? 'line-through' : 'none' }}>{c.name}</span>
                <button onClick={() => archiveItem('categories', c)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.9rem', lineHeight: 1, padding: '0 0.2rem', marginLeft: '0.2rem' }} title={c.archived ? "Wiederherstellen" : "Archivieren"}>{c.archived ? '🔄' : '📦'}</button>
                <button onClick={() => editItem('categories', c)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary)', fontSize: '0.9rem', lineHeight: 1, padding: '0 0.2rem' }} title="Umbenennen">✏️</button>
                <button onClick={() => deleteItem('categories', c)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', fontSize: '0.9rem', lineHeight: 1, padding: '0 0.2rem' }} title="Löschen">✕</button>
              </div>
            ))}
            {categories.length === 0 && <p style={{ opacity: 0.5, fontSize: '0.9rem' }}>Noch keine Berufsfelder angelegt.</p>}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
        {/* K.O.-Fragen Katalog */}
        <div className="glass-panel" style={{ padding: '2rem', borderRadius: '16px' }}>
          <h2 style={{ marginBottom: '1.5rem', fontSize: '1.3rem' }}>🛡️ K.O.-Fragen Katalog ({questions.length})</h2>
          <p style={{ opacity: 0.7, marginBottom: '1.5rem', fontSize: '0.9rem' }}>Diese Fragen können später beim Erstellen eines Stellenangebots aus einem Dropdown ausgewählt werden.</p>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <input value={newQuestion} onChange={e => setNewQuestion(e.target.value)} onKeyDown={e => e.key === 'Enter' && addQuestion()} placeholder="z.B. Besitzen Sie die Führerscheinklasse B?" style={inputStyle} />
            <button className="btn-primary" style={{ padding: '0.65rem 1rem', flexShrink: 0 }} onClick={addQuestion}>+ Hinzufügen</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {questions.map(q => (
              <div key={q.id} style={getTagStyle(!!q.archived)}>
                <span style={{ fontWeight: 500, textDecoration: q.archived ? 'line-through' : 'none' }}>{q.question}</span>
                <button onClick={() => archiveItem('questions', q)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.9rem', lineHeight: 1, padding: '0 0.2rem', marginLeft: '0.2rem' }} title={q.archived ? "Wiederherstellen" : "Archivieren"}>{q.archived ? '🔄' : '📦'}</button>
                <button onClick={() => editItem('questions', q)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary)', fontSize: '0.9rem', lineHeight: 1, padding: '0 0.2rem' }} title="Bearbeiten">✏️</button>
                <button onClick={() => deleteItem('questions', q)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', fontSize: '0.9rem', lineHeight: 1, padding: '0 0.2rem' }} title="Löschen">✕</button>
              </div>
            ))}
            {questions.length === 0 && <p style={{ opacity: 0.5, fontSize: '0.9rem' }}>Noch keine Fragen angelegt.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
