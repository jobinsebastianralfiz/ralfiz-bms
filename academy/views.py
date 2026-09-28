"""Student-facing Academy portal at /academy/."""
import io
import json
import random
import re
import zipfile
from html import unescape

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .access import is_admin, learner_required, visible_tracks
from .models import (
    ExerciseFile, LabProgress, Lesson, Question, QuizAnswer, Student, TestAttempt, Track,
)
from . import perks as perks_mod
from .locks import course_lock, course_locks, lesson_lock, locked_lessons, locks_apply
from .progress import DONE, lesson_statuses, track_summary
from .public_views import _contact
from .sanitize import headings

REMEMBER_ME_SECONDS = 30 * 24 * 60 * 60
PATH_ORDER = ['pl900', 'ab410', 'pl300', 'ab400', 'flutter']
PATH_LINES = {
    'pl900': 'Start with the basics and understand the core services.',
    'ab410': 'Build real business apps with AI and Dataverse.',
    'pl300': 'Analyse data and build interactive reports.',
    'ab400': 'Extend the platform with custom code and integrations.',
    'flutter': 'Build and publish mobile apps with Flutter and Dart.',
}
FILE_BADGES = {'csv': 'CSV', 'json': 'JSON', 'md': 'DOC', 'txt': 'TXT', 'cs': 'C#', 'ts': 'TS',
               'tsx': 'TSX', 'js': 'JS', 'py': 'PY', 'yml': 'YAML', 'xml': 'XML',
               'csproj': 'PROJ', 'css': 'CSS', 'dart': 'DART', 'yaml': 'YAML'}


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
            # Unticked: the session ends when the browser closes.
            request.session.set_expiry(REMEMBER_ME_SECONDS if request.POST.get('remember') else 0)
            nxt = request.GET.get('next', '')
            return redirect(nxt if nxt.startswith('/academy/') else 'academy:home')
    return render(request, 'academy/login.html', {
        'error': error,
        'has_flutter': Track.objects.filter(pk='flutter', is_published=True).exists(),
    })


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
    """The course outline: domains (collapsible) with lessons and status dots."""
    lessons = list(Lesson.objects.filter(track=track).select_related('domain'))
    statuses = lesson_statuses(request.user, lessons)
    locked = locked_lessons(request, lessons, statuses, course_lock(request, track))
    domains = []
    for lesson in lessons:
        if not domains or domains[-1]['domain'].pk != lesson.domain_id:
            domains.append({'domain': lesson.domain, 'index': len(domains), 'lessons': [],
                            'done': 0, 'open': False})
        st = statuses[lesson.id]['status']
        domains[-1]['lessons'].append({'lesson': lesson, 'status': st,
                                       'locked': locked.get(lesson.id)})
        domains[-1]['done'] += st == DONE
        if lesson.id == current:
            domains[-1]['open'] = True
    if not any(d['open'] for d in domains):
        # Off a lesson page: open the first skill area that still has work.
        first = next((d for d in domains if d['done'] < len(d['lessons'])), None)
        if first:
            first['open'] = True
    done = sum(1 for s in statuses.values() if s['status'] == DONE)
    return {'side_domains': domains, 'side_track': track, 'side_current': current,
            'side_done': done, 'side_total': len(lessons),
            'side_percent': round(done / len(lessons) * 100) if lessons else 0,
            'side_tracks': visible_tracks(request),
            'nav': 'assessments' if current == 'test' else 'courses'}


def _lead(summary_html, limit=190):
    """A one- or two-sentence plain-text intro from a lesson summary."""
    text = re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', summary_html))).strip()
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    out = ''
    for sentence in sentences:
        if out and len(out) + len(sentence) + 1 > limit:
            break
        out = f'{out} {sentence}'.strip()
    return out if len(out) <= limit + 60 else out[:limit].rsplit(' ', 1)[0] + '…'


def _split_step(step):
    """Split "Do this. More detail." into a bold title and a detail line."""
    m = re.match(r'^(.{8,}?[a-z0-9)\]"\u2019])[.:]\s+([A-Z].+)$', step)
    if m:
        return m.group(1), m.group(2)
    return step.rstrip('.'), ''


def _lesson_pct(st):
    """Share of a lesson's work done: lab steps and quiz questions together."""
    total = st['lab_total'] + st['quiz_total']
    return round((st['lab_ticked'] + st['quiz_right']) / total * 100) if total else 0


def _json_body(request):
    try:
        return json.loads(request.body or b'{}')
    except ValueError:
        return None


