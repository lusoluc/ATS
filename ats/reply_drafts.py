"""C4: Antwort-Entwuerfe auf Bewerber-Nachrichten.

Zweck: Wenn eine Bewerberin/ein Bewerber schreibt, soll der HR-Mensch nicht
vor dem leeren Feld sitzen. SecurATS schlaegt einen hoeflichen, zum aktuellen
Stand passenden Entwurf vor - den der Mensch prueft, anpasst und erst dann
sendet. Nie automatisch versenden, nie Zusagen erfinden.

Zweistufig wie beim Prozess-Berater: eine regelbasierte Grundlage, die IMMER
funktioniert (auch ohne KI), und optional lokale Gemma-Verfeinerung im View.
Die Grundlage lebt hier - testbar, typisiert, ohne Netz.
"""
from .board_insights import status_label

# Status-spezifischer Kernsatz. Bewusst ohne verbindliche Zusagen (Termin,
# Zu-/Absage, Gehalt) - der Entwurf haelt den Ton, die Entscheidung trifft
# der Mensch.
_STATUS_LINES: dict[str, str] = {
    "NEW": ("Ihre Unterlagen sind bei uns eingegangen und werden derzeit "
            "gesichtet. Sobald es einen neuen Stand gibt, melden wir uns bei Ihnen."),
    "IN_REVIEW": ("Ihre Bewerbung liegt uns vor und wird gerade sorgfaeltig "
                  "geprueft. Wir melden uns zeitnah mit einer Rueckmeldung."),
    "INVITED": ("Wir freuen uns, mit Ihnen ins Gespraech zu kommen. Gern "
                "stimmen wir die naechsten Schritte mit Ihnen ab."),
    "HIRED": ("Wir freuen uns sehr auf die Zusammenarbeit mit Ihnen und "
              "unterstuetzen Sie gern bei den naechsten Schritten."),
    "REJECTED": ("Vielen Dank fuer Ihr Interesse und Ihre Geduld im Verfahren."),
    "WITHDRAWN": ("Vielen Dank fuer Ihre Rueckmeldung und Ihr Interesse an uns."),
}

_DEFAULT_LINE = ("Wir kuemmern uns um Ihr Anliegen und melden uns zeitnah "
                 "bei Ihnen.")


def status_line(status: str) -> str:
    """Der zum Bewerbungsstatus passende Kernsatz des Entwurfs."""
    return _STATUS_LINES.get(status, _DEFAULT_LINE)


def rule_based_draft(*, status: str, job_title: str) -> str:
    """Ein vollstaendiger, hoeflicher Antwort-Entwurf ohne KI.

    Dient zugleich als sichere Rueckfallebene, wenn die lokale KI nicht
    erreichbar ist - der Flow liefert also immer etwas Brauchbares.
    """
    job = (job_title or "").strip()
    bezug = f" zu Ihrer Bewerbung als {job}" if job else ""
    return (
        "Guten Tag,\n\n"
        f"vielen Dank fuer Ihre Nachricht{bezug}.\n\n"
        f"{status_line(status)}\n\n"
        "Fuer Rueckfragen sind wir gern fuer Sie da.\n\n"
        "Freundliche Gruesse\n"
        "Ihr Recruiting-Team"
    )


