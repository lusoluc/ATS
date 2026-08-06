"""Welche E-Mail-Vorlage für welchen Zweck — eine Wahrheit statt Namensraten.

WAS VORHER WAR: Die Automatik suchte ihre Vorlage über den Namen —
`EmailTemplate.objects.filter(name__icontains='absage')`. Zwei Folgen, beide
still:

* Wer seine Vorlage „Ablehnung" nannte oder „Absage" in „Rückmeldung nach
  Sichtung" umbenannte, bekam keine Fehlermeldung. Die Absage fiel auf einen
  fest einprogrammierten Text zurück — den niemand im Haus je gesehen oder
  freigegeben hatte, und den Bewerbende trotzdem lasen.
* Auf einer Installation, die über Datenimport statt über den Seed startet,
  existiert gar keine Vorlage. Auch das fiel niemandem auf, weil der Fallback
  ja griff.

WIE ES JETZT LÄUFT: Jede Vorlage trägt einen ZWECK. Der Name bleibt frei
wählbar — er ist Beschriftung, keine Steuerung. Fehlt für einen Zweck eine
Vorlage, sagt die Verwaltungsseite das offen, statt den Ersatztext als
Normalfall auszugeben.
"""
from __future__ import annotations

from typing import Any

from .models import EmailTemplate
from .models.system import TEMPLATE_PURPOSES

#: Zwecke, die die Automatik wirklich benutzt (ohne den freien Baustein).
AUTOMATED_PURPOSES = [(code, label) for code, label in TEMPLATE_PURPOSES if code]

#: Stichworte fuer die EINMALIGE Zuordnung bestehender Vorlagen.
#:
#: Bewusst knapp und eindeutig: Ein erster Entwurf fuehrte hier auch "gespräch"
#: und "interview" als Hinweis auf eine Einladung - womit "Ablehnung nach
#: Gespräch" als Einladung durchging. Genau die Sorte Beinahe-Treffer, die das
#: ganze Namensraten unbrauchbar macht. Lieber ein Zweck bleibt offen und die
#: Verwaltungsseite fragt nach, als eine Absage geht als Einladung raus.
LEGACY_NAME_HINTS = {
    "REJECTION": ("absage", "ablehnung"),
    "INVITATION": ("einladung",),
    "CONFIRMATION": ("eingangsbest", "eingangsbestätigung", "empfangsbest"),
}


def template_for(purpose: str) -> EmailTemplate | None:
    """Die Vorlage fuer diesen Zweck - oder None.

    None heisst: Es gibt keine. Der Aufrufer benutzt dann seinen Ersatztext,
    ABER der Zustand ist auf der Verwaltungsseite sichtbar. Frueher war beides
    ununterscheidbar.
    """
    if not purpose:
        return None
    return (EmailTemplate.objects
            .filter(purpose=purpose)
            .exclude(subject="")
            .order_by("name")
            .first())


def guess_purpose(name: str) -> str:
    """Zweck aus einem alten Vorlagen-Namen ableiten (nur fuer die Migration).

    Bewusst nur hier: Im laufenden Betrieb wird nicht mehr geraten.
    """
    lowered = (name or "").lower()
    for purpose, hints in LEGACY_NAME_HINTS.items():
        if any(hint in lowered for hint in hints):
            return purpose
    return ""


def purpose_overview() -> list[dict[str, Any]]:
    """Je automatisiertem Zweck: belegt oder nicht, und was sonst passiert."""
    fallback = {
        "CONFIRMATION": "Es geht ein schlichter Standardtext mit Portal-Link raus.",
        "INVITATION": "Die Einladung nutzt einen Standardtext ohne Ihre Formulierung.",
        "REJECTION": "Die Absage nutzt einen Standardtext – Bewerbende lesen "
                     "Wortlaut, den niemand bei Ihnen freigegeben hat.",
    }
    rows = []
    for code, label in AUTOMATED_PURPOSES:
        tpl = template_for(code)
        rows.append({
            "code": code,
            "label": label,
            "template": tpl,
            "missing": tpl is None,
            "consequence": fallback.get(code, ""),
        })
    return rows


def missing_purposes() -> list[str]:
    return [row["label"] for row in purpose_overview() if row["missing"]]
