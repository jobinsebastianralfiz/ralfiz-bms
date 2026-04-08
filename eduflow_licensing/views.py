"""
EduFlow Licensing API — Online validation endpoints.

Each EduFlow FastAPI deployment calls these to validate its license.
All endpoints are CSRF-exempt (called from FastAPI backends).
"""

import json

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import EduFlowLicense, EduFlowLicenseLog


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_event(license_obj, event, status, request=None, domain='', details=None):
    EduFlowLicenseLog.objects.create(
        license=license_obj,
        event=event,
        status=status,
        ip_address=get_client_ip(request) if request else None,
        domain=domain,
        details=details or {},
    )


def license_response(license_obj, extra=None):
    data = {
        'valid': license_obj.is_valid() or license_obj.is_in_grace_period(),
        'license': {
            'id': str(license_obj.id),
            'institute_name': license_obj.institute_name,
            'license_key': license_obj.license_key,
            'license_type': license_obj.license_type,
            'status': license_obj.status,
            'valid_from': license_obj.valid_from.isoformat(),
            'valid_until': license_obj.valid_until.isoformat(),
            'days_remaining': license_obj.days_remaining(),
            'in_grace_period': license_obj.is_in_grace_period(),
            'enabled_modules': license_obj.get_enabled_modules(),
            'max_users': license_obj.max_users,
            'max_batches': license_obj.max_batches,
            'billing_cycle': license_obj.billing_cycle,
            'renewal_count': license_obj.renewal_count,
        },
    }
    if extra:
        data.update(extra)
    return data


def _get_admin_key():
    return getattr(settings, 'EDUFLOW_ADMIN_KEY', getattr(settings, 'LICENSE_ADMIN_KEY', ''))


# ─── 1. VALIDATE LICENSE ─────────────────────────────────────

@csrf_exempt
@require_POST
def validate_license(request):
    """First-time activation: bind license to a domain."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'valid': False, 'error': 'Invalid JSON'}, status=400)

    license_key = data.get('license_key', '').strip()
    domain = data.get('domain', '').strip()

    if not license_key or not domain:
        return JsonResponse({'valid': False, 'error': 'license_key and domain are required'}, status=400)

    try:
        license_obj = EduFlowLicense.objects.get(license_key=license_key)
    except EduFlowLicense.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Invalid license key'}, status=404)

    if license_obj.status == 'revoked':
        log_event(license_obj, 'validate', 'revoked', request, domain)
        return JsonResponse({'valid': False, 'error': 'This license has been revoked'}, status=403)

    if license_obj.status == 'suspended':
        log_event(license_obj, 'validate', 'suspended', request, domain)
        return JsonResponse({'valid': False, 'error': 'This license has been suspended'}, status=403)

    if not license_obj.is_valid() and not license_obj.is_in_grace_period():
        license_obj.status = 'expired'
        license_obj.save(update_fields=['status'])
        log_event(license_obj, 'validate', 'expired', request, domain)
        return JsonResponse({
            'valid': False,
            'error': 'License has expired',
            'expired': True,
            'valid_until': license_obj.valid_until.isoformat(),
            'can_renew': True,
            'billing_cycle': license_obj.billing_cycle,
        }, status=400)

    if not license_obj.api_domain:
        license_obj.api_domain = domain
        license_obj.save(update_fields=['api_domain'])
    elif not license_obj.validate_domain(domain):
        log_event(license_obj, 'domain_mismatch', 'rejected', request, domain, {
            'expected': license_obj.api_domain, 'received': domain,
        })
        return JsonResponse({
            'valid': False,
            'error': f'License is bound to domain: {license_obj.api_domain}',
        }, status=403)

    license_obj.record_check(get_client_ip(request))
    log_event(license_obj, 'validate', 'valid', request, domain)
    return JsonResponse(license_response(license_obj))


# ─── 2. CHECK LICENSE ────────────────────────────────────────

@csrf_exempt
@require_POST
def check_license(request):
    """Periodic license check (every ~4h)."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'valid': False, 'error': 'Invalid JSON'}, status=400)

    license_key = data.get('license_key', '').strip()
    domain = data.get('domain', '').strip()

    if not license_key:
        return JsonResponse({'valid': False, 'error': 'license_key required'}, status=400)

    try:
        license_obj = EduFlowLicense.objects.get(license_key=license_key)
    except EduFlowLicense.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Invalid license key'}, status=404)

    if domain and license_obj.api_domain and not license_obj.validate_domain(domain):
        log_event(license_obj, 'domain_mismatch', 'rejected', request, domain)
        return JsonResponse({'valid': False, 'error': 'Domain mismatch'}, status=403)

    if license_obj.status in ('revoked', 'suspended'):
        log_event(license_obj, 'check', license_obj.status, request, domain)
        return JsonResponse({
            'valid': False,
            'error': f'License is {license_obj.status}',
            'status': license_obj.status,
        }, status=403)

    is_valid = license_obj.is_valid()
    in_grace = license_obj.is_in_grace_period()

    if not is_valid and not in_grace:
        license_obj.status = 'expired'
        license_obj.save(update_fields=['status'])
        log_event(license_obj, 'check', 'expired', request, domain)
        return JsonResponse({
            'valid': False,
            'error': 'License expired',
            'expired': True,
            'valid_until': license_obj.valid_until.isoformat(),
            'days_remaining': license_obj.days_remaining(),
            'can_renew': True,
        }, status=400)

    license_obj.record_check(get_client_ip(request))
    log_event(license_obj, 'check', 'valid', request, domain)
    return JsonResponse(license_response(license_obj))


