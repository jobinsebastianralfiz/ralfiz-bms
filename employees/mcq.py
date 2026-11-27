"""MCQ tests for interns: read HR's JSON upload, give the test, mark it.

Upload format (one file = one test)::

    {
      "title": "Python Basics - Test 1",
      "description": "Read each question carefully.",
      "duration_minutes": 30,
      "questions": [
        {
          "question": "Which keyword defines a function in Python?",
          "options": ["func", "def", "function", "lambda"],
          "answer": "B",
          "marks": 1,
          "explanation": "Functions are defined with def."
        }
      ]
    }

``answer`` may be a letter ("B"), the option number (2, counted from 1) or the
exact option text. ``marks`` (default 1) and ``explanation`` are optional. A
bare list of questions is also accepted; the title then comes from the form.

Written questions are marked by HR::

    {"type": "code", "question": "Write is_prime(n).", "language": "python",
     "starter": "def is_prime(n):\n    pass", "answer": "model solution", "marks": 10}
    {"type": "text", "question": "Explain a REST API.", "answer": "key points", "marks": 5}

``"proctored": true`` at the top turns on webcam + fullscreen + lock on leaving;
``"max_violations"`` (default 1) is how many times leaving locks the test.
"""
import json
import random
import string
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

LETTERS = string.ascii_uppercase
MAX_QUESTIONS = 300
MAX_ANSWER_CHARS = 20000
QUESTION_TYPES = ('mcq', 'code', 'text')
LANGUAGES = ('python', 'javascript', 'java', 'c', 'cpp', 'php', 'dart', 'sql', 'html', 'other')
# Seconds allowed after the timer ends for a slow network to land the submit.
GRACE_SECONDS = 120

SAMPLE = {
    'title': 'Python Basics - Test 1',
    'description': 'Answer every question. Each question has one correct option.',
    'duration_minutes': 20,
    'questions': [
        {
            'question': 'Which keyword defines a function in Python?',
            'options': ['func', 'def', 'function', 'lambda'],
            'answer': 'B',
            'marks': 1,
            'explanation': 'Functions are defined with def; lambda makes a small anonymous function.',
        },
        {
            'question': 'What does len([1, 2, 3]) return?',
            'options': ['2', '3', '4', 'An error'],
            'answer': 2,
            'marks': 1,
        },
        {
            'question': 'Which of these is an immutable type?',
            'options': ['list', 'dict', 'tuple', 'set'],
            'answer': 'tuple',
            'marks': 2,
            'explanation': 'Tuples cannot be changed after they are made.',
        },
        {
            'type': 'code',
            'question': 'Write a function is_prime(n) that returns True if n is a prime number, else False.',
            'language': 'python',
            'starter': 'def is_prime(n):\n    # your code here\n    pass\n\nprint(is_prime(7))',
            'answer': 'def is_prime(n):\n    if n < 2:\n        return False\n'
                      '    for i in range(2, int(n ** 0.5) + 1):\n        if n % i == 0:\n'
                      '            return False\n    return True',
            'marks': 5,
        },
        {
            'type': 'text',
            'question': 'In two or three lines, what is the difference between a list and a tuple?',
            'answer': 'A list can be changed (mutable); a tuple cannot. Tuples can be dict keys.',
            'marks': 2,
        },
    ],
}


class McqFormatError(ValueError):
    pass


def _first(d, *keys):
    for k in keys:
        if k in d and d[k] not in (None, ''):
            return d[k]
    return None


