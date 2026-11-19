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

    def test_board_tasks_are_kept_out_of_my_tasks(self):
        r = self.client.get(reverse('staff:work_list'))
        self.assertNotContains(r, 'Write the homepage copy')
        self.assertEqual(r.context['counts']['total'], 0)
        r = self.client.get(reverse('staff:dashboard'))
        self.assertEqual(r.context['open_task_total'], 0)          # My Tasks count: own work only
        self.assertEqual([t['title'] for t in r.context['tasks']], [])
        # ...the project shows in its own Home section instead.
        self.assertEqual([c['project'] for c in r.context['my_projects']], [self.project])
        self.assertContains(r, 'My projects')

    def test_projects_page_and_board(self):
        r = self.client.get(reverse('staff:project_list'))
        self.assertContains(r, 'AGC Website')
        self.assertContains(r, reverse('staff:project_list'))     # sidebar entry
        card = r.context['cards'][0]
        self.assertEqual((card['open'], card['mine_open'], card['done']), (2, 1, 0))
        r = self.client.get(reverse('staff:project_board', args=[self.project.pk]))
        cols = {c['key']: [t.title for t in c['tasks']] for c in r.context['columns']}
        self.assertEqual(sorted(cols['todo']), ['Someone else', 'Write the homepage copy'])
        mine = self.client.get(reverse('staff:project_board', args=[self.project.pk]), {'mine': '1'})
        self.assertEqual([t.title for c in mine.context['columns'] for t in c['tasks']],
                         ['Write the homepage copy'])

    def test_board_is_only_for_the_projects_team(self):
        other = Project.objects.create(client=self.project.client, name='Secret', status='in_progress')
        Task.objects.create(project=other, title='Hidden', status='todo')
        self.assertEqual(self.client.get(reverse('staff:project_board', args=[other.pk])).status_code, 404)
        hidden = Task.objects.get(title='Hidden')
        self.assertEqual(self.client.get(reverse('staff:board_task_detail', args=[hidden.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('staff:project_list')), 'Secret')
        # Being put on the team opens the board, even with no task of your own.
        other.team_members.add(self.member)
        self.assertEqual(self.client.get(reverse('staff:project_board', args=[other.pk])).status_code, 200)

    def test_a_finished_task_alone_does_not_list_the_project(self):
        old_project = Project.objects.create(client=self.project.client, name='Lecule Pharma',
                                             status='in_progress')
        done = Task.objects.create(project=old_project, title='Old copy', status='completed',
                                   assigned_to=self.member)
        names = [c['project'].name for c in self.client.get(reverse('staff:project_list')).context['cards']]
        self.assertNotIn('Lecule Pharma', names)
        self.assertEqual(self.client.get(reverse('staff:project_board', args=[old_project.pk])).status_code, 404)
        # Reopened work brings it back; so does being put on the team.
        done.status = 'todo'
        done.save()
        names = [c['project'].name for c in self.client.get(reverse('staff:project_list')).context['cards']]
        self.assertIn('Lecule Pharma', names)

    def test_teammates_task_opens_read_only(self):
        other = Task.objects.get(title='Someone else')
        r = self.client.get(reverse('staff:board_task_detail', args=[other.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context['is_mine'])
        self.assertNotContains(r, reverse('staff:board_task_update', args=[other.pk]))
        r = self.client.get(reverse('staff:board_task_detail', args=[self.task.pk]))
        self.assertTrue(r.context['is_mine'])
        self.assertContains(r, reverse('staff:board_task_update', args=[self.task.pk]))

    def test_no_projects_no_sidebar_entry(self):
        self.task.delete()
        r = self.client.get(reverse('staff:dashboard'))
        self.assertFalse(r.context['has_projects'])
        self.assertNotContains(r, reverse('staff:project_list'))

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
        self.assertEqual(r['Location'], reverse('staff:project_board', args=[self.project.pk]))

    def test_login_stays_confined(self):
        self.assertIsNone(TeamMember.objects.get(pk=self.member.pk).user)
        r = self.client.get('/invoices/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/staff/', r['Location'])


class StaffTaskPageTests(StaffBoardTaskTests):
    def test_task_page_shows_files_and_takes_comments(self):
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from core.models import TaskAttachment
        with override_settings(MEDIA_ROOT=tempfile.mkdtemp()):
            TaskAttachment.objects.create(task=self.task, name='brief.pdf',
                                          file=SimpleUploadedFile('brief.pdf', b'%PDF-1.4'))
            r = self.client.get(reverse('staff:board_task_detail', args=[self.task.pk]))
            self.assertContains(r, 'brief.pdf')
            self.client.post(reverse('staff:board_task_detail', args=[self.task.pk]), {'body': 'Which font?'})
            self.assertTrue(self.task.comments.filter(body='Which font?', author=self.user).exists())
            r = self.client.get(reverse('staff:project_board', args=[self.project.pk]))
            self.assertContains(r, '<i class="fas fa-paperclip"></i> 1')

    def test_cannot_open_a_task_on_another_projects_board(self):
        elsewhere = Project.objects.create(client=self.project.client, name='Elsewhere', status='in_progress')
        other = Task.objects.create(project=elsewhere, title='Not mine', status='todo')
        self.assertEqual(self.client.get(reverse('staff:board_task_detail', args=[other.pk])).status_code, 404)


class StaffPagesTests(StaffBoardTaskTests):
    def test_search_only_finds_own_things(self):
        r = self.client.get(reverse('staff:search'), {'q': 'homepage'})
        self.assertContains(r, 'Write the homepage copy')
        r = self.client.get(reverse('staff:search'), {'q': 'someone'})
        self.assertNotContains(r, 'Someone else')

    def test_work_counts_and_pages_render(self):
        r = self.client.get(reverse('staff:work_list'))
        self.assertEqual(r.context['counts']['total'], 0)    # board tasks are under Projects
        self.assertEqual(r.context['work_total'], 0)
        for name in ['staff:dashboard', 'staff:attendance', 'staff:leave', 'staff:daily_report',
                     'staff:payslip_list', 'staff:notification_list', 'staff:attendance_history']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)


class StaffLeaveDailyHistoryTests(StaffBoardTaskTests):
    def test_leave_filters_by_status_and_year(self):
        from datetime import date
        from employees.models import LeaveRequest, LeaveType
        lt, _ = LeaveType.objects.get_or_create(name='Sick Leave', defaults={'days_allowed': 10})
        y = date.today().year
        LeaveRequest.objects.create(employee=self.employee, leave_type=lt, start_date=date(y, 1, 5),
                                    end_date=date(y, 1, 5), reason='flu', status='approved')
        LeaveRequest.objects.create(employee=self.employee, leave_type=lt, start_date=date(y - 1, 3, 1),
                                    end_date=date(y - 1, 3, 1), reason='old', status='approved')
        r = self.client.get(reverse('staff:leave'), {'status': 'approved'})
        self.assertEqual(r.context['status_counts']['all'], 1)
        self.assertContains(r, 'flu')
        self.assertNotContains(r, '>old<')
        r = self.client.get(reverse('staff:leave'), {'year': y - 1})
        self.assertContains(r, 'old')

    def test_daily_updates_ranges(self):
        from datetime import date, timedelta
        from employees.models import DailyReport
        today = date.today()
        DailyReport.objects.create(employee=self.employee, date=today, work_done='Homepage copy\nmore detail')
        r = self.client.get(reverse('staff:daily_report'), {'range': 'last7'})
        self.assertEqual(r.context['range_counts']['last7'], 1)
        self.assertContains(r, 'Homepage copy')
        r = self.client.get(reverse('staff:daily_report'), {'month': 'nonsense'})
        self.assertEqual(r.status_code, 200)

    def test_long_daily_update_is_not_cut_off(self):
        from employees.portal_views import _split_headline
        text = ('Built the login screen for the Flutter app and wired the API client. '
                'Fixed two layout bugs on the profile page that showed up on small phones.')
        head, rest = _split_headline(text)
        self.assertEqual(head, 'Built the login screen for the Flutter app and wired the API client.')
        self.assertIn('showed up on small phones.', rest)
        head, rest = _split_headline('word ' * 60)
        self.assertTrue(head.endswith('…') and len(head) <= 121)
        self.assertEqual((head[:-1] + ' ' + rest[1:]).split(), ['word'] * 60)
        self.assertEqual(_split_headline('Short\nsecond line'), ('Short', 'second line'))

    def test_history_hours_and_trend(self):
        from datetime import datetime, time
        from django.utils import timezone
        from employees.models import Attendance
        today = timezone.localdate()
        start = timezone.make_aware(datetime.combine(today, time(9, 0)))
        Attendance.objects.create(employee=self.employee, date=today, check_in=start,
                                  check_out=start + timezone.timedelta(hours=6), status='present')
        r = self.client.get(reverse('staff:attendance_history'))
        self.assertEqual(r.context['total_hours'], 6.0)
        self.assertEqual(next(d for d in r.context['trend'] if d['day'] == today.day)['hours'], 6.0)


class StaffNotificationPageTests(StaffBoardTaskTests):
    def test_groups_filters_and_leave_details(self):
        from datetime import timedelta
        from django.utils import timezone
        from employees.models import Notification
        mk = Notification.objects.create
        mk(employee=self.employee, title='Leave Approved', notification_type='leave',
           body='Your leave from 2026-10-13 to 2026-10-14 has been approved.')
        old = mk(employee=self.employee, title='Leave Rejected', notification_type='leave',
                 body='Your leave from 2026-01-05 to 2026-01-05 has been rejected.', is_read=True)
        Notification.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=60))
        mk(employee=self.employee, title='Daily update reply', body='HR replied', notification_type='general')
        mk(employee=None, title='Office closed Monday', body='Holiday', notification_type='announcement')

        r = self.client.get(reverse('staff:notification_list'))
        counts = {key: n for key, _, n in r.context['filters']}
        self.assertEqual(counts, {'': 4, 'leave': 2, 'attendance': 0, 'work': 0, 'announcement': 1, 'other': 1})
        groups = dict(r.context['groups'])
        self.assertEqual(len(groups['Today']), 3)
        self.assertEqual([n.title for n in groups['Earlier']], ['Leave Rejected'])
        approved = next(n for n in groups['Today'] if n.title == 'Leave Approved')
        self.assertEqual((approved.status, approved.days, str(approved.on_date)), ('approved', 2, '2026-10-13'))
        broadcast = next(n for n in groups['Today'] if n.employee_id is None)
        self.assertFalse(broadcast.can_mark_read)

        r = self.client.get(reverse('staff:notification_list'), {'type': 'other'})
        self.assertEqual([n.title for _, items in r.context['groups'] for n in items], ['Daily update reply'])
        r = self.client.get(reverse('staff:notification_list'), {'type': 'bogus'})
        self.assertEqual(r.context['kind'], '')


class StaffProfilePageTests(StaffBoardTaskTests):
    def test_profile_page_and_self_edit(self):
        r = self.client.get(reverse('staff:profile'))
        self.assertContains(r, 'Personal Information')
        self.assertContains(r, 'id="pfInstall"')
        self.assertContains(r, 'Missing')  # no face photo yet

        r = self.client.patch('/api/employees/profile/', {'phone': '9000011111', 'address': 'Kochi',
                                                          'employee_id': 'HACK'},
                              content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.employee.refresh_from_db()
        self.assertEqual((self.employee.phone, self.employee.address, self.employee.employee_id),
                         ('9000011111', 'Kochi', 'EMP006'))
        self.assertContains(self.client.get(reverse('staff:profile')), 'Kochi')
