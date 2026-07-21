"""AGG-Konformitätsprüfung für Stellentexte (Diskriminierung + Entgelttransparenz).

Aufgeteilt aus views/ai.py, wo die Prüfung als 200-Zeilen-Funktion in der
View steckte. Hier liegt die vollständige Logik: Prompt-Aufbau, Auswertung
der KI-Antwort und der deterministische Regex-Fallback, der greift, wenn die
lokale KI nicht erreichbar ist. Die View ist nur noch Einstiegspunkt.

Die Prüfung deckt zwei Regelwerke ab:
- AGG: Alter, Geschlecht, Religion, Herkunft, Behinderung
- EU-RL 2023/970 Art. 5 Abs. 2: keine Frage nach der Gehaltshistorie
"""
import json
import re
import time
import uuid
from typing import Any, NamedTuple


class AggResult(NamedTuple):
    """Ergebnis einer Prüfung: gefundene Verstöße und der bereinigte Text."""

    violations: list[str]
    optimized_text: str


DEFAULT_PROMPT = """Du bist der SecurATS AGG-Konformitätsprüfer (basierend auf Gemma).
Analysiere den folgenden Stellentext (Stellentitel und Beschreibung) auf mögliche Diskriminierungen (AGG-Verstöße) bezüglich Alter (z. B. 'Junior', 'Senior', 'jung'), Geschlecht (z. B. fehlendes m/w/d), Religion, Rasse oder Behinderung.
Halte gezielt nach 'Junior' oder 'Senior' Ausschau, da dies im deutschen Arbeitsrecht als verdeckte Alterskriterien ausgelegt werden kann! Empfiehl stattdessen neutrale Bezeichnungen mit Angabe der benötigten Berufserfahrung in Jahren.
Prüfe zusätzlich auf Entgelttransparenz (EU-RL 2023/970, Art. 5): Aufforderungen, das aktuelle oder frühere Gehalt zu nennen oder Gehaltsnachweise einzureichen, sind unzulässig und müssen als Verstoß gemeldet werden (die Frage nach der Gehaltsvorstellung ist zulässig).

Ausschreibungstext:
{text}

Bitte antworte genau im folgenden Format, damit das System deine Antwort parsen kann. Verwende exakt die Trenner:

=== VERSTÖSSE ===
- (Liste hier alle gefundenen Verstöße und problematischen Formulierungen stichpunktartig auf. Wenn keine vorhanden sind, schreibe "Keine Verstöße gefunden".)

=== OPTIMIERTER TEXT ===
(Gib hier den vollständigen, korrigierten, AGG-konformen Ausschreibungstext aus. Keine weiteren Kommentare vor oder nach diesem Block.)"""

# Regex-Fallback: (Suchbegriff, Begründung, [(Muster, Ersetzung), ...])
# Bewusst konservativ und erklärbar – dieser Weg läuft ohne KI und muss
# nachvollziehbar bleiben.
_FALLBACK_RULES: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("jung",
     "Mögliche Altersdiskriminierung durch das Wort 'jung/junge'. "
     "Empfohlen: 'engagierte Talente (m/w/d)'.",
     [(r"\bjunges\b", "engagiertes"), (r"\bjunge\b", "engagierte"),
      (r"\bjungen\b", "engagierten"), (r"\bjung\b", "engagiert")]),
    ("arzt",
     "Geschlechtsspezifische Formulierung 'Arzt'. Empfohlen: 'Arzt/Ärztin (m/w/d)'.",
     [(r"\barzt\b", "Arzt/Ärztin (m/w/d)")]),
    ("gesund",
     "Formulierung 'gesund' diskriminiert potenziell Bewerber mit chronischen "
     "Erkrankungen oder körperlichen Einschränkungen.",
     [(r"\bgesund\b", "qualifiziert")]),
    ("belastbar",
     "Formulierung 'belastbar' kann chronisch kranke oder behinderte Menschen "
     "abschrecken. Empfohlen: 'zuverlässig' oder 'engagiert'.",
     [(r"\bbelastbar\b", "engagiert")]),
]

_WHITELIST_HINTS = ("ok", "erlaubt", "bag", "keine änderung", "keine aenderung",
                    "nicht das alter")


def get_custom_prompt() -> str:
    """Eigener Prüf-Prompt aus den Systemeinstellungen (leer = Standard)."""
    from .models import SystemSetting
    setting = SystemSetting.objects.filter(key="AI_AGG_PROMPT").first()
    if setting and setting.value.strip():
        return setting.value.strip()
    return ""


