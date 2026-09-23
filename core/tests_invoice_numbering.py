"""GST and no-GST invoices are numbered in separate series, so the GST series
the return is filed from never has gaps."""
from decimal import Decimal
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from .models import Client, CompanySettings, Invoice, Payment


class SeriesSetup(TestCase):
    def setUp(self):
        s = CompanySettings.get_settings()
        s.invoice_prefix, s.invoice_starting_number = 'INV', 201
        s.non_gst_invoice_prefix, s.non_gst_invoice_starting_number = 'NG', 1
        s.save()
        self.client_obj = Client.objects.create(name='Acme Ltd')

    def make(self, tax='18', **kwargs):
        return Invoice.objects.create(client=self.client_obj, title='Work', tax_rate=Decimal(tax), **kwargs)


class InvoiceSeriesTests(SeriesSetup):
    def test_no_gst_invoice_does_not_consume_a_gst_number(self):
        a = self.make()
        b = self.make(tax='0')
        c = self.make()
        d = self.make(gst_filing_status='not_applicable')
        self.assertEqual([a.invoice_number, c.invoice_number], ['INV201', 'INV202'])
        self.assertEqual([b.invoice_number, d.invoice_number], ['NG1', 'NG2'])

    def test_switching_to_no_gst_moves_the_invoice_to_the_no_gst_series(self):
        inv = self.make()
        inv.gst_filing_status = 'not_applicable'
        inv.save(update_fields=['gst_filing_status'])
        inv.refresh_from_db()
        self.assertEqual(inv.invoice_number, 'NG1')
        self.assertEqual(inv.renumbered_from, 'INV201')

    def test_switching_back_to_gst_takes_the_next_gst_number(self):
        self.make()
        inv = self.make(tax='0')
        inv.tax_rate = Decimal('18')
        inv.save()
        self.assertEqual(inv.invoice_number, 'INV202')

    def test_moving_an_older_invoice_out_closes_the_gst_gap(self):
        a, b, c, d = self.make(), self.make(), self.make(), self.make()
        b.gst_filing_status = 'not_applicable'
        b.save(update_fields=['gst_filing_status'])
        nums = [Invoice.all_objects.get(pk=i.pk).invoice_number for i in (a, b, c, d)]
        self.assertEqual(nums, ['INV201', 'NG1', 'INV202', 'INV203'])
        self.assertEqual(Invoice.all_objects.get(pk=c.pk).renumbered_from, 'INV203')
        self.assertEqual(self.make().invoice_number, 'INV204')

    def test_moving_back_to_gst_closes_the_no_gst_gap(self):
        x, y = self.make(tax='0'), self.make(tax='0')
        x.tax_rate = Decimal('18')
        x.save()
        self.assertEqual(Invoice.all_objects.get(pk=y.pk).invoice_number, 'NG1')
        self.assertEqual(x.invoice_number, 'INV201')

    def test_blocked_when_a_later_gst_invoice_is_filed(self):
        a, b = self.make(), self.make()
        Invoice.all_objects.filter(pk=b.pk).update(gst_filing_status='filed')
        a.gst_filing_status = 'not_applicable'
        with self.assertRaises(ValidationError):
            a.save(update_fields=['gst_filing_status'])
        self.assertEqual(Invoice.all_objects.get(pk=a.pk).invoice_number, 'INV201')
        self.assertEqual(Invoice.all_objects.get(pk=b.pk).invoice_number, 'INV202')

    def test_blocked_when_the_invoice_itself_is_filed(self):
        a = self.make(gst_filing_status='filed')
        a.gst_filing_status = 'not_applicable'
        with self.assertRaises(ValidationError):
            a.save()

    def test_web_gst_status_change_shows_error_instead_of_crashing(self):
        user = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        a, b = self.make(), self.make()
        Invoice.all_objects.filter(pk=b.pk).update(gst_filing_status='filed')
        r = self.client.post(reverse('invoice_set_gst_status', args=[a.pk]),
                             {'gst_filing_status': 'not_applicable'}, follow=True)
        self.assertContains(r, 'already filed in GSTR')
        self.assertEqual(Invoice.all_objects.get(pk=a.pk).gst_filing_status, 'pending')

    def test_hand_typed_numbers_are_left_alone(self):
        inv = self.make(invoice_number='SPECIAL-7')
        inv.tax_rate = Decimal('0')
        inv.save()
        self.assertEqual(inv.invoice_number, 'SPECIAL-7')

    def legacy_no_gst(self):
        """Invoices as they were before the series split: a no-GST invoice
        holding a GST number, with GST invoices after it."""
        a, b, c = self.make(), self.make(), self.make()
        Invoice.all_objects.filter(pk=b.pk).update(tax_rate=Decimal('0'))
        return a, Invoice.all_objects.get(pk=b.pk), c

    def test_saving_a_legacy_no_gst_invoice_keeps_every_number(self):
        a, b, c = self.legacy_no_gst()
        b.title = 'Edited'
        b.save()
        nums = [Invoice.all_objects.get(pk=i.pk).invoice_number for i in (a, b, c)]
        self.assertEqual(nums, ['INV201', 'INV202', 'INV203'])

    def test_paying_a_legacy_no_gst_invoice_keeps_every_number(self):
        a, b, c = self.legacy_no_gst()
        Invoice.all_objects.filter(pk=c.pk).update(gst_filing_status='filed')
        Payment.all_objects.create(invoice=b, amount=Decimal('100'))
        nums = [Invoice.all_objects.get(pk=i.pk).invoice_number for i in (a, b, c)]
        self.assertEqual(nums, ['INV201', 'INV202', 'INV203'])

    def test_settings_reject_overlapping_prefixes(self):
        user = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        self.client.post(reverse('settings'), {'invoice_prefix': 'INV', 'non_gst_invoice_prefix': 'INV2'})
        self.assertEqual(CompanySettings.get_settings().non_gst_invoice_prefix, 'NG')


