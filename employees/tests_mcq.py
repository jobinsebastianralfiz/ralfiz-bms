import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import mcq
from .models import Employee, InternAssessment, McqTest, Notification


MCQ_ONLY = {**mcq.SAMPLE, 'questions': mcq.SAMPLE['questions'][:3]}


def _file(data, name='test.json'):
    return SimpleUploadedFile(name, json.dumps(data).encode(), content_type='application/json')


class McqParseTests(TestCase):
    def test_sample_parses_with_all_answer_forms(self):
        data = mcq.parse_upload(json.dumps(MCQ_ONLY).encode())
        self.assertEqual(data['title'], 'Python Basics - Test 1')
        self.assertEqual(data['duration_minutes'], 20)
        # "B" letter, 2 as option number (1-based), "tuple" as option text
        self.assertEqual([q['answer'] for q in data['questions']], [1, 1, 2])
        self.assertEqual(data['questions'][2]['marks'], 2)

    def test_bare_list_and_dict_options(self):
        data = mcq.parse_upload(json.dumps([
            {'q': 'Pick b', 'choices': {'A': 'a', 'B': 'b'}, 'answer_index': 1}]).encode())
        self.assertEqual(data['questions'][0]['options'], ['a', 'b'])
        self.assertEqual(data['questions'][0]['answer'], 1)
        self.assertEqual(data['title'], '')

    def test_errors_name_the_question(self):
        bad = {'questions': [{'question': 'ok', 'options': ['x', 'y'], 'answer': 'A'},
                             {'question': 'bad', 'options': ['x', 'y'], 'answer': 'Z'}]}
        with self.assertRaisesMessage(mcq.McqFormatError, 'Question 2'):
            mcq.parse_upload(json.dumps(bad).encode())
        with self.assertRaisesMessage(mcq.McqFormatError, 'Not valid JSON'):
            mcq.parse_upload(b'{"questions": [')
        with self.assertRaisesMessage(mcq.McqFormatError, 'at least 2'):
            mcq.parse_upload(json.dumps([{'question': 'x', 'options': ['only'], 'answer': 1}]).encode())
        with self.assertRaisesMessage(mcq.McqFormatError, 'not one of the 2 options'):
            mcq.parse_upload(json.dumps([{'question': 'x', 'options': ['a', 'b'], 'answer': 3}]).encode())


class McqFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('mq_admin', 'a@example.com', 'pw')
        cls.user = User.objects.create_user('mq_intern', password='pw', first_name='Anu')
        cls.intern = Employee.objects.create(user=cls.user, employee_id='MQ01', employment_type='intern',
                                             role='intern', status='active')
        other = User.objects.create_user('mq_other', password='pw')
        cls.other = Employee.objects.create(user=other, employee_id='MQ02', employment_type='intern',
                                            role='intern', status='active')

    def upload(self, data=None, **extra):
        self.client.force_login(self.admin)
        return self.client.post(reverse('mcq_test_list'), {'file': _file(data or MCQ_ONLY), **extra})

    def test_upload_assign_take_and_score(self):
        res = self.upload()
        test = McqTest.objects.get()
        self.assertRedirects(res, reverse('mcq_test_detail', args=[test.pk]))
        self.assertEqual(test.question_count, 3)
        self.assertEqual(test.total_marks, 4)

        self.client.post(reverse('mcq_test_assign', args=[test.pk]), {'employees': [self.intern.pk]})
        a = InternAssessment.objects.get(employee=self.intern, mcq_test=test)
        self.assertTrue(a.mcq_pending)
        self.assertEqual(a.max_score, 4)
        self.assertTrue(Notification.objects.filter(employee=self.intern, title__contains=test.title).exists())
        # Assigning again does not duplicate.
        self.client.post(reverse('mcq_test_assign', args=[test.pk]), {'employees': [self.intern.pk]})
        self.assertEqual(test.assessments.count(), 1)

        # Intern sees it on their dashboard and list.
        self.client.force_login(self.user)
        dash = self.client.get(reverse('staff:dashboard'))
        self.assertContains(dash, 'Tests to take')
        self.assertContains(dash, reverse('staff:assessment_take', args=[a.pk]))
        self.assertContains(self.client.get(reverse('staff:assessment_list')), 'Tests to take')

        take = reverse('staff:assessment_take', args=[a.pk])
        self.assertContains(self.client.get(take), 'Start test')
        self.client.get(take + '?start=1')
        page = self.client.get(take)
        self.assertContains(page, 'name="q_0"')
        # The answer key never reaches the page before submitting.
        self.assertNotContains(page, 'Functions are defined with def')

        # q0 right (B=1, 1 mark), q1 wrong, q2 right (tuple=2, 2 marks) -> 3/4
        res = self.client.post(take, {'q_0': '1', 'q_1': '0', 'q_2': '2'})
        self.assertRedirects(res, reverse('staff:assessment_result', args=[a.pk]))
        a.refresh_from_db()
        self.assertEqual(a.scored, 3)
        self.assertEqual(a.percentage, 75.0)
        self.assertIsNotNone(a.submitted_at)
        result = self.client.get(reverse('staff:assessment_result', args=[a.pk]))
        self.assertContains(result, '75.0%')
        self.assertContains(result, 'Functions are defined with def')

        # Can't take it twice.
        self.client.post(take, {'q_1': '1'})
        a.refresh_from_db()
        self.assertEqual(a.scored, 3)

        # HR sees the result, and the employee page shows it.
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('mcq_test_detail', args=[test.pk])), '75.0%')
        self.assertContains(self.client.get(reverse('emp_employee_detail', args=[self.intern.pk])), 'MCQ')

    def test_other_intern_cannot_open_my_test(self):
        self.upload()
        test = McqTest.objects.get()
        a = mcq.assign(test, [self.intern])[0]
        self.client.force_login(self.other.user)
        self.assertEqual(self.client.get(reverse('staff:assessment_take', args=[a.pk])).status_code, 404)

    def test_timer_expired_submits_empty(self):
        self.upload({**MCQ_ONLY, 'duration_minutes': 5})
        a = mcq.assign(McqTest.objects.get(), [self.intern])[0]
        a.started_at = timezone.now() - timedelta(minutes=30)
        a.save()
        self.client.force_login(self.user)
        self.client.get(reverse('staff:assessment_take', args=[a.pk]))
        a.refresh_from_db()
        self.assertEqual(a.scored, 0)
        self.assertIsNotNone(a.submitted_at)

    def test_give_from_employee_page_and_bad_upload(self):
        res = self.upload({'questions': [{'question': 'x', 'options': ['a'], 'answer': 1}]})
        self.assertEqual(McqTest.objects.count(), 0)
        self.assertIn('Could not read the file', [str(m) for m in res.wsgi_request._messages][0])

        self.upload()
        test = McqTest.objects.get()
        self.client.post(reverse('emp_employee_detail', args=[self.intern.pk]),
                         {'action': 'give_mcq', 'mcq_test': test.pk})
        self.assertTrue(test.assessments.filter(employee=self.intern).exists())

    def test_reset_and_delete_keep_finished_scores(self):
        self.upload()
        test = McqTest.objects.get()
        done, pending = mcq.assign(test, [self.intern, self.other])
        mcq.grade(done, {'0': '1'})
        self.client.post(reverse('mcq_test_delete', args=[test.pk]))
        self.assertFalse(InternAssessment.objects.filter(pk=pending.pk).exists())
        done.refresh_from_db()
        self.assertEqual(done.scored, 1)
        self.assertIsNone(done.mcq_test)


CODE_TEST = {
    'title': 'Coding round', 'proctored': True, 'duration_minutes': 30,
    'questions': [
        {'question': '2 + 2?', 'options': ['3', '4'], 'answer': 'B', 'marks': 1},
        {'type': 'code', 'question': 'Write add(a, b).', 'language': 'python',
         'starter': 'def add(a, b):\n    pass', 'answer': 'def add(a, b):\n    return a + b', 'marks': 5},
        {'type': 'text', 'question': 'What is a list?', 'answer': 'mutable sequence', 'marks': 2},
    ],
}


class WrittenAndProctoredTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('wp_admin', 'w@example.com', 'pw')
        cls.user = User.objects.create_user('wp_intern', password='pw', first_name='Anees')
        cls.intern = Employee.objects.create(user=cls.user, employee_id='WP01', employment_type='intern',
                                             role='intern', status='active')

    def setUp(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('mcq_test_list'), {'file': _file(CODE_TEST)})
        self.test = McqTest.objects.get()
        self.a = mcq.assign(self.test, [self.intern])[0]
        self.client.force_login(self.user)

    def url(self, name):
        return reverse(f'staff:assessment_{name}', args=[self.a.pk])

    def begin(self):
        return self.client.post(self.url('begin')).json()

    def test_parse_written(self):
        self.assertTrue(self.test.proctored)
        self.assertTrue(self.test.has_written)
        self.assertEqual(self.test.kind_label, 'Mixed')
        self.assertEqual(self.test.total_marks, 8)
        with self.assertRaisesMessage(mcq.McqFormatError, 'type "essayx"'):
            mcq.parse_upload(json.dumps([{'type': 'essayx', 'question': 'x'}]).encode())

    def test_gate_hides_questions_until_begin(self):
        gate = self.client.get(self.url('take'))
        self.assertContains(gate, 'Turn on camera')
        self.assertNotContains(gate, 'Write add(a, b)')
        d = self.begin()
        self.assertIn('Write add(a, b)', d['html'])
        self.assertIn('def add(a, b):', d['html'])          # starter code
        self.assertNotIn('return a + b', d['html'])         # model answer never sent
        self.assertNotIn('mutable sequence', d['html'])

    def test_reopening_after_start_locks(self):
        self.begin()
        d = self.begin()   # page reloaded
        self.assertTrue(d['locked'])
        self.a.refresh_from_db()
        self.assertIsNotNone(self.a.locked_at)
        self.assertIn('Reloaded', self.a.lock_reason)

    def test_tab_switch_locks_and_keeps_answers_then_unlock_resumes(self):
        self.begin()
        self.client.post(self.url('autosave'), {'q_0': '1', 'q_1': 'def add(a, b):\n    return a+b'})
        img = SimpleUploadedFile('s.jpg', b'\xff\xd8\xff fakejpeg', content_type='image/jpeg')
        d = self.client.post(self.url('proctor'), {'kind': 'tab_hidden', 'detail': 'x', 'q_2': 'a list',
                                                   'image': img}).json()
        self.assertTrue(d['locked'])
        self.a.refresh_from_db()
        self.assertIsNotNone(self.a.submitted_at)
        self.assertEqual(self.a.answers['1'], 'def add(a, b):\n    return a+b')
        self.assertEqual(self.a.answers['2'], 'a list')
        self.assertEqual(self.a.auto_score, 1)
        self.assertIsNone(self.a.scored)               # written part waits for HR
        self.assertEqual(self.a.snapshots.count(), 1)
        self.assertContains(self.client.get(self.url('result')), 'This test was locked')

        # HR sees it, the still, and unlocks.
        self.client.force_login(self.admin)
        page = self.client.get(reverse('mcq_attempt', args=[self.test.pk, self.a.pk]))
        self.assertContains(page, 'Switched tab')
        snap = self.a.snapshots.get()
        self.assertEqual(self.client.get(reverse('mcq_snapshot', args=[snap.pk])).status_code, 200)
        self.client.post(reverse('mcq_test_update', args=[self.test.pk]),
                         {'action': 'unlock', 'assessment_id': self.a.pk})
        self.a.refresh_from_db()
        self.assertIsNone(self.a.submitted_at)
        self.assertTrue(self.a.resume_allowed)

        # Intern continues once, answers still there.
        self.client.force_login(self.user)
        d = self.begin()
        self.assertIn('return a+b', d['html'])
        self.assertIn('a list', d['html'])
        self.assertTrue(self.begin()['locked'])        # a second reopen locks again

    def test_flags_do_not_lock(self):
        self.begin()
        d = self.client.post(self.url('proctor'), {'kind': 'no_face'}).json()
        self.assertFalse(d['locked'])
        self.a.refresh_from_db()
        self.assertIsNone(self.a.locked_at)
        self.assertEqual(self.a.flag_count, 1)

    def test_submit_then_hr_marks(self):
        self.begin()
        self.client.post(self.url('take'), {'q_0': '1', 'q_1': 'def add(a,b): return a+b', 'q_2': 'changeable'})
        self.a.refresh_from_db()
        self.assertTrue(self.a.needs_marking)
        self.assertContains(self.client.get(self.url('result')), 'Waiting for marking')

        self.client.force_login(self.admin)
        url = reverse('mcq_attempt', args=[self.test.pk, self.a.pk])
        self.assertContains(self.client.get(url), 'return a + b')   # model answer for HR
        self.client.post(url, {'mark_1': '4', 'comment_1': 'Good', 'mark_2': ''})
        self.a.refresh_from_db()
        self.assertIsNone(self.a.scored)                             # one still unmarked
        self.client.post(url, {'mark_1': '4', 'comment_1': 'Good', 'mark_2': '9'})  # capped at 2
        self.a.refresh_from_db()
        self.assertEqual(self.a.scored, 7)                           # 1 + 4 + 2
        self.client.force_login(self.user)
        res = self.client.get(self.url('result'))
        self.assertContains(res, 'Good')
        self.assertContains(res, '87.5%')

    def test_retake_clears_everything(self):
        self.begin()
        self.client.post(self.url('proctor'), {'kind': 'tab_hidden'})
        self.client.force_login(self.admin)
        self.client.post(reverse('mcq_test_update', args=[self.test.pk]),
                         {'action': 'reset', 'assessment_id': self.a.pk})
        self.a.refresh_from_db()
        self.assertEqual((self.a.violations, self.a.answers, self.a.started_at, self.a.locked_at), ([], {}, None, None))


