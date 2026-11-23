from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import AMCContract, Client, Project


class PortalProjectTabsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('agc', 'design@agc.example', 'portal-pass-1')
        self.client_obj = Client.objects.create(name='AGC', email='design@agc.example', user=self.user)
        self.project = Project.objects.create(client=self.client_obj, name='Corporate Site', final_amount=Decimal('110000'))
        self.amc = AMCContract.objects.create(
            project=self.project, annual_amount=Decimal('15000'), included_in_project=True,
            start_date=date(2026, 11, 23), end_date=date(2027, 11, 22), next_due_date=date(2027, 11, 22))

    def test_login_by_email_and_project_tabs(self):
        resp = self.client.post(reverse('client_portal:portal_login'),
                                {'username': 'design@agc.example', 'password': 'portal-pass-1'})
        self.assertEqual(resp.status_code, 302)
        html = self.client.get(reverse('client_portal:portal_project_detail', args=[self.project.pk])).content.decode()
        for text in ('tab-invoices', 'tab-amc', 'tab-signoffs', 'Included in project', self.amc.reference):
            self.assertIn(text, html)
        page = self.client.get(reverse('client_portal:portal_amc_agreement', args=[self.amc.pk]))
        self.assertContains(page, 'included in the project fee')

    def test_other_clients_amc_is_hidden(self):
        other = User.objects.create_user('other', 'o@example.com', 'portal-pass-2')
        Client.objects.create(name='Other', email='o@example.com', user=other)
        self.client.force_login(other)
        resp = self.client.get(reverse('client_portal:portal_amc_agreement', args=[self.amc.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_staff_sets_chosen_portal_password(self):
        staff = User.objects.create_superuser('boss', 'b@example.com', 'pw')
        self.client.force_login(staff)
        self.client.post(reverse('client_portal_reset_password', args=[self.client_obj.pk]), {'password': 'Agc@123!#x'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Agc@123!#x'))
