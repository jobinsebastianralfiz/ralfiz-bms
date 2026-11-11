"""Everything that moves XP. Views, signals and commands go through here.

Rules (from design/intern_xp_wallet_plan.md):
- Finished work only creates *pending* XP. Nothing reaches the wallet without
  Admin/HR approval.
- Balance = sum of approved rows. Pending = sum of pending rows.
- The balance never goes below 0, and you can't cash out more than it.
- A payout freezes the rate it was paid at.
"""
import logging
from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from .models import XPEntry, XPPayout, XPSettings, xp_to_rupees

log = logging.getLogger(__name__)


class WalletError(Exception):
    """A rule was broken; the message is shown to the person."""


# --- Who has a wallet --------------------------------------------------------

def is_intern(employee):
    return employee.role == 'intern' or employee.employment_type == 'intern'


def has_wallet(employee, settings=None):
    if employee is None or employee.role in ('owner', 'partner'):
        return False
    if is_intern(employee):
        return True
    return (settings or XPSettings.current()).include_employees


def wallet_people(settings=None):
    """Everyone who can have a wallet (any status, so leavers with XP still show)."""
    from employees.models import Employee
    settings = settings or XPSettings.current()
    qs = Employee.objects.select_related('user').exclude(role__in=('owner', 'partner'))
    if not settings.include_employees:
        qs = qs.filter(Q(role='intern') | Q(employment_type='intern'))
    return qs


# --- Sums --------------------------------------------------------------------

def _sum(qs):
    return qs.aggregate(t=Sum('xp'))['t'] or 0


def balance(employee):
    return _sum(XPEntry.objects.filter(employee=employee, status='approved'))


def pending(employee):
    return _sum(XPEntry.objects.filter(employee=employee, status='pending'))


def paid_total(employee):
    return -_sum(XPEntry.objects.filter(employee=employee, kind='payout', status='approved'))


def paid_amount(employee, since=None):
    qs = XPPayout.objects.filter(employee=employee, status='paid')
    if since:
        qs = qs.filter(paid_on__gte=since)
    return qs.aggregate(t=Sum('amount'))['t'] or 0


def summary(employee, settings=None):
    settings = settings or XPSettings.current()
    bal, pend, paid = balance(employee), pending(employee), paid_total(employee)
    month_start = timezone.localdate().replace(day=1)
    return {
        'balance': bal, 'balance_rs': xp_to_rupees(bal, settings.rate_paise),
        'pending': pend, 'pending_rs': xp_to_rupees(pend, settings.rate_paise),
        'paid_xp': paid, 'paid_rs': paid_amount(employee),
        'paid_month_rs': paid_amount(employee, since=month_start),
        'rate_paise': settings.rate_paise, 'xp_per_rupee': settings.xp_per_rupee,
    }


def earned_this_month(employee, today=None):
    today = today or timezone.localdate()
    return _sum(XPEntry.objects.filter(employee=employee, kind='earned', status='approved',
                                       decided_at__year=today.year, decided_at__month=today.month))


def month_gained(employee, today=None):
    """XP added to the wallet this month (approved earnings and bonuses)."""
    today = today or timezone.localdate()
    return _sum(XPEntry.objects.filter(employee=employee, kind__in=('earned', 'adjustment'), status='approved',
                                       xp__gt=0, decided_at__year=today.year, decided_at__month=today.month))


def monthly_earned(employee, months=6):
    """[(label, xp)] for the last `months` months, oldest first: approved earnings by month."""
    today = timezone.localdate()
    out = []
    y, m = today.year, today.month
    for _ in range(months):
        out.append((y, m))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    rows = []
    for y, m in reversed(out):
        xp = _sum(XPEntry.objects.filter(employee=employee, kind__in=('earned', 'adjustment'), status='approved',
                                         xp__gt=0, decided_at__year=y, decided_at__month=m))
        rows.append({'label': date(y, m, 1).strftime('%b'), 'xp': xp})
    top = max((r['xp'] for r in rows), default=0) or 1
    for r in rows:
        r['pct'] = round(r['xp'] * 100 / top)
    return rows


# --- Notifications -------------------------------------------------------------

def notify(employee, title, body, data=None):
    """Staff-portal notification + push. A push failure must never break the page."""
    from employees.models import Notification
    payload = {'type': 'wallet', **(data or {})}
    Notification.objects.create(employee=employee, title=title, body=body, notification_type='general',
                                data=payload)
    try:
        from employees.utils import send_push_notification
        send_push_notification(employee, title, body, data=payload)
    except Exception as e:  # noqa: BLE001
        log.warning('Wallet push failed for %s: %s', employee, e)


