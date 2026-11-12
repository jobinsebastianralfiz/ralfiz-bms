import json
import secrets
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.models import AccessToken, Application

from core.models import Client, CompanySettings, Project
from core.signoff_models import ProjectSignoff, SignoffError, build_signoff_snapshot, create_signoff
from employees.models import Employee, Notification

SECTIONS = [
    {'heading': 'Purpose', 'blocks': [{'type': 'text', 'text': 'By signing, Anil Traders confirms delivery.'}]},
    {'heading': 'What was delivered', 'blocks': [
        {'type': 'checklist', 'title': 'Website', 'items': ['Home page', 'Contact form']},
        {'type': 'checklist', 'title': 'Admin', 'items': ['Leads inbox']},
    ]},
    {'heading': 'Where it runs', 'blocks': [
        {'type': 'table', 'columns': ['Item', 'Owner'], 'rows': [['Website', 'Client'], ['Source code', 'Ralfiz']]},
        {'type': 'note', 'text': 'Go-live is the date this is signed.'},
    ]},
    {'heading': 'Maintenance', 'blocks': [
        {'type': 'bullets', 'items': ['AI chatbot']},
        {'type': 'cards', 'cards': [
            {'title': 'Covers', 'tone': 'good', 'items': ['Bug fixes']},
            {'title': 'Does not cover', 'note': 'quoted separately', 'tone': 'bad', 'items': ['New features']},
        ]},
    ]},
]
ACCEPTANCE = 'Anil Traders accepts the website as handed over.'


class SignoffBase(TestCase):
    def setUp(self):
        CompanySettings.get_settings().save()
        self.staff = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.owner = Employee.objects.create(
            user=self.staff, employee_id='EMP-OWNER', role='owner', status='active',
            joining_date=date(2025, 1, 1), employment_type='fulltime')
        self.client_rec = Client.objects.create(name='Anil Kumar', company_name='Anil Traders',
                                                email='anil@example.com', phone='9876543210')
        self.project = Project.objects.create(client=self.client_rec, name='Billing App',
                                              final_amount=Decimal('125000'))

    def make(self, **kw):
        return create_signoff(self.project, self.staff, title='Billing App Go-live Sign-off',
                              sections=SECTIONS, acceptance=ACCEPTANCE, **kw)

    def approve_data(self, signoff, **overrides):
        data = {'decision': 'approve', 'signer_name': 'Anil Kumar', 'signer_role': 'Owner',
                'signed_name': 'Anil Kumar', 'agreed': 'on', 'check': signoff.check_ids}
        data.update(overrides)
        return data


class SnapshotTests(SignoffBase):
    def test_checklist_items_get_ids(self):
        signoff = self.make()
        self.assertEqual(signoff.check_ids, ['c1', 'c2', 'c3'])
        self.assertTrue(signoff.reference.startswith('RT/SO/'))
        self.assertEqual(signoff.snapshot_json['client_party'], 'Anil Traders')
        self.assertEqual(signoff.snapshot_json['eyebrow'], 'PROJECT HANDOVER')

    def test_bad_content_names_the_problem(self):
        cases = [
            ([], 'at least one section'),
            ([{'heading': 'A', 'blocks': [{'type': 'video'}]}], 'type must be one of'),
            ([{'heading': 'A', 'blocks': [{'type': 'table', 'columns': ['a', 'b'], 'rows': [['x']]}]}],
             'row 1 must have 2 cells'),
            ([{'heading': '', 'blocks': [{'type': 'text', 'text': 'x'}]}], 'heading is empty'),
            ([{'heading': 'A', 'blocks': [{'type': 'checklist', 'items': []}]}], 'at least 1 item'),
        ]
        for sections, message in cases:
            with self.assertRaisesMessage(SignoffError, message):
                build_signoff_snapshot(self.project, title='T', sections=sections, acceptance='ok')

    def test_replacing_supersedes_the_open_one(self):
        first = self.make()
        second = self.make(replaces=first)
        first.refresh_from_db()
        self.assertEqual(first.status, ProjectSignoff.STATUS_SUPERSEDED)
        self.assertEqual(first.superseded_by, second)
        self.assertEqual(second.snapshot_json['version'], 'v2.0')


