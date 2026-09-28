"""
RalfPOS licences in the Ralfiz admin dashboard (HTML views, logged-in Ralfiz staff).
Same pattern as the EduFlow licence pages.
"""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Client

from .models import RalfPOSLicense, RalfPOSLicenseLog


def _int(value, default=0):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


@login_required
def ralfpos_license_list(request):
    licenses = RalfPOSLicense.objects.select_related('client')
    search = request.GET.get('search', '').strip()
    if search:
        licenses = licenses.filter(
            Q(shop_name__icontains=search) | Q(license_key__icontains=search)
            | Q(shop_email__icontains=search) | Q(api_domain__icontains=search) | Q(country__icontains=search)
        )
    status_filter = request.GET.get('status', '')
    if status_filter:
        licenses = licenses.filter(status=status_filter)
    now = timezone.now()
    return render(request, 'ralfpos/license_list.html', {
        'licenses': licenses,
        'search': search,
        'status_filter': status_filter,
        'total': RalfPOSLicense.objects.count(),
        'active': RalfPOSLicense.objects.filter(status='active').count(),
        'expired': RalfPOSLicense.objects.filter(status='expired').count(),
        'expiring_soon': RalfPOSLicense.objects.filter(
            status='active', valid_until__lte=now + timedelta(days=30), valid_until__gte=now).count(),
        'module_names': dict(RalfPOSLicense.MODULE_CHOICES),
    })


@login_required
def ralfpos_license_create(request):
    clients = Client.objects.filter(is_active=True).order_by('name')
    if request.method == 'POST':
        client_id = request.POST.get('client')
        valid_key = [k for k, _ in RalfPOSLicense.MODULE_CHOICES]
        license_obj = RalfPOSLicense(
            client=Client.objects.filter(id=client_id).first() if client_id else None,
            shop_name=request.POST.get('shop_name', '').strip(),
            owner_name=request.POST.get('owner_name', ''),
            shop_email=request.POST.get('shop_email', ''),
            shop_phone=request.POST.get('shop_phone', ''),
            shop_address=request.POST.get('shop_address', ''),
            country=request.POST.get('country', ''),
            api_domain=RalfPOSLicense.normalize_domain(request.POST.get('api_domain', '')),
            license_type=request.POST.get('license_type', 'yearly'),
            billing_cycle=request.POST.get('billing_cycle', 'yearly'),
            grace_period_days=_int(request.POST.get('grace_period_days'), 7),
            max_counters=_int(request.POST.get('max_counters')),
            enabled_modules=[m for m in request.POST.getlist('modules') if m in valid_key],
            server_ip=request.POST.get('server_ip', '') or None,
            deployment_notes=request.POST.get('deployment_notes', ''),
            notes=request.POST.get('notes', ''),
        )
        if not license_obj.shop_name:
            messages.error(request, 'Shop name is required.')
        else:
            license_obj.save()
            RalfPOSLicenseLog.objects.create(license=license_obj, event='create', status='active',
                                             details={'created_by': request.user.username,
                                                      'modules': license_obj.enabled_modules})
            messages.success(request, f'Licence created for {license_obj.shop_name}: {license_obj.license_key}')
            return redirect('ralfpos_license_detail', pk=license_obj.pk)
    return render(request, 'ralfpos/license_form.html', {
        'clients': clients,
        'license_types': RalfPOSLicense.LICENSE_TYPE_CHOICES,
        'billing_cycles': RalfPOSLicense.BILLING_CYCLE_CHOICES,
        'modules': RalfPOSLicense.MODULE_CHOICES,
    })


@login_required
def ralfpos_license_detail(request, pk):
    license_obj = get_object_or_404(RalfPOSLicense, pk=pk)
    return render(request, 'ralfpos/license_detail.html', {
        'license': license_obj,
        'logs': license_obj.logs.all()[:20],
        'modules': RalfPOSLicense.MODULE_CHOICES,
        'enabled': license_obj.get_enabled_modules(),
    })


@login_required
@require_POST
def ralfpos_license_update(request, pk):
    license_obj = get_object_or_404(RalfPOSLicense, pk=pk)
    action = request.POST.get('action')
    who = request.user.username

    if action == 'update_details':
        for field in ('shop_name', 'owner_name', 'shop_email', 'shop_phone', 'country', 'notes', 'deployment_notes'):
            if field in request.POST:
                setattr(license_obj, field, request.POST.get(field, '').strip())
        license_obj.api_domain = RalfPOSLicense.normalize_domain(request.POST.get('api_domain', license_obj.api_domain))
        license_obj.max_counters = _int(request.POST.get('max_counters'), license_obj.max_counters)
        license_obj.grace_period_days = _int(request.POST.get('grace_period_days'), license_obj.grace_period_days)
        license_obj.save()
        RalfPOSLicenseLog.objects.create(license=license_obj, event='update', status=license_obj.status,
                                         details={'details_updated': True, 'changed_by': who})
        messages.success(request, 'Licence details updated.')

    elif action == 'extend':
        days = _int(request.POST.get('extend_days'))
        if days > 0:
            old = license_obj.valid_until.isoformat()
            license_obj.renew(extend_days=days)
            RalfPOSLicenseLog.objects.create(license=license_obj, event='renew', status=license_obj.status,
                                             details={'old_valid_until': old, 'extend_days': days, 'changed_by': who})
            messages.success(request, f'Licence extended by {days} days.')

    elif action == 'update_modules':
        # Unlike EduFlow, nothing ticked means no add-ons (basic app only).
        valid = [k for k, _ in RalfPOSLicense.MODULE_CHOICES]
        before = license_obj.get_enabled_modules()
        license_obj.enabled_modules = [m for m in request.POST.getlist('modules') if m in valid]
        license_obj.save(update_fields=['enabled_modules', 'updated_at'])
        RalfPOSLicenseLog.objects.create(license=license_obj, event='update', status=license_obj.status,
                                         details={'modules_before': before, 'modules_after': license_obj.enabled_modules,
                                                  'changed_by': who})
        messages.success(request, f'Add-ons updated ({len(license_obj.enabled_modules)} enabled). '
                                  'The shop picks this up on its next check, or at once with "Refresh licence".')

    elif action == 'change_status':
        new_status = request.POST.get('new_status')
        if new_status in dict(RalfPOSLicense.STATUS_CHOICES):
            old_status = license_obj.status
            license_obj.status = new_status
            license_obj.save(update_fields=['status', 'updated_at'])
            event = {'active': 'reactivate', 'expired': 'expire', 'suspended': 'suspend', 'revoked': 'revoke'}[new_status]
            RalfPOSLicenseLog.objects.create(license=license_obj, event=event, status=new_status,
                                             details={'old_status': old_status, 'changed_by': who})
            messages.success(request, f'Status changed to {new_status}.')

    elif action == 'reset_domain':
        # Moving a shop to a new server address: the next activation binds the new one.
        old = license_obj.api_domain
        license_obj.api_domain = ''
        license_obj.save(update_fields=['api_domain', 'updated_at'])
        RalfPOSLicenseLog.objects.create(license=license_obj, event='update', status=license_obj.status,
                                         details={'domain_reset_from': old, 'changed_by': who})
        messages.success(request, 'Installation address cleared. The next activation will bind the new address.')

    return redirect('ralfpos_license_detail', pk=pk)
