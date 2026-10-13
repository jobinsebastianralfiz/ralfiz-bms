"""Social Hub web pages. Every rule lives in services.py; these views only
read the request, call a service and render.
"""
import calendar as cal
import hashlib
import base64
import json
import secrets
from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import Client
from . import services as S
from .adapters import REAL, get_adapter
from .adapters.base import AdapterError, NotSupported
from .adapters.whatsapp import wa_app
from .crypto import decrypt, encrypt
from .models import (PLATFORM_CHOICES, PLATFORM_LABELS, AuditLog, InboxItem, MediaAsset, Membership,
                     Post, SocialAccount, Workspace)

PLATFORM_ORDER = [p for p, _ in PLATFORM_CHOICES]
#: No feed to post to: these only feed the inbox.
INBOX_ONLY = ('whatsapp', 'email')
PLATFORM_META = {
    'facebook': {'short': 'f', 'color': '#1877F2', 'icon': 'fa-brands fa-facebook-f'},
    'instagram': {'short': 'IG', 'color': '#E1306C', 'icon': 'fa-brands fa-instagram'},
    'linkedin': {'short': 'in', 'color': '#0A66C2', 'icon': 'fa-brands fa-linkedin-in'},
    'youtube': {'short': 'YT', 'color': '#FF0000', 'icon': 'fa-brands fa-youtube'},
    'x': {'short': 'X', 'color': '#E8E8F0', 'icon': 'fa-brands fa-x-twitter'},
    'whatsapp': {'short': 'WA', 'color': '#25D366', 'icon': 'fa-brands fa-whatsapp'},
    'google_business': {'short': 'G', 'color': '#F4B400', 'icon': 'fa-brands fa-google'},
    'email': {'short': '@', 'color': '#EA4335', 'icon': 'fas fa-envelope'},
}
STATUS_TONE = {
    'draft': 'secondary', 'review': 'warning', 'changes': 'danger', 'scheduled': 'info',
    'publishing': 'info', 'published': 'success', 'partial': 'warning', 'failed': 'danger',
}


