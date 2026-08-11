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

__all__ = ["get_ollama_url", "get_ai_model", "make_ollama_request", "evaluate_with_local_gemma", "try_parse_json_reply", "log_ai_execution", "classify_ai_error", "test_gemma", "get_ai_execution_logs", "gemma_agg_check", "gemma_agg_check_status", "gemma_translate_simple_german", "gemma_translate_english", "validate_ai_prompt", "validate_ai_prompt_status", "save_ai_settings", "polish_message", "apply_template_tone", "suggest_process", "suggest_job_draft", "analytics_ask", "healthz_ai", "ingest_best_performers", "best_performer_profiles"]



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


#: Gefundene Basis-Adresse (host:port) samt Zeitpunkt - siehe _discover_ollama_base.
_OLLAMA_BASE_CACHE: tuple[float, str] | None = None

#: Wie lange eine Suche gilt. Kurz genug, dass ein spaeter gestarteter Ollama
#: von selbst gefunden wird, lang genug, dass eine Schleife von KI-Aufrufen
#: nicht bei jedem Schritt neu sucht.
OLLAMA_DISCOVERY_TTL = 60.0


def reset_ollama_url_cache() -> None:
    """Suche vergessen - fuer Tests und fuer `ai_doctor`, das den echten
    Zustand sehen soll statt einer Minute alter Erkenntnis."""
    global _OLLAMA_BASE_CACHE
    _OLLAMA_BASE_CACHE = None


def _discover_ollama_base(port: str) -> str:
    """Sucht die erreichbare Ollama-Adresse - hoechstens einmal je TTL.

    WARUM GEPUFFERT: Die Suche probiert zwei TCP-Verbindungen mit je zwei
    Sekunden Zeitlimit und danach eine Namensaufloesung. Sie lief bei JEDEM
    KI-Aufruf erneut - also auch mitten in einer Schleife ueber 30 Bewerbungen,
    und selbst dann, wenn die vorherige Antwort eine Sekunde alt war. Ohne
    laufenden Ollama kostete jeder Aufruf mehrere Sekunden, bevor ueberhaupt
    etwas passierte; in der Testsuite summierte sich das auf Minuten.

    Die Puffer-Zeit ist bewusst kurz: Wer Ollama nachtraeglich startet, muss
    nicht neu starten, sondern wartet hoechstens eine Minute.
    """
    global _OLLAMA_BASE_CACHE
    import socket
    import time

    now = time.monotonic()
    cached = _OLLAMA_BASE_CACHE
    if cached is not None and now - cached[0] < OLLAMA_DISCOVERY_TTL:
        found = cached[1]
        # Ein gepufferter Treffer gilt nur fuer denselben Port.
        if found.endswith(f":{port}"):
            return found

    base = None
    for host in ["host.docker.internal", "127.0.0.1"]:
        try:
            s = socket.create_connection((host, int(port)), timeout=2.0)
            s.close()
            base = f"{host}:{port}"
            break
        except Exception:              # noqa: BLE001 - jeder Fehler = nicht da
            pass

    if base is None:
        # Kein Dienst erreichbar: im Container ist host.docker.internal der Wirt.
        try:
            socket.gethostbyname("host.docker.internal")
            base = f"host.docker.internal:{port}"
        except Exception:              # noqa: BLE001
            base = f"127.0.0.1:{port}"

    _OLLAMA_BASE_CACHE = (now, base)
    return base


def get_ollama_url(endpoint="api/generate"):
    """
    Dynamically determines the Ollama service URL.
    Checks host.docker.internal first (to reach the host from inside the Docker container),
    then falls back to 127.0.0.1 (local execution).

    Der Port kam frueher aus einer festen 11434 - waehrend die Diagnose
    (`manage.py ai_doctor`) empfahl, "Host/Port via OLLAMA_HOST/OLLAMA_PORT"
    zu pruefen. Wer dem Rat folgte, aenderte eine Variable, die niemand las.
    Jetzt gilt OLLAMA_PORT wirklich; OLLAMA_HOST darf wie bei Ollama ueblich
    auch "rechner:11500" enthalten.
    """
    port = (os.environ.get("OLLAMA_PORT") or "").strip()
    if not port.isdigit():
        port = "11434"

    # Allow override via environment variable
    env_host = (os.environ.get("OLLAMA_HOST") or "").strip()
    if env_host:
        host_part = env_host if ":" in env_host else f"{env_host}:{port}"
        return f"http://{host_part}/{endpoint}"

    return f"http://{_discover_ollama_base(port)}/{endpoint}"


