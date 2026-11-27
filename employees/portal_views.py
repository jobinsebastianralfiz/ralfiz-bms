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

from . import bootcamp, work_calendar
from .leave_rules import year_days_used
from .models import (
    Attendance, DailyReport, Employee, InternAssessment, LeaveRequest, LeaveType,
    Notification, OfficeConfig, Payroll, ScheduledClass, WorkAssignment,
)

# Bump this whenever a file under static/css, static/js or static/staff
# changes. Whitenoise serves these unhashed, and the service worker is
# cache-first for static assets, so an unversioned URL is served from the old
# cache forever -- which is exactly how the app icon got stuck.
ASSET_V = '22'

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
    """The delivery TeamMember that project-board tasks are assigned to."""
    from core.models import TeamMember
    return TeamMember.match_employee(employee)


def board_tasks_for(employee, open_only=True):
    from core.models import Task
    member = board_member_for(employee)
    if member is None:
        return Task.objects.none()
    # Backlog cards are not the person's work yet: they appear when the lead starts the week.
    tasks = Task.objects.filter(assigned_to=member).exclude(status='backlog').select_related('project')
    if open_only:
        tasks = tasks.exclude(status='completed')
    return tasks


def staff_projects(employee, member=None):
    """Projects this person works on: on the project's team list, or holding an
    unfinished task on its board (so work still to do never goes missing).
    A finished task alone does not keep a project listed.

    Cancelled projects are left out. Returns (projects queryset, TeamMember or None).
    """
    from core.models import Project
    member = member or board_member_for(employee)
    if member is None:
        return Project.objects.none(), None
    projects = (Project.objects.filter(
                    Q(team_members=member)
                    | (Q(tasks__assigned_to=member) & Q(tasks__status__in=('todo', 'in_progress', 'review'))))
                .exclude(status='cancelled').distinct())
    return projects, member


def visible_board_tasks(employee):
    """Board tasks this person may open: everything on their projects' boards except
    the backlog, which only the project's lead sees. Who may move what is decided
    by core.task_rules."""
    from core.models import Task
    from core.task_rules import visible_to
    projects, member = staff_projects(employee)
    if member is None:
        return Task.objects.none()
    return visible_to(Task.objects.filter(Q(project__in=projects) | Q(assigned_to=member)),
                      member=member).distinct()


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
        'open_task_total': open_work,
        'todays_report': DailyReport.objects.filter(employee=employee, date=today).first(),
        'pending_leave': LeaveRequest.objects.filter(employee=employee, status='pending').count(),
    }


def _wallet_card(employee):
    from wallet.staff_views import card
    return card(employee)


def _has_wallet(employee):
    from wallet.services import has_wallet
    return has_wallet(employee)


def _base_context(request, active_nav=''):
    employee = request.employee
    return {
        'has_wallet': _has_wallet(employee),
        'employee': employee,
        'is_intern': is_intern(employee),
        'active_nav': active_nav,
        'unread_count': _unread_count(employee),
        'photo_url': photo_url(employee),
        'asset_v': ASSET_V,
        'has_projects': staff_projects(employee)[0].exists(),
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
        # Project boards are their own section, never mixed into My Tasks.
        'my_projects': project_cards(employee)[:4],
        'open_task_total': open_work_count,
        'greeting': ('Good morning' if timezone.localtime().hour < 12
                     else 'Good afternoon' if timezone.localtime().hour < 17 else 'Good evening'),
        'pending_leave': pending_leave,
        'upcoming_classes': upcoming_classes,
        'tests_to_take': list(InternAssessment.objects.filter(
            employee=employee, mcq_test__isnull=False, submitted_at__isnull=True)
            .select_related('mcq_test').order_by('due_date', 'created_at')[:5]),
        'bootcamp': bootcamp.dashboard_summary(employee) if is_intern(employee) else None,
        'wallet': _wallet_card(employee),
        'days_present': month_attendance.exclude(status='absent').count(),
        'todays_report': DailyReport.objects.filter(employee=employee, date=today).first(),
        'recent_notifications': Notification.objects.filter(
            Q(employee=employee) | Q(employee__isnull=True))[:5],
    })
    ctx.update(_board_dashboard(employee, today, record, [], list(open_work),
                                ctx['upcoming_leave'], upcoming_classes, ctx['recent_notifications']))
    return render(request, 'staff/dashboard.html', ctx)


TONES = ('plum', 'teal', 'coral')


