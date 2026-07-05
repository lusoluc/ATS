"""Corporate-Identity-Branding der oeffentlichen Seiten (Stellenboerse,
Bewerbungsstrecke, Bewerberportal, CMS-Seiten).

Muster aus der CI-Analyse (TUM Klinikum, UKE, BwKrankenhaus, Deutsche Bank,
Telekom): eine dominante Primaerfarbe, heller Grund, Logo oben links,
automatisch korrekter Kontrast. Das Recruiter-ATS unter /recruiter/ behaelt
bewusst die SecurATS-Produktidentitaet.
"""
import re
from urllib.parse import urljoin

HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def normalize_hex(value):
    """'#abc' -> '#aabbcc'; ungueltig -> None (nie ungeprueft ins CSS)."""
    value = (value or "").strip()
    if not HEX_RE.match(value):
        return None
    if len(value) == 4:
        value = "#" + "".join(c * 2 for c in value[1:])
    return value.lower()


def on_color(hex_color):
    """WCAG-Kontrast-Automatik: liefert '#ffffff' oder '#111827' als
    Textfarbe AUF der gegebenen Farbe (relative Luminanz, sRGB).
    Telekom-Magenta braucht Weiss, ein helles Gelb braucht Dunkel –
    das soll kein Admin ausrechnen muessen."""
    h = normalize_hex(hex_color) or "#000000"
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    luminance = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return "#111827" if luminance > 0.42 else "#ffffff"


def darken(hex_color, factor=0.85):
    h = normalize_hex(hex_color) or "#000000"
    vals = [max(0, min(255, int(int(h[i:i + 2], 16) * factor)))
            for i in (1, 3, 5)]
    return "#{:02x}{:02x}{:02x}".format(*vals)


def extract_branding_from_html(html, base_url):
    """Best-Effort-Import von einer Unternehmens-Website: theme-color,
    Logo-Kandidat (apple-touch-icon > icon > og:logo), Bildvorschlag
    (og:image). Reine Funktion -> ohne Netz testbar. Liefert nur Vorschlaege;
    der Admin bestaetigt und kann alles uebersteuern."""
    out = {"primary": None, "logo": None, "hero": None}
    m = re.search(r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']([^"\']+)', html, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']theme-color["\']', html, re.I)
    if m:
        out["primary"] = normalize_hex(m.group(1))
    for pattern in (
            r'<link[^>]+rel=["\']apple-touch-icon[^"\']*["\'][^>]+href=["\']([^"\']+)',
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']apple-touch-icon',
            r'<meta[^>]+property=["\']og:logo["\'][^>]+content=["\']([^"\']+)',
            r'<link[^>]+rel=["\'](?:shortcut )?icon["\'][^>]+href=["\']([^"\']+)'):
        m = re.search(pattern, html, re.I)
        if m:
            out["logo"] = urljoin(base_url, m.group(1))
            break
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
    if m:
        out["hero"] = urljoin(base_url, m.group(1))
    return out


def fetch_branding_suggestions(url, timeout=6):
    """Homepage laden (nur http/https, Groessenlimit) und Vorschlaege
    extrahieren. On-prem-Adminfunktion; Fehler -> leere Vorschlaege."""
    from urllib.request import Request, urlopen
    if not re.match(r"^https?://", url or ""):
        return {"primary": None, "logo": None, "hero": None,
                "error": "Nur http/https-Adressen."}
    try:
        req = Request(url, headers={"User-Agent": "SecurATS-Branding/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            html = resp.read(400_000).decode("utf-8", errors="replace")
        return extract_branding_from_html(html, url)
    except Exception as exc:  # Best effort, Admin sieht die Meldung
        return {"primary": None, "logo": None, "hero": None,
                "error": f"Abruf fehlgeschlagen: {exc.__class__.__name__}"}


def brand_context(organization):
    """Fertige CSS-Variablen fuer das Template (None wenn inaktiv)."""
    if organization is None or not organization.brandEnabled:
        return None
    primary = normalize_hex(organization.brandPrimary) or "#0065bd"
    accent = normalize_hex(organization.brandAccent) or darken(primary)
    return {
        "mode": organization.brandMode or "LIGHT",
        "primary": primary,
        "primary_dark": darken(primary),
        "accent": accent,
        "on_primary": on_color(primary),
        "on_accent": on_color(accent),
        "logo": organization.brandLogoUrl,
        "hero": organization.brandHeroUrl,
        "name": organization.name,
    }


def branding_context_processor(request):
    """Stellt `brand` auf OEFFENTLICHEN Pfaden bereit. /recruiter/ und
    /admin/ bleiben SecurATS (Produktidentitaet) – die Trennung ist Muster 5
    der CI-Analyse und passiert zentral hier, nicht in jedem Template."""
    path = request.path or "/"
    if path.startswith("/recruiter") or path.startswith("/admin"):
        return {"brand": None}
    from .models import Organization
    org = Organization.objects.first()
    return {"brand": brand_context(org)}
