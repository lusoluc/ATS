"""SecurATS Views — CMS: Seiten, Landingpages, Bloecke, Branding, Medien.

Teil des View-Pakets (aufgeteilt aus der frueheren Monolith-views.py).
Oeffentliche Namen werden in ats/views/__init__.py re-exportiert, damit
urls.py und bestehende Importe (`from ats.views import X`) unveraendert
funktionieren.
"""
import datetime
import json
import logging

from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify

from ..audit import write_audit
from ..models import (
    Application,
    AuditLog,
    ContactPerson,
    Department,
    Facility,
    JobFamily,
    Location,
    MediaAsset,
    Organization,
    Page,
)
from ..permissions import any_staff_required, hr_admin_required
from .common import campaign_expired

logger = logging.getLogger(__name__)

__all__ = ["save_page", "pages_manage", "delete_page", "media_manage", "delete_media", "blocks_editor", "branding_view", "landing_pages_manage", "snippets_manage"]


@hr_admin_required
def save_page(request):
    """Creates or updates a CMS Page."""
    if request.method == 'POST':
        page_id = request.POST.get('page_id')
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip().lower()
        content = request.POST.get('content', '').strip()
        status = request.POST.get('status', 'published')
        nav_enabled = request.POST.get('nav_enabled') == 'on'
        nav_label = request.POST.get('nav_label', '').strip()
        nav_order = int(request.POST.get('nav_order', '0'))
        meta_desc = request.POST.get('meta_desc', '').strip()

        with transaction.atomic():
            if page_id:
                page = get_object_or_404(Page, id=page_id)
                page.title = title
                page.slug = slug
                page.content = content
                page.status = status
                page.navEnabled = nav_enabled
                page.navLabel = nav_label or title
                page.navOrder = nav_order
                page.metaDesc = meta_desc
                page.save()
                action = "UPDATE_PAGE"
            else:
                page = Page.objects.create(
                    title=title,
                    slug=slug,
                    content=content,
                    status=status,
                    navEnabled=nav_enabled,
                    navLabel=nav_label or title,
                    navOrder=nav_order,
                    metaDesc=meta_desc
                )
                action = "CREATE_PAGE"

            AuditLog.objects.create(
                action=action,
                metadataJson=json.dumps({"pageId": str(page.id), "slug": page.slug})
            )

        return redirect('ats:pages_manage')
    return redirect('ats:pages_manage')


@hr_admin_required
def pages_manage(request):
    """Die EINE Seiten-Verwaltung: anlegen, bearbeiten, loeschen, Baukasten.

    Frueher gab es zwei Editoren nebeneinander. Dieser hier konnte loeschen und
    fuehrte zum Baukasten, kannte aber nur vier Felder; der andere ("CMS
    Seiten-Editor") hatte Navigations-Beschriftung, Position, SEO-Text und
    Sichtbarkeit, dafuer weder Loeschen noch Baukasten. Wer eine Seite anlegte
    UND veroeffentlichte, brauchte beide Bildschirme.

    Gespeichert wird ueber `save_page` - der Endpunkt kannte die vollstaendigen
    Felder schon und schreibt einen Audit-Eintrag. Die frueher hier eingebaute
    zweite, aermere Speicher-Logik ist damit entfallen.
    """
    pages = Page.objects.order_by('navOrder', 'title')
    return render(request, 'pages_manage.html', {'pages': pages})


@hr_admin_required
def delete_page(request, page_id):
    get_object_or_404(Page, id=page_id).delete()
    return redirect('ats:pages_manage')


