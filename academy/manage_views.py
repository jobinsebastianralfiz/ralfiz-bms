"""Owner pages for the Academy, inside the BMS layout at /academy/manage/."""
import csv
import secrets

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Max, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .access import admin_required
from .models import (
    ContentImport, Enrollment, LabProgress, Lesson, Question, QuizAnswer, Student,
    TestAttempt, Track,
)
from . import perks as perks_mod
from .progress import DONE, IN_PROGRESS, lesson_statuses, track_summary


def _new_password():
    # Readable enough to read out over the phone: no 0/O or 1/l.
    alphabet = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alphabet) for _ in range(10))


class StudentForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=False)
    batch = forms.CharField(max_length=100, required=False,
                            help_text='For example "Oct 2026 weekend". Used to filter reports.')
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    tracks = forms.ModelMultipleChoiceField(queryset=Track.objects.all(), required=False,
                                            widget=forms.CheckboxSelectMultiple)


class NewStudentForm(StudentForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=128, required=False,
                               help_text='Leave blank to generate one.')

    field_order = ['first_name', 'last_name', 'username', 'password', 'email', 'phone',
                   'batch', 'tracks', 'notes']

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('That username is taken.')
        return username


def _sync_enrollments(student, tracks):
    wanted = {t.pk for t in tracks}
    student.enrollments.exclude(track_id__in=wanted).delete()
    have = set(student.enrollments.values_list('track_id', flat=True))
    Enrollment.objects.bulk_create([Enrollment(student=student, track_id=t, batch=student.batch)
                                    for t in wanted - have])


# --- Overview --------------------------------------------------------------------

@admin_required
def manage_home(request):
    tracks = Track.objects.annotate(
        lesson_count=Count('lessons', distinct=True),
        student_count=Count('enrollments', distinct=True),
    )
    question_counts = dict(Question.objects.filter(is_active=True).values('track')
                           .annotate(n=Count('id')).values_list('track', 'n'))
    for t in tracks:
        t.question_count = question_counts.get(t.pk, 0)
    students = Student.objects.select_related('user')
    recent_tests = (TestAttempt.objects.filter(submitted_at__isnull=False,
                                               user__student_profile__isnull=False)
                    .select_related('user', 'track')[:8])
    return render(request, 'academy/manage/home.html', {
        'tracks': tracks,
        'student_total': students.count(),
        'student_active': students.filter(status='active').count(),
        'batches': (Student.objects.exclude(batch='').values('batch')
                    .annotate(n=Count('id')).order_by('batch')),
        'recent_tests': recent_tests,
        'last_import': ContentImport.objects.first(),
    })


# --- Students --------------------------------------------------------------------

@admin_required
def manage_students(request):
    students = (Student.objects.select_related('user', 'last_lesson')
                .prefetch_related('enrollments__track'))
    search = request.GET.get('search', '').strip()
    batch = request.GET.get('batch', '')
    track = request.GET.get('track', '')
    if search:
        students = students.filter(Q(user__first_name__icontains=search) |
                                   Q(user__last_name__icontains=search) |
                                   Q(user__username__icontains=search) |
                                   Q(user__email__icontains=search) | Q(phone__icontains=search))
    if batch:
        students = students.filter(batch=batch)
    if track:
        students = students.filter(enrollments__track_id=track)

    last_seen = dict(LabProgress.objects.filter(user__student_profile__in=students)
                     .values('user').annotate(t=Max('updated_at')).values_list('user', 't'))
    last_answer = dict(QuizAnswer.objects.filter(user__student_profile__in=students)
                       .values('user').annotate(t=Max('updated_at')).values_list('user', 't'))
    rows = []
    for s in students:
        stamps = [t for t in (last_seen.get(s.user_id), last_answer.get(s.user_id)) if t]
        rows.append({'student': s, 'tracks': [e.track for e in s.enrollments.all()],
                     'last_active': max(stamps) if stamps else None})
    return render(request, 'academy/manage/students.html', {
        'rows': rows, 'search': search, 'batch': batch, 'track': track,
        'batches': Student.objects.exclude(batch='').values_list('batch', flat=True)
                   .distinct().order_by('batch'),
        'tracks': Track.objects.all(),
    })


@admin_required
def manage_student_new(request):
    form = NewStudentForm(request.POST or None,
                          initial={'tracks': Track.objects.filter(pk='pl900')})
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        password = d['password'] or _new_password()
        with transaction.atomic():
            user = User.objects.create_user(username=d['username'], password=password,
                                            email=d['email'], first_name=d['first_name'],
                                            last_name=d['last_name'])
            student = Student.objects.create(user=user, phone=d['phone'], batch=d['batch'],
                                             notes=d['notes'], created_by=request.user)
            _sync_enrollments(student, d['tracks'])
        # Shown once, on the next page only.
        request.session['academy_new_password'] = {'student': str(student.pk), 'password': password}
        messages.success(request, f'Student "{student.name}" created.')
        return redirect('academy:manage_student_detail', pk=student.pk)
    return render(request, 'academy/manage/student_form.html', {'form': form, 'is_new': True})


