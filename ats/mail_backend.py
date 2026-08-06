"""E-Mail-Versand über den konfigurierten Mailserver.

Django liest seine `EMAIL_*`-Einstellungen beim Start. Ein Mailserver, den
HR-Admins in der Oberfläche pflegen, wäre damit erst nach einem Neustart
wirksam — für ein Produkt, das Träger selbst betreiben, keine Zumutbarkeit.
Dieser Backend holt die Zugangsdaten deshalb bei JEDEM Versand aus
`ats.mail_config`.

Zweiter Zweck: ehrlich sein. Ist kein Versandweg hinterlegt, wird das
protokolliert und im Zustand vermerkt, statt in Djangos Standard
`localhost:25` zu laufen und dort still zu scheitern.
"""
from __future__ import annotations

import logging
from typing import Any

from django.core.mail.backends.smtp import EmailBackend as SmtpBackend

from .mail_config import mail_settings, record_result

logger = logging.getLogger(__name__)


class ConfiguredSmtpBackend(SmtpBackend):
    """SMTP-Backend, das seine Zugangsdaten zur Sendezeit holt."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cfg = mail_settings()
        self._securats_configured = cfg.configured
        if cfg.configured:
            self.host = cfg.host
            self.port = cfg.port
            self.username = cfg.user
            self.password = cfg.password
            self.use_tls = cfg.use_tls
            self.use_ssl = cfg.use_ssl

    def send_messages(self, email_messages: Any) -> int:
        if not email_messages:
            return 0
        if not self._securats_configured:
            # Kein Absturz (Hintergrund-Jobs sollen weiterlaufen), aber auch
            # kein Schweigen: Der Zustand ist auf der Konfigurations-Seite
            # sichtbar, und im Log steht der Grund.
            count = len(list(email_messages))
            logger.error(
                "Mailversand nicht moeglich: kein Mailserver hinterlegt "
                "(%s Nachricht(en) nicht zugestellt).", count)
            record_result(False, "Kein Mailserver hinterlegt")
            return 0
        try:
            sent = super().send_messages(email_messages)
        except Exception as exc:            # noqa: BLE001
            record_result(False, f"{type(exc).__name__}: {exc}")
            raise
        if sent:
            record_result(True, f"{sent} Nachricht(en)")
        return sent
