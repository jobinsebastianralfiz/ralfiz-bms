"""Phase 2 connector tools: clients, projects, quotes, GST invoices, payments,
expenses, AMC payments and PDF links -- each against the real owner view."""

from datetime import date, timedelta
from decimal import Decimal
from unittest import mock
from urllib.parse import urlparse

from django.core import signing
from django.test import TestCase

from connector import files
from core.models import (AMCContract, AMCPayment, Client, CompanySettings, Expense, Invoice, Payment,
                         Project, Quote)
from crm.models import Lead
from employees.models import Employee

from .test_connector import MCPClientMixin, make_employee, make_token


class MoneyToolTests(MCPClientMixin, TestCase):
    def setUp(self):
        self.owner = make_employee('owner', 'owner')
        self.token = make_token(self.owner)
        # Saved and re-read, as in production: the rate is then Decimal('18.00'),
        # not the int default, and travels to the view as a string.
        CompanySettings.get_settings().save()
        self.client_rec = Client.objects.create(name='Ajith Kumar', company_name='Ajith Traders')
        self.project = Project.objects.create(client=self.client_rec, name='Patient Portal',
                                              project_type='web_app', status='in_progress')

    def make_invoice(self, **extra):
        data = self.ok('create_invoice', {
            'client_id': str(self.client_rec.id), 'project_id': str(self.project.id),
            'title': 'Website build',
            'items': [{'description': 'Design', 'unit_price': 10000},
                      {'description': 'Hosting', 'quantity': 2, 'unit_price': '2,500.50'}],
            **extra,
        })
        return Invoice.objects.get(pk=data['id'])

    # ---------------------------------------------------------- clients / projects

    def test_create_client_then_project(self):
        created = self.ok('create_client', {'name': 'Riya', 'company_name': 'Riya Foods',
                                            'phone': '9000000009'})
        project = self.ok('create_project', {'client_id': created['id'], 'name': 'Food app',
                                             'project_type': 'mobile_app', 'final_amount': 85000})
        self.assertEqual(project['name'], 'Food app')
        self.assertEqual(Project.objects.get(name='Food app').final_amount, Decimal('85000'))

    def test_create_project_for_unknown_client_is_explained(self):
        is_error, message = self.call('create_project', {
            'client_id': '00000000-0000-0000-0000-000000000000', 'name': 'X'})
        self.assertTrue(is_error)
        self.assertIn('No client with that id', message)

    # ---------------------------------------------------------- invoices

    def test_create_invoice_is_gst_with_totals(self):
        invoice = self.make_invoice()
        self.assertTrue(invoice.is_gst)
        self.assertEqual(invoice.tax_rate, Decimal('18'))  # company default
        self.assertEqual(invoice.subtotal, Decimal('15001.00'))
        self.assertEqual(invoice.total_amount, Decimal('17701.18'))
        self.assertTrue(invoice.invoice_number)

    def test_explicit_fractional_tax_rate(self):
        invoice = self.make_invoice(tax_rate=12.5, discount='1.00')
        self.assertTrue(invoice.is_gst)
        self.assertEqual(invoice.total_amount, Decimal('16875.00'))

    def test_invoice_without_gst_is_refused(self):
        is_error, message = self.call('create_invoice', {
            'client_id': str(self.client_rec.id), 'title': 'X', 'tax_rate': 0,
            'items': [{'description': 'A', 'unit_price': 1}]})
        self.assertTrue(is_error)
        self.assertEqual(Invoice.all_objects.count(), 0)

    def test_invoice_project_must_belong_to_client(self):
        other = Client.objects.create(name='Someone else')
        is_error, message = self.call('create_invoice', {
            'client_id': str(other.id), 'project_id': str(self.project.id), 'title': 'X',
            'items': [{'description': 'A', 'unit_price': 1}]})
        self.assertTrue(is_error)
        self.assertIn('belongs to another client', message)

    def test_bad_items_are_explained(self):
        for items, expected in (([], 'at least one'),
                                ([{'description': 'A'}], 'unit_price'),
                                ([{'description': 'A', 'unit_price': 'lots'}], 'must be a number'),
                                ([{'description': 'A', 'unit_price': 5, 'qty': 1}], 'unknown field')):
            is_error, message = self.call('create_invoice', {
                'client_id': str(self.client_rec.id), 'title': 'X', 'items': items})
            self.assertTrue(is_error, items)
            self.assertIn(expected, message)

    # ---------------------------------------------------------- payments

    def test_record_payment_updates_invoice(self):
        invoice = self.make_invoice()
        result = self.ok('record_payment', {'invoice_id': str(invoice.id), 'amount': 7000,
                                            'payment_method': 'upi', 'transaction_id': 'UTR1'})
        self.assertEqual(result['invoice_status'], 'partial')
        payment = Payment.objects.get()
        self.assertEqual(payment.payment_date, date.today())
        self.ok('record_payment', {'invoice_id': str(invoice.id), 'amount': '10701.18'})
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')

    def test_overpayment_needs_confirmation(self):
        invoice = self.make_invoice()
        is_error, message = self.call('record_payment', {'invoice_id': str(invoice.id),
                                                         'amount': 50000})
        self.assertTrue(is_error)
        self.assertIn('left to pay', message)
        self.assertEqual(Payment.all_objects.count(), 0)
        self.ok('record_payment', {'invoice_id': str(invoice.id), 'amount': 50000,
                                   'allow_overpayment': True})

    def test_no_gst_ledger_is_unreachable(self):
        hidden = Invoice.all_objects.create(client=self.client_rec, title='Cash job', tax_rate=0)
        for name, args in (('record_payment', {'invoice_id': str(hidden.id), 'amount': 100}),
                           ('get_invoice_pdf', {'invoice_id': str(hidden.id)})):
            is_error, message = self.call(name, args)
            self.assertTrue(is_error, name)
            self.assertIn('No GST invoice', message)

    def test_payment_route_works_for_the_app_too(self):
        # The app posts to owner/invoices/<id>/payments/; the view used to
        # crash on the route's pk argument.
        from rest_framework.test import APIClient
        invoice = self.make_invoice()
        api = APIClient()
        api.force_authenticate(self.owner)
        response = api.post(f'/api/employees/owner/invoices/{invoice.id}/payments/',
                            {'amount': '100'}, format='json')
        self.assertEqual(response.status_code, 201, response.content)

    # ---------------------------------------------------------- quotes

    def test_quote_for_lead_then_update(self):
        lead = Lead.objects.create(contact_person='Asha', phone='9000000001', created_by=self.owner)
        quote = self.ok('create_quote', {'lead_id': lead.id, 'title': 'Bakery site',
                                         'items': [{'description': 'Site', 'unit_price': 20000}]})
        self.assertEqual(Decimal(str(quote['total_amount'])), Decimal('23600'))
        self.assertEqual(quote['valid_until'], (date.today() + timedelta(days=30)).isoformat())

        updated = self.ok('update_quote', {'quote_id': quote['id'], 'status': 'sent',
                                           'items': [{'description': 'Site', 'unit_price': 15000}],
                                           'tax_rate': 0})
        self.assertEqual(updated['status'], 'sent')
        self.assertEqual(Quote.objects.get().total_amount, Decimal('15000'))

    def test_quote_needs_client_or_lead(self):
        is_error, message = self.call('create_quote', {
            'title': 'X', 'items': [{'description': 'A', 'unit_price': 1}]})
        self.assertTrue(is_error)
        self.assertIn('client_id', message)

    # ---------------------------------------------------------- expenses / AMC

    def test_add_expense_defaults_to_today(self):
        self.ok('add_expense', {'amount': 899, 'vendor': 'Hostinger', 'category': 'software',
                                'project_id': str(self.project.id)})
        expense = Expense.objects.get()
        self.assertEqual((expense.date, expense.amount, expense.project), (date.today(), Decimal('899'), self.project))

    def test_amc_payment_defaults_period_and_advances_due_date(self):
        amc = AMCContract.objects.create(
            project=self.project, contract_type='amc', annual_amount=12000,
            billing_cycle='yearly', start_date=date(2026, 1, 1), end_date=date(2030, 12, 31),
            next_due_date=date(2026, 1, 1))
        result = self.ok('record_amc_payment', {'amc_id': str(amc.id), 'amount': 12000})
        payment = AMCPayment.objects.get()
        self.assertEqual((payment.period_start, payment.period_end), (date(2026, 1, 1), date(2026, 12, 31)))
        self.assertEqual(result['next_due_date'], '2027-01-01')

    # ---------------------------------------------------------- PDF links

    def test_invoice_pdf_link_downloads(self):
        invoice = self.make_invoice()
        link = self.ok('get_invoice_pdf', {'invoice_id': str(invoice.id)})
        path = urlparse(link['download_url']).path
        with mock.patch('employees.views.OwnerInvoicePDFView.get', autospec=True) as get:
            from django.http import HttpResponse
            get.return_value = HttpResponse(b'%PDF-1.7', content_type='application/pdf')
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'%PDF-1.7')
        request = get.call_args.args[1]
        self.assertEqual(request.query_params['gst'], '1')
        self.assertEqual(request.user, self.owner)

    def test_pdf_link_is_tamper_proof_expires_and_follows_access(self):
        invoice = self.make_invoice()
        path = urlparse(self.ok('get_invoice_pdf', {'invoice_id': str(invoice.id)})['download_url']).path
        self.assertEqual(self.client.get(path[:-6] + 'xxxxx/').status_code, 404)

        with mock.patch.object(files, 'PDF_LINK_MAX_AGE', -1):
            self.assertEqual(self.client.get(path).status_code, 410)

        Employee.objects.filter(user=self.owner).update(role='employee')
        self.assertEqual(self.client.get(path).status_code, 403)

    def test_quote_pdf_link(self):
        quote = Quote.objects.create(client=self.client_rec, title='Q', valid_until=date(2030, 1, 1))
        link = self.ok('get_quote_pdf', {'quote_id': str(quote.id)})
        token = urlparse(link['download_url']).path.rstrip('/').rsplit('/', 1)[1]
        claim = signing.loads(token, salt=files.SALT)
        self.assertEqual((claim['k'], claim['g']), ('quote', False))

    # ---------------------------------------------------------- permissions

    def test_read_only_token_cannot_move_money(self):
        invoice = self.make_invoice()
        read_only = make_token(self.owner, scope='bms:read')
        is_error, message = self.call('record_payment', {'invoice_id': str(invoice.id), 'amount': 1},
                                      token=read_only.token)
        self.assertTrue(is_error)
        self.assertIn('reading only', message)
        # PDF links are reads.
        self.assertFalse(self.call('get_invoice_pdf', {'invoice_id': str(invoice.id)},
                                   token=read_only.token)[0])
