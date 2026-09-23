"""The light redesign: lakh-grouped amounts, the financial-year quick filter,
breadcrumbs that pages can finally set, and the invoice page's side panels."""
from datetime import date
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import Client, Invoice
from .templatetags.money import inr
from .views import _period_range


class InrFilterTests(SimpleTestCase):
    def test_groups_in_lakhs(self):
        self.assertEqual(inr(Decimal('598850')), '5,98,850.00')
        self.assertEqual(inr(Decimal('164556.34')), '1,64,556.34')
        self.assertEqual(inr(Decimal('10000000')), '1,00,00,000.00')
        self.assertEqual(inr(Decimal('999.5')), '999.50')
        self.assertEqual(inr(None), '0.00')
        self.assertEqual(inr(Decimal('-1500')), '-1,500.00')
        self.assertEqual(inr(Decimal('1234.5'), 0), '1,235')


class PeriodRangeTests(SimpleTestCase):
    def test_financial_year_runs_april_to_march(self):
        with mock.patch('datetime.date', wraps=date) as fake:
            fake.today.return_value = date(2026, 9, 23)
            self.assertEqual(_period_range('this_fy'), ('2026-04-01', '2027-03-31'))
            fake.today.return_value = date(2027, 2, 10)
            self.assertEqual(_period_range('this_fy'), ('2026-04-01', '2027-03-31'))
            self.assertEqual(_period_range('nonsense'), ('', ''))


class InvoicePageTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.client.force_login(owner)
        client = Client.objects.create(name='Acme Ltd')
        Invoice.objects.create(client=client, title='Site', tax_rate=Decimal('18'), total_amount=Decimal('118000'))
        Invoice.objects.create(client=client, title='Hidden', tax_rate=Decimal('0'), total_amount=Decimal('5000'))

    def test_breadcrumb_block_reaches_the_page(self):
        r = self.client.get(reverse('invoice_list'))
        self.assertContains(r, '<span class="breadcrumb-item active">Invoices</span>', html=True)

    def test_panels_count_only_gst_invoices(self):
        r = self.client.get(reverse('invoice_list'))
        self.assertEqual(r.context['stats']['count'], 1)
        self.assertEqual(r.context['stats']['total'], Decimal('118000'))
        self.assertContains(r, '1,18,000.00')
        self.assertNotContains(r, 'Hidden')
