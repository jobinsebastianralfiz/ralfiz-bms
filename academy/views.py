"""Student-facing Academy portal at /academy/."""
import io
import json
import random
import zipfile

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .access import is_admin, learner_required, visible_tracks
from .models import (
    ExerciseFile, LabProgress, Lesson, Question, QuizAnswer, Student, TestAttempt, Track,
)
from .progress import DONE, lesson_statuses, track_summary
from .sanitize import headings

FILE_BADGES = {'csv': 'CSV', 'json': 'JSON', 'md': 'DOC', 'txt': 'TXT', 'cs': 'C#', 'ts': 'TS',
               'tsx': 'TSX', 'js': 'JS', 'py': 'PY', 'yml': 'YAML', 'xml': 'XML',
               'csproj': 'PROJ', 'css': 'CSS'}


# --- Auth ------------------------------------------------------------------------

def academy_login(request):
    if request.user.is_authenticated:
        has_access = (Student.objects.filter(user=request.user, status='active').exists()
                      or is_admin(request.user))
        if has_access:
            return redirect('academy:home')

    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username', '').strip(),
                            password=request.POST.get('password', ''))
        if user is None:
            error = 'Invalid username or password.'
        elif not (Student.objects.filter(user=user, status='active').exists() or is_admin(user)):
            error = 'This account has no active Academy access. Ask your trainer.'
        else:
            login(request, user)
            nxt = request.GET.get('next', '')
            return redirect(nxt if nxt.startswith('/academy/') else 'academy:home')
    return render(request, 'academy/login.html', {'error': error})


def academy_logout(request):
    logout(request)
    return redirect('academy:login')


# --- Helpers ---------------------------------------------------------------------

def _track_or_404(request, track_id):
    track = visible_tracks(request).filter(pk=track_id).first()
    if track is None:
        raise Http404('Track not found or not enrolled.')
    return track


def _lesson_or_404(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('track', 'domain'), pk=lesson_id)
    _track_or_404(request, lesson.track_id)
    return lesson


def _file_rows(files):
    return [{
        'file': f, 'badge': FILE_BADGES.get(f.ext, f.ext.upper() or 'FILE'),
        'size': f'{f.size_bytes} B' if f.size_bytes < 1024 else f'{f.size_bytes / 1024:.1f} KB',
    } for f in files]


def _sidebar(request, track, current=None):
    """Domains with their lessons and status dots for the lesson sidebar."""
    lessons = list(Lesson.objects.filter(track=track).select_related('domain'))
    statuses = lesson_statuses(request.user, lessons)
    domains = []
    for lesson in lessons:
        if not domains or domains[-1]['domain'].pk != lesson.domain_id:
            domains.append({'domain': lesson.domain, 'lessons': []})
        domains[-1]['lessons'].append({'lesson': lesson, 'status': statuses[lesson.id]['status']})
    done = sum(1 for s in statuses.values() if s['status'] == DONE)
    return {'side_domains': domains, 'side_track': track, 'side_current': current,
            'side_done': done, 'side_total': len(lessons),
            'side_percent': round(done / len(lessons) * 100) if lessons else 0,
            'side_tracks': visible_tracks(request)}


def _json_body(request):
    try:
        return json.loads(request.body or b'{}')
    except ValueError:
        return None


# --- Dashboard -------------------------------------------------------------------

@learner_required
@never_cache
def home(request):
    tracks = list(visible_tracks(request))
    summaries = [track_summary(request.user, t) for t in tracks]
    enrolled_ids = {t.id for t in tracks}
    locked = Track.objects.filter(is_published=True).exclude(pk__in=enrolled_ids)

    done = sum(s['done'] for s in summaries)
    total = sum(s['total'] for s in summaries)
    answers = QuizAnswer.objects.filter(user=request.user, question__track_id__in=enrolled_ids)
    answered = answers.count()
    right = answers.filter(ever_correct=True).count()
    tests = (TestAttempt.objects.filter(user=request.user, submitted_at__isnull=False,
                                        track_id__in=enrolled_ids)
             .select_related('track')[:5])

    resume = None
    student = request.student
    if student and student.last_lesson_id and student.last_lesson.track_id in enrolled_ids:
        resume = student.last_lesson
    if resume is None:
        resume = next((s['next_lesson'] for s in summaries if s['started'] and s['done'] < s['total']),
                      summaries[0]['next_lesson'] if summaries else None)

    # Suggested path: PL-900, then AB-410 or PL-300, then AB-400.
    by_id = {t.id: t for t in Track.objects.filter(is_published=True)}
    pct = {s['track'].id: s['percent'] for s in summaries}
    path = [[{'track': by_id[tid], 'enrolled': tid in enrolled_ids, 'percent': pct.get(tid, 0)}
             for tid in step if tid in by_id]
            for step in (['pl900'], ['ab410', 'pl300'], ['ab400'])]

    return render(request, 'academy/home.html', {
        'path': [step for step in path if step],
        'summaries': summaries, 'locked': locked, 'resume': resume,
        'resume_status': (lesson_statuses(request.user, [resume])[resume.id]['status']
                          if resume else None),
        'stats': {'done': done, 'total': total, 'answered': answered, 'right': right,
                  'minutes_left': sum(l.minutes for s in summaries for l in s['lessons']
                                      if s['statuses'][l.id]['status'] != DONE),
                  'tracks': len(tracks),
                  'best': max((s['best_score'] for s in summaries if s['best_score'] is not None),
                              default=None)},
        'tests': tests,
        'enrolled_ids': enrolled_ids,
        'nav': 'home',
    })


