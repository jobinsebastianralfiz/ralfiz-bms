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


class LeadListPageTests(TestCase):
    def setUp(self):
        from crm.models import Lead
        self.admin = User.objects.create_superuser('boss', password='pw')
        self.intern_user = User.objects.create_user('anu', first_name='Anu', last_name='K')
        Employee.objects.create(user=self.intern_user, employee_id='EMP901', employment_type='intern',
                                role='intern', intern_type='digital')
        Lead.objects.create(contact_person='New One', phone='900000001', created_by=self.admin)
        Lead.objects.create(contact_person='Won', phone='900000002', status='converted', created_by=self.admin)
        Lead.objects.create(contact_person='Chasing', phone='900000003', status='follow_up',
                            assigned_to=self.intern_user, created_by=self.intern_user)
        Lead.objects.create(contact_person='Gone', phone='900000004', status='lost', created_by=self.admin)

    def test_stats_and_chart_for_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('crm:lead_list'))
        self.assertEqual(r.status_code, 200)
        stats = r.context['stats']
        self.assertEqual((stats['total'], stats['new'], stats['converted'], stats['in_progress'], stats['lost']),
                         (4, 1, 1, 1, 1))
        self.assertEqual(stats['conversion'], 25)
        self.assertEqual(len(r.context['chart']['bars']), 30)
        self.assertEqual(r.context['chart']['total'], 4)
        today = r.context['chart']['bars'][-1]
        self.assertEqual(dict(today['people']), {'boss': 3, 'Anu K': 1})

    def test_intern_sees_only_assigned_leads(self):
        self.client.force_login(self.intern_user)
        r = self.client.get(reverse('crm:lead_list'), {'range': '7'})
        self.assertEqual(r.context['stats']['total'], 1)
        self.assertEqual(len(r.context['chart']['bars']), 7)
        self.assertEqual([lead.contact_person for lead in r.context['leads']], ['Chasing'])

    def test_export_follows_filters(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('crm:lead_export'), {'status': 'lost'})
        self.assertEqual(r['Content-Type'], 'text/csv')
        rows = r.content.decode().strip().splitlines()
        self.assertEqual(len(rows), 2)
        self.assertIn('Gone', rows[1])

    def test_intern_export_is_scoped(self):
        self.client.force_login(self.intern_user)
        rows = self.client.get(reverse('crm:lead_export')).content.decode().strip().splitlines()
        self.assertEqual(len(rows), 2)
        self.assertIn('Chasing', rows[1])