def hub_view(fn):
    """Login required, and the user must manage at least one workspace."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not S.can_use_hub(request.user):
            raise PermissionDenied('The Social Hub is for the social media team.')
        try:
            return fn(request, *args, **kwargs)
        except S.SocialError as exc:
            if request.headers.get('x-requested-with') == 'fetch':
                return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
            messages.error(request, str(exc))
            from core.security import safe_next
            return redirect(safe_next(request, request.META.get('HTTP_REFERER'), reverse('social:calendar')))
    wrapper.__name__ = fn.__name__
    return wrapper


# ================================================================ shared context

def _scope(request):
    """The workspaces in view (?ws= or the remembered one) and the platform filter."""
    allowed = S.workspaces_for(request.user)
    ws_id = request.GET.get('ws')
    if ws_id is not None:
        request.session['social_ws'] = ws_id
    ws_id = request.session.get('social_ws', 'all')
    current = allowed.filter(pk=ws_id).first() if ws_id and ws_id != 'all' else None
    platform = request.GET.get('p', '')
    if platform not in PLATFORM_LABELS:
        platform = ''
    return allowed, current, platform


def _ctx(request, tab, **extra):
    allowed, current, platform = _scope(request)
    in_view = [current] if current else list(allowed)
    att = S.attention(in_view)
    wss = []
    for w in allowed.annotate(
            n_review=Count('posts', filter=Q(posts__status='review'), distinct=True),
            n_failed=Count('posts', filter=Q(posts__status__in=('failed', 'partial')), distinct=True),
            n_bad=Count('accounts', filter=Q(accounts__status__in=('expiring', 'reconnect')), distinct=True)):
        w.platforms = sorted({a.platform for a in w.accounts.all()}, key=PLATFORM_ORDER.index)
        w.alert = w.n_failed + w.n_bad
        w.attention = w.n_review + w.alert
        wss.append(w)
    accounts = SocialAccount.objects.filter(workspace__in=in_view)
    platforms_present = sorted({a.platform for a in accounts}, key=PLATFORM_ORDER.index)
    ctx = {
        'tab': tab, 'workspaces': wss, 'current': current, 'in_view': in_view, 'platform': platform,
        'platforms_present': [(p, PLATFORM_LABELS[p], PLATFORM_META[p]) for p in platforms_present],
        'platform_meta': PLATFORM_META, 'attention': att,
        'is_manager': S.is_social_admin(request.user) or (current and S.role_for(request.user, current) == 'manager'),
        'me_initial': (request.user.first_name or request.user.username or '?')[:1].upper(),
        'hub_only': S.social_only(request.user),  # no BMS behind the hub for this login
        'is_admin': S.is_social_admin(request.user),
    }
    ctx.update(extra)
    return ctx


def _accounts_in_view(ctx):
    qs = SocialAccount.objects.filter(workspace__in=ctx['in_view']).select_related('workspace')
    if ctx['platform']:
        qs = qs.filter(platform=ctx['platform'])
    return qs


def _post_card(post):
    targets = list(post.targets.all())
    post.platforms = [t.account.platform for t in targets]
    post.target_list = targets
    post.tone = STATUS_TONE.get(post.status, 'secondary')
    post.first_media = next(iter(post.ordered_media()), None)
    post.last_note = post.approvals.filter(decision='changes').first() if post.status == 'changes' else None
    post.errors = [t for t in targets if t.status == 'failed' and t.error]
    return post


# ================================================================ home

@hub_view
def home(request):
    """The prototype's dashboard: this week's reach, the posting goal, the
    30-day trend, best times, the next posts out and what needs a person."""
    ctx = _ctx(request, 'home')
    accounts = list(_accounts_in_view(ctx))
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    tz = timezone.get_current_timezone()
    week = S.analytics(accounts, today - timedelta(days=6), today)
    before = S.analytics(accounts, today - timedelta(days=13), today - timedelta(days=7))
    reach, prev_reach = week['totals']['reach'], before['totals']['reach']
    trend = S.analytics(accounts, today - timedelta(days=29), today)
    top_platform = next(iter(week['by_platform']), None)

    week_posts = Post.objects.filter(
        workspace__in=ctx['in_view'], scheduled_at__gte=datetime.combine(week_start, time.min, tz),
        scheduled_at__lt=datetime.combine(week_start + timedelta(days=7), time.min, tz))
    if ctx['platform']:
        week_posts = week_posts.filter(targets__account__platform=ctx['platform']).distinct()
    planned = week_posts.exclude(status='draft').count()
    published = week_posts.filter(status__in=('published', 'partial')).count()

    queue = (Post.objects.filter(workspace__in=ctx['in_view'], status__in=('scheduled', 'review'),
                                 scheduled_at__gte=timezone.now())
             .select_related('workspace').prefetch_related('targets__account').order_by('scheduled_at'))
    if ctx['platform']:
        queue = queue.filter(targets__account__platform=ctx['platform']).distinct()

    att = ctx['attention']
    claude_replies = InboxItem.objects.filter(account__in=accounts, status='open',
                                              replies__status='draft', replies__source='mcp').distinct().count()
    claude_posts = Post.objects.filter(workspace__in=ctx['in_view'], source='mcp', status='review').count()
    claude_drafts = Post.objects.filter(workspace__in=ctx['in_view'], source='mcp', status='draft').count()
    needs = []
    if att['failed']:
        p = att['failed'][0]
        needs.append({'tone': 'bad', 'text': f"{len(att['failed'])} post{'s' if len(att['failed']) != 1 else ''} "
                      f"failed to go out. “{(p.base_text or p.title)[:60]}” for {p.workspace.name} is one.",
                      'action': 'Open', 'url': f"{reverse('social:calendar')}?day="
                      f"{timezone.localdate(p.scheduled_at).isoformat()}#p{p.pk}"})
    for a in att['accounts'][:2]:
        needs.append({'tone': 'warn', 'text': f"{a.workspace.name}'s {a.get_platform_display()} "
                      + ('sign-in expires soon.' if a.status == 'expiring' else 'needs reconnecting.'),
                      'action': 'Reconnect', 'url': f"{reverse('social:connect', args=[a.platform])}?ws={a.workspace_id}"})
    if att['review']:
        needs.append({'tone': 'ai' if claude_posts else '', 'text': f"{att['review']} post{'s' if att['review'] != 1 else ''} "
                      f"waiting for approval" + (f", {claude_posts} drafted by Claude." if claude_posts else '.'),
                      'action': 'Review posts', 'url': reverse('social:approvals')})
    if claude_drafts:
        needs.append({'tone': 'ai', 'text': f"Claude drafted {claude_drafts} post{'s' if claude_drafts != 1 else ''} "
                      'that nobody has sent for approval yet.', 'action': 'Open drafts',
                      'url': reverse('social:approvals') + '?tab=drafts'})
    if claude_replies:
        needs.append({'tone': 'ai', 'text': f'Claude drafted {claude_replies} repl{"ies" if claude_replies != 1 else "y"} '
                      'in the inbox. Check them before they go out.', 'action': 'Review replies',
                      'url': reverse('social:inbox')})
    elif att['inbox']:
        needs.append({'tone': '', 'text': f"{att['inbox']} comment{'s' if att['inbox'] != 1 else ''} and messages are "
                      'waiting for a reply.', 'action': 'Open inbox', 'url': reverse('social:inbox')})

    new_followers = week['totals']['followers_gained']
    if not new_followers:  # platforms that only report a running total
        level = [v for v in week['series']['followers'] if v]
        new_followers = max(0, level[-1] - level[0]) if len(level) > 1 else 0
    ctx.update({
        'reach': reach, 'new_followers': new_followers,
        'reach_change': round(100 * (reach - prev_reach) / prev_reach, 1) if prev_reach else None,
        'week_totals': week['totals'],
        'headline': (f"{PLATFORM_LABELS[top_platform]} brought the most reach this week."
                     if top_platform else 'Connect accounts and their numbers appear here after the first sync.'),
        'planned': planned, 'published': published,
        'goal_pct': round(100 * published / planned) if planned else 0,
        'queue': [_post_card(p) for p in queue[:4]], 'needs': needs[:4],
        'best': S.best_times(accounts), 'slots': ['6a', '9a', '12p', '3p', '6p', '9p'], 'daynames': S.DAYS,
        'trend': {'labels': [d.strftime('%d %b') for d in trend['days']],
                  'reach': trend['series']['reach'], 'engagement': trend['series']['engagement'],
                  'followers': trend['series']['followers_gained'] if any(trend['series']['followers_gained'])
                  else trend['series']['followers']},
        'has_accounts': bool(accounts),
    })
    return render(request, 'social/home.html', ctx)


# ================================================================ calendar

def _month_arg(value):
    try:
        y, m = map(int, (value or '').split('-'))
        return date(y, m, 1)
    except ValueError:
        return timezone.localdate().replace(day=1)


@hub_view
def calendar_view(request):
    ctx = _ctx(request, 'calendar')
    today = timezone.localdate()
    mode = request.GET.get('mode') or request.session.get('social_cal_mode', 'month')
    request.session['social_cal_mode'] = mode = mode if mode in ('month', 'week') else 'month'
    try:
        selected = date.fromisoformat(request.GET.get('day', ''))
    except ValueError:
        selected = None
    month = _month_arg(request.GET.get('month')) if request.GET.get('month') else (selected or today).replace(day=1)
    selected = selected if selected and (mode == 'week' or selected.month == month.month) else \
        (today if today.month == month.month else month)

    if mode == 'month':
        start = month - timedelta(days=month.weekday())
        last = month.replace(day=cal.monthrange(month.year, month.month)[1])
        end = last + timedelta(days=7 - last.weekday())
    else:
        start = selected - timedelta(days=selected.weekday())
        end = start + timedelta(days=7)
    tz = timezone.get_current_timezone()
    posts = S.posts_between(ctx['in_view'], datetime.combine(start, time.min, tz),
                            datetime.combine(end, time.min, tz),
                            [ctx['platform']] if ctx['platform'] else None)
    by_day, unscheduled = {}, []
    for p in posts:
        _post_card(p)
        if p.scheduled_at:
            by_day.setdefault(timezone.localdate(p.scheduled_at), []).append(p)
        elif p.status in ('draft', 'review', 'changes'):
            unscheduled.append(p)
    weeks, day = [], start
    while day < end:
        weeks.append([{'date': d, 'posts': sorted(by_day.get(d, []), key=lambda p: p.scheduled_at),
                       'out': mode == 'month' and d.month != month.month, 'today': d == today,
                       'past': d < today, 'selected': d == selected}
                      for d in (day + timedelta(days=i) for i in range(7))])
        day += timedelta(days=7)
    prev_month = (month - timedelta(days=1)).replace(day=1)
    next_month = (month + timedelta(days=32)).replace(day=1)
    ctx.update({
        'mode': mode, 'month': month, 'weeks': weeks, 'selected': selected, 'today': today,
        'agenda': sorted(by_day.get(selected, []), key=lambda p: p.scheduled_at),
        'unscheduled': unscheduled[:12],
        'prev': prev_month.strftime('%Y-%m') if mode == 'month' else (selected - timedelta(days=7)).isoformat(),
        'next': next_month.strftime('%Y-%m') if mode == 'month' else (selected + timedelta(days=7)).isoformat(),
        'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    })
    return render(request, 'social/calendar.html', ctx)


@hub_view
@require_POST
def post_move(request, pk):
    """Drag-and-drop: move a post to another day, keeping its time."""
    post = get_object_or_404(Post, pk=pk)
    try:
        day = date.fromisoformat(request.POST.get('date', ''))
    except ValueError:
        raise S.SocialError('Pick a day.')
    old = timezone.localtime(post.scheduled_at) if post.scheduled_at else None
    at = time(old.hour, old.minute) if old else time(10, 0)
    when = timezone.make_aware(datetime.combine(day, at))
    was = post.status
    S.reschedule(request.user, post, when)
    note = f'Moved to {when:%a %d %b, %I:%M %p}.'
    if was == 'scheduled' and post.status == 'review':
        note += f' {post.workspace.name} must approve it again.'
    return JsonResponse({'ok': True, 'message': note, 'status': post.status})


@hub_view
@require_POST
def post_action(request, pk):
    post = get_object_or_404(Post, pk=pk)
    action, comment = request.POST.get('action'), request.POST.get('comment', '').strip()
    user = request.user
    if action == 'submit':
        S.submit(user, post, note=comment)
        msg = 'Scheduled.' if post.status == 'scheduled' else 'Sent for approval.'
    elif action == 'approve':
        S.approve(post, user=user, comment=comment)
        msg = f'Approved. It goes out {timezone.localtime(post.scheduled_at):%a %d %b, %I:%M %p}.'
    elif action == 'changes':
        S.request_changes(post, user=user, comment=comment)
        msg = 'Sent back with your note.'
    elif action == 'retry':
        S.retry(user, post)
        msg = 'Queued to try again.'
    elif action == 'duplicate':
        copy = S.duplicate(user, post)
        messages.success(request, 'Copied as a new draft.')
        return redirect('social:post_edit', pk=copy.pk)
    elif action == 'delete':
        S.delete_post(user, post)
        messages.success(request, 'Post deleted.')
        return redirect('social:calendar')
    elif action == 'publish_now':
        S.require(user, post.workspace, 'manager')
        post.scheduled_at = timezone.now()
        post.save(update_fields=['scheduled_at'])
        if post.status == 'review':
            S.approve(post, user=user, comment='Published now')
        else:
            S.schedule(user, post)
        msg = 'Publishing now. It will show here in a minute.'
    else:
        raise S.SocialError('Unknown action.')
    messages.success(request, msg)
    from core.security import safe_next
    return redirect(safe_next(request, request.POST.get('next') or request.META.get('HTTP_REFERER'), reverse('social:calendar')))


# ================================================================ composer

def _caps_json(accounts):
    out = {}
    for a in accounts:
        c = get_adapter(a.platform).caps
        out[str(a.pk)] = {
            'platform': a.platform, 'label': PLATFORM_LABELS[a.platform], 'name': a.name,
            'handle': a.handle, 'max_chars': c.max_chars, 'requires_media': c.requires_media,
            'video': c.video, 'images': c.images, 'max_media': c.max_media,
            'first_comment': c.first_comment, 'title': c.title, 'healthy': a.healthy,
            'workspace': str(a.workspace_id), 'color': PLATFORM_META[a.platform]['color'],
        }
    return out


@hub_view
def compose(request, pk=None):
    post = get_object_or_404(Post, pk=pk) if pk else None
    ctx = _ctx(request, 'calendar')
    allowed = S.workspaces_for(request.user)
    if post:
        S.require(request.user, post.workspace)
        workspace = post.workspace
    else:
        workspace = allowed.filter(pk=request.GET.get('ws') or request.POST.get('workspace')).first() \
            or ctx['current'] or allowed.first()
    if workspace is None:
        messages.info(request, 'Add a client first.')
        return redirect('social:workspaces')

    if request.method == 'POST':
        f = request.POST
        account_ids = f.getlist('accounts')
        when = None
        if f.get('date'):
            try:
                when = timezone.make_aware(datetime.combine(
                    date.fromisoformat(f['date']), time.fromisoformat(f.get('time') or '10:00')))
            except ValueError:
                raise S.SocialError('That date or time is not valid.')
        overrides = {aid: f.get(f'override_{aid}', '') for aid in account_ids}
        post = S.save_post(request.user, workspace, account_ids=account_ids, text=f.get('text', ''),
                           overrides=overrides, scheduled_at=when, first_comment=f.get('first_comment', ''),
                           title=f.get('title', ''), link=f.get('link', ''),
                           media_ids=[m for m in f.get('media', '').split(',') if m], post=post)
        intent = f.get('intent', 'draft')
        if intent == 'submit':
            try:
                S.submit(request.user, post)
            except S.SocialError as exc:
                messages.error(request, f'Saved as a draft, but not sent: {exc}')
                return redirect('social:post_edit', pk=post.pk)
            messages.success(request, 'Scheduled.' if post.status == 'scheduled' else 'Sent for approval.')
        else:
            messages.success(request, 'Draft saved.')
        day = timezone.localdate(post.scheduled_at) if post.scheduled_at else timezone.localdate()
        return redirect(f"{reverse('social:calendar')}?day={day.isoformat()}")

    # WhatsApp has no feed to post to; it lives in the inbox.
    accounts = list(workspace.accounts.exclude(status='disconnected').exclude(platform__in=INBOX_ONLY))
    when = timezone.localtime(post.scheduled_at) if post and post.scheduled_at else None
    if not when and request.GET.get('day'):
        try:
            when = timezone.make_aware(datetime.combine(date.fromisoformat(request.GET['day']), time(10, 0)))
        except ValueError:
            pass
    best = S.best_times(accounts)
    targets = {str(t.account_id): t for t in post.targets.all()} if post else {}
    ctx.update({
        'post': post, 'workspace': workspace, 'all_workspaces': allowed,
        'accounts': accounts, 'caps': _caps_json(accounts),
        'selected_ids': list(targets) if post else [str(a.pk) for a in accounts if a.healthy][:3],
        'overrides': {k: t.text for k, t in targets.items() if t.text},
        'media_library': workspace.media.all()[:60],
        'post_media_ids': ','.join(str(m.pk) for m in post.ordered_media()) if post else '',
        'when_date': when.date().isoformat() if when else '',
        'when_time': when.strftime('%H:%M') if when else '10:00',
        'best': best['best'][0] if best else None,
        'problems': S.problems_for(post) if post else {},
        'history': post.approvals.all()[:10] if post else [],
    })
    if post:
        _post_card(post)
    return render(request, 'social/compose.html', ctx)


# ================================================================ posts library

KIND_LABELS = {'post': 'Posts', 'reel': 'Reels', 'video': 'Videos', 'carousel': 'Carousels', 'story': 'Stories'}


@hub_view
def posts_library(request):
    """Everything published on the connected accounts: imported history plus hub posts."""
    from django.db.models import OuterRef, Subquery, Value
    from django.db.models.functions import Coalesce
    from .models import PostMetric, PostTarget
    ctx = _ctx(request, 'posts')
    qs = (PostTarget.objects.filter(account__in=_accounts_in_view(ctx), status='published')
          .select_related('post__workspace', 'account').prefetch_related('metrics'))
    counts = {}
    for opts in qs.values_list('options', flat=True):
        k = (opts or {}).get('kind', 'post')
        counts[k] = counts.get(k, 0) + 1
    kind = request.GET.get('kind', '')
    if kind in KIND_LABELS:
        qs = qs.filter(options__kind=kind) if kind != 'post' else \
            qs.filter(Q(options__kind='post') | Q(options__kind__isnull=True))
    sort = request.GET.get('sort', 'new')
    if sort == 'top':
        eng = PostMetric.objects.filter(target=OuterRef('pk'), metric='engagement').values('value')[:1]
        qs = qs.annotate(eng=Coalesce(Subquery(eng), Value(0))).order_by('-eng', '-published_at')
    else:
        qs = qs.order_by('-published_at')
    page = Paginator(qs, 36).get_page(request.GET.get('page'))
    for t in page:
        t.m = {m.metric: m.value for m in t.metrics.all()}
        t.local = next(iter(t.post.ordered_media()), None) if t.post.source != 'import' else None
    ctx.update({
        'items': page, 'kind': kind, 'sort': sort, 'total': sum(counts.values()),
        'kinds': [(k, label, counts.get(k, 0)) for k, label in KIND_LABELS.items() if counts.get(k)],
        'has_accounts': _accounts_in_view(ctx).exists(),
    })
    return render(request, 'social/posts.html', ctx)


# ================================================================ approvals

@hub_view
def approvals(request):
    ctx = _ctx(request, 'approvals')
    base = Post.objects.filter(workspace__in=ctx['in_view']).select_related('workspace') \
        .prefetch_related('targets__account')
    if ctx['platform']:
        base = base.filter(targets__account__platform=ctx['platform']).distinct()
    soon = timezone.now() + timedelta(days=7)
    lists = {
        'review': base.filter(status='review').order_by('scheduled_at'),
        'changes': base.filter(status='changes').order_by('scheduled_at'),
        # Claude only ever drafts, so its posts sit here until someone sends them on.
        'drafts': base.filter(status='draft').order_by('scheduled_at')[:30],
        'upcoming': base.filter(status='scheduled', scheduled_at__lte=soon).order_by('scheduled_at')[:20],
    }
    lists = {k: [_post_card(p) for p in qs] for k, qs in lists.items()}
    labels = {'review': 'Waiting for approval', 'changes': 'Changes requested',
              'drafts': 'Drafts', 'upcoming': 'Going out this week'}
    empty = {'review': 'Nothing is waiting for approval.', 'changes': 'No posts were sent back.',
             'drafts': 'No drafts. Posts Claude writes land here until someone sends them for approval.',
             'upcoming': 'Nothing approved for the next 7 days.'}
    # Open on the tab asked for, else the first one with something in it.
    tab = request.GET.get('tab')
    if tab not in lists:
        tab = next((k for k in lists if lists[k]), 'review')
    ctx.update({
        'tabs': [{'key': k, 'label': labels[k], 'count': len(v), 'on': k == tab} for k, v in lists.items()],
        'posts': lists[tab], 'empty_text': empty[tab],
        'link_workspaces': [w for w in ctx['in_view'] if w.requires_approval],
    })
    return render(request, 'social/approvals.html', ctx)


# ================================================================ inbox

@hub_view
def inbox(request):
    ctx = _ctx(request, 'inbox')
    status = request.GET.get('status', 'open')
    items = (InboxItem.objects.filter(account__in=_accounts_in_view(ctx))
             .select_related('account__workspace', 'assigned_to').prefetch_related('replies'))
    counts = {'open': items.filter(status='open').count(), 'done': items.filter(status='done').count(),
              'mine': items.filter(status='open', assigned_to=request.user).count()}
    if status == 'mine':
        items = items.filter(status='open', assigned_to=request.user)
    else:
        status = status if status in ('open', 'done') else 'open'
        items = items.filter(status=status)
    page = Paginator(items, 40).get_page(request.GET.get('page'))
    for it in page:
        replies = list(it.replies.all())
        it.draft = next((r for r in reversed(replies) if r.status == 'draft'), None)
        it.sent = [r for r in replies if r.status == 'sent']
        it.meta = PLATFORM_META[it.account.platform]
        if it.kind == 'email':
            it.subject = (it.raw or {}).get('subject') or it.text.split('\n', 1)[0]
            body = it.text[len(it.subject):] if it.text.startswith(it.subject) else it.text
            it.body = body.strip()
            it.snippet = ' '.join(it.body.split())[:140]
    if ctx['platform'] == 'email':
        # Mail layout: a list on the left, the open email on the right.
        chosen = request.GET.get('item')
        selected = next((it for it in page if str(it.pk) == chosen), None) or (page[0] if page else None)
        ctx.update({'items': page, 'status': status, 'counts': counts, 'selected': selected})
        return render(request, 'social/inbox_email.html', ctx)
    columns = {}
    for it in page:
        columns.setdefault(it.account.platform, []).append(it)
    streams = [{'platform': p, 'label': PLATFORM_LABELS[p], 'meta': PLATFORM_META[p], 'items': columns[p],
                'sub': {'facebook': 'Comments & Messenger', 'instagram': 'Comments & DMs', 'linkedin': 'Page comments',
                        'youtube': 'Video comments', 'x': 'Mentions', 'whatsapp': 'Customer messages',
                        'google_business': 'Reviews', 'email': 'Emails'}[p]}
               for p in PLATFORM_ORDER if p in columns]
    ctx.update({'items': page, 'streams': streams, 'status': status, 'counts': counts})
    return render(request, 'social/inbox.html', ctx)


@hub_view
@require_POST
def inbox_action(request, pk):
    item = get_object_or_404(InboxItem.objects.select_related('account__workspace'), pk=pk)
    action, text = request.POST.get('action'), request.POST.get('text', '')
    if action == 'send':
        S.send_reply(request.user, item, text)
        messages.success(request, f'Reply sent to {item.author_name or "them"}.')
    elif action == 'draft':
        S.draft_reply(request.user, item, text)
        messages.success(request, 'Draft saved.')
    elif action == 'discard':
        S.require(request.user, item.account.workspace)
        item.replies.filter(status='draft').delete()
    elif action == 'ai_draft':
        from .ai import draft_reply_text
        S.require(request.user, item.account.workspace)
        text = draft_reply_text(item)
        if text:
            item.replies.filter(status='draft').delete()
            S.draft_reply(request.user, item, text, source='ai')
            messages.success(request, 'AI reply written. Read it, edit if needed, then Send.')
        else:
            messages.info(request, 'The AI thinks this one needs no reply (spam or an automatic notice). '
                                   'Mark it Done, or write a reply yourself.')
    elif action in ('done', 'open'):
        S.set_item_status(request.user, item, action)
    elif action == 'assign_me':
        S.assign_item(request.user, item, request.user)
    elif action == 'unassign':
        S.assign_item(request.user, item, None)
    elif action == 'template':
        S.require(request.user, item.account.workspace)
        adapter = get_adapter(item.account.platform)
        try:
            adapter.send_template(item.account, item.author_id, request.POST.get('template', 'hello_world'))
        except (AdapterError, AttributeError) as exc:
            raise S.SocialError(getattr(exc, 'message', str(exc)))
        S.audit(item.account.workspace, 'reply.template', item.author_name, user=request.user)
        messages.success(request, 'Template sent.')
    from core.security import safe_next
    return redirect(safe_next(request, request.META.get('HTTP_REFERER'), reverse('social:inbox')))


# ================================================================ website (GA4 + Search Console)

@hub_view
def website(request):
    """ralfiz.com visitors, leads and Google searches. Owners only: it is Ralfiz's own site."""
    from . import website as W
    if not S.is_social_admin(request.user):
        raise PermissionDenied
    ctx = _ctx(request, 'website')
    days = int(request.GET.get('days', 30)) if request.GET.get('days', '30').isdigit() else 30
    days = days if days in (7, 30, 90) else 30
    action = request.POST.get('action') if request.method == 'POST' else None
    data = W.report(days, refresh=action == 'refresh') if W.is_configured() else None
    kpis = (data['ga']['kpis'] if data and data['ga'] else []) + (data['gsc']['kpis'] if data and data['gsc'] else [])
    ideas_key = f'social:website:ideas:{days}'
    if action == 'ideas' and data:
        from .ai import website_ideas
        cache.set(ideas_key, website_ideas(W.summary_text(data, days), settings.WEBSITE_LABEL), 24 * 3600)
        return redirect(f"{reverse('social:website')}?days={days}#ideas")
    chart = {}
    if data and data['ga']:
        chart.update(labels=data['ga']['labels'], users=data['ga']['series'], views=data['ga']['views_series'])
    if data and data['gsc']:
        chart.setdefault('labels', data['gsc']['labels'])
        chart.update(clicks=data['gsc']['clicks_series'], shown=data['gsc']['shown_series'])
    chart['units'] = {'users': 'visitors', 'views': 'page views', 'clicks': 'clicks from Google',
                      'shown': 'times shown in Google'}
    ctx.update({'days': days, 'data': data, 'kpis': kpis, 'site_label': settings.WEBSITE_LABEL,
                'sparks': {k['key']: k['spark'] for k in kpis}, 'chart': chart,
                'ga_has_visits': bool(data and data['ga'] and data['ga']['sessions']),
                'tips': W.tips(data) if data else [], 'ideas': _md_list(cache.get(ideas_key) or ''),
                'donut': _donut(data['ga']['channels']) if data and data['ga'] else None})
    return render(request, 'social/website.html', ctx)


