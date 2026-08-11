"""Verlaufs-Kurzfassung: den Schriftwechsel in Sekunden erfassen, nicht in Minuten.

Wer einen Fall übernimmt – Urlaubsvertretung, Krankheitsfall, „Mein Bereich"
einer Kollegin –, liest heute den ganzen Nachrichtenverlauf von unten nach
oben, nur um drei Fragen zu beantworten: Wie viel wurde geschrieben, wer ist
am Zug, und worum ging es zuletzt? Der Steckbrief beantwortet das für die
BEWERBUNG, aber nicht für den SCHRIFTWECHSEL.

Gebaut nach dem Steckbrief-Muster (`profile_summary`):
- Die Fakten sind deterministisch – Zählung, Zeitspanne, wer zuletzt schrieb,
  wie lange eine Frage unbeantwortet ist, das Anliegen der letzten
  eingehenden Nachricht (über die bestehende Postfach-Klassifikation, kein
  neues Regelwerk).
- Die lokale KI darf den Text NUR umformulieren – erfinden, hinzufügen oder
  weglassen ist ausgeschlossen, und ohne KI bleibt der deterministische Text
  (fail-safe, macht die View).

Der Auszug der letzten eingehenden Nachricht steht bewusst mit drin: Er ist
die eine Zeile, die dem Menschen sagt, ob es eilt. Sichtbar ist er nur für
Berechtigte (BOLA prüft die View), und er wird nie geloggt – für Logs gilt
weiter `redact_for_log`.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass

from django.utils import timezone

from .models import Application, Message

#: Laenge des Auszugs aus der letzten eingehenden Nachricht.
AUSZUG_LAENGE = 160


@dataclass(frozen=True)
class VerlaufFakten:
    """Deterministische Fakten über einen Schriftwechsel."""

    gesamt: int
    eingehend: int
    ausgehend: int
    erste_am: datetime.datetime
    letzte_am: datetime.datetime
    letzte_richtung: str             # INBOUND | OUTBOUND
    wartet_seit_tagen: int | None    # nur gesetzt, wenn die letzte eingehend ist
    letztes_anliegen: str            # Label der Postfach-Klassifikation, "" ohne eingehende
    auszug: str                      # letzte eingehende Nachricht, gekuerzt


def build_verlauf(app: Application) -> VerlaufFakten | None:
    """Fakten aus dem Schriftwechsel – EIN Query, ohne Nachrichten fehlt nichts."""
    nachrichten = list(Message.objects.filter(application=app)
                       .order_by('createdAt'))
    if not nachrichten:
        return None
    eingehend = [n for n in nachrichten if n.direction == 'INBOUND']
    letzte = nachrichten[-1]
    wartet = None
    if letzte.direction == 'INBOUND':
        wartet = max(0, (timezone.now() - letzte.createdAt).days)

    anliegen = ""
    auszug = ""
    if eingehend:
        from .inbox_intents import INTENT_LABELS, analyze
        letzte_ein = eingehend[-1]
        inhalt = letzte_ein.content or ""
        analyse = analyze(inhalt)
        anliegen = INTENT_LABELS.get(analyse.bucket, "")
        kurz = " ".join(inhalt.split())
        auszug = kurz[:AUSZUG_LAENGE] + ("…" if len(kurz) > AUSZUG_LAENGE else "")

    return VerlaufFakten(
        gesamt=len(nachrichten),
        eingehend=len(eingehend),
        ausgehend=len(nachrichten) - len(eingehend),
        erste_am=nachrichten[0].createdAt,
        letzte_am=letzte.createdAt,
        letzte_richtung=letzte.direction,
        wartet_seit_tagen=wartet,
        letztes_anliegen=anliegen,
        auszug=auszug,
    )


def verlauf_text(f: VerlaufFakten) -> str:
    """Die Fakten als deutscher Fließtext – nüchtern, ohne Wertung.

    Jede Angabe hier stammt aus `VerlaufFakten`; der Satzbau ist das Einzige,
    was diese Funktion hinzufügt. Genau deshalb darf die KI-Stufe später nur
    UMFORMULIEREN: Der Informationsgehalt ist an dieser Stelle abschließend.
    """
    teile = []
    von = timezone.localtime(f.erste_am).strftime('%d.%m.%Y')
    bis = timezone.localtime(f.letzte_am).strftime('%d.%m.%Y')
    zeitraum = f"seit {von}" if von == bis else f"zwischen {von} und {bis}"
    teile.append(f"{f.gesamt} Nachricht{'en' if f.gesamt != 1 else ''} "
                 f"{zeitraum} – {f.eingehend} von der bewerbenden Person, "
                 f"{f.ausgehend} von uns.")
    if f.letzte_richtung == 'INBOUND':
        if f.wartet_seit_tagen is not None and f.wartet_seit_tagen >= 1:
            teile.append(f"Die letzte Nachricht kam von der bewerbenden Person "
                         f"und ist seit {f.wartet_seit_tagen} "
                         f"Tag{'en' if f.wartet_seit_tagen != 1 else ''} "
                         f"unbeantwortet.")
        else:
            teile.append("Die letzte Nachricht kam von der bewerbenden Person "
                         "und ist noch unbeantwortet.")
    else:
        teile.append("Zuletzt haben wir geantwortet – die bewerbende Person "
                     "ist am Zug.")
    if f.letztes_anliegen:
        teile.append(f"Anliegen zuletzt: {f.letztes_anliegen}.")
    return " ".join(teile)