class RenumberCommandTests(SeriesSetup):
    def run_cmd(self, *args):
        out = StringIO()
        call_command('renumber_invoices', *args, stdout=out)
        return out.getvalue()

    def legacy(self):
        # Invoices numbered before the split: one shared series with no-GST ones mixed in.
        rows = [('INV201', '18'), ('INV202', '0'), ('INV203', '18'), ('INV204', '0'), ('INV205', '18')]
        invs = {}
        for n, t in rows:
            inv = self.make(tax=t)
            Invoice.all_objects.filter(pk=inv.pk).update(invoice_number=n)  # bypass save(): it would split them
            invs[n] = inv
        return invs

    def numbers(self, invs):
        return {old: Invoice.all_objects.get(pk=i.pk).invoice_number for old, i in invs.items()}

    def test_dry_run_changes_nothing(self):
        invs = self.legacy()
        out = self.run_cmd()
        self.assertIn('Dry run', out)
        self.assertEqual(self.numbers(invs), {n: n for n in invs})

    def test_apply_closes_gst_gaps_and_moves_no_gst(self):
        invs = self.legacy()
        self.run_cmd('--apply')
        self.assertEqual(self.numbers(invs), {
            'INV201': 'INV201', 'INV202': 'NG1', 'INV203': 'INV202', 'INV204': 'NG2', 'INV205': 'INV203',
        })
        self.assertEqual(Invoice.all_objects.get(pk=invs['INV203'].pk).renumbered_from, 'INV203')
        self.assertEqual(self.make().invoice_number, 'INV204')
        self.assertEqual(self.make(tax='0').invoice_number, 'NG3')

    def test_refuses_to_renumber_filed_invoices(self):
        invs = self.legacy()
        Invoice.all_objects.filter(pk=invs['INV205'].pk).update(gst_filing_status='filed')
        with self.assertRaises(CommandError):
            self.run_cmd('--apply')
        self.assertEqual(self.numbers(invs), {n: n for n in invs})

    def test_earlier_fy_prefixes_are_untouched(self):
        old = self.make(tax='0', invoice_number='OLD-9')
        self.legacy()
        self.run_cmd('--apply')
        old.refresh_from_db()
        self.assertEqual(old.invoice_number, 'OLD-9')


