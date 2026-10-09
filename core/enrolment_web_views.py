"""HR screens for internship enrolment: send a student their personal link,
review what they submitted, and approve them into an intern login."""
import mimetypes
import secrets
from datetime import date
from functools import wraps
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from employees.enrolment_models import (WORK_MODE_CHOICES, EnrolmentSettings, InternEnrolment,
                                        default_enrolment_expiry)
from employees.models import Employee

DOCUMENT_FIELDS = ('photo', 'id_proof', 'resume', 'college_letter')
#: No 0/O, 1/l/I: the password is read off a phone and typed by hand.
PASSWORD_ALPHABET = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def can_manage_enrolments(user):
    """Enrolments hold ID proofs, so only the people who run the business see
    them -- not an intern who happens to be logged in to the web app."""
    if user.is_superuser or user.is_staff or hasattr(user, 'team_profile'):
        return True
    return Employee.objects.filter(user=user, status='active', role__in=('owner', 'partner')).exists()


def enrolment_admin(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not can_manage_enrolments(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


@enrolment_admin
def enrolment_list(request):
    qs = InternEnrolment.objects.select_related('employee')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()
    now = timezone.now()

    if status_filter == 'expired':
        qs = qs.filter(status__in=InternEnrolment.OPEN_STATUSES, expires_at__lt=now)
    elif status_filter == 'open':
        qs = qs.filter(status__in=InternEnrolment.OPEN_STATUSES, expires_at__gte=now)
    elif status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(Q(invite_name__icontains=search) | Q(full_name__icontains=search)
                       | Q(invite_phone__icontains=search) | Q(phone__icontains=search)
                       | Q(college_name__icontains=search))

    all_rows = InternEnrolment.objects.all()
    open_rows = all_rows.filter(status__in=InternEnrolment.OPEN_STATUSES)
    counters = {
        'waiting': open_rows.filter(expires_at__gte=now).count(),
        'to_review': all_rows.filter(status=InternEnrolment.STATUS_SUBMITTED).count(),
        'approved': all_rows.filter(status=InternEnrolment.STATUS_APPROVED).count(),
        'expired': open_rows.filter(expires_at__lt=now).count(),
    }
    return render(request, 'hr/enrolment_list.html', {
        'enrolments': qs[:300],
        'counters': counters,
        'status_filter': status_filter,
        'search': search,
        'statuses': InternEnrolment.STATUS_CHOICES,
    })


@enrolment_admin
def enrolment_send(request):
    posted = {}
    if request.method == 'POST':
        posted = {k: (request.POST.get(k) or '').strip() for k in ('name', 'phone', 'email')}
        if not posted['name']:
            messages.error(request, "Enter the student's name.")
        elif not posted['phone'] and not posted['email']:
            messages.error(request, 'Enter a phone number or an email so you can send the link.')
        else:
            enrolment = InternEnrolment.objects.create(
                invite_name=posted['name'], invite_phone=posted['phone'],
                invite_email=posted['email'], created_by=request.user,
            )
            messages.success(request, f'Enrolment link created for {enrolment.invite_name}. '
                                      'Send it on WhatsApp or copy it below.')
            return redirect('enrolment_detail', pk=enrolment.pk)
    return render(request, 'hr/enrolment_send.html', {'posted': posted})


@enrolment_admin
def enrolment_detail(request, pk):
    enrolment = get_object_or_404(
        InternEnrolment.objects.select_related('employee__user', 'created_by', 'reviewed_by'), pk=pk)
    login = request.session.pop(f'enrolment_login_{enrolment.pk}', None)
    if login:
        login['whatsapp'] = _login_whatsapp(request, enrolment, login)
    return render(request, 'hr/enrolment_detail.html', {
        'enrolment': enrolment,
        'url': enrolment.public_url(request),
        'whatsapp': enrolment.whatsapp_url(request),
        'login': login,
        'departments': Employee.DEPARTMENT_CHOICES,
        'suggested': {
            'username': enrolment.suggested_username() if enrolment.status == 'submitted' else '',
            'joining_date': (enrolment.preferred_start_date or timezone.localdate()).isoformat(),
            'department': EnrolmentSettings.get().department_for(enrolment.track),
            'designation': f'{enrolment.track_label} Intern' if enrolment.track else 'Intern',
        },
    })


def _login_whatsapp(request, enrolment, login):
    from urllib.parse import quote
    digits = ''.join(ch for ch in (enrolment.whatsapp or enrolment.phone or '') if ch.isdigit())
    if not digits:
        return ''
    if len(digits) == 10:
        digits = '91' + digits
    message = (
        f'Hi {enrolment.full_name},\n\nYour internship at Ralfiz Technologies is confirmed. '
        f'Sign in to the staff portal here:\n{request.build_absolute_uri("/staff/")}\n\n'
        f'Username: {login["username"]}\nPassword: {login["password"]}\n\n'
        'Please change your password after you sign in.'
    )
    return f'https://wa.me/{digits}?text={quote(message)}'


@enrolment_admin
@require_POST
def enrolment_approve(request, pk):
    enrolment = get_object_or_404(InternEnrolment, pk=pk)
    username = (request.POST.get('username') or '').strip()
    department = request.POST.get('department') or 'other'
    designation = (request.POST.get('designation') or 'Intern').strip()
    try:
        joining_date = date.fromisoformat(request.POST.get('joining_date') or '')
    except ValueError:
        messages.error(request, 'Choose a valid joining date.')
        return redirect('enrolment_detail', pk=pk)
    if not username or not username.replace('.', '').replace('_', '').isalnum():
        messages.error(request, 'Usernames can use letters, numbers, dots and underscores only.')
        return redirect('enrolment_detail', pk=pk)
    if department not in dict(Employee.DEPARTMENT_CHOICES):
        department = 'other'

    password = ''.join(secrets.choice(PASSWORD_ALPHABET) for _ in range(10))
    try:
        employee = enrolment.approve(request.user, username=username, password=password,
                                     joining_date=joining_date, department=department,
                                     designation=designation)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('enrolment_detail', pk=pk)

    # Shown once on the next page load, then gone -- like the employee form's message.
    request.session[f'enrolment_login_{enrolment.pk}'] = {'username': username, 'password': password}
    messages.success(request, f'{employee.full_name} is now intern {employee.employee_id}.')
    return redirect('enrolment_detail', pk=pk)


@enrolment_admin
@require_POST
def enrolment_reject(request, pk):
    enrolment = get_object_or_404(InternEnrolment, pk=pk)
    try:
        enrolment.reject(request.user, (request.POST.get('reason') or '').strip())
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, 'Enrolment rejected.')
    return redirect('enrolment_detail', pk=pk)


@enrolment_admin
@require_POST
def enrolment_cancel(request, pk):
    enrolment = get_object_or_404(InternEnrolment, pk=pk)
    if enrolment.status in InternEnrolment.OPEN_STATUSES:
        enrolment.status = InternEnrolment.STATUS_CANCELLED
        enrolment.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Link cancelled. It no longer opens.')
    else:
        messages.error(request, 'This enrolment has already been filled in.')
    return redirect('enrolment_detail', pk=pk)


@enrolment_admin
@require_POST
def enrolment_extend(request, pk):
    """Give an unfilled link another 14 days (same link, so a resend works)."""
    enrolment = get_object_or_404(InternEnrolment, pk=pk)
    if enrolment.status in InternEnrolment.OPEN_STATUSES:
        enrolment.expires_at = default_enrolment_expiry()
        enrolment.save(update_fields=['expires_at', 'updated_at'])
        messages.success(request, 'Link extended by 14 days.')
    return redirect('enrolment_detail', pk=pk)


@enrolment_admin
def enrolment_file(request, pk, field):
    if field not in DOCUMENT_FIELDS:
        raise Http404
    enrolment = get_object_or_404(InternEnrolment, pk=pk)
    document = getattr(enrolment, field)
    if not document:
        raise Http404
    name = f'{enrolment.display_name} - {field.replace("_", " ")}{Path(document.name).suffix}'
    content_type = mimetypes.guess_type(document.name)[0] or 'application/octet-stream'
    response = FileResponse(document.open('rb'), content_type=content_type, filename=name)
    response['X-Content-Type-Options'] = 'nosniff'
    return response


#: Rows offered on the settings page beyond the current areas, for adding new ones.
BLANK_TRACK_ROWS = 3
MAX_DURATION_MONTHS = 12


@enrolment_admin
def enrolment_settings(request):
    """What the student form offers: work modes, internship areas, durations."""
    settings = EnrolmentSettings.get()
    departments = dict(Employee.DEPARTMENT_CHOICES)

    if request.method == 'POST':
        work_modes = [k for k, _ in WORK_MODE_CHOICES if request.POST.get(f'work_mode_{k}')]
        tracks, seen = [], set()
        for label, department in zip(request.POST.getlist('track_label'),
                                     request.POST.getlist('track_department')):
            label = label.strip()[:200]
            if label and label.casefold() not in seen:
                seen.add(label.casefold())
                tracks.append({'label': label,
                               'department': department if department in departments else 'other'})
        durations = sorted({int(n) for n in request.POST.getlist('duration')
                            if n.isdigit() and 1 <= int(n) <= MAX_DURATION_MONTHS})
        allow_other = bool(request.POST.get('allow_other_track'))

        problems = []
        if not work_modes:
            problems.append('Tick at least one work mode.')
        if not tracks and not allow_other:
            problems.append('Add at least one internship area, or allow "Other".')
        if not durations:
            problems.append('Tick at least one duration.')
        if problems:
            for problem in problems:
                messages.error(request, problem)
        else:
            settings.work_modes = work_modes
            settings.tracks = tracks
            settings.durations = durations
            settings.allow_other_track = allow_other
            settings.save()
            messages.success(request, 'Enrolment form options saved. New and open links use them right away.')
            return redirect('enrolment_settings')

    rows = list(settings.tracks) + [{'label': '', 'department': 'engineering'}] * BLANK_TRACK_ROWS
    return render(request, 'hr/enrolment_settings.html', {
        'settings': settings,
        'work_modes': [(k, label, k in settings.work_modes) for k, label in WORK_MODE_CHOICES],
        'track_rows': rows,
        'departments': Employee.DEPARTMENT_CHOICES,
        'durations': [(n, n in settings.durations) for n in range(1, MAX_DURATION_MONTHS + 1)],
    })
