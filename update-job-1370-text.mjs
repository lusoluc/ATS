import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function updateJob() {
  console.log("Aktualisiere Textstruktur für Job 1370...");

  const modernMarkdown = `
**Suchtmedizin ist mehr als nur Therapie – es ist die Begleitung von Menschen zurück ins Leben.** 

Wir suchen nicht einfach eine ärztliche Kraft. Wir suchen eine Persönlichkeit, die unsere offene Suchtstation im *Psychiatrischen Krankenhaus Rickling* mit Fachkompetenz und menschlicher Wärme leitet. 

Als Akademisches Lehrkrankenhaus der Universität zu Lübeck verbinden wir in unserer 2. Klinik für Suchtpsychiatrie (127 Betten) modernste Leitlinien-Medizin mit einem familiären, hochspezialisierten Teamumfeld. Wir behandeln Menschen aus der gesamten Metropolregion Hamburg und Schleswig-Holstein.

Wenn Sie Lust haben, Verantwortung zu übernehmen, eigene Konzepte einzubringen und ein interdisziplinäres Team zu führen, dann sind Sie bei uns genau richtig.

---

### 🚀 Das erwartet Sie bei uns
Anstatt starrer Hierarchien finden Sie bei uns Raum für Gestaltung. Zu Ihren Kernaufgaben gehören:

- **Medizinische Leitung:** Sie leiten eine offen geführte Suchtstation (Schwerpunkt: qualifizierte Entzugsbehandlung) und tragen die fachärztliche Verantwortung für die Diagnostik und Therapie.
- **Team-Entwicklung:** Sie supervidieren und leiten unsere Assistenzärzt*innen an und prägen durch regelmäßige Oberarztvisiten die Behandlungsqualität.
- **Konzept-Arbeit:** In engen Leitungskonferenzen entwickeln Sie unsere Stations- und Behandlungskonzepte aktiv weiter.
- **Netzwerken:** Sie arbeiten Hand in Hand mit unserem Sozialdienst für ein strukturiertes Entlassungsmanagement und kooperieren mit dem regionalen Suchthilfesystem.

---

### 👤 Das bringen Sie mit
Wir legen Wert auf Persönlichkeit und Zusammenarbeit auf Augenhöhe. 

- Sie sind **Facharzt/Fachärztin für Psychiatrie und Psychotherapie**.
- Sie haben Empathie und tiefes Verständnis für die Arbeit mit sucht- und psychisch kranken Menschen.
- *Zusatz-Plus:* Erfahrung in der Suchtmedizin. Falls diese fehlt, bilden wir Sie in diesem Schwerpunkt umfassend und auf unsere Kosten aus!
- Sie haben Organisationstalent, treffen gerne Entscheidungen und schätzen den Austausch in einem multiprofessionellen Team.

---

### 💎 Warum der Landesverein? (Ihre Benefits)
Wir wissen, was Ärztinnen und Ärzte leisten. Deshalb sorgen wir dafür, dass die Rahmenbedingungen stimmen:

- **Top Vergütung & Sicherheit:** Leistungsgerechte Bezahlung nach dem Tarifvertrag AVR DD, betriebliche Altersvorsorge und 31 Tage Urlaub.
- **Zeit für Patienten:** Wir entlasten Sie durch digitale Prozesse und feste administrative Strukturen, damit Sie sich auf die Medizin konzentrieren können.
- **Beruf & Privatleben:** Verlässliche und flexible Arbeitszeitregelungen, die wirklich funktionieren.
- **Exzellente Fortbildung:** Großzügiges Budget und Freistellungen für Ihre individuelle Weiterbildung.
- **Moderne Mobilität:** Profitieren Sie von unserem attraktiven Dienstradleasing (E-Bikes).

*Als diakonischer Träger leben wir Vielfalt. Bei uns zählt Ihr Talent – unabhängig von Geschlecht, Religion, Alter oder Herkunft.*
`;

  await prisma.jobPosting.update({
    where: { id: "1370" },
    data: { description: modernMarkdown }
  });

  console.log("Job 1370 erfolgreich aktualisiert!");
}

updateJob()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
