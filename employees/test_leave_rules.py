"""Monthly leave rules: one casual day a month (no carry forward), a prescription
for sick leave past one day a month, and 'Call office' once casual is used up."""
import os
import shutil
import tempfile
from datetime import date
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from employees.models import Employee, LeaveRequest, LeaveType

MEDIA = os.path.realpath(tempfile.mkdtemp())
TODAY = date(2026, 11, 10)
URL = '/api/employees/leave/requests/'


@override_settings(MEDIA_ROOT=MEDIA, OFFICE_PHONE='9895663498')
class LeaveRuleTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        LeaveType.objects.all().delete()
        self.casual = LeaveType.objects.create(name='Casual Leave', days_allowed=12, monthly_limit=1)
        self.sick = LeaveType.objects.create(name='Sick Leave', days_allowed=10, document_after_days=1)
        self.user = User.objects.create_user('anu', password='pw-12345', first_name='Anu')
        self.emp = Employee.objects.create(user=self.user, employee_id='EMP100', employment_type='intern',
                                           role='intern', status='active', phone='9000000000')
        self.client.force_login(self.user)
        patcher = mock.patch('django.utils.timezone.localdate', return_value=TODAY)
        patcher.start()
        self.addCleanup(patcher.stop)

    def apply(self, lt, start, end, **extra):
        data = {'leave_type': str(lt.pk), 'start_date': start, 'end_date': end, 'reason': 'x', **extra}
        return self.client.post(URL, data)   # multipart, as the PWA and app send it

    def test_one_casual_day_a_month_no_carry_forward(self):
        self.assertEqual(self.apply(self.casual, '2026-11-12', '2026-11-12').status_code, 201)
        r = self.apply(self.casual, '2026-11-20', '2026-11-20')
        self.assertEqual(r.status_code, 400)
        msg = r.json()['non_field_errors'][0]
        self.assertIn('already used it for November', msg)
        self.assertIn('98956 63498', msg)
        # December has its own day; October's unused day did not carry into November
        self.assertEqual(self.apply(self.casual, '2026-12-03', '2026-12-03').status_code, 201)

    def test_two_casual_days_in_one_request_refused(self):
        r = self.apply(self.casual, '2026-11-12', '2026-11-13')
        self.assertEqual(r.status_code, 400)
        self.assertIn('1 left for November', r.json()['non_field_errors'][0])

    def test_existing_leave_left_alone(self):
        # Two casual days taken earlier this month, before the rule: kept as they are
        old = LeaveRequest.objects.create(employee=self.emp, leave_type=self.casual, start_date=date(2026, 11, 2),
                                          end_date=date(2026, 11, 3), reason='x', status='approved')
        pending = LeaveRequest.objects.create(employee=self.emp, leave_type=self.casual, start_date=date(2026, 11, 20),
                                              end_date=date(2026, 11, 20), reason='x', status='pending')
        self.assertEqual(self.apply(self.casual, '2026-11-25', '2026-11-25').status_code, 400)
        self.assertEqual(self.apply(self.sick, '2026-11-26', '2026-11-26').status_code, 201)
        old.refresh_from_db()
        pending.refresh_from_db()
        self.assertEqual((old.status, pending.status), ('approved', 'pending'))
        admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client.force_login(admin)
        self.client.post(reverse('emp_leave_action', args=[pending.pk]), {'action': 'approve'})
        pending.refresh_from_db()
        self.assertEqual(pending.status, 'approved')    # HR can still approve what was already asked for

    def test_cancelled_or_rejected_casual_frees_the_day(self):
        LeaveRequest.objects.create(employee=self.emp, leave_type=self.casual, start_date=date(2026, 11, 3),
                                    end_date=date(2026, 11, 3), reason='x', status='rejected')
        self.assertEqual(self.apply(self.casual, '2026-11-12', '2026-11-12').status_code, 201)

    def test_sick_past_one_day_needs_prescription(self):
        self.assertEqual(self.apply(self.sick, '2026-11-12', '2026-11-12').status_code, 201)
        r = self.apply(self.sick, '2026-11-16', '2026-11-17')
        self.assertEqual(r.status_code, 400)
        self.assertIn("doctor's prescription", r.json()['non_field_errors'][0])
        rx = SimpleUploadedFile('rx.jpg', b'\xff\xd8photo', content_type='image/jpeg')
        r = self.apply(self.sick, '2026-11-16', '2026-11-17', document=rx)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.json()['has_document'])
        leave = LeaveRequest.objects.get(start_date=date(2026, 11, 16))
        self.assertTrue(leave.document.path.startswith(os.path.join(MEDIA, 'private')))

    def test_prescription_must_be_pdf_or_photo(self):
        bad = SimpleUploadedFile('rx.exe', b'MZ', content_type='application/octet-stream')
        r = self.apply(self.sick, '2026-11-16', '2026-11-17', document=bad)
        self.assertEqual(r.status_code, 400)
        self.assertIn('document', r.json())

    def test_rules_endpoint_and_call_office(self):
        r = self.client.get('/api/employees/leave/rules/').json()
        self.assertTrue(r['can_apply'])
        self.assertEqual(r['monthly'][0]['remaining'], 1)
        self.assertEqual(r['office_phone'], '9895663498')

        self.apply(self.casual, '2026-11-12', '2026-11-12')
        r = self.client.get('/api/employees/leave/rules/').json()
        self.assertFalse(r['can_apply'])

        page = self.client.get(reverse('staff:leave'))
        self.assertContains(page, 'href="tel:+919895663498"')
        self.assertContains(page, 'Call Office')
        self.assertContains(page, 'Apply sick leave')        # sick leave stays online
        self.assertContains(page, f'<option value="{self.sick.pk}"')
        self.assertNotContains(page, f'<option value="{self.casual.pk}"')
        self.assertEqual(r['online_type_ids'], [str(self.sick.pk)])
        dash = self.client.get(reverse('staff:dashboard'))
        self.assertContains(dash, 'Call Office')
        self.assertNotContains(dash, 'Apply Leave')

    def test_apply_button_while_casual_left(self):
        page = self.client.get(reverse('staff:leave'))
        self.assertContains(page, 'id="sfNewLeave"')
        self.assertContains(page, 'Casual Leave: 1 of 1 day left in November 2026')

    def test_hr_downloads_prescription(self):
        rx = SimpleUploadedFile('rx.pdf', b'%PDF-1.4 rx', content_type='application/pdf')
        self.apply(self.sick, '2026-11-12', '2026-11-12', document=rx)
        leave = LeaveRequest.objects.get()
        admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client.force_login(admin)
        self.assertContains(self.client.get(reverse('emp_leave_list')), reverse('emp_leave_document', args=[leave.pk]))
        r = self.client.get(reverse('emp_leave_document', args=[leave.pk]))
        self.assertEqual(b''.join(r.streaming_content), b'%PDF-1.4 rx')

    def test_hr_edits_monthly_rules(self):
        admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client.force_login(admin)
        self.client.post(reverse('emp_leave_types'), {'action': 'rules', 'pk': self.casual.pk,
                                                      'monthly_limit': '2', 'document_after_days': ''})
        self.casual.refresh_from_db()
        self.assertEqual((self.casual.monthly_limit, self.casual.document_after_days), (2, 0))
