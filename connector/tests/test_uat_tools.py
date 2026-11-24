"""UAT connector tools: list/read plans with the same progress the BMS page shows,
handle problems (tester told to retest), create plans with testers per section,
reassign, and complete/reopen."""

from django.test import TestCase

from employees.models import Employee, Notification
from uat.models import UATCase, UATPlan, UATResult, UATSection

from .test_connector import MCPClientMixin, make_employee, make_token


class UATToolTests(MCPClientMixin, TestCase):
    def setUp(self):
        self.owner = make_employee('owner', 'owner')
        self.token = make_token(self.owner)
        make_employee('anu', 'intern')
        make_employee('ravi', 'intern')
        self.anu = Employee.objects.get(user__username='anu')
        self.ravi = Employee.objects.get(user__username='ravi')
        self.plan = UATPlan.objects.create(name='Shop Manager UAT', product='Shop Manager')
        self.plan.testers.set([self.anu, self.ravi])
        self.setup = UATSection.objects.create(plan=self.plan, key='SET', name='Shop setup', order=0)
        self.billing = UATSection.objects.create(plan=self.plan, key='BIL', name='Billing', order=1,
                                                 starts_after=self.setup)
        self.billing.assignees.set([self.anu])
        self.c1 = UATCase.objects.create(section=self.setup, code='SET-01', title='Add shop details')
        self.c2 = UATCase.objects.create(section=self.billing, code='BIL-01', title='Print a bill')
        UATResult.objects.create(case=self.c1, tester=self.anu, status='pass')
        self.fail = UATResult.objects.create(case=self.c2, tester=self.anu, status='fail', note='GST missing')

    def test_tools_are_listed(self):
        names = {t['name'] for t in self.rpc('tools/list', token=self.token.token).json()['result']['tools']}
        for name in ('list_uat_plans', 'get_uat_plan', 'update_uat_problem', 'create_uat_plan',
                     'assign_uat_testers', 'complete_uat_plan'):
            self.assertIn(name, names)

    def test_list_and_detail_match_the_page(self):
        listed = self.ok('list_uat_plans', {'query': 'shop'})
        row = listed['items'][0]
        self.assertEqual((row['failed'], row['open_problems']), (1, 1))
        detail = self.ok('get_uat_plan', {'plan_id': str(self.plan.id)})
        self.assertEqual(detail['tests'], 2)
        billing = next(s for s in detail['sections'] if s['name'] == 'Billing')
        self.assertEqual(billing['assigned'], 'specific testers')
        self.assertEqual(billing['locked_until_done'], 'Shop setup')
        self.assertEqual(detail['problems'][0]['tester_note'], 'GST missing')
        anu = next(t for t in detail['testers'] if 'Anu' in t['name'])
        self.assertEqual(anu['progress'], '2 of 2 (100%)')
        ravi = next(t for t in detail['testers'] if 'Ravi' in t['name'])
        self.assertEqual(ravi['sections'], ['Shop setup'])
        self.assertNotIn('cases', detail)
        full = self.ok('get_uat_plan', {'plan_id': str(self.plan.id), 'include_cases': True})
        self.assertEqual(len(full['cases']), 2)

    def test_marking_fixed_asks_the_tester_to_retest(self):
        out = self.ok('update_uat_problem', {'result_id': str(self.fail.id), 'fix_status': 'fixed',
                                             'note': 'GST added'})
        self.assertTrue(out['tester_notified'])
        self.fail.refresh_from_db()
        self.assertEqual((self.fail.fix_status, self.fail.fixed_by), ('fixed', self.owner))
        self.assertTrue(Notification.objects.filter(employee=self.anu, title__contains='retest BIL-01').exists())
        self.ok('update_uat_problem', {'result_id': str(self.fail.id), 'fix_status': 'open'})
        self.fail.refresh_from_db()
        self.assertEqual((self.fail.fix_status, self.fail.fixed_by), ('', None))

    def test_create_plan_with_section_testers(self):
        out = self.ok('create_uat_plan', {
            'name': 'POS round 2', 'product': 'Coffee POS', 'xp_reward': 50,
            'tester_ids': [str(self.anu.pk), str(self.ravi.pk)],
            'sections': [
                {'name': 'Login', 'key': 'LOG', 'tests': [{'title': 'Sign in', 'steps': ['Open', 'Sign in'],
                                                           'expected': 'Dashboard shows'}]},
                {'name': 'Orders', 'key': 'ORD', 'after': 'LOG', 'assignee_ids': [str(self.ravi.pk)],
                 'tests': [{'title': 'Take an order'}, {'title': 'Cancel an order'}]},
            ]})
        plan = UATPlan.objects.get(name='POS round 2')
        orders = plan.sections.get(key='ORD')
        self.assertEqual(list(orders.assignees.all()), [self.ravi])
        self.assertEqual(orders.starts_after.key, 'LOG')
        self.assertEqual([c.code for c in orders.cases.all()], ['ORD-01', 'ORD-02'])
        self.assertEqual(out['tests'], 3)
        self.assertTrue(out['testers_notified'])
        self.assertTrue(Notification.objects.filter(employee=self.ravi, title='UAT: POS round 2').exists())

    def test_create_rejects_section_tester_not_on_plan(self):
        is_error, message = self.call('create_uat_plan', {
            'name': 'Bad', 'tester_ids': [str(self.anu.pk)],
            'sections': [{'name': 'A', 'assignee_ids': [str(self.ravi.pk)], 'tests': [{'title': 'x'}]}]})
        self.assertTrue(is_error)
        self.assertIn('not in tester_ids', message)
        self.assertFalse(UATPlan.objects.filter(name='Bad').exists())   # rolled back

    def test_assign_by_section_name_notifies_new_testers(self):
        Notification.objects.all().delete()
        self.ok('assign_uat_testers', {'plan_id': str(self.plan.id), 'tester_ids': [str(self.ravi.pk)],
                                       'sections': {'billing': [str(self.ravi.pk)]}})
        self.assertEqual(list(self.plan.testers.all()), [self.ravi])
        self.assertEqual(list(self.billing.assignees.all()), [self.ravi])
        self.assertFalse(Notification.objects.exists())   # Ravi was already on the plan

    def test_complete_and_reopen(self):
        out = self.ok('complete_uat_plan', {'plan_id': str(self.plan.id)})
        self.assertEqual(out['testers_thanked'], 2)
        self.plan.refresh_from_db()
        self.assertTrue(self.plan.is_completed)
        is_error, _ = self.call('complete_uat_plan', {'plan_id': str(self.plan.id)})
        self.assertTrue(is_error)
        self.ok('complete_uat_plan', {'plan_id': str(self.plan.id), 'completed': False})
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.is_completed)
