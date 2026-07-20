"""Tests for the command centre page itself."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Client, Project, Task, TaskIssue, TeamMember
from employees.models import Employee


class CommandCenterPageTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.owner = User.objects.create_user(username='owner', password='pw')
        Employee.objects.create(
            user=self.owner, employee_id='EMP-O', role='owner',
            status='active', joining_date=today,
        )
        self.worker = User.objects.create_user(username='worker', password='pw')
        Employee.objects.create(
            user=self.worker, employee_id='EMP-W', role='employee',
            status='active', joining_date=today,
        )

        self.client_obj = Client.objects.create(name='Northwind')
        self.project = Project.objects.create(
            client=self.client_obj, name='iRAD 2027',
            project_type='web_app', status='in_progress',
        )
        member = TeamMember.objects.create(name='Asha', role='developer')
        self.project.team_members.add(member)

        task = Task.objects.create(
            project=self.project, title='Ship auth', status='in_progress'
        )
        Task.objects.create(project=self.project, title='Done', status='completed')
        TaskIssue.objects.create(
            task=task, title='API down', description='blocked',
            severity='critical', status='open',
        )

        self.url = reverse('pulse:command-center')

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_non_owner_is_redirected_away(self):
        self.client.force_login(self.worker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_owner_gets_the_page(self):
        """Renders the real template -- catches template syntax errors."""
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pulse/command_center.html')

    def test_page_ships_bootstrap_data_for_first_paint(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        body = response.content.decode()
        self.assertIn('pulse-bootstrap', body)
        self.assertIn('iRAD 2027', body)

    def test_bootstrap_json_carries_real_counts(self):
        import json
        import re

        self.client.force_login(self.owner)
        body = self.client.get(self.url).content.decode()
        raw = re.search(
            r'id="pulse-bootstrap" type="application/json">(.*?)</script>',
            body, re.S,
        ).group(1)
        data = json.loads(raw)

        self.assertEqual(data['name'], 'iRAD 2027')
        self.assertEqual(data['client'], 'Northwind')
        self.assertEqual(data['tasks']['total'], 2)
        self.assertEqual(data['tasks']['open'], 1)
        self.assertEqual(data['issues']['open'], 1)
        self.assertEqual(data['issues']['critical'], 1)
        self.assertEqual(len(data['team']), 1)

    def test_explicit_project_query_param_is_honoured(self):
        other = Project.objects.create(
            client=self.client_obj, name='Second Project',
            project_type='api', status='confirmed',
        )
        self.client.force_login(self.owner)
        response = self.client.get(self.url, {'project': str(other.id)})
        self.assertIn('Second Project', response.content.decode())

    def test_assets_are_referenced_not_inlined(self):
        """The design spec requires self-contained pulse.css / pulse.js."""
        self.client.force_login(self.owner)
        body = self.client.get(self.url).content.decode()
        self.assertIn('css/pulse.css', body)
        self.assertIn('js/pulse.js', body)
        self.assertNotIn('css/styles.css', body)
        self.assertNotIn('js/app.js', body)


class DashboardRoutingTests(TestCase):
    """The constellation is mounted at '/'; the classic dashboard moved.

    The loop risk is specific: GraphDashboardView refuses non-owners, and if
    it refused them *to '/'* that would be an infinite redirect now that '/'
    is the constellation.
    """

    def setUp(self):
        today = timezone.localdate()
        self.owner = User.objects.create_user(username='o', password='pw')
        Employee.objects.create(
            user=self.owner, employee_id='E-O', role='owner',
            status='active', joining_date=today,
        )
        self.worker = User.objects.create_user(username='w', password='pw')
        Employee.objects.create(
            user=self.worker, employee_id='E-W', role='employee',
            status='active', joining_date=today,
        )

    def test_root_is_the_constellation_for_owners(self):
        self.client.force_login(self.owner)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pulse/graph_dashboard.html')

    def test_non_owner_at_root_does_not_loop(self):
        self.client.force_login(self.worker)
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        # One hop to the legacy dashboard, and it must not bounce again.
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][0], '/dashboard/legacy/')

    def test_legacy_dashboard_still_serves_the_original_view(self):
        self.client.force_login(self.worker)
        response = self.client.get(reverse('dashboard-legacy'))
        self.assertEqual(response.status_code, 200)

    def test_login_redirect_target_still_resolves(self):
        """LOGIN_REDIRECT_URL points at the 'dashboard' name."""
        from django.conf import settings
        self.assertEqual(reverse(settings.LOGIN_REDIRECT_URL), '/')

    def test_command_center_non_owner_does_not_loop(self):
        self.client.force_login(self.worker)
        response = self.client.get(reverse('pulse:command-center'), follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][0], '/dashboard/legacy/')
