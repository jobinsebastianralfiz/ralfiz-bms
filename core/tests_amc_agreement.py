from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import AMCContract, Client, Project


class AMCPercentageAndAgreementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('owner', 'o@example.com', 'pw')
        self.client.force_login(self.user)
        client = Client.objects.create(name='Asha', company_name='Perfect Institutions', email='a@example.com')
        self.project = Project.objects.create(client=client, name='Fee Management', final_amount=Decimal('80000'))

    def _post(self, **extra):
        data = {'project': self.project.pk, 'contract_type': 'amc', 'billing_cycle': 'quarterly',
                'start_date': '2026-10-01', 'end_date': '2027-09-30', 'annual_amount': '1'}
        data.update(extra)
        return self.client.post(reverse('amc_create'), data)

    def test_percentage_mode_computes_amount_from_project_value(self):
        self._post(amount_mode='percent', percentage='22')
        amc = AMCContract.objects.get()
        self.assertEqual(amc.percentage, Decimal('22'))
        self.assertEqual(amc.annual_amount, Decimal('17600.00'))
        self.assertEqual(amc.instalment_amount, Decimal('4400.00'))

    def test_fixed_mode_keeps_typed_amount(self):
        self._post(amount_mode='fixed', percentage='22', annual_amount='12000')
        amc = AMCContract.objects.get()
        self.assertIsNone(amc.percentage)
        self.assertEqual(amc.annual_amount, Decimal('12000'))

    def test_covered_system_rows_and_agreement_numbers(self):
        self._post()
        self._post(covered_system='Android App | Flutter | com.example.app\n\nAPI | Django')
        first, second = AMCContract.objects.order_by('agreement_no')
        self.assertEqual((first.agreement_no, second.agreement_no), ('RT/AMC/2026/001', 'RT/AMC/2026/002'))
        self.assertEqual(first.covered_rows[0][0], 'Web Application \u2013 Fee Management')
        self.assertEqual(second.covered_rows, [['Android App', 'Flutter', 'com.example.app'], ['API', 'Django', '']])

    def test_agreement_page_shows_parties_fee_plan_and_gst(self):
        self._post(amount_mode='percent', percentage='25', plan='premium', include_gst='on', extra_hourly_rate='800')
        amc = AMCContract.objects.get()
        html = self.client.get(reverse('amc_agreement', args=[amc.pk])).content.decode()
        self.assertIn('Perfect Institutions', html)
        self.assertIn('RT/AMC/2026/001', html)
        self.assertIn('20,000', html)          # 25% of 80,000
        self.assertIn('23,600', html)          # + 18% GST
        self.assertIn('5,900', html)           # quarterly instalment
        self.assertIn('10 hours per month', html)
        self.assertIn('800', html)

    def test_no_gst_agreement_says_so(self):
        self._post(annual_amount='12000')
        amc = AMCContract.objects.get()
        html = self.client.get(reverse('amc_agreement', args=[amc.pk])).content.decode()
        self.assertIn('No GST is charged', html)
