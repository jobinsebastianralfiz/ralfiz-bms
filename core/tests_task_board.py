from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Client, Project, Task, TeamMember


class TaskBoardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        client = Client.objects.create(name='Acme', email='acme@example.com')
        self.project = Project.objects.create(client=client, name='Acme Website', status='in_progress')
        self.other = Project.objects.create(client=client, name='Acme App', status='in_progress')
        self.dev = TeamMember.objects.create(name='Diya Wilson', role='designer')
        Task.objects.create(project=self.project, title='Landing page', status='in_progress',
                            priority='high', category='Website Design', progress=60, assigned_to=self.dev)
        Task.objects.create(project=self.project, title='Login screen', status='todo', priority='low')
        Task.objects.create(project=self.other, title='Push alerts', status='review')

    def board(self, **params):
        self.client.force_login(self.admin)
        return self.client.get(reverse('task_board'), params)

    def test_project_board_shows_its_tasks_in_columns(self):
        r = self.board(project=self.project.pk)
        self.assertEqual(r.status_code, 200)
        cols = {c['key']: [t.title for t in c['tasks']] for c in r.context['columns']}
        self.assertEqual(cols['in_progress'], ['Landing page'])
        self.assertEqual(cols['todo'], ['Login screen'])
        self.assertEqual(cols['review'], [])
        self.assertContains(r, 'Website Design')
        self.assertContains(r, '60% complete')
        self.assertContains(r, '40% left')

    def test_tag_falls_back_to_assignee_role(self):
        Task.objects.filter(title='Landing page').update(category='')
        r = self.board(project=self.project.pk)
        self.assertContains(r, 'Designer')

    def test_filters(self):
        r = self.board(project=self.project.pk, priority='low')
        self.assertEqual(r.context['task_count'], 1)
        r = self.board(q='landing')
        self.assertEqual(r.context['task_count'], 1)
        r = self.board(assignee='none')
        self.assertEqual(r.context['task_count'], 2)

    def test_all_projects_and_bad_project_id(self):
        self.assertEqual(self.board().context['task_count'], 3)
        r = self.board(project='nope')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['task_count'], 3)

    def test_team_member_sees_only_own_tasks(self):
        user = User.objects.create_user('diya', password='pw-12345')
        self.dev.user = user
        self.dev.save()
        self.client.force_login(user)
        r = self.client.get(reverse('task_board'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['task_count'], 1)
        self.assertNotContains(r, 'New Task')

    def test_completed_task_reads_full_progress(self):
        t = Task.objects.get(title='Login screen')
        t.status = 'completed'
        self.assertEqual(t.progress_percent, 100)

    def test_create_saves_label_and_progress_and_returns_to_board(self):
        self.client.force_login(self.admin)
        url = reverse('task_create') + f'?next=board&project={self.project.pk}&status=review'
        form = self.client.get(url)
        self.assertEqual(form.context['prefill_status'], 'review')
        r = self.client.post(url, {'title': 'QA pass', 'project': self.project.pk, 'status': 'review',
                                   'priority': 'medium', 'category': 'Testing', 'progress': '150'})
        self.assertRedirects(r, reverse('task_board') + f'?project={self.project.pk}', fetch_redirect_response=False)
        t = Task.objects.get(title='QA pass')
        self.assertEqual((t.category, t.progress), ('Testing', 100))


class PortalTaskBoardTests(TestCase):
    def test_client_sees_board_without_internal_issues(self):
        from core.models import TaskIssue
        user = User.objects.create_user('acme_login', password='pw-12345')
        client = Client.objects.create(name='Acme', email='acme@example.com', user=user)
        project = Project.objects.create(client=client, name='Acme Website', status='in_progress')
        task = Task.objects.create(project=project, title='Profile page', status='review', progress=80)
        TaskIssue.objects.create(task=task, title='Internal only', is_visible_to_client=False)
        self.client.force_login(user)
        r = self.client.get(reverse('client_portal:portal_project_detail', args=[project.pk]))
        self.assertEqual(r.status_code, 200)
        review = [c for c in r.context['board_columns'] if c['key'] == 'review'][0]
        self.assertEqual([t.title for t in review['tasks']], ['Profile page'])
        self.assertEqual(review['tasks'][0].open_issue_total, 0)
        self.assertContains(r, '80% complete')
        self.assertNotContains(r, 'draggable="true"')


class ProjectDetailBoardLinkTests(TestCase):
    def test_project_page_links_to_its_board(self):
        admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        client = Client.objects.create(name='Acme', email='acme@example.com')
        project = Project.objects.create(client=client, name='Acme Website', status='in_progress')
        Task.objects.create(project=project, title='One')
        self.client.force_login(admin)
        r = self.client.get(reverse('project_detail', args=[project.pk]))
        self.assertContains(r, f'{reverse("task_board")}?project={project.pk}')
        self.assertContains(r, 'Task Board (1)')


class ProjectProgressTests(TestCase):
    def setUp(self):
        client = Client.objects.create(name='Acme', email='acme@example.com')
        self.project = Project.objects.create(client=client, name='Acme Website', status='confirmed')

    def progress(self):
        from core.task_board import project_progress
        return project_progress(self.project)

    def test_one_done_task_is_not_a_done_project(self):
        Task.objects.create(project=self.project, title='Design', status='completed')
        self.assertEqual(self.progress(), 99)
        self.project.status = 'completed'
        self.project.save()
        self.assertEqual(self.progress(), 100)

    def test_average_of_task_progress(self):
        Task.objects.create(project=self.project, title='A', status='completed')
        Task.objects.create(project=self.project, title='B', status='in_progress', progress=50)
        Task.objects.create(project=self.project, title='C', status='todo')
        self.assertEqual(self.progress(), 50)

    def test_posted_update_wins(self):
        from client_portal.models import ProjectUpdate
        Task.objects.create(project=self.project, title='A', status='completed')
        author = User.objects.create_user('pm', password='pw-12345')
        ProjectUpdate.objects.create(project=self.project, author=author, title='Kick-off', description='Started',
                                     progress_percentage=15, is_visible_to_client=True)
        self.assertEqual(self.progress(), 15)
