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
            'contract_value': '20000', 'partner_share_percent': '40'})
        project = JointProject.objects.get()
        self.assertEqual(project.partner, partner)

        self.client.post(reverse('bizpartners:item_create', args=[project.pk, 'payment']), {
            'kind': 'client_to_ralfiz', 'amount': '10000', 'payment_date': '2026-11-17', 'method': 'bank_transfer'})
        self.client.post(reverse('bizpartners:item_create', args=[project.pk, 'quote']), {
            'title': 'Phase 1', 'amount': '20000', 'quote_date': '2026-11-01', 'status': 'accepted'})
        self.client.post(reverse('bizpartners:item_create', args=[project.pk, 'expense']), {
            'description': 'Hosting', 'amount': '500', 'expense_date': '2026-11-10', 'paid_by': 'ralfiz'})
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

    def test_unknown_item_kind_404(self):
        partner = BusinessPartner.objects.create(name='X')
        project = JointProject.objects.create(partner=partner, title='P')
        self.assertEqual(self.client.get(f'/business-partners/projects/{project.pk}/bogus/new/').status_code, 404)
