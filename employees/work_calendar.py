"""Working days: weekly offs (interns Sat + Sun, staff Sun by default) and the
holidays HR marks in HR > Calendar. Leave, payroll and attendance count with this.

current() shares one calendar within a request (cleared when each request starts,
and when a holiday or the settings are saved); outside requests it lasts TTL seconds.
"""
import time
from calendar import monthrange
from datetime import date, timedelta

WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def parse_days(value):
    return {int(d) for d in str(value or '').split(',') if d.strip().isdigit() and int(d) < 7}


def is_intern(employee):
    return employee.employment_type == 'intern' or employee.role == 'intern'


class WorkCalendar:
    def __init__(self):
        from core.models import CompanySettings
        from .models import Holiday
        s = CompanySettings.get_settings()
        self.intern_off = parse_days(s.intern_weekly_off)
        self.staff_off = parse_days(s.staff_weekly_off)
        self.count_from = s.leave_count_from
        self.holidays = dict(Holiday.objects.values_list('date', 'name'))

    def weekly_off(self, employee=None):
        """Without an employee: the staff week (the shorter one)."""
        return self.intern_off if employee is not None and is_intern(employee) else self.staff_off

    def is_working_day(self, day, employee=None):
        return day.weekday() not in self.weekly_off(employee) and day not in self.holidays

    def working_days(self, lo, hi, employee=None):
        n, day = 0, lo
        while day <= hi:
            n += self.is_working_day(day, employee)
            day += timedelta(days=1)
        return n

    def month_working_days(self, year, month, employee=None):
        return self.working_days(date(year, month, 1), date(year, month, monthrange(year, month)[1]), employee)

    def counted(self, leaves):
        """Drop leave that ends before the 'count leave from' date."""
        return leaves.filter(end_date__gte=self.count_from) if self.count_from else leaves


TTL = 30
_cached = None


def current():
    global _cached
    if _cached is None or time.monotonic() - _cached[0] > TTL:
        _cached = (time.monotonic(), WorkCalendar())
    return _cached[1]


def clear(**kwargs):
    global _cached
    _cached = None
