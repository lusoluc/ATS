import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const SEED_PAGES = [
  { title: 'Über uns', slug: 'ueber-uns', navLabel: 'Über uns', navParent: 'beruf-karriere', navOrder: 0, content: `# Über den Enterprise

Der **Enterprise** ist ein diakonisches Sozialunternehmen mit über 145 Jahren Tradition.

## Unsere Geschichte

Seit 1876 engagieren wir uns für Menschen in besonderen Lebenslagen. Unsere Einrichtungen sind in der norddeutschen Landschaft verwurzelt — eingebettet in Natur, Gemeinschaft und gelebte Nächstenliebe.

## Was uns ausmacht

- **2.000+ Mitarbeitende** aus der Region
- **10 Einrichtungen** in Schleswig-Holstein
- Psychiatrie, Jugendhilfe, Altenpflege und soziale Dienste
- Vergütung nach kirchlichem Tarifvertrag (KTD)
- Familiäre Atmosphäre und flache Hierarchien

## Unsere Standorte

Unsere Hauptstandorte befinden sich in **Rickling**, **Bad Segeberg**, **Neumünster** und weiteren Orten in Schleswig-Holstein.
` },
  { title: 'Benefits & Vorteile', slug: 'benefits', navLabel: 'Benefits', navParent: 'beruf-karriere', navOrder: 1, content: `# Benefits & Vorteile

Beim Enterprise arbeiten heißt: Sinnvoll arbeiten und dabei gut versorgt sein.

## Vergütung & Finanzen

- **Kirchlicher Tarifvertrag (KTD)** — faire, transparente Bezahlung
- **Jahressonderzahlung** — 13. Monatsgehalt
- **Betriebliche Altersvorsorge** — wir sichern deine Zukunft
- **Vermögenswirksame Leistungen**

## Work-Life-Balance

- **30 Tage Urlaub** plus Zusatzurlaub für Schichtarbeit
- **Flexible Arbeitszeitmodelle** — Voll- und Teilzeit
- **Familienfreundlich** — betriebliche Kinderbetreuung

## Entwicklung & Bildung

- **Fort- und Weiterbildung** — bezahlte Fortbildungstage
- **Fachliche Spezialisierung** möglich
- **Karrierepfade** innerhalb des Unternehmens

## Arbeitsumfeld

- **Ländliche Lage** — kurze Wege, viel Natur
- **Kollegiales Miteinander** — familiäre Teams
- **Moderne Ausstattung** in unseren Einrichtungen
` },
  { title: 'Beruf & Karriere', slug: 'beruf-karriere', navLabel: 'Beruf & Karriere', navParent: '', navOrder: 0, content: `# Beruf & Karriere beim Enterprise

Finde deinen Platz bei uns — ob Pflege, Medizin, Pädagogik, Verwaltung oder Technik.

## Deine Möglichkeiten

Der Enterprise bietet vielfältige Karrierewege in einem sinnstiftenden Arbeitsumfeld:

- **Pflege & Betreuung** — Psychiatrische Pflege, Altenpflege, Behindertenbetreuung
- **Medizin** — Ärztliche Tätigkeit in unseren Kliniken
- **Pädagogik & Therapie** — Jugendhilfe, Sozialpädagogik, Ergotherapie
- **Verwaltung & IT** — Kaufmännische Berufe, Digitalisierung
- **Hauswirtschaft & Technik** — Gebäudemanagement, Küche, Reinigung

## Dein Weg zu uns

1. **Stellenangebote durchsuchen** — nutze unsere Jobbörse mit Umkreissuche
2. **Initiativ bewerben** — auch ohne passende Ausschreibung
3. **Bewerbungsgespräch** — wir melden uns innerhalb von 2 Werktagen
4. **Willkommen im Team** — strukturierte Einarbeitung
` },
  { title: 'Arbeitgeber', slug: 'arbeitgeber', navLabel: 'Arbeitgeber', navParent: '', navOrder: 1, content: `# Der Enterprise als Arbeitgeber

## Arbeitgeber mit Charakter

Wir sind kein Konzern. Wir sind Gemeinschaft. Unsere Mitarbeitenden kommen aus den umliegenden Dörfern und kehren jeden Tag nach Hause zurück.

## Unsere Werte

- **Menschlichkeit** — Jeder Mensch ist wertvoll
- **Gemeinschaft** — Wir arbeiten im Team
- **Verlässlichkeit** — Faire Bezahlung, sichere Arbeitsplätze
- **Nachhaltigkeit** — Verantwortung für Region und Umwelt

## Unsere Einrichtungen

Zum Enterprise gehören psychiatrische Einrichtungen, Jugendhilfe-Angebote, Altenpflegeheime und weitere soziale Dienste — alle eingebettet in die norddeutsche Landschaft.

## Gemeinnützig aus Überzeugung

Als diakonisches Unternehmen sind wir gemeinnützig. Das bedeutet: Alle Gewinne fließen zurück in unsere Arbeit, in unsere Mitarbeitenden und in die Region.
` },
  { title: 'Ausbildung', slug: 'ausbildung', navLabel: 'Ausbildung', navParent: 'beruf-karriere', navOrder: 2, content: `# Ausbildung beim Enterprise

## Deine Ausbildung bei uns

Wir bilden in verschiedenen Berufen aus und begleiten dich auf deinem Weg in einen sinnvollen Beruf.

### Ausbildungsberufe

- **Pflegefachfrau / Pflegefachmann** (3 Jahre)
- **Altenpflegehelfer*in** (1 Jahr)
- **Erzieher*in** (schulische Ausbildung mit Praxisphasen)
- **Kauffrau/-mann für Büromanagement**
- **Hauswirtschafter*in**

### Was wir bieten

- Vergütung nach KTD-Ausbildungstarif
- 30 Tage Urlaub
- Praxisanleitung durch erfahrene Kolleg*innen
- Übernahmegarantie bei guten Leistungen
- Azubi-Projekte und Teamevents
` },
  { title: 'FAQ', slug: 'faq', navLabel: 'FAQ', navParent: '', navOrder: 5, content: `# Häufig gestellte Fragen

## Bewerbung

**Kann ich mich initiativ bewerben?**
Ja, absolut! Wir freuen uns über Initiativbewerbungen. Nutze unser Online-Formular — wir melden uns innerhalb von zwei Werktagen.

**Welche Unterlagen brauche ich?**
Lebenslauf und relevante Zeugnisse genügen für den Anfang. Ein Anschreiben ist willkommen, aber nicht zwingend.

**Wie lange dauert der Bewerbungsprozess?**
In der Regel melden wir uns innerhalb von 2 Werktagen. Das Bewerbungsgespräch findet zeitnah statt.

## Arbeiten beim Enterprise

**Welcher Tarifvertrag gilt?**
Wir vergüten nach dem Kirchlichen Tarifvertrag Diakonie (KTD) inklusive Jahressonderzahlung und betrieblicher Altersversorgung.

**Sind Teilzeitstellen möglich?**
Ja. Viele unserer Stellen sind auch in Teilzeit zu besetzen.

**Gibt es Ausbildungsplätze?**
Ja! Wir bilden in verschiedenen Pflege-, Sozial- und Verwaltungsberufen aus.

## Standorte

**Wo befinden sich die Einrichtungen?**
Unsere Hauptstandorte sind in Rickling, Bad Segeberg und Neumünster — eingebettet in die norddeutsche Natur.
` },
  { title: 'Weiterbildung', slug: 'weiterbildung', navLabel: 'Weiterbildung', navParent: 'beruf-karriere', navOrder: 3, content: `# Fort- und Weiterbildung

## Wir investieren in dich

Der Enterprise unterstützt deine fachliche und persönliche Entwicklung — mit bezahlten Fortbildungstagen und vielfältigen Angeboten.

### Angebote

- Fachweiterbildung Psychiatrie
- Praxisanleiter-Qualifikation
- Führungskräfte-Entwicklung
- Deeskalationstraining
- Erste-Hilfe-Auffrischung
- Digitale Kompetenz-Schulungen
` },
  { title: 'Kontakt', slug: 'kontakt', navLabel: 'Kontakt', navParent: '', navOrder: 6, navEnabled: true, content: `# Kontakt

## Recruiting-Team

Wir freuen uns auf deine Fragen und deine Bewerbung!

**E-Mail:** karriere@Enterprise.de
**Telefon:** 04326 / 500

**Bürozeiten:** Mo–Fr, 8:30 bis 15:00 Uhr

## Adresse

Enterprise
Daldorfer Straße 2
24635 Rickling
` },
];

// POST /api/cms/pages/seed — importiert alle Standardseiten
export async function POST() {
  try {
    let created = 0;
    let skipped = 0;
    for (const page of SEED_PAGES) {
      const existing = await prisma.page.findUnique({ where: { slug: page.slug } });
      if (existing) { skipped++; continue; }
      await prisma.page.create({
        data: {
          title: page.title,
          slug: page.slug,
          content: page.content,
          status: 'published',
          navEnabled: page.navEnabled !== undefined ? page.navEnabled : true,
          navLabel: page.navLabel || null,
          navParent: page.navParent || null,
          navOrder: page.navOrder || 0,
        },
      });
      created++;
    }
    return NextResponse.json({ success: true, created, skipped, total: SEED_PAGES.length });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
