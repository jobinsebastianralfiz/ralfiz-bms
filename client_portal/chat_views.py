"""Live support chat between a client (portal) and the Ralfiz team (staff inbox).

No websockets: both sides poll small JSON endpoints every few seconds, which works on the
plain gunicorn deploy. Every message is kept, so the whole conversation stays as history.
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from core.models import Client
from .middleware import client_only
from .models import SupportMessage
from .web_views import client_required, _base_context

HISTORY = 200      # messages sent on first load
MAX_LEN = 4000


def _after(request):
    return parse_datetime(request.GET.get('after') or '')


def _clean_body(request):
    return (request.POST.get('body') or '').strip()[:MAX_LEN]


# ─── Client side (/portal/chat/...) ─────────────────────────────

def client_unread(client):
    return SupportMessage.objects.filter(client=client, from_client=False, read_at__isnull=True).count()


def _client_feed(client, after, mark_read):
    qs = SupportMessage.objects.filter(client=client).select_related('sender', 'client')
    if after:
        msgs = list(qs.filter(created_at__gt=after))
    else:
        msgs = list(qs.order_by('-created_at')[:HISTORY])[::-1]
    if mark_read:
        SupportMessage.objects.filter(client=client, from_client=False, read_at__isnull=True).update(read_at=timezone.now())
    return {'messages': [m.as_dict() for m in msgs], 'unread': client_unread(client)}


@client_required
def portal_chat(request):
    """Full-page chat with the whole history."""
    ctx = _base_context(request, 'chat')
    ctx['chat_full'] = True
    return render(request, 'client_portal/chat.html', ctx)


@client_required
def portal_chat_poll(request):
    return JsonResponse(_client_feed(request.client, _after(request), request.GET.get('open') == '1'))


@client_required
@require_POST
def portal_chat_send(request):
    body = _clean_body(request)
    if not body:
        return JsonResponse({'detail': 'Write a message first.'}, status=400)
    m = SupportMessage.objects.create(client=request.client, sender=request.user, from_client=True, body=body)
    return JsonResponse({'message': m.as_dict()})


# ─── Staff side (/support-chat/...) ─────────────────────────────

def staff_required(view):
    """Signed-in business users only: not client logins, not interns/employees."""
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        from core.views import _staff_portal_user
        if client_only(request.user) or _staff_portal_user(request.user):
            return HttpResponseForbidden('Not available.')
        return view(request, *args, **kwargs)
    return wrapper


def _conversations():
    return (Client.objects.filter(support_messages__isnull=False)
            .annotate(last_at=Max('support_messages__created_at'),
                      unread=Count('support_messages', filter=Q(support_messages__from_client=True,
                                                                support_messages__read_at__isnull=True)))
            .order_by('-last_at'))


def recent_conversations(limit=None):
    """Conversations newest first, each with `.last_message` and `.unread` (client messages not yet read)."""
    convos = _conversations()
    convos = list(convos[:limit] if limit else convos)
    for c in convos:
        c.last_message = SupportMessage.objects.filter(client=c).order_by('-created_at').first()
    return convos


@staff_required
def inbox(request, client_id=None):
    convos = recent_conversations()
    current = None
    if client_id:
        current = get_object_or_404(Client, pk=client_id)
    elif convos:
        current = convos[0]
    # Clients with a portal login, so staff can start a chat with anyone who can read it.
    startable = Client.objects.filter(user__isnull=False).exclude(
        pk__in=[c.pk for c in convos]).order_by('name')
    return render(request, 'client_portal/staff_chat.html', {
        'convos': convos, 'current': current, 'startable': startable,
    })


@staff_required
def staff_poll(request, client_id):
    client = get_object_or_404(Client, pk=client_id)
    after = _after(request)
    qs = SupportMessage.objects.filter(client=client).select_related('sender', 'client')
    msgs = list(qs.filter(created_at__gt=after)) if after else list(qs.order_by('-created_at')[:HISTORY])[::-1]
    if request.GET.get('open') == '1':
        SupportMessage.objects.filter(client=client, from_client=True, read_at__isnull=True).update(read_at=timezone.now())
    # Has the client seen our replies? Lets the page show "Seen".
    last_ours = qs.filter(from_client=False).order_by('-created_at').first()
    return JsonResponse({'messages': [m.as_dict() for m in msgs],
                         'seen': bool(last_ours and last_ours.read_at)})


@staff_required
@require_POST
def staff_send(request, client_id):
    client = get_object_or_404(Client, pk=client_id)
    body = _clean_body(request)
    if not body:
        return JsonResponse({'detail': 'Write a message first.'}, status=400)
    m = SupportMessage.objects.create(client=client, sender=request.user, from_client=False, body=body)
    return JsonResponse({'message': m.as_dict()})


@staff_required
def alerts(request):
    """For the chime on every staff page (_chat_alerts.html).

    `after`: newest client message this browser has already announced. Without it the
    browser starts from now, so old messages never chime. `unread` feeds the sidebar badge.
    """
    unread_qs = SupportMessage.objects.filter(from_client=True, read_at__isnull=True)
    latest = SupportMessage.objects.filter(from_client=True).aggregate(m=Max('created_at'))['m']
    out = {'latest': (latest or timezone.now()).isoformat(), 'items': [],
           'unread': unread_qs.count()}
    after = _after(request)
    if after:
        new = (SupportMessage.objects.filter(from_client=True, created_at__gt=after,
                                             created_at__gte=timezone.now() - timezone.timedelta(days=1))
               .select_related('client').order_by('created_at'))
        groups = {}
        for m in new:
            g = groups.setdefault(m.client_id, {'client': m.client.name, 'count': 0, 'text': '',
                                                'url': f'/support-chat/{m.client_id}/'})
            g['count'] += 1
            g['text'] = m.body[:140]
        out['items'] = list(groups.values())
    return JsonResponse(out)
