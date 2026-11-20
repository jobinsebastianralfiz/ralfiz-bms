"""Issue list on joint projects: model, Word reader, AI fallback, partner portal and staff views."""
from decimal import Decimal as D
from io import BytesIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .issue_ai import Feedback, IssueAIError, draft_issues, draft_issues_plain, read_docx, read_upload
from .issue_views import read_issue_workbook
from .models import BusinessPartner, JointIssue, JointProject, JointUpdate

AI = 'bizpartners.issue_ai.draft_issues_ai'


def png():
    from PIL import Image
    out = BytesIO()
    Image.new('RGB', (4, 4), 'red').save(out, 'PNG')
    out.seek(0)
    return out


def make_docx():
    import docx
    doc = docx.Document()
    doc.add_picture(png())
    doc.add_paragraph('Remove above')
    t = doc.add_table(rows=1, cols=2)
    t.cell(0, 0).text, t.cell(0, 1).text = 'Footer', 'Fix the phone number'
    out = BytesIO()
    doc.save(out)
    return out.getvalue()


def make_xlsx():
    """Built like Dr George's tracker: a Dashboard sheet first, the header in row 4."""
    from openpyxl import Workbook
    wb = Workbook()
    wb.active.title = 'Dashboard'
    wb.active['B3'] = 'Total'
    ws = wb.create_sheet('Issue List')
    ws.append(['Dr Jyothis George Website – Issue List'])
    ws.append(['Change Status to Done / Not Done from the dropdown.'])
    ws.append([])
    ws.append(['ID', 'Page', 'Section', 'Issue', 'Action Required', 'Source', 'Status', 'Notes'])
    ws.append(['JG-01', 'Home', 'Hero', 'Banner is blurry', 'Replace the photo', 'Client feedback', 'Done', 'Sent new one'])
    ws.append(['JG-02', 'About', '', 'Typo in bio', 'Fix "Kerela"', 'Gemini review', 'Not Done', None])
    ws.append(['JG-03', 'Global', 'Footer', 'Old phone', '', 'Claude review', 'Not Done', None])
    ws.append([None, None, None, None, None, None, None, None])
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


class Base(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ahmed', 'a@x.sa', 'pass12345')
        self.partner = BusinessPartner.objects.create(name='Ahmed', email='a@x.sa', user=self.user)
        self.project = JointProject.objects.create(partner=self.partner, title='jyothisgeorge.com',
                                                   client_name='Dr Jyothis George', contract_value=D('1000'))
        other = BusinessPartner.objects.create(name='Other Co')
        self.theirs = JointProject.objects.create(partner=other, title='Secret', contract_value=D('1'))

    def issue(self, title, **kw):
        return JointIssue.add_many(kw.pop('project', self.project), [{'title': title, **kw}])[0]


class ModelTests(Base):
    def test_numbers_carry_on_and_empty_titles_skipped(self):
        a = JointIssue.add_many(self.project, [{'title': 'One'}, {'title': '  '}, {'title': 'Two'}])
        b = JointIssue.add_many(self.project, [{'title': 'Three'}])
        self.assertEqual([i.number for i in a + b], [1, 2, 3])
        self.assertEqual(JointIssue.add_many(self.theirs, [{'title': 'X'}])[0].number, 1)

    def test_set_done_stamps_and_clears(self):
        i = self.issue('A')
        i.set_done(True, self.user)
        self.assertIsNotNone(i.done_at)
        self.assertEqual(i.done_by, self.user)
        self.assertEqual(i.status_label, 'Done')
        i.set_done(False)
        self.assertIsNone(i.done_at)
        self.assertIsNone(i.done_by)
        self.assertEqual(i.status_label, 'Not Done')


class ReaderTests(TestCase):
    def test_word_reader_marks_pictures_and_keeps_order(self):
        fb = read_docx(make_docx())
        lines = fb.text.splitlines()
        self.assertEqual(lines[0], '[Picture]')
        self.assertEqual(lines[1], 'Remove above')
        self.assertEqual(lines[2], 'Footer | Fix the phone number')
        self.assertEqual(fb.picture_count, 1)
        self.assertFalse(hasattr(fb, 'images'))

    def test_bad_upload(self):
        with self.assertRaises(IssueAIError):
            read_upload(SimpleUploadedFile('notes.pdf', b'%PDF-1.4'))

    def test_plain_fallback_strips_bullets_and_markers(self):
        rows = draft_issues_plain('• Fix the logo\n\n- [Picture] Remove above\n2. Change footer\n')
        self.assertEqual([r['title'] for r in rows], ['Fix the logo', 'Remove above', 'Change footer'])

    def test_ai_error_falls_back_with_notice(self):
        with mock.patch(AI, side_effect=IssueAIError('The AI is busy right now. Try again in a minute.')):
            drafts, notice = draft_issues(Feedback('Fix the logo\nChange footer', 2), None)
        self.assertEqual(len(drafts), 2)
        self.assertIn('busy', notice)
        self.assertIn('Pictures in the Word file were not read', notice)

    def test_excel_reader(self):
        items = read_issue_workbook(make_xlsx())
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]['title'], 'Banner is blurry')
        self.assertTrue(items[0]['is_done'])
        self.assertEqual(items[0]['notes'], 'Sent new one')
        self.assertFalse(items[1]['is_done'])
        self.assertEqual([i['source'] for i in items], ['client', 'review', 'review'])


