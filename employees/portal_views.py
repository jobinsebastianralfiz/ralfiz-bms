"""Session-based web views for the staff portal (interns & employees).

Design note
-----------
Reads are rendered server-side straight from the models. Writes are NOT
re-implemented here -- the templates POST to the existing DRF endpoints in
``employees.views`` using session auth (already enabled in
``REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']``), so attendance rules,
leave validation and face matching keep exactly one implementation shared with
the Flutter app.
"""
import re
from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .models import (
    Attendance, DailyReport, Employee, InternAssessment, LeaveRequest, LeaveType,
    Notification, OfficeConfig, Payroll, ScheduledClass, WorkAssignment,
)

# Bump this whenever a file under static/css, static/js or static/staff
# changes. Whitenoise serves these unhashed, and the service worker is
# cache-first for static assets, so an unversioned URL is served from the old
# cache forever -- which is exactly how the app icon got stuck.
ASSET_V = '19'

MONTHS = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


def staff_required(view_func):
    """User must be logged in AND have an active Employee profile."""
    @wraps(view_func)
    @login_required(login_url='staff:login')
    def wrapper(request, *args, **kwargs):
        employee = (Employee.objects
                    .select_related('user')
                    .filter(user=request.user, status='active')
                    .first())
        if employee is None:
            messages.error(request, 'This account has no active staff profile.')
            return redirect('staff:login')
        request.employee = employee
        return view_func(request, *args, **kwargs)
    return wrapper


def is_intern(employee):
    return employee.role == 'intern' or employee.employment_type == 'intern'


def photo_url(employee):
    """Best available picture of this person, or None for a letter avatar.

    Falls back to the face photo because an intern who has enrolled for
    attendance has a usable portrait even with no profile photo set.
    """
    for field in (employee.profile_photo, employee.face_photo):
        if field:
            try:
                return field.url
            except ValueError:      # FileField with no file behind it
                continue
    return None


def _unread_count(employee):
    return Notification.objects.filter(
        Q(employee=employee) | Q(employee__isnull=True), is_read=False
    ).count()


def board_member_for(employee):
    """The delivery TeamMember that project-board tasks are assigned to.

    Staff logins are Employees; board tasks point at TeamMembers, and the two
    are separate records. Linking the login to the TeamMember would let it out
    of the staff portal, so match instead: same login, else same email, else
    the one TeamMember with exactly the same name.
    """
    from core.models import TeamMember
    active = TeamMember.objects.filter(is_active=True)
    member = active.filter(user=employee.user).first()
    email = (employee.user.email or '').strip()
    if member is None and email:
        member = active.filter(email__iexact=email).first()
    if member is None:
        by_name = list(active.filter(name__iexact=employee.full_name.strip())[:2])
        if len(by_name) == 1:
            member = by_name[0]
    return member


def board_tasks_for(employee, open_only=True):
    from core.models import Task
    member = board_member_for(employee)
    if member is None:
        return Task.objects.none()
    tasks = Task.objects.filter(assigned_to=member).select_related('project')
    if open_only:
        tasks = tasks.exclude(status='completed')
    return tasks


def _split_headline(text, limit=120):
    """Bold first line for a daily update card, plus everything after it.

    A long single paragraph is split at its first sentence (or the last word
    before `limit`), so none of what the person wrote is dropped.
    """
    lines = [l.strip() for l in (text or '').strip().splitlines() if l.strip()]
    if not lines:
        return 'Update', ''
    first, rest = lines[0], lines[1:]
    if len(first) > limit:
        m = re.match(r'(.{20,%d}?[.!?])\s+(.*)' % limit, first)
        if m:
            first, tail = m.group(1), m.group(2)
        else:
            cut = first.rfind(' ', 0, limit)
            cut = cut if cut > 0 else limit
            first, tail = first[:cut].rstrip() + '…', '…' + first[cut:].lstrip()
        rest = [tail] + rest
    return first, '\n'.join(rest)


def _greeting():
    hour = timezone.localtime().hour
    return 'Good morning' if hour < 12 else ('Good afternoon' if hour < 17 else 'Good evening')