# --- Track -----------------------------------------------------------------------

@learner_required
@never_cache
def track_detail(request, track_id):
    track = _track_or_404(request, track_id)
    summary = track_summary(request.user, track)
    domains = []
    for lesson in summary['lessons']:
        if not domains or domains[-1]['domain'].pk != lesson.domain_id:
            domains.append({'domain': lesson.domain, 'lessons': [], 'done': 0})
        domains[-1]['lessons'].append({'lesson': lesson, **summary['statuses'][lesson.id]})
        if summary['statuses'][lesson.id]['status'] == DONE:
            domains[-1]['done'] += 1
    for d in domains:
        d['percent'] = round(d['done'] / len(d['lessons']) * 100)
        d['minutes'] = sum(x['lesson'].minutes for x in d['lessons'])

    resume = summary['next_lesson']
    student = request.student
    if student and student.last_lesson_id and student.last_lesson.track_id == track.id:
        resume = student.last_lesson
    data_files = ExerciseFile.objects.filter(pk__in=track.data_file_ids)
    data_files = sorted(data_files, key=lambda f: track.data_file_ids.index(f.pk))

    return render(request, 'academy/track.html', {
        'track': track, 'summary': summary, 'domains': domains, 'resume': resume,
        'data_files': _file_rows(data_files),
        'tests': TestAttempt.objects.filter(user=request.user, track=track,
                                            submitted_at__isnull=False)[:5],
        'pool_size': Question.objects.filter(track=track, is_active=True).count(),
        **_sidebar(request, track, current='overview'),
    })


# --- Lesson ----------------------------------------------------------------------

@learner_required
@never_cache
def lesson_detail(request, lesson_id):
    lesson = _lesson_or_404(request, lesson_id)
    track = lesson.track
    if request.student and not request.is_preview and request.student.last_lesson_id != lesson.id:
        Student.objects.filter(pk=request.student.pk).update(last_lesson=lesson)

    siblings = list(Lesson.objects.filter(track=track).only('id', 'num', 'title'))
    idx = next(i for i, l in enumerate(siblings) if l.id == lesson.id)
    prev_lesson = siblings[idx - 1] if idx > 0 else None
    next_lesson = siblings[idx + 1] if idx + 1 < len(siblings) else None

    status = lesson_statuses(request.user, [lesson])[lesson.id]
    ticks = (LabProgress.objects.filter(user=request.user, lesson=lesson)
             .values_list('ticked_steps', flat=True).first()) or []
    questions = list(Question.objects.filter(lesson=lesson, source='lesson', is_active=True))
    answers = {a.question_id: a for a in QuizAnswer.objects.filter(user=request.user,
                                                                   question__in=questions)}
    quiz = []
    for q in questions:
        a = answers.get(q.id)
        # The answer key only reaches the page for a question already answered.
        quiz.append({'q': q, 'options': list(enumerate(q.options)),
                     'chosen': a.last_choice if a else None,
                     'correct_index': q.answer if a else None,
                     'explanation': q.explanation if a else ''})

    files = [lf.file for lf in lesson.lesson_files.select_related('file')]
    words = len(lesson.content_html.replace('<', ' <').split())
    tab = request.GET.get('tab', 'learn')
    return render(request, 'academy/lesson.html', {
        'lesson': lesson, 'track': track, 'status': status,
        'toc': headings(lesson.content_html),
        'read_minutes': max(1, round(words / 200)),
        'ticks': [i for i in ticks if isinstance(i, int)],
        'quiz': quiz, 'files': _file_rows(files),
        'prev_lesson': prev_lesson, 'next_lesson': next_lesson,
        'tab': tab if tab in ('learn', 'lab', 'quiz') else 'learn',
        **_sidebar(request, track, current=lesson.id),
    })


