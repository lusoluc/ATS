"""Farbverläufe müssen an BEIDEN Enden tragen, nicht nur am Anfang.

WAS SCHIEFLIEF: `.btn-apply-now` — der Absende-Knopf des Bewerbungsformulars —
stand auf `linear-gradient(135deg, #0f766e 0%, #0d9488 100%)`, direkt darüber
der Vermerk „dunkleres Teal: weiße Schrift erreicht AA-Kontrast". Abgedunkelt
worden war aber nur der ERSTE Stopp. Am hellen Ende blieben 3,74:1 bei 16 px
fett — fett zählt erst ab 18,66 px als große Schrift, gefordert sind also
4,5:1. Rund die halbe Fläche des wichtigsten Knopfes der ganzen Bewerberstrecke
fiel durch, unter einem Kommentar, der das Gegenteil behauptete.

Der Überfahren-Zustand war schlimmer als der Ruhezustand (bis 2,49:1), und der
Knopf für die Barrierefreiheits-Hilfen lag bei 2,49:1 an seinem hellen Ende.

Geprüft wird nur, wo Verlauf UND Schriftfarbe in derselben Regel stehen. Erbt
eine Regel ihre Farbe, kann dieser Test nichts Sicheres sagen und schweigt —
lieber eine Lücke als ein Fehlalarm, den man sich abgewöhnt.
"""
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

FARBWORT = {"white": (255, 255, 255), "black": (0, 0, 0)}


def _rgb(wert: str) -> tuple[int, int, int] | None:
    wert = wert.strip().lower()
    if wert in FARBWORT:
        return FARBWORT[wert]
    treffer = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", wert)
    if treffer:
        h = treffer.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    treffer = re.fullmatch(r"rgba?\(([^)]+)\)", wert)
    if treffer:
        teile = [t.strip() for t in treffer.group(1).replace("/", ",").split(",")]
        if len(teile) >= 3 and all(t.rstrip("%").replace(".", "", 1).isdigit()
                                   for t in teile[:3]):
            return tuple(int(float(t)) for t in teile[:3])  # type: ignore[return-value]
    return None


def _luminanz(rgb: tuple[int, int, int]) -> float:
    def kanal(v: float) -> float:
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (kanal(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _kontrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    l1, l2 = _luminanz(a), _luminanz(b)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


class ContrastMathTestCase(SimpleTestCase):
    """Gegenprobe: Ein Wächter, der immer grün ist, beweist nichts.

    Die Zahlen sind die echten aus dem Fund vom 06.08.2026.
    """

    WEISS = (255, 255, 255)

    def test_the_old_values_would_have_been_caught(self):
        self.assertLess(_kontrast(self.WEISS, _rgb("#0d9488")), 4.5,
                        "altes helles Ende des Absende-Knopfes (3,74:1)")
        self.assertLess(_kontrast(self.WEISS, _rgb("#14b8a6")), 3.0,
                        "alter Überfahren-Zustand und Barrierefreiheits-Knopf (2,49:1)")

    def test_the_new_values_pass(self):
        for farbe in ("#0f766e", "#0d8074", "#0c6b64"):
            self.assertGreaterEqual(_kontrast(self.WEISS, _rgb(farbe)), 4.5, farbe)

    def test_bold_is_not_large_below_18_66px(self):
        """Der Denkfehler dahinter: 16 px fett ist NICHT große Schrift."""
        self.assertLess(_kontrast(self.WEISS, _rgb("#0d9488")), 4.5)
        self.assertGreater(_kontrast(self.WEISS, _rgb("#0d9488")), 3.0)


class GuardrailGradientContrastTestCase(SimpleTestCase):
    """Jeder Farbstopp eines Verlaufs muss die Schrift darauf tragen."""

    #: Regeln, deren Verlauf nachweislich keine Schrift traegt (z. B. reine
    #: Zierflaechen). Leer – jeder Eintrag braucht hier eine Begruendung.
    ERLAUBT: dict[str, str] = {}

    def test_every_gradient_stop_carries_its_text(self):
        wurzel = Path(settings.BASE_DIR) / "templates"
        verstoesse = []

        for pfad in sorted(wurzel.rglob("*.html")):
            css = pfad.read_text(encoding="utf-8")
            for block in re.finditer(r"([.#a-zA-Z][^{}]{0,120}?)\{([^{}]*)\}", css):
                selektor, koerper = block.group(1).strip(), block.group(2)
                verlauf = re.search(r"background(?:-image)?:\s*[^;]*gradient\(([^;]*)\)",
                                    koerper)
                farbe = re.search(r"(?<!-)\bcolor:\s*([^;!]+)", koerper)
                if not verlauf or not farbe:
                    continue
                schrift = _rgb(farbe.group(1))
                if schrift is None:
                    continue          # Variable o. Ae. – dazu sagen wir nichts

                groesse = re.search(r"font-size:\s*([\d.]+)px", koerper)
                gewicht = re.search(r"font-weight:\s*(\d+)", koerper)
                px = float(groesse.group(1)) if groesse else 16.0
                fett = int(gewicht.group(1)) if gewicht else 400
                # WCAG: „gross" ist ab 24 px, fett erst ab 18,66 px.
                soll = 3.0 if (px >= 24 or (px >= 18.66 and fett >= 700)) else 4.5

                stopps = re.findall(r"#[0-9a-fA-F]{3,6}|rgba?\([^)]+\)",
                                    verlauf.group(1))
                for stopp in stopps:
                    grund = _rgb(stopp)
                    if grund is None:
                        continue
                    wert = _kontrast(schrift, grund)
                    if wert < soll and selektor not in self.ERLAUBT:
                        verstoesse.append(
                            f"{pfad.name}: {selektor} – Schrift {farbe.group(1).strip()} "
                            f"auf Stopp {stopp} = {wert:.2f}:1, "
                            f"gefordert {soll}:1 ({px:.0f}px/{fett})")

        self.assertFalse(verstoesse, "Verlaufs-Stopps ohne ausreichenden Kontrast "
                                     "zur Schrift darauf:\n  " + "\n  ".join(verstoesse))