class PortalTests(Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.url = reverse('bizpartners_portal:project', args=[self.project.pk])
        self.done = self.issue('Banner is blurry', page='Home', is_done=True)
        self.open = self.issue('Typo in bio', page='About')

    def test_project_page_shows_the_list(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'id="issues"')
        self.assertContains(r, 'Banner is blurry')
        self.assertContains(r, 'Typo in bio')
        self.assertContains(r, 'ji-badge done')
        self.assertContains(r, 'ji-badge open')
        self.assertNotContains(r, 'class="ji-switch"')  # no switches for the partner
        r = self.client.get(self.url + '?status=open')
        self.assertNotContains(r, 'Banner is blurry')
        self.assertContains(r, 'Typo in bio')

    def test_other_partners_project_is_404(self):
        pk = self.theirs.pk
        self.assertEqual(self.client.get(reverse('bizpartners_portal:project', args=[pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('bizpartners_portal:issue_export', args=[pk])).status_code, 404)
        r = self.client.post(reverse('bizpartners_portal:issue_add', args=[pk]), {'title': 'x'})
        self.assertEqual(r.status_code, 404)
        r = self.client.post(reverse('bizpartners_portal:issue_draft', args=[pk]), {'text': 'x'})
        self.assertEqual(r.status_code, 404)
        self.assertFalse(self.theirs.issues.exists())

    def test_paste_review_then_add_ticked(self):
        drafts = [{'page': 'Home', 'section': 'Hero', 'title': 'Swap photo', 'action': 'Use the new one'},
                  {'page': 'Contact', 'section': '', 'title': 'Not an issue', 'action': ''}]
        with mock.patch(AI, return_value=drafts) as ai:
            r = self.client.post(reverse('bizpartners_portal:issue_draft', args=[self.project.pk]),
                                 {'text': 'Swap the photo please'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Swap photo')
        self.assertEqual(ai.call_args.args[0].text, 'Swap the photo please')
        self.assertEqual(self.project.issues.count(), 2)  # nothing saved yet
        r = self.client.post(reverse('bizpartners_portal:issue_add', args=[self.project.pk]), {
            'count': '2', 'source': 'client',
            'include_0': '1', 'page_0': 'Home', 'section_0': 'Hero', 'title_0': 'Swap photo', 'action_0': 'Use it',
            'page_1': 'Contact', 'title_1': 'Not an issue'})
        self.assertRedirects(r, self.url + '#issues', fetch_redirect_response=False)
        new = self.project.issues.get(number=3)
        self.assertEqual((new.title, new.page, new.source, new.created_by), ('Swap photo', 'Home', 'client', self.user))
        self.assertEqual(self.project.issues.count(), 3)

    def test_word_upload_sends_text_only(self):
        with mock.patch(AI, return_value=[{'page': '', 'section': '', 'title': 'Remove the banner', 'action': ''}]) as ai:
            r = self.client.post(reverse('bizpartners_portal:issue_draft', args=[self.project.pk]),
                                 {'file': SimpleUploadedFile('notes.docx', make_docx())})
        fb = ai.call_args.args[0]
        self.assertIn('[Picture]', fb.text)
        self.assertNotIn('PNG', fb.text)
        self.assertContains(r, 'Pictures in the Word file were not read')

    def test_ai_error_shows_paragraphs_and_notice(self):
        with mock.patch(AI, side_effect=IssueAIError('The AI is busy right now. Try again in a minute.')):
            r = self.client.post(reverse('bizpartners_portal:issue_draft', args=[self.project.pk]),
                                 {'text': 'Fix logo\nChange footer'})
        self.assertContains(r, 'The AI is busy right now')
        self.assertContains(r, 'Change footer')

    def test_quick_add_notifies_owners(self):
        from employees.models import Employee, Notification
        owner_user = User.objects.create_user('owner', 'o@x.in', 'x')
        owner = Employee.objects.create(user=owner_user, employee_id='EMP900', role='owner', status='active')
        with mock.patch('employees.utils.send_push_notification') as push:
            self.client.post(reverse('bizpartners_portal:issue_add', args=[self.project.pk]),
                             {'title': 'Menu overlaps on mobile', 'page': 'Header', 'source': 'partner'})
        i = self.project.issues.get(number=3)
        self.assertEqual((i.title, i.source), ('Menu overlaps on mobile', 'partner'))
        n = Notification.objects.get(employee=owner)
        self.assertIn('added 1 issue', n.title)
        self.assertEqual(n.data['kind'], 'joint_issues')
        push.assert_called_once()

    def test_partner_cannot_use_staff_toggle(self):
        self.client.post(reverse('bizpartners:issue_toggle', args=[self.project.pk, self.open.pk]), {'done': '1'})
        self.open.refresh_from_db()
        self.assertFalse(self.open.is_done)

    def test_excel_export(self):
        from openpyxl import load_workbook
        r = self.client.get(reverse('bizpartners_portal:issue_export', args=[self.project.pk]) + '?status=open')
        self.assertEqual(r.status_code, 200)
        self.assertIn('_issues_', r['Content-Disposition'])
        wb = load_workbook(BytesIO(r.content))
        self.assertEqual(wb.sheetnames, ['Dashboard', 'Issue List'])
        rows = list(wb['Issue List'].iter_rows(values_only=True))
        self.assertEqual(rows[0][:7], ('#', 'Page', 'Section', 'Issue', 'Action Required', 'Source', 'Status'))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][6], 'Not Done')

    def test_open_issue_count_on_project_list(self):
        r = self.client.get(reverse('bizpartners_portal:projects'))
        self.assertContains(r, '1 open issue')


class StaffTests(Base):
    def setUp(self):
        super().setUp()
        self.staff = User.objects.create_superuser('boss', 'b@x.in', 'pass12345')
        self.client.force_login(self.staff)
        self.url = reverse('bizpartners:project', args=[self.project.pk])
        self.a = self.issue('A one', page='Home')
        self.b = self.issue('B two', page='About')

    def test_page_and_ajax_toggle(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'class="ji-switch"')
        self.assertContains(r, 'A one')
        r = self.client.post(reverse('bizpartners:issue_toggle', args=[self.project.pk, self.a.pk]), {'done': '1'},
                             HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.content, b'Done')
        self.a.refresh_from_db()
        self.assertEqual(self.a.done_by, self.staff)

    def test_bulk_done_posts_one_update(self):
        self.client.post(reverse('bizpartners:issue_bulk', args=[self.project.pk]),
                         {'ids': [self.a.pk, self.b.pk], 'done': '1'})
        self.assertEqual(self.project.issues.filter(is_done=True).count(), 2)
        u = JointUpdate.objects.get(project=self.project)
        self.assertIn('2 issues done', u.message)
        self.client.post(reverse('bizpartners:issue_bulk', args=[self.project.pk]), {'ids': [self.a.pk], 'done': '0'})
        self.assertEqual(JointUpdate.objects.filter(project=self.project).count(), 1)

    def test_edit_and_delete(self):
        self.client.post(reverse('bizpartners:issue_save', args=[self.project.pk, self.a.pk]), {
            'title': 'A edited', 'page': 'Home', 'notes': 'Waiting for the photo', 'source': 'ralfiz', 'done': '1'})
        self.a.refresh_from_db()
        self.assertEqual((self.a.title, self.a.notes, self.a.source, self.a.is_done),
                         ('A edited', 'Waiting for the photo', 'ralfiz', True))
        self.client.post(reverse('bizpartners:issue_delete', args=[self.project.pk, self.b.pk]))
        self.assertFalse(JointIssue.objects.filter(pk=self.b.pk).exists())

    def test_excel_import(self):
        r = self.client.post(reverse('bizpartners:issue_import', args=[self.project.pk]),
                             {'file': SimpleUploadedFile('list.xlsx', make_xlsx())})
        self.assertRedirects(r, self.url + '#issues', fetch_redirect_response=False)
        imported = list(self.project.issues.filter(number__gt=2))
        self.assertEqual([i.number for i in imported], [3, 4, 5])
        self.assertEqual([i.is_done for i in imported], [True, False, False])
        self.assertEqual(imported[1].source, 'review')
        self.assertIsNone(imported[0].done_at)  # imported Done rows carry no made-up date

    def test_ai_draft_keeps_source(self):
        with mock.patch(AI, return_value=[{'page': 'Home', 'section': '', 'title': 'X', 'action': ''}]):
            r = self.client.post(reverse('bizpartners:issue_draft', args=[self.project.pk]),
                                 {'text': 'x', 'source': 'review'})
        self.assertContains(r, '<option value="review" selected>', html=False)

    def test_bms_project_links_to_partner_issues(self):
        from core.models import Client, Project
        c = Client.objects.create(name='Dr George')
        p = Project.objects.create(client=c, name='jyothisgeorge.com')
        self.project.linked_project = p
        self.project.save()
        r = self.client.get(reverse('project_detail', args=[p.pk]))
        self.assertContains(r, 'Partner issues (2 open)')


class ProgressAndPictureTests(Base):
    """'% done' follows the issue list; issues can carry screenshots."""

    def setUp(self):
        super().setUp()
        import shutil
        import tempfile
        from django.test import override_settings
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, True)
        self._media = override_settings(MEDIA_ROOT=media)
        self._media.enable()
        self.addCleanup(self._media.disable)
        self.staff = User.objects.create_superuser('boss', 'b@x.in', 'pass12345')

    def pic(self, name='shot.png'):
        return SimpleUploadedFile(name, png().getvalue(), 'image/png')

    def pct(self):
        self.project.refresh_from_db()
        return self.project.progress

    def test_progress_follows_done_share(self):
        self.project.progress = 0
        self.project.save()
        a = self.issue('A', is_done=True)
        self.issue('B')
        self.issue('C')
        self.assertEqual(self.pct(), 33)
        self.client.force_login(self.staff)
        r = self.client.post(reverse('bizpartners:issue_toggle', args=[self.project.pk, a.pk]), {'done': '0'},
                             HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r['X-Progress'], '0')
        self.client.post(reverse('bizpartners:issue_bulk', args=[self.project.pk]),
                         {'ids': list(self.project.issues.values_list('pk', flat=True)), 'done': '1'})
        self.assertEqual(self.pct(), 100)
        self.client.post(reverse('bizpartners:issue_save', args=[self.project.pk, a.pk]),
                         {'title': 'A', 'done': '0'})
        self.assertEqual(self.pct(), 67)
        self.client.post(reverse('bizpartners:issue_delete', args=[self.project.pk, a.pk]))
        self.assertEqual(self.pct(), 100)

    def test_no_issues_keeps_typed_progress(self):
        self.project.progress = 40
        self.project.save()
        JointIssue.sync_progress(self.project)
        self.assertEqual(self.pct(), 40)

    def test_staff_add_with_pictures_then_remove_one(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('bizpartners:issue_add', args=[self.project.pk]),
                         {'title': 'Logo blurry', 'images': [self.pic('a.png'), self.pic('b.png')]})
        issue = self.project.issues.get(title='Logo blurry')
        self.assertEqual(issue.images.count(), 2)
        first = issue.images.first()
        path = first.image.path
        r = self.client.get(reverse('bizpartners:project', args=[self.project.pk]))
        self.assertContains(r, first.image.url)
        self.client.post(reverse('bizpartners:issue_save', args=[self.project.pk, issue.pk]),
                         {'title': 'Logo blurry', 'remove_image': [first.pk]})
        self.assertEqual(issue.images.count(), 1)
        import os
        self.assertFalse(os.path.exists(path))

    def test_partner_add_with_picture_and_bad_file_skipped(self):
        self.client.force_login(self.user)
        bad = SimpleUploadedFile('notes.png', b'not a picture', 'image/png')
        r = self.client.post(reverse('bizpartners_portal:issue_add', args=[self.project.pk]),
                             {'title': 'Menu overlaps', 'images': [self.pic(), bad]}, follow=True)
        issue = self.project.issues.get(title='Menu overlaps')
        self.assertEqual(issue.images.count(), 1)
        self.assertTrue(issue.images.first().image.name.startswith('joint_issues/'))
        self.assertContains(r, 'notes.png (not a picture)')
        r = self.client.get(reverse('bizpartners_portal:project', args=[self.project.pk]))
        self.assertContains(r, issue.images.first().image.url)


class LayoutTests(Base):
    """The project page is tabbed, and staff edit an issue in a modal."""

    def test_partner_page_has_tabs_with_open_count(self):
        self.issue('Open one')
        self.client.force_login(self.user)
        r = self.client.get(reverse('bizpartners_portal:project', args=[self.project.pk]))
        for name in ('issues', 'money', 'access', 'updates'):
            self.assertContains(r, f'data-bp-panel="{name}"')
        self.assertContains(r, 'data-default="issues"')
        self.assertContains(r, '1 open</span>')
        self.assertContains(r, 'id="quotes"')  # old #quotes links still find their section

    def test_money_tab_first_when_nothing_open(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('bizpartners_portal:project', args=[self.project.pk]))
        self.assertContains(r, 'data-default="money"')

    def test_staff_edit_is_a_modal(self):
        issue = self.issue('Fix logo')
        self.client.force_login(User.objects.create_superuser('boss2', 'b2@x.in', 'pass12345'))
        r = self.client.get(reverse('bizpartners:project', args=[self.project.pk]))
        self.assertContains(r, f'<dialog class="ji-modal" id="jiEdit{issue.pk}"')
        self.assertContains(r, 'enctype="multipart/form-data" action="%s"'
                            % reverse('bizpartners:issue_save', args=[self.project.pk, issue.pk]))
        self.assertNotContains(r, 'ji-edit-row')


class OrderAndAddModalTests(Base):
    def test_newest_issue_first_and_add_is_a_modal(self):
        self.issue('Old one'); self.issue('New one')
        self.client.force_login(self.user)
        html = self.client.get(reverse('bizpartners_portal:project', args=[self.project.pk])).content.decode()
        self.assertLess(html.index('New one'), html.index('Old one'))
        self.assertIn('<dialog class="ji-modal ji-add-modal" id="jiAdd"', html)

    def test_empty_list_offers_add_button(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('bizpartners_portal:project', args=[self.project.pk]))
        self.assertContains(r, 'No issues yet.')


class StaffAddModalTests(Base):
    def test_staff_add_modal_has_import_and_edit_modals_stay(self):
        issue = self.issue('One')
        self.client.force_login(User.objects.create_superuser('boss3', 'b3@x.in', 'pass12345'))
        html = self.client.get(reverse('bizpartners:project', args=[self.project.pk])).content.decode()
        add = html[html.index('id="jiAdd"'):html.index('</dialog>', html.index('id="jiAdd"'))]
        self.assertIn('data-ji-pane="import"', add)
        self.assertIn('data-ji-pane="one"', add)
        self.assertIn(f'id="jiEdit{issue.pk}"', html)
