import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from employees.models import Employee, Notification

from .models import UATPlan, UATResult

MEDIA = tempfile.mkdtemp()
PNG = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
       b'\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')


@override_settings(MEDIA_ROOT=MEDIA)
class UATTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pw = 'uat-pass-123'
        cls.emps = []
        for i, name in enumerate(['Hamitha', 'Fathima', 'Mithra'], start=14):
            u = User.objects.create_user(username=f'u{i}', password=cls.pw, first_name=name)
            cls.emps.append(Employee.objects.create(user=u, employee_id=f'EMP0{i}', employment_type='intern',
                                                    role='intern', status='active'))
        cls.hr = User.objects.create_user(username='hr', password=cls.pw, is_staff=True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def load(self):
        call_command('load_uat_plan', 'uat/data/shop_manager_uat.json', '--due', '2026-11-13', '--notify',
                     '--owner', 'Admin=EMP014', '--owner', 'Intern 1=EMP014', '--owner', 'Intern 2=EMP015',
                     '--owner', 'Intern 3=EMP016', stdout=io.StringIO())
        return UATPlan.objects.get()

    def finish_setup(self, plan):
        for case in plan.sections.get(key='SETUP').cases.all():
            UATResult.objects.create(case=case, tester=self.emps[0], status='pass')

    def test_load_assigns_sections_and_notifies(self):
        plan = self.load()
        self.assertEqual(plan.cases().count(), 93)
        ham, fat, mit = self.emps
        billing = plan.sections.get(key='BIL')
        self.assertEqual([e.pk for e in billing.testers()], [fat.pk])
        everyone = plan.sections.get(key='GEN0')
        self.assertEqual(len(everyone.testers()), 3)  # "Everyone" sections go to all testers
        self.assertEqual(Notification.objects.filter(notification_type='work', title__startswith='UAT').count(), 3)

    def test_intern_sees_only_own_sections_and_records_results(self):
        plan = self.load()
        ham, fat, _ = self.emps
        self.client.login(username='u15', password=self.pw)  # Fathima
        home = self.client.get(reverse('staff:uat_home'))
        self.assertContains(home, 'Billing counter')
        self.assertNotContains(home, 'More settings')
        sett = plan.sections.get(key='SET')
        self.assertEqual(self.client.get(reverse('staff:uat_section', args=[plan.pk, sett.pk])).status_code, 404)
        self.finish_setup(plan)

        billing = plan.sections.get(key='BIL')
        url = reverse('staff:uat_section', args=[plan.pk, billing.pk])
        page = self.client.get(url)
        self.assertContains(page, 'Expected result')
        case = billing.cases.first()
        ajax = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        r = self.client.post(url, {'case': case.pk, 'status': 'fail', 'note': ''}, **ajax)
        self.assertEqual(r.status_code, 400)  # Fail needs a note
        r = self.client.post(url, {'case': case.pk, 'status': 'fail', 'note': 'Total wrong',
                                   'screenshot': SimpleUploadedFile('s.png', PNG, 'image/png')}, **ajax)
        self.assertEqual((r.status_code, r.json()['done']), (200, 1))
        res = UATResult.objects.get(tester=fat)
        self.assertTrue(res.screenshot.name.startswith('uat/screens/'))
        r = self.client.post(url, {'case': case.pk, 'status': 'pass', 'note': ''}, **ajax)
        res.refresh_from_db()
        self.assertEqual((res.status, len(res.history), UATResult.objects.filter(tester=fat).count()), ("pass", 1, 1))

    def test_dashboard_progress_and_fix_flow(self):
        plan = self.load()
        fat = self.emps[1]
        case = plan.sections.get(key='BIL').cases.first()
        res = UATResult(case=case, tester=fat)
        res.record('blocked', 'Printer not found')
        self.client.login(username='hr', password=self.pw)
        page = self.client.get(reverse('uat_plan_detail', args=[plan.pk]))
        self.assertContains(page, 'Printer not found')
        self.assertContains(page, 'Fathima')
        self.assertEqual(self.client.get(reverse('uat_plan_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('uat_plan_cases', args=[plan.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('uat_plan_create')).status_code, 200)

        self.client.post(reverse('uat_problem_update', args=[res.pk]), {'fix_status': 'fixed', 'fix_note': 'Driver added'})
        res.refresh_from_db()
        self.assertTrue(res.needs_retest)
        self.assertTrue(Notification.objects.filter(employee=fat, title__contains=case.code).exists())

        self.client.logout()
        self.client.login(username='u15', password=self.pw)
        self.assertContains(self.client.get(reverse('staff:uat_home')), 'please test again')
        res.record('pass', '')
        self.assertFalse(res.needs_retest)

    def test_reassign_and_close(self):
        plan = self.load()
        ham, fat, mit = self.emps
        self.client.login(username='hr', password=self.pw)
        bil = plan.sections.get(key='BIL')
        data = {'action': 'assign', 'testers': [e.pk for e in self.emps], f'section_{bil.pk}': [mit.pk]}
        self.client.post(reverse('uat_plan_update', args=[plan.pk]), data)
        self.assertEqual([e.pk for e in bil.testers()], [mit.pk])
        self.client.post(reverse('uat_plan_update', args=[plan.pk]),
                         {'action': 'details', 'name': plan.name, 'status': 'closed'})
        self.client.logout()
        self.client.login(username='u16', password=self.pw)
        self.assertContains(self.client.get(reverse('staff:uat_home')), 'No testing assigned')

    def test_create_plan_from_dashboard_with_file(self):
        self.client.login(username='hr', password=self.pw)
        f = SimpleUploadedFile('c.json', b'{"sections":[{"name":"Login","tests":[{"code":"L1","title":"Log in",'
                                         b'"steps":["Open"],"expected":"Works"}]}]}', 'application/json')
        r = self.client.post(reverse('uat_plan_create'), {'name': 'Mini', 'testers': [self.emps[0].pk], 'cases_json': f})
        plan = UATPlan.objects.get(name='Mini')
        self.assertRedirects(r, reverse('uat_plan_detail', args=[plan.pk]))
        self.assertEqual(plan.cases().count(), 1)

    def test_login_required(self):
        self.assertEqual(self.client.get(reverse('uat_plan_list')).status_code, 302)
        self.assertEqual(self.client.get(reverse('staff:uat_home')).status_code, 302)


    def test_sections_wait_for_shop_setup(self):
        plan = self.load()
        setup, billing = plan.sections.get(key='SETUP'), plan.sections.get(key='BIL')
        self.assertEqual(billing.starts_after, setup)
        self.assertEqual([e.pk for e in setup.testers()], [self.emps[0].pk])
        self.client.login(username='u15', password=self.pw)  # Fathima, billing
        home = self.client.get(reverse('staff:uat_home'))
        self.assertContains(home, 'Locked until')
        self.assertContains(home, 'class="ut-dock"')
        url = reverse('staff:uat_section', args=[plan.pk, billing.pk])
        self.assertContains(self.client.get(url), '<b>Locked.</b>')
        ajax = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        r = self.client.post(url, {'case': billing.cases.first().pk, 'status': 'pass'}, **ajax)
        self.assertEqual(r.status_code, 400)
        cases = list(setup.cases.all())
        for case in cases[:-1]:
            UATResult.objects.create(case=case, tester=self.emps[0], status='pass')
        self.assertIsNotNone(billing.waiting_on())  # one setup test still unmarked
        UATResult.objects.create(case=cases[-1], tester=self.emps[0], status='blocked', note='printer off')
        self.assertIsNone(billing.waiting_on())  # blocked counts as marked
        self.assertNotContains(self.client.get(url), '<b>Locked.</b>')
        r = self.client.post(url, {'case': billing.cases.first().pk, 'status': 'pass'}, **ajax)
        self.assertEqual(r.status_code, 200)

    def test_replace_keeps_results(self):
        plan = self.load()
        case = plan.sections.get(key='GEN0').cases.get(code='GS-01')
        UATResult.objects.create(case=case, tester=self.emps[1], status='fail', note='padlock missing')
        out = io.StringIO()
        call_command('load_uat_plan', 'uat/data/shop_manager_uat.json', '--replace',
                     '--owner', 'Admin=EMP014', '--owner', 'Intern 1=EMP014', '--owner', 'Intern 2=EMP015',
                     '--owner', 'Intern 3=EMP016', stdout=out)
        new = UATPlan.objects.get()
        self.assertNotEqual(new.pk, plan.pk)
        self.assertEqual(str(new.due_date), '2026-11-13')
        r = UATResult.objects.get()
        self.assertEqual((r.case.section.plan_id, r.case.code, r.note), (new.pk, 'GS-01', 'padlock missing'))
        self.assertIn('Kept 1 of 1', out.getvalue())
