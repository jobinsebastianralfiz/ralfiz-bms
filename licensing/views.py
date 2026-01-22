import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import License, LicenseActivation, LicenseKey


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
        
        # Get active key pair
        key_pair = LicenseKey.objects.filter(is_active=True).first()
        if not key_pair:
            return JsonResponse({
                'valid': False,
                'error': 'License system not configured'
            }, status=500)
        
        # Validate the license code cryptographically
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
        
        # License code is valid, now check database record
        license_id = result.get('lid')
        try:
            license_obj = License.objects.get(id=license_id)
        except License.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'error': 'License not found in database'
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
        
        # Check/create activation
        activation, created = LicenseActivation.objects.get_or_create(
            license=license_obj,
            machine_id=machine_id,
            defaults={
                'machine_name': machine_name,
                'ip_address': get_client_ip(request),
                'is_active': True
            }
        )
        
        if created:
            # New activation
            active_count = license_obj.activations.filter(is_active=True).count()
            if active_count > license_obj.max_activations:
                # Too many activations, deactivate this one
                activation.is_active = False
                activation.save()
                return JsonResponse({
                    'valid': False,
                    'error': f'Maximum activations ({license_obj.max_activations}) exceeded'
                }, status=400)
            
            license_obj.current_activations = active_count
            license_obj.save()
        else:
            # Existing activation, update last check
            activation.last_check = timezone.now()
            activation.ip_address = get_client_ip(request)
            if machine_name:
                activation.machine_name = machine_name
            activation.save()
            
            if not activation.is_active:
                return JsonResponse({
                    'valid': False,
                    'error': 'This activation has been deactivated'
                }, status=400)
        
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
        
        # Check if valid
        if not license_obj.is_valid():
            return JsonResponse({
                'valid': False,
                'error': 'License expired or invalid'
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
        
        return JsonResponse({
            'valid': True,
            'days_remaining': license_obj.days_remaining(),
            'valid_until': license_obj.valid_until.isoformat()
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
