"""Fee payment QR for interns who accept an internship agreement that carries a fee."""
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.models import CompanySettings
from employees.agreement_models import MONEY_FEE, MONEY_NONE
from employees.models import AgreementRequest, AgreementTemplate, Employee


class AgreementPaymentTests(TestCase):
    def setUp(self):
        company = CompanySettings.get_settings()
        company.upi_id = 'main@hdfcbank'
        company.ng_upi_id = 'fees@okaxis'
        company.ng_account_holder_name = 'Ralfiz Technologies'
        company.save()
        self.hr = User.objects.create_superuser('boss', 'boss@example.com', 'pw-123456')
        user = User.objects.create_user('asha', first_name='Asha', last_name='Nair')
        self.emp = Employee.objects.create(user=user, employee_id='EMP902', employment_type='intern',
                                           role='intern', phone='9876543210',
                                           joining_date=timezone.localdate())
        self.template = AgreementTemplate.objects.create(name='T', monthly_fee=Decimal('750'),
                                                         money_mode=MONEY_FEE)

    def make(self, mode=MONEY_FEE, fee=Decimal('750'), status='accepted', decision='continue'):
        return AgreementRequest.objects.create(
            employee=self.emp, template=self.template,
            snapshot_json=self.template.build_snapshot(), snapshot_fee=fee, snapshot_money_mode=mode,
            status=status, decision=decision, full_name='Asha Nair', responded_at=timezone.now())

    def test_fee_agreement_gets_upi_link_to_the_no_gst_account(self):
        agreement = self.make()
        self.assertTrue(agreement.needs_payment)
        uri = agreement.upi_uri()
        self.assertTrue(uri.startswith('upi://pay?'))
        query = parse_qs(urlparse(uri).query)
        self.assertEqual(query['pa'], ['fees@okaxis'])
        self.assertEqual(query['am'], ['750.00'])
        self.assertEqual(query['cu'], ['INR'])
        self.assertIn(agreement.reference, query['tn'][0])
        self.assertTrue(agreement.upi_qr_data_uri().startswith('data:image/png;base64,'))

    def test_falls_back_to_main_upi_when_no_gst_is_blank(self):
        company = CompanySettings.get_settings()
        company.ng_upi_id = ''
        company.save()
        query = parse_qs(urlparse(self.make().upi_uri()).query)
        self.assertEqual(query['pa'], ['main@hdfcbank'])

    def test_qr_encodes_exactly_the_upi_link(self):
        """Re-encode the link with the same settings and compare pixels (see the certificate QR trap)."""
        import base64
        import io

        import qrcode
        agreement = self.make()
        qr = qrcode.QRCode(border=4, box_size=8, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(agreement.upi_uri())
        qr.make(fit=True)
        buf = io.BytesIO()
        qr.make_image(fill_color='black', back_color='white').save(buf, format='PNG')
        self.assertEqual(agreement.upi_qr_data_uri().split(',', 1)[1], base64.b64encode(buf.getvalue()).decode())

    def test_no_payment_for_free_stipend_declined_or_unsigned(self):
        self.assertFalse(self.make(mode=MONEY_NONE, fee=None).needs_payment)
        self.assertFalse(self.make(mode='stipend').needs_payment)
        self.assertFalse(self.make(status='declined', decision='discontinue').needs_payment)
        self.assertFalse(self.make(status='pending', decision='').needs_payment)

    def test_done_and_pay_pages_show_the_qr(self):
        agreement = self.make()
        done = self.client.get(f'/agreement/{agreement.token}/done/')
        self.assertContains(done, 'Pay your internship fee')
        self.assertContains(done, 'fees@okaxis')
        pay = self.client.get(agreement.payment_path())
        self.assertContains(pay, 'data:image/png;base64,')
        self.assertContains(pay, 'upi://pay?')

    def test_pay_page_redirects_when_nothing_to_pay(self):
        agreement = self.make(mode=MONEY_NONE, fee=None)
        response = self.client.get(agreement.payment_path())
        self.assertRedirects(response, f'/agreement/{agreement.token}/done/')

    def test_hr_page_and_welcome_message_carry_the_payment_link(self):
        agreement = self.make()
        self.assertIn(agreement.payment_path(), agreement.welcome_message())
        self.client.force_login(self.hr)
        page = self.client.get(f'/hr/agreements/{agreement.pk}/')
        self.assertContains(page, 'Send payment QR')
        self.assertContains(page, 'wa.me/919876543210')
