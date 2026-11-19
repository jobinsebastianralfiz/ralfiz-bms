"""Project task board connector tools: list by column, details, create, update, comment."""

from datetime import date, timedelta

from django.test import TestCase

from core.models import Client, Project, Task, TaskActivity, TaskComment, TeamMember

from .test_connector import MCPClientMixin, make_employee, make_token


class TaskToolTests(MCPClientMixin, TestCase):
    def setUp(self):
        self.owner = make_employee('owner', 'owner', staff=True)
        self.token = make_token(self.owner)
        client = Client.objects.create(name='Ajith Kumar', company_name='Ajith Traders')
        self.project = Project.objects.create(client=client, name='Patient Portal',
                                              project_type='web_app', status='in_progress')
        self.other = Project.objects.create(client=client, name='Clinic App',
                                            project_type='web_app', status='in_progress')
        self.dev = TeamMember.objects.create(name='Arun', role='developer')
        self.qa = TeamMember.objects.create(name='Sneha', role='qa')
        self.login = Task.objects.create(project=self.project, title='Login screen',
                                         assigned_to=self.dev, status='in_progress',
                                         due_date=date.today() - timedelta(days=2))
        self.api = Task.objects.create(project=self.project, title='Booking API', status='todo')
        self.done = Task.objects.create(project=self.project, title='Wireframes', status='completed')
        Task.objects.create(project=self.other, title='Clinic setup', status='todo')

    def test_tools_are_listed(self):
        names = {t['name'] for t in self.rpc('tools/list', token=self.token.token).json()['result']['tools']}
        for name in ('list_project_tasks', 'get_task', 'create_task', 'update_task', 'add_task_comment'):
            self.assertIn(name, names)

    def test_list_groups_open_tasks_by_column(self):
        board = self.ok('list_project_tasks', {'project_id': str(self.project.id)})
        self.assertEqual(board['count'], 2)
        self.assertEqual(board['per_status'], {'backlog': 0, 'todo': 1, 'in_progress': 1, 'review': 0, 'completed': 0})
        self.assertEqual(board['columns']['in_progress'][0]['assigned_to'], 'Arun')
        self.assertTrue(board['columns']['in_progress'][0]['is_overdue'])

        everything = self.ok('list_project_tasks', {'project_id': str(self.project.id),
                                                    'include_completed': True})
        self.assertEqual(everything['count'], 3)
        mine = self.ok('list_project_tasks', {'assigned_to': str(self.dev.id)})
        self.assertEqual([t['title'] for t in mine['columns']['in_progress']], ['Login screen'])
        overdue = self.ok('list_project_tasks', {'overdue_only': True})
        self.assertEqual(overdue['count'], 1)

    def test_search_finds_tasks(self):
        found = self.ok('search', {'query': 'booking', 'types': ['tasks']})
        self.assertEqual(found['tasks'][0]['id'], str(self.api.id))

    def test_create_task_logs_activity(self):
        result = self.ok('create_task', {
            'project_id': str(self.project.id), 'title': 'Payment gateway',
            'assigned_to': str(self.qa.id), 'priority': 'high', 'due_date': '2026-12-01',
            'label': 'Backend'})
        task = Task.objects.get(title='Payment gateway')
        self.assertEqual((task.status, task.priority, task.assigned_to, task.category),
                         ('todo', 'high', self.qa, 'Backend'))
        self.assertEqual(task.due_date, date(2026, 12, 1))
        self.assertTrue(TaskActivity.objects.filter(task=task, verb='created').exists())
        self.assertIn(f'/tasks/{task.pk}/', result['task']['url'])

    def test_create_rejects_unknown_member(self):
        is_error, message = self.call('create_task', {
            'project_id': str(self.project.id), 'title': 'X',
            'assigned_to': '00000000-0000-0000-0000-000000000000'})
        self.assertTrue(is_error)
        self.assertIn('team member', message)
        self.assertFalse(Task.objects.filter(title='X').exists())

    def test_update_moves_column_and_reassigns(self):
        result = self.ok('update_task', {'task_id': str(self.login.id), 'status': 'completed',
                                         'assigned_to': str(self.qa.id), 'priority': 'urgent'})
        self.assertEqual(sorted(result['updated']), ['assigned_to', 'priority', 'status'])
        self.login.refresh_from_db()
        self.assertEqual(self.login.completed_date, date.today())
        self.assertEqual(self.login.assigned_to, self.qa)
        status_log = TaskActivity.objects.get(task=self.login, verb='status_changed')
        self.assertEqual((status_log.from_value, status_log.to_value), ('in_progress', 'completed'))
        self.assertTrue(status_log.is_visible_to_client)
        self.assertTrue(TaskActivity.objects.filter(task=self.login, verb='assigned', to_value='Sneha').exists())

        self.ok('update_task', {'task_id': str(self.login.id), 'status': 'review', 'unassign': True})
        self.login.refresh_from_db()
        self.assertIsNone(self.login.completed_date)
        self.assertIsNone(self.login.assigned_to)

    def test_update_with_nothing_is_an_error(self):
        is_error, _ = self.call('update_task', {'task_id': str(self.api.id)})
        self.assertTrue(is_error)

    def test_comment_and_detail(self):
        self.ok('add_task_comment', {'task_id': str(self.api.id), 'body': 'Waiting on client keys'})
        comment = TaskComment.objects.get(task=self.api)
        self.assertFalse(comment.is_visible_to_client)
        self.assertEqual(comment.author, self.owner)
        detail = self.ok('get_task', {'task_id': str(self.api.id)})
        self.assertEqual(detail['comments'][0]['body'], 'Waiting on client keys')
        self.assertEqual(detail['recent_activity'][0]['verb'], 'commented')
        self.assertEqual(detail['client'], 'Ajith Kumar')