def _board_dashboard(employee, today, record, board_tasks, open_work, leave, classes, notes):
    """Pieces for the card-and-calendar Home: today's three cards, one task list
    and a calendar column of what is coming up and what happened lately."""
    from collections import OrderedDict
    from datetime import timedelta
    from .models import Holiday

    # Hours worked today against this person's required hours.
    required = float(employee.attendance_policy().required_hours or 6)
    worked = 0.0
    if record and record.check_in:
        end = record.check_out or timezone.now()
        worked = max(0.0, (end - record.check_in).total_seconds() / 3600)
    att_pct = min(100, round(worked * 100 / required)) if required else 0

    tasks = []
    for t in board_tasks:
        tasks.append({'title': t.title, 'url': reverse('staff:board_task_detail', args=[t.pk]),
                      'project': t.project.name if t.project_id else '', 'due': t.due_date,
                      'overdue': t.is_overdue, 'status': t.get_status_display(),
                      'progress': t.progress, 'files': t.attachments.count(),
                      'done': t.status == 'review'})
    for w in open_work:
        tasks.append({'title': w.title, 'url': reverse('staff:work_detail', args=[w.pk]),
                      'project': w.project.name if w.project_id else '', 'due': w.due_date,
                      'overdue': w.is_overdue, 'status': 'Overdue' if w.is_overdue else w.get_status_display(),
                      'progress': 0, 'files': 0, 'done': False})
    far = today + timedelta(days=3650)
    tasks.sort(key=lambda x: (not x['overdue'], x['due'] or far))
    for i, t in enumerate(tasks):
        t['tone'] = 'coral' if t['overdue'] else TONES[i % 2]
    with_progress = [t['progress'] for t in tasks if t['progress']]
    task_pct = round(sum(with_progress) / len(with_progress)) if with_progress else 0

    # Calendar: the next two months.
    horizon = today + timedelta(days=60)
    days = {}

    def add(day, when, what, title, tone, url=''):
        days.setdefault(day, []).append({'when': when, 'what': what, 'title': title, 'tone': tone, 'url': url})

    for c in classes:
        if c.date <= horizon:
            add(c.date, c.start_time.strftime('%I:%M %p').lstrip('0'), 'Class', c.title, 'plum',
                reverse('staff:class_detail', args=[c.pk]))
    for t in tasks:
        if t['due'] and today <= t['due'] <= horizon:
            add(t['due'], 'Due', t['project'] or 'Task', t['title'], 'teal', t['url'])
    for l in leave:
        add(max(l.start_date, today), f"{l.total_days:g}d" if l.total_days else 'Leave',
            f"{l.leave_type.name if l.leave_type_id else 'Leave'} · {l.get_status_display()}",
            'Your leave', 'coral', reverse('staff:leave'))
    for h in Holiday.objects.filter(date__gte=today, date__lte=horizon).order_by('date')[:6]:
        add(h.date, 'Holiday', h.get_kind_display(), h.name, 'coral')
    upcoming = [{'date': d, 'events': days[d]} for d in sorted(days)][:8]

    recent = OrderedDict()
    for n in notes:
        recent.setdefault(timezone.localtime(n.created_at).date(), []).append(n)
    recent = [{'date': d, 'events': ev} for d, ev in recent.items()]

    return {
        'first_name': (employee.user.first_name or employee.full_name.split(' ')[0] or employee.user.username),
        'hours_worked': worked,
        'att_pct': att_pct,
        'tasks': tasks[:6],
        'task_pct': task_pct,
        'upcoming': upcoming,
        'recent': recent,
    }


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
        used = year_days_used(employee, lt, year)
        balances.append({
            'leave_type': lt,
            'total_allowed': lt.days_allowed,
            'used': used,
            'remaining': max(0, lt.days_allowed - used),
        })

    year_requests = work_calendar.current().counted(
        LeaveRequest.objects.filter(employee=employee, start_date__year=year)).select_related('leave_type')
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

_TASK_PILLS = {  # status -> (label, ut-pill tone)
    'todo': ('To do', ''), 'assigned': ('Assigned', ''), 'in_progress': ('In progress', 'dark'),
    'review': ('In review', 'lime'), 'on_hold': ('On hold', 'blocked'),
    'completed': ('Completed', 'pass'), 'cancelled': ('Cancelled', 'fail'),
}
_PRIORITY_RANK = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}


def _due_text(due, is_open):
    """'3 days left', 'tomorrow', '2 days late' for an open item; '' otherwise."""
    if not due or not is_open:
        return '', False
    days = (due - timezone.localdate()).days
    if days < 0:
        return f'{-days} day{"s" if days < -1 else ""} late', True
    return {0: 'today', 1: 'tomorrow'}.get(days, f'{days} days left'), False


def _task_card(obj, kind, xp_settings=None):
    """A project-board task or a work assignment, shaped for the My Tasks card grid."""
    is_board = kind == 'board'
    is_open = obj.status not in ('completed', 'cancelled')
    due_text, late = _due_text(obj.due_date, is_open)
    label, tone = _TASK_PILLS.get(obj.status, (obj.get_status_display(), ''))
    if late:
        label, tone = 'Overdue', 'fail'
    return {
        'kind': kind,
        'kicker': (obj.category or 'Project task') if is_board else 'Work assignment',
        'title': obj.title,
        'url': reverse('staff:board_task_detail' if is_board else 'staff:work_detail', args=[obj.pk]),
        'desc': obj.description,
        'project': obj.project.name if obj.project_id else '',
        'due': obj.due_date, 'due_text': due_text, 'late': late,
        'priority': obj.priority, 'priority_label': obj.get_priority_display(),
        'pill': label, 'tone': tone,
        'progress': obj.progress_percent if is_board else (100 if obj.status == 'completed' else None),
        'files': obj.attachments.count() if is_board else (1 if obj.attachment else 0),
        'assigned_by': '' if is_board else (
            (obj.assigned_by.get_full_name() or obj.assigned_by.username) if obj.assigned_by_id else ''),
        'done': not is_open,
        # Work assignments earn XP (blank = the priority default); board tasks don't.
        'xp': None if is_board or xp_settings is None else (
            obj.xp_reward if obj.xp_reward is not None else xp_settings.priority_xp(obj.priority)),
    }


