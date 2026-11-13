from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from crm.models import Lead
from employees.models import Employee, InternAssessment, Notification, Payroll, WorkAssignment
from uat.models import UATCase, UATPlan, UATResult, UATSection

from . import services
from .models import XPEntry, XPPayout, XPSettings
from .services import WalletError


def make_person(username, role='intern', **kw):
    u = User.objects.create_user(username=username, password='pw-12345', first_name=username.title())
    return Employee.objects.create(user=u, employee_id=f'E-{username}', role=role,
                                   employment_type='intern' if role == 'intern' else 'fulltime',
                                   status='active', **kw)


class WalletTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hr = User.objects.create_user(username='hr', password='pw-12345', is_staff=True)
        cls.anu = make_person('anu')
        cls.ben = make_person('ben')
        cls.staffer = make_person('sam', role='employee', monthly_salary=Decimal('20000'))

    def work(self, people, priority='medium', status='assigned', xp=None):
        w = WorkAssignment.objects.create(title='Build the login page', priority=priority, status=status,
                                          xp_reward=xp, assigned_by=self.hr)
        w.assigned_to.set(people)
        return w

    def complete(self, w):
        w.status = 'completed'
        w.save()
        return w


class LedgerTests(WalletTestCase):
    def test_completed_work_creates_pending_not_balance(self):
        self.complete(self.work([self.anu], priority='high'))
        e = XPEntry.objects.get(employee=self.anu)
        self.assertEqual((e.status, e.xp, e.suggested_xp, e.source_kind), ('pending', 200, 200, 'work'))
        self.assertEqual(services.balance(self.anu), 0)
        self.assertEqual(services.pending(self.anu), 200)

    def test_xp_field_overrides_priority_and_each_assignee_gets_own_row(self):
        self.complete(self.work([self.anu, self.ben], priority='low', xp=1000))
        self.assertEqual(sorted(XPEntry.objects.values_list('xp', flat=True)), [1000, 1000])

    def test_same_work_cannot_pay_twice(self):
        w = self.complete(self.work([self.anu]))
        w.save()
        self.complete(w)
        self.assertEqual(XPEntry.objects.filter(employee=self.anu).count(), 1)
        e = XPEntry.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            XPEntry.objects.create(employee=self.anu, xp=5, kind='earned', content_type=e.content_type,
                                   object_id=e.object_id, title='dup')

    def test_employees_have_wallets_unless_switched_off(self):
        self.complete(self.work([self.staffer]))
        self.assertEqual(XPEntry.objects.filter(employee=self.staffer).count(), 1)
        s = XPSettings.current()
        s.include_employees = False
        s.save()
        self.complete(self.work([self.staffer]))
        self.assertEqual(XPEntry.objects.filter(employee=self.staffer).count(), 1)
        owner = make_person('olivia', role='owner')
        self.assertFalse(services.has_wallet(owner))

    def test_balance_is_sum_of_approved_rows(self):
        self.complete(self.work([self.anu], priority='high'))
        services.approve(XPEntry.objects.get(), self.hr)
        services.adjust(self.anu, self.hr, 30, 'Helped a teammate')
        services.adjust(self.anu, self.hr, -10, 'Late report')
        self.complete(self.work([self.anu]))  # still pending
        self.assertEqual(services.balance(self.anu), 220)
        self.assertEqual(services.balance(self.anu), sum(XPEntry.objects.filter(
            employee=self.anu, status='approved').values_list('xp', flat=True)))

    def test_approve_with_new_amount_needs_reason_and_notifies(self):
        self.complete(self.work([self.anu, self.ben], xp=100))
        a, b = XPEntry.objects.get(employee=self.anu), XPEntry.objects.get(employee=self.ben)
        with self.assertRaises(WalletError):
            services.approve(a, self.hr, xp=60)
        services.approve(a, self.hr, xp=60, note='Split 60/40')
        services.approve(b, self.hr, xp=40, note='Split 60/40')
        a.refresh_from_db()
        self.assertEqual((a.xp, a.suggested_xp, a.decided_by), (60, 100, self.hr))
        self.assertTrue(Notification.objects.filter(employee=self.anu, title='XP approved').exists())

    def test_reject_needs_reason(self):
        self.complete(self.work([self.anu]))
        e = XPEntry.objects.get()
        with self.assertRaises(WalletError):
            services.reject(e, self.hr, '')
        services.reject(e, self.hr, 'Not finished properly')
        self.assertEqual(services.pending(self.anu), 0)
        with self.assertRaises(WalletError):
            services.approve(e, self.hr)

    def test_reopened_task_reverses_approved_xp(self):
        w = self.complete(self.work([self.anu]))
        services.approve(XPEntry.objects.get(), self.hr)
        w.status = 'in_progress'
        w.save()
        self.assertEqual(services.balance(self.anu), 0)
        rev = XPEntry.objects.get(kind='reversal')
        self.assertEqual(rev.xp, -100)
        # Finished again: asks for approval once more, never twice.
        self.complete(w)
        self.complete(w)
        self.assertEqual(XPEntry.objects.filter(status='pending').count(), 1)

    def test_reopened_before_approval_closes_pending_then_reopens_it(self):
        w = self.complete(self.work([self.anu]))
        w.status = 'cancelled'
        w.save()
        e = XPEntry.objects.get()
        self.assertEqual((e.status, e.closed_by_system), ('rejected', True))
        self.complete(w)
        e.refresh_from_db()
        self.assertEqual(e.status, 'pending')

    def test_hr_rejection_is_not_asked_again(self):
        w = self.complete(self.work([self.anu]))
        services.reject(XPEntry.objects.get(), self.hr, 'No')
        w.status = 'in_progress'
        w.save()
        self.complete(w)
        self.assertEqual(XPEntry.objects.get().status, 'rejected')

    def test_balance_never_below_zero(self):
        services.adjust(self.anu, self.hr, 50, 'Bonus')
        with self.assertRaises(WalletError):
            services.adjust(self.anu, self.hr, -60, 'Too much')
        # Reversal after it was paid out takes back only what is left.
        w = self.complete(self.work([self.anu]))
        services.approve(XPEntry.objects.get(kind='earned'), self.hr)
        services.cash_out(self.anu, self.hr, 120, 'cash')
        w.status = 'in_progress'
        w.save()
        self.assertEqual(services.balance(self.anu), 0)
        self.assertIn('already been paid out', XPEntry.objects.get(kind='reversal').note)

    def test_monthly_cap(self):
        s = XPSettings.current()
        s.monthly_cap = 150
        s.save()
        self.complete(self.work([self.anu]))
        self.complete(self.work([self.anu]))
        first, second = XPEntry.objects.filter(employee=self.anu).order_by('created_at')
        services.approve(first, self.hr)
        with self.assertRaises(WalletError):
            services.approve(second, self.hr)
        services.approve(second, self.hr, xp=50, note='Cap')
        self.assertEqual(services.balance(self.anu), 150)


