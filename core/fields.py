"""Model fields that encrypt their value in the database.

Secrets (credential passwords, SSH keys, development notes) are stored as
Fernet tokens prefixed with ``enc1:`` and decrypted when read, so code that
uses ``credential.password`` keeps working unchanged. Values written before
the field was encrypted (no prefix) are read as plain text and encrypted the
next time the row is saved.

Key: ``CREDENTIAL_ENCRYPTION_KEY`` (a Fernet key) when set, plus a key derived
from ``SECRET_KEY``. New values are encrypted with the first; any of them can
decrypt, so adding the env key later does not lose existing data. Changing or
losing SECRET_KEY without setting CREDENTIAL_ENCRYPTION_KEY first makes stored
secrets unreadable.
"""
import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.db import models

PREFIX = 'enc1:'
UNREADABLE = '[unreadable - encryption key changed]'
log = logging.getLogger(__name__)
_fernet = None


def _cipher():
    global _fernet
    if _fernet is None:
        keys = []
        explicit = getattr(settings, 'CREDENTIAL_ENCRYPTION_KEY', '')
        if explicit:
            keys.append(Fernet(explicit.encode() if isinstance(explicit, str) else explicit))
        derived = base64.urlsafe_b64encode(
            hashlib.sha256(f'ralfiz-credentials:{settings.SECRET_KEY}'.encode()).digest())
        keys.append(Fernet(derived))
        _fernet = MultiFernet(keys)
    return _fernet


def encrypt(value):
    if not value or str(value).startswith(PREFIX):
        return value
    return PREFIX + _cipher().encrypt(str(value).encode()).decode()


def decrypt(value):
    if not value or not str(value).startswith(PREFIX):
        return value
    try:
        return _cipher().decrypt(str(value)[len(PREFIX):].encode()).decode()
    except InvalidToken:
        log.error('Could not decrypt a stored secret: the encryption key has changed.')
        return UNREADABLE


class EncryptedTextField(models.TextField):
    """A TextField whose value is encrypted at rest."""

    def from_db_value(self, value, expression, connection):
        return decrypt(value)

    def to_python(self, value):
        return decrypt(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value == UNREADABLE:
            raise ValueError('Refusing to save a secret that could not be decrypted.')
        return encrypt(value)
