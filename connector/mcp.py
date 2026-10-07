"""The MCP endpoint Claude talks to: POST /mcp.

Stateless "streamable HTTP" transport: every request is one JSON-RPC message
answered with one JSON response, no session id and no server-sent events. That
is enough for tools-only servers and keeps this a plain Django view under
gunicorn, instead of the ASGI app the official SDK needs.
"""

import json
import logging
import time
from dataclasses import dataclass
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .auth import (WRITE_SCOPE, authenticate_bearer, can_use_connector, ensure_superuser_owner,
                   www_authenticate)
from .dispatch import ToolError
from .models import ConnectorCallLog
from .tools import TOOLS, run_tool

logger = logging.getLogger(__name__)

#: Newest first. An initialize asking for one of these gets it echoed back;
#: anything else gets the newest, and the client decides whether to continue.
SUPPORTED_PROTOCOL_VERSIONS = ('2025-11-25', '2025-06-18', '2025-03-26')

SERVER_INFO = {'name': 'ralfiz-bms', 'title': 'Ralfiz BMS', 'version': '1.0.0'}

INSTRUCTIONS = (
    "Ralfiz BMS is the business management system of Ralfiz Technologies, a software "
    "agency in Kerala, India. Tools read and update its clients, projects, invoices, "
    "quotes, expenses, AMC contracts, CRM leads, employees, attendance and leave.\n"
    "- When the user names a client, project, lead or person, call `search` first and "
    "use the id it returns. Never ask the user for an id.\n"
    "- Lead and follow-up ids are integers; every other id is a UUID.\n"
    "- Amounts are Indian Rupees. Write them the Indian way: ₹3,06,950 not ₹306,950.\n"
    "- Dates are YYYY-MM-DD, India time.\n"
    "- Tools that change data tell the user what will change; confirm before calling them "
    "unless the user has clearly asked for that exact change."
)

MAX_RESULT_CHARS = 150_000

# JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602


@dataclass
class CallContext:
    request: object
    user: object
    token: object


def _rpc_result(msg_id, result):
    return JsonResponse({'jsonrpc': '2.0', 'id': msg_id, 'result': result},
                        json_dumps_params={'ensure_ascii': False})


def _rpc_error(msg_id, code, message, status=200):
    return JsonResponse({'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': code, 'message': message}},
                        status=status)


def _origin_allowed(request):
    """Reject browser requests from other sites (DNS-rebinding guard).

    Claude's servers and Claude Code send no Origin header; a browser always
    does, so anything present must be one we trust.
    """
    origin = request.META.get('HTTP_ORIGIN')
    if not origin:
        return True
    host = (urlparse(origin).hostname or '').lower()
    allowed = getattr(settings, 'CONNECTOR_ALLOWED_ORIGIN_HOSTS', ())
    own = request.get_host().split(':')[0].lower()
    return host == own or any(host == h or host.endswith('.' + h) for h in allowed)


@method_decorator(csrf_exempt, name='dispatch')
class MCPView(View):
    http_method_names = ['post', 'get', 'delete', 'options']

    def get(self, request):
        # No server-to-client stream on this server.
        return HttpResponse(status=405, headers={'Allow': 'POST'})

    def delete(self, request):
        return HttpResponse(status=405, headers={'Allow': 'POST'})

    def post(self, request):
        if not _origin_allowed(request):
            return _rpc_error(None, INVALID_REQUEST, 'Origin not allowed', status=403)

        token = authenticate_bearer(request)
        if token is None:
            error = 'invalid_token' if 'HTTP_AUTHORIZATION' in request.META else None
            response = JsonResponse({'error': 'unauthorized',
                                     'error_description': 'Sign in to Ralfiz BMS to use this connector.'},
                                    status=401)
            response['WWW-Authenticate'] = www_authenticate(request, error)
            return response

        user = token.user
        ensure_superuser_owner(user)  # tokens issued before this rule existed
        if not can_use_connector(user):
            return _rpc_error(None, INVALID_REQUEST,
                              'This connector is available to owner and partner accounts only.',
                              status=403)

        try:
            message = json.loads(request.body or b'')
        except (ValueError, UnicodeDecodeError):
            return _rpc_error(None, PARSE_ERROR, 'Parse error', status=400)
        if isinstance(message, list):
            return _rpc_error(None, INVALID_REQUEST, 'Batch requests are not supported', status=400)
        if not isinstance(message, dict) or message.get('jsonrpc') != '2.0' or 'method' not in message:
            return _rpc_error(message.get('id') if isinstance(message, dict) else None,
                              INVALID_REQUEST, 'Invalid request', status=400)

        method = message['method']
        params = message.get('params') or {}
        if 'id' not in message:
            # Notification (e.g. notifications/initialized): acknowledge, no body.
            return HttpResponse(status=202)
        msg_id = message['id']

        ctx = CallContext(request=request, user=user, token=token)
        if method == 'initialize':
            return _rpc_result(msg_id, self.initialize(params))
        if method == 'ping':
            return _rpc_result(msg_id, {})
        if method == 'tools/list':
            return _rpc_result(msg_id, {'tools': [t.definition() for t in TOOLS.values()]})
        if method == 'tools/call':
            return self.call_tool(ctx, msg_id, params)
        return _rpc_error(msg_id, METHOD_NOT_FOUND, f'Method not found: {method}')

    def initialize(self, params):
        requested = params.get('protocolVersion')
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else SUPPORTED_PROTOCOL_VERSIONS[0]
        return {
            'protocolVersion': version,
            'capabilities': {'tools': {'listChanged': False}},
            'serverInfo': SERVER_INFO,
            'instructions': INSTRUCTIONS,
        }

    def call_tool(self, ctx, msg_id, params):
        name = params.get('name')
        args = params.get('arguments') or {}
        tool = TOOLS.get(name)
        if tool is None:
            return _rpc_error(msg_id, INVALID_PARAMS, f'Unknown tool: {name}')

        started = time.monotonic()
        ok, error_text, result = True, '', None
        if tool.write and not ctx.token.allow_scopes([WRITE_SCOPE]):
            ok, error_text = False, ('This connection was approved for reading only. Reconnect '
                                     'the Ralfiz BMS connector and allow changes to use this tool.')
        else:
            try:
                result = run_tool(ctx, name, args)
            except ToolError as exc:
                ok, error_text = False, str(exc)
            except Exception:
                logger.exception('Connector tool %s failed', name)
                ok, error_text = False, f'{name} failed with an internal error. Try again or narrow the request.'

        self._log(ctx, tool, args, ok, error_text, started)

        if not ok:
            return _rpc_result(msg_id, {'content': [{'type': 'text', 'text': error_text}], 'isError': True})

        text = json.dumps(result, default=str, ensure_ascii=False)
        if len(text) > MAX_RESULT_CHARS:
            return _rpc_result(msg_id, {
                'content': [{'type': 'text', 'text': (
                    f'The result was too large to return ({len(text):,} characters). '
                    'Use filters or a smaller limit.')}],
                'isError': True,
            })
        return _rpc_result(msg_id, {'content': [{'type': 'text', 'text': text}], 'isError': False})

    @staticmethod
    def _log(ctx, tool, args, ok, error_text, started):
        try:
            ConnectorCallLog.objects.create(
                user=ctx.user,
                client_name=getattr(ctx.token.application, 'name', '') or '',
                tool=tool.name,
                arguments=args if isinstance(args, dict) else {'raw': str(args)},
                is_write=tool.write,
                ok=ok,
                error=error_text[:2000],
                duration_ms=int((time.monotonic() - started) * 1000),
            )
        except Exception:
            logger.exception('Could not write connector call log')