def _plan_status(p):
    if p.get('completed') or (p['total'] and p['done'] == p['total'] and not p['retest']):
        return 'completed'
    return 'in_progress' if p['done'] else 'assigned'


@staff_required
def work_list(request):
    """My Tasks: the person's own work assignments and UAT plans. Project board
    tasks are kept apart, under Projects."""
    from uat.staff_views import _my_plans, _summary as uat_summary
    employee = request.employee
    assignments = WorkAssignment.objects.filter(assigned_to=employee).select_related('project', 'assigned_by')
    status_filter = request.GET.get('status', '')
    if status_filter:
        assignments = assignments.filter(status=status_filter)

    all_plans = [uat_summary(plan, employee) for plan in _my_plans(employee).order_by('due_date', 'name')]
    for p in all_plans:
        p['status_key'] = _plan_status(p)
        p['due_text'], p['late'] = _due_text(p['plan'].due_date, p['status_key'] != 'completed')
    plans = [p for p in all_plans if not status_filter or p['status_key'] == status_filter]

    from wallet.models import XPSettings
    xp_settings = XPSettings.current()
    # Only the person's own work: project board tasks live under Projects.
    cards = [_task_card(w, 'work', xp_settings) for w in assignments]
    far = date.max
    cards.sort(key=lambda c: (c['done'], c['due'] or far, _PRIORITY_RANK.get(c['priority'], 9), c['title'].lower()))

    all_work = WorkAssignment.objects.filter(assigned_to=employee)
    week_ago = timezone.now() - timedelta(days=7)
    plan_keys = [p['status_key'] for p in all_plans]
    counts = {
        'total': all_work.count() + len(all_plans),
        'new_week': (all_work.filter(created_at__gte=week_ago).count()
                     + sum(1 for p in all_plans if p['plan'].created_at >= week_ago)),
        'in_progress': all_work.filter(status='in_progress').count() + plan_keys.count('in_progress'),
        'on_hold': all_work.filter(status='on_hold').count(),
        'completed': all_work.filter(status='completed').count() + plan_keys.count('completed'),
        'cancelled': all_work.filter(status='cancelled').count(),
    }
    total = counts['total'] or 1
    for key in ('in_progress', 'on_hold', 'completed', 'cancelled'):
        counts[key + '_pct'] = round(counts[key] * 100 / total)

    ctx = _base_context(request, 'work')
    ctx.update(_summary(employee))
    ctx.update({
        'counts': counts,
        'work_total': len(cards) + len(plans),
        'cards': cards,
        'plans': plans,
        'status_filter': status_filter,
        'status_choices': WorkAssignment.STATUS_CHOICES,
    })
    return render(request, 'staff/work_list.html', ctx)


@staff_required
def board_task_detail(request, pk):
    """One of your project-board tasks: details, attached files and comments."""
    from core.models import Task, TaskComment
    task = get_object_or_404(visible_board_tasks(request.employee).select_related('project', 'assigned_to'), pk=pk)
    member = board_member_for(request.employee)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()[:4000]
        if body:
            TaskComment.objects.create(task=task, author=request.user, body=body)
            messages.success(request, 'Comment added.')
        return redirect('staff:board_task_detail', pk=task.pk)
    from core.task_rules import MEMBER_MOVES, is_lead
    lead = is_lead(task.project, member)
    mine = member is not None and task.assigned_to_id == member.pk
    # The columns this person may move the card to.
    if lead:
        moves = Task.STATUS_CHOICES
    elif mine and task.status != 'backlog':
        allowed = MEMBER_MOVES + (('completed',) if task.project.members_can_complete else ())
        moves = [(k, v) for k, v in Task.STATUS_CHOICES if k in allowed or k == task.status]
    else:
        moves = []
    ctx = _base_context(request, 'projects')
    ctx.update({
        'task': task,
        'is_mine': mine,
        'is_lead': lead,
        'can_move': bool(moves),
        'can_tick': lead or mine,
        'needs_pr': bool(task.project.github_repo),
        'checklist': task.checklist.all(),
        'blocked_by': [l for l in task.links_in.select_related('from_task') if l.kind == 'blocks'],
        'blocks': [l for l in task.links_out.select_related('to_task') if l.kind == 'blocks'],
        'relates': list(task.links_in.filter(kind='relates').select_related('from_task'))
                   + list(task.links_out.filter(kind='relates').select_related('to_task')),
        'bugs': task.bugs.all(),
        'history': _readable_history(task),
        'attachments': task.attachments.all(),
        'comments': task.comments.filter(is_deleted=False, parent__isnull=True)
                        .select_related('author').prefetch_related('replies__author'),
        'task_status_choices': moves,
    })
    return render(request, 'staff/board_task_detail.html', ctx)