class SourceTests(WalletTestCase):
    def uat_plan(self, xp=600):
        plan = UATPlan.objects.create(name='Shop UAT', xp_reward=xp)
        plan.testers.set([self.anu, self.ben])
        s1 = UATSection.objects.create(plan=plan, name='Setup')
        s1.assignees.set([self.anu])
        s2 = UATSection.objects.create(plan=plan, name='Billing')
        cases = [UATCase.objects.create(section=s1, code='S-1', title='a'),
                 UATCase.objects.create(section=s2, code='B-1', title='b'),
                 UATCase.objects.create(section=s2, code='B-2', title='c')]
        return plan, cases

    def test_uat_reward_once_tester_marks_all_their_tests(self):
        plan, (s1, b1, b2) = self.uat_plan()
        UATResult.objects.create(case=b1, tester=self.ben, status='fail', note='x')
        self.assertFalse(XPEntry.objects.filter(employee=self.ben).exists())
        UATResult.objects.create(case=b2, tester=self.ben, status='pass')
        self.assertEqual(XPEntry.objects.get(employee=self.ben).xp, 600)  # fails don't change it
        for c in (s1, b1):
            UATResult.objects.create(case=c, tester=self.anu, status='pass')
        self.assertFalse(XPEntry.objects.filter(employee=self.anu).exists())
        r = UATResult.objects.create(case=b2, tester=self.anu, status='pass')
        r.record('pass', 'again')
        self.assertEqual(XPEntry.objects.filter(employee=self.anu).count(), 1)

    def test_uat_reward_when_plan_is_marked_completed(self):
        plan, (s1, b1, b2) = self.uat_plan()
        UATResult.objects.create(case=b1, tester=self.ben, status='pass')  # ben left B-2 unmarked; anu tested nothing
        self.assertFalse(XPEntry.objects.exists())
        plan.set_completed(True)
        plan.save()
        self.assertEqual(XPEntry.objects.get().employee, self.ben)
        self.assertEqual(XPEntry.objects.get().status, 'pending')
        plan.set_completed(False)
        plan.save()
        plan.set_completed(True)
        plan.save()
        self.assertEqual(XPEntry.objects.count(), 1)

    def test_uat_reward_set_after_finishing_still_arrives(self):
        plan, (_, b1, b2) = self.uat_plan(xp=0)
        for c in (b1, b2):
            UATResult.objects.create(case=c, tester=self.ben, status='pass')
        self.assertFalse(XPEntry.objects.exists())
        plan.xp_reward = 400
        plan.save()
        self.assertEqual(XPEntry.objects.get(employee=self.ben).xp, 400)

    def test_assessment_score_percent(self):
        a = InternAssessment.objects.create(employee=self.anu, title='Test 1', max_score=40)
        self.assertFalse(XPEntry.objects.exists())
        a.scored = 34
        a.save()
        self.assertEqual(XPEntry.objects.get().xp, 85)
        a.scored = 36  # regraded before approval: suggestion follows
        a.save()
        self.assertEqual(XPEntry.objects.get().xp, 90)

    def test_converted_lead(self):
        lead = Lead.objects.create(contact_person='Raj', phone='9999999999', created_by=self.anu.user)
        self.assertFalse(XPEntry.objects.exists())
        lead.status = 'converted'
        lead.save()
        e = XPEntry.objects.get()
        self.assertEqual((e.xp, e.source_kind), (500, 'lead'))


