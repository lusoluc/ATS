# AI-DEV Guidelines: SecurATS

**AN ALLE KÜNFTIGEN KI-AGENTEN / LLMs:**
Bevor du an dieser Codebasis arbeitest, lies diese Regeln. Sie sind aus echten
Fehlern dieser Codebasis entstanden – nicht aus Theorie. Zuwiderhandeln
riskiert Sicherheitslücken, kaputte Fachlogik oder das Wiederaufleben bereits
stillgelegter Architektur.

> **Frühere Version dieses Dokuments beschrieb Next.js + Prisma als
> kanonischen Stack.** Das ist überholt. Die Kanon-Entscheidung (siehe
> `NORTHSTAR.md` Abschnitt 6) fiel zugunsten von **Django** – Next.js/Prisma
> und die Express-Ebene liegen vollständig in `legacy/` und werden **nicht
> mehr ausgeliefert**. Next.js-, Prisma- oder Express-Code in `legacy/` ist
> Referenzmaterial für den Feature-Abgleich (`FEATURE_BACKLOG.md`), keine
> Vorlage zum Weiterbauen.

---

## 1. Tech-Stack & Architektur (verbindlich)

* **Framework:** Django 6, klassische server-gerenderte Templates
  (`templates/`, Django-Template-Sprache). Kein React/Next.js im
  ausgelieferten Produkt.
* **App-Layout:** Projekt `securats/` (Settings, URLs, WSGI), App `ats/`
  (Modelle, Views, Business-Logik). Ein Modul je Fachdomäne statt
  Alles-in-`views.py`, wo sinnvoll: `ats/panel.py` (Gremien-Auflösung),
  `ats/approvals.py` (Freigabeketten inkl. Stellenfreigabe/Requisition),
  `ats/blocks.py` (CMS-Baukasten), `ats/questions.py` (Fragen-Registry für
  Screening/Mindeststandards), `ats/importer.py` (CSV/XLSX-Import),
  `ats/analytics.py` (Kennzahlen), `ats/audit.py` (Audit-Kette).
* **Datenbank:** SQLite in Entwicklung, **PostgreSQL in Produktion**
  (Entscheidung wegen Nebenläufigkeit KI-Worker + Web, siehe `OPERATIONS.md`).
  Alle Migrationen unter `ats/migrations/`, sequenziell nummeriert – niemals
  eine Migration nachträglich umschreiben, die schon angewendet wurde.
* **Styling:** Inline-Styles auf CSS-Variablen (`var(--primary)`,
  `var(--space-*)`, `var(--border-radius-*)` etc.), definiert in
  `templates/base.html`. Kein Tailwind, kein CSS-Framework. Wiederverwendbare
  Klassen (`.card`, `.btn`, `.field`, `.data-table`, `.badge`, `.status-badge`)
  liegen ebenfalls in `base.html` – neue Verwaltungsseiten nutzen diese
  Klassen statt Inline-Styles neu zu erfinden.
* **KI-Anbindung:** Lokales Ollama/Gemma, nie Cloud-LLMs. Async über
  `ats/management/commands/ai_worker.py` (eigene Queue), nicht über
  `threading.Thread` (siehe Abschnitt 5, historischer Fund M3).

## 2. Sicherheits-Grundsätze (KRITISCH)

Die Plattform verarbeitet hochsensible Personendaten (Lebensläufe,
Gesundheitsangaben, AGG-relevante Merkmale). Sicherheit hat Vorrang vor
Geschwindigkeit.

### 2.1 BOLA-Vermeidung (Broken Object Level Authorization)
**Nie nur per ID abfragen.** Jede Abfrage, die einer eingeloggten Rolle Daten
zeigt, muss durch den Scope dieser Rolle gefiltert sein.

* **SCHLECHT:** `Application.objects.get(id=app_id)`
* **GUT** (das reale Muster in diesem Repo, `ats/permissions.py`):
  ```python
  app = get_object_or_404(Application, id=app_id)
  if not can_access_application(request.user, app):
      raise Http404("Nicht im Zugriffsbereich.")
  ```
  `has_full_access(user)` und `scope_applications(user, qs)` /
  `scope_jobs(user, qs)` kapseln die BOLA-Logik (Standort-/Einrichtungs-Scope
  über `UserScope`). Neue Listen-Views MÜSSEN durch `scope_*` laufen, neue
  Detail-Views MÜSSEN `can_access_*` prüfen – auch wenn der Aufruf
  „offensichtlich harmlos" wirkt.

### 2.2 CSRF
Alle `@csrf_exempt`-Ausnahmen wurden entfernt. `templates/base.html` enthält
einen globalen `fetch`-Wrapper, der `X-CSRFToken` automatisch an
Same-Origin-POSTs anhängt. **Kein neuer `@csrf_exempt`-Endpunkt**, außer für
öffentliche, unauthentifizierte Webhooks mit eigener Absicherung (Token/IP) –
und dann nur nach expliziter Rücksprache.

