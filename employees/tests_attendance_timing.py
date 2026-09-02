"""Per-person attendance timing and the early (force) check-out path."""
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Attendance, Employee, OfficeConfig


def make_employee(username, employee_id, **kwargs):
    user = User.objects.create_user(username=username, password='pw-123456',
                                    first_name=username.title())
    return Employee.objects.create(user=user, employee_id=employee_id,
                                   employment_type='intern', role='intern',
                                   status='active', **kwargs)


class AttendancePolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.config = OfficeConfig.objects.create(
            qr_code='OFFICE-QR-1', office_name='HQ',
            daily_required_hours=Decimal('6.00'),
            check_in_deadline=time(10, 15),
            min_checkout_time_floor=time(16, 0))
        cls.standard = make_employee('timing_standard', 'EMPX01')
        cls.flexible = make_employee(
            'timing_flexible', 'EMPX02',
            custom_check_in_deadline=time(12, 30),
            custom_checkout_time_floor=time(19, 0),
            custom_required_hours=Decimal('4.00'))

    def test_blank_overrides_follow_the_office_default(self):
        policy = self.standard.attendance_policy()
        self.assertEqual(policy.check_in_deadline, time(10, 15))
        self.assertEqual(policy.checkout_floor, time(16, 0))
        self.assertEqual(Decimal(policy.required_hours), Decimal('6.00'))
        self.assertFalse(self.standard.has_custom_timing)

    def test_per_person_overrides_win(self):
        policy = self.flexible.attendance_policy()
        self.assertEqual(policy.check_in_deadline, time(12, 30))
        self.assertEqual(policy.checkout_floor, time(19, 0))
        self.assertEqual(Decimal(policy.required_hours), Decimal('4.00'))
        self.assertTrue(self.flexible.has_custom_timing)

    def test_partial_override_only_replaces_that_piece(self):
        emp = make_employee('timing_partial', 'EMPX03',
                            custom_checkout_time_floor=time(13, 0))
        policy = emp.attendance_policy()
        self.assertEqual(policy.check_in_deadline, time(10, 15))   # office default
        self.assertEqual(policy.checkout_floor, time(13, 0))       # personal
        self.assertTrue(emp.has_custom_timing)

    def test_falls_back_to_built_in_defaults_without_office_config(self):
        OfficeConfig.objects.all().delete()
        policy = self.standard.attendance_policy()
        self.assertEqual(policy.check_in_deadline, time(10, 15))
        self.assertEqual(policy.checkout_floor, time(16, 0))
        self.assertEqual(Decimal(policy.required_hours), Decimal('6.00'))

    def test_minimum_checkout_time_uses_the_personal_floor(self):
        check_in = timezone.make_aware(
            timezone.datetime.combine(timezone.localdate(), time(9, 0)))
        record = Attendance.objects.create(
            employee=self.flexible, date=timezone.localdate(),
            check_in=check_in, required_hours=Decimal('4.00'))
        # 9:00 + 4h = 13:00, but this person's floor is 19:00, so 19:00 wins.
        self.assertEqual(timezone.localtime(record.minimum_checkout_time()).time(),
                         time(19, 0))

    def test_minimum_checkout_time_uses_hours_when_they_end_later(self):
        check_in = timezone.make_aware(
            timezone.datetime.combine(timezone.localdate(), time(16, 0)))
        record = Attendance.objects.create(
            employee=self.standard, date=timezone.localdate(),
            check_in=check_in, required_hours=Decimal('6.00'))
        # 16:00 + 6h = 22:00 is later than the 16:00 floor.
        self.assertEqual(timezone.localtime(record.minimum_checkout_time()).time(),
                         time(22, 0))


