"""HR leave summary report and the WhatsApp reply on leave requests."""
from datetime import date
from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from employees.models import Employee, LeaveRequest, LeaveType


class LeaveSummaryTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client.force_login(self.admin)
        self.casual = LeaveType.objects.create(name='Casual', days_allowed=12)
        self.lop = LeaveType.objects.create(name='Loss of Pay', days_allowed=30, is_paid=False)
        self.intern = self._emp('anu', 'EMP100', 'intern', phone='98956 63498')
        self.staff = self._emp('ravi', 'EMP101', 'fulltime')

    def _emp(self, username, emp_id, employment_type, phone=''):
        user = User.objects.create_user(username, first_name=username.title())
        return Employee.objects.create(
            user=user, employee_id=emp_id, employment_type=employment_type,
            role='intern' if employment_type == 'intern' else 'employee', phone=phone, status='active')

    def _leave(self, emp, lt, start, end, status='approved'):
        return LeaveRequest.objects.create(employee=emp, leave_type=lt, start_date=start, end_date=end,
                                           reason='x', status=status)

    def rows(self, **params):
        r = self.client.get(reverse('emp_leave_summary'), params)
        self.assertEqual(r.status_code, 200)
        return {row['employee'].employee_id: row for row in r.context['rows']}

    def test_year_totals_remaining_and_counts(self):
        self._leave(self.intern, self.casual, date(2026, 3, 2), date(2026, 3, 4))      # 3
        self._leave(self.intern, self.lop, date(2026, 5, 1), date(2026, 5, 1))         # 1 unpaid
        self._leave(self.intern, self.casual, date(2026, 6, 1), date(2026, 6, 2), 'pending')
        self._leave(self.intern, self.casual, date(2026, 7, 1), date(2026, 7, 2), 'rejected')
        r = self.client.get(reverse('emp_leave_summary'), {'year': 2026})
        row = next(x for x in r.context['rows'] if x['employee'] == self.intern)
        by_name = dict(zip([lt.name for lt in r.context['leave_types']], row['by_type']))
        self.assertEqual((by_name['Casual'], by_name['Loss of Pay']), (3, 1))
        self.assertEqual(sum(row['by_type']), 4)
        self.assertEqual((row['total'], row['unpaid'], row['pending'], row['rejected']), (4, 1, 1, 1))
        allowed = sum(lt.days_allowed for lt in r.context['leave_types'])
        self.assertEqual(row['remaining'], allowed - 4)

    def test_leave_crossing_period_edge_counts_only_days_inside(self):
        self._leave(self.staff, self.casual, date(2026, 3, 30), date(2026, 4, 2))      # 2 in Mar, 2 in Apr
        self.assertEqual(self.rows(year=2026, month=3)['EMP101']['total'], 2)
        self.assertEqual(self.rows(year=2026, month=4)['EMP101']['total'], 2)
        self.assertIsNone(self.rows(year=2026, month=4)['EMP101']['remaining'])
        self._leave(self.staff, self.casual, date(2025, 12, 31), date(2026, 1, 1))
        self.assertEqual(self.rows(year=2026)['EMP101']['total'], 5)

    def test_interns_and_employees_filter(self):
        self.assertEqual(set(self.rows(people='interns')), {'EMP100'})
        self.assertEqual(set(self.rows(people='employees')), {'EMP101'})
        self.assertEqual(set(self.rows()), {'EMP100', 'EMP101'})

    def test_former_staff_hidden_unless_asked(self):
        self.staff.status = 'terminated'
        self.staff.save()
        self.assertNotIn('EMP101', self.rows())
        self.assertIn('EMP101', self.rows(inactive='1'))

    def test_excel_export(self):
        self._leave(self.intern, self.casual, date(2026, 3, 2), date(2026, 3, 4))
        r = self.client.get(reverse('emp_leave_summary'), {'year': 2026, 'people': 'interns', 'export': 'xlsx'})
        self.assertIn('leave_summary_2026.xlsx', r['Content-Disposition'])
        ws = load_workbook(BytesIO(r.content)).active
        self.assertEqual(ws['A1'].value, 'Leave summary: 2026')
        header = [c.value for c in ws[2]]
        line = dict(zip(header, [c.value for c in ws[3]]))
        self.assertEqual((line['Name'], line['Type'], line['Casual (12/yr)'], line['Total Days']),
                         ('Anu', 'Intern', 3, 3))
        self.assertEqual(ws.max_row, 3)

    def test_whatsapp_reply_button_on_leave_list(self):
        self._leave(self.intern, self.casual, date(2026, 3, 2), date(2026, 3, 4), 'pending')
        self._leave(self.staff, self.casual, date(2026, 3, 2), date(2026, 3, 4), 'pending')
        self.assertEqual(self.intern.whatsapp_number, '919895663498')
        r = self.client.get(reverse('emp_leave_list'))
        self.assertContains(r, 'data-phone="919895663498"')
        self.assertContains(r, "No phone number on Ravi")   # no phone: button disabled

    def test_decision_from_dialog_saves_message_as_note(self):
        lr = self._leave(self.intern, self.casual, date(2026, 3, 2), date(2026, 3, 4), 'pending')
        self.client.post(reverse('emp_leave_action', args=[lr.pk]), {'action': 'approve', 'notes': 'Hi Anu, approved.'})
        lr.refresh_from_db()
        self.assertEqual((lr.status, lr.review_notes), ('approved', 'Hi Anu, approved.'))
