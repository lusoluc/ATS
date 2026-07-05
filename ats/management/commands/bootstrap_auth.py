"""Richtet die RBAC-Rollen ein und legt optional einen ersten Admin an.

Nutzung:
    python manage.py bootstrap_auth
    SECURATS_ADMIN_USER=admin SECURATS_ADMIN_PASSWORD=... python manage.py bootstrap_auth
    python manage.py bootstrap_auth --username admin --password ... --email admin@example.org

Legt die vier Rollen-Groups (idempotent) an. Wird ein Benutzer angegeben
(per Argument oder Env), wird er als Superuser in der Rolle 'HR-Admin' erstellt
bzw. aktualisiert. Passwörter werden nie hartcodiert – nur aus Env/Argument.
"""
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

ROLE_GROUPS = ["HR-Admin", "Recruiter", "Hiring-Manager", "Viewer"]


class Command(BaseCommand):
    help = "Erstellt RBAC-Rollen (Groups) und optional einen ersten HR-Admin."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.environ.get("SECURATS_ADMIN_USER"))
        parser.add_argument("--password", default=os.environ.get("SECURATS_ADMIN_PASSWORD"))
        parser.add_argument("--email", default=os.environ.get("SECURATS_ADMIN_EMAIL", ""))

    def handle(self, *args, **opts):
        for name in ROLE_GROUPS:
            _, created = Group.objects.get_or_create(name=name)
            self.stdout.write(("Rolle angelegt: " if created else "Rolle vorhanden: ") + name)

        username = opts.get("username")
        password = opts.get("password")
        if not username or not password:
            self.stdout.write(self.style.WARNING(
                "Kein Admin angelegt (SECURATS_ADMIN_USER/PASSWORD bzw. --username/--password fehlen)."
            ))
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username, defaults={"email": opts.get("email") or ""}
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        user.groups.add(Group.objects.get(name="HR-Admin"))
        self.stdout.write(self.style.SUCCESS(
            ("Admin erstellt: " if created else "Admin aktualisiert: ") + username
        ))