def build_prompt(text: str, custom_prompt: str = "") -> str:
    if custom_prompt:
        return f"{custom_prompt}\n\nAusschreibungstext zum Prüfen:\n{text}"
    return DEFAULT_PROMPT.format(text=text)


def _clean_violations(violations: list[str]) -> list[str]:
    """Entfernt Leerzeilen und die „nichts gefunden"-Meldungen der KI."""
    unwanted = ("keine verstöße", "keine offensichtlichen", "keine risiken")
    return [v for v in violations
            if v and not any(u in v.lower() for u in unwanted)]


def parse_ai_reply(reply: str, original_text: str) -> AggResult:
    """Wertet die KI-Antwort aus – als JSON oder im Trenner-Format."""
    from .views.ai import try_parse_json_reply

    parsed_json, is_json = try_parse_json_reply(reply)
    if is_json:
        return _parse_json_result(parsed_json, original_text)
    return _parse_text_result(reply, original_text)


def _parse_json_result(parsed: dict[str, Any], original_text: str) -> AggResult:
    status_val = str(parsed.get("status", "")).strip().lower()
    is_green = status_val in ["grün", "gruen", "green", "konform", "safe",
                              "ok", "compliant"]
    violations: list[str] = []
    if not is_green:
        raw = (parsed.get("violations") or parsed.get("verstoesse")
               or parsed.get("verstöße") or [])
        if isinstance(raw, list):
            violations = [str(v).strip() for v in raw if str(v).strip()]
        elif isinstance(raw, str):
            violations = [v.strip() for v in raw.split("\n") if v.strip()]
        elif raw:
            violations = [str(raw).strip()]

    opt = (parsed.get("optimized_text") or parsed.get("optimized")
           or parsed.get("text"))
    optimized = str(opt).strip() if opt else original_text
    return AggResult(_clean_violations(violations), optimized)


def _parse_text_result(reply: str, original_text: str) -> AggResult:
    """Antwort im Trenner-Format; die KI variiert die Überschriften."""
    reply_lower = reply.lower()
    opt_headers = ["=== optimierter text ===", "optimierter text-vorschlag:",
                   "optimierter text:", "optimierter text vorschlag:"]
    header = next((h for h in opt_headers if h in reply_lower), None)

    if header:
        idx = reply_lower.find(header)
        optimized = reply[idx + len(header):].strip()
        violation_part = reply[:idx].strip()
        for noise in ["=== verstösse ===", "=== verstoesse ===",
                      "=== verstöße ===", "identifizierte risiken:",
                      "ki agg-check ergebnis:"]:
            violation_part = re.sub(noise, "", violation_part, flags=re.IGNORECASE)
        violations = [v.strip().lstrip("-*•# ")
                      for v in violation_part.split("\n") if v.strip()]
    elif "=== OPTIMIERTER TEXT ===" in reply:
        head, _, tail = reply.partition("=== OPTIMIERTER TEXT ===")
        optimized = tail.strip()
        violation_part = head.replace("=== VERSTÖSSE ===", "").strip()
        violations = [v.strip().lstrip("-*• ")
                      for v in violation_part.split("\n") if v.strip()]
    else:
        # Unverständliches Format: die Antwort selbst als Hinweis zeigen
        return AggResult(_clean_violations([reply]), original_text)

    return AggResult(_clean_violations(violations), optimized)


