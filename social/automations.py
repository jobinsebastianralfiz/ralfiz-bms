"""Comment-to-DM automations.

A new comment that matches an automation's keyword is queued here (from
``services.ingest``, so webhooks and inbox syncs both feed it). The worker then
sends the private reply DM first, since Meta only allows it for about a week,
and the public reply under the comment second. Each comment is queued once and
each person gets one DM per automation and post.

With the "opener" delivery the first DM carries a button instead of the link.
The tap arrives as a webhook postback and opens Meta's 24-hour messaging
window, which lets us check an Instagram follow before sending the link, and
send one follow-up later. Inside that window a DM with the automation's lead
keyword starts a three-question lead form that ends in a BMS CRM lead.
"""
import logging
import random
import re
import secrets
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q
from django.utils import timezone
from django.utils.text import slugify

from .adapters import get_adapter
from .adapters.base import AdapterError, AuthError, RateLimited
from .models import (Automation, AutomationRun, Contact, InboxReply, LeadCapture, LinkClick,
                     SocialAccount, TrackedLink)

log = logging.getLogger(__name__)

PLATFORMS = ('facebook', 'instagram')
#: Meta stops accepting private replies about seven days after the comment.
REPLY_WINDOW = timedelta(days=7)
#: After a person writes or taps, the account may message them for 24 hours.
MESSAGE_WINDOW = timedelta(hours=24)
#: Well under Meta's messaging limits, so a viral reel cannot get the Page throttled.
HOURLY_LIMIT = 150
#: A run stuck in "sending" this long may already have sent its DM: never retry it.
STALE_LOCK = timedelta(minutes=10)
#: Button template text limit on Messenger and Instagram.
DM_MAX = 640
#: Older DMs (pulled in by an inbox sync) never start or advance the lead form.
FRESH_DM = timedelta(minutes=15)
PAYLOAD_PREFIX = 'AUTO:'

DEFAULT_OPENER = 'Send me the link'
DEFAULT_LINK_TEXT = 'Here you go 👇'
DEFAULT_GATE_TEXT = 'Follow us first, then tap the button again and the link is yours 👇'
GATE_AGAIN = 'I followed'
LEAD_ASK = {
    'name': "Great! What's your name?",
    'business': 'And the name of your business?',
    'phone': "Last one: your WhatsApp number? We'll message you there.",
}
LEAD_BAD_PHONE = "That doesn't look like a phone number. Please send it with the country code, e.g. +91 98765 43210."
LEAD_THANKS = 'Thanks {name}! Our team will WhatsApp you soon.'
PHONE_RE = re.compile(r'^\+?[\d\s\-()]{10,20}$')
#: Link-preview crawlers open the link when the DM is sent; they are not clicks.
CRAWLERS = ('facebookexternalhit', 'facebot', 'meta-externalagent', 'whatsapp/')


# ---------------------------------------------------------------- matching

def _norm(text):
    return ' '.join(text.casefold().split())


def _keyword_hit(keyword, text, exact):
    kw, text = _norm(keyword), _norm(text)
    if not kw:
        return False
    if exact:
        # "Skill 🔥" and "skill!" still count as just the keyword.
        return re.sub(r'^\W+|\W+$', '', text) == kw
    return bool(re.search(rf'(?<!\w){re.escape(kw)}(?!\w)', text))


def matches(automation, text):
    return any(_keyword_hit(kw, text, automation.match_type == 'exact') for kw in automation.keywords)


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


def _text(data, key, label, required=False):
    value = (data.get(key) or '').strip()
    if required and not value:
        raise _error(f'Write the {label}.')
    if len(value) > DM_MAX:
        raise _error(f'The {label} is {len(value)} characters; Meta allows {DM_MAX}.')
    return value


def _error(message):
    from .services import SocialError
    return SocialError(message)


