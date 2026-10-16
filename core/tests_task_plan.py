from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from core.models import Client, Project, Task, TeamMember
from core.task_plan_ai import PlanAIError, _clean_task, draft_tasks_from_checklist

PLAN = """# Phase 1 - Foundation
- [ ] Set up the Next.js project - repo, CI and Railway
- [x] Kick-off call
## Phase 2 - Pages
- [ ] Build the homepage
* [ ] Build the product listing
"""

AI_TASKS = [
    {'title': 'Set up the Next.js project', 'description': 'Repo, CI and Railway ready.', 'label': 'DevOps',
     'priority': 'high', 'role': 'devops', 'phase': 'Phase 1', 'due_date': '2026-11-01'},
    {'title': 'Design the homepage', 'description': 'Figma design approved.', 'label': 'Design',
     'priority': 'medium', 'role': 'designer', 'phase': 'Phase 2', 'due_date': ''},
]


class ChecklistReaderTests(TestCase):
    def test_open_items_become_tasks_under_their_heading(self):
        tasks = draft_tasks_from_checklist(PLAN)
        self.assertEqual([t['title'] for t in tasks],
                         ['Set up the Next.js project', 'Build the homepage', 'Build the product listing'])
        self.assertEqual(tasks[0]['description'], 'repo, CI and Railway')
        self.assertEqual(tasks[0]['phase'], 'Phase 1 - Foundation')
        self.assertEqual(tasks[1]['phase'], 'Phase 2 - Pages')

    def test_cleaning_drops_bad_values(self):
        t = _clean_task({'title': '  - Ship it', 'priority': 'asap', 'role': 'wizard', 'due_date': '31/12/2026'})
        self.assertEqual((t['title'], t['priority'], t['role'], t['due_date']), ('Ship it', 'medium', 'other', ''))
        self.assertIsNone(_clean_task({'title': '   '}))


class PlanImportViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        biz = Client.objects.create(name='AGC', email='agc@example.com')
        self.project = Project.objects.create(client=biz, name='AGC Website', status='confirmed')
        self.designer = TeamMember.objects.create(name='Diya', role='designer')
        self.project.team_members.add(self.designer)
        self.client.force_login(self.admin)

    def post_plan(self, mode='ai', text=PLAN, upload=True):
        data = {'project': self.project.pk, 'mode': mode}
        if upload:
            data['plan_file'] = SimpleUploadedFile('plan.md', text.encode(), content_type='text/markdown')
        else:
            data['plan_text'] = text
        return self.client.post(reverse('task_plan_import'), data)

    def test_ai_drafts_are_shown_for_review_and_nothing_is_saved(self):
        with mock.patch('core.task_plan_ai.draft_tasks_ai', return_value=[dict(t) for t in AI_TASKS]):
            r = self.post_plan()
        self.assertTemplateUsed(r, 'tasks/plan_review.html')
        self.assertContains(r, 'Design the homepage')
        drafts = r.context['drafts']
        self.assertEqual(drafts[1]['assignee'], str(self.designer.pk))
        self.assertEqual(Task.objects.count(), 0)

    def test_ai_failure_falls_back_to_checklist(self):
        with mock.patch('core.task_plan_ai.draft_tasks_ai', side_effect=PlanAIError('The AI is busy right now.')):
            r = self.post_plan()
        self.assertEqual(len(r.context['drafts']), 3)
        self.assertContains(r, 'checklist items instead')

    def test_ai_failure_without_checklist_shows_error(self):
        with mock.patch('core.task_plan_ai.draft_tasks_ai', side_effect=PlanAIError('The AI is busy right now.')):
            r = self.post_plan(text='Just prose, no checklist.', upload=False)
        self.assertTemplateUsed(r, 'tasks/plan_import.html')
        self.assertContains(r, 'The AI is busy right now.')

    def test_checklist_mode_needs_no_ai(self):
        with mock.patch('core.task_plan_ai.draft_tasks_ai') as ai:
            r = self.post_plan(mode='checklist')
        ai.assert_not_called()
        self.assertEqual(len(r.context['drafts']), 3)

    def test_wrong_file_type_refused(self):
        r = self.client.post(reverse('task_plan_import'), {
            'project': self.project.pk, 'mode': 'ai',
            'plan_file': SimpleUploadedFile('plan.pdf', b'%PDF', content_type='application/pdf')})
        self.assertContains(r, 'Upload the plan as a .md')

    def test_existing_title_is_unticked(self):
        Task.objects.create(project=self.project, title='Design the homepage')
        with mock.patch('core.task_plan_ai.draft_tasks_ai', return_value=[dict(t) for t in AI_TASKS]):
            r = self.post_plan()
        self.assertTrue(r.context['drafts'][1]['duplicate'])

    def test_create_only_ticked_rows(self):
        r = self.client.post(reverse('task_plan_create'), {
            'project': self.project.pk, 'count': '2',
            'include_0': '1', 'title_0': 'Set up the project', 'label_0': 'DevOps', 'priority_0': 'high',
            'due_0': '2026-11-01', 'assignee_0': str(self.designer.pk), 'description_0': 'CI ready', 'phase_0': 'Phase 1',
            'title_1': 'Skipped one', 'priority_1': 'low',
        })
        self.assertRedirects(r, reverse('task_board') + f'?project={self.project.pk}', fetch_redirect_response=False)
        task = Task.objects.get()
        self.assertEqual((task.title, task.category, task.priority, task.status, task.assigned_to),
                         ('Set up the project', 'DevOps', 'high', 'todo', self.designer))
        self.assertEqual(str(task.due_date), '2026-11-01')
        self.assertEqual(task.notes, 'Phase: Phase 1')

    def test_team_member_cannot_import(self):
        user = User.objects.create_user('dev', password='pw-12345')
        TeamMember.objects.create(name='Dev', role='developer', user=user)
        self.client.force_login(user)
        r = self.client.get(reverse('task_plan_import'))
        self.assertRedirects(r, reverse('task_board'), fetch_redirect_response=False)
        r = self.client.post(reverse('task_plan_create'), {'project': self.project.pk, 'count': '1',
                                                           'include_0': '1', 'title_0': 'Sneaky'})
        self.assertFalse(Task.objects.exists())