@staff_required
def board_task_update(request, pk):
    """Move a card or set its progress, through the board rules: a member moves their
    own card (To Do, In Progress, In Review); the lead moves any card."""
    from core.task_rules import TaskRuleError, change_status, is_lead
    task = get_object_or_404(visible_board_tasks(request.employee).select_related('project', 'project__team_lead'), pk=pk)
    member = board_member_for(request.employee)
    if request.method == 'POST':
        status = request.POST.get('status', task.status)
        try:
            change_status(task, status, request.user, member=member, pr_url=request.POST.get('pr_url'))
            if getattr(task, 'override_warning', ''):
                messages.warning(request, task.override_warning)
            if is_lead(task.project, member) or task.assigned_to_id == (member.pk if member else None):
                try:
                    task.progress = max(0, min(100, int(request.POST.get('progress', task.progress))))
                    task.save(update_fields=['progress', 'updated_at'])
                except (TypeError, ValueError):
                    pass
            messages.success(request, f'"{task.title}" updated.')
        except TaskRuleError as e:
            messages.error(request, str(e))
    from core.security import safe_next
    return redirect(safe_next(request, request.POST.get('back'),
                              reverse('staff:project_board', args=[task.project_id])))


BACKLOG_COLUMN = ('backlog', 'Backlog', 'backlog')
BOARD_COLUMNS = (('todo', 'To Do', 'muted'), ('in_progress', 'In Progress', 'info'),
                 ('review', 'In Review', 'warn'), ('completed', 'Completed', 'ok'))


def project_cards(employee):
    """The person's projects with their board totals, open work first."""
    from django.db.models import Count
    projects, member = staff_projects(employee)
    if member is None:
        return []
    from core.models import Project
    # Count on a fresh queryset: annotating `projects` would reuse its filtered
    # tasks join and count only this person's tasks.
    rows = (Project.objects.filter(pk__in=projects.values('pk')).select_related('client')
            .annotate(total=Count('tasks', filter=~Q(tasks__status='backlog'), distinct=True),
                      done=Count('tasks', filter=Q(tasks__status='completed'), distinct=True),
                      backlog=Count('tasks', filter=Q(tasks__status='backlog'), distinct=True),
                      mine_open=Count('tasks', filter=Q(tasks__assigned_to=member)
                                      & Q(tasks__status__in=('todo', 'in_progress', 'review')), distinct=True)))
    cards = []
    for p in rows:
        cards.append({
            'project': p, 'total': p.total, 'done': p.done, 'open': p.total - p.done,
            'mine_open': p.mine_open, 'pct': round(p.done * 100 / p.total) if p.total else 0,
            'on_team': p.team_members.filter(pk=member.pk).exists(),
            'is_lead': p.team_lead_id == member.pk,
            'backlog': p.backlog if p.team_lead_id == member.pk else 0,
        })
    cards.sort(key=lambda c: (c['project'].status == 'completed', -c['mine_open'], -c['open'],
                              c['project'].name.lower()))
    return cards


@staff_required
def project_list(request):
    """Projects: every project this person is on, each opening its own task board."""
    ctx = _base_context(request, 'projects')
    ctx['cards'] = project_cards(request.employee)
    return render(request, 'staff/project_list.html', ctx)


@staff_required
def project_board(request, pk):
    """One project's task board, in columns. Everyone on the project sees the live
    cards; the team lead also sees the Backlog and plans the weeks."""
    from core.task_rules import epic_rows, is_lead, visible_to
    projects, member = staff_projects(request.employee)
    project = get_object_or_404(projects.select_related('client', 'team_lead'), pk=pk)
    lead = is_lead(project, member)
    tasks = visible_to(project.tasks.all(), member=member).select_related('assigned_to', 'sprint', 'epic') \
        .prefetch_related('attachments', 'checklist', 'links_in__from_task')

    # Weeks: default to the running week; "all" shows every card.
    sprints = list(project.sprints.all())
    week = request.GET.get('week', '')
    sprint = None
    if week != 'all':
        sprint = next((sp for sp in sprints if str(sp.pk) == week), None) or \
            next((sp for sp in sprints if sp.status == 'active'), None)
        week = str(sprint.pk) if sprint else 'all'
    if sprint:
        tasks = tasks.filter(Q(sprint=sprint) | Q(sprint__isnull=True))

    mine_only = request.GET.get('mine') == '1'
    if mine_only:
        tasks = tasks.filter(assigned_to=member)
    issue_type = request.GET.get('type', '')
    if issue_type in ('task', 'bug', 'story'):
        tasks = tasks.filter(issue_type=issue_type)
    else:
        issue_type = ''
    epic_id = request.GET.get('epic', '')
    epics = list(project.epics.all())
    if epic_id and any(str(e.pk) == epic_id for e in epics):
        tasks = tasks.filter(epic_id=epic_id)
    else:
        epic_id = ''
    q = request.GET.get('q', '').strip()
    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q)
                             | Q(code__icontains=q))
    by_status = {}
    for t in tasks.order_by('due_date', '-created_at'):
        t.is_mine = t.assigned_to_id == member.pk
        by_status.setdefault(t.status, []).append(t)
    # The backlog reads as the plan: week by week, then in code order.
    by_status.get('backlog', []).sort(key=lambda t: (t.sprint.order if t.sprint_id else 9999, t.code, t.title))
    board = (BACKLOG_COLUMN,) + BOARD_COLUMNS if lead else BOARD_COLUMNS
    columns = [{'key': key, 'label': label, 'tone': tone, 'tasks': by_status.get(key, [])}
               for key, label, tone in board]
    team = [(m, m.staff_employee()) for m in project.team_members.filter(is_active=True)]
    active = next((sp for sp in sprints if sp.status == 'active'), None)
    ctx = _base_context(request, 'projects')
    ctx.update({
        'project': project, 'columns': columns, 'team': team, 'mine_only': mine_only, 'q': q,
        'is_lead': lead, 'sprints': sprints, 'sprint': sprint, 'week': week,
        'issue_type': issue_type, 'epic_id': epic_id, 'epics': epics,
        'epic_rows': epic_rows(project) if lead else [],
        'active_sprint': active,
        'next_sprint': _startable(sprints, active, sprint),
        # Only what the team needs: internal notes, money and files stay staff-only.
        'shared_notes': project.note_entries.filter(share_with_team=True).order_by('-pinned', '-updated_at'),
        'links': project.links.all(),
        'needs_github': not request.employee.github_username,
        'total': sum(len(c['tasks']) for c in columns),
        'mine_open': project.tasks.filter(assigned_to=member, status__in=('todo', 'in_progress', 'review')).count(),
    })
    return render(request, 'staff/project_board.html', ctx)