def regex_fallback(text: str, custom_prompt: str = "") -> AggResult:
    """Deterministische Prüfung ohne KI (greift, wenn Ollama ausfällt).

    Ein eigener Prüf-Prompt kann 'Junior'/'Senior' ausdrücklich erlauben –
    dann schlägt der Fallback dort nicht an, sonst würde er die bewusste
    Entscheidung des Trägers überstimmen.
    """
    text_lower = text.lower()
    custom_lower = custom_prompt.lower()
    violations: list[str] = []
    optimized = text

    for needle, reason, replacements in _FALLBACK_RULES:
        if needle not in text_lower:
            continue
        if needle == "arzt" and ("ärztin" in text_lower or "m/w/d" in text_lower):
            continue
        violations.append(reason)
        for pattern, repl in replacements:
            optimized = re.sub(pattern, repl, optimized, flags=re.IGNORECASE)

    for term, reason, replacement in [
        ("junior",
         "Formulierung 'Junior' im Stellentitel oder Text kann als "
         "Altersdiskriminierung (Bevorzugung jüngerer Bewerber) ausgelegt "
         "werden. Empfehlung: Angabe konkreter Berufserfahrung (z. B. 'mit "
         "erster Praxiserfahrung / Berufseinsteiger') statt Altersbegriffen.",
         "mit erster Praxiserfahrung"),
        ("senior",
         "Formulierung 'Senior' im Stellentitel oder Text kann als "
         "Altersdiskriminierung (Benachteiligung jüngerer Bewerber) ausgelegt "
         "werden. Empfehlung: Angabe konkreter Berufserfahrung (z. B. 'mit "
         "mehrjähriger Berufserfahrung') statt Altersbegriffen.",
         "mit mehrjähriger Berufserfahrung"),
    ]:
        whitelisted = term in custom_lower and any(h in custom_lower
                                                   for h in _WHITELIST_HINTS)
        if term in text_lower and not whitelisted:
            violations.append(reason)
            optimized = re.sub(rf"\b{term}\b", replacement, optimized,
                               flags=re.IGNORECASE)

    # Entgelttransparenz (EU-RL 2023/970, Art. 5 Abs. 2)
    from .pay_transparency import salary_history_violation
    hit = salary_history_violation(text)
    if hit:
        violations.append(
            f"Unzulässige Gehaltshistorie-Abfrage ('{hit}'): Nach EU-RL "
            "2023/970 Art. 5 Abs. 2 darf nicht nach aktuellem oder früherem "
            "Gehalt gefragt werden. Zulässig: Frage nach der Gehaltsvorstellung.")

    return AggResult(violations, optimized)


def start_check(text: str) -> uuid.UUID:
    """Startet die Prüfung im Hintergrund und liefert die Vorgangs-ID.

    Der Fortschritt liegt im Audit-Log (AI_TASK_PENDING → AI_TASK_COMPLETED);
    die Oberfläche fragt ihn über gemma_agg_check_status ab.
    """
    from .models import AuditLog
    from .views.ai import _run_in_background

    task_id = uuid.uuid4()
    custom_prompt = get_custom_prompt()
    prompt = build_prompt(text, custom_prompt)

    AuditLog.objects.create(
        action="AI_TASK_PENDING", userId=str(task_id),
        metadataJson=json.dumps({"status": "pending", "type": "AGG_CHECK"}))

    _run_in_background(lambda: _worker(text, prompt, custom_prompt, task_id))
    return task_id


def _worker(text: str, prompt: str, custom_prompt: str,
            task_id: uuid.UUID) -> None:
    from .models import AuditLog
    from .views.ai import (
        classify_ai_error,
        get_ai_model,
        get_ollama_url,
        log_ai_execution,
        make_ollama_request,
    )

    payload = {
        "model": get_ai_model(), "prompt": prompt, "stream": False,
        "options": {"temperature": 0.1, "num_predict": 300,
                    "top_k": 20, "top_p": 0.5},
    }
    start = time.time()
    try:
        success, res_data = make_ollama_request(get_ollama_url(), payload,
                                                timeout=80.0)
        latency = round(time.time() - start, 2)
        if not success:
            log_ai_execution("AGG-Check", get_ai_model(), latency, False, True,
                             f"Ollama-Fehler: {res_data}", bool(custom_prompt),
                             prompt)
            raise RuntimeError(str(res_data))

        result = parse_ai_reply(res_data.get("response", "").strip(), text)
        log_ai_execution("AGG-Check", get_ai_model(), latency, True, False, "",
                         bool(custom_prompt), prompt)
        AuditLog.objects.create(
            action="AI_TASK_COMPLETED", userId=str(task_id),
            metadataJson=json.dumps({
                "status": "completed", "success": True,
                "violations": result.violations,
                "optimized_text": result.optimized_text,
                "original_text": text, "fallback_mode": False,
                "latency": latency}))
    except Exception as exc:
        # KI nicht erreichbar oder Antwort unbrauchbar: deterministisch prüfen
        latency = round(time.time() - start, 2)
        log_ai_execution("AGG-Check", get_ai_model(), latency, False, True,
                         str(exc), bool(custom_prompt), prompt)
        result = regex_fallback(text, custom_prompt)
        AuditLog.objects.create(
            action="AI_TASK_COMPLETED", userId=str(task_id),
            metadataJson=json.dumps({
                "status": "completed", "success": True,
                "violations": result.violations,
                "optimized_text": result.optimized_text,
                "original_text": text, "fallback_mode": True,
                "error_msg": classify_ai_error(exc, get_ai_model()),
                "latency": latency}))