# --- Sammel-Antworten: eine Vorlage je Anliegen, pro Person eingesetzt -------
# Platzhalter werden beim Senden je Bewerbung ersetzt - so liest sich die
# Antwort individuell, obwohl HR nur EINE Vorlage prueft. Kein Massenversand.
_BATCH_TEMPLATES: dict[str, str] = {
    "STATUS": (
        "Guten Tag [[Vorname]],\n\n"
        "vielen Dank fuer Ihre Nachricht zu Ihrer Bewerbung als [[Stelle]].\n\n"
        "Ihre Bewerbung liegt uns vor (aktueller Stand: [[Stand]]) und wird "
        "sorgfaeltig geprueft. Sobald es einen neuen Stand gibt, melden wir uns "
        "bei Ihnen.\n\n"
        "Fuer Rueckfragen sind wir gern fuer Sie da.\n\n"
        "Freundliche Gruesse\nIhr Recruiting-Team"
    ),
    "PROCESS": (
        "Guten Tag [[Vorname]],\n\n"
        "gern erlaeutern wir den weiteren Ablauf zu Ihrer Bewerbung als "
        "[[Stelle]]: Wir sichten die Unterlagen, laden passende Bewerber:innen "
        "zum Gespraech ein und geben anschliessend eine Rueckmeldung. Aktueller "
        "Stand Ihrer Bewerbung: [[Stand]].\n\n"
        "Bei Fragen sind wir gern fuer Sie da.\n\n"
        "Freundliche Gruesse\nIhr Recruiting-Team"
    ),
    "DOCUMENTS": (
        "Guten Tag [[Vorname]],\n\n"
        "vielen Dank fuer Ihre Nachricht zu Ihren Unterlagen fuer die Stelle "
        "[[Stelle]]. Ihre Bewerbung ist bei uns eingegangen. Sollten Unterlagen "
        "fehlen, kommen wir aktiv auf Sie zu - Sie muessen zunaechst nichts "
        "weiter veranlassen.\n\n"
        "Fuer Rueckfragen sind wir gern fuer Sie da.\n\n"
        "Freundliche Gruesse\nIhr Recruiting-Team"
    ),
    "SCHEDULING": (
        "Guten Tag [[Vorname]],\n\n"
        "vielen Dank fuer Ihre Nachricht zum Termin fuer die Stelle [[Stelle]]. "
        "Gern finden wir einen passenden Zeitpunkt - bitte nennen Sie uns zwei "
        "bis drei Zeitfenster, die Ihnen passen, dann stimmen wir uns ab.\n\n"
        "Freundliche Gruesse\nIhr Recruiting-Team"
    ),
    "WITHDRAWAL": (
        "Guten Tag [[Vorname]],\n\n"
        "vielen Dank fuer Ihre Rueckmeldung. Wir haben Ihren Wunsch zur Stelle "
        "[[Stelle]] notiert und melden uns bei Ihnen. Fuer Ihre weitere "
        "berufliche Zukunft wuenschen wir Ihnen alles Gute.\n\n"
        "Freundliche Gruesse\nIhr Recruiting-Team"
    ),
}


def batch_template(intent: str) -> str:
    """Sammel-Antwort-Vorlage je Anliegen (mit Platzhaltern). Leer fuer OTHER -
    dort gibt es bewusst keine Sammel-Antwort (individuelle Pruefung)."""
    return _BATCH_TEMPLATES.get(intent, "")


def personalize(template: str, *, first_name: str, job_title: str,
                status: str) -> str:
    """Setzt die Platzhalter einer Sammel-Vorlage je Bewerbung ein."""
    return (template
            .replace("[[Vorname]]", (first_name or "").strip())
            .replace("[[Stelle]]", (job_title or "").strip())
            .replace("[[Stand]]", status_label(status)))


def ai_system_prompt(*, status: str, job_title: str) -> str:
    """Systemanweisung fuer die lokale KI-Verfeinerung des Entwurfs.

    Klare Leitplanken: hoeflich, knapp, Sie-Form, AGG-neutral und - der
    wichtigste Punkt - KEINE verbindlichen Zusagen erfinden.
    """
    stand = status_label(status)
    job = (job_title or "die ausgeschriebene Stelle").strip()
    return (
        "Du entwirfst eine kurze, freundliche Antwort an eine Bewerberin/einen "
        "Bewerber auf deren Nachricht. Kontext (nur zur Orientierung, nicht "
        f"woertlich zitieren): Bewerbung als {job}, aktueller Stand: {stand}. "
        "Regeln: Sie-Form, hoeflich und wertschaetzend, maximal kurz. "
        "AGG-neutral (keine Aussagen zu Alter, Geschlecht, Herkunft, Religion, "
        "Gesundheit). Mache KEINE verbindlichen Zusagen zu Terminen, Zu- oder "
        "Absagen, Gehalt oder Ergebnissen - formuliere neutral und verweise bei "
        "Entscheidungen auf das Team. Erfinde keine Fakten. Antworte NUR mit dem "
        "fertigen Nachrichtentext, ohne Anrede-Platzhalter in eckigen Klammern."
    )
