import base64
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import License, LicenseActivation, LicenseKey


def _extract_license_id(license_code):
    """Decode a license code far enough to read its embedded license id (lid).

    Does NOT verify the signature — that happens later against the correct key.
    Returns the lid string, or raises ValueError on malformed input.
    """
    code = license_code.strip()
    if code.startswith('REP-'):
        parts = code.split('-', 2)
        if len(parts) < 3:
            raise ValueError('Malformed license code')
        code = parts[2]
    outer = json.loads(base64.b64decode(code.encode('utf-8')).decode('utf-8'))
    payload = json.loads(base64.b64decode(outer['p']).decode('utf-8'))
    lid = payload.get('lid')
    if not lid:
        raise ValueError('License code missing lid')
    return lid


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
@require_http_methods(["POST"])
def validate_license(request):
    """
    Validate a license code.
    
    POST body:
    {
        "license_code": "REP-XXXXXXXX-...",
        "machine_id": "abc123...",
        "machine_name": "John's MacBook Pro"  (optional)
    }
    """
    try:
        data = json.loads(request.body)
        license_code = data.get('license_code', '').strip()
        machine_id = data.get('machine_id', '').strip()
        machine_name = data.get('machine_name', '')
        
        if not license_code:
            return JsonResponse({
                'valid': False,
                'error': 'License code is required'
            }, status=400)
        
        if not machine_id:
            return JsonResponse({
                'valid': False,
                'error': 'Machine ID is required'
            }, status=400)
        
        # Look up the License first so we can verify with the key that signed it.
        # Multiple products (RetailEase, InterioDesk, etc.) can share this app,
        # each with its own LicenseKey; picking the first active key is wrong.
        try:
            license_id = _extract_license_id(license_code)
        except Exception:
            return JsonResponse({
                'valid': False,
                'error': 'Invalid license code format'
            }, status=400)

        try:
            license_obj = License.objects.select_related('key_pair').get(id=license_id)
        except License.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'error': 'License not found in database'
            }, status=400)

        key_pair = license_obj.key_pair
        if not key_pair or not key_pair.is_active:
            return JsonResponse({
                'valid': False,
                'error': 'Signing key is missing or inactive'
            }, status=400)

        # Validate the license code cryptographically against its OWN signing key
        is_valid, result = License.validate_license_code(
            license_code,
            key_pair.public_key,
            machine_id
        )

        if not is_valid:
            return JsonResponse({
                'valid': False,
                'error': result
            }, status=400)
        
        # Check license status
        if license_obj.status == 'revoked':
            return JsonResponse({
                'valid': False,
                'error': 'License has been revoked'
            }, status=400)
        
        if license_obj.status == 'suspended':
            return JsonResponse({
                'valid': False,
                'error': 'License has been suspended'
            }, status=400)
        
        if license_obj.status == 'expired' or not license_obj.is_valid():
            license_obj.status = 'expired'
            license_obj.save()
            return JsonResponse({
                'valid': False,
                'error': 'License has expired'
            }, status=400)
        
        # Check if this machine already has an activation
        try:
            activation = LicenseActivation.objects.get(
                license=license_obj,
                machine_id=machine_id
            )
            # Existing activation — update last check
            if not activation.is_active:
                return JsonResponse({
                    'valid': False,
                    'error': 'This activation has been deactivated'
                }, status=400)
            activation.last_check = timezone.now()
            activation.ip_address = get_client_ip(request)
            if machine_name:
                activation.machine_name = machine_name
            activation.save()
        except LicenseActivation.DoesNotExist:
            # New machine — check activation limit BEFORE creating
            active_count = license_obj.activations.filter(is_active=True).count()
            if active_count >= license_obj.max_activations:
                return JsonResponse({
                    'valid': False,
                    'error': f'Maximum activations ({license_obj.max_activations}) reached. '
                             f'This license is already activated on {active_count} device(s). '
                             f'Deactivate an existing device first.'
                }, status=400)

            activation = LicenseActivation.objects.create(
                license=license_obj,
                machine_id=machine_id,
                machine_name=machine_name,
                ip_address=get_client_ip(request),
                is_active=True
            )
            license_obj.current_activations = active_count + 1
            license_obj.save()
        
        # Return success with license details
        return JsonResponse({
            'valid': True,
            'license': {
                'id': str(license_obj.id),
                'type': license_obj.license_type,
                'customer_name': license_obj.customer_name,
                'customer_email': license_obj.customer_email,
                'valid_until': license_obj.valid_until.isoformat(),
                'days_remaining': license_obj.days_remaining(),
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'valid': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def check_license(request):
    """
    Quick check if a license is still valid (for periodic checks).
    Also returns updated license info if it was renewed on the backend.

    POST body:
    {
        "license_id": "uuid",
        "machine_id": "abc123..."
    }

    Response includes 'renewed' flag if license was renewed since last check.
    """
    try:
        data = json.loads(request.body)
        license_id = data.get('license_id', '').strip()
        machine_id = data.get('machine_id', '').strip()
        last_known_expiry = data.get('last_known_expiry', '')  # ISO format

        if not license_id or not machine_id:
            return JsonResponse({
                'valid': False,
                'error': 'License ID and Machine ID are required'
            }, status=400)

        try:
            license_obj = License.objects.get(id=license_id)
        except License.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'error': 'License not found'
            }, status=400)

        # Check activation
        try:
            activation = LicenseActivation.objects.get(
                license=license_obj,
                machine_id=machine_id,
                is_active=True
            )
            activation.last_check = timezone.now()
            activation.ip_address = get_client_ip(request)
            activation.save()
        except LicenseActivation.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'error': 'Machine not activated'
            }, status=400)

        # Check if license is valid or in grace period
        is_valid = license_obj.is_valid()
        in_grace_period = license_obj.is_in_grace_period() if hasattr(license_obj, 'is_in_grace_period') else False

        # Check if license was renewed (expiry date changed)
        was_renewed = False
        if last_known_expiry:
            try:
                from datetime import datetime
                last_expiry = datetime.fromisoformat(last_known_expiry.replace('Z', '+00:00'))
                if timezone.is_naive(last_expiry):
                    last_expiry = timezone.make_aware(last_expiry)
                was_renewed = license_obj.valid_until > last_expiry
            except (ValueError, TypeError):
                pass

        if not is_valid and not in_grace_period:
            return JsonResponse({
                'valid': False,
                'error': 'License expired',
                'expired': True,
                'valid_until': license_obj.valid_until.isoformat(),
                'can_renew': True,
                'billing_cycle': license_obj.billing_cycle,
            }, status=400)

        response_data = {
            'valid': True,
            'days_remaining': license_obj.days_remaining(),
            'valid_until': license_obj.valid_until.isoformat(),
            'renewed': was_renewed,
            'in_grace_period': in_grace_period,
            'billing_cycle': license_obj.billing_cycle,
            'license_type': license_obj.license_type,
        }

        # If renewed, include full license data so client can update local storage
        if was_renewed:
            response_data['license'] = {
                'id': str(license_obj.id),
                'type': license_obj.license_type,
                'customer_name': license_obj.customer_name,
                'customer_email': license_obj.customer_email,
                'valid_until': license_obj.valid_until.isoformat(),
                'days_remaining': license_obj.days_remaining(),
                'renewal_count': license_obj.renewal_count,
            }

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({
            'valid': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def renew_license(request):
    """
    Renew a license (called after payment is confirmed).
    This is typically called by admin/payment webhook, not directly by app.

    POST body:
    {
        "license_id": "uuid",
        "admin_key": "secret-admin-key",  # For security
        "extend_days": 365,  # Optional, defaults to billing cycle
        "payment_reference": "PAY123"  # Optional, for audit
    }
    """
    try:
        data = json.loads(request.body)
        license_id = data.get('license_id', '').strip()
        admin_key = data.get('admin_key', '').strip()
        extend_days = data.get('extend_days')
        payment_reference = data.get('payment_reference', '')

        # Simple admin key check (in production, use proper auth)
        # You should set this in Django settings
        from django.conf import settings
        expected_key = getattr(settings, 'LICENSE_ADMIN_KEY', 'retailease-admin-secret')

        if admin_key != expected_key:
            return JsonResponse({
                'success': False,
                'error': 'Unauthorized'
            }, status=401)

        if not license_id:
            return JsonResponse({
                'success': False,
                'error': 'License ID is required'
            }, status=400)

        try:
            license_obj = License.objects.get(id=license_id)
        except License.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'License not found'
            }, status=404)

        # Renew the license
        old_valid_until = license_obj.valid_until
        new_valid_until = license_obj.renew(extend_days=extend_days)

        # Add note about renewal
        renewal_note = f"\n[{timezone.now().isoformat()}] Renewed from {old_valid_until.date()} to {new_valid_until.date()}"
        if payment_reference:
            renewal_note += f" (Payment: {payment_reference})"
        license_obj.notes += renewal_note
        license_obj.save(update_fields=['notes'])

        return JsonResponse({
            'success': True,
            'license': {
                'id': str(license_obj.id),
                'customer_name': license_obj.customer_name,
                'old_valid_until': old_valid_until.isoformat(),
                'new_valid_until': new_valid_until.isoformat(),
                'days_remaining': license_obj.days_remaining(),
                'renewal_count': license_obj.renewal_count,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_license(request):
    """
    Refresh license data from server (called by app to get latest license info).
    If license was renewed on backend, returns updated license data.

    IMPORTANT: This endpoint should ALWAYS return the current license state,
    including when the license has been deactivated, revoked, suspended, or expired.
    The client uses this to sync local state with server state.

    POST body:
    {
        "license_id": "uuid",
        "machine_id": "abc123..."
    }
    """
    try:
        data = json.loads(request.body)
        license_id = data.get('license_id', '').strip()
        machine_id = data.get('machine_id', '').strip()

        if not license_id or not machine_id:
            return JsonResponse({
                'success': False,
                'valid': False,
                'error': 'License ID and Machine ID are required'
            }, status=400)

        try:
            license_obj = License.objects.get(id=license_id)
        except License.DoesNotExist:
            return JsonResponse({
                'success': False,
                'valid': False,
                'error': 'License not found'
            }, status=404)

        # Check license status FIRST before checking machine activation
        # This ensures deactivated/revoked licenses are caught even if machine is valid
        if license_obj.status == 'revoked':
            return JsonResponse({
                'success': False,
                'valid': False,
                'error': 'License has been revoked',
                'status': 'revoked',
                'license': {
                    'id': str(license_obj.id),
                    'type': license_obj.license_type,
                    'customer_name': license_obj.customer_name,
                    'customer_email': license_obj.customer_email,
                    'valid_until': license_obj.valid_until.isoformat(),
                    'status': license_obj.status,
                }
            })

        if license_obj.status == 'suspended':
            return JsonResponse({
                'success': False,
                'valid': False,
                'error': 'License has been suspended. Please contact support.',
                'status': 'suspended',
                'license': {
                    'id': str(license_obj.id),
                    'type': license_obj.license_type,
                    'customer_name': license_obj.customer_name,
                    'customer_email': license_obj.customer_email,
                    'valid_until': license_obj.valid_until.isoformat(),
                    'status': license_obj.status,
                }
            })

        # Verify machine is activated
        try:
            activation = LicenseActivation.objects.get(
                license=license_obj,
                machine_id=machine_id
            )

            # Check if this specific activation is deactivated
            if not activation.is_active:
                return JsonResponse({
                    'success': False,
                    'valid': False,
                    'error': 'This device has been deactivated. Please reactivate.',
                    'status': 'device_deactivated',
                    'license': {
                        'id': str(license_obj.id),
                        'type': license_obj.license_type,
                        'customer_name': license_obj.customer_name,
                        'status': license_obj.status,
                    }
                })

            activation.last_check = timezone.now()
            activation.save(update_fields=['last_check'])
        except LicenseActivation.DoesNotExist:
            return JsonResponse({
                'success': False,
                'valid': False,
                'error': 'Machine not activated for this license'
            }, status=403)

        # Check validity and grace period
        is_valid = license_obj.is_valid()
        in_grace_period = license_obj.is_in_grace_period()

        # Check if license is expired (status might still be 'active' but date passed)
        now = timezone.now()
        is_expired = now > license_obj.valid_until

        # Update status to expired if needed
        if is_expired and license_obj.status == 'active' and not in_grace_period:
            license_obj.status = 'expired'
            license_obj.save(update_fields=['status', 'updated_at'])

        # If expired and not in grace period, return error with full info
        if is_expired and not in_grace_period:
            return JsonResponse({
                'success': False,
                'valid': False,
                'error': 'License has expired',
                'status': 'expired',
                'in_grace_period': False,
                'license': {
                    'id': str(license_obj.id),
                    'type': license_obj.license_type,
                    'customer_name': license_obj.customer_name,
                    'customer_email': license_obj.customer_email,
                    'valid_from': license_obj.valid_from.isoformat(),
                    'valid_until': license_obj.valid_until.isoformat(),
                    'days_remaining': 0,
                    'status': 'expired',
                    'billing_cycle': license_obj.billing_cycle,
                    'renewal_count': license_obj.renewal_count,
                    'last_renewed_at': license_obj.last_renewed_at.isoformat() if license_obj.last_renewed_at else None,
                }
            })

        # License is valid (or in grace period)
        return JsonResponse({
            'success': True,
            'valid': True,
            'in_grace_period': in_grace_period,
            'license': {
                'id': str(license_obj.id),
                'type': license_obj.license_type,
                'customer_name': license_obj.customer_name,
                'customer_email': license_obj.customer_email,
                'valid_from': license_obj.valid_from.isoformat(),
                'valid_until': license_obj.valid_until.isoformat(),
                'days_remaining': license_obj.days_remaining(),
                'status': license_obj.status,
                'billing_cycle': license_obj.billing_cycle,
                'renewal_count': license_obj.renewal_count,
                'last_renewed_at': license_obj.last_renewed_at.isoformat() if license_obj.last_renewed_at else None,
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def deactivate_license(request):
    """
    Deactivate a license on a specific machine.
    
    POST body:
    {
        "license_id": "uuid",
        "machine_id": "abc123..."
    }
    """
    try:
        data = json.loads(request.body)
        license_id = data.get('license_id', '').strip()
        machine_id = data.get('machine_id', '').strip()
        
        if not license_id or not machine_id:
            return JsonResponse({
                'success': False,
                'error': 'License ID and Machine ID are required'
            }, status=400)
        
        try:
            activation = LicenseActivation.objects.get(
                license_id=license_id,
                machine_id=machine_id
            )
            activation.is_active = False
            activation.save()
            
            # Update activation count
            license_obj = activation.license
            license_obj.current_activations = license_obj.activations.filter(is_active=True).count()
            license_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': 'License deactivated successfully'
            })
        except LicenseActivation.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Activation not found'
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_public_key(request):
    """Return the public key for embedding in apps"""
    key_pair = LicenseKey.objects.filter(is_active=True).first()
    if not key_pair:
        return JsonResponse({
            'error': 'No active key pair'
        }, status=500)

    return JsonResponse({
        'public_key': key_pair.public_key
    })


@csrf_exempt
@require_http_methods(["POST"])
def get_licenses_by_email(request):
    """
    Get all licenses for a customer email.
    Used by RetailEase website to show licenses in user dashboard.

    POST body:
    {
        "email": "customer@example.com",
        "api_key": "retailease-website-secret-key"
    }

    Response:
    {
        "success": true,
        "licenses": [
            {
                "id": "uuid",
                "license_type": "basic",
                "status": "active",
                "valid_from": "iso-datetime",
                "valid_until": "iso-datetime",
                "days_remaining": 365,
                "billing_cycle": "yearly",
                "customer_name": "John Doe",
                "customer_company": "ABC Store",
                "max_activations": 1,
                "current_activations": 0,
                "created_at": "iso-datetime"
            }
        ]
    }
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        api_key = data.get('api_key', '').strip()

        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email is required'
            }, status=400)

        # Verify API key (shared secret between RetailEase website and ralfizdigital)
        from django.conf import settings
        expected_key = getattr(settings, 'RETAILEASE_WEBSITE_API_KEY', 'retailease-website-secret')

        if api_key != expected_key:
            return JsonResponse({
                'success': False,
                'error': 'Invalid API key'
            }, status=401)

        # Fetch all licenses for this email
        # Search by both License's customer_email AND linked Client's email
        from django.db.models import Q
        licenses = License.objects.filter(
            Q(customer_email__iexact=email) | Q(client__email__iexact=email)
        ).select_related('client').distinct().order_by('-created_at')

        licenses_data = []
        for lic in licenses:
            # Update status if expired
            if lic.status == 'active' and not lic.is_valid() and not lic.is_in_grace_period():
                lic.status = 'expired'
                lic.save(update_fields=['status', 'updated_at'])

            license_data = {
                'id': str(lic.id),
                'license_code': lic.license_code,
                'license_type': lic.license_type,
                'license_type_display': lic.get_license_type_display(),
                'status': lic.status,
                'status_display': lic.get_status_display(),
                'valid_from': lic.valid_from.isoformat(),
                'valid_until': lic.valid_until.isoformat(),
                'days_remaining': lic.days_remaining(),
                'is_valid': lic.is_valid(),
                'in_grace_period': lic.is_in_grace_period(),
                'billing_cycle': lic.billing_cycle,
                'billing_cycle_display': lic.get_billing_cycle_display(),
                'customer_name': lic.customer_name,
                'customer_company': lic.customer_company,
                'max_activations': lic.max_activations,
                'current_activations': lic.current_activations,
                'renewal_count': lic.renewal_count,
                'created_at': lic.created_at.isoformat(),
            }

            # Include client info if linked
            if lic.client:
                license_data['client'] = {
                    'id': str(lic.client.id),
                    'name': lic.client.name,
                    'company_name': lic.client.company_name,
                    'email': lic.client.email,
                    'phone': lic.client.phone,
                }

            licenses_data.append(license_data)

        return JsonResponse({
            'success': True,
            'email': email,
            'count': len(licenses_data),
            'licenses': licenses_data
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
