import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const aboutUsHtml = `
<p class="section-label" style="color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.8rem; margin-bottom: 0.5rem;">Wer wir sind</p>
<h2 class="section-title" style="font-family: var(--font-outfit); font-size: clamp(1.8rem,4vw,2.5rem); font-weight: 900; margin-bottom: 1.5rem; color: var(--foreground); line-height: 1.15;">
  Spitzenmedizin mit Herz & Verstand
</h2>

<p style="font-size: 1.1rem; line-height: 1.7; color: var(--muted); margin-bottom: 2rem;">
  Die <strong>Nordicum Health Group</strong> ist einer der führenden Klinikverbünde in Norddeutschland. Mit über 4.500 Mitarbeitenden an 12 Standorten sichern wir täglich die Maximalversorgung für die Menschen in unserer Region. Doch was uns wirklich auszeichnet, ist nicht nur unsere Größe oder modernste Medizintechnik — sondern die familiäre Atmosphäre, in der wir arbeiten, und die echte Menschlichkeit, die wir unseren Patienten und Kollegen entgegenbringen.
</p>

<!-- STATS INNER CARD -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 1rem; background: var(--surface-2); padding: 1.5rem; border-radius: 12px; margin: 2rem 0; box-shadow: var(--shadow-sm);">
  <div style="text-align: center;">
    <span style="color: var(--primary); font-size: 1.8rem; font-weight: 900; font-family: var(--font-outfit); display: block;">12</span>
    <span style="font-size: 0.8rem; font-weight: 600; color: var(--foreground);">Klinikstandorte</span>
  </div>
  <div style="text-align: center;">
    <span style="color: var(--primary); font-size: 1.8rem; font-weight: 900; font-family: var(--font-outfit); display: block;">4.500+</span>
    <span style="font-size: 0.8rem; font-weight: 600; color: var(--foreground);">Mitarbeitende</span>
  </div>
  <div style="text-align: center;">
    <span style="color: var(--primary); font-size: 1.8rem; font-weight: 900; font-family: var(--font-outfit); display: block;">120.000+</span>
    <span style="font-size: 0.8rem; font-weight: 600; color: var(--foreground);">Patienten / Jahr</span>
  </div>
  <div style="text-align: center;">
    <span style="color: var(--primary); font-size: 1.8rem; font-weight: 900; font-family: var(--font-outfit); display: block;">45</span>
    <span style="font-size: 0.8rem; font-weight: 600; color: var(--foreground);">Fachrichtungen</span>
  </div>
</div>

<div style="border-radius: 16px; overflow: hidden; margin: 2rem 0; box-shadow: var(--shadow);">
  <img src="https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?q=80&w=800&auto=format&fit=crop" alt="Moderner Campus der Nordicum Health Group" style="width:100%; max-height: 320px; object-fit: cover;" />
  <div style="background: var(--surface); padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.8rem; color: var(--muted); text-align: center;">
    Zukunftsorientierte Architektur: Unser moderner Maximalversorger-Campus bietet ideale Arbeitsbedingungen.
  </div>
</div>

<h3 style="font-family: var(--font-outfit); font-size: 1.4rem; font-weight: 800; color: var(--primary); margin-top: 2rem; margin-bottom: 0.75rem;">Unsere drei Säulen: Heilen. Helfen. Entwickeln.</h3>
<p style="color: var(--muted); margin-bottom: 1.5rem; line-height: 1.65;">
  Als Maximalversorger decken wir das gesamte medizinische Spektrum ab. Doch Spitzenmedizin gelingt nur, wenn auch die Arbeitsbedingungen erstklassig sind. Deshalb beruht unser Erfolg auf drei Kernprinzipien:
</p>

<ul style="padding-left: 1.2rem; margin-bottom: 2rem; color: var(--foreground);">
  <li style="margin-bottom: 0.75rem;">
    <strong>Interdisziplinäre Exzellenz:</strong> Wir arbeiten in flachen Hierarchien, in denen die Expertise jeder Berufsgruppe — von der Pflegekraft bis zur Chefärztin — gleichermaßen zählt und respektiert wird.
  </li>
  <li style="margin-bottom: 0.75rem;">
    <strong>Patientenzentrierte Fürsorge:</strong> Wir nehmen uns Zeit. Trotz des Klinikalltags steht die Empathie bei jeder Behandlung an erster Stelle.
  </li>
  <li style="margin-bottom: 0.75rem;">
    <strong>Fortschritt durch Weiterbildung:</strong> Wir sind ein akademisches Lehrkrankenhaus. Die ständige berufliche Entwicklung unserer Teams fördern wir mit 100% Kostenübernahme und bezahlter Freistellung.
  </li>
</ul>

<div style="border-radius: 16px; overflow: hidden; margin: 2rem 0; box-shadow: var(--shadow);">
  <img src="https://images.unsplash.com/photo-1576765608535-5f04d1e3f289?q=80&w=800&auto=format&fit=crop" alt="Medizinische Besprechung auf Augenhöhe" style="width:100%; max-height: 320px; object-fit: cover;" />
  <div style="background: var(--surface); padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.8rem; color: var(--muted); text-align: center;">
    Gemeinsam stark: Tägliche Fallbesprechungen finden interprofessionell und auf Augenhöhe statt.
  </div>
</div>

<h3 style="font-family: var(--font-outfit); font-size: 1.4rem; font-weight: 800; color: var(--primary); margin-top: 2.5rem; margin-bottom: 1rem;">Unsere Hauptstandorte</h3>
<p style="color: var(--muted); margin-bottom: 1.5rem; line-height: 1.65;">
  Unsere Kliniken sind fest in der norddeutschen Landschaft verwurzelt und bieten modernste Arbeitsplätze in Regionen mit exzellenter Lebensqualität:
</p>

<!-- CARDS GRID -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.25rem; margin-bottom: 2rem;">
  <div class="benefit-card" style="background: var(--surface-2); border-radius: 12px; padding: 1.25rem; border-top: 3px solid var(--primary); transition: all 0.2s;">
    <h4 style="font-size: 1.05rem; font-weight: 800; color: var(--primary); margin-bottom: 0.5rem; font-family: var(--font-outfit);">Campus Hamburg-Mitte</h4>
    <p style="font-size: 0.85rem; color: var(--muted); line-height: 1.5;">Das wissenschaftliche Zentrum mit Fokus auf Kardiologie, Onkologie und zertifizierte Organtransplantationen.</p>
  </div>
  <div class="benefit-card" style="background: var(--surface-2); border-radius: 12px; padding: 1.25rem; border-top: 3px solid var(--primary); transition: all 0.2s;">
    <h4 style="font-size: 1.05rem; font-weight: 800; color: var(--primary); margin-bottom: 0.5rem; font-family: var(--font-outfit);">Campus Kiel-Förde</h4>
    <p style="font-size: 0.85rem; color: var(--muted); line-height: 1.5;">Direkt am Wasser gelegen. Unser Exzellenzzentrum für Orthopädie, Neurologie und neurologische Frührehabilitation.</p>
  </div>
  <div class="benefit-card" style="background: var(--surface-2); border-radius: 12px; padding: 1.25rem; border-top: 3px solid var(--primary); transition: all 0.2s;">
    <h4 style="font-size: 1.05rem; font-weight: 800; color: var(--primary); margin-bottom: 0.5rem; font-family: var(--font-outfit);">Campus Lübeck-Ost</h4>
    <p style="font-size: 0.85rem; color: var(--muted); line-height: 1.5;">Bekannt für familienfreundliche Geburtshilfe, Neonatologie und hochpräzise roboter-assistierte Chirurgie.</p>
  </div>
</div>

<div style="background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); color: white; padding: 2rem; border-radius: 16px; text-align: center; margin-top: 3rem; box-shadow: var(--shadow);">
  <h3 style="color: white; font-family: var(--font-outfit); font-size: 1.3rem; font-weight: 800; margin-bottom: 0.75rem;">Bereit für deinen Neustart?</h3>
  <p style="font-size: 0.95rem; opacity: 0.9; margin-bottom: 1.5rem; max-width: 500px; margin-left: auto; margin-right: auto; line-height: 1.6;">
    Finde deinen Platz in einem Team, das dich wertschätzt, fördert und wirklich für dich da ist.
  </p>
  <a href="/jobs" class="btn-secondary" style="text-decoration: none; color: white; border-radius: 8px; padding: 0.7rem 1.5rem; font-weight: bold; display: inline-block;">
    Jetzt Stellenangebote ansehen
  </a>
</div>
`;

