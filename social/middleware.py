from django.http import JsonResponse
from django.shortcuts import redirect

from .services import social_only

# What a Social-Hub-only login may reach outside /social/.
OPEN_PREFIXES = ('/social/', '/static/', '/media/', '/logout/', '/favicon',
                 '/privacy/', '/terms/', '/data-deletion/')


class SocialConfinementMiddleware:
    """Keep Social-Hub-only logins inside the hub.

    Most BMS pages only check @login_required, so without this a client's
    reviewer (or Meta's app reviewer) could open invoices and clients. Users
    with any other role are not affected.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (user is not None and user.is_authenticated
                and not request.path.startswith(OPEN_PREFIXES)
                and social_only(user)):
            if request.path.startswith('/api/') or request.path.startswith('/mcp'):
                return JsonResponse({'detail': 'Not available to Social Hub logins.'}, status=403)
            return redirect('social:home')
        return self.get_response(request)
