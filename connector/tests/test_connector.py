"""Tests for the Claude connector: OAuth discovery and flow, the MCP endpoint,
and every tool against the real views it wraps."""

import base64
import hashlib
import json
import secrets
from datetime import date, timedelta
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from oauth2_provider.models import AccessToken, Application

from connector.models import ConnectorCallLog
from connector.tools import TOOLS
from core.models import Client, Credential, Project
from crm.models import Lead
from employees.models import Employee, LeaveRequest, LeaveType, WorkAssignment

CLAUDE_CALLBACK = 'https://claude.ai/api/mcp/auth_callback'
RESOURCE = 'http://testserver/mcp'


def make_employee(username, role, *, staff=False, status='active'):
    user = User.objects.create_user(username=username, password='pw-123456',
                                    first_name=username.title(), is_staff=staff)
    Employee.objects.create(user=user, employee_id=f'EMP-{username.upper()}', role=role,
                            status=status, joining_date=date(2025, 1, 1),
                            employment_type='intern' if role == 'intern' else 'fulltime')
    return user


def make_token(user, scope='bms:read bms:write', resource=None):
    app = Application.objects.create(
        name='Claude', client_type='public', authorization_grant_type='authorization-code',
        redirect_uris=CLAUDE_CALLBACK,
    )
    return AccessToken.objects.create(
        user=user, application=app, token=secrets.token_urlsafe(32), scope=scope,
        expires=timezone.now() + timedelta(hours=1), resource=resource or [],
    )


class MCPClientMixin:
    """Helpers that speak JSON-RPC to /mcp like Claude does."""

    rpc_id = 0

    def rpc(self, method, params=None, token=None, **extra):
        self.rpc_id += 1
        headers = {}
        if token is not None:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        headers.update(extra)
        body = {'jsonrpc': '2.0', 'id': self.rpc_id, 'method': method}
        if params is not None:
            body['params'] = params
        return self.client.post('/mcp', json.dumps(body), content_type='application/json', **headers)

    def call(self, name, args=None, token=None):
        response = self.rpc('tools/call', {'name': name, 'arguments': args or {}},
                            token=token or self.token.token)
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()['result']
        text = result['content'][0]['text']
        return result['isError'], (text if result['isError'] else json.loads(text))

    def ok(self, name, args=None, token=None):
        is_error, data = self.call(name, args, token)
        self.assertFalse(is_error, f'{name} failed: {data}')
        return data


# ---------------------------------------------------------------- discovery

class DiscoveryTests(TestCase):
    def test_protected_resource_metadata_points_at_this_server(self):
        data = self.client.get('/.well-known/oauth-protected-resource/mcp').json()
        self.assertEqual(data['resource'], RESOURCE)
        self.assertEqual(data['authorization_servers'], ['http://testserver'])
        self.assertEqual(sorted(data['scopes_supported']), ['bms:read', 'bms:write'])

    def test_authorization_server_metadata(self):
        data = self.client.get('/.well-known/oauth-authorization-server').json()
        self.assertEqual(data['issuer'], 'http://testserver')
        self.assertEqual(data['authorization_endpoint'], 'http://testserver/oauth/authorize/')
        self.assertEqual(data['token_endpoint'], 'http://testserver/oauth/token/')
        self.assertEqual(data['registration_endpoint'], 'http://testserver/oauth/register/')
        self.assertEqual(data['code_challenge_methods_supported'], ['S256'])
        self.assertEqual(data['response_types_supported'], ['code'])
        self.assertIn('none', data['token_endpoint_auth_methods_supported'])
        self.assertNotIn('password', data['grant_types_supported'])

    def test_unauthenticated_mcp_request_starts_oauth(self):
        response = self.client.post('/mcp', '{}', content_type='application/json')
        self.assertEqual(response.status_code, 401)
        challenge = response['WWW-Authenticate']
        self.assertIn('resource_metadata="http://testserver/.well-known/oauth-protected-resource/mcp"',
                      challenge)
        self.assertIn('scope="bms:read bms:write"', challenge)

    def test_bad_token_is_401_invalid_token(self):
        response = self.client.post('/mcp', '{}', content_type='application/json',
                                    HTTP_AUTHORIZATION='Bearer nope')
        self.assertEqual(response.status_code, 401)
        self.assertIn('error="invalid_token"', response['WWW-Authenticate'])

    def test_get_is_405(self):
        self.assertEqual(self.client.get('/mcp').status_code, 405)


