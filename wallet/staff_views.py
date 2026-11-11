"""The intern's wallet in the staff portal (/staff/wallet/). Look only: no redeeming or editing."""
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse

from employees.portal_views import _base_context, staff_required

from . import services
from .models import XPSettings, xp_to_rupees


def staff_link(entry):
    if not entry.object_id:
        return ''
    names = {'work': 'staff:work_detail', 'uat': 'staff:uat_plan', 'lead': 'staff:lead_detail'}
    try:
        if entry.source_kind == 'assessment':
            return reverse('staff:assessment_list')
        if entry.source_kind in names:
            return reverse(names[entry.source_kind], args=[entry.object_id])
    except Exception:  # noqa: BLE001
        return ''
    return ''


def card(employee):
    """The Home page XP banner, or None when this person has no wallet."""
    settings = XPSettings.current()
    if not services.has_wallet(employee, settings):
        return None
    data = services.summary(employee, settings)
    recent = list(employee.xp_entries.filter(status__in=('approved', 'pending'))
                  .exclude(kind='payout').order_by('-created_at')[:3])
    for e in recent:
        e.link = staff_link(e)
    month = services.month_gained(employee)
    data.update({
        'chart': services.monthly_earned(employee),
        'recent': recent,
        'month_xp': month, 'month_rs': xp_to_rupees(month, settings.rate_paise),
        'ways': [
            ('fa-list-check', 'Finish a work assignment', f'{settings.xp_low}–{settings.xp_urgent} XP'),
            ('fa-clipboard-check', 'Complete a UAT plan', 'Reward shown on the plan'),
            ('fa-file-pen', 'Score in an assessment', f'{settings.xp_per_assessment_percent.normalize()} XP per %'),
            ('fa-bullseye', 'Your lead becomes a client', f'{settings.xp_lead_converted} XP'),
        ],
    })
    return data


@staff_required
def wallet(request):
    employee = request.employee
    settings = XPSettings.current()
    if not services.has_wallet(employee, settings):
        raise Http404
    entries = list(employee.xp_entries.select_related('payout').order_by('-created_at')[:300])
    for e in entries:
        e.link = staff_link(e)
        e.rupees = xp_to_rupees(abs(e.xp), e.rate_paise or settings.rate_paise)
    ctx = _base_context(request, 'wallet')
    ctx.update({'s': services.summary(employee, settings), 'entries': entries,
                'chart': services.monthly_earned(employee), 'settings': settings})
    return render(request, 'staff/wallet.html', ctx)