def save_automation(user, workspace, data, automation=None):
    """Create or update an automation from form or tool data."""
    from .services import audit, require
    require(user, workspace, 'manager')
    account = SocialAccount.objects.filter(workspace=workspace, pk=data.get('account'),
                                           platform__in=PLATFORMS).first()
    if account is None:
        raise _error('Pick a connected Facebook Page or Instagram account.')
    keywords = _clean_list(data.get('keywords'))
    if not keywords:
        raise _error('Add at least one keyword.')
    dm_text = _text(data, 'dm_text', 'DM people will get', required=True)
    label, url = (data.get('button_label') or '').strip(), (data.get('button_url') or '').strip()
    if bool(label) != bool(url):
        raise _error('A button needs both a label and a link.')
    opener = (data.get('opener_label') or '').strip()
    if max(len(label), len(opener)) > 20:
        raise _error('Button labels can be at most 20 characters.')
    if url and not url.startswith('https://'):
        raise _error('The button link must start with https://')
    delivery = data.get('delivery') if data.get('delivery') in ('direct', 'opener') else 'direct'
    follow_gate = bool(data.get('follow_gate'))
    if follow_gate and (delivery != 'opener' or account.platform != 'instagram'):
        raise _error('The follow check needs an Instagram account and the "button first" delivery.')
    link_text, gate_text = _text(data, 'link_text', 'link message'), _text(data, 'gate_text', 'follow message')
    if delivery == 'opener' and not (url or link_text):
        raise _error('Add the link, or the message people get after they tap.')
    followup_text = _text(data, 'followup_text', 'follow-up')
    try:
        followup_hours = int(data.get('followup_hours') or 6)
    except (TypeError, ValueError):
        followup_hours = 0
    if followup_text and not 1 <= followup_hours <= 23:
        raise _error('Send the follow-up 1 to 23 hours after the tap; Meta closes the chat at 24.')
    if followup_text and delivery != 'opener':
        raise _error('A follow-up needs the "button first" delivery: only a tap lets us message again.')
    lead_keyword = (data.get('lead_keyword') or '').strip()[:30]

    a = automation or Automation(workspace=workspace, created_by=user)
    a.account, a.keywords, a.dm_text = account, keywords, dm_text
    a.name = (data.get('name') or '').strip()[:120] or f'{keywords[0].upper()} automation'
    a.post_id = (data.get('post_id') or '').strip()
    a.match_type = data.get('match_type') if data.get('match_type') in ('exact', 'contains') else 'contains'
    a.public_replies = _clean_list(data.get('public_replies') or '')
    a.button_label, a.button_url = label, url
    a.delivery, a.opener_label, a.follow_gate = delivery, opener, follow_gate
    a.link_text, a.gate_text, a.lead_keyword = link_text, gate_text, lead_keyword
    a.followup_text, a.followup_hours = followup_text, max(1, min(23, followup_hours or 6))
    a.ends_at = data.get('ends_at') or None
    a.is_active = bool(data.get('is_active', True))
    a.save()
    if url:
        link_for(a)
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


# ---------------------------------------------------------------- tracked links

def link_for(automation):
    """The automation's /go/ short link, created on first use and kept pointing at its URL."""
    link = TrackedLink.objects.filter(automation=automation).first()
    if link is None:
        while True:
            slug = secrets.token_urlsafe(5).replace('_', 'x').replace('-', 'y')
            if not TrackedLink.objects.filter(slug=slug).exists():
                break
        return TrackedLink.objects.create(automation=automation, slug=slug, target_url=automation.button_url)
    if link.target_url != automation.button_url:
        link.target_url = automation.button_url
        link.save(update_fields=['target_url'])
    return link


def tracked_url(run):
    link = link_for(run.automation)
    return f"{settings.SOCIAL_PUBLIC_BASE_URL.rstrip('/')}/go/{link.slug}/?r={run.pk}"


def with_utm(url, automation, platform):
    """Add UTM tags so the website's analytics credit the reel; tags already on the link win."""
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for key, value in (('utm_source', platform), ('utm_medium', 'social_dm'),
                       ('utm_campaign', slugify(automation.name)[:60] or 'automation')):
        query.setdefault(key, value)
    return urlunsplit(parts._replace(query=urlencode(query)))


def record_click(link, run_id, user_agent):
    """Count one click and return where to send the person."""
    run = None
    if str(run_id or '').isdigit():
        run = AutomationRun.objects.filter(pk=int(run_id), automation_id=link.automation_id).first()
    platform = link.automation.account.platform
    if not any(c in (user_agent or '').lower() for c in CRAWLERS):
        LinkClick.objects.create(link=link, run=run, platform=platform, user_agent=(user_agent or '')[:300])
    return with_utm(link.target_url, link.automation, platform)


