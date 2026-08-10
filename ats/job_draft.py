"""Stellen-Entwurf: aus dem, was das Haus schon hat, wird ein Textvorschlag.

Die Konvertierung einer Bedarfsmeldung erzeugte bisher wörtlich
„<Titel> – Beschreibung folgt." – und im Wizard beginnt die Beschreibung als
leeres Feld. Dabei liegt das Material längst im System: Textbausteine je
Jobfamilie (INTRO/TASKS/REQUIREMENTS), die Benefits des Hauses, das
Einrichtungsprofil. Niemand sollte abtippen, was schon da ist.

Muster wie beim Prozess-Berater:
- **Regelbasiert zuerst**: der Entwurf entsteht deterministisch aus den
  vorhandenen Bausteinen und funktioniert ohne KI.
- **KI optional obendrauf**: die lokale LLM darf den Entwurf flüssig
  formulieren und fehlende Aufgaben/Anforderungen ergänzen – hart validiert,
  bei jedem Fehler fällt der deterministische Entwurf durch.
- **Mensch entscheidet**: der Entwurf füllt nur leere Felder im Formular vor;
  wirksam wird nichts ohne Speichern, und vor der Veröffentlichung stehen die
  bestehenden Gates (Entgeltband, Frageverbot, Freigabe) unverändert.

Eine Grenze ist hart: **Der Entwurf nennt nie Gehaltszahlen.** Die Spanne
kommt aus dem Entgeltband und nur von dort (EU-RL 2023/970) – ein erfundener
Betrag im Anzeigentext wäre schlimmer als keiner. Der deterministische Teil
enthält konstruktionsbedingt keine Beträge; eine KI-Fassung mit Betrag wird
komplett verworfen, nicht repariert.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .models import Benefit, Facility, FacilityProfile, JobFamily, TextSnippet

#: Obergrenzen des Entwurfs – identisch fuer Regelwerk und KI-Fassung.
MAX_DESCRIPTION = 2000
MAX_ITEMS = 8
MAX_ITEM_LEN = 200

#: Erkennnt Geldbetraege und Gehaltsangaben. Bewusst grob: lieber eine
#: harmlose Formulierung zu viel verwerfen als einen erfundenen Betrag
#: durchlassen.
_MONEY = re.compile(
    r"€|\bEUR\b|\bEuro\b|\bGehalt\w*[:\s]*\d|\bVerg(ue|ü)tung\w*[:\s]*\d"
    r"|\b\d{1,3}(\.\d{3})+(,\d+)?\b",
    re.IGNORECASE)


def mentions_money(text: str) -> bool:
    """Steht in dem Text ein Betrag oder eine bezifferte Gehaltsangabe?"""
    return bool(_MONEY.search(text or ""))


def _snippet(category: str, family: JobFamily | None) -> str:
    """Textbaustein der Kategorie: familienspezifisch schlaegt allgemein."""
    if family is not None:
        treffer = (TextSnippet.objects
                   .filter(category=category, jobFamily=family)
                   .order_by("-createdAt").first())
        if treffer:
            return treffer.content.strip()
    treffer = (TextSnippet.objects
               .filter(category=category, jobFamily__isnull=True)
               .order_by("-createdAt").first())
    return treffer.content.strip() if treffer else ""


def _zeilen(text: str) -> list[str]:
    """Baustein-Inhalt als Liste: eine Zeile je Punkt, Aufzaehlungszeichen ab."""
    zeilen = []
    for zeile in (text or "").splitlines():
        sauber = zeile.strip().lstrip("-•*").strip()
        if sauber:
            zeilen.append(sauber[:MAX_ITEM_LEN])
    return zeilen[:MAX_ITEMS]


def rule_based_draft(title: str, family: JobFamily | None,
                     facility: Facility | None,
                     benefit_names: list[str] | None = None) -> dict[str, Any]:
    """Der deterministische Entwurf – funktioniert immer, auch ohne KI.

    Rueckgabe: description/tasks/requirements plus `quellen` (welche Bausteine
    verwendet wurden – die Oberflaeche sagt es dazu, damit nachvollziehbar
    bleibt, woher der Text kommt).
    """
    title = (title or "").strip()[:200]
    quellen: list[str] = []
    absaetze: list[str] = []

    intro = _snippet("INTRO", family)
    if intro:
        absaetze.append(intro)
        quellen.append("Einleitungs-Baustein"
                       + (f" ({family.name})" if family and TextSnippet.objects
                          .filter(category="INTRO", jobFamily=family).exists()
                          else ""))
    elif title:
        absaetze.append(
            f"Für unser Team suchen wir Verstärkung als {title}.")

    if facility is not None:
        profil = FacilityProfile.objects.filter(facility=facility).first()
        if profil and profil.description:
            # Nur der erste Satz: das Profil hat eine eigene Seite, die
            # Anzeige soll neugierig machen, nicht das Profil duplizieren.
            erster_satz = profil.description.strip().split(". ")[0].rstrip(".")
            if erster_satz:
                absaetze.append(erster_satz + ".")
                quellen.append(f"Einrichtungsprofil {facility.name}")

    if benefit_names is None:
        benefit_names = list(Benefit.objects.order_by("name")
                             .values_list("name", flat=True))
    benefits = [b.strip() for b in benefit_names if b.strip()][:4]
    if benefits:
        absaetze.append("Wir bieten " + ", ".join(benefits[:-1])
                        + (f" und {benefits[-1]}" if len(benefits) > 1
                           else benefits[0]) + ".")
        quellen.append("Benefits des Hauses")

    tasks = _zeilen(_snippet("TASKS", family))
    if tasks:
        quellen.append("Aufgaben-Baustein")
    requirements = _zeilen(_snippet("REQUIREMENTS", family))
    if requirements:
        quellen.append("Anforderungs-Baustein")

    return {
        "description": "\n\n".join(absaetze)[:MAX_DESCRIPTION],
        "tasks": tasks,
        "requirements": requirements,
        "quellen": quellen,
    }


def ai_draft_payload(title: str, family_name: str, base: dict[str, Any],
                     model: str) -> dict[str, Any]:
    """Ollama-Payload: die KI formuliert den Regel-Entwurf aus, erfindet aber
    keine Fakten – und vor allem keine Zahlen."""
    from .ai_safety import compose_system_prompt, default_options, wrap_untrusted
    material = json.dumps({
        "titel": title, "bereich": family_name,
        "entwurf": base.get("description", ""),
        "aufgaben": base.get("tasks", []),
        "anforderungen": base.get("requirements", []),
    }, ensure_ascii=False)
    return {
        "model": model,
        "system": compose_system_prompt() + (
            " Formuliere aus dem Material einen Stellenanzeigen-Entwurf. "
            "Drei kurze Absätze Beschreibung, dazu je 3 bis 6 Aufgaben und "
            "Anforderungen. Nutze NUR die genannten Fakten; erfinde nichts "
            "dazu. NIEMALS Gehaltszahlen oder Beträge nennen (die Spanne "
            "kommt aus dem Entgeltband). Keine Fragen zu Alter, Herkunft, "
            "Religion, Familie oder Gesundheit (AGG). Antworte NUR als JSON: "
            '{"description": "...", "tasks": ["..."], "requirements": ["..."]}'),
        "prompt": wrap_untrusted(material),
        "stream": False, "format": "json",
        "options": default_options(temperature=0.4),
        "keep_alive": "10m",
    }


def validate_ai_draft(raw: str, fallback: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Haerte-Pruefung der KI-Fassung. Rueckgabe: (Entwurf, kam_von_der_KI).

    Bei JEDEM Mangel – kein JSON, falsche Typen, leere Beschreibung, ein
    Geldbetrag irgendwo – kommt der deterministische Entwurf zurueck. Eine
    KI-Fassung wird verworfen, nicht repariert: Wer an einem Betrag
    herumschneidet, laesst den halben Satz stehen.
    """
    try:
        parsed = json.loads((raw or "").strip())
    except (ValueError, TypeError):
        return fallback, False
    if not isinstance(parsed, dict):
        return fallback, False
    description = parsed.get("description")
    tasks = parsed.get("tasks")
    requirements = parsed.get("requirements")
    if not isinstance(description, str) or not description.strip():
        return fallback, False
    if not isinstance(tasks, list) or not isinstance(requirements, list):
        return fallback, False
    tasks = [str(t).strip()[:MAX_ITEM_LEN] for t in tasks
             if str(t).strip()][:MAX_ITEMS]
    requirements = [str(r).strip()[:MAX_ITEM_LEN] for r in requirements
                    if str(r).strip()][:MAX_ITEMS]
    alles = " ".join([description, *tasks, *requirements])
    if mentions_money(alles):
        return fallback, False
    return {
        "description": description.strip()[:MAX_DESCRIPTION],
        "tasks": tasks or fallback.get("tasks", []),
        "requirements": requirements or fallback.get("requirements", []),
        "quellen": fallback.get("quellen", []) + ["KI-Formulierung"],
    }, True