def _readable_history(task):
    """Activity rows with column keys turned into names (todo -> To Do)."""
    from core.models import Task
    names = dict(Task.STATUS_CHOICES)
    rows = list(task.activities.select_related('actor')[:30])
    for a in rows:
        if a.verb in ('status_changed', 'sprint_started'):
            a.from_value = names.get(a.from_value, a.from_value)
            a.to_value = names.get(a.to_value, a.to_value)
    return rows


def _startable(sprints, active, selected):
    """The week a Start button is for: the next planned one, shown only when the
    picker is on that week or on All weeks, and never while a week is running."""
    nxt = None if active else next((sp for sp in sprints if sp.status == 'planned'), None)
    return nxt if nxt and (selected is None or selected.pk == nxt.pk) else None


def _lead_project(request, pk):
    """The project, if the signed-in person is its team lead; else 404."""
    from core.task_rules import is_lead
    projects, member = staff_projects(request.employee)
    project = get_object_or_404(projects.select_related('team_lead'), pk=pk)
    if not is_lead(project, member):
        raise Http404('Only the team lead can plan this board.')
    return project, member


def _task_form_values(request, project):
    """Fields a lead sets on a card, read from the staff task form."""
    from datetime import date as _date
    from core.models import Task
    post = request.POST
    member_id = post.get('assigned_to', '')
    sprint_id = post.get('sprint', '')
    due = post.get('due_date', '').strip()
    priority = post.get('priority', 'medium')
    pr = post.get('pr_url', '').strip()[:500]
    try:
        due = _date.fromisoformat(due) if due else None
    except ValueError:
        due = None
    return {
        'description': post.get('description', '').strip()[:5000],
        'assigned_to': project.team_members.filter(pk=member_id).first() if _uuid_ok(member_id) else None,
        'sprint': project.sprints.filter(pk=sprint_id).first() if _uuid_ok(sprint_id) else None,
        'due_date': due,
        'priority': priority if priority in dict(Task.PRIORITY_CHOICES) else 'medium',
        'category': post.get('label', '').strip()[:60],
        'branch_name': post.get('branch_name', '').strip()[:120],
        'pr_url': pr if pr.startswith(('http://', 'https://')) else '',
        'issue_type': post.get('issue_type') if post.get('issue_type') in ('task', 'bug', 'story') else 'task',
        'epic': project.epics.filter(pk=post.get('epic', '')).first() if _uuid_ok(post.get('epic', '')) else None,
        'steps_to_reproduce': post.get('steps_to_reproduce', '').strip()[:5000],
    }


def _uuid_ok(value):
    import uuid as _uuid
    try:
        _uuid.UUID(str(value))
        return True
    except ValueError:
        return False


@staff_required
def board_task_create(request, pk):
    """Team lead: add a card (to the backlog of a week, or straight to To Do)."""
    from core.task_rules import TaskRuleError, create_task
    project, member = _lead_project(request, pk)
    if request.method == 'POST':
        status = request.POST.get('status', 'backlog')
        try:
            task = create_task(project, request.user, title=request.POST.get('title', ''),
                               checklist=request.POST.get('checklist', '').splitlines(),
                               status=status if status in ('backlog', 'todo') else 'backlog',
                               **_task_form_values(request, project))
        except TaskRuleError as e:
            messages.error(request, str(e))
            return redirect('staff:board_task_create', pk=project.pk)
        messages.success(request, f'{task.code or "Card"} added{" to the backlog" if task.status == "backlog" else ""}.')
        if request.POST.get('another'):
            return redirect(f"{reverse('staff:board_task_create', args=[project.pk])}?week={task.sprint_id or ''}")
        return redirect('staff:project_board', pk=project.pk)
    from core.models import Task
    ctx = _base_context(request, 'projects')
    ctx.update({'project': project, 'task': None, 'team_options': project.team_members.filter(is_active=True),
                'sprint_options': project.sprints.exclude(status='done'),
                'epic_options': project.epics.filter(is_closed=False), 'type_choices': Task.ISSUE_TYPES,
                'priority_choices': Task.PRIORITY_CHOICES, 'preset_week': request.GET.get('week', '')})
    return render(request, 'staff/board_task_form.html', ctx)