# ---------------------------------------------------------------- registration

class RegistrationTests(TestCase):
    def setUp(self):
        cache.clear()

    def register(self, uris, method='none'):
        return self.client.post('/oauth/register/', json.dumps({
            'client_name': 'Claude', 'redirect_uris': uris,
            'grant_types': ['authorization_code', 'refresh_token'],
            'response_types': ['code'], 'token_endpoint_auth_method': method,
        }), content_type='application/json')

    def test_claude_can_register(self):
        response = self.register([CLAUDE_CALLBACK])
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()
        self.assertTrue(data['client_id'])
        self.assertEqual(data['token_endpoint_auth_method'], 'none')
        self.assertEqual(Application.objects.get(client_id=data['client_id']).client_type, 'public')

    def test_confidential_registration_returns_a_secret(self):
        data = self.register([CLAUDE_CALLBACK], method='client_secret_post').json()
        self.assertTrue(data.get('client_secret'))

    def test_loopback_redirect_is_allowed_for_claude_code(self):
        self.assertEqual(self.register(['http://localhost:54321/callback']).status_code, 201)

    def test_foreign_redirect_is_rejected(self):
        for uri in ('https://evil.example/cb', 'http://claude.ai/api/mcp/auth_callback',
                    'https://claude.ai/somewhere-else'):
            response = self.register([uri])
            self.assertEqual(response.status_code, 400, uri)
            self.assertEqual(response.json()['error'], 'invalid_redirect_uri')
        self.assertEqual(self.register([]).status_code, 400)
        self.assertFalse(Application.objects.exists())

    def test_registration_is_rate_limited(self):
        for _ in range(20):
            self.register([CLAUDE_CALLBACK])
        self.assertEqual(self.register([CLAUDE_CALLBACK]).status_code, 429)


# ---------------------------------------------------------------- full OAuth flow

