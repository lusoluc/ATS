"""Gemeinsame Test-Helfer (aufgeteilt aus der frueheren Monolith-tests.py)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


def make_user(username, role=None, superuser=False):
    u = User.objects.create_user(username=username, password="pw12345!")
    if superuser:
        u.is_superuser = True
        u.is_staff = True
        u.save()
    if role:
        u.groups.add(Group.objects.get(name=role))
    return u