def _money(amount):
    from .templatetags.xp import rs
    return rs(amount)


def _rs(xp, settings):
    from .templatetags.xp import rs
    return f'₹{rs(xp_to_rupees(xp, settings.rate_paise))}'


# --- Automatic pending XP from finished work ------------------------------------

SOURCE_KINDS = {'employees.workassignment': 'work', 'uat.uatplan': 'uat',
                'employees.internassessment': 'assessment', 'crm.lead': 'lead'}


def _source_rows(employee, obj):
    ct = ContentType.objects.get_for_model(obj)
    return ct, XPEntry.objects.filter(employee=employee, content_type=ct, object_id=str(obj.pk))


@transaction.atomic
def sync_source(employee, obj, done, xp, title):
    """Bring this person's XP for one piece of work in line with its state.

    done=True  -> make sure there is pending (or approved) XP for it.
    done=False -> the work was reopened/cancelled: close pending XP, and reverse
                  approved XP with a correcting row.
    Safe to call on every save: the unique source constraint plus these checks
    mean re-saving never creates a second row.
    """
    if not has_wallet(employee):
        return None
    ct, rows = _source_rows(employee, obj)
    rows = rows.select_for_update()
    kind = SOURCE_KINDS.get(f'{ct.app_label}.{ct.model}', 'manual')
    earned = rows.filter(kind='earned').first()
    open_rows = rows.filter(status='pending')
    net = _sum(rows.filter(status='approved'))

    if done:
        xp = max(int(xp or 0), 0)
        if open_rows.exists():
            # Not decided yet: keep the suggestion current (e.g. a regraded test).
            for row in open_rows:
                if row.suggested_xp != xp and xp:
                    row.xp = row.suggested_xp = xp
                    row.title = title[:255]
                    row.save(update_fields=['xp', 'suggested_xp', 'title'])
            return open_rows.first()
        if net > 0 or not xp:
            return None
        if earned is None:
            return XPEntry.objects.create(employee=employee, xp=xp, suggested_xp=xp, kind='earned',
                                          status='pending', source_kind=kind, content_type=ct,
                                          object_id=str(obj.pk), title=title[:255])
        if earned.status == 'rejected':
            if earned.closed_by_system and not earned.decided_by_id:
                # Closed only because the work was reopened: it is back for approval.
                earned.status, earned.closed_by_system = 'pending', False
                earned.xp = earned.suggested_xp = xp
                earned.note, earned.decided_at = '', None
                earned.save()
                return earned
            return None  # Admin/HR said no; finishing it again doesn't ask twice.
        # Approved, then reversed when reopened, now done again: ask once more.
        return XPEntry.objects.create(employee=employee, xp=xp, suggested_xp=xp, kind='adjustment',
                                      status='pending', source_kind=kind, content_type=ct,
                                      object_id=str(obj.pk), title=f'{title} (completed again)'[:255])

    now = timezone.now()
    for row in open_rows:
        row.status, row.closed_by_system, row.decided_at = 'rejected', True, now
        row.note = 'Closed automatically: the work was reopened or cancelled.'
        row.save()
    if net > 0:
        take = min(net, max(balance(employee), 0))
        note = 'The work was reopened or cancelled after the XP was approved.'
        if take < net:
            note += f' {net - take} XP had already been paid out and was not taken back.'
        if take > 0:
            last = rows.filter(status='approved', xp__gt=0).order_by('-created_at').first()
            row = XPEntry.objects.create(employee=employee, xp=-take, kind='reversal', status='approved',
                                         source_kind=kind, content_type=ct, object_id=str(obj.pk),
                                         title=f'Reversed: {title}'[:255], note=note, reverses=last,
                                         decided_at=now)
            notify(employee, 'XP reversed', f'{take} XP for "{title}" was taken back: the work was reopened.',
                   {'entry_id': str(row.pk)})
            return row
    return None


def sync_work_assignment(assignment):
    settings = XPSettings.current()
    xp = assignment.xp_reward if assignment.xp_reward is not None else settings.priority_xp(assignment.priority)
    done = assignment.status == 'completed'
    for emp in assignment.assigned_to.all():
        sync_source(emp, assignment, done, xp, assignment.title)


def uat_tester_done(plan, employee):
    from uat.models import UATCase, UATResult
    from uat.services import tester_sections
    sections = tester_sections(plan, employee)
    case_ids = set(UATCase.objects.filter(section__in=sections).values_list('id', flat=True))
    if not case_ids:
        return False
    marked = set(UATResult.objects.filter(tester=employee, case_id__in=case_ids).values_list('case_id', flat=True))
    return marked == case_ids


