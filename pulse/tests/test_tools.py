"""Tests for the whitelisted query functions.

These build their own fixtures rather than relying on dev data, so they assert
real behaviour (counts, filtering rules, the permission gate) instead of just
"it did not raise".
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from core.models import Client, Invoice, Project
from crm.models import Lead
from employees.models import Employee

from pulse import tools
from pulse.scoping import PulseScope, resolve_scope


def owner_scope():
    return PulseScope(user=None, employee=None, can_query_business=True)


def denied_scope():
    return PulseScope(user=None, employee=None, can_query_business=False)


class PermissionGateTests(TestCase):
    """Every tool must refuse a scope that lacks business access."""

    def test_all_tools_refuse_unprivileged_scope(self):
        scope = denied_scope()
        sample_args = {
            'find_entity': {'name': 'anything'},
            'get_project_summary': {'project_id': '00000000-0000-0000-0000-000000000000'},
            'get_team_for_project': {'project_id': '00000000-0000-0000-0000-000000000000'},
            'get_lead_quotes': {'lead_id': 1},
        }
        for name, fn in tools.TOOL_REGISTRY.items():
            with self.subTest(tool=name):
                with self.assertRaises(PermissionDenied):
                    fn(scope, **sample_args.get(name, {}))

    def test_gate_refuses_before_touching_the_database(self):
        """The refusal must not be a silent empty result."""
        with self.assertRaises(PermissionDenied):
            tools.get_outstanding_receivables(denied_scope())


class ScopeResolutionTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

    def _employee(self, username, role, is_staff=False, status='active'):
        user = User.objects.create_user(username=username, password='x', is_staff=is_staff)
        Employee.objects.create(
            user=user,
            employee_id=f'EMP-{username}',
            role=role,
            status=status,
            joining_date=self.today,
        )
        return user

    def test_owner_role_gets_business_access(self):
        user = self._employee('owner1', 'owner')
        self.assertTrue(resolve_scope(user).can_query_business)

    def test_partner_role_gets_business_access(self):
        user = self._employee('partner1', 'partner')
        self.assertTrue(resolve_scope(user).can_query_business)

    def test_plain_employee_is_refused(self):
        user = self._employee('emp1', 'employee')
        self.assertFalse(resolve_scope(user).can_query_business)

    def test_intern_is_refused(self):
        user = self._employee('intern1', 'intern')
        self.assertFalse(resolve_scope(user).can_query_business)

    def test_staff_without_employee_record_gets_access(self):
        """A Django admin with no Employee row must not be locked out."""
        user = User.objects.create_user(username='admin1', password='x', is_staff=True)
        self.assertTrue(resolve_scope(user).can_query_business)

    def test_inactive_owner_falls_back_to_no_access(self):
        """Mirrors employees.views.get_employee, which filters status='active'."""
        user = self._employee('exowner', 'owner', status='terminated')
        self.assertFalse(resolve_scope(user).can_query_business)


class ProjectToolTests(TestCase):
    def setUp(self):
        self.scope = owner_scope()
        self.today = timezone.localdate()
        self.client_obj = Client.objects.create(name='Acme Ltd')

        self.overdue = Project.objects.create(
            client=self.client_obj, name='Late Project',
            project_type='web_app', status='in_progress',
            deadline=self.today - timedelta(days=5),
        )
        self.on_hold = Project.objects.create(
            client=self.client_obj, name='Paused Project',
            project_type='web_app', status='on_hold',
        )
        self.healthy = Project.objects.create(
            client=self.client_obj, name='Fine Project',
            project_type='web_app', status='in_progress',
            deadline=self.today + timedelta(days=30),
        )
        # Past deadline but finished -- must NOT be flagged.
        self.done = Project.objects.create(
            client=self.client_obj, name='Finished Project',
            project_type='web_app', status='completed',
            deadline=self.today - timedelta(days=90),
        )

    def test_needing_attention_finds_overdue_and_on_hold_only(self):
        result = tools.get_projects_needing_attention(self.scope)
        names = {p['name'] for p in result['projects']}
        self.assertEqual(names, {'Late Project', 'Paused Project'})
        self.assertEqual(result['count'], 2)

    def test_completed_project_past_deadline_is_not_flagged(self):
        result = tools.get_projects_needing_attention(self.scope)
        self.assertNotIn('Finished Project', {p['name'] for p in result['projects']})

    def test_days_overdue_is_computed(self):
        result = tools.get_projects_needing_attention(self.scope)
        late = next(p for p in result['projects'] if p['name'] == 'Late Project')
        self.assertEqual(late['days_overdue'], 5)
        self.assertTrue(late['is_overdue'])

    def test_on_hold_project_reports_reason(self):
        result = tools.get_projects_needing_attention(self.scope)
        paused = next(p for p in result['projects'] if p['name'] == 'Paused Project')
        self.assertEqual(paused['reason'], 'on hold')
        self.assertEqual(paused['days_overdue'], 0)

    def test_status_counts_include_empty_statuses(self):
        result = tools.count_projects_by_status(self.scope)
        self.assertEqual(result['total'], 4)
        statuses = {row['status'] for row in result['breakdown']}
        self.assertEqual(statuses, {v for v, _ in Project.STATUS_CHOICES})

    def test_active_count_uses_the_named_constant(self):
        result = tools.count_projects_by_status(self.scope)
        # in_progress x2 are active; on_hold and completed are not.
        self.assertEqual(result['active'], 2)
        self.assertEqual(result['active_definition'], list(tools.ACTIVE_PROJECT_STATUSES))

    def test_project_summary_returns_found_false_for_unknown_id(self):
        result = tools.get_project_summary(
            self.scope, '00000000-0000-0000-0000-000000000000'
        )
        self.assertFalse(result['found'])

    def test_project_summary_rejects_malformed_uuid(self):
        with self.assertRaises(ValueError):
            tools.get_project_summary(self.scope, 'not-a-uuid')

    def test_project_summary_shape(self):
        result = tools.get_project_summary(self.scope, str(self.overdue.id))
        self.assertTrue(result['found'])
        self.assertEqual(result['name'], 'Late Project')
        self.assertEqual(result['client'], 'Acme Ltd')
        self.assertTrue(result['is_overdue'])
        self.assertIn('by_status', result['tasks'])


class FindEntityTests(TestCase):
    def setUp(self):
        self.scope = owner_scope()
        self.ajith = Client.objects.create(
            name='Dr C Ajithkumar', company_name='runwithajith.com',
        )
        self.other = Client.objects.create(name='Zokko Toys')
        Client.objects.create(name='Ajith Old Account', is_active=False)
        self.portal = Project.objects.create(
            client=self.ajith, name='Patient Portal',
            project_type='web_app', status='in_progress',
        )

    def test_finds_client_by_partial_name_case_insensitive(self):
        result = tools.find_entity(self.scope, 'ajith')
        names = [c['name'] for c in result['clients']]
        self.assertEqual(names, ['Dr C Ajithkumar'])
        self.assertEqual(result['clients'][0]['id'], str(self.ajith.id))

    def test_finds_client_by_company_name(self):
        result = tools.find_entity(self.scope, 'runwithajith')
        self.assertEqual(result['clients'][0]['name'], 'Dr C Ajithkumar')

    def test_inactive_clients_are_not_returned(self):
        result = tools.find_entity(self.scope, 'Old Account')
        self.assertEqual(result['clients'], [])

    def test_finds_project_with_its_client_ids(self):
        result = tools.find_entity(self.scope, 'patient portal')
        self.assertEqual(len(result['projects']), 1)
        row = result['projects'][0]
        self.assertEqual(row['id'], str(self.portal.id))
        self.assertEqual(row['client_id'], str(self.ajith.id))

    def test_rejects_queries_too_short_to_mean_anything(self):
        with self.assertRaises(ValueError):
            tools.find_entity(self.scope, 'a')
        with self.assertRaises(ValueError):
            tools.find_entity(self.scope, '  ')


class InvoiceToolTests(TestCase):
    def setUp(self):
        self.scope = owner_scope()
        self.today = timezone.localdate()
        self.client_obj = Client.objects.create(name='Payer Ltd')

        self.late = Invoice.objects.create(
            invoice_number='INV-LATE', client=self.client_obj, title='Late',
            status='sent', issue_date=self.today - timedelta(days=60),
            due_date=self.today - timedelta(days=30),
            total_amount=Decimal('100000.00'), amount_paid=Decimal('25000.00'),
        )
        self.settled = Invoice.objects.create(
            invoice_number='INV-PAID', client=self.client_obj, title='Paid',
            status='paid', issue_date=self.today - timedelta(days=60),
            due_date=self.today - timedelta(days=30),
            total_amount=Decimal('50000.00'), amount_paid=Decimal('50000.00'),
        )
        self.draft = Invoice.objects.create(
            invoice_number='INV-DRAFT', client=self.client_obj, title='Draft',
            status='draft', issue_date=self.today,
            due_date=self.today - timedelta(days=1),
            total_amount=Decimal('9999.00'), amount_paid=Decimal('0.00'),
        )

    def test_overdue_excludes_paid_and_draft(self):
        result = tools.get_overdue_invoices(self.scope)
        numbers = {i['invoice_number'] for i in result['invoices']}
        self.assertEqual(numbers, {'INV-LATE'})

    def test_balance_is_total_minus_paid(self):
        result = tools.get_overdue_invoices(self.scope)
        self.assertEqual(result['invoices'][0]['balance'], 75000.0)
        self.assertEqual(result['total_outstanding'], 75000.0)

    def test_receivables_totals(self):
        result = tools.get_outstanding_receivables(self.scope)
        self.assertEqual(result['total_outstanding'], 75000.0)
        self.assertEqual(result['open_invoice_count'], 1)
        self.assertEqual(result['overdue_outstanding'], 75000.0)


class LeadToolTests(TestCase):
    def setUp(self):
        self.scope = owner_scope()
        self.today = timezone.localdate()

        self.due = Lead.objects.create(
            contact_person='Due Follow-up', phone='9000000001',
            status='interested',
            next_follow_up_date=self.today - timedelta(days=2),
            closing_probability=40,
        )
        self.future = Lead.objects.create(
            contact_person='Future', phone='9000000002',
            status='contacted',
            next_follow_up_date=self.today + timedelta(days=7),
        )
        self.won = Lead.objects.create(
            contact_person='Won Already', phone='9000000003',
            status='converted',
            next_follow_up_date=self.today - timedelta(days=10),
        )
        self.lost = Lead.objects.create(
            contact_person='Lost', phone='9000000004',
            status='lost',
            next_follow_up_date=self.today - timedelta(days=10),
        )

    def test_followup_excludes_closed_and_future_leads(self):
        result = tools.get_leads_needing_followup(self.scope)
        names = {lead['contact_person'] for lead in result['leads']}
        self.assertEqual(names, {'Due Follow-up'})

    def test_followup_reports_days_overdue(self):
        result = tools.get_leads_needing_followup(self.scope)
        self.assertEqual(result['leads'][0]['days_overdue'], 2)

    def test_followup_limit_is_clamped(self):
        result = tools.get_leads_needing_followup(self.scope, limit=99999)
        self.assertLessEqual(result['count'], 100)

    def test_pipeline_summary_open_excludes_converted_and_lost(self):
        result = tools.get_lead_pipeline_summary(self.scope)
        self.assertEqual(result['total'], 4)
        self.assertEqual(result['open'], 2)

    def test_lead_quotes_accepts_integer_pk(self):
        """crm.Lead uses BigAutoField, not the UUID keys used elsewhere."""
        result = tools.get_lead_quotes(self.scope, self.due.pk)
        self.assertTrue(result['found'])
        self.assertEqual(result['quotes'], [])

    def test_lead_quotes_rejects_non_integer(self):
        with self.assertRaises(ValueError):
            tools.get_lead_quotes(self.scope, 'abc')

    def test_lead_quotes_unknown_id(self):
        result = tools.get_lead_quotes(self.scope, 999999)
        self.assertFalse(result['found'])


class AttendanceToolTests(TestCase):
    def setUp(self):
        self.scope = owner_scope()

    def test_rejects_malformed_date(self):
        with self.assertRaises(ValueError):
            tools.get_attendance_summary(self.scope, date='20-07-2026')

    def test_defaults_to_today(self):
        result = tools.get_attendance_summary(self.scope)
        self.assertEqual(result['date'], timezone.localdate().isoformat())


class PortfolioGraphTests(TestCase):
    """The constellation's data layer."""

    def setUp(self):
        self.scope = owner_scope()
        self.today = timezone.localdate()

        self.busy = Client.objects.create(name='Busy Co', is_active=True)
        self.quiet = Client.objects.create(name='Quiet Co', is_active=True)
        Client.objects.create(name='Gone Co', is_active=False)

        self.live = Project.objects.create(
            client=self.busy, name='Live One', project_type='web_app',
            status='in_progress', deadline=self.today + timedelta(days=10),
        )
        self.late = Project.objects.create(
            client=self.busy, name='Late One', project_type='web_app',
            status='in_progress', deadline=self.today - timedelta(days=7),
        )
        Invoice.objects.create(
            invoice_number='INV-G1', client=self.busy, project=self.live,
            title='x', status='sent', issue_date=self.today,
            total_amount=Decimal('100000.00'), amount_paid=Decimal('0.00'),
        )

    def test_inactive_clients_are_excluded(self):
        g = tools.get_portfolio_graph(self.scope)
        self.assertNotIn('Gone Co', [n['label'] for n in g['nodes']])

    def test_clients_with_no_projects_are_kept(self):
        """An empty orbit is information, not something to hide."""
        g = tools.get_portfolio_graph(self.scope)
        quiet = next(n for n in g['nodes'] if n['label'] == 'Quiet Co')
        self.assertEqual(quiet['project_count'], 0)
        self.assertEqual(quiet['satellites'], [])

    def test_projects_become_satellites(self):
        g = tools.get_portfolio_graph(self.scope)
        busy = next(n for n in g['nodes'] if n['label'] == 'Busy Co')
        self.assertEqual(
            {s['label'] for s in busy['satellites']}, {'Live One', 'Late One'}
        )

    def test_overdue_project_flags_attention_and_carries_day_count(self):
        g = tools.get_portfolio_graph(self.scope)
        busy = next(n for n in g['nodes'] if n['label'] == 'Busy Co')
        late = next(s for s in busy['satellites'] if s['label'] == 'Late One')
        self.assertTrue(late['needs_attention'])
        self.assertEqual(late['tag'], 7)

    def test_attention_uses_rose_not_gold(self):
        """Gold is reserved for selection; it must not also encode data."""
        g = tools.get_portfolio_graph(self.scope)
        busy = next(n for n in g['nodes'] if n['label'] == 'Busy Co')
        self.assertTrue(busy['needs_attention'])
        self.assertEqual(busy['hue'], tools.ATTENTION_HUE)
        self.assertNotEqual(busy['hue'], tools.SELECTION_HUE)

    def test_edges_connect_core_to_clients_to_projects(self):
        g = tools.get_portfolio_graph(self.scope)
        busy_id = next(n['id'] for n in g['nodes'] if n['label'] == 'Busy Co')
        self.assertIn({'from': 'core', 'to': busy_id}, g['edges'])
        self.assertEqual(
            sum(1 for e in g['edges'] if e['from'] == busy_id), 2
        )

    def test_core_totals_are_real(self):
        g = tools.get_portfolio_graph(self.scope)
        self.assertEqual(g['core']['client_count'], 2)
        self.assertEqual(g['core']['project_count'], 2)
        self.assertEqual(g['core']['billed'], 100000.0)

    def test_shares_are_percentages_of_total_billing(self):
        g = tools.get_portfolio_graph(self.scope)
        busy = next(n for n in g['nodes'] if n['label'] == 'Busy Co')
        quiet = next(n for n in g['nodes'] if n['label'] == 'Quiet Co')
        self.assertEqual(busy['share'], 100)
        self.assertEqual(quiet['share'], 0)

    def test_no_billing_anywhere_does_not_divide_by_zero(self):
        Invoice.objects.all().delete()
        g = tools.get_portfolio_graph(self.scope)
        self.assertTrue(all(n['share'] == 0 for n in g['nodes']))

    def test_requires_business_scope(self):
        with self.assertRaises(PermissionDenied):
            tools.get_portfolio_graph(denied_scope())


