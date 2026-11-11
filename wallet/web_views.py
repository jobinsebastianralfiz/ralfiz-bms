"""HR screens: XP approvals, wallets, one person's ledger (adjust / cash out), settings."""
import calendar
from datetime import date

from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.enrolment_web_views import enrolment_admin as hr_admin
from employees.models import Employee

from . import services
from .models import XPEntry, XPPayout, XPSettings, xp_to_rupees
from .services import WalletError
from .templatetags.xp import rs


def source_link(entry):
    """Where the HR person can look at the work behind an entry."""
    from django.urls import reverse
    if not entry.object_id:
        return ''
    try:
        if entry.source_kind == 'work':
            return reverse('emp_work_detail', args=[entry.object_id])
        if entry.source_kind == 'uat':
            return reverse('uat_plan_detail', args=[entry.object_id])
        if entry.source_kind == 'lead':
            return reverse('crm:lead_detail', args=[entry.object_id])
        if entry.source_kind == 'assessment':
            return reverse('emp_employee_detail', args=[entry.employee_id])
    except Exception:  # noqa: BLE001 - a missing URL name must not break the page
        return ''
    return ''


def _decorate(entries, settings):
    for e in entries:
        e.link = source_link(e)
        e.rupees = xp_to_rupees(abs(e.xp), e.rate_paise or settings.rate_paise)
    return entries


@hr_admin
def approvals(request):
    settings = XPSettings.current()
    qs = (XPEntry.objects.filter(status='pending').select_related('employee__user')
          .order_by('created_at'))
    source = request.GET.get('source', '')
    if source:
        qs = qs.filter(source_kind=source)
    items = _decorate(list(qs[:300]), settings)
    # Same piece of work for several people: show who else is on it, so it can be split.
    groups = {}
    for e in items:
        groups.setdefault((e.content_type_id, e.object_id), []).append(e)
    for e in items:
        e.shared_with = [o.employee.full_name for o in groups[(e.content_type_id, e.object_id)] if o is not e]
    recent = _decorate(list(XPEntry.objects.filter(kind__in=('earned', 'adjustment'), decided_by__isnull=False)
                            .exclude(source_kind='manual').select_related('employee__user', 'decided_by')
                            .order_by('-decided_at')[:15]), settings)
    reversals = _decorate(list(XPEntry.objects.filter(kind='reversal').exclude(source_kind='payout')
                               .select_related('employee__user').order_by('-created_at')[:10]), settings)
    return render(request, 'wallet/approvals.html', {
        'items': items, 'settings': settings, 'source': source, 'sources': XPEntry.SOURCE_CHOICES[:4],
        'pending_total': sum(e.xp for e in items), 'recent': recent, 'reversals': reversals,
    })


@hr_admin
@require_POST
def decide(request):
    """Approve / approve with a new amount / reject one entry, or approve several at once."""
    p = request.POST
    action = p.get('action')
    done, errors = 0, []
    if action == 'approve_selected':
        for entry in XPEntry.objects.filter(pk__in=p.getlist('entries'), status='pending'):
            try:
                services.approve(entry, request.user)
                done += 1
            except WalletError as e:
                errors.append(str(e))
        if done:
            messages.success(request, f'Approved {done} XP item{"s" if done != 1 else ""}.')
    else:
        entry = get_object_or_404(XPEntry, pk=p.get('entry'))
        try:
            if action == 'approve':
                services.approve(entry, request.user, xp=p.get('xp'), note=p.get('note', ''))
                messages.success(request, f'Approved {entry.employee.full_name}: {entry.title}.')
            elif action == 'reject':
                services.reject(entry, request.user, p.get('note', ''))
                messages.success(request, f'Rejected {entry.employee.full_name}: {entry.title}.')
        except (WalletError, ValueError) as e:
            errors.append(str(e) if isinstance(e, WalletError) else 'Enter a whole number of XP.')
    for e in errors:
        messages.error(request, e)
    return redirect(p.get('next') or 'wallet:approvals')


