"""Basis-Bausteine der Modellschicht: Fernet-Verschluesselung at-rest und E-Mail-Blind-Index."""
import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


# Helper to get a secure Fernet cipher using the settings key
def get_fernet_cipher():
    key_str = getattr(settings, 'PII_ENCRYPTION_KEY', 'securats-fallback-super-secure-encryption-key-for-pii-at-rest=')
    key_hash = hashlib.sha256(key_str.encode()).digest()
    key_b64 = base64.urlsafe_b64encode(key_hash)
    return Fernet(key_b64)


def email_blind_index(email: str) -> str:
    """Deterministischer Blind-Index für E-Mail-Adressen (WP2-Nachtrag, Go-Live-Blocker).

    Fernet ist nicht-deterministisch, daher kann die verschlüsselte E-Mail-Spalte
    weder unique sein noch per Lookup gefunden werden. Lösung: HMAC-SHA256 über die
    normalisierte Adresse (lower/strip) mit dem PII-Schlüssel als HMAC-Key.
    - HMAC statt reinem Hash: ohne Schlüssel kein Wörterbuch-/Brute-Force-Angriff
      auf die Indexspalte.
    - Deterministisch: unique-Constraint + get_or_create funktionieren weiter.
    - Schlüsselrotation rotiert zwingend AUCH den Index (Neuberechnung nötig).
    """
    import hmac as _hmac
    key_str = getattr(settings, 'PII_ENCRYPTION_KEY', 'securats-fallback-super-secure-encryption-key-for-pii-at-rest=')
    normalized = (email or "").strip().lower().encode("utf-8")
    return _hmac.new(key_str.encode("utf-8"), normalized, hashlib.sha256).hexdigest()

class EncryptedCharField(models.CharField):
    """CharField that encrypts data at-rest using Fernet.

    WICHTIG:
    - Der Ciphertext ist deutlich laenger als der Klartext (Fernet-Overhead).
      Daher wird die Spalte als TEXT angelegt (get_internal_type -> 'TextField'),
      damit auf strikten Datenbanken (PostgreSQL/MySQL) kein
      "value too long for type varchar(n)" Fehler auftritt. max_length gilt
      weiterhin fuer die Formular-/Klartext-Validierung.
    - Fernet ist nicht-deterministisch (Zufalls-IV + Timestamp). Exakte Lookups
      wie filter(firstName="...") oder __icontains funktionieren daher NICHT und
      liefern immer 0 Treffer. Suche/Filter auf diesen Feldern vermeiden.
    """
    def get_internal_type(self):
        # Ciphertext in einer laengenlosen TEXT-Spalte ablegen.
        return 'TextField'

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        cipher = get_fernet_cipher()
        return cipher.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        cipher = get_fernet_cipher()
        try:
            return cipher.decrypt(value.encode()).decode()
        except Exception:
            return value  # Return as-is if decryption fails (e.g. migration / unencrypted legacy)

class EncryptedTextField(models.TextField):
    """TextField that encrypts data at-rest using Fernet.

    Hinweis: Fernet ist nicht-deterministisch, exakte Lookups auf diesem Feld
    funktionieren daher nicht.
    """
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        cipher = get_fernet_cipher()
        return cipher.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        cipher = get_fernet_cipher()
        try:
            return cipher.decrypt(value.encode()).decode()
        except Exception:
            return value