class TodayAttendanceWindowTests(TestCase):
    """The API tells each person the window that applies to them."""

    @classmethod
    def setUpTestData(cls):
        OfficeConfig.objects.create(
            qr_code='OFFICE-QR-2', daily_required_hours=Decimal('6.00'),
            check_in_deadline=time(10, 15), min_checkout_time_floor=time(16, 0))
        cls.flexible = make_employee(
            'timing_api', 'EMPX04',
            custom_check_in_deadline=time(23, 59),
            custom_checkout_time_floor=time(20, 0),
            custom_required_hours=Decimal('3.50'))

    def test_today_endpoint_reports_the_personal_window(self):
        self.client.login(username='timing_api', password='pw-123456')
        res = self.client.get('/api/employees/attendance/today/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['check_in_deadline'], '23:59')
        self.assertEqual(res.json()['min_checkout_time_floor'], '20:00')
        self.assertEqual(res.json()['required_hours'], 3.5)
        self.assertTrue(res.json()['has_custom_timing'])
        # A late-shift person is still inside their own check-in window.
        self.assertTrue(res.json()['can_check_in'])


class ForceCheckOutTests(TestCase):
    """Leaving early is allowed, but it has to carry a reason."""

    @classmethod
    def setUpTestData(cls):
        OfficeConfig.objects.create(
            qr_code='OFFICE-QR-3', daily_required_hours=Decimal('6.00'),
            check_in_deadline=time(10, 15), min_checkout_time_floor=time(16, 0))
        cls.employee = make_employee('force_user', 'EMPX05', work_mode='remote')

    def setUp(self):
        self.client.login(username='force_user', password='pw-123456')
        # Remote record so the check-out needs no office QR in the test.
        self.record = Attendance.objects.create(
            employee=self.employee, date=timezone.localdate(),
            check_in=timezone.now() - timedelta(hours=1),
            required_hours=Decimal('6.00'), is_remote=True, status='present')

    def post_checkout(self, **body):
        return self.client.post('/api/employees/attendance/check-out/',
                                body, content_type='application/json')

    def test_early_checkout_without_force_is_refused_and_offers_the_force_path(self):
        res = self.post_checkout()
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertTrue(data['can_force'])
        self.assertTrue(data['reason_required'])
        self.assertGreater(data['seconds_remaining'], 0)
        self.record.refresh_from_db()
        self.assertIsNone(self.record.check_out)

    def test_force_without_a_reason_is_refused(self):
        res = self.post_checkout(force=True)
        self.assertEqual(res.status_code, 400)
        self.assertTrue(res.json()['reason_required'])
        self.record.refresh_from_db()
        self.assertIsNone(self.record.check_out)

    def test_force_with_a_too_short_reason_is_refused(self):
        res = self.post_checkout(force=True, reason='ok')
        self.assertEqual(res.status_code, 400)
        self.record.refresh_from_db()
        self.assertIsNone(self.record.check_out)

    def test_force_with_a_reason_checks_out_and_records_the_shortfall(self):
        res = self.post_checkout(force=True, reason='Doctor appointment at 3 PM')
        self.assertEqual(res.status_code, 200)
        self.record.refresh_from_db()
        self.assertIsNotNone(self.record.check_out)
        self.assertTrue(self.record.is_force_checkout)
        self.assertEqual(self.record.force_checkout_reason, 'Doctor appointment at 3 PM')
        self.assertGreater(self.record.pending_hours, 0)
        self.assertEqual(self.record.status, 'half_day')

    def test_on_time_checkout_needs_no_reason(self):
        # Floor already passed for the day, so only the hours worked matter.
        self.employee.custom_checkout_time_floor = time(0, 1)
        self.employee.save(update_fields=['custom_checkout_time_floor'])
        self.record.check_in = timezone.now() - timedelta(hours=9)
        self.record.save(update_fields=['check_in'])
        res = self.post_checkout()
        self.assertEqual(res.status_code, 200)
        self.record.refresh_from_db()
        self.assertFalse(self.record.is_force_checkout)
        self.assertEqual(self.record.force_checkout_reason, '')
        self.assertEqual(self.record.pending_hours, 0)

    def test_personal_floor_makes_an_otherwise_full_day_early(self):
        """A late shift with a 20:00 floor can't close at 18:00 without a reason."""
        self.employee.custom_checkout_time_floor = time(23, 59)
        self.employee.save(update_fields=['custom_checkout_time_floor'])
        self.record.check_in = timezone.now() - timedelta(hours=9)
        self.record.save(update_fields=['check_in'])
        res = self.post_checkout()
        self.assertEqual(res.status_code, 400)
        self.assertTrue(res.json()['can_force'])


class StaffPortalForceCheckOutUITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        OfficeConfig.objects.create(
            qr_code='OFFICE-QR-4', daily_required_hours=Decimal('6.00'),
            check_in_deadline=time(10, 15), min_checkout_time_floor=time(16, 0))
        cls.employee = make_employee(
            'portal_force', 'EMPX06',
            custom_checkout_time_floor=time(18, 30),
            custom_required_hours=Decimal('5.00'))

    def setUp(self):
        self.client.login(username='portal_force', password='pw-123456')

    def test_early_in_the_day_the_page_offers_the_early_exit_button(self):
        Attendance.objects.create(
            employee=self.employee, date=timezone.localdate(),
            check_in=timezone.now() - timedelta(minutes=30),
            required_hours=Decimal('5.00'), is_remote=True)
        res = self.client.get(reverse('staff:attendance'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'id="sfForceCheckOut"')
        self.assertContains(res, 'Leaving early — check out anyway')

    def test_page_shows_this_persons_own_timing(self):
        res = self.client.get(reverse('staff:attendance'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Custom shift')
        self.assertContains(res, '06:30 PM')

    def test_recorded_reason_is_shown_back_after_an_early_exit(self):
        Attendance.objects.create(
            employee=self.employee, date=timezone.localdate(),
            check_in=timezone.now() - timedelta(hours=2),
            check_out=timezone.now(), required_hours=Decimal('5.00'),
            worked_hours=Decimal('2.00'), pending_hours=Decimal('3.00'),
            is_force_checkout=True, force_checkout_reason='Family emergency',
            is_remote=True)
        res = self.client.get(reverse('staff:attendance'))
        self.assertContains(res, 'Family emergency')
        # The day is closed, so the button itself is gone (its handler still
        # ships in the shared script block).
        self.assertNotContains(res, 'Leaving early — check out anyway')


class HRTimingFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hr = User.objects.create_user(username='hr_timing', password='pw-123456',
                                          is_staff=True)
        cls.employee = make_employee('hr_target', 'EMPX07')

    def setUp(self):
        self.client.force_login(self.hr)

    def post_edit(self, **extra):
        body = {
            'action': 'edit_info',
            'first_name': 'Target', 'last_name': '', 'email': '',
            'employment_type': 'intern', 'role': 'intern',
            'department': 'marketing', 'designation': '', 'status': 'active',
            'phone': '', 'emergency_contact': '', 'address': '',
            'joining_date': '', 'monthly_salary': '', 'hourly_rate': '',
        }
        body.update(extra)
        return self.client.post(
            reverse('emp_employee_detail', args=[self.employee.pk]), body)

    def test_hr_can_set_a_flexible_shift(self):
        self.post_edit(custom_check_in_deadline='12:00',
                       custom_checkout_time_floor='18:30',
                       custom_required_hours='4.5')
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.custom_check_in_deadline, time(12, 0))
        self.assertEqual(self.employee.custom_checkout_time_floor, time(18, 30))
        self.assertEqual(self.employee.custom_required_hours, Decimal('4.50'))

    def test_clearing_the_boxes_returns_the_person_to_the_office_default(self):
        self.employee.custom_check_in_deadline = time(12, 0)
        self.employee.custom_required_hours = Decimal('4.50')
        self.employee.save()
        self.post_edit(custom_check_in_deadline='',
                       custom_checkout_time_floor='',
                       custom_required_hours='')
        self.employee.refresh_from_db()
        self.assertIsNone(self.employee.custom_check_in_deadline)
        self.assertIsNone(self.employee.custom_required_hours)
        self.assertFalse(self.employee.has_custom_timing)