class PayoutTests(WalletTestCase):
    def setUp(self):
        services.adjust(self.anu, self.hr, 1000, 'Start')

    def test_payout_freezes_rate(self):
        p = services.cash_out(self.anu, self.hr, 600, 'upi', reference='UPI123')
        s = XPSettings.current()
        s.rate_paise = 100
        s.save()
        p.refresh_from_db()
        self.assertEqual((p.amount, p.rate_paise), (Decimal('300.00'), 50))
        self.assertEqual(XPEntry.objects.get(kind='payout').rate_paise, 50)
        self.assertEqual(services.balance(self.anu), 400)
        self.assertEqual(services.paid_total(self.anu), 600)

    def test_cannot_cash_out_more_than_balance(self):
        with self.assertRaises(WalletError):
            services.cash_out(self.anu, self.hr, 1001, 'cash')

    def test_payslip_payout_has_its_own_line_and_survives_bonus_edit(self):
        today = timezone.localdate()
        services.cash_out(self.anu, self.hr, 400, 'payslip', month=today.month, year=today.year)
        pr = Payroll.objects.get(employee=self.anu)
        self.assertEqual((pr.xp_payout, pr.net_pay), (Decimal('200.00'), Decimal('200.00')))
        pr.bonus = Decimal('50')
        pr.calculate()
        pr.save()
        self.assertEqual((pr.xp_payout, pr.net_pay), (Decimal('200.00'), Decimal('250.00')))

    def test_deleting_payslip_puts_xp_back(self):
        today = timezone.localdate()
        services.cash_out(self.anu, self.hr, 400, 'payslip', month=today.month, year=today.year)
        Payroll.objects.get(employee=self.anu).delete()
        self.assertEqual(services.balance(self.anu), 1000)
        self.assertEqual(XPPayout.objects.get().status, 'undone')

    def test_undo_separate_payment(self):
        p = services.cash_out(self.anu, self.hr, 400, 'cash')
        services.undo_payout(p, self.hr, 'Paid twice by mistake')
        self.assertEqual(services.balance(self.anu), 1000)
        with self.assertRaises(WalletError):
            services.undo_payout(p, self.hr, 'again')

    def test_paid_payslip_is_locked(self):
        today = timezone.localdate()
        p = services.cash_out(self.anu, self.hr, 100, 'payslip', month=today.month, year=today.year)
        Payroll.objects.filter(pk=p.payroll_id).update(status='paid')
        with self.assertRaises(WalletError):
            services.cash_out(self.anu, self.hr, 100, 'payslip', month=today.month, year=today.year)
        with self.assertRaises(WalletError):
            services.undo_payout(p, self.hr, 'oops')


