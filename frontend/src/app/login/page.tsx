'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const [role, setRole] = useState('global_admin');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // RBAC Mock: Rolle im localStorage speichern
    localStorage.setItem('securats_role', role);
    router.push('/admin');
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
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Passwort (Optional)</label>
            <input type="password" placeholder="••••••••" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' }} />
          </div>
          <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '1rem', textAlign: 'center' }}>
            Als {role.replace('_', ' ')} anmelden
          </button>
        </form>
        
        <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.9rem', opacity: 0.7 }}>
          <p>Interner Bereich. Zugriff nur für berechtigte Personen gemäß RBAC.</p>
        </div>
      </div>
    </main>
  );
}