class WeekPlanningToolTests(MCPClientMixin, TestCase):
    """Bulk-loading a week plan, weeks, and board settings from Claude."""

    def setUp(self):
        self.owner = make_employee('owner', 'owner', staff=True)
        self.token = make_token(self.owner)
        client = Client.objects.create(name='Alameriah')
        self.project = Project.objects.create(client=client, name='Alameriah Website', status='in_progress')
        self.sana = TeamMember.objects.create(name='Sana', role='developer')
        self.outsider = TeamMember.objects.create(name='Not on team', role='developer')
        self.project.team_members.add(self.sana)
        Task.objects.create(project=self.project, title='ALW-016 Settings app', status='completed')

    def test_configure_then_bulk_load_weeks(self):
        err, msg = self.call('configure_project_board', {'project_id': str(self.project.pk),
                                                          'team_lead': str(self.outsider.pk)})
        self.assertTrue(err)
        self.assertIn('must be on the project team', msg)
        cfg = self.ok('configure_project_board', {'project_id': str(self.project.pk), 'team_lead': str(self.sana.pk),
                                                  'task_prefix': 'alw'})
        self.assertEqual((cfg['task_prefix'], cfg['next_code'], cfg['existing_cards_coded_from_title']),
                         ('ALW', 'ALW-017', 1))
        week = self.ok('create_sprint', {'project_id': str(self.project.pk), 'name': 'Week 2',
                                         'start_date': '2026-11-23', 'end_date': '2026-11-28'})['week']
        out = self.ok('create_tasks_bulk', {'project_id': str(self.project.pk), 'tasks': [
            {'title': 'Page model', 'status': 'backlog', 'sprint_id': week['id'], 'assigned_to': str(self.sana.pk),
             'checklist': ['Migrations run', 'Admin works']},
            {'title': 'Menu', 'status': 'backlog', 'sprint_id': week['id']},
        ]})
        self.assertEqual((out['created'], out['codes']), (2, ['ALW-017', 'ALW-018']))
        listed = self.ok('list_project_tasks', {'project_id': str(self.project.pk), 'status': 'backlog'})
        self.assertEqual(listed['per_status']['backlog'], 2)
        self.assertEqual(listed['columns']['backlog'][0]['sprint'], 'Week 2')
        started = self.ok('start_sprint', {'sprint_id': week['id']})
        self.assertEqual(started['moved_to_todo'], 2)
        self.assertEqual(started['cards_without_owner'], ['ALW-018 Menu'])
        weeks = self.ok('list_sprints', {'project_id': str(self.project.pk)})
        self.assertEqual(weeks['weeks'][0]['status'], 'active')
        self.assertEqual(weeks['team_lead'], 'Sana')

    def test_bulk_is_all_or_nothing(self):
        err, msg = self.call('create_tasks_bulk', {'project_id': str(self.project.pk), 'tasks': [
            {'title': 'Fine'}, {'title': 'Bad', 'priority': 'extreme'}]})
        self.assertTrue(err)
        self.assertIn('Card 2', msg)
        self.assertFalse(Task.objects.filter(title='Fine').exists())

    def test_close_sprint_needs_a_next_week(self):
        week = self.ok('create_sprint', {'project_id': str(self.project.pk), 'name': 'Week 2',
                                         'start_date': '2026-11-23', 'end_date': '2026-11-28'})['week']
        self.ok('create_task', {'project_id': str(self.project.pk), 'title': 'Open card', 'sprint_id': week['id']})
        self.ok('start_sprint', {'sprint_id': week['id']})
        err, msg = self.call('close_sprint', {'sprint_id': week['id']})
        self.assertTrue(err)
        self.assertIn('no next week', msg)
        out = self.ok('close_sprint', {'sprint_id': week['id'], 'carry_over': 'backlog'})
        self.assertEqual((out['carried_over'], out['to']), (1, 'backlog'))
