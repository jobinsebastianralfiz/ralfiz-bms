"""Comment-to-DM automations.

A new comment that matches an automation's keyword is queued here (from
``services.ingest``, so webhooks and inbox syncs both feed it). The worker then
sends the private reply DM first, since Meta only allows it for about a week,
and the public reply under the comment second. Each comment is queued once and
each person gets one DM per automation and post.
"""
import random
import re
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q
from django.utils import timezone

from .adapters import get_adapter
from .adapters.base import AdapterError, AuthError, RateLimited
from .models import Automation, AutomationRun, InboxReply, SocialAccount

PLATFORMS = ('facebook', 'instagram')
#: Meta stops accepting private replies about seven days after the comment.
REPLY_WINDOW = timedelta(days=7)
#: Well under Meta's messaging limits, so a viral reel cannot get the Page throttled.
HOURLY_LIMIT = 150
#: A run stuck in "sending" this long may already have sent its DM: never retry it.
STALE_LOCK = timedelta(minutes=10)
#: Button template text limit on Messenger and Instagram.
DM_MAX = 640


# ---------------------------------------------------------------- matching

def _norm(text):
    return ' '.join(text.casefold().split())


def matches(automation, text):
    text = _norm(text)
    for kw in automation.keywords:
        kw = _norm(kw)
        if not kw:
            continue
        if automation.match_type == 'exact':
            # "Skill 🔥" and "skill!" still count as just the keyword.
            if re.sub(r'^\W+|\W+$', '', text) == kw:
                return True
        elif re.search(rf'(?<!\w){re.escape(kw)}(?!\w)', text):
            return True
    return False


def queue_for(item):
    """Queue the first live automation this new comment matches. Returns the run or None."""
    if item.kind != 'comment' or item.account.platform not in PLATFORMS:
        return None
    now = timezone.now()
    for auto in item.account.automations.filter(is_active=True).order_by('created_at'):
        if not auto.is_live or (auto.post_id and auto.post_id != item.thread_id):
            continue
        # A first inbox sync pulls in weeks of old comments; only answer what came after
        # (with a minute of grace, as Meta timestamps are whole seconds).
        since = max(auto.created_at - timedelta(minutes=1), now - REPLY_WINDOW)
        if item.received_at < since:
            continue
        if not matches(auto, item.text):
            continue
        try:
            with transaction.atomic():
                return AutomationRun.objects.create(automation=auto, item=item,
                                                    commenter_id=item.author_id)
        except IntegrityError:          # already queued for this comment
            return None
    return None


# ---------------------------------------------------------------- managing

def _clean_list(raw):
    if isinstance(raw, str):
        raw = re.split(r'[\n,]', raw)
    return [x.strip() for x in raw or [] if x and x.strip()]


def save_automation(user, workspace, data, automation=None):
    """Create or update an automation from form or tool data."""
    from .services import SocialError, audit, require
    require(user, workspace, 'manager')
    account = SocialAccount.objects.filter(workspace=workspace, pk=data.get('account'),
                                           platform__in=PLATFORMS).first()
    if account is None:
        raise SocialError('Pick a connected Facebook Page or Instagram account.')
    keywords = _clean_list(data.get('keywords'))
    if not keywords:
        raise SocialError('Add at least one keyword.')
    dm_text = (data.get('dm_text') or '').strip()
    if not dm_text:
        raise SocialError('Write the DM people will get.')
    if len(dm_text) > DM_MAX:
        raise SocialError(f'The DM is {len(dm_text)} characters; Meta allows {DM_MAX}.')
    label, url = (data.get('button_label') or '').strip(), (data.get('button_url') or '').strip()
    if bool(label) != bool(url):
        raise SocialError('A button needs both a label and a link.')
    if len(label) > 20:
        raise SocialError('Button labels can be at most 20 characters.')
    if url and not url.startswith('https://'):
        raise SocialError('The button link must start with https://')
    a = automation or Automation(workspace=workspace, created_by=user)
    a.account, a.keywords, a.dm_text = account, keywords, dm_text
    a.name = (data.get('name') or '').strip()[:120] or f'{keywords[0].upper()} automation'
    a.post_id = (data.get('post_id') or '').strip()
    a.match_type = data.get('match_type') if data.get('match_type') in ('exact', 'contains') else 'contains'
    a.public_replies = _clean_list(data.get('public_replies') or '')
    a.button_label, a.button_url = label, url
    a.ends_at = data.get('ends_at') or None
    a.is_active = bool(data.get('is_active', True))
    a.save()
    audit(workspace, 'automation.save', f'{a.name}: {", ".join(keywords)}', user=user,
          via=data.get('via', 'web'), automation=str(a.pk))
    return a


