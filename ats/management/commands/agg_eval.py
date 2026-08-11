"""AGG-Prüfstrecke gegen die lokale LLM (WP4).

    python manage.py agg_eval

Gehört an denselben Platz wie `ai_eval`: nach jeder Änderung an
`ai_safety.PROMPT_VERSION`, am Modell oder an den Reasoning-Parametern. Nicht
in die CI – der Lauf braucht ein erreichbares Ollama und dauert je nach Modell
einige Minuten.

Der Befund ist bewusst hart formuliert: Weicht eine Variante von ihrer
Referenz ab, endet das Kommando mit Exit-Code 1. Eine Fairness-Prüfung, deren
Ergebnis man überlesen kann, ist keine.
"""
from __future__ import annotations

import json
import sys
from typing import Any

from django.core.management.base import BaseCommand

from ats.agg_eval import (
    PAARE,
    REQUIREMENTS,
    UNBEKANNT,
    Befund,
    bewerte_paare,
    mehrheitsnote,
)
from ats.ai_safety import PROMPT_VERSION, build_evaluation_payload, coerce_score
from ats.views import get_ai_model, get_ollama_url, make_ollama_request

#: Wie oft dieselbe Formulierung bewertet wird. Sprachmodelle streuen; eine
#: einzelne Abweichung waere sonst nicht von Zufall zu unterscheiden. Gewertet
#: wird die haeufigste Note (bei Gleichstand die schlechtere - im Zweifel
#: gegen das Modell).
LAEUFE_JE_TEXT = 3


class Command(BaseCommand):
    help = ("Prüft, ob sich die KI-Note bei gleicher Qualifikation durch ein "
            "Merkmal nach § 1 AGG verschiebt (braucht laufendes Ollama).")

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--laeufe", type=int, default=LAEUFE_JE_TEXT,
            help=f"Bewertungen je Formulierung (Standard: {LAEUFE_JE_TEXT}).")

    def handle(self, *args: Any, **options: Any) -> None:
        import urllib.request

        model = get_ai_model()
        laeufe = max(1, int(options["laeufe"]))
        self.stdout.write(f"Modell: {model} · Prompt-Version: {PROMPT_VERSION} "
                          f"· {laeufe} Bewertung(en) je Formulierung")
        try:
            urllib.request.urlopen(get_ollama_url("api/tags"), timeout=3)
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"Ollama nicht erreichbar ({e}) – AGG-Strecke übersprungen. "
                "Zuerst 'python manage.py ai_doctor' ausführen."))
            return

        gesamt = sum(1 + len(p.varianten) for p in PAARE) * laeufe
        self.stdout.write(f"{len(PAARE)} Merkmale, {gesamt} Bewertungen. "
                          "Das dauert einen Moment …\n")

        befunde = bewerte_paare(lambda text: self._note(model, text, laeufe))
        self._bericht(befunde)
        if any(not b.bestanden for b in befunde):
            sys.exit(1)

    # -- Innereien ---------------------------------------------------------

    def _note(self, model: str, text: str, laeufe: int) -> str:
        """Mehrheitsnote über mehrere Läufe (Regel siehe `mehrheitsnote`)."""
        noten: list[str] = []
        for _ in range(laeufe):
            payload = build_evaluation_payload(text, REQUIREMENTS, model)
            ok, data = make_ollama_request(get_ollama_url(), payload, timeout=60.0)
            if not ok:
                self.stderr.write(self.style.ERROR(f"  Request fehlgeschlagen: {data}"))
                noten.append(UNBEKANNT)
                continue
            try:
                parsed = json.loads((data.get("response") or "").strip())
                noten.append(coerce_score(parsed.get("score")))
            except (ValueError, TypeError, AttributeError):
                noten.append(UNBEKANNT)
        return mehrheitsnote(noten)

    def _bericht(self, befunde: list[Befund]) -> None:
        for b in befunde:
            noten = "/".join(b.varianten_noten)
            zeile = (f"{b.merkmal:34} Referenz {b.referenz_note} · "
                     f"Varianten {noten}")
            if b.bestanden:
                self.stdout.write(self.style.SUCCESS(f"OK   {zeile}"))
            elif b.unvollstaendig:
                self.stdout.write(self.style.WARNING(f"OFFEN  {zeile}"))
                self.stdout.write("    nicht ermittelt – siehe Fehler oben")
            else:
                self.stdout.write(self.style.ERROR(f"FEHLER {zeile}"))
                self.stdout.write(f"    {b.rechtsgrund}")

        schief = [b for b in befunde if not b.bestanden]
        if not schief:
            self.stdout.write(self.style.SUCCESS(
                f"\nAGG-Strecke: {len(befunde)} Merkmale ohne Notenverschiebung."))
            self.stdout.write(
                "Das ist ein Rauchmelder, kein Gutachten: geprüft wurden "
                "wenige Formulierungen. Der verbindliche Status steht in der "
                "COMPLIANCE_MATRIX.")
            return
        self.stdout.write(self.style.ERROR(
            f"\nAGG-Strecke: {len(schief)} von {len(befunde)} Merkmalen "
            "verschieben die Note."))
        self.stdout.write(
            "Bei gleicher Qualifikation darf das nicht passieren. Vor einem "
            "Opt-in fürs KI-Scoring gehört das geklärt: Prompt nachschärfen, "
            "Modell wechseln – oder die Vorbewertung aus lassen.")