def _summary(employee):
    """The four tiles shown on Home, Attendance and Work."""
    today = timezone.localdate()
    open_work = (WorkAssignment.objects.filter(assigned_to=employee)
                 .exclude(status__in=['completed', 'cancelled']).count())
    return {
        'today': today,
        'greeting': _greeting(),
        'record': Attendance.objects.filter(employee=employee, date=today).first(),
        'days_present': Attendance.objects.filter(
            employee=employee, date__year=today.year, date__month=today.month).exclude(status='absent').count(),
        'open_task_total': open_work + board_tasks_for(employee).count(),
        'todays_report': DailyReport.objects.filter(employee=employee, date=today).first(),
        'pending_leave': LeaveRequest.objects.filter(employee=employee, status='pending').count(),
    }


def _base_context(request, active_nav=''):
    employee = request.employee
    return {
        'employee': employee,
        'is_intern': is_intern(employee),
        'active_nav': active_nav,
        'unread_count': _unread_count(employee),
        'photo_url': photo_url(employee),
        'asset_v': ASSET_V,
    }


# --- Auth ------------------------------------------------------------------

def staff_login(request):
    if request.user.is_authenticated:
        if Employee.objects.filter(user=request.user, status='active').exists():
            return redirect('staff:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, 'staff/login.html',
                          {'error': 'Invalid username or password.', 'asset_v': ASSET_V})
        if not Employee.objects.filter(user=user, status='active').exists():
            return render(request, 'staff/login.html',
                          {'error': 'This account has no active staff profile.',
                           'asset_v': ASSET_V})
        login(request, user)
        from core.security import safe_next
        return redirect(safe_next(request, request.GET.get('next'), 'staff:dashboard'))

    return render(request, 'staff/login.html', {'asset_v': ASSET_V})


def staff_logout(request):
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('staff:login')


# --- Dashboard -------------------------------------------------------------

@staff_required
@never_cache
def dashboard(request):
    employee = request.employee
    today = timezone.localdate()

    # Named `record` to match what the template reads -- passing it as
    # `attendance` meant the card always claimed "Not checked in".
    record = Attendance.objects.filter(employee=employee, date=today).first()
    open_work = (WorkAssignment.objects
                 .filter(assigned_to=employee)
                 .exclude(status__in=['completed', 'cancelled'])
                 .order_by('due_date', '-created_at')[:5])
    pending_leave = LeaveRequest.objects.filter(employee=employee, status='pending').count()
    board_tasks = list(board_tasks_for(employee).order_by('due_date', '-created_at')[:6])
    open_board_count = board_tasks_for(employee).count()
    open_work_count = (WorkAssignment.objects.filter(assigned_to=employee)
                       .exclude(status__in=['completed', 'cancelled']).count())

    upcoming_classes = [c for c in ScheduledClass.objects.filter(
        Q(interns=employee) | Q(interns__isnull=True),
        date__gte=today,
    ).exclude(status='cancelled').distinct().order_by('date', 'start_time')[:5]]

    month_attendance = Attendance.objects.filter(
        employee=employee, date__year=today.year, date__month=today.month)

    from .leave_rules import monthly_status
    leave_rules = monthly_status(employee, today)
    ctx = _base_context(request, 'dashboard')
    ctx.update(_summary(employee))
    ctx.update({
        'can_apply_leave': leave_rules['can_apply'],
        'office_tel': _tel(leave_rules['office_phone']),
        'upcoming_leave': LeaveRequest.objects.filter(
            employee=employee, end_date__gte=today, status__in=['pending', 'approved']
        ).select_related('leave_type').order_by('start_date')[:3],
        'today': today,
        'record': record,
        'open_work': open_work,
        'board_tasks': board_tasks,
        'open_task_total': open_work_count + open_board_count,
        'greeting': ('Good morning' if timezone.localtime().hour < 12
                     else 'Good afternoon' if timezone.localtime().hour < 17 else 'Good evening'),
        'pending_leave': pending_leave,
        'upcoming_classes': upcoming_classes,
        'days_present': month_attendance.exclude(status='absent').count(),
        'todays_report': DailyReport.objects.filter(employee=employee, date=today).first(),
        'recent_notifications': Notification.objects.filter(
            Q(employee=employee) | Q(employee__isnull=True))[:5],
    })
    return render(request, 'staff/dashboard.html', ctx)


