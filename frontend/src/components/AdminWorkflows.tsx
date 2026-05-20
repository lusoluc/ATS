'use client';
import { useState, useEffect } from 'react';

type WorkflowStep = { id: string; name: string; type: 'SYSTEM' | 'HUMAN' | 'APPROVAL'; description?: string };
type Workflow = { id: string; name: string; locationIdsJson?: string; categoryIdsJson?: string; jobIdsJson?: string; stepsJson: string };

export default function AdminWorkflows() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [locations, setLocations] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [editing, setEditing] = useState<Workflow | null>(null);
  const [parsedSteps, setParsedSteps] = useState<WorkflowStep[]>([]);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    try {
      const [wfRes, locRes, catRes, jobRes] = await Promise.all([
        fetch('/api/cms/workflows'),
        fetch('/api/cms/locations'),
        fetch('/api/cms/categories'),
        fetch('/api/cms/jobs')
      ]);
      const wfData = await wfRes.json();
      setWorkflows(wfData.workflows || []);

      const locData = await locRes.json();
      setLocations(locData.locations || []);

      const catData = await catRes.json();
      setCategories(catData.categories || []);

      const jobData = await jobRes.json();
      setJobs(jobData.jobs || []);
    } catch (e) {
      console.error(e);
    }
  };

  const startEdit = (wf: Workflow) => {
    setEditing(wf);
    try {
      setParsedSteps(JSON.parse(wf.stepsJson) || []);
    } catch {
      setParsedSteps([]);
    }
    setMsg('');
  };

  const createNew = () => {
    setEditing({ id: '', name: 'Neuer Workflow', stepsJson: '[]' });
    setParsedSteps([
      { id: 'step-1', name: 'Eingang / HR-Sichtung', type: 'HUMAN' },
      { id: 'step-2', name: 'Fachabteilung prüfen', type: 'APPROVAL' },
      { id: 'step-3', name: 'Hospitation', type: 'HUMAN' },
      { id: 'step-4', name: 'Vertragsangebot', type: 'SYSTEM' }
    ]);
    setMsg('');
  };

  const save = async () => {
    if (!editing) return;
    try {
      const payload = {
        id: editing.id || undefined,
        name: editing.name,
        locationIdsJson: editing.locationIdsJson || '[]',
        categoryIdsJson: editing.categoryIdsJson || '[]',
        jobIdsJson: editing.jobIdsJson || '[]',
        stepsJson: JSON.stringify(parsedSteps)
      };
      
      const res = await fetch('/api/cms/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setMsg('✅ Workflow erfolgreich gespeichert!');
        setEditing(null);
        load();
      } else {
        const d = await res.json();
        setMsg(`❌ Fehler: ${d.error}`);
      }
    } catch (e) {
      setMsg('❌ Verbindungsfehler beim Speichern.');
    }
  };

  const del = async (id: string) => {
    if (!window.confirm('Workflow wirklich löschen?')) return;
    try {
      const res = await fetch(`/api/cms/workflows?id=${id}`, { method: 'DELETE' });
      if (res.ok) {
        setMsg('✅ Workflow gelöscht.');
        load();
      } else {
        const d = await res.json();
        setMsg(`❌ Fehler: ${d.error}`);
      }
    } catch (e) {
      setMsg('❌ Verbindungsfehler beim Löschen.');
    }
  };

  const moveStep = (index: number, direction: 'up' | 'down') => {
    const newSteps = [...parsedSteps];
    if (direction === 'up' && index > 0) {
      const temp = newSteps[index - 1];
      newSteps[index - 1] = newSteps[index];
      newSteps[index] = temp;
    } else if (direction === 'down' && index < newSteps.length - 1) {
      const temp = newSteps[index + 1];
      newSteps[index + 1] = newSteps[index];
      newSteps[index] = temp;
    }
    setParsedSteps(newSteps);
  };

  const addStep = () => {
    setParsedSteps([...parsedSteps, { id: `step-${Date.now()}`, name: 'Neuer Schritt', type: 'HUMAN' }]);
  };

  const removeStep = (index: number) => {
    const newSteps = [...parsedSteps];
    newSteps.splice(index, 1);
    setParsedSteps(newSteps);
  };

  const updateStep = (index: number, field: keyof WorkflowStep, value: string) => {
    const newSteps = [...parsedSteps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setParsedSteps(newSteps);
  };

  const toggleSelection = (field: 'locationIdsJson' | 'categoryIdsJson' | 'jobIdsJson', id: string) => {
    if (!editing) return;
    let current = [];
    try { current = JSON.parse(editing[field] || '[]'); } catch {}
    
    if (current.includes(id)) {
      current = current.filter((x: string) => x !== id);
    } else {
      current.push(id);
    }
    setEditing({ ...editing, [field]: JSON.stringify(current) });
  };

  const inputStyle = { padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' };

  if (editing) {
    return (
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', color: 'var(--primary)' }}>Workflow Editor</h1>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button onClick={() => setEditing(null)} className="btn-outline">Abbrechen</button>
            <button onClick={save} className="btn-primary">💾 Speichern</button>
          </div>
        </div>

        {msg && <p style={{ marginBottom: '1rem', color: msg.startsWith('✅') ? 'green' : 'red', fontWeight: 'bold' }}>{msg}</p>}

        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>Allgemeine Einstellungen</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '2rem', marginTop: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem' }}>🌍 Standorte</label>
              <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '6px', padding: '0.5rem', background: 'var(--background)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem', cursor: 'pointer', borderBottom: '1px solid var(--border)', fontWeight: 'bold', opacity: (!editing.locationIdsJson || editing.locationIdsJson === '[]') ? 1 : 0.5 }}>
                  <input type="checkbox" checked={!editing.locationIdsJson || editing.locationIdsJson === '[]'} onChange={() => setEditing({ ...editing, locationIdsJson: '[]' })} />
                  Alle Standorte (Global)
                </label>
                {locations.map(loc => {
                  let isSelected = false;
                  try { isSelected = JSON.parse(editing.locationIdsJson || '[]').includes(loc.id); } catch {}
                  return (
                    <label key={loc.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem', cursor: 'pointer', borderBottom: '1px solid var(--border)' }}>
                      <input type="checkbox" checked={isSelected} onChange={() => toggleSelection('locationIdsJson', loc.id)} />
                      {loc.name}
                    </label>
                  );
                })}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem' }}>🏷️ Berufsfelder</label>
              <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '6px', padding: '0.5rem', background: 'var(--background)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem', cursor: 'pointer', borderBottom: '1px solid var(--border)', fontWeight: 'bold', opacity: (!editing.categoryIdsJson || editing.categoryIdsJson === '[]') ? 1 : 0.5 }}>
                  <input type="checkbox" checked={!editing.categoryIdsJson || editing.categoryIdsJson === '[]'} onChange={() => setEditing({ ...editing, categoryIdsJson: '[]' })} />
                  Alle Berufsfelder
                </label>
                {categories.map(cat => {
                  let isSelected = false;
                  try { isSelected = JSON.parse(editing.categoryIdsJson || '[]').includes(cat.id); } catch {}
                  return (
                    <label key={cat.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem', cursor: 'pointer', borderBottom: '1px solid var(--border)' }}>
                      <input type="checkbox" checked={isSelected} onChange={() => toggleSelection('categoryIdsJson', cat.id)} />
                      {cat.name}
                    </label>
                  );
                })}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem' }}>💼 Spezielle Jobs</label>
              <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '6px', padding: '0.5rem', background: 'var(--background)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem', cursor: 'pointer', borderBottom: '1px solid var(--border)', fontWeight: 'bold', opacity: (!editing.jobIdsJson || editing.jobIdsJson === '[]') ? 1 : 0.5 }}>
                  <input type="checkbox" checked={!editing.jobIdsJson || editing.jobIdsJson === '[]'} onChange={() => setEditing({ ...editing, jobIdsJson: '[]' })} />
                  Alle Jobs (Keine Ausnahme)
                </label>
                {jobs.map(job => {
                  let isSelected = false;
                  try { isSelected = JSON.parse(editing.jobIdsJson || '[]').includes(job.id); } catch {}
                  return (
                    <label key={job.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem', cursor: 'pointer', borderBottom: '1px solid var(--border)' }}>
                      <input type="checkbox" checked={isSelected} onChange={() => toggleSelection('jobIdsJson', job.id)} />
                      {job.title}
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '2rem', borderRadius: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3>Kanban-Spalten (Prozessschritte)</h3>
            <button onClick={addStep} className="btn-primary" style={{ padding: '0.5rem 1rem' }}>+ Schritt hinzufügen</button>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {parsedSteps.map((step, index) => (
              <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', background: 'var(--background)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                  <button onClick={() => moveStep(index, 'up')} disabled={index === 0} style={{ border: 'none', background: 'none', cursor: index === 0 ? 'not-allowed' : 'pointer', opacity: index === 0 ? 0.3 : 1 }}>🔼</button>
                  <button onClick={() => moveStep(index, 'down')} disabled={index === parsedSteps.length - 1} style={{ border: 'none', background: 'none', cursor: index === parsedSteps.length - 1 ? 'not-allowed' : 'pointer', opacity: index === parsedSteps.length - 1 ? 0.3 : 1 }}>🔽</button>
                </div>
                
                <div style={{ flex: 1 }}>
                  <input value={step.name} onChange={e => updateStep(index, 'name', e.target.value)} style={{ ...inputStyle, width: '100%', fontWeight: 'bold' }} placeholder="Spalten-Name (z.B. Telefon-Interview)" />
                </div>
                
                <div style={{ width: '200px' }}>
                  <select value={step.type} onChange={e => updateStep(index, 'type', e.target.value)} style={{ ...inputStyle, width: '100%' }}>
                    <option value="HUMAN">👤 Manuell (HR)</option>
                    <option value="APPROVAL">✅ Fachabteilung (Approval)</option>
                    <option value="SYSTEM">🤖 System-Aktion (Auto)</option>
                  </select>
                </div>

                <div style={{ flex: 1 }}>
                  <input value={step.description || ''} onChange={e => updateStep(index, 'description', e.target.value)} style={{ ...inputStyle, width: '100%' }} placeholder="Kurze Beschreibung (optional)" />
                </div>

                <button onClick={() => removeStep(index)} style={{ border: 'none', background: '#ef4444', color: 'white', padding: '0.5rem', borderRadius: '6px', cursor: 'pointer' }}>✕</button>
              </div>
            ))}
            {parsedSteps.length === 0 && <p style={{ opacity: 0.6 }}>Keine Schritte definiert. Füge mindestens einen Schritt hinzu.</p>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', color: 'var(--primary)' }}>Prozessflows (Bewerber-Pipelines)</h1>
        <button onClick={createNew} className="btn-primary">✨ Neuen Workflow erstellen</button>
      </div>

      <p style={{ opacity: 0.8, marginBottom: '2rem' }}>Definiere individuelle Bewerber-Pipelines (Kanban-Spalten) für bestimmte Standorte oder globale Standard-Prozesse.</p>

      {msg && <div style={{ marginBottom: '1.5rem', padding: '1rem', borderRadius: '8px', background: msg.startsWith('✅') ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: msg.startsWith('✅') ? 'green' : 'red', fontWeight: 'bold' }}>{msg}</div>}

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        {workflows.map(wf => {
          let stepsCount = 0;
          try { stepsCount = JSON.parse(wf.stepsJson).length; } catch {}
          
          return (
            <div key={wf.id} className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderLeft: wf.facilityId ? '4px solid var(--primary)' : '4px solid #10b981' }}>
              <div>
                <h3 style={{ fontSize: '1.3rem', marginBottom: '0.3rem' }}>{wf.name}</h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', fontSize: '0.9rem', opacity: 0.7 }}>
                  <span>📍 Standorte: {(() => {
                    try {
                      const ids = JSON.parse(wf.locationIdsJson || '[]');
                      if (ids.length === 0) return 'Global (Alle)';
                      return ids.map((id: string) => locations.find(l => l.id === id)?.name || id).join(', ');
                    } catch { return 'Global (Alle)'; }
                  })()}</span>
                  <span>|</span>
                  <span>🏷️ Berufsfelder: {(() => {
                    try {
                      const ids = JSON.parse(wf.categoryIdsJson || '[]');
                      if (ids.length === 0) return 'Global (Alle)';
                      return ids.map((id: string) => categories.find(c => c.id === id)?.name || id).join(', ');
                    } catch { return 'Global (Alle)'; }
                  })()}</span>
                  <span>|</span>
                  <span>💼 Ausnahmen: {(() => {
                    try {
                      const ids = JSON.parse(wf.jobIdsJson || '[]');
                      if (ids.length === 0) return 'Keine speziellen Jobs';
                      return `${ids.length} Jobs`;
                    } catch { return 'Keine speziellen Jobs'; }
                  })()}</span>
                  <span>|</span>
                  <span>📑 {stepsCount} Prozessschritte</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button onClick={() => startEdit(wf)} className="btn-outline">✏️ Bearbeiten</button>
                <button onClick={() => del(wf.id)} style={{ padding: '0.5rem 1rem', background: '#ef4444', color: 'white', borderRadius: '8px', border: 'none', cursor: 'pointer' }}>Löschen</button>
              </div>
            </div>
          );
        })}
        {workflows.length === 0 && (
          <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', borderRadius: '12px', opacity: 0.6 }}>
            <p style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Noch keine eigenen Workflows definiert.</p>
            <p>Das System nutzt intern einen Hardcoded-Standard. Klicke auf "Neuen Workflow erstellen", um diesen zu überschreiben.</p>
          </div>
        )}
      </div>
    </div>
  );
}