# ---------------------------------------------------------------- sending

def _claim(run_id, now):
    return AutomationRun.objects.filter(pk=run_id, status='queued').update(
        status='sending', locked_at=now, attempts=F('attempts') + 1) == 1


def _sent_last_hour(account, now):
    return AutomationRun.objects.filter(automation__account=account, status='sent',
                                        sent_at__gte=now - timedelta(hours=1)).count()


def run_due(now=None, limit=50):
    """Worker job: send the queued DMs and the follow-ups that are due. Returns how many went."""
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
    return sent + _send_followups(now, limit)


def _retry(run, now, message, delay=None):
    if run.attempts >= run.MAX_ATTEMPTS:
        run.status, run.error = 'failed', message
    else:
        run.status, run.error = 'queued', message
        run.next_attempt_at = now + (delay or timedelta(minutes=2 ** run.attempts))
    run.save(update_fields=['status', 'error', 'next_attempt_at'])
    return 0


def _contact_for(run):
    item = run.item
    contact, _ = Contact.objects.get_or_create(
        workspace=run.automation.workspace, platform=run.automation.account.platform,
        platform_user_id=run.commenter_id or f'comment:{item.external_id}',
        defaults={'name': item.author_name if run.automation.account.platform == 'facebook' else '',
                  'username': item.author_name if run.automation.account.platform == 'instagram' else ''})
    contact.last_seen_at = timezone.now()
    contact.save(update_fields=['last_seen_at'])
    return contact


def _first_buttons(run):
    auto = run.automation
    if auto.delivery == 'opener':
        return [{'title': auto.opener_label or DEFAULT_OPENER, 'payload': f'{PAYLOAD_PREFIX}{run.pk}'}]
    if auto.button_url:
        return [{'title': auto.button_label, 'url': tracked_url(run)}]
    return None


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
    try:
        run.dm_id = adapter.private_reply(account, item.external_id, auto.dm_text, _first_buttons(run)) or ''
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
    run.contact = _contact_for(run)
    if auto.delivery == 'direct' and auto.button_url:
        run.link_sent_at = now
    if auto.public_replies:
        text = random.choice(auto.public_replies)
        try:
            run.reply_id = adapter.reply(account, item, text) or ''
            InboxReply.objects.create(item=item, text=text, status='sent', source='auto',
                                      external_id=run.reply_id, sent_at=now)
        except AdapterError as exc:     # the DM went; a missing public reply is only noted
            run.error = f'DM sent, but the public reply failed: {exc.message}'
    run.save(update_fields=['status', 'sent_at', 'error', 'dm_id', 'reply_id', 'contact', 'link_sent_at'])
    if item.status == 'open':
        item.status = 'done'
        item.save(update_fields=['status'])
    return 1


# ---------------------------------------------------------------- button taps

def handle_postback(account, sender, payload, mid):
    """A tap on an opener (or "I followed") button. Called from the webhook; never raises."""
    if not payload.startswith(PAYLOAD_PREFIX) or not payload[len(PAYLOAD_PREFIX):].isdigit():
        return None
    run = (AutomationRun.objects.select_related('automation__account', 'contact')
           .filter(pk=int(payload[len(PAYLOAD_PREFIX):]), automation__account=account).first())
    if run is None or run.last_postback == mid:
        return None                     # not ours, or Meta delivered the same tap twice
    now = timezone.now()
    auto = run.automation
    contact = run.contact or _contact_for(run)
    contact.messaging_id, contact.last_seen_at = sender, now
    run.contact, run.last_postback = contact, mid
    if run.tapped_at is None:
        run.tapped_at = now
        if auto.followup_text:
            run.followup_due_at = now + timedelta(hours=auto.followup_hours)
    adapter = get_adapter(account.platform)
    try:
        if auto.follow_gate and account.platform == 'instagram':
            following = _check_follow(adapter, account, contact, run)
            if following is False:
                adapter.send_dm(account, sender, auto.gate_text or DEFAULT_GATE_TEXT,
                                [{'title': GATE_AGAIN, 'payload': f'{PAYLOAD_PREFIX}{run.pk}'}])
                return _save_tap(run, contact)
        buttons = [{'title': auto.button_label, 'url': tracked_url(run)}] if auto.button_url else None
        adapter.send_dm(account, sender, auto.link_text or (DEFAULT_LINK_TEXT if buttons else auto.dm_text),
                        buttons)
        run.link_sent_at, run.error = now, ''
    except AuthError as exc:
        account.status, account.last_error = 'reconnect', exc.message
        account.save(update_fields=['status', 'last_error'])
        run.error = f'Tap not answered: {exc.message}'
    except AdapterError as exc:
        run.error = f'Tap not answered: {exc.message}'
    return _save_tap(run, contact)


