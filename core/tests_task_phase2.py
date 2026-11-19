"""Phase 2: issue types + bug reporting, blocked-by links, epics, stuck flag."""
from datetime import date, datetime, timedelta
from unittest import mock

from django.urls import reverse
from django.utils import timezone

from core import task_rules
from core.models import Task, TaskLink
from core.tests_task_backlog import BoardSetup
from employees.models import Notification


class LinkTests(BoardSetup):
    def setUp(self):
        super().setUp()
        self.a = task_rules.create_task(self.project, self.admin, title='Section registry', status='todo',
                                        assigned_to=self.lead)
        self.b = task_rules.create_task(self.project, self.admin, title='Hero section', status='todo',
                                        assigned_to=self.dev)
        task_rules.link_tasks(self.a, self.b, 'blocks', self.admin)

    def test_member_cannot_start_blocked_card_lead_can_with_warning(self):
        with self.assertRaisesMessage(task_rules.TaskRuleError, f'Blocked by {self.a.code} · Section registry, To Do'):
            task_rules.change_status(self.b, 'in_progress', self.dev_user, member=self.dev)
        task_rules.change_status(self.b, 'in_progress', self.lead_user, member=self.lead)
        self.assertIn('started anyway', self.b.override_warning)

    def test_completing_blocker_notifies_owner_once(self):
        task_rules.change_status(self.a, 'completed', self.lead_user, member=self.lead)
        n = Notification.objects.filter(employee=self.dev_emp)
        self.assertEqual(n.count(), 1)
        self.assertIn(f'{self.b.code} is unblocked', n.first().title)
        self.b.refresh_from_db()
        self.assertFalse(self.b.is_blocked)

    def test_no_loops_no_self_no_other_project(self):
        c = task_rules.create_task(self.project, self.admin, title='C', status='todo')
        task_rules.link_tasks(self.b, c, 'blocks', self.admin)
        with self.assertRaisesMessage(task_rules.TaskRuleError, 'loop'):
            task_rules.link_tasks(c, self.a, 'blocks', self.admin)
        with self.assertRaises(task_rules.TaskRuleError):
            task_rules.link_tasks(c, c, 'blocks', self.admin)
        task_rules.link_tasks(c, self.a, 'relates', self.admin)   # relates links may go both ways

    def test_staff_board_shows_blocked_and_lead_links_by_code(self):
        self.client.force_login(self.dev_user)
        r = self.client.get(reverse('staff:project_board', args=[self.project.pk]) + '?week=all')
        self.assertContains(r, 'Blocked</span>')
        r = self.client.post(reverse('staff:board_task_update', args=[self.b.pk]), {'status': 'in_progress'}, follow=True)
        self.assertContains(r, 'Blocked by')
        self.assertEqual(self.client.post(reverse('staff:link_add', args=[self.b.pk]),
                                          {'code': self.live.code, 'relation': 'relates'}).status_code, 404)
        self.client.force_login(self.lead_user)
        self.client.post(reverse('staff:link_add', args=[self.b.pk]),
                         {'code': self.live.code.lower(), 'relation': 'blocked_by'})
        self.assertTrue(TaskLink.objects.filter(from_task=self.live, to_task=self.b).exists())


class BugTests(BoardSetup):
    def test_member_reports_bug_into_running_week(self):
        task_rules.start_sprint(self.week2, self.lead_user)
        self.client.force_login(self.dev_user)
        r = self.client.post(reverse('staff:bug_report', args=[self.project.pk]) + f'?found_in={self.live.pk}',
                             {'title': 'Slug 404', 'steps_to_reproduce': '1. rename', 'found_in': str(self.live.pk)})
        bug = Task.objects.get(title='Slug 404')
        self.assertRedirects(r, reverse('staff:board_task_detail', args=[bug.pk]))
        self.assertEqual((bug.issue_type, bug.status, bug.sprint, bug.assigned_to, bug.found_in, bug.code),
                         ('bug', 'todo', self.week2, None, self.live, 'ALW-020'))
        self.assertTrue(Notification.objects.filter(employee=self.lead_emp, title__startswith='Bug reported').exists())
        r = self.client.get(reverse('staff:project_board', args=[self.project.pk]) + '?week=all&type=bug')
        self.assertContains(r, 'Slug 404')
        self.assertNotContains(r, 'Page model')


class EpicTests(BoardSetup):
    def test_epic_progress_and_weeks(self):
        e = task_rules.create_epic(self.project, name='Pages & Sections')
        for t in (self.live, self.planned):
            task_rules.set_epic(t, e, self.admin)
        task_rules.change_status(self.live, 'completed', self.admin, is_admin=True)
        row = task_rules.epic_rows(self.project)[0]
        self.assertEqual((row['done'], row['total'], row['pct'], row['weeks']), (1, 2, 50, ['Week 2']))
        with self.assertRaises(task_rules.TaskRuleError):
            task_rules.create_epic(self.project, name='pages & sections')

    def test_lead_adds_epic_member_cannot(self):
        url = reverse('staff:epic_create', args=[self.project.pk])
        self.client.force_login(self.dev_user)
        self.assertEqual(self.client.post(url, {'name': 'Menus'}).status_code, 404)
        self.client.force_login(self.lead_user)
        self.client.post(url, {'name': 'Menus'})
        self.assertTrue(self.project.epics.filter(name='Menus').exists())


class StuckTests(BoardSetup):
    def test_working_days_skip_sunday(self):
        fri, mon, tue = date(2026, 11, 27), date(2026, 11, 30), date(2026, 12, 1)
        self.assertEqual(task_rules.working_days_between(fri, mon), 2)    # Sat + Mon
        self.assertEqual(task_rules.working_days_between(date(2026, 11, 28), mon), 1)
        self.assertEqual(task_rules.working_days_between(mon, tue), 1)

    def test_stuck_after_two_working_days_in_progress(self):
        self.live.status = 'in_progress'
        self.live.status_changed_at = timezone.make_aware(datetime(2026, 11, 27, 10))
        with mock.patch('django.utils.timezone.localdate', side_effect=lambda *a: date(2026, 11, 30) if not a else a[0].date()):
            self.assertTrue(self.live.is_stuck)
        self.live.status = 'review'
        self.assertFalse(self.live.is_stuck)