# --- Attendance ------------------------------------------------------------

@staff_required
@never_cache
def attendance(request):
    employee = request.employee
    today = timezone.localdate()
    cfg = OfficeConfig.objects.first()
    record = Attendance.objects.filter(employee=employee, date=today).first()
    policy = employee.attendance_policy()
    open_record = bool(record and record.check_in and not record.check_out)

    ctx = _base_context(request, 'attendance')
    ctx.update(_summary(employee))
    ctx.update({
        'recent_records': Attendance.objects.filter(employee=employee).order_by('-date')[:5],
        'today': today,
        'record': record,
        'config': cfg,
        'office_configured': bool(cfg),
        'has_face': bool(employee.face_photo),
        'face_required': employee.face_check_required,
        'can_remote': employee.work_mode in ('hybrid', 'remote'),
        'checkout_allowed': record.is_checkout_allowed() if record and record.check_in else False,
        'seconds_until_eligible': (record.seconds_until_eligible()
                                   if open_record else 0),
        # Timing this person actually works to -- their own shift if HR set one,
        # otherwise the office default.
        'policy': policy,
        'has_custom_timing': employee.has_custom_timing,
        'earliest_checkout': record.minimum_checkout_time() if open_record else None,
    })
    return render(request, 'staff/attendance.html', ctx)


@staff_required
def attendance_history(request):
    employee = request.employee
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
        year, month = today.year, today.month
    if not 1 <= month <= 12:
        year, month = today.year, today.month

    records = Attendance.objects.filter(
        employee=employee, date__year=year, date__month=month).order_by('-date')

    import calendar
    by_day = {r.date.day: float(r.worked_hours or r.working_hours or 0) for r in records}
    days_in_month = calendar.monthrange(year, month)[1]
    top = max([8.0] + list(by_day.values()))
    trend = [{'day': d, 'hours': by_day.get(d, 0), 'pct': round(by_day.get(d, 0) * 100 / top),
              'label': d in (1, 8, 15, 22, days_in_month)} for d in range(1, days_in_month + 1)]
    for r in records:
        r.hours_shown = float(r.worked_hours or r.working_hours or 0)

    ctx = _base_context(request, 'attendance_history')
    ctx.update({
        'records': records,
        'year': year,
        'month': month,
        'month_name': MONTHS[month],
        'months': list(enumerate(MONTHS))[1:],
        'years': list(range(today.year, today.year - 4, -1)),
        'trend': trend,
        'trend_top': int(top),
        'total_hours': sum(r.hours_shown for r in records),
        'present_count': records.exclude(status='absent').count(),
        'late_count': records.filter(status='late').count(),
    })
    return render(request, 'staff/attendance_history.html', ctx)


# --- Leave -----------------------------------------------------------------

def _tel(phone):
    """tel: link target; a 10-digit Indian number gets +91."""
    digits = ''.join(ch for ch in phone if ch.isdigit())
    return '+91' + digits if len(digits) == 10 else '+' + digits


@staff_required
def leave(request):
    employee = request.employee
    this_year = timezone.localdate().year
    try:
        year = int(request.GET.get('year', this_year))
    except (TypeError, ValueError):
        year = this_year
    status = request.GET.get('status', '')

    balances = []
    for lt in LeaveType.objects.filter(is_active=True):
        approved = LeaveRequest.objects.filter(
            employee=employee, leave_type=lt, status='approved', start_date__year=year)
        used = sum(lr.total_days for lr in approved)
        balances.append({
            'leave_type': lt,
            'total_allowed': lt.days_allowed,
            'used': used,
            'remaining': max(0, lt.days_allowed - used),
        })

    year_requests = LeaveRequest.objects.filter(employee=employee, start_date__year=year).select_related('leave_type')
    status_counts = {'all': year_requests.count()}
    for key in ('pending', 'approved', 'rejected'):
        status_counts[key] = year_requests.filter(status=key).count()
    shown = year_requests.filter(status=status) if status in dict(LeaveRequest.STATUS_CHOICES) else year_requests
    years = sorted({d.year for d in LeaveRequest.objects.filter(employee=employee).dates('start_date', 'year')}
                   | {this_year}, reverse=True)
    for i, b in enumerate(balances):
        name = b['leave_type'].name.lower()
        b['icon'] = ('fa-plane' if 'casual' in name else 'fa-calendar-check' if 'earn' in name or 'privilege' in name
                     else 'fa-kit-medical' if 'sick' in name or 'medical' in name else 'fa-hourglass-half')
        b['tone'] = ['violet', 'green', 'red', 'blue'][i % 4]
        b['pct'] = round(b['remaining'] * 100 / b['total_allowed']) if b['total_allowed'] else 0

    from .leave_rules import monthly_status
    rules = monthly_status(employee)
    ctx = _base_context(request, 'leave')
    ctx.update({
        'rules': rules,
        'office_tel': _tel(rules['office_phone']),
        'balances': balances,
        'leave_types': LeaveType.objects.filter(is_active=True, pk__in=rules['online_type_ids']),
        'requests': shown.order_by('-start_date'),
        'status_counts': status_counts,
        'status': status,
        'years': years,
        'year': year,
    })
    return render(request, 'staff/leave.html', ctx)


