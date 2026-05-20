'use client';
import { useState, useEffect } from 'react';

export default function AdminAnalytics() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await fetch('/api/cms/analytics');
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p>Lade Statistiken...</p>;
  if (!data || data.error || !data.metrics) return <p>Fehler beim Laden der Daten: {data?.error || 'Unbekannt'}</p>;

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', color: 'var(--primary)', marginBottom: '0.5rem' }}>Analytics & Reporting</h1>
        <p style={{ opacity: 0.7 }}>Erkenne Engpässe und miss den Erfolg deiner Recruiting-Kanäle in Echtzeit.</p>
      </div>

      {/* Top Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', borderLeft: '4px solid #3b82f6' }}>
          <p style={{ fontSize: '0.9rem', opacity: 0.7, marginBottom: '0.5rem' }}>Aktive Stellenangebote</p>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>{data.metrics.totalJobs}</div>
        </div>
        
        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', borderLeft: '4px solid #10b981' }}>
          <p style={{ fontSize: '0.9rem', opacity: 0.7, marginBottom: '0.5rem' }}>Eingegangene Bewerbungen</p>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>{data.metrics.totalApplications}</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', borderLeft: '4px solid #8b5cf6' }}>
          <p style={{ fontSize: '0.9rem', opacity: 0.7, marginBottom: '0.5rem' }}>Ø Conversion Rate (Views zu Bewerbung)</p>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>{data.metrics.conversionRate}%</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem' }}>
        
        {/* Bottleneck Analysis */}
        <div className="glass-panel" style={{ padding: '2rem', borderRadius: '12px' }}>
          <h3 style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>⚠️</span> Engpass-Analyse (Bottlenecks)
          </h3>
          <p style={{ fontSize: '0.85rem', opacity: 0.7, marginBottom: '1.5rem' }}>
            In diesen Workflow-Schritten stauen sich aktuell die meisten Bewerber.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {data.bottlenecks.map((b: any, i: number) => {
              const max = data.bottlenecks[0].count;
              const percent = (b.count / max) * 100;
              return (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '0.3rem' }}>
                    <span style={{ fontWeight: 'bold' }}>{b.step}</span>
                    <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>{b.count} Kandidaten</span>
                  </div>
                  <div style={{ height: '8px', background: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${percent}%`, background: i === 0 ? '#ef4444' : 'var(--primary)', borderRadius: '4px' }}></div>
                  </div>
                </div>
              );
            })}
            {data.bottlenecks.length === 0 && <p style={{ opacity: 0.5 }}>Keine Daten verfügbar.</p>}
          </div>
        </div>

        {/* Top Locations */}
        <div className="glass-panel" style={{ padding: '2rem', borderRadius: '12px' }}>
          <h3 style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>📍</span> Top Standorte (Nach Bewerbungen)
          </h3>
          <p style={{ fontSize: '0.85rem', opacity: 0.7, marginBottom: '1.5rem' }}>
            Diese Einrichtungen generieren die meisten Kandidaten.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {data.topFacilities.map((f: any, i: number) => {
              const max = data.topFacilities[0].count;
              const percent = (f.count / max) * 100;
              return (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '0.3rem' }}>
                    <span style={{ fontWeight: 'bold' }}>{f.name}</span>
                    <span style={{ color: '#10b981', fontWeight: 'bold' }}>{f.count} Bewerber</span>
                  </div>
                  <div style={{ height: '8px', background: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${percent}%`, background: '#10b981', borderRadius: '4px' }}></div>
                  </div>
                </div>
              );
            })}
            {data.topFacilities.length === 0 && <p style={{ opacity: 0.5 }}>Keine Daten verfügbar.</p>}
          </div>
        </div>

      </div>
    </div>
  );
}
