"""Where the Claude API key comes from.

The owner saves it in Settings > AI, encrypted in the database. Until then, or
after it is removed, the ANTHROPIC_API_KEY environment variable is used. Every
Claude caller asks here instead of reading settings.ANTHROPIC_API_KEY.
"""
from django.conf import settings


def anthropic_api_key():
    from .models import CompanySettings
    try:
        saved = CompanySettings.objects.values_list('anthropic_api_key', flat=True).filter(pk=1).first()
    except Exception:    # table not migrated yet
        saved = None
    from .fields import UNREADABLE
    if saved and saved != UNREADABLE:     # the field decrypts on read
        return saved
    return settings.ANTHROPIC_API_KEY


def key_source():
    """'saved', 'environment' or '' for the Settings page."""
    from .models import CompanySettings
    if CompanySettings.objects.filter(pk=1).exclude(anthropic_api_key='').exists():
        return 'saved'
    return 'environment' if settings.ANTHROPIC_API_KEY else ''


def masked(key):
    return f'{key[:7]}…{key[-4:]}' if len(key) > 14 else '••••'