def _check_follow(adapter, account, contact, run):
    """True or False; None when Instagram would not say, and then the link goes anyway."""
    try:
        profile = adapter.user_profile(account, contact.messaging_id)
    except AuthError:
        raise
    except AdapterError as exc:
        log.warning('Follow check failed for run %s: %s', run.pk, exc.message)
        return None
    contact.name = profile.get('name') or contact.name
    contact.username = profile.get('username') or contact.username
    following = profile.get('is_follower')
    if following is not None:
        contact.is_follower = following
        if run.was_follower is None:
            run.was_follower = following
    return following


def _save_tap(run, contact):
    contact.save()
    run.save(update_fields=['contact', 'last_postback', 'tapped_at', 'followup_due_at',
                            'was_follower', 'link_sent_at', 'error'])
    return run


def _send_followups(now, limit):
    """One follow-up per tapped run, while Meta's 24-hour window is still open."""
    sent = 0
    due = (AutomationRun.objects.filter(followup_due_at__lte=now, followup_sent_at__isnull=True)
           .select_related('automation__account', 'contact').order_by('followup_due_at')[:limit])
    for run in due:
        # Claim first, so two workers can never send the same follow-up.
        if not AutomationRun.objects.filter(pk=run.pk, followup_sent_at__isnull=True).update(followup_sent_at=now):
            continue
        account, contact = run.automation.account, run.contact
        if not run.tapped_at or run.tapped_at < now - MESSAGE_WINDOW or not (contact and contact.messaging_id):
            AutomationRun.objects.filter(pk=run.pk).update(followup_sent_at=None, followup_due_at=None)
            continue
        if not (run.automation.is_live and account.healthy):
            continue
        try:
            get_adapter(account.platform).send_dm(account, contact.messaging_id, run.automation.followup_text)
            sent += 1
        except AdapterError as exc:
            AutomationRun.objects.filter(pk=run.pk).update(error=f'Follow-up failed: {exc.message}')
    return sent


# ---------------------------------------------------------------- lead form

def on_message(item):
    """A new DM: answer the lead form if this person is in one, or start it on the keyword."""
    account = item.account
    if item.kind != 'dm' or account.platform not in PLATFORMS or not item.author_id:
        return None
    now = timezone.now()
    if item.received_at < now - FRESH_DM:
        return None
    contact = (Contact.objects.filter(workspace=account.workspace, platform=account.platform)
               .filter(Q(messaging_id=item.author_id) | Q(platform_user_id=item.author_id)).first())
    if contact is None:
        return None                     # only people an automation has DMed
    if not contact.messaging_id:
        contact.messaging_id = item.author_id
    contact.last_seen_at = now
    contact.save(update_fields=['messaging_id', 'last_seen_at'])
    capture = (contact.lead_captures.exclude(step='done')
               .filter(updated_at__gte=now - MESSAGE_WINDOW).select_related('automation').first())
    if capture:
        return _advance(item, capture)
    auto = _lead_automation(contact, item.text)
    if auto is None:
        return None
    capture = LeadCapture.objects.create(contact=contact, automation=auto)
    _bot_reply(item, LEAD_ASK['name'])
    return capture


def _lead_automation(contact, text):
    """The automation whose lead keyword the DM is, preferring the one that DMed this person."""
    autos = list(Automation.objects.filter(account__workspace=contact.workspace,
                                           account__platform=contact.platform)
                 .exclude(lead_keyword='').order_by('-created_at'))
    last = contact.runs.order_by('-created_at').values_list('automation_id', flat=True).first()
    autos.sort(key=lambda a: a.pk != last)
    return next((a for a in autos if _keyword_hit(a.lead_keyword, text, exact=False)), None)


