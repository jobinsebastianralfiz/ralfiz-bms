"""Sequential unlocking: courses follow the learning path, lessons go in order.

- A course unlocks when every prerequisite course the student is enrolled in
  is complete (all lessons done and a practice test at the pass mark). A
  prerequisite the student is not enrolled in does not block them: the
  trainer chose to enrol them further along. A course the student has
  already started stays open.
- Inside a course, a lesson unlocks when the lesson before it is done. A
  lesson the student has already started stays open.
- Owner previews and students with `unlock_all` see everything.
"""
from .models import LabProgress, Lesson, QuizAnswer, TestAttempt, Track
from .progress import DONE, NOT_STARTED, lesson_statuses, track_summary

PREREQS = {'ab410': ['pl900'], 'pl300': ['pl900'], 'ab400': ['ab410'], 'dom': ['js']}


def locks_apply(request):
    student = getattr(request, 'student', None)
    return not request.is_preview and student is not None and not student.unlock_all


def course_lock(request, track, summaries=None):
    """None if the course is open, else the reason it is locked."""
    if not locks_apply(request):
        return None
    prereqs = PREREQS.get(track.id, [])
    if not prereqs or _started(request.user, track):
        return None
    enrolled = set(request.student.enrollments.values_list('track_id', flat=True))
    for pid in prereqs:
        if pid not in enrolled:
            continue
        s = (summaries or {}).get(pid)
        if s is None:
            s = track_summary(request.user, Track.objects.get(pk=pid))
        if not s['completed']:
            return f'Complete {s["track"].code} first (every lesson and a 700+ practice test).'
    return None


def _started(user, track):
    return (LabProgress.objects.filter(user=user, lesson__track=track).exclude(ticked_steps=[]).exists()
            or QuizAnswer.objects.filter(user=user, question__track=track).exists()
            or TestAttempt.objects.filter(user=user, track=track).exists())


def course_locks(request, summaries):
    """{track_id: reason or None} for a list of track summaries."""
    by_id = {s['track'].id: s for s in summaries}
    return {s['track'].id: course_lock(request, s['track'], by_id) for s in summaries}


def locked_lessons(request, lessons, statuses, course_reason=None):
    """{lesson_id: reason} for the locked lessons of one course, in order."""
    if not locks_apply(request):
        return {}
    if course_reason:
        return {l.id: course_reason for l in lessons}
    out, prev = {}, None
    for lesson in lessons:
        st = statuses[lesson.id]['status']
        if prev is not None and statuses[prev.id]['status'] != DONE and st == NOT_STARTED:
            # Chains: if the previous one is locked, this one is too.
            out[lesson.id] = f'Finish {prev.num} {prev.title} first.'
        prev = lesson
    return out


def lesson_lock(request, lesson):
    """None if the student may open this lesson, else why not."""
    if not locks_apply(request):
        return None
    reason = course_lock(request, lesson.track)
    if reason:
        return reason
    lessons = list(Lesson.objects.filter(track_id=lesson.track_id).only('id', 'num', 'title',
                                                                           'lab_steps'))
    idx = next(i for i, l in enumerate(lessons) if l.id == lesson.id)
    if idx == 0:
        return None
    pair = lessons[idx - 1:idx + 1]
    st = lesson_statuses(request.user, pair)
    if st[pair[0].id]['status'] != DONE and st[lesson.id]['status'] == NOT_STARTED:
        return f'Finish {pair[0].num} {pair[0].title} first.'
    return None