# --- Daily report ----------------------------------------------------------

@staff_required
def daily_report(request):
    """Today's write-up plus the last few weeks of them.

    The form POSTs to the DRF endpoint, so the one-per-day rule and the edit
    window live in a single place shared with the app.
    """
    employee = request.employee
    today = timezone.localdate()

    month_param = request.GET.get('month', today.strftime('%Y-%m'))
    try:
        my, mm = (int(x) for x in month_param.split('-'))
        date(my, mm, 1)
    except (ValueError, TypeError):
        my, mm = today.year, today.month
    in_month = DailyReport.objects.filter(employee=employee, date__year=my, date__month=mm)
    week_start = today - timedelta(days=today.weekday())
    ranges = {
        'all': in_month,
        'week': in_month.filter(date__gte=week_start),
        'last7': in_month.filter(date__gte=today - timedelta(days=6)),
        'month': in_month.filter(date__year=today.year, date__month=today.month),
    }
    range_key = request.GET.get('range', 'all')
    if range_key not in ranges:
        range_key = 'all'
    reports = list(ranges[range_key].prefetch_related('comments__author').order_by('-date')[:60])
    todays = DailyReport.objects.filter(employee=employee, date=today).prefetch_related('comments__author').first()
    months = [d.strftime('%Y-%m') for d in DailyReport.objects.filter(employee=employee).dates('date', 'month', order='DESC')[:18]]
    if today.strftime('%Y-%m') not in months:
        months.insert(0, today.strftime('%Y-%m'))
    for r in reports:
        r.headline, r.rest = _split_headline(r.work_done)

    ctx = _base_context(request, 'daily_report')
    ctx.update({
        'today': today,
        'todays_report': todays,
        'reports': reports,
        'range_key': range_key,
        'range_counts': {k: v.count() for k, v in ranges.items()},
        'month_value': f'{my:04d}-{mm:02d}',
        'month_options': [(m, date(int(m[:4]), int(m[5:]), 1)) for m in months],
        'streak': _report_streak(employee, today),
    })
    return render(request, 'staff/daily_report.html', ctx)


def _report_streak(employee, today):
    """How many days running, ending today or yesterday, have a report."""
    filed = set(DailyReport.objects
                .filter(employee=employee, date__lte=today)
                .values_list('date', flat=True)[:120])
    if not filed:
        return 0
    cursor = today if today in filed else today - timedelta(days=1)
    streak = 0
    while cursor in filed:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


# --- Work assignments ------------------------------------------------------

