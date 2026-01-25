import json
import hashlib
from functools import wraps
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.files.base import ContentFile

from licensing.models import License, LicenseActivation
from .models import Business, Counter, Backup, SyncLog, APIToken, AppConfig


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def token_required(f):
    """Decorator to require valid API token"""
    @wraps(f)
    def decorated(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'error': 'Missing or invalid Authorization header',
                'code': 'AUTH_REQUIRED'
            }, status=401)

        token_value = auth_header[7:]  # Remove 'Bearer '

        try:
            api_token = APIToken.objects.select_related('license', 'counter').get(token=token_value)
        except APIToken.DoesNotExist:
            return JsonResponse({
                'error': 'Invalid API token',
                'code': 'INVALID_TOKEN'
            }, status=401)

        if not api_token.is_valid():
            return JsonResponse({
                'error': 'Token is expired or inactive',
                'code': 'TOKEN_EXPIRED'
            }, status=401)

        # Update last used
        api_token.update_last_used()

        # Add token info to request
        request.api_token = api_token
        request.license = api_token.license
        request.counter = api_token.counter

        return f(request, *args, **kwargs)
    return decorated


# ============================================
# PUBLIC CONFIG ENDPOINT (No Auth Required)
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
def get_app_config(request):
    """
    Get public app configuration including Google OAuth credentials.
    This endpoint does NOT require authentication so the app can
    fetch config before user logs in.

    Query params:
    - platform: 'macos' | 'windows' | 'linux' | 'ios' | 'android'
    - app_version: '1.0.0'
    """
    platform = request.GET.get('platform', 'desktop')
    app_version = request.GET.get('app_version', '')

    config = AppConfig.get_config()

    # Check maintenance mode
    if config.maintenance_mode:
        return JsonResponse({
            'maintenance_mode': True,
            'maintenance_message': config.maintenance_message,
        })

    # Determine which Google Client ID to return based on platform
    google_client_id = config.google_client_id  # Default (desktop)
    if platform == 'ios' and config.google_client_id_ios:
        google_client_id = config.google_client_id_ios
    elif platform == 'android' and config.google_client_id_android:
        google_client_id = config.google_client_id_android

    response_data = {
        'maintenance_mode': False,

        # Google OAuth
        'google': {
            'client_id': google_client_id,
            'reversed_client_id': config.google_reversed_client_id,
            'enabled': config.google_drive_enabled and bool(google_client_id),
        },

        # Feature flags
        'features': {
            'google_drive_backup': config.google_drive_enabled,
            'server_backup': config.server_backup_enabled,
            'local_backup': config.local_backup_enabled,
        },

        # App version info
        'app': {
            'min_version': config.min_app_version,
            'latest_version': config.latest_app_version,
            'update_url': config.app_update_url,
            'force_update': config.force_update,
        },

        # Support info
        'support': {
            'email': config.support_email,
            'phone': config.support_phone,
            'whatsapp': config.support_whatsapp,
        },

        # Legal
        'legal': {
            'terms_url': config.terms_url,
            'privacy_url': config.privacy_url,
        },

        'server_time': timezone.now().isoformat(),
    }

    # Check if app needs update
    if app_version and config.force_update:
        from packaging import version
        try:
            if version.parse(app_version) < version.parse(config.min_app_version):
                response_data['update_required'] = True
                response_data['update_message'] = f'Please update to version {config.min_app_version} or later.'
        except Exception:
            pass  # Ignore version parsing errors

    return JsonResponse(response_data)


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def authenticate(request):
    """
    Authenticate with license code and get API token.
    Called after license validation to get a token for subsequent API calls.

    Request:
    {
        "license_id": "uuid",
        "machine_id": "hardware-fingerprint",
        "machine_name": "Counter 1",
        "device_type": "desktop",
        "os_info": "macOS 14.0",
        "app_version": "1.0.0"
    }

    Response:
    {
        "token": "api-token-string",
        "business": {...} or null,
        "counter": {...} or null,
        "expires_at": "iso-datetime" or null
    }
    """
    try:
        data = json.loads(request.body)
        license_id = data.get('license_id')
        machine_id = data.get('machine_id')
        machine_name = data.get('machine_name', '')
        device_type = data.get('device_type', '')
        os_info = data.get('os_info', '')
        app_version = data.get('app_version', '')

        if not license_id or not machine_id:
            return JsonResponse({
                'error': 'license_id and machine_id are required',
                'code': 'MISSING_PARAMS'
            }, status=400)

        # Get license
        try:
            license = License.objects.get(id=license_id)
        except License.DoesNotExist:
            return JsonResponse({
                'error': 'License not found',
                'code': 'LICENSE_NOT_FOUND'
            }, status=404)

        if not license.is_valid():
            return JsonResponse({
                'error': 'License is not valid',
                'code': 'LICENSE_INVALID'
            }, status=403)

        # Get or create activation
        activation, created = LicenseActivation.objects.get_or_create(
            license=license,
            machine_id=machine_id,
            defaults={
                'machine_name': machine_name,
                'ip_address': get_client_ip(request),
                'is_active': True
            }
        )

        if created:
            # Check activation limit
            if license.current_activations >= license.max_activations:
                activation.delete()
                return JsonResponse({
                    'error': f'Maximum activations ({license.max_activations}) reached',
                    'code': 'MAX_ACTIVATIONS'
                }, status=403)

            # Increment activation count
            license.current_activations += 1
            license.save(update_fields=['current_activations'])
        else:
            # Update existing activation
            activation.machine_name = machine_name or activation.machine_name
            activation.ip_address = get_client_ip(request)
            activation.last_check = timezone.now()
            activation.save()

        # Get or create business for this license
        business = Business.objects.filter(license=license).first()

        # Get or create counter for this activation
        counter = None
        if business:
            counter, _ = Counter.objects.get_or_create(
                business=business,
                activation=activation,
                defaults={
                    'name': machine_name or f'Counter {business.counters.count() + 1}',
                    'device_type': device_type,
                    'os_info': os_info,
                    'app_version': app_version,
                    'is_primary': business.counters.count() == 0
                }
            )
            # Update counter info
            counter.device_type = device_type or counter.device_type
            counter.os_info = os_info or counter.os_info
            counter.app_version = app_version or counter.app_version
            counter.save()

        # Create or get API token
        api_token, _ = APIToken.objects.get_or_create(
            license=license,
            counter=counter,
            defaults={
                'token': APIToken.generate_token(),
                'name': machine_name or 'API Token',
                'is_active': True
            }
        )

        # Ensure token is active
        if not api_token.is_active:
            api_token.is_active = True
            api_token.token = APIToken.generate_token()
            api_token.save()

        response_data = {
            'token': api_token.token,
            'expires_at': api_token.expires_at.isoformat() if api_token.expires_at else None,
            'business': None,
            'counter': None
        }

        if business:
            response_data['business'] = {
                'id': str(business.id),
                'name': business.name,
                'email': business.email,
                'phone': business.phone,
            }

        if counter:
            response_data['counter'] = {
                'id': str(counter.id),
                'name': counter.name,
                'is_primary': counter.is_primary,
            }

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON',
            'code': 'INVALID_JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'code': 'SERVER_ERROR'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def logout(request):
    """Invalidate the API token"""
    request.api_token.is_active = False
    request.api_token.save()
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})


