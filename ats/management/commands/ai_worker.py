"""WP7/L6: Worker für die KI-Task-Queue (siehe ats/queue.py)."""
import time

from django.core.management.base import BaseCommand

from ats.queue import queue_depth, run_pending


class Command(BaseCommand):
    help = "Arbeitet KI-Tasks aus der Queue ab (--once oder --loop)."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true",
                            help="Einmal alle PENDING-Tasks abarbeiten, dann beenden.")
        parser.add_argument("--loop", action="store_true",
                            help="Dauerbetrieb (Poll-Intervall --interval Sekunden).")
        parser.add_argument("--interval", type=int, default=3)

    def handle(self, *args, **options):
        if options["loop"]:
            self.stdout.write("KI-Worker im Dauerbetrieb (Strg+C zum Beenden) …")
            try:
                while True:
                    n = run_pending()
                    if n:
                        self.stdout.write(f"{n} Task(s) verarbeitet · Queue: {queue_depth()}")
                    time.sleep(options["interval"])
            except KeyboardInterrupt:
                self.stdout.write("Worker beendet.")
        else:
            n = run_pending()
            self.stdout.write(self.style.SUCCESS(
                f"{n} Task(s) verarbeitet · Queue: {queue_depth()}"))
