"""Encrypt platform tokens at rest.

A leaked page token lets someone post as a client's brand, so tokens are
stored encrypted with a key held outside the database (SOCIAL_TOKEN_KEY, a
Fernet key, set as a Railway secret). In DEBUG a key derived from SECRET_KEY
is used so local development works without setup; production refuses to run
without the real key rather than silently using a weaker one.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _fernet():
    key = getattr(settings, 'SOCIAL_TOKEN_KEY', '')
    if not key:
        if not settings.DEBUG:
            raise ImproperlyConfigured('SOCIAL_TOKEN_KEY is not set.')
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt(value):
    if not value:
        return ''
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value):
    if not value:
        return ''
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        # Wrong key (rotated, or a DEBUG-derived token in production): treat
        # as no token so the account shows "Reconnect needed".
        return ''
