"""Die Air-Gap-Zusage als Browser-Regel — nicht als Vorsatz.

`System_Architektur_und_Feature_Katalog.md` wirbt wörtlich mit „Air-Gapped
Architektur (keine Cloud-APIs, keine Tracker, keine Google Fonts)". Genau
diese Zusage war schon einmal gebrochen: `base.html` lud Schriften und Symbole
von cdnjs und Google, jahrelang, ohne dass es auffiel. Behoben wurde es von
Hand — und damit gilt sie seither wieder nur, solange alle daran denken.

Eine Regel, die auf Disziplin baut, hält nicht. Die Content-Security-Policy
macht daraus eine Regel, die der Browser durchsetzt: Was nicht von diesem
Server kommt, wird nicht geladen. Trägt jemand morgen wieder ein CDN ein,
bleibt das Bild leer und die Konsole sagt warum — statt dass die IP-Adresse
jeder bewerbenden Person still an einen Dritten geht.

**Was die Regel NICHT leistet.** `'unsafe-inline'` steht für Skripte und
Stile drin, weil die Oberfläche durchgehend mit `onclick="…"` und
`style="…"` arbeitet. Das ist ehrlich benannt und keine Kleinigkeit: Gegen
eine XSS-Lücke im eigenen Markup schützt die Regel damit nicht. Sie schützt
gegen das, was hier real passiert ist — externe Quellen — und gegen
Abfluss (`connect-src`), Einbettung (`frame-ancestors`) und entführte
Formulare (`form-action`). Die Inline-Handler zu entfernen ist ein eigenes
Paket; es wäre unehrlich, die Politik jetzt strenger aussehen zu lassen,
als sie ist.

Bewusst ohne Zusatz-Abhängigkeit (django-csp): Es sind zwei Kopfzeilen.
Ein Paket dafür wäre eine Abhängigkeit mehr in einem Produkt, das auf
abgeschotteten Servern läuft.
"""
from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponseBase

#: Die Politik als Daten – so kann der Wächter sie prüfen, statt eine
#: Zeichenkette zu vergleichen.
CSP_DIREKTIVEN: dict[str, str] = {
    # Grundregel: alles nur von diesem Server.
    "default-src": "'self'",
    # 'unsafe-inline': siehe Modul-Kopf. Wichtig ist, dass KEINE fremde
    # Herkunft erlaubt ist - ein CDN-Skript wird geblockt.
    "script-src": "'self' 'unsafe-inline'",
    "style-src": "'self' 'unsafe-inline'",
    # data: fuer eingebettete SVG-Pfeile (Auswahlfelder in base.html).
    "img-src": "'self' data:",
    "font-src": "'self'",
    # Kein Abfluss an Dritte: fetch/XHR/WebSocket nur zum eigenen Server.
    "connect-src": "'self'",
    # Nichts einbetten, nirgends eingebettet werden (Clickjacking).
    "frame-ancestors": "'none'",
    "frame-src": "'none'",
    "object-src": "'none'",
    # Ein entfuehrtes Formular soll Bewerberdaten nicht woandershin senden.
    "form-action": "'self'",
    "base-uri": "'self'",
}

#: Ein Bewerbungssystem braucht weder Kamera noch Mikrofon noch Standort.
#: Ohne diese Zeile darf jedes eingebettete Skript danach fragen - und der
#: Dialog allein verunsichert bewerbende Personen zu Recht.
PERMISSIONS_POLICY = (
    "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
    "magnetometer=(), gyroscope=(), accelerometer=(), midi=()"
)


def csp_wert() -> str:
    """Die Politik als Kopfzeilen-Wert."""
    return "; ".join(f"{name} {wert}" for name, wert in CSP_DIREKTIVEN.items())


class SicherheitsHeaderMiddleware:
    """Setzt CSP und Permissions-Policy an JEDE Antwort.

    Django deckt Referrer-Policy, X-Frame-Options, nosniff und COOP bereits
    ueber die SecurityMiddleware ab (gemessen). Diese beiden fehlten.

    Die Django-Admin-Oberflaeche ist ausgenommen: Sie bringt eigene Skripte
    mit und ist kein Teil des Produkts - sie mit einer Politik zu brechen,
    die fuer die Bewerberstrecke gedacht ist, hilft niemandem.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponseBase]):
        self.get_response = get_response
        self._csp = csp_wert()

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        antwort = self.get_response(request)
        if not request.path.startswith("/admin/"):
            antwort.setdefault("Content-Security-Policy", self._csp)
            antwort.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
        return antwort