DONUT_COLORS = ('#FF2E88', '#9B4DFF', '#3D8BFF', '#FF7A3D', '#3EF0A0', '#2EE6D6', '#FFC93D', '#94A3B8')


def _donut(channels):
    """A conic-gradient donut: each channel's share of visits."""
    total = sum(c['sessions'] for c in channels)
    if not total:
        return None
    stops, at, legend = [], 0.0, []
    for i, c in enumerate(channels[:8]):
        share = 100 * c['sessions'] / total
        color = DONUT_COLORS[i % len(DONUT_COLORS)]
        stops.append(f'{color} {at:.2f}% {at + share:.2f}%')
        legend.append({**c, 'color': color, 'share': round(share)})
        at += share
    return {'gradient': ', '.join(stops), 'legend': legend, 'total': total}


def _md_list(text):
    """The AI's numbered Markdown list as safe items: [(title, body)]. Everything is escaped."""
    import re
    from django.utils.html import escape
    items = []
    for block in re.split(r'\n\s*(?=\d+[.)]\s)', '\n' + (text or '').strip()):
        block = re.sub(r'^\s*\d+[.)]\s*', '', block).strip()
        if not block:
            continue
        m = re.match(r'\*\*(.+?)\*\*[:.\s-]*(.*)', block, re.S)
        title, body = (m.group(1), m.group(2)) if m else ('', block)
        body = re.sub(r'\*\*(.+?)\*\*', r'\1', body)
        items.append((escape(title.strip().rstrip(':')), escape(' '.join(body.split()))))
    return items