def sync_uat_tester(plan, employee):
    if not plan.xp_reward:
        return None
    if not uat_tester_done(plan, employee):
        return None  # Results aren't taken back, so an unfinished plan never reverses XP.
    return sync_source(employee, plan, True, plan.xp_reward, f'UAT: {plan.name}')


def sync_assessment(assessment):
    settings = XPSettings.current()
    pct = assessment.percentage
    done = pct is not None
    xp = round(pct * float(settings.xp_per_assessment_percent)) if done else 0
    return sync_source(assessment.employee, assessment, done, xp, f'Assessment: {assessment.title}')


def sync_lead(lead):
    from employees.models import Employee
    if not lead.created_by_id:
        return None
    emp = Employee.objects.filter(user_id=lead.created_by_id).first()
    if emp is None:
        return None
    # Only a lead that once reached the wallet can be reversed; others are ignored.
    done = lead.status == 'converted'
    if not done and not _source_rows(emp, lead)[1].exists():
        return None
    name = lead.company_name or lead.contact_person
    return sync_source(emp, lead, done, XPSettings.current().xp_lead_converted, f'Lead became a client: {name}')


# --- Admin / HR decisions --------------------------------------------------------

def _check_cap(entry, xp, settings):
    if not settings.monthly_cap or entry.kind != 'earned' or xp <= 0:
        return
    already = earned_this_month(entry.employee)
    if already + xp > settings.monthly_cap:
        left = max(settings.monthly_cap - already, 0)
        raise WalletError(f'{entry.employee.full_name} can earn only {left} more XP this month '
                          f'(monthly cap {settings.monthly_cap} XP). Lower the amount.')


@transaction.atomic
def approve(entry, user, xp=None, note=''):
    entry = XPEntry.objects.select_for_update().get(pk=entry.pk)
    if entry.status != 'pending':
        raise WalletError('This XP was already decided.')
    settings = XPSettings.current()
    new_xp = entry.xp if xp in (None, '') else int(xp)
    if new_xp <= 0:
        raise WalletError('Approve a positive amount, or reject it.')
    if new_xp != entry.xp and not note.strip():
        raise WalletError('Give a reason when you change the amount.')
    _check_cap(entry, new_xp, settings)
    entry.xp, entry.status = new_xp, 'approved'
    entry.note = note.strip()
    entry.decided_by, entry.decided_at = user, timezone.now()
    entry.save()
    body = f'{new_xp} XP ({_rs(new_xp, settings)}) for "{entry.title}" is in your wallet.'
    if entry.suggested_xp and new_xp != entry.suggested_xp:
        body += f' Changed from {entry.suggested_xp} XP: {entry.note}'
    notify(entry.employee, 'XP approved', body, {'entry_id': str(entry.pk)})
    return entry


@transaction.atomic
def reject(entry, user, note):
    entry = XPEntry.objects.select_for_update().get(pk=entry.pk)
    if entry.status != 'pending':
        raise WalletError('This XP was already decided.')
    if not (note or '').strip():
        raise WalletError('Give a reason for rejecting it.')
    entry.status, entry.note = 'rejected', note.strip()
    entry.decided_by, entry.decided_at = user, timezone.now()
    entry.save()
    notify(entry.employee, 'XP not approved', f'"{entry.title}" was not approved: {entry.note}',
           {'entry_id': str(entry.pk)})
    return entry


@transaction.atomic
def adjust(employee, user, xp, note):
    """Manual award (+) or removal (−), approved straight away."""
    xp = int(xp)
    note = (note or '').strip()
    if not xp:
        raise WalletError('Enter an amount other than 0.')
    if not note:
        raise WalletError('Give a reason for the adjustment.')
    if not has_wallet(employee):
        raise WalletError(f'{employee.full_name} has no wallet.')
    _lock(employee)
    if xp < 0 and balance(employee) + xp < 0:
        raise WalletError(f'{employee.full_name} has only {balance(employee)} XP; you can remove at most that.')
    entry = XPEntry.objects.create(employee=employee, xp=xp, kind='adjustment', status='approved',
                                   source_kind='manual', title=note[:255] if xp > 0 else f'Removed: {note}'[:255],
                                   note=note, decided_by=user, decided_at=timezone.now(), created_by=user)
    settings = XPSettings.current()
    if xp > 0:
        notify(employee, 'XP added', f'{xp} XP ({_rs(xp, settings)}) was added to your wallet: {note}',
               {'entry_id': str(entry.pk)})
    else:
        notify(employee, 'XP removed', f'{-xp} XP was removed from your wallet: {note}', {'entry_id': str(entry.pk)})
    return entry


