'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import 'react-quill-new/dist/quill.snow.css';

const ReactQuill = dynamic(() => import('react-quill-new'), { ssr: false, loading: () => <p>Lade Editor...</p> });

type Page = {
  id: string; title: string; slug: string; content: string;
  status: string; navEnabled: boolean; navLabel: string | null;
  navParent: string | null; navOrder: number; metaDesc: string | null;
};
type ImageFile = { name: string; url: string; size: number };

const STATUS_META: Record<string, { label: string; color: string; bg: string }> = {
  published: { label: '✅ Veröffentlicht', color: 'var(--green-dark)', bg: 'rgba(133,172,55,0.12)' },
  draft:     { label: '📝 Entwurf',        color: '#e0932a',           bg: 'rgba(224,147,42,0.12)' },
  archived:  { label: '📦 Archiviert',     color: '#888',              bg: 'rgba(128,128,128,0.1)' },
  system:    { label: '⚙️ System-Seite',   color: '#2563eb',           bg: 'rgba(37,99,235,0.1)' },
};

function slugify(t: string) {
  return t.toLowerCase()
    .replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss')
    .replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
}

export default function AdminPages() {
  const [pages, setPages] = useState<Page[]>([]);
  const [images, setImages] = useState<ImageFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'list'|'edit'|'new'>('list');
  const [editing, setEditing] = useState<Page|null>(null);
  const [showImages, setShowImages] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [form, setForm] = useState({
    title: '', slug: '', content: '', status: 'published',
    navEnabled: true, navLabel: '', navParent: '', navOrder: 0, metaDesc: '',
  });

  const load = useCallback(async () => {
    setLoading(true);
    const [pr, ir] = await Promise.all([fetch('/api/cms/pages'), fetch('/api/cms/images')]);
    const [pd, id] = await Promise.all([pr.json(), ir.json()]);
    setPages(pd.pages || []);
    setImages(id.images || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const openNew = () => {
    setForm({ title:'', slug:'', content:'', status:'published', navEnabled:true, navLabel:'', navParent:'', navOrder: pages.length, metaDesc:'' });
    setMsg(''); setEditing(null); setView('new');
  };

  const openEdit = (p: Page) => {
    setForm({ title:p.title, slug:p.slug, content:p.content, status:p.status, navEnabled:p.navEnabled, navLabel:p.navLabel||'', navParent:p.navParent||'', navOrder:p.navOrder, metaDesc:p.metaDesc||'' });
    setMsg(''); setEditing(p); setView('edit');
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setMsg('');
    const isEdit = view === 'edit' && editing;
    const url = isEdit ? `/api/cms/pages?id=${editing.id}` : '/api/cms/pages';
    const res = await fetch(url, { method: isEdit ? 'PUT' : 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(form) });
    const d = await res.json();
    if (res.ok) { setMsg('✅ Gespeichert!'); await load(); setTimeout(() => setView('list'), 800); }
    else setMsg(`❌ ${d.error}`);
  };

  const archive = async (p: Page) => {
    await fetch(`/api/cms/pages?id=${p.id}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ status: 'archived' }) });
    load();
  };

  const del = async (id: string) => {
    if (!confirm('Seite endgültig löschen?')) return;
    await fetch(`/api/cms/pages?id=${id}`, { method: 'DELETE' });
    load();
  };

  const uploadImage = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    setUploading(true);
    const fd = new FormData(); fd.append('file', file);
    const res = await fetch('/api/cms/images', { method: 'POST', body: fd });
    const d = await res.json();
    if (res.ok) { await load(); setMsg(`✅ Bild hochgeladen: ${d.url}`); }
    else setMsg(`❌ ${d.error}`);
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const deleteImage = async (name: string) => {
    if (!confirm(`Bild "${name}" löschen?`)) return;
    await fetch(`/api/cms/images?name=${encodeURIComponent(name)}`, { method: 'DELETE' });
    load();
  };

  const insertImageToContent = (url: string) => {
    const md = `\n![Bild](${url})\n`;
    setForm(f => ({ ...f, content: f.content + md }));
    setShowImages(false);
    setMsg('🖼️ Bild in Inhalt eingefügt — scrolle im Editor nach unten.');
  };

  const input = { width:'100%', padding:'0.7rem', borderRadius:'8px', border:'1px solid var(--border)', background:'var(--background)', color:'var(--foreground)', fontSize:'0.92rem' } as const;

  const filtered = (filterStatus === 'all' ? pages : pages.filter(p => p.status === filterStatus))
    .filter(p => p.title.toLowerCase().includes(searchQuery.toLowerCase()) || p.slug.toLowerCase().includes(searchQuery.toLowerCase()));
  
  const publishedParents = pages.filter(p => p.status === 'published' && p.navEnabled);

  const getTreeSortedPages = (list: Page[]) => {
    if (searchQuery.trim() !== '') return list.map(p => ({ ...p, level: 0 }));

    const parents = list.filter(p => !p.navParent);
    const children = list.filter(p => p.navParent);
    
    parents.sort((a,b) => a.navOrder - b.navOrder);
    
    const result: (Page & { level: number })[] = [];
    
    const addChildren = (parentSlug: string, level: number) => {
      const myChildren = children.filter(c => c.navParent === parentSlug);
      myChildren.sort((a,b) => a.navOrder - b.navOrder);
      for (const child of myChildren) {
        result.push({ ...child, level });
        addChildren(child.slug, level + 1);
      }
    };
    
    for (const parent of parents) {
      result.push({ ...parent, level: 0 });
      addChildren(parent.slug, 1);
    }
    
    const addedIds = new Set(result.map(r => r.id));
    const orphans = list.filter(p => !addedIds.has(p.id));
    for (const orphan of orphans) {
      result.push({ ...orphan, level: 0 });
    }
    
    return result;
  };

  const treePages = getTreeSortedPages(filtered);

  // ── EDITOR VIEW ──
  if (view !== 'list') return (
    <div style={{ maxWidth: '860px' }}>
      <button type="button" onClick={(e) => { e.preventDefault(); setView('list'); }} style={{ background:'none', border:'none', cursor:'pointer', color:'var(--primary)', marginBottom:'1rem', fontSize:'0.9rem', padding:0 }}>← Zurück zur Seitenübersicht</button>
      <h1 style={{ fontSize:'2rem', color:'var(--primary)', marginBottom:'0.25rem' }}>{view==='edit' ? 'Seite bearbeiten' : 'Neue Seite erstellen'}</h1>
      {editing && <p style={{ fontSize:'0.82rem', opacity:0.5, marginBottom:'1.5rem' }}>ID: {editing.id} · Erstellt: {new Date(editing?.slug).toLocaleDateString?.() || '–'}</p>}

      <form onSubmit={save} style={{ display:'flex', flexDirection:'column', gap:'1.25rem' }}>

        {/* TITEL + SLUG */}
        <div className="glass-panel" style={{ padding:'1.5rem', display:'grid', gridTemplateColumns:'1fr 1fr', gap:'1rem' }}>
          <div>
            <label style={{ display:'block', fontWeight:700, marginBottom:'0.35rem', fontSize:'0.85rem' }}>Seitentitel *</label>
            <input required value={form.title} onChange={e => { const t = e.target.value; setForm(f=>({...f, title:t, slug: view==='new' ? slugify(t) : f.slug})); }} style={input} placeholder="z.B. Über uns" />
          </div>
          <div>
            <label style={{ display:'block', fontWeight:700, marginBottom:'0.35rem', fontSize:'0.85rem' }}>URL-Slug (Adresse) *</label>
            <div style={{ position:'relative' }}>
              <span style={{ position:'absolute', left:'0.7rem', top:'50%', transform:'translateY(-50%)', fontSize:'0.8rem', opacity:0.5 }}>/info/</span>
              <input required value={form.slug} onChange={e => setForm(f=>({...f, slug: slugify(e.target.value)}))} style={{ ...input, paddingLeft:'2.8rem' }} placeholder="ueber-uns" />
            </div>
            <p style={{ fontSize:'0.75rem', opacity:0.5, marginTop:'0.25rem' }}>Nur Kleinbuchstaben und Bindestriche. Wird automatisch generiert.</p>
          </div>
          <div>
            <label style={{ display:'block', fontWeight:700, marginBottom:'0.35rem', fontSize:'0.85rem' }}>Status</label>
            <select value={form.status} onChange={e=>setForm(f=>({...f,status:e.target.value}))} style={input} disabled={form.status === 'system'}>
              <option value="published">✅ Veröffentlicht</option>
              <option value="draft">📝 Entwurf (nicht sichtbar)</option>
              <option value="archived">📦 Archiviert</option>
              {form.status === 'system' && <option value="system">⚙️ System-Seite</option>}
            </select>
          </div>
          <div>
            <label style={{ display:'block', fontWeight:700, marginBottom:'0.35rem', fontSize:'0.85rem' }}>Meta-Beschreibung (SEO)</label>
            <input value={form.metaDesc} onChange={e=>setForm(f=>({...f,metaDesc:e.target.value}))} style={input} placeholder="Kurzbeschreibung für Suchmaschinen..." maxLength={160} />
            <p style={{ fontSize:'0.75rem', opacity:0.5, marginTop:'0.25rem' }}>{form.metaDesc.length}/160 Zeichen</p>
          </div>
        </div>

        {/* NAVIGATION */}
        <div className="glass-panel" style={{ padding:'1.5rem' }}>
          <h3 style={{ marginBottom:'1rem', fontSize:'1.1rem' }}>🧭 Navigation</h3>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:'1rem' }}>
            <div>
              <label style={{ display:'block', fontWeight:700, marginBottom:'0.35rem', fontSize:'0.85rem' }}>In Navigation anzeigen?</label>
              <select value={form.navEnabled ? 'yes' : 'no'} onChange={e=>setForm(f=>({...f, navEnabled: e.target.value==='yes'}))} style={input}>
                <option value="yes">✅ Ja, in Navigation zeigen</option>
                <option value="no">🚫 Nein, ausblenden</option>
              </select>
            </div>
            <div>
              <label style={{ display:'block', fontWeight:700, marginBottom:'0.35rem', fontSize:'0.85rem' }}>Navigationsbezeichnung</label>
              <input value={form.navLabel} onChange={e=>setForm(f=>({...f,navLabel:e.target.value}))} style={input} placeholder={form.title || 'Wie der Seitentitel'} />
              <p style={{ fontSize:'0.75rem', opacity:0.5, marginTop:'0.2rem' }}>Leer = Seitentitel wird verwendet</p>
            </div>
            <div>
              <label style={{ display:'block', fontWeight:700, marginBottom:'0.35rem', fontSize:'0.85rem' }}>Übergeordnete Seite</label>
              <select value={form.navParent} onChange={e=>setForm(f=>({...f,navParent:e.target.value}))} style={input}>
                <option value="">— Hauptmenü (keine Überordnung) —</option>
                {getTreeSortedPages(publishedParents).filter(p=>p.id !== editing?.id).map(p=>(
                  <option key={p.id} value={p.slug}>
                    {'\u00A0\u00A0'.repeat(p.level * 2)}{p.level > 0 ? '↳ ' : ''}{p.navLabel||p.title}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display:'block', fontWeight:700, marginBottom:'0.35rem', fontSize:'0.85rem' }}>Reihenfolge (Position)</label>
              <input type="number" min={0} value={form.navOrder} onChange={e=>setForm(f=>({...f,navOrder:parseInt(e.target.value)||0}))} style={input} />
              <p style={{ fontSize:'0.75rem', opacity:0.5, marginTop:'0.2rem' }}>Niedrigere Zahl = weiter vorne</p>
            </div>
          </div>
        </div>

        {/* BILD-MANAGER */}
        <div className="glass-panel" style={{ padding:'1.5rem' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1rem', flexWrap:'wrap', gap:'0.5rem' }}>
            <h3 style={{ fontSize:'1.1rem' }}>🖼️ Bilder</h3>
            <div style={{ display:'flex', gap:'0.5rem' }}>
              <button type="button" onClick={() => setShowImages(v=>!v)} style={{ padding:'0.4rem 0.9rem', fontSize:'0.85rem', background:'var(--surface-2)', border:'1px solid var(--border)', borderRadius:'6px', cursor:'pointer' }}>
                {showImages ? 'Bibliothek ausblenden' : `Bibliothek anzeigen (${images.length})`}
              </button>
              <input ref={fileInputRef} type="file" accept="image/*" style={{ display:'none' }} onChange={uploadImage} />
              <button type="button" onClick={() => fileInputRef.current?.click()} disabled={uploading} style={{ padding:'0.4rem 0.9rem', fontSize:'0.85rem', background:'var(--primary)', color:'white', border:'none', borderRadius:'6px', cursor:'pointer' }}>
                {uploading ? 'Lädt...' : '⬆️ Bild hochladen'}
              </button>
            </div>
          </div>
          {showImages && (
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(120px, 1fr))', gap:'0.75rem' }}>
              {images.length === 0 && <p style={{ opacity:0.5, fontSize:'0.85rem', gridColumn:'1/-1' }}>Noch keine Bilder hochgeladen.</p>}
              {images.map(img => (
                <div key={img.name} style={{ position:'relative', borderRadius:'8px', overflow:'hidden', border:'2px solid var(--border)', background:'var(--surface-2)', cursor:'pointer' }} onClick={() => insertImageToContent(img.url)} title="Klicken = in Inhalt einfügen">
                  <img src={img.url} alt={img.name} style={{ width:'100%', aspectRatio:'1', objectFit:'cover', display:'block' }} />
                  <div style={{ padding:'0.3rem 0.4rem', fontSize:'0.65rem', opacity:0.6, overflow:'hidden', whiteSpace:'nowrap', textOverflow:'ellipsis' }}>{img.name}</div>
                  <button type="button" onClick={ev => { ev.stopPropagation(); deleteImage(img.name); }} style={{ position:'absolute', top:'3px', right:'3px', background:'rgba(239,68,68,0.85)', border:'none', borderRadius:'4px', color:'white', fontSize:'0.7rem', cursor:'pointer', padding:'1px 5px', lineHeight:'1.4' }}>✕</button>
                </div>
              ))}
            </div>
          )}
          <p style={{ fontSize:'0.78rem', opacity:0.5, marginTop:'0.75rem' }}>💡 Klicke auf ein Bild um es in den Inhalt einzufügen. Füge es manuell ein mit: <code>![Alt-Text](/uploads/dateiname.jpg)</code></p>
        </div>

        {/* INHALT-EDITOR */}
        <div className="glass-panel" style={{ padding:'1.5rem' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'0.75rem' }}>
            <h3 style={{ fontSize:'1.1rem' }}>📄 Seiteninhalt</h3>
            {editing && <a href={`/info/${editing.slug}`} target="_blank" rel="noreferrer" style={{ fontSize:'0.85rem', color:'var(--primary)' }}>Vorschau →</a>}
          </div>
          <div style={{ background: 'white', color: 'black', borderRadius: '8px', overflow: 'hidden' }}>
            <ReactQuill 
              theme="snow" 
              value={form.content} 
              onChange={val => setForm(f=>({...f, content: val}))} 
              style={{ minHeight: '400px' }}
              modules={{
                toolbar: [
                  [{ 'header': [1, 2, 3, false] }],
                  ['bold', 'italic', 'underline', 'strike'],
                  [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                  ['link', 'image', 'clean']
                ]
              }}
            />
          </div>
        </div>

        {msg && <p style={{ padding:'0.75rem', borderRadius:'8px', background: msg.startsWith('✅')||msg.startsWith('🖼️') ? 'rgba(133,172,55,0.12)' : 'rgba(239,68,68,0.1)', color: msg.startsWith('✅')||msg.startsWith('🖼️') ? 'var(--green-dark)' : '#ef4444' }}>{msg}</p>}
        <button type="submit" className="btn-primary" style={{ padding:'0.9rem', fontSize:'1.05rem' }}>💾 Seite speichern</button>
      </form>
    </div>
  );

  // ── LIST VIEW ──
  const tabs = [
    { key:'all', label:`Alle (${pages.length})` },
    { key:'published', label:`Aktiv (${pages.filter(p=>p.status==='published').length})` },
    { key:'system', label:`System (${pages.filter(p=>p.status==='system').length})` },
    { key:'draft', label:`Entwürfe (${pages.filter(p=>p.status==='draft').length})` },
    { key:'archived', label:`Archiv (${pages.filter(p=>p.status==='archived').length})` },
  ];

  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1.5rem', flexWrap:'wrap', gap:'1rem' }}>
        <div>
          <h1 style={{ fontSize:'2rem', color:'var(--primary)' }}>Seitenmanager</h1>
          <p style={{ opacity:0.7 }}>{pages.length} Seiten verwaltet · Vollständiges CMS</p>
        </div>
        <div style={{ display:'flex', gap:'1rem', alignItems:'center', flexWrap:'wrap' }}>
          <input 
            type="text" 
            placeholder="🔍 Seiten durchsuchen..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ padding:'0.7rem 1rem', borderRadius:'8px', border:'1px solid var(--border)', background:'var(--surface)', minWidth:'250px' }}
          />
          <button className="btn-primary" onClick={openNew}>➕ Neue Seite erstellen</button>
        </div>
      </div>

      {/* Status Tabs */}
      <div style={{ display:'flex', gap:'0.25rem', marginBottom:'1.5rem', borderBottom:'1px solid var(--border)' }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setFilterStatus(t.key)} style={{ padding:'0.5rem 1rem', fontSize:'0.85rem', border:'none', cursor:'pointer', background:'transparent', fontWeight: filterStatus===t.key ? 700 : 400, color: filterStatus===t.key ? 'var(--primary)' : 'var(--foreground)', borderBottom: filterStatus===t.key ? '2px solid var(--primary)' : '2px solid transparent', opacity: filterStatus===t.key ? 1 : 0.6 }}>{t.label}</button>
        ))}
      </div>

      {loading ? <p style={{ textAlign:'center', padding:'3rem', opacity:0.6 }}>Lädt...</p> : (
        <div style={{ display:'flex', flexDirection:'column', gap:'0.6rem' }}>
          {treePages.length === 0 && <div style={{ textAlign:'center', padding:'3rem', opacity:0.6, border:'1px dashed var(--border)', borderRadius:'12px' }}>Keine Seiten gefunden.</div>}
          {treePages.map(page => {
            const st = STATUS_META[page.status] || STATUS_META.draft;
            const isTree = searchQuery.trim() === '';
            const indent = isTree ? page.level * 2 : 0;
            return (
              <div key={page.id} className="glass-panel" style={{ position:'relative', padding:`1rem 1.5rem 1rem ${1.5 + indent}rem`, marginLeft: indent > 0 ? '1rem' : '0', borderLeft: indent > 0 ? '4px solid var(--border)' : '1px solid var(--glass-border)', borderRadius:'10px', display:'flex', alignItems:'center', justifyContent:'space-between', gap:'1rem', flexWrap:'wrap', opacity: page.status==='archived' ? 0.7 : 1 }}>
                {isTree && page.level > 0 && <span style={{position:'absolute', left:'-0.6rem', top:'50%', transform:'translateY(-50%)', opacity:0.4, fontSize:'1.2rem', color:'var(--primary)'}}>↳</span>}
                <div style={{ minWidth:0 }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'0.75rem', flexWrap:'wrap', marginBottom:'0.2rem' }}>
                    <p style={{ fontWeight:700 }}>{page.title}</p>
                    <span style={{ fontSize:'0.72rem', padding:'0.15rem 0.55rem', borderRadius:'20px', background:st.bg, color:st.color, whiteSpace:'nowrap' }}>{st.label}</span>
                    {page.navEnabled && page.status==='published' && (
                      <span style={{ fontSize:'0.72rem', opacity:0.6 }}>🧭 {page.navParent ? `↳ unter ${page.navParent}` : 'Hauptmenü'} (Pos. {page.navOrder})</span>
                    )}
                    {page.status === 'system' && (
                      <span style={{ fontSize:'0.72rem', opacity:0.8, color: 'var(--blue)' }}>⚠️ Code-basiertes Layout</span>
                    )}
                  </div>
                  <p style={{ fontSize:'0.78rem', opacity:0.5, fontFamily:'monospace' }}>/info/{page.slug}</p>
                </div>
                <div style={{ display:'flex', gap:'0.4rem', flexShrink:0, flexWrap:'wrap' }}>
                  <button onClick={() => openEdit(page)} style={{ padding:'0.4rem 0.8rem', fontSize:'0.82rem', background:'var(--primary)', color:'white', border:'none', borderRadius:'6px', cursor:'pointer' }}>✏️ Bearbeiten</button>
                  {page.status !== 'archived' && <a href={page.slug === 'home' ? '/' : `/info/${page.slug}`} target="_blank" rel="noreferrer" style={{ padding:'0.4rem 0.7rem', fontSize:'0.82rem', background:'transparent', border:'1px solid var(--border)', borderRadius:'6px', cursor:'pointer', color:'var(--foreground)', display:'inline-flex', alignItems:'center', textDecoration:'none' }}>👁️ Ansehen</a>}
                  {page.status !== 'archived' && <button onClick={() => archive(page)} style={{ padding:'0.4rem 0.7rem', fontSize:'0.82rem', background:'rgba(128,128,128,0.08)', border:'1px solid rgba(128,128,128,0.25)', borderRadius:'6px', cursor:'pointer', color:'#888' }}>📦 Archivieren</button>}
                  {page.status === 'archived' && <button onClick={() => { openEdit(page); }} style={{ padding:'0.4rem 0.7rem', fontSize:'0.82rem', background:'rgba(133,172,55,0.1)', border:'1px solid var(--green)', borderRadius:'6px', cursor:'pointer', color:'var(--green-dark)' }}>♻️ Reaktivieren</button>}
                  <button onClick={() => del(page.id)} title="Endgültig löschen" style={{ padding:'0.4rem 0.6rem', fontSize:'0.82rem', background:'rgba(239,68,68,0.08)', border:'1px solid rgba(239,68,68,0.2)', borderRadius:'6px', cursor:'pointer', color:'#ef4444' }}>🗑️</button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