# ================================================================ analytics

@hub_view
def analytics(request):
    ctx = _ctx(request, 'analytics')
    days = int(request.GET.get('days', 30)) if request.GET.get('days', '30').isdigit() else 30
    days = days if days in (7, 30, 90) else 30
    end = timezone.localdate()
    start = end - timedelta(days=days - 1)
    accounts = list(_accounts_in_view(ctx))
    if request.method == 'POST':
        for a in accounts:
            S.require(request.user, a.workspace)
            S.sync_insights(a, days=days)
            S.sync_post_metrics(a)
        messages.success(request, 'Analytics refreshed from the platforms.')
        return redirect(request.get_full_path())
    data = S.analytics(accounts, start, end)
    prev = S.analytics(accounts, start - timedelta(days=days), start - timedelta(days=1))
    kpis = []
    for key, label in (('reach', 'Reach'), ('impressions', 'Impressions'), ('engagement', 'Engagement'),
                       ('clicks', 'Clicks')):
        now_v, before = data['totals'][key], prev['totals'][key]
        change = round(100 * (now_v - before) / before, 1) if before else None
        kpis.append({'label': label, 'value': now_v, 'change': change, 'key': key,
                     'spark': data['series'][key][-30:]})
    peak = max(data['by_platform'].values() or [0])
    ctx.update({
        'days': days, 'kpis': kpis, 'data': data, 'engagement_rate': data['engagement_rate'],
        'chart': {'labels': [d.strftime('%d %b') for d in data['days']],
                  'reach': data['series']['reach'], 'engagement': data['series']['engagement']},
        'by_platform': [(p, PLATFORM_LABELS.get(p, p), v, round(100 * v / peak) if peak else 0,
                         PLATFORM_META.get(p, {})) for p, v in data['by_platform'].items()],
        'sparks': {k['key']: k['spark'] for k in kpis},
        'best': S.best_times(accounts), 'slots': ['6am', '9am', '12pm', '3pm', '6pm', '9pm'],
        'daynames': S.DAYS, 'has_accounts': bool(accounts),
    })
    return render(request, 'social/analytics.html', ctx)