# --- Dashboard -------------------------------------------------------------------

def landing(request):
    """/academy/: visitors see the public course catalog, signed-in learners their dashboard."""
    if not request.user.is_authenticated:
        return redirect('academy:catalog')
    return home(request)


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

    # Suggested learning path, one step per track in the recommended order.
    by_id = {t.id: t for t in Track.objects.filter(is_published=True)}
    by_summary = {s['track'].id: s for s in summaries}
    path = []
    for tid in PATH_ORDER:
        if tid not in by_id:
            continue
        s = by_summary.get(tid)
        state = ('locked' if s is None else 'completed' if s['completed'] else
                 'in_progress' if s['started'] else 'not_started')
        path.append({'track': by_id[tid], 'state': state, 'line': PATH_LINES.get(tid, by_id[tid].blurb),
                     'percent': s['percent'] if s else 0})

    # Practice tests table: a 30-question test and, where the pool allows, a
    # 50-question mock for every enrolled course.
    attempts = list(TestAttempt.objects.filter(user=request.user, track_id__in=enrolled_ids))
    pools = dict(Question.objects.filter(track_id__in=enrolled_ids, is_active=True)
                 .values_list('track').annotate(n=Count('id')))
    test_rows = []
    for s in summaries:
        tid = s['track'].id
        for size, label in ((30, 'Practice test'), (50, 'Full mock test')):
            if size == 50 and pools.get(tid, 0) < 50:
                continue
            mine = [a for a in attempts if a.track_id == tid and a.size == size]
            finished = [a for a in mine if a.submitted_at]
            test_rows.append({
                'track': s['track'], 'size': size, 'label': label,
                'best': max((a.score for a in finished), default=None),
                'last': max(finished, key=lambda a: a.submitted_at) if finished else None,
                'open': next((a for a in mine if not a.submitted_at), None),
            })

    for s in summaries:
        s['state'] = ('completed' if s['total'] and s['done'] == s['total'] else
                      'in_progress' if s['started'] else 'not_started')
    locks = course_locks(request, summaries)
    for s in summaries:
        s['lock'] = locks[s['track'].id]
    for p in path:
        p['lock'] = locks.get(p['track'].id)
    for r in test_rows:
        r['lock'] = locks.get(r['track'].id)
    perks = perks_mod.for_request(request)
    counts = {k: sum(1 for s in summaries if s['state'] == k)
              for k in ('in_progress', 'not_started', 'completed')}
    minutes_total = sum(l.minutes for s in summaries for l in s['lessons'])
    minutes_left = sum(l.minutes for s in summaries for l in s['lessons']
                       if s['statuses'][l.id]['status'] != DONE)
    best = max((s['best_score'] for s in summaries if s['best_score'] is not None), default=None)

    return render(request, 'academy/home.html', {
        'counts': counts, 'any_started': any(s['started'] for s in summaries),
        'path': path, 'test_rows': test_rows,
        'summaries': summaries, 'locked': locked, 'resume': resume,
        'resume_status': (lesson_statuses(request.user, [resume])[resume.id]['status']
                          if resume else None),
        'stats': {'done': done, 'total': total, 'answered': answered, 'right': right,
                  'done_pct': round(done / total * 100) if total else 0,
                  'right_pct': round(right / answered * 100) if answered else 0,
                  'hours_left': round(minutes_left / 60),
                  'left_pct': round(minutes_left / minutes_total * 100) if minutes_total else 0,
                  'tracks': len(tracks), 'best': best,
                  'best_pct': round(best / 10) if best is not None else 0},
        'tests': tests, 'perks': perks,
        'new_badges': perks_mod.announce_new(request, perks),
        'enrolled_ids': enrolled_ids,
        'nav': 'home',
    })


def _summaries(request):
    tracks = list(visible_tracks(request))
    summaries = [track_summary(request.user, t) for t in tracks]
    for s in summaries:
        s['state'] = ('completed' if s['total'] and s['done'] == s['total'] else
                      'in_progress' if s['started'] else 'not_started')
    return tracks, summaries


@learner_required
@never_cache
def courses(request):
    tracks, summaries = _summaries(request)
    counts = {k: sum(1 for s in summaries if s['state'] == k)
              for k in ('in_progress', 'not_started', 'completed')}
    locked = Track.objects.filter(is_published=True).exclude(pk__in=[t.id for t in tracks])
    locks = course_locks(request, summaries)
    for s in summaries:
        s['lock'] = locks[s['track'].id]
    return render(request, 'academy/courses.html', {
        'summaries': summaries, 'counts': counts, 'locked': locked, 'nav': 'courses',
    })


