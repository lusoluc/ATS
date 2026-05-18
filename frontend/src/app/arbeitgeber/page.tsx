import Link from 'next/link';
import Image from 'next/image';

export default function ArbeitgeberPage() {
  return (
    <main>
      {/* Hero Section */}
      <section className="hero-section" style={{ minHeight: '60vh' }}>
        <div className="hero-background" style={{ backgroundImage: 'url(/hero_team.png)', backgroundSize: 'cover', backgroundPosition: 'center', opacity: 0.15, filter: 'saturate(1.5)' }}></div>
        <div className="container">
          <h1 className="hero-title animate-fade-in opacity-0">
            Ihr Platz mit Sinn im Herzen Holsteins.
          </h1>
          <p className="hero-subtitle animate-fade-in delay-100 opacity-0">
            Moin! Wir sind der Landesverein. Seit 1875 sind wir hier in Schleswig-Holstein verwurzelt. Wir sind kein anonymer Konzern, sondern ein Team aus Pflegern, Therapeuten und Mutmachern.
          </p>
        </div>
      </section>

      {/* Content Section */}
      <section className="container" style={{ padding: '4rem 2rem', maxWidth: '900px' }}>
        <div className="glass-panel animate-fade-in delay-200 opacity-0" style={{ padding: '3rem', borderRadius: '16px' }}>
          
          <h2 style={{ fontSize: '2rem', marginBottom: '1.5rem', color: 'var(--primary)' }}>Der Vibe: Wir packen an.</h2>
          <p style={{ fontSize: '1.1rem', lineHeight: '1.8', marginBottom: '3rem', opacity: 0.9 }}>
            Bei uns arbeiten über 3.100 Menschen Hand in Hand. Wir reden Klartext, halten zusammen und packen an – auch bei steifer Brise. Suchen Sie sinnstiftende Jobs im echten Norden mit tariflicher Sicherheit? Hier finden Sie Ihre berufliche Heimat.
          </p>

          <h2 style={{ fontSize: '2rem', marginBottom: '1.5rem', color: 'var(--primary)' }}>Warum wir?</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '3rem' }}>
            <div>
              <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>🛡️ Sicherheit</h3>
              <p style={{ opacity: 0.8 }}>Wir bieten faire Bezahlung nach kirchlichem Tarifvertrag (KTD) inklusive Zusatzversorgung.</p>
            </div>
            <div>
              <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>🌱 Wachstum</h3>
              <p style={{ opacity: 0.8 }}>Nutzen Sie unsere Fort- und Weiterbildungen für Ihre Karriere in der Diakonie.</p>
            </div>
            <div>
              <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>🤝 Vielfalt</h3>
              <p style={{ opacity: 0.8 }}>Arbeiten Sie in der Psychiatrie, Suchthilfe oder Seniorenpflege an Standorten wie Rickling oder Neumünster.</p>
            </div>
            <div>
              <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>❤️ Menschlichkeit</h3>
              <p style={{ opacity: 0.8 }}>Wir begegnen uns auf Augenhöhe. Hier zählt Ihre Persönlichkeit genauso wie Ihre Fachlichkeit.</p>
            </div>
          </div>

          <h2 style={{ fontSize: '2rem', marginBottom: '1.5rem', color: 'var(--primary)' }}>Was Sie mitbringen</h2>
          <p style={{ fontSize: '1.1rem', lineHeight: '1.8', marginBottom: '3rem', opacity: 0.9 }}>
            Sie sind Profi in der Pflege, Pädagogik oder Therapie? Oder Sie suchen als Quereinsteiger eine neue Perspektive im Sozialwesen? Wichtig ist uns: Sie haben das Herz am rechten Fleck. Sie arbeiten gerne mit Menschen und schätzen die Verlässlichkeit eines traditionsreichen, diakonischen Trägers in Schleswig-Holstein.
          </p>

          <div style={{ padding: '2rem', backgroundColor: 'var(--secondary)', borderRadius: '12px', textAlign: 'center' }}>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: 'var(--secondary-foreground)' }}>Lust auf Butter bei die Fische?</h3>
            <p style={{ marginBottom: '2rem', opacity: 0.8 }}>Schauen Sie sich unsere offenen Stellen an oder schicken Sie uns eine Initiativbewerbung.</p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <Link href="/jobs" className="btn-primary">Jetzt Stellenangebote finden</Link>
            </div>
          </div>

        </div>
      </section>
    </main>
  );
}
