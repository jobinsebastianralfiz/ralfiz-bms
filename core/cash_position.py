"""Cash position helpers.

Single source of truth for "how much money does each BankAccount hold
right now (or as of date X)?" — used by the dashboard, monthly report,
and owner API so all surfaces agree.

Account balance =
    opening_balance (if opening_date <= as_of)
  + payments received via this account's resolved methods (Payment)
  - expenses paid via this account's resolved methods (Expense)
  + internal transfers IN (date <= as_of)
  - internal transfers OUT (date <= as_of)

Future-dated transfers are intentionally excluded from current balance
but exposed separately by pending_transfers().
"""
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from .models import BankAccount, InternalTransfer, Payment, Expense


def _zero():
    return Decimal('0')


def compute_account_balance(account, as_of=None):
    """Return the balance of one BankAccount as of a given date (default today)."""
    if as_of is None:
        as_of = timezone.now().date()

    if account.opening_date and account.opening_date <= as_of:
        balance = Decimal(account.opening_balance or 0)
        since = account.opening_date
    else:
        balance = _zero()
        since = None

    pay_methods = account.resolved_payment_methods()
    exp_methods = account.resolved_expense_methods()

    if pay_methods and since:
        balance += Payment.objects.filter(
            payment_date__gte=since,
            payment_date__lte=as_of,
            payment_method__in=pay_methods,
        ).aggregate(t=Sum('amount'))['t'] or _zero()

    if exp_methods and since:
        balance -= Expense.objects.filter(
            date__gte=since,
            date__lte=as_of,
            payment_method__in=exp_methods,
        ).aggregate(t=Sum('amount'))['t'] or _zero()

    balance += InternalTransfer.objects.filter(
        to_account=account, date__lte=as_of,
    ).aggregate(t=Sum('amount'))['t'] or _zero()

    balance -= InternalTransfer.objects.filter(
        from_account=account, date__lte=as_of,
    ).aggregate(t=Sum('amount'))['t'] or _zero()

    return balance


def cash_position(as_of=None, include_inactive=False):
    """Return list of {account, balance} for all (active) accounts plus total."""
    qs = BankAccount.objects.all() if include_inactive else BankAccount.objects.filter(is_active=True)
    accounts = list(qs.order_by('display_order', 'name'))
    rows = [{'account': a, 'balance': compute_account_balance(a, as_of)} for a in accounts]
    total = sum((r['balance'] for r in rows), _zero())
    return {'accounts': rows, 'total': total}


def pending_transfers(today=None):
    """Future-dated transfers not yet effective."""
    if today is None:
        today = timezone.now().date()
    return InternalTransfer.objects.filter(date__gt=today).select_related('from_account', 'to_account')