class PublicFlowTests(SignoffBase):
    def url(self, signoff):
        return reverse('signoff_sign', args=[signoff.token])

    def test_page_shows_content_and_counts_the_view(self):
        signoff = self.make()
        res = self.client.get(self.url(signoff))
        self.assertContains(res, 'Billing App Go-live Sign-off')
        self.assertContains(res, 'Contact form')
        self.assertContains(res, 'Does not cover')
        self.assertContains(res, ACCEPTANCE)
        signoff.refresh_from_db()
        self.assertEqual((signoff.status, signoff.view_count), (ProjectSignoff.STATUS_VIEWED, 1))

    def test_staff_preview_is_not_counted(self):
        signoff = self.make()
        self.client.force_login(self.staff)
        self.client.get(self.url(signoff))
        signoff.refresh_from_db()
        self.assertEqual((signoff.status, signoff.view_count), (ProjectSignoff.STATUS_PENDING, 0))

    def test_approve_needs_every_tick(self):
        signoff = self.make()
        res = self.client.post(self.url(signoff), self.approve_data(signoff, check=['c1', 'c2']))
        self.assertEqual(res.status_code, 400)
        self.assertContains(res, '1 item is not ticked', status_code=400)
        signoff.refresh_from_db()
        self.assertFalse(signoff.has_responded)

    def test_approve_records_signature_and_notifies_owner(self):
        signoff = self.make()
        res = self.client.post(self.url(signoff), self.approve_data(signoff), REMOTE_ADDR='10.1.2.3')
        self.assertRedirects(res, reverse('signoff_done', args=[signoff.token]))
        signoff.refresh_from_db()
        self.assertEqual(signoff.status, ProjectSignoff.STATUS_APPROVED)
        self.assertEqual(signoff.checked_items, ['c1', 'c2', 'c3'])
        self.assertEqual((signoff.signed_name, signoff.signer_role), ('Anil Kumar', 'Owner'))
        self.assertEqual(signoff.ip_address, '10.1.2.3')
        self.assertEqual(signoff.body_hash, signoff.compute_body_hash())
        note = Notification.objects.get(employee=self.owner)
        self.assertEqual(note.title, 'Sign-off approved')
        done = self.client.get(reverse('signoff_done', args=[signoff.token]))
        self.assertContains(done, '3 of 3')
        # answered: the link no longer accepts a second response
        again = self.client.post(self.url(signoff), self.approve_data(signoff, signed_name='Someone Else'))
        self.assertRedirects(again, reverse('signoff_done', args=[signoff.token]))
        signoff.refresh_from_db()
        self.assertEqual(signoff.signed_name, 'Anil Kumar')

    def test_report_a_problem_keeps_partial_ticks(self):
        signoff = self.make()
        res = self.client.post(self.url(signoff), {
            'decision': 'issues', 'signer_name': 'Anil Kumar', 'check': ['c1', 'bogus'],
            'issue_notes': 'Contact form does not send email.'})
        self.assertRedirects(res, reverse('signoff_done', args=[signoff.token]))
        signoff.refresh_from_db()
        self.assertEqual(signoff.status, ProjectSignoff.STATUS_ISSUES)
        self.assertEqual(signoff.checked_items, ['c1'])
        self.assertEqual(signoff.unticked_items, ['Contact form', 'Leads inbox'])
        self.assertEqual(signoff.signed_name, '')

    def test_problem_needs_a_note(self):
        signoff = self.make()
        res = self.client.post(self.url(signoff), {'decision': 'issues', 'signer_name': 'Anil'})
        self.assertEqual(res.status_code, 400)

    def test_closed_links(self):
        expired = self.make()
        expired.expires_at = timezone.now() - timedelta(days=1)
        expired.save()
        self.assertContains(self.client.get(self.url(expired)), 'This link has expired')
        self.assertContains(self.client.post(self.url(expired), self.approve_data(expired)),
                            'This link has expired')
        cancelled = self.make()
        cancelled.status = ProjectSignoff.STATUS_CANCELLED
        cancelled.save()
        self.assertContains(self.client.get(self.url(cancelled)), 'no longer active')
        self.assertEqual(self.client.get(reverse('signoff_sign', args=['nope'])).status_code, 404)

    def test_signed_copy_only_after_approval(self):
        signoff = self.make()
        copy = reverse('signoff_copy_pdf', args=[signoff.token])
        self.assertRedirects(self.client.get(copy), self.url(signoff), fetch_redirect_response=False)
        self.client.post(self.url(signoff), self.approve_data(signoff))
        res = self.client.get(copy)
        self.assertEqual(res.status_code, 200)
        if res['Content-Type'] == 'application/pdf':
            self.assertTrue(res.content.startswith(b'%PDF'))
        else:  # WeasyPrint's native libraries are missing: printable page instead
            self.assertContains(res, 'Approved &amp; signed electronically')

    def test_content_is_escaped(self):
        sections = [{'heading': '<script>alert(1)</script>', 'blocks': [{'type': 'text', 'text': '<b>x</b>'}]}]
        signoff = create_signoff(self.project, self.staff, title='T', sections=sections, acceptance='ok')
        res = self.client.get(self.url(signoff))
        self.assertNotContains(res, '<script>alert(1)</script>')
        self.assertContains(res, '&lt;b&gt;x&lt;/b&gt;')


