"""Meta webhook: Page comments and Messenger, Instagram comments and DMs, WhatsApp messages,
and taps on the buttons comment-to-DM automations send.

One endpoint receives all three products (subscribe each in the app dashboard
to the same callback URL). Meta signs every POST with the app secret; anything
unsigned or wrongly signed is refused. Valid deliveries always get a 200, even
for accounts we do not know, or Meta backs off and eventually disables the
subscription.

Message and comment text is customer content: it is stored, never interpreted.
"""
import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .adapters.base import FetchedItem
from .adapters.meta import _parse_time
from .models import SocialAccount

log = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def meta_webhook(request):
    if request.method == 'GET':
        expected = getattr(settings, 'META_WEBHOOK_VERIFY_TOKEN', '')
        token = request.GET.get('hub.verify_token', '')
        if (request.GET.get('hub.mode') == 'subscribe' and expected
                and hmac.compare_digest(token.encode(), expected.encode())):
            return HttpResponse(request.GET.get('hub.challenge', ''), content_type='text/plain')
        return HttpResponseForbidden('Verification failed.')

    if not _signature_ok(request.body, request.headers.get('X-Hub-Signature-256', '')):
        return HttpResponseForbidden('Bad signature.')
    try:
        payload = json.loads(request.body or b'{}')
    except ValueError:
        return HttpResponse('ok')
    handle(payload)
    return HttpResponse('ok')


def _signature_ok(body, header):
    """Signed by the main Meta app, or by the separate WhatsApp app when there is one."""
    if not header.startswith('sha256='):
        return False
    for name in ('META_APP_SECRET', 'META_WHATSAPP_APP_SECRET'):
        secret = getattr(settings, name, '')
        if secret and hmac.compare_digest(hmac.new(secret.encode(), body, hashlib.sha256).hexdigest(),
                                          header[len('sha256='):]):
            return True
    return False


PARSERS = {}


def handle(payload):
    """Route each entry to its parser and store the items for every matching account."""
    from .services import ingest
    platform = {'page': 'facebook', 'instagram': 'instagram',
                'whatsapp_business_account': 'whatsapp'}.get(payload.get('object'))
    if not platform:
        return
    for entry in payload.get('entry') or []:
        try:
            batches = PARSERS[platform](entry)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError):
            log.warning('Unreadable %s webhook entry skipped', platform, exc_info=True)
            continue
        for external_id, items in batches:
            if not items:
                continue
            accounts = SocialAccount.objects.filter(platform=platform, external_id=external_id) \
                .exclude(status='disconnected')
            for account in accounts:
                ingest(account, items)
        if platform == 'whatsapp':
            _store_echoes(entry)
        else:
            _handle_postbacks(platform, entry)


def _messaging(entry):
    """Messenger / Instagram messaging events. Echoes are the business's own messages."""
    own, items = str(entry['id']), []
    for ev in entry.get('messaging') or []:
        msg, sender = ev.get('message'), str((ev.get('sender') or {}).get('id', ''))
        if not msg or msg.get('is_echo') or msg.get('is_deleted') or sender == own:
            continue
        items.append(FetchedItem(
            kind='dm', external_id=msg['mid'], text=msg.get('text') or '[attachment]',
            author_id=sender, thread_id=sender, received_at=_parse_time(ev.get('timestamp')), raw=ev))
    return items


def _postbacks(entry):
    """Button taps: (sender id, payload, message id) for each ``postback`` event."""
    for ev in entry.get('messaging') or []:
        pb = ev.get('postback')
        if pb and pb.get('payload'):
            yield (str((ev.get('sender') or {}).get('id', '')), pb['payload'],
                   pb.get('mid') or f"{ev.get('timestamp', '')}:{pb['payload']}")


def _handle_postbacks(platform, entry):
    from .automations import handle_postback
    try:
        taps = list(_postbacks(entry))
    except (KeyError, TypeError, ValueError, AttributeError):
        log.warning('Unreadable %s postback skipped', platform, exc_info=True)
        return
    if not taps:
        return
    for account in SocialAccount.objects.filter(platform=platform, external_id=str(entry.get('id', ''))) \
            .exclude(status='disconnected'):
        for sender, payload, mid in taps:
            handle_postback(account, sender, payload, mid)


