"""
Shop Manager licences in the Ralfiz BMS dashboard (logged-in Ralfiz staff).
Same pattern as the RalfPOS / EduFlow licence pages.
"""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Client

from .models import ShopLicense, ShopLicenseLog


def _int(value, default=0):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _date(value, default=None):
    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError):
        return default


def _money(value, default):
    try:
        return max(Decimal(str(value).strip()), Decimal('0'))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _choice(value, choices, default):
    return value if value in dict(choices) else default


def _log(lic, event, who, **details):
    ShopLicenseLog.objects.create(license=lic, event=event, status=lic.status, details={'by': who, **details})


@login_required
def shop_license_list(request):
    licenses = ShopLicense.objects.select_related('client')
    search = request.GET.get('search', '').strip()
    if search:
        licenses = licenses.filter(Q(shop_name__icontains=search) | Q(license_key__icontains=search)
                                   | Q(shop_phone__icontains=search) | Q(api_domain__icontains=search)
                                   | Q(owner_name__icontains=search))
    status_filter = request.GET.get('status', '')
    if status_filter:
        licenses = licenses.filter(status=status_filter)
    today = timezone.localdate()
    all_lic = ShopLicense.objects.all()
    return render(request, 'shopmanager/license_list.html', {
        'licenses': licenses,
        'search': search,
        'status_filter': status_filter,
        'total': all_lic.count(),
        'active': all_lic.filter(status='active', valid_until__gte=today).count(),
        'expired': all_lic.filter(Q(status='expired') | Q(status='active', valid_until__lt=today)).count(),
        'expiring_soon': all_lic.filter(status='active', valid_until__gte=today,
                                        valid_until__lte=today + timedelta(days=30)).count(),
    })


@login_required
def shop_license_create(request):
    clients = Client.objects.filter(is_active=True).order_by('name')
    if request.method == 'POST':
        p = request.POST
        plan = _choice(p.get('plan'), ShopLicense.PLAN_CHOICES, 'software')
        lic = ShopLicense(
            client=Client.objects.filter(id=p.get('client')).first() if p.get('client') else None,
            shop_name=p.get('shop_name', '').strip(),
            owner_name=p.get('owner_name', '').strip(),
            shop_phone=p.get('shop_phone', '').strip(),
            shop_email=p.get('shop_email', '').strip(),
            shop_address=p.get('shop_address', '').strip(),
            api_domain=ShopLicense.normalize_domain(p.get('api_domain', '')),
            plan=plan,
            yearly_fee=_money(p.get('yearly_fee'), Decimal(ShopLicense.PLAN_FEES.get(plan, 5500))),
            valid_from=_date(p.get('valid_from'), timezone.localdate()),
            valid_until=_date(p.get('valid_until')),
            on_expiry=_choice(p.get('on_expiry'), ShopLicense.ON_EXPIRY_CHOICES, 'read_only'),
            warn_days=_int(p.get('warn_days'), 30),
            grace_period_days=_int(p.get('grace_period_days'), 7),
            notes=p.get('notes', ''),
        )
        if not lic.shop_name:
            messages.error(request, 'Shop name is required.')
        elif lic.valid_until and lic.valid_until < lic.valid_from:
            messages.error(request, 'The end date is before the start date.')
        else:
            lic.save()
            _log(lic, 'create', request.user.username, plan=lic.plan, valid_until=lic.valid_until.isoformat())
            messages.success(request, f'Licence created for {lic.shop_name}: {lic.license_key}')
            return redirect('shop_license_detail', pk=lic.pk)
    return render(request, 'shopmanager/license_form.html', {
        'clients': clients,
        'plans': ShopLicense.PLAN_CHOICES,
        'plan_fees': ShopLicense.PLAN_FEES,
        'on_expiry_choices': ShopLicense.ON_EXPIRY_CHOICES,
        'today': timezone.localdate(),
    })


@login_required
def shop_license_detail(request, pk):
    lic = get_object_or_404(ShopLicense.objects.select_related('client'), pk=pk)
    return render(request, 'shopmanager/license_detail.html', {
        'license': lic,
        'state': lic.state(),
        'logs': lic.logs.all()[:30],
        'clients': Client.objects.filter(is_active=True).order_by('name'),
        'plans': ShopLicense.PLAN_CHOICES,
        'on_expiry_choices': ShopLicense.ON_EXPIRY_CHOICES,
    })


@login_required
@require_POST
def shop_license_update(request, pk):
    lic = get_object_or_404(ShopLicense, pk=pk)
    p = request.POST
    action = p.get('action')
    who = request.user.username

    if action == 'update_details':
        for field in ('shop_name', 'owner_name', 'shop_phone', 'shop_email', 'shop_address', 'notes'):
            if field in p:
                setattr(lic, field, p.get(field, '').strip())
        if 'client' in p:
            lic.client = Client.objects.filter(id=p.get('client')).first() if p.get('client') else None
        lic.plan = _choice(p.get('plan'), ShopLicense.PLAN_CHOICES, lic.plan)
        lic.yearly_fee = _money(p.get('yearly_fee'), lic.yearly_fee)
        lic.on_expiry = _choice(p.get('on_expiry'), ShopLicense.ON_EXPIRY_CHOICES, lic.on_expiry)
        lic.warn_days = _int(p.get('warn_days'), lic.warn_days)
        lic.grace_period_days = _int(p.get('grace_period_days'), lic.grace_period_days)
        new_from = _date(p.get('valid_from'), lic.valid_from)
        new_until = _date(p.get('valid_until'), lic.valid_until)
        if not lic.shop_name:
            messages.error(request, 'Shop name is required.')
            return redirect('shop_license_detail', pk=pk)
        if new_until < new_from:
            messages.error(request, 'The end date is before the start date.')
            return redirect('shop_license_detail', pk=pk)
        lic.valid_from, lic.valid_until = new_from, new_until
        if lic.status == 'expired' and new_until >= timezone.localdate():
            lic.status = 'active'
        lic.save()
        _log(lic, 'update', who, details_updated=True, valid_until=lic.valid_until.isoformat())
        messages.success(request, 'Licence updated. The shop picks this up on its next check.')

    elif action == 'renew':
        days = _int(p.get('extend_days'))
        old = lic.valid_until.isoformat()
        lic.renew(days=days or None)
        _log(lic, 'renew', who, old_valid_until=old, new_valid_until=lic.valid_until.isoformat(),
             extend_days=days or 'one year')
        messages.success(request, f'Renewed. Valid until {lic.valid_until:%d %b %Y}.')

    elif action == 'change_status':
        new_status = p.get('new_status')
        if new_status in ('active', 'suspended', 'revoked'):
            old_status = lic.status
            lic.status = new_status
            lic.status_reason = p.get('reason', '').strip()[:255] if new_status != 'active' else ''
            lic.save(update_fields=['status', 'status_reason', 'updated_at'])
            event = {'active': 'reactivate', 'suspended': 'suspend', 'revoked': 'revoke'}[new_status]
            _log(lic, event, who, old_status=old_status, reason=lic.status_reason)
            messages.success(request, f'Status changed to {new_status}. The shop picks this up on its next check.')

    elif action == 'reset_domain':
        old = lic.api_domain
        lic.api_domain = ''
        lic.save(update_fields=['api_domain', 'updated_at'])
        _log(lic, 'update', who, domain_reset_from=old)
        messages.success(request, 'Installation address cleared. The next activation will bind the new address.')

    return redirect('shop_license_detail', pk=pk)