@learner_required
@never_cache
def assessments(request):
    tracks, summaries = _summaries(request)
    attempts = (TestAttempt.objects.filter(user=request.user, track__in=tracks)
                .select_related('track'))
    rows = []
    locks = course_locks(request, summaries)
    for s in summaries:
        s['lock'] = locks[s['track'].id]
        mine = [a for a in attempts if a.track_id == s['track'].id]
        done = [a for a in mine if a.submitted_at]
        rows.append({**s, 'attempts': len(done),
                     'open_attempt': next((a for a in mine if not a.submitted_at), None),
                     'last': done[0] if done else None,
                     'passes': sum(1 for a in done if a.passed),
                     'pool': Question.objects.filter(track=s['track'], is_active=True).count()})
    return render(request, 'academy/assessments.html', {
        'rows': rows, 'history': [a for a in attempts if a.submitted_at][:30],
        'pass_mark': TestAttempt.PASS_MARK, 'nav': 'assessments',
    })


@learner_required
@never_cache
def certificates(request):
    tracks, summaries = _summaries(request)
    for s in summaries:
        s['test_ok'] = s['best_score'] is not None and s['best_score'] >= TestAttempt.PASS_MARK
        s['lessons_ok'] = s['total'] > 0 and s['done'] == s['total']
    return render(request, 'academy/certificates.html', {
        'summaries': summaries, 'pass_mark': TestAttempt.PASS_MARK, 'nav': 'certificates',
    })


# --- Track -----------------------------------------------------------------------

