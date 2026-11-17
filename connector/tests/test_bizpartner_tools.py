"""Business Partner connector tools: list, details, payments (INR converted),
expenses and project updates, against the same money() the portal shows."""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from bizpartners.models import BusinessPartner, JointExpense, JointPayment, JointProject

from .test_connector import MCPClientMixin, make_employee, make_token


class BizPartnerToolTests(MCPClientMixin, TestCase):
    def setUp(self):
        self.owner = make_employee('owner', 'owner')
        self.token = make_token(self.owner)
        self.partner = BusinessPartner.objects.create(name='Arfad Khan', company_name='Riyadh Tech')
        self.fixed = JointProject.objects.create(
            partner=self.partner, title='Nous QR And Web', client_name='Nous', deal_type='fixed',
            contract_value=Decimal('2900'), status='in_progress', progress=60)
        self.split = JointProject.objects.create(
            partner=self.partner, title='Clinic app', client_name='Al Noor', deal_type='split',
            contract_value=Decimal('10000'), partner_share_percent=Decimal('40'), status='in_progress')

    def test_tools_are_listed(self):
        names = {t['name'] for t in self.rpc('tools/list', token=self.token.token).json()['result']['tools']}
        for name in ('list_business_partners', 'get_business_partner', 'get_joint_project',
                     'record_joint_payment', 'add_joint_expense', 'update_joint_project'):
            self.assertIn(name, names)

    def test_search_finds_partner_and_project(self):
        found = self.ok('search', {'query': 'nous', 'types': ['joint_projects']})
        self.assertEqual(found['joint_projects'][0]['id'], str(self.fixed.id))
        found = self.ok('search', {'query': 'riyadh', 'types': ['business_partners']})
        self.assertEqual(found['business_partners'][0]['id'], str(self.partner.id))

    def test_list_and_detail_show_the_balance(self):
        listed = self.ok('list_business_partners')
        self.assertEqual(listed['items'][0]['projects'], 2)
        self.assertIn('owes Ralfiz SAR 2900.00', listed['items'][0]['balance'])
        detail = self.ok('get_business_partner', {'partner_id': str(self.partner.id)})
        self.assertEqual(detail['fixed_deals']['still_to_pay'], '2900.00')
        self.assertEqual(len(detail['projects']), 2)

    def test_inr_payment_is_converted_to_sar(self):
        result = self.ok('record_joint_payment', {
            'project_id': str(self.fixed.id), 'amount': 10000, 'currency': 'INR', 'exchange_rate': 23.5})
        pay = JointPayment.objects.get()
        self.assertEqual(pay.kind, 'partner_to_ralfiz')            # default on a fixed deal
        self.assertEqual(pay.amount, Decimal('425.53'))
        self.assertEqual(pay.paid_amount, Decimal('10000'))
        self.assertEqual(result['project']['still_to_pay'], '2474.47')
        project = self.ok('get_joint_project', {'project_id': str(self.fixed.id)})
        self.assertIn('INR 10000.00 at 23.5', project['payments'][0]['paid_as'])

    def test_foreign_currency_needs_a_rate(self):
        is_error, message = self.call('record_joint_payment', {
            'project_id': str(self.fixed.id), 'amount': 10000, 'currency': 'INR'})
        self.assertTrue(is_error)
        self.assertIn('exchange_rate', message)
        self.assertEqual(JointPayment.objects.count(), 0)

    def test_split_expense_changes_the_shares(self):
        self.ok('record_joint_payment', {'project_id': str(self.split.id), 'amount': 5000})
        result = self.ok('add_joint_expense', {'project_id': str(self.split.id), 'description': 'Hosting',
                                               'amount': 1000, 'paid_by': 'partner'})
        self.assertEqual(JointExpense.objects.get().paid_by, 'partner')
        self.assertEqual(result['project']['profit'], '4000.00')
        self.assertEqual(result['project']['partner_share'], '1600.00')
        self.assertNotIn('note', result)

    def test_update_project_marks_completed(self):
        result = self.ok('update_joint_project', {'project_id': str(self.fixed.id), 'status': 'completed'})
        self.fixed.refresh_from_db()
        self.assertEqual((self.fixed.status, self.fixed.progress), ('completed', 100))
        self.assertEqual(self.fixed.completed_date, date.today())
        self.assertIn('status', result['updated'])
        self.assertTrue(self.call('update_joint_project', {'project_id': str(self.fixed.id)})[0])

    def test_read_only_token_cannot_record(self):
        read_only = make_token(self.owner, scope='bms:read')
        is_error, _ = self.call('record_joint_payment', {'project_id': str(self.fixed.id), 'amount': 1},
                                token=read_only.token)
        self.assertTrue(is_error)
        self.assertEqual(JointPayment.objects.count(), 0)
        self.assertFalse(self.call('get_joint_project', {'project_id': str(self.fixed.id)},
                                   token=read_only.token)[0])
