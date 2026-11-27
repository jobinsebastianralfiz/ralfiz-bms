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
"""
import json
import random
import string
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

LETTERS = string.ascii_uppercase
MAX_QUESTIONS = 300
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
        text = _first(item, 'question', 'q', 'text', 'title')
        if not isinstance(text, str) or not text.strip():
            raise McqFormatError(f'Question {n} has no "question" text.')
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

    return {
        'title': str(_first(data, 'title', 'name') or '').strip()[:255],
        'description': str(_first(data, 'description', 'instructions') or '').strip(),
        'duration_minutes': duration,
        'questions': questions,
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


def grade(assessment, posted):
    """Mark the intern's answers and save. ``posted`` maps question index (as
    str) to the chosen option index (as str); unanswered questions are absent."""
    questions = assessment.mcq_test.questions
    answers, score = {}, 0.0
    for i, q in enumerate(questions):
        raw = posted.get(str(i))
        try:
            choice = int(raw)
        except (TypeError, ValueError):
            continue
        if not 0 <= choice < len(q['options']):
            continue
        answers[str(i)] = choice
        if choice == q['answer']:
            score += float(q.get('marks', 1))
    assessment.answers = answers
    assessment.scored = Decimal(str(round(score, 2)))
    assessment.max_score = Decimal(str(assessment.mcq_test.total_marks))
    assessment.submitted_at = timezone.now()
    assessment.date = timezone.localdate()
    assessment.save()
    return assessment


def review_rows(assessment):
    """Each question with the intern's choice and the right answer, in the
    order the intern saw them."""
    questions = assessment.mcq_test.questions
    rows = []
    for n, i in enumerate(question_order(assessment), start=1):
        q = questions[i]
        chosen = assessment.answers.get(str(i))
        rows.append({
            'num': n, 'question': q['question'], 'explanation': q.get('explanation', ''),
            'marks': q.get('marks', 1), 'chosen': chosen, 'correct': q['answer'],
            'is_right': chosen == q['answer'], 'skipped': chosen is None,
            'options': [{'letter': LETTERS[j], 'text': t, 'idx': j} for j, t in enumerate(q['options'])],
        })
    return rows