@hr_admin_required
def media_manage(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']
        # WP8/WCAG 1.1.1: Alt-Text ist Pflicht – auch bei direkten POSTs
        # ohne das (required-)Formular entstehen keine Bilder ohne Alt-Text.
        alt_text = (request.POST.get('altText') or '').strip()
        if not alt_text:
            return redirect('ats:media_manage')
        MediaAsset.objects.create(
            name=(request.POST.get('name') or f.name)[:255],
            altText=alt_text[:255],
            file=f,
            contentType=getattr(f, 'content_type', None),
        )
        write_audit('MEDIA_UPLOADED', user=request.user, name=f.name)
        return redirect('ats:media_manage')
    assets = MediaAsset.objects.order_by('-createdAt')[:200]
    return render(request, 'media_manage.html', {'assets': assets})


@hr_admin_required
def delete_media(request, asset_id):
    a = get_object_or_404(MediaAsset, id=asset_id)
    try:
        a.file.delete(save=False)
    except Exception:
        logger.exception("Datei-Löschung fehlgeschlagen für %s", asset_id)
    a.delete()
    return redirect('ats:media_manage')


@any_staff_required
def blocks_editor(request, kind, obj_id):
    """CMS-Baukasten: Bloecke hinzufuegen, ausfuellen, sortieren – ohne HTML.

    Ein Editor fuer beide Seitentypen (kind: 'page' | 'landing').
    Server-gerendert, jede Aktion ein POST (add/save/up/down/delete) –
    funktioniert ohne JavaScript und laesst sich vollstaendig testen.
    Rechte folgen der jeweiligen Verwaltung: CMS-Seiten nur HR-Admin.
    """
    from django.http import HttpResponseForbidden

    from ..blocks import BLOCK_TYPES, enrich_blocks, load_blocks, normalize_block
    from ..models import LandingPage
    if kind == 'page':
        if not (request.user.is_superuser
                or request.user.groups.filter(name='HR-Admin').exists()):
            return HttpResponseForbidden("Nur HR-Admin.")
        obj = get_object_or_404(Page, id=obj_id)
        public_url = f"/pages/{obj.slug}/"
    elif kind == 'landing':
        obj = get_object_or_404(LandingPage, id=obj_id)
        public_url = f"/k/{obj.slug}/"
    else:
        return HttpResponseForbidden("Unbekannter Seitentyp.")

    blocks = load_blocks(obj)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        idx = request.POST.get('idx')
        idx = int(idx) if idx and idx.isdigit() else None
        if action == 'add':
            btype = request.POST.get('block_type', '')
            if btype in BLOCK_TYPES and len(blocks) < 30:
                blocks.append(normalize_block({"type": btype}))
        elif action == 'save' and idx is not None and idx < len(blocks):
            raw = {"type": blocks[idx]["type"]}
            for name, _ftype, _label in BLOCK_TYPES[blocks[idx]["type"]]["fields"]:
                raw[name] = request.POST.get(f"f_{name}", "")
            blocks[idx] = normalize_block(raw)
        elif action == 'up' and idx and idx < len(blocks):
            blocks[idx - 1], blocks[idx] = blocks[idx], blocks[idx - 1]
        elif action == 'down' and idx is not None and idx < len(blocks) - 1:
            blocks[idx + 1], blocks[idx] = blocks[idx], blocks[idx + 1]
        elif action == 'delete' and idx is not None and idx < len(blocks):
            blocks.pop(idx)
        obj.blocksJson = blocks
        obj.save(update_fields=['blocksJson'])
        write_audit('CMS_BLOCKS_CHANGED', user=request.user, kind=kind,
                    target=str(obj_id), op=action, count=len(blocks))
        return redirect('ats:blocks_editor', kind=kind, obj_id=obj_id)

    # Editor-Anzeige: Bloecke mit Feldwerten + Typen-Palette
    editor_blocks = []
    for i, b in enumerate(blocks):
        spec = BLOCK_TYPES[b["type"]]
        fields = []
        for name, ftype, label in spec["fields"]:
            val = b.get(name, "")
            if ftype == "lines":
                val = "\n".join(val or [])
            fields.append({"name": name, "type": ftype, "label": label,
                           "value": val})
        editor_blocks.append({"i": i, "type": b["type"],
                              "label": spec["label"], "fields": fields})
    palette = [{"type": t, "label": spec["label"]}
               for t, spec in BLOCK_TYPES.items()]
    return render(request, 'blocks_editor.html', {
        'kind': kind, 'obj': obj, 'public_url': public_url,
        'editor_blocks': editor_blocks, 'palette': palette,
        'contacts': ContactPerson.objects.order_by('lastName'),
        'preview': enrich_blocks(blocks)})


@hr_admin_required
def branding_view(request):
    """Erscheinungsbild: CI/CD des Traegers auf die Bewerberseiten bringen.

    Zwei Wege: (a) Ein-Klick-Import von der Unternehmens-Website
    (theme-color, Logo-Kandidat, Bildvorschlag – Best Effort, Admin
    bestaetigt), (b) manuelle Pflege. Kontrastfarben werden automatisch
    berechnet (WCAG) – niemand muss wissen, ob auf Magenta Weiss gehoert.
    """
    from ..branding import brand_context, fetch_branding_suggestions, normalize_hex
    org = Organization.objects.first()
    if org is None:
        return render(request, 'branding.html', {'org': None})
    suggestion = None
    if request.method == 'POST' and request.POST.get('form') == 'import':
        url = (request.POST.get('website') or '').strip()[:300]
        suggestion = fetch_branding_suggestions(url)
        suggestion['website'] = url
        write_audit('BRANDING_IMPORT_ATTEMPTED', user=request.user,
                    website=url, found_primary=bool(suggestion.get('primary')))
    elif request.method == 'POST':
        primary = normalize_hex(request.POST.get('primary'))
        accent = normalize_hex(request.POST.get('accent'))
        org.brandEnabled = request.POST.get('enabled') == '1'
        org.brandMode = ('DARK' if request.POST.get('mode') == 'DARK'
                         else 'LIGHT')
        if primary:
            org.brandPrimary = primary
        org.brandAccent = accent or ''
        org.brandLogoUrl = (request.POST.get('logo_url') or '').strip()[:500]
        org.brandHeroUrl = (request.POST.get('hero_url') or '').strip()[:500]
        org.save(update_fields=['brandEnabled', 'brandMode', 'brandPrimary',
                                'brandAccent', 'brandLogoUrl', 'brandHeroUrl'])
        write_audit('BRANDING_CHANGED', user=request.user,
                    enabled=org.brandEnabled, primary=org.brandPrimary,
                    mode=org.brandMode)
        return redirect('ats:branding')
    return render(request, 'branding.html',
                  {'org': org, 'suggestion': suggestion,
                   'preview': brand_context(org) if org.brandEnabled else None})


@any_staff_required
def landing_pages_manage(request):
    """Landingpages verwalten: anlegen/bearbeiten, Link+QR, Kennzahlen."""

    from ..models import LandingPage
    if request.method == 'POST' and request.POST.get('form') == 'expiry':
        # Kampagnen-Ablaufdatum: leer = laeuft unbegrenzt; Datum wirkt bis
        # einschliesslich Tagesende (QR bleibt bis 23:59 des Tages gueltig).
        from ..models import LandingPage as _LPx
        obj = get_object_or_404(_LPx, id=request.POST.get('expiry_lp_id'))
        raw = (request.POST.get('expires') or '').strip()
        if raw:
            try:
                d = datetime.date.fromisoformat(raw)
            except ValueError:
                return redirect('ats:landing_pages')
            obj.expiresAt = timezone.make_aware(
                datetime.datetime.combine(d, datetime.time(23, 59)))
        else:
            obj.expiresAt = None
        obj.save(update_fields=['expiresAt'])
        write_audit('LANDING_PAGE_EXPIRY_SET', user=request.user,
                    name=obj.name, expires=raw or 'unbegrenzt')
        return redirect('ats:landing_pages')

    if request.method == 'POST':
        lp = None
        if request.POST.get('lp_id'):
            lp = get_object_or_404(LandingPage, id=request.POST['lp_id'])
        name = (request.POST.get('name') or '').strip()[:120]
        if not name:
            return redirect('ats:landing_pages')
        if lp is None:
            base = slugify(name)[:40] or 'kampagne'
            slug, n = base, 2
            while LandingPage.objects.filter(slug=slug).exists():
                slug, n = f"{base}-{n}", n + 1
            lp = LandingPage(slug=slug)
        def fk(model, key):
            val = request.POST.get(key)
            return model.objects.filter(id=val).first() if val else None
        lp.name = name
        lp.headline = (request.POST.get('headline') or '').strip()[:200]
        lp.introText = (request.POST.get('intro_text') or '').strip()[:4000]
        lp.heroUrl = (request.POST.get('hero_url') or '').strip()[:500]
        lp.facility = fk(Facility, 'facility')
        lp.department = fk(Department, 'department')
        lp.jobFamily = fk(JobFamily, 'job_family')
        lp.location = fk(Location, 'location')
        lp.contactPerson = fk(ContactPerson, 'contact_person')
        lp.active = request.POST.get('active') == '1'
        lp.save()
        write_audit('LANDING_PAGE_SAVED', user=request.user,
                    name=lp.name, slug=lp.slug, active=lp.active)
        return redirect('ats:landing_pages')

    import segno
    rows = []
    for lp in LandingPage.objects.select_related(
            'facility', 'department', 'jobFamily', 'location',
            'contactPerson').order_by('-createdAt'):
        lp.is_expired = campaign_expired(lp)
        link = request.build_absolute_uri(f'/k/{lp.slug}/')
        src = lp.slug.upper()
        apps = Application.objects.filter(source=src,
                                          createdAt__gte=lp.createdAt)
        total = apps.count()
        invited = apps.filter(status__in=['INVITED', 'HIRED']).count()
        hired_qs = apps.filter(status='HIRED', hiredAt__isnull=False)
        hired = hired_qs.count()
        days = [ (a.hiredAt - a.createdAt).days for a in hired_qs ]
        avg_days_to_hire = round(sum(days) / len(days), 1) if days else None
        rows.append({
            'lp': lp, 'link': link, 'hired': hired, 'days': avg_days_to_hire,
            'qr': segno.make(link, error='m').svg_data_uri(scale=3),
            'apps': total, 'invited': invited,
            'app_rate': round(100 * total / lp.views, 1) if lp.views else None,
            'invite_rate': round(100 * invited / total) if total else None,
        })
    ctx = {'rows': rows,
           'facilities': Facility.objects.order_by('name'),
           'departments': Department.objects.select_related('facility').order_by('name'),
           'families': JobFamily.objects.filter(archived=False).order_by('name'),
           'locations': Location.objects.order_by('name'),
           'contacts': ContactPerson.objects.order_by('lastName')}
    return render(request, 'landing_pages_manage.html', ctx)


@hr_admin_required
def snippets_manage(request):
    """Textbausteine (TextSnippet): wiederkehrende Absätze zentral pflegen,
    per Dropdown in die Job-Anlage einfügbar (schneller schreiben)."""
    from ..models import TextSnippet
    if request.method == 'POST':
        if request.POST.get('delete_id'):
            TextSnippet.objects.filter(id=request.POST['delete_id']).delete()
        else:
            content = (request.POST.get('content') or '').strip()
            if content:
                TextSnippet.objects.create(
                    category=(request.POST.get('category') or 'INTRO').upper()[:100],
                    content=content,
                    jobFamily_id=(request.POST.get('jobFamily') or None) or None,
                )
        return redirect('ats:snippets')
    return render(request, 'snippets.html', {
        'snippets': TextSnippet.objects.select_related('jobFamily').order_by('category', '-createdAt'),
        'families': JobFamily.objects.order_by('name'),
    })
