"""Diagnose der lokalen LLM-Anbindung (WP2/L1).

Adressiert die häufigsten Setup-Fehler: Ollama nicht erreichbar, Modell nicht
gepullt, hohe Latenz. Gibt klare, umsetzbare Handlungsanweisungen.
"""
import json
import time
import urllib.request

from django.core.management.base import BaseCommand

from ats.views import get_ai_model, get_ollama_url


class Command(BaseCommand):
    help = "Prüft Erreichbarkeit, Modell-Verfügbarkeit und Latenz der lokalen LLM."

    def handle(self, *args, **options):
        model = get_ai_model()
        base = get_ollama_url("api/tags")
        self.stdout.write(f"Ollama-URL: {base}")
        self.stdout.write(f"Konfiguriertes Modell (AI_MODEL): {model}")

        # 1) Erreichbarkeit + installierte Modelle
        try:
            with urllib.request.urlopen(base, timeout=5) as r:
                tags = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"✗ Ollama nicht erreichbar: {e}\n"
                "  → Läuft der Dienst? 'ollama serve'. Host/Port via OLLAMA_HOST "
                "(auch 'rechner:11500') bzw. OLLAMA_PORT setzen."))
            return

        installed = [m.get("name", "") for m in tags.get("models", [])]
        self.stdout.write(self.style.SUCCESS(f"✓ Ollama erreichbar. Modelle: {', '.join(installed) or '—'}"))

        # 2) Ist das konfigurierte Modell gepullt?
        if not any(model == m or m.startswith(model + ":") or m.split(":")[0] == model.split(":")[0]
                   for m in installed):
            self.stdout.write(self.style.ERROR(
                f"✗ Modell '{model}' nicht installiert.\n  → 'ollama pull {model}' ausführen."))
            return
        self.stdout.write(self.style.SUCCESS(f"✓ Modell '{model}' ist installiert."))

        # 3) Latenz eines Mini-Prompts
        gen = get_ollama_url("api/generate")
        payload = json.dumps({"model": model, "prompt": "Sag nur: OK.",
                              "stream": False, "keep_alive": "10m"}).encode()
        try:
            req = urllib.request.Request(gen, data=payload,
                                         headers={"Content-Type": "application/json"})
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            latency = round(time.time() - t0, 2)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Testabfrage fehlgeschlagen: {e}"))
            return

        tokens = data.get("eval_count")
        self.stdout.write(self.style.SUCCESS(f"✓ Testabfrage ok in {latency}s (eval_count={tokens})."))
        if latency > 10:
            self.stdout.write(self.style.WARNING(
                "  ⚠ Hohe Latenz. Kleineres Modell erwägen oder 'keep_alive' nutzen (Modell warm halten)."))
