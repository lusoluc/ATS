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
    if (selectedWorkflow) loadTickets();
  }, [selectedWorkflow, search]);

  const loadTickets = async () => {
    setLoading(true);
    const res = await fetch(`/api/cms/applications?workflowId=${selectedWorkflow}&q=${encodeURIComponent(search)}`);
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
          <input 
            type="text" 
            placeholder="Suchen (Name, E-Mail)..." 
            value={search} 
            onChange={e => setSearch(e.target.value)}
            style={{ padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' }}
          />
          <select 
            value={selectedWorkflow} 
            onChange={e => setSelectedWorkflow(e.target.value)}
            style={{ padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--primary)', background: 'var(--card-bg)', color: 'var(--foreground)', fontWeight: 'bold' }}
          >
            {workflows.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select>
        </div>
      </div>

      {!currentWorkflow && <p>Lade Workflows...</p>}

      {currentWorkflow && (
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
