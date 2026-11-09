"""The intern bootcamp: the Academy course `django`, opened from the staff portal.

Interns are Employees, not Academy students, so the first time one opens the
course we give their login a Student profile and enrol it. Academy then
tracks lessons, labs, quizzes and tests as for any learner. An active
employee with a Student profile is not confined to /academy/ (see
academy.access.student_only), so this does not change their portal access.
"""
from academy.models import Enrollment, Student, Track
from academy.progress import track_summary

TRACK_ID = 'django'


def bootcamp_track():
    return Track.objects.filter(pk=TRACK_ID, is_published=True).first()


def enrol(employee):
    """Give the employee's login Academy access to the bootcamp. Idempotent."""
    track = bootcamp_track()
    if track is None:
        return None
    student, _ = Student.objects.get_or_create(user=employee.user, defaults={'batch': 'Interns'})
    if student.status != 'active':
        # HR switched their Academy access off; don't silently turn it back on.
        return None
    Enrollment.objects.get_or_create(student=student, track=track, defaults={'batch': 'Interns'})
    return track


def dashboard_summary(employee):
    """Progress for the dashboard card, or None when the course isn't installed."""
    track = bootcamp_track()
    if track is None:
        return None
    return track_summary(employee.user, track)