def _advance(item, capture):
    answer = item.text.strip()
    if capture.step == 'name':
        capture.name, capture.step = answer[:200], 'business'
        _bot_reply(item, LEAD_ASK['business'])
    elif capture.step == 'business':
        capture.business, capture.step = answer[:200], 'phone'
        _bot_reply(item, LEAD_ASK['phone'])
    elif capture.step == 'phone':
        if not PHONE_RE.match(answer):
            _bot_reply(item, LEAD_BAD_PHONE)
            capture.save(update_fields=['updated_at'])
            return capture
        capture.phone, capture.step = answer[:20], 'done'
        capture.crm_lead = _create_lead(capture)
        _bot_reply(item, LEAD_THANKS.format(name=capture.name.split()[0] if capture.name else 'you'))
    capture.save()
    return capture


def _bot_reply(item, text):
    try:
        ext = get_adapter(item.account.platform).reply(item.account, item, text) or ''
    except AdapterError as exc:
        log.warning('Lead form reply failed: %s', exc.message)
        InboxReply.objects.create(item=item, text=text, status='failed', source='auto', error=exc.message)
        return
    InboxReply.objects.create(item=item, text=text, status='sent', source='auto', external_id=ext,
                              sent_at=timezone.now())
    if item.status == 'open':
        item.status = 'done'
        item.save(update_fields=['status'])


def _create_lead(capture):
    """Ralfiz's own accounts feed the BMS CRM. A client's leads stay in the hub for them."""
    contact, auto = capture.contact, capture.automation
    if contact.workspace.client_id is not None:
        return None
    from crm.models import Lead, LeadActivity
    source_name = auto.name if auto else 'a comment automation'
    handle = f' (@{contact.username})' if contact.username else ''
    with transaction.atomic():
        lead = Lead.objects.create(
            contact_person=capture.name or contact.name or 'Unknown', company_name=capture.business,
            phone=capture.phone, source=contact.platform, status='new',
            notes=f'From the "{source_name}" automation: {contact.get_platform_display()} DM{handle}.')
        LeadActivity.objects.create(lead=lead, activity_type='created',
                                    description=f'Lead form in {contact.get_platform_display()} DMs: {source_name}',
                                    metadata={'via': 'social_automation',
                                              'automation': str(auto.pk) if auto else ''})
    _notify_owners(lead, source_name)
    return lead


def _notify_owners(lead, source_name):
    """Push to owners' phones. Never blocks the conversation."""
    try:
        from employees.models import Employee
        from employees.utils import send_push_notification
        for emp in Employee.objects.filter(status='active', role__in=('owner', 'partner')):
            send_push_notification(emp, 'New lead from a reel',
                                   f'{lead.contact_person} ({lead.phone}): {source_name}',
                                   {'type': 'lead', 'lead_id': str(lead.pk)})
    except Exception:
        log.exception('automation lead push failed')


# ---------------------------------------------------------------- numbers

def stats(automations):
    """Per automation: comments matched, how they ended, taps, clicks, follows and leads."""
    rows = (AutomationRun.objects.filter(automation__in=automations).values('automation')
            .annotate(total=Count('pk'), sent=Count('pk', filter=Q(status='sent')),
                      failed=Count('pk', filter=Q(status='failed')),
                      waiting=Count('pk', filter=Q(status__in=('queued', 'sending'))),
                      taps=Count('pk', filter=Q(tapped_at__isnull=False)),
                      follows=Count('pk', filter=Q(was_follower=False, link_sent_at__isnull=False))))
    out = {r['automation']: r for r in rows}
    for automation_id, clicks in (LinkClick.objects.filter(link__automation__in=automations)
                                  .values_list('link__automation').annotate(n=Count('pk'))):
        out.setdefault(automation_id, {})['clicks'] = clicks
    for automation_id, leads in (LeadCapture.objects.filter(automation__in=automations, step='done')
                                 .values_list('automation').annotate(n=Count('pk'))):
        out.setdefault(automation_id, {})['leads'] = leads
    return out