# ================================================================ reports

@hub_view
def reports(request):
    ctx = _ctx(request, 'reports')
    today = timezone.localdate()
    months, m = [], today.replace(day=1)
    for _ in range(6):
        months.append(m)
        m = (m - timedelta(days=1)).replace(day=1)
    ctx.update({'months': months, 'this_month': today.replace(day=1)})
    return render(request, 'social/reports.html', ctx)


@hub_view
def report_pdf(request, ws, month):
    workspace = get_object_or_404(Workspace, pk=ws)
    S.require(request.user, workspace)
    start = _month_arg(month)
    end = start.replace(day=cal.monthrange(start.year, start.month)[1])
    pdf = render_report_pdf(workspace, start, end, request)
    S.audit(workspace, 'report.download', f'{start:%B %Y}', user=request.user)
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="{workspace.name} {start:%Y-%m} social report.pdf"'
    return resp


def render_report_pdf(workspace, start, end, request=None):
    from django.template.loader import render_to_string
    from weasyprint import HTML

    from core.models import CompanySettings
    accounts = list(workspace.accounts.all())
    data = S.analytics(accounts, start, end)
    prev_end = start - timedelta(days=1)
    prev = S.analytics(accounts, prev_end.replace(day=1), prev_end)
    published = (Post.objects.filter(workspace=workspace, status__in=('published', 'partial'),
                                     scheduled_at__date__gte=start, scheduled_at__date__lte=end)
                 .prefetch_related('targets__account'))
    rows = []
    for key, label in (('reach', 'Reach'), ('impressions', 'Impressions'), ('engagement', 'Engagement'),
                       ('clicks', 'Link clicks'), ('views', 'Video views')):
        now_v, before = data['totals'][key], prev['totals'][key]
        rows.append({'label': label, 'value': now_v,
                     'change': round(100 * (now_v - before) / before, 1) if before else None})
    peak = max(data['by_platform'].values() or [0])
    html = render_to_string('social/report_pdf.html', {
        'workspace': workspace, 'start': start, 'end': end, 'rows': rows, 'data': data,
        'company': CompanySettings.get_settings(), 'posts_count': published.count(),
        'by_platform': [(PLATFORM_LABELS.get(p, p), v, round(100 * v / peak) if peak else 0,
                         PLATFORM_META.get(p, {}).get('color', '#64748b'))
                        for p, v in data['by_platform'].items()],
        'accounts': accounts, 'font_dir': (settings.BASE_DIR / 'static' / 'certificates' / 'fonts').as_uri(),
        'best': S.best_times(accounts), 'generated': timezone.localtime(),
    })
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()