@learner_required
@never_cache
def track_detail(request, track_id):
    track = _track_or_404(request, track_id)
    summary = track_summary(request.user, track)
    lock = course_lock(request, track)
    locked = locked_lessons(request, summary['lessons'], summary['statuses'], lock)
    domains = []
    for lesson in summary['lessons']:
        if not domains or domains[-1]['domain'].pk != lesson.domain_id:
            domains.append({'domain': lesson.domain, 'lessons': [], 'done': 0})
        domains[-1]['lessons'].append({'lesson': lesson, 'locked': locked.get(lesson.id),
                                       **summary['statuses'][lesson.id]})
        if summary['statuses'][lesson.id]['status'] == DONE:
            domains[-1]['done'] += 1
    open_left = 2
    for i, d in enumerate(domains):
        d['index'] = i
        d['percent'] = round(d['done'] / len(d['lessons']) * 100)
        d['minutes'] = sum(x['lesson'].minutes for x in d['lessons'])
        # Open the first two skill areas that still have work in them.
        d['open'] = d['done'] < len(d['lessons']) and open_left > 0
        open_left -= d['open']
    fact_icons = [('fa-trophy', 'amber'), ('fa-layer-group', 'violet'),
                  ('fa-calendar-days', 'blue'), ('fa-clock', 'teal')]
    facts = [{'value': f[0], 'label': f[1], 'icon': fact_icons[i % 4][0], 'tone': fact_icons[i % 4][1]}
             for i, f in enumerate(track.facts)]

    resume = summary['next_lesson']
    student = request.student
    if student and student.last_lesson_id and student.last_lesson.track_id == track.id:
        resume = student.last_lesson
    data_files = ExerciseFile.objects.filter(pk__in=track.data_file_ids)
    data_files = sorted(data_files, key=lambda f: track.data_file_ids.index(f.pk))

    return render(request, 'academy/track.html', {
        'track': track, 'summary': summary, 'domains': domains,
        'resume': None if lock else resume, 'course_lock': lock,
        'facts': facts,
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
    reason = lesson_lock(request, lesson)
    if reason:
        messages.info(request, f'{lesson.num} {lesson.title} is locked. {reason}')
        return redirect('academy:track', track_id=track.id)
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
    next_status = (lesson_statuses(request.user, [Lesson.objects.get(pk=next_lesson.pk)])[next_lesson.pk]
                   if next_lesson else None)
    if next_lesson:
        next_lesson = Lesson.objects.get(pk=next_lesson.pk)
    tab = request.GET.get('tab', 'learn')
    return render(request, 'academy/lesson.html', {
        'lesson': lesson, 'track': track, 'status': status,
        'toc': headings(lesson.content_html),
        'read_minutes': max(1, round(words / 200)),
        'ticks': [i for i in ticks if isinstance(i, int)],
        'steps': [{'i': i, 'title': t, 'detail': d}
                  for i, (t, d) in enumerate(_split_step(x) for x in lesson.lab_steps)],
        'lead': _lead(lesson.summary_html),
        'files_kb': round(sum(f.size_bytes for f in files) / 1024, 1),
        'next_status': next_status,
        'next_locked': bool(next_lesson and locks_apply(request) and status['status'] != DONE
                            and next_status['status'] == 'not_started'),
        'lab_pct': round(status['lab_ticked'] / status['lab_total'] * 100) if status['lab_total'] else 100,
        'lesson_pct': _lesson_pct(status),
        'quiz': quiz, 'files': _file_rows(files),
        'prev_lesson': prev_lesson, 'next_lesson': next_lesson,
        'tab': tab if tab in ('learn', 'lab', 'quiz') else 'learn',
        'contact': _contact(),
        'new_badges': perks_mod.announce_new(request, perks_mod.for_request(request)),
        **_sidebar(request, track, current=lesson.id),
    })


@require_POST
@learner_required
def api_lab(request, lesson_id):
    lesson = _lesson_or_404(request, lesson_id)
    reason = lesson_lock(request, lesson)
    if reason:
        return JsonResponse({'detail': reason}, status=403)
    data = _json_body(request)
    if data is None or not isinstance(data.get('ticked_steps'), list):
        return HttpResponseBadRequest('ticked_steps must be a list')
    steps = sorted({i for i in data['ticked_steps']
                    if isinstance(i, int) and 0 <= i < len(lesson.lab_steps)})
    before = perks_mod.for_request(request)['xp']
    LabProgress.objects.update_or_create(user=request.user, lesson=lesson,
                                         defaults={'ticked_steps': steps})
    return JsonResponse({'ticked_steps': steps,
                         'status': lesson_statuses(request.user, [lesson])[lesson.id],
                         'perks': perks_mod.event_payload(request, before)})


@require_POST
@learner_required
def api_answer(request, question_id):
    question = get_object_or_404(Question, pk=question_id, is_active=True)
    _track_or_404(request, question.track_id)
    if question.lesson_id:
        reason = lesson_lock(request, Lesson.objects.select_related('track').get(pk=question.lesson_id))
        if reason:
            return JsonResponse({'detail': reason}, status=403)
    data = _json_body(request)
    choice = data.get('choice') if data else None
    if not isinstance(choice, int) or not 0 <= choice < len(question.options):
        return HttpResponseBadRequest('choice must be an option index')
    correct = choice == question.answer
    before = perks_mod.for_request(request)['xp']
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
    payload['perks'] = perks_mod.event_payload(request, before)
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
    if lesson_lock(request, lesson):
        raise Http404
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
    reason = course_lock(request, track)
    if reason:
        messages.info(request, f'The {track.code} practice test is locked. {reason}')
        return redirect('academy:track', track_id=track.id)
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
        perks_mod.record_activity(request.user)
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
        'new_badges': perks_mod.announce_new(request, perks_mod.for_request(request)),
        **_sidebar(request, attempt.track, current='test'),
    })


# --- Account ---------------------------------------------------------------------

class ProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=False)


@learner_required
def profile(request):
    user, student = request.user, request.student
    action = request.POST.get('action') if request.method == 'POST' else None
    pw_form = PasswordChangeForm(user, request.POST if action == 'password' else None)
    info_form = ProfileForm(request.POST if action == 'info' else None, initial={
        'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email,
        'phone': student.phone if student else '',
    })
    if action == 'password' and pw_form.is_valid():
        update_session_auth_hash(request, pw_form.save())
        messages.success(request, 'Password changed.')
        return redirect('academy:profile')
    if action == 'info' and info_form.is_valid():
        d = info_form.cleaned_data
        user.first_name, user.last_name, user.email = d['first_name'], d['last_name'], d['email']
        user.save(update_fields=['first_name', 'last_name', 'email'])
        if student:
            student.phone = d['phone']
            student.save(update_fields=['phone'])
        messages.success(request, 'Profile updated.')
        return redirect('academy:profile')

    enrolled = {e.track_id: e.enrolled_at for e in student.enrollments.all()} if student else {}
    courses = []
    for t in visible_tracks(request):
        s = track_summary(user, t)
        s['enrolled_at'] = enrolled.get(t.id)
        courses.append(s)
    return render(request, 'academy/profile.html', {
        'pw_form': pw_form, 'info_form': info_form, 'courses': courses,
        'perks': perks_mod.for_request(request),
        'edit_open': action == 'info', 'nav': 'profile',
    })