### 2.3 PII-Verschlüsselung at-rest
`EncryptedCharField`/`EncryptedTextField` (Fernet, `ats/fields.py`) für alles,
was personenbezogen ist (Name, Telefon, Adresse, E-Mail-Blind-Index). Neue
Felder mit PII-Charakter bekommen den verschlüsselten Feldtyp, nicht
`CharField`. Spalten sind `TEXT` (nicht `max_length`-begrenzt auf DB-Ebene) –
Fernet-Ciphertext ist länger als der Klartext; das war ein realer,
produktionskritischer Bug (siehe `PROJECT_ANALYSIS.md`, Befund C1).

### 2.4 Zero-Data-Transfer-KI
Keine externen APIs, kein Tracking, keine Cloud-Fonts/CDNs im Datenpfad von
Bewerberdaten. KI-Aufrufe gehen ausschließlich an das lokale Ollama.

### 2.5 Prompt-Injection-Schutz
Bei jeder Erweiterung der KI-Anbindung: System-Prompt und Nutzereingaben
strikt trennen; Anweisung an das Modell, Inhalte in `<CV_TEXT>`-artigen Tags
niemals als Instruktion zu behandeln.

## 3. Rechtliche Leitplanken (AGG & DSGVO)

* **AGG:** Kein Bewertungs- oder Scoring-Feature darf Alter, Geschlecht,
  Herkunft, Religion oder Aussehen einbeziehen. KI-Prompts verbieten diese
  Merkmale explizit.
* **Automatische Absage nur bei objektiven K.-o.-Kriterien** – das ist ein
  hart codiertes Prinzip, keine Empfehlung: `isMandatory` + gesetztes
  `expectedAnswer` = K.O.; `isMandatory` ohne `expectedAnswer` = Pflichtfeld
  mit Formular-Fehler, NIE automatische Ablehnung (siehe `ats/questions.py`).
  Wer einen neuen Fragetyp einführt, muss diese Unterscheidung erhalten.
* **Löschung/Retention:** Neue Datenspeicherung braucht einen Bezug zur
  bestehenden Retention-Logik (Command `retention_cleanup` o. ä.), keine
  Speicherung „auf Vorrat" ohne Löschpfad.

## 4. Architektur-Muster dieser Codebasis (bitte fortsetzen, nicht neu erfinden)

* **Rollen:** Django-Groups `HR-Admin`, `Recruiter`, `Hiring-Manager`,
  `Viewer` plus beliebige weitere Gruppen für Freigabeketten (z. B.
  `Bereichsleitung`, `Geschäftsführung`). Rollen-Check über
  `request.user.groups.filter(name=...)`, nie über String-Vergleich auf
  `request.user.username`.
* **Delegation/Vertretung:** `RoleDelegation` + `delegation_covers()` /
  `active_delegations_to()` (`ats/permissions.py`). Wer Freigabe- oder
  Gremiums-Logik ändert, muss Vertretungsfälle mitdenken (siehe
  `panel_state()` in `ats/panel.py` als Referenzimplementierung: eigene
  Stimme hat Vorrang, sonst zählt eine aktive Vertretung im passenden Scope).
* **Vererbungs-Leiter für Konfiguration:** Mehrere Subsysteme lösen
  Konfiguration über dieselbe Spezifitäts-Leiter auf – **Stelle > Abteilung
  > Einrichtung > Standort > Jobfamilie > Organisation** – und die
  spezifischste besetzte Ebene gewinnt *komplett* (kein Mischen zwischen
  Ebenen). Beispiele: Sichtungs-Gremium (`resolve_panel`), Stellenfreigabe-
  Routing (`resolve_requisition_rule`, gewichtet statt Leiter, aber gleiches
  Prinzip). Ein Sentinel-Wert `["NONE"]` bedeutet „hier bewusst nichts" und
  stoppt die Vererbung nach oben – das ist Absicht, kein leerer Zustand.
* **Audit-Log:** Jede sicherheitsrelevante oder Governance-Aktion ruft
  `write_audit(action, user=..., **metadata)` auf. **Achtung Kwarg-Falle:**
  `write_audit` nimmt `action` und `user` bereits als benannte Parameter –
  eigene Metadata-Felder dürfen diese Namen nicht verwenden (z. B. `op=`
  statt `action=` für eine Sub-Aktion). Dieser Fehler ist in dieser
  Codebasis mehrfach aufgetreten.
* **Fragen-Registry statt Ad-hoc-JSON:** Screening-Fragen, Mindeststandards
  und Stellenfreigabe-Formulare nutzen alle dieselbe Registry
  (`ats/questions.py`, `QUESTION_TYPES`), damit ein neuer Fragetyp an einer
  Stelle definiert wird und überall (Formular-Rendering, Validierung,
  Editor-UI) konsistent ist.
