import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const homeJson = {
  content: [
    { type: "HomeHero", props: {
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
      author: '— Sarah, Stationsleitung',
      id: "HomeHero-1"
    }},
    { type: "HomeStatBar", props: {
      stats: [
        { num: '4.500+', label: 'Mitarbeitende' },
        { num: '12',     label: 'Klinikstandorte' },
        { num: '30 Tage', label: 'Urlaub (KTD Tarif)' },
        { num: 'Top 100',   label: 'Arbeitgeber 2026' }
      ],
      id: "HomeStatBar-1"
    }},
    { type: "HomeTargetGroups", props: {
      label: 'Dein Einstieg bei uns',
      title: 'Wofür schlägt dein Herz?',
      subtitle: 'Finde genau den Bereich, der zu deiner Expertise und deinen Lebenszielen passt.',
      groups: [
        { title: 'Pflege & Betreuung', icon: '🩺', desc: 'Stationär, ambulant oder Intensiv – werde Teil der größten Pflege-Community im Norden.', link: '/jobs?category=pflege' },
        { title: 'Medizin & Therapie', icon: '⚕️', desc: 'Modernste Medizintechnik trifft auf exzellente Fallbesprechungen. Für Ärzte und Therapeuten.', link: '/jobs?category=medizin' },
        { title: 'IT & Verwaltung', icon: '💻', desc: 'Die Infrastruktur am Laufen halten. Digitalisierung im Gesundheitswesen aktiv mitgestalten.', link: '/jobs?category=verwaltung' },
        { title: 'Ausbildung & Studium', icon: '🎓', desc: 'Starte deine Karriere mit unseren exzellenten Dual-Programmen und Mentoring.', link: '/jobs?category=ausbildung' }
      ],
      id: "HomeTargetGroups-1"
    }},
    { type: "HomeJobsTeaser", props: {
      label: 'Offene Stellen',
      title: 'Neu veröffentlicht',
      btnText: 'Alle 142 Jobs durchsuchen →',
      btnUrl: '/jobs',
      jobs: [
        { title: 'Gesundheits- und Krankenpfleger (m/w/d) Intensivstation', location: 'Campus Hamburg-Mitte', category: 'Pflege', type: 'Vollzeit / Teilzeit', salary: 'KTD Tarif + Zulagen', url: '/jobs/1' },
        { title: 'Facharzt (m/w/d) für Psychiatrie und Psychotherapie', location: 'Klinik Norderstedt', category: 'Medizin', type: 'Vollzeit', salary: 'Chefarzt-Bonusmodell', url: '/jobs/2' },
        { title: 'Senior IT-Systemadministrator (m/w/d) Infrastruktur', location: 'Zentrale Kiel', category: 'IT & Technik', type: 'Vollzeit (Hybrid)', salary: 'Bis zu 80k', url: '/jobs/3' },
        { title: 'Auszubildende (m/w/d) Pflegefachfrau/-mann', location: 'Campus Hamburg-Mitte', category: 'Ausbildung', type: 'Ausbildung', salary: '1.300€ im 1. Jahr', url: '/jobs/4' },
      ],
      id: "HomeJobsTeaser-1"
    }},
    { type: "HomeBenefits", props: {
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
      ],
      id: "HomeBenefits-1"
    }},
    { type: "HomeEmployerBranding", props: {
      label: 'Kultur & Alltag',
      titlePrefix: 'Wir arbeiten auf',
      titleHighlight: 'Augenhöhe.',
      text: 'Egal ob Chefarzt oder Pflegeschüler: Bei Nordicum Health zählen die Argumente, nicht die Hierarchie. Unser Leitbild basiert auf bedingungsloser Teamarbeit und radikaler Transparenz im klinischen Alltag.',
      btnText: 'Lerne unser Team kennen',
      btnUrl: '/info/kultur',
      videoText: 'Play: Ein Tag auf Station 4',
      bgImage: '/kultur_augenhoehe.png',
      id: "HomeEmployerBranding-1"
    }},
    { type: "HomeFAQ", props: {
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
      contactWhatsapp: '4912345678',
      id: "HomeFAQ-1"
    }}
  ],
  root: { props: { title: "Startseite" } },
  zones: {}
};

async function run() {
  await prisma.page.upsert({
    where: { slug: 'home' },
    update: {
      status: 'system',
      content: JSON.stringify(homeJson),
    },
    create: {
      slug: 'home',
      title: 'Startseite',
      status: 'system',
      navEnabled: false,
      content: JSON.stringify(homeJson),
    }
  });
  console.log("Homepage wurde erfolgreich nach Puck migriert.");
}

run().catch(console.error).finally(() => prisma.$disconnect());
