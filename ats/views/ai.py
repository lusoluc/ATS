"""SecurATS Views — Lokale KI (Ollama/Gemma): Scoring, AGG-Check, Prompt-Tests, Textwerkzeuge.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import json
import logging
import os

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect

from ..audit import write_audit
from ..models import (
    Application,
    AuditLog,
    Facility,
    JobFamily,
    SystemSetting,
)
from ..permissions import (
    any_staff_required,
    hr_admin_required,
    recruiter_required,
    scope_applications,
)

logger = logging.getLogger(__name__)

__all__ = ["get_ollama_url", "get_ai_model", "make_ollama_request", "evaluate_with_local_gemma", "try_parse_json_reply", "log_ai_execution", "classify_ai_error", "test_gemma", "get_ai_execution_logs", "gemma_agg_check", "gemma_agg_check_status", "gemma_translate_simple_german", "validate_ai_prompt", "validate_ai_prompt_status", "save_ai_settings", "polish_message", "apply_template_tone", "suggest_process", "analytics_ask", "healthz_ai", "ingest_best_performers", "best_performer_profiles"]



def _run_in_background(worker):
    """Startet einen Hintergrund-Thread und schliesst dessen DB-Verbindung.

    WARUM: Ein Thread bekommt in Django eine EIGENE Datenbankverbindung.
    Wird sie nicht geschlossen, bleibt sie offen – unter PostgreSQL ist die
    Zahl der Verbindungen hart begrenzt (Standard 100), ein Betrieb mit vielen
    KI-Pruefungen wuerde den Pool langsam leerlaufen lassen ("too many
    clients"). SQLite verzeiht das, PostgreSQL nicht.
    """
    import threading

    from django.db import connection as _conn

    def _wrapped():
        try:
            worker()
        finally:
            try:
                _conn.close()
            except Exception:      # noqa: BLE001 - Aufraeumen darf nie werfen
                pass

    t = threading.Thread(target=_wrapped, daemon=True)
    t.start()
    return t


def get_ollama_url(endpoint="api/generate"):
    """
    Dynamically determines the Ollama service URL.
    Checks host.docker.internal first (to reach the host from inside the Docker container),
    then falls back to 127.0.0.1 (local execution).
    """
    import socket

    # Allow override via environment variable
    env_host = os.environ.get("OLLAMA_HOST")
    if env_host:
        return f"http://{env_host}:11434/{endpoint}"

    for host in ["host.docker.internal", "127.0.0.1"]:
        try:
            s = socket.create_connection((host, 11434), timeout=2.0)
            s.close()
            return f"http://{host}:11434/{endpoint}"
        except Exception:
            pass

    # Intelligent default fallback: inside a container, host.docker.internal is the host
    try:
        socket.gethostbyname("host.docker.internal")
        return f"http://host.docker.internal:11434/{endpoint}"
    except Exception:
        pass
    return f"http://127.0.0.1:11434/{endpoint}"


def get_ai_model():
    """Dynamically retrieves the configured AI model, defaulting to gemma:2b."""
    try:
        setting = SystemSetting.objects.filter(key="AI_MODEL").first()
        if setting and setting.value.strip():
            return setting.value.strip()
    except Exception:
        pass
    return "gemma:2b"


def make_ollama_request(url, payload, timeout=8.0):
    """
    Makes a POST request to Ollama using python's built-in urllib.
    Completely eliminates third-party dependencies like 'requests'.
    """
    import json
    import urllib.error
    import urllib.request

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode('utf-8'))
                return True, res_data
            else:
                return False, f"Status Code: {response.status}"
    except urllib.error.URLError as e:
        return False, str(e.reason)
    except Exception as e:
        return False, str(e)


def evaluate_with_local_gemma(cover_letter, requirements_list, application_id=None):
    """
    Evaluates the applicant's cover letter against the job requirements using local Gemma AI.
    If the local Gemma service (Ollama on port 11434) is offline, it falls back to high-fidelity rule matching.
    """
    import json

    from ..ai_safety import (
        PROMPT_VERSION,
        build_evaluation_payload,
        build_repair_payload,
        coerce_score,
        default_options,
    )

    def _setting(key, default=""):
        try:
            s = SystemSetting.objects.filter(key=key).first()
            return s.value.strip() if s and s.value else default
        except Exception:
            return default

    # L4: Tonalität nur fürs Formulieren der Begründung; L5: steuerbare Parameter
    tone_key = _setting("AI_TONE") or None
    try:
        options = default_options(
            temperature=float(_setting("AI_TEMPERATURE", "0.2")),
            num_ctx=int(_setting("AI_NUM_CTX", "0")) or None,
            num_predict=int(_setting("AI_NUM_PREDICT", "0")) or None,
        )
    except (TypeError, ValueError):
        options = default_options()

    payload = build_evaluation_payload(cover_letter, requirements_list, get_ai_model(),
                                       tone_key=tone_key, options=options)

    try:
        success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=28.0)
        if success:
            response_text = (res_data.get("response") or "").strip()
            repaired = False
            try:
                parsed = json.loads(response_text)
            except (ValueError, TypeError):
                # L5: eine Reparatur-Runde – Modell soll sein eigenes JSON fixen
                ok2, res2 = make_ollama_request(
                    get_ollama_url(), build_repair_payload(response_text, get_ai_model()),
                    timeout=15.0)
                if not ok2:
                    raise
                parsed = json.loads((res2.get("response") or "").strip())
                repaired = True
            score = coerce_score(parsed.get("score"))
            rationale = str(parsed.get("rationale", "Automatische Analyse durchgeführt."))[:500]
            log_ai_execution("Bewerbungs-Scoring", get_ai_model(),
                             res_data.get("total_duration"), True, False, "", bool(tone_key),
                             prompt_used=cover_letter,
                             tokens=res_data.get("eval_count"),
                             params=options, prompt_version=PROMPT_VERSION,
                             repaired=repaired,
                             application_id=str(application_id) if application_id else None)
            return score, rationale
    except Exception as e:
        logger.exception("Lokales KI-Scoring fehlgeschlagen; regelbasierter Fallback aktiv")
        log_ai_execution("Bewerbungs-Scoring", get_ai_model(), None, False, True, str(e), False,
                         prompt_used=cover_letter, prompt_version=PROMPT_VERSION,
                         application_id=str(application_id) if application_id else None)

    # Fallback to high-fidelity rule-based parsing
    text_lower = cover_letter.lower()
    matches = 0
    keywords = ["django", "python", "javascript", "react", "html", "css", "postgresql", "mysql", "recruiting", "hr", "sales"]
    for kw in keywords:
        if kw in text_lower:
            matches += 1

    if matches >= 4:
        return 'A', "Hervorragende Passgenauigkeit (Fallback). Anschreiben enthält exzellente Übereinstimmungen mit den geforderten Kompetenzen."
    elif matches >= 2:
        return 'B', "Gute Passgenauigkeit (Fallback). Mehrere relevante Fähigkeiten wurden identifiziert. Eignung im persönlichen Gespräch vertiefen."
    elif matches >= 1:
        return 'C', "Durchschnittliche Passgenauigkeit (Fallback). Grundlegende Kenntnisse vorhanden, detaillierte Unterlagenprüfung empfohlen."
    else:
        return 'D', "Geringe Übereinstimmung mit dem Anforderungsprofil (Fallback). Keine der gesuchten Schlüsselqualifikationen im Anschreiben identifiziert."


def try_parse_json_reply(reply):
    """
    Attempts to extract and parse a JSON object from the LLM reply.
    Supports raw JSON strings or JSON wrapped in markdown code blocks.
    """
    import json
    import re

    cleaned = reply.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            part_str = part.strip()
            if part_str.startswith("json"):
                part_str = part_str[4:].strip()
            if (part_str.startswith("{") and part_str.endswith("}")) or (part_str.startswith("[") and part_str.endswith("]")):
                cleaned = part_str
                break

    try:
        return json.loads(cleaned), True
    except Exception:
        match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1)), True
            except Exception:
                pass
    return None, False


def log_ai_execution(action_name, model_used, latency, success, fallback_mode, error_msg, custom_prompt_active, prompt_used="", **extra):
    import json
    try:
        from ..ai_safety import redact_for_log
        metadata = {
            'model': model_used,
            'latency': latency,
            'success': success,
            'fallback_mode': fallback_mode,
            'error_class': classify_ai_error(str(error_msg), model_used) if error_msg else "",
            'error_msg': (str(error_msg)[:300] if error_msg else ""),
            'custom_prompt_active': custom_prompt_active,
            # PII-Redaction (DSGVO): kein Klartext-Bewerberinhalt ins Log – nur Länge + Hash.
            'prompt_redacted': redact_for_log(prompt_used) if prompt_used else None,
        }
        metadata.update(extra)  # z.B. tokens, params, raw_snippet
        from ..audit import create_chained_audit
        create_chained_audit(
            action="AI_EXECUTION",
            user_id=action_name,
            metadata_json=json.dumps(metadata, default=str),
        )
    except Exception:
        logger.exception("AI-Execution-Logging fehlgeschlagen für %s", action_name)


def classify_ai_error(error_str, model_name):
    """Classifies AI/Ollama connection issues and returns a highly detailed diagnostic message in German."""
    err_lower = str(error_str).lower()

    if "timed out" in err_lower or "timeout" in err_lower:
        return (
            "⏳ Zeitüberschreitung bei der KI-Antwort (Timeout)\n\n"
            "Die lokale KI (Ollama) hat nicht innerhalb des Timeout-Fensters von 25 Sekunden geantwortet.\n\n"
            "• Mögliche Ursache: Dies tritt fast immer beim ERSTEN Start auf (Cold Start), da Ollama das schwere Sprachmodell erst von der Festplatte in den Hauptspeicher (RAM) laden muss, oder wenn der Prozessor des Servers stark ausgelastet ist.\n"
            "• Empfehlung: Bitte warte ca. 10 bis 15 Sekunden (damit Ollama den Ladevorgang im Hintergrund abschließen kann) und klicke dann erneut auf 'Validieren'. Sobald das Modell im Speicher liegt, antwortet es in unter 5 Sekunden!"
        )
    elif "connection refused" in err_lower or "unreachable" in err_lower or "refused" in err_lower:
        return (
            "🔌 Verbindung zum KI-Dienst fehlgeschlagen\n\n"
            "Der lokale Ollama-Daemon unter http://host.docker.internal:11434 konnte nicht kontaktiert werden.\n\n"
            "• Mögliche Ursache: Der Ollama-Service läuft auf dem Server nicht, oder die Docker-Container-Netzwerkbrücke blockiert den Port.\n"
            "• Empfehlung: Bitte melde dich in der Server-Konsole an und prüfe den Dienststatus (z. B. mit 'sudo systemctl status ollama' oder 'docker ps')."
        )
    elif "404" in err_lower or "not found" in err_lower:
        return (
            f"❌ Modell nicht gefunden (404 Not Found)\n\n"
            f"Das ausgewählte KI-Modell '{model_name}' ist auf dem Ollama-Server nicht vorhanden.\n\n"
            f"• Empfehlung: Bitte melde dich in der Server-Konsole an und lade das Modell manuell mit dem Befehl 'ollama pull {model_name}' herunter."
        )
    else:
        return (
            f"⚠️ Allgemeiner Fehler der lokalen KI-Verbindung\n\n"
            f"Details: {error_str}\n\n"
            "• Empfehlung: Überprüfe die Auslastung und die Systemprotokolle deines Ollama-Dienstes auf dem VM-Server."
        )


@recruiter_required
def test_gemma(request):
    """Tests the local Gemma AI connection by querying a short test prompt."""
    if request.method == 'POST':
        prompt = request.POST.get('prompt', 'Hallo Gemma, bist du bereit?').strip()
        import time

        payload = {
            "model": get_ai_model(),
            "prompt": prompt,
            "stream": False
        }

        start_time = time.time()
        try:
            success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=20.0)
            latency = round(time.time() - start_time, 2)
            if success:
                reply = res_data.get("response", "").strip()
                log_ai_execution("Verbindungstest", get_ai_model(), latency, True, False, "", False, prompt)
                return JsonResponse({'success': True, 'reply': reply, 'latency': latency})
            else:
                log_ai_execution("Verbindungstest", get_ai_model(), latency, False, False, str(res_data), False, prompt)
                return JsonResponse({'success': False, 'error': str(res_data)})
        except Exception as e:
            latency = round(time.time() - start_time, 2)
            log_ai_execution("Verbindungstest", get_ai_model(), latency, False, False, str(e), False, prompt)
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@hr_admin_required
def get_ai_execution_logs(request):
    """Returns the latest 10 AI execution logs for developer/admin diagnostics."""
    import json
    try:
        from ..models import AuditLog
        logs = AuditLog.objects.filter(action="AI_EXECUTION").order_by('-createdAt')[:10]
        data = []
        for log in logs:
            try:
                meta = json.loads(log.metadataJson)
            except Exception:
                meta = {}
            data.append({
                'id': str(log.id),
                'action_name': log.userId or "KI-Aktion",
                'createdAt': log.createdAt.strftime('%Y-%m-%d %H:%M:%S'),
                'model': meta.get('model', 'gemma:2b'),
                'latency': meta.get('latency', 0),
                'success': meta.get('success', False),
                'fallback_mode': meta.get('fallback_mode', False),
                'error_msg': meta.get('error_msg', ''),
                'custom_prompt_active': meta.get('custom_prompt_active', False),
                'prompt_snippet': meta.get('prompt_snippet', '')
            })
        return JsonResponse({'success': True, 'logs': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@recruiter_required
def gemma_agg_check(request):
    """Checks job text for AGG violations (discrimination) using local Gemma asynchronously."""
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if not text:
            return JsonResponse({'success': False, 'error': 'Kein Text übermittelt.'})

        # Get custom prompt from DB
        custom_prompt = ""
        try:
            setting = SystemSetting.objects.filter(key="AI_AGG_PROMPT").first()
            if setting and setting.value.strip():
                custom_prompt = setting.value.strip()
        except Exception:
            pass

        if custom_prompt:
            prompt = f"{custom_prompt}\n\nAusschreibungstext zum Prüfen:\n{text}"
        else:
            prompt = f"""Du bist der SecurATS AGG-Konformitätsprüfer (basierend auf Gemma).
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

        import json
        import uuid

        from ..models import AuditLog

        task_id = uuid.uuid4()

        # Save a pending task status
        AuditLog.objects.create(
            action="AI_TASK_PENDING",
            userId=str(task_id),
            metadataJson=json.dumps({"status": "pending", "type": "AGG_CHECK"})
        )


        def run_async_agg_check_worker():
            payload = {
                "model": get_ai_model(),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300,
                    "top_k": 20,
                    "top_p": 0.5
                }
            }

            import time
            start_time = time.time()
            try:
                # Asynchronous worker timeout of 80 seconds
                success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=80.0)
                latency = round(time.time() - start_time, 2)
                if success:
                    reply = res_data.get("response", "").strip()

                    violations = []
                    optimized_text = text

                    parsed_json, is_json = try_parse_json_reply(reply)
                    if is_json:
                        status_val = str(parsed_json.get("status", "")).strip().lower()
                        is_green = status_val in ["grün", "gruen", "green", "konform", "safe", "ok", "compliant"]

                        if is_green:
                            violations = []
                        else:
                            viols = parsed_json.get("violations") or parsed_json.get("verstoesse") or parsed_json.get("verstöße") or []
                            if isinstance(viols, list):
                                violations = [str(v).strip() for v in viols if str(v).strip()]
                            elif isinstance(viols, str):
                                violations = [v.strip() for v in viols.split("\n") if v.strip()]
                            else:
                                violations = [str(viols).strip()] if viols else []

                        opt_text = parsed_json.get("optimized_text") or parsed_json.get("optimized") or parsed_json.get("text")
                        if opt_text:
                            optimized_text = str(opt_text).strip()
                    else:
                        reply_lower = reply.lower()
                        import re

                        opt_headers = [
                            "=== optimierter text ===",
                            "optimierter text-vorschlag:",
                            "optimierter text:",
                            "optimierter text vorschlag:"
                        ]
                        opt_header_found = None
                        for h in opt_headers:
                            if h in reply_lower:
                                opt_header_found = h
                                break

                        if opt_header_found:
                            idx = reply_lower.find(opt_header_found)
                            opt_part = reply[idx + len(opt_header_found):].strip()
                            violation_part = reply[:idx].strip()

                            for h_val in ["=== verstösse ===", "=== verstoesse ===", "=== verstöße ===", "identifizierte risiken:", "ki agg-check ergebnis:"]:
                                violation_part = re.sub(h_val, "", violation_part, flags=re.IGNORECASE)

                            violations = [v.strip().lstrip("-*•# ") for v in violation_part.split("\n") if v.strip()]
                            optimized_text = opt_part
                        elif "=== OPTIMIERTER TEXT ===" in reply:
                            parts = reply.split("=== OPTIMIERTER TEXT ===")
                            opt_part = parts[1].strip()
                            violation_part = parts[0].replace("=== VERSTÖSSE ===", "").strip()
                            violations = [v.strip().lstrip("-*• ") for v in violation_part.split("\n") if v.strip()]
                            optimized_text = opt_part
                        else:
                            violations = [reply]
                            optimized_text = text

                    violations = [v for v in violations if v and "keine verstöße" not in v.lower() and "keine offensichtlichen" not in v.lower() and "keine risiken" not in v.lower()]

                    log_ai_execution("AGG-Check", get_ai_model(), latency, True, False, "", bool(custom_prompt), prompt)

                    AuditLog.objects.create(
                        action="AI_TASK_COMPLETED",
                        userId=str(task_id),
                        metadataJson=json.dumps({
                            "status": "completed",
                            "success": True,
                            "violations": violations,
                            "optimized_text": optimized_text,
                            "original_text": text,
                            "fallback_mode": False,
                            "latency": latency
                        })
                    )
                else:
                    log_ai_execution("AGG-Check", get_ai_model(), latency, False, True, f"Ollama-Fehler: {res_data}", bool(custom_prompt), prompt)
                    raise Exception(str(res_data))
            except Exception as e:
                # Log execution as failure, and trigger regex fallback
                latency = round(time.time() - start_time, 2)
                log_ai_execution("AGG-Check", get_ai_model(), latency, False, True, str(e), bool(custom_prompt), prompt)

                violations = []
                optimized_text = text
                text_lower = text.lower()
                import re

                custom_lower = custom_prompt.lower()
                junior_whitelisted = "junior" in custom_lower and ("ok" in custom_lower or "erlaubt" in custom_lower or "bag" in custom_lower or "keine änderung" in custom_lower or "keine aenderung" in custom_lower or "nicht das alter" in custom_lower)
                senior_whitelisted = "senior" in custom_lower and ("ok" in custom_lower or "erlaubt" in custom_lower or "bag" in custom_lower or "keine änderung" in custom_lower or "keine aenderung" in custom_lower or "nicht das alter" in custom_lower)

                if "jung" in text_lower or "junge" in text_lower:
                    violations.append("Mögliche Altersdiskriminierung durch das Wort 'jung/junge'. Empfohlen: 'dynamische/engagierte Talente (m/w/d)'.")
                    optimized_text = re.sub(r'\bjunges\b', 'dynamisches', optimized_text, flags=re.IGNORECASE)
                    optimized_text = re.sub(r'\bjunge\b', 'dynamische', optimized_text, flags=re.IGNORECASE)
                    optimized_text = re.sub(r'\bjung\b', 'dynamisch', optimized_text, flags=re.IGNORECASE)
                    optimized_text = re.sub(r'\bjungen\b', 'dynamischen', optimized_text, flags=re.IGNORECASE)

                if "junior" in text_lower and not junior_whitelisted:
                    violations.append("Formulierung 'Junior' im Stellentitel oder Text kann als Altersdiskriminierung (Bevorzugung jüngerer Bewerber) ausgelegt werden. Empfehlung: Angabe konkreter Berufserfahrung (z. B. 'mit erste Praxiserfahrung / Berufseinsteiger') statt Altersbegriffen.")
                    optimized_text = re.sub(r'\bJunior\b', '', optimized_text)
                    optimized_text = re.sub(r'\bjunior\b', 'mit erster Praxiserfahrung', optimized_text, flags=re.IGNORECASE)

                if "senior" in text_lower and not senior_whitelisted:
                    violations.append("Formulierung 'Senior' im Stellentitel oder Text kann als Altersdiskriminierung (Benachteiligung jüngerer Bewerber) ausgelegt werden. Empfehlung: Angabe konkreter Berufserfahrung (z. B. 'mit mehrjähriger Berufserfahrung') statt Altersbegriffen.")
                    optimized_text = re.sub(r'\bSenior\b', '', optimized_text)
                    optimized_text = re.sub(r'\bsenior\b', 'mit mehrjähriger Berufserfahrung', optimized_text, flags=re.IGNORECASE)

                if "arzt" in text_lower and "ärztin" not in text_lower and "m/w/d" not in text_lower:
                    violations.append("Geschlechtsspezifische Formulierung 'Arzt'. Empfohlen: 'Arzt/Ärztin (m/w/d)'.")
                    optimized_text = re.sub(r'\barzt\b', 'Arzt/Ärztin (m/w/d)', optimized_text, flags=re.IGNORECASE)

                if "gesund" in text_lower:
                    violations.append("Formulierung 'gesund' diskriminiert potenziell Bewerber mit chronischen Erkrankungen oder körperlichen Einschränkungen.")
                    optimized_text = re.sub(r'\bgesund\b', 'qualifiziert', optimized_text, flags=re.IGNORECASE)

                if "belastbar" in text_lower:
                    violations.append("Formulierung 'belastbar' kann chronisch kranke oder behinderte Menschen abschrecken. Empfohlen: 'zuverlässig' oder 'engagiert'.")
                    optimized_text = re.sub(r'\bbelastbar\b', 'engagiert', optimized_text, flags=re.IGNORECASE)

                # Entgelttransparenz (EU-RL 2023/970, Art. 5 Abs. 2):
                # Gehaltshistorie-Aufforderungen im Anzeigentext melden
                from ..pay_transparency import salary_history_violation
                _pay_hit = salary_history_violation(text)
                if _pay_hit:
                    violations.append(
                        f"Unzulässige Gehaltshistorie-Abfrage ('{_pay_hit}'): Nach "
                        "EU-RL 2023/970 Art. 5 Abs. 2 darf nicht nach aktuellem oder "
                        "früherem Gehalt gefragt werden. Zulässig: Frage nach der "
                        "Gehaltsvorstellung.")

                AuditLog.objects.create(
                    action="AI_TASK_COMPLETED",
                    userId=str(task_id),
                    metadataJson=json.dumps({
                        "status": "completed",
                        "success": True,
                        "violations": violations,
                        "optimized_text": optimized_text,
                        "original_text": text,
                        "fallback_mode": True,
                        "error_msg": classify_ai_error(e, get_ai_model()),
                        "latency": latency
                    })
                )

        _run_in_background(run_async_agg_check_worker)

        return JsonResponse({'success': True, 'async': True, 'task_id': str(task_id)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@recruiter_required
def gemma_agg_check_status(request, task_id):
    """Checks the status of an asynchronous AGG checker background task."""
    import json

    from ..models import AuditLog

    try:
        task = AuditLog.objects.filter(action="AI_TASK_COMPLETED", userId=str(task_id)).first()
        if task:
            res_data = json.loads(task.metadataJson)
            return JsonResponse({'success': True, 'status': 'completed', **res_data})

        pending = AuditLog.objects.filter(action="AI_TASK_PENDING", userId=str(task_id)).first()
        if pending:
            return JsonResponse({'success': True, 'status': 'pending'})

        return JsonResponse({'success': False, 'error': 'Task nicht gefunden.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@recruiter_required
def gemma_translate_simple_german(request):
    """Translates CMS page text or email text into Simple German (Leichte Sprache) for accessibility."""
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if not text:
            return JsonResponse({'success': False, 'error': 'Kein Text übermittelt.'})

        prompt = f"""
        Du bist der SecurATS Übersetzer für Leichte Sprache (basierend auf Gemma).
        Übersetze den folgenden Text in Leichte Sprache (barrierefrei, WCAG/BFSG compliant).
        Verwende kurze Sätze, einfache Wörter, erkläre schwierige Begriffe und verzichte auf Metaphern.

        Text zum Übersetzen:
        {text}

        NUR die Übersetzung ausgeben.
        """

        payload = {
            "model": get_ai_model(),
            "prompt": prompt,
            "stream": False
        }

        import time
        start_time = time.time()
        try:
            success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=28.0)
            latency = round(time.time() - start_time, 2)
            if success:
                reply = res_data.get("response", "").strip()
                log_ai_execution("Leichte Sprache", get_ai_model(), latency, True, False, "", False, prompt)
                return JsonResponse({'success': True, 'result': reply})
            else:
                log_ai_execution("Leichte Sprache", get_ai_model(), latency, False, True, f"Ollama-Fehler: {res_data}", False, prompt)
        except Exception as e:
            latency = round(time.time() - start_time, 2)
            log_ai_execution("Leichte Sprache", get_ai_model(), latency, False, True, str(e), False, prompt)

        # Fallback
        sentences = text.split(".")
        short_sentences = []
        for s in sentences:
            if len(s.strip()) > 3:
                short_sentences.append(s.strip() + ".")
        reply = "📖 Leichte Sprache Übersetzung (Fallback-Modus):\n\n" + " ".join(short_sentences)
        return JsonResponse({'success': True, 'result': reply})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@hr_admin_required
def validate_ai_prompt(request):
    """Validates the current custom AGG or Leichte Sprache prompt by running it on a test input asynchronously."""
    if request.method == 'POST':
        prompt_type = request.POST.get('type', 'AGG').strip()
        custom_prompt = request.POST.get('prompt', '').strip()

        if not custom_prompt:
            return JsonResponse({'success': False, 'error': 'Kein Prompt übermittelt.'})

        # Realistic, non-faked test text matching user expectations
        test_text = "Wir suchen ab sofort einen belastbaren Junior-Softwareentwickler (m/w/d) zur Verstärkung des Teams."

        if prompt_type == 'AGG':
            prompt = f"{custom_prompt}\n\nAusschreibungstext zum Prüfen:\n{test_text}"
        else:
            prompt = f"{custom_prompt}\n\nText zum Übersetzen:\n{test_text}"

        import json
        import uuid

        from ..models import AuditLog

        task_id = uuid.uuid4()

        # Save a pending task status
        AuditLog.objects.create(
            action="AI_TASK_PENDING",
            userId=str(task_id),
            metadataJson=json.dumps({"status": "pending", "type": f"VALIDATE_{prompt_type}"})
        )


        def run_async_validate_worker():
            payload = {
                "model": get_ai_model(),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300,
                    "top_k": 20,
                    "top_p": 0.5
                }
            }

            import time
            start_time = time.time()
            try:
                # Asynchronous worker timeout of 85 seconds
                success, res_data = make_ollama_request(get_ollama_url(), payload, timeout=85.0)
                latency = round(time.time() - start_time, 2)
                if success:
                    reply = res_data.get("response", "").strip()
                    reply_lower = reply.lower()

                    if prompt_type == 'AGG':
                        parsed_json, is_json = try_parse_json_reply(reply)
                        if is_json:
                            log_ai_execution("Prompt-Validierung (AGG-JSON)", get_ai_model(), latency, True, False, "", True, prompt)
                            status_val = str(parsed_json.get("status", "")).strip().lower()
                            is_green = status_val in ["grün", "gruen", "green", "konform", "safe", "ok", "compliant"]

                            if is_green:
                                msg = 'Der Prompt wurde erfolgreich im JSON-Format ausgeführt und die Stellenausschreibung wurde als AGG-konform ("GRÜN") eingestuft.'
                            else:
                                msg = 'Der Prompt wurde erfolgreich im JSON-Format ausgeführt. Es wurden AGG-Risiken ("ROT") identifiziert.'

                            result = {
                                'valid': True,
                                'reply_preview': reply[:300] + "...",
                                'message': msg
                            }
                        else:
                            opt_headers = [
                                "=== optimierter text ===",
                                "optimierter text-vorschlag:",
                                "optimierter text:",
                                "optimierter text vorschlag:"
                            ]
                            opt_header_found = None
                            for h in opt_headers:
                                if h in reply_lower:
                                    opt_header_found = h
                                    break

                            has_delimiters = opt_header_found is not None or "=== OPTIMIERTER TEXT ===" in reply

                            if has_delimiters:
                                log_ai_execution("Prompt-Validierung (AGG)", get_ai_model(), latency, True, False, "", True, prompt)
                                result = {
                                    'valid': True,
                                    'reply_preview': reply[:250] + "...",
                                    'message': 'Der Prompt wurde erfolgreich von der lokalen KI angewendet und das Antwortformat ist korrekt strukturiert.'
                                }
                            else:
                                log_ai_execution("Prompt-Validierung (AGG)", get_ai_model(), latency, True, True, "Warnung: Keine standardmäßigen Antwort-Trenner gefunden.", True, prompt)
                                result = {
                                    'valid': False,
                                    'reply_preview': reply[:300] + "...",
                                    'message': 'Die KI hat geantwortet, aber es wurden keine standardmäßigen Trenner wie "=== OPTIMIERTER TEXT ===" oder "=== VERSTÖSSE ===" im Antworttext gefunden. Das System wird versuchen, die Antwort als Freitext anzuzeigen, dies kann jedoch zu ungenauen Darstellungen führen.'
                                }
                    else:
                        if reply and reply != test_text:
                            log_ai_execution("Prompt-Validierung (Easy)", get_ai_model(), latency, True, False, "", True, prompt)
                            result = {
                                'valid': True,
                                'reply_preview': reply[:250] + "...",
                                'message': 'Der Prompt für Leichte Sprache wurde erfolgreich validiert.'
                            }
                        else:
                            log_ai_execution("Prompt-Validierung (Easy)", get_ai_model(), latency, True, True, "Fehler bei der Übersetzung.", True, prompt)
                            result = {
                                'valid': False,
                                'reply_preview': reply[:200] + "...",
                                'message': 'Der Antworttext der KI ist leer oder identisch mit dem Ausgangstext.'
                            }

                    AuditLog.objects.create(
                        action="AI_TASK_COMPLETED",
                        userId=str(task_id),
                        metadataJson=json.dumps({
                            "status": "completed",
                            "success": True,
                            "latency": latency,
                            **result
                        })
                    )
                else:
                    log_ai_execution("Prompt-Validierung", get_ai_model(), latency, False, True, f"Ollama-Fehler: {res_data}", True, prompt)
                    detailed_error = classify_ai_error(res_data, get_ai_model())
                    AuditLog.objects.create(
                        action="AI_TASK_COMPLETED",
                        userId=str(task_id),
                        metadataJson=json.dumps({
                            "status": "completed",
                            "success": False,
                            "error": detailed_error
                        })
                    )
            except Exception as e:
                latency = round(time.time() - start_time, 2)
                log_ai_execution("Prompt-Validierung", get_ai_model(), latency, False, True, str(e), True, prompt)
                detailed_error = classify_ai_error(e, get_ai_model())
                AuditLog.objects.create(
                    action="AI_TASK_COMPLETED",
                    userId=str(task_id),
                    metadataJson=json.dumps({
                        "status": "completed",
                        "success": False,
                        "error": detailed_error
                    })
                )

        _run_in_background(run_async_validate_worker)

        return JsonResponse({'success': True, 'async': True, 'task_id': str(task_id)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@hr_admin_required
def validate_ai_prompt_status(request, task_id):
    """Checks the status of an asynchronous custom prompt validation background task."""
    import json

    from ..models import AuditLog

    try:
        task = AuditLog.objects.filter(action="AI_TASK_COMPLETED", userId=str(task_id)).first()
        if task:
            res_data = json.loads(task.metadataJson)
            return JsonResponse({'success': True, 'status': 'completed', **res_data})

        pending = AuditLog.objects.filter(action="AI_TASK_PENDING", userId=str(task_id)).first()
        if pending:
            return JsonResponse({'success': True, 'status': 'pending'})

        return JsonResponse({'success': False, 'error': 'Task nicht gefunden.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@hr_admin_required
def save_ai_settings(request):
    """Saves all consolidated AI settings from the KI-Steuerungszentrum form."""
    if request.method == 'POST':
        tone = request.POST.get('AI_TONE', 'EMPATHETIC').strip()
        lang = request.POST.get('AI_LANGUAGE', 'DE_DU').strip()
        auto_reject = 'true' if request.POST.get('AI_AUTO_REJECT_ENABLED') == 'on' or request.POST.get('AI_AUTO_REJECT_ENABLED') == 'true' else 'false'
        th_d = request.POST.get('AI_THRESHOLD_D_REJECT', '15').strip()
        th_c = request.POST.get('AI_THRESHOLD_C_WAITLIST', '50').strip()
        th_a = request.POST.get('AI_THRESHOLD_A_INVITE', '80').strip()
        cv_learning = 'true' if request.POST.get('AI_CV_LEARNING_MODE') == 'on' or request.POST.get('AI_CV_LEARNING_MODE') == 'true' else 'false'
        agg_check = 'true' if request.POST.get('AI_AGG_CHECK_ENABLED') == 'on' or request.POST.get('AI_AGG_CHECK_ENABLED') == 'true' else 'false'
        agg_prompt = request.POST.get('AI_AGG_PROMPT', '').strip()
        translate_easy = 'true' if request.POST.get('AI_TRANSLATE_EASY_LANGUAGE') == 'on' or request.POST.get('AI_TRANSLATE_EASY_LANGUAGE') == 'true' else 'false'
        easy_prompt = request.POST.get('AI_EASY_LANGUAGE_PROMPT', '').strip()

        settings_dict = {
            'AI_TONE': tone,
            'AI_LANGUAGE': lang,
            'AI_AUTO_REJECT_ENABLED': auto_reject,
            'AI_THRESHOLD_D_REJECT': th_d,
            'AI_THRESHOLD_C_WAITLIST': th_c,
            'AI_THRESHOLD_A_INVITE': th_a,
            'AI_CV_LEARNING_MODE': cv_learning,
            'AI_AGG_CHECK_ENABLED': agg_check,
            'AI_AGG_PROMPT': agg_prompt,
            'AI_TRANSLATE_EASY_LANGUAGE': translate_easy,
            'AI_EASY_LANGUAGE_PROMPT': easy_prompt,
        }

        with transaction.atomic():
            for key, value in settings_dict.items():
                setting, created = SystemSetting.objects.get_or_create(key=key, defaults={'value': value})
                if not created:
                    setting.value = value
                    setting.save()

            AuditLog.objects.create(
                action="UPDATE_AI_SETTINGS",
                metadataJson=json.dumps({"keys": list(settings_dict.keys())})
            )

        return redirect('ats:dashboard')
    return redirect('ats:dashboard')


# --- Einladen: lokaler KI-Feinschliff fuer Nachrichten -------------------------
@recruiter_required
def polish_message(request):
    """Formuliert eine Nachricht an Bewerbende hoeflich/klar um – vollstaendig lokal.

    Guardrails: Der Text laeuft als nicht vertrauenswuerdige Eingabe durch
    ai_safety (auch interne Nutzer koennen nichts injizieren); die KI erhaelt
    KEINE weiteren Bewerberdaten. Ohne erreichbares Ollama kommt der
    Originaltext unveraendert zurueck – der Flow bricht nie.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    text = (request.POST.get('text') or '').strip()[:4000]
    if not text:
        return JsonResponse({'error': 'Kein Text.'}, status=400)

    from ..ai_safety import PROMPT_VERSION, compose_system_prompt, wrap_untrusted
    payload = {
        "model": get_ai_model(),
        "system": compose_system_prompt() + (
            " Du überarbeitest eine Einladungs-Nachricht an eine Bewerberin/einen "
            "Bewerber: freundlich, klar, AGG-neutral (keine Aussagen zu Alter, "
            "Geschlecht, Herkunft, Religion), Sie-Form, maximal gleiche Länge. "
            "Platzhalter in doppelten eckigen Klammern und Namen unverändert lassen. "
            "Antworte NUR mit dem überarbeiteten Text."),
        "prompt": wrap_untrusted(text),
        "stream": False,
        "options": {"temperature": 0.3},
        "keep_alive": "10m",
    }
    import time
    start = time.time()
    try:
        ok, data = make_ollama_request(get_ollama_url(), payload, timeout=20.0)
        latency = round(time.time() - start, 2)
        if ok and (data.get('response') or '').strip():
            polished = data['response'].strip()[:4000]
            log_ai_execution("Einladung-Feinschliff", get_ai_model(), latency, True,
                             False, "", False, prompt_used=text,
                             tokens=data.get('eval_count'), prompt_version=PROMPT_VERSION)
            return JsonResponse({'polished': polished, 'used_ai': True,
                                 'note': 'Überarbeitet – bitte vor dem Senden prüfen.'})
    except Exception:
        logger.exception("KI-Feinschliff nicht verfügbar")
    return JsonResponse({'polished': text, 'used_ai': False,
                         'note': 'Lokale KI nicht erreichbar – Text unverändert.'})


# --- B12 (Ausbau): KI-Tonalitäts-Overlay für Job-Vorlagen --------------------
@hr_admin_required
def apply_template_tone(request):
    """Formuliert Vorlagen-Inhalt via lokaler KI in eine Ziel-Tonalität um.

    Trennt Inhalt (Vorlage) von Tonalität (Overlay je Abteilung/Kategorie).
    Fällt bei nicht erreichbarer KI sauber auf den Originaltext zurück.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    content = request.POST.get('content', '') or ''
    tone = (request.POST.get('tone', 'SIE') or 'SIE').upper()
    tone_hint = {
        'DU': 'lockere Du-Ansprache', 'SIE': 'professionelle Sie-Ansprache',
        'HERZLICH': 'herzliche, wertschätzende Ansprache',
        'NUECHTERN': 'nüchterne, sachliche Ansprache',
    }.get(tone, 'professionelle Ansprache')

    reformulated, used_ai = content, False
    if content.strip():
        try:
            prompt = (f"Formuliere den folgenden Stellenausschreibungs-Text in eine {tone_hint} um. "
                      f"Ändere KEINE Fakten, Anforderungen oder Aufgaben. Gib nur den Text zurück:\n\n{content}")
            payload = {"model": get_ai_model(), "prompt": prompt, "stream": False}
            ok, data = make_ollama_request(get_ollama_url("api/generate"), payload, timeout=8.0)
            if ok and isinstance(data, dict) and data.get('response', '').strip():
                reformulated, used_ai = data['response'].strip(), True
        except Exception:
            logger.exception("Ton-Anpassung fehlgeschlagen; Fallback auf Original")
    return JsonResponse({'reformulated': reformulated, 'used_ai': used_ai})


@recruiter_required
def suggest_process(request):
    """Prozess-Berater: schlaegt Screening-/K.O.-Fragen + Prozess-Hinweise vor.

    Regelbasiert (immer verfuegbar) + optional lokale KI fuer Zusatzfragen.
    Governance wird nur ANGEZEIGT (Gate-Info), nie veraendert; wirksam wird
    nichts ohne Speichern durch den Menschen.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    from ..process_advisor import ai_extra_questions, gate_info, rule_based_suggestions
    title = (request.POST.get('title') or '').strip()[:200]
    family_id = request.POST.get('job_family') or ''
    facility_id = request.POST.get('facility') or ''
    family = JobFamily.objects.filter(id=family_id).first() if family_id else None
    facility = Facility.objects.filter(id=facility_id).first() if facility_id else None

    questions, notes = rule_based_suggestions(title, family.name if family else '')
    used_ai = False
    if request.POST.get('with_ai') == '1':
        extra = ai_extra_questions(title, family.name if family else '',
                                   {q['id'] for q in questions})
        if extra:
            questions += extra
            used_ai = True
            notes.append("KI-Zusatzfragen sind bewusst OHNE K.O.-Wirkung "
                         "(keine automatische Absage möglich).")
    return JsonResponse({
        'questions': questions,
        'notes': notes,
        'gate': gate_info(facility),
        'used_ai': used_ai,
    })


# --- WP5: Lokaler KI-Analyst „Frag deine Daten" (§4.3) ------------------------
@any_staff_required
def analytics_ask(request):
    """Beantwortet Fragen zu den eigenen Recruiting-Daten – vollständig lokal.

    Der KI werden ausschließlich aggregierte, PII-freie Kennzahlen übergeben
    (build_data_summary). Die Frage wird als nicht vertrauenswürdige Eingabe
    gekapselt (ai_safety) – auch interne Nutzer können keine Prompts injizieren.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    question = (request.POST.get('question') or '').strip()[:500]
    if not question:
        return JsonResponse({'error': 'Bitte eine Frage stellen.'}, status=400)

    from ..ai_safety import PROMPT_VERSION, compose_system_prompt, wrap_untrusted
    from ..analytics import build_data_summary
    apps = scope_applications(request.user, Application.objects.all())
    summary = build_data_summary(apps)

    payload = {
        "model": get_ai_model(),
        "system": compose_system_prompt() + (
            " Du bist zusätzlich Recruiting-Daten-Analyst: Beantworte Fragen NUR auf "
            "Basis der übergebenen aggregierten Kennzahlen, auf Deutsch, in 2-5 Sätzen. "
            "Erfinde keine Zahlen. Fehlen Daten für eine Antwort, sage das klar."),
        "prompt": (f"--- KENNZAHLEN (vertrauenswürdig, aggregiert) ---\n{summary}\n--- ENDE ---\n\n"
                   f"Frage der nutzenden Person:\n{wrap_untrusted(question)}"),
        "stream": False,
        "options": {"temperature": 0.2},
        "keep_alive": "10m",
    }
    import time
    start = time.time()
    try:
        ok, data = make_ollama_request(get_ollama_url(), payload, timeout=28.0)
        latency = round(time.time() - start, 2)
        if ok and (data.get('response') or '').strip():
            answer = data['response'].strip()[:2000]
            log_ai_execution("KI-Analyst", get_ai_model(), latency, True, False, "", False,
                             prompt_used=question, tokens=data.get('eval_count'),
                             prompt_version=PROMPT_VERSION)
            return JsonResponse({'answer': answer, 'used_ai': True, 'latency': latency})
        log_ai_execution("KI-Analyst", get_ai_model(), latency, False, True, str(data), False,
                         prompt_used=question, prompt_version=PROMPT_VERSION)
    except Exception as e:
        logger.exception("KI-Analyst nicht verfügbar")
        log_ai_execution("KI-Analyst", get_ai_model(), None, False, True, str(e), False,
                         prompt_used=question, prompt_version=PROMPT_VERSION)
    return JsonResponse({
        'answer': ("Die lokale KI ist gerade nicht erreichbar. Diagnose: "
                   "`python manage.py ai_doctor`. Die Kennzahlen-Ansicht oben bleibt "
                   "vollständig nutzbar."),
        'used_ai': False,
    })


def healthz_ai(request):
    """WP2/L1: Leichtgewichtiger Health-Check der LLM-Anbindung (für Monitoring)."""
    import json as _json
    import urllib.request
    model = get_ai_model()
    try:
        with urllib.request.urlopen(get_ollama_url("api/tags"), timeout=3) as r:
            tags = _json.loads(r.read().decode("utf-8"))
        installed = [m.get("name", "") for m in tags.get("models", [])]
        model_ready = any(m.split(":")[0] == model.split(":")[0] for m in installed)
        status = "ok" if model_ready else "degraded"
        return JsonResponse({"status": status, "reachable": True,
                             "model": model, "model_ready": model_ready}, status=200 if model_ready else 503)
    except Exception as e:
        return JsonResponse({"status": "down", "reachable": False,
                             "model": model, "error": str(e)[:200]}, status=503)


def _get_embedding(text):
    """Holt ein Embedding von Ollama. Gibt (vektor, modell) zurueck ODER wirft.

    Kein Schein: Schlaegt der Aufruf fehl, propagiert die Ausnahme - der
    Aufrufer entscheidet dann ehrlich (kein Profil, klare Meldung).
    """
    import json as _json
    model = get_ai_model()
    url = get_ollama_url("api/embeddings")
    # Ollama-Embedding-API: {"model": ..., "prompt": ...} -> {"embedding": [...]}
    resp = make_ollama_request(url, {"model": model, "prompt": text[:8000]},
                               timeout=20.0)
    if not resp:
        raise RuntimeError("Ollama nicht erreichbar")
    if isinstance(resp, str):
        resp = _json.loads(resp)
    vec = resp.get("embedding") if isinstance(resp, dict) else None
    if not vec or not isinstance(vec, list):
        raise RuntimeError("Ollama lieferte kein Embedding")
    return vec, model


def _extract_pdf_text(django_file):
    """Text aus einem hochgeladenen PDF ziehen. Leerer String bei Problemen.

    pypdf fehlt evtl. in einer Minimal-Installation - dann ehrlich leer
    zurueckgeben statt mit ModuleNotFoundError abzustuerzen.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(django_file)
        parts = []
        for page in reader.pages[:15]:      # genug fuer ein CV-Profil
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()
    except Exception:                        # noqa: BLE001
        return ""


@hr_admin_required
def ingest_best_performers(request):
    """Anonymisierte Best-Performer-Lebenslaeufe zu semantischen Profilen
    verarbeiten - ECHT, nicht simuliert.

    Ablauf je Datei: PDF-Text lesen -> Ollama-Embedding -> speichern.
    Ist Ollama nicht erreichbar, wird NICHTS gespeichert und der Nutzer klar
    informiert (frueher lief hier nur ein Fortschrittsbalken, der Erfolg
    vortaeuschte und die Dateien wegwarf).
    """
    from ..models import BestPerformerProfile, JobFamily
    if request.method != 'POST':
        return JsonResponse({'success': False,
                             'error': 'Nur POST.'}, status=405)

    files = request.FILES.getlist('cvs')
    if not files:
        return JsonResponse({'success': False,
                             'error': 'Keine Dateien empfangen.'}, status=400)

    jf_id = request.POST.get('job_family') or None
    job_family = JobFamily.objects.filter(id=jf_id).first() if jf_id else None

    created, skipped = [], []
    for f in files:
        text = _extract_pdf_text(f)
        if len(text) < 50:
            skipped.append({'name': f.name,
                            'reason': 'Kein lesbarer Text im PDF.'})
            continue
        try:
            vec, model = _get_embedding(text)
        except Exception as exc:              # noqa: BLE001
            # EHRLICH: kein Profil, echter Grund. Nicht so tun als ob.
            return JsonResponse({
                'success': False,
                'error': 'Die lokale KI (Ollama) ist nicht erreichbar – es '
                         'wurde NICHTS gespeichert. ' + classify_ai_error(
                             exc, get_ai_model()),
                'created': len(created),
            }, status=503)

        label = (f.name.rsplit('.', 1)[0] or 'Profil')[:200]
        prof = BestPerformerProfile.objects.create(
            label=label, jobFamily=job_family, model=model,
            dim=len(vec), vectorJson=vec,
            createdBy=request.user if request.user.is_authenticated else None)
        write_audit('BEST_PERFORMER_INGESTED', user=request.user,
                    profile=str(prof.id), dim=len(vec))
        created.append({'label': label, 'dim': len(vec)})

    return JsonResponse({
        'success': True,
        'created': created,
        'skipped': skipped,
        'total_profiles': BestPerformerProfile.objects.count(),
        'message': (f'{len(created)} Profil(e) aus echten Embeddings '
                    f'gespeichert.' + (f' {len(skipped)} übersprungen.'
                                       if skipped else '')),
    })


@hr_admin_required
def best_performer_profiles(request):
    """Verwaltung: vorhandene Profile ansehen und loeschen."""
    from ..models import BestPerformerProfile
    if request.method == 'POST' and request.POST.get('delete_id'):
        prof = BestPerformerProfile.objects.filter(
            id=request.POST['delete_id']).first()
        if prof:
            write_audit('BEST_PERFORMER_DELETED', user=request.user,
                        profile=str(prof.id))
            prof.delete()
        return JsonResponse({'success': True,
                             'total': BestPerformerProfile.objects.count()})
    profs = [{'id': str(p.id), 'label': p.label, 'dim': p.dim,
              'model': p.model,
              'jobFamily': p.jobFamily.name if p.jobFamily else None,
              'createdAt': p.createdAt.strftime('%d.%m.%Y')}
             for p in BestPerformerProfile.objects.all()]
    return JsonResponse({'profiles': profs, 'total': len(profs)})

