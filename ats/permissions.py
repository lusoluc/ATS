"""Rollenbasierte Zugriffskontrolle (RBAC) für SecurATS.

Nutzt Djangos bewährtes contrib.auth (Sessions, Passwort-Hashing, Groups).
Rollen sind als Django-Groups abgebildet. Superuser umgehen die Prüfung.

Hinweis: Dies ist die grundlegende RBAC-Schicht (Phase 2). Feingranulares
BOLA-Scoping (Standort-/Abteilungssilos) ist ein separater Folgeschritt.
"""
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponseBase

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser, User

    from .models import Application, JobPosting, RoleDelegation

# Views liefern beliebige Response-Typen; mehr Praezision braucht der Decorator nicht.
_ViewFunc = Callable[..., HttpResponseBase]

# Rollen (= Django-Group-Namen)
HR_ADMIN = "HR-Admin"
RECRUITER = "Recruiter"
HIRING_MANAGER = "Hiring-Manager"
VIEWER = "Viewer"

ALL_ROLES = (HR_ADMIN, RECRUITER, HIRING_MANAGER, VIEWER)


def role_required(*roles: str) -> Callable[[_ViewFunc], _ViewFunc]:
    """View-Decorator: erfordert Login UND Mitgliedschaft in einer der Rollen.

    - Anonym            -> Redirect zum Login (via login_required).
    - Eingeloggt, aber
      falsche Rolle     -> 403 PermissionDenied.
    - Superuser         -> immer erlaubt.
    """
    def decorator(view_func: _ViewFunc) -> _ViewFunc:
        @wraps(view_func)
        @login_required
        def _wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
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

#: Rollen, die allgemein bearbeiten duerfen - alle ausser Viewer.
WRITING_ROLES = (HR_ADMIN, RECRUITER, HIRING_MANAGER)


def may_modify(user: "User | AnonymousUser") -> bool:
    """Darf diese Person allgemein etwas veraendern?

    Die Rolle heisst `Viewer` - bis hierher konnte sie trotzdem das Board
    umsortieren, Aufgaben abhaken, Seiteninhalte bearbeiten und Personalbedarf
    melden: Sie war technisch mit `Hiring-Manager` identisch, weil beide nur
    ueber `any_staff_required` liefen. Ein Name, der etwas anderes verspricht
    als er haelt, ist in einer Rechteverwaltung besonders teuer - danach
    werden Zugaenge vergeben.

    ALLGEMEIN heisst: das taegliche Bearbeiten. NICHT gemeint sind
    ausdrueckliche Einzelbenennungen (Auswahlgremium, Freigabestufe) - wer
    dort namentlich berufen wurde, entscheidet genau dort, und die Befugnis
    kommt aus der Benennung, nicht aus der Basisrolle. Sonst koennte ein
    Betriebsratsmitglied mit Basisrolle `Viewer` seine eigene Freigabe nicht
    mehr erteilen.
    """
    # Nicht angemeldet: Der Decorator soll auch dann sicher sein, wenn er
    # einmal ohne `any_staff_required` darueber steht.
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=WRITING_ROLES).exists()


def denies_viewer_writes(view_func: _ViewFunc) -> _ViewFunc:
    """Laesst `Viewer` die Seite LESEN, aber nichts darauf veraendern.

    Bewusst am Verfahren (POST/PUT/PATCH/DELETE) statt an der ganzen View:
    Diese Seiten zeigen und aendern zugleich. Ein Decorator ueber alles wuerde
    dem Viewer die Einsicht nehmen - genau das, wofuer es die Rolle gibt.
    """
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        if request.method not in ("GET", "HEAD", "OPTIONS") and \
                not may_modify(request.user):
            raise PermissionDenied(
                "Die Rolle Viewer darf Inhalte einsehen, aber nicht ändern.")
        return view_func(request, *args, **kwargs)
    return _wrapped


# ============================================================================
# BOLA-Scoping: begrenzt Datenzugriff auf erlaubte Standorte/Einrichtungen
# ============================================================================
def has_full_access(user: "User") -> bool:
    """HR-Admin/Superuser oder Nutzer ohne Einschränkung sehen alles."""
    if user.is_superuser or user.groups.filter(name=HR_ADMIN).exists():
        return True
    scope = getattr(user, "scope", None)
    return scope is None or bool(scope.full_access)


def _scope_ids(user: "User") -> tuple[set[Any], set[Any]]:
    # UUID-Mengen; values_list liefert ohnehin Any-Elemente
    scope = user.scope
    return (
        set(scope.locations.values_list("id", flat=True)),
        set(scope.facilities.values_list("id", flat=True)),
    )


def scope_applications(user: "User", qs: "QuerySet[Application]") -> "QuerySet[Application]":
    if has_full_access(user):
        return qs
    loc_ids, fac_ids = _scope_ids(user)
    return qs.filter(Q(jobPosting__location_id__in=loc_ids) | Q(jobPosting__facility_id__in=fac_ids))


def scope_jobs(user: "User", qs: "QuerySet[JobPosting]") -> "QuerySet[JobPosting]":
    if has_full_access(user):
        return qs
    loc_ids, fac_ids = _scope_ids(user)
    return qs.filter(Q(location_id__in=loc_ids) | Q(facility_id__in=fac_ids))


def can_access_application(user: "User", app: "Application") -> bool:
    if has_full_access(user):
        return True
    loc_ids, fac_ids = _scope_ids(user)
    return app.jobPosting.location_id in loc_ids or app.jobPosting.facility_id in fac_ids


def active_delegations_to(user: "User") -> "list[RoleDelegation]":
    """Aktive Vertretungen, bei denen `user` die Vertretung IST (delegatee).

    Zeitfenster wird serverseitig geprueft – eine abgelaufene Vertretung
    wirkt nirgends mehr, egal was die UI zeigt. Halb-offenes Intervall
    [validFrom, validUntil): das Ende ist exklusiv, damit „vorzeitig
    beenden" (validUntil = jetzt) auch bei grober Uhr-Aufloesung sofort
    wirkt und nicht bis zum naechsten Uhrtick weiterlebt.
    """
    from django.utils import timezone

    from .models import RoleDelegation
    now = timezone.now()
    return list(RoleDelegation.objects
                .filter(delegatee=user, validFrom__lte=now, validUntil__gt=now)
                .select_related('delegator'))


def delegation_covers(delegation: "RoleDelegation", job: "JobPosting | None") -> bool:
    """Greift diese Vertretung fuer diese Stelle? (ALL / FACILITY / JOB)"""
    if delegation.scopeType == 'ALL':
        return True
    if delegation.scopeType == 'FACILITY':
        return job is not None and str(job.facility_id) == (delegation.scopeId or '')
    if delegation.scopeType == 'JOB':
        return job is not None and str(job.id) == (delegation.scopeId or '')
    return False


def can_override(user: "User") -> bool:
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
