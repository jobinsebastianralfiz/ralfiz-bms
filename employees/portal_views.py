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
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .models import (
    Attendance, Employee, InternAssessment, LeaveRequest, LeaveType,
    Notification, OfficeConfig, Payroll, ScheduledClass, WorkAssignment,
)

# Bump this whenever a file under static/css, static/js or static/staff
# changes. Whitenoise serves these unhashed, and the service worker is
# cache-first for static assets, so an unversioned URL is served from the old
# cache forever -- which is exactly how the app icon got stuck.
ASSET_V = '6'

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
        return redirect(request.GET.get('next') or 'staff:dashboard')

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

    attendance = Attendance.objects.filter(employee=employee, date=today).first()
    open_work = (WorkAssignment.objects
                 .filter(assigned_to=employee)
                 .exclude(status__in=['completed', 'cancelled'])
                 .order_by('due_date', '-created_at')[:5])
    pending_leave = LeaveRequest.objects.filter(employee=employee, status='pending').count()

    upcoming_classes = [c for c in ScheduledClass.objects.filter(
        Q(interns=employee) | Q(interns__isnull=True),
        date__gte=today,
    ).exclude(status='cancelled').distinct().order_by('date', 'start_time')[:5]]

    month_attendance = Attendance.objects.filter(
        employee=employee, date__year=today.year, date__month=today.month)

    ctx = _base_context(request, 'dashboard')
    ctx.update({
        'today': today,
        'attendance': attendance,
        'open_work': open_work,
        'pending_leave': pending_leave,
        'upcoming_classes': upcoming_classes,
        'days_present': month_attendance.exclude(status='absent').count(),
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

    ctx = _base_context(request, 'attendance')
    ctx.update({
        'today': today,
        'record': record,
        'config': cfg,
        'office_configured': bool(cfg),
        'has_face': bool(employee.face_photo),
        'can_remote': employee.work_mode in ('hybrid', 'remote'),
        'checkout_allowed': record.is_checkout_allowed() if record and record.check_in else False,
        'seconds_until_eligible': (record.seconds_until_eligible()
                                   if record and record.check_in and not record.check_out else 0),
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

    ctx = _base_context(request, 'attendance')
    ctx.update({
        'records': records,
        'year': year,
        'month': month,
        'month_name': MONTHS[month],
        'present_count': records.exclude(status='absent').count(),
        'late_count': records.filter(status='late').count(),
        'total_hours': sum(float(r.worked_hours or 0) for r in records),
    })
    return render(request, 'staff/attendance_history.html', ctx)


# --- Leave -----------------------------------------------------------------

@staff_required
def leave(request):
    employee = request.employee
    year = timezone.localdate().year

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

    ctx = _base_context(request, 'leave')
    ctx.update({
        'balances': balances,
        'leave_types': LeaveType.objects.filter(is_active=True),
        'requests': LeaveRequest.objects.filter(employee=employee).select_related('leave_type'),
        'year': year,
    })
    return render(request, 'staff/leave.html', ctx)


# --- Work assignments ------------------------------------------------------

@staff_required
def work_list(request):
    employee = request.employee
    assignments = WorkAssignment.objects.filter(assigned_to=employee).select_related('project')
    status_filter = request.GET.get('status', '')
    if status_filter:
        assignments = assignments.filter(status=status_filter)

    ctx = _base_context(request, 'work')
    ctx.update({
        'assignments': assignments,
        'status_filter': status_filter,
        'status_choices': WorkAssignment.STATUS_CHOICES,
    })
    return render(request, 'staff/work_list.html', ctx)


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
    notifications = Notification.objects.filter(
        Q(employee=employee) | Q(employee__isnull=True))[:100]

    ctx = _base_context(request, 'notifications')
    ctx.update({'notifications': notifications})
    return render(request, 'staff/notification_list.html', ctx)


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
