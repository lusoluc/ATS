import Link from 'next/link';

export default function HomePage() {
  return (
    <main>
      {/* ── HERO ── */}
      <section className="hero-section" style={{ padding: '5rem 0 0', minHeight: 'auto' }}>
        <div className="container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem', alignItems: 'center' }}>
          <div className="animate-fade-in opacity-0">
            <p className="section-label">Stellenangebote beim Enterprise</p>
            <h1 className="hero-title">
              Du bedeutest
              <span className="accent">uns was.</span>
            </h1>
            <p className="hero-subtitle">
              So wie du bist. Wir sind ein diakonisches Sozialunternehmen in Schleswig-Holstein —
              mit Herz, mit Haltung und mit echten Menschen.
            </p>
            <div className="hero-actions">
              <Link href="/jobs" className="btn-secondary" style={{ fontSize: '1rem', padding: '0.9rem 2rem' }}>
                Alle Jobs ansehen
              </Link>
              <Link href="/bewerben" className="btn-outline" style={{ color: 'white', borderColor: 'rgba(255,255,255,0.5)', fontSize: '1rem' }}>
                Initiativbewerbung
              </Link>
            </div>
          </div>
          <div className="animate-fade-in delay-200 opacity-0 hide-mobile" style={{ position: 'relative' }}>
            <div style={{ borderRadius: '20px', overflow: 'hidden', aspectRatio: '4/3', position: 'relative' }}>
              <img src="/hero_landscape.png" alt="Enterprise Einrichtung in norddeutscher Landschaft"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              <div style={{ position: 'absolute', bottom: '1.5rem', left: '1.5rem', background: 'rgba(255,255,255,0.92)', padding: '0.75rem 1.25rem', borderRadius: '10px', backdropFilter: 'blur(8px)' }}>
                <p style={{ fontWeight: 800, color: 'var(--primary)', fontSize: '0.9rem' }}>🌿 Rickling, Schleswig-Holstein</p>
                <p style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '0.1rem' }}>Eingebettet in die norddeutsche Natur</p>
              </div>
            </div>
          </div>
        </div>

        {/* Curved bottom */}
        <div style={{ height: '60px', background: 'var(--background)', marginTop: '4rem', clipPath: 'ellipse(55% 100% at 50% 100%)' }} />
      </section>

      {/* ── STAT BAR ── */}
      <section className="stat-bar">
        <div className="container">
          <div className="stat-bar-inner">
            {[
              { num: '2.000+', label: 'Mitarbeitende' },
              { num: '10',     label: 'Einrichtungen' },
              { num: 'seit 1876', label: 'Für die Region' },
              { num: '100%',   label: 'Diakonisch & sozial' },
            ].map(s => (
              <div key={s.label} className="stat-item">
                <span className="stat-number">{s.num}</span>
                <span className="stat-label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── AKTUELLE JOBS (Liste, DRK-Stil) ── */}
      <section style={{ padding: '5rem 0', background: 'var(--background)' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <p className="section-label">Offene Stellen</p>
              <h2 className="section-title" style={{ marginBottom: 0 }}>Aktuelle Stellenangebote</h2>
            </div>
            <Link href="/jobs" className="btn-outline">Alle Jobs ansehen →</Link>
          </div>

          {/* Job-List Teaser */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '2rem' }}>
            {[
              { title: 'Pflegefachkraft (m/w/d) für die Psychiatrie', location: 'Rickling', category: 'Pflege & Betreuung' },
              { title: 'Erzieher*in / Sozialpädagog*in (m/w/d) in der Jugendhilfe', location: 'Bad Segeberg', category: 'Pädagogik & Therapie' },
              { title: 'Assistenzarzt (m/w/d) Psychiatrie & Psychotherapie', location: 'Rickling', category: 'Medizin' },
              { title: 'Pflegefachkraft Altenpflege (m/w/d)', location: 'Neumünster', category: 'Pflege & Betreuung' },
              { title: 'IT-Systemadministrator*in (m/w/d)', location: 'Rickling', category: 'Verwaltung' },
            ].map((job, i) => (
              <Link href="/jobs" key={i} className="job-list-item animate-fade-in opacity-0"
                style={{ animationDelay: `${i * 80}ms` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                  <div>
                    <h2>{job.title}</h2>
                    <div style={{ display: 'flex', gap: '1rem', marginTop: '0.3rem', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.83rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>📍 {job.location}</span>
                      <span className="badge badge-primary">{job.category}</span>
                    </div>
                  </div>
                  <span style={{ color: 'var(--primary)', fontWeight: 700, fontSize: '0.9rem', flexShrink: 0 }}>Details →</span>
                </div>
              </Link>
            ))}
          </div>

          <div style={{ textAlign: 'center' }}>
            <Link href="/jobs" className="btn-primary" style={{ fontSize: '1rem' }}>Alle Stellenangebote anzeigen</Link>
          </div>
        </div>
      </section>

      {/* ── BENEFITS (Gehalt/Benefits wie DRK) ── */}
      <section style={{ padding: '5rem 0', background: 'var(--surface-2)' }}>
        <div className="container">
          <p className="section-label">Was wir bieten</p>
          <h2 className="section-title">Dein Talent für die gute Sache</h2>
          <p className="section-subtitle">
            Wir sind gemeinnützig. Das bedeutet: Wir investieren in unsere Mitarbeitenden — nicht in Profit.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem' }}>
            {[
              { icon: '💰', title: 'Faire Vergütung', text: 'Vergütung nach KTD (kirchlicher Tarifvertrag) inkl. Jahressonderzahlung' },
              { icon: '🌿', title: 'Natur pur', text: 'Eingebettet in die norddeutsche Natur — kurze Wege, frische Luft, echte Ruhe' },
              { icon: '🤝', title: 'Kollegiales Team', text: 'Familiäres Miteinander — die Mehrheit unserer Mitarbeitenden kommt aus der Region' },
              { icon: '📚', title: 'Weiterbildung', text: 'Umfangreiche Fort- und Weiterbildungsangebote, inklusive bezahlter Fortbildungstage' },
              { icon: '👶', title: 'Familie & Beruf', text: 'Flexible Arbeitszeitmodelle, Teilzeit möglich, betriebliche Kinderbetreuung' },
              { icon: '🏠', title: 'Betriebliche Altersvorsorge', text: 'Wir sichern deine Zukunft — mit attraktiver betrieblicher Altersversorgung' },
            ].map(b => (
              <div key={b.title} className="benefit-card">
                <div className="benefit-icon">{b.icon}</div>
                <p className="benefit-title">{b.title}</p>
                <p style={{ fontSize: '0.88rem', color: 'var(--muted)', lineHeight: 1.6 }}>{b.text}</p>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: '3rem' }}>
            <Link href="/info/_de_benefits_" className="btn-primary">Alle Benefits entdecken</Link>
          </div>
        </div>
      </section>

      {/* ── EMPLOYER BRANDING (DRK: "Du bedeutest uns was") ── */}
      <section style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: '420px' }}>
          <div style={{ background: 'var(--primary)', color: 'white', padding: '4rem 3rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <p style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', opacity: 0.7, marginBottom: '1rem' }}>Über uns</p>
            <h2 style={{ fontFamily: 'var(--font-outfit)', fontSize: 'clamp(2rem,4vw,3rem)', fontWeight: 900, lineHeight: 1.1, marginBottom: '1.5rem' }}>
              Arbeitgeber mit<br />
              <span style={{ color: 'var(--yellow)' }}>Charakter.</span>
            </h2>
            <p style={{ opacity: 0.85, lineHeight: 1.8, marginBottom: '2rem', maxWidth: '420px' }}>
              Seit 1876 steht der Enterprise für gelebte Nächstenliebe. 
              Unsere Einrichtungen sind keine Konzerne — sie sind Gemeinschaft. 
              Unsere Mitarbeitenden kommen aus den umliegenden Dörfern und kehren jeden Tag nach Hause zurück.
            </p>
            <Link href="/info/_de_arbeitgeber_" className="btn-secondary" style={{ alignSelf: 'flex-start' }}>
              Mehr über uns erfahren
            </Link>
          </div>
          <div style={{ background: 'var(--teal)', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '4rem 3rem', color: 'white' }}>
            <p style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', opacity: 0.7, marginBottom: '1rem' }}>Schnellbewerbung</p>
            <h3 style={{ fontFamily: 'var(--font-outfit)', fontSize: '1.8rem', fontWeight: 900, marginBottom: '1rem', lineHeight: 1.2 }}>
              Kein passender Job dabei?
            </h3>
            <p style={{ opacity: 0.85, marginBottom: '2rem', lineHeight: 1.7 }}>
              Schick uns deine Initiativbewerbung — wir suchen immer nach engagierten Menschen, 
              die zu uns und unserer Region passen.
            </p>
            <Link href="/bewerben" style={{ background: 'white', color: 'var(--teal)', padding: '0.85rem 1.75rem', borderRadius: '8px', fontWeight: 700, display: 'inline-flex', alignSelf: 'flex-start', fontSize: '0.95rem' }}>
              Initiativ bewerben →
            </Link>
          </div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section style={{ padding: '5rem 0', background: 'var(--background)' }}>
        <div className="container" style={{ maxWidth: '760px' }}>
          <p className="section-label">Häufige Fragen</p>
          <h2 className="section-title">Was Bewerber*innen uns oft fragen</h2>
          <div>
            {[
              { q: 'Kann ich mich initiativ bewerben?', a: 'Ja, absolut! Wir freuen uns über Initiativbewerbungen. Nutze unser Formular — wir melden uns innerhalb von zwei Werktagen.' },
              { q: 'Welche Einrichtungen gehören zum Enterprise?', a: 'Wir betreiben psychiatrische Einrichtungen, Jugendhilfe, Altenpflege und weitere soziale Dienste in Schleswig-Holstein, hauptsächlich rund um Rickling und Bad Segeberg.' },
              { q: 'Sind Teilzeitstellen möglich?', a: 'Ja. Viele unserer Stellen sind auch in Teilzeit zu besetzen. Sprich uns gerne darauf an.' },
              { q: 'Welcher Tarifvertrag gilt?', a: 'Wir vergüten nach dem Kirchlichen Tarifvertrag Diakonie (KTD) inklusive Jahressonderzahlung und betrieblicher Altersversorgung.' },
              { q: 'Gibt es Ausbildungsplätze?', a: 'Ja! Wir bilden in verschiedenen Pflegeberufen, im sozialen Bereich und in der Verwaltung aus. Alle Ausbildungsstellen findest du in unserer Jobbörse.' },
            ].map((item, i) => (
              <details key={i} className="faq-item" style={{ listStyle: 'none' }}>
                <summary className="faq-question" style={{ listStyle: 'none', outline: 'none' }}>
                  <span style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span style={{ color: 'var(--teal)', fontSize: '1.2rem' }}>○</span>
                    {item.q}
                  </span>
                  <span style={{ fontSize: '1.2rem', flexShrink: 0 }}>+</span>
                </summary>
                <p className="faq-answer">{item.a}</p>
              </details>
            ))}
          </div>
          <div style={{ marginTop: '2.5rem', textAlign: 'center' }}>
            <Link href="/info/_de_faq_" className="btn-outline">Vollständige FAQ ansehen</Link>
          </div>
        </div>
      </section>

      {/* ── CONTACT CTA ── */}
      <section style={{ padding: '0 0 5rem', background: 'var(--background)' }}>
        <div className="container">
          <div className="contact-bar" style={{ padding: '3rem', display: 'grid', gridTemplateColumns: '1fr auto', gap: '2rem', alignItems: 'center', borderRadius: '20px' }}>
            <div>
              <h3 style={{ color: 'white', fontFamily: 'var(--font-outfit)', fontSize: '1.6rem', fontWeight: 900, marginBottom: '0.5rem' }}>
                Deine Ansprechpartnerin im Recruiting
              </h3>
              <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.95rem' }}>
                Wir beantworten alle Fragen wochentags zwischen 8:30 und 15:00 Uhr.
              </p>
              <div style={{ marginTop: '1rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                <a href="mailto:karriere@Enterprise.de" style={{ color: 'white', fontWeight: 600, fontSize: '0.9rem' }}>✉️ karriere@Enterprise.de</a>
                <a href="tel:+494326500" style={{ color: 'white', fontWeight: 600, fontSize: '0.9rem' }}>📞 04326 / 500</a>
              </div>
            </div>
            <Link href="/bewerben" className="btn-secondary" style={{ padding: '1rem 2rem', fontSize: '1rem', flexShrink: 0, whiteSpace: 'nowrap' }}>
              Jetzt bewerben
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