class StaffPageTests(SignoffBase):
    def test_login_required(self):
        signoff = self.make()
        res = self.client.get(reverse('signoff_detail', args=[signoff.pk]))
        self.assertEqual(res.status_code, 302)

    def test_detail_and_cancel(self):
        signoff = self.make()
        self.client.force_login(self.staff)
        res = self.client.get(reverse('signoff_detail', args=[signoff.pk]))
        self.assertContains(res, signoff.public_path())
        self.assertContains(res, 'wa.me/919876543210')
        self.assertContains(self.client.get(reverse('project_detail', args=[self.project.pk])), 'Sign-off')
        self.client.post(reverse('signoff_cancel', args=[signoff.pk]))
        signoff.refresh_from_db()
        self.assertEqual(signoff.status, ProjectSignoff.STATUS_CANCELLED)

    def test_cannot_cancel_after_answer(self):
        signoff = self.make()
        self.client.post(reverse('signoff_sign', args=[signoff.token]), self.approve_data(signoff))
        self.client.force_login(self.staff)
        self.client.post(reverse('signoff_cancel', args=[signoff.pk]))
        signoff.refresh_from_db()
        self.assertEqual(signoff.status, ProjectSignoff.STATUS_APPROVED)


class ConnectorToolTests(SignoffBase):
    def setUp(self):
        super().setUp()
        app = Application.objects.create(
            name='Claude', client_type='public', authorization_grant_type='authorization-code',
            redirect_uris='https://claude.ai/api/mcp/auth_callback')
        self.token = AccessToken.objects.create(
            user=self.staff, application=app, token=secrets.token_urlsafe(32),
            scope='bms:read bms:write', expires=timezone.now() + timedelta(hours=1), resource=[])

    def call(self, name, args):
        body = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}
        res = self.client.post('/mcp', json.dumps(body), content_type='application/json',
                               HTTP_AUTHORIZATION=f'Bearer {self.token.token}')
        self.assertEqual(res.status_code, 200, res.content)
        result = res.json()['result']
        text = result['content'][0]['text']
        return result['isError'], (text if result['isError'] else json.loads(text))

    def create(self, **extra):
        args = {'project_id': str(self.project.pk), 'title': 'Billing App Go-live Sign-off',
                'sections': SECTIONS, 'acceptance': ACCEPTANCE}
        args.update(extra)
        return self.call('create_signoff', args)

    def test_create_returns_working_client_link(self):
        is_error, data = self.create(document_date='2026-11-12')
        self.assertFalse(is_error, data)
        signoff = ProjectSignoff.objects.get()
        self.assertEqual(signoff.sent_by, self.staff)
        self.assertEqual(signoff.snapshot_json['date'], '12 November 2026')
        self.assertEqual(data['client_link'], f'http://testserver{signoff.public_path()}')
        self.assertEqual(data['checklist_items'], 3)
        self.assertIn('wa.me/919876543210', data['whatsapp_link'])
        self.assertContains(self.client.get(signoff.public_path()), 'Leads inbox')

    def test_bad_content_is_a_readable_error(self):
        is_error, text = self.create(sections=[{'heading': 'A', 'blocks': [{'type': 'video'}]}])
        self.assertTrue(is_error)
        self.assertIn('type must be one of', text)
        self.assertFalse(ProjectSignoff.objects.exists())

    def test_get_list_and_replace(self):
        _, first = self.create()
        signoff = ProjectSignoff.objects.get()
        self.client.post(signoff.public_path(), {
            'decision': 'issues', 'signer_name': 'Anil Kumar', 'check': ['c1'],
            'issue_notes': 'Contact form does not send email.'})
        _, detail = self.call('get_signoff', {'signoff_id': first['id']})
        self.assertEqual(detail['status'], 'Problem reported')
        self.assertEqual(detail['left_unticked'], ['Contact form', 'Leads inbox'])
        self.assertNotIn('client_link', detail)
        self.assertEqual(len(detail['sections']), 4)

        _, second = self.create(replaces_signoff_id=first['id'])
        self.assertEqual(second['version'], 'v2.0')
        signoff.refresh_from_db()
        self.assertEqual(signoff.status, ProjectSignoff.STATUS_SUPERSEDED)

        _, listing = self.call('list_signoffs', {'project_id': str(self.project.pk), 'awaiting_only': True})
        self.assertEqual([i['id'] for i in listing['items']], [second['id']])

    def test_approved_gives_signed_pdf_and_cannot_be_replaced_or_cancelled(self):
        _, first = self.create()
        signoff = ProjectSignoff.objects.get()
        self.client.post(signoff.public_path(), self.approve_data(signoff))
        _, detail = self.call('get_signoff', {'signoff_id': first['id']})
        self.assertEqual(detail['signed_pdf'], f'http://testserver{signoff.public_path()}copy.pdf')
        self.assertEqual(detail['items_ticked'], '3 of 3')
        is_error, text = self.create(replaces_signoff_id=first['id'])
        self.assertTrue(is_error)
        self.assertIn('already approved', text)
        is_error, _ = self.call('cancel_signoff', {'signoff_id': first['id']})
        self.assertTrue(is_error)

    def test_cancel_closes_the_link(self):
        _, first = self.create()
        is_error, data = self.call('cancel_signoff', {'signoff_id': first['id']})
        self.assertFalse(is_error, data)
        self.assertEqual(data['status'], 'Cancelled')
        signoff = ProjectSignoff.objects.get()
        self.assertContains(self.client.get(signoff.public_path()), 'no longer active')