class OAuthFlowTests(MCPClientMixin, TestCase):
    """Register, consent, exchange the code, then use the token -- what claude.ai does."""

    def setUp(self):
        cache.clear()
        self.owner = make_employee('owner', 'owner', staff=True)
        reg = self.client.post('/oauth/register/', json.dumps({
            'client_name': 'Claude', 'redirect_uris': [CLAUDE_CALLBACK],
            'grant_types': ['authorization_code', 'refresh_token'],
            'response_types': ['code'], 'token_endpoint_auth_method': 'none',
        }), content_type='application/json').json()
        self.client_id = reg['client_id']
        self.verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.verifier.encode()).digest()).rstrip(b'=').decode()
        self.authorize_params = {
            'response_type': 'code', 'client_id': self.client_id, 'redirect_uri': CLAUDE_CALLBACK,
            'scope': 'bms:read bms:write', 'state': 'xyz', 'code_challenge': challenge,
            'code_challenge_method': 'S256', 'resource': RESOURCE,
        }

    def authorize(self, allow=True):
        page = self.client.get('/oauth/authorize/', self.authorize_params)
        self.assertEqual(page.status_code, 200)
        form = {f.name: f.value() for f in page.context['form'] if f.is_hidden}
        form = {k: v for k, v in form.items() if v is not None}
        if allow:
            form['allow'] = 'Authorize'
        return self.client.post('/oauth/authorize/?' + '&'.join(
            f'{k}={v}' for k, v in self.authorize_params.items() if k != 'resource'), form)

    def exchange(self, code):
        return self.client.post('/oauth/token/', {
            'grant_type': 'authorization_code', 'code': code, 'redirect_uri': CLAUDE_CALLBACK,
            'client_id': self.client_id, 'code_verifier': self.verifier, 'resource': RESOURCE,
        })

    def test_anonymous_user_is_sent_to_login_and_back(self):
        response = self.client.get('/oauth/authorize/', self.authorize_params)
        self.assertEqual(response.status_code, 302)
        login_url = response['Location']
        self.assertTrue(login_url.startswith('/login/?next=/oauth/authorize/'))
        back = self.client.post(login_url, {'username': 'owner', 'password': 'pw-123456'})
        self.assertEqual(back.status_code, 302)
        self.assertTrue(back['Location'].startswith('/oauth/authorize/'))

    def test_login_honours_oauth_next_even_for_team_members(self):
        from core.models import TeamMember
        TeamMember.objects.create(user=self.owner, name='Owner', email='o@x.in')
        next_url = '/oauth/authorize/?client_id=' + self.client_id
        back = self.client.post('/login/?next=' + next_url.replace('?', '%3F').replace('=', '%3D'),
                                {'username': 'owner', 'password': 'pw-123456'})
        self.assertEqual(back['Location'], next_url)

    def test_consent_page_shows_what_is_shared(self):
        self.client.force_login(self.owner)
        page = self.client.get('/oauth/authorize/', self.authorize_params)
        self.assertContains(page, 'Allow Claude to use Ralfiz BMS?')
        self.assertContains(page, 'claude.ai')
        self.assertContains(page, 'Make changes you ask for')

    def test_full_flow_then_mcp(self):
        self.client.force_login(self.owner)
        response = self.authorize()
        self.assertEqual(response.status_code, 302)
        callback = urlparse(response['Location'])
        self.assertEqual(f'{callback.scheme}://{callback.netloc}{callback.path}', CLAUDE_CALLBACK)
        query = parse_qs(callback.query)
        self.assertEqual(query['state'], ['xyz'])

        tokens = self.exchange(query['code'][0])
        self.assertEqual(tokens.status_code, 200, tokens.content)
        tokens = tokens.json()
        self.assertEqual(tokens['token_type'], 'Bearer')
        self.assertEqual(tokens['expires_in'], 3600)
        self.assertTrue(tokens['refresh_token'])
        self.assertEqual(AccessToken.objects.get(token=tokens['access_token']).resource, [RESOURCE])

        self.client.logout()  # Claude has no session cookie, only the token
        init = self.rpc('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                                       'clientInfo': {'name': 'claude-ai', 'version': '1'}},
                        token=tokens['access_token'])
        self.assertEqual(init.status_code, 200)
        self.assertEqual(init.json()['result']['protocolVersion'], '2025-06-18')
        self.assertIn('tools', init.json()['result']['capabilities'])

        listed = self.rpc('tools/list', token=tokens['access_token']).json()['result']['tools']
        self.assertEqual({t['name'] for t in listed}, set(TOOLS))

        self.token = AccessToken.objects.get(token=tokens['access_token'])
        self.assertIn('projects', self.ok('get_dashboard'))

    def test_refresh_token_rotates(self):
        self.client.force_login(self.owner)
        code = parse_qs(urlparse(self.authorize()['Location']).query)['code'][0]
        first = self.exchange(code).json()
        refreshed = self.client.post('/oauth/token/', {
            'grant_type': 'refresh_token', 'refresh_token': first['refresh_token'],
            'client_id': self.client_id,
        })
        self.assertEqual(refreshed.status_code, 200, refreshed.content)
        self.assertNotEqual(refreshed.json()['refresh_token'], first['refresh_token'])

    def test_wrong_pkce_verifier_is_rejected(self):
        self.client.force_login(self.owner)
        code = parse_qs(urlparse(self.authorize()['Location']).query)['code'][0]
        self.verifier = 'x' * 50
        self.assertEqual(self.exchange(code).status_code, 400)

    def test_cancel_returns_access_denied(self):
        self.client.force_login(self.owner)
        response = self.authorize(allow=False)
        self.assertIn('error=access_denied', response['Location'])

    def test_intern_cannot_authorize(self):
        intern = make_employee('intern', 'intern')
        self.client.force_login(intern)
        page = self.client.get('/oauth/authorize/', self.authorize_params)
        self.assertEqual(page.status_code, 403)
        self.assertContains(page, 'for owner and partner accounts', status_code=403)
        self.assertFalse(AccessToken.objects.filter(user=intern).exists())

    def test_registration_token_cannot_call_mcp(self):
        # DCR hands back a user-less RFC 7592 management token; it must not open /mcp.
        reg_token = AccessToken.objects.get(user__isnull=True)
        self.assertEqual(self.rpc('tools/list', token=reg_token.token).status_code, 403)

    def test_staff_without_owner_profile_cannot_authorize(self):
        admin = User.objects.create_superuser('admin', 'a@x.in', 'pw-123456')
        self.client.force_login(admin)
        page = self.client.get('/oauth/authorize/', self.authorize_params)
        self.assertEqual(page.status_code, 403)
        self.assertContains(page, 'no owner or partner profile', status_code=403)

    def test_token_for_other_resource_is_rejected(self):
        token = make_token(self.owner, resource=['https://other.example/mcp'])
        self.assertEqual(self.rpc('tools/list', token=token.token).status_code, 401)

    def test_expired_token_is_rejected(self):
        token = make_token(self.owner)
        token.expires = timezone.now() - timedelta(seconds=1)
        token.save()
        self.assertEqual(self.rpc('tools/list', token=token.token).status_code, 401)


