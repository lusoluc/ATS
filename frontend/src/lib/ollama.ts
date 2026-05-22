export async function analyzeCVWithLocalModel(cvText: string, jobTitle: string, modelName: string = 'gemma:2b') {
  try {
    const prompt = `Du bist ein HR-Experte. Bewerte den folgenden Lebenslauf für die Stelle "${jobTitle}".
Gib NUR ein JSON-Objekt zurück, ohne zusätzlichen Text. Das JSON muss genau dieses Format haben:
{"score": 85, "reason": "Kurze Begründung"}

Lebenslauf:
${cvText || 'Kein Text vorhanden.'}`;

    // Ollama läuft standardmäßig auf Port 11434 oder über Umgebungsvariable
    const response = await fetch(process.env.OLLAMA_URL || 'http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: modelName,
        prompt: prompt,
        stream: false,
        format: 'json'
      })
    });

    if (!response.ok) {
      throw new Error('Ollama Server nicht erreichbar');
    }

    const data = await response.json();
    const result = JSON.parse(data.response);
    
    return {
      score: result.score || 0,
      reason: result.reason || 'Keine Begründung generiert.'
    };
  } catch (error) {
    console.error('LLM Error:', error);
    // Fallback: Wenn Ollama (noch) nicht läuft, geben wir einen simulierten Wert zurück
    return {
      score: Math.floor(Math.random() * 50) + 40, // Random zwischen 40 und 90
      reason: 'Lokales Modell noch nicht erreichbar (Simulation).'
    };
  }
}
