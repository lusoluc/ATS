"""Fehlerseiten, die einen Weg zurück zeigen.

Ohne diese Seiten liefert Django in Produktion seinen englischen Standardtext:
„Not Found — The requested resource was not found on this server.", mit
`lang="en"` und ohne einen einzigen Link. Für eine deutsche Karriereseite in
der Pflege ist das eine verlorene Bewerbung — zumal der häufigste 404 kein
Tippfehler ist, sondern eine besetzte Stelle, deren Link noch in einer
Jobbörse oder E-Mail steht.

Hier liegt nur die CSRF-Sicht: 404/500/403/400 findet Django über die
Vorlagen `404.html` & Co. von selbst. Für den CSRF-Fall gibt es keine
Vorlagen-Konvention — er braucht eine eigene Sicht (`CSRF_FAILURE_VIEW`).

Teil des View-Pakets; oeffentliche Namen werden in ats/views/__init__.py
re-exportiert.
"""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

__all__ = ["csrf_failure"]


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    """Abgelaufene Sitzung beim Absenden eines Formulars.

    Der Regelfall ist harmlos und trifft die falschen Leute: Jemand füllt das
    Bewerbungsformular in Ruhe aus, füllt es weiter, telefoniert dazwischen —
    und beim Absenden ist der Sitzungs-Zeitstempel abgelaufen. Django
    antwortet dann mit „CSRF verification failed. Request aborted." Wer das
    liest, denkt an einen Defekt und gibt auf.

    Der Hinweis auf den Zurück-Knopf ist keine Floskel: Die Eingaben stehen
    noch im Formular, weil der Browser sie zwischenspeichert. Genau das weiss
    aber niemand, dem man es nicht sagt.

    Der Grund (`reason`) bleibt bewusst draussen: Er nennt technische Details
    zum Ablehnungsgrund, die einem Angreifer beim Sondieren helfen und einer
    bewerbenden Person nichts sagen.
    """
    return render(request, "csrf_failure.html", status=403)
