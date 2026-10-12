"""Adapter registry: ``get_adapter('instagram')`` returns the one to use.

SOCIAL_FAKE_ADAPTERS: 'true' uses FakeAdapter everywhere (tests), 'false'
never does, 'auto' (default) fakes a platform only in DEBUG when its app
credentials are not set, so the hub can be tried locally with no keys.
"""
from django.conf import settings

from .fake import FakeAdapter
from .google import GoogleBusinessAdapter, YouTubeAdapter
from .linkedin import LinkedInAdapter
from .meta import FacebookAdapter, InstagramAdapter
from .whatsapp import WhatsAppAdapter
from .x import XAdapter

REAL = {a.platform: a for a in (
    FacebookAdapter(), InstagramAdapter(), LinkedInAdapter(), YouTubeAdapter(), XAdapter(),
    WhatsAppAdapter(), GoogleBusinessAdapter(),
)}
_FAKES = {}


def _fake_mode(real):
    mode = str(getattr(settings, 'SOCIAL_FAKE_ADAPTERS', 'auto')).lower()
    if mode in ('true', '1', 'yes'):
        return True
    if mode in ('false', '0', 'no'):
        return False
    return settings.DEBUG and not real.is_configured()


def get_adapter(platform):
    real = REAL[platform]
    if _fake_mode(real):
        if platform not in _FAKES:
            _FAKES[platform] = FakeAdapter(real)
        return _FAKES[platform]
    return real


def reset_fakes():
    """Tests: forget what the fake adapters recorded."""
    _FAKES.clear()
