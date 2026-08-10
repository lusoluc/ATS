"""Das Benutzerhandbuch in der Anwendung — dort, wo die Fragen entstehen.

Als Datei im Projektordner erreicht ein Handbuch niemanden, der es braucht:
Wer im Board steht und nicht weiterweiß, öffnet kein Repository. Deshalb wird
`HANDBUCH.md` hier gerendert und ist über das Menü erreichbar.

Eine Quelle, zwei Ausgaben: Die Markdown-Datei bleibt die Wahrheit (im Pull
Request les- und prüfbar, und nur so können die Wächter überhaupt vergleichen,
ob jede Seite dokumentiert ist). Diese Ansicht ist die Darstellung — samt
Druckansicht, sodass ein ausgedrucktes Heft ohne Zusatzwerkzeug entsteht.
"""
from __future__ import annotations

import pathlib
import re

from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import render

from ..permissions import any_staff_required

#: Bilder liegen im Repo unter docs/handbuch/ und werden ueber diese Sicht
#: ausgeliefert - so muss niemand den Medienordner umbauen.
BILDER_PRAEFIX = "docs/handbuch/"


def _handbuch_pfad() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent.parent / "HANDBUCH.md"


def _bildpfade_umschreiben(markdown_text: str) -> str:
    """`docs/handbuch/x.png` -> die Adresse, unter der die Anwendung liefert."""
    return markdown_text.replace(f"]({BILDER_PRAEFIX}", "](/hilfe/bild/")


def kapitel_liste(markdown_text: str) -> list[dict[str, str]]:
    """Überschriften für das Inhaltsverzeichnis am Seitenrand.

    Die Anker kommen aus DERSELBEN Funktion, mit der die `toc`-Erweiterung die
    `id` an die Überschrift schreibt. Vorher rechnete diese Liste sie selbst
    aus - und zwar anders: Ein Punkt wurde zu „-" statt zu entfallen
    („6.3 …" -> `6-3-…` gegen `63-…`), Umlaute fielen ersatzlos weg statt
    umgeschrieben zu werden („Das Menü" -> `1-3-das-men` gegen `13-das-menu`).
    47 von 67 Einträgen im Inhaltsverzeichnis führten damit ins Leere: Ein
    Klick sprang nirgendwohin, und wer Kapitel 6.3 aufrufen wollte, landete
    wieder am Seitenanfang.

    Zwei Berechnungen desselben Wertes gehen früher oder später auseinander.
    Deshalb hier keine zweite, sondern die geliehene erste.
    """
    from markdown.extensions.toc import slugify

    kapitel = []
    for zeile in markdown_text.splitlines():
        treffer = re.match(r"^(#{1,3})\s+(.*)$", zeile)
        if not treffer:
            continue
        ebene, titel = len(treffer.group(1)), treffer.group(2).strip()
        if ebene == 1 and titel.startswith("SecurATS"):
            continue        # der Dokumenttitel ist kein Kapitel
        kapitel.append({"ebene": str(ebene), "titel": titel,
                        "anker": slugify(titel, "-")})
    return kapitel


@any_staff_required
def hilfe_view(request: HttpRequest) -> HttpResponse:
    """Das Handbuch, gerendert im Design der Anwendung."""
    import markdown as md

    quelle = _handbuch_pfad()
    if not quelle.exists():
        # Ehrlich statt leer: Wer das Handbuch sucht und eine leere Seite
        # bekommt, haelt die Funktion fuer kaputt.
        return render(request, "hilfe.html", {
            "fehlt": True, "inhalt": "", "kapitel": []})

    import nh3

    text = quelle.read_text(encoding="utf-8")
    roh = md.markdown(
        _bildpfade_umschreiben(text),
        extensions=["tables", "toc", "fenced_code", "sane_lists"])
    # Markdown reicht eingebettetes HTML unveraendert durch. Die Quelle ist
    # zwar eine Repo-Datei - aber „nur Entwickler aendern das" ist keine
    # Sicherheitsmassnahme, sondern eine Annahme. nh3 laesst genau die Tags
    # stehen, die ein Handbuch braucht, und wirft alles andere weg
    # (insbesondere <script>, Ereignis-Attribute und fremde Adressen).
    inhalt = nh3.clean(
        roh,
        tags={"h1", "h2", "h3", "h4", "p", "ul", "ol", "li", "strong", "em",
              "code", "pre", "blockquote", "table", "thead", "tbody", "tr",
              "th", "td", "img", "a", "hr", "br"},
        attributes={"img": {"src", "alt"}, "a": {"href", "title"},
                    "h1": {"id"}, "h2": {"id"}, "h3": {"id"}, "h4": {"id"}},
        url_schemes={"http", "https"})
    return render(request, "hilfe.html", {
        "fehlt": False,
        "inhalt": inhalt,
        "kapitel": kapitel_liste(text),
    })


@any_staff_required
def hilfe_bild(request: HttpRequest, name: str) -> HttpResponseBase:
    """Liefert ein Handbuch-Bild aus docs/handbuch/.

    Bewusst mit fester Endung und ohne Pfadanteile: Der Name kommt aus der
    Adresszeile, und ein `../` darin duerfte niemals eine andere Datei
    erreichbar machen.
    """
    from django.http import FileResponse, Http404

    if not re.fullmatch(r"[a-z0-9-]+\.png", name):
        raise Http404("Kein Handbuch-Bild.")
    ordner = _handbuch_pfad().parent / BILDER_PRAEFIX
    datei = ordner / name
    if not datei.exists():
        raise Http404("Bild nicht gefunden.")
    return FileResponse(datei.open("rb"), content_type="image/png")
