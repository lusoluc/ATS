'use client';

import { useState, useEffect } from 'react';

export default function JobAlertPage() {
  const [options, setOptions] = useState<{ categories: any[]; locations: any[] }>({ categories: [], locations: [] });
  const [loadingOptions, setLoadingOptions] = useState(true);

  const [email, setEmail] = useState('');
  const [globalAlert, setGlobalAlert] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetch('/api/public/job-alerts/options')
      .then(res => res.json())
      .then(data => {
        setOptions({
          categories: data.categories || [],
          locations: data.locations || []
        });
        setLoadingOptions(false);
      })
      .catch(err => {
        console.error(err);
        setLoadingOptions(false);
      });
  }, []);

  const handleCategoryChange = (id: string) => {
    setSelectedCategories(prev => 
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const handleLocationChange = (id: string) => {
    setSelectedLocations(prev => 
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage(null);

    try {
      const res = await fetch('/api/public/job-alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          globalAlert,
          categories: selectedCategories,
          locations: selectedLocations
        })
      });

      const data = await res.json();

      if (res.ok) {
        setMessage({ type: 'success', text: data.message });
      } else {
        setMessage({ type: 'error', text: data.error || 'Es ist ein Fehler aufgetreten.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Netzwerkfehler. Bitte versuchen Sie es später erneut.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container" style={{ marginTop: '100px', marginBottom: '100px' }}>
      <div className="glass-panel" style={{ maxWidth: '600px', margin: '0 auto', padding: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: 'var(--brand)' }}>Job-Alert aktivieren</h1>
        <p style={{ marginBottom: '2rem', color: '#555' }}>
          Verpassen Sie keine neuen Stellenangebote mehr! Abonnieren Sie unseren Job-Alert und erhalten Sie passende Jobs direkt in Ihr Postfach.
        </p>

        {message && (
          <div style={{
            padding: '1rem', 
            marginBottom: '1.5rem', 
            borderRadius: '6px', 
            backgroundColor: message.type === 'success' ? '#dcfce7' : '#fee2e2',
            color: message.type === 'success' ? '#166534' : '#991b1b',
            border: `1px solid ${message.type === 'success' ? '#bbf7d0' : '#fecaca'}`
          }}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem' }}>E-Mail-Adresse *</label>
            <input 
              type="email" 
              required 
              value={email} 
              onChange={e => setEmail(e.target.value)}
              placeholder="ihre.email@beispiel.de"
              style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #ccc' }}
            />
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #eee' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontWeight: 'bold' }}>
              <input 
                type="checkbox" 
                checked={globalAlert} 
                onChange={e => setGlobalAlert(e.target.checked)} 
                style={{ width: '18px', height: '18px' }}
              />
              Alle neuen Stellenangebote erhalten (Keine Filter)
            </label>
          </div>

          {!globalAlert && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1rem', border: '1px solid #eee', borderRadius: '6px' }}>
              <h3 style={{ fontSize: '1.2rem', margin: 0 }}>Filterkriterien</h3>
              
              {loadingOptions ? (
                <p>Lade Optionen...</p>
              ) : (
                <>
                  <div>
                    <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem' }}>Berufsfelder</label>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                      {options.categories.map(cat => (
                        <label key={cat.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
                          <input 
                            type="checkbox" 
                            checked={selectedCategories.includes(cat.id)}
                            onChange={() => handleCategoryChange(cat.id)}
                          />
                          {cat.name}
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '0.5rem' }}>Standorte</label>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                      {options.locations.map(loc => (
                        <label key={loc.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
                          <input 
                            type="checkbox" 
                            checked={selectedLocations.includes(loc.id)}
                            onChange={() => handleLocationChange(loc.id)}
                          />
                          {loc.city || loc.name}
                        </label>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          <button 
            type="submit" 
            disabled={isSubmitting || loadingOptions}
            className="btn-primary" 
            style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', marginTop: '1rem' }}
          >
            {isSubmitting ? 'Wird gespeichert...' : 'Job-Alert aktivieren / aktualisieren'}
          </button>
          
          <p style={{ fontSize: '0.8rem', color: '#666', textAlign: 'center', marginTop: '0.5rem' }}>
            Sie erhalten nach Klick auf den Button eine E-Mail mit einem Bestätigungslink (Double Opt-In).
            Durch die Anmeldung stimmen Sie unserer Datenschutzerklärung zu.
          </p>

        </form>
      </div>
    </div>
  );
}
