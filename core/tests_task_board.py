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

    def test_label_filter(self):
        r = self.board(project=self.project.pk, label='website design')
        self.assertEqual(r.context['task_count'], 1)
        self.assertEqual(r.context['labels'], ['Website Design'])

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

    def progress(self, **kw):
        from core.task_board import project_progress
        return project_progress(self.project, **kw)

    def test_no_percentage_without_a_posted_update(self):
        Task.objects.create(project=self.project, title='Design', status='completed')
        self.assertIsNone(self.progress())

    def test_one_done_task_is_not_a_done_project(self):
        Task.objects.create(project=self.project, title='Design', status='completed')
        self.assertEqual(self.progress(from_tasks=True), 99)
        self.project.status = 'completed'
        self.project.save()
        self.assertEqual(self.progress(), 100)

    def test_average_of_task_progress(self):
        Task.objects.create(project=self.project, title='A', status='completed')
        Task.objects.create(project=self.project, title='B', status='in_progress', progress=50)
        Task.objects.create(project=self.project, title='C', status='todo')
        self.assertEqual(self.progress(from_tasks=True), 50)

    def test_posted_update_wins(self):
        from client_portal.models import ProjectUpdate
        Task.objects.create(project=self.project, title='A', status='completed')
        author = User.objects.create_user('pm', password='pw-12345')
        ProjectUpdate.objects.create(project=self.project, author=author, title='Kick-off', description='Started',
                                     progress_percentage=15, is_visible_to_client=True)
        self.assertEqual(self.progress(), 15)


class ProjectLogoTests(TestCase):
    def setUp(self):
        import tempfile
        from django.test import override_settings
        self._media = override_settings(MEDIA_ROOT=tempfile.mkdtemp())
        self._media.enable()
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        client = Client.objects.create(name='Acme', email='acme@example.com')
        self.project = Project.objects.create(client=client, name='Acme Website', status='in_progress')
        self.client.force_login(self.admin)

    def tearDown(self):
        self._media.disable()

    def upload(self, f):
        return self.client.post(reverse('project_logo_upload', args=[self.project.pk]), {'logo': f})

    def test_image_is_saved(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        buf = io.BytesIO()
        Image.new('RGB', (20, 20), 'red').save(buf, 'PNG')
        self.upload(SimpleUploadedFile('logo.png', buf.getvalue(), content_type='image/png'))
        self.project.refresh_from_db()
        self.assertTrue(self.project.logo.name.startswith('project_logos/'))

    def test_non_image_is_refused(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.upload(SimpleUploadedFile('logo.png', b'not an image', content_type='image/png'))
        self.project.refresh_from_db()
        self.assertFalse(self.project.logo)


class ProjectLinkTests(TestCase):
    def setUp(self):
        from core.models import ProjectLink  # noqa: F401
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client_user = User.objects.create_user('acme_login', password='pw-12345')
        self.biz = Client.objects.create(name='Acme', email='acme@example.com', user=self.client_user)
        self.project = Project.objects.create(client=self.biz, name='Acme Website', status='in_progress')
        other = Client.objects.create(name='Other', email='o@example.com')
        self.other_project = Project.objects.create(client=other, name='Other Site', status='in_progress')

    def add(self, **data):
        self.client.force_login(self.admin)
        return self.client.post(reverse('project_link_add', args=[self.project.pk]), data)

    def test_visible_link_notifies_and_shows_in_portal(self):
        from client_portal.models import ClientNotification
        self.add(title='Homepage design', url='figma.com/file/abc', link_type='design',
                 visible_to_client='1', notify_client='1')
        link = self.project.links.get()
        self.assertEqual(link.url, 'https://figma.com/file/abc')
        self.assertTrue(ClientNotification.objects.filter(client=self.biz, title__contains='Homepage design').exists())
        self.client.force_login(self.client_user)
        r = self.client.get(reverse('client_portal:portal_project_detail', args=[self.project.pk]))
        self.assertContains(r, 'Homepage design')
        self.assertContains(self.client.get('/portal/files/'), 'Homepage design')

    def test_staff_only_link_is_hidden_from_client(self):
        self.add(title='Admin panel', url='https://admin.acme.example', link_type='other')
        self.assertFalse(self.project.links.get().visible_to_client)
        self.client.force_login(self.client_user)
        r = self.client.get(reverse('client_portal:portal_project_detail', args=[self.project.pk]))
        self.assertEqual(list(r.context['project_links']), [])

    def test_bad_url_is_refused(self):
        self.add(title='Bad', url='javascript:alert(1)', visible_to_client='1')
        self.assertFalse(self.project.links.exists())

    def test_other_clients_links_never_show(self):
        from core.models import ProjectLink
        ProjectLink.objects.create(project=self.other_project, title='Their secret design', url='https://x.example')
        self.client.force_login(self.client_user)
        self.assertNotContains(self.client.get('/portal/files/'), 'Their secret design')

    def test_toggle_and_delete(self):
        self.add(title='Preview', url='https://preview.acme.example', link_type='preview', visible_to_client='1')
        link = self.project.links.get()
        self.client.post(reverse('project_link_toggle', args=[self.project.pk, link.pk]))
        link.refresh_from_db()
        self.assertFalse(link.visible_to_client)
        self.client.post(reverse('project_link_delete', args=[self.project.pk, link.pk]))
        self.assertFalse(self.project.links.exists())


class TaskFormProjectListTests(TestCase):
    def test_lead_and_review_projects_can_get_tasks(self):
        admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        biz = Client.objects.create(name='SunNok', email='s@example.com')
        lead = Project.objects.create(client=biz, name='SunNok Website', status='lead')
        review = Project.objects.create(client=biz, name='SunNok App', status='review')
        done = Project.objects.create(client=biz, name='Old Site', status='completed')
        self.client.force_login(admin)
        r = self.client.get(reverse('task_create') + f'?project={lead.pk}&next=board')
        names = [p.name for p in r.context['projects']]
        self.assertIn('SunNok Website', names)
        self.assertIn('SunNok App', names)
        self.assertNotIn('Old Site', names)
        self.assertContains(r, f'value="{lead.pk}" selected')
        # Coming from a finished project still lists it.
        r = self.client.get(reverse('task_create') + f'?project={done.pk}')
        self.assertIn('Old Site', [p.name for p in r.context['projects']])
