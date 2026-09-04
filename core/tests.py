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
