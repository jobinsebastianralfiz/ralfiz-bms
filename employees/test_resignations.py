"""Resignations: HR link or staff portal -> person signs with a reason ->
HR approves -> person downloads the resignation and the relieving letter."""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from employees.models import Employee, ResignationRequest


class ResignationTests(TestCase):
    def setUp(self):
        self.hr = User.objects.create_superuser('boss', 'boss@example.com', 'pw-123456')
        self.user = User.objects.create_user('asha', password='pw-123456', first_name='Asha', last_name='Nair')
        self.emp = Employee.objects.create(user=self.user, employee_id='EMP901', employment_type='intern',
                                           role='intern', designation='Flutter Intern', phone='9876543210',
                                           joining_date=date(2026, 8, 1), status='active')

    def send(self):
        self.client.force_login(self.hr)
        self.client.post(reverse('resignation_send'), {'employee': self.emp.pk})
        self.client.logout()
        return ResignationRequest.objects.get()

    def sign(self, res, **overrides):
        data = {'reason_category': 'higher_studies', 'reason': 'My final exams start next month.',
                'last_working_day': '2026-11-30', 'signed_name': 'Asha Nair', 'agree': 'on'}
        data.update(overrides)
        return self.client.post(reverse('resignation_form', args=[res.token]), data)

    def test_hr_link_sign_approve_download(self):
        res = self.send()
        self.assertTrue(res.reference.startswith('RT/RES/'))
        page = self.client.get(reverse('resignation_form', args=[res.token]))
        self.assertContains(page, 'Flutter Intern')

        response = self.sign(res)
        self.assertRedirects(response, reverse('resignation_done', args=[res.token]))
        res.refresh_from_db()
        self.assertEqual(res.status, ResignationRequest.STATUS_SUBMITTED)
        self.assertEqual(res.reason_category, 'higher_studies')
        self.assertEqual(len(res.body_hash), 64)

        # Letters stay locked until HR approves.
        self.assertRedirects(self.client.get(reverse('relieving_letter', args=[res.token])),
                             reverse('resignation_done', args=[res.token]))

        self.client.force_login(self.hr)
        self.client.post(reverse('resignation_approve', args=[res.pk]),
                         {'relieving_date': '2026-12-05', 'relieving_note': 'Worked on client apps.'})
        res.refresh_from_db()
        self.assertEqual(res.status, ResignationRequest.STATUS_APPROVED)
        self.assertEqual(res.final_date, date(2026, 12, 5))
        self.emp.refresh_from_db()
        self.assertEqual(self.emp.status, 'active')  # not deactivated unless asked
        self.assertContains(self.client.get(reverse('resignation_detail', args=[res.pk])), 'Send both letters')

        self.client.logout()
        relieving = self.client.get(reverse('relieving_letter', args=[res.token]))
        self.assertContains(relieving, 'RELIEVING LETTER')
        self.assertContains(relieving, '05 Dec 2026')
        self.assertContains(relieving, 'Worked on client apps.')
        letter = self.client.get(reverse('resignation_letter', args=[res.token]))
        self.assertContains(letter, 'My final exams start next month.')
        self.assertContains(letter, 'Accepted by')
        self.assertContains(self.client.get(reverse('resignation_done', args=[res.token])),
                            'Download relieving letter')

    def test_form_validation(self):
        res = self.send()
        response = self.sign(res, reason_category='', reason='short', signed_name='', agree='',
                             last_working_day='2020-01-01')
        self.assertEqual(response.status_code, 400)
        for msg in ('Choose the main reason', 'a little more', 'before your joining date',
                    'Type your full name'):
            self.assertContains(response, msg, status_code=400)

    def test_approve_can_deactivate_login(self):
        res = self.send()
        self.sign(res)
        self.client.force_login(self.hr)
        self.client.post(reverse('resignation_approve', args=[res.pk]),
                         {'relieving_date': '2026-11-30', 'deactivate': 'on'})
        self.emp.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.emp.status, 'inactive')
        self.assertFalse(self.user.is_active)

    def test_reject_shows_reason(self):
        res = self.send()
        self.sign(res)
        self.client.force_login(self.hr)
        self.client.post(reverse('resignation_reject', args=[res.pk]), {'reason': 'Talk to your mentor'})
        self.client.logout()
        done = self.client.get(reverse('resignation_done', args=[res.token]))
        self.assertContains(done, 'Talk to your mentor')
        self.assertNotContains(done, 'Download relieving letter')

    def test_intern_starts_from_staff_portal(self):
        self.client.force_login(self.user)
        page = self.client.get(reverse('staff:resignation'))
        self.assertContains(page, 'Start my resignation')
        response = self.client.post(reverse('staff:resignation'))
        res = ResignationRequest.objects.get()
        self.assertEqual(res.source, 'self')
        self.assertRedirects(response, res.public_path())
        # Posting again reuses the same open request.
        self.client.post(reverse('staff:resignation'))
        self.assertEqual(ResignationRequest.objects.count(), 1)

    def test_hr_send_reuses_open_request(self):
        self.send()
        self.send()
        self.assertEqual(ResignationRequest.objects.count(), 1)

    def test_expired_link_closed(self):
        res = self.send()
        ResignationRequest.objects.filter(pk=res.pk).update(expires_at=timezone.now() - timedelta(days=1))
        self.assertContains(self.client.get(reverse('resignation_form', args=[res.token])), 'expired')

    def test_interns_cannot_reach_hr_pages(self):
        self.client.force_login(self.user)
        self.assertIn(self.client.get(reverse('resignation_list')).status_code, (302, 403))