class PageTests(WalletTestCase):
    def test_intern_wallet_page_and_home_card(self):
        services.adjust(self.anu, self.hr, 600, 'Great demo')
        self.client.login(username='anu', password='pw-12345')
        r = self.client.get(reverse('staff:wallet'))
        self.assertContains(r, '600 XP')
        self.assertContains(r, '₹300')
        self.assertContains(r, 'Great demo')
        self.assertContains(self.client.get(reverse('staff:dashboard')), 'Your XP Wallet')

    def test_employee_wallet_shows_and_can_be_switched_off(self):
        self.client.login(username='sam', password='pw-12345')
        self.assertEqual(self.client.get(reverse('staff:wallet')).status_code, 200)
        XPSettings.objects.update(include_employees=False)
        self.assertEqual(self.client.get(reverse('staff:wallet')).status_code, 404)
        self.assertNotContains(self.client.get(reverse('staff:dashboard')), 'Your XP Wallet')

    def test_interns_cannot_open_hr_pages(self):
        self.client.login(username='anu', password='pw-12345')
        for name in ('wallet:approvals', 'wallet:list', 'wallet:settings'):
            self.assertNotEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_hr_flow(self):
        self.client.login(username='hr', password='pw-12345')
        w = self.work([self.anu, self.ben], xp=100)
        self.client.post(reverse('emp_work_detail', args=[w.pk]), {
            'title': w.title, 'priority': 'medium', 'status': 'completed', 'xp_reward': '100',
            'employees': [self.anu.pk, self.ben.pk]})
        r = self.client.get(reverse('wallet:approvals'))
        self.assertContains(r, 'also on it: Ben')
        ids = list(XPEntry.objects.values_list('pk', flat=True))
        self.client.post(reverse('wallet:decide'), {'action': 'approve_selected', 'entries': ids})
        self.assertEqual(services.balance(self.anu), 100)
        r = self.client.post(reverse('wallet:detail', args=[self.anu.pk]),
                             {'action': 'cash_out', 'xp': '100', 'method': 'upi', 'reference': 'R1'}, follow=True)
        self.assertContains(r, 'Paid out 100 XP = ₹50')
        self.assertContains(self.client.get(reverse('wallet:list')), 'Anu')
        r = self.client.post(reverse('wallet:settings'), {
            'rate_paise': '25', 'xp_low': '10', 'xp_medium': '20', 'xp_high': '30', 'xp_urgent': '40',
            'xp_lead_converted': '5', 'monthly_cap': '0', 'xp_per_assessment_percent': '1'}, follow=True)
        self.assertContains(r, '4 XP = ₹1')