def _answer_index(raw, options, n):
    """Turn a letter, 1-based number or option text into a 0-based index."""
    if isinstance(raw, bool):
        raise McqFormatError(f'Question {n}: "answer" must be a letter, number or the option text.')
    if isinstance(raw, int) or (isinstance(raw, float) and raw.is_integer()):
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return idx
        raise McqFormatError(f'Question {n}: answer {int(raw)} is not one of the {len(options)} options '
                             f'(count from 1).')
    if isinstance(raw, str):
        text = raw.strip()
        if len(text) == 1 and text.upper() in LETTERS[:len(options)]:
            return LETTERS.index(text.upper())
        if text.isdigit():
            return _answer_index(int(text), options, n)
        for i, opt in enumerate(options):
            if opt.strip().lower() == text.lower():
                return i
        raise McqFormatError(f'Question {n}: answer "{text}" does not match any option.')
    raise McqFormatError(f'Question {n}: "answer" is missing.')


def parse_upload(raw_bytes):
    """Read an uploaded JSON file. Returns a dict with title, description,
    duration_minutes and a clean questions list, or raises McqFormatError."""
    try:
        data = json.loads(raw_bytes.decode('utf-8-sig'))
    except UnicodeDecodeError:
        raise McqFormatError('The file is not UTF-8 text. Save it as a .json text file.')
    except json.JSONDecodeError as e:
        raise McqFormatError(f'Not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}.')

    if isinstance(data, list):
        data = {'questions': data}
    if not isinstance(data, dict):
        raise McqFormatError('The file must hold a test object or a list of questions.')

    items = _first(data, 'questions', 'mcqs', 'items')
    if not isinstance(items, list) or not items:
        raise McqFormatError('No questions found. Put them in a "questions" list.')
    if len(items) > MAX_QUESTIONS:
        raise McqFormatError(f'Too many questions ({len(items)}); the limit is {MAX_QUESTIONS}.')

    questions = []
    for n, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise McqFormatError(f'Question {n} is not an object with "question" and "options".')
        text = _first(item, 'question', 'q', 'title')
        if not isinstance(text, str) or not text.strip():
            raise McqFormatError(f'Question {n} has no "question" text.')
        qtype = str(item.get('type') or 'mcq').strip().lower()
        qtype = {'programming': 'code', 'program': 'code', 'coding': 'code', 'written': 'text',
                 'descriptive': 'text', 'essay': 'text', 'short': 'text'}.get(qtype, qtype)
        if qtype not in QUESTION_TYPES:
            raise McqFormatError(f'Question {n}: type "{qtype}" is not mcq, code or text.')
        if qtype != 'mcq':
            questions.append(_written_question(item, text, qtype, n))
            continue
        options = _first(item, 'options', 'choices')
        if isinstance(options, dict):  # {"A": "...", "B": "..."}
            options = [options[k] for k in sorted(options)]
        if not isinstance(options, list) or len(options) < 2:
            raise McqFormatError(f'Question {n} needs an "options" list with at least 2 choices.')
        if len(options) > len(LETTERS):
            raise McqFormatError(f'Question {n} has too many options.')
        options = [str(o).strip() for o in options]
        if any(not o for o in options):
            raise McqFormatError(f'Question {n} has an empty option.')

        if 'answer_index' in item:
            idx = item['answer_index']
            if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(options):
                raise McqFormatError(f'Question {n}: "answer_index" must be 0 to {len(options) - 1}.')
        else:
            idx = _answer_index(_first(item, 'answer', 'correct', 'correct_answer'), options, n)

        marks = item.get('marks', 1)
        try:
            marks = float(marks)
        except (TypeError, ValueError):
            raise McqFormatError(f'Question {n}: "marks" must be a number.')
        if marks <= 0:
            raise McqFormatError(f'Question {n}: "marks" must be more than 0.')

        questions.append({
            'type': 'mcq',
            'question': text.strip(),
            'options': options,
            'answer': idx,
            'marks': int(marks) if marks.is_integer() else marks,
            'explanation': str(item.get('explanation') or '').strip(),
        })

    duration = _first(data, 'duration_minutes', 'duration', 'time_limit')
    try:
        duration = max(0, int(duration or 0))
    except (TypeError, ValueError):
        raise McqFormatError('"duration_minutes" must be a whole number.')

    try:
        max_violations = max(1, int(data.get('max_violations') or 1))
    except (TypeError, ValueError):
        raise McqFormatError('"max_violations" must be a whole number.')

    return {
        'title': str(_first(data, 'title', 'name') or '').strip()[:255],
        'description': str(_first(data, 'description', 'instructions') or '').strip(),
        'duration_minutes': duration,
        'proctored': bool(data.get('proctored', False)),
        'max_violations': max_violations,
        'questions': questions,
    }