def toggle(user, automation):
    from .services import audit, require
    require(user, automation.workspace, 'manager')
    automation.is_active = not automation.is_active
    automation.save(update_fields=['is_active'])
    audit(automation.workspace, 'automation.toggle',
          f'{automation.name} {"on" if automation.is_active else "off"}', user=user)
    return automation


# ---------------------------------------------------------------- sending

def _claim(run_id, now):
    return AutomationRun.objects.filter(pk=run_id, status='queued').update(
        status='sending', locked_at=now, attempts=F('attempts') + 1) == 1


def _sent_last_hour(account, now):
    return AutomationRun.objects.filter(automation__account=account, status='sent',
                                        sent_at__gte=now - timedelta(hours=1)).count()


def run_due(now=None, limit=50):
    """Worker job: send the queued DMs. Returns how many were sent."""
    now = now or timezone.now()
    AutomationRun.objects.filter(status='sending', locked_at__lt=now - STALE_LOCK).update(
        status='failed', error='Stopped part-way; not retried so nobody gets the DM twice.')
    due = (AutomationRun.objects.filter(status='queued', next_attempt_at__lte=now)
           .order_by('next_attempt_at').values_list('pk', flat=True)[:limit])
    sent = 0
    for run_id in list(due):
        if not _claim(run_id, now):
            continue
        run = AutomationRun.objects.select_related('automation__account', 'item').get(pk=run_id)
        sent += _send(run, now)
    return sent


def _retry(run, now, message, delay=None):
    if run.attempts >= run.MAX_ATTEMPTS:
        run.status, run.error = 'failed', message
    else:
        run.status, run.error = 'queued', message
        run.next_attempt_at = now + (delay or timedelta(minutes=2 ** run.attempts))
    run.save(update_fields=['status', 'error', 'next_attempt_at'])
    return 0


def _send(run, now):
    auto, item = run.automation, run.item
    account = auto.account
    if not auto.is_live:
        run.status, run.error = 'skipped', 'The automation was switched off before it sent.'
        run.save(update_fields=['status', 'error'])
        return 0
    if not account.healthy:
        run.status, run.error = 'failed', f'{account.name} needs reconnecting.'
        run.save(update_fields=['status', 'error'])
        return 0
    if item.received_at < now - REPLY_WINDOW:
        run.status, run.error = 'skipped', 'The comment is too old for Meta to allow a DM.'
        run.save(update_fields=['status', 'error'])
        return 0
    already = AutomationRun.objects.filter(
        automation=auto, commenter_id=run.commenter_id, item__thread_id=item.thread_id,
        status='sent').exclude(pk=run.pk)
    if run.commenter_id and already.exists():
        run.status, run.error = 'skipped', 'This person already got the DM for this post.'
        run.save(update_fields=['status', 'error'])
        return 0
    if _sent_last_hour(account, now) >= HOURLY_LIMIT:
        run.attempts -= 1               # waiting for the limit is not a failed attempt
        run.save(update_fields=['attempts'])
        return _retry(run, now, 'Hourly DM limit reached; waiting.', delay=timedelta(minutes=5))

    adapter = get_adapter(account.platform)
    button = (auto.button_label, auto.button_url) if auto.button_url else None
    try:
        run.dm_id = adapter.private_reply(account, item.external_id, auto.dm_text, button) or ''
    except AuthError as exc:
        account.status, account.last_error = 'reconnect', exc.message
        account.save(update_fields=['status', 'last_error'])
        run.status, run.error = 'failed', exc.message
        run.save(update_fields=['status', 'error'])
        return 0
    except RateLimited as exc:
        return _retry(run, now, exc.message, delay=timedelta(seconds=exc.retry_after))
    except AdapterError as exc:
        if exc.retryable:
            return _retry(run, now, exc.message)
        run.status, run.error = 'failed', exc.message
        run.save(update_fields=['status', 'error'])
        return 0

    run.status, run.sent_at, run.error = 'sent', now, ''
    if auto.public_replies:
        text = random.choice(auto.public_replies)
        try:
            run.reply_id = adapter.reply(account, item, text) or ''
            InboxReply.objects.create(item=item, text=text, status='sent', source='auto',
                                      external_id=run.reply_id, sent_at=now)
        except AdapterError as exc:     # the DM went; a missing public reply is only noted
            run.error = f'DM sent, but the public reply failed: {exc.message}'
    run.save(update_fields=['status', 'sent_at', 'error', 'dm_id', 'reply_id'])
    if item.status == 'open':
        item.status = 'done'
        item.save(update_fields=['status'])
    return 1


def stats(automations):
    """Per automation: how many comments matched and how they ended."""
    rows = (AutomationRun.objects.filter(automation__in=automations).values('automation')
            .annotate(total=Count('pk'), sent=Count('pk', filter=Q(status='sent')),
                      failed=Count('pk', filter=Q(status='failed')),
                      waiting=Count('pk', filter=Q(status__in=('queued', 'sending')))))
    return {r['automation']: r for r in rows}
