"""
RalfPOS Licensing API — called by each shop's RalfPOS server.

POST /api/ralfpos/activate/  {"license_key", "domain", "app_version"?}  first run: binds the domain
POST /api/ralfpos/check/     same body                                   every few hours

Both answer {"valid": bool, "token": "<signed>", "license": {...}}. The token (signing.py) carries the
status, dates, add-on modules and limits; RalfPOS trusts only the token, never the plain "license" copy.
Revoked, suspended and expired licences get a signed token too, so the shop can lock reliably.
There is deliberately no shared-secret admin API: Ralfiz staff manage licences in the dashboard.
"""

import json
from datetime import timedelta

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import signing
from .models import RalfPOSLicense, RalfPOSLicenseLog

REFRESH_DAYS = 30  # the shop must reach this server at least this often, or its cached licence lapses
RATE_LIMIT = (60, 600)  # requests per IP per 10 minutes


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_event(license_obj, event, status, request=None, domain='', details=None):
    RalfPOSLicenseLog.objects.create(
        license=license_obj, event=event, status=status,
        ip_address=get_client_ip(request) if request else None, domain=domain, details=details or {},
    )


def _state(license_obj):
    if license_obj.status in ('revoked', 'suspended'):
        return license_obj.status
    if license_obj.is_valid() or license_obj.is_in_grace_period():
        return 'active'
    return 'expired'


def signed_answer(license_obj, domain):
    now = timezone.now()
    state = _state(license_obj)
    payload = {
        'v': 1,
        'key': license_obj.license_key,
        'shop': license_obj.shop_name,
        'domain': RalfPOSLicense.normalize_domain(domain),
        'status': state,
        'valid_from': license_obj.valid_from.isoformat(),
        'valid_until': license_obj.valid_until.isoformat(),
        'grace_days': license_obj.grace_period_days,
        'modules': license_obj.get_enabled_modules(),
        'max_counters': license_obj.max_counters,
        'issued_at': now.isoformat(),
        'refresh_by': (now + timedelta(days=REFRESH_DAYS)).isoformat(),
    }
    return {
        'valid': state == 'active',
        'token': signing.sign(payload),
        'license': {**payload, 'days_remaining': license_obj.days_remaining(),
                    'in_grace_period': license_obj.is_in_grace_period()},
    }


def _read(request):
    ip = get_client_ip(request) or 'unknown'
    hits = cache.get_or_set(f'ralfpos-lic:{ip}', 0, RATE_LIMIT[1])
    if hits >= RATE_LIMIT[0]:
        return None, JsonResponse({'valid': False, 'error': 'Too many requests. Try again later.'}, status=429)
    try:
        cache.incr(f'ralfpos-lic:{ip}')
    except ValueError:
        pass
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({'valid': False, 'error': 'Invalid JSON'}, status=400)
    key = str(data.get('license_key', '')).strip().upper()
    domain = str(data.get('domain', '')).strip()
    if not key or not domain:
        return None, JsonResponse({'valid': False, 'error': 'license_key and domain are required'}, status=400)
    try:
        lic = RalfPOSLicense.objects.get(license_key=key)
    except RalfPOSLicense.DoesNotExist:
        return None, JsonResponse({'valid': False, 'error': 'Invalid licence key'}, status=404)
    return (lic, domain, str(data.get('app_version', ''))), None


def _answer(request, event):
    parsed, error = _read(request)
    if error:
        return error
    lic, domain, version = parsed
    if not lic.api_domain and event == 'activate':
        lic.api_domain = RalfPOSLicense.normalize_domain(domain)
        lic.save(update_fields=['api_domain'])
    elif not lic.api_domain or not lic.validate_domain(domain):
        log_event(lic, 'domain_mismatch', 'rejected', request, domain, {'expected': lic.api_domain, 'received': domain})
        where = lic.api_domain or 'not activated yet'
        return JsonResponse({'valid': False, 'error': f'This licence belongs to another installation ({where}).'},
                            status=403)
    if _state(lic) == 'expired' and lic.status == 'active':
        lic.status = 'expired'
        lic.save(update_fields=['status'])
    try:
        answer = signed_answer(lic, domain)
    except ImproperlyConfigured:
        return JsonResponse({'valid': False, 'error': 'The licence server is not configured. Contact Ralfiz Technologies.'},
                            status=503)
    lic.record_check(get_client_ip(request), version)
    log_event(lic, event, answer['license']['status'], request, domain)
    return JsonResponse(answer)


@csrf_exempt
@require_POST
def activate_license(request):
    """First run on a shop's server: binds the licence to that installation's address."""
    return _answer(request, 'activate')


@csrf_exempt
@require_POST
def check_license(request):
    """Periodic check (RalfPOS asks every few hours and on "Refresh licence")."""
    return _answer(request, 'check')
