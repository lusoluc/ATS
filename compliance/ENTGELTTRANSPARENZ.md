# Entgelttransparenz in SecurATS (EU-RL 2023/970)

Stand: Juli 2026. Dieses Dokument beschreibt, was SecurATS zur EU-Entgelttransparenzrichtlinie
durchsetzt, wie der Nachweis funktioniert und wo die Verantwortung des Trägers beginnt.

**Rechtlicher Rahmen, kurz:** Die Richtlinie (EU) 2023/970 war bis zum 7. Juni 2026 in
deutsches Recht umzusetzen. Das ist nicht geschehen; bis zum Umsetzungsgesetz gilt das
EntgTranspG von 2017. Öffentliche Träger müssen damit rechnen, dass sich Bewerbende nach
Fristablauf unmittelbar auf hinreichend bestimmte Richtlinienrechte berufen — insbesondere
Art. 5. Dieses Dokument ist keine Rechtsberatung. Vor der Vermarktung als Compliance-Feature
gehört die Einordnung zu einem Fachanwalt.

## Was SecurATS durchsetzt

**Art. 5 Abs. 1 — Auskunft über das Einstiegsentgelt vor dem Gespräch.**
Jede Stelle referenziert ein Entgeltband (TVöD, AVR oder Haustarif) mit Spanne, Zeitraum
und Tarifhinweis. Ohne Band lässt sich keine Stelle veröffentlichen: der Editor stuft auf
Entwurf zurück, der Schnell-Toggle verweigert. Die Spanne steht öffentlich im Stellendetail
und wandert in den BA-Feed. Weil das Band die Grundlage ist, sind die Kriterien per
Konstruktion objektiv und geschlechtsneutral — Freitext-Gehaltsangaben gibt es nicht mehr.

**Art. 5 Abs. 2 — Verbot der Frage nach der Gehaltshistorie.**
Fragen nach aktuellem oder früherem Gehalt (auch Gehaltsnachweise und -abrechnungen)
werden an allen vier Eingangswegen abgefangen: Stellen-Editor, zentrale Fragen-Registry,
Jobfamilien-Mindeststandards und KI-Zusatzfragen. Jede Blockade wird auditiert.
Die Frage nach der Gehaltsvorstellung bleibt zulässig und wird bewusst nicht angetastet.
Der AGG-Check meldet Historie-Aufforderungen zusätzlich im freien Anzeigentext — per
lokaler KI und, wenn die nicht erreichbar ist, über deterministische Muster.

**Art. 4 — gleichwertige Arbeit, objektive Kriterien.**
Jedes Entgeltband trägt eine Tätigkeitsbewertung nach den vier Kriterien der Richtlinie:
Kompetenzen, Belastungen, Verantwortung, Arbeitsbedingungen. Die Bewertung hängt am Band,
nicht an der Einzelstelle — das Band bündelt gleichwertige Tätigkeiten, die Begründung
gilt einheitlich. Der Bewertungsstatus ist auf der Entgeltbänder-Seite sichtbar und
fließt in den Veröffentlichungs-Nachweis ein.

## Der Nachweis

Jede Veröffentlichung einer Spanne (und jeder Bandwechsel einer veröffentlichten Stelle)
erzeugt einen Eintrag `PAY_RANGE_PUBLISHED` in der Audit-Hash-Kette: Stelle, Band, Spanne,
Tarif, Bewertungsstatus, Zeitpunkt. Die Kette verkettet jeden Eintrag kryptografisch mit
seinem Vorgänger; nachträgliche Änderung oder Löschung meldet `manage.py verify_audit`.
Ein Träger beantwortet die Frage „Welche Spanne war am Tag X öffentlich?" also nicht mit
einer Behauptung, sondern mit einem prüfbaren Kettenauszug.

Die Erfassung läuft über Django-Signale und greift damit auf jedem Pfad, der eine Stelle
veröffentlicht — Editor, Schnell-Toggle, Freigabe-Automatik und alles, was künftig dazukommt.

## Laufende Kontrolle

Die Analytics-Seite zeigt ein Entgelttransparenz-Cockpit: Band-Abdeckung der
veröffentlichten Stellen (Altbestand ohne Band wird sichtbar), Bänder ohne vollständige
Art.-4-Bewertung und Jobfamilien, deren Stellen mehr als ein Band nutzen. Letzteres ist
kein Fehler — unterschiedliche Qualifikationsstufen sind legitim —, aber genau diese
Fälle muss ein Träger begründen können. Deshalb stehen sie dort.

## Was SecurATS bewusst nicht abdeckt

- **Art. 6/7 (Auskunftsrechte Beschäftigter) und Art. 9/10 (Berichtspflichten,
  gemeinsame Entgeltbewertung):** Das betrifft Beschäftigtendaten und gehört ins
  HRIS/Payroll-System, nicht ins Bewerbermanagement. SecurATS erfasst bewusst keine
  Geschlechtsdaten von Bewerbenden (Datensparsamkeit, siehe `analytics.fairness_overview`)
  und wird das für Pay-Gap-Berichte auch nicht tun.
- **Pflicht zur Tätigkeitsbewertung als Publish-Gate:** Die Bewertung ist sichtbar und
  auditiert, blockiert aber nicht die Veröffentlichung. Die Richtlinie verlangt objektive
  Strukturen, kein ausgefülltes Formular pro Anzeige.

## Tests und Wächter

`ats/tests/test_pay_transparency.py` deckt Gate, Anzeige, Feed, Frageverbot (inklusive
der Grenze zur zulässigen Gehaltsvorstellung), Ketten-Verankerung und Bewertung ab.
Guardrail-Tests schlagen an, wenn eine der Verdrahtungen entfernt wird. Zuordnung
Norm → Code → Test: siehe `COMPLIANCE_MATRIX.md`.
