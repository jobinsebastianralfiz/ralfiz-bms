"""HR > Calendar: weekly offs (interns Sat + Sun, staff Sun), holidays, working
days per month, leave counted in working days, and 'count leave from'."""
from datetime import date
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import CompanySettings
from employees import holiday_import, work_calendar
from employees.models import Employee, Holiday, LeaveRequest, LeaveType, Payroll

TODAY = date(2026, 11, 10)
ICS = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;VALUE=DATE:20261108
SUMMARY:Diwali/Deepavali
DESCRIPTION:Public holiday
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20261124
SUMMARY:Guru Nanak Jayanti
DESCRIPTION:Public holiday
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20261224
SUMMARY:Christmas Eve
DESCRIPTION:Observance
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20261225
SUMMARY:Christmas
DESCRIPTION:Public holiday
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20270126
SUMMARY:Republic Day
DESCRIPTION:Public holiday
END:VEVENT
END:VCALENDAR
"""


class WorkCalendarTests(TestCase):
    def setUp(self):
        work_calendar.clear()
        LeaveType.objects.all().delete()
        self.casual = LeaveType.objects.create(name='Casual Leave', days_allowed=12, monthly_limit=1)
        self.intern = Employee.objects.create(
            user=User.objects.create_user('anu', password='pw-12345', first_name='Anu'),
            employee_id='EMP200', employment_type='intern', role='intern', status='active')
        self.staff = Employee.objects.create(
            user=User.objects.create_user('ravi', password='pw-12345', first_name='Ravi'),
            employee_id='EMP201', employment_type='full_time', role='employee', status='active',
            monthly_salary=30000)
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        patcher = mock.patch('django.utils.timezone.localdate', return_value=TODAY)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(work_calendar.clear)     # rollback doesn't fire delete signals

    def test_month_working_days_by_weekly_off_and_holidays(self):
        cal = work_calendar.current()
        # November 2026: 30 days, 5 Sundays, 4 Saturdays
        self.assertEqual(cal.month_working_days(2026, 11, self.staff), 25)
        self.assertEqual(cal.month_working_days(2026, 11, self.intern), 21)
        Holiday.objects.create(date=date(2026, 11, 10), name='Test holiday')
        Holiday.objects.create(date=date(2026, 11, 8), name='Diwali')       # a Sunday: changes nothing
        cal = work_calendar.current()                                        # saving cleared the cache
        self.assertEqual(cal.month_working_days(2026, 11, self.staff), 24)
        self.assertEqual(cal.month_working_days(2026, 11, self.intern), 20)

    def test_leave_counts_working_days_only(self):
        # Fri 13 Nov .. Mon 16 Nov: interns skip Sat + Sun, staff skip Sun
        lr = LeaveRequest.objects.create(employee=self.intern, leave_type=self.casual, start_date=date(2026, 11, 13),
                                         end_date=date(2026, 11, 16), reason='x', status='approved')
        self.assertEqual(lr.total_days, 2)
        lr2 = LeaveRequest.objects.create(employee=self.staff, leave_type=self.casual, start_date=date(2026, 11, 13),
                                          end_date=date(2026, 11, 16), reason='x', status='approved')
        self.assertEqual(lr2.total_days, 3)

    def test_casual_over_a_weekend_is_one_day(self):
        self.client.force_login(self.intern.user)
        url = '/api/employees/leave/requests/'
        # Sat 14 .. Mon 16 Nov is one working day for an intern, inside the 1-a-month cap
        r = self.client.post(url, {'leave_type': str(self.casual.pk), 'start_date': '2026-11-14',
                                   'end_date': '2026-11-16', 'reason': 'x'})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['total_days'], 1)
        r = self.client.post(url, {'leave_type': str(self.casual.pk), 'start_date': '2026-11-21',
                                   'end_date': '2026-11-22', 'reason': 'x'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('holidays or weekly offs', r.json()['non_field_errors'][0])

    def test_count_from_hides_old_leave_without_deleting(self):
        old = LeaveRequest.objects.create(employee=self.staff, leave_type=self.casual, start_date=date(2026, 9, 2),
                                          end_date=date(2026, 9, 4), reason='old', status='approved')
        LeaveRequest.objects.create(employee=self.staff, leave_type=self.casual, start_date=date(2026, 10, 5),
                                    end_date=date(2026, 10, 5), reason='new', status='approved')
        s = CompanySettings.get_settings()
        s.leave_count_from = date(2026, 10, 1)
        s.save()
        self.client.force_login(self.admin)
        r = self.client.get(reverse('emp_leave_summary'), {'year': 2026})
        row = next(x for x in r.context['rows'] if x['employee'] == self.staff)
        self.assertEqual(row['total'], 1)
        self.assertNotIn(old, list(self.client.get(reverse('emp_leave_list')).context['leaves']))
        self.client.force_login(self.staff.user)
        bal = self.client.get('/api/employees/leave/balance/').json()
        self.assertEqual(next(b for b in bal if b['leave_type'] == 'Casual Leave')['used'], 1)
        self.assertTrue(LeaveRequest.objects.filter(pk=old.pk).exists())

    def test_calendar_page_marks_and_removes_holidays_and_saves_settings(self):
        self.client.force_login(self.admin)
        url = reverse('emp_calendar')
        page = self.client.get(url, {'year': 2026, 'month': 11})
        self.assertContains(page, 'Working days in November')
        self.assertEqual(page.context['this_month']['staff'], 25)
        self.client.post(url, {'action': 'add', 'date': '2026-11-10', 'name': 'Office closed', 'kind': 'company',
                               'year': 2026, 'month': 11})
        h = Holiday.objects.get()
        self.assertEqual((h.name, h.kind, h.created_by), ('Office closed', 'company', self.admin))
        self.assertEqual(self.client.get(url, {'year': 2026, 'month': 11}).context['this_month']['staff'], 24)
        self.client.post(url, {'action': 'delete', 'pk': h.pk, 'year': 2026, 'month': 11})
        self.assertFalse(Holiday.objects.exists())

        self.client.post(url, {'action': 'settings', 'intern_off': ['5', '6'], 'staff_off': ['5', '6'],
                               'leave_count_from': '2026-10-01'})
        s = CompanySettings.get_settings()
        self.assertEqual((s.staff_weekly_off, s.leave_count_from), ('5,6', date(2026, 10, 1)))
        self.assertEqual(work_calendar.current().month_working_days(2026, 11, self.staff), 21)

    def test_import_ticks_kerala_holidays_and_saves_ticked(self):
        self.client.force_login(self.admin)
        url = reverse('emp_calendar')
        with mock.patch.object(holiday_import, 'fetch', lambda year: holiday_import.parse_ics(ICS, year)):
            page = self.client.get(url, {'year': 2026, 'month': 11, 'import': 1})
        rows = {r['date']: r for r in page.context['suggestions']}
        self.assertTrue(rows[date(2026, 11, 8)]['checked'])                  # Diwali
        self.assertTrue(rows[date(2026, 12, 25)]['checked'])                 # Christmas
        self.assertFalse(rows[date(2026, 11, 24)]['checked'])                # Guru Nanak: not Kerala
        self.assertFalse(rows[date(2026, 12, 24)]['kerala'])                 # Christmas Eve
        self.assertTrue(rows[date(2026, 5, 1)]['checked'])                   # May Day, Kerala fixed list
        self.assertNotIn(date(2027, 1, 26), rows)
        self.client.post(url, {'action': 'import', 'year': 2026, 'month': 11,
                               'pick': ['2026-11-08|public|google|Diwali/Deepavali', '2026-05-01|kerala|kerala|May Day']})
        self.assertEqual(sorted(Holiday.objects.values_list('name', flat=True)), ['Diwali/Deepavali', 'May Day'])
        self.assertTrue(rows[date(2026, 4, 15)]['checked'])                  # Vishu on its own day
        self.assertEqual(rows[date(2026, 3, 20)]['name'], 'Id-ul-Fitr (Ramzan)')   # Govt date, not Google's 21st
        self.assertEqual(len([r for r in rows.values() if r['checked']]), 25)       # the whole Govt list

    def test_import_offers_to_remove_dates_not_on_kerala_list(self):
        wrong = Holiday.objects.create(date=date(2026, 3, 21), name='Ramzan Id', source='google')
        own = Holiday.objects.create(date=date(2026, 11, 10), name='Office closed', kind='kerala')   # added by hand
        self.client.force_login(self.admin)
        url = reverse('emp_calendar')
        with mock.patch.object(holiday_import, 'fetch', lambda year: []):
            page = self.client.get(url, {'year': 2026, 'import': 1})
        self.assertEqual(page.context['not_official'], [wrong])        # hand-added holidays are kept
        self.client.post(url, {'action': 'import', 'year': 2026, 'remove': [wrong.pk],
                               'pick': ['2026-03-20|public|kerala|Id-ul-Fitr (Ramzan)']})
        self.assertEqual(sorted(Holiday.objects.values_list('date', flat=True)), [date(2026, 3, 20), own.date])

    def test_import_renames_imported_holidays_to_government_name(self):
        Holiday.objects.create(date=date(2026, 10, 20), name='Dussehra', source='google')
        Holiday.objects.create(date=date(2026, 9, 4), name='Our name', source='manual')
        self.client.force_login(self.admin)
        with mock.patch.object(holiday_import, 'fetch', lambda year: []):
            self.client.post(reverse('emp_calendar'), {'action': 'import', 'year': 2026})
        self.assertEqual(Holiday.objects.get(date=date(2026, 10, 20)).name, 'Mahanavami')
        self.assertEqual(Holiday.objects.get(date=date(2026, 9, 4)).name, 'Our name')   # HR's own name kept

    def test_other_years_use_google(self):
        self.client.force_login(self.admin)
        with mock.patch.object(holiday_import, 'fetch', lambda year: holiday_import.parse_ics(ICS, year)):
            page = self.client.get(reverse('emp_calendar'), {'year': 2027, 'import': 1})
        rows = {r['date']: r for r in page.context['suggestions']}
        self.assertTrue(rows[date(2027, 1, 26)]['checked'])
        self.assertTrue(rows[date(2027, 1, 2)]['checked'])                   # Mannam Jayanthi, fixed list

    def test_import_failure_is_shown_not_raised(self):
        self.client.force_login(self.admin)
        with mock.patch('urllib.request.urlopen', side_effect=OSError('offline')):
            page = self.client.get(reverse('emp_calendar'), {'year': 2027, 'import': 1})   # 2026 works offline
        self.assertContains(page, "Couldn&#x27;t reach Google")

    def test_employee_page_shows_leave_summary(self):
        s = CompanySettings.get_settings()
        s.leave_count_from = date(2026, 10, 1)
        s.save()
        unpaid = LeaveType.objects.create(name='Loss of Pay', days_allowed=0, is_paid=False)
        for start, end, lt, status in [
            (date(2026, 9, 2), date(2026, 9, 2), self.casual, 'approved'),      # before 'count from': hidden
            (date(2026, 11, 13), date(2026, 11, 16), self.casual, 'approved'),  # Fri..Mon: 3 staff days
            (date(2026, 10, 6), date(2026, 10, 7), unpaid, 'approved'),
            (date(2026, 11, 20), date(2026, 11, 20), self.casual, 'pending'),
        ]:
            LeaveRequest.objects.create(employee=self.staff, leave_type=lt, start_date=start, end_date=end,
                                        reason='x', status=status)
        self.client.force_login(self.admin)
        page = self.client.get(reverse('emp_employee_detail', args=[self.staff.pk]))
        self.assertContains(page, 'Leave Summary 2026')
        summary = page.context['leave_summary']
        casual = next(r for r in summary['rows'] if r['leave_type'] == self.casual)
        self.assertEqual((casual['month_used'], casual['year_used'], casual['year_left']), (3, 3, 9))
        self.assertEqual((summary['total'], summary['unpaid'], summary['pending']), (5, 2, 1))

    def test_leave_summary_pdf_for_everyone_and_one_person(self):
        LeaveRequest.objects.create(employee=self.staff, leave_type=self.casual, start_date=date(2026, 11, 13),
                                    end_date=date(2026, 11, 16), reason='Family function', status='approved')
        self.client.force_login(self.admin)
        rendered = []
        fake = mock.MagicMock()
        fake.side_effect = lambda string, base_url: rendered.append(string) or mock.Mock(write_pdf=lambda: b'%PDF')
        with mock.patch('weasyprint.HTML', fake):
            r = self.client.get(reverse('emp_leave_summary'), {'year': 2026, 'export': 'pdf'})
            one = self.client.get(reverse('emp_leave_summary'), {'year': 2026, 'export': 'pdf',
                                                                 'employee': str(self.staff.pk)})
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertIn('Anu', rendered[0])
        self.assertIn('Ravi', rendered[0])
        self.assertIn('leave_summary_EMP201_2026.pdf', one['Content-Disposition'])
        self.assertNotIn('Anu', rendered[1])
        self.assertIn('Family function', rendered[1])

    def test_payroll_uses_calendar_working_days_when_left_blank(self):
        Holiday.objects.create(date=date(2026, 11, 10), name='Test holiday')
        self.client.force_login(self.admin)
        self.client.post(reverse('emp_payroll_list') + '?month=11&year=2026',
                         {'action': 'generate', 'working_days': ''})
        self.assertEqual(Payroll.objects.get(employee=self.staff).working_days, 24)
        self.assertEqual(Payroll.objects.get(employee=self.intern).working_days, 20)
