import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function seed() {
  console.log("Starte Seeding für Job 1370...");

  // 1. Organization
  let org = await prisma.organization.findFirst();
  if (!org) org = await prisma.organization.create({ data: { name: "Enterprise" } });

  // 2. Location
  let loc = await prisma.location.findFirst({ where: { name: "Rickling" } });
  if (!loc) loc = await prisma.location.create({ data: { name: "Rickling", city: "Rickling", postalCode: "24635" } });

  // 3. Facility
  let fac = await prisma.facility.findFirst({ where: { name: "Psychiatrisches Krankenhaus Rickling" } });
  if (!fac) fac = await prisma.facility.create({ data: { name: "Psychiatrisches Krankenhaus Rickling", organizationId: org.id } });

  // 4. JobFamily
  let fam = await prisma.jobFamily.findFirst({ where: { name: "Medizin" } });
  if (!fam) fam = await prisma.jobFamily.create({ data: { name: "Medizin" } });

  // 5. WorkflowState
  let state = await prisma.workflowState.findFirst({ where: { name: "published" } });
  if (!state) state = await prisma.workflowState.create({ data: { name: "published" } });

  // Job Description in Markdown
  const markdownDesc = `
Der Enterprise ist ein diakonischer Komplexträger mit ca. 4.000 Mitarbeitenden und Beschäftigten. In über 110 Einrichtungen leistet er wichtige Dienste für ca. 4.500 Menschen aller Altersgruppen mit psychischen Störungen, mit Suchtverhalten und mit Behinderungen durch professionelle Begleitung, Behandlung, Beratung, Betreuung, Pflege und Schutz.

Wir suchen zur Verstärkung unseres Teams im Psychiatrischen Krankenhaus Rickling ab sofort eine/n **Oberärztin/Oberarzt für Psychiatrie und Psychotherapie (m/w/d)** für die 2. Klinik Suchtpsychiatrie und Psychotherapie (unbefristet | Voll- und Teilzeit).

Das Psychiatrische Krankenhaus Rickling ist mit 360 Betten ein zentraler Bestandteil der psychiatrischen und psychotherapeutischen Versorgung im Kreis Segeberg. Unsere Behandlungsangebote erstrecken sich zudem auf die Städte Hamburg, Lübeck, Neumünster und Kiel. Als Akademisches Lehrkrankenhaus der Universität zu Lübeck bieten wir regelmäßig Medizinstudierenden die Möglichkeit, praktische Erfahrungen zu sammeln und von unserem erfahrenen Team zu lernen.

Die 2. Klinik für Suchtpsychiatrie und Psychotherapie führt suchtpsychiatrische Akut- und Komplexbehandlungen für Menschen mit substanzbezogenen Störungen und psychiatrischer Komorbidität aus Schleswig-Holstein und der Metropolregion Hamburg durch. Dafür stehen aktuell insgesamt 127 suchtspezifische stationäre Behandlungsplätze verteilt auf fünf Stationen zur Verfügung. Die Therapie erfolgt in kleineren Einheiten, die eine Spezialisierung sowohl nach der Art der komorbiden psychischen Störungen wie auch der Substanz bzw. Lebenswelt der Patient*innen ermöglichen.

Werden Sie Teil unseres engagierten Teams und prägen Sie aktiv die Zukunft unseres Enterprises mit. Freuen Sie sich auf eine spannende Herausforderung, die Möglichkeit, Ihre Ideen einzubringen, und ein Umfeld, in dem Sie Ihr Potenzial voll entfalten können.

### Ihre Aufgabe:
- Oberärztliche Leitung einer offen geführten Suchtstation mit dem Schwerpunkt der qualifizierten Entzugsbehandlung
- Sicherstellung einer differenzierten Diagnostik, Therapieplanung und Durchführung einer leitliniengerechten medikamentösen Therapie (inklusive Substitution) und Psychotherapie
- Gewährleistung der Dokumentationspflichten sowie einer hohen Behandlungsqualität- und Sicherheit
- Fachärztliche Anleitung und Supervision der Assistenzärzt*innen hinsichtlich der ihnen übertragenen diagnostischen-therapeutischen Aufgaben
- Regelmäßige Durchführung von Oberarztvisiten mit Evaluation der Behandlungsverläufe sowie fortlaufender Einschätzung des Therapieresponse sowie möglicher Eigen- oder Fremdgefährdung
- Teilnahme an Leitungskonferenzen und Weiterentwicklung der Stations- und Behandlungskonzepte in enger Abstimmung mit dem Leitungsteam
- Sicherstellung des strukturierten Entlassungsmanagements unter Einbeziehung des Sozialdienstes mit Planung der Weiterbehandlung
- Teilnahme am oberärztlichen Hintergrunddienst
- Kooperation mit den umliegenden Suchhilfesystem, psychosozialen Einrichtungen sowie den Einrichtungen des Enterprises

### Wir wünschen uns:
- Abgeschlossene Facharztausbildung in Psychiatrie und Psychotherapie
- Interesse an der stationären Versorgung sowie an patientenorientierten und kontinuierlichen Behandlungsbeziehungen
- Erfahrung in der Suchtmedizin. Bei fehlender Vorerfahrung haben wir die Möglichkeit, Sie in diesem Schwerpunkt umfassend fortzubilden.
- Freude an interdisziplinärer Zusammenarbeit und Offenheit für innovative Versorgungsformen
- Organisationgeschick und ein hohes Maß an Eigenverantwortung
- Empathie, Kommunikationsstärke und Freude an der Arbeit mit Menschen
- Sensibilität für Diversität und kulturelle Unterschiede

### Wir bieten Ihnen:
- **Sicherheit:** Einen sinnstiftenden Arbeitsplatz bei einem diakonischen Komplexträger, eine leistungsgerechte Bezahlung nach Tarifvertrag (AVR DD) und 31 Tage Urlaub
- **Gesundheit:** Nutzung der Angebote unseres betrieblichen Gesundheitsmanagements
- **Perspektive:** Einen Arbeitsplatz in einem interessanten und anspruchsvollen Arbeitsfeld mit viel Eigenverantwortung
- **Flexibilität:** Attraktive und flexible Arbeitszeitregelungen
- **Gemeinschaft:** Eine kollegiale Arbeitsatmosphäre und eine wertschätzende Teamkultur
- **Wissensfluss:** Individuelle Entwicklungs- und Weiterbildungsmöglichkeiten
- **Mobilität:** Dienstradleasing – nicht nur für den Weg zur Arbeit, sondern auch für Ihre privaten Zwecke
- **Nachhaltigkeit:** Attraktive Mitarbeiterrabatte über die Plattform FutureBens (mehr als 120 nachhaltige Marken)

*Weitere Informationen zum AVR DD Tarif finden Sie unter attraktiver.de*

### Vielfalt bereichert uns!
Als Unterzeichner der Charta der Vielfalt setzen wir uns für ein Arbeitsumfeld ein, das frei von Vorurteilen ist. Alle qualifizierten Bewerberinnen und Bewerber werden berücksichtigt, unabhängig von Geschlecht, Nationalität, ethnischer Herkunft, Religion oder Weltanschauung, Behinderung, Alter, sexueller Orientierung und Identität.
`;

  // Job Posting erstellen
  const job = await prisma.jobPosting.create({
    data: {
      id: "1370", // Feste ID setzen für einfachen Aufruf
      title: "Oberärztin/Oberarzt für Psychiatrie und Psychotherapie (m/w/d)",
      description: markdownDesc,
      organizationId: org.id,
      facilityId: fac.id,
      locationId: loc.id,
      jobFamilyId: fam.id,
      workflowStateId: state.id,
    }
  });

  console.log("Job erfolgreich erstellt! ID:", job.id);
}

seed()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