class InrFormattingTests(TestCase):
    """Indian digit grouping, so server- and client-rendered money match."""

    def test_grouping(self):
        cases = {
            0: '0', 5: '5', 999: '999', 1000: '1,000', 12345: '12,345',
            100300: '1,00,300', 306950: '3,06,950', 598850: '5,98,850',
            10000000: '1,00,00,000', 123456789: '12,34,56,789',
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(tools._inr(raw), expected)

    def test_handles_none_and_negatives(self):
        self.assertEqual(tools._inr(None), '0')
        self.assertEqual(tools._inr(-306950), '-3,06,950')


class DashboardMetricsTests(TestCase):
    def setUp(self):
        self.scope = owner_scope()
        self.today = timezone.localdate()
        self.client_obj = Client.objects.create(name='Metric Co')

        Project.objects.create(
            client=self.client_obj, name='Live', project_type='web_app',
            status='in_progress', deadline=self.today + timedelta(days=5),
        )
        Project.objects.create(
            client=self.client_obj, name='Slipping', project_type='web_app',
            status='in_progress', deadline=self.today - timedelta(days=3),
        )
        Invoice.objects.create(
            invoice_number='INV-M1', client=self.client_obj, title='m',
            status='sent', issue_date=self.today - timedelta(days=40),
            due_date=self.today - timedelta(days=10),
            total_amount=Decimal('50000.00'), amount_paid=Decimal('20000.00'),
        )
        Lead.objects.create(
            contact_person='Chase me', phone='9000000009', status='interested',
            next_follow_up_date=self.today - timedelta(days=1),
        )
        Lead.objects.create(
            contact_person='Later', phone='9000000010', status='new',
            next_follow_up_date=self.today + timedelta(days=9),
        )
        Lead.objects.create(
            contact_person='Won', phone='9000000011', status='converted',
        )

    def _by_key(self):
        return {m['key']: m for m in tools.get_dashboard_metrics(self.scope)}

    def test_outstanding_is_billed_minus_paid(self):
        m = self._by_key()['outstanding']
        self.assertEqual(m['value'], 30000.0)
        self.assertEqual(m['display'], '₹30,000')
        self.assertTrue(m['alert'])
        self.assertEqual(m['note'], '1 invoice overdue')

    def test_open_leads_excludes_converted(self):
        m = self._by_key()['leads']
        self.assertEqual(m['value'], 2)
        self.assertEqual(m['note'], '1 need chasing')

    def test_active_projects_and_attention_count(self):
        m = self._by_key()['projects']
        self.assertEqual(m['value'], 2)
        self.assertEqual(m['note'], '1 needs a human')

    def test_singular_and_plural_notes(self):
        Project.objects.create(
            client=self.client_obj, name='Also late', project_type='web_app',
            status='in_progress', deadline=self.today - timedelta(days=9),
        )
        self.assertEqual(self._by_key()['projects']['note'], '2 need a human')

    def test_no_data_reads_calmly(self):
        Invoice.objects.all().delete()
        Lead.objects.all().delete()
        Project.objects.all().delete()
        m = self._by_key()
        self.assertEqual(m['outstanding']['note'], 'none overdue')
        self.assertFalse(m['outstanding']['alert'])
        self.assertEqual(m['leads']['note'], 'all up to date')
        self.assertEqual(m['projects']['note'], 'all on track')

    def test_client_node_separates_billed_from_owed(self):
        node = next(
            n for n in tools.get_portfolio_graph(self.scope)['nodes']
            if n['label'] == 'Metric Co'
        )
        self.assertEqual(node['billed'], 50000.0)
        self.assertEqual(node['collected'], 20000.0)
        self.assertEqual(node['outstanding'], 30000.0)

    def test_requires_business_scope(self):
        with self.assertRaises(PermissionDenied):
            tools.get_dashboard_metrics(denied_scope())


class DuesAndRenewalsTests(TestCase):
    def setUp(self):
        from core.models import AMCContract, Credential
        self.Credential = Credential
        self.AMCContract = AMCContract

        self.scope = owner_scope()
        self.today = timezone.localdate()
        self.client_obj = Client.objects.create(name='Renewal Co')
        self.project = Project.objects.create(
            client=self.client_obj, name='Hosted Thing',
            project_type='web_app', status='in_progress',
        )

        self.expired = Credential.objects.create(
            project=self.project, credential_type='domain', name='late.example',
            expiry_date=self.today - timedelta(days=30), is_active=True,
        )
        self.soon = Credential.objects.create(
            project=self.project, credential_type='ssl', name='ssl.example',
            expiry_date=self.today + timedelta(days=12), is_active=True,
            auto_renew=True,
        )
        self.far = Credential.objects.create(
            project=self.project, credential_type='hosting', name='far.example',
            expiry_date=self.today + timedelta(days=400), is_active=True,
        )
        self.inactive = Credential.objects.create(
            project=self.project, credential_type='domain', name='dead.example',
            expiry_date=self.today - timedelta(days=2), is_active=False,
        )
        Credential.objects.create(
            project=self.project, credential_type='api', name='no-expiry',
            is_active=True,
        )

    def test_beyond_the_horizon_is_excluded(self):
        labels = {i['label'] for i in
                  tools.get_dues_and_renewals(self.scope)['items']}
        self.assertNotIn('far.example', labels)

    def test_inactive_credentials_are_excluded(self):
        labels = {i['label'] for i in
                  tools.get_dues_and_renewals(self.scope)['items']}
        self.assertNotIn('dead.example', labels)

    def test_credentials_without_an_expiry_are_excluded(self):
        labels = {i['label'] for i in
                  tools.get_dues_and_renewals(self.scope)['items']}
        self.assertNotIn('no-expiry', labels)

    def test_overdue_sorts_before_upcoming(self):
        items = tools.get_dues_and_renewals(self.scope)['items']
        self.assertEqual(items[0]['label'], 'late.example')
        self.assertTrue(items[0]['overdue'])

    def test_days_abs_is_positive_for_overdue(self):
        item = tools.get_dues_and_renewals(self.scope)['items'][0]
        self.assertEqual(item['days'], -30)
        self.assertEqual(item['days_abs'], 30)

    def test_client_is_reached_through_the_project(self):
        item = tools.get_dues_and_renewals(self.scope)['items'][0]
        self.assertEqual(item['client'], 'Renewal Co')

    def test_project_is_required_by_the_schema(self):
        """Credential.project is NOT NULL, so an unattached credential cannot
        exist. The tool still guards for None because the FK could be relaxed
        later, but nothing can currently reach that branch."""
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.Credential.objects.create(
                    project=None, credential_type='domain', name='orphan',
                    expiry_date=self.today, is_active=True,
                )

    def test_amc_contracts_are_merged_in(self):
        self.AMCContract.objects.create(
            project=self.project, contract_type='amc',
            annual_amount=Decimal('24000.00'), billing_cycle='yearly',
            start_date=self.today - timedelta(days=365),
            end_date=self.today + timedelta(days=30),
            next_due_date=self.today + timedelta(days=5), status='active',
        )
        items = tools.get_dues_and_renewals(self.scope)['items']
        amc = next(i for i in items if i['kind'] == 'amc')
        self.assertEqual(amc['client'], 'Renewal Co')
        self.assertEqual(amc['amount'], 24000.0)

    def test_cancelled_amc_is_excluded(self):
        self.AMCContract.objects.create(
            project=self.project, contract_type='amc',
            annual_amount=Decimal('9000.00'), billing_cycle='yearly',
            start_date=self.today, end_date=self.today + timedelta(days=30),
            next_due_date=self.today + timedelta(days=3), status='cancelled',
        )
        items = tools.get_dues_and_renewals(self.scope)['items']
        self.assertEqual([i for i in items if i['kind'] == 'amc'], [])

    def test_counts_and_auto_renew_flag(self):
        result = tools.get_dues_and_renewals(self.scope)
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['overdue_count'], 1)
        ssl = next(i for i in result['items'] if i['label'] == 'ssl.example')
        self.assertTrue(ssl['auto_renew'])

    def test_horizon_is_adjustable(self):
        wide = tools.get_dues_and_renewals(self.scope, horizon_days=500)
        self.assertIn('far.example', {i['label'] for i in wide['items']})

    def test_requires_business_scope(self):
        with self.assertRaises(PermissionDenied):
            tools.get_dues_and_renewals(denied_scope())
