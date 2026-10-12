from django import template
from django.utils.html import format_html

from social.models import PLATFORM_LABELS
from social.views import PLATFORM_META

register = template.Library()


@register.filter
def get_item(mapping, key):
    """mapping[key] for dicts, lists and tuples; None if missing."""
    try:
        return mapping.get(key) if hasattr(mapping, 'get') else mapping[key]
    except (IndexError, KeyError, TypeError):
        return None


@register.filter
def platform_label(key):
    return PLATFORM_LABELS.get(key, key)


@register.simple_tag
def picon(platform, size=''):
    """A small round platform badge."""
    m = PLATFORM_META.get(platform, {'icon': 'fas fa-globe', 'color': '#64748b'})
    light = ' is-light' if platform == 'x' else ''
    return format_html('<span class="sh-pi {}{}" style="--pc:{}" title="{}"><i class="{}"></i></span>',
                       size, light, m['color'], PLATFORM_LABELS.get(platform, platform), m['icon'])


@register.filter
def compact(n):
    """12,345 -> 12.3K for big figures; Indian grouping is used elsewhere for money only."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return n
    if n >= 10_000_000:
        return f'{n / 10_000_000:.1f}Cr'
    if n >= 100_000:
        return f'{n / 100_000:.1f}L'
    if n >= 1000:
        return f'{n / 1000:.1f}K'
    return str(n)


@register.filter
def ago(when):
    """12m, 3h, 2d: short ages for stream cards."""
    from django.utils import timezone
    if not when:
        return ''
    secs = max(0, int((timezone.now() - when).total_seconds()))
    if secs < 60:
        return 'now'
    for size, unit in ((86400 * 7, 'w'), (86400, 'd'), (3600, 'h'), (60, 'm')):
        if secs >= size:
            return f'{secs // size}{unit}'
