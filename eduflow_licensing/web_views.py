"""
Web views for managing EduFlow licenses from the Ralfiz admin dashboard.
HTML views (not API) — accessible by logged-in Ralfiz admins.
"""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import Client

from .models import EduFlowLicense, EduFlowLicenseLog


@login_required
def eduflow_license_list(request):
    licenses = EduFlowLicense.objects.all()

    search = request.GET.get('search', '').strip()
    if search:
        licenses = licenses.filter(
            Q(institute_name__icontains=search)
            | Q(license_key__icontains=search)
            | Q(institute_email__icontains=search)
            | Q(api_domain__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        licenses = licenses.filter(status=status_filter)

    total = EduFlowLicense.objects.count()
    active = EduFlowLicense.objects.filter(status='active').count()
    expired = EduFlowLicense.objects.filter(status='expired').count()
    expiring_soon = EduFlowLicense.objects.filter(
        status='active',
        valid_until__lte=timezone.now() + timedelta(days=30),
        valid_until__gte=timezone.now(),
    ).count()

    return render(request, 'eduflow/license_list.html', {
        'licenses': licenses,
        'search': search,
        'status_filter': status_filter,
        'total': total,
        'active': active,
        'expired': expired,
        'expiring_soon': expiring_soon,
    })


@login_required
def eduflow_license_create(request):
    clients = Client.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        client_id = request.POST.get('client')
        client = Client.objects.get(id=client_id) if client_id else None

        license_obj = EduFlowLicense(
            client=client,
            institute_name=request.POST.get('institute_name', ''),
            institute_owner_name=request.POST.get('institute_owner_name', ''),
            institute_email=request.POST.get('institute_email', ''),
            institute_phone=request.POST.get('institute_phone', ''),
            institute_address=request.POST.get('institute_address', ''),
            api_domain=request.POST.get('api_domain', ''),
            landing_domain=request.POST.get('landing_domain', ''),
            license_type=request.POST.get('license_type', 'yearly'),
            billing_cycle=request.POST.get('billing_cycle', 'yearly'),
            grace_period_days=int(request.POST.get('grace_period_days', 7) or 7),
            max_users=int(request.POST.get('max_users', 0) or 0),
            max_batches=int(request.POST.get('max_batches', 0) or 0),
            server_ip=request.POST.get('server_ip', '') or None,
            deployment_notes=request.POST.get('deployment_notes', ''),
            notes=request.POST.get('notes', ''),
        )
        license_obj.save()

        EduFlowLicenseLog.objects.create(
            license=license_obj,
            event='create',
            status='active',
            details={'created_by': request.user.username},
        )

        messages.success(
            request,
            f'License created for {license_obj.institute_name}: {license_obj.license_key}',
        )
        return redirect('eduflow_license_detail', pk=license_obj.pk)

    return render(request, 'eduflow/license_form.html', {
        'clients': clients,
        'license_types': EduFlowLicense.LICENSE_TYPE_CHOICES,
        'billing_cycles': EduFlowLicense.BILLING_CYCLE_CHOICES,
    })


@login_required
def eduflow_license_detail(request, pk):
    license_obj = get_object_or_404(EduFlowLicense, pk=pk)
    logs = license_obj.logs.all()[:20]

    return render(request, 'eduflow/license_detail.html', {
        'license': license_obj,
        'logs': logs,
        'modules': EduFlowLicense.MODULE_CHOICES,
    })


@login_required
def eduflow_license_update(request, pk):
    license_obj = get_object_or_404(EduFlowLicense, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_details':
            license_obj.institute_name = request.POST.get('institute_name', license_obj.institute_name)
            license_obj.institute_email = request.POST.get('institute_email', license_obj.institute_email)
            license_obj.institute_phone = request.POST.get('institute_phone', license_obj.institute_phone)
            license_obj.api_domain = request.POST.get('api_domain', license_obj.api_domain)
            license_obj.max_users = int(request.POST.get('max_users', 0) or 0)
            license_obj.max_batches = int(request.POST.get('max_batches', 0) or 0)
            license_obj.notes = request.POST.get('notes', '')
            license_obj.save()
            messages.success(request, 'License details updated.')

        elif action == 'extend':
            days = int(request.POST.get('extend_days', 0) or 0)
            if days > 0:
                license_obj.renew(extend_days=days)
                messages.success(request, f'License extended by {days} days.')

        elif action == 'update_modules':
            selected = request.POST.getlist('modules')
            all_module_keys = [m[0] for m in EduFlowLicense.MODULE_CHOICES]
            if set(selected) == set(all_module_keys) or not selected:
                license_obj.enabled_modules = []
            else:
                license_obj.enabled_modules = selected
            license_obj.save(update_fields=['enabled_modules'])
            EduFlowLicenseLog.objects.create(
                license=license_obj,
                event='update',
                status=license_obj.status,
                details={'modules_updated': selected, 'changed_by': request.user.username},
            )
            messages.success(
                request,
                f'Module access updated ({len(selected)} modules enabled).',
            )

        elif action == 'change_status':
            new_status = request.POST.get('new_status')
            if new_status in dict(EduFlowLicense.STATUS_CHOICES):
                old_status = license_obj.status
                license_obj.status = new_status
                license_obj.save(update_fields=['status'])
                EduFlowLicenseLog.objects.create(
                    license=license_obj,
                    event=new_status,
                    status=new_status,
                    details={'old_status': old_status, 'changed_by': request.user.username},
                )
                messages.success(request, f'Status changed to {new_status}.')

        return redirect('eduflow_license_detail', pk=pk)

    return redirect('eduflow_license_detail', pk=pk)