@hr_admin
def wallet_list(request):
    settings = XPSettings.current()
    month_start = timezone.localdate().replace(day=1)
    sums = {r['employee']: r for r in XPEntry.objects.values('employee').annotate(
        bal=Sum('xp', filter=Q(status='approved')),
        pend=Sum('xp', filter=Q(status='pending')),
        paid=Sum('xp', filter=Q(kind='payout', status='approved')))}
    paid_month = dict(XPPayout.objects.filter(status='paid', paid_on__gte=month_start)
                      .values('employee').annotate(t=Sum('amount')).values_list('employee', 't'))
    paid_all = dict(XPPayout.objects.filter(status='paid').values('employee').annotate(t=Sum('amount'))
                    .values_list('employee', 't'))
    rows = []
    for emp in services.wallet_people(settings).order_by('user__first_name'):
        s = sums.get(emp.pk, {})
        bal = s.get('bal') or 0
        if emp.status != 'active' and not bal:
            continue  # leavers only while they still have XP to settle
        rows.append({'employee': emp, 'balance': bal, 'balance_rs': xp_to_rupees(bal, settings.rate_paise),
                     'pending': s.get('pend') or 0, 'paid_month': paid_month.get(emp.pk, 0),
                     'paid_total': paid_all.get(emp.pk, 0), 'left': emp.status != 'active'})
    totals = {'balance': sum(r['balance'] for r in rows), 'pending': sum(r['pending'] for r in rows)}
    totals['balance_rs'] = xp_to_rupees(totals['balance'], settings.rate_paise)
    return render(request, 'wallet/wallet_list.html', {'rows': rows, 'settings': settings, 'totals': totals,
                                                       'queue': XPEntry.objects.filter(status='pending').count()})


def _months():
    today = timezone.localdate()
    out = []
    y, m = today.year, today.month
    for _ in range(3):
        out.append((m, y, f'{calendar.month_name[m]} {y}'))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    nm, ny = (today.month % 12) + 1, today.year + (1 if today.month == 12 else 0)
    return [(nm, ny, f'{calendar.month_name[nm]} {ny}')] + out


@hr_admin
def wallet_detail(request, pk):
    settings = XPSettings.current()
    emp = get_object_or_404(Employee.objects.select_related('user'), pk=pk)
    if request.method == 'POST':
        p = request.POST
        try:
            if p.get('action') == 'adjust':
                sign = -1 if p.get('direction') == 'remove' else 1
                services.adjust(emp, request.user, sign * abs(int(p.get('xp') or 0)), p.get('note', ''))
                messages.success(request, 'Wallet adjusted.')
            elif p.get('action') == 'cash_out':
                month, _, year = (p.get('payslip') or '').partition('-')
                payout = services.cash_out(
                    emp, request.user, int(p.get('xp') or 0), p.get('method', ''),
                    month=month or None, year=year or None, reference=p.get('reference', ''),
                    paid_on=date.fromisoformat(p['paid_on']) if p.get('paid_on') else None)
                messages.success(request, f'Paid out {payout.xp} XP = ₹{rs(payout.amount)}.')
            elif p.get('action') == 'undo_payout':
                payout = get_object_or_404(XPPayout, pk=p.get('payout'), employee=emp)
                services.undo_payout(payout, request.user, p.get('note', ''))
                messages.success(request, f'Payout undone; {payout.xp} XP is back in the wallet.')
        except WalletError as e:
            messages.error(request, str(e))
        except ValueError:
            messages.error(request, 'Enter a whole number of XP and a valid date.')
        return redirect('wallet:detail', pk=emp.pk)

    entries = _decorate(list(emp.xp_entries.select_related('decided_by', 'created_by', 'payout')
                             .order_by('-created_at')[:400]), settings)
    payouts = list(emp.xp_payouts.select_related('payroll', 'created_by').order_by('-created_at')[:50])
    for p in payouts:
        p.month_label = f'{calendar.month_name[p.payroll.month]} {p.payroll.year}' if p.payroll else ''
    return render(request, 'wallet/wallet_detail.html', {
        'emp': emp, 'settings': settings, 's': services.summary(emp, settings), 'entries': entries,
        'payouts': payouts, 'has_wallet': services.has_wallet(emp, settings), 'months': _months(),
        'methods': [m for m in XPPayout.METHOD_CHOICES if m[0] != 'payslip'], 'today': timezone.localdate(),
    })


FIELDS = ['rate_paise', 'xp_low', 'xp_medium', 'xp_high', 'xp_urgent', 'xp_lead_converted', 'monthly_cap']


@hr_admin
def settings_view(request):
    settings = XPSettings.current()
    if request.method == 'POST':
        p = request.POST
        try:
            values = {f: int(p.get(f) or 0) for f in FIELDS}
            per_pct = float(p.get('xp_per_assessment_percent') or 0)
        except ValueError:
            messages.error(request, 'Every amount must be a number.')
            return redirect('wallet:settings')
        if values['rate_paise'] <= 0 or any(v < 0 for v in values.values()) or per_pct < 0:
            messages.error(request, 'The rate must be above 0 and no amount can be negative.')
            return redirect('wallet:settings')
        for f, v in values.items():
            setattr(settings, f, v)
        settings.xp_per_assessment_percent = round(per_pct, 2)
        settings.include_employees = p.get('include_employees') == 'on'
        settings.updated_by = request.user
        settings.save()
        messages.success(request, f'XP settings saved. 1 XP = ₹{settings.rate_paise / 100:.2f}. '
                                  'Payouts already made keep the rate they were paid at.')
        return redirect('wallet:settings')
    return render(request, 'wallet/settings.html', {'settings': settings})