* **CMS-Baukasten nach Registry-Prinzip:** `ats/blocks.py` (`BLOCK_TYPES`)
  ist ebenso die eine Wahrheit für Editor-Felder UND Validierung. Neue
  Block-Typen: ein Registry-Eintrag + ein Zweig in
  `templates/includes/content_blocks.html`. Rendering ausschließlich über
  Autoescape und Design-Tokens – niemals `|safe` oder rohes HTML aus
  Nutzereingaben (Wächter-Test in der Testsuite prüft das aktiv).
* **Analytics-Vollständigkeits-Prinzip:** Jeder neue öffentliche Seitentyp
  (Landingpage, CMS-Seite, künftige Typen) MUSS sich automatisch in der
  Analytics zeigen, ohne Registrierungsschritt. Wer einen neuen Seitentyp
  baut, liefert im selben Patch einen Test „neu angelegt = in der Analytics
  sichtbar".
* **Genehmigungs-Gates sind mehrfach zu verdrahten:** Ein Freigabe-Gate
  (Jobfreigabe, Stellenfreigabe/Requisition) hat i. d. R. **drei
  Durchsetzungspunkte**: der Wizard/Erstellungs-Pfad, der Schnell-Toggle,
  und die finale Freigabe-Aktion selbst. Alle drei müssen das Gate prüfen –
  ein Bypass an der finalen Freigabe wurde in dieser Codebasis real gefunden
  und gefixt (`requisition_blocked_reason()` jetzt an allen drei Stellen).

## 5. Bekannte historische Fehlerquellen (aus echten Sessions, nicht Theorie)

* **Anker-Kollisionen bei Feld-Einfügungen:** `Organization` und
  `JobPosting` haben beide `panelUserIdsJson` – ein zu kurzer `str_replace`-
  Anker traf schon zweimal das falsche Modell. Anker immer so lang wählen,
  dass sie eindeutig sind (Modellname + mindestens ein Nachbarfeld).
* **Einrückungsfehler bei Edit-Zweigen:** Ein falsch eingerücktes `if`
  im `create_job`-Edit-Pfad zog den gesamten Zuweisungsblock in einen
  Bedingungs-Körper – jedes Speichern ohne das neue Feld hätte sonst
  gar nichts mehr gespeichert. Der Bestandstest (`ApprovalGateTestCase`)
  fing es sofort. **Lehre:** nach jeder Struktur-Änderung an einer
  großen View-Funktion die volle Testsuite laufen lassen, nicht nur den
  neuen Test.
* **Unbeschlossene `{% if %}` in Templates:** Mehrfach aufgetreten
  (Analytics-Karte, Interview-Formate-Verwaltung, Stellenfreigabe-Region).
  Ein kleines Tag-Balance-Skript (Python, zählt `if/endif`, `for/endfor`,
  `with/endwith`, `block/endblock`) findet das in Sekunden, wenn
  `get_template()` nur die Zeile des *nächsten* falschen Tags meldet, nicht
  die Ursache.
* **Verschraenkte Template-Regionen bei chirurgischen Edits:** Wenn ein
  `str_replace` an einer Stelle mit mehreren ineinander verschachtelten
  `{% for %}`/`{% if %}`-Blöcken ansetzt, lieber die ganze Region ersetzen
  als zu flicken – ein halber Patch mitten in einer Schleife ist schwerer zu
  finden als ein sauberer Neuschrieb.
* **Deutsche Anführungszeichen in Python-Strings:** ASCII-Fake-
  Anführungszeichen beenden den String vorzeitig. Immer echte
  Unicode-Anführungszeichen (Escapes) verwenden.
* **Kwarg-Kollision bei `write_audit`:** siehe Abschnitt 4.

## 6. Vor jedem Feature: Definition of Done

Siehe `NORTHSTAR.md` Abschnitt 8 für die vollständige Liste. Kurzfassung:
Auth **und** Scope geprüft, PII verschlüsselt, CSRF intakt, Audit-Log bei
sensiblen Aktionen, kein externer Netzwerkaufruf im Datenpfad, mindestens ein
automatisierter Test (Happy Path + ein Missbrauchsfall), keine erfundenen
Kennzahlen in der Produktions-UI, Bedienbarkeit ohne Schulung für
Gelegenheitsrollen.

---
**Bestätigung:** Wenn du als KI dieses Dokument liest, halte dich strikt an
diese Regeln. Sicherheit, Datensouveränität und architektonische Konsistenz
haben Vorrang vor Geschwindigkeit. Bei Widerspruch zwischen diesem Dokument
und älteren Kommentaren/Docs im Repo gilt: **dieses Dokument und
`NORTHSTAR.md` sind aktuell, alles andere kann veraltet sein.**