@admin_required
def manage_student_edit(request, pk):
    student = get_object_or_404(Student.objects.select_related('user'), pk=pk)
    initial = {'first_name': student.user.first_name, 'last_name': student.user.last_name,
               'email': student.user.email, 'phone': student.phone, 'batch': student.batch,
               'notes': student.notes,
               'tracks': Track.objects.filter(enrollments__student=student)}
    form = StudentForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            u = student.user
            u.first_name, u.last_name, u.email = d['first_name'], d['last_name'], d['email']
            u.save(update_fields=['first_name', 'last_name', 'email'])
            student.phone, student.batch, student.notes = d['phone'], d['batch'], d['notes']
            student.save(update_fields=['phone', 'batch', 'notes'])
            _sync_enrollments(student, d['tracks'])
        messages.success(request, 'Student updated.')
        return redirect('academy:manage_student_detail', pk=student.pk)
    return render(request, 'academy/manage/student_form.html',
                  {'form': form, 'is_new': False, 'student': student})


@admin_required
def manage_student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related('user', 'last_lesson'), pk=pk)
    summaries = []
    for e in student.enrollments.select_related('track'):
        s = track_summary(student.user, e.track)
        s['enrolled_at'] = e.enrolled_at
        s['in_progress'] = sum(1 for x in s['statuses'].values() if x['status'] == IN_PROGRESS)
        s['cells'] = [{'lesson': l, **s['statuses'][l.id]} for l in s['lessons']]
        summaries.append(s)
    new_password = request.session.pop('academy_new_password', None)
    if new_password and new_password.get('student') != str(student.pk):
        new_password = None
    return render(request, 'academy/manage/student_detail.html', {
        'student': student, 'summaries': summaries,
        'perks': perks_mod.compute(student.user, [e.track for e in student.enrollments.select_related('track')]),
        'tests': TestAttempt.objects.filter(user=student.user).select_related('track')[:20],
        'new_password': new_password['password'] if new_password else None,
        'login_url': request.build_absolute_uri('/academy/login/'),
    })


@require_POST
@admin_required
def manage_student_password(request, pk):
    student = get_object_or_404(Student.objects.select_related('user'), pk=pk)
    password = _new_password()
    student.user.set_password(password)
    student.user.save(update_fields=['password'])
    request.session['academy_new_password'] = {'student': str(student.pk), 'password': password}
    messages.success(request, 'New password set. Share it with the student.')
    return redirect('academy:manage_student_detail', pk=student.pk)


@require_POST
@admin_required
def manage_student_unlock(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.unlock_all = not student.unlock_all
    student.save(update_fields=['unlock_all'])
    messages.success(request, f'{student.name}: ' + (
        'every course and lesson is now open.' if student.unlock_all
        else 'courses and lessons unlock in order again.'))
    return redirect('academy:manage_student_detail', pk=student.pk)


@require_POST
@admin_required
def manage_student_status(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.status = 'inactive' if student.status == 'active' else 'active'
    student.save(update_fields=['status'])
    messages.success(request, f'{student.name} is now {student.get_status_display().lower()}. '
                              + ('They can no longer open the Academy.'
                                 if student.status == 'inactive' else 'They can sign in again.'))
    return redirect('academy:manage_student_detail', pk=student.pk)


# --- Progress matrix -------------------------------------------------------------

@admin_required
def manage_progress(request):
    tracks = Track.objects.all()
    track = tracks.filter(pk=request.GET.get('track') or 'pl900').first() or tracks.first()
    batch = request.GET.get('batch', '')
    if track is None:
        messages.error(request, 'No course content yet. Run "python manage.py import_labs".')
        return redirect('academy:manage_home')

    students = (Student.objects.filter(enrollments__track=track).select_related('user')
                .order_by('user__first_name', 'user__username'))
    if batch:
        students = students.filter(batch=batch)
    lessons = list(Lesson.objects.filter(track=track).select_related('domain'))

    rows = []
    for s in students:
        statuses = lesson_statuses(s.user, lessons)
        tests = list(TestAttempt.objects.filter(user=s.user, track=track, submitted_at__isnull=False))
        done = sum(1 for x in statuses.values() if x['status'] == DONE)
        rows.append({
            'student': s, 'cells': [statuses[l.id]['status'] for l in lessons],
            'done': done, 'percent': round(done / len(lessons) * 100) if lessons else 0,
            'best': max((t.score for t in tests), default=None), 'tests': len(tests),
        })

    # Quiz accuracy per lesson across these students: first-try-right is not
    # stored, so this is "ever correct / answered".
    user_ids = [s.user_id for s in students]
    acc = {}
    for lid, answered, right in (QuizAnswer.objects
                                 .filter(user_id__in=user_ids, question__lesson__in=lessons,
                                         question__source='lesson')
                                 .values_list('question__lesson').annotate(
                                     n=Count('id'), r=Count('id', filter=Q(ever_correct=True)))):
        acc[lid] = round(right / answered * 100) if answered else None
    lesson_cols = [{'lesson': l, 'accuracy': acc.get(l.id)} for l in lessons]

    if request.GET.get('export') == 'csv':
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = (f'attachment; filename="academy-{track.pk}'
                                       f'{"-" + batch if batch else ""}-progress.csv"')
        w = csv.writer(resp)
        w.writerow(['Student', 'Username', 'Batch', 'Lessons done', 'Percent',
                    'Best test score', 'Tests taken'] + [f'{l.num} {l.title}' for l in lessons])
        for r in rows:
            s = r['student']
            w.writerow([s.name, s.user.username, s.batch, r['done'], r['percent'],
                        r['best'] if r['best'] is not None else '', r['tests']]
                       + [c.replace('_', ' ') for c in r['cells']])
        return resp

    return render(request, 'academy/manage/progress.html', {
        'tracks': tracks, 'track': track, 'batch': batch, 'rows': rows,
        'lesson_cols': lesson_cols,
        'batches': Student.objects.exclude(batch='').values_list('batch', flat=True)
                   .distinct().order_by('batch'),
    })
