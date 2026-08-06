"""Versenden mit Rückmeldung — statt Schweigen.

An 31 Stellen im Code steht `fail_silently=True`. Das war einmal richtig
gedacht: Ein Absturz im nächtlichen Erinnerungs-Job wäre schlimmer als eine
verlorene Mail. Nur führte es dazu, dass eine Absage im Kanban „verschickt"
meldete, während der Mailserver sie abgelehnt hatte — und niemand erfuhr es.

Diese Schicht trennt die beiden Fälle sauber:

* **Ein Mensch wartet** (Recruiter klickt „Absagen", „Einladen", „Senden"):
  Fehler gehört sofort auf den Bildschirm, im Klartext des Mailservers.
  Dafür `request` übergeben.
* **Niemand wartet** (Cron, Hintergrund-Job): Kein Absturz, aber der Fehler
  wird protokolliert und im Zustand vermerkt, damit er auf der
  Einstellungs-Seite und im Dashboard-Hinweis auftaucht.

In beiden Fällen bleibt der Rückgabewert die Wahrheit: `False` heißt, es ging
nichts raus. Wer danach „verschickt" in die Oberfläche schreibt, tut es gegen
besseres Wissen.
"""
from __future__ import annotations

import logging

from django.contrib import messages
from django.core.mail import send_mail

from .mail_config import delivery_possible, record_result

logger = logging.getLogger(__name__)


def send_notice(subject: str, body: str, recipients: list[str] | tuple[str, ...],
                request=None, from_email: str | None = None,
                context: str = "") -> bool:
    """Nachricht verschicken und ehrlich melden, ob sie rausging.

    `context` beschreibt den Vorgang für Protokoll und Fehlermeldung
    ("Absage", "Einladung") - der Nutzer soll wissen, WAS nicht ankam.
    """
    targets = [r for r in (recipients or []) if r]
    if not targets:
        return False

    label = f"{context}: " if context else ""

    if not delivery_possible():
        logger.error("%sNicht zugestellt - kein Mailserver hinterlegt (%s)",
                     label, ", ".join(targets))
        record_result(False, f"{label}kein Mailserver hinterlegt")
        if request is not None:
            messages.error(
                request,
                f"{label}Nicht zugestellt – es ist kein Mailserver "
                "hinterlegt. Einzurichten unter Einstellungen → E-Mail-Versand.")
        return False

    try:
        send_mail(subject, body, from_email, targets, fail_silently=False)
    except Exception as exc:            # noqa: BLE001 - Grund gehoert gemeldet
        reason = f"{type(exc).__name__}: {exc}"
        logger.exception("%sVersand fehlgeschlagen (%s)", label, ", ".join(targets))
        record_result(False, f"{label}{reason}")
        if request is not None:
            messages.error(request,
                           f"{label}Nicht zugestellt – der Mailserver meldet: "
                           f"{reason}")
        return False

    record_result(True, f"{label}{len(targets)} Empfänger")
    return True