# ================================================================ media

@hub_view
def media_library(request):
    ctx = _ctx(request, 'media')
    if request.method == 'POST':
        ws = get_object_or_404(Workspace, pk=request.POST.get('workspace'))
        if request.POST.get('url'):
            S.save_media_from_url(request.user, ws, request.POST['url'].strip())
            n = 1
        else:
            files = request.FILES.getlist('files')
            for f in files:
                S.save_media(request.user, ws, f, tags=request.POST.get('tags', ''))
            n = len(files)
        if request.headers.get('x-requested-with') == 'fetch':
            assets = ws.media.all()[:n]
            return JsonResponse({'ok': True, 'assets': [
                {'id': str(a.pk), 'url': a.file.url, 'kind': a.kind, 'name': a.name} for a in assets]})
        messages.success(request, f'Added {n} file{"s" if n != 1 else ""}.')
        return redirect('social:media')
    tag = request.GET.get('tag', '')
    assets = MediaAsset.objects.filter(workspace__in=ctx['in_view']).select_related('workspace') \
        .annotate(uses=Count('posts'))
    if tag:
        assets = assets.filter(tags__icontains=tag)
    tags = sorted({t.strip() for ts in MediaAsset.objects.filter(workspace__in=ctx['in_view'])
                   .values_list('tags', flat=True) for t in ts.split(',') if t.strip()})
    ctx.update({'assets': Paginator(assets, 48).get_page(request.GET.get('page')), 'tags': tags,
                'tag': tag})
    return render(request, 'social/media.html', ctx)


@hub_view
@require_POST
def media_delete(request, pk):
    asset = get_object_or_404(MediaAsset, pk=pk)
    S.require(request.user, asset.workspace)
    if asset.posts.exclude(status__in=('published', 'partial', 'failed')).exists():
        raise S.SocialError('That file is used by a post that has not gone out yet.')
    S.audit(asset.workspace, 'media.delete', asset.name, user=request.user)
    asset.file.delete(save=False)
    asset.delete()
    messages.success(request, 'File removed.')
    return redirect('social:media')


