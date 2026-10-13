"""The per-person "selfie check" switch on check-in."""
import io
from datetime import time
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import Attendance, Employee, OfficeConfig


def selfie():
    buf = io.BytesIO()
    Image.new('RGB', (8, 8), (200, 160, 140)).save(buf, 'JPEG')
    return SimpleUploadedFile('selfie.jpg', buf.getvalue(), content_type='image/jpeg')


def make_employee(username, **kwargs):
    user = User.objects.create_user(username=username, password='pw-123456', first_name=username.title())
    # A late personal deadline so the tests pass whatever time they run.
    return Employee.objects.create(user=user, employee_id=username.upper(), employment_type='intern',
                                   role='intern', status='active', custom_check_in_deadline=time(23, 59),
                                   face_photo=selfie(), **kwargs)


@mock.patch('employees.views.compare_faces', return_value=(False, 0.31, None))
class FaceCheckSwitchTests(TestCase):
    URL = '/api/employees/attendance/check-in/'

    @classmethod
    def setUpTestData(cls):
        OfficeConfig.objects.create(qr_code='OFFICE-QR-F', daily_required_hours=Decimal('6.00'),
                                    check_in_deadline=time(10, 15), min_checkout_time_floor=time(16, 0))

    def check_in(self, username, **body):
        self.client.login(username=username, password='pw-123456')
        data = {'latitude': '10.9760000', 'longitude': '76.2250000', **body}
        return self.client.post(self.URL, data)

    def test_on_by_default_and_a_mismatch_is_refused(self, compare):
        emp = make_employee('fc_on')
        self.assertTrue(emp.face_check_required)
        res = self.check_in('fc_on', verification_method='face_qr', qr_code='OFFICE-QR-F', face_photo=selfie())
        self.assertEqual(res.status_code, 403)
        self.assertFalse(Attendance.objects.filter(employee=emp).exists())

    def test_on_closes_the_qr_only_shortcut(self, compare):
        make_employee('fc_qr_only')
        res = self.check_in('fc_qr_only', verification_method='qr', qr_code='OFFICE-QR-F')
        self.assertEqual(res.status_code, 400)
        self.assertIn('selfie', res.json()['error'])

    def test_off_skips_the_match(self, compare):
        emp = make_employee('fc_off', face_check_required=False)
        res = self.check_in('fc_off', verification_method='face_qr', qr_code='OFFICE-QR-F', face_photo=selfie())
        self.assertEqual(res.status_code, 201, res.content)
        compare.assert_not_called()
        record = Attendance.objects.get(employee=emp)
        self.assertFalse(record.face_verified)
        self.assertTrue(record.qr_verified)

    def test_off_allows_qr_and_location_without_a_selfie(self, compare):
        emp = make_employee('fc_off_qr', face_check_required=False)
        res = self.check_in('fc_off_qr', verification_method='qr', qr_code='OFFICE-QR-F')
        self.assertEqual(res.status_code, 201, res.content)
        self.assertTrue(Attendance.objects.get(employee=emp).qr_verified)

    def test_off_still_needs_the_office_qr(self, compare):
        make_employee('fc_off_noqr', face_check_required=False)
        res = self.check_in('fc_off_noqr', verification_method='location')
        self.assertEqual(res.status_code, 400)
        self.assertIn('QR', res.json()['error'])

    def test_off_remote_check_in_is_not_matched(self, compare):
        emp = make_employee('fc_off_remote', face_check_required=False, work_mode='remote')
        res = self.check_in('fc_off_remote', verification_method='remote', is_remote='true', face_photo=selfie())
        self.assertEqual(res.status_code, 201, res.content)
        compare.assert_not_called()
        self.assertFalse(Attendance.objects.get(employee=emp).face_verified)

    def test_login_payload_tells_the_app(self, compare):
        make_employee('fc_api', face_check_required=False)
        res = self.client.post('/api/employees/auth/login/', {'username': 'fc_api', 'password': 'pw-123456'})
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIs(res.json()['employee']['face_check_required'], False)


class FaceCheckAdminTests(TestCase):
    def test_hr_can_turn_it_off_and_the_portal_stops_asking(self):
        emp = make_employee('fc_hr')
        User.objects.create_superuser('boss', 'b@x.com', 'pw-123456')
        self.client.login(username='boss', password='pw-123456')
        url = reverse('emp_employee_detail', args=[emp.pk])
        self.assertContains(self.client.get(url), 'Selfie check at check-in')
        self.client.post(url, {'action': 'toggle_face_check', 'required': '0'})
        emp.refresh_from_db()
        self.assertFalse(emp.face_check_required)

        emp.face_photo = None
        emp.save(update_fields=['face_photo'])
        self.client.logout()
        self.client.login(username='fc_hr', password='pw-123456')
        page = self.client.get(reverse('staff:attendance')).content.decode()
        self.assertNotIn('Register your face first', page)
        self.assertIn('var FACE_REQUIRED = false;', page)
