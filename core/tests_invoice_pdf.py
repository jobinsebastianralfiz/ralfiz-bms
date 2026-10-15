"""Invoice PDF: the Billed By block and the no-GST payment account."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Client, CompanySettings, Invoice


class InvoicePdfTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('boss', 'b@x.com', 'pw')
        self.client.force_login(self.user)
        c = CompanySettings.get_settings()
        c.company_name = 'Ralfiz Technologies'
        c.address = 'KIMS Avenue\nPerinthalmanna'
        c.bank_name, c.bank_account_number, c.upi_id = 'Firm Bank', 'FIRM-111', 'firm@upi'
        c.account_holder_name = 'Ralfiz Technologies'
        c.save()
        self.company = c
        self.acme = Client.objects.create(name='Acme Ltd', address='Riyadh')

    def _pdf_html(self, tax_rate):
        inv = Invoice.objects.create(client=self.acme, title='Site', tax_rate=Decimal(tax_rate),
                                     total_amount=Decimal('1000'))
        return self.client.get(reverse('invoice_pdf', args=[inv.pk])).content.decode()

    def test_shows_who_billed_and_who_is_billed(self):
        html = self._pdf_html('18')
        self.assertIn('Billed By', html)
        self.assertIn('KIMS Avenue, Perinthalmanna', html)
        self.assertIn('Bill To', html)
        self.assertIn('Riyadh', html)

    def test_no_gst_invoice_uses_the_no_gst_account(self):
        c = self.company
        c.ng_account_holder_name, c.ng_bank_account_number, c.ng_upi_id = 'Jobin Sebastian', 'OWN-222', 'own@upi'
        c.save()
        html = self._pdf_html('0')
        self.assertIn('OWN-222', html)
        self.assertIn('Jobin Sebastian', html)
        self.assertNotIn('FIRM-111', html)

    def test_gst_invoice_keeps_the_firm_account(self):
        self.company.ng_bank_account_number = 'OWN-222'
        self.company.save()
        html = self._pdf_html('18')
        self.assertIn('FIRM-111', html)
        self.assertNotIn('OWN-222', html)

    def test_no_gst_invoice_falls_back_when_no_separate_account(self):
        self.assertIn('FIRM-111', self._pdf_html('0'))

    def test_settings_page_saves_the_no_gst_account(self):
        self.client.post(reverse('settings'), {
            'company_name': 'Ralfiz Technologies', 'account_holder_name': 'Ralfiz Technologies',
            'ng_bank_account_number': ' OWN-333 ', 'ng_account_holder_name': 'Jobin Sebastian'})
        c = CompanySettings.objects.get(pk=1)
        self.assertEqual(c.ng_bank_account_number, 'OWN-333')
        self.assertEqual(c.account_holder_name, 'Ralfiz Technologies')