def media_file(request, token):
    """Signed, expiring media URL that platforms fetch when publishing. No login."""
    asset = S.asset_from_token(token)
    if asset is None:
        raise Http404
    ct = asset.content_type if asset.content_type in {*S.IMAGE_TYPES.values(), *S.VIDEO_TYPES.values()} \
        else 'application/octet-stream'
    resp = FileResponse(asset.file.open('rb'), content_type=ct)
    resp['X-Content-Type-Options'] = 'nosniff'
    resp['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return resp


# ================================================================ accounts & connecting

@hub_view
def accounts(request):
    ctx = _ctx(request, 'accounts')
    groups = []
    for w in ctx['in_view']:
        accs = list(w.accounts.all())
        for a in accs:
            a.meta = PLATFORM_META[a.platform]
            q = get_adapter(a.platform).quota_status(a, S.published_last_24h(a))
            a.quota = {'used': q[0], 'limit': q[1], 'pct': min(100, round(100 * q[0] / q[1]))} if q else None
        groups.append((w, accs))
    connectors = []
    for p in PLATFORM_ORDER:
        adapter = get_adapter(p)
        connectors.append({'platform': p, 'label': PLATFORM_LABELS[p], 'meta': PLATFORM_META[p],
                           'ready': adapter.is_configured(), 'fake': adapter.connect_mode == 'fake',
                           'needs': ', '.join(REAL[p].required_settings)})
    ctx.update({'groups': groups, 'connectors': connectors})
    return render(request, 'social/accounts.html', ctx)


def _redirect_uri(platform):
    return f"{settings.SOCIAL_PUBLIC_BASE_URL.rstrip('/')}{reverse('social:oauth_callback', args=[platform])}"


@hub_view
def connect_start(request, platform):
    if platform not in PLATFORM_LABELS:
        raise Http404
    workspace = get_object_or_404(Workspace, pk=request.GET.get('ws'))
    S.require(request.user, workspace, 'manager')
    adapter = get_adapter(platform)
    if adapter.connect_mode == 'fake':
        return _hold_candidates(request, workspace, platform, [adapter.demo_candidate(workspace.name)])
    if platform == 'whatsapp' and REAL['whatsapp'].embedded_ready():
        return redirect(f"{reverse('social:connect_whatsapp')}?ws={workspace.pk}")
    if adapter.connect_mode == 'manual':
        return redirect(f"{reverse('social:connect_manual', args=[platform])}?ws={workspace.pk}")
    if not adapter.is_configured():
        raise S.SocialError(f'{adapter.label} is not set up yet. Add {", ".join(adapter.required_settings)} '
                            f'to the server settings.')
    nonce = secrets.token_urlsafe(16)
    request.session['social_oauth'] = {'nonce': nonce, 'ws': str(workspace.pk), 'platform': platform}
    challenge = None
    if adapter.uses_pkce:
        verifier = secrets.token_urlsafe(64)
        request.session['social_oauth']['verifier'] = verifier
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    state = signing.dumps({'n': nonce, 'p': platform}, salt='social-oauth')
    return redirect(adapter.authorize_url(state, _redirect_uri(platform), challenge))


@hub_view
def oauth_callback(request, platform):
    held = request.session.pop('social_oauth', None)
    try:
        state = signing.loads(request.GET.get('state', ''), salt='social-oauth', max_age=900)
    except signing.BadSignature:
        state = None
    if not held or not state or state['n'] != held['nonce'] or state['p'] != platform or \
            held['platform'] != platform:
        raise S.SocialError('That sign-in link expired or did not come from here. Try connecting again.')
    if request.GET.get('error'):
        raise S.SocialError(f'{PLATFORM_LABELS[platform]} sign-in was cancelled: '
                            f'{request.GET.get("error_description") or request.GET["error"]}')
    workspace = get_object_or_404(Workspace, pk=held['ws'])
    S.require(request.user, workspace, 'manager')
    try:
        candidates = get_adapter(platform).exchange_code(
            request.GET.get('code', ''), _redirect_uri(platform), held.get('verifier'))
    except AdapterError as exc:
        raise S.SocialError(exc.message)
    if not candidates:
        raise S.SocialError(f'No {PLATFORM_LABELS[platform]} pages or accounts were found that you manage.')
    return _hold_candidates(request, workspace, platform, candidates)


def _hold_candidates(request, workspace, platform, candidates):
    """Keep found accounts (tokens encrypted) in the session until the user picks."""
    request.session['social_candidates'] = {
        'ws': str(workspace.pk), 'platform': platform,
        'items': [{'external_id': c.external_id, 'name': c.name, 'handle': c.handle,
                   'avatar_url': c.avatar_url, 'token': encrypt(c.token),
                   'refresh_token': encrypt(c.refresh_token),
                   'expires_at': c.expires_at.isoformat() if c.expires_at else None, 'extra': c.extra}
                  for c in candidates],
    }
    return redirect('social:connect_pick')


@hub_view
def connect_pick(request):
    from .adapters.base import AccountCandidate
    held = request.session.get('social_candidates')
    if not held:
        return redirect('social:accounts')
    workspace = get_object_or_404(Workspace, pk=held['ws'])
    S.require(request.user, workspace, 'manager')
    if request.method == 'POST':
        chosen = set(request.POST.getlist('pick'))
        cands = [AccountCandidate(
            external_id=i['external_id'], name=i['name'], handle=i['handle'], avatar_url=i['avatar_url'],
            token=decrypt(i['token']), refresh_token=decrypt(i['refresh_token']),
            expires_at=datetime.fromisoformat(i['expires_at']) if i['expires_at'] else None,
            extra=i['extra']) for i in held['items'] if i['external_id'] in chosen]
        if not cands:
            raise S.SocialError('Pick at least one account.')
        saved = S.connect_candidates(request.user, workspace, held['platform'], cands)
        request.session.pop('social_candidates', None)
        for acc in saved:
            try:
                S.sync_account(acc, first=True)  # inbox, last 90 days of posts, 30 days of stats
            except AdapterError:
                pass
        messages.success(request, f'Connected {", ".join(a.name for a in saved)}.')
        return redirect('social:accounts')
    ctx = _ctx(request, 'accounts', held=held, workspace=workspace,
               platform_label=PLATFORM_LABELS[held['platform']], meta=PLATFORM_META[held['platform']])
    return render(request, 'social/connect_pick.html', ctx)


@hub_view
def connect_manual(request, platform):
    adapter = get_adapter(platform)
    if adapter.connect_mode not in ('manual', 'fake'):
        raise Http404
    workspace = get_object_or_404(Workspace, pk=request.GET.get('ws') or request.POST.get('ws'))
    S.require(request.user, workspace, 'manager')
    fields = getattr(REAL[platform], 'manual_fields', [])
    if request.method == 'POST':
        data = {name: request.POST.get(name, '').strip() for name, _, _ in fields}
        try:
            cands = adapter.manual_connect(data) if adapter.connect_mode == 'manual' else \
                [adapter.demo_candidate(workspace.name)]
        except AdapterError as exc:
            raise S.SocialError(exc.message)
        return _hold_candidates(request, workspace, platform, cands)
    return render(request, 'social/connect_manual.html',
                  _ctx(request, 'accounts', fields=fields, workspace=workspace,
                       platform_label=PLATFORM_LABELS[platform], platform_key=platform))


@hub_view
def connect_whatsapp(request):
    """WhatsApp Embedded Signup: Meta's popup, then the popup's code is finished here.

    Coexistence keeps the number working in the WhatsApp Business app on the phone.
    """
    adapter = REAL['whatsapp']
    if not adapter.embedded_ready():
        raise Http404
    workspace = get_object_or_404(Workspace, pk=request.GET.get('ws') or request.POST.get('ws'))
    S.require(request.user, workspace, 'manager')
    if request.method == 'POST':
        try:
            body = json.loads(request.body or b'{}')
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'Bad request.'}, status=400)
        try:
            cands = adapter.embedded_connect(body.get('code', ''), str(body.get('phone_number_id', '')),
                                             str(body.get('waba_id', '')),
                                             coexistence=bool(body.get('coexistence', True)))
        except AdapterError as exc:
            return JsonResponse({'ok': False, 'error': exc.message}, status=400)
        _hold_candidates(request, workspace, 'whatsapp', cands)
        return JsonResponse({'ok': True, 'next': reverse('social:connect_pick')})
    resp = render(request, 'social/connect_whatsapp.html', _ctx(
        request, 'accounts', workspace=workspace, app_id=wa_app()[0],
        config_id=settings.META_WHATSAPP_CONFIG_ID, graph_version=settings.META_GRAPH_VERSION or 'v23.0'))
    # Facebook's login popup talks back to this page; the default same-origin policy cuts it off.
    resp['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
    return resp


@hub_view
@require_POST
def account_action(request, pk):
    acc = get_object_or_404(SocialAccount, pk=pk)
    action = request.POST.get('action')
    if action == 'disconnect':
        S.disconnect(request.user, acc)
        messages.success(request, f'{acc.name} disconnected.')
    elif action == 'sync':
        S.require(request.user, acc.workspace)
        n, p = S.sync_account(acc, first=not acc.targets.filter(post__source='import').exists())
        S.sync_post_metrics(acc)
        messages.success(request, f'Synced {acc.name}: {p} new post{"s" if p != 1 else ""}, '
                                  f'{n} new inbox item{"s" if n != 1 else ""}.')
    elif action == 'delete':
        S.require(request.user, acc.workspace, 'manager')
        if acc.targets.filter(status__in=('pending', 'publishing')).exists():
            raise S.SocialError('Scheduled posts still use this account.')
        S.audit(acc.workspace, 'account.delete', acc.name, user=request.user)
        acc.delete()
        messages.success(request, 'Account removed.')
    return redirect('social:accounts')


# ================================================================ activity

@hub_view
def activity(request):
    ctx = _ctx(request, 'activity')
    logs = AuditLog.objects.filter(workspace__in=ctx['in_view']).select_related('workspace', 'user')
    via = request.GET.get('via', '')
    if via in ('web', 'mcp', 'link', 'worker'):
        logs = logs.filter(via=via)
    ctx.update({'logs': Paginator(logs, 60).get_page(request.GET.get('page')), 'via': via})
    return render(request, 'social/activity.html', ctx)


# ================================================================ workspaces (clients)

@hub_view
def workspaces(request):
    ctx = _ctx(request, 'clients')
    if not S.is_social_admin(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        f = request.POST
        ws = get_object_or_404(Workspace, pk=f['id']) if f.get('id') else Workspace()
        if f.get('action') == 'add_member':
            user = get_user_model().objects.filter(Q(username__iexact=f.get('who', '').strip()) |
                                                   Q(email__iexact=f.get('who', '').strip())).first()
            if not user:
                raise S.SocialError('No login found with that username or email.')
            Membership.objects.update_or_create(user=user, workspace=ws, defaults={'role': f.get('role', 'editor')})
            messages.success(request, f'{user.get_full_name() or user.username} can now work on {ws.name}.')
            return redirect('social:workspaces')
        if f.get('action') == 'remove_member':
            Membership.objects.filter(pk=f.get('member'), workspace=ws).delete()
            return redirect('social:workspaces')
        if f.get('action') == 'new_link':
            ws.review_token = secrets.token_urlsafe(24)
            ws.save(update_fields=['review_token'])
            messages.success(request, 'New review link made. The old one no longer works.')
            return redirect('social:workspaces')
        client = Client.objects.filter(pk=f.get('client')).first() if f.get('client') else None
        ws.name = f.get('name', '').strip() or (client.company_name or client.name if client else '')
        if not ws.name:
            raise S.SocialError('Give the client a name.')
        ws.client, ws.color = client, f.get('color') or ws.color
        ws.requires_approval = f.get('requires_approval') == 'on'
        ws.reviewer_name = f.get('reviewer_name', '').strip()
        ws.brand_kit = {'hashtags': f.get('hashtags', '').strip(), 'tone': f.get('tone', '').strip()}
        ws.save()
        S.audit(ws, 'workspace.save', ws.name, user=request.user)
        messages.success(request, f'{ws.name} saved.')
        return redirect('social:workspaces')
    used = Workspace.objects.exclude(client=None).values_list('client_id', flat=True)
    ctx.update({
        'all_ws': Workspace.objects.prefetch_related('memberships__user', 'accounts'),
        'clients': Client.objects.filter(is_active=True).exclude(pk__in=used).order_by('name'),
        'review_base': settings.SOCIAL_PUBLIC_BASE_URL.rstrip('/'),
    })
    return render(request, 'social/workspaces.html', ctx)


# ================================================================ client review link (public)

def review(request, token):
    workspace = get_object_or_404(Workspace, review_token=token, is_active=True)
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=request.POST.get('post'), workspace=workspace)
        name = request.POST.get('name', '').strip()[:120] or workspace.reviewer_name or 'Client'
        request.session['social_reviewer'] = name
        try:
            if request.POST.get('decision') == 'approve':
                S.approve(post, reviewer_name=name, via='link', comment=request.POST.get('comment', ''))
                messages.success(request, 'Approved. Thank you!')
            else:
                S.request_changes(post, reviewer_name=name, via='link',
                                  comment=request.POST.get('comment', ''))
                messages.success(request, 'Sent back to the Ralfiz team with your note.')
        except S.SocialError as exc:
            messages.error(request, str(exc))
        return redirect('social:review', token=token)
    waiting = [_post_card(p) for p in workspace.posts.filter(status='review')
               .prefetch_related('targets__account').order_by('scheduled_at')]
    recent = [_post_card(p) for p in workspace.posts.filter(
        status__in=('scheduled', 'changes', 'published')).prefetch_related('targets__account')
        .order_by('-updated_at')[:8]]
    return render(request, 'social/review.html', {
        'workspace': workspace, 'waiting': waiting, 'recent': recent, 'platform_meta': PLATFORM_META,
        'reviewer': request.session.get('social_reviewer', workspace.reviewer_name),
    })


@csrf_exempt
def meta_webhook(request):
    from .webhooks import meta_webhook as handler
    return handler(request)
