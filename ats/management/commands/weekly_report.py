"""GF/CFO-Wochenreport (WP6/UC-CV-12) – geplanter KPI-Report als Markdown.

Ohne `--out` wird der Bericht an alle HR-Admins mit hinterlegter Adresse
VERSANDT. Vorher ging er nach stdout — im Zeitplan-Dienst also ins
Docker-Log, das niemand liest: Der Job stand grün im Vermerk, und die Leitung
bekam nie einen Bericht. (Der Docstring vertröstete auf "Versand folgt mit
WP7" — die Versand-Schicht existierte längst.)

Kann nicht zugestellt werden (kein Mailserver, keine Adressen), endet das
Kommando mit einem Fehler statt mit einem grünen Haken: Ein Bericht, der
niemanden erreicht, ist kein Erfolg.

Mit `--out DATEI` wird stattdessen in die Datei geschrieben (für Ablage oder
eigene Verteilwege).
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from ats.analytics import detect_anomalies, fairness_overview, location_benchmark, time_to_fill_forecast
from ats.models import Application, JobPosting


class Command(BaseCommand):
    help = "Erzeugt den wöchentlichen Leitungs-KPI-Report (Markdown)."

    def add_arguments(self, parser):
        parser.add_argument("--out", help="Zieldatei (Default: stdout)")

    def handle(self, *args, **options):
        now = timezone.now()
        apps = Application.objects.all()
        week = apps.filter(createdAt__gte=now - timedelta(days=7))

        lines = [f"# SecurATS Wochenreport – {now.strftime('%d.%m.%Y')}", ""]
        lines.append(f"**Neue Bewerbungen (7 Tage):** {week.count()}  ·  "
                     f"**Gesamtbestand:** {apps.count()}")
        lines.append("")

        lines.append("## Pipeline")
        for r in apps.values('status').annotate(c=Count('id')).order_by('-c'):
            lines.append(f"- {r['status']}: {r['c']}")
        lines.append("")

        lines.append("## Standorte")
        for b in location_benchmark(apps)[:8]:
            avg = f"{b['avg_days']} Tage" if b['avg_days'] is not None else "–"
            lines.append(f"- {b['location']}: {b['total']} Bewerbungen, "
                         f"{b['conversion_pct']}% Einladungsquote, Ø {avg}")
        lines.append("")

        fc = time_to_fill_forecast(apps, JobPosting.objects.filter(
            workflowState__name='published'))
        overdue = [r for r in fc['rows'] if r['overdue']]
        lines.append("## Besetzungs-Prognose")
        lines.append(f"- Offene Stellen: {len(fc['rows'])}, davon **überfällig: {len(overdue)}**")
        for r in overdue[:5]:
            lines.append(f"  - {r['job']} ({r['location']}): offen seit {r['age_days']} Tagen, "
                         f"Prognose ~{r['forecast_days']} Tage")
        lines.append("")

        lines.append("## Hinweise & Handlungsvorschläge")
        for f in detect_anomalies(apps):
            lines.append(f"- [{f['severity']}] {f['title']} → {f['action']}")
        lines.append("")

        fair = fairness_overview(apps)
        lines.append("## Fairness (KI-Entscheidungen, aggregiert)")
        d = fair['score_dist']
        lines.append(f"- Score-Verteilung: A {d['A']} · B {d['B']} · C {d['C']} · D {d['D']}")
        rate = f"{fair['override_rate_pct']}%" if fair['override_rate_pct'] is not None else "–"
        lines.append(f"- Mensch-über-KI-Quote: {rate}")

        report = "\n".join(lines)
        if options.get("out"):
            with open(options["out"], "w", encoding="utf-8") as fh:
                fh.write(report)
            self.stdout.write(self.style.SUCCESS(f"Report geschrieben: {options['out']}"))
            return

        from django.contrib.auth.models import Group
        from django.core.management.base import CommandError

        from ats.mail_send import send_notice
        admins = Group.objects.filter(name="HR-Admin").first()
        adressen = ([u.email for u in admins.user_set.all() if u.email]
                    if admins else [])
        if not adressen:
            raise CommandError(
                "Kein Versand moeglich: Kein HR-Admin hat eine E-Mail-Adresse "
                "hinterlegt. Der Bericht erreicht so niemanden.")
        zugestellt = send_notice(
            f"SecurATS Wochenreport – {now.strftime('%d.%m.%Y')}",
            report, None, adressen, context="Wochenreport")
        if not zugestellt:
            raise CommandError(
                "Wochenreport nicht zugestellt - Grund steht im Protokoll "
                "und unter Einstellungen -> E-Mail-Versand.")
        self.stdout.write(self.style.SUCCESS(
            f"Wochenreport an {len(adressen)} Empfaenger versandt."))
