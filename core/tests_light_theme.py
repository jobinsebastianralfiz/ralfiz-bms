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


class ProjectListPageTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        from .models import Project
        self.user = User.objects.create_superuser('boss', 'b@x.com', 'pw')
        self.client.force_login(self.user)
        c = Client.objects.create(name='Acme')
        today = timezone.now().date()
        Project.objects.create(client=c, name='Late One', status='in_progress',
                               deadline=today - timedelta(days=3))
        Project.objects.create(client=c, name='On Time', status='in_progress',
                               deadline=today + timedelta(days=10))
        Project.objects.create(client=c, name='Shipped', status='completed',
                               deadline=today - timedelta(days=30))
        Project.objects.create(client=c, name='Maybe', status='lead')

    def test_stat_cards_and_panels(self):
        r = self.client.get(reverse('project_list'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['stats'],
                         {'count': 4, 'active': 2, 'completed': 1, 'overdue': 1, 'pipeline': 1})
        self.assertEqual([p.name for p in r.context['upcoming_deadlines']], ['Late One', 'On Time'])
        self.assertContains(r, 'Project Status')

    def test_overdue_quick_filter_skips_completed(self):
        r = self.client.get(reverse('project_list'), {'quick': 'overdue'})
        self.assertEqual([p.name for p in r.context['projects']], ['Late One'])

    def test_pipeline_quick_filter(self):
        r = self.client.get(reverse('project_list'), {'quick': 'pipeline'})
        self.assertEqual([p.name for p in r.context['projects']], ['Maybe'])


class ClientDetailPageTests(TestCase):
    """The client page used to read total_revenue / pending_amount /
    credentials_count from the context without the view ever setting them,
    so it always showed zero."""

    def setUp(self):
        from .models import Credential, Payment, Project
        self.user = User.objects.create_superuser('boss', 'b@x.com', 'pw')
        self.client.force_login(self.user)
        self.c = Client.objects.create(name='Acme', email='a@acme.test')
        project = Project.objects.create(client=self.c, name='Site')
        Credential.objects.create(project=project, name='Admin')
        inv = Invoice.objects.create(client=self.c, project=project, title='Build',
                                     issue_date=date(2026, 3, 1), due_date=date(2026, 3, 15),
                                     total_amount=Decimal('1000'), tax_rate=Decimal('18'), status='partial', amount_paid=Decimal('0'))
        Payment.objects.create(invoice=inv, amount=Decimal('400'), payment_date=date(2026, 3, 5),
                               payment_method='upi')

    def test_money_and_counts_reach_the_page(self):
        r = self.client.get(reverse('client_detail', args=[self.c.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['total_revenue'], Decimal('400'))
        self.assertEqual(r.context['pending_amount'], Decimal('600'))
        self.assertEqual(r.context['credentials_count'], 1)

    def test_activity_is_newest_first(self):
        r = self.client.get(reverse('client_detail', args=[self.c.pk]))
        whens = [e['when'] for e in r.context['client_activity']]
        self.assertEqual(whens, sorted(whens, reverse=True))
        self.assertTrue(any(e['kind'] == 'payment' for e in r.context['client_activity']))


class ClientListPageTests(TestCase):
    def setUp(self):
        from .models import Project
        self.client.force_login(User.objects.create_superuser('boss', 'b@x.com', 'pw'))
        a = Client.objects.create(name='A', email='a@x.test', priority='high')
        Client.objects.create(name='B', email='b@x.test', is_active=False)
        Project.objects.create(client=a, name='P1')
        Project.objects.create(client=a, name='P2')

    def test_stats_and_project_counts(self):
        r = self.client.get(reverse('client_list'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['stats'],
                         {'total': 2, 'new_this_month': 2, 'active': 1, 'inactive': 1, 'high': 1})
        counts = {c.name: c.project_count for c in r.context['clients']}
        self.assertEqual(counts, {'A': 2, 'B': 0})


class RecordPaymentFlowTests(TestCase):
    """Recording a payment used to land back on the invoice with no receipt in
    sight, and "Record Payment" from an invoice did not preselect it."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('boss', 'b@x.com', 'pw'))
        c = Client.objects.create(name='Acme', email='a@acme.test')
        self.inv = Invoice.objects.create(client=c, title='Build', issue_date=date(2026, 3, 1),
                                          due_date=date(2026, 3, 15), total_amount=Decimal('1000'),
                                          tax_rate=Decimal('18'), status='sent')

    def test_invoice_is_preselected(self):
        r = self.client.get(reverse('payment_create'), {'invoice': str(self.inv.pk)})
        self.assertContains(r, f'value="{self.inv.pk}"')
        self.assertRegex(r.content.decode(), rf'value="{self.inv.pk}"[^>]*selected')

    def test_recording_opens_the_receipt(self):
        from .models import Payment
        r = self.client.post(reverse('payment_create'), {
            'invoice': str(self.inv.pk), 'amount': '400', 'payment_date': '2026-03-05',
            'payment_method': 'upi', 'transaction_id': 'T1',
        })
        payment = Payment.all_objects.get(transaction_id='T1')
        self.assertRedirects(r, reverse('payment_receipt', args=[payment.pk]), fetch_redirect_response=False)
        page = self.client.get(reverse('payment_receipt', args=[payment.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'T1')
