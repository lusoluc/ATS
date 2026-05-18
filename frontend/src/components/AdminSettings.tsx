'use client';
import { useState, useEffect } from 'react';

export default function AdminSettings() {
  const [settings, setSettings] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saveMsg, setSaveMsg] = useState('');
  const [pingStatus, setPingStatus] = useState<{ loading: boolean; success?: boolean; message?: string }>({ loading: false });

  const [activeTab, setActiveTab] = useState<'settings' | 'templates' | 'delegations' | 'interfaces' | 'sap'>('settings');

  const [delegations, setDelegations] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [newDelegation, setNewDelegation] = useState({ delegatorId: '', delegateeId: '', scopeType: 'FACILITY', scopeId: '', validFrom: '', validUntil: '' });

  const [editSetting, setEditSetting] = useState<any>(null);
  const [editTemplate, setEditTemplate] = useState<any>(null);

  const logAudit = async (action: string, metadata: any = {}) => {
    try {
      const isDevMode = settings.find(s => s.key === 'dev_mode')?.value === 'true';
      
      // Performance-Messung in Dev-Mode aktivieren
      const perfMetrics = isDevMode ? {
        memory: (performance as any).memory?.usedJSHeapSize,
        timeSinceLoad: performance.now()
      } : undefined;

      await fetch('/api/cms/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          action, 
          metadata: { ...metadata, ...(perfMetrics && { dev_metrics: perfMetrics }) } 
        })
      });
    } catch (e) {
      console.warn('Failed to log audit event', e);
    }
  };

  const handleTabChange = (tab: any) => {
    setActiveTab(tab);
    logAudit('ADMIN_TAB_CLICKED', { tab });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/cms/settings');
      const data = await res.json();
      setSettings(data.settings || []);
      setTemplates(data.templates || []);

      const delRes = await fetch('/api/cms/delegations');
      const delData = await delRes.json();
      setDelegations(delData.delegations || []);
      setUsers(delData.users || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const saveSetting = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveMsg('Speichert...');
    try {
      const res = await fetch('/api/cms/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'setting', data: editSetting })
      });
      if (res.ok) {
        setSaveMsg('Erfolgreich gespeichert!');
        setEditSetting(null);
        fetchData();
      } else {
        setSaveMsg('Fehler beim Speichern');
      }
    } catch {
      setSaveMsg('Fehler beim Speichern');
    }
  };

  const saveTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveMsg('Speichert...');
    try {
      const res = await fetch('/api/cms/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'template', data: editTemplate })
      });
      if (res.ok) {
        setSaveMsg('Erfolgreich gespeichert!');
        setEditTemplate(null);
        fetchData();
      } else {
        setSaveMsg('Fehler beim Speichern');
      }
    } catch {
      setSaveMsg('Fehler beim Speichern');
    }
  };

  const createDelegation = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveMsg('Speichert Delegation...');
    try {
      const res = await fetch('/api/cms/delegations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newDelegation)
      });
      if (res.ok) {
        setSaveMsg('Urlaubsvertretung erfolgreich angelegt!');
        setNewDelegation({ delegatorId: '', delegateeId: '', scopeType: 'FACILITY', scopeId: '', validFrom: '', validUntil: '' });
        fetchData();
      } else {
        const d = await res.json();
        setSaveMsg(`Fehler: ${d.error}`);
      }
    } catch {
      setSaveMsg('Fehler beim Speichern');
    }
  };

  const revokeDelegation = async (id: string) => {
    if (!window.confirm('Vertretung wirklich sofort beenden?')) return;
    try {
      const res = await fetch(`/api/cms/delegations?id=${id}`, { method: 'DELETE' });
      if (res.ok) {
        setSaveMsg('Vertretung beendet.');
        fetchData();
      }
    } catch {}
  };

  const testSAPPing = async () => {
    setPingStatus({ loading: true });
    try {
      const baseUrl = settings.find(s => s.key === 'sap_base_url')?.value;
      const clientId = settings.find(s => s.key === 'sap_client_id')?.value;
      const clientSecret = settings.find(s => s.key === 'sap_client_secret')?.value;
      const companyId = settings.find(s => s.key === 'sap_company_id')?.value;

      const res = await fetch('/api/cms/sap/ping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ baseUrl, clientId, clientSecret, companyId })
      });
      const data = await res.json();
      setPingStatus({ loading: false, success: data.success, message: data.success ? data.message : data.error });
      logAudit('SAP_PING_TEST', { success: data.success, error: data.error });
    } catch (err: any) {
      setPingStatus({ loading: false, success: false, message: 'Netzwerkfehler beim Ping' });
      logAudit('SAP_PING_ERROR', { error: err?.message || 'Network Error' });
    }
  };

  const inputStyle = { width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' };

  if (loading) return <p>Lade Einstellungen...</p>;

  const isDevMode = settings.find(s => s.key === 'dev_mode')?.value === 'true';

  const toggleDevMode = async () => {
    const newValue = isDevMode ? 'false' : 'true';
    try {
      await fetch('/api/cms/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'dev_mode', value: newValue })
      });
      fetchData(); // Reload settings
      logAudit('DEV_MODE_TOGGLED', { enabled: newValue === 'true' });
    } catch (err) {}
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '2rem', color: 'var(--primary)' }}>Globale Einstellungen & E-Mail Vorlagen</h1>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', background: isDevMode ? 'var(--primary)' : 'var(--background)', color: isDevMode ? 'white' : 'var(--foreground)', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--border)', fontWeight: 'bold' }}>
          <input 
            type="checkbox" 
            checked={isDevMode} 
            onChange={toggleDevMode} 
            style={{ display: 'none' }} 
          />
          {isDevMode ? '🟢 Developer Mode ON (KI & Perf. Tracking)' : '⚪ Developer Mode OFF'}
        </label>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button 
          onClick={() => handleTabChange('settings')}
          className={activeTab === 'settings' ? 'btn-primary' : ''}
          style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', cursor: 'pointer', border: '1px solid var(--border)', background: activeTab === 'settings' ? '' : 'transparent' }}
        >
          Allgemeine Daten
        </button>
        <button 
          onClick={() => handleTabChange('templates')}
          className={activeTab === 'templates' ? 'btn-primary' : ''}
          style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', cursor: 'pointer', border: '1px solid var(--border)', background: activeTab === 'templates' ? '' : 'transparent' }}
        >
          E-Mail Templates (Job-Alert)
        </button>
        <button 
          onClick={() => handleTabChange('delegations')}
          className={activeTab === 'delegations' ? 'btn-primary' : ''}
          style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', cursor: 'pointer', border: '1px solid var(--border)', background: activeTab === 'delegations' ? '' : 'transparent' }}
        >
          🏖️ Urlaubsvertretungen
        </button>
        <button 
          onClick={() => handleTabChange('interfaces')}
          className={activeTab === 'interfaces' ? 'btn-primary' : ''}
          style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', cursor: 'pointer', border: '1px solid var(--border)', background: activeTab === 'interfaces' ? '' : 'transparent' }}
        >
          🔌 Schnittstellen (BA)
        </button>
        <button 
          onClick={() => handleTabChange('sap')}
          className={activeTab === 'sap' ? 'btn-primary' : ''}
          style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', cursor: 'pointer', border: '1px solid var(--border)', background: activeTab === 'sap' ? '' : 'transparent' }}
        >
          ☁️ SAP SuccessFactors
        </button>
      </div>

      {saveMsg && <p style={{ marginBottom: '1rem', color: saveMsg.includes('Fehler') ? 'red' : 'green' }}>{saveMsg}</p>}

      {activeTab === 'settings' && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {editSetting ? (
            <form onSubmit={saveSetting} className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
              <h3 style={{ marginBottom: '1rem' }}>Einstellung bearbeiten</h3>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Schlüssel</label>
              <input value={editSetting.key} disabled style={{ ...inputStyle, opacity: 0.5, marginBottom: '1rem' }} />
              
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Wert (Text oder JSON)</label>
              <textarea 
                value={editSetting.value} 
                onChange={(e) => setEditSetting({ ...editSetting, value: e.target.value })} 
                style={{ ...inputStyle, height: '150px', marginBottom: '1rem', fontFamily: 'monospace' }} 
              />
              
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="submit" className="btn-primary" style={{ padding: '0.5rem 1rem' }}>Speichern</button>
                <button type="button" onClick={() => setEditSetting(null)} style={{ padding: '0.5rem 1rem' }}>Abbrechen</button>
              </div>
            </form>
          ) : (
            <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th style={{ padding: '0.75rem' }}>Schlüssel</th>
                    <th style={{ padding: '0.75rem' }}>Wert</th>
                    <th style={{ padding: '0.75rem' }}>Aktion</th>
                  </tr>
                </thead>
                <tbody>
                  {settings.map(s => (
                    <tr key={s.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>{s.key}</td>
                      <td style={{ padding: '0.75rem' }}><pre style={{ maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.value}</pre></td>
                      <td style={{ padding: '0.75rem' }}>
                        <button onClick={() => setEditSetting(s)} style={{ padding: '0.25rem 0.75rem', cursor: 'pointer' }}>Bearbeiten</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button 
                onClick={() => setEditSetting({ key: 'neuer_key', value: '' })}
                className="btn-primary" 
                style={{ marginTop: '1.5rem', padding: '0.5rem 1rem' }}
              >
                + Neue Einstellung
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'templates' && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {editTemplate ? (
            <form onSubmit={saveTemplate} className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
              <h3 style={{ marginBottom: '1rem' }}>Template bearbeiten</h3>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Name (Key)</label>
              <input value={editTemplate.name} disabled={!!editTemplate.id} onChange={(e) => setEditTemplate({ ...editTemplate, name: e.target.value })} style={{ ...inputStyle, marginBottom: '1rem' }} />
              
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Betreff (Subject)</label>
              <input value={editTemplate.subject} onChange={(e) => setEditTemplate({ ...editTemplate, subject: e.target.value })} style={{ ...inputStyle, marginBottom: '1rem' }} />

              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>HTML Inhalt</label>
              <textarea 
                value={editTemplate.htmlContent} 
                onChange={(e) => setEditTemplate({ ...editTemplate, htmlContent: e.target.value })} 
                style={{ ...inputStyle, height: '250px', marginBottom: '1rem', fontFamily: 'monospace' }} 
              />

              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Text Inhalt (Fallback)</label>
              <textarea 
                value={editTemplate.textContent || ''} 
                onChange={(e) => setEditTemplate({ ...editTemplate, textContent: e.target.value })} 
                style={{ ...inputStyle, height: '100px', marginBottom: '1rem', fontFamily: 'monospace' }} 
              />
              
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="submit" className="btn-primary" style={{ padding: '0.5rem 1rem' }}>Speichern</button>
                <button type="button" onClick={() => setEditTemplate(null)} style={{ padding: '0.5rem 1rem' }}>Abbrechen</button>
              </div>
            </form>
          ) : (
            <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th style={{ padding: '0.75rem' }}>Template Name</th>
                    <th style={{ padding: '0.75rem' }}>Betreff</th>
                    <th style={{ padding: '0.75rem' }}>Aktion</th>
                  </tr>
                </thead>
                <tbody>
                  {templates.map(t => (
                    <tr key={t.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>{t.name}</td>
                      <td style={{ padding: '0.75rem' }}>{t.subject}</td>
                      <td style={{ padding: '0.75rem' }}>
                        <button onClick={() => setEditTemplate(t)} style={{ padding: '0.25rem 0.75rem', cursor: 'pointer' }}>Bearbeiten</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button 
                onClick={() => setEditTemplate({ name: '', subject: '', htmlContent: '', textContent: '' })}
                className="btn-primary" 
                style={{ marginTop: '1.5rem', padding: '0.5rem 1rem' }}
              >
                + Neues Template
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'delegations' && (
        <div style={{ display: 'grid', gap: '2rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ marginBottom: '1.5rem' }}>Aktive & Geplante Vertretungen</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '0.75rem' }}>Von (Urlauber)</th>
                  <th style={{ padding: '0.75rem' }}>An (Vertretung)</th>
                  <th style={{ padding: '0.75rem' }}>Bereich</th>
                  <th style={{ padding: '0.75rem' }}>Zeitraum</th>
                  <th style={{ padding: '0.75rem' }}>Aktion</th>
                </tr>
              </thead>
              <tbody>
                {delegations.map(d => {
                  const isActive = new Date(d.validFrom) <= new Date() && new Date(d.validUntil) >= new Date();
                  return (
                    <tr key={d.id} style={{ borderBottom: '1px solid var(--border)', background: isActive ? 'rgba(16, 185, 129, 0.05)' : '' }}>
                      <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>{d.delegator.email}</td>
                      <td style={{ padding: '0.75rem' }}>{d.delegatee.email}</td>
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem', background: 'var(--border)', borderRadius: '4px' }}>
                          {d.scopeType} {d.scopeId ? `(${d.scopeId})` : ''}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        {new Date(d.validFrom).toLocaleDateString()} - {new Date(d.validUntil).toLocaleDateString()}
                        {isActive && <span style={{ marginLeft: '0.5rem', color: '#10b981', fontSize: '0.8rem', fontWeight: 'bold' }}>Aktiv</span>}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <button onClick={() => revokeDelegation(d.id)} style={{ color: 'red', border: 'none', background: 'none', cursor: 'pointer' }}>Beenden</button>
                      </td>
                    </tr>
                  );
                })}
                {delegations.length === 0 && <tr><td colSpan={5} style={{ padding: '1rem', opacity: 0.6 }}>Keine Vertretungen aktiv.</td></tr>}
              </tbody>
            </table>
          </div>

          <form onSubmit={createDelegation} className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--primary)' }}>
            <h3 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>+ Neue Urlaubsvertretung einrichten</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Wer geht in den Urlaub? (Delegator)</label>
                <select required value={newDelegation.delegatorId} onChange={e => setNewDelegation({...newDelegation, delegatorId: e.target.value})} style={inputStyle}>
                  <option value="">-- Bitte wählen --</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.email} ({u.role})</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Wer übernimmt? (Vertretung)</label>
                <select required value={newDelegation.delegateeId} onChange={e => setNewDelegation({...newDelegation, delegateeId: e.target.value})} style={inputStyle}>
                  <option value="">-- Bitte wählen --</option>
                  {users.map(u => <option key={u.id} value={u.id}>{u.email} ({u.role})</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Welche Rechte werden übergeben?</label>
                <select required value={newDelegation.scopeType} onChange={e => setNewDelegation({...newDelegation, scopeType: e.target.value})} style={inputStyle}>
                  <option value="FACILITY">Standort (Facility)</option>
                  <option value="JOB">Spezifischer Job</option>
                  <option value="ALL">Alles (Global)</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>ID des Standorts/Jobs (Optional)</label>
                <input type="text" placeholder="Standort-ID oder Job-ID..." value={newDelegation.scopeId} onChange={e => setNewDelegation({...newDelegation, scopeId: e.target.value})} style={inputStyle} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Gültig von</label>
                <input required type="date" value={newDelegation.validFrom} onChange={e => setNewDelegation({...newDelegation, validFrom: e.target.value})} style={inputStyle} />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Gültig bis</label>
                <input required type="date" value={newDelegation.validUntil} onChange={e => setNewDelegation({...newDelegation, validUntil: e.target.value})} style={inputStyle} />
              </div>
            </div>

            <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.05)', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
              <strong>Sicherheitshinweis (Segregation of Duties):</strong> Die Vertretung darf in diesem Zeitraum keine Selbsterhöhung von Rechten vornehmen und ihre eigenen Anträge nicht freigeben. Eine Weiterdelegierung ist untersagt. Das System entzieht die Rechte am Enddatum automatisch.
            </div>

            <button type="submit" className="btn-primary" style={{ padding: '0.75rem 2rem', fontSize: '1rem' }}>✅ Vertretung speichern</button>
          </form>
        </div>
      )}

      {activeTab === 'interfaces' && (
        <div style={{ display: 'grid', gap: '2rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Arbeitsagentur Schnittstelle (HR-BA-XML)</h3>
            <p style={{ opacity: 0.8, marginBottom: '2rem' }}>
              Hinterlegen Sie hier die von der Bundesagentur für Arbeit erhaltenen Kennungen für den vollautomatischen XML-Stellenexport. 
              <br/><br/>
              <a href="/api/cms/export/ba-xml" target="_blank" style={{ color: 'var(--primary)', textDecoration: 'underline' }}>📥 Aktuellen XML-Export generieren und herunterladen</a>
            </p>

            <form onSubmit={saveSetting} style={{ display: 'grid', gap: '1.5rem', maxWidth: '600px' }}>
              {['ba_supplier_id', 'ba_hiring_org_id'].map(key => {
                const settingObj = settings.find(s => s.key === key) || { key, value: '' };
                const label = key === 'ba_supplier_id' ? 'Supplier ID (Anbieter-Kennung)' : 'Hiring Org ID (Betriebsnummer/Arbeitgeber-Kennung)';
                
                return (
                  <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <label style={{ fontWeight: 'bold' }}>{label}</label>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                      <input 
                        type="text" 
                        value={settingObj.value} 
                        onChange={(e) => {
                          const newSettings = [...settings];
                          const idx = newSettings.findIndex(s => s.key === key);
                          if(idx >= 0) newSettings[idx].value = e.target.value;
                          else newSettings.push({ key, value: e.target.value });
                          setSettings(newSettings);
                          setEditSetting({ key, value: e.target.value }); // Trick to let saveSetting work
                        }}
                        placeholder="z.B. V123456789"
                        style={inputStyle}
                      />
                      <button type="button" onClick={() => saveSetting({ preventDefault: ()=>{} } as any)} className="btn-primary" style={{ padding: '0 1.5rem' }}>Speichern</button>
                    </div>
                  </div>
                );
              })}
            </form>
          </div>
        </div>
      )}

      {activeTab === 'sap' && (
        <div style={{ display: 'grid', gap: '2rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: '12px' }}>
            <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>SAP SuccessFactors Integration</h3>
            <p style={{ opacity: 0.8, marginBottom: '2rem', lineHeight: '1.6' }}>
              Diese OData-API-Verbindung konvertiert Kandidaten automatisch zu Mitarbeitern (Candidate-to-Employee).
              <br /><strong>Übertragene Datenfelder:</strong> Vorname, Nachname, E-Mail, Telefon, Adresse, Geburtsdatum, Stellenbezeichnung, Abteilungs-ID (OrgChart), Startdatum, sowie das verschlüsselte CV-PDF.
            </p>

            <div style={{ marginBottom: '2rem', background: 'var(--background)', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead style={{ background: 'var(--card-bg)' }}>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Funktion (API Capability)</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Recruiting (RCK)</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Onboarding 2.0</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Employee Central (EC)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 'bold' }}>Basis-Profilanlage (Pre-Hire)</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#10b981' }}>✔️ Ja</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#10b981' }}>✔️ Ja</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#10b981' }}>✔️ Ja</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 'bold' }}>Digitale Vertragsunterschrift (eSign)</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#ef4444' }}>❌ Nein</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#10b981' }}>✔️ Ja</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#ef4444' }}>❌ Nein</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 'bold' }}>Autom. Gehaltsband-Zuweisung</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#ef4444' }}>❌ Nein</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#ef4444' }}>❌ Nein</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#10b981' }}>✔️ Ja</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 'bold' }}>IT-Hardware Bereitstellung (Tasks)</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#ef4444' }}>❌ Nein</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#10b981' }}>✔️ Ja</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#ef4444' }}>❌ Nein</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid var(--primary)', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.05)' }}>
              <h4 style={{ marginBottom: '0.5rem' }}>API-Umgebung (Environment)</h4>
              <p style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '1rem' }}>Wählen Sie die Umgebung aus. Neue Integrationen sollten zuerst in der Test-Umgebung (Sandbox) validiert werden, bevor sie produktiv geschaltet werden.</p>
              
              <div style={{ display: 'flex', gap: '2rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontWeight: 'bold' }}>
                  <input 
                    type="radio" 
                    name="sap_env" 
                    value="test"
                    checked={(settings.find(s => s.key === 'sap_env')?.value || 'test') === 'test'}
                    onChange={(e) => {
                      const newSettings = [...settings];
                      const idx = newSettings.findIndex(s => s.key === 'sap_env');
                      if(idx >= 0) newSettings[idx].value = e.target.value;
                      else newSettings.push({ key: 'sap_env', value: e.target.value });
                      setSettings(newSettings);
                      setEditSetting({ key: 'sap_env', value: e.target.value });
                      setTimeout(() => saveSetting({ preventDefault: ()=>{} } as any), 100);
                    }}
                  />
                  🧪 Sandbox / Test-Umgebung
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontWeight: 'bold', color: '#ef4444' }}>
                  <input 
                    type="radio" 
                    name="sap_env" 
                    value="prod"
                    checked={(settings.find(s => s.key === 'sap_env')?.value) === 'prod'}
                    onChange={(e) => {
                      if(!window.confirm('Warnung: Änderungen hier wirken sich auf reale Mitarbeiterdaten aus. Fortfahren?')) return;
                      const newSettings = [...settings];
                      const idx = newSettings.findIndex(s => s.key === 'sap_env');
                      if(idx >= 0) newSettings[idx].value = e.target.value;
                      else newSettings.push({ key: 'sap_env', value: e.target.value });
                      setSettings(newSettings);
                      setEditSetting({ key: 'sap_env', value: e.target.value });
                      setTimeout(() => saveSetting({ preventDefault: ()=>{} } as any), 100);
                    }}
                  />
                  🚀 Produktion (Live)
                </label>
              </div>
            </div>

            <form style={{ display: 'grid', gap: '1.5rem', maxWidth: '600px', marginBottom: '2rem' }}>
              {[
                { key: 'sap_base_url', label: 'API Base URL (OData)', placeholder: 'z.B. https://api4.successfactors.com' },
                { key: 'sap_company_id', label: 'Company ID', placeholder: 'z.B. EnterpriseXYZ' },
                { key: 'sap_client_id', label: 'Client ID / API Key', placeholder: 'z.B. MDEyMzQ1Njc4OTA=' },
                { key: 'sap_client_secret', label: 'Client Secret (Password)', placeholder: 'z.B. geheimes_passwort', type: 'password' }
              ].map(({ key, label, placeholder, type = 'text' }) => {
                const settingObj = settings.find(s => s.key === key) || { key, value: '' };
                
                return (
                  <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <label style={{ fontWeight: 'bold' }}>{label}</label>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                      <input 
                        type={type} 
                        value={settingObj.value} 
                        onChange={(e) => {
                          const newSettings = [...settings];
                          const idx = newSettings.findIndex(s => s.key === key);
                          if(idx >= 0) newSettings[idx].value = e.target.value;
                          else newSettings.push({ key, value: e.target.value });
                          setSettings(newSettings);
                          setEditSetting({ key, value: e.target.value }); // Trick to trigger save
                        }}
                        placeholder={placeholder}
                        style={inputStyle}
                      />
                      <button type="button" onClick={() => saveSetting({ preventDefault: ()=>{} } as any)} className="btn-primary" style={{ padding: '0 1.5rem' }}>Speichern</button>
                    </div>
                  </div>
                );
              })}
            </form>

            <div style={{ padding: '1.5rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--card-bg)', marginBottom: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h4 style={{ margin: 0 }}>Dynamisches Daten-Feld Mapping (OData Payload)</h4>
                <span style={{ fontSize: '0.8rem', background: 'var(--primary)', color: 'white', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>Pro Feature</span>
              </div>
              <p style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '1.5rem' }}>Ordnen Sie die internen Datenfelder unserer Plattform den exakten Schlüsseln (JSON Keys) Ihrer SAP SuccessFactors Instanz zu. Das verhindert API-Fehler durch kundenspezifische SAP-Felder (Custom Fields).</p>
              
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead style={{ background: 'var(--background)' }}>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Internes Feld (ATS)</th>
                    <th style={{ padding: '0.75rem 1rem' }}>➡️</th>
                    <th style={{ padding: '0.75rem 1rem' }}>SAP Feld (OData Key)</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Typ</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { internal: 'candidate.firstName', sapKey: 'personalInfo/firstName', type: 'String' },
                    { internal: 'candidate.lastName', sapKey: 'personalInfo/lastName', type: 'String' },
                    { internal: 'candidate.email', sapKey: 'emailInfo/emailAddress', type: 'String' },
                    { internal: 'candidate.phone', sapKey: 'phoneInfo/phoneNumber', type: 'String' },
                    { internal: 'candidate.address.street', sapKey: 'addressInfo/address1', type: 'String' },
                    { internal: 'candidate.address.city', sapKey: 'addressInfo/city', type: 'String' },
                    { internal: 'candidate.address.zip', sapKey: 'addressInfo/zipCode', type: 'String' },
                    { internal: 'candidate.birthDate', sapKey: 'personalInfo/dateOfBirth', type: 'Date' },
                    { internal: 'cv.parsed.languages', sapKey: 'backgroundInfo/languages', type: 'Array<String>' },
                    { internal: 'cv.parsed.driverLicense', sapKey: 'backgroundInfo/driverLicenseClass', type: 'String' },
                    { internal: 'healthcare.approbation', sapKey: 'cust_Healthcare/approbationId', type: 'String (Custom)' },
                    { internal: 'healthcare.facharztZertifikat', sapKey: 'cust_Healthcare/specialistCert', type: 'Attachment (PDF)' },
                    { internal: 'compliance.masernschutz', sapKey: 'cust_Compliance/measlesVaccine', type: 'Boolean' },
                    { internal: 'compliance.fuehrungszeugnis', sapKey: 'backgroundCheck/policeClearance', type: 'Attachment (PDF)' },
                    { internal: 'job.departmentId', sapKey: 'jobInfo/department', type: 'String (OrgChart)' },
                    { internal: 'contract.startDate', sapKey: 'jobInfo/expectedStartDate', type: 'Date (ISO 8601)' },
                  ].map((field, i) => {
                    const settingKey = `sap_map_${field.internal.replace('.', '_')}`;
                    const settingObj = settings.find(s => s.key === settingKey) || { key: settingKey, value: field.sapKey };
                    
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace', opacity: 0.8 }}>{field.internal}</td>
                        <td style={{ padding: '0.75rem 1rem' }}>➡️</td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <input 
                            type="text" 
                            value={settingObj.value} 
                            onChange={(e) => {
                              const newSettings = [...settings];
                              const idx = newSettings.findIndex(s => s.key === settingKey);
                              if(idx >= 0) newSettings[idx].value = e.target.value;
                              else newSettings.push({ key: settingKey, value: e.target.value });
                              setSettings(newSettings);
                              setEditSetting({ key: settingKey, value: e.target.value });
                            }}
                            onBlur={() => saveSetting({ preventDefault: ()=>{} } as any)}
                            style={{ ...inputStyle, padding: '0.4rem 0.75rem' }} 
                          />
                        </td>
                        <td style={{ padding: '0.75rem 1rem', opacity: 0.6, fontSize: '0.8rem' }}>{field.type}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <button className="btn-primary" style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: 'transparent', border: '1px dashed var(--primary)', color: 'var(--primary)' }}>+ Custom Field (z.B. cust_XYZ) hinzufügen</button>
            </div>
            <div style={{ padding: '1.5rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--card-bg)' }}>
              <h4 style={{ marginBottom: '1rem' }}>Verbindungsdiagnose</h4>
              <p style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '1rem' }}>Überprüfen Sie, ob die Zugangsdaten korrekt sind und die Firewall den Zugriff auf die SAP OData API erlaubt.</p>
              
              <button 
                onClick={testSAPPing} 
                disabled={pingStatus.loading}
                style={{ 
                  padding: '0.75rem 1.5rem', 
                  borderRadius: '8px', 
                  cursor: pingStatus.loading ? 'not-allowed' : 'pointer', 
                  background: pingStatus.loading ? 'var(--border)' : 'var(--primary)', 
                  color: 'white',
                  border: 'none',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {pingStatus.loading ? '⏳ Teste Verbindung...' : '🔌 Ping Test starten'}
              </button>

              {pingStatus.message && (
                <div style={{ 
                  marginTop: '1rem', 
                  padding: '1rem', 
                  borderRadius: '6px', 
                  background: pingStatus.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                  color: pingStatus.success ? '#10b981' : '#ef4444',
                  border: `1px solid ${pingStatus.success ? '#10b981' : '#ef4444'}`
                }}>
                  <strong style={{ display: 'block', marginBottom: '0.25rem' }}>
                    {pingStatus.success ? 'Erfolg' : 'Fehler bei der Verbindung'}
                  </strong>
                  {pingStatus.message}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
