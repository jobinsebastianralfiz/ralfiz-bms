"""OAuth pieces specific to the connector, on top of django-oauth-toolkit.

* ConnectorAuthorizationView -- DOT's consent page, restyled, and refused to
  anyone who is not an owner/partner/staff user.
* ConnectorRegistrationView -- DOT's RFC 7591 dynamic client registration,
  open (Claude registers itself without credentials) but limited to redirect
  URIs on Claude's own domains or this machine, with a per-IP rate limit.
"""

import json
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.views import AuthorizationView, DynamicClientRegistrationView

from .auth import can_use_connector

LOOPBACK_HOSTS = ('localhost', '127.0.0.1', '[::1]', '::1')


class ConnectorAuthorizationView(AuthorizationView):
    template_name = 'connector/authorize.html'

    def dispatch(self, request, *args, **kwargs):
        # Anonymous users fall through to DOT, which redirects to the login page.
        if request.user.is_authenticated and not can_use_connector(request.user):
            return render(request, 'connector/authorize.html', {
                'denied': True,
                'username': request.user.get_username(),
            }, status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        redirect_uri = self.oauth2_data.get('redirect_uri') if hasattr(self, 'oauth2_data') else None
        if redirect_uri:
            context['redirect_host'] = urlparse(redirect_uri).hostname
        context['can_write'] = 'bms:write' in (context.get('scopes') or [])
        return context


def redirect_uri_allowed(uri):
    parsed = urlparse(uri)
    if parsed.scheme == 'http' and parsed.hostname in LOOPBACK_HOSTS:
        return True  # Claude Code / MCP Inspector on this computer
    if parsed.scheme != 'https' or parsed.fragment:
        return False
    return uri in settings.CONNECTOR_REDIRECT_URIS


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (forwarded.split(',')[-1].strip() if forwarded else request.META.get('REMOTE_ADDR', '')) or 'unknown'


@method_decorator(csrf_exempt, name='dispatch')
class ConnectorRegistrationView(DynamicClientRegistrationView):
    RATE_LIMIT = 20          # registrations
    RATE_WINDOW = 60 * 60    # per hour per IP

    def post(self, request, *args, **kwargs):
        key = f'connector-dcr:{_client_ip(request)}'
        count = cache.get(key, 0)
        if count >= self.RATE_LIMIT:
            return JsonResponse({'error': 'slow_down',
                                 'error_description': 'Too many registrations; try again later.'},
                                status=429)
        cache.set(key, count + 1, self.RATE_WINDOW)

        try:
            data = json.loads(request.body or b'{}')
        except ValueError:
            data = None
        if isinstance(data, dict):
            uris = data.get('redirect_uris') or []
            if isinstance(uris, list):
                rejected = [u for u in uris if not (isinstance(u, str) and redirect_uri_allowed(u))]
                if rejected or not uris:
                    return JsonResponse({
                        'error': 'invalid_redirect_uri',
                        'error_description': 'This server only accepts redirect URIs for Claude '
                                             'or a local client.',
                    }, status=400)
        return super().post(request, *args, **kwargs)
