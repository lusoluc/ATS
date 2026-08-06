"""Postleitzahl → Koordinaten, offline.

Die Umkreissuche des Job-Alerts braucht Koordinaten je Standort
(`ats/job_alerts.py`). Eintragen konnte sie bis U6 niemand, und selbst danach
kennt kein Mensch die Breite seines Standorts auswendig. Bleiben sie leer,
fällt „im Umkreis von 30 km" still auf „exakt derselbe Ort" zurück.

WARUM EINE MITGELIEFERTE TABELLE UND KEIN DIENST: Ein Geocoding-Dienst wäre
bequemer und hausnummerngenau — aber jede Standortanlage schickte dann eine
Adresse des Trägers nach außen. Das widerspricht dem Versprechen, mit dem
SecurATS antritt. Die Tabelle liegt im Repo, wird nie aktualisiert, ohne dass
es jemand merkt, und funktioniert in einer Installation ohne Internetzugang.

GENAUIGKEIT: Mittelpunkt je Postleitzahl, keine Hausnummern. Für „im Umkreis
von X km" ist das reichlich; für eine Wegbeschreibung wäre es zu grob. Genau
dafür ist es auch nicht gedacht.

Quelle der Daten: GeoNames (https://www.geonames.org), Lizenz CC BY 4.0.
Die Herkunft steht auch im Kopf der Datei selbst — sie muss mitwandern.
"""
from __future__ import annotations

import csv
from pathlib import Path

#: Mitgelieferte Tabelle (PLZ;lat;lng), Kommentarzeilen beginnen mit '#'.
PLZ_TABLE_PATH = Path(__file__).resolve().parent / "data" / "plz_de.csv"

_TABLE: dict[str, tuple[float, float]] | None = None


def _load() -> dict[str, tuple[float, float]]:
    """Tabelle einmal je Prozess einlesen (rund 10.800 Zeilen)."""
    global _TABLE
    if _TABLE is not None:
        return _TABLE
    table: dict[str, tuple[float, float]] = {}
    try:
        with PLZ_TABLE_PATH.open(encoding="utf-8") as fh:
            rows = csv.reader(
                (line for line in fh if not line.startswith("#")), delimiter=";")
            next(rows, None)                      # Kopfzeile
            for row in rows:
                if len(row) < 3:
                    continue
                try:
                    table[row[0].strip()] = (float(row[1]), float(row[2]))
                except ValueError:
                    continue
    except OSError:
        # Fehlende Tabelle darf die Anwendung nicht anhalten: ohne sie gibt es
        # eben keinen Vorschlag, von Hand eintragen bleibt moeglich.
        table = {}
    _TABLE = table
    return table


def lookup_plz(postal_code: str | None) -> tuple[float, float] | None:
    """Mittelpunkt der Postleitzahl, oder None wenn unbekannt.

    Akzeptiert die ueblichen Schreibweisen ("21335", " 21335 ", "D-21335").
    Nur fuenfstellige deutsche Postleitzahlen - fuer andere Laender liegt
    keine Tabelle bei, und ein Ratespiel waere schlimmer als kein Ergebnis.
    """
    text = (postal_code or "").strip().upper().removeprefix("D-").strip()
    if not (len(text) == 5 and text.isdigit()):
        return None
    return _load().get(text)


def table_size() -> int:
    """Anzahl bekannter Postleitzahlen - fuer Anzeige und Diagnose."""
    return len(_load())