def _marks(item, n):
    marks = item.get('marks', 1)
    try:
        marks = float(marks)
    except (TypeError, ValueError):
        raise McqFormatError(f'Question {n}: "marks" must be a number.')
    if marks <= 0:
        raise McqFormatError(f'Question {n}: "marks" must be more than 0.')
    return int(marks) if marks.is_integer() else marks


def _written_question(item, text, qtype, n):
    language = ''
    if qtype == 'code':
        language = str(item.get('language') or 'python').strip().lower()
        language = {'py': 'python', 'js': 'javascript', 'c++': 'cpp', 'flutter': 'dart'}.get(language, language)
        if language not in LANGUAGES:
            language = 'other'
    return {
        'type': qtype,
        'question': text.strip(),
        'language': language,
        'starter': str(item.get('starter') or item.get('starter_code') or ''),
        # Model answer / key points: shown to HR while marking, and to the
        # intern afterwards if the test shows answers.
        'answer': str(_first(item, 'answer', 'sample_answer', 'solution') or ''),
        'marks': _marks(item, n),
        'explanation': str(item.get('explanation') or '').strip(),
    }


def question_order(assessment):
    """The order this intern sees the questions in: shuffled once per intern
    (seeded by their assessment id) so a page reload keeps the same order."""
    count = assessment.mcq_test.question_count
    order = list(range(count))
    if assessment.mcq_test.shuffle_questions:
        random.Random(str(assessment.pk)).shuffle(order)
    return order


def deadline(assessment):
    """When the timer runs out, or None for an untimed test / not started."""
    minutes = assessment.mcq_test.duration_minutes
    if not minutes or not assessment.started_at:
        return None
    return assessment.started_at + timedelta(minutes=minutes)


def assign(test, employees, by=None, due_date=None):
    """Give the test to each intern who doesn't already have it. Returns the
    new InternAssessment rows."""
    from .models import InternAssessment, Notification
    from .utils import send_push_notification

    have = set(test.assessments.values_list('employee_id', flat=True))
    created = []
    for emp in employees:
        if emp.pk in have:
            continue
        a = InternAssessment.objects.create(
            employee=emp, mcq_test=test, title=test.title, description=test.description,
            date=timezone.localdate(), max_score=Decimal(str(test.total_marks)),
            due_date=due_date, created_by=by,
        )
        created.append(a)
        body = f'{test.question_count} questions'
        if test.duration_minutes:
            body += f' · {test.duration_minutes} min'
        if due_date:
            body += f' · take it by {due_date:%d %b}'
        Notification.objects.create(employee=emp, title=f'New test: {test.title}', body=body,
                                    notification_type='general',
                                    data={'type': 'assessment', 'assessment_id': str(a.pk)})
        try:
            send_push_notification(emp, f'New test: {test.title}', body,
                                   {'type': 'assessment', 'assessment_id': str(a.pk)})
        except Exception:  # push is best effort; the in-app notification is enough
            pass
    return created


def clean_answers(test, posted):
    """Keep only valid answers: MCQ option index (int) or written text (str)."""
    answers = {}
    for i, q in enumerate(test.questions):
        raw = posted.get(str(i))
        if raw is None:
            continue
        if q.get('type', 'mcq') == 'mcq':
            try:
                choice = int(raw)
            except (TypeError, ValueError):
                continue
            if 0 <= choice < len(q['options']):
                answers[str(i)] = choice
        else:
            text = str(raw)[:MAX_ANSWER_CHARS]
            if text.strip():
                answers[str(i)] = text
    return answers


