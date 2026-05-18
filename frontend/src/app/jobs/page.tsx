'use client';
import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

interface Job {
  id: string;
  title: string;
  description: string;
  distanceKm?: number | null;
  facility: { name: string };
  location: { id: string; name: string; lat?: number; lng?: number };
  jobFamily: { id: string; name: string };
  workflowState: { name: string };
}
interface Filter { id: string; name: string; archived?: boolean; }

const RADIUS_OPTIONS = [10, 25, 50, 100, 150, 200];

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [locations, setLocations] = useState<Filter[]>([]);
  const [categories, setCategories] = useState<Filter[]>([]);
  const [loading, setLoading] = useState(true);
  const [geocodeMsg, setGeocodeMsg] = useState('');

  // Filter state
  const [q, setQ] = useState('');
  const [locationId, setLocationId] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [searchLocation, setSearchLocation] = useState('');
  const [radiusKm, setRadiusKm] = useState(50);
  const [useRadius, setUseRadius] = useState(false);

  const didMount = useRef(false);

  const loadMeta = async () => {
    const [lr, cr] = await Promise.all([fetch('/api/cms/locations'), fetch('/api/cms/categories')]);
    const [ld, cd] = await Promise.all([lr.json(), cr.json()]);
    // Auf der öffentlichen Seite nur aktive (nicht-archivierte) Filter anzeigen
    setLocations((ld.locations || []).filter((l: Filter) => !l.archived));
    setCategories((cd.categories || []).filter((c: Filter) => !c.archived));
  };

  const search = async (overrides?: Partial<{ q: string; locationId: string; categoryId: string; searchLocation: string; radiusKm: number; useRadius: boolean }>) => {
    setLoading(true);
    setGeocodeMsg('');
    const state = { q, locationId, categoryId, searchLocation, radiusKm, useRadius, ...overrides };
    const params = new URLSearchParams();
    if (state.q) params.set('q', state.q);
    if (state.locationId) params.set('locationId', state.locationId);
    if (state.categoryId) params.set('categoryId', state.categoryId);
    if (state.useRadius && state.searchLocation.trim()) {
      params.set('searchLocation', state.searchLocation.trim());
      params.set('radiusKm', String(state.radiusKm));
    }
    try {
      const res = await fetch(`/api/public/jobs?${params}`);
      const data = await res.json();
      setJobs(data.jobs || []);
      if (data.geocodeResult) {
        setGeocodeMsg(`📍 Umkreis von ${state.radiusKm} km um "${data.geocodeResult.displayName.split(',')[0]}" — ${data.totalFound} Ergebnis${data.totalFound !== 1 ? 'se' : ''}`);
      }
    } catch {
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMeta();
    search();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-search when dropdowns change
  useEffect(() => {
    if (!didMount.current) { didMount.current = true; return; }
    search();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locationId, categoryId]);

  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); search(); };

  const reset = () => {
    setQ(''); setLocationId(''); setCategoryId('');
    setSearchLocation(''); setRadiusKm(50); setUseRadius(false);
    setGeocodeMsg('');
    search({ q: '', locationId: '', categoryId: '', searchLocation: '', useRadius: false });
  };

  const hasFilter = q || locationId || categoryId || (useRadius && searchLocation);

  const inputCls = {
    padding: '0.7rem 1rem', borderRadius: '8px', border: '1px solid var(--border)',
    background: 'var(--background)', color: 'var(--foreground)', fontSize: '0.95rem', width: '100%',
  } as const;

  return (
    <main style={{ minHeight: '100vh', paddingBottom: '5rem' }}>
      {/* Hero Header */}
      <div style={{ backgroundColor: 'var(--primary)', color: 'white', padding: '4rem 1.5rem 6rem', textAlign: 'center' }}>
        <div className="container animate-fade-in opacity-0">
          <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3rem)', marginBottom: '1rem', fontFamily: 'var(--font-outfit)' }}>Stellenangebote</h1>
          <p style={{ fontSize: '1.1rem', opacity: 0.9, maxWidth: '580px', margin: '0 auto' }}>
            Finde deinen Platz beim Landesverein – bodenständig, sinnvoll, norddeutsch.
          </p>
        </div>
      </div>

      <div className="container" style={{ marginTop: '-4rem', position: 'relative', zIndex: 10, padding: '0 1rem' }}>
        {/* ===== SUCHMASKE ===== */}
        <form onSubmit={handleSearch} className="glass-panel animate-fade-in delay-100 opacity-0"
          style={{ padding: '1.5rem 2rem', marginBottom: '2rem', backgroundColor: 'var(--card-bg)', borderRadius: '16px', boxShadow: 'var(--shadow)' }}>

          {/* Zeile 1: Stichwort + Kategorie + Standort */}
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
            <div style={{ flex: '2 1 220px' }}>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, marginBottom: '0.35rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Stichwort</label>
              <input type="text" value={q} onChange={e => setQ(e.target.value)} placeholder="z.B. Pflege, Arzt, IT..." style={inputCls} />
            </div>
            <div style={{ flex: '1 1 160px' }}>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, marginBottom: '0.35rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Berufsfeld</label>
              <select value={categoryId} onChange={e => setCategoryId(e.target.value)} style={inputCls}>
                <option value="">Alle Bereiche</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div style={{ flex: '1 1 160px' }}>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, marginBottom: '0.35rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Standort</label>
              <select value={locationId} onChange={e => setLocationId(e.target.value)} style={inputCls}>
                <option value="">Alle Standorte</option>
                {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
          </div>

          {/* Zeile 2: Umkreissuche */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
              <input type="checkbox" id="useRadius" checked={useRadius} onChange={e => setUseRadius(e.target.checked)} style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--primary)' }} />
              <label htmlFor="useRadius" style={{ fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                📍 Umkreissuche aktivieren
              </label>
            </div>

            <div style={{ flex: '2 1 200px', opacity: useRadius ? 1 : 0.4, transition: 'opacity 0.2s', pointerEvents: useRadius ? 'auto' : 'none' }}>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, marginBottom: '0.35rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Dein Wohnort / PLZ</label>
              <input type="text" value={searchLocation} onChange={e => setSearchLocation(e.target.value)}
                placeholder="z.B. Kiel, 24103 oder Hamburg" style={inputCls} disabled={!useRadius} />
            </div>

            <div style={{ flex: '1 1 200px', opacity: useRadius ? 1 : 0.4, transition: 'opacity 0.2s', pointerEvents: useRadius ? 'auto' : 'none' }}>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, marginBottom: '0.35rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Umkreis: <strong style={{ color: 'var(--primary)' }}>{radiusKm} km</strong>
              </label>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {RADIUS_OPTIONS.map(r => (
                  <button type="button" key={r} onClick={() => setRadiusKm(r)} disabled={!useRadius} style={{
                    padding: '0.35rem 0.7rem', fontSize: '0.82rem', borderRadius: '20px', border: '1px solid var(--border)',
                    cursor: 'pointer', background: radiusKm === r ? 'var(--primary)' : 'transparent',
                    color: radiusKm === r ? 'white' : 'var(--foreground)', fontWeight: radiusKm === r ? 700 : 400, transition: 'all 0.15s',
                  }}>
                    {r} km
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
              <button type="submit" className="btn-primary" style={{ padding: '0.7rem 1.5rem', whiteSpace: 'nowrap' }}>
                🔍 Suchen
              </button>
              {hasFilter && (
                <button type="button" onClick={reset} style={{ padding: '0.7rem 1rem', background: 'transparent', border: '1px solid var(--border)', borderRadius: '8px', cursor: 'pointer', color: 'var(--foreground)', fontSize: '0.9rem' }}>
                  ✕ Reset
                </button>
              )}
            </div>
          </div>
        </form>

        {/* Geocoding Ergebnis-Hinweis */}
        {geocodeMsg && (
          <div style={{ marginBottom: '1.5rem', padding: '0.75rem 1rem', borderRadius: '10px', background: 'rgba(99,37,116,0.08)', border: '1px solid rgba(99,37,116,0.2)', color: 'var(--primary)', fontSize: '0.9rem', fontWeight: 500 }}>
            {geocodeMsg}
          </div>
        )}

        {/* Ergebniszähler */}
        <div style={{ marginBottom: '1rem', opacity: 0.6, fontSize: '0.88rem' }}>
          {loading ? 'Suche läuft...' : `${jobs.length} ${jobs.length === 1 ? 'Stelle' : 'Stellen'} gefunden`}
          {hasFilter && !loading && <span style={{ marginLeft: '0.5rem', color: 'var(--primary)', fontWeight: 600 }}>· Filter aktiv</span>}
        </div>

        {/* Job-Karten */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {!loading && jobs.length === 0 && (
            <div style={{ textAlign: 'center', padding: '4rem 2rem', background: 'var(--card-bg)', borderRadius: '16px', border: '1px dashed var(--border)' }}>
              <p style={{ fontSize: '1.1rem', opacity: 0.7, marginBottom: '1.5rem' }}>
                {useRadius && searchLocation ? `Keine Stellen im Umkreis von ${radiusKm} km um "${searchLocation}" gefunden.` : 'Keine Stellen für diese Suche gefunden.'}
              </p>
              <button onClick={reset} className="btn-primary">Alle Stellen anzeigen</button>
            </div>
          )}

          {jobs.map((job, i) => (
            <div key={job.id}
              className="card animate-fade-in opacity-0"
              style={{ animationDelay: `${i * 60}ms`, display: 'block' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ flex: '1 1 300px', minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {job.jobFamily.name}
                    </span>
                    {job.distanceKm != null && (
                      <span style={{ fontSize: '0.78rem', padding: '0.15rem 0.6rem', borderRadius: '20px', background: 'rgba(99,37,116,0.1)', color: 'var(--primary)', fontWeight: 600 }}>
                        ~ {job.distanceKm} km entfernt
                      </span>
                    )}
                  </div>
                  <h2 style={{ fontSize: 'clamp(1.1rem, 2.5vw, 1.45rem)', margin: '0 0 0.5rem', color: 'var(--foreground)', lineHeight: 1.3 }}>{job.title}</h2>
                  <div style={{ display: 'flex', gap: '1.25rem', opacity: 0.65, fontSize: '0.88rem', flexWrap: 'wrap' }}>
                    <span>📍 {job.location.name}</span>
                    <span>🏢 {job.facility.name}</span>
                  </div>
                  {job.description && (
                    <p style={{ marginTop: '0.6rem', fontSize: '0.88rem', opacity: 0.65, maxWidth: '600px', lineHeight: 1.5 }}>
                      {job.description.slice(0, 130)}{job.description.length > 130 ? '…' : ''}
                    </p>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', alignSelf: 'center', flexShrink: 0, flexWrap: 'wrap' }}>
                  <Link href={`/jobs/${job.id}`} className="btn-secondary" style={{ padding: '0.6rem 1.25rem', fontSize: '0.9rem' }}>
                    Details ansehen
                  </Link>
                  <Link href={`/bewerben?jobId=${job.id}`} className="btn-primary" style={{ padding: '0.6rem 1.25rem', fontSize: '0.9rem' }}>
                    🚀 Direkt bewerben
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
