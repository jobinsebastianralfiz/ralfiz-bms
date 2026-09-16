"""Tests for the daily update -- what each person did and learned that day.

Covers the API the Flutter app calls, the staff portal page, and the HR feed.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import DailyReport, DailyReportComment, Employee, Notification


class DailyReportTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'daily-pass-123'

        cls.intern_user = User.objects.create_user(
            username='dr_intern', password=cls.password, first_name='Asha', last_name='Nair')
        cls.intern = Employee.objects.create(
            user=cls.intern_user, employee_id='DR001',
            employment_type='intern', role='intern', status='active')

        cls.peer_user = User.objects.create_user(
            username='dr_peer', password=cls.password, first_name='Ravi')
        cls.peer = Employee.objects.create(
            user=cls.peer_user, employee_id='DR002',
            employment_type='fulltime', role='employee', status='active')

        cls.hr_user = User.objects.create_user(
            username='dr_hr', password=cls.password, first_name='Jobin', is_staff=True)

        cls.today = timezone.localdate()

    def login_intern(self):
        self.client.login(username='dr_intern', password=self.password)


class DailyReportAPITests(DailyReportTestBase):
    url = '/api/employees/daily-reports/'

    def test_create_todays_report(self):
        self.login_intern()
        res = self.client.post(self.url, {
            'work_done': 'Built the lead import screen.',
            'learned': 'How Django form wizards keep state.',
        }, content_type='application/json')

        self.assertEqual(res.status_code, 201)
        report = DailyReport.objects.get(employee=self.intern)
        self.assertEqual(report.date, self.today)
        self.assertEqual(report.learned, 'How Django form wizards keep state.')

    def test_work_done_is_required(self):
        self.login_intern()
        res = self.client.post(self.url, {'work_done': '   ', 'learned': 'Something'},
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertFalse(DailyReport.objects.exists())

    def test_posting_twice_for_a_day_updates_instead_of_erroring(self):
        self.login_intern()
        self.client.post(self.url, {'work_done': 'First draft'},
                         content_type='application/json')
        res = self.client.post(self.url, {'work_done': 'Fuller version', 'blockers': 'Need API keys'},
                               content_type='application/json')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(DailyReport.objects.filter(employee=self.intern).count(), 1)
        report = DailyReport.objects.get(employee=self.intern)
        self.assertEqual(report.work_done, 'Fuller version')
        self.assertEqual(report.blockers, 'Need API keys')

    def test_cannot_file_for_a_future_date(self):
        self.login_intern()
        res = self.client.post(self.url, {
            'date': str(self.today + timedelta(days=1)),
            'work_done': 'Time travel',
        }, content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_cannot_file_for_a_date_more_than_a_week_back(self):
        self.login_intern()
        res = self.client.post(self.url, {
            'date': str(self.today - timedelta(days=9)),
            'work_done': 'Catching up late',
        }, content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_list_only_returns_my_own_reports(self):
        DailyReport.objects.create(employee=self.intern, date=self.today, work_done='Mine')
        DailyReport.objects.create(employee=self.peer, date=self.today, work_done='Theirs')

        self.login_intern()
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        bodies = [r['work_done'] for r in res.json()['results']] \
            if isinstance(res.json(), dict) else [r['work_done'] for r in res.json()]
        self.assertEqual(bodies, ['Mine'])

    def test_an_old_report_can_no_longer_be_edited(self):
        old = DailyReport.objects.create(
            employee=self.intern, date=self.today - timedelta(days=5), work_done='Old news')
        self.login_intern()
        res = self.client.patch(f'{self.url}{old.id}/', {'work_done': 'Rewritten'},
                                content_type='application/json')
        self.assertEqual(res.status_code, 400)
        old.refresh_from_db()
        self.assertEqual(old.work_done, 'Old news')

    def test_yesterdays_report_is_still_editable(self):
        yesterday = DailyReport.objects.create(
            employee=self.intern, date=self.today - timedelta(days=1), work_done='Draft')
        self.login_intern()
        res = self.client.patch(f'{self.url}{yesterday.id}/', {'work_done': 'Tidied up'},
                                content_type='application/json')
        self.assertEqual(res.status_code, 200)
        yesterday.refresh_from_db()
        self.assertEqual(yesterday.work_done, 'Tidied up')

    def test_cannot_read_someone_elses_report(self):
        theirs = DailyReport.objects.create(
            employee=self.peer, date=self.today, work_done='Private')
        self.login_intern()
        res = self.client.get(f'{self.url}{theirs.id}/')
        self.assertEqual(res.status_code, 404)


class DailyReportCommentTests(DailyReportTestBase):
    def setUp(self):
        self.report = DailyReport.objects.create(
            employee=self.intern, date=self.today, work_done='Shipped the invoice fix')
        self.url = f'/api/employees/daily-reports/{self.report.id}/comments/'

    def test_hr_reply_notifies_the_author(self):
        self.client.login(username='dr_hr', password=self.password)
        res = self.client.post(self.url, {'message': 'Nice work on that fix.'},
                               content_type='application/json')

        self.assertEqual(res.status_code, 201)
        self.assertEqual(self.report.comments.count(), 1)
        note = Notification.objects.get(employee=self.intern)
        self.assertIn('replied to your daily update', note.title)
        self.assertEqual(note.data['report_id'], str(self.report.id))

    def test_author_can_reply_without_notifying_themselves(self):
        self.login_intern()
        res = self.client.post(self.url, {'message': 'Adding a detail I forgot.'},
                               content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertFalse(Notification.objects.exists())

    def test_an_unrelated_employee_cannot_comment(self):
        self.client.login(username='dr_peer', password=self.password)
        res = self.client.post(self.url, {'message': 'Butting in'},
                               content_type='application/json')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(self.report.comments.count(), 0)

    def test_empty_message_is_rejected(self):
        self.login_intern()
        res = self.client.post(self.url, {'message': '  '}, content_type='application/json')
        self.assertEqual(res.status_code, 400)


class AdminDailyReportAPITests(DailyReportTestBase):
    url = '/api/employees/admin/daily-reports/'

    def setUp(self):
        DailyReport.objects.create(employee=self.intern, date=self.today,
                                   work_done='Lead screen', blockers='Waiting on design')
        DailyReport.objects.create(employee=self.peer, date=self.today, work_done='Payroll run')

    def _rows(self, res):
        data = res.json()
        return data['results'] if isinstance(data, dict) and 'results' in data else data

    def test_hr_sees_everyone(self):
        self.client.login(username='dr_hr', password=self.password)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(self._rows(res)), 2)

    def test_a_plain_employee_sees_nothing_in_the_admin_feed(self):
        self.login_intern()
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(self._rows(res)), 0)

    def test_blockers_filter(self):
        self.client.login(username='dr_hr', password=self.password)
        res = self.client.get(self.url, {'blockers': '1'})
        rows = self._rows(res)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['blockers'], 'Waiting on design')

    def test_missing_endpoint_lists_who_has_not_filed(self):
        third_user = User.objects.create_user(username='dr_third', password=self.password,
                                              first_name='Meera')
        Employee.objects.create(user=third_user, employee_id='DR003',
                                employment_type='fulltime', role='employee', status='active')

        self.client.login(username='dr_hr', password=self.password)
        res = self.client.get('/api/employees/admin/daily-reports/missing/')
        self.assertEqual(res.status_code, 200)
        names = [m['employee_id'] for m in res.json()['missing']]
        self.assertEqual(names, ['DR003'])


class StaffPortalDailyReportTests(DailyReportTestBase):
    def test_page_lists_my_reports(self):
        DailyReport.objects.create(employee=self.intern, date=self.today,
                                   work_done='Wrote the import parser',
                                   learned='csv.DictReader keeps the header')
        DailyReport.objects.create(employee=self.peer, date=self.today, work_done='Not mine')

        self.login_intern()
        res = self.client.get(reverse('staff:daily_report'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Wrote the import parser')
        self.assertContains(res, 'csv.DictReader keeps the header')
        self.assertNotContains(res, 'Not mine')

    def test_page_prompts_when_today_is_unwritten(self):
        self.login_intern()
        res = self.client.get(reverse('staff:daily_report'))
        self.assertContains(res, "Write today's update")

    def test_dashboard_shows_the_update_as_due_then_done(self):
        self.login_intern()
        res = self.client.get(reverse('staff:dashboard'))
        self.assertContains(res, 'Not written yet')

        DailyReport.objects.create(employee=self.intern, date=self.today, work_done='Done it')
        res = self.client.get(reverse('staff:dashboard'))
        self.assertContains(res, "Today's update is in")

    def test_streak_counts_consecutive_days(self):
        for offset in range(3):
            DailyReport.objects.create(employee=self.intern,
                                       date=self.today - timedelta(days=offset),
                                       work_done=f'Day {offset}')
        self.login_intern()
        res = self.client.get(reverse('staff:daily_report'))
        self.assertEqual(res.context['streak'], 3)

    def test_streak_breaks_over_a_gap(self):
        DailyReport.objects.create(employee=self.intern, date=self.today, work_done='Today')
        DailyReport.objects.create(employee=self.intern,
                                   date=self.today - timedelta(days=3), work_done='Earlier')
        self.login_intern()
        res = self.client.get(reverse('staff:daily_report'))
        self.assertEqual(res.context['streak'], 1)

    def test_signed_out_visitor_is_redirected(self):
        res = self.client.get(reverse('staff:daily_report'))
        self.assertEqual(res.status_code, 302)


class HRDailyReportFeedTests(DailyReportTestBase):
    def setUp(self):
        self.report = DailyReport.objects.create(
            employee=self.intern, date=self.today,
            work_done='Reworked the quote PDF', blockers='Need the new logo')
        DailyReport.objects.create(employee=self.peer, date=self.today, work_done='Ran payroll')
        self.client.login(username='dr_hr', password=self.password)

    def test_feed_lists_everyone(self):
        res = self.client.get(reverse('emp_daily_report_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Reworked the quote PDF')
        self.assertContains(res, 'Ran payroll')

    def test_feed_counts_who_is_still_missing(self):
        third_user = User.objects.create_user(username='hr_third', password=self.password,
                                              first_name='Meera')
        Employee.objects.create(user=third_user, employee_id='DR004',
                                employment_type='fulltime', role='employee', status='active')

        res = self.client.get(reverse('emp_daily_report_list'))
        self.assertEqual(res.context['filed_today_count'], 2)
        self.assertEqual([e.employee_id for e in res.context['missing_today']], ['DR004'])

    def test_blockers_filter(self):
        res = self.client.get(reverse('emp_daily_report_list'), {'blockers': '1'})
        self.assertContains(res, 'Reworked the quote PDF')
        self.assertNotContains(res, 'Ran payroll')

    def test_employee_filter(self):
        res = self.client.get(reverse('emp_daily_report_list'),
                              {'employee': str(self.peer.id)})
        self.assertContains(res, 'Ran payroll')
        self.assertNotContains(res, 'Reworked the quote PDF')

    def test_replying_from_the_feed_notifies_the_author(self):
        res = self.client.post(
            reverse('emp_daily_report_comment', args=[self.report.id]),
            {'message': 'Logo is in the shared drive.'})
        self.assertEqual(res.status_code, 302)

        comment = DailyReportComment.objects.get()
        self.assertEqual(comment.message, 'Logo is in the shared drive.')
        self.assertEqual(comment.author, self.hr_user)
        self.assertTrue(Notification.objects.filter(employee=self.intern).exists())

    def test_empty_reply_is_not_saved(self):
        self.client.post(reverse('emp_daily_report_comment', args=[self.report.id]),
                         {'message': '   '})
        self.assertFalse(DailyReportComment.objects.exists())


class DailyReportModelTests(DailyReportTestBase):
    def test_one_report_per_person_per_day(self):
        DailyReport.objects.create(employee=self.intern, date=self.today, work_done='One')
        with self.assertRaises(Exception):
            DailyReport.objects.create(employee=self.intern, date=self.today, work_done='Two')

    def test_has_blockers_ignores_whitespace(self):
        report = DailyReport.objects.create(
            employee=self.intern, date=self.today, work_done='Work', blockers='   ')
        self.assertFalse(report.has_blockers)
