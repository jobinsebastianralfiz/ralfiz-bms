"""Who may use the Academy portal, and which tracks they see."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import Student, Track


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def student_only(user):
    """True for a login whose only role is Academy student.

    Such a login is kept inside /academy/ (see middleware). Anyone who also
    has a staff, team, employee or client role keeps their usual access.
    """
    if not user.is_authenticated or user.is_staff or user.is_superuser:
        return False
    if not Student.objects.filter(user=user).exists():
        return False
    if hasattr(user, 'team_profile') or hasattr(user, 'client_profile'):
        return False
    from employees.models import Employee
    return not Employee.objects.filter(user=user, status='active').exists()


def learner_required(view_func):
    """An active student, or an admin previewing the courses."""
    @wraps(view_func)
    @login_required(login_url='academy:login')
    def wrapper(request, *args, **kwargs):
        student = Student.objects.select_related('user').filter(user=request.user).first()
        if student and student.status == 'active':
            request.student, request.is_preview = student, False
        elif is_admin(request.user):
            request.student, request.is_preview = student, True
        else:
            messages.error(request, 'This account has no active Academy access.')
            return redirect('academy:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def visible_tracks(request):
    """Published tracks this learner is enrolled in (all of them for a preview)."""
    tracks = Track.objects.filter(is_published=True)
    if request.is_preview:
        return tracks
    return tracks.filter(enrollments__student=request.student)


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
