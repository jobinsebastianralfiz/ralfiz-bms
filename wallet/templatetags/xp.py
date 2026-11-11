from django import template

from core.templatetags.money import inr

register = template.Library()


@register.filter
def rs(value):
    """₹ amount the Indian way, paise only when there are some: 1,25,000 / 42.50."""
    text = inr(value, 2)
    return text[:-3] if isinstance(text, str) and text.endswith('.00') else text


@register.filter
def xpn(value):
    """XP count with Indian grouping."""
    return inr(value, 0)


@register.filter
def xp_rs(xp):
    """What this many XP is worth at today's rate, e.g. 600 -> '300'."""
    from wallet.models import XPSettings, xp_to_rupees
    return rs(xp_to_rupees(xp or 0, XPSettings.current().rate_paise))
