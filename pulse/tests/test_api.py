"""Tests for POST /api/pulse/ask/.

The model call is stubbed throughout -- these assert the auth boundary and the
response contract, not the model's judgement.
"""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from employees.models import Employee
from pulse.supervisor import PulseConfigurationError


class AskEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('pulse:ask')
        today = timezone.localdate()

        self.owner = User.objects.create_user(username='owner', password='pw')
        Employee.objects.create(
            user=self.owner, employee_id='EMP-OWNER', role='owner',
            status='active', joining_date=today,
        )
        self.staffer = User.objects.create_user(username='staffer', password='pw')
        Employee.objects.create(
            user=self.staffer, employee_id='EMP-STAFF', role='employee',
            status='active', joining_date=today,
        )

    # -- auth boundary --------------------------------------------------

    def test_anonymous_is_rejected(self):
        """settings has no DEFAULT_PERMISSION_CLASSES, so this guards against
        a future edit dropping permission_classes from the view."""
        response = self.client.post(self.url, {'query': 'how many projects'}, format='json')
        self.assertIn(response.status_code, (401, 403))

    def test_get_is_not_allowed(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    @patch('pulse.views.ask')
    def test_owner_is_allowed(self, mock_ask):
        mock_ask.return_value = {'answer': 'Five.', 'intent': 'count_projects_by_status', 'data': {}}
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.url, {'query': 'how many projects'}, format='json')
        self.assertEqual(response.status_code, 200)

    @patch('pulse.views.ask')
    def test_non_owner_employee_is_refused_before_the_model_is_called(self, mock_ask):
        """Authorisation must not depend on the model choosing to call a tool."""
        self.client.force_authenticate(user=self.staffer)
        response = self.client.post(
            self.url, {'query': 'what is our outstanding revenue'}, format='json'
        )
        self.assertEqual(response.status_code, 403)
        mock_ask.assert_not_called()

    # -- request validation ---------------------------------------------

    def test_empty_query_is_rejected(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.url, {'query': '   '}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_missing_query_is_rejected(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.post(self.url, {}, format='json').status_code, 400)

    # -- response contract ----------------------------------------------

    @patch('pulse.views.ask')
    def test_response_shape(self, mock_ask):
        mock_ask.return_value = {
            'answer': 'Two projects need attention.',
            'intent': 'get_projects_needing_attention',
            'data': {'count': 2, 'projects': []},
        }
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.url, {'query': 'what is stuck'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json().keys()), {'answer', 'intent', 'data'}
        )
        self.assertEqual(response.json()['intent'], 'get_projects_needing_attention')
        self.assertEqual(response.json()['data']['count'], 2)

    @patch('pulse.views.ask')
    def test_query_is_forwarded_to_supervisor(self, mock_ask):
        mock_ask.return_value = {'answer': '', 'intent': None, 'data': None}
        self.client.force_authenticate(user=self.owner)
        self.client.post(self.url, {'query': 'who is late'}, format='json')
        self.assertEqual(mock_ask.call_args.args[0], 'who is late')

    # -- failure modes ---------------------------------------------------

    @patch('pulse.views.ask')
    def test_missing_api_key_returns_503_not_500(self, mock_ask):
        mock_ask.side_effect = PulseConfigurationError('ANTHROPIC_API_KEY is not set.')
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.url, {'query': 'anything'}, format='json')
        self.assertEqual(response.status_code, 503)

    @patch('pulse.views.ask')
    def test_bad_tool_argument_returns_400_not_500(self, mock_ask):
        mock_ask.side_effect = ValueError('project_id must be a valid UUID')
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.url, {'query': 'summarise project foo'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('Traceback', str(response.content))


class SupervisorWiringTests(TestCase):
    """Guards on the model-facing surface that do not need an API call."""

    def test_every_registered_tool_is_exposed_to_the_model(self):
        from pulse.supervisor import TOOL_SPECS
        from pulse.tools import TOOL_REGISTRY
        self.assertEqual(set(TOOL_SPECS), set(TOOL_REGISTRY))

    def test_missing_api_key_raises_configuration_error(self):
        from pulse.supervisor import _build_model
        with self.settings(ANTHROPIC_API_KEY=''):
            with self.assertRaises(PulseConfigurationError):
                _build_model()

    def test_tools_bind_to_scope_and_carry_descriptions(self):
        from pulse.scoping import PulseScope
        from pulse.supervisor import build_tools

        scope = PulseScope(user=None, employee=None, can_query_business=True)
        built = build_tools(scope)
        # Derived, not hardcoded: adding a tool should not fail this test.
        from pulse.tools import TOOL_REGISTRY
        self.assertEqual(len(built), len(TOOL_REGISTRY))
        for tool in built:
            with self.subTest(tool=tool.name):
                self.assertTrue(tool.description.startswith('Call '))

    def test_bound_tools_survive_langgraph_type_inspection(self):
        """Regression: scope binding must not be a functools.partial.

        LangGraph's ToolNode runs typing.get_type_hints() over each tool's
        callable while building the graph. get_type_hints() raises TypeError
        on partial objects, so the graph failed to build before any model call
        -- invisible to every mocked test. Needs no API key.
        """
        import typing

        from langgraph.prebuilt import ToolNode

        from pulse.scoping import PulseScope
        from pulse.supervisor import build_tools

        scope = PulseScope(user=None, employee=None, can_query_business=True)
        built = build_tools(scope)

        for tool in built:
            with self.subTest(tool=tool.name):
                typing.get_type_hints(tool.func, include_extras=True)

        ToolNode(built)  # raised TypeError before the fix

    def test_bound_tools_actually_reach_the_query_functions(self):
        """The closure must forward both the scope and the model's arguments."""
        from pulse.scoping import PulseScope
        from pulse.supervisor import build_tools

        scope = PulseScope(user=None, employee=None, can_query_business=True)
        by_name = {t.name: t for t in build_tools(scope)}

        no_args = by_name['count_projects_by_status'].func()
        self.assertIn('breakdown', no_args)

        with_args = by_name['get_project_summary'].func(
            project_id='00000000-0000-0000-0000-000000000000'
        )
        self.assertFalse(with_args['found'])