const cultureHtml = `
<p class="section-label" style="color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.8rem; margin-bottom: 0.5rem;">Kultur & Werte</p>
<h2 class="section-title" style="font-family: var(--font-outfit); font-size: clamp(1.8rem,4vw,2.5rem); font-weight: 900; margin-bottom: 1.5rem; color: var(--foreground); line-height: 1.15;">
  Wie wir zusammenarbeiten
</h2>

<p style="font-size: 1.1rem; line-height: 1.7; color: var(--muted); margin-bottom: 2.5rem;">
  Echte Teamarbeit lässt sich nicht verordnen — man muss sie leben. Bei der <strong>Nordicum Health Group</strong> haben wir verkrustete Hierarchien abgeschafft. Egal ob erfahrener Chefarzt, frischgebackene Stationsleitung oder Pflegeschüler: Wir begegnen uns auf Augenhöhe und ziehen an einem Strang.
</p>

<!-- VALUES CHUNKS -->
<div style="display: flex; flex-direction: column; gap: 1.5rem; margin-bottom: 3rem;">
  
  <div style="background: var(--surface-2); padding: 1.5rem; border-radius: 12px; border-left: 5px solid var(--primary);">
    <h3 style="margin-top: 0; font-family: var(--font-outfit); font-size: 1.2rem; font-weight: 800; color: var(--primary); margin-bottom: 0.5rem;">
      🤝 1. Augenhöhe & flache Hierarchien
    </h3>
    <p style="font-size: 0.95rem; color: var(--muted); line-height: 1.6; margin-bottom: 0;">
      "Kein Chefarzt-Gehabe" ist bei uns gelebte Realität. In den täglichen Teambesprechungen zählt das beste medizinische und pflegerische Argument, nicht das Namensschild. Wir duzen uns über viele Hierarchieebenen hinweg und pflegen einen wertschätzenden, kollegialen Umgang.
    </p>
  </div>

  <div style="background: var(--surface-2); padding: 1.5rem; border-radius: 12px; border-left: 5px solid var(--green);">
    <h3 style="margin-top: 0; font-family: var(--font-outfit); font-size: 1.2rem; font-weight: 800; color: var(--green-dark); margin-bottom: 0.5rem;">
      📅 2. Verlässliche Freizeit & Dienstplan-Wünsche
    </h3>
    <p style="font-size: 0.95rem; color: var(--muted); line-height: 1.6; margin-bottom: 0;">
      Freizeit muss heilig sein, um gesund zu bleiben. Über unsere digitale Dienstplan-App kannst du deine Freiwünsche einreichen und Dienste unkompliziert mit Kollegen tauschen. Und falls du doch einmal einspringen musst, wird dies bei uns über ein attraktives Prämiensystem extra vergütet.
    </p>
  </div>

  <div style="background: var(--surface-2); padding: 1.5rem; border-radius: 12px; border-left: 5px solid var(--teal);">
    <h3 style="margin-top: 0; font-family: var(--font-outfit); font-size: 1.2rem; font-weight: 800; color: var(--teal); margin-bottom: 0.5rem;">
      🎓 3. Förderung deiner Potenziale
    </h3>
    <p style="font-size: 0.95rem; color: var(--muted); line-height: 1.6; margin-bottom: 0;">
      Wir investieren in deinen Kopf. Ob Fachweiterbildung Intensivpflege, Wundmanagement, Facharztcurriculum oder Studiengänge im Pflegemanagement — wir übernehmen 100% der Fortbildungskosten und stellen dich für Seminare bezahlt frei. Deine Karriere steht bei uns niemals still.
    </p>
  </div>

</div>

<div style="border-radius: 16px; overflow: hidden; margin: 2rem 0; box-shadow: var(--shadow);">
  <img src="https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?q=80&w=800&auto=format&fit=crop" alt="Unser Team im Gemeinschaftsraum" style="width:100%; max-height: 320px; object-fit: cover;" />
  <div style="background: var(--surface); padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.8rem; color: var(--muted); text-align: center;">
    Lachen gehört dazu: Eine positive und fröhliche Stimmung im Team ist uns genauso wichtig wie fachliche Perfektion.
  </div>
</div>

<!-- TESTIMONIAL BLOCK -->
<div style="background: var(--surface-2); border-radius: 16px; padding: 2rem; margin: 3rem 0; border: 1px solid var(--border); box-shadow: var(--shadow-sm); position: relative;">
  <span style="font-size: 4rem; color: var(--primary); opacity: 0.15; position: absolute; top: -10px; left: 15px; font-family: Georgia, serif;">“</span>
  <p style="font-size: 1.05rem; font-style: italic; line-height: 1.65; color: var(--foreground); position: relative; z-index: 1; margin-bottom: 1.5rem; padding-left: 1rem;">
    Bei Nordicum Health habe ich zum ersten Mal erlebt, dass meine Meinung als Krankenpfleger genauso viel zählt wie die der Ärzte. Wir arbeiten wirklich Hand in Hand, besprechen Herausforderungen gemeinsam auf Augenhöhe und lachen viel zusammen. Man wird als Mensch gesehen und nicht als austauschbare Nummer.
  </p>
  <div style="display: flex; align-items: center; gap: 1rem; padding-left: 1rem;">
    <div style="width: 50px; height: 50px; border-radius: 50%; overflow: hidden; box-shadow: var(--shadow-sm);">
      <img src="https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?q=80&w=150&auto=format&fit=crop" alt="Tobias Schmidt" style="width: 100%; height: 100%; object-fit: cover;" />
    </div>
    <div>
      <strong style="color: var(--primary); font-size: 0.95rem; display: block;">Tobias Schmidt</strong>
      <span style="font-size: 0.8rem; color: var(--muted);">Fachkrankenpfleger für Intensivpflege am Campus Lübeck-Ost</span>
    </div>
  </div>
</div>

<h3 style="font-family: var(--font-outfit); font-size: 1.4rem; font-weight: 800; color: var(--primary); margin-top: 2.5rem; margin-bottom: 1rem;">Häufige Fragen zu unserer Zusammenarbeit</h3>

<!-- FAQ ACCORDION -->
<div style="display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 3rem;">
  
  <details style="border-bottom: 1px solid var(--border); padding: 1rem 0; outline: none;">
    <summary style="font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 1rem; color: var(--foreground); list-style: none; outline: none;">
      <span>Wie geht ihr mit Fehlern oder Stresssituationen um?</span>
      <span style="color: var(--primary); font-size: 1.3rem; font-weight: bold;">+</span>
    </summary>
    <p style="margin-top: 0.75rem; color: var(--muted); line-height: 1.6; font-size: 0.9rem; padding-left: 0.5rem;">
      Fehler passieren überall, wo Menschen arbeiten. Bei uns wird niemand beschuldigt oder bloßgestellt. Wir nutzen ein etabliertes, anonymes Fehlermeldesystem (CIRS) und arbeiten in interdisziplinären Runden kontinuierlich daran, Prozesse sicherer und stressfreier zu gestalten. Nach harten Diensten bieten wir zudem gezieltes Coaching und Supervisionen an.
    </p>
  </details>

  <details style="border-bottom: 1px solid var(--border); padding: 1rem 0; outline: none;">
    <summary style="font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 1rem; color: var(--foreground); list-style: none; outline: none;">
      <span>Gibt es Aufstiegsmöglichkeiten auch für Teilzeitkräfte?</span>
      <span style="color: var(--primary); font-size: 1.3rem; font-weight: bold;">+</span>
    </summary>
    <p style="margin-top: 0.75rem; color: var(--muted); line-height: 1.6; font-size: 0.9rem; padding-left: 0.5rem;">
      Ja, absolut! Wir glauben, dass Führung und Karriere keine Vollzeitpräsenz erfordern. Bei uns arbeiten über 40% der Team- und Stationsleitungen in Teilzeitmodellen oder nutzen das Modell des "Job-Sharings", bei dem sich zwei Führungskräfte eine Position teilen.
    </p>
  </details>

  <details style="border-bottom: 1px solid var(--border); padding: 1rem 0; outline: none;">
    <summary style="font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 1rem; color: var(--foreground); list-style: none; outline: none;">
      <span>Wie fördert ihr das Teambuilding abseits der Arbeit?</span>
      <span style="color: var(--primary); font-size: 1.3rem; font-weight: bold;">+</span>
    </summary>
    <p style="margin-top: 0.75rem; color: var(--muted); line-height: 1.6; font-size: 0.9rem; padding-left: 0.5rem;">
      Wir unterstützen gemeinsame Team-Events mit einem jährlichen Teambudget für jede Abteilung. Ob Grillabende, Kanutouren, Drachenbootrennen oder gemeinsame Teilnahmen an Firmenläufen — wir schaffen Gelegenheiten, sich als Menschen abseits des stressigen Klinikalltags noch besser kennenzulernen.
    </p>
  </details>

</div>

<div style="background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); color: white; padding: 2rem; border-radius: 16px; text-align: center; margin-top: 3rem; box-shadow: var(--shadow);">
  <h3 style="color: white; font-family: var(--font-outfit); font-size: 1.3rem; font-weight: 800; margin-bottom: 0.75rem;">Lerne uns persönlich kennen</h3>
  <p style="font-size: 0.95rem; opacity: 0.9; margin-bottom: 1.5rem; max-width: 500px; margin-left: auto; margin-right: auto; line-height: 1.6;">
    Hospitiere unverbindlich einen Tag bei uns, wirke im Team mit und spüre selbst, was unsere Kultur so besonders macht!
  </p>
  <a href="/bewerben" class="btn-secondary" style="text-decoration: none; color: white; border-radius: 8px; padding: 0.7rem 1.5rem; font-weight: bold; display: inline-block;">
    Schnuppertag vereinbaren
  </a>
</div>
`;

