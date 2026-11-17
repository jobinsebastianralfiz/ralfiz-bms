from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def sar(value, places=2):
    """1234567.5 -> '1,234,567.50' (Saudi riyals group in threes)."""
    try:
        d = Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        return value
    places = int(places)
    text = f'{abs(d):,.{places}f}'
    return f'-{text}' if d < 0 else text


@register.filter
def absval(value):
    try:
        return abs(value)
    except TypeError:
        return value
