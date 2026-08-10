"""Einmal-Werkzeug: Google-Fonts-CSS in lokale Dateien überführen.

Liegt bewusst neben den Schriften, damit beim nächsten Schriftwechsel
nachvollziehbar ist, WIE die Dateien entstanden sind — statt dass jemand raten
muss, woher ein `.woff2` im Repository kommt.

    python static/vendor/fonts/_holen.py

Behalten werden die Zeichensätze `latin` und `latin-ext`. Das deckt Deutsch
und die west-/mitteleuropäischen Sprachen ab (auch polnische, tschechische,
ungarische, rumänische Namen). Für Namen in kyrillischer, griechischer oder
vietnamesischer Schrift greift die Systemschrift des Browsers: Der Name wird
korrekt angezeigt, nur in anderer Type. Alle Zeichensätze mitzuliefern hätte
die Datenmenge mehr als verdreifacht.
"""
import pathlib
import re
import urllib.request

HIER = pathlib.Path(__file__).resolve().parent
QUELLE = ("https://fonts.googleapis.com/css2"
          "?family=Inter:wght@300;400;500;600;700"
          "&family=Outfit:wght@400;500;600;700;800&display=swap")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
BEHALTEN = ("/* latin */", "/* latin-ext */")


def hole(url: str) -> bytes:
    anfrage = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(anfrage, timeout=30) as antwort:
        return antwort.read()


def main() -> None:
    css = hole(QUELLE).decode("utf-8")
    bloecke = re.split(r"(?=/\* [a-z-]+ \*/)", css)
    ausgabe, geladen = [], 0
    for block in bloecke:
        if not any(block.startswith(k) for k in BEHALTEN):
            continue
        for url in re.findall(r"url\((https://[^)]+)\)", block):
            name = url.rsplit("/", 1)[-1]
            ziel = HIER / name
            if not ziel.exists():
                ziel.write_bytes(hole(url))
                geladen += 1
            block = block.replace(url, name)
        ausgabe.append(block)
    (HIER / "schriften.css").write_text(
        "/* Erzeugt von _holen.py aus Google Fonts (Inter, Outfit - SIL OFL 1.1).\n"
        "   Lokal ausgeliefert: Die Plattform laeuft auch ohne Internetzugang,\n"
        "   und es gehen keine Nutzer-IP-Adressen an Google. */\n"
        + "".join(ausgabe), encoding="utf-8")
    print(f"{geladen} Schriftdateien geladen, schriften.css geschrieben.")


if __name__ == "__main__":
    main()
