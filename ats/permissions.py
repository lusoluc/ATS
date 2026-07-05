"""Rollenbasierte Zugriffskontrolle (RBAC) für SecurATS.

Nutzt Djangos bewährtes contrib.auth (Sessions, Passwort-Hashing, Groups).
Rollen sind als Django-Groups abgebildet. Superuser umgehen die Prüfung.

Hinweis: Dies ist die grundlegende RBAC-Schicht (Phase 2). Feingranulares
BOLA-Scoping (Standort-/Abteilungssilos) ist ein separater Folgeschritt.
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

# Rollen (= Django-Group-Namen)
HR_ADMIN = "HR-Admin"
RECRUITER = "Recruiter"
HIRING_MANAGER = "Hiring-Manager"
VIEWER = "Viewer"

ALL_ROLES = (HR_ADMIN, RECRUITER, HIRING_MANAGER, VIEWER)


def role_required(*roles):
    """View-Decorator: erfordert Login UND Mitgliedschaft in einer der Rollen.

    - Anonym            -> Redirect zum Login (via login_required).
    - Eingeloggt, aber
      falsche Rolle     -> 403 PermissionDenied.
    - Superuser         -> immer erlaubt.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.groups.filter(name__in=roles).exists():
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("Für diese Aktion fehlt die erforderliche Rolle.")
        return _wrapped
    return decorator


# Bequeme, wiederverwendbare Decorator-Instanzen
any_staff_required = role_required(*ALL_ROLES)          # jede interne Rolle
recruiter_required = role_required(HR_ADMIN, RECRUITER)  # operative Recruiting-Aktionen
hr_admin_required = role_required(HR_ADMIN)              # Konfiguration/Administration


# ============================================================================
# BOLA-Scoping: begrenzt Datenzugriff auf erlaubte Standorte/Einrichtungen
# ============================================================================
from django.db.models import Q


def has_full_access(user):
    """HR-Admin/Superuser oder Nutzer ohne Einschränkung sehen alles."""
    if user.is_superuser or user.groups.filter(name=HR_ADMIN).exists():
        return True
    scope = getattr(user, "scope", None)
    return scope is None or scope.full_access


def _scope_ids(user):
    scope = user.scope
    return (
        set(scope.locations.values_list("id", flat=True)),
        set(scope.facilities.values_list("id", flat=True)),
    )


def scope_applications(user, qs):
    if has_full_access(user):
        return qs
    loc_ids, fac_ids = _scope_ids(user)
    return qs.filter(Q(jobPosting__location_id__in=loc_ids) | Q(jobPosting__facility_id__in=fac_ids))


def scope_jobs(user, qs):
    if has_full_access(user):
        return qs
    loc_ids, fac_ids = _scope_ids(user)
    return qs.filter(Q(location_id__in=loc_ids) | Q(facility_id__in=fac_ids))


def can_access_application(user, app):
    if has_full_access(user):
        return True
    loc_ids, fac_ids = _scope_ids(user)
    return app.jobPosting.location_id in loc_ids or app.jobPosting.facility_id in fac_ids


def active_delegations_to(user):
    """Aktive Vertretungen, bei denen `user` die Vertretung IST (delegatee).

    Zeitfenster wird serverseitig geprueft – eine abgelaufene Vertretung
    wirkt nirgends mehr, egal was die UI zeigt.
    """
    from django.utils import timezone
    from .models import RoleDelegation
    now = timezone.now()
    return list(RoleDelegation.objects
                .filter(delegatee=user, validFrom__lte=now, validUntil__gte=now)
                .select_related('delegator'))


def delegation_covers(delegation, job):
    """Greift diese Vertretung fuer diese Stelle? (ALL / FACILITY / JOB)"""
    if delegation.scopeType == 'ALL':
        return True
    if delegation.scopeType == 'FACILITY':
        return job is not None and str(job.facility_id) == (delegation.scopeId or '')
    if delegation.scopeType == 'JOB':
        return job is not None and str(job.id) == (delegation.scopeId or '')
    return False


def can_override(user):
    """Darf diese Person Gremien-/Prozess-Entscheidungen uebersteuern?

    Granular konfigurierbar: SystemSetting OVERRIDE_GROUPS (Kommaliste von
    Gruppennamen, Default 'HR-Admin'). So kann der Vorstand z. B. der Gruppe
    'Geschaeftsfuehrung' das Uebersteuern geben, ohne ihr HR-Admin-Rechte
    (Nutzerverwaltung, Audit-Export, ...) zu verleihen. Jede Uebersteuerung
    bleibt einzeln auditiert.
    """
    if user.is_superuser:
        return True
    from .models import SystemSetting
    raw = (SystemSetting.objects.filter(key='OVERRIDE_GROUPS')
           .values_list('value', flat=True).first()) or 'HR-Admin'
    allowed = {g.strip() for g in raw.split(',') if g.strip()}
    return user.groups.filter(name__in=allowed).exists()
