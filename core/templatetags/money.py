from decimal import Decimal, ROUND_HALF_UP

from django import template

register = template.Library()


@register.filter
def inr(value, places=2):
    """Indian digit grouping: 598850 -> '5,98,850.00' (the ₹ sign stays in the template)."""
    try:
        amount = Decimal(str(value or 0))
    except Exception:
        return value
    places = int(places)
    quantum = Decimal(1).scaleb(-places) if places else Decimal(1)
    amount = amount.quantize(quantum, rounding=ROUND_HALF_UP)
    sign = '-' if amount < 0 else ''
    whole, _, fraction = f'{abs(amount):f}'.partition('.')
    head, tail = whole[:-3], whole[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    grouped = ','.join(groups + [tail])
    return f'{sign}{grouped}.{fraction}' if places else f'{sign}{grouped}'