@require_POST
@learner_required
def api_lab(request, lesson_id):
    lesson = _lesson_or_404(request, lesson_id)
    data = _json_body(request)
    if data is None or not isinstance(data.get('ticked_steps'), list):
        return HttpResponseBadRequest('ticked_steps must be a list')
    steps = sorted({i for i in data['ticked_steps']
                    if isinstance(i, int) and 0 <= i < len(lesson.lab_steps)})
    LabProgress.objects.update_or_create(user=request.user, lesson=lesson,
                                         defaults={'ticked_steps': steps})
    return JsonResponse({'ticked_steps': steps,
                         'status': lesson_statuses(request.user, [lesson])[lesson.id]})


@require_POST
@learner_required
def api_answer(request, question_id):
    question = get_object_or_404(Question, pk=question_id, is_active=True)
    _track_or_404(request, question.track_id)
    data = _json_body(request)
    choice = data.get('choice') if data else None
    if not isinstance(choice, int) or not 0 <= choice < len(question.options):
        return HttpResponseBadRequest('choice must be an option index')
    correct = choice == question.answer
    ans, _ = QuizAnswer.objects.get_or_create(user=request.user, question=question,
                                              defaults={'last_choice': choice})
    ans.last_choice = choice
    ans.attempts += 1
    ans.ever_correct = ans.ever_correct or correct
    ans.save()
    payload = {'correct': correct, 'answer': question.answer, 'explanation': question.explanation}
    if question.lesson_id:
        lesson = Lesson.objects.get(pk=question.lesson_id)
        payload['status'] = lesson_statuses(request.user, [lesson])[lesson.id]
    return JsonResponse(payload)


# --- Exercise files --------------------------------------------------------------

def _file_allowed(request, f):
    return visible_tracks(request).filter(pk__in=f.track_ids).exists()


def _attachment(data, filename, content_type):
    resp = HttpResponse(data, content_type=content_type)
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp


@learner_required
def file_download(request, file_id):
    f = get_object_or_404(ExerciseFile, pk=file_id)
    if not _file_allowed(request, f):
        raise Http404
    # Always a download, never rendered: some files are code.
    return _attachment(f.content.encode('utf-8'), f.filename, 'application/octet-stream')


def _zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, text in entries:
            z.writestr(name, text)
    return buf.getvalue()


def _lab_md(lesson):
    lines = [f'# {lesson.track.code} · {lesson.num} {lesson.title}', '', '## Steps']
    lines += [f'{i}. {s}' for i, s in enumerate(lesson.lab_steps, 1)]
    if lesson.lab_check:
        lines += ['', '## Check your work'] + [f'- [ ] {c}' for c in lesson.lab_check]
    return '\n'.join(lines) + '\n'


@learner_required
def lesson_zip(request, lesson_id):
    lesson = _lesson_or_404(request, lesson_id)
    files = [lf.file for lf in lesson.lesson_files.select_related('file')]
    data = _zip([(f.zip_path, f.content) for f in files] + [('LAB.md', _lab_md(lesson))])
    name = f'{lesson.track.code.lower()}-{lesson.num.lower().replace(".", "-")}-exercise-files.zip'
    return _attachment(data, name, 'application/zip')


@learner_required
def track_data_zip(request, track_id):
    track = _track_or_404(request, track_id)
    files = ExerciseFile.objects.filter(pk__in=track.data_file_ids)
    data = _zip([(f.zip_path, f.content) for f in files])
    return _attachment(data, f'{track.code.lower()}-course-data.zip', 'application/zip')


# --- Practice tests --------------------------------------------------------------

def _grade(attempt, questions):
    correct = sum(1 for i, q in enumerate(questions)
                  if q is not None and attempt.answers.get(str(i)) == q.answer)
    return correct, round(correct / len(questions) * 1000) if questions else 0


def _attempt_questions(attempt):
    by_id = Question.objects.select_related('lesson').in_bulk(attempt.question_ids)
    return [by_id.get(qid) for qid in attempt.question_ids]


