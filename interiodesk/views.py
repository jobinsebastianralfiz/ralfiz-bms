from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from core.models import CompanySettings


@require_GET
def get_app_config(request):
    """
    Public endpoint for InterioDesk desktop app to check for updates.
    No authentication required.

    Query params:
    - platform: 'macos' | 'windows'
    - app_version: '1.0.0' (current installed version)
    """
    platform = request.GET.get('platform', 'macos')
    app_version = request.GET.get('app_version', '')

    settings = CompanySettings.get_settings()

    # Check maintenance mode
    if settings.interiodesk_maintenance_mode:
        return JsonResponse({
            'maintenance_mode': True,
            'maintenance_message': settings.interiodesk_maintenance_message,
        })

    latest_version = settings.interiodesk_latest_version or '1.0.0'
    min_version = settings.interiodesk_min_version or '1.0.0'

    # Pick platform-specific download URL (uploaded file takes priority over manual URL)
    if platform == 'windows':
        if settings.interiodesk_file_windows:
            update_url = request.build_absolute_uri(settings.interiodesk_file_windows.url)
        else:
            update_url = settings.interiodesk_update_url_windows or ''
    else:
        if settings.interiodesk_file_macos:
            update_url = request.build_absolute_uri(settings.interiodesk_file_macos.url)
        else:
            update_url = settings.interiodesk_update_url_macos or ''

    response_data = {
        'maintenance_mode': False,

        'app': {
            'min_version': min_version,
            'latest_version': latest_version,
            'update_url': update_url,
            'force_update': settings.interiodesk_force_update,
            'release_notes': settings.interiodesk_release_notes or '',
        },

        'server_time': timezone.now().isoformat(),
    }

    # Check if update is available / required
    if app_version:
        try:
            from packaging import version
            current = version.parse(app_version)
            latest = version.parse(latest_version)
            minimum = version.parse(min_version)

            response_data['update_available'] = current < latest
            response_data['update_required'] = current < minimum and settings.interiodesk_force_update

            if response_data['update_required']:
                response_data['update_message'] = f'Please update to version {min_version} or later to continue using InterioDesk.'
            elif response_data['update_available']:
                response_data['update_message'] = f'InterioDesk {latest_version} is available.'
        except Exception:
            response_data['update_available'] = False
            response_data['update_required'] = False

    return JsonResponse(response_data)