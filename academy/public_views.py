"""Public Academy pages: course catalogue, course overviews and free sample
lessons. No login. Only lesson Learn content is public; labs, files, quizzes
and answers stay behind sign-in.
"""
import re
from html import unescape

import json

from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import CompanySettings

from .access import is_admin
from .models import ExerciseFile, Lesson, Question, Student, Track
from .sanitize import headings

# The first lessons of every course are free to read.
FREE_LESSONS_PER_TRACK = 2


def free_lesson_ids(track):
    return list(Lesson.objects.filter(track=track)
                .values_list('id', flat=True)[:FREE_LESSONS_PER_TRACK])


def _plain(html, limit=None):
    text = re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', html or ''))).strip()
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    if limit and len(text) > limit:
        text = text[:limit].rsplit(' ', 1)[0] + '…'
    return text


def _contact():
    s = CompanySettings.get_settings()
    phone = re.sub(r'\D', '', s.phone or '')
    if len(phone) == 10:
        phone = '91' + phone
    return {'name': s.company_name, 'email': s.email, 'phone': s.phone,
            'whatsapp': f'https://wa.me/{phone}' if phone else ''}


def _viewer(request):
    """Where the 'account' button in the header goes."""
    u = request.user
    if u.is_authenticated and (is_admin(u) or Student.objects.filter(user=u, status='active').exists()):
        return {'signed_in': True, 'url': reverse('academy:home')}
    return {'signed_in': False, 'url': reverse('academy:login')}


def _base_url(request):
    """Absolute site root. Railway terminates HTTPS at its proxy, so Django
    sees plain HTTP; trust the proxy's header here rather than site-wide."""
    scheme = 'https' if (request.is_secure() or
                         request.META.get('HTTP_X_FORWARDED_PROTO') == 'https') else 'http'
    return f'{scheme}://{request.get_host()}'


def _common(request):
    return {'contact': _contact(), 'viewer': _viewer(request), 'site': _base_url(request)}


PUBLIC_CACHE = cache_control(public=True, max_age=600)


def sample_question(track):
    """One real exam-style question per course, from its last free lesson."""
    free = free_lesson_ids(track)
    if not free:
        return None
    return (Question.objects.filter(lesson_id=free[-1], source='lesson', is_active=True)
            .order_by('sort_order').first())


@csrf_exempt  # grades public content only; stores nothing
@require_POST
def try_question(request, question_id):
    q = get_object_or_404(Question, pk=question_id, is_active=True, source='lesson')
    if q.lesson_id is None or q.lesson_id not in free_lesson_ids(q.track):
        raise Http404
    try:
        choice = json.loads(request.body or b'{}').get('choice')
    except ValueError:
        choice = None
    if not isinstance(choice, int) or not 0 <= choice < len(q.options):
        return HttpResponseBadRequest('choice must be an option index')
    return JsonResponse({'correct': choice == q.answer, 'answer': q.answer,
                         'explanation': q.explanation})


@PUBLIC_CACHE
def catalog(request):
    tracks = list(Track.objects.filter(is_published=True))
    rows = []
    for t in tracks:
        lessons = list(Lesson.objects.filter(track=t).only('id', 'num', 'title', 'minutes'))
        rows.append({'track': t, 'lessons': len(lessons),
                     'hours': round(sum(l.minutes for l in lessons) / 60),
                     'questions': Question.objects.filter(track=t, is_active=True).count(),
                     'free': lessons[:FREE_LESSONS_PER_TRACK],
                     'sample': sample_question(t)})
    totals = {
        'tracks': len(tracks),
        'lessons': Lesson.objects.filter(track__in=tracks).count(),
        'files': ExerciseFile.objects.count(),
        'questions': Question.objects.filter(track__in=tracks, is_active=True).count(),
    }
    return render(request, 'academy/public/catalog.html', {
        'rows': rows, 'totals': totals, **_common(request),
    })


@PUBLIC_CACHE
def course(request, track_id):
    track = get_object_or_404(Track, pk=track_id, is_published=True)
    lessons = list(Lesson.objects.filter(track=track).select_related('domain'))
    free = set(free_lesson_ids(track))
    domains = []
    for l in lessons:
        if not domains or domains[-1]['domain'].pk != l.domain_id:
            domains.append({'domain': l.domain, 'index': len(domains), 'lessons': [], 'minutes': 0})
        domains[-1]['lessons'].append({'lesson': l, 'free': l.id in free})
        domains[-1]['minutes'] += l.minutes
    fact_icons = [('fa-trophy', 'amber'), ('fa-layer-group', 'violet'),
                  ('fa-calendar-days', 'blue'), ('fa-clock', 'teal')]
    facts = [{'value': f[0], 'label': f[1], 'icon': fact_icons[i % 4][0], 'tone': fact_icons[i % 4][1]}
             for i, f in enumerate(track.facts)]
    labs_with_sim = sum(1 for l in lessons if l.widget)
    return render(request, 'academy/public/course.html', {
        'track': track, 'domains': domains, 'facts': facts,
        'lesson_count': len(lessons), 'hours': round(sum(l.minutes for l in lessons) / 60),
        'questions': Question.objects.filter(track=track, is_active=True).count(),
        'steps': sum(len(l.lab_steps) for l in lessons),
        'files': sum(1 for ids in ExerciseFile.objects.values_list('track_ids', flat=True)
                     if track.id in ids),
        'simulators': labs_with_sim,
        'free_lessons': [x for d in domains for x in d['lessons'] if x['free']],
        'others': Track.objects.filter(is_published=True).exclude(pk=track.pk),
        **_common(request),
    })


@PUBLIC_CACHE
def sample_lesson(request, track_id, lesson_id):
    track = get_object_or_404(Track, pk=track_id, is_published=True)
    lesson = get_object_or_404(Lesson.objects.select_related('domain'), pk=lesson_id, track=track)
    free = free_lesson_ids(track)
    if lesson.id not in free:
        raise Http404('Only the free sample lessons are public.')
    idx = free.index(lesson.id)
    next_free = Lesson.objects.filter(pk=free[idx + 1]).first() if idx + 1 < len(free) else None
    words = len(lesson.content_html.replace('<', ' <').split())
    return render(request, 'academy/public/lesson.html', {
        'track': track, 'lesson': lesson, 'toc': headings(lesson.content_html),
        'read_minutes': max(1, round(words / 200)),
        'lead': _plain(lesson.summary_html, 200),
        'description': _plain(lesson.summary_html, 155),
        'quiz_count': Question.objects.filter(lesson=lesson, source='lesson', is_active=True).count(),
        'file_count': lesson.lesson_files.count(),
        'next_free': next_free, **_common(request),
    })


def sitemap(request):
    base = _base_url(request)
    urls = [reverse('academy:catalog')]
    for t in Track.objects.filter(is_published=True):
        urls.append(reverse('academy:catalog_course', args=[t.id]))
        urls += [reverse('academy:catalog_lesson', args=[t.id, lid]) for lid in free_lesson_ids(t)]
    body = ''.join(f'<url><loc>{base}{u}</loc></url>' for u in urls)
    return HttpResponse('<?xml version="1.0" encoding="UTF-8"?>'
                        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>',
                        content_type='application/xml')


def robots(request):
    base = _base_url(request)
    return HttpResponse(
        'User-agent: *\n'
        'Allow: /academy/catalog/\n'
        'Disallow: /admin/\n'
        f'\nSitemap: {base}/academy/sitemap.xml\n',
        content_type='text/plain')
