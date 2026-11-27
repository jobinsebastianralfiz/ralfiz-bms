import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import mcq
from .models import Employee, InternAssessment, McqTest, Notification


def _file(data, name='test.json'):
    return SimpleUploadedFile(name, json.dumps(data).encode(), content_type='application/json')


class McqParseTests(TestCase):
    def test_sample_parses_with_all_answer_forms(self):
        data = mcq.parse_upload(json.dumps(mcq.SAMPLE).encode())
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
        return self.client.post(reverse('mcq_test_list'), {'file': _file(data or mcq.SAMPLE), **extra})

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
        self.upload({**mcq.SAMPLE, 'duration_minutes': 5})
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