def _page(entry):
    page, items = str(entry['id']), _messaging(entry)
    for change in entry.get('changes') or []:
        v = change.get('value') or {}
        who = v.get('from') or {}
        if (change.get('field') != 'feed' or v.get('item') != 'comment' or v.get('verb') != 'add'
                or str(who.get('id', '')) == page):
            continue
        items.append(FetchedItem(
            kind='comment', external_id=v['comment_id'], text=v.get('message', ''),
            author_name=who.get('name', ''), author_id=str(who.get('id', '')),
            thread_id=v.get('post_id', ''), received_at=_parse_time(v.get('created_time')), raw=v))
    return [(page, items)]


def _instagram(entry):
    ig, items = str(entry['id']), _messaging(entry)
    for change in entry.get('changes') or []:
        v = change.get('value') or {}
        who = v.get('from') or {}
        if change.get('field') not in ('comments', 'live_comments') or str(who.get('id', '')) == ig:
            continue
        items.append(FetchedItem(
            kind='comment', external_id=v['id'], text=v.get('text', ''),
            author_name=who.get('username', ''), author_id=str(who.get('id', '')),
            thread_id=(v.get('media') or {}).get('id', ''), raw=v))
    return [(ig, items)]


def _wa_text(m):
    kind = m.get('type')
    if kind == 'text':
        return (m.get('text') or {}).get('body', '')
    if kind == 'button':
        return (m.get('button') or {}).get('text', '')
    if kind == 'interactive':
        reply = m.get('interactive') or {}
        reply = reply.get('button_reply') or reply.get('list_reply') or {}
        return reply.get('title', '')
    if kind in ('image', 'video', 'document', 'audio', 'sticker'):
        caption = (m.get(kind) or {}).get('caption', '')
        return f'[{kind}] {caption}'.strip()
    return f'[{kind or "message"}]'


def _whatsapp(entry):
    """Incoming messages only; delivery/read ``statuses`` are ignored."""
    out = []
    for change in entry.get('changes') or []:
        v = change.get('value') or {}
        if change.get('field') != 'messages' or not v.get('messages'):
            continue
        names = {c.get('wa_id'): (c.get('profile') or {}).get('name', '') for c in v.get('contacts') or []}
        items = [FetchedItem(
            kind='dm', external_id=m['id'], text=_wa_text(m), author_name=names.get(m.get('from'), ''),
            author_id=m.get('from', ''), thread_id=m.get('from', ''),
            received_at=_parse_time(m.get('timestamp')), raw=m) for m in v['messages']]
        out.append((str(v['metadata']['phone_number_id']), items))
    return out


def _whatsapp_echoes(entry):
    """Coexistence: messages the business sent from the WhatsApp Business app on its phone
    arrive as ``smb_message_echoes``. Yields (phone_number_id, echo) pairs."""
    for change in entry.get('changes') or []:
        v = change.get('value') or {}
        if change.get('field') != 'smb_message_echoes':
            continue
        number_id = str((v.get('metadata') or {}).get('phone_number_id', ''))
        for m in v.get('message_echoes') or []:
            yield number_id, {'id': m.get('id', ''), 'to': m.get('to', ''), 'text': _wa_text(m),
                              'sent_at': _parse_time(m.get('timestamp'))}


def _store_echoes(entry):
    from .services import record_echo
    try:
        echoes = list(_whatsapp_echoes(entry))
    except (KeyError, TypeError, ValueError, AttributeError):
        log.warning('Unreadable WhatsApp echo skipped', exc_info=True)
        return
    for number_id, echo in echoes:
        for account in SocialAccount.objects.filter(platform='whatsapp', external_id=number_id) \
                .exclude(status='disconnected'):
            record_echo(account, echo)


PARSERS.update(facebook=_page, instagram=_instagram, whatsapp=_whatsapp)
