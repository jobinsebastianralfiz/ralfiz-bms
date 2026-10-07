"""Run an existing DRF view in-process on behalf of the connector's user.

Every connector tool that maps to an owner/admin/CRM endpoint goes through
call_view(). The request is built with APIRequestFactory and force-
authenticated as the OAuth user, then routed with resolve() exactly as a real
request would be -- so the view's own permission classes, validation and side
effects (notifications, activity logs, GST-only managers) all run unchanged.
"""

from django.urls import resolve, reverse
from rest_framework.test import APIRequestFactory, force_authenticate


class ToolError(Exception):
    """A failure Claude should see and can act on (bad ID, invalid value...)."""


#: Substrings of keys whose values never leave the server. Project detail, for
#: one, returns hosting passwords and SSH keys for the owner app.
SECRET_KEY_PARTS = ('password', 'secret', 'ssh_key', 'private_key', 'api_key', 'token', 'face_encoding')

REDACTED = '[hidden]'


def redact(value):
    if isinstance(value, dict):
        return {
            k: (REDACTED if v and any(part in str(k).lower() for part in SECRET_KEY_PARTS) else redact(v))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    return value


def _error_message(status_code, data):
    if isinstance(data, dict):
        for key in ('error', 'detail', 'message'):
            if data.get(key):
                return f'{data[key]} (HTTP {status_code})'
        return f'{data} (HTTP {status_code})'
    return f'Request failed (HTTP {status_code})'


def call_view(ctx, method, url_name, kwargs=None, query=None, data=None):
    """Call the view behind ``url_name`` and return its response data.

    ``ctx`` carries the authenticated user and the outer request; the outer
    request's host is reused so views that build absolute URLs (PDF links,
    attachments) produce real ones, and ALLOWED_HOSTS is satisfied.
    """
    path = reverse(url_name, kwargs=kwargs or {})
    outer = ctx.request
    extra = {'HTTP_HOST': outer.get_host(), 'secure': outer.is_secure()}
    factory = APIRequestFactory()
    method = method.lower()
    if method == 'get':
        # Views test flags with truthy strings, so a False flag is simply left out.
        query = {k: ('true' if v is True else v) for k, v in (query or {}).items()
                 if v is not None and v != '' and v is not False}
        request = factory.get(path, query, **extra)
    else:
        request = getattr(factory, method)(path, data or {}, format='json', **extra)
    force_authenticate(request, user=ctx.user)

    match = resolve(path)
    response = match.func(request, *match.args, **match.kwargs)
    payload = getattr(response, 'data', None)
    if response.status_code >= 400:
        raise ToolError(_error_message(response.status_code, payload))
    return payload


def shape(data, limit=None, item_fields=None):
    """Trim list output so one call can't flood the conversation.

    Applies to a top-level list, or to each list directly under a top-level
    dict. Truncation is reported so Claude knows to narrow the query.
    """

    def trim(items):
        if item_fields:
            items = [{k: it.get(k) for k in item_fields if k in it} if isinstance(it, dict) else it
                     for it in items]
        if limit is not None and len(items) > limit:
            return items[:limit], len(items)
        return items, None

    if isinstance(data, list):
        items, total = trim(list(data))
        if total is None:
            return {'count': len(items), 'items': items}
        return {'count': total, 'returned': len(items), 'truncated': True,
                'items': items, 'hint': 'Narrow the filters or raise limit to see more.'}

    if isinstance(data, dict):
        out, truncated = {}, {}
        for key, value in data.items():
            if isinstance(value, list) and (item_fields or limit is not None):
                value, total = trim(list(value))
                if total is not None:
                    truncated[key] = total
            out[key] = value
        if truncated:
            out['_truncated'] = {k: f'showing {limit} of {n}' for k, n in truncated.items()}
        return out

    return data
