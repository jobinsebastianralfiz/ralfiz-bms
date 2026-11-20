from datetime import date
from decimal import Decimal as D

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import BusinessPartner, JointExpense, JointPayment, JointProject, JointQuote


def pay(project, kind, amount):
    return JointPayment.objects.create(project=project, kind=kind, amount=D(amount))


class MoneyTests(TestCase):
    def setUp(self):
        self.partner = BusinessPartner.objects.create(name='Ahmed', company_name='Riyadh Tech')
        self.project = JointProject.objects.create(partner=self.partner, title='ERP', contract_value=D('10000'),
                                                   partner_share_percent=D('50'))

    def m(self):
        return JointProject.objects.get(pk=self.project.pk).money()

    def test_client_pays_ralfiz_we_owe_partner_half(self):
        pay(self.project, 'client_to_ralfiz', '10000')
        m = self.m()
        self.assertEqual(m['profit'], D('10000'))
        self.assertEqual(m['partner_share'], D('5000'))
        self.assertEqual(m['due_to_partner'], D('5000'))
        self.assertEqual(m['pending_from_client'], D('0'))
        pay(self.project, 'ralfiz_to_partner', '5000')
        self.assertEqual(self.m()['due_to_partner'], D('0'))

    def test_client_pays_partner_partner_owes_us(self):
        self.project.partner_share_percent = D('40')  # Ralfiz 60 / partner 40
        self.project.save()
        pay(self.project, 'client_to_partner', '4000')
        m = self.m()
        self.assertEqual(m['pending_from_client'], D('6000'))
        self.assertEqual(m['ralfiz_share'], D('2400'))
        self.assertEqual(m['due_to_partner'], D('-2400'))
        pay(self.project, 'partner_to_ralfiz', '2400')
        self.assertEqual(self.m()['due_to_partner'], D('0'))
        self.assertEqual(self.m()['projected_partner_share'], D('4000'))

    def test_expenses_come_off_the_top_and_payer_is_reimbursed(self):
        pay(self.project, 'client_to_ralfiz', '10000')
        JointExpense.objects.create(project=self.project, description='Server', amount=D('1000'), paid_by='partner')
        m = self.m()
        self.assertEqual(m['profit'], D('9000'))
        self.assertEqual(m['partner_share'], D('4500'))
        self.assertEqual(m['due_to_partner'], D('5500'))  # 4500 share + 1000 spent back

    def test_partner_totals_skip_cancelled(self):
        pay(self.project, 'client_to_ralfiz', '1000')
        other = JointProject.objects.create(partner=self.partner, title='Dead', contract_value=D('500'), status='cancelled')
        pay(other, 'client_to_ralfiz', '500')
        t = self.partner.totals()
        self.assertEqual(t['projects'], 1)
        self.assertEqual(t['received'], D('1000'))

    def test_quote_numbers(self):
        a = JointQuote.objects.create(project=self.project, title='A', amount=D('1'))
        b = JointQuote.objects.create(project=self.project, title='B', amount=D('1'))
        self.assertEqual((a.quote_number, b.quote_number), ('JQ-0001', 'JQ-0002'))


class PortalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ahmed', 'a@x.sa', 'pass12345')
        self.partner = BusinessPartner.objects.create(name='Ahmed', email='a@x.sa', user=self.user)
        self.mine = JointProject.objects.create(partner=self.partner, title='Mine Project', contract_value=D('10000'))
        other = BusinessPartner.objects.create(name='Other Co')
        self.theirs = JointProject.objects.create(partner=other, title='Secret Project', contract_value=D('99'))
        self.draft = JointQuote.objects.create(project=self.mine, title='Draft quote', amount=D('5'), status='draft')
        JointQuote.objects.create(project=self.mine, title='Sent quote', amount=D('7'), status='sent')
        pay(self.mine, 'client_to_ralfiz', '2000')

    def test_login_with_email_and_pages_render(self):
        r = self.client.post(reverse('bizpartners_portal:login'), {'username': 'a@x.sa', 'password': 'pass12345'})
        self.assertRedirects(r, reverse('bizpartners_portal:dashboard'))
        for name in ('dashboard', 'projects', 'payments', 'quotes', 'password'):
            r = self.client.get(reverse(f'bizpartners_portal:{name}'))
            self.assertEqual(r.status_code, 200, name)
            self.assertNotContains(r, 'Secret Project')
        r = self.client.get(reverse('bizpartners_portal:dashboard'))
        self.assertContains(r, 'Mine Project')
        self.assertContains(r, 'Ralfiz owes you SAR 1,000.00')

    def test_cannot_open_another_partners_project(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('bizpartners_portal:project', args=[self.theirs.pk]))
        self.assertEqual(r.status_code, 404)

    def test_draft_quotes_hidden(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('bizpartners_portal:project', args=[self.mine.pk]))
        self.assertContains(r, 'Sent quote')
        self.assertNotContains(r, 'Draft quote')
        r = self.client.get(reverse('bizpartners_portal:quotes'))
        self.assertNotContains(r, 'Draft quote')

    def test_partner_confined_to_portal(self):
        self.client.force_login(self.user)
        for url in ('/', '/clients/', reverse('bizpartners:list'), reverse('bizpartners:project', args=[self.mine.pk])):
            r = self.client.get(url)
            self.assertRedirects(r, reverse('bizpartners_portal:dashboard'), fetch_redirect_response=False, msg_prefix=url)
        r = self.client.get('/api/employees/owner/dashboard/')
        self.assertEqual(r.status_code, 403)

    def test_partner_can_post_message(self):
        self.client.force_login(self.user)
        self.client.post(reverse('bizpartners_portal:project', args=[self.mine.pk]), {'message': 'When is the demo?'})
        u = self.mine.updates.get()
        self.assertTrue(u.from_partner)

    def test_inactive_partner_locked_out(self):
        self.partner.is_active = False
        self.partner.save()
        self.client.force_login(self.user)
        r = self.client.get(reverse('bizpartners_portal:dashboard'))
        self.assertRedirects(r, reverse('bizpartners_portal:login'), fetch_redirect_response=False)


class FixedDealTests(TestCase):
    def setUp(self):
        self.partner = BusinessPartner.objects.create(name='Arfad')
        self.project = JointProject.objects.create(
            partner=self.partner, title='Nous', deal_type='fixed', contract_value=D('2900'),
            amc_amount=D('500'), amc_cycle='yearly', amc_start_date=date(2026, 1, 1),
            server_amount=D('50'), server_cycle='monthly', server_start_date=date(2026, 10, 15))

    def test_periods_due(self):
        p = self.project
        self.assertEqual(p.periods_due(date(2026, 1, 1), 'yearly', today=date(2025, 12, 31)), 0)
        self.assertEqual(p.periods_due(date(2026, 1, 1), 'yearly', today=date(2026, 1, 1)), 1)
        self.assertEqual(p.periods_due(date(2026, 1, 1), 'yearly', today=date(2027, 1, 1)), 2)
        self.assertEqual(p.periods_due(date(2026, 10, 15), 'monthly', today=date(2026, 11, 14)), 1)
        self.assertEqual(p.periods_due(date(2026, 10, 15), 'monthly', today=date(2026, 11, 15)), 2)
        self.assertEqual(p.periods_due(date(2026, 1, 31), 'quarterly', today=date(2026, 4, 30)), 1)
        p.recurring_end_date = date(2026, 3, 1)
        self.assertEqual(p.periods_due(date(2026, 1, 1), 'monthly', today=date(2026, 12, 1)), 3)

    def test_next_charge_date_and_calendar(self):
        p = self.project
        self.assertEqual(p.next_charge_date(date(2026, 1, 1), 'yearly', today=date(2026, 11, 17)), date(2027, 1, 1))
        self.assertEqual(p.next_charge_date(date(2026, 1, 31), 'monthly', today=date(2026, 2, 1)), date(2026, 2, 28))
        self.assertEqual(p.next_charge_date(date(2026, 12, 1), 'yearly', today=date(2026, 11, 17)), date(2026, 12, 1))
        p.recurring_end_date = date(2026, 12, 31)
        self.assertIsNone(p.next_charge_date(date(2026, 1, 1), 'yearly', today=date(2026, 11, 17)))
        p.recurring_end_date = None
        p.save()
        user = User.objects.create_user('arfad2', password='pass12345')
        self.partner.user = user
        self.partner.save()
        self.client.force_login(user)
        r = self.client.get(reverse('bizpartners_portal:dashboard'))
        self.assertContains(r, 'Hello, Arfad')
        self.assertContains(r, 'AMC due')
        self.assertContains(r, 'Server charges due')

    def test_fixed_money_ignores_split_and_client_price(self):
        with self.settings(TIME_ZONE='Asia/Kolkata'):
            from unittest import mock
            with mock.patch('django.utils.timezone.localdate', return_value=date(2026, 11, 17)):
                pay(self.project, 'client_to_partner', '9999')  # partner's own deal with the client
                JointPayment.objects.create(project=self.project, kind='partner_to_ralfiz', amount=D('2000'))
                JointPayment.objects.create(project=self.project, kind='partner_to_ralfiz', amount=D('500'),
                                            purpose='amc')
                m = JointProject.objects.get(pk=self.project.pk).money()
        self.assertTrue(m['is_fixed'])
        self.assertEqual(m['amc_due'], D('500'))       # one yearly period from 1 Jan 2026
        self.assertEqual(m['server_due'], D('100'))    # 15 Oct and 15 Nov
        self.assertEqual(m['fixed_due'], D('3500'))
        self.assertEqual(m['fixed_paid'], D('2500'))
        self.assertEqual(m['fixed_balance'], D('1000'))
        self.assertEqual(m['due_to_partner'], D('-1000'))
        self.assertEqual(m['partner_share'], D('0'))
        lines = {l['key']: l for l in m['recurring']}
        self.assertEqual((lines['amc']['paid'], lines['server']['paid']), (D('500'), D('0')))
        self.assertEqual(m['fixed_agreed_paid'], D('2000'))

    def test_partner_sees_fixed_balance(self):
        user = User.objects.create_user('arfad', password='pass12345')
        self.partner.user = user
        self.partner.save()
        JointPayment.objects.create(project=self.project, kind='partner_to_ralfiz', amount=D('2900'))
        self.project.amc_amount = self.project.server_amount = D('0')
        self.project.save()
        self.client.force_login(user)
        r = self.client.get(reverse('bizpartners_portal:dashboard'))
        self.assertContains(r, 'All settled')
        self.assertContains(r, 'Due to Ralfiz so far')
        self.assertNotContains(r, 'profit share')
        r = self.client.get(reverse('bizpartners_portal:project', args=[self.project.pk]))
        self.assertContains(r, 'What you pay Ralfiz')
        self.assertContains(r, 'Fully paid')
        self.assertNotContains(r, 'Profit split')
        self.assertNotContains(r, 'What is charged')  # no AMC/server: the summary says it all


class StaffTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser('boss', 'b@x.in', 'pass12345')
        self.client.force_login(self.staff)

    def test_full_flow(self):
        r = self.client.post(reverse('bizpartners:create'), {
            'company_name': 'Riyadh Tech', 'name': 'Ahmed', 'email': 'ahmed@rt.sa', 'country': 'Saudi Arabia',
            'currency': 'SAR', 'default_partner_share': '40', 'is_active': 'on'})
        partner = BusinessPartner.objects.get()
        self.assertRedirects(r, reverse('bizpartners:detail', args=[partner.pk]))

        r = self.client.get(reverse('bizpartners:project_create', args=[partner.pk]))
        self.assertContains(r, 'value="40.00"')
        r = self.client.post(reverse('bizpartners:project_create', args=[partner.pk]), {
            'title': 'Clinic app', 'client_name': 'Al Noor', 'status': 'in_progress', 'progress': '30',
            'deal_type': 'split', 'contract_value': '20000', 'partner_share_percent': '40'})
        project = JointProject.objects.get()
        self.assertEqual(project.partner, partner)

        self.client.post(reverse('bizpartners:item_create', args=[project.pk, 'payment']), {
            'kind': 'client_to_ralfiz', 'paid_currency': 'SAR', 'paid_amount': '10000', 'payment_date': '2026-11-17', 'method': 'bank_transfer'})
        self.client.post(reverse('bizpartners:item_create', args=[project.pk, 'quote']), {
            'title': 'Phase 1', 'amount': '20000', 'quote_date': '2026-11-01', 'status': 'accepted'})
        self.client.post(reverse('bizpartners:item_create', args=[project.pk, 'expense']), {
            'description': 'Hosting', 'paid_currency': 'SAR', 'paid_amount': '500', 'expense_date': '2026-11-10', 'paid_by': 'ralfiz'})
        self.assertEqual(project.money()['due_to_partner'], D('3800.00'))  # 40% of 9,500

        for url in (reverse('bizpartners:list'), reverse('bizpartners:detail', args=[partner.pk]),
                    reverse('bizpartners:project', args=[project.pk])):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        r = self.client.get(reverse('bizpartners:project', args=[project.pk]))
        self.assertContains(r, 'We owe the partner SAR 3,800.00')

        r = self.client.post(reverse('bizpartners:login', args=[partner.pk]), {'username': 'ahmed', 'password': 'secret-pw-1'})
        partner.refresh_from_db()
        self.assertEqual(partner.user.username, 'ahmed')
        self.assertTrue(partner.user.check_password('secret-pw-1'))
        r = self.client.get(reverse('bizpartners:detail', args=[partner.pk]))
        self.assertContains(r, 'secret-pw-1')
        r = self.client.get(reverse('bizpartners:detail', args=[partner.pk]))
        self.assertNotContains(r, 'secret-pw-1')

    def test_inr_payment_converted_to_sar(self):
        partner = BusinessPartner.objects.create(name='Arfad', default_partner_share=D('50'))
        project = JointProject.objects.create(partner=partner, title='Nous', contract_value=D('2900'))
        url = reverse('bizpartners:item_create', args=[project.pk, 'payment'])
        r = self.client.post(url, {'kind': 'client_to_ralfiz', 'paid_currency': 'INR', 'paid_amount': '10000',
                                   'payment_date': '2026-11-17', 'method': 'bank_transfer'})
        self.assertContains(r, 'Enter how many INR make 1 SAR')
        self.assertFalse(project.payments.exists())

        self.client.post(url, {'kind': 'client_to_ralfiz', 'paid_currency': 'INR', 'paid_amount': '10000',
                               'exchange_rate': '23.5', 'payment_date': '2026-11-17', 'method': 'bank_transfer'})
        pay = project.payments.get()
        self.assertEqual(pay.amount, D('425.53'))
        self.assertEqual((pay.paid_currency, pay.paid_amount, pay.exchange_rate), ('INR', D('10000'), D('23.5')))
        self.assertEqual(project.money()['received'], D('425.53'))
        r = self.client.get(reverse('bizpartners:project', args=[project.pk]))
        self.assertContains(r, 'paid INR 10,000.00 @ 23.5')

        # The next entry remembers INR and the rate.
        r = self.client.get(reverse('bizpartners:item_create', args=[project.pk, 'expense']))
        self.assertContains(r, '<option value="INR" selected>')
        self.assertContains(r, 'value="23.5000"')

        # Paid in SAR: no rate needed, booked one to one.
        self.client.post(reverse('bizpartners:item_create', args=[project.pk, 'expense']), {
            'description': 'Domain', 'paid_currency': 'SAR', 'paid_amount': '50', 'expense_date': '2026-11-17',
            'paid_by': 'ralfiz'})
        e = project.expenses.get()
        self.assertEqual((e.amount, e.exchange_rate), (D('50'), D('1')))

    def test_editing_an_old_payment_switches_it_to_inr(self):
        partner = BusinessPartner.objects.create(name='Arfad')
        project = JointProject.objects.create(partner=partner, title='Nous', contract_value=D('2900'))
        pay = JointPayment.objects.create(project=project, kind='client_to_ralfiz', amount=D('10000'))
        url = reverse('bizpartners:item_edit', args=[project.pk, 'payment', pay.pk])
        self.assertContains(self.client.get(url), 'value="10000.00"')
        self.client.post(url, {'kind': 'client_to_ralfiz', 'paid_currency': 'INR', 'paid_amount': '10000',
                               'exchange_rate': '25', 'payment_date': '2026-11-17', 'method': 'bank_transfer'})
        pay.refresh_from_db()
        self.assertEqual(pay.amount, D('400.00'))

    def test_fixed_project_form(self):
        partner = BusinessPartner.objects.create(name='Arfad')
        url = reverse('bizpartners:project_create', args=[partner.pk])
        base = {'title': 'Nous', 'status': 'in_progress', 'progress': '90', 'deal_type': 'fixed',
                'contract_value': '2900', 'partner_share_percent': '50'}
        r = self.client.post(url, {**base, 'amc_amount': '500'})
        self.assertContains(r, 'Pick the date the AMC start')
        self.client.post(url, {**base, 'amc_amount': '500', 'amc_cycle': 'yearly', 'amc_start_date': '2026-12-01'})
        project = JointProject.objects.get()
        self.assertTrue(project.is_fixed)
        self.assertEqual((project.server_amount, project.server_cycle), (D('0'), 'yearly'))
        r = self.client.get(reverse('bizpartners:item_create', args=[project.pk, 'payment']))
        self.assertContains(r, '<option value="partner_to_ralfiz" selected>')
        r = self.client.get(reverse('bizpartners:project', args=[project.pk]))
        self.assertContains(r, 'What is charged')
        self.assertContains(r, 'Not started yet')
        # The next project for this partner starts as a fixed deal too.
        r = self.client.get(url)
        self.assertContains(r, '<option value="fixed" selected>')

    def test_unknown_item_kind_404(self):
        partner = BusinessPartner.objects.create(name='X')
        project = JointProject.objects.create(partner=partner, title='P')
        self.assertEqual(self.client.get(f'/business-partners/projects/{project.pk}/bogus/new/').status_code, 404)


