"""Konfiguration des Mailversands — eine Wahrheit für alle Versandwege.

WAS VORHER WAR: Es gab überhaupt keine Mail-Einstellungen. Django versucht dann
seinen Standard, `localhost:25`, und weil im Code an 31 Stellen
`fail_silently=True` steht, verschwanden Absagen, Einladungen und Magic-Links
spurlos. Die Oberfläche meldete „verschickt", zugestellt wurde nichts. Das ist
derselbe Fehlertyp wie die stille Umkreissuche: Eine Funktion, die tut, als
täte sie etwas.

WIE ES JETZT LÄUFT: Der Versandweg wird hier zusammengetragen — aus
Umgebungsvariablen (Vorrang, weil eine Deployment-Entscheidung schwerer wiegt
als ein Formular) oder aus den Einstellungen, die HR-Admins auf der
Konfigurations-Seite pflegen. Ist nichts hinterlegt, sagt das die Anwendung
offen, statt in einen toten Standard zu laufen.

Das Passwort liegt verschlüsselt in der Datenbank (dieselbe Fernet-Schicht wie
die Bewerber-PII) und wird nie an die Oberfläche zurückgegeben — angezeigt wird
nur, OB eines gesetzt ist.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from .models import SystemSetting
from .models.base import get_fernet_cipher

HOST_KEY = "MAIL_HOST"
PORT_KEY = "MAIL_PORT"
USER_KEY = "MAIL_USER"
PASSWORD_KEY = "MAIL_PASSWORD_ENC"
SECURITY_KEY = "MAIL_SECURITY"
FROM_KEY = "MAIL_FROM"
LAST_RESULT_KEY = "MAIL_LAST_RESULT"

#: Verbindungsart. „starttls" ist der Regelfall bei Haus-Mailservern (Port 587),
#: „ssl" die ältere Variante auf 465, „none" nur für interne Relays ohne Auth.
SECURITY_CHOICES = {
    "starttls": "STARTTLS (Port 587, Regelfall)",
    "ssl": "SSL/TLS (Port 465)",
    "none": "ohne Verschlüsselung (nur internes Relais)",
}
DEFAULT_SECURITY = "starttls"


@dataclass(frozen=True)
class MailSettings:
    host: str
    port: int
    user: str
    password: str
    security: str
    from_address: str
    #: Schlüssel, die aus der Umgebung kommen und deshalb im Formular
    #: gesperrt sind - sonst tippt jemand einen Wert ein, der nie wirkt.
    from_env: frozenset[str]

    @property
    def configured(self) -> bool:
        return bool(self.host and self.from_address)

    @property
    def use_tls(self) -> bool:
        return self.security == "starttls"

    @property
    def use_ssl(self) -> bool:
        return self.security == "ssl"


def _setting(key: str) -> str:
    row = SystemSetting.objects.filter(key=key).first()
    return (row.value or "").strip() if row else ""


def _stored_password() -> str:
    """Passwort entschluesseln. Ein nicht entschluesselbarer Wert (Schluessel
    gewechselt) gilt als NICHT gesetzt - lieber ein ehrliches „fehlt" als ein
    Anmeldeversuch mit Buchstabensalat."""
    raw = _setting(PASSWORD_KEY)
    if not raw:
        return ""
    try:
        return get_fernet_cipher().decrypt(raw.encode()).decode()
    except Exception:                       # noqa: BLE001
        return ""


def store_password(plain: str) -> None:
    """Passwort verschluesselt ablegen; leerer Wert loescht es."""
    if not plain:
        SystemSetting.objects.filter(key=PASSWORD_KEY).delete()
        return
    token = get_fernet_cipher().encrypt(plain.encode()).decode()
    SystemSetting.objects.update_or_create(key=PASSWORD_KEY,
                                           defaults={"value": token})


def has_password() -> bool:
    return bool(os.environ.get("EMAIL_HOST_PASSWORD") or _setting(PASSWORD_KEY))


def mail_settings() -> MailSettings:
    """Der gueltige Versandweg. Umgebung schlaegt Datenbank."""
    env = os.environ
    from_env: set[str] = set()

    def pick(env_name: str, key: str, field: str) -> str:
        value = (env.get(env_name) or "").strip()
        if value:
            from_env.add(field)
            return value
        return _setting(key)

    host = pick("EMAIL_HOST", HOST_KEY, "host")
    user = pick("EMAIL_HOST_USER", USER_KEY, "user")
    from_address = pick("DEFAULT_FROM_EMAIL", FROM_KEY, "from_address")
    security = pick("EMAIL_SECURITY", SECURITY_KEY, "security") or DEFAULT_SECURITY
    if security not in SECURITY_CHOICES:
        security = DEFAULT_SECURITY

    password = (env.get("EMAIL_HOST_PASSWORD") or "").strip()
    if password:
        from_env.add("password")
    else:
        password = _stored_password()

    port_raw = pick("EMAIL_PORT", PORT_KEY, "port")
    if port_raw.isdigit():
        port = int(port_raw)
    else:
        port = 465 if security == "ssl" else 587

    return MailSettings(host=host, port=port, user=user, password=password,
                        security=security, from_address=from_address,
                        from_env=frozenset(from_env))


def is_configured() -> bool:
    return mail_settings().configured


def record_result(ok: bool, detail: str = "") -> None:
    """Ergebnis des letzten Versands festhalten.

    Ohne diese Spur bleibt ein kaputter Mailweg unsichtbar: Die Aufrufer
    schlucken Fehler (`fail_silently=True`), weil ein Absturz im
    Hintergrund-Job schlimmer waere. Sichtbar sein muss der Fehler trotzdem.
    """
    from django.utils import timezone
    stamp = timezone.now().strftime("%d.%m.%Y %H:%M")
    value = f"{'OK' if ok else 'FEHLER'}|{stamp}|{detail[:300]}"
    SystemSetting.objects.update_or_create(key=LAST_RESULT_KEY,
                                           defaults={"value": value})


def last_result() -> dict[str, Any] | None:
    raw = _setting(LAST_RESULT_KEY)
    if not raw:
        return None
    parts = raw.split("|", 2)
    return {
        "ok": parts[0] == "OK",
        "when": parts[1] if len(parts) > 1 else "",
        "detail": parts[2] if len(parts) > 2 else "",
    }


def mail_status() -> dict[str, Any]:
    """Zustand fuer Konfigurations-Seite und Uebersicht."""
    cfg = mail_settings()
    return {
        "configured": cfg.configured,
        "host": cfg.host,
        "port": cfg.port,
        "user": cfg.user,
        "security": cfg.security,
        "security_label": SECURITY_CHOICES.get(cfg.security, cfg.security),
        "from_address": cfg.from_address,
        "has_password": bool(cfg.password),
        "from_env": sorted(cfg.from_env),
        "last": last_result(),
    }


def send_test_mail(recipient: str) -> tuple[bool, str]:
    """Eine echte Testmail verschicken und das Ergebnis ehrlich zurueckgeben.

    Bewusst OHNE fail_silently: Wer hier auf den Knopf drueckt, will genau
    wissen, was der Mailserver sagt.
    """
    from django.core.mail import get_connection, send_mail
    cfg = mail_settings()
    if not cfg.configured:
        return False, "Es ist kein Mailserver hinterlegt."
    try:
        connection = get_connection(fail_silently=False)
        send_mail(
            "SecurATS: Testnachricht",
            "Diese Nachricht bestätigt, dass der Mailversand aus SecurATS "
            "funktioniert.\n\nWenn Sie sie erhalten haben, ist der Versandweg "
            "richtig eingerichtet.",
            cfg.from_address, [recipient],
            connection=connection, fail_silently=False)
    except Exception as exc:                # noqa: BLE001 - Grund gehoert angezeigt
        record_result(False, f"{type(exc).__name__}: {exc}")
        return False, f"{type(exc).__name__}: {exc}"
    record_result(True, f"Testnachricht an {recipient}")
    return True, f"Testnachricht an {recipient} verschickt."
