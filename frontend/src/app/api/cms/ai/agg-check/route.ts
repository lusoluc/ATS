import { NextRequest, NextResponse } from 'next/server';

// Künstliche Verzögerung zur Simulation
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * ==========================================================
 * AGG CHECK AI ENDPOINT (Simulation für lokales LLM)
 * ==========================================================
 */
const SYSTEM_PROMPT = `
Du bist ein Fachanwalt für deutsches Arbeitsrecht (Fokus AGG - Allgemeines Gleichbehandlungsgesetz).
Prüfe den folgenden Stellenanzeigen-Text auf mögliche Diskriminierungen.
Finde Formulierungen, die wegen Alter, Geschlecht, Religion, Ethnie, Behinderung oder sexueller Identität abmahnfähig sein könnten.
Beispiele für Verstöße: "junges Team", "Digital Native", "Muttersprachler", "Putzfrau" (ohne m/w/d), "körperlich belastbar" (kann indirekt diskriminieren).
Gib eine Liste von Warnungen zurück. Ist alles einwandfrei, gib ein leeres Array zurück.
`;

export async function POST(req: NextRequest) {
  try {
    const { title, description, tasks, requirements } = await req.json();

    const fullText = `
      Titel: ${title}
      Beschreibung: ${description}
      Aufgaben: ${tasks.join(' ')}
      Anforderungen: ${requirements.join(' ')}
    `.toLowerCase();

    // Simuliere Ladezeit des lokalen Modells
    await delay(2000);

    const warnings: string[] = [];

    // Simple Heuristik zur Simulation der KI:
    if (!fullText.includes('(m/w/d)') && !fullText.includes('(w/m/d)') && !fullText.includes('(m/w/x)')) {
      warnings.push(`Der Titel oder Text enthält keine geschlechtsneutrale Endung wie (m/w/d).`);
    }

    if (fullText.includes('junges') || fullText.includes('junger') || fullText.includes('jungen')) {
      warnings.push(`Das Wort "jung" (z.B. "junges Team") diskriminiert wegen des Alters. Besser: "dynamisches Team" oder "motiviertes Team".`);
    }

    if (fullText.includes('muttersprache') || fullText.includes('muttersprachler') || fullText.includes('deutsch als muttersprache')) {
      warnings.push(`"Muttersprachler" diskriminiert aufgrund der ethnischen Herkunft. Besser: "Verhandlungssichere Deutschkenntnisse (C1/C2)".`);
    }

    if (fullText.includes('digital native')) {
      warnings.push(`"Digital Native" schließt indirekt ältere Bewerber aus (Altersdiskriminierung). Besser: "Hohe IT-Affinität".`);
    }

    const mockResponse = {
      isCompliant: warnings.length === 0,
      warnings: warnings,
      aiModel: 'Gemma 7B (Lokal, AGG-Tuned)'
    };

    return NextResponse.json(mockResponse);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