class CredentialTests(TestCase):
    """Server/domain logins and the GitHub link on a joint project."""

    def setUp(self):
        from .models import JointCredential  # noqa: F401
        self.staff = User.objects.create_superuser('boss2', 'b2@x.in', 'pass12345')
        self.puser = User.objects.create_user('p@rt.sa', 'p@rt.sa', 'partner-pass-1')
        self.partner = BusinessPartner.objects.create(user=self.puser, name='Arfad', email='p@rt.sa')
        self.project = JointProject.objects.create(partner=self.partner, title='Nous QR', deal_type='fixed',
                                                   contract_value=D('2900'), status='in_progress',
                                                   repo_url='https://github.com/ralfiz/nous-web')

    def add(self, **extra):
        self.client.force_login(self.staff)
        data = {'kind': 'server', 'name': 'Hostinger VPS', 'url': '82.25.1.9', 'username': 'root',
                'password': 'S3cret-Pass!', 'notes': 'SSH port 2222', 'shared_with_partner': 'on'}
        data.update(extra)
        r = self.client.post(reverse('bizpartners:item_create', args=[self.project.pk, 'credential']), data)
        self.assertEqual(r.status_code, 302)
        self.client.logout()

    def test_password_and_notes_are_encrypted_at_rest(self):
        from .models import JointCredential
        self.add()
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute(f'SELECT password, notes FROM {JointCredential._meta.db_table}')
            raw = cur.fetchone()
        self.assertTrue(raw[0].startswith('enc1:') and raw[1].startswith('enc1:'))
        self.assertEqual(JointCredential.objects.get().password, 'S3cret-Pass!')

    def test_partner_sees_shared_logins_and_repo_not_hidden_ones(self):
        self.add()
        self.add(name='Internal DB', password='only-us', shared_with_partner='')
        self.client.login(username='p@rt.sa', password='partner-pass-1')
        r = self.client.get(reverse('bizpartners_portal:project', args=[self.project.pk]))
        self.assertContains(r, 'Hostinger VPS')
        self.assertContains(r, 'S3cret-Pass!')
        self.assertContains(r, 'https://github.com/ralfiz/nous-web')
        self.assertNotContains(r, 'Internal DB')
        self.assertNotContains(r, 'only-us')
        self.assertIn('no-cache', r['Cache-Control'])

    def test_another_partner_cannot_open_the_project(self):
        self.add()
        other = User.objects.create_user('o@x.sa', 'o@x.sa', 'other-pass-1')
        BusinessPartner.objects.create(user=other, name='Other')
        self.client.login(username='o@x.sa', password='other-pass-1')
        r = self.client.get(reverse('bizpartners_portal:project', args=[self.project.pk]))
        self.assertEqual(r.status_code, 404)

    def test_staff_page_lists_hidden_ones_too_and_edit_keeps_password(self):
        from .models import JointCredential
        self.add(shared_with_partner='')
        self.client.force_login(self.staff)
        r = self.client.get(reverse('bizpartners:project', args=[self.project.pk]))
        self.assertContains(r, 'Not shown to the partner')
        c = JointCredential.objects.get()
        r = self.client.get(reverse('bizpartners:item_edit', args=[self.project.pk, 'credential', c.pk]))
        self.assertContains(r, 'value="S3cret-Pass!"')
        r = self.client.get(reverse('bizpartners:item_delete', args=[self.project.pk, 'credential', c.pk]))
        self.assertEqual(r.status_code, 200)
        self.client.post(reverse('bizpartners:item_delete', args=[self.project.pk, 'credential', c.pk]))
        self.assertFalse(JointCredential.objects.exists())
