"""Who may use the connector, and how a bearer token becomes a user.

The connector exposes business-wide data (revenue, clients, salaries), so it is
limited to the same people the owner API serves: active owner/partner
employees, plus Django staff. The same check runs twice -- on the OAuth consent
page, so nobody else can mint a token, and on every MCP request, so a token
outlives neither a role change nor a deactivated account.
"""

from django.urls import reverse
from oauth2_provider.oauth2_backends import get_oauthlib_core

from employees.models import Employee

OWNER_ROLES = ('owner', 'partner')

READ_SCOPE = 'bms:read'
WRITE_SCOPE = 'bms:write'
ALL_SCOPES = (READ_SCOPE, WRITE_SCOPE)


def can_use_connector(user) -> bool:
    if user is None or not user.is_authenticated or not user.is_active:
        return False
    if user.is_staff:
        return True
    return Employee.objects.filter(
        user=user, status='active', role__in=OWNER_ROLES,
    ).exists()


def authenticate_bearer(request):
    """Return the AccessToken for a valid bearer token, else None.

    Delegates to django-oauth-toolkit, which checks expiry and -- because
    Claude sends an RFC 8707 resource indicator -- that the token was issued
    for this endpoint and not some other resource.
    """
    if not request.META.get('HTTP_AUTHORIZATION', '').startswith('Bearer '):
        return None
    valid, oauth_request = get_oauthlib_core().verify_request(request, scopes=[])
    if not valid:
        return None
    return oauth_request.access_token


def resource_metadata_url(request) -> str:
    """Absolute URL of the RFC 9728 document for the /mcp resource."""
    path = reverse('oauth2_provider:oauth-resource-metadata-path', kwargs={'resource_path': 'mcp'})
    return request.build_absolute_uri(path)


def www_authenticate(request, error=None) -> str:
    parts = [f'resource_metadata="{resource_metadata_url(request)}"']
    parts.append(f'scope="{" ".join(ALL_SCOPES)}"')
    if error:
        parts.insert(0, f'error="{error}"')
    return 'Bearer ' + ', '.join(parts)