# ─── 3. RENEW LICENSE ────────────────────────────────────────

@csrf_exempt
@require_POST
def renew_license(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    expected_key = _get_admin_key()
    if not expected_key or data.get('admin_key', '') != expected_key:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    license_key = data.get('license_key', '').strip()
    extend_days = data.get('extend_days')
    payment_reference = data.get('payment_reference', '')

    try:
        license_obj = EduFlowLicense.objects.get(license_key=license_key)
    except EduFlowLicense.DoesNotExist:
        return JsonResponse({'error': 'License not found'}, status=404)

    old_valid_until = license_obj.valid_until.isoformat()
    license_obj.renew(extend_days=extend_days)

    note = f"Renewed on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
    if payment_reference:
        note += f" (Payment: {payment_reference})"
    license_obj.notes = (license_obj.notes + '\n' + note) if license_obj.notes else note
    license_obj.save(update_fields=['notes'])

    log_event(license_obj, 'renew', 'success', request, details={
        'old_valid_until': old_valid_until,
        'new_valid_until': license_obj.valid_until.isoformat(),
        'extend_days': extend_days,
        'payment_reference': payment_reference,
    })

    return JsonResponse({
        'success': True,
        'license': {
            'id': str(license_obj.id),
            'institute_name': license_obj.institute_name,
            'old_valid_until': old_valid_until,
            'new_valid_until': license_obj.valid_until.isoformat(),
            'days_remaining': license_obj.days_remaining(),
            'renewal_count': license_obj.renewal_count,
            'status': license_obj.status,
        },
    })


# ─── 4. REVOKE LICENSE ───────────────────────────────────────

@csrf_exempt
@require_POST
def revoke_license(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    expected_key = _get_admin_key()
    if not expected_key or data.get('admin_key', '') != expected_key:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    license_key = data.get('license_key', '').strip()
    reason = data.get('reason', 'Revoked by admin')

    try:
        license_obj = EduFlowLicense.objects.get(license_key=license_key)
    except EduFlowLicense.DoesNotExist:
        return JsonResponse({'error': 'License not found'}, status=404)

    license_obj.status = 'revoked'
    license_obj.notes = (
        f"{license_obj.notes}\nRevoked: {reason} ({timezone.now().strftime('%Y-%m-%d %H:%M')})"
    )
    license_obj.save(update_fields=['status', 'notes'])

    log_event(license_obj, 'revoke', 'revoked', request, details={'reason': reason})
    return JsonResponse({'success': True, 'message': f'License for {license_obj.institute_name} revoked'})


# ─── 5. SUSPEND / REACTIVATE ─────────────────────────────────

@csrf_exempt
@require_POST
def suspend_license(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    expected_key = _get_admin_key()
    if not expected_key or data.get('admin_key', '') != expected_key:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    license_key = data.get('license_key', '').strip()
    reason = data.get('reason', 'Suspended by admin')

    try:
        license_obj = EduFlowLicense.objects.get(license_key=license_key)
    except EduFlowLicense.DoesNotExist:
        return JsonResponse({'error': 'License not found'}, status=404)

    license_obj.status = 'suspended'
    license_obj.save(update_fields=['status'])
    log_event(license_obj, 'suspend', 'suspended', request, details={'reason': reason})
    return JsonResponse({'success': True, 'message': f'License suspended for {license_obj.institute_name}'})


@csrf_exempt
@require_POST
def reactivate_license(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    expected_key = _get_admin_key()
    if not expected_key or data.get('admin_key', '') != expected_key:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    license_key = data.get('license_key', '').strip()

    try:
        license_obj = EduFlowLicense.objects.get(license_key=license_key)
    except EduFlowLicense.DoesNotExist:
        return JsonResponse({'error': 'License not found'}, status=404)

    if license_obj.status not in ('suspended', 'expired'):
        return JsonResponse({'error': f'Cannot reactivate — current status is {license_obj.status}'}, status=400)

    if not license_obj.is_valid() and not license_obj.is_in_grace_period():
        return JsonResponse({'error': 'License has expired. Renew first.'}, status=400)

    license_obj.status = 'active'
    license_obj.save(update_fields=['status'])
    log_event(license_obj, 'reactivate', 'active', request)
    return JsonResponse(license_response(license_obj, {'success': True}))


# ─── 6. STATUS (Public) ──────────────────────────────────────

@csrf_exempt
@require_GET
def license_status(request):
    license_key = request.GET.get('license_key', '').strip()
    if not license_key:
        return JsonResponse({'error': 'license_key query param required'}, status=400)

    try:
        license_obj = EduFlowLicense.objects.get(license_key=license_key)
    except EduFlowLicense.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Invalid license key'}, status=404)

    return JsonResponse({
        'valid': license_obj.is_valid() or license_obj.is_in_grace_period(),
        'status': license_obj.status,
        'days_remaining': license_obj.days_remaining(),
        'in_grace_period': license_obj.is_in_grace_period(),
        'valid_until': license_obj.valid_until.isoformat(),
    })
