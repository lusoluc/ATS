"""Eine Wahrheit fuer E-Mail-Vorlagen: Platzhalter und HTML-Abbau.

Im Durchgang "unerreichbare Funktionen" gefunden: Es gab ZWEI Platzhalter-
Syntaxen, die sich nie trafen. Die mitgelieferten Vorlagen schreiben
`[[COMPANY_NAME]]`, `[[FIRST_NAME]]`, `[[JOB_TITLE]]`; die Versandpfade
ersetzten nur `{name}`, `{stelle}`, `{firma}`, `{portal}`. Wer die Vorlagen
unveraendert liess, verschickte woertlich "Bewerbungseingang bei
[[COMPANY_NAME]]" - und dazu rohes HTML als Klartext, weil `htmlContent` als
Mailtext genutzt wurde.

Deshalb hier zentral:
- BEIDE Syntaxen werden ersetzt (auch gemischt in einer Vorlage),
- unbekannte Platzhalter werden entfernt statt an die Person zu schicken,
- HTML wird in lesbaren Text ueberfuehrt (Absaetze bleiben Absaetze).
"""
import re

# Beide historisch gewachsenen Schreibweisen zeigen auf denselben Wert.
# Reihenfolge egal - ersetzt wird ueber ein Dict.
_ALIASES: dict[str, tuple[str, ...]] = {
    "first_name": ("[[FIRST_NAME]]", "[[Vorname]]", "{vorname}", "{name}"),
    "last_name": ("[[LAST_NAME]]", "[[Nachname]]", "{nachname}"),
    "job_title": ("[[JOB_TITLE]]", "[[Stelle]]", "{stelle}"),
    "company": ("[[COMPANY_NAME]]", "[[Firma]]", "{firma}"),
    "portal_url": ("[[PORTAL]]", "{portal}"),
    "status": ("[[Stand]]", "{stand}"),
}

_PLACEHOLDER_LEFTOVER = re.compile(r"\[\[[^\]\n]{1,40}\]\]|\{[a-zA-Z_]{1,30}\}")


def html_to_text(value: str) -> str:
    """HTML einer Vorlage in lesbaren Mailtext ueberfuehren.

    Absatz- und Zeilenumbruch-Tags werden zu echten Umbruechen, alles
    andere faellt weg - sonst stehen `<h3>`-Tags in der Mail.
    """
    text = value or ""
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|h[1-6]|li)>", "\n\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "• ", text)
    text = re.sub(r"<[^>]+>", "", text)
    for entity, char in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                         ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        text = text.replace(entity, char)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def render_template(value: str, **context: str) -> str:
    """Platzhalter ersetzen - beide Syntaxen, Reste entfernen.

    Bekannte Schluessel: first_name, last_name, job_title, company,
    portal_url, status. Was danach noch wie ein Platzhalter aussieht, wird
    entfernt: lieber eine Luecke als `[[COMPANY_NAME]]` in der Anrede.
    """
    text = value or ""
    for key, tokens in _ALIASES.items():
        replacement = str(context.get(key) or "").strip()
        for token in tokens:
            if token in text:
                text = text.replace(token, replacement)
    text = _PLACEHOLDER_LEFTOVER.sub("", text)
    # Doppelte Leerzeichen aus entfernten Platzhaltern gluetten
    text = re.sub(r"[ \t]{2,}", " ", text)
    return re.sub(r" +\n", "\n", text).strip()


def render_email(template, **context: str) -> tuple[str, str]:
    """(Betreff, Text) aus einem EmailTemplate - fertig zum Versenden.

    Nutzt textContent, wenn gepflegt; sonst wird htmlContent lesbar
    gemacht. Beides laeuft durch dieselbe Platzhalter-Ersetzung.
    """
    raw_body = (getattr(template, "textContent", "") or "").strip()
    if not raw_body:
        raw_body = html_to_text(getattr(template, "htmlContent", "") or "")
    subject = render_template(getattr(template, "subject", "") or "", **context)
    return subject, render_template(raw_body, **context)
