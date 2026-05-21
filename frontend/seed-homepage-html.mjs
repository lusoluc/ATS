import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const homeHtml = `
<!-- HERO -->
<section class="hero-section" style="padding: 6rem 0 4rem; position: relative; overflow: hidden; background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 50%, #2a0d40 100%); color: white;">
  <div class="container" style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 4rem; align-items: center;">
    <div class="animate-fade-in">
      <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
        <p class="section-label" style="margin-bottom: 0; color: var(--yellow);">Nordicum Health Group</p>
        <div style="display: flex; align-items: center; gap: 0.3rem; background: rgba(133,172,55,0.25); color: #c4f2bb; padding: 0.3rem 0.6rem; border-radius: 20px; font-size: 0.75rem; font-weight: bold;">
          ⭐ 4.6 Kununu Score
        </div>
      </div>
      <h1 class="hero-title" style="font-size: clamp(2.5rem, 5vw, 4.2rem); font-family: var(--font-outfit); font-weight: 900; line-height: 1.05; margin-bottom: 1.5rem; color: white;">
        Gemeinsam für
        <span class="accent" style="display: block; margin-top: 0.5rem; color: var(--yellow);">die Gesundheit.</span>
      </h1>
      <p class="hero-subtitle" style="font-size: 1.2rem; opacity: 0.85; max-width: 540px; margin-bottom: 2.5rem; line-height: 1.7;">
        Wir sind einer der führenden Maximalversorger in Norddeutschland. Modernste Medizin, familiäre Teams und echte Wertschätzung für deine Arbeit.
      </p>
      <div class="hero-actions" style="display: flex; gap: 1rem; flex-wrap: wrap;">
        <a href="/jobs" class="btn-primary" style="font-size: 1.05rem; padding: 0.9rem 2.2rem; box-shadow: 0 8px 25px rgba(99,37,116, 0.4); text-decoration: none; color: white; border-radius: 8px;">
          Jetzt offene Stellen finden
        </a>
        <a href="/bewerben" class="btn-outline" style="font-size: 1.05rem; padding: 0.85rem 2rem; border: 2px solid white; color: white; text-decoration: none; border-radius: 8px;">
          1-Klick Initiativbewerbung
        </a>
      </div>
    </div>
    <div class="animate-fade-in hide-mobile" style="position: relative;">
      <div style="border-radius: 24px; overflow: hidden; aspect-ratio: 4/5; position: relative; box-shadow: var(--shadow-lg);">
        <img src="https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=600&auto=format&fit=crop" alt="Pflegeteam Nordicum Health im Einsatz" style="width: 100%; height: 100%; object-fit: cover;" />
        <div style="position: absolute; bottom: 1.5rem; left: 1.5rem; right: 1.5rem; background: rgba(255,255,255,0.95); padding: 1.25rem 1.5rem; border-radius: 16px; backdrop-filter: blur(10px); color: black;">
          <p style="font-weight: 800; color: var(--primary); font-size: 0.95rem; display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
            <span>📍 Campus Hamburg-Mitte</span>
            <span style="font-size: 1.2rem;">👩‍⚕️</span>
          </p>
          <p style="font-size: 0.85rem; color: var(--muted); line-height: 1.4;">
            "Das beste Team, das ich je hatte. Hier wird zusammen gelacht und gearbeitet."<br/>
            <strong style="color: var(--foreground); margin-top: 0.3rem; display: block; font-weight: 700;">— Sarah, Stationsleitung</strong>
          </p>
        </div>
      </div>
    </div>
  </div>
  <div style="height: 60px; background: var(--background); margin-top: 4rem; clip-path: ellipse(60% 100% at 50% 100%);"></div>
</section>

<!-- STATS BAR -->
<section class="stat-bar" style="margin-top: -2rem; z-index: 10; position: relative; background: var(--teal); padding: 1.5rem 0;">
  <div class="container">
    <div class="stat-bar-inner" style="display: flex; flex-wrap: wrap; justify-content: space-around; background: white; border-radius: 16px; box-shadow: var(--shadow); color: var(--foreground);">
      <div class="stat-item" style="display: flex; flex-direction: column; align-items: center; padding: 1.5rem 1rem;">
        <span class="stat-number" style="color: var(--primary); font-size: 2.3rem; font-weight: 900; font-family: var(--font-outfit);">4.500+</span>
        <span class="stat-label" style="color: var(--foreground); font-weight: 600; margin-top: 0.3rem; font-size: 0.85rem;">Mitarbeitende</span>
      </div>
      <div class="stat-item" style="display: flex; flex-direction: column; align-items: center; padding: 1.5rem 1rem;">
        <span class="stat-number" style="color: var(--primary); font-size: 2.3rem; font-weight: 900; font-family: var(--font-outfit);">12</span>
        <span class="stat-label" style="color: var(--foreground); font-weight: 600; margin-top: 0.3rem; font-size: 0.85rem;">Klinikstandorte</span>
      </div>
      <div class="stat-item" style="display: flex; flex-direction: column; align-items: center; padding: 1.5rem 1rem;">
        <span class="stat-number" style="color: var(--primary); font-size: 2.3rem; font-weight: 900; font-family: var(--font-outfit);">30 Tage</span>
        <span class="stat-label" style="color: var(--foreground); font-weight: 600; margin-top: 0.3rem; font-size: 0.85rem;">Urlaub (KTD Tarif)</span>
      </div>
      <div class="stat-item" style="display: flex; flex-direction: column; align-items: center; padding: 1.5rem 1rem;">
        <span class="stat-number" style="color: var(--primary); font-size: 2.3rem; font-weight: 900; font-family: var(--font-outfit);">Top 100</span>
        <span class="stat-label" style="color: var(--foreground); font-weight: 600; margin-top: 0.3rem; font-size: 0.85rem;">Arbeitgeber 2026</span>
      </div>
    </div>
  </div>
</section>

<!-- TARGET GROUPS -->
<section style="padding: 5rem 0; background: var(--background);">
  <div class="container">
    <div style="text-align: center; margin-bottom: 3.5rem;">
      <p class="section-label" style="color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.8rem; margin-bottom: 0.5rem;">Dein Einstieg bei uns</p>
      <h2 class="section-title" style="font-family: var(--font-outfit); font-size: 2.3rem; font-weight: 900; margin-bottom: 1rem; color: var(--foreground);">Wofür schlägt dein Herz?</h2>
      <p style="font-size: 1.1rem; color: var(--muted); max-width: 600px; margin: 0 auto;">Finde genau den Bereich, der zu deiner Expertise und deinen Lebenszielen passt.</p>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem;">
      <a href="/jobs?category=pflege" class="card" style="background: white; padding: 2rem; border-radius: 16px; text-decoration: none; color: inherit; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 1rem; box-shadow: var(--shadow-sm); transition: all 0.2s;">
        <div style="font-size: 2.5rem; background: var(--background); width: 70px; height: 70px; display: flex; align-items: center; justify-content: center; border-radius: 16px;">🩺</div>
        <h3 style="font-size: 1.35rem; font-weight: 800; font-family: var(--font-outfit); margin-top: 0.5rem; color: var(--foreground);">Pflege & Betreuung</h3>
        <p style="color: var(--muted); line-height: 1.6; font-size: 0.95rem;">Stationär, ambulant oder Intensiv – werde Teil der größten Pflege-Community im Norden.</p>
        <span style="color: var(--primary); font-weight: 700; margin-top: auto; display: flex; align-items: center; gap: 0.5rem; font-size: 0.95rem;">Jobs entdecken <span>→</span></span>
      </a>
      <a href="/jobs?category=medizin" class="card" style="background: white; padding: 2rem; border-radius: 16px; text-decoration: none; color: inherit; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 1rem; box-shadow: var(--shadow-sm); transition: all 0.2s;">
        <div style="font-size: 2.5rem; background: var(--background); width: 70px; height: 70px; display: flex; align-items: center; justify-content: center; border-radius: 16px;">⚕️</div>
        <h3 style="font-size: 1.35rem; font-weight: 800; font-family: var(--font-outfit); margin-top: 0.5rem; color: var(--foreground);">Medizin & Therapie</h3>
        <p style="color: var(--muted); line-height: 1.6; font-size: 0.95rem;">Modernste Medizintechnik trifft auf exzellente Fallbesprechungen. Für Ärzte und Therapeuten.</p>
        <span style="color: var(--primary); font-weight: 700; margin-top: auto; display: flex; align-items: center; gap: 0.5rem; font-size: 0.95rem;">Jobs entdecken <span>→</span></span>
      </a>
      <a href="/jobs?category=verwaltung" class="card" style="background: white; padding: 2rem; border-radius: 16px; text-decoration: none; color: inherit; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 1rem; box-shadow: var(--shadow-sm); transition: all 0.2s;">
        <div style="font-size: 2.5rem; background: var(--background); width: 70px; height: 70px; display: flex; align-items: center; justify-content: center; border-radius: 16px;">💻</div>
        <h3 style="font-size: 1.35rem; font-weight: 800; font-family: var(--font-outfit); margin-top: 0.5rem; color: var(--foreground);">IT & Verwaltung</h3>
        <p style="color: var(--muted); line-height: 1.6; font-size: 0.95rem;">Die Infrastruktur am Laufen halten. Digitalisierung im Gesundheitswesen aktiv mitgestalten.</p>
        <span style="color: var(--primary); font-weight: 700; margin-top: auto; display: flex; align-items: center; gap: 0.5rem; font-size: 0.95rem;">Jobs entdecken <span>→</span></span>
      </a>
      <a href="/jobs?category=ausbildung" class="card" style="background: white; padding: 2rem; border-radius: 16px; text-decoration: none; color: inherit; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 1rem; box-shadow: var(--shadow-sm); transition: all 0.2s;">
        <div style="font-size: 2.5rem; background: var(--background); width: 70px; height: 70px; display: flex; align-items: center; justify-content: center; border-radius: 16px;">🎓</div>
        <h3 style="font-size: 1.35rem; font-weight: 800; font-family: var(--font-outfit); margin-top: 0.5rem; color: var(--foreground);">Ausbildung & Studium</h3>
        <p style="color: var(--muted); line-height: 1.6; font-size: 0.95rem;">Starte deine Karriere mit unseren exzellenten Dual-Programmen und Mentoring.</p>
        <span style="color: var(--primary); font-weight: 700; margin-top: auto; display: flex; align-items: center; gap: 0.5rem; font-size: 0.95rem;">Jobs entdecken <span>→</span></span>
      </a>
    </div>
  </div>
</section>

<!-- LIVE JOBS LIST SECTION -->
<section style="padding: 3rem 0 5rem; background: var(--background);">
  <div class="container">
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2.5rem; flex-wrap: wrap; gap: 1rem;">
      <div>
        <p class="section-label" style="color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.8rem; margin-bottom: 0.5rem;">Offene Stellen</p>
        <h2 class="section-title" style="font-family: var(--font-outfit); font-size: 2.3rem; font-weight: 900; margin-bottom: 0; color: var(--foreground);">Neu veröffentlicht</h2>
      </div>
      <a href="/jobs" class="btn-outline" style="text-decoration: none; border-radius: 8px;">Alle Stellen durchsuchen →</a>
    </div>
    
    <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1.5rem;">
      {{LIVE_JOBS_LIST}}
    </div>
  </div>
</section>

<!-- BENEFITS -->
<section style="padding: 5rem 0; background: var(--background);">
  <div class="container">
    <div style="text-align: center; margin-bottom: 3.5rem;">
      <p class="section-label" style="color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.8rem; margin-bottom: 0.5rem;">Was wir bieten</p>
      <h2 class="section-title" style="font-family: var(--font-outfit); font-size: 2.3rem; font-weight: 900; margin-bottom: 1rem; color: var(--foreground);">Deine Arbeit, unser Respekt.</h2>
      <p style="font-size: 1.1rem; color: var(--muted); max-width: 600px; margin: 0 auto;">Wir investieren in dich. Entdecke Benefits, die wirklich einen Unterschied in deinem Alltag machen.</p>
    </div>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">
      <div class="benefit-card" style="background: var(--surface-2); border-radius: 16px; padding: 2rem; border-top: 4px solid var(--primary); transition: all 0.2s;">
        <div class="benefit-icon" style="font-size: 2.5rem; margin-bottom: 1rem;">💰</div>
        <h3 class="benefit-title" style="font-size: 1.15rem; font-weight: 800; margin-bottom: 0.5rem; color: var(--primary); font-family: var(--font-outfit);">Tarifliche Top-Vergütung</h3>
        <p style="color: var(--muted); font-size: 0.95rem; line-height: 1.6;">Nach KTD-Tarifvertrag. Inklusive 13. Monatsgehalt, pflegebezogenen Zulagen und pünktlicher Gehaltsentwicklung.</p>
      </div>
      <div class="benefit-card" style="background: var(--surface-2); border-radius: 16px; padding: 2rem; border-top: 4px solid var(--primary); transition: all 0.2s;">
        <div class="benefit-icon" style="font-size: 2.5rem; margin-bottom: 1rem;">🏖️</div>
        <h3 class="benefit-title" style="font-size: 1.15rem; font-weight: 800; margin-bottom: 0.5rem; color: var(--primary); font-family: var(--font-outfit);">30 Tage Urlaub + Flexzeit</h3>
        <p style="color: var(--muted); font-size: 0.95rem; line-height: 1.6;">Damit du abschalten kannst. Flexible Dienstpläne per App und garantierte freie Wochenenden.</p>
      </div>
      <div class="benefit-card" style="background: var(--surface-2); border-radius: 16px; padding: 2rem; border-top: 4px solid var(--primary); transition: all 0.2s;">
        <div class="benefit-icon" style="font-size: 2.5rem; margin-bottom: 1rem;">🚴</div>
        <h3 class="benefit-title" style="font-size: 1.15rem; font-weight: 800; margin-bottom: 0.5rem; color: var(--primary); font-family: var(--font-outfit);">E-Bike Leasing & Mobilität</h3>
        <p style="color: var(--muted); font-size: 0.95rem; line-height: 1.6;">JobRad für dich und deinen Partner, plus 100% Zuschuss zum Deutschlandticket für alle Standorte.</p>
      </div>
      <div class="benefit-card" style="background: var(--surface-2); border-radius: 16px; padding: 2rem; border-top: 4px solid var(--primary); transition: all 0.2s;">
        <div class="benefit-icon" style="font-size: 2.5rem; margin-bottom: 1rem;">📈</div>
        <h3 class="benefit-title" style="font-size: 1.15rem; font-weight: 800; margin-bottom: 0.5rem; color: var(--primary); font-family: var(--font-outfit);">Garantierte Weiterbildung</h3>
        <p style="color: var(--muted); font-size: 0.95rem; line-height: 1.6;">Wir finanzieren deine Karriere: Fachweiterbildungen, Führungskräfte-Training und Kongressbesuche.</p>
      </div>
      <div class="benefit-card" style="background: var(--surface-2); border-radius: 16px; padding: 2rem; border-top: 4px solid var(--primary); transition: all 0.2s;">
        <div class="benefit-icon" style="font-size: 2.5rem; margin-bottom: 1rem;">👶</div>
        <h3 class="benefit-title" style="font-size: 1.15rem; font-weight: 800; margin-bottom: 0.5rem; color: var(--primary); font-family: var(--font-outfit);">Familie & Beruf</h3>
        <p style="color: var(--muted); font-size: 0.95rem; line-height: 1.6;">Betriebs-Kitas an 4 Standorten, Notfallbetreuung und flexible Teilzeit-Modelle (auch für Führungskräfte).</p>
      </div>
      <div class="benefit-card" style="background: var(--surface-2); border-radius: 16px; padding: 2rem; border-top: 4px solid var(--primary); transition: all 0.2s;">
        <div class="benefit-icon" style="font-size: 2.5rem; margin-bottom: 1rem;">👵</div>
        <h3 class="benefit-title" style="font-size: 1.15rem; font-weight: 800; margin-bottom: 0.5rem; color: var(--primary); font-family: var(--font-outfit);">Betriebliche Altersvorsorge</h3>
        <p style="color: var(--muted); font-size: 0.95rem; line-height: 1.6;">Sichere Zukunft: Wir zahlen 5,4% deines Bruttogehalts zusätzlich in deine Pensionskasse.</p>
      </div>
    </div>
  </div>
</section>

<!-- EMPLOYER BRANDING (AUGENHÖHE) -->
<section style="padding: 5rem 0; background: var(--background);">
  <div class="container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 4rem; align-items: center;">
    <div>
      <p class="section-label" style="color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.8rem; margin-bottom: 0.5rem;">Kultur & Alltag</p>
      <h2 class="section-title" style="font-family: var(--font-outfit); font-size: 2.3rem; font-weight: 900; margin-bottom: 1.5rem; color: var(--foreground);">
        Wir arbeiten auf
        <span style="color: var(--primary); display: block; margin-top: 0.3rem;">Augenhöhe.</span>
      </h2>
      <p style="color: var(--muted); font-size: 1.05rem; line-height: 1.7; margin-bottom: 2rem;">
        Egal ob Chefarzt oder Pflegeschüler: Bei Nordicum Health zählen die Argumente, nicht die Hierarchie. Unser Leitbild basiert auf bedingungsloser Teamarbeit und radikaler Transparenz im klinischen Alltag.
      </p>
      <a href="/info/kultur" class="btn-primary" style="text-decoration: none; color: white;">Lerne unser Team kennen</a>
    </div>
    <div style="position: relative; border-radius: 24px; overflow: hidden; aspect-ratio: 16/10; box-shadow: var(--shadow-lg);">
      <img src="https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?q=80&w=800&auto=format&fit=crop" alt="Team auf Augenhöhe" style="width: 100%; height: 100%; object-fit: cover;" />
    </div>
  </div>
</section>

<!-- FAQ + CONTACT -->
<section style="padding: 5rem 0 6rem; background: var(--background);">
  <div class="container" style="display: grid; grid-template-columns: 1.5fr 1fr; gap: 4rem;">
    <div>
      <p class="section-label" style="color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.8rem; margin-bottom: 0.5rem;">Häufige Fragen</p>
      <h2 class="section-title" style="font-family: var(--font-outfit); font-size: 2.3rem; font-weight: 900; margin-bottom: 2rem; color: var(--foreground);">Transparenz vor der Bewerbung</h2>
      
      <div style="margin-top: 2rem;">
        <details class="faq-item" style="border-bottom: 1px solid var(--border); padding: 1.25rem 0;">
          <summary class="faq-question" style="font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 1.05rem; color: var(--foreground); list-style: none; outline: none;">
            <span>Wie läuft der Bewerbungsprozess (One-Click) ab?</span>
            <span style="color: var(--primary); font-size: 1.5rem; font-weight: 300;">+</span>
          </summary>
          <p class="faq-answer" style="margin-top: 0.75rem; color: var(--muted); line-height: 1.7; font-size: 0.95rem; padding-right: 2rem;">
            Wir haben den Prozess radikal vereinfacht: Klicke auf "Bewerben", lade deinen Lebenslauf hoch (oder verlinke dein LinkedIn-Profil). Kein Anschreiben nötig. Wir rufen dich innerhalb von 48 Stunden an!
          </p>
        </details>
        <details class="faq-item" style="border-bottom: 1px solid var(--border); padding: 1.25rem 0;">
          <summary class="faq-question" style="font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 1.05rem; color: var(--foreground); list-style: none; outline: none;">
            <span>Gibt es Hospitations-Tage?</span>
            <span style="color: var(--primary); font-size: 1.5rem; font-weight: 300;">+</span>
          </summary>
          <p class="faq-answer" style="margin-top: 0.75rem; color: var(--muted); line-height: 1.7; font-size: 0.95rem; padding-right: 2rem;">
            Ja! Nach einem kurzen Telefon-Interview laden wir dich gerne zu einem bezahlten Schnuppertag (Hospitation) auf deiner zukünftigen Station ein. So lernst du das Team ungefiltert kennen.
          </p>
        </details>
        <details class="faq-item" style="border-bottom: 1px solid var(--border); padding: 1.25rem 0;">
          <summary class="faq-question" style="font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 1.05rem; color: var(--foreground); list-style: none; outline: none;">
            <span>Wie funktioniert das Onboarding?</span>
            <span style="color: var(--primary); font-size: 1.5rem; font-weight: 300;">+</span>
          </summary>
          <p class="faq-answer" style="margin-top: 0.75rem; color: var(--muted); line-height: 1.7; font-size: 0.95rem; padding-right: 2rem;">
            Du erhältst in den ersten 6 Monaten einen festen Mentor. Zudem gibt es strukturierte Einarbeitungskonzepte für jede Abteilung, damit du niemals ins kalte Wasser geworfen wirst.
          </p>
        </details>
        <details class="faq-item" style="border-bottom: 1px solid var(--border); padding: 1.25rem 0;">
          <summary class="faq-question" style="font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 1.05rem; color: var(--foreground); list-style: none; outline: none;">
            <span>Ist eine Initiativbewerbung sinnvoll?</span>
            <span style="color: var(--primary); font-size: 1.5rem; font-weight: 300;">+</span>
          </summary>
          <p class="faq-answer" style="margin-top: 0.75rem; color: var(--muted); line-height: 1.7; font-size: 0.95rem; padding-right: 2rem;">
            Absolut. Über 30% unserer Einstellungen entstehen durch Initiativbewerbungen. Unser Recruiting-Team findet intern genau den richtigen Platz für deine Fähigkeiten.
          </p>
        </details>
      </div>
    </div>
    
    <div>
      <div style="background: white; padding: 2.5rem; border-radius: 24px; border: 1px solid var(--border); box-shadow: var(--shadow); position: sticky; top: 100px; color: var(--foreground);">
        <div style="width: 80px; height: 80px; border-radius: 50%; overflow: hidden; margin-bottom: 1.5rem;">
          <img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=200&auto=format&fit=crop" alt="Anna Müller" style="width: 100%; height: 100%; object-fit: cover;" />
        </div>
        <h3 style="font-size: 1.35rem; font-weight: 800; margin-bottom: 0.2rem; font-family: var(--font-outfit);">Anna Müller</h3>
        <p style="color: var(--primary); font-weight: 600; font-size: 0.9rem; margin-bottom: 1.5rem;">Leitung Talent Acquisition</p>
        <p style="color: var(--muted); line-height: 1.6; margin-bottom: 2rem; font-size: 0.95rem;">
          "Du hast Fragen zum Gehalt, zum Team oder zum Ablauf? Schreib mir einfach direkt auf WhatsApp oder ruf kurz durch. Wir klären das ganz unkompliziert!"
        </p>
        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
          <a href="tel:0401234560" class="btn-primary" style="display: flex; justify-content: center; gap: 0.5rem; padding: 0.85rem; text-decoration: none; border-radius: 8px; color: white;">
            📞 040 / 123 456 - 0
          </a>
          <a href="https://wa.me/4912345678" class="btn-outline" style="display: flex; justify-content: center; gap: 0.5rem; padding: 0.85rem; color: #25D366; border-color: #25D366; text-decoration: none; border-radius: 8px; font-weight: 600;">
            💬 WhatsApp schreiben
          </a>
        </div>
      </div>
    </div>
  </div>
</section>
`;

async function seed() {
  console.log('Seeding beautiful new responsive HTML homepage content into database...');
  await prisma.page.upsert({
    where: { slug: 'home' },
    update: {
      content: homeHtml,
      status: 'published' // Ensure it is published
    },
    create: {
      title: 'Startseite',
      slug: 'home',
      content: homeHtml,
      status: 'published',
      navEnabled: false
    }
  });
  console.log('✅ Homepage seed success!');
}

seed()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