@staff_required
def board_task_edit(request, pk):
    """Team lead: edit a card's details, owner, week, branch and checklist."""
    from core.models import Task
    from core.task_rules import is_lead, log
    task = get_object_or_404(visible_board_tasks(request.employee).select_related('project', 'assigned_to'), pk=pk)
    project, member = _lead_project(request, task.project_id)
    if request.method == 'POST':
        values = _task_form_values(request, project)
        old_owner, old_sprint, old_epic = task.assigned_to, task.sprint, task.epic
        title = request.POST.get('title', '').strip()[:255]
        if title:
            task.title = title
        for field, value in values.items():
            setattr(task, field, value)
        task.save()
        if old_owner != task.assigned_to:
            log(task, request.user, 'assigned', from_value=old_owner.name if old_owner else '',
                to_value=task.assigned_to.name if task.assigned_to else '')
        if old_sprint != task.sprint:
            log(task, request.user, 'sprint_changed', from_value=old_sprint.name if old_sprint else '',
                to_value=task.sprint.name if task.sprint else '')
        if old_epic != task.epic:
            log(task, request.user, 'epic_changed', from_value=old_epic.name if old_epic else '',
                to_value=task.epic.name if task.epic else '')
        from core.views import _save_checklist
        _save_checklist(task, request.POST.get('checklist', ''))
        messages.success(request, f'{task.code or task.title} saved.')
        return redirect('staff:board_task_detail', pk=task.pk)
    ctx = _base_context(request, 'projects')
    ctx.update({'project': project, 'task': task, 'team_options': project.team_members.filter(is_active=True),
                'sprint_options': project.sprints.exclude(status='done'),
                'epic_options': project.epics.filter(is_closed=False), 'type_choices': Task.ISSUE_TYPES,
                'priority_choices': Task.PRIORITY_CHOICES,
                'checklist_text': '\n'.join(task.checklist.values_list('text', flat=True))})
    return render(request, 'staff/board_task_form.html', ctx)


@staff_required
def bug_report(request, pk):
    """Anyone on the project reports a bug: unassigned, To Do of the running week."""
    from core.models import Task
    from core.task_rules import TaskRuleError, report_bug
    projects, member = staff_projects(request.employee)
    project = get_object_or_404(projects, pk=pk)
    found_id = request.POST.get('found_in') or request.GET.get('found_in', '')
    found_in = visible_board_tasks(request.employee).filter(project=project, pk=found_id).first() \
        if _uuid_ok(found_id) else None
    if request.method == 'POST':
        priority = request.POST.get('priority', 'medium')
        try:
            bug = report_bug(project, request.user, title=request.POST.get('title', ''),
                             description=request.POST.get('description', '').strip()[:5000],
                             steps=request.POST.get('steps_to_reproduce', '').strip()[:5000],
                             found_in=found_in,
                             priority=priority if priority in dict(Task.PRIORITY_CHOICES) else 'medium')
        except TaskRuleError as e:
            messages.error(request, str(e))
            return redirect(request.get_full_path())
        lead = project.team_lead
        if lead and lead != member:
            from core.task_rules import _notify_member
            _notify_member(lead, f'Bug reported: {bug.code or bug.title}',
                           f'{request.user.get_full_name() or request.user.username} reported "{bug.title}".', project)
        messages.success(request, f'Bug {bug.code or ""} reported. {project.team_lead.name if project.team_lead else "An admin"} will triage it.')
        return redirect('staff:board_task_detail', pk=bug.pk)
    ctx = _base_context(request, 'projects')
    ctx.update({'project': project, 'found_in': found_in, 'priority_choices': Task.PRIORITY_CHOICES})
    return render(request, 'staff/bug_form.html', ctx)


def _find_card(project, ref):
    """A card on the project by code (ALW-019, any case) or id."""
    from core.models import Task
    ref = (ref or '').strip()
    if _uuid_ok(ref):
        return project.tasks.filter(pk=ref).first()
    return project.tasks.filter(code__iexact=ref).first() if ref else None


@staff_required
def link_add(request, pk):
    """Team lead: this card is blocked by / blocks / relates to another card (by code)."""
    from core.task_rules import TaskRuleError, link_tasks
    task = get_object_or_404(visible_board_tasks(request.employee).select_related('project'), pk=pk)
    _lead_project(request, task.project_id)
    if request.method == 'POST':
        other = _find_card(task.project, request.POST.get('code'))
        relation = request.POST.get('relation', 'blocked_by')
        if other is None:
            messages.error(request, f'No card "{request.POST.get("code", "")}" on {task.project.name}.')
        else:
            try:
                if relation == 'blocked_by':
                    link_tasks(other, task, 'blocks', request.user)
                elif relation == 'blocks':
                    link_tasks(task, other, 'blocks', request.user)
                else:
                    link_tasks(task, other, 'relates', request.user)
                messages.success(request, 'Link added.')
            except TaskRuleError as e:
                messages.error(request, str(e))
    return redirect('staff:board_task_detail', pk=task.pk)


@staff_required
def link_remove(request, pk, link_id):
    from django.db.models import Q as _Q
    from core.models import TaskLink
    from core.task_rules import unlink_tasks
    task = get_object_or_404(visible_board_tasks(request.employee).select_related('project'), pk=pk)
    _lead_project(request, task.project_id)
    link = get_object_or_404(TaskLink.objects.filter(_Q(from_task=task) | _Q(to_task=task)), pk=link_id)
    if request.method == 'POST':
        unlink_tasks(link, request.user)
        messages.success(request, 'Link removed.')
    return redirect('staff:board_task_detail', pk=task.pk)


