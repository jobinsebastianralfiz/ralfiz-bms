"""Project-board tasks show up for the staff member they are assigned to.

Board tasks point at a core.TeamMember; staff logins are Employees. The two
are matched by email, then exact name, without linking the login (which would
let it out of the staff portal)."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Client, Project, Task, TeamMember
from employees.models import Employee
from employees.portal_views import board_member_for


class StaffBoardTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('sana', password='pw-123456', first_name='Sana',
                                             last_name='Parvin M', email='Sana@Example.com')
        self.employee = Employee.objects.create(user=self.user, employee_id='EMP006',
                                                employment_type='fulltime', role='employee', status='active')
        self.member = TeamMember.objects.create(name='Sana Parvin M', role='growth_outreach')
        biz = Client.objects.create(name='AGC', email='agc@example.com')
        self.project = Project.objects.create(client=biz, name='AGC Website', status='confirmed')
        self.task = Task.objects.create(project=self.project, title='Write the homepage copy',
                                        assigned_to=self.member, category='Content', status='todo')
        Task.objects.create(project=self.project, title='Someone else', status='todo')
        self.client.force_login(self.user)

    def test_matched_by_exact_name(self):
        self.assertEqual(board_member_for(self.employee), self.member)

    def test_email_match_wins_and_two_same_names_do_not_guess(self):
        other = TeamMember.objects.create(name='Sana Parvin M', role='designer')
        self.assertIsNone(board_member_for(self.employee))   # two with the same name: no guess
        other.email = 'sana@example.com'
        other.save()
        self.assertEqual(board_member_for(self.employee), other)

    def test_dashboard_and_work_list_show_the_task(self):
        r = self.client.get(reverse('staff:dashboard'))
        self.assertContains(r, 'Write the homepage copy')
        self.assertNotContains(r, 'Someone else')
        self.assertEqual(r.context['open_task_total'], 1)
        r = self.client.get(reverse('staff:work_list'))
        self.assertContains(r, 'Write the homepage copy')

    def test_can_move_own_task_but_not_others(self):
        self.client.post(reverse('staff:board_task_update', args=[self.task.pk]),
                         {'status': 'in_progress', 'progress': '40'})
        self.task.refresh_from_db()
        self.assertEqual((self.task.status, self.task.progress), ('in_progress', 40))
        other = Task.objects.get(title='Someone else')
        r = self.client.post(reverse('staff:board_task_update', args=[other.pk]), {'status': 'completed'})
        self.assertEqual(r.status_code, 404)

    def test_back_link_cannot_leave_the_site(self):
        r = self.client.post(reverse('staff:board_task_update', args=[self.task.pk]),
                             {'status': 'review', 'back': 'https://evil.example/'})
        self.assertEqual(r['Location'], reverse('staff:work_list'))

    def test_login_stays_confined(self):
        self.assertIsNone(TeamMember.objects.get(pk=self.member.pk).user)
        r = self.client.get('/invoices/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/staff/', r['Location'])
