"""
Shop Manager Licensing API, called by each shop's Shop Manager server.

POST /api/shopmanager/activate/  {"license_key", "domain", "app_version"?}  first run: binds the domain
POST /api/shopmanager/check/     same body                                   every few hours

Both answer {"valid": bool, "token": "<signed>", "license": {...}}. The shop trusts only the token.
Suspended, revoked and expired licences get a signed token too, so the shop can act on them reliably.
Ralfiz staff manage licences in the BMS dashboard (web_views.py); there is no admin API.
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
from .models import ShopLicense, ShopLicenseLog

REFRESH_DAYS = 30  # the shop must reach this server at least this often, or its cached licence lapses
RATE_LIMIT = (60, 600)  # requests per IP per 10 minutes
VENDOR = {'name': 'Ralfiz Technologies', 'phone': '+91 98956 63498', 'website': 'www.ralfiz.com'}


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_event(lic, event, status, request=None, domain='', details=None):
    ShopLicenseLog.objects.create(license=lic, event=event, status=status,
                                  ip_address=get_client_ip(request) if request else None,
                                  domain=domain, details=details or {})


def signed_answer(lic, domain):
    now = timezone.now()
    state = lic.state()
    payload = {
        'v': 1,
        'product': 'shopmanager',
        'key': lic.license_key,
        'shop': lic.shop_name,
        'domain': ShopLicense.normalize_domain(domain),
        'status': state,
        'reason': lic.status_reason,
        'plan': lic.plan,
        'plan_label': lic.get_plan_display(),
        'yearly_fee': str(lic.yearly_fee),
        'valid_from': lic.valid_from.isoformat(),
        'valid_until': lic.valid_until.isoformat(),
        'grace_days': lic.grace_period_days,
        'warn_days': lic.warn_days,
        'on_expiry': lic.on_expiry,
        'vendor': VENDOR,
        'issued_at': now.isoformat(),
        'refresh_by': (now + timedelta(days=REFRESH_DAYS)).isoformat(),
    }
    return {
        'valid': state in ('active', 'expiring', 'grace'),
        'token': signing.sign(payload),
        'license': {**payload, 'days_remaining': lic.days_remaining()},
    }


def _read(request):
    ip = get_client_ip(request) or 'unknown'
    hits = cache.get_or_set(f'shopmgr-lic:{ip}', 0, RATE_LIMIT[1])
    if hits >= RATE_LIMIT[0]:
        return None, JsonResponse({'valid': False, 'error': 'Too many requests. Try again later.'}, status=429)
    try:
        cache.incr(f'shopmgr-lic:{ip}')
    except ValueError:
        pass
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({'valid': False, 'error': 'Invalid JSON'}, status=400)
    if not isinstance(data, dict):
        return None, JsonResponse({'valid': False, 'error': 'Invalid JSON'}, status=400)
    key = str(data.get('license_key', '')).strip().upper()
    domain = str(data.get('domain', '')).strip()
    if not key or not domain:
        return None, JsonResponse({'valid': False, 'error': 'license_key and domain are required'}, status=400)
    try:
        lic = ShopLicense.objects.get(license_key=key)
    except ShopLicense.DoesNotExist:
        return None, JsonResponse({'valid': False, 'error': 'Invalid licence key'}, status=404)
    return (lic, domain, str(data.get('app_version', ''))), None


def _answer(request, event):
    parsed, error = _read(request)
    if error:
        return error
    lic, domain, version = parsed
    if not lic.api_domain and event == 'activate':
        lic.api_domain = ShopLicense.normalize_domain(domain)
        lic.save(update_fields=['api_domain'])
    elif not lic.api_domain or not lic.validate_domain(domain):
        log_event(lic, 'domain_mismatch', 'rejected', request, domain,
                  {'expected': lic.api_domain, 'received': domain})
        where = lic.api_domain or 'not activated yet'
        return JsonResponse({'valid': False,
                             'error': f'This licence belongs to another installation ({where}).'}, status=403)
    if lic.state() == 'expired' and lic.status == 'active':
        lic.status = 'expired'
        lic.save(update_fields=['status'])
    try:
        answer = signed_answer(lic, domain)
    except ImproperlyConfigured:
        return JsonResponse({'valid': False,
                             'error': 'The licence server is not configured. Contact Ralfiz Technologies.'},
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
    """Periodic check (every few hours, and when the shop clicks "Check now")."""
    return _answer(request, 'check')