@staff_required
def epic_create(request, pk):
    from core.task_rules import TaskRuleError, create_epic
    project, member = _lead_project(request, pk)
    if request.method == 'POST':
        try:
            e = create_epic(project, name=request.POST.get('name', ''), color=request.POST.get('color', ''))
            messages.success(request, f'Epic "{e.name}" added.')
        except TaskRuleError as e:
            messages.error(request, str(e))
    return redirect(f"{reverse('staff:project_board', args=[project.pk])}#epics")


@staff_required
def epic_toggle(request, pk, epic_id):
    project, member = _lead_project(request, pk)
    epic = get_object_or_404(project.epics, pk=epic_id)
    if request.method == 'POST':
        epic.is_closed = not epic.is_closed
        epic.save(update_fields=['is_closed'])
        messages.success(request, f'Epic "{epic.name}" {"closed" if epic.is_closed else "reopened"}.')
    return redirect(f"{reverse('staff:project_board', args=[project.pk])}#epics")


@staff_required
def checklist_toggle(request, pk, item_id):
    """Tick or untick a Done-when line (card owner, lead)."""
    from core.models import TaskChecklistItem
    from core.task_rules import TaskRuleError, set_checklist_item
    task = get_object_or_404(visible_board_tasks(request.employee), pk=pk)
    item = get_object_or_404(TaskChecklistItem.objects.select_related('task__project'), pk=item_id, task=task)
    if request.method == 'POST':
        try:
            set_checklist_item(item, request.POST.get('done') == '1', request.user,
                               member=board_member_for(request.employee))
        except TaskRuleError as e:
            messages.error(request, str(e))
    return redirect('staff:board_task_detail', pk=task.pk)


@staff_required
def sprint_create(request, pk):
    """Team lead: add a week to the plan."""
    from datetime import date as _date
    from core.task_rules import TaskRuleError, create_sprint
    project, member = _lead_project(request, pk)
    if request.method == 'POST':
        try:
            sp = create_sprint(project, name=request.POST.get('name', ''), goal=request.POST.get('goal', ''),
                               start_date=_date.fromisoformat(request.POST.get('start_date', '')),
                               end_date=_date.fromisoformat(request.POST.get('end_date', '')))
            messages.success(request, f'{sp.name} added.')
        except ValueError:
            messages.error(request, 'Give the week a start and end date.')
        except TaskRuleError as e:
            messages.error(request, str(e))
    return redirect('staff:project_board', pk=project.pk)


@staff_required
def sprint_action(request, pk, sprint_id, action):
    """Team lead: start or close a week."""
    from core.task_rules import TaskRuleError, close_sprint, start_sprint
    project, member = _lead_project(request, pk)
    sprint = get_object_or_404(project.sprints, pk=sprint_id)
    if request.method == 'POST':
        try:
            if action == 'start':
                r = start_sprint(sprint, request.user)
                msg = f'{sprint.name} started: {r["moved"]} card{"s" if r["moved"] != 1 else ""} moved to To Do and the team was notified.'
                if r['unassigned']:
                    msg += f' {len(r["unassigned"])} card{"s have" if len(r["unassigned"]) != 1 else " has"} no owner.'
                messages.success(request, msg)
            elif action == 'close':
                r = close_sprint(sprint, request.user, request.POST.get('carry_over', 'next'))
                msg = f'{sprint.name} closed: {r["completed"]} completed.'
                if r['carried_over']:
                    msg += f' {r["carried_over"]} open card{"s" if r["carried_over"] != 1 else ""} moved to {r["to"]}.'
                messages.success(request, msg)
        except TaskRuleError as e:
            messages.error(request, str(e))
    return redirect('staff:project_board', pk=project.pk)


@staff_required
def work_detail(request, pk):
    employee = request.employee
    assignment = get_object_or_404(
        WorkAssignment.objects.filter(assigned_to=employee).select_related('project'), pk=pk)

    from wallet.models import XPSettings
    ctx = _base_context(request, 'work')
    ctx.update({
        'assignment': assignment,
        'xp': assignment.xp_reward if assignment.xp_reward is not None
              else XPSettings.current().priority_xp(assignment.priority),
        'updates': assignment.updates.select_related('employee__user'),
        'status_choices': WorkAssignment.STATUS_CHOICES,
    })
    return render(request, 'staff/work_detail.html', ctx)


# --- Intern bootcamp (Academy course) --------------------------------------

@staff_required
def bootcamp_open(request):
    """Enrol the intern in the bootcamp on first visit, then open the course or a lesson."""
    employee = request.employee
    if not is_intern(employee):
        raise Http404
    track = bootcamp.enrol(employee)
    if track is None:
        messages.info(request, 'The bootcamp is not available on your account right now. Please ask HR.')
        return redirect('staff:dashboard')
    lesson_id = request.GET.get('lesson', '')
    if lesson_id and track.lessons.filter(pk=lesson_id).exists():
        return redirect('academy:lesson', lesson_id=lesson_id)
    return redirect('academy:track', track_id=track.id)


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
    assessments = list(InternAssessment.objects.filter(employee=employee).select_related('mcq_test'))
    graded = [a for a in assessments if a.is_graded]
    to_take = [a for a in assessments if a.mcq_pending and a.mcq_test]

    ctx = _base_context(request, 'assessments')
    ctx.update({
        'to_take': to_take,
        'today': timezone.localdate(),
        'assessments': [a for a in assessments if a not in to_take],
        'average': round(sum(a.percentage for a in graded) / len(graded), 1) if graded else None,
        'graded_count': len(graded),
    })
    return render(request, 'staff/assessment_list.html', ctx)