# ---------------------------------------------------------------- endpoint behaviour

class MCPEndpointTests(MCPClientMixin, TestCase):
    def setUp(self):
        self.owner = make_employee('owner', 'owner', staff=True)
        self.token = make_token(self.owner)

    def test_notification_is_accepted_without_body(self):
        body = json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        response = self.client.post('/mcp', body, content_type='application/json',
                                    HTTP_AUTHORIZATION=f'Bearer {self.token.token}')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.content, b'')

    def test_trailing_slash_works(self):
        body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'ping'})
        response = self.client.post('/mcp/', body, content_type='application/json',
                                    HTTP_AUTHORIZATION=f'Bearer {self.token.token}')
        self.assertEqual(response.json(), {'jsonrpc': '2.0', 'id': 1, 'result': {}})

    def test_unknown_protocol_version_gets_latest(self):
        result = self.rpc('initialize', {'protocolVersion': '1999-01-01'}, token=self.token.token)
        self.assertEqual(result.json()['result']['protocolVersion'], '2025-11-25')

    def test_unknown_method_and_tool(self):
        self.assertEqual(self.rpc('resources/list', token=self.token.token).json()['error']['code'], -32601)
        response = self.rpc('tools/call', {'name': 'drop_tables'}, token=self.token.token)
        self.assertEqual(response.json()['error']['code'], -32602)

    def test_malformed_body(self):
        response = self.client.post('/mcp', 'not json', content_type='application/json',
                                    HTTP_AUTHORIZATION=f'Bearer {self.token.token}')
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/mcp', '[]', content_type='application/json',
                                    HTTP_AUTHORIZATION=f'Bearer {self.token.token}')
        self.assertEqual(response.status_code, 400)

    def test_foreign_browser_origin_is_refused(self):
        response = self.rpc('ping', token=self.token.token, HTTP_ORIGIN='https://evil.example')
        self.assertEqual(response.status_code, 403)
        response = self.rpc('ping', token=self.token.token, HTTP_ORIGIN='https://claude.ai')
        self.assertEqual(response.status_code, 200)

    def test_demoted_user_loses_access_with_a_live_token(self):
        Employee.objects.filter(user=self.owner).update(role='employee')
        self.owner.is_staff = False
        self.owner.save()
        self.assertEqual(self.rpc('tools/list', token=self.token.token).status_code, 403)

    def test_read_only_token_cannot_write(self):
        read_only = make_token(self.owner, scope='bms:read')
        is_error, message = self.call('create_lead', {'contact_person': 'Asha'}, token=read_only.token)
        self.assertTrue(is_error)
        self.assertIn('reading only', message)
        self.assertFalse(Lead.objects.exists())
        self.ok('list_leads', token=read_only.token)

    def test_calls_are_logged(self):
        self.ok('get_dashboard')
        self.call('get_project', {'project_id': 'not-a-uuid'})
        logs = list(ConnectorCallLog.objects.order_by('created_at'))
        self.assertEqual([(l.tool, l.ok) for l in logs], [('get_dashboard', True), ('get_project', False)])
        self.assertEqual(logs[0].user, self.owner)
        self.assertEqual(logs[0].client_name, 'Claude')

    def test_argument_validation_messages(self):
        cases = [
            ('get_project', {'project_id': 'abc'}, 'must be a UUID'),
            ('get_attendance', {'start_date': '07/10/2026'}, 'YYYY-MM-DD'),
            ('list_projects', {'status': 'blocked'}, 'must be one of'),
            ('get_lead', {}, 'Missing required argument(s): lead_id'),
            ('list_leads', {'colour': 'red'}, 'Unknown argument(s): colour'),
            ('get_lead', {'lead_id': 'seven'}, 'must be an integer'),
        ]
        for name, args, expected in cases:
            is_error, message = self.call(name, args)
            self.assertTrue(is_error, name)
            self.assertIn(expected, message, name)

    def test_view_errors_reach_claude(self):
        is_error, message = self.call('get_lead', {'lead_id': 999999})
        self.assertTrue(is_error)
        self.assertIn('404', message)


