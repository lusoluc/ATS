import React from 'react';
import Link from 'next/link';

export const HomeHero = {
  fields: {
    label: { type: 'text' },
    score: { type: 'text' },
    titlePrefix: { type: 'text' },
    titleHighlight: { type: 'text' },
    subtitle: { type: 'textarea' },
    btnPrimaryText: { type: 'text' },
    btnPrimaryUrl: { type: 'text' },
    btnSecondaryText: { type: 'text' },
    btnSecondaryUrl: { type: 'text' },
    imageAlt: { type: 'text' },
    imageLocation: { type: 'text' },
    quote: { type: 'textarea' },
    author: { type: 'text' }
  },
  defaultProps: {
    label: 'Nordicum Health Group',
    score: '⭐ 4.6 Kununu Score',
    titlePrefix: 'Gemeinsam für',
    titleHighlight: 'die Gesundheit.',
    subtitle: 'Wir sind einer der führenden Maximalversorger in Norddeutschland. Modernste Medizin, familiäre Teams und echte Wertschätzung für deine Arbeit.',
    btnPrimaryText: 'Jetzt offene Stellen finden',
    btnPrimaryUrl: '/jobs',
    btnSecondaryText: '1-Klick Initiativbewerbung',
    btnSecondaryUrl: '/bewerben',
    imageAlt: 'Pflegeteam Nordicum Health im Einsatz',
    imageLocation: '📍 Campus Hamburg-Mitte',
    quote: '"Das beste Team, das ich je hatte. Hier wird zusammen gelacht und gearbeitet."',
    author: '— Sarah, Stationsleitung'
  },
  render: ({ label, score, titlePrefix, titleHighlight, subtitle, btnPrimaryText, btnPrimaryUrl, btnSecondaryText, btnSecondaryUrl, imageAlt, imageLocation, quote, author }: any) => (
    <section className="hero-section" style={{ padding: '6rem 0 0', minHeight: 'auto', background: 'var(--background)' }}>
      <div className="container" style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '4rem', alignItems: 'center' }}>
        <div className="animate-fade-in">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
            <p className="section-label" style={{ marginBottom: 0 }}>{label}</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', background: '#e3f5eb', color: '#107a43', padding: '0.3rem 0.6rem', borderRadius: '20px', fontSize: '0.75rem', fontWeight: 'bold' }}>
              {score}
            </div>
          </div>
          <h1 className="hero-title" style={{ fontSize: 'clamp(3rem, 5vw, 4.5rem)', lineHeight: 1.05, color: 'var(--foreground)' }}>
            {titlePrefix}
            <span className="accent" style={{ display: 'block', marginTop: '0.5rem', color: 'var(--primary)' }}>{titleHighlight}</span>
          </h1>
          <p className="hero-subtitle" style={{ fontSize: '1.25rem', marginTop: '1.5rem', color: 'var(--muted)' }}>
            {subtitle}
          </p>
          <div className="hero-actions" style={{ marginTop: '2.5rem' }}>
            <a href={btnPrimaryUrl} className="btn-primary" style={{ fontSize: '1.1rem', padding: '1.1rem 2.5rem', boxShadow: '0 8px 25px rgba(0, 80, 255, 0.3)', textDecoration:'none', display:'inline-block' }}>
              {btnPrimaryText}
            </a>
            <a href={btnSecondaryUrl} className="btn-outline" style={{ fontSize: '1.1rem', padding: '1.1rem 2rem', textDecoration:'none', display:'inline-block', marginLeft: '1rem' }}>
              {btnSecondaryText}
            </a>
          </div>
        </div>
        <div className="animate-fade-in hide-mobile" style={{ position: 'relative' }}>
          <div style={{ borderRadius: '24px', overflow: 'hidden', aspectRatio: '4/5', position: 'relative', boxShadow: '0 20px 40px rgba(0,0,0,0.1)' }}>
            <img src="/pflege_portrait.png" alt={imageAlt} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            <div style={{ position: 'absolute', bottom: '1.5rem', left: '1.5rem', right: '1.5rem', background: 'rgba(255,255,255,0.95)', padding: '1rem 1.5rem', borderRadius: '16px', backdropFilter: 'blur(10px)' }}>
              <p style={{ fontWeight: 800, color: 'var(--primary)', fontSize: '1rem', display: 'flex', justifyContent: 'space-between' }}>
                <span>{imageLocation}</span>
                <span style={{ fontSize: '1.2rem' }}>👩‍⚕️</span>
              </p>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: '0.3rem', lineHeight: 1.4 }}>
                {quote}<br/>
                <strong style={{ color: 'var(--text)', marginTop: '0.3rem', display: 'block' }}>{author}</strong>
              </p>
            </div>
          </div>
        </div>
      </div>
      <div style={{ height: '80px', background: 'var(--background)', marginTop: '5rem', clipPath: 'ellipse(60% 100% at 50% 100%)' }} />
    </section>
  )
};

