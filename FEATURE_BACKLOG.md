# SecurATS – Feature-Gap-Backlog (Next.js → Django)

> Entstanden bei der Stack-Konsolidierung (NORTHSTAR.md, Phase 1). Erfasst, was der
> stillgelegte Next.js-Stack (`legacy/frontend/`) konnte und in Django noch nach-
> zubauen ist.

## Status – Backlog vollständig abgearbeitet
**Alle 18 Punkte umgesetzt & getestet.** (Dieser Ursprungs-Backlog stammt aus der
Stack-Konsolidierung; die seither entstandene Governance-Ebene – Stellenfreigabe,
Gremien-Quorum, Gesprächsrunden – ist ein EIGENES Arbeitsfeld und unten als
Abschnitt „Nach dem Backlog" geführt. Gesamt-Teststand aktuell: 300 grün.)
- Vollständig: B1, B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B13, B14, B15, B17, B18 + BOLA-Scoping.
- Kern umgesetzt (Feinschliff offen): **B12** (Vorlagen-Bibliothek + KI-Tonalitäts-Overlay; Versionierung/Master-Hierarchie offen), **B16** (Seiten-Editor statt visuellem Drag-&-Drop-Builder), **B10** (Ordering backend-seitig; feines Drag-Reorder-JS im Dashboard offen).

## Wichtigste Erkenntnis
Die **Datenmodelle existieren in Django bereits fast vollständig** (aus dem Prisma-
Schema portiert: `RoleDelegation`, `AuditLog`, `JobAlertSubscription`,
`ApplicantToken`, `Interview`/`InterviewSlot`, `ScreeningQuestion`, `JobTemplate`,
`Location`/`Facility`/`Department`, `Page`, `Message`, `TalentPoolSubscription`, …).
Der Gap ist daher überwiegend **Views/Endpoints/UI auf vorhandenen Modellen** – nicht
die Datenschicht. Das reduziert Aufwand und Risiko erheblich.

Legende Ist-Stand: ❌ fehlt · ◐ teilweise · ✅ vorhanden (nur Modell = „Modell ✅, UI ❌")
Aufwand: S/M/L.

---

## P1 – Sicherheit & Compliance (zuerst)

| # | Feature | Frontend-Referenz | Django-Modell | Django-Ist | Aufwand |
|---|---|---|---|---|---|
| B1 ✅ | **Sicherer CV-Download** (auth + Rolle + Audit-Log; kein direkter `media/`-Zugriff) | `cms/applications/[id]/cv` | `Application.cvStorageId` | ❌ Endpoint fehlt (CV wird gespeichert, aber ungeschützt ausgeliefert) | M |
| B2 ✅ | **Audit-Log-Viewer** (Filter, Export) | `cms/audit` | `AuditLog` ✅ | Modell ✅, UI ❌ | M |
| B3 ✅ | **Retention/Löschung planbar** (Cron/Scheduling + Trockenlauf-Report) | `cms/cron/data-retention` | — | ◐ (Command `data_retention` vorhanden, Scheduling fehlt) | S |

## P2 – Kandidaten-facing

| # | Feature | Frontend-Referenz | Django-Modell | Django-Ist | Aufwand |
|---|---|---|---|---|---|
| B4 ✅ | **Magic-Link-Statusportal** (passwortloser Kandidaten-Login via Token, Status/Rückfragen) | `/bewerber/[token]` | `ApplicantToken` ✅, `Message` ✅ | Modell ✅, Views ❌ | L |
| B5 ✅ | **Job-Alerts** (öffentliches Abo + Matching/Benachrichtigung) | `public/job-alerts`, `cms/job-alerts`, `/job-alert` | `JobAlertSubscription` ✅, `JobAlertLog` ✅ | Modell ✅, Endpoints/UI ❌ | M |
| B6 ✅ | **Kandidaten-Nachrichten** (Verlauf, Vorlagen-Versand) | (Teil Portal/Detail) | `Message` ✅, `EmailTemplate` ✅ | ◐ (E-Mail-Vorlagen da, Verlaufs-UI ❌) | M |

## P3 – Recruiter-Produktivität

| # | Feature | Frontend-Referenz | Django-Modell | Django-Ist | Aufwand |
|---|---|---|---|---|---|
| B7 ✅ | **Analytics/Insight-Dashboard ausbauen** (Quellen, Verweildauer je Phase, Prognosen, KI-Analyst – NORTHSTAR §4) | `cms/analytics` | (aggregiert) | ◐ (Dashboard-Tab „KPIs & Funnel" vorhanden) | L |
| B8 ✅ | **Delegationen** (Vertretung/Zuweisung von Bewerbungen) | `cms/delegations` | `RoleDelegation` ✅ | Modell ✅, UI ❌ | M |
| B9 ✅ | **Interview-Kalender** (Ansicht + Slots) | `/admin/calendar` | `Interview` ✅, `InterviewSlot` ✅ | ◐ (`schedule_interview` da, Kalender-UI ❌) | M |
| B10 ✅ | **Kanban-Move mit Reihenfolge** (Drag-&-Drop-Ordering) | `cms/applications/move` | `Application` ✅ | ◐ (`update_status` da, Ordering ❌) | S |
| B11 ✅ | **Talent-Pool-Verwaltung** | (Teil Applicants) | `TalentPoolSubscription` ✅ | Modell ✅, UI ❌ | S |

## P4 – Stammdaten & Konfiguration

| # | Feature | Frontend-Referenz | Django-Modell | Django-Ist | Aufwand |
|---|---|---|---|---|---|
| B12 ✅ | **Job-Vorlagen-Bibliothek** (NORTHSTAR §3.7: Vorschlag, 1-Klick, Tonalitäts-Overlay, Master/Version) | (Teil `cms/jobs`) | `JobTemplate` ✅, `TextSnippet` ✅ | Modell ✅, Logik/UI ❌ | L |
| B13 ✅ | **Kategorien / Jobfamilien-CRUD** | `cms/categories`, `cms/job-metadata` | `JobFamily` ✅, `CareerPath` ✅ | Modell ✅, CRUD ❌ | S |
| B14 ✅ | **Standorte/Einrichtungen/Abteilungen-CRUD** | `cms/locations` | `Location`/`Facility`/`Department` ✅ | Modell ✅, CRUD ❌ | M |
| B15 ✅ | **Screening-Fragen-Bank** (wiederverwendbar) | `cms/questions` | `ScreeningQuestion` ✅ | Modell ✅, UI ❌ | S |

## P5 – CMS & Content

| # | Feature | Frontend-Referenz | Django-Modell | Django-Ist | Aufwand |
|---|---|---|---|---|---|
| B16 ◐ | **Seiten-Builder** (früher Puck-Drag-&-Drop) | `cms/pages`, `cms/pages/seed` | `Page` ✅ | ◐ (`save_page` einfach vorhanden; visueller Builder ❌) | L |
| B17 ✅ | **Content-Seiten** (Arbeitgeber, Einrichtungen, Info) | `/arbeitgeber`, `/einrichtungen/[slug]`, `/info/[slug]` | `Page` ✅, `FacilityProfile` ✅ | ◐ | M |
| B18 ✅ | **Medien-/Datei-Verwaltung** (Bilder, Downloads) | `cms/files`, `cms/images`, `cms/file/[slug]` | — | ❌ | M |

---

## Vorgeschlagene Reihenfolge
1. **B1** (CV-Download-Sicherheit) – schließt die letzte offensichtliche PII-Lücke; direkt nach der Auth.
2. **B2/B3** – Compliance nachweisbar (Audit-Viewer, Retention-Scheduling) → NORTHSTAR Phase 3.
3. **B4/B5** – Kandidaten-Erlebnis (Magic-Link, Job-Alerts).
4. **B7/B8/B9** – Recruiter-Produktivität (Analytics, Delegationen, Kalender).
5. **B12** – Job-Vorlagen (hoher Nutzen, NORTHSTAR §3.7).
6. Rest (Stammdaten-CRUD, CMS) nach Bedarf.

---

## Nach dem Backlog – Governance-Ebene (P1-Prozess-Review, Releases 1.5–1.7)

Diese Features standen NICHT im Next.js-Ursprungs-Backlog; sie entstanden aus dem
Prozess-Review und heben SecurATS vom „ATS mit CMS" zum governance-fähigen System
für regulierte Träger. Alle umgesetzt & getestet.

| Feature | Kern | Migration | Status |
|---|---|---|---|
| **Einstellungs-Ereignis** | Status „Eingestellt" nur aus „Eingeladen"; Time-to-Fill; Kosten je Einstellung | 0029–0032 | ✅ |
| **CMS-Baukasten** | 10 Block-Typen für Seiten/Landingpages, Live-Vorschau, ohne HTML | — | ✅ |
| **Fragen-Builder / Pflicht-Dokumente** | Screening-Fragen & Pflichtnachweise per Formular, kein JSON | — | ✅ |
| **Gremium-Quorum & Frist** | „N von M"-Quorum je Stelle, Abstimmungsfrist mit Eskalations-Mail | 0034 | ✅ |
| **Stellenfreigabe** | Personalbedarf → mehrstufige Genehmigungskette → Konvertierung; 3 dichte Veröffentlichungs-Gates | 0035 | ✅ |
| **No-Code Routing-Matrix** | Regel = Geltungsbereich × dynamisches Formular × Kette; Spezifitäts-Auflösung | 0036 | ✅ |
| **Kampagnen-Ablaufdatum** | Landingpage-Endseite (QR-tauglich), Kanal-Attribution stoppt nach Ablauf | 0037 | ✅ |
| **Gesprächsrunden als Zustände** | Runden je Stelle; Einstellen erst nach Abschluss aller Runden | 0038 | ✅ |
| **Parallele Genehmigungsstufen** | Ketten-Syntax „+"; alle Rollen einer Stufe, Rückgabe stoppt | — | ✅ |
| **Vertretung in der Kette („i. V.")** | Aktive Delegation entscheidet fällige Stufe; Selbstbedienungs-UI; Assistenz-Fall | 0039 | ✅ |
| **Engpass-Kennzahl** | Analytics: Ø Wartetage je Freigabestufe, Engpass-Badge, parallel-korrekt | — | ✅ |
| **Fälligkeits-Benachrichtigung** | Ereignis-Mail an Genehmiger + Vertretungen, sobald ihre Stufe fällig wird | — | ✅ |

### Offen hinter Evidenz-Gate (bewusst NICHT gebaut)
Diese Ideen sind aufgenommen, warten aber auf Design-Partner-Evidenz statt auf
Spekulation:
- **Freie Status-Pipelines je Jobkategorie** + Automatisierungs-Trigger (größter Brocken)
- **Erinnerung bei Liegenbleiben** (Cron „seit X Tagen fällig", Einmal-Marker wie beim Gremium)
- **Quorum innerhalb einer Parallelgruppe** („2 von 3 Bereichsleitungen")
- **Trend/Ampel** für die Engpass-Kennzahl (je Quartal, je Einrichtung)
- **Runde-an-Termin-Kopplung** (Interview-Ergebnis schließt Runde automatisch)
- CV-Parsing-Feldbefüllung, 1-Klick LinkedIn/Xing-Import, Mehrfachbewerbung, A/B-Landingpages, Offboarding

### Real offen (außerhalb der Codebasis)
Demo-Hosting, produktives SMTP, und – das wichtigste V0-Gate – **10 Discovery-Gespräche**
mit Trägern aus Pflege/Sozialwirtschaft, bevor weitere große Wetten gebaut werden.

> Referenz für den Nachbau ist jeweils der Code in `legacy/frontend/src/app/api/...`
> bzw. `.../app/...`. Die Django-Modelle sind die Datenautorität.
