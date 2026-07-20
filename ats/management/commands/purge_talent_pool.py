"""DSGVO-Hygiene: abgelaufene Talent-Pool-Einwilligungen endgültig löschen.

Betrieb (Cron, siehe OPERATIONS.md):
    30 3 * * *  python manage.py purge_talent_pool

Abgelaufene Einträge bleiben --grace-days (Default 30) sichtbar-ausgegraut im
Recruiter-Blick ("kürzlich abgelaufen" – Gelegenheit, die Person aktiv um
Verlängerung zu bitten), werden aber nie mehr gematcht oder angesprochen.
Danach werden sie mitsamt Ansprache-Historie geloescht: Die Einwilligung war
befristet – nach Ablauf gibt es keine Rechtsgrundlage fuer die Speicherung.
"""
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from ats.audit import write_audit
from ats.models import TalentPoolSubscription


class Command(BaseCommand):
    help = "Löscht Talent-Pool-Einträge, deren Einwilligung länger als --grace-days abgelaufen ist."

    def add_arguments(self, parser):
        parser.add_argument("--grace-days", type=int, default=30,
                            help="Kulanzfrist nach Ablauf (Default 30 Tage).")

    def handle(self, *args, **options):
        cutoff = timezone.now() - datetime.timedelta(days=max(0, options["grace_days"]))
        qs = TalentPoolSubscription.objects.filter(expiresAt__lt=cutoff)
        count = qs.count()
        qs.delete()  # CASCADE loescht die TalentPoolContact-Historie mit
        if count:
            write_audit("TALENT_POOL_PURGED", purged=count,
                        grace_days=options["grace_days"])
        self.stdout.write(self.style.SUCCESS(
            f"{count} abgelaufene Talent-Pool-Einträge gelöscht "
            f"(Kulanz: {options['grace_days']} Tage)."))