# ---------------------------------------------------------------- tools

class ToolCatalogueTests(TestCase):
    def test_every_wrapped_endpoint_exists(self):
        """Catches a renamed URL in employees/urls.py before Claude does."""
        for tool in TOOLS.values():
            if not tool.endpoint:
                continue
            _, url_name = tool.endpoint
            try:
                reverse(url_name)
            except NoReverseMatch:
                # Detail routes need kwargs; resolving with dummy ones proves the name exists.
                for kwargs in ({'pk': 1}, {'pk': '00000000-0000-0000-0000-000000000000'},
                               {'lead_id': 1}, {'follow_up_id': 1}):
                    try:
                        reverse(url_name, kwargs=kwargs)
                        break
                    except NoReverseMatch:
                        continue
                else:
                    self.fail(f'{tool.name}: no URL named {url_name}')

    def test_definitions_are_well_formed(self):
        for tool in TOOLS.values():
            d = tool.definition()
            self.assertRegex(d['name'], r'^[a-z_]{3,64}$')
            self.assertGreater(len(d['description']), 30, tool.name)
            for req in d['inputSchema']['required']:
                self.assertIn(req, d['inputSchema']['properties'], tool.name)
            self.assertEqual(d['annotations']['readOnlyHint'], not tool.write)

    def test_nothing_deletes(self):
        for tool in TOOLS.values():
            self.assertNotEqual(tool.endpoint[:1], ('delete',), tool.name)
            self.assertFalse(tool.destructive, tool.name)


