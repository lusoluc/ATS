"""Stufe 4: Auto-Antwort auf sichere, eindeutige Bewerber-Fragen.

Sehr bewusst eng gebaut. Automatisch beantwortet wird NUR, was zugleich:
- ein reines Kommunikations-Anliegen ist (STATUS/PROCESS - nie eine
  Entscheidung wie Einladung/Absage/Zusage; EU AI Act, Beschaeftigung),
- als sauber gilt (analyze().auto_safe: eine einzige, klar erkannte Frage,
  nicht zusammengesetzt), UND
- vom Betrieb freigeschaltet ist.

Jede Auto-Antwort ist transparent als automatisch gekennzeichnet, nennt den
Weg zu einem Menschen und wird auditiert. Das Lernen (Stufe 5) darf diesen
Kreis NIE erweitern - die freigeschalteten Anliegen kommen ausschliesslich
aus der Einstellung, gefiltert durch AUTO_SAFE_INTENTS.
"""
import json

from .audit import write_audit
from .inbox_intents import AUTO_SAFE_INTENTS, analyze
from .models import Application, Message, SystemSetting, TextSnippet
from .reply_drafts import batch_template, personalize

AUTO_REPLY_ENABLED_KEY = "AUTO_REPLY_ENABLED"
AUTO_REPLY_INTENTS_KEY = "AUTO_REPLY_INTENTS"

# Ab Werk: an, fuer Stand und Ablauf (bewusste Betreiber-Entscheidung).
_DEFAULT_ENABLED = True
_DEFAULT_INTENTS = ["STATUS", "PROCESS"]

# Transparenz-Hinweis (EU AI Act, Art. 50): klar als automatisch kennzeichnen
# und immer einen Weg zum Menschen offenhalten.
_TRANSPARENCY = (
    "\n\n— Diese Antwort wurde automatisch erstellt. Fuer ein persoenliches "
    "Anliegen antworten Sie einfach auf diese Nachricht; eine Person aus dem "
    "Team ist fuer Sie da."
)


def _get(key: str) -> str | None:
    row = SystemSetting.objects.filter(key=key).first()
    return row.value if row else None


def is_master_enabled() -> bool:
    raw = _get(AUTO_REPLY_ENABLED_KEY)
    if raw is None:
        return _DEFAULT_ENABLED
    return str(raw).strip().lower() not in ("0", "false", "off", "nein", "")


def configured_intents() -> list[str]:
    """Die eingestellten Anliegen (roh, vor der Sicherheitsfilterung)."""
    raw = _get(AUTO_REPLY_INTENTS_KEY)
    if raw is None:
        return list(_DEFAULT_INTENTS)
    try:
        data = json.loads(raw)
        return [str(i) for i in data] if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


def enabled_intents() -> set[str]:
    """Tatsaechlich auto-antwortbare Anliegen: eingestellt UND als sicher
    erlaubt. Die Schnittmenge mit AUTO_SAFE_INTENTS ist die harte Grenze -
    ein Entscheidungs-Anliegen wird selbst dann nie automatisch beantwortet,
    wenn es jemand in die Einstellung schreibt."""
    if not is_master_enabled():
        return set()
    return {i for i in configured_intents() if i in AUTO_SAFE_INTENTS}


def _suggested_template(intent: str) -> str:
    """Gleiche Quelle wie der Postfach-Vorschlag: juengster gespeicherter
    Baustein je Anliegen, sonst die eingebaute Vorlage."""
    snip = (TextSnippet.objects.filter(category=f"REPLY_{intent}")
            .order_by('-createdAt').first())
    return snip.content if snip else batch_template(intent)


def auto_reply_text(app: Application, intent: str) -> str:
    body = personalize(_suggested_template(intent),
                       first_name=app.applicant.firstName,
                       job_title=app.jobPosting.title, status=app.status)
    return body + _TRANSPARENCY


def maybe_auto_reply(app: Application, content: str) -> bool:
    """Beantwortet eine frisch eingegangene Bewerber-Nachricht automatisch,
    wenn ALLE Bedingungen erfuellt sind. Gibt True zurueck, wenn gesendet.

    Fail-safe gedacht: der Aufrufer kapselt den Aufruf, ein Fehler darf die
    Nachricht des Bewerbers nie blockieren.
    """
    analysis = analyze(content)
    if not analysis.auto_safe:
        return False
    if analysis.bucket not in enabled_intents():
        return False
    Message.objects.create(application=app, direction='OUTBOUND',
                           content=auto_reply_text(app, analysis.bucket))
    write_audit('AUTO_REPLY_SENT', application_id=app.id,
                intent=analysis.bucket)
    return True