class ReceiptDownloadTests(TestCase):
    def test_invoice_page_links_receipt_download(self):
        user = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        inv = Invoice.objects.create(client=Client.objects.create(name='Acme'), title='Work', tax_rate=Decimal('18'))
        pay = Payment.objects.create(invoice=inv, amount=Decimal('100'))
        page = self.client.get(reverse('invoice_detail', args=[inv.pk])).content.decode()
        self.assertIn(reverse('payment_receipt', args=[pay.pk]) + '?download=1', page)

    def test_receipt_download_returns_a_pdf(self):
        user = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        inv = Invoice.objects.create(client=Client.objects.create(name='Acme'), title='Work', tax_rate=Decimal('18'))
        pay = Payment.objects.create(invoice=inv, amount=Decimal('100'))
        try:
            import weasyprint  # noqa: F401
        except (ImportError, OSError):
            self.skipTest('WeasyPrint system libraries not available')
        r = self.client.get(reverse('payment_receipt', args=[pay.pk]) + '?download=1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))


class NonGstLedgerTests(SeriesSetup):
    """No-GST invoices sit in their own ledger and never reach a total."""

    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.gst = self.make()
        self.gst.total_amount = Decimal('1180')
        self.gst.save()
        self.ng = self.make(tax='0')
        self.ng.total_amount = Decimal('500')
        self.ng.save()
        Payment.objects.create(invoice=self.gst, amount=Decimal('1180'))
        Payment.objects.create(invoice=self.ng, amount=Decimal('500'))

    def test_default_managers_only_see_gst(self):
        self.assertEqual(list(Invoice.objects.all()), [self.gst])
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Invoice.all_objects.count(), 2)
        self.assertEqual(Payment.all_objects.count(), 2)
        self.assertEqual(list(self.client_obj.invoices.all()), [self.gst])

    def test_no_gst_payment_still_marks_its_invoice_paid(self):
        self.ng.refresh_from_db()
        self.assertEqual(self.ng.amount_paid, Decimal('500'))
        self.assertEqual(self.ng.status, 'paid')

    def test_revenue_report_leaves_out_no_gst(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('payment_list'))
        self.assertNotContains(r, self.ng.invoice_number + '<')
        self.assertContains(r, self.gst.invoice_number)

    def test_invoice_list_hides_no_gst(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('invoice_list'))
        self.assertContains(r, self.gst.invoice_number)
        self.assertNotContains(r, self.ng.invoice_number + '<')

    def test_ledger_shows_only_no_gst_with_its_totals(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('non_gst_ledger'))
        self.assertContains(r, self.ng.invoice_number)
        self.assertNotContains(r, self.gst.invoice_number + '<')
        self.assertEqual(r.context['total_invoiced'], Decimal('500'))
        self.assertEqual(r.context['total_received'], Decimal('500'))

    def test_ledger_is_owner_only(self):
        staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client.force_login(staff)
        r = self.client.get(reverse('non_gst_ledger'))
        self.assertRedirects(r, reverse('invoice_list'), fetch_redirect_response=False)

    def test_no_gst_invoice_page_still_opens_with_its_payment(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('invoice_detail', args=[self.ng.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'No-GST series')
        self.assertContains(r, '500.00')

    def test_client_delete_guard_counts_no_gst_invoices(self):
        other = Client.objects.create(name='Only no-GST')
        Invoice.objects.create(client=other, title='x', tax_rate=Decimal('0'))
        self.client.force_login(self.owner)
        self.client.post(reverse('client_delete', args=[other.pk]))
        self.assertTrue(Client.objects.filter(pk=other.pk).exists())


class InvoiceListOrderTests(SeriesSetup):
    def test_list_runs_by_number_highest_first(self):
        from datetime import date
        owner = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.client.force_login(owner)
        dates = {'INRT-9': date(2026, 6, 16), 'INRT-10': date(2026, 6, 18), 'INRT-15': date(2026, 7, 11),
                 'INRT-16': date(2026, 5, 7), 'INV2425-40': date(2025, 3, 30)}
        for number, issued in dates.items():
            self.make(invoice_number=number, issue_date=issued)
        r = self.client.get(reverse('invoice_list'))
        self.assertEqual([i.invoice_number for i in r.context['invoices']],
                         ['INRT-16', 'INRT-15', 'INRT-10', 'INRT-9', 'INV2425-40'])