def save_draft(assessment, posted):
    """Autosave while the test is open."""
    assessment.answers = clean_answers(assessment.mcq_test, posted)
    assessment.save(update_fields=['answers', 'updated_at'])


def grade(assessment, posted=None):
    """Submit: mark the MCQ part and save. ``posted`` maps question index (as
    str) to the choice index or written answer; None keeps the saved draft.
    Tests with written questions wait for HR (scored stays empty)."""
    test = assessment.mcq_test
    if posted is not None:
        assessment.answers = clean_answers(test, posted)
    auto = 0.0
    for i, q in enumerate(test.questions):
        if q.get('type', 'mcq') == 'mcq' and assessment.answers.get(str(i)) == q['answer']:
            auto += float(q.get('marks', 1))
    assessment.auto_score = Decimal(str(round(auto, 2)))
    assessment.max_score = Decimal(str(test.total_marks))
    assessment.submitted_at = timezone.now()
    assessment.resume_allowed = False
    assessment.date = timezone.localdate()
    if test.has_written:
        assessment.scored = None
        _apply_written(assessment)
    else:
        assessment.scored = assessment.auto_score
    assessment.save()
    return assessment


def _apply_written(assessment):
    """Total = MCQ + HR marks, once every written question has a mark."""
    written = [i for i, q in enumerate(assessment.mcq_test.questions) if q.get('type', 'mcq') != 'mcq']
    given = assessment.marks or {}
    if written and all(str(i) in given and given[str(i)].get('marks') is not None for i in written):
        manual = sum(float(given[str(i)]['marks']) for i in written)
        assessment.scored = Decimal(str(round(float(assessment.auto_score or 0) + manual, 2)))
        assessment.marked_at = assessment.marked_at or timezone.now()


def mark_written(assessment, marks):
    """HR marks: {index(str): {"marks": number|None, "comment": str}}."""
    questions = assessment.mcq_test.questions
    clean = {}
    for key, val in marks.items():
        try:
            i = int(key)
            q = questions[i]
        except (ValueError, IndexError):
            continue
        if q.get('type', 'mcq') == 'mcq':
            continue
        m = val.get('marks')
        if m not in (None, ''):
            m = max(0.0, min(float(m), float(q.get('marks', 1))))
            m = int(m) if m.is_integer() else round(m, 2)
        else:
            m = None
        clean[str(i)] = {'marks': m, 'comment': str(val.get('comment') or '')[:2000]}
    assessment.marks = clean
    assessment.scored = None
    _apply_written(assessment)
    assessment.save()
    return assessment


# --- Proctoring --------------------------------------------------------------

LOCKING = {
    'tab_hidden': 'Switched tab or minimised the browser',
    'window_blur': 'Switched to another window or app',
    'fullscreen_exit': 'Left fullscreen',
    'camera_off': 'Turned the camera off',
    'second_screen': 'Connected a second screen',
    'reload': 'Reloaded or left the test page',
}
FLAGS = {
    'no_face': 'No face in front of the camera',
    'multiple_faces': 'More than one face in view',
    'looking_away': 'Looked away from the screen',
    'paste_blocked': 'Tried to paste',
    'devtools': 'Opened developer tools',
    'face_tracking_off': 'Face tracking could not start',
}


def record_event(assessment, kind, detail=''):
    """Log a proctoring event. Locking events past the test's limit lock and
    submit the test. Returns True if the test is now locked."""
    if assessment.submitted_at:
        return bool(assessment.locked_at)
    locks = kind in LOCKING
    label = LOCKING.get(kind) or FLAGS.get(kind) or kind
    assessment.violations = (assessment.violations or []) + [{
        'at': timezone.now().isoformat(), 'kind': kind, 'label': label,
        'detail': str(detail)[:200], 'locks': locks,
    }]
    strikes = sum(1 for v in assessment.violations if v.get('locks'))
    if locks and strikes >= assessment.mcq_test.max_violations:
        assessment.locked_at = timezone.now()
        assessment.lock_reason = label
        assessment.save(update_fields=['violations', 'locked_at', 'lock_reason', 'updated_at'])
        grade(assessment)
        return True
    assessment.save(update_fields=['violations', 'updated_at'])
    return False