def _my_mcq(request, pk):
    return get_object_or_404(
        InternAssessment.objects.select_related('mcq_test'),
        pk=pk, employee=request.employee, mcq_test__isnull=False)


@staff_required
def assessment_take(request, pk):
    """Take an MCQ test: one page of questions, an optional countdown, marked
    on submit. Answers never reach the page until the test is submitted."""
    from . import mcq
    a = _my_mcq(request, pk)
    test = a.mcq_test
    if a.submitted_at:
        return redirect('staff:assessment_result', pk=a.pk)
    if not test.is_active and not a.started_at:
        messages.info(request, 'This test is closed. Please ask HR.')
        return redirect('staff:assessment_list')

    if request.method == 'POST':
        if not a.started_at:
            return redirect('staff:assessment_take', pk=a.pk)
        posted = {k[2:]: v for k, v in request.POST.items() if k.startswith('q_')}
        mcq.grade(a, posted)
        messages.success(request, f'Test submitted. You scored {a.scored.normalize()} out of '
                                  f'{a.max_score.normalize()}.')
        return redirect('staff:assessment_result', pk=a.pk)

    if request.GET.get('start') == '1' and not a.started_at:
        a.started_at = timezone.now()
        a.save(update_fields=['started_at', 'updated_at'])
        return redirect('staff:assessment_take', pk=a.pk)

    ctx = _base_context(request, 'assessments')
    ctx.update({'a': a, 'test': test})
    if not a.started_at:
        return render(request, 'staff/assessment_start.html', ctx)

    ends = mcq.deadline(a)
    if ends and timezone.now() > ends + timedelta(seconds=mcq.GRACE_SECONDS):
        # Time ran out and nothing came back (closed tab, lost network): mark it
        # with whatever was answered, which is nothing.
        mcq.grade(a, {})
        messages.warning(request, 'Time is up for this test, so it was submitted with no answers.')
        return redirect('staff:assessment_result', pk=a.pk)

    questions = test.questions
    ctx.update({
        'questions': [{'num': n, 'idx': i, 'text': questions[i]['question'], 'marks': questions[i].get('marks', 1),
                       'options': [{'letter': mcq.LETTERS[j], 'text': t, 'idx': j}
                                   for j, t in enumerate(questions[i]['options'])]}
                      for n, i in enumerate(mcq.question_order(a), start=1)],
        'seconds_left': max(0, int((ends - timezone.now()).total_seconds())) if ends else None,
    })
    return render(request, 'staff/assessment_take.html', ctx)


@staff_required
def assessment_result(request, pk):
    from . import mcq
    a = _my_mcq(request, pk)
    if not a.submitted_at:
        return redirect('staff:assessment_take', pk=a.pk)
    rows = mcq.review_rows(a)
    ctx = _base_context(request, 'assessments')
    ctx.update({
        'a': a, 'test': a.mcq_test, 'rows': rows, 'show_answers': a.mcq_test.show_answers,
        'right': sum(r['is_right'] for r in rows), 'wrong': sum(not r['is_right'] and not r['skipped'] for r in rows),
        'skipped': sum(r['skipped'] for r in rows),
    })
    return render(request, 'staff/assessment_result.html', ctx)


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


# --- Resignation -----------------------------------------------------------

@staff_required
def resignation(request):
    """Start a resignation, or see where it stands and download the letters.

    Starting one only creates the request and hands the person to the same
    public form HR links use, so there is one form to keep right.
    """
    from .resignation_models import ResignationRequest

    employee = request.employee
    current = employee.resignations.exclude(status=ResignationRequest.STATUS_CANCELLED).first()
    if request.method == 'POST':
        open_one = employee.resignations.filter(status__in=ResignationRequest.ACTIVE_STATUSES).first()
        if open_one is None:
            open_one = ResignationRequest.objects.create(employee=employee, created_by=request.user,
                                                         source='self')
        elif open_one.is_expired:
            from .resignation_models import default_resignation_expiry
            open_one.expires_at = default_resignation_expiry()
            open_one.save(update_fields=['expires_at', 'updated_at'])
        return redirect(open_one.public_path())

    ctx = _base_context(request, 'resignation')
    ctx.update({'current': current})
    return render(request, 'staff/resignation.html', ctx)


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


GITHUB_RE = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$')


@staff_required
def github_save(request):
    """Save the person's GitHub username (from Profile or a project board)."""
    from core.security import safe_next
    if request.method == 'POST':
        name = request.POST.get('github_username', '').strip().lstrip('@')
        name = re.sub(r'^(https?://)?(www\.)?github\.com/', '', name).strip('/')
        if name and not GITHUB_RE.match(name):
            messages.error(request, 'That does not look like a GitHub username: letters, numbers and '
                                    'single hyphens only, up to 39 characters.')
        else:
            request.employee.github_username = name
            request.employee.save(update_fields=['github_username'])
            messages.success(request, f'GitHub username saved: {name}.' if name else 'GitHub username removed.')
    return redirect(safe_next(request, request.POST.get('back'), 'staff:profile'))


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
