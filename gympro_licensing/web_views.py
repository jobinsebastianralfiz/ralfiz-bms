"""
Web views for managing GymPro licenses from the Ralfiz admin dashboard.
These are HTML views (not API) — accessible by logged-in Ralfiz admins.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import GymLicense, GymLicenseLog
from core.models import Client


@login_required
def gym_license_list(request):
    """List all GymPro licenses with filters."""
    licenses = GymLicense.objects.all()

    # Search
    search = request.GET.get('search', '').strip()
    if search:
        licenses = licenses.filter(
            models_Q(gym_name__icontains=search) |
            models_Q(license_key__icontains=search) |
            models_Q(gym_email__icontains=search) |
            models_Q(api_domain__icontains=search)
        )

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        licenses = licenses.filter(status=status_filter)

    # Stats
    total = GymLicense.objects.count()
    active = GymLicense.objects.filter(status='active').count()
    expired = GymLicense.objects.filter(status='expired').count()
    expiring_soon = GymLicense.objects.filter(
        status='active',
        valid_until__lte=timezone.now() + timedelta(days=30),
        valid_until__gte=timezone.now(),
    ).count()

    return render(request, 'gympro/license_list.html', {
        'licenses': licenses,
        'search': search,
        'status_filter': status_filter,
        'total': total,
        'active': active,
        'expired': expired,
        'expiring_soon': expiring_soon,
    })


@login_required
def gym_license_create(request):
    """Create a new GymPro license."""
    clients = Client.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        client_id = request.POST.get('client')
        client = Client.objects.get(id=client_id) if client_id else None

        license_obj = GymLicense(
            client=client,
            gym_name=request.POST.get('gym_name', ''),
            gym_owner_name=request.POST.get('gym_owner_name', ''),
            gym_email=request.POST.get('gym_email', ''),
            gym_phone=request.POST.get('gym_phone', ''),
            gym_address=request.POST.get('gym_address', ''),
            api_domain=request.POST.get('api_domain', ''),
            landing_domain=request.POST.get('landing_domain', ''),
            license_type=request.POST.get('license_type', 'yearly'),
            billing_cycle=request.POST.get('billing_cycle', 'yearly'),
            grace_period_days=int(request.POST.get('grace_period_days', 7)),
            max_members=int(request.POST.get('max_members', 0)),
            max_trainers=int(request.POST.get('max_trainers', 0)),
            server_ip=request.POST.get('server_ip', '') or None,
            deployment_notes=request.POST.get('deployment_notes', ''),
            notes=request.POST.get('notes', ''),
        )
        license_obj.save()

        GymLicenseLog.objects.create(
            license=license_obj,
            event='create',
            status='active',
            details={'created_by': request.user.username},
        )

        messages.success(request, f'License created for {license_obj.gym_name}: {license_obj.license_key}')
        return redirect('gym_license_detail', pk=license_obj.pk)

    return render(request, 'gympro/license_form.html', {
        'clients': clients,
        'license_types': GymLicense.LICENSE_TYPE_CHOICES,
        'billing_cycles': GymLicense.BILLING_CYCLE_CHOICES,
    })


@login_required
def gym_license_detail(request, pk):
    """View and manage a GymPro license."""
    license_obj = get_object_or_404(GymLicense, pk=pk)
    logs = license_obj.logs.all()[:20]

    return render(request, 'gympro/license_detail.html', {
        'license': license_obj,
        'logs': logs,
        'modules': GymLicense.MODULE_CHOICES,
    })


@login_required
def gym_license_update(request, pk):
    """Update license details."""
    license_obj = get_object_or_404(GymLicense, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_details':
            license_obj.gym_name = request.POST.get('gym_name', license_obj.gym_name)
            license_obj.gym_email = request.POST.get('gym_email', license_obj.gym_email)
            license_obj.gym_phone = request.POST.get('gym_phone', license_obj.gym_phone)
            license_obj.api_domain = request.POST.get('api_domain', license_obj.api_domain)
            license_obj.max_members = int(request.POST.get('max_members', 0))
            license_obj.max_trainers = int(request.POST.get('max_trainers', 0))
            license_obj.notes = request.POST.get('notes', '')
            license_obj.save()
            messages.success(request, 'License details updated.')

        elif action == 'extend':
            days = int(request.POST.get('extend_days', 0))
            if days > 0:
                license_obj.renew(extend_days=days)
                messages.success(request, f'License extended by {days} days.')

        elif action == 'update_modules':
            selected = request.POST.getlist('modules')
            all_module_keys = [m[0] for m in GymLicense.MODULE_CHOICES]
            # If all are selected or none selected, store empty list (= all enabled)
            if set(selected) == set(all_module_keys) or not selected:
                license_obj.enabled_modules = []
            else:
                license_obj.enabled_modules = selected
            license_obj.save(update_fields=['enabled_modules'])
            GymLicenseLog.objects.create(
                license=license_obj, event='update',
                status=license_obj.status,
                details={'modules_updated': selected, 'changed_by': request.user.username},
            )
            messages.success(request, f'Module access updated ({len(selected)} modules enabled).')

        elif action == 'change_status':
            new_status = request.POST.get('new_status')
            if new_status in dict(GymLicense.STATUS_CHOICES):
                old_status = license_obj.status
                license_obj.status = new_status
                license_obj.save(update_fields=['status'])
                GymLicenseLog.objects.create(
                    license=license_obj, event=new_status,
                    status=new_status,
                    details={'old_status': old_status, 'changed_by': request.user.username},
                )
                messages.success(request, f'Status changed to {new_status}.')

        return redirect('gym_license_detail', pk=pk)

    return redirect('gym_license_detail', pk=pk)


# Django Q import for search
from django.db.models import Q as models_Q