class EmployeeTestsTests(TestCase):
    def test_employee_can_be_given_and_take_a_test(self):
        admin = User.objects.create_superuser('et_admin', 'e@example.com', 'pw')
        u = User.objects.create_user('et_emp', password='pw', first_name='Ravi')
        emp = Employee.objects.create(user=u, employee_id='ET01', employment_type='fulltime',
                                      role='employee', status='active', designation='Developer')
        owner_u = User.objects.create_user('et_owner', password='pw')
        Employee.objects.create(user=owner_u, employee_id='ET02', employment_type='fulltime', role='owner',
                                status='active')
        self.client.force_login(admin)
        self.client.post(reverse('mcq_test_list'), {'file': _file(MCQ_ONLY)})
        test = McqTest.objects.get()
        page = self.client.get(reverse('mcq_test_detail', args=[test.pk]))
        self.assertContains(page, 'All employees')
        self.assertContains(page, 'Ravi')
        self.assertNotContains(page, 'ET02')                 # owners are not offered
        self.client.post(reverse('mcq_test_assign', args=[test.pk]), {'employees': [emp.pk]})
        a = test.assessments.get(employee=emp)
        self.assertContains(self.client.get(reverse('emp_employee_detail', args=[emp.pk])), 'Give an online MCQ test')

        self.client.force_login(u)
        self.assertContains(self.client.get(reverse('staff:dashboard')), 'Tests to take')
        self.assertContains(self.client.get(reverse('staff:dashboard')), reverse('staff:assessment_list'))
        self.client.get(reverse('staff:assessment_take', args=[a.pk]) + '?start=1')
        self.client.post(reverse('staff:assessment_take', args=[a.pk]), {'q_0': '1', 'q_1': '1', 'q_2': '2'})
        a.refresh_from_db()
        self.assertEqual(a.scored, 4)