def get_ai_model():
    """Dynamically retrieves the configured AI model, defaulting to gemma:2b."""
    try:
        setting = SystemSetting.objects.filter(key="AI_MODEL").first()
        if setting and setting.value.strip():
            return setting.value.strip()
    except Exception:
        # Der Standardwert ist ein sinnvoller Rueckfall - aber wenn die
        # Datenbank hier streikt, ist das keine Nebensaechlichkeit.
        logger.exception("AI_MODEL nicht lesbar - benutze Standardmodell")
    return "gemma:2b"


#: Letzte Erreichbarkeits-Antwort samt Zeitpunkt (siehe ollama_reachable).
_OLLAMA_REACHABLE_CACHE: tuple[float, bool] | None = None

#: Kurz halten: Das Abzeichen darf nicht minutenlang eine tote KI als online
#: ausgeben - aber auch nicht bei jedem Seitenaufruf blockieren.
OLLAMA_STATUS_TTL = 20.0


def ollama_reachable() -> bool:
    """Ist die lokale KI erreichbar? Hoechstens einmal je TTL wirklich gefragt.

    WARUM GEPUFFERT: Diese Frage haengt am Dashboard-Abzeichen - also an der
    meistgeoeffneten Seite des Produkts. Sie kostete bei ABWESENDER KI bis zu
    vier Sekunden (zwei Verbindungsversuche a zwei Sekunden), und zwar bei
    JEDEM Aufruf. Genau die Konstellation, die beim Kunden ohne KI-Profil der
    Normalfall ist: Das Dashboard war dort dauerhaft langsam, ohne dass jemand
    den Grund sah.

    Ausserdem nutzt die Pruefung jetzt dieselbe Adresse wie die echten
    KI-Aufrufe. Vorher stand hier fest Port 11434 - wer OLLAMA_PORT setzte,
    bekam ein OFFLINE-Abzeichen ueber einer funktionierenden KI.
    """
    global _OLLAMA_REACHABLE_CACHE
    import socket
    import time
    from urllib.parse import urlsplit

    now = time.monotonic()
    cached = _OLLAMA_REACHABLE_CACHE
    if cached is not None and now - cached[0] < OLLAMA_STATUS_TTL:
        return cached[1]

    parts = urlsplit(get_ollama_url("api/tags"))
    host, port = parts.hostname or "127.0.0.1", parts.port or 11434
    try:
        socket.create_connection((host, port), timeout=2.0).close()
        alive = True
    except OSError:
        alive = False
    _OLLAMA_REACHABLE_CACHE = (now, alive)
    return alive


