'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [role, setRole] = useState('global_admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, password })
      });

      if (res.ok) {
        // Für das Frontend UI auch im localStorage speichern (RBAC Ansicht)
        localStorage.setItem('securats_role', role);
        router.push('/admin');
      } else {
        const data = await res.json();
        setError(data.error || 'Falsches Passwort.');
      }
    } catch (err) {
      setError('Verbindungsfehler.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div className="glass-panel animate-fade-in opacity-0" style={{ padding: '3rem', borderRadius: '16px', maxWidth: '400px', width: '100%', boxShadow: 'var(--shadow)' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', textAlign: 'center', color: 'var(--primary)' }}>CMS Login</h1>
        <p style={{ textAlign: 'center', opacity: 0.8, marginBottom: '2rem' }}>RBAC Demo-Modus</p>
        
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Rolle simulieren</label>
            <select 
              value={role} 
              onChange={(e) => setRole(e.target.value)}
              style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' }}
            >
              <option value="global_admin">Globaler Administrator (Vollzugriff)</option>
              <option value="content_editor">Redakteur (Nur CMS / Seiten)</option>
              <option value="local_hr">Lokaler HR-Manager (Nur Jobs & Alerts)</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>E-Mail Adresse (Optional)</label>
            <input type="email" placeholder="name@Enterprise.local" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Passwort (Demo-Schutz)</label>
            <input 
              type="password" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' }} 
            />
          </div>

          {error && (
            <div style={{ padding: '0.75rem', borderRadius: '8px', background: '#ffebee', color: '#c62828', fontSize: '0.9rem', border: '1px solid #ef9a9a' }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary" style={{ width: '100%', marginTop: '0.5rem', textAlign: 'center', opacity: loading ? 0.7 : 1 }}>
            {loading ? 'Wird angemeldet...' : `Als ${role.replace('_', ' ')} anmelden`}
          </button>
        </form>
        
        <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.9rem', opacity: 0.7 }}>
          <p>Interner Bereich. Zugriff nur für berechtigte Personen gemäß RBAC.</p>
        </div>
      </div>
    </main>
  );
}