@staff_required
def work_list(request):
    employee = request.employee
    assignments = WorkAssignment.objects.filter(assigned_to=employee).select_related('project')
    status_filter = request.GET.get('status', '')
    if status_filter:
        assignments = assignments.filter(status=status_filter)

    from core.models import Task
    board_tasks = board_tasks_for(employee, open_only=False)
    board_filter = {'assigned': 'todo', 'in_progress': 'in_progress', 'completed': 'completed'}.get(status_filter)
    if status_filter and board_filter:
        board_tasks = board_tasks.filter(status=board_filter)
    elif status_filter:
        board_tasks = board_tasks.none()
    else:
        board_tasks = board_tasks.exclude(status='completed')

    all_tasks = board_tasks_for(employee, open_only=False)
    all_work = WorkAssignment.objects.filter(assigned_to=employee)
    week_ago = timezone.now() - timedelta(days=7)
    counts = {
        'total': all_tasks.count() + all_work.count(),
        'new_week': all_tasks.filter(created_at__gte=week_ago).count() + all_work.filter(created_at__gte=week_ago).count(),
        'in_progress': all_tasks.filter(status__in=['in_progress', 'review']).count() + all_work.filter(status='in_progress').count(),
        'on_hold': all_work.filter(status='on_hold').count(),
        'completed': all_tasks.filter(status='completed').count() + all_work.filter(status='completed').count(),
        'cancelled': all_work.filter(status='cancelled').count(),
    }
    total = counts['total'] or 1
    for key in ('in_progress', 'on_hold', 'completed', 'cancelled'):
        counts[key + '_pct'] = round(counts[key] * 100 / total)

    ctx = _base_context(request, 'work')
    ctx.update(_summary(employee))
    ctx.update({
        'counts': counts,
        'work_total': board_tasks.count() + assignments.count(),
        'assignments': assignments,
        'board_tasks': board_tasks.order_by('due_date', '-created_at'),
        'task_status_choices': Task.STATUS_CHOICES,
        'status_filter': status_filter,
        'status_choices': WorkAssignment.STATUS_CHOICES,
    })
    return render(request, 'staff/work_list.html', ctx)


@staff_required
def board_task_detail(request, pk):
    """One of your project-board tasks: details, attached files and comments."""
    from core.models import Task, TaskComment
    task = get_object_or_404(board_tasks_for(request.employee, open_only=False), pk=pk)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()[:4000]
        if body:
            TaskComment.objects.create(task=task, author=request.user, body=body)
            messages.success(request, 'Comment added.')
        return redirect('staff:board_task_detail', pk=task.pk)
    ctx = _base_context(request, 'work')
    ctx.update({
        'task': task,
        'attachments': task.attachments.all(),
        'comments': task.comments.filter(is_deleted=False, parent__isnull=True)
                        .select_related('author').prefetch_related('replies__author'),
        'task_status_choices': Task.STATUS_CHOICES,
    })
    return render(request, 'staff/board_task_detail.html', ctx)


@staff_required
def board_task_update(request, pk):
    """Move one of your own project-board tasks along, or set its progress."""
    from core.models import Task, TaskActivity
    task = get_object_or_404(board_tasks_for(request.employee, open_only=False), pk=pk)
    if request.method == 'POST':
        old_status = task.status
        status = request.POST.get('status', task.status)
        if status in dict(Task.STATUS_CHOICES):
            task.status = status
            task.completed_date = timezone.localdate() if status == 'completed' else None
        try:
            task.progress = max(0, min(100, int(request.POST.get('progress', task.progress))))
        except (TypeError, ValueError):
            pass
        task.save()
        if old_status != task.status:
            TaskActivity.objects.create(task=task, actor=request.user, verb='status_changed',
                                        from_value=old_status, to_value=task.status, is_visible_to_client=True)
        messages.success(request, f'"{task.title}" updated.')
    from core.security import safe_next
    return redirect(safe_next(request, request.POST.get('back'), 'staff:work_list'))


@staff_required
def work_detail(request, pk):
    employee = request.employee
    assignment = get_object_or_404(
        WorkAssignment.objects.filter(assigned_to=employee).select_related('project'), pk=pk)

    ctx = _base_context(request, 'work')
    ctx.update({
        'assignment': assignment,
        'updates': assignment.updates.select_related('employee__user'),
        'status_choices': WorkAssignment.STATUS_CHOICES,
    })
    return render(request, 'staff/work_detail.html', ctx)


# --- Classes & assessments -------------------------------------------------

@staff_required
def class_list(request):
    employee = request.employee
    today = timezone.localdate()
    classes = ScheduledClass.objects.filter(
        Q(interns=employee) | Q(interns__isnull=True)).distinct().order_by('-date', '-start_time')

    ctx = _base_context(request, 'classes')
    ctx.update({
        'upcoming': [c for c in classes if c.date >= today][::-1],
        'past': [c for c in classes if c.date < today],
    })
    return render(request, 'staff/class_list.html', ctx)