def reset_ollama_status_cache() -> None:
    """Erreichbarkeits-Antwort vergessen (Tests, Diagnose)."""
    global _OLLAMA_REACHABLE_CACHE
    _OLLAMA_REACHABLE_CACHE = None


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
    """Bewertet das Anschreiben gegen die Anforderungen mit der lokalen KI.

    Ist die KI nicht erreichbar oder ihre Antwort unbrauchbar, wird ein
    Fehler GEWORFEN - frueher fiel die Funktion still auf ein Keyword-Raten
    zurueck (django/python/react/sales ...), das jeder Pflege-Bewerbung ohne
    Tech-Vokabular ein "D - Geringe Uebereinstimmung" verpasste und den
    KI-Ausfall damit als Ergebnis maskierte. Ein erfundener Score ist
    schlimmer als keiner: Aufrufer entscheiden selbst, was ein Ausfall
    bedeutet (Queue: Backoff/FAILED; Bewerbungseingang: ohne Score annehmen
    und zur Nachbewertung einreihen).
    """
    import json

    from ..ai_safety import (
        PROMPT_VERSION,
        build_evaluation_payload,
        build_repair_payload,
        coerce_score,
        default_options,
        tone_applied,
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
                             res_data.get("total_duration"), True, False, "",
                             # Ehrlich protokollieren: nur wenn die Tonalitaet
                             # WIRKLICH als Overlay im Prompt landete. Vorher
                             # stand hier bool(tone_key) - das Nachweisprotokoll
                             # behauptete eine aktive Stilvorgabe, obwohl der
                             # Prompt unveraendert blieb (EU-AI-Act-Nachweis).
                             tone_applied(tone_key),
                             prompt_used=cover_letter,
                             tokens=res_data.get("eval_count"),
                             params=options, prompt_version=PROMPT_VERSION,
                             repaired=repaired,
                             application_id=str(application_id) if application_id else None)
            return score, rationale
        # make_ollama_request hat den Fehler bereits gefangen und (False, ...)
        # geliefert - fuer den Aufrufer ist das derselbe Ausfall.
        raise RuntimeError(f"KI nicht erreichbar: {res_data}")
    except Exception as e:
        logger.exception("Lokales KI-Scoring fehlgeschlagen - KEIN Ersatz-Score")
        log_ai_execution("Bewerbungs-Scoring", get_ai_model(), None, False, True, str(e), False,
                         prompt_used=cover_letter, prompt_version=PROMPT_VERSION,
                         application_id=str(application_id) if application_id else None)
        raise


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
                # KEIN verschluckter Fehler, sondern Ablaufsteuerung: Ein
                # Sprachmodell liefert nun einmal manchmal kein gueltiges
                # JSON. Der Rueckgabewert `(None, False)` IST die Meldung -
                # der Aufrufer wertet sie aus und faellt auf seinen
                # regelbasierten Weg zurueck. Hier zu protokollieren wuerde
                # das Log mit Normalfaellen fluten.
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
    """Startet die AGG-Pruefung eines Stellentextes (Logik in ats/agg_check.py)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'success': False, 'error': 'Kein Text übermittelt.'})

    from ..agg_check import start_check
    task_id = start_check(text)
    return JsonResponse({'success': True, 'async': True, 'task_id': str(task_id)})


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

        # Die KI-Zentrale bietet einen pflegbaren Prompt an - inklusive
        # "Prompt live testen". Der wurde bisher nirgends benutzt: hier stand
        # ein fest verdrahteter Text. Damit testete der Knopf einen Prompt,
        # den das System danach nie verwendete (das Gegenstueck
        # AI_AGG_PROMPT wird sehr wohl gelesen - die Asymmetrie war
        # unsichtbar). Jetzt gilt der gepflegte Prompt, sonst der Default.
        _row = SystemSetting.objects.filter(key='AI_EASY_LANGUAGE_PROMPT').first()
        instruction = ((_row.value.strip() if _row and _row.value else '') or
                       "Du bist der SecurATS Übersetzer für Leichte Sprache. "
                       "Übersetze den folgenden Text in Leichte Sprache "
                       "(barrierefrei, WCAG/BFSG). Verwende kurze Sätze, "
                       "einfache Wörter, erkläre schwierige Begriffe und "
                       "verzichte auf Metaphern.")
        prompt = f"""
        {instruction}

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


