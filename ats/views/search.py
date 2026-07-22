"""Globale Suche (B1): ein Feld im Header über Bewerber, Stellen, Inhaltsseiten.

Bewusst BOLA-treu: Bewerber-Treffer entstehen nur innerhalb des
Zugriffsbereichs der suchenden Person (scope_applications). Namen liegen
verschlüsselt vor und sind nicht per SQL durchsuchbar - sie werden im
Zugriffsbereich entschlüsselt und in Python abgeglichen (gedeckelt). Die
E-Mail trifft exakt über den Blind-Index, ohne Klartext preiszugeben.
"""
from django.shortcuts import render

from ..models import Application, JobPosting, Page, email_blind_index
from ..permissions import any_staff_required, has_full_access, scope_applications, scope_jobs

# Obergrenze fuer den Klartext-Namensscan: schuetzt vor teuren Vollscans bei
# grossen Bestaenden; wer mehr sucht, praezisiert den Begriff.
_NAME_SCAN_CAP = 500
_MAX_HITS = 8

__all__ = ["global_search"]


@any_staff_required
def global_search(request):
    q = (request.GET.get("q") or "").strip()
    applicants: list = []
    jobs: list = []
    pages: list = []

    if len(q) >= 2:
        q_lower = q.lower()

        # Stellen: Titel ist Klartext -> direkte, scope-treue Suche
        jobs = list(scope_jobs(
            request.user,
            JobPosting.objects.filter(title__icontains=q)
            .select_related("location", "facility"))[:_MAX_HITS])

        # Bewerber: exakter E-Mail-Treffer ueber den Blind-Index ...
        scoped = scope_applications(
            request.user,
            Application.objects.select_related("applicant", "jobPosting"))
        seen: set = set()
        if "@" in q:
            hits = scoped.filter(
                applicant__emailHash=email_blind_index(q)).order_by("-createdAt")
            for a in hits[:_MAX_HITS]:
                applicants.append(a)
                seen.add(a.id)
        # ... sonst Namensabgleich im entschluesselten Zugriffsbereich
        if len(applicants) < _MAX_HITS:
            for a in scoped.order_by("-createdAt")[:_NAME_SCAN_CAP]:
                if a.id in seen:
                    continue
                name = f"{a.applicant.firstName} {a.applicant.lastName}".lower()
                if q_lower in name:
                    applicants.append(a)
                    if len(applicants) >= _MAX_HITS:
                        break

        # Inhaltsseiten: nur fuer HR-Admin (Pflege-Kontext)
        if has_full_access(request.user):
            pages = list(Page.objects.filter(title__icontains=q)[:5])

    return render(request, "search_results.html", {
        "q": q, "applicants": applicants, "jobs": jobs, "pages": pages,
        "total": len(applicants) + len(jobs) + len(pages),
    })
