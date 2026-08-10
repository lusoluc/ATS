# Mitgelieferte Schriften und Symbole

Diese Dateien liegen bewusst **im Projekt** statt von einem Netz-Dienst geladen
zu werden. Zwei Gründe:

1. **Die Plattform läuft ohne Internetzugang.** SecurATS wird als
   On-Premise-System betrieben, teils in abgeschotteten Netzen. Wurden Schrift
   und Symbole von `cdnjs.cloudflare.com` und `fonts.googleapis.com` geladen,
   fehlten dort **alle** Symbole (leere Kästchen), und die Hausschrift fiel auf
   eine Systemschrift zurück.
2. **Kein Datenabfluss.** Jeder Seitenaufruf teilte Cloudflare und Google die
   IP-Adresse der Nutzenden mit — bei einer Bewerbungsplattform ein
   Personenbezug, den niemand angekündigt hat.

## Font Awesome Free 6.4.0

- Quelle: <https://fontawesome.com>
- Dateien: `fontawesome/css/fontawesome.min.css`,
  `fontawesome/css/solid.min.css`, `fontawesome/webfonts/fa-solid-900.woff2`
- Die Ordnerstruktur `css/` + `webfonts/` ist die des Originals und muss so
  bleiben: Die CSS verweist relativ mit `../webfonts/`. Legt man die CSS eine
  Ebene hoeher, laeuft der Verweis ins Leere - die Seite laedt dann ohne
  Symbole, ohne dass ein Test das bemerkt.
- Lizenz: Icons **CC BY 4.0**, Schriftdateien **SIL OFL 1.1**, Code **MIT**
  (<https://fontawesome.com/license/free>)
- Mitgeliefert wird **nur der Stil „solid"** — die Anwendung verwendet
  ausschließlich `fa-solid`. Regular und Brands würden nur Datenmenge kosten.
- Der `.ttf`-Fallback wurde aus `solid.min.css` entfernt, weil die Datei nicht
  mitgeliefert wird; jeder Browser seit 2016 versteht WOFF2. Ohne diese
  Änderung hätte jeder Seitenaufruf eine fehlende Datei angefordert.

## Inter und Outfit

- Quelle: Google Fonts, geholt mit `fonts/_holen.py` (liegt daneben, damit
  nachvollziehbar bleibt, wie die Dateien entstanden sind)
- Dateien: `fonts/schriften.css` und vier `.woff2` (beide Schriften sind
  variabel — eine Datei deckt alle Schnitte ab)
- Lizenz: **SIL Open Font License 1.1** für beide
  (Inter: <https://github.com/rsms/inter>, Outfit:
  <https://github.com/Outfitio/Outfit-Fonts>)
- Mitgeliefert sind die Zeichensätze **latin** und **latin-ext**. Das deckt
  Deutsch und die west-/mitteleuropäischen Sprachen ab. Für Namen in
  kyrillischer, griechischer oder vietnamesischer Schrift greift die
  Systemschrift: Der Name wird korrekt dargestellt, nur in anderer Type. Alle
  Zeichensätze hätten die Datenmenge mehr als verdreifacht.

## Aktualisieren

Font Awesome: neue Version von der Projektseite laden, dieselben drei Dateien
ersetzen, `.ttf`-Verweis wieder entfernen, Versionsnummer hier anpassen.

Schriften: `python static/vendor/fonts/_holen.py` — lädt nur, was fehlt.
