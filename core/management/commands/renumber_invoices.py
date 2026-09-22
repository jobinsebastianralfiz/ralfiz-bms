"""Split the current financial year's invoices into a gap-free GST series and
a separate no-GST series.

Only invoices numbered in the current invoice prefix or the no-GST prefix are
touched; earlier financial years and hand-typed numbers are left alone.
Relative order is kept: invoices are sorted by their existing number, then by
creation time.

Dry run by default. Pass --apply to write.
"""
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import CompanySettings, Invoice


class Command(BaseCommand):
    help = 'Renumber this FY\'s invoices so GST invoices run without gaps and no-GST invoices get their own series.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Write the new numbers (default is a dry run).')
        parser.add_argument('--gst-start', type=int, help='First GST number (default: lowest number now in the series).')
        parser.add_argument('--non-gst-start', type=int, help='First no-GST number (default: the no-GST starting number in settings).')
        parser.add_argument('--allow-filed', action='store_true',
                            help='Also renumber invoices already marked "Filed in GSTR".')

    def handle(self, *args, **opts):
        settings = CompanySettings.get_settings()
        gst_prefix, ng_prefix = settings.invoice_prefix, settings.non_gst_invoice_prefix
        if gst_prefix.startswith(ng_prefix) or ng_prefix.startswith(gst_prefix):
            raise CommandError(f'Prefixes "{gst_prefix}" and "{ng_prefix}" overlap; change the no-GST prefix in Settings first.')

        in_scope = []
        for inv in Invoice.all_objects.all():
            gst_n = Invoice.series_number(inv.invoice_number, gst_prefix)
            ng_n = Invoice.series_number(inv.invoice_number, ng_prefix)
            if gst_n is not None or ng_n is not None:
                in_scope.append((inv, gst_n, ng_n))
        if not in_scope:
            self.stdout.write(f'No invoices numbered {gst_prefix}… or {ng_prefix}…. Nothing to do.')
            return

        gst_numbers = [g for _, g, _ in in_scope if g is not None]
        gst_start = opts['gst_start'] or (min(gst_numbers) if gst_numbers else settings.invoice_starting_number)
        ng_start = opts['non_gst_start'] or settings.non_gst_invoice_starting_number

        # GST numbers were issued first, so they sort ahead of no-GST ones.
        def order(row):
            inv, gst_n, ng_n = row
            return (0, gst_n, inv.created_at) if gst_n is not None else (1, ng_n, inv.created_at)

        plan = []
        next_gst, next_ng = gst_start, ng_start
        for inv, _, _ in sorted(in_scope, key=order):
            if inv.is_gst:
                new = f'{gst_prefix}{next_gst}'
                next_gst += 1
            else:
                new = f'{ng_prefix}{next_ng}'
                next_ng += 1
            plan.append((inv, new))

        changes = [(inv, new) for inv, new in plan if inv.invoice_number != new]
        for inv, new in plan:
            mark = '->' if inv.invoice_number != new else '  '
            kind = 'GST   ' if inv.is_gst else 'no-GST'
            filed = '  [FILED]' if inv.gst_filing_status == 'filed' else ''
            self.stdout.write(f'{kind}  {inv.invoice_number:>20} {mark} {new:<20} {inv.issue_date}  {inv.status}{filed}')
        self.stdout.write(f'\n{len(changes)} of {len(plan)} invoices change number.')

        filed_changes = [inv for inv, _ in changes if inv.gst_filing_status == 'filed']
        if filed_changes and not opts['allow_filed']:
            raise CommandError(
                f'{len(filed_changes)} invoice(s) already filed in GSTR would change number: '
                + ', '.join(i.invoice_number for i in filed_changes)
                + '. Rerun with --allow-filed only if you will amend those returns.'
            )
        if not changes:
            return
        if not opts['apply']:
            self.stdout.write(self.style.WARNING('Dry run. Rerun with --apply to write these numbers.'))
            return

        with transaction.atomic():
            # Park every changing invoice on a temporary number first, so a new
            # number never collides with one not yet moved off it.
            for inv, _ in changes:
                Invoice.all_objects.filter(pk=inv.pk).update(invoice_number=f'TMP-{uuid.uuid4().hex[:12]}')
            for inv, new in changes:
                Invoice.all_objects.filter(pk=inv.pk).update(invoice_number=new, renumbered_from=inv.invoice_number)
        self.stdout.write(self.style.SUCCESS(f'Renumbered {len(changes)} invoice(s).'))
