"""Monthly leave rules, checked wherever leave is applied for (app API and staff PWA).

- A type with monthly_limit (Casual: 1) allows that many days per calendar month;
  unused days do not carry forward.
- A type with document_after_days (Sick: 1) needs a document, such as a doctor's
  prescription, once a month's days go past that number.
Pending and approved requests both count, so two requests can't slip past together.
Days are working days (employees/work_calendar.py): weekly offs and holidays are free.
A working day marked Absent with no approved leave uses up a Casual Leave day (absent_days).
"""
from calendar import monthrange
from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone

from .models import Attendance, LeaveRequest, LeaveType
from .work_calendar import current


def _months(start, end):
    """(year, month, first_day, last_day) for every month start..end touches."""
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m, date(y, m, 1), date(y, m, monthrange(y, m)[1])
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def casual_type():
    """The leave type that Absent days are taken from: the active one named Casual."""
    return LeaveType.objects.filter(is_active=True, name__icontains='casual').order_by('name').first()


def absent_days(employees, lo, hi):
    """{employee pk: [dates]} of working days in lo..hi marked Absent with no approved
    leave, from the joining date and the 'count leave from' date (HR > Calendar).
    Each one uses up a Casual Leave day."""
    employees = list(employees)
    cal = current()
    if cal.count_from:
        lo = max(lo, cal.count_from)
    out = {e.pk: [] for e in employees}
    if lo > hi or not employees:
        return out
    on_leave = {}
    for e_id, start, end in LeaveRequest.objects.filter(employee__in=employees, status='approved', start_date__lte=hi,
                                                        end_date__gte=lo).values_list('employee_id', 'start_date', 'end_date'):
        on_leave.setdefault(e_id, []).append((start, end))
    by_pk = {e.pk: e for e in employees}
    for e_id, day in (Attendance.objects.filter(employee__in=employees, date__range=(lo, hi), status='absent')
                      .order_by('date').values_list('employee_id', 'date')):
        e = by_pk[e_id]
        joined = e.joining_date.date() if hasattr(e.joining_date, 'date') else e.joining_date
        if ((not joined or day >= joined) and cal.is_working_day(day, e)
                and not any(a <= day <= b for a, b in on_leave.get(e_id, ()))):
            out[e_id].append(day)
    return out


def _absent_as(employee, leave_type, lo, hi):
    """Absent days charged to this leave type: all of them for Casual, none otherwise."""
    casual = casual_type()
    if not casual or leave_type is None or leave_type.pk != casual.pk:
        return 0
    return len(absent_days([employee], lo, hi)[employee.pk])


def days_used(employee, leave_type, lo, hi, exclude_pk=None):
    qs = LeaveRequest.objects.filter(employee=employee, leave_type=leave_type, status__in=['pending', 'approved'],
                                     start_date__lte=hi, end_date__gte=lo)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    cal = current()
    return sum(lr.days_in(lo, hi, cal) for lr in qs) + _absent_as(employee, leave_type, lo, hi)


def year_days_used(employee, leave_type, year):
    """Approved working days of this type in the year, for balances. Leave before
    the 'count leave from' date (HR > Calendar) is left out."""
    cal = current()
    lo, hi = date(year, 1, 1), date(year, 12, 31)
    qs = cal.counted(LeaveRequest.objects.filter(employee=employee, leave_type=leave_type, status='approved',
                                                 start_date__lte=hi, end_date__gte=lo))
    return sum(lr.days_in(lo, hi, cal) for lr in qs) + _absent_as(employee, leave_type, lo, hi)


def month_leave_days(employee, year, month):
    """(paid, unpaid) approved working days of leave inside the month, for payroll."""
    cal = current()
    lo, hi = date(year, month, 1), date(year, month, monthrange(year, month)[1])
    paid = unpaid = 0
    for lr in LeaveRequest.objects.filter(employee=employee, status='approved', start_date__lte=hi,
                                          end_date__gte=lo).select_related('leave_type'):
        days = lr.days_in(lo, hi, cal)
        if lr.leave_type and lr.leave_type.is_paid:
            paid += days
        else:
            unpaid += days
    return paid, unpaid


