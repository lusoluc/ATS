# SecurATS – Preismodell (Hypothese V0, Juli 2026)

> **Status: HYPOTHESE.** Dieses Modell ist festgelegt, um es zu testen – nicht,
> weil es validiert wäre (ROADMAP P0.3). Es wird in **jedem** Discovery-Gespräch
> genannt; die Reaktionen werden protokolliert (Abschnitt 4). Änderungen nur
> gegen Gesprächs-Evidenz, nicht aus Bauchgefühl.

## 1. Das Modell

**Der Open-Source-Kern bleibt frei.** Bezahlt wird Betriebssicherheit, nicht Code.

| Baustein | Preis | Enthalten |
|---|---|---|
| **Open Source (Selbstbetrieb)** | 0 € | Voller Funktionsumfang, Community-Support (GitHub), Updates ohne SLA |
| **Support-Abo S** (Einrichtung bis 300 MA) | **390 €/Monat** | Update-Begleitung mit SLA, Support ≤ 1 Werktag Reaktionszeit, Security-Advisories, Einspielhilfe bei Problemen |
| **Support-Abo M** (301–1.000 MA) | **690 €/Monat** | wie S |
| **Support-Abo L** (1.001–2.000 MA) | **990 €/Monat** | wie S, plus jährlicher Betriebs-Check |
| **Einführungspauschale** (einmalig) | **2.900 €** | Begleitete Installation, Import der Bestandsdaten (CSV), 2×2 h Schulung, Go-Live-Check |
| Managed On-Prem / größere Träger | auf Anfrage | wird in Phase V1 über Partner getestet (P1.5) |

Abrechnung jährlich im Voraus je **Einrichtung** (nicht je Nutzer). Kündigung
zum Laufzeitende. **Design-Partner (die ersten 2–3 Häuser): Einführungspauschale
entfällt, Support-Abo 12 Monate –50 %** – gegen Referenz, Logo und monatliches
Feedback.

## 2. Warum dieses Modell (Begründung der Hypothese)

- **Je Einrichtung statt je Nutzer:** Die Zielgruppe hat 1–3 Recruiting-Nutzer –
  Sitzpreise wären Kleingeld und bestrafen ausgerechnet die Einbindung von
  Hiring-Managern, Betriebsrat und Leitung, die das Produkt will.
- **Support statt Lizenz:** Der Code ist öffentlich; künstliche Lizenzschranken
  wären unglaubwürdig und mit dem Open-Source-Versprechen unvereinbar. Was der
  Kunde real fürchtet, ist der ungepatchte, verwaiste Betrieb (Premortem #3) –
  genau das versichert das Abo.
- **Preisanker:** Etablierte ATS-SaaS im Gesundheitswesen liegen für Häuser
  dieser Größe grob bei 400–1.200 €/Monat. Das Support-Abo liegt bewusst in
  derselben Zone: Es soll über Datensouveränität gewinnen, nicht über
  Billigkeit (Billigpreis = „Hobby-Projekt"-Signal an den Einkauf).
- **Einführungspauschale:** deckt die realen Stunden und filtert
  Gratis-Deployments ohne Ernsthaftigkeit (Premortem #5: „platziert ≠ bezahlt").

## 3. Was das Ziel „50 Einrichtungen" damit bedeutet

50 zahlende Einrichtungen im Mix (≈ 60 % S / 30 % M / 10 % L) ergäben ca.
**320 T€ Jahresumsatz** wiederkehrend plus Einführungen – genug für eine
tragfähige Ein-Firma-Struktur mit Partner-Support, nicht genug für ein großes
Team. Das ist ehrlich: Dieses Modell finanziert ein solides Nischenprodukt,
keinen Hyperscaler. Passt zur Vision (NORTHSTAR).

## 4. Test-Protokoll (P0.6-Gespräche)

In jedem Gespräch wird genannt: *„Der Kern ist Open Source; Betrieb mit Support
kostet je nach Hausgröße 390–990 € im Monat plus 2.900 € Einführung."* Danach
protokollieren:

| Reaktion | Zählung | Interpretation |
|---|---|---|
| „Zu teuer" + Begründung | ☐☐☐… | Prüfen: falsches Segment oder falscher Anker? |
| „Ok / im Rahmen" | ☐☐☐… | Hypothese hält |
| „Zu billig / wirkt unseriös" | ☐☐☐… | Anker anheben |
| „Anderes Modell erwartet" (z. B. je Nutzer, Kauf) | ☐☐☐… | Modellfrage neu stellen |

**Revisionsregel:** Nach 10 protokollierten Reaktionen wird dieses Dokument
überprüft; Preisänderung braucht ≥ 4 gleichgerichtete Signale.

## 5. Sichtbarkeit

- Öffentlich: `/preise/` – **nur auf der Demo-Instanz** (`DEMO_MODE=1`).
  Kundeninstanzen sind Karriereseiten für Bewerbende; dort haben Anbieterpreise
  nichts verloren.
- Formulierung auf der Seite: „Frühphasen-Konditionen" + Design-Partner-Hinweis
  (ehrlich, ohne die interne Hypothesen-Mechanik zu exponieren).