def unlock(assessment, by=''):
    """HR lets the intern carry on: the clock resumes with the time that was
    left when it locked, and the saved answers are kept."""
    if assessment.locked_at and assessment.started_at:
        used = assessment.locked_at - assessment.started_at
        assessment.started_at = timezone.now() - used
    assessment.violations = (assessment.violations or []) + [{
        'at': timezone.now().isoformat(), 'kind': 'unlocked', 'label': f'Unlocked by {by or "HR"}',
        'detail': '', 'locks': False}]
    # Earlier strikes no longer count toward the next lock.
    for v in assessment.violations:
        v['locks'] = False
    assessment.locked_at = None
    assessment.lock_reason = ''
    assessment.submitted_at = None
    assessment.scored = None
    assessment.auto_score = None
    assessment.resume_allowed = True
    assessment.save()


def reset(assessment):
    """Retake from scratch."""
    for snap in assessment.snapshots.all():
        snap.image.delete(save=False)
    assessment.snapshots.all().delete()
    assessment.answers, assessment.marks, assessment.violations = {}, {}, []
    assessment.scored = assessment.auto_score = None
    assessment.started_at = assessment.submitted_at = assessment.marked_at = assessment.locked_at = None
    assessment.lock_reason = ''
    assessment.resume_allowed = False
    assessment.save()


def question_rows(assessment):
    """Questions as the intern sees them while taking the test (no answers)."""
    questions = assessment.mcq_test.questions
    rows = []
    for n, i in enumerate(question_order(assessment), start=1):
        q = questions[i]
        saved = (assessment.answers or {}).get(str(i))
        row = {'num': n, 'idx': i, 'type': q.get('type', 'mcq'), 'text': q['question'],
               'marks': q.get('marks', 1), 'saved': saved}
        if row['type'] == 'mcq':
            row['options'] = [{'letter': LETTERS[j], 'text': t, 'idx': j, 'checked': saved == j}
                              for j, t in enumerate(q['options'])]
        else:
            row['language'] = q.get('language', '')
            row['value'] = saved if isinstance(saved, str) else q.get('starter', '')
        rows.append(row)
    return rows


def review_rows(assessment):
    """Each question with the intern's answer and the right answer, in the
    order the intern saw them."""
    questions = assessment.mcq_test.questions
    marks = assessment.marks or {}
    rows = []
    for n, i in enumerate(question_order(assessment), start=1):
        q = questions[i]
        qtype = q.get('type', 'mcq')
        chosen = (assessment.answers or {}).get(str(i))
        row = {'num': n, 'idx': i, 'type': qtype, 'question': q['question'],
               'explanation': q.get('explanation', ''), 'marks': q.get('marks', 1), 'chosen': chosen,
               'skipped': chosen is None}
        if qtype == 'mcq':
            row.update({
                'correct': q['answer'], 'is_right': chosen == q['answer'],
                'got': q.get('marks', 1) if chosen == q['answer'] else 0,
                'options': [{'letter': LETTERS[j], 'text': t, 'idx': j} for j, t in enumerate(q['options'])],
            })
        else:
            m = marks.get(str(i), {})
            row.update({
                'language': q.get('language', ''), 'model_answer': q.get('answer', ''),
                'got': m.get('marks'), 'comment': m.get('comment', ''),
                'is_right': m.get('marks') is not None and float(m['marks']) >= float(q.get('marks', 1)),
                'is_marked': m.get('marks') is not None,
            })
        rows.append(row)
    return rows
