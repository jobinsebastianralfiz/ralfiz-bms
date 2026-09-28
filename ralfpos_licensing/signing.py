"""
Ed25519-signed licence tokens for RalfPOS.

token = base64url(payload JSON) + "." + base64url(signature over the payload bytes)

The private key comes only from the environment (RALFPOS_LICENSE_SIGNING_KEY, base64 of the 32 raw bytes);
it is never stored in the database. Generate a pair with:  python manage.py ralfpos_signing_key
The public key (base64 raw 32 bytes) is built into RalfPOS, which verifies every token it receives.
"""

import base64
import json
import os

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from django.core.exceptions import ImproperlyConfigured


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _private_key():
    raw = os.environ.get('RALFPOS_LICENSE_SIGNING_KEY', '').strip()
    if not raw:
        raise ImproperlyConfigured('RALFPOS_LICENSE_SIGNING_KEY is not set')
    try:
        return Ed25519PrivateKey.from_private_bytes(base64.b64decode(raw + '=' * (-len(raw) % 4)))
    except ValueError as e:
        raise ImproperlyConfigured('RALFPOS_LICENSE_SIGNING_KEY is not a valid Ed25519 key') from e


def sign(payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return f"{_b64(body)}.{_b64(_private_key().sign(body))}"


def new_key_pair():
    """(private_b64, public_b64), both the raw 32 bytes in standard base64."""
    key = Ed25519PrivateKey.generate()
    priv = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(priv).decode(), base64.b64encode(pub).decode()