def unmarked_days(employees, lo, hi, count_absent=False):
    """{employee pk: [dates]} of working days in lo..hi with no attendance marked
    and no approved leave. Shown to HR as unmarked leave; payroll doesn't cut for
    them. Counts only up to yesterday, from the person's joining date and from the
    'count leave from' date (HR > Calendar). count_absent also takes in days
    marked Absent (the leave summaries; the attendance report counts those itself)."""
    employees = list(employees)
    cal = current()
    hi = min(hi, timezone.localdate() - timedelta(days=1))
    if cal.count_from:
        lo = max(lo, cal.count_from)
    out = {e.pk: [] for e in employees}
    if lo > hi or not employees:
        return out
    attended = Attendance.objects.filter(employee__in=employees, date__range=(lo, hi))
    if count_absent:
        attended = attended.exclude(status='absent')
    marked = set(attended.values_list('employee_id', 'date'))
    on_leave = {}
    for e_id, start, end in LeaveRequest.objects.filter(employee__in=employees, status='approved', start_date__lte=hi,
                                                        end_date__gte=lo).values_list('employee_id', 'start_date', 'end_date'):
        on_leave.setdefault(e_id, []).append((start, end))
    for e in employees:
        joined = e.joining_date.date() if hasattr(e.joining_date, 'date') else e.joining_date
        day = max(lo, joined) if joined else lo
        while day <= hi:
            if (cal.is_working_day(day, e) and (e.pk, day) not in marked
                    and not any(a <= day <= b for a, b in on_leave.get(e.pk, ()))):
                out[e.pk].append(day)
            day += timedelta(days=1)
    return out


def is_sick(leave_type):
    return 'sick' in leave_type.name.lower() or leave_type.document_after_days > 0


def office_phone():
    return settings.OFFICE_PHONE


def _office_display():
    digits = ''.join(ch for ch in office_phone() if ch.isdigit())
    return f'{digits[:5]} {digits[5:]}' if len(digits) == 10 else office_phone()


def check_request(employee, leave_type, start, end, has_document=False):
    """Return a message saying why this request breaks a rule, or '' if it is fine."""
    if not leave_type or start > end:
        return ''
    cal = current()
    if not cal.working_days(start, end, employee):
        return 'Those dates are all holidays or weekly offs, so no leave is needed.'
    for _, _, lo, hi in _months(start, end):
        new = cal.working_days(max(start, lo), min(end, hi), employee)
        if not new:
            continue
        used = days_used(employee, leave_type, lo, hi)
        month = lo.strftime('%B')
        if leave_type.monthly_limit and used + new > leave_type.monthly_limit:
            allowed = leave_type.monthly_limit
            left = max(0, allowed - used)
            day_s = 'day' if allowed == 1 else 'days'
            return (f'You can take {allowed} {leave_type.name} {day_s} a month'
                    + (f' and have already used it for {month}' if not left else f'; {left} left for {month}')
                    + f'. Unused days do not carry forward. For more leave, call the office on {_office_display()}.')
        if leave_type.document_after_days and used + new > leave_type.document_after_days and not has_document:
            free = leave_type.document_after_days
            return (f'More than {free} {leave_type.name} day{"s" if free != 1 else ""} in {month} needs a '
                    "doctor's prescription. Attach it and submit again.")
    return ''


def monthly_status(employee, today=None):
    """This month's position on every monthly-capped type, plus what the person may
    still apply for online. When the monthly casual allowance is used up the apps show
    'Call office' instead of 'Apply leave', and only sick leave stays online
    (`online_type_ids`). Leave already applied for is never changed."""
    today = today or timezone.localdate()
    lo = today.replace(day=1)
    hi = date(today.year, today.month, monthrange(today.year, today.month)[1])
    capped = []
    for lt in LeaveType.objects.filter(is_active=True, monthly_limit__gt=0):
        used = days_used(employee, lt, lo, hi)
        capped.append({'leave_type': lt.name, 'limit': lt.monthly_limit, 'used': used,
                       'remaining': max(0, lt.monthly_limit - used)})
    casual = next((c for c in capped if 'casual' in c['leave_type'].lower()), capped[0] if capped else None)
    can_apply = not (casual and casual['remaining'] == 0)
    active = list(LeaveType.objects.filter(is_active=True))
    # Casual used up: only sick leave (with a prescription past the free days) stays online
    online = active if can_apply else [lt for lt in active if is_sick(lt)]
    return {
        'month': lo.strftime('%B %Y'),
        'monthly': capped,
        'can_apply': can_apply,
        'online_type_ids': [str(lt.pk) for lt in online],
        'office_phone': office_phone(),
        'document_rules': [{'leave_type': lt.name, 'free_days_per_month': lt.document_after_days}
                           for lt in LeaveType.objects.filter(is_active=True, document_after_days__gt=0)],
    }