def _lock(employee):
    """Serialise money moves for one person (no-op on SQLite, row lock on Postgres)."""
    from employees.models import Employee
    Employee.objects.select_for_update().filter(pk=employee.pk).first()


# --- Cash out ------------------------------------------------------------------

def refresh_payroll(payroll):
    """Payroll.xp_payout is the sum of the payouts on it, recomputed, never typed in."""
    total = (XPPayout.objects.filter(payroll=payroll, status='paid').aggregate(t=Sum('amount'))['t'] or 0)
    payroll.xp_payout = total
    payroll.calculate()
    payroll.save()


def payroll_for(employee, month, year, user):
    """That month's payslip; a draft is started if there isn't one yet."""
    from employees.models import Payroll
    payroll = Payroll.objects.filter(employee=employee, month=month, year=year).first()
    if payroll is None:
        payroll = Payroll(employee=employee, month=month, year=year,
                          base_salary=employee.monthly_salary or 0, generated_by=user,
                          notes='Started by an XP payout. Run Generate or edit the days before confirming.')
        payroll.calculate()
        payroll.save()
    return payroll


@transaction.atomic
def cash_out(employee, user, xp, method, month=None, year=None, reference='', paid_on=None):
    xp = int(xp)
    if xp <= 0:
        raise WalletError('Cash out at least 1 XP.')
    if method not in dict(XPPayout.METHOD_CHOICES):
        raise WalletError('Choose how it is paid.')
    _lock(employee)
    bal = balance(employee)
    if xp > bal:
        raise WalletError(f'{employee.full_name} has only {bal} XP.')
    settings = XPSettings.current()
    if not settings.rate_paise:
        raise WalletError('Set the XP rate in XP settings first.')
    payroll = None
    if method == 'payslip':
        if not (month and year):
            raise WalletError('Choose the payslip month.')
        payroll = payroll_for(employee, int(month), int(year), user)
        if payroll.status == 'paid':
            raise WalletError('That payslip is already paid. Pick another month or pay separately.')
    payout = XPPayout.objects.create(
        employee=employee, xp=xp, rate_paise=settings.rate_paise, amount=xp_to_rupees(xp, settings.rate_paise),
        method=method, payroll=payroll, reference=(reference or '').strip()[:120],
        paid_on=paid_on or timezone.localdate(), created_by=user)
    where = (f'{date(payroll.year, payroll.month, 1):%B %Y} payslip' if payroll
             else payout.get_method_display())
    XPEntry.objects.create(employee=employee, xp=-xp, kind='payout', status='approved', source_kind='payout',
                           title=f'Paid out · {where}', rate_paise=settings.rate_paise, payout=payout,
                           decided_by=user, decided_at=timezone.now(), created_by=user)
    if payroll:
        refresh_payroll(payroll)
    notify(employee, 'XP paid out', f'{xp} XP was paid out as ₹{_money(payout.amount)} ({where}).',
           {'payout_id': str(payout.pk)})
    return payout


@transaction.atomic
def undo_payout(payout, user, reason, payroll_gone=False):
    """The payslip or payment was undone: a correcting row puts the XP back."""
    payout = XPPayout.objects.select_for_update().get(pk=payout.pk)
    if payout.status != 'paid':
        raise WalletError('This payout was already undone.')
    if not (reason or '').strip():
        raise WalletError('Give a reason.')
    if payout.payroll_id and not payroll_gone and payout.payroll.status == 'paid':
        raise WalletError('That payslip is already paid, so its XP payout can\'t be undone.')
    payout.status, payout.undo_reason = 'undone', reason.strip()[:255]
    payout.undone_by, payout.undone_at = user, timezone.now()
    payroll = payout.payroll
    payout.save()
    original = payout.entries.filter(kind='payout').first()
    XPEntry.objects.create(employee=payout.employee, xp=payout.xp, kind='reversal', status='approved',
                           source_kind='payout', title='Payout undone, XP back in the wallet',
                           note=payout.undo_reason, reverses=original, rate_paise=payout.rate_paise,
                           payout=payout, decided_by=user, decided_at=timezone.now(), created_by=user)
    if payroll and not payroll_gone:
        refresh_payroll(payroll)
    notify(payout.employee, 'XP payout undone',
           f'The payout of {payout.xp} XP was undone and the XP is back in your wallet: {payout.undo_reason}',
           {'payout_id': str(payout.pk)})
    return payout