# ============================================
# BUSINESS ENDPOINTS
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
@token_required
def register_business(request):
    """
    Register or update business information.
    Called during onboarding or when business details change.

    Request:
    {
        "name": "My Store",
        "legal_name": "My Store Pvt Ltd",
        "business_type": "retail",
        "email": "store@example.com",
        ...
    }
    """
    try:
        data = json.loads(request.body)

        # Get or create business
        business, created = Business.objects.get_or_create(
            license=request.license,
            defaults={'name': data.get('name', 'My Business')}
        )

        # Update business fields
        updatable_fields = [
            'name', 'legal_name', 'business_type', 'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code',
            'gst_number', 'pan_number', 'currency_code', 'currency_symbol', 'date_format'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(business, field, data[field])

        business.last_synced_at = timezone.now()
        business.save()

        # Create counter if not exists
        if request.counter is None and hasattr(request, 'api_token'):
            activation = LicenseActivation.objects.filter(
                license=request.license
            ).first()

            if activation:
                counter, _ = Counter.objects.get_or_create(
                    business=business,
                    activation=activation,
                    defaults={
                        'name': 'Main Counter',
                        'is_primary': True
                    }
                )
                # Update API token with counter
                request.api_token.counter = counter
                request.api_token.save()

        return JsonResponse({
            'success': True,
            'business': {
                'id': str(business.id),
                'name': business.name,
                'email': business.email,
                'phone': business.phone,
                'gst_number': business.gst_number,
                'created': created
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@token_required
def get_business(request):
    """Get business information"""
    business = Business.objects.filter(license=request.license).first()

    if not business:
        return JsonResponse({
            'error': 'Business not registered',
            'code': 'BUSINESS_NOT_FOUND'
        }, status=404)

    return JsonResponse({
        'id': str(business.id),
        'name': business.name,
        'legal_name': business.legal_name,
        'business_type': business.business_type,
        'email': business.email,
        'phone': business.phone,
        'website': business.website,
        'address_line1': business.address_line1,
        'address_line2': business.address_line2,
        'city': business.city,
        'state': business.state,
        'country': business.country,
        'postal_code': business.postal_code,
        'gst_number': business.gst_number,
        'pan_number': business.pan_number,
        'currency_code': business.currency_code,
        'currency_symbol': business.currency_symbol,
        'date_format': business.date_format,
        'logo_url': business.logo.url if business.logo else None,
        'counters_count': business.counters.count(),
        'created_at': business.created_at.isoformat(),
        'last_synced_at': business.last_synced_at.isoformat() if business.last_synced_at else None,
    })


# ============================================
# COUNTER ENDPOINTS
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
@token_required
def list_counters(request):
    """List all counters for the business"""
    business = Business.objects.filter(license=request.license).first()

    if not business:
        return JsonResponse({'counters': []})

    counters = business.counters.select_related('activation').all()

    return JsonResponse({
        'counters': [{
            'id': str(c.id),
            'name': c.name,
            'device_name': c.device_name,
            'device_type': c.device_type,
            'status': c.status,
            'is_primary': c.is_primary,
            'last_sync_at': c.last_sync_at.isoformat() if c.last_sync_at else None,
            'app_version': c.app_version,
            'is_current': request.counter and str(request.counter.id) == str(c.id)
        } for c in counters]
    })


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def update_counter(request, counter_id):
    """Update counter information"""
    try:
        data = json.loads(request.body)
        business = Business.objects.filter(license=request.license).first()

        if not business:
            return JsonResponse({'error': 'Business not found'}, status=404)

        try:
            counter = business.counters.get(id=counter_id)
        except Counter.DoesNotExist:
            return JsonResponse({'error': 'Counter not found'}, status=404)

        updatable_fields = ['name', 'description', 'device_name', 'device_type', 'os_info', 'app_version', 'sync_enabled']
        for field in updatable_fields:
            if field in data:
                setattr(counter, field, data[field])

        counter.save()

        return JsonResponse({
            'success': True,
            'counter': {
                'id': str(counter.id),
                'name': counter.name,
                'status': counter.status
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


# ============================================
# BACKUP ENDPOINTS
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
@token_required
def upload_backup(request):
    """
    Upload an encrypted backup file.

    Request (multipart/form-data):
    - file: The encrypted backup file
    - backup_type: 'manual' | 'auto' | 'pre_restore'
    - app_version: '1.0.0'
    - db_version: 5
    - record_counts: '{"products": 100, "invoices": 50}'
    - checksum: 'sha256-hash'
    - notes: 'Optional notes'
    """
    try:
        business = Business.objects.filter(license=request.license).first()

        if not business:
            return JsonResponse({
                'error': 'Business not registered. Register business first.',
                'code': 'BUSINESS_NOT_FOUND'
            }, status=404)

        if 'file' not in request.FILES:
            return JsonResponse({
                'error': 'No file uploaded',
                'code': 'NO_FILE'
            }, status=400)

        uploaded_file = request.FILES['file']

        # Get metadata from POST data
        backup_type = request.POST.get('backup_type', 'manual')
        app_version = request.POST.get('app_version', '')
        db_version = int(request.POST.get('db_version', 1))
        notes = request.POST.get('notes', '')
        checksum = request.POST.get('checksum', '')

        # Parse record counts
        record_counts = {}
        if request.POST.get('record_counts'):
            try:
                record_counts = json.loads(request.POST.get('record_counts'))
            except json.JSONDecodeError:
                pass

        # Generate filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        counter_name = request.counter.name if request.counter else 'unknown'
        filename = f"backup_{business.id}_{counter_name}_{timestamp}.enc"

        # Calculate checksum if not provided
        if not checksum:
            file_content = uploaded_file.read()
            checksum = hashlib.sha256(file_content).hexdigest()
            uploaded_file.seek(0)  # Reset file pointer

        # Create backup record
        backup = Backup.objects.create(
            business=business,
            counter=request.counter,
            filename=filename,
            file_size=uploaded_file.size,
            checksum=checksum,
            is_encrypted=True,
            backup_type=backup_type,
            status='completed',
            app_version=app_version,
            db_version=db_version,
            record_counts=record_counts,
            uploaded_at=timezone.now(),
            notes=notes
        )

        # Save file
        backup.file.save(filename, uploaded_file)

        # Update counter last sync time
        if request.counter:
            request.counter.last_sync_at = timezone.now()
            request.counter.save(update_fields=['last_sync_at'])

        return JsonResponse({
            'success': True,
            'backup': {
                'id': str(backup.id),
                'filename': backup.filename,
                'file_size': backup.file_size,
                'checksum': backup.checksum,
                'created_at': backup.created_at.isoformat()
            }
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'code': 'UPLOAD_ERROR'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@token_required
def list_backups(request):
    """List all backups for the business"""
    business = Business.objects.filter(license=request.license).first()

    if not business:
        return JsonResponse({'backups': []})

    # Get query params
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))
    backup_type = request.GET.get('type')

    backups = business.backups.select_related('counter').all()

    if backup_type:
        backups = backups.filter(backup_type=backup_type)

    total = backups.count()
    backups = backups[offset:offset + limit]

    return JsonResponse({
        'total': total,
        'limit': limit,
        'offset': offset,
        'backups': [{
            'id': str(b.id),
            'filename': b.filename,
            'file_size': b.file_size,
            'backup_type': b.backup_type,
            'status': b.status,
            'app_version': b.app_version,
            'db_version': b.db_version,
            'record_counts': b.record_counts,
            'counter_name': b.counter.name if b.counter else None,
            'created_at': b.created_at.isoformat(),
            'notes': b.notes
        } for b in backups]
    })


@csrf_exempt
@require_http_methods(["GET"])
@token_required
def download_backup(request, backup_id):
    """Download a backup file"""
    from django.http import FileResponse

    business = Business.objects.filter(license=request.license).first()

    if not business:
        return JsonResponse({'error': 'Business not found'}, status=404)

    try:
        backup = business.backups.get(id=backup_id)
    except Backup.DoesNotExist:
        return JsonResponse({'error': 'Backup not found'}, status=404)

    if not backup.file:
        return JsonResponse({'error': 'Backup file not available'}, status=404)

    response = FileResponse(
        backup.file.open('rb'),
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{backup.filename}"'
    response['X-Checksum'] = backup.checksum
    response['X-File-Size'] = str(backup.file_size)

    return response


@csrf_exempt
@require_http_methods(["DELETE"])
@token_required
def delete_backup(request, backup_id):
    """Delete a backup"""
    business = Business.objects.filter(license=request.license).first()

    if not business:
        return JsonResponse({'error': 'Business not found'}, status=404)

    try:
        backup = business.backups.get(id=backup_id)
    except Backup.DoesNotExist:
        return JsonResponse({'error': 'Backup not found'}, status=404)

    backup.delete()

    return JsonResponse({'success': True, 'message': 'Backup deleted'})


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def cleanup_old_backups(request):
    """
    Delete old backups keeping only the most recent ones.

    Request:
    {
        "keep_count": 10,
        "backup_type": "auto"  // optional, filter by type
    }
    """
    try:
        data = json.loads(request.body)
        keep_count = data.get('keep_count', 10)
        backup_type = data.get('backup_type')

        business = Business.objects.filter(license=request.license).first()

        if not business:
            return JsonResponse({'error': 'Business not found'}, status=404)

        backups = business.backups.all()
        if backup_type:
            backups = backups.filter(backup_type=backup_type)

        # Get IDs to keep
        keep_ids = list(backups.order_by('-created_at')[:keep_count].values_list('id', flat=True))

        # Delete old backups
        to_delete = backups.exclude(id__in=keep_ids)
        deleted_count = to_delete.count()

        for backup in to_delete:
            backup.delete()

        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'remaining_count': len(keep_ids)
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


# ============================================
# SYNC ENDPOINTS
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
@token_required
def start_sync(request):
    """
    Start a sync session.
    Returns a sync_log ID to track the sync progress.
    """
    try:
        data = json.loads(request.body)
        sync_type = data.get('sync_type', 'incremental')
        sync_direction = data.get('direction', 'upload')

        business = Business.objects.filter(license=request.license).first()

        if not business:
            return JsonResponse({'error': 'Business not found'}, status=404)

        if not request.counter:
            return JsonResponse({'error': 'Counter not registered'}, status=400)

        sync_log = SyncLog.objects.create(
            business=business,
            counter=request.counter,
            sync_type=sync_type,
            sync_direction=sync_direction,
            status='started'
        )

        return JsonResponse({
            'success': True,
            'sync_id': str(sync_log.id),
            'started_at': sync_log.started_at.isoformat()
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def complete_sync(request, sync_id):
    """
    Mark a sync session as complete.

    Request:
    {
        "status": "completed" | "failed" | "partial",
        "records_uploaded": 100,
        "records_downloaded": 50,
        "conflicts_detected": 2,
        "conflicts_resolved": 2,
        "error_message": "",
        "details": {}
    }
    """
    try:
        data = json.loads(request.body)

        business = Business.objects.filter(license=request.license).first()

        if not business:
            return JsonResponse({'error': 'Business not found'}, status=404)

        try:
            sync_log = business.sync_logs.get(id=sync_id)
        except SyncLog.DoesNotExist:
            return JsonResponse({'error': 'Sync log not found'}, status=404)

        # Update sync log
        sync_log.records_uploaded = data.get('records_uploaded', 0)
        sync_log.records_downloaded = data.get('records_downloaded', 0)
        sync_log.conflicts_detected = data.get('conflicts_detected', 0)
        sync_log.conflicts_resolved = data.get('conflicts_resolved', 0)
        sync_log.details = data.get('details', {})

        sync_log.complete(
            status=data.get('status', 'completed'),
            error_message=data.get('error_message', '')
        )

        # Update counter last sync time
        if request.counter:
            request.counter.last_sync_at = timezone.now()
            request.counter.save(update_fields=['last_sync_at'])

        return JsonResponse({
            'success': True,
            'sync_id': str(sync_log.id),
            'duration_seconds': sync_log.duration_seconds,
            'completed_at': sync_log.completed_at.isoformat()
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
@token_required
def sync_history(request):
    """Get sync history for the business"""
    business = Business.objects.filter(license=request.license).first()

    if not business:
        return JsonResponse({'sync_logs': []})

    limit = int(request.GET.get('limit', 20))
    counter_id = request.GET.get('counter_id')

    sync_logs = business.sync_logs.select_related('counter').all()

    if counter_id:
        sync_logs = sync_logs.filter(counter_id=counter_id)

    sync_logs = sync_logs[:limit]

    return JsonResponse({
        'sync_logs': [{
            'id': str(s.id),
            'sync_type': s.sync_type,
            'sync_direction': s.sync_direction,
            'status': s.status,
            'counter_name': s.counter.name,
            'records_uploaded': s.records_uploaded,
            'records_downloaded': s.records_downloaded,
            'conflicts_detected': s.conflicts_detected,
            'started_at': s.started_at.isoformat(),
            'completed_at': s.completed_at.isoformat() if s.completed_at else None,
            'duration_seconds': s.duration_seconds
        } for s in sync_logs]
    })


# ============================================
# STATUS ENDPOINT
# ============================================

@csrf_exempt
@require_http_methods(["GET"])
@token_required
def status(request):
    """Get current status including license, business, and counter info"""
    business = Business.objects.filter(license=request.license).first()

    return JsonResponse({
        'license': {
            'id': str(request.license.id),
            'type': request.license.license_type,
            'status': request.license.status,
            'valid_until': request.license.valid_until.isoformat(),
            'days_remaining': request.license.days_remaining(),
            'max_activations': request.license.max_activations,
            'current_activations': request.license.current_activations
        },
        'business': {
            'id': str(business.id),
            'name': business.name,
            'counters_count': business.counters.count()
        } if business else None,
        'counter': {
            'id': str(request.counter.id),
            'name': request.counter.name,
            'is_primary': request.counter.is_primary,
            'last_sync_at': request.counter.last_sync_at.isoformat() if request.counter.last_sync_at else None
        } if request.counter else None,
        'server_time': timezone.now().isoformat()
    })