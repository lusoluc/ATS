"""Prozess-Berater: intelligente Prozess-Vorschläge je Stelle – ohne Governance-Umgehung.

Prinzipien:
- **Regelbasiert zuerst** (funktioniert immer, auch ohne KI): kuratierte
  K.O.-/Screening-Bibliothek nach Stichworten im Jobtitel bzw. Jobfamilie.
- **KI optional obendrauf**: die lokale KI darf 1–3 ZUSÄTZLICHE stellenbezogene
  Fragen vorschlagen (injection-gekapselt, striktes JSON, hart validiert).
  Nicht erreichbar → still weglassen.
- **Governance unantastbar**: Das Freigabe-Gate der Einrichtung wird hier nur
  ANGEZEIGT (Info an den Menschen), nie verändert. K.O.-Vorschläge sind
  ausschließlich objektive Muss-Kriterien (Qualifikation/Erlaubnis) – niemals
  AGG-relevante Merkmale.
- **Mensch entscheidet**: Vorschläge füllen nur das Formular vor; wirksam wird
  nichts ohne Speichern.
"""
import json

# (Stichworte im Titel/der Familie, Fragenliste)
RULES = [
    ({"pflegefach", "pflegekraft", "gesundheits- und kranken", "altenpfleg"}, [
        {"id": "examen", "question": "Haben Sie ein abgeschlossenes Examen als Pflegefachkraft?",
         "isMandatory": True, "expectedAnswer": "Ja"},
        {"id": "schicht", "question": "Können Sie im Schichtdienst (Früh/Spät/Nacht) arbeiten?",
         "isMandatory": False, "expectedAnswer": "Ja"},
    ]),
    ({"arzt", "ärzt", "mediziner"}, [
        {"id": "approbation", "question": "Verfügen Sie über eine deutsche Approbation?",
         "isMandatory": True, "expectedAnswer": "Ja"},
    ]),
    ({"fahrer", "logistik", "transport"}, [
        {"id": "fuehrerschein", "question": "Besitzen Sie einen gültigen Führerschein der erforderlichen Klasse?",
         "isMandatory": True, "expectedAnswer": "Ja"},
    ]),
    ({"erzieher", "kita", "pädagog"}, [
        {"id": "anerkennung", "question": "Haben Sie eine staatliche Anerkennung als Erzieher:in bzw. eine gleichwertige Qualifikation?",
         "isMandatory": True, "expectedAnswer": "Ja"},
        {"id": "fuehrungszeugnis", "question": "Können Sie ein erweitertes Führungszeugnis vorlegen?",
         "isMandatory": True, "expectedAnswer": "Ja"},
    ]),
    ({"it", "administrator", "entwickler", "informatik"}, [
        {"id": "berufserfahrung_it", "question": "Haben Sie mindestens zwei Jahre einschlägige Berufserfahrung?",
         "isMandatory": False, "expectedAnswer": "Ja"},
    ]),
    ({"azubi", "ausbildung", "auszubildende"}, [
        # Bewusst KEINE K.O.-Fragen: Azubi-Prozess soll maximal niedrigschwellig sein
    ]),
    ({"reinigung", "lager", "helfer", "küche", "hauswirtschaft"}, [
        # Niedrigschwellig: keine K.O.-Hürden; Erreichbarkeit klärt das Gespräch
    ]),
]

LOW_BARRIER_KEYS = {"azubi", "ausbildung", "auszubildende", "reinigung", "lager",
                    "helfer", "küche", "hauswirtschaft", "praktik"}


def rule_based_suggestions(title: str, family: str):
    """Kuratierte Fragen + Prozess-Hinweise aus Titel/Jobfamilie."""
    haystack = f"{title} {family}".lower()
    questions: list[dict] = []
    notes: list[str] = []
    matched = False
    for keys, qs in RULES:
        if any(k in haystack for k in keys):
            matched = True
            for q in qs:
                if q["id"] not in {x["id"] for x in questions}:
                    questions.append(dict(q))
    if any(k in haystack for k in LOW_BARRIER_KEYS):
        notes.append("Niedrigschwellige Zielgruppe erkannt: bewusst keine K.O.-Fragen "
                     "vorgeschlagen – jede Hürde kostet hier Bewerbungen.")
    if not matched:
        notes.append("Keine Spezial-Regel für diesen Titel – nur allgemeine Hinweise. "
                     "Fragen bei Bedarf manuell oder per KI ergänzen.")
    if questions:
        notes.append("K.O.-Fragen führen bei Nicht-Erfüllung zur automatischen Absage "
                     "(objektive Muss-Kriterien) – bitte nur einsetzen, wenn das "
                     "Kriterium rechtlich/fachlich zwingend ist.")
    return questions, notes


