from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from employees.models import AgreementRequest, Attendance, Employee


class EmployeeDeleteTests(TestCase):
    """AgreementRequest.employee is PROTECT, which used to 500 the delete view."""

    def setUp(self):
        self.admin = User.objects.create_superuser('boss', password='pw')
        self.client.force_login(self.admin)
        self.staff_user = User.objects.create_user('ravi', first_name='Ravi')
        self.employee = Employee.objects.create(
            user=self.staff_user,
            employee_id='EMP901',
            employment_type='intern',
            role='intern',
        )

    def _delete(self):
        return self.client.post(reverse('emp_employee_delete', args=[self.employee.pk]))

    def test_deletes_employee_holding_a_signed_agreement(self):
        AgreementRequest.objects.create(
            employee=self.employee,
            full_name='Ravi',
            status=AgreementRequest.STATUS_ACCEPTED,
        )
        resp = self._delete()
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Employee.objects.filter(pk=self.employee.pk).exists())
        self.assertFalse(AgreementRequest.objects.exists())

    def test_deletes_employee_with_pending_agreement_and_attendance(self):
        AgreementRequest.objects.create(employee=self.employee, full_name='Ravi')
        Attendance.objects.create(employee=self.employee, date='2026-09-01')
        self._delete()
        self.assertFalse(Employee.objects.filter(pk=self.employee.pk).exists())
        self.assertFalse(Attendance.objects.exists())

    def test_user_account_survives_the_delete(self):
        self._delete()
        self.assertTrue(User.objects.filter(pk=self.staff_user.pk).exists())

    def test_get_does_not_delete(self):
        self.client.get(reverse('emp_employee_delete', args=[self.employee.pk]))
        self.assertTrue(Employee.objects.filter(pk=self.employee.pk).exists())


class RevokedLoginTests(TestCase):
    """Deleting someone has to actually shut them out, not just tidy the HR list."""

    PASSWORD = 'lettherein123'

    def setUp(self):
        self.admin = User.objects.create_superuser('boss', password='pw')
        self.staff_user = User.objects.create_user('ravi', password=self.PASSWORD, first_name='Ravi')
        self.employee = Employee.objects.create(
            user=self.staff_user,
            employee_id='EMP902',
            employment_type='intern',
            role='intern',
        )

    def _delete_employee(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('emp_employee_delete', args=[self.employee.pk]))
        self.client.logout()

    def test_password_login_is_refused_after_the_delete(self):
        self.assertTrue(self.client.login(username='ravi', password=self.PASSWORD))
        self.client.logout()

        self._delete_employee()
        self.assertFalse(self.client.login(username='ravi', password=self.PASSWORD))

    def test_mobile_token_endpoint_refuses_the_account(self):
        url = reverse('employees:login')
        ok = self.client.post(url, {'username': 'ravi', 'password': self.PASSWORD})
        self.assertEqual(ok.status_code, 200)

        self._delete_employee()
        denied = self.client.post(url, {'username': 'ravi', 'password': self.PASSWORD})
        self.assertEqual(denied.status_code, 401)

    def test_an_access_token_issued_before_the_delete_stops_working(self):
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        token = str(RefreshToken.for_user(self.staff_user).access_token)
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(api.get(reverse('employees:profile')).status_code, 200)

        self._delete_employee()
        self.assertEqual(api.get(reverse('employees:profile')).status_code, 401)

    def test_a_live_staff_portal_session_is_signed_out(self):
        portal = self.client
        portal.login(username='ravi', password=self.PASSWORD)
        self._delete_employee()

        portal.login(username='ravi', password=self.PASSWORD)
        self.assertNotIn('_auth_user_id', portal.session)

    def test_the_account_survives_so_history_is_not_cascaded_away(self):
        self._delete_employee()
        self.staff_user.refresh_from_db()
        self.assertFalse(self.staff_user.is_active)
        self.assertFalse(self.staff_user.has_usable_password())


class RevokeOrphanLoginsCommandTests(TestCase):
    """Accounts orphaned by deletions made before the view revoked logins."""

    def _run(self, *args):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command('revoke_orphan_logins', *args, stdout=out)
        return out.getvalue()

    def test_dry_run_lists_but_does_not_revoke(self):
        orphan = User.objects.create_user('gone', password='pw')
        output = self._run()
        self.assertIn('gone', output)
        self.assertIn('Dry run', output)
        orphan.refresh_from_db()
        self.assertTrue(orphan.is_active)

    def test_apply_revokes_the_orphan(self):
        orphan = User.objects.create_user('gone', password='pw')
        self._run('--apply')
        orphan.refresh_from_db()
        self.assertFalse(orphan.is_active)

    def test_people_who_still_have_a_role_are_left_alone(self):
        keeper = User.objects.create_user('still_here', password='pw')
        Employee.objects.create(user=keeper, employee_id='EMP903', employment_type='fulltime')
        self._run('--apply')
        keeper.refresh_from_db()
        self.assertTrue(keeper.is_active)

    def test_staff_and_superusers_are_never_touched(self):
        boss = User.objects.create_superuser('boss', password='pw')
        self._run('--apply')
        boss.refresh_from_db()
        self.assertTrue(boss.is_active)

    def test_named_account_is_revoked_even_with_a_profile(self):
        leaver = User.objects.create_user('leaver', password='pw')
        Employee.objects.create(user=leaver, employee_id='EMP904', employment_type='intern')
        self._run('--username', 'leaver', '--apply')
        leaver.refresh_from_db()
        self.assertFalse(leaver.is_active)

    def test_named_superuser_is_refused(self):
        from django.core.management.base import CommandError
        User.objects.create_superuser('boss', password='pw')
        with self.assertRaises(CommandError):
            self._run('--username', 'boss', '--apply')
