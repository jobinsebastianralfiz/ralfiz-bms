"""Backlog & weekly planning: who sees backlog cards, who may move what, task codes and weeks."""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core import task_rules
from core.models import Client, Project, ProjectSprint, Task, TaskChecklistItem, TeamMember
from employees.models import Employee, Notification


def staff(username, name):
    first, last = name.split(' ', 1)
    user = User.objects.create_user(username, f'{username}@example.com', 'pw-123456',
                                    first_name=first, last_name=last)
    emp = Employee.objects.create(user=user, employee_id=f'EMP-{username}', role='intern',
                                  employment_type='intern', status='active')
    member = TeamMember.objects.create(name=name, email=f'{username}@example.com', role='developer')
    return user, emp, member


class BoardSetup(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-123456')
        self.client_user = User.objects.create_user('alameriah', password='pw-123456')
        biz = Client.objects.create(name='Alameriah', email='al@example.com', user=self.client_user)
        self.lead_user, self.lead_emp, self.lead = staff('sana', 'Sana Parvin')
        self.dev_user, self.dev_emp, self.dev = staff('mithra', 'Mithra K')
        self.project = Project.objects.create(client=biz, name='Alameriah Website', status='in_progress',
                                              task_prefix='ALW', next_task_number=17, team_lead=self.lead)
        self.project.team_members.set([self.lead, self.dev])
        today = date.today()
        self.week2 = task_rules.create_sprint(self.project, name='Week 2', start_date=today,
                                              end_date=today + timedelta(days=5))
        self.week3 = task_rules.create_sprint(self.project, name='Week 3', start_date=today + timedelta(days=7),
                                              end_date=today + timedelta(days=12))
        self.live = task_rules.create_task(self.project, self.admin, title='Page model', status='todo',
                                           assigned_to=self.dev)
        self.planned = task_rules.create_task(self.project, self.admin, title='Contact form',
                                              status='backlog', sprint=self.week2, assigned_to=self.dev,
                                              checklist=['Form saves', 'Email sent'])
        self.later = task_rules.create_task(self.project, self.admin, title='Blog', status='backlog',
                                            sprint=self.week3)


class CodeTests(BoardSetup):
    def test_codes_follow_the_prefix_and_never_repeat(self):
        self.assertEqual([self.live.code, self.planned.code, self.later.code], ['ALW-017', 'ALW-018', 'ALW-019'])
        Task.objects.create(project=self.project, title='Manual', code='ALW-020')
        self.assertEqual(task_rules.next_code(self.project), 'ALW-021')   # skips a taken code
        self.assertIn('ALW-017', str(self.live))

    def test_no_prefix_no_code(self):
        other = Project.objects.create(client=self.project.client, name='Other')
        self.assertEqual(task_rules.create_task(other, self.admin, title='x').code, '')

    def test_backfill_moves_codes_out_of_titles(self):
        p = Project.objects.create(client=self.project.client, name='Old board')
        Task.objects.create(project=p, title='ALW-004 Pages app')
        Task.objects.create(project=p, title='alw-9: Footer')
        Task.objects.create(project=p, title='No code here')
        p.task_prefix = 'ALW'
        p.save()
        self.assertEqual(task_rules.backfill_codes(p), 2)
        self.assertEqual(sorted(p.tasks.exclude(code='').values_list('code', 'title')),
                         [('ALW-004', 'Pages app'), ('ALW-009', 'Footer')])
        p.refresh_from_db()
        self.assertEqual(p.next_task_number, 10)


class VisibilityTests(BoardSetup):
    def test_rules(self):
        qs = self.project.tasks.all()
        self.assertEqual(set(task_rules.visible_to(qs, member=self.dev)), {self.live})
        self.assertEqual(set(task_rules.visible_to(qs, member=self.lead)), {self.live, self.planned, self.later})
        self.assertEqual(task_rules.visible_to(qs, is_admin=True).count(), 3)

    def test_client_portal_never_shows_backlog(self):
        self.client.force_login(self.client_user)
        r = self.client.get(f'/portal/projects/{self.project.pk}/')
        self.assertContains(r, 'Page model')
        self.assertNotContains(r, 'Contact form')
        self.assertNotContains(r, 'Blog')

    def test_member_board_hides_backlog_lead_board_shows_it(self):
        self.client.force_login(self.dev_user)
        url = reverse('staff:project_board', args=[self.project.pk])
        r = self.client.get(url + '?week=all')
        self.assertContains(r, 'Page model')
        self.assertNotContains(r, 'Contact form')
        self.assertNotContains(r, 'Start Week 2')
        self.assertEqual(self.client.get(reverse('staff:board_task_detail', args=[self.planned.pk])).status_code, 404)
        self.client.force_login(self.lead_user)
        r = self.client.get(url + '?week=all')
        self.assertContains(r, 'Contact form')
        self.assertContains(r, 'Start Week 2')
        self.assertContains(r, 'ALW-018')

    def test_backlog_only_project_not_listed_for_member(self):
        p = Project.objects.create(client=self.project.client, name='Future project', status='confirmed')
        task_rules.create_task(p, self.admin, title='Later', status='backlog', assigned_to=self.dev)
        from employees.portal_views import staff_projects
        self.assertNotIn(p, staff_projects(self.dev_emp)[0])

    def test_admin_board_has_backlog_column_and_weeks(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('task_board') + f'?project={self.project.pk}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([c['key'] for c in r.context['columns']][0], 'backlog')
        self.assertContains(r, 'Start Week 2')
        self.assertContains(r, 'ALW-018')


class MoveRuleTests(BoardSetup):
    def test_member_moves_own_card_within_live_columns(self):
        task_rules.change_status(self.live, 'in_progress', self.dev_user, member=self.dev)
        self.assertEqual(self.live.status, 'in_progress')
        self.assertIsNotNone(self.live.status_changed_at)
        with self.assertRaisesMessage(task_rules.TaskRuleError, 'Sana Parvin (team lead)'):
            task_rules.change_status(self.live, 'completed', self.dev_user, member=self.dev)

    def test_member_cannot_move_others_or_backlog(self):
        mine_later = task_rules.create_task(self.project, self.admin, title='x', status='backlog',
                                            assigned_to=self.dev)
        with self.assertRaises(task_rules.TaskRuleError):
            task_rules.change_status(mine_later, 'todo', self.dev_user, member=self.dev)
        theirs = task_rules.create_task(self.project, self.admin, title='y', status='todo', assigned_to=self.lead)
        with self.assertRaises(task_rules.TaskRuleError):
            task_rules.change_status(theirs, 'in_progress', self.dev_user, member=self.dev)

    def test_members_can_complete_setting(self):
        self.project.members_can_complete = True
        self.project.save()
        task_rules.change_status(self.live, 'completed', self.dev_user, member=self.dev)
        self.assertEqual(self.live.completed_date, date.today())

    def test_review_needs_pr_link_when_repo_set(self):
        self.project.github_repo = 'https://github.com/Ralfiz-Technologies/alameriah-website'
        self.project.save()
        with self.assertRaisesMessage(task_rules.TaskRuleError, 'pull request link'):
            task_rules.change_status(self.live, 'review', self.dev_user, member=self.dev)
        task_rules.change_status(self.live, 'review', self.dev_user, member=self.dev,
                                 pr_url='https://github.com/x/y/pull/3')
        self.assertEqual((self.live.status, self.live.pr_url), ('review', 'https://github.com/x/y/pull/3'))

    def test_lead_moves_anything(self):
        task_rules.change_status(self.planned, 'todo', self.lead_user, member=self.lead)
        task_rules.change_status(self.live, 'completed', self.lead_user, member=self.lead)
        self.assertEqual(self.live.status, 'completed')

    def test_staff_portal_move_shows_the_rule(self):
        self.client.force_login(self.dev_user)
        r = self.client.post(reverse('staff:board_task_update', args=[self.live.pk]),
                             {'status': 'completed'}, follow=True)
        self.assertContains(r, 'Only Sana Parvin (team lead) can move this card')
        self.live.refresh_from_db()
        self.assertEqual(self.live.status, 'todo')

    def test_checklist_ticks(self):
        item = self.planned.checklist.first()
        task_rules.set_checklist_item(item, True, self.dev_user, member=self.dev)
        self.assertEqual(self.planned.checklist_progress, (1, 2))
        outsider = TeamMember.objects.create(name='Other')
        with self.assertRaises(task_rules.TaskRuleError):
            task_rules.set_checklist_item(item, False, self.admin, member=outsider)


class WeekTests(BoardSetup):
    def test_start_week_moves_backlog_and_notifies_once_per_owner(self):
        result = task_rules.start_sprint(self.week2, self.lead_user)
        self.assertEqual(result['moved'], 1)
        self.planned.refresh_from_db()
        self.later.refresh_from_db()
        self.assertEqual((self.planned.status, self.later.status), ('todo', 'backlog'))
        self.assertEqual(Notification.objects.filter(employee=self.dev_emp).count(), 1)
        with self.assertRaisesMessage(task_rules.TaskRuleError, 'Week 2 is still running'):
            task_rules.start_sprint(self.week3, self.lead_user)

    def test_close_week_carries_open_cards(self):
        task_rules.start_sprint(self.week2, self.lead_user)
        done = task_rules.create_task(self.project, self.admin, title='Done one', status='completed',
                                      sprint=self.week2)
        result = task_rules.close_sprint(self.week2, self.lead_user)
        self.assertEqual((result['completed'], result['carried_over'], result['to']), (1, 1, 'Week 3'))
        self.planned.refresh_from_db()
        done.refresh_from_db()
        self.assertEqual((self.planned.sprint, self.planned.status), (self.week3, 'todo'))
        self.assertEqual(done.sprint, self.week2)

    def test_close_week_to_backlog(self):
        task_rules.start_sprint(self.week2, self.lead_user)
        task_rules.close_sprint(self.week2, self.lead_user, 'backlog')
        self.planned.refresh_from_db()
        self.assertEqual(self.planned.status, 'backlog')

    def test_lead_starts_week_from_staff_portal_member_cannot(self):
        url = reverse('staff:sprint_action', args=[self.project.pk, self.week2.pk, 'start'])
        self.client.force_login(self.dev_user)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.lead_user)
        r = self.client.post(url, follow=True)
        self.assertContains(r, 'Week 2 started: 1 card moved to To Do')
        self.week2.refresh_from_db()
        self.assertEqual(self.week2.status, 'active')

    def test_lead_adds_card_from_staff_portal(self):
        self.client.force_login(self.lead_user)
        r = self.client.post(reverse('staff:board_task_create', args=[self.project.pk]), {
            'title': 'Gallery', 'assigned_to': str(self.dev.pk), 'sprint': str(self.week3.pk),
            'status': 'backlog', 'priority': 'high', 'checklist': 'Images upload\nLightbox works\n',
            'branch_name': 'feature/alw-020-gallery'})
        self.assertEqual(r.status_code, 302)
        t = Task.objects.get(title='Gallery')
        self.assertEqual((t.code, t.status, t.sprint, t.assigned_to, t.checklist.count()),
                         ('ALW-020', 'backlog', self.week3, self.dev, 2))
        self.client.force_login(self.dev_user)
        self.assertEqual(self.client.get(reverse('staff:board_task_create', args=[self.project.pk])).status_code, 404)

    def test_admin_starts_week_from_board(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('project_sprint_action', args=[self.project.pk, self.week2.pk, 'start']),
                             follow=True)
        self.assertContains(r, 'Week 2 started')

    def test_one_active_week_constraint(self):
        from django.db import IntegrityError, transaction
        ProjectSprint.objects.filter(pk=self.week2.pk).update(status='active')
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProjectSprint.objects.filter(pk=self.week3.pk).update(status='active')


class ProjectFormBoardSettingsTests(BoardSetup):
    def test_saving_prefix_and_lead(self):
        self.client.force_login(self.admin)
        Task.objects.create(project=self.project, title='ALW-050 Old card')
        r = self.client.post(reverse('project_update', args=[self.project.pk]), {
            'client': str(self.project.client_id), 'name': self.project.name,
            'project_type': self.project.project_type, 'status': self.project.status,
            'team_members': [str(self.lead.pk), str(self.dev.pk)],
            'team_lead': str(self.dev.pk), 'task_prefix': 'alw', 'next_task_number': '20',
            'members_can_complete': '1'})
        self.assertEqual(r.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual((self.project.team_lead, self.project.task_prefix, self.project.members_can_complete),
                         (self.dev, 'ALW', True))
        self.assertTrue(Task.objects.filter(code='ALW-050', title='Old card').exists())
        self.assertEqual(self.project.next_task_number, 51)


class WeekFilteredBacklogTests(BoardSetup):
    """Backlog counts and cards follow the week picker; members never get backlog cards."""

    def setUp(self):
        super().setUp()
        for w in (self.week2, self.week3):
            for n in range(16 if w == self.week2 else 5):
                task_rules.create_task(self.project, self.admin, title=f'{w.name} #{n}', status='backlog',
                                       sprint=w, assigned_to=self.dev)
        # a lead whose login is linked to the TeamMember (uses /tasks/board/)
        self.linked_lead_user = User.objects.create_user('lead2', password='pw-123456')
        self.lead.user = self.linked_lead_user
        self.lead.save()

    def backlog(self, response):
        col = next(c for c in response.context['columns'] if c['key'] == 'backlog')
        return col['tasks']

    def board(self, week):
        return self.client.get(reverse('task_board') + f'?project={self.project.pk}&week={week}')

    def test_admin_sees_week2_backlog_only(self):
        self.client.force_login(self.admin)
        cards = self.backlog(self.board(self.week2.pk))
        self.assertEqual(len(cards), 17)                    # 16 + the Contact form card from setUp
        self.assertTrue(all(t.sprint_id == self.week2.pk for t in cards))
        r = self.board(self.week2.pk)
        self.assertContains(r, f'Backlog · {len(cards)}')
        self.assertContains(r, 'class="vk-card', count=sum(len(c['tasks']) for c in r.context['columns']))
        self.assertEqual(len(self.backlog(self.board('all'))), 23)

    def test_linked_lead_gets_backlog_on_admin_board(self):
        self.client.force_login(self.linked_lead_user)
        r = self.board(self.week2.pk)
        self.assertEqual(len(self.backlog(r)), 17)
        self.assertContains(r, 'Start Week 2')

    def test_staff_lead_and_member(self):
        url = reverse('staff:project_board', args=[self.project.pk]) + f'?week={self.week2.pk}'
        self.client.force_login(self.lead_user)
        r = self.client.get(url)
        cards = next(c for c in r.context['columns'] if c['key'] == 'backlog')['tasks']
        self.assertEqual(len(cards), 17)
        self.assertContains(r, 'Backlog · 17')
        self.client.force_login(self.dev_user)
        r = self.client.get(url)
        self.assertNotIn('backlog', [c['key'] for c in r.context['columns']])
        self.assertNotContains(r, 'Week 2 #')

    def test_start_button_only_on_its_week_or_all(self):
        self.client.force_login(self.admin)
        self.assertContains(self.board('all'), 'Start Week 2')
        self.assertContains(self.board(self.week2.pk), 'Start Week 2')
        self.assertNotContains(self.board(self.week3.pk), 'Start Week')

    def test_admin_drags_backlog_to_todo_member_cannot(self):
        url = reverse('task_status_update', args=[self.planned.pk])
        self.client.force_login(self.dev_user)
        self.client.post(url, {'status': 'todo'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.planned.refresh_from_db()
        self.assertEqual(self.planned.status, 'backlog')
        self.client.force_login(self.admin)
        r = self.client.post(url, {'status': 'todo'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.json(), {'success': True})
        self.client.post(url, {'status': 'backlog'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.planned.refresh_from_db()
        self.assertEqual(self.planned.status, 'backlog')