async function main() {
  console.log('Seeding premium subpages (ueber-uns, kultur) into database...');

  await prisma.page.upsert({
    where: { slug: 'ueber-uns' },
    update: {
      title: 'Wer wir sind',
      content: aboutUsHtml,
      status: 'published',
      navEnabled: true,
      navLabel: 'Über uns',
      navParent: 'beruf-karriere',
      navOrder: 0,
      metaDesc: 'Die Nordicum Health Group ist Norddeutschlands führender Klinikverbund für Spitzenmedizin mit Herz und Verstand. Erfahre mehr über unsere 12 Standorte und 4.500 Kollegen.'
    },
    create: {
      title: 'Wer wir sind',
      slug: 'ueber-uns',
      content: aboutUsHtml,
      status: 'published',
      navEnabled: true,
      navLabel: 'Über uns',
      navParent: 'beruf-karriere',
      navOrder: 0,
      metaDesc: 'Die Nordicum Health Group ist Norddeutschlands führender Klinikverbund für Spitzenmedizin mit Herz und Verstand. Erfahre mehr über unsere 12 Standorte und 4.500 Kollegen.'
    }
  });
  console.log('✅ Upserted ueber-uns page!');

  await prisma.page.upsert({
    where: { slug: 'kultur' },
    update: {
      title: 'Kultur & Werte',
      content: cultureHtml,
      status: 'published',
      navEnabled: true,
      navLabel: 'Kultur & Werte',
      navParent: 'beruf-karriere',
      navOrder: 1,
      metaDesc: 'Erfahre mehr über die einzigartige Unternehmenskultur der Nordicum Health Group. Warum bei uns Augenhöhe, flache Hierarchien und Dienstpläne nach Wunsch gelebte Praxis sind.'
    },
    create: {
      title: 'Kultur & Werte',
      slug: 'kultur',
      content: cultureHtml,
      status: 'published',
      navEnabled: true,
      navLabel: 'Kultur & Werte',
      navParent: 'beruf-karriere',
      navOrder: 1,
      metaDesc: 'Erfahre mehr über die einzigartige Unternehmenskultur der Nordicum Health Group. Warum bei uns Augenhöhe, flache Hierarchien und Dienstpläne nach Wunsch gelebte Praxis sind.'
    }
  });
  console.log('✅ Upserted kultur page!');
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
