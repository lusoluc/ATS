'use client';
import { useState, useEffect, useCallback } from 'react';

type Item = { id: string; name: string; archived?: boolean };
type Metadata = {
  locations: Item[];
  categories: Item[];
  facilities: { id: string; name: string }[];
  departments: { id: string; name: string; facilityId: string }[];
  contacts: { id: string; firstName: string; lastName: string; globalJobTitle: string }[];
  benefits: { id: string; name: string; icon: string }[];
  snippets: { id: string; category: string; content: string; jobFamilyId: string | null }[];
  questions: { id: string; question: string; archived: boolean }[];
};

type Job = { 
  id: string; title: string; description: string; 
  tasksJson: string; requirementsJson: string; screeningQuestionsJson: string;
  location: Item; jobFamily: Item; workflowState: Item; facility: Item;
  contactPerson?: { id: string; firstName: string; lastName: string };
  benefits: { id: string; name: string }[];
  departmentId?: string;
};

type FilterTab = 'all' | 'published' | 'draft' | 'in_review' | 'archived';

export default function AdminJobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [meta, setMeta] = useState<Metadata | null>(null);
  const [aiSettings, setAiSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  
  // Form State
  const [form, setForm] = useState({ 
    title: '', description: '', locationId: '', facilityId: '', departmentId: '',
    jobFamilyId: '', contactPersonId: '', workflowState: 'published',
    tasks: [] as string[], requirements: [] as string[], benefitIds: [] as string[],
    screeningQuestions: [] as string[]
  });
  
  // AGG Check State
  const [aggCheckLoading, setAggCheckLoading] = useState(false);
  const [aggWarnings, setAggWarnings] = useState<string[]>([]);
  const [aggChecked, setAggChecked] = useState(false);

  // Translate State
  const [translateLoading, setTranslateLoading] = useState(false);
  
  const [newTask, setNewTask] = useState('');
  const [newReq, setNewReq] = useState('');
  const [msg, setMsg] = useState('');
  const [view, setView] = useState<'list' | 'new' | 'edit'>('list');
  const [activeTab, setActiveTab] = useState<FilterTab>('all');

  const load = useCallback(async () => {
    setLoading(true);
    const [j, m, l, c, q] = await Promise.all([
      fetch('/api/cms/jobs'), 
      fetch('/api/cms/job-metadata'),
      fetch('/api/cms/locations'), 
      fetch('/api/cms/categories'),
      fetch('/api/cms/questions'),
      fetch('/api/cms/ai-settings')
    ]);
    const [jd, md, ld, cd, qd, ai] = await Promise.all([j.json(), m.json(), l.json(), c.json(), q.json(), aiRes.json()]);
    
    setJobs(jd.jobs || []);
    setMeta({
      locations: ld.locations || [],
      categories: cd.categories || [],
      facilities: md.facilities || [],
      departments: md.departments || [],
      contacts: md.contacts || [],
      benefits: md.benefits || [],
      snippets: md.snippets || [],
      questions: qd.questions || [],
    });
    setAiSettings(ai);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const openNew = () => {
    setForm({ 
      title: '', description: '', 
      locationId: meta?.locations[0]?.id || '', 
      jobFamilyId: meta?.categories[0]?.id || '', 
      facilityId: meta?.facilities[0]?.id || '',
      departmentId: '', contactPersonId: '',
      workflowState: 'published',
      tasks: [], requirements: [], benefitIds: [], screeningQuestions: []
    });
    setMsg(''); setEditingJob(null); setView('new');
  };

  const openEdit = (job: Job) => {
    let t: string[] = []; let r: string[] = []; let s: string[] = [];
    try { t = JSON.parse(job.tasksJson || '[]'); } catch(e){}
    try { r = JSON.parse(job.requirementsJson || '[]'); } catch(e){}
    try { s = JSON.parse(job.screeningQuestionsJson || '[]'); } catch(e){}

    setForm({ 
      title: job.title, description: job.description || '', 
      locationId: job.location.id, jobFamilyId: job.jobFamily.id, 
      facilityId: job.facility.id, departmentId: job.departmentId || '',
      contactPersonId: job.contactPerson?.id || '',
      workflowState: job.workflowState.name,
      tasks: t, requirements: r,
      benefitIds: job.benefits.map(b => b.id),
      screeningQuestions: s
    });
    setMsg(''); setEditingJob(job); setView('edit');
  };

  const duplicate = (job: Job) => {
    openEdit(job);
    setForm(p => ({ ...p, title: `Kopie von ${job.title}`, workflowState: 'draft' }));
    setMsg('✏️ Kopie erstellt – bitte anpassen und speichern.');
    setEditingJob(null); // Force it to be a NEW job
    setView('new');
  };

  const archive = async (job: Job) => {
    if (!confirm(`"${job.title}" archivieren?`)) return;
    const res = await fetch(`/api/cms/jobs?id=${job.id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ workflowState: 'archived' }),
    });
    if (res.ok) load();
  };

  const reactivate = async (job: Job) => {
    await fetch(`/api/cms/jobs?id=${job.id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ workflowState: 'published' }),
    });
    load();
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg('');
    const isEdit = view === 'edit' && editingJob;
    const url = isEdit ? `/api/cms/jobs?id=${editingJob.id}` : '/api/cms/jobs';
    
    const payload = {
      ...form,
      tasksJson: JSON.stringify(form.tasks),
      requirementsJson: JSON.stringify(form.requirements),
      screeningQuestionsJson: JSON.stringify(form.screeningQuestions)
    };

    const res = await fetch(url, { method: isEdit ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const d = await res.json();
    if (res.ok) { setMsg('✅ Gespeichert!'); await load(); setTimeout(() => setView('list'), 800); }
    else setMsg(`❌ ${d.error}`);
  };

  const del = async (id: string) => {
    if (!confirm('Job endgültig löschen? (Archivieren ist besser)')) return;
    await fetch(`/api/cms/jobs?id=${id}`, { method: 'DELETE' });
    load();
  };

  const toggleBenefit = (id: string) => {
    setForm(p => ({
      ...p,
      benefitIds: p.benefitIds.includes(id) ? p.benefitIds.filter(b => b !== id) : [...p.benefitIds, id]
    }));
  };

  const toggleQuestion = (q: string) => {
    setForm(p => ({
      ...p,
      screeningQuestions: p.screeningQuestions.includes(q) ? p.screeningQuestions.filter(sq => sq !== q) : [...p.screeningQuestions, q]
    }));
  };

  const addArrayItem = (type: 'tasks' | 'requirements', val: string, setVal: (v: string) => void) => {
    if (!val.trim()) return;
    setForm(p => ({ ...p, [type]: [...p[type], val.trim()] }));
    setVal('');
  };

  const removeArrayItem = (type: 'tasks' | 'requirements', idx: number) => {
    setForm(p => ({ ...p, [type]: p[type].filter((_, i) => i !== idx) }));
  };

  const runAggCheck = async () => {
    setAggCheckLoading(true);
    setAggWarnings([]);
    try {
      const res = await fetch('/api/cms/ai/agg-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: form.title,
          description: form.description,
          tasks: form.tasks,
          requirements: form.requirements,
          prompt: aiSettings?.AI_AGG_PROMPT
        })
      });
      const data = await res.json();
      if (res.ok) {
        setAggWarnings(data.warnings || []);
        setAggChecked(true);
      }
    } catch (e) {
      console.error("AGG Check error", e);
    } finally {
      setAggCheckLoading(false);
    }
  };

  const translateToEasyLanguage = () => {
    setTranslateLoading(true);
    // Simulation API Call for translation
    setTimeout(() => {
      setForm(p => ({
        ...p,
        description: 'Diese Stelle wurde in leichte Sprache übersetzt. Wir suchen nette Menschen. Die Arbeit ist leicht zu verstehen.',
        tasks: p.tasks.map(t => 'Leicht: ' + t),
        requirements: p.requirements.map(r => 'Du kannst: ' + r)
      }));
      setTranslateLoading(false);
      setMsg('✨ In leichte Sprache übersetzt!');
    }, 2000);
  };

  const inputStyle = { width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)', fontSize: '0.95rem' } as const;

  const statusLabel: Record<string, { label: string; color: string; bg: string }> = {
    published: { label: '✅ Veröffentlicht', color: 'var(--secondary)', bg: 'rgba(133,172,55,0.15)' },
    draft:     { label: '📝 Entwurf',        color: '#e0932a',          bg: 'rgba(224,147,42,0.15)' },
    in_review: { label: '🔍 In Prüfung',     color: '#7b8cde',          bg: 'rgba(123,140,222,0.15)' },
    archived:  { label: '📦 Archiviert',     color: '#888',             bg: 'rgba(128,128,128,0.1)' },
  };

  const tabs: { key: FilterTab; label: string }[] = [
    { key: 'all',       label: `Alle (${jobs.length})` },
    { key: 'published', label: `Aktiv (${jobs.filter(j => j.workflowState.name === 'published').length})` },
    { key: 'draft',     label: `Entwürfe (${jobs.filter(j => j.workflowState.name === 'draft').length})` },
    { key: 'in_review', label: `In Prüfung (${jobs.filter(j => j.workflowState.name === 'in_review').length})` },
    { key: 'archived',  label: `Archiv (${jobs.filter(j => j.workflowState.name === 'archived').length})` },
  ];

  const filtered = activeTab === 'all' ? jobs : jobs.filter(j => j.workflowState.name === activeTab);

  // ===== FORMULAR-ANSICHT (Neu / Bearbeiten) =====
  if (view !== 'list' && meta) {
    const relevantSnippets = meta.snippets.filter(s => s.jobFamilyId === form.jobFamilyId || !s.jobFamilyId);
    const taskSnippets = relevantSnippets.filter(s => s.category === 'TASKS');
    const reqSnippets = relevantSnippets.filter(s => s.category === 'REQUIREMENTS');

    return (
      <div style={{ maxWidth: '900px' }}>
        <button type="button" onClick={(e) => { e.preventDefault(); setView('list'); }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary)', marginBottom: '1rem', padding: 0, fontSize: '0.9rem' }}>← Zurück zur Liste</button>
        <h1 style={{ fontSize: '2rem', color: 'var(--primary)', marginBottom: '0.5rem', fontFamily: 'var(--font-outfit)' }}>
          {view === 'edit' ? 'Job bearbeiten (Modular)' : 'Neues Stellenangebot (Wizard)'}
        </h1>
        <p style={{ opacity: 0.7, marginBottom: '2rem' }}>Erstelle Stellenangebote schneller und konsistenter mithilfe unserer Textbausteine.</p>
        
        <form onSubmit={save} style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Basisdaten */}
          <div className="glass-panel" style={{ padding: '2rem', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <h3 style={{ margin: 0, color: 'var(--primary)', fontFamily: 'var(--font-outfit)' }}>1. Grunddaten & Zuordnung</h3>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <label style={{ display: 'block', fontWeight: 600 }}>Jobtitel *</label>
                {form.title.length > 0 && !form.title.toLowerCase().includes('(m/w/d)') && (
                  <span style={{ fontSize: '0.8rem', color: '#ef4444', fontWeight: 600 }}>⚠️ AGG-Hinweis: Geschlechtsneutrale Endung (m/w/d) fehlt!</span>
                )}
              </div>
              <input required value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="z.B. Pflegefachkraft (m/w/d)" style={{...inputStyle, border: form.title.length > 0 && !form.title.toLowerCase().includes('(m/w/d)') ? '1px solid #ef4444' : inputStyle.border}} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem' }}>Berufsfeld (Kategorie)</label>
                <select value={form.jobFamilyId} onChange={e => setForm(p => ({ ...p, jobFamilyId: e.target.value }))} style={inputStyle}>
                  <option value="">– Auswählen –</option>
                  {meta.categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem' }}>Einrichtung</label>
                <select value={form.facilityId} onChange={e => setForm(p => ({ ...p, facilityId: e.target.value }))} style={inputStyle}>
                  <option value="">– Auswählen –</option>
                  {meta.facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem' }}>Arbeitsort (PLZ / Stadt)</label>
                <select value={form.locationId} onChange={e => setForm(p => ({ ...p, locationId: e.target.value }))} style={inputStyle}>
                  <option value="">– Auswählen –</option>
                  {meta.locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Aufgaben & Profil (Modular) */}
          <div className="glass-panel" style={{ padding: '2rem', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: 'var(--primary)', fontFamily: 'var(--font-outfit)' }}>2. Inhalte (Aufgaben & Profil)</h3>
              {aiSettings?.AI_TRANSLATE_EASY_LANGUAGE === 'true' && (
                <button type="button" onClick={translateToEasyLanguage} disabled={translateLoading} className="btn-secondary" style={{ padding: '0.4rem 0.8rem', background: 'linear-gradient(135deg, #10b981 0%, #3b82f6 100%)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '0.85rem' }}>
                  {translateLoading ? 'Übersetze...' : '✨ In Leichte Sprache übersetzen'}
                </button>
              )}
            </div>
            
            {/* TASKS */}
            <div>
              <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem' }}>Deine Aufgaben</label>
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1rem 0', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {form.tasks.map((t, idx) => (
                  <li key={idx} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span style={{ color: 'var(--secondary)' }}>✓</span>
                    <input value={t} onChange={e => {
                      const newT = [...form.tasks]; newT[idx] = e.target.value;
                      setForm(p => ({...p, tasks: newT}));
                    }} style={{...inputStyle, padding: '0.4rem', fontSize: '0.9rem'}} />
                    <button type="button" onClick={() => removeArrayItem('tasks', idx)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}>✕</button>
                  </li>
                ))}
              </ul>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input value={newTask} onChange={e => setNewTask(e.target.value)} onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addArrayItem('tasks', newTask, setNewTask))} placeholder="Neue Aufgabe tippen..." style={{...inputStyle, padding: '0.5rem'}} />
                <button type="button" onClick={() => addArrayItem('tasks', newTask, setNewTask)} className="btn-secondary" style={{ padding: '0.5rem 1rem' }}>Hinzufügen</button>
              </div>
              
              {/* Snippet Suggestions */}
              {taskSnippets.length > 0 && (
                <div style={{ marginTop: '1rem', padding: '1rem', background: '#f3f4f6', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#6b7280', marginBottom: '0.5rem', textTransform: 'uppercase' }}>💡 Intelligente Vorschläge (Berufsfeld)</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {taskSnippets.map(s => (
                      <button type="button" key={s.id} onClick={() => setForm(p => ({...p, tasks: [...p.tasks, s.content]}))}
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem', background: 'white', border: '1px solid #d1d5db', borderRadius: '4px', cursor: 'pointer', textAlign: 'left' }}>
                        + {s.content.slice(0, 40)}...
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* REQUIREMENTS */}
            <div>
              <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem' }}>Dein Profil (Anforderungen)</label>
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1rem 0', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {form.requirements.map((r, idx) => (
                  <li key={idx} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span style={{ color: 'var(--secondary)' }}>✓</span>
                    <input value={r} onChange={e => {
                      const newR = [...form.requirements]; newR[idx] = e.target.value;
                      setForm(p => ({...p, requirements: newR}));
                    }} style={{...inputStyle, padding: '0.4rem', fontSize: '0.9rem'}} />
                    <button type="button" onClick={() => removeArrayItem('requirements', idx)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}>✕</button>
                  </li>
                ))}
              </ul>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input value={newReq} onChange={e => setNewReq(e.target.value)} onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addArrayItem('requirements', newReq, setNewReq))} placeholder="Neue Anforderung tippen..." style={{...inputStyle, padding: '0.5rem'}} />
                <button type="button" onClick={() => addArrayItem('requirements', newReq, setNewReq)} className="btn-secondary" style={{ padding: '0.5rem 1rem' }}>Hinzufügen</button>
              </div>

              {/* Snippet Suggestions */}
              {reqSnippets.length > 0 && (
                <div style={{ marginTop: '1rem', padding: '1rem', background: '#f3f4f6', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#6b7280', marginBottom: '0.5rem', textTransform: 'uppercase' }}>💡 Intelligente Vorschläge (Berufsfeld)</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {reqSnippets.map(s => (
                      <button type="button" key={s.id} onClick={() => setForm(p => ({...p, requirements: [...p.requirements, s.content]}))}
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem', background: 'white', border: '1px solid #d1d5db', borderRadius: '4px', cursor: 'pointer', textAlign: 'left' }}>
                        + {s.content.slice(0, 40)}...
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem', color: '#6b7280' }}>Alter Freitext (Optional / Fallback)</label>
              <textarea rows={3} value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} placeholder="Wird nur angezeigt, wenn modular nichts gepflegt ist..." style={{ ...inputStyle, resize: 'vertical', fontSize: '0.85rem' }} />
            </div>
          </div>

          {/* Benefits & Contact */}
          <div className="glass-panel" style={{ padding: '2rem', borderRadius: '16px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
            <div>
              <h3 style={{ margin: '0 0 1rem 0', color: 'var(--primary)', fontFamily: 'var(--font-outfit)' }}>3. Benefits auswählen</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {meta.benefits.map(b => (
                  <label key={b.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', padding: '0.5rem', background: form.benefitIds.includes(b.id) ? 'rgba(133,172,55,0.1)' : 'transparent', borderRadius: '8px', border: form.benefitIds.includes(b.id) ? '1px solid var(--secondary)' : '1px solid transparent' }}>
                    <input type="checkbox" checked={form.benefitIds.includes(b.id)} onChange={() => toggleBenefit(b.id)} style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }} />
                    <span style={{ fontSize: '1.2rem' }}>{b.icon}</span>
                    <span style={{ fontWeight: form.benefitIds.includes(b.id) ? 600 : 400 }}>{b.name}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <h3 style={{ margin: '0 0 1rem 0', color: 'var(--primary)', fontFamily: 'var(--font-outfit)' }}>4. Ansprechpartner & Workflow</h3>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem' }}>Ansprechpartner (Für Rückfragen)</label>
                <select value={form.contactPersonId} onChange={e => setForm(p => ({ ...p, contactPersonId: e.target.value }))} style={inputStyle}>
                  <option value="">– Keiner ausgewählt –</option>
                  {meta.contacts.map(c => <option key={c.id} value={c.id}>{c.firstName} {c.lastName} ({c.globalJobTitle})</option>)}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem' }}>Veröffentlichungs-Status</label>
                <select value={form.workflowState} onChange={e => setForm(p => ({ ...p, workflowState: e.target.value }))} style={{...inputStyle, background: 'var(--primary)', color: 'white', fontWeight: 600}}>
                  <option value="published">✅ Veröffentlicht (Online)</option>
                  <option value="draft">📝 Entwurf (Offline)</option>
                  <option value="in_review">🔍 In Freigabe-Prüfung</option>
                  <option value="archived">📦 Archiviert (Offline)</option>
                </select>
              </div>
            </div>

            <div style={{ gridColumn: '1 / -1' }}>
              <h3 style={{ margin: '1rem 0', color: 'var(--primary)', fontFamily: 'var(--font-outfit)' }}>5. K.O.-Fragen (Screening)</h3>
              <p style={{ opacity: 0.7, fontSize: '0.9rem', marginBottom: '1rem' }}>Wähle Fragen aus dem Katalog, die Bewerber zwingend beantworten müssen.</p>
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {meta.questions.filter(q => !q.archived || form.screeningQuestions.includes(q.question)).map(q => (
                  <label key={q.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', padding: '0.75rem 1rem', background: form.screeningQuestions.includes(q.question) ? 'rgba(37, 99, 235, 0.05)' : 'var(--background)', borderRadius: '8px', border: form.screeningQuestions.includes(q.question) ? '1px solid var(--primary)' : '1px solid var(--border)' }}>
                    <input type="checkbox" checked={form.screeningQuestions.includes(q.question)} onChange={() => toggleQuestion(q.question)} style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }} />
                    <span style={{ fontWeight: form.screeningQuestions.includes(q.question) ? 600 : 400 }}>{q.question}</span>
                  </label>
                ))}
                {meta.questions.length === 0 && <p style={{ opacity: 0.6, fontSize: '0.9rem' }}>Keine K.O.-Fragen im Katalog hinterlegt. (Siehe Stammdaten)</p>}
              </div>
            </div>
          </div>

          {aiSettings?.AI_AGG_CHECK_ENABLED === 'true' && (
          <div style={{ padding: '1.5rem', background: 'var(--card-bg)', borderRadius: '16px', border: aggChecked && aggWarnings.length === 0 ? '1px solid #10b981' : aggWarnings.length > 0 ? '1px solid #ef4444' : '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, color: 'var(--foreground)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>⚖️ Arbeitsrechtlicher AGG-Check (KI)</h3>
              <button type="button" onClick={runAggCheck} disabled={aggCheckLoading} className="btn-secondary" style={{ padding: '0.5rem 1rem', background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)', color: 'white', border: 'none', opacity: aggCheckLoading ? 0.7 : 1 }}>
                {aggCheckLoading ? 'Prüft...' : '🔍 Gesamte Anzeige prüfen'}
              </button>
            </div>
            
            {!aggChecked && !aggCheckLoading && (
              <p style={{ margin: 0, opacity: 0.7, fontSize: '0.9rem' }}>Bevor Sie die Anzeige veröffentlichen, können Sie den gesamten Text von unserer KI auf mögliche Verstöße gegen das Allgemeine Gleichbehandlungsgesetz (AGG) prüfen lassen.</p>
            )}

            {aggCheckLoading && (
               <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#6366f1', fontWeight: 600 }}>
                 <div className="spinner" style={{ width: '20px', height: '20px', border: '2px solid rgba(99,102,241,0.2)', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
                 Gemma prüft Formulierungen...
               </div>
            )}

            {aggChecked && aggWarnings.length === 0 && !aggCheckLoading && (
              <div style={{ color: '#10b981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                ✅ Keine AGG-Verstöße gefunden. Die Anzeige kann sicher veröffentlicht werden!
              </div>
            )}

            {aggChecked && aggWarnings.length > 0 && !aggCheckLoading && (
              <div style={{ color: '#ef4444', background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px' }}>
                <strong style={{ display: 'block', marginBottom: '0.5rem' }}>⚠️ Achtung! KI hat kritische Formulierungen entdeckt:</strong>
                <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
                  {aggWarnings.map((w, idx) => <li key={idx} style={{ marginBottom: '0.3rem' }}>{w}</li>)}
                </ul>
              </div>
            )}
          </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button type="submit" className="btn-primary" style={{ padding: '1rem 2rem', fontSize: '1.1rem' }}>💾 Job {view === 'edit' ? 'aktualisieren' : 'anlegen'}</button>
            {msg && <span style={{ padding: '0.75rem 1rem', borderRadius: '8px', background: msg.startsWith('✅') ? 'rgba(133,172,55,0.15)' : msg.startsWith('✏️') ? 'rgba(123,140,222,0.15)' : 'rgba(239,68,68,0.1)', color: msg.startsWith('✅') ? 'var(--secondary)' : msg.startsWith('✏️') ? '#7b8cde' : '#ef4444', fontWeight: 600 }}>{msg}</span>}
          </div>
        </form>
      </div>
    );
  }

  // ===== LISTEN-ANSICHT =====
  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', color: 'var(--primary)' }}>Stellenangebote</h1>
          <p style={{ opacity: 0.7 }}>{jobs.length} Jobs gesamt in der Datenbank</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn-primary" onClick={openNew}>➕ Neuer Job (Wizard)</button>
          <button onClick={() => window.open('/jobs', '_blank')} style={{ padding: '0.6rem 1rem', background: 'transparent', border: '1px solid var(--border)', borderRadius: '8px', cursor: 'pointer', color: 'var(--foreground)', fontSize: '0.9rem' }}>Website ansehen →</button>
        </div>
      </div>

      {/* Status-Tabs */}
      <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1.5rem', flexWrap: 'wrap', borderBottom: '1px solid var(--border)', paddingBottom: '0' }}>
        {tabs.map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{
            padding: '0.5rem 1rem', fontSize: '0.85rem', border: 'none', cursor: 'pointer',
            background: 'transparent', fontWeight: activeTab === tab.key ? 700 : 400,
            color: activeTab === tab.key ? 'var(--primary)' : 'var(--foreground)',
            borderBottom: activeTab === tab.key ? '2px solid var(--primary)' : '2px solid transparent',
            opacity: activeTab === tab.key ? 1 : 0.6, transition: 'all 0.15s',
          }}>{tab.label}</button>
        ))}
      </div>

      {/* Job-Liste */}
      {loading ? <p style={{ opacity: 0.6, padding: '3rem', textAlign: 'center' }}>Lädt intelligente Module...</p> : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {filtered.length === 0 && (
            <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', borderRadius: '12px', opacity: 0.7 }}>
              {activeTab === 'all' ? 'Noch keine Jobs. Klicke auf "Neuer Job (Wizard)".' : `Keine Jobs mit Status "${activeTab}".`}
            </div>
          )}
          {filtered.map(job => {
            const st = statusLabel[job.workflowState?.name || 'draft'] || { label: 'Unbekannt', color: '#888', bg: 'transparent' };
            const isArchived = job.workflowState?.name === 'archived';
            return (
              <div key={job.id} className="glass-panel" style={{ padding: '1rem 1.5rem', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', opacity: isArchived ? 0.75 : 1 }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <p style={{ fontWeight: 600, margin: '0 0 0.2rem 0', fontSize: '1.1rem' }}>{job.title}</p>
                    <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem', borderRadius: '20px', background: st.bg, color: st.color, whiteSpace: 'nowrap', fontWeight: 600 }}>{st.label}</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', opacity: 0.7, margin: 0 }}>
                    📍 {job.location?.name} · 🏢 {job.facility?.name} · 🏷️ {job.jobFamily?.name}
                  </p>
                </div>

                {/* Aktions-Buttons */}
                <div style={{ display: 'flex', gap: '0.4rem', flexShrink: 0, flexWrap: 'wrap' }}>
                  {!isArchived && (
                    <>
                      <button onClick={() => openEdit(job)} style={{ padding: '0.4rem 0.8rem', fontSize: '0.82rem', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                        ✏️ Bearbeiten
                      </button>
                      <button onClick={() => window.open(`/jobs/${job.id}`, '_blank')} style={{ padding: '0.4rem 0.7rem', fontSize: '0.82rem', background: 'transparent', border: '1px solid var(--border)', borderRadius: '6px', cursor: 'pointer', color: 'var(--foreground)' }}>
                        👁️ Vorschau
                      </button>
                      <button onClick={() => archive(job)} title="Job archivieren" style={{ padding: '0.4rem 0.7rem', fontSize: '0.82rem', background: 'rgba(128,128,128,0.1)', border: '1px solid rgba(128,128,128,0.3)', borderRadius: '6px', cursor: 'pointer', color: '#888' }}>
                        📦
                      </button>
                    </>
                  )}
                  {isArchived && (
                    <button onClick={() => reactivate(job)} style={{ padding: '0.4rem 0.8rem', fontSize: '0.82rem', background: 'rgba(133,172,55,0.15)', border: '1px solid var(--secondary)', borderRadius: '6px', cursor: 'pointer', color: 'var(--secondary)' }}>
                      ♻️ Reaktivieren
                    </button>
                  )}
                  <button onClick={() => duplicate(job)} title="Kopieren" style={{ padding: '0.4rem 0.7rem', fontSize: '0.82rem', background: 'rgba(123,140,222,0.12)', border: '1px solid rgba(123,140,222,0.4)', borderRadius: '6px', cursor: 'pointer', color: '#7b8cde' }}>
                    📋
                  </button>
                  <button onClick={() => del(job.id)} title="Löschen" style={{ padding: '0.4rem 0.7rem', fontSize: '0.82rem', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: '6px', cursor: 'pointer', color: '#ef4444' }}>
                    🗑️
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