@learner_required
@never_cache
def test_start(request, track_id):
    track = _track_or_404(request, track_id)
    pool = list(Question.objects.filter(track=track, is_active=True).values_list('id', flat=True))
    if request.method == 'POST':
        size = 50 if request.POST.get('size') == '50' and len(pool) >= 50 else 30
        chosen = random.sample(pool, min(size, len(pool)))
        attempt = TestAttempt.objects.create(user=request.user, track=track, question_ids=chosen)
        return redirect('academy:test_take', attempt_id=attempt.id)

    history = TestAttempt.objects.filter(user=request.user, track=track)
    return render(request, 'academy/test_start.html', {
        'track': track, 'pool_size': len(pool), 'history': history[:20],
        'open_attempt': history.filter(submitted_at__isnull=True).first(),
        **_sidebar(request, track, current='test'),
    })


def _own_attempt(request, attempt_id):
    attempt = get_object_or_404(TestAttempt.objects.select_related('track'),
                                pk=attempt_id, user=request.user)
    _track_or_404(request, attempt.track_id)
    return attempt


@learner_required
@never_cache
def test_take(request, attempt_id):
    attempt = _own_attempt(request, attempt_id)
    if attempt.submitted_at:
        return redirect('academy:test_result', attempt_id=attempt.id)
    questions = _attempt_questions(attempt)
    items = [{'i': i, 'q': q, 'options': list(enumerate(q.options)),
              'chosen': attempt.answers.get(str(i))}
             for i, q in enumerate(questions) if q is not None]
    return render(request, 'academy/test_take.html', {
        'attempt': attempt, 'track': attempt.track, 'items': items,
        'answered': len(attempt.answers),
        **_sidebar(request, attempt.track, current='test'),
    })


@require_POST
@learner_required
def api_test_save(request, attempt_id):
    attempt = _own_attempt(request, attempt_id)
    if attempt.submitted_at:
        return JsonResponse({'detail': 'Already submitted.'}, status=409)
    data = _json_body(request)
    if data is None or not isinstance(data.get('answers'), dict):
        return HttpResponseBadRequest('answers must be an object')
    clean = {}
    for k, v in data['answers'].items():
        if str(k).isdigit() and int(k) < attempt.size and isinstance(v, int) and 0 <= v <= 3:
            clean[str(int(k))] = v
    attempt.answers = clean
    attempt.save(update_fields=['answers'])
    return JsonResponse({'answered': len(clean)})


@require_POST
@learner_required
def test_submit(request, attempt_id):
    attempt = _own_attempt(request, attempt_id)
    if not attempt.submitted_at:
        # The form carries the final answers too, in case the last autosave was lost.
        for key, value in request.POST.items():
            if key.startswith('q') and key[1:].isdigit() and value.isdigit():
                if int(key[1:]) < attempt.size and 0 <= int(value) <= 3:
                    attempt.answers[str(int(key[1:]))] = int(value)
        attempt.correct_count, attempt.score = _grade(attempt, _attempt_questions(attempt))
        attempt.submitted_at = timezone.now()
        attempt.save()
    return redirect('academy:test_result', attempt_id=attempt.id)


@learner_required
@never_cache
def test_result(request, attempt_id):
    attempt = _own_attempt(request, attempt_id)
    if not attempt.submitted_at:
        return redirect('academy:test_take', attempt_id=attempt.id)
    questions = _attempt_questions(attempt)
    items = []
    for i, q in enumerate(questions):
        if q is None:
            continue
        chosen = attempt.answers.get(str(i))
        items.append({'i': i, 'q': q, 'options': list(enumerate(q.options)), 'chosen': chosen,
                      'correct': chosen == q.answer})
    missed_lessons = {}
    for it in items:
        if not it['correct'] and it['q'].lesson:
            missed_lessons.setdefault(it['q'].lesson.id, {'lesson': it['q'].lesson, 'n': 0})['n'] += 1
    return render(request, 'academy/test_result.html', {
        'attempt': attempt, 'track': attempt.track, 'items': items,
        'missed_lessons': sorted(missed_lessons.values(), key=lambda m: -m['n'])[:6],
        'pass_mark': TestAttempt.PASS_MARK,
        **_sidebar(request, attempt.track, current='test'),
    })


# --- Account ---------------------------------------------------------------------

@learner_required
def profile(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed.')
        return redirect('academy:profile')
    enrollments = (request.student.enrollments.select_related('track')
                   if request.student else [])
    return render(request, 'academy/profile.html', {
        'form': form, 'enrollments': enrollments, 'nav': 'profile',
    })