@staff_required
def class_detail(request, pk):
    employee = request.employee
    scheduled = get_object_or_404(
        ScheduledClass.objects.filter(Q(interns=employee) | Q(interns__isnull=True)).distinct(), pk=pk)

    ctx = _base_context(request, 'classes')
    ctx.update({'scheduled': scheduled})
    return render(request, 'staff/class_detail.html', ctx)


@staff_required
def assessment_list(request):
    employee = request.employee
    assessments = InternAssessment.objects.filter(employee=employee)
    graded = [a for a in assessments if a.is_graded]

    ctx = _base_context(request, 'assessments')
    ctx.update({
        'assessments': assessments,
        'average': round(sum(a.percentage for a in graded) / len(graded), 1) if graded else None,
        'graded_count': len(graded),
    })
    return render(request, 'staff/assessment_list.html', ctx)


# --- Payslips --------------------------------------------------------------

@staff_required
def payslip_list(request):
    employee = request.employee
    payslips = Payroll.objects.filter(employee=employee).exclude(status='draft')

    ctx = _base_context(request, 'payslips')
    ctx.update({
        'payslips': [(p, MONTHS[p.month]) for p in payslips],
    })
    return render(request, 'staff/payslip_list.html', ctx)


@staff_required
def payslip_detail(request, pk):
    employee = request.employee
    payslip = get_object_or_404(
        Payroll.objects.filter(employee=employee).exclude(status='draft'), pk=pk)

    ctx = _base_context(request, 'payslips')
    ctx.update({'payslip': payslip, 'month_name': MONTHS[payslip.month]})
    return render(request, 'staff/payslip_detail.html', ctx)


# --- Notifications ---------------------------------------------------------

@staff_required
def notification_list(request):
    employee = request.employee
    mine = Notification.objects.filter(Q(employee=employee) | Q(employee__isnull=True))
    kind = request.GET.get('type', '')
    if kind not in dict(NOTIFICATION_FILTERS):
        kind = ''

    counts = {'': mine.count(), 'other': mine.filter(notification_type__in=['general', '']).count()}
    for key, _ in NOTIFICATION_FILTERS[1:-1]:
        counts[key] = mine.filter(notification_type=key).count()
    filters = [(key, label, counts[key]) for key, label in NOTIFICATION_FILTERS]

    shown = mine
    if kind == 'other':
        shown = shown.filter(notification_type__in=['general', ''])
    elif kind:
        shown = shown.filter(notification_type=kind)

    today = timezone.localdate()
    groups = {'today': [], 'month': [], 'earlier': []}
    for n in shown[:100]:
        _decorate_notification(n)
        day = timezone.localtime(n.created_at).date()
        if day == today:
            groups['today'].append(n)
        elif (day.year, day.month) == (today.year, today.month):
            groups['month'].append(n)
        else:
            groups['earlier'].append(n)

    ctx = _base_context(request, 'notifications')
    ctx.update({
        'today': today,
        'kind': kind,
        'filters': filters,
        'groups': [(label, groups[key]) for key, label in
                   [('today', 'Today'), ('month', 'This Month'), ('earlier', 'Earlier')] if groups[key]],
        'has_unread': mine.filter(employee=employee, is_read=False).exists(),
    })
    return render(request, 'staff/notification_list.html', ctx)


NOTIFICATION_FILTERS = [('', 'All'), ('leave', 'Leave'), ('attendance', 'Attendance'),
                        ('work', 'Work'), ('announcement', 'Announcements'), ('other', 'Other')]
_NOTIFICATION_LOOK = {  # type -> (icon, tone, link)
    'leave': ('fa-plane', 'violet', 'staff:leave'),
    'attendance': ('fa-fingerprint', 'green', 'staff:attendance'),
    'work': ('fa-list-check', 'blue', 'staff:work_list'),
    'announcement': ('fa-bullhorn', 'orange', ''),
}
_LEAVE_RANGE = re.compile(r'from (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})')


