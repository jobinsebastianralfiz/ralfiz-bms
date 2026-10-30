from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import redirect

# What a client portal login may reach. The business side (invoices, clients,
# projects...) mostly only checks @login_required, so without this a client
# could open every other client's records by URL.
OPEN_PREFIXES = (
    '/portal/', '/api/client/', '/static/', '/media/', '/logout/',
    '/client-agreement/', '/agreement/', '/v/', '/card/', '/go/', '/.well-known/', '/favicon', '/robots.txt',
    '/privacy/', '/terms/', '/data-deletion/',
)


def _has(user, attr):
    try:
        return getattr(user, attr) is not None
    except ObjectDoesNotExist:
        return False


def client_only(user):
    """A login that belongs to a client and to no staff role."""
    if user.is_staff or user.is_superuser or not _has(user, 'client_profile'):
        return False
    return not (_has(user, 'team_profile') or _has(user, 'employee_profile'))


class ClientConfinementMiddleware:
    """Keep client logins inside the client portal."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (user is not None and user.is_authenticated
                and not request.path.startswith(OPEN_PREFIXES)
                and client_only(user)):
            # The Notes app (/notes/) is staff-only and deliberately not in OPEN_PREFIXES.
            if request.path.startswith(('/api/', '/mcp', '/notes/api/')):
                return JsonResponse({'detail': 'Not available to client portal logins.'}, status=403)
            return redirect('client_portal:portal_dashboard')
        return self.get_response(request)
