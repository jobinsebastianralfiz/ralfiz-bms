from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import redirect

# What a business-partner login may reach. Most business pages only check
# @login_required, so without this a partner could open any record by URL.
OPEN_PREFIXES = (
    '/partner/', '/static/', '/media/', '/logout/', '/favicon', '/robots.txt',
    '/privacy/', '/terms/', '/.well-known/',
)


def _has(user, attr):
    try:
        return getattr(user, attr) is not None
    except ObjectDoesNotExist:
        return False


def partner_only(user):
    """A login that belongs to a business partner and to no staff role."""
    if user.is_staff or user.is_superuser or not _has(user, 'business_partner_profile'):
        return False
    return not any(_has(user, a) for a in ('team_profile', 'employee_profile', 'client_profile'))


class PartnerConfinementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (user is not None and user.is_authenticated
                and not request.path.startswith(OPEN_PREFIXES)
                and partner_only(user)):
            if request.path.startswith(('/api/', '/mcp', '/notes/api/')):
                return JsonResponse({'detail': 'Not available to partner portal logins.'}, status=403)
            return redirect('bizpartners_portal:dashboard')
        return self.get_response(request)
