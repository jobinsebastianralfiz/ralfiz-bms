from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from employees.models import Employee


class InternPageTests(TestCase):
    """Interns moved from crm.InternProfile (int pk) to employees.Employee (uuid pk)."""

    def setUp(self):
        self.admin = User.objects.create_superuser('boss', password='pw')
        self.client.force_login(self.admin)
        self.intern_user = User.objects.create_user('anu', first_name='Anu', last_name='K')
        self.intern = Employee.objects.create(
            user=self.intern_user,
            employee_id='EMP900',
            employment_type='intern',
            role='intern',
            intern_type='digital',
        )

    def test_list_renders_when_intern_has_no_supervisor(self):
        self.assertIsNone(self.intern.supervisor)
        resp = self.client.get(reverse('crm:intern_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Anu K')

    def test_list_shows_supervisor_when_set(self):
        self.intern.supervisor = self.admin
        self.intern.save()
        resp = self.client.get(reverse('crm:intern_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'boss')

    def test_detail_and_edit_reverse_with_uuid_pk(self):
        for name in ('crm:intern_profile_detail', 'crm:intern_profile_edit'):
            url = reverse(name, kwargs={'pk': self.intern.pk})
            self.assertIn(str(self.intern.pk), url)
            self.assertEqual(self.client.get(url).status_code, 200)