@recruiter_required
def gemma_translate_english(request):
    """Englische Fassung der Stellenbeschreibung entwerfen (lokale KI).

    Gleiche Mechanik wie die Leichte Sprache: Der Entwurf landet im Textfeld
    zur Pruefung, nie ungesehen auf der Anzeige. Anders als dort gibt es KEINEN
    deterministischen Fallback - eine Uebersetzung laesst sich nicht durch
    Satzkuerzung ersetzen. Ist die KI nicht erreichbar, sagt die Antwort das,
    und das Feld bleibt unveraendert.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'},
                            status=405)
    text = (request.POST.get('text') or '').strip()
    if not text:
        return JsonResponse({'success': False, 'error': 'Kein Text übermittelt.'})

    _row = SystemSetting.objects.filter(key='AI_ENGLISH_PROMPT').first()
    instruction = ((_row.value.strip() if _row and _row.value else '') or
                   "Du bist der SecurATS Übersetzer für Stellenanzeigen. "
                   "Übersetze den folgenden deutschen Anzeigentext in "
                   "klares, natürliches Englisch (B1-Niveau, freundlich, "
                   "ohne Amtsdeutsch). Erfinde nichts dazu, lass nichts weg "
                   "und nenne KEINE Gehaltszahlen, auch wenn der Text "
                   "welche enthalten sollte.")
    prompt = (f"{instruction}\n\nText zum Übersetzen:\n{text}\n\n"
              "NUR die Übersetzung ausgeben.")
    payload = {"model": get_ai_model(), "prompt": prompt, "stream": False}

    import time
    start_time = time.time()
    try:
        success, res_data = make_ollama_request(get_ollama_url(), payload,
                                                timeout=28.0)
        latency = round(time.time() - start_time, 2)
        if success and (res_data.get("response") or "").strip():
            log_ai_execution("Englische Fassung", get_ai_model(), latency,
                             True, False, "", False, prompt)
            return JsonResponse({'success': True,
                                 'result': res_data["response"].strip()})
        log_ai_execution("Englische Fassung", get_ai_model(), latency,
                         False, False, f"Ollama-Fehler: {res_data}", False, prompt)
    except Exception as e:
        latency = round(time.time() - start_time, 2)
        log_ai_execution("Englische Fassung", get_ai_model(), latency,
                         False, False, str(e), False, prompt)
    return JsonResponse({'success': False,
                         'error': 'KI nicht erreichbar – Feld unverändert.'})


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
        # AI_AUTO_REJECT_ENABLED + AI_THRESHOLD_* entfernt: wurden nur
        # gespeichert, nie durchgesetzt - tote Schalter versprechen
        # Funktionen, die es bewusst nicht gibt (keine automatische
        # KI-Absage; K.O. nur regelbasiert ueber Pflichtkriterien).
        agg_prompt = request.POST.get('AI_AGG_PROMPT', '').strip()
        easy_prompt = request.POST.get('AI_EASY_LANGUAGE_PROMPT', '').strip()
        english_prompt = request.POST.get('AI_ENGLISH_PROMPT', '').strip()

        # Das zentrale KI-Opt-in war bisher nur per Shell schaltbar, obwohl es
        # an vier Stellen wirkt (EU AI Act: Aktivierung ist eine bewusste
        # Entscheidung - dann muss sie auch im Produkt treffbar sein).
        scoring_on = '1' if request.POST.get('AI_SCORING_ENABLED') else '0'
        # AI_ASYNC wirkte seit L6, war aber nur per Shell setzbar - das
        # Queue-Versprechen (Bewerbungsseite wartet nie auf die KI) war im
        # Produkt nicht aktivierbar.
        async_on = '1' if request.POST.get('AI_ASYNC') else '0'
        settings_dict = {
            'AI_SCORING_ENABLED': scoring_on,
            'AI_ASYNC': async_on,
            'AI_TONE': tone,
            'AI_AGG_PROMPT': agg_prompt,
            'AI_EASY_LANGUAGE_PROMPT': easy_prompt,
            'AI_ENGLISH_PROMPT': english_prompt,
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

        return redirect('ats:ki_page')
    return redirect('ats:ki_page')


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


@recruiter_required
def suggest_job_draft(request):
    """Stellen-Entwurf: Beschreibung, Aufgaben und Anforderungen vorbefuellen.

    Regelbasiert aus den Bausteinen des Hauses (immer verfuegbar), optional
    von der lokalen KI ausformuliert. Die Oberflaeche fuellt damit NUR leere
    Felder – nichts wird ueberschrieben, nichts ohne Speichern wirksam.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST erforderlich'}, status=405)
    from ..job_draft import ai_draft_payload, rule_based_draft, validate_ai_draft
    from ..models import Benefit
    title = (request.POST.get('title') or '').strip()[:200]
    family = (JobFamily.objects.filter(id=request.POST.get('job_family')).first()
              if request.POST.get('job_family') else None)
    facility = (Facility.objects.filter(id=request.POST.get('facility')).first()
                if request.POST.get('facility') else None)
    benefit_ids = [b for b in request.POST.getlist('benefits') if b]
    benefit_names = (list(Benefit.objects.filter(id__in=benefit_ids)
                          .order_by('name').values_list('name', flat=True))
                     if benefit_ids else None)

    draft = rule_based_draft(title, family, facility, benefit_names)
    used_ai = False
    if request.POST.get('with_ai') == '1':
        payload = ai_draft_payload(title, family.name if family else '',
                                   draft, get_ai_model())
        try:
            ok, data = make_ollama_request(get_ollama_url(), payload, timeout=25.0)
            if ok:
                draft, used_ai = validate_ai_draft(
                    (data.get('response') or '').strip(), draft)
        except Exception:
            # Der Regel-Entwurf bleibt richtig – aber der Grund gehoert ins
            # Protokoll, sonst sucht jemand, warum "+ KI" nie etwas tut.
            logger.exception("Stellen-Entwurf: KI-Formulierung nicht abrufbar")
    notes = []
    if draft['quellen']:
        notes.append("Quellen: " + ", ".join(draft['quellen']) + ".")
    else:
        notes.append("Keine Textbausteine hinterlegt – der Entwurf ist "
                     "entsprechend knapp. Bausteine pflegen Sie unter "
                     "Einstellungen → Textbausteine.")
    notes.append("Der Entwurf füllt nur leere Felder; die Gehaltsspanne "
                 "kommt weiterhin aus dem Entgeltband.")
    return JsonResponse({
        'description': draft['description'],
        'tasks': draft['tasks'],
        'requirements': draft['requirements'],
        'notes': notes,
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