class ToolBehaviourTests(MCPClientMixin, TestCase):
    def setUp(self):
        self.owner = make_employee('owner', 'owner', staff=True)
        self.token = make_token(self.owner)
        self.client_rec = Client.objects.create(name='Ajith Kumar', company_name='Ajith Traders',
                                                email='ajith@example.com', phone='9846000001')
        self.project = Project.objects.create(client=self.client_rec, name='Patient Portal',
                                              project_type='web_app', status='in_progress')
        self.intern = make_employee('meera', 'intern')

    def test_every_read_tool_runs_without_arguments(self):
        for tool in TOOLS.values():
            if tool.write or tool.required:
                continue
            is_error, data = self.call(tool.name)
            self.assertFalse(is_error, f'{tool.name}: {data}')

    def test_search_finds_records_by_name(self):
        data = self.ok('search', {'query': 'ajith'})
        self.assertEqual(data['clients'][0]['id'], str(self.client_rec.id))
        self.assertEqual(data['projects'][0]['name'], 'Patient Portal')
        data = self.ok('search', {'query': 'meera', 'types': ['employees']})
        self.assertEqual(list(data), ['employees'])
        self.assertEqual(data['employees'][0]['employee_id'], 'EMP-MEERA')

    def test_project_detail_never_includes_secrets(self):
        Credential.objects.create(project=self.project, credential_type='hosting', name='VPS',
                                  username='root', password='hunter2', ssh_key='-----BEGIN KEY')
        data = self.ok('get_project', {'project_id': str(self.project.id)})
        text = json.dumps(data)
        self.assertNotIn('hunter2', text)
        self.assertNotIn('BEGIN KEY', text)
        self.assertIn('[hidden]', text)
        self.assertIn('root', text)  # usernames are fine

    def test_update_project_status(self):
        self.ok('update_project_status', {'project_id': str(self.project.id), 'status': 'completed'})
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'completed')
        self.assertIsNotNone(self.project.completed_date)

    def test_lead_lifecycle(self):
        lead = self.ok('create_lead', {'contact_person': 'Asha', 'company_name': 'Asha Bakes',
                                       'phone': '9000000001', 'source': 'instagram'})
        lead_id = lead['id']
        is_error, message = self.call('create_lead', {'contact_person': 'Asha again', 'phone': '9000000001'})
        self.assertTrue(is_error)
        self.assertIn('already exists', message)
        self.ok('create_lead', {'contact_person': 'Asha again', 'phone': '9000000001',
                                'allow_duplicate': True})

        self.ok('add_lead_note', {'lead_id': lead_id, 'note': 'Wants a website by Diwali'})
        follow_up = self.ok('schedule_followup', {'lead_id': lead_id, 'follow_up_type': 'call',
                                                  'scheduled_date': '2030-01-05T11:00'})
        self.ok('update_followup', {'follow_up_id': follow_up['id'], 'status': 'completed',
                                    'outcome': 'Sent quote'})
        self.ok('update_lead_status', {'lead_id': lead_id, 'status': 'proposal_sent'})

        detail = self.ok('get_lead', {'lead_id': lead_id})
        self.assertEqual(detail['status'], 'proposal_sent')
        self.assertEqual(detail['notes_list'][0]['note'], 'Wants a website by Diwali')
        timeline = json.dumps(self.ok('get_lead_timeline', {'lead_id': lead_id}))
        self.assertIn('Sent quote', timeline)

        listed = self.ok('list_leads', {'status': 'proposal_sent'})
        self.assertEqual(listed['count'], 1)
        self.assertNotIn('notes_list', listed['items'][0])  # list view is compact

    def test_list_limit_is_reported(self):
        for i in range(5):
            Lead.objects.create(contact_person=f'L{i}', phone=f'90000000{i}', created_by=self.owner)
        data = self.ok('list_leads', {'limit': 2})
        self.assertEqual((data['count'], data['returned'], data['truncated']), (5, 2, True))

    def test_leave_review_and_work_assignment(self):
        leave_type = LeaveType.objects.create(name='Casual', days_allowed=12)
        leave = LeaveRequest.objects.create(
            employee=Employee.objects.get(user=self.intern), leave_type=leave_type,
            start_date=date(2030, 1, 6), end_date=date(2030, 1, 7), reason='Wedding')
        pending = self.ok('list_pending_leave_requests')
        self.assertEqual(pending['items'][0]['id'], str(leave.id))
        self.ok('review_leave_request', {'leave_request_id': str(leave.id), 'action': 'approve',
                                         'notes': 'Enjoy'})
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'approved')

        intern_id = str(Employee.objects.get(user=self.intern).id)
        self.ok('assign_work', {'employee_ids': [intern_id], 'title': 'Landing page copy',
                                'due_date': '2030-01-10', 'priority': 'high'})
        work = self.ok('list_work_assignments', {'employee_id': intern_id})
        self.assertEqual(work['items'][0]['title'], 'Landing page copy')
        self.assertEqual(WorkAssignment.objects.get().assigned_by, self.owner)

    def test_daily_tasks(self):
        task = self.ok('add_daily_task', {'title': 'Call GST consultant', 'priority': 'high',
                                          'project_id': str(self.project.id)})
        self.ok('update_daily_task', {'task_id': task['id'], 'status': 'done'})
        day = self.ok('list_daily_tasks')
        self.assertEqual(day['counts']['done'], 1)

    def test_admin_tools_need_staff(self):
        partner = make_employee('partner', 'partner')  # owner-role but not is_staff
        token = make_token(partner)
        self.assertFalse(self.call('get_dashboard', token=token.token)[0])
        is_error, message = self.call('list_pending_leave_requests', token=token.token)
        self.assertTrue(is_error)
        self.assertIn('403', message)
