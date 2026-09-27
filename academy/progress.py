"""Progress rules from the integration guide (section 9).

- Lab complete: every step ticked.
- Quiz complete: every lesson question has ever_correct.
- Lesson: done when both are complete; in_progress when any step is ticked or
  any question answered; otherwise not_started.
- Track progress: done lessons / total lessons.
"""
from collections import defaultdict

from .models import LabProgress, Lesson, Question, QuizAnswer, TestAttempt

DONE, IN_PROGRESS, NOT_STARTED = 'done', 'in_progress', 'not_started'


def lesson_statuses(user, lessons):
    """{lesson_id: {'status', 'lab_done', 'lab_ticked', 'quiz_done', 'quiz_right', 'quiz_total'}}

    Three queries however many lessons are passed in.
    """
    lessons = list(lessons)
    ids = [l.id for l in lessons]
    ticks = dict(LabProgress.objects.filter(user=user, lesson_id__in=ids)
                 .values_list('lesson_id', 'ticked_steps'))
    questions = defaultdict(list)
    for qid, lid in (Question.objects.filter(lesson_id__in=ids, source='lesson', is_active=True)
                     .values_list('id', 'lesson_id')):
        questions[lid].append(qid)
    answers = dict(QuizAnswer.objects.filter(user=user, question__lesson_id__in=ids,
                                             question__source='lesson')
                   .values_list('question_id', 'ever_correct'))

    out = {}
    for lesson in lessons:
        steps = len(lesson.lab_steps)
        ticked = {i for i in (ticks.get(lesson.id) or []) if isinstance(i, int) and 0 <= i < steps}
        qids = questions.get(lesson.id, [])
        right = sum(1 for q in qids if answers.get(q))
        answered = any(q in answers for q in qids)
        lab_done = len(ticked) == steps
        quiz_done = right == len(qids)
        if lab_done and quiz_done:
            status = DONE
        elif ticked or answered:
            status = IN_PROGRESS
        else:
            status = NOT_STARTED
        out[lesson.id] = {
            'status': status, 'lab_done': lab_done, 'lab_ticked': len(ticked),
            'lab_total': steps, 'quiz_done': quiz_done, 'quiz_right': right,
            'quiz_total': len(qids),
        }
    return out


def track_summary(user, track, lessons=None):
    """Counts and the next lesson for one track."""
    if lessons is None:
        lessons = list(Lesson.objects.filter(track=track).select_related('domain'))
    statuses = lesson_statuses(user, lessons)
    done = sum(1 for s in statuses.values() if s['status'] == DONE)
    started = any(s['status'] != NOT_STARTED for s in statuses.values())
    next_lesson = next((l for l in lessons if statuses[l.id]['status'] != DONE), lessons[0] if lessons else None)
    tests = TestAttempt.objects.filter(user=user, track=track, submitted_at__isnull=False)
    best = max((t.score for t in tests), default=None)
    total = len(lessons)
    return {
        'track': track, 'lessons': lessons, 'statuses': statuses,
        'done': done, 'total': total, 'started': started,
        'percent': round(done / total * 100) if total else 0,
        'next_lesson': next_lesson, 'best_score': best,
        'tests_taken': tests.count(),
        # Section 9: every lesson done and one practice test at the pass mark.
        'completed': total > 0 and done == total and best is not None and best >= TestAttempt.PASS_MARK,
    }