def gate_info(facility):
    """Nur Information – das Gate ist hier nicht veränderbar (Governance)."""
    if facility is None:
        return {"active": False, "text": "Keine Einrichtung gewählt."}
    if facility.requiresApproval:
        from .approvals import approval_chain
        chain = " → ".join(approval_chain(facility))
        return {"active": True,
                "text": (f"Diese Einrichtung ist zustimmungspflichtig: Die Anzeige startet "
                         f"als Entwurf und durchläuft die Freigabekette {chain}. "
                         f"Das ist hier bewusst nicht abschaltbar.")}
    return {"active": False,
            "text": "Keine Freigabepflicht für diese Einrichtung – Anzeige kann direkt veröffentlicht werden."}


def _validate_ai_questions(raw_text: str, existing_ids: set):
    """Hart validieren, was die KI liefert: Struktur, Anzahl, keine K.O.-Eskalation."""
    try:
        data = json.loads(raw_text)
    except (ValueError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    out = []
    for i, item in enumerate(data[:3]):
        q = str(item.get("question", "")).strip() if isinstance(item, dict) else ""
        if not (10 <= len(q) <= 200):
            continue
        # Entgelttransparenz (Art. 5 Abs. 2): auch die KI darf keine
        # Gehaltshistorie-Fragen vorschlagen.
        from .pay_transparency import salary_history_violation
        if salary_history_violation(q):
            continue
        qid = f"ki_{i+1}"
        if qid in existing_ids:
            continue
        # KI-Fragen sind IMMER weiche Fragen – niemals automatische Absage:
        out.append({"id": qid, "question": q, "isMandatory": False, "expectedAnswer": ""})
    return out


def ai_extra_questions(title: str, family: str, existing_ids: set):
    """Optional: 1–3 stellenbezogene Zusatzfragen von der lokalen KI. Fällt still aus."""
    from .ai_safety import compose_system_prompt, wrap_untrusted
    from .views import get_ai_model, get_ollama_url, make_ollama_request
    payload = {
        "model": get_ai_model(),
        "system": compose_system_prompt() + (
            " Schlage 1 bis 3 kurze Screening-Fragen für die genannte Stelle vor. "
            "Nur fachliche/organisatorische Fragen; NIEMALS Fragen zu Alter, "
            "Geschlecht, Herkunft, Religion, Familie oder Gesundheit (AGG). "
            'Antworte NUR als JSON-Liste: [{"question": "..."}] – nichts anderes.'),
        "prompt": wrap_untrusted(f"Stelle: {title} (Bereich: {family})"),
        "stream": False, "format": "json",
        "options": {"temperature": 0.4},
        "keep_alive": "10m",
    }
    try:
        ok, data = make_ollama_request(get_ollama_url(), payload, timeout=12.0)
        if ok:
            return _validate_ai_questions((data.get("response") or "").strip(), existing_ids)
    except Exception:
        pass
    return []


def ensure_minimum_standards(job):
    """Vorstands-Mindeststandards serverseitig durchsetzen (nicht umgehbar).

    Mergt die Pflichtfragen der Jobfamilie in die Stelle: fehlende Fragen
    (Abgleich ueber id ODER Fragetext) werden eingefuegt, bei vorhandenen wird
    isMandatory=True erzwungen. Rueckgabe: Anzahl der Korrekturen (0 = Stelle
    erfuellte den Standard bereits). Aufrufer speichert und auditiert.
    """
    fam = getattr(job, 'jobFamily', None)
    if fam is None:
        return 0
    minimum = fam.minimumQuestionsJson or []
    if not minimum:
        return 0
    current = job.screeningQuestionsJson or []
    if not isinstance(current, list):
        current = []
    changes = 0
    for req in minimum:
        if not isinstance(req, dict) or not req.get('question'):
            continue
        text = str(req['question']).strip().lower()
        existing = next((q for q in current if isinstance(q, dict)
                         and (str(q.get('id')) == str(req.get('id'))
                              or str(q.get('question', '')).strip().lower() == text)),
                        None)
        if existing is None:
            item = dict(req)
            item['isMandatory'] = True
            current.append(item)
            changes += 1
        elif not existing.get('isMandatory'):
            existing['isMandatory'] = True   # Abschwaechen unmoeglich
            changes += 1
    if changes:
        job.screeningQuestionsJson = current
    return changes