export const HomeStatBar = {
  fields: {
    stats: {
      type: 'array',
      arrayFields: { num: { type: 'text' }, label: { type: 'text' } }
    }
  },
  defaultProps: {
    stats: [
      { num: '4.500+', label: 'Mitarbeitende' },
      { num: '12',     label: 'Klinikstandorte' },
      { num: '30 Tage', label: 'Urlaub (KTD Tarif)' },
      { num: 'Top 100',   label: 'Arbeitgeber 2026' }
    ]
  },
  render: ({ stats }: any) => (
    <section className="stat-bar" style={{ marginTop: '-2rem', zIndex: 10, position: 'relative' }}>
      <div className="container">
        <div className="stat-bar-inner" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-around', background: 'white', borderRadius: '16px', boxShadow: '0 10px 30px rgba(0,0,0,0.05)' }}>
          {stats.map((s:any, i:number) => (
            <div key={i} className="stat-item" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem 1rem' }}>
              <span className="stat-number" style={{ color: 'var(--primary)', fontSize: '2.5rem', fontWeight: 800 }}>{s.num}</span>
              <span className="stat-label" style={{ color: 'var(--foreground)', fontWeight: 600, marginTop: '0.5rem' }}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
};

export const HomeTargetGroups = {
  fields: {
    label: { type: 'text' },
    title: { type: 'text' },
    subtitle: { type: 'text' },
    groups: {
      type: 'array',
      arrayFields: { title: { type: 'text' }, icon: { type: 'text' }, desc: { type: 'textarea' }, link: { type: 'text' } }
    }
  },
  defaultProps: {
    label: 'Dein Einstieg bei uns',
    title: 'Wofür schlägt dein Herz?',
    subtitle: 'Finde genau den Bereich, der zu deiner Expertise und deinen Lebenszielen passt.',
    groups: [
      { title: 'Pflege & Betreuung', icon: '🩺', desc: 'Stationär, ambulant oder Intensiv – werde Teil der größten Pflege-Community im Norden.', link: '/jobs?category=pflege' },
      { title: 'Medizin & Therapie', icon: '⚕️', desc: 'Modernste Medizintechnik trifft auf exzellente Fallbesprechungen. Für Ärzte und Therapeuten.', link: '/jobs?category=medizin' },
      { title: 'IT & Verwaltung', icon: '💻', desc: 'Die Infrastruktur am Laufen halten. Digitalisierung im Gesundheitswesen aktiv mitgestalten.', link: '/jobs?category=verwaltung' },
      { title: 'Ausbildung & Studium', icon: '🎓', desc: 'Starte deine Karriere mit unseren exzellenten Dual-Programmen und Mentoring.', link: '/jobs?category=ausbildung' }
    ]
  },
  render: ({ label, title, subtitle, groups }: any) => (
    <section style={{ padding: '6rem 0', background: 'var(--background)' }}>
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <p className="section-label">{label}</p>
          <h2 className="section-title">{title}</h2>
          <p style={{ fontSize: '1.2rem', color: 'var(--muted)', maxWidth: '600px', margin: '0 auto' }}>{subtitle}</p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
          {groups.map((tg:any, i:number) => (
            <a href={tg.link} key={i} style={{ background: 'white', padding: '2.5rem', borderRadius: '20px', textDecoration: 'none', color: 'inherit', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ fontSize: '3rem', background: 'var(--surface-1)', width: '80px', height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '20px' }}>{tg.icon}</div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 800, marginTop: '0.5rem' }}>{tg.title}</h3>
              <p style={{ color: 'var(--muted)', lineHeight: 1.6 }}>{tg.desc}</p>
              <span style={{ color: 'var(--primary)', fontWeight: 700, marginTop: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>Jobs entdecken <span>→</span></span>
            </a>
          ))}
        </div>
      </div>
    </section>
  )
};

export const HomeBenefits = {
  fields: {
    label: { type: 'text' },
    title: { type: 'text' },
    subtitle: { type: 'text' },
    benefits: {
      type: 'array',
      arrayFields: { icon: { type: 'text' }, title: { type: 'text' }, text: { type: 'textarea' } }
    }
  },
  defaultProps: {
    label: 'Was wir bieten',
    title: 'Deine Arbeit, unser Respekt.',
    subtitle: 'Wir investieren in dich. Entdecke Benefits, die wirklich einen Unterschied in deinem Alltag machen.',
    benefits: [
      { icon: '💰', title: 'Tarifliche Top-Vergütung', text: 'Nach KTD-Tarifvertrag. Inklusive 13. Monatsgehalt, Pflegezulagen und pünktlicher Gehaltsentwicklung.' },
      { icon: '🏖️', title: '30 Tage Urlaub + Flexzeit', text: 'Damit du abschalten kannst. Flexible Dienstpläne per App und garantierte freie Wochenenden.' },
      { icon: '🚴', title: 'E-Bike Leasing & Mobilität', text: 'JobRad für dich und deinen Partner, plus 100% Zuschuss zum Deutschlandticket für alle Standorte.' },
      { icon: '📈', title: 'Garantierte Weiterbildung', text: 'Wir finanzieren deine Karriere: Fachweiterbildungen, Führungskräfte-Training und Kongressbesuche.' },
      { icon: '👶', title: 'Familie & Beruf', text: 'Betriebs-Kitas an 4 Standorten, Notfallbetreuung und flexible Teilzeit-Modelle (auch für Führungskräfte).' },
      { icon: '👵', title: 'Betriebliche Altersvorsorge', text: 'Sichere Zukunft: Wir zahlen 5,4% deines Bruttogehalts zusätzlich in deine Pensionskasse.' }
    ]
  },
  render: ({ label, title, subtitle, benefits }: any) => (
    <section style={{ padding: '6rem 0', background: 'var(--surface-2)' }}>
      <div className="container">
        <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <p className="section-label">{label}</p>
          <h2 className="section-title">{title}</h2>
          <p className="section-subtitle" style={{ margin: '0 auto' }}>{subtitle}</p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
          {benefits.map((b:any, i:number) => (
            <div key={i} className="benefit-card" style={{ background: 'white', padding: '2rem', borderRadius: '16px', border: '1px solid var(--border)' }}>
              <div className="benefit-icon" style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>{b.icon}</div>
              <h3 className="benefit-title" style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.5rem' }}>{b.title}</h3>
              <p style={{ fontSize: '0.95rem', color: 'var(--muted)', lineHeight: 1.6 }}>{b.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
};

export const HomeEmployerBranding = {
  fields: {
    label: { type: 'text' },
    titlePrefix: { type: 'text' },
    titleHighlight: { type: 'text' },
    text: { type: 'textarea' },
    btnText: { type: 'text' },
    btnUrl: { type: 'text' },
    videoText: { type: 'text' },
    bgImage: { type: 'text' }
  },
  defaultProps: {
    label: 'Kultur & Alltag',
    titlePrefix: 'Wir arbeiten auf',
    titleHighlight: 'Augenhöhe.',
    text: 'Egal ob Chefarzt oder Pflegeschüler: Bei Nordicum Health zählen die Argumente, nicht die Hierarchie. Unser Leitbild basiert auf bedingungsloser Teamarbeit und radikaler Transparenz im klinischen Alltag.',
    btnText: 'Lerne unser Team kennen',
    btnUrl: '/info/kultur',
    videoText: 'Play: Ein Tag auf Station 4',
    bgImage: '/kultur_augenhoehe.png'
  },
  render: ({ label, titlePrefix, titleHighlight, text, btnText, btnUrl, videoText, bgImage }: any) => (
    <section style={{ padding: '0', overflow: 'hidden' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: '500px' }}>
        <div style={{ background: '#0a2540', color: 'white', padding: '6rem 4rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <p style={{ fontSize: '0.9rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.15em', opacity: 0.8, marginBottom: '1.5rem', color: '#63b3ed' }}>{label}</p>
          <h2 style={{ fontFamily: 'var(--font-outfit)', fontSize: 'clamp(2.5rem,5vw,3.5rem)', fontWeight: 900, lineHeight: 1.1, marginBottom: '2rem' }}>
            {titlePrefix}<br />
            <span style={{ color: '#63b3ed' }}>{titleHighlight}</span>
          </h2>
          <p style={{ opacity: 0.9, lineHeight: 1.8, marginBottom: '2.5rem', maxWidth: '480px', fontSize: '1.1rem' }}>{text}</p>
          <a href={btnUrl} className="btn-secondary" style={{ alignSelf: 'flex-start', background: 'white', color: '#0a2540', border: 'none', padding: '1rem 2.5rem', fontSize: '1.1rem', textDecoration:'none' }}>
            {btnText}
          </a>
        </div>
        <div style={{ background: `url(${bgImage}) center/cover`, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', position: 'relative' }}>
           <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.3)' }}></div>
           <button style={{ zIndex: 10, width: '90px', height: '90px', background: 'var(--primary)', color: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', border: 'none', boxShadow: '0 10px 30px rgba(0,0,0,0.3)' }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
           </button>
           <p style={{ zIndex: 10, color: 'white', fontWeight: 800, marginTop: '1.5rem', fontSize: '1.2rem', textShadow: '0 2px 10px rgba(0,0,0,0.5)' }}>{videoText}</p>
        </div>
      </div>
    </section>
  )
};

export const HomeFAQ = {
  fields: {
    label: { type: 'text' },
    title: { type: 'text' },
    faqs: {
      type: 'array',
      arrayFields: { q: { type: 'text' }, a: { type: 'textarea' } }
    },
    contactName: { type: 'text' },
    contactRole: { type: 'text' },
    contactText: { type: 'textarea' },
    contactPhone: { type: 'text' },
    contactWhatsapp: { type: 'text' }
  },
  defaultProps: {
    label: 'Häufige Fragen',
    title: 'Transparenz vor der Bewerbung',
    faqs: [
      { q: 'Wie läuft der Bewerbungsprozess (One-Click) ab?', a: 'Wir haben den Prozess radikal vereinfacht: Klicke auf "Bewerben", lade deinen Lebenslauf hoch (oder verlinke dein LinkedIn-Profil). Kein Anschreiben nötig. Wir rufen dich innerhalb von 48 Stunden an!' },
      { q: 'Gibt es Hospitations-Tage?', a: 'Ja! Nach einem kurzen Telefon-Interview laden wir dich gerne zu einem bezahlten Schnuppertag (Hospitation) auf deiner zukünftigen Station ein. So lernst du das Team ungefiltert kennen.' },
      { q: 'Wie funktioniert das Onboarding?', a: 'Du erhältst in den ersten 6 Monaten einen festen Mentor. Zudem gibt es strukturierte Einarbeitungskonzepte für jede Abteilung, damit du niemals ins kalte Wasser geworfen wirst.' },
      { q: 'Ist eine Initiativbewerbung sinnvoll?', a: 'Absolut. Über 30% unserer Einstellungen entstehen durch Initiativbewerbungen. Unser Recruiting-Team findet intern genau den richtigen Platz für deine Fähigkeiten.' }
    ],
    contactName: 'Anna Müller',
    contactRole: 'Leitung Talent Acquisition',
    contactText: '"Du hast Fragen zum Gehalt, zum Team oder zum Ablauf? Schreib mir einfach direkt auf WhatsApp oder ruf kurz durch. Wir klären das ganz unkompliziert!"',
    contactPhone: '040 / 123 456 - 0',
    contactWhatsapp: '4912345678'
  },
  render: ({ label, title, faqs, contactName, contactRole, contactText, contactPhone, contactWhatsapp }: any) => (
    <section style={{ padding: '6rem 0', background: 'var(--background)' }}>
      <div className="container" style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '4rem' }}>
        <div>
          <p className="section-label">{label}</p>
          <h2 className="section-title">{title}</h2>
          <div style={{ marginTop: '2.5rem' }}>
            {faqs.map((item:any, i:number) => (
              <details key={i} className="faq-item" style={{ listStyle: 'none', borderBottom: '1px solid var(--border)', padding: '1.5rem 0' }}>
                <summary className="faq-question" style={{ listStyle: 'none', outline: 'none', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text)' }}>{item.q}</span>
                  <span style={{ color: 'var(--primary)', fontSize: '1.5rem', fontWeight: 300 }}>+</span>
                </summary>
                <p className="faq-answer" style={{ marginTop: '1rem', color: 'var(--muted)', lineHeight: 1.7, paddingRight: '2rem' }}>{item.a}</p>
              </details>
            ))}
          </div>
        </div>
        
        <div>
           <div style={{ background: 'white', padding: '3rem', borderRadius: '24px', border: '1px solid var(--border)', boxShadow: '0 20px 40px rgba(0,0,0,0.04)', position: 'sticky', top: '100px' }}>
              <div style={{ width: '80px', height: '80px', borderRadius: '50%', overflow: 'hidden', marginBottom: '1.5rem' }}>
                 <img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=200&auto=format&fit=crop" alt={contactName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
              <h3 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.2rem' }}>{contactName}</h3>
              <p style={{ color: 'var(--primary)', fontWeight: 600, fontSize: '0.9rem', marginBottom: '1.5rem' }}>{contactRole}</p>
              <p style={{ color: 'var(--muted)', lineHeight: 1.6, marginBottom: '2rem', fontSize: '0.95rem' }}>{contactText}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <a href={`tel:${contactPhone.replace(/\D/g,'')}`} className="btn-primary" style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', padding: '1rem', textDecoration:'none' }}>📞 {contactPhone}</a>
                <a href={`https://wa.me/${contactWhatsapp}`} className="btn-outline" style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', padding: '1rem', color: '#25D366', borderColor: '#25D366', textDecoration:'none' }}>💬 WhatsApp schreiben</a>
              </div>
           </div>
        </div>
      </div>
    </section>
  )
};

export const HomeJobsTeaser = {
  fields: {
    label: { type: 'text' },
    title: { type: 'text' },
    btnText: { type: 'text' },
    btnUrl: { type: 'text' },
    jobs: {
      type: 'array',
      arrayFields: { title: { type: 'text' }, location: { type: 'text' }, category: { type: 'text' }, type: { type: 'text' }, salary: { type: 'text' }, url: { type: 'text' } }
    }
  },
  defaultProps: {
    label: 'Offene Stellen',
    title: 'Neu veröffentlicht',
    btnText: 'Alle 142 Jobs durchsuchen →',
    btnUrl: '/jobs',
    jobs: [
      { title: 'Gesundheits- und Krankenpfleger (m/w/d) Intensivstation', location: 'Campus Hamburg-Mitte', category: 'Pflege', type: 'Vollzeit / Teilzeit', salary: 'KTD Tarif + Zulagen', url: '/jobs/1' },
      { title: 'Facharzt (m/w/d) für Psychiatrie und Psychotherapie', location: 'Klinik Norderstedt', category: 'Medizin', type: 'Vollzeit', salary: 'Chefarzt-Bonusmodell', url: '/jobs/2' },
      { title: 'Senior IT-Systemadministrator (m/w/d) Infrastruktur', location: 'Zentrale Kiel', category: 'IT & Technik', type: 'Vollzeit (Hybrid)', salary: 'Bis zu 80k', url: '/jobs/3' },
      { title: 'Auszubildende (m/w/d) Pflegefachfrau/-mann', location: 'Campus Hamburg-Mitte', category: 'Ausbildung', type: 'Ausbildung', salary: '1.300€ im 1. Jahr', url: '/jobs/4' },
    ]
  },
  render: ({ label, title, btnText, btnUrl, jobs }: any) => {
    const [liveJobs, setLiveJobs] = React.useState<any[]>([]);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
      fetch('/api/public/jobs?limit=4')
        .then(res => res.json())
        .then(data => {
          if (data && data.jobs) {
            setLiveJobs(data.jobs.slice(0, 4).map((j: any) => ({
              title: j.title,
              location: j.location?.name || 'Home Office',
              category: j.jobFamily?.name || 'Allgemein',
              type: 'Vollzeit / Teilzeit', // Fallback for demo
              salary: 'Nach Tarif', // Fallback for demo
              url: `/jobs/${j.id}`
            })));
          }
        })
        .catch(err => console.error("Error fetching live jobs:", err))
        .finally(() => setLoading(false));
    }, []);

    const displayJobs = liveJobs.length > 0 ? liveJobs : (jobs || []);

    return (
      <section style={{ padding: '2rem 0 6rem', background: 'var(--background)' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '3rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <p className="section-label">{label}</p>
              <h2 className="section-title" style={{ marginBottom: 0 }}>{title}</h2>
            </div>
            <a href={btnUrl} className="btn-outline" style={{textDecoration:'none'}}>{btnText}</a>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', opacity: 0.5, padding: '2rem' }}>Lade aktuelle Stellen...</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '3rem' }}>
              {displayJobs.map((job:any, i:number) => (
                <a href={job.url} key={i} className="job-list-item animate-fade-in"
                  style={{ padding: '1.5rem 2rem', background: 'white', borderRadius: '16px', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem', textDecoration: 'none' }}
                >
                  <div style={{ flex: '1 1 500px' }}>
                    <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.8rem' }}>{job.title}</h3>
                    <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', color: 'var(--muted)', fontSize: '0.9rem' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>📍 <strong>{job.location}</strong></span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>⏱️ {job.type}</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>💶 {job.salary}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <span className="badge" style={{ background: 'var(--surface-2)', color: 'var(--text)' }}>{job.category}</span>
                    <span className="btn-primary" style={{ padding: '0.6rem 1.5rem', fontSize: '0.95rem', borderRadius: '8px' }}>Bewerben</span>
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      </section>
    );
  }
};
