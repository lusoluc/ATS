# Refactor: views.py → Domänen-Paket `ats/views/`

**Warum:** Die frühere `ats/views.py` war ~6.260 Zeilen mit 110 Views/Helfern in
einer Datei. Das ist ein Wartungs- und Sicherheitsrisiko: Der im Audit gefundene
fehlende Auth-Decorator auf `schedule_interview` konnte nur deshalb unentdeckt
bleiben, weil niemand die Datei überblickt.

**Was:** Aufteilung in ein Python-Paket mit 12 Domänen-Modulen. **Verhaltensneutral** –
kein Import und keine URL ändert sich, weil `ats/views/__init__.py` alle Namen
re-exportiert (`from .modul import *`). `from ats.views import X` und `views.X` in
`urls.py` funktionieren unverändert.

## Module

| Modul | Inhalt |
|-------|--------|
| `common.py` | Gemeinsame Helfer (keine Abhängigkeit zu anderen View-Modulen) |
| `ai.py` | Lokale KI (Ollama/Gemma): Scoring, AGG-Check, Prompt-Tests, Textwerkzeuge |
| `public.py` | Öffentlich: Stellenbörse, Bewerbung, Kandidatenportal, CMS-Seiten |
| `applications.py` | Kanban-Board, Status, Notizen, CV, Workflow-Automatik |
| `interviews.py` | Termine, Gesprächsrunden, strukturiertes Feedback |
| `jobs.py` | Stellenanzeigen und Job-Vorlagen (inkl. Versionierung) |
| `governance.py` | Freigaben, Gremium, Stellenfreigabe-Ketten, Vertretung, Audit |
| `analytics_views.py` | Analytics-Dashboard und Exporte |
| `cms.py` | Seiten, Landingpages, Blöcke, Branding, Medien |
| `settings_admin.py` | Stammdaten, Workflows, Vorlagen, Import, Kanäle |
| `feeds.py` | Externe Feeds (Stepstone, BA-XML, SAP SF) |
| `auth_views.py` | Login inkl. Brute-Force-Sperre |

**Abhängigkeiten:** gerichteter Baum, **keine Zyklen** (per AST-Analyse geprüft).
Nur `applications → {common, governance}`, `public → {ai, common}`, sowie
`cms/interviews/settings_admin → common`.

## Absicherung

- Verlustfreiheit maschinell geprüft: alle 110 Definitionen genau einmal vorhanden.
- **346 Tests grün** nach dem Umbau (verhaltensneutral).
- Zwei Tests mussten das Mock-Ziel anpassen (Regel „patchen, wo der Name
  nachgeschlagen wird"): `bewerben` nutzt `ats.views.public.evaluate_with_local_gemma`,
  der Queue-Worker das Paket-Level `ats.views.evaluate_with_local_gemma`.

## Hinweis für die Weiterentwicklung

Neue Views ins passende Domänen-Modul legen; öffentliche Namen werden automatisch
re-exportiert. Jede View trägt ihren **eigenen** Auth-Decorator – es gibt KEINE
globale Login-Middleware (siehe SECURITY_AUDIT.md).
