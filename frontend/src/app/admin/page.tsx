'use client';
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';

const AdminJobs = dynamic(() => import('../../components/AdminJobs'), { ssr: false });
const AdminJobAlerts = dynamic(() => import('../../components/AdminJobAlerts'), { ssr: false });
const AdminMasterData = dynamic(() => import('../../components/AdminMasterData'), { ssr: false });
const AdminPages = dynamic(() => import('../../components/AdminPages'), { ssr: false });
const AdminSettings = dynamic(() => import('../../components/AdminSettings'), { ssr: false });
const AdminWorkflows = dynamic(() => import('../../components/AdminWorkflows'), { ssr: false });
const AdminApplicants = dynamic(() => import('../../components/AdminApplicants'), { ssr: false });

type View = 'dashboard' | 'applicants' | 'jobs' | 'job-alerts' | 'masterdata' | 'pages' | 'settings' | 'workflows';

export default function AdminDashboard() {
  const [view, setView] = useState<View>('dashboard');
  const [role, setRole] = useState<string>('global_admin');

  useEffect(() => {
    const savedRole = localStorage.getItem('securats_role') || 'global_admin';
    setRole(savedRole);
  }, []);

  const hasAccess = useCallback((v: View) => {
    if (role === 'global_admin') return true;
    if (role === 'content_editor') return ['dashboard', 'pages'].includes(v);
    if (role === 'local_hr') return ['dashboard', 'applicants', 'jobs', 'job-alerts', 'workflows'].includes(v);
    return false;
  }, [role]);

  const nav = (label: string, icon: string, v: View) => (
    <button key={v} onClick={() => setView(v)} style={{
      display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem',
      borderRadius: '8px', border: 'none', width: '100%', textAlign: 'left',
      background: view === v ? 'var(--primary)' : 'transparent',
      color: view === v ? 'white' : 'var(--foreground)',
      cursor: 'pointer', fontSize: '0.95rem', fontWeight: 500, transition: 'all 0.2s',
    }}>
      <span>{icon}</span> {label}
    </button>
  );

  return (
    <main style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside style={{ width: '240px', flexShrink: 0, background: 'var(--card-bg)', borderRight: '1px solid var(--border)', padding: '2rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        <div style={{ padding: '0 0.5rem 1.5rem', borderBottom: '1px solid var(--border)', marginBottom: '0.5rem' }}>
          <p style={{ fontSize: '0.7rem', opacity: 0.5, textTransform: 'uppercase', letterSpacing: '1px' }}>CMS</p>
          <p style={{ fontWeight: 700, color: 'var(--primary)', fontFamily: 'var(--font-outfit)' }}>Admin-Bereich</p>
        </div>
        {nav('Dashboard', '🏠', 'dashboard')}
        {hasAccess('applicants') && nav('Bewerber (Kanban)', '👥', 'applicants')}
        {hasAccess('pages') && nav('Seiten verwalten', '📑', 'pages')}
        {hasAccess('jobs') && nav('Stellenangebote', '💼', 'jobs')}
        {hasAccess('job-alerts') && nav('Job-Alerts & KPIs', '🔔', 'job-alerts')}
        {hasAccess('masterdata') && nav('Standorte & Kategorien', '🏷️', 'masterdata')}
        {hasAccess('workflows') && nav('Prozessflows', '🔄', 'workflows')}
        {hasAccess('settings') && nav('Einstellungen', '⚙️', 'settings')}
        <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
          <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', opacity: 0.6, padding: '0.5rem' }}>← Zur Website</Link>
        </div>
      </aside>

      {/* Main */}
      <div style={{ flex: 1, padding: '2.5rem', overflow: 'auto' }}>

        {/* DASHBOARD */}
        {view === 'dashboard' && (
          <div>
            <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', color: 'var(--primary)' }}>
              Willkommen im CMS ({role === 'global_admin' ? 'Global Admin' : role === 'content_editor' ? 'Redakteur' : 'HR Manager'})
            </h1>
            <p style={{ opacity: 0.7, marginBottom: '2.5rem' }}>Verwalte alle Inhalte der Enterprise Karriereplattform.</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
              {[
                { icon: '👥', title: 'Bewerber (Kanban)', desc: 'Alle Bewerber per Drag & Drop verwalten', v: 'applicants' as View },
                { icon: '📑', title: 'Seiten verwalten', desc: 'Neue Seiten anlegen, bearbeiten, Slug & Navigation setzen', v: 'pages' as View },
                { icon: '💼', title: 'Stellenangebote', desc: 'Jobs anlegen, bearbeiten, löschen', v: 'jobs' as View },
                { icon: '🔔', title: 'Job-Alerts & KPIs', desc: 'Abonnenten verwalten und Statistiken einsehen', v: 'job-alerts' as View },
                { icon: '🏷️', title: 'Standorte & Kategorien', desc: 'Eigene Standorte und Berufsfelder anlegen', v: 'masterdata' as View },
                { icon: '🔄', title: 'Prozessflows', desc: 'Bewerber-Pipelines (Kanban) konfigurieren', v: 'workflows' as View },
                { icon: '⚙️', title: 'Einstellungen', desc: 'Systemstatus und Sicherheit', v: 'settings' as View },
              ].filter(card => hasAccess(card.v)).map(card => (
                <div key={card.v} onClick={() => setView(card.v)} className="glass-panel"
                  style={{ padding: '1.5rem', borderRadius: '12px', cursor: 'pointer', border: '2px solid transparent', transition: 'border-color 0.2s' }}
                  onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--primary)')}
                  onMouseLeave={e => (e.currentTarget.style.borderColor = 'transparent')}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>{card.icon}</div>
                  <h3 style={{ marginBottom: '0.4rem' }}>{card.title}</h3>
                  <p style={{ fontSize: '0.85rem', opacity: 0.7 }}>{card.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}



        {/* BEWERBER – Kanban */}
        {view === 'applicants' && <AdminApplicants />}

        {/* SEITEN – CMS Page Manager */}
        {view === 'pages' && <AdminPages />}

        {/* JOBS – separate Komponente */}
        {view === 'jobs' && <AdminJobs />}

        {/* JOB ALERTS – separate Komponente */}
        {view === 'job-alerts' && <AdminJobAlerts />}

        {/* STAMMDATEN – separate Komponente */}
        {view === 'masterdata' && <AdminMasterData />}

        {/* SETTINGS */}
        {view === 'settings' && <AdminSettings />}

        {/* WORKFLOWS */}
        {view === 'workflows' && <AdminWorkflows />}
      </div>
    </main>
  );
}
