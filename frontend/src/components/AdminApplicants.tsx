'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';

type Workflow = { id: string; name: string; stepsJson: string };
type Ticket = {
  id: string;
  workflowId: string;
  steps: { stepOrder: number }[];
  application: {
    id: string;
    applicant: { firstName: string; lastName: string; email: string };
    jobPosting: { title: string };
    status: string;
  };
};

export default function AdminApplicants() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('');
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'kanban' | 'table'>('kanban');

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    const res = await fetch('/api/cms/workflows');
    const data = await res.json();
    setWorkflows(data.workflows || []);
    if (data.workflows && data.workflows.length > 0) {
      setSelectedWorkflow(data.workflows[0].id);
    }
  };

  useEffect(() => {
    if (viewMode === 'table' || selectedWorkflow) {
      loadTickets();
    }
  }, [selectedWorkflow, search, viewMode]);

  const loadTickets = async () => {
    setLoading(true);
    const wfParam = viewMode === 'table' ? '' : selectedWorkflow;
    const res = await fetch(`/api/cms/applications?workflowId=${wfParam}&q=${encodeURIComponent(search)}`);
    const data = await res.json();
    setTickets(data.tickets || []);
    setLoading(false);
  };

  const currentWorkflow = workflows.find(w => w.id === selectedWorkflow);
  let steps: any[] = [];
  try {
    if (currentWorkflow) steps = JSON.parse(currentWorkflow.stepsJson || '[]');
  } catch {}

  const handleDragStart = (e: React.DragEvent, ticketId: string) => {
    e.dataTransfer.setData('ticketId', ticketId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault(); // Erlaubt das Droppen
  };

  const handleDrop = async (e: React.DragEvent, stepIndex: number) => {
    const ticketId = e.dataTransfer.getData('ticketId');
    if (!ticketId) return;

    // Optimistic UI Update
    const oldTickets = [...tickets];
    setTickets(tickets.map(t => {
      if (t.id === ticketId) {
        return { ...t, steps: [{ stepOrder: stepIndex }] };
      }
      return t;
    }));

    // API Call
    try {
      const res = await fetch('/api/cms/applications/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticketId, stepIndex })
      });
      if (!res.ok) throw new Error('Fehler beim Verschieben');
    } catch (err) {
      console.error(err);
      setTickets(oldTickets); // Rollback
      alert('Verschieben fehlgeschlagen.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 100px)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', color: 'var(--primary)', marginBottom: '0.5rem' }}>Bewerber-Board (Kanban)</h1>
          <p style={{ opacity: 0.7 }}>Ziehe Bewerber per Drag & Drop in die nächste Prozess-Spalte.</p>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <div style={{ display: 'flex', background: 'var(--card-bg)', borderRadius: '8px', border: '1px solid var(--border)', overflow: 'hidden' }}>
            <button 
              onClick={() => setViewMode('kanban')} 
              style={{ padding: '0.6rem 1rem', border: 'none', background: viewMode === 'kanban' ? 'var(--primary)' : 'transparent', color: viewMode === 'kanban' ? 'white' : 'var(--foreground)', cursor: 'pointer', fontWeight: viewMode === 'kanban' ? 'bold' : 'normal' }}
            >
              📋 Kanban
            </button>
            <button 
              onClick={() => setViewMode('table')} 
              style={{ padding: '0.6rem 1rem', border: 'none', background: viewMode === 'table' ? 'var(--primary)' : 'transparent', color: viewMode === 'table' ? 'white' : 'var(--foreground)', cursor: 'pointer', fontWeight: viewMode === 'table' ? 'bold' : 'normal' }}
            >
              🗂️ Gesamtübersicht
            </button>
          </div>

          <input 
            type="text" 
            placeholder="Suchen (Name, E-Mail)..." 
            value={search} 
            onChange={e => setSearch(e.target.value)}
            style={{ padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' }}
          />
          {viewMode === 'kanban' && (
            <select 
              value={selectedWorkflow} 
              onChange={e => setSelectedWorkflow(e.target.value)}
              style={{ padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--primary)', background: 'var(--card-bg)', color: 'var(--foreground)', fontWeight: 'bold' }}
            >
              {workflows.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          )}
        </div>
      </div>

      {!currentWorkflow && viewMode === 'kanban' && <p>Lade Workflows...</p>}

      {viewMode === 'table' && (
        <div className="glass-panel" style={{ flex: 1, borderRadius: '12px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ overflowX: 'auto', flex: 1 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead style={{ background: 'rgba(0,0,0,0.05)', borderBottom: '2px solid var(--border)' }}>
                <tr>
                  <th style={{ padding: '1rem' }}>Bewerber</th>
                  <th style={{ padding: '1rem' }}>Jobtitel</th>
                  <th style={{ padding: '1rem' }}>Workflow</th>
                  <th style={{ padding: '1rem' }}>Aktueller Status</th>
                  <th style={{ padding: '1rem' }}>Aktion</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map(ticket => {
                  const wf = workflows.find(w => w.id === ticket.workflowId);
                  let currentStepName = 'Unbekannt';
                  try {
                    const parsedSteps = JSON.parse(wf?.stepsJson || '[]');
                    const order = ticket.steps?.[0]?.stepOrder || 0;
                    currentStepName = parsedSteps[order]?.name || `Schritt ${order + 1}`;
                  } catch {}

                  return (
                    <tr key={ticket.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ fontWeight: 'bold' }}>{ticket.application.applicant.firstName} {ticket.application.applicant.lastName}</div>
                        <div style={{ fontSize: '0.85rem', opacity: 0.6 }}>{ticket.application.applicant.email}</div>
                      </td>
                      <td style={{ padding: '1rem' }}>{ticket.application.jobPosting.title}</td>
                      <td style={{ padding: '1rem' }}>
                        <span style={{ fontSize: '0.85rem', background: 'var(--background)', padding: '0.3rem 0.6rem', borderRadius: '4px', border: '1px solid var(--border)' }}>
                          {wf?.name || 'Standard'}
                        </span>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                          {currentStepName}
                        </span>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <Link href={`/admin/applications/${ticket.application.id}`} style={{ padding: '0.5rem 1rem', background: 'var(--primary)', color: 'white', borderRadius: '6px', textDecoration: 'none', fontSize: '0.85rem' }}>
                          Öffnen
                        </Link>
                      </td>
                    </tr>
                  );
                })}
                {tickets.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ padding: '3rem', textAlign: 'center', opacity: 0.5 }}>Keine Bewerber gefunden.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {viewMode === 'kanban' && currentWorkflow && (
        <div style={{ display: 'flex', gap: '1.5rem', overflowX: 'auto', flex: 1, paddingBottom: '1rem' }}>
          {steps.map((step, index) => {
            const columnTickets = tickets.filter(t => {
              const currentStep = t.steps?.[0]?.stepOrder || 0;
              return currentStep === index;
            });

            return (
              <div 
                key={index}
                onDragOver={handleDragOver}
                onDrop={e => handleDrop(e, index)}
                className="glass-panel"
                style={{ 
                  minWidth: '320px', 
                  maxWidth: '320px', 
                  borderRadius: '12px', 
                  display: 'flex', 
                  flexDirection: 'column',
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px dashed var(--border)',
                  padding: '1rem'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid var(--primary)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                  <h3 style={{ fontSize: '1.1rem', margin: 0 }}>{step.name}</h3>
                  <span style={{ background: 'var(--border)', padding: '0.2rem 0.6rem', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 'bold' }}>
                    {columnTickets.length}
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1, overflowY: 'auto' }}>
                  {columnTickets.map(ticket => (
                    <div 
                      key={ticket.id}
                      draggable
                      onDragStart={e => handleDragStart(e, ticket.id)}
                      style={{ 
                        background: 'var(--card-bg)', 
                        padding: '1rem', 
                        borderRadius: '8px', 
                        border: '1px solid var(--border)', 
                        cursor: 'grab',
                        boxShadow: '0 4px 6px rgba(0,0,0,0.05)',
                        borderLeft: '4px solid var(--primary)'
                      }}
                    >
                      <h4 style={{ margin: '0 0 0.3rem 0', fontSize: '1.05rem' }}>
                        {ticket.application.applicant.firstName} {ticket.application.applicant.lastName}
                      </h4>
                      <p style={{ margin: '0 0 0.8rem 0', fontSize: '0.8rem', opacity: 0.6 }}>{ticket.application.jobPosting.title}</p>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', borderRadius: '4px', fontWeight: 'bold' }}>
                          KI Score: A
                        </span>
                        <Link href={`/admin/applications/${ticket.application.id}`} style={{ fontSize: '0.8rem', color: 'var(--primary)', textDecoration: 'none' }}>
                          Profil öffnen →
                        </Link>
                      </div>
                    </div>
                  ))}
                  
                  {columnTickets.length === 0 && (
                    <div style={{ opacity: 0.3, textAlign: 'center', padding: '2rem 0', fontSize: '0.9rem' }}>
                      Hierher ziehen
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