def _decorate_notification(n):
    """Icon, status pill and the leave dates a notification card shows.

    Leave notifications only carry their dates in the body text
    ("from 2026-10-13 to 2026-10-13"), so they are read back from there.
    """
    icon, tone, link = _NOTIFICATION_LOOK.get(n.notification_type, ('fa-bell', 'grey', ''))
    n.icon, n.tone = icon, tone
    n.link = reverse(link) if link else ''
    title = n.title.lower()
    n.status = next((s for s in ('approved', 'rejected', 'cancelled') if s in title), '')
    if not n.status and n.notification_type == 'leave' and 'request' in title:
        n.status = 'pending'
    n.on_date, n.days = None, None
    m = _LEAVE_RANGE.search(n.body or '')
    if m:
        try:
            start, end = date.fromisoformat(m.group(1)), date.fromisoformat(m.group(2))
            n.on_date, n.days = start, (end - start).days + 1
        except ValueError:
            pass
    # Non-breaking hyphens so "2026-10-13" never wraps onto two lines.
    n.body_display = re.sub(r'\d{4}-\d{2}-\d{2}', lambda d: d.group(0).replace('-', '‑'), n.body or '')
    n.can_mark_read = n.employee_id is not None and not n.is_read
    return n


# --- Profile ---------------------------------------------------------------

@staff_required
def profile(request):
    employee = request.employee
    ctx = _base_context(request, 'profile')
    ctx.update({
        'has_face': bool(employee.face_photo),
        'work_mode_display': employee.get_work_mode_display(),
    })
    return render(request, 'staff/profile.html', ctx)


# --- CRM leads (marketing interns) ----------------------------------------

@staff_required
def lead_list(request):
    from crm.models import Lead

    employee = request.employee
    leads = Lead.objects.filter(assigned_to=request.user).order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        leads = leads.filter(status=status_filter)

    ctx = _base_context(request, 'leads')
    ctx.update({
        'leads': leads,
        'status_filter': status_filter,
        'status_choices': Lead.STATUS_CHOICES,
        'total': Lead.objects.filter(assigned_to=request.user).count(),
        'converted': Lead.objects.filter(assigned_to=request.user, status='converted').count(),
    })
    return render(request, 'staff/lead_list.html', ctx)


@staff_required
def lead_detail(request, pk):
    from crm.models import Lead

    lead = get_object_or_404(Lead.objects.filter(assigned_to=request.user), pk=pk)

    ctx = _base_context(request, 'leads')
    ctx.update({
        'lead': lead,
        'notes': lead.lead_notes.select_related('created_by')[:50],
        'status_choices': Lead.STATUS_CHOICES,
    })
    return render(request, 'staff/lead_detail.html', ctx)


# --- PWA plumbing ----------------------------------------------------------

def manifest(request):
    """Web app manifest. Served from /staff/ so the PWA scope covers the portal."""
    body = render_to_string('staff/manifest.webmanifest', {'asset_v': ASSET_V}, request=request)
    return HttpResponse(body, content_type='application/manifest+json')


def service_worker(request):
    """Service worker. Must be served from /staff/ for its scope to cover the portal."""
    body = render_to_string('staff/sw.js', {'asset_v': ASSET_V}, request=request)
    response = HttpResponse(body, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/staff/'
    response['Cache-Control'] = 'no-cache'
    return response


def offline(request):
    return render(request, 'staff/offline.html', {'asset_v': ASSET_V})



@staff_required
def staff_search(request):
    """Search your own tasks, work assignments and notifications."""
    employee = request.employee
    q = request.GET.get('q', '').strip()[:100]
    tasks = work = notes = []
    if q:
        tasks = board_tasks_for(employee, open_only=False).filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(project__name__icontains=q))[:20]
        work = WorkAssignment.objects.filter(assigned_to=employee).filter(
            Q(title__icontains=q) | Q(description__icontains=q))[:20]
        notes = Notification.objects.filter(Q(employee=employee) | Q(employee__isnull=True)).filter(
            Q(title__icontains=q) | Q(body__icontains=q))[:20]
    ctx = _base_context(request, '')
    ctx.update({'q': q, 'tasks': tasks, 'work': work, 'notes': notes,
                'result_count': len(tasks) + len(work) + len(notes)})
    return render(request, 'staff/search.html', ctx)
