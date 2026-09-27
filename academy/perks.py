"""XP, levels, badges and streaks.

XP and badges are derived from progress that is already stored (lab ticks,
quiz answers, lessons, tests), so they are always consistent and existing
students are credited for work done before perks existed. Only streaks need
their own record: one LearningDay row per active day.
"""
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from .models import LearningDay, Lesson, QuizAnswer, TestAttempt
from .progress import DONE, lesson_statuses

XP = {'step': 5, 'answer': 10, 'lesson': 50, 'section': 100, 'test': 200, 'course': 500}

LEVELS = [(0, 'Explorer'), (400, 'Learner'), (1200, 'Builder'), (3000, 'Practitioner'),
          (6000, 'Expert'), (10000, 'Master')]

# key, name, icon, what earns it
BADGES = [
    ('first_step', 'First step', 'fa-shoe-prints', 'Tick your first lab step'),
    ('first_lesson', 'Lesson one', 'fa-book-open', 'Complete your first lesson'),
    ('perfect_quiz', 'Sharp shooter', 'fa-bullseye', 'Get every question in a lesson quiz right first time'),
    ('section', 'Section cleared', 'fa-layer-group', 'Complete every lesson in a section'),
    ('lab_100', 'Hands-on hero', 'fa-flask', 'Tick 100 lab steps'),
    ('quiz_50', 'Quiz master', 'fa-brain', 'Answer 50 quiz questions correctly'),
    ('test_pass', 'Exam ready', 'fa-medal', 'Score 700+ on a practice test'),
    ('test_900', 'Top scorer', 'fa-trophy', 'Score 900+ on a practice test'),
    ('course', 'Graduate', 'fa-graduation-cap', 'Complete a whole course'),
    ('streak_3', 'On a roll', 'fa-fire', 'Learn 3 days in a row'),
    ('streak_7', 'Week warrior', 'fa-fire-flame-curved', 'Learn 7 days in a row'),
]
BADGE_BY_KEY = {b[0]: b for b in BADGES}


def record_activity(user):
    LearningDay.objects.get_or_create(user=user, date=timezone.localdate())


def streaks(user):
    days = list(LearningDay.objects.filter(user=user).values_list('date', flat=True))
    today = timezone.localdate()
    current = 0
    day_set = set(days)
    # A streak survives until the end of the day after the last activity.
    start = today if today in day_set else today - timedelta(days=1)
    while start in day_set:
        current += 1
        start -= timedelta(days=1)
    longest = run = 0
    prev = None
    for d in sorted(day_set):
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        longest = max(longest, run)
        prev = d
    return {'current': current, 'longest': longest, 'today': today in day_set}


def level_for(xp):
    idx = max(i for i, (floor, _) in enumerate(LEVELS) if xp >= floor)
    floor, name = LEVELS[idx]
    nxt = LEVELS[idx + 1] if idx + 1 < len(LEVELS) else None
    return {
        'number': idx + 1, 'name': name, 'floor': floor,
        'next_name': nxt[1] if nxt else None, 'next_at': nxt[0] if nxt else None,
        'to_next': (nxt[0] - xp) if nxt else 0,
        'percent': round((xp - floor) / (nxt[0] - floor) * 100) if nxt else 100,
    }


def compute(user, tracks):
    """Everything the dashboard, profile and toasts need, for these tracks."""
    tracks = list(tracks)
    lessons = list(Lesson.objects.filter(track__in=tracks).select_related('domain'))
    statuses = lesson_statuses(user, lessons)

    steps = sum(s['lab_ticked'] for s in statuses.values())
    lessons_done = sum(1 for s in statuses.values() if s['status'] == DONE)
    answers = QuizAnswer.objects.filter(user=user, question__track__in=tracks)
    right = answers.filter(ever_correct=True).count()

    by_domain = defaultdict(list)
    by_track = defaultdict(list)
    for l in lessons:
        by_domain[l.domain_id].append(statuses[l.id]['status'] == DONE)
        by_track[l.track_id].append(statuses[l.id]['status'] == DONE)
    sections_done = sum(1 for v in by_domain.values() if v and all(v))

    best = {}
    for a in TestAttempt.objects.filter(user=user, track__in=tracks, submitted_at__isnull=False):
        best[a.track_id] = max(best.get(a.track_id, 0), a.score or 0)
    tests_passed = sum(1 for v in best.values() if v >= TestAttempt.PASS_MARK)
    courses_done = sum(1 for tid, v in by_track.items()
                       if v and all(v) and best.get(tid, 0) >= TestAttempt.PASS_MARK)

    # A lesson quiz where every question was right on the first attempt.
    perfect = (answers.filter(question__source='lesson')
               .values('question__lesson')
               .annotate(n=Count('id'), first=Count('id', filter=Q(attempts=1, ever_correct=True)))
               .filter(n__gt=0))
    lesson_q = dict(Lesson.objects.filter(pk__in=[p['question__lesson'] for p in perfect])
                    .annotate(q=Count('questions', filter=Q(questions__source='lesson',
                                                            questions__is_active=True)))
                    .values_list('id', 'q'))
    perfect_quiz = any(p['first'] == p['n'] == lesson_q.get(p['question__lesson'])
                       for p in perfect)

    xp = (steps * XP['step'] + right * XP['answer'] + lessons_done * XP['lesson']
          + sections_done * XP['section'] + tests_passed * XP['test'] + courses_done * XP['course'])
    streak = streaks(user)
    top = max(best.values(), default=0)
    earned_keys = {
        'first_step': steps >= 1, 'first_lesson': lessons_done >= 1, 'perfect_quiz': perfect_quiz,
        'section': sections_done >= 1, 'lab_100': steps >= 100, 'quiz_50': right >= 50,
        'test_pass': top >= TestAttempt.PASS_MARK, 'test_900': top >= 900,
        'course': courses_done >= 1, 'streak_3': streak['longest'] >= 3,
        'streak_7': streak['longest'] >= 7,
    }
    badges = [{'key': k, 'name': n, 'icon': i, 'how': h, 'earned': earned_keys[k]}
              for k, n, i, h in BADGES]
    return {
        'xp': xp, 'level': level_for(xp), 'streak': streak, 'badges': badges,
        'earned': [b for b in badges if b['earned']],
        'counts': {'steps': steps, 'right': right, 'lessons': lessons_done,
                   'sections': sections_done, 'tests_passed': tests_passed,
                   'courses': courses_done},
    }


def for_request(request):
    from .access import visible_tracks
    return compute(request.user, visible_tracks(request))


def announce_new(request, perks):
    """Badges earned since the student last saw them; marks them seen."""
    student = getattr(request, 'student', None)
    if student is None or request.is_preview:
        return []
    earned = [b['key'] for b in perks['earned']]
    new = [k for k in earned if k not in (student.seen_badges or [])]
    if new:
        student.seen_badges = sorted(set(student.seen_badges or []) | set(new))
        student.save(update_fields=['seen_badges'])
    return [{'name': BADGE_BY_KEY[k][1], 'icon': BADGE_BY_KEY[k][2]} for k in new]


def event_payload(request, before_xp):
    """What an API response tells the page after a learning action."""
    record_activity(request.user)
    perks = for_request(request)
    return {
        'xp': perks['xp'], 'xp_gain': max(0, perks['xp'] - before_xp),
        'level': perks['level']['name'],
        'level_up': perks['level']['floor'] > 0 and before_xp < perks['level']['floor'],
        'streak': perks['streak']['current'],
        'new_badges': announce_new(request, perks),
    }
