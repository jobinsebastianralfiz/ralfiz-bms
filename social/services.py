"""The rules of the Social Hub, in one place.

Web views, the client review link, the MCP tools and the worker all call
these functions, so a permission check or an approval rule cannot differ
between the dashboard and Claude. Functions raise SocialError with a message
fit to show a person.
"""
import mimetypes
import os
import uuid
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone

from .adapters import get_adapter
from .adapters.base import AdapterError, AuthError, MediaInput, RateLimited
from .models import (Approval, AuditLog, InboxItem, InboxReply, MediaAsset, Membership, MetricDaily,
                     Post, PostMedia, PostMetric, PostTarget, SocialAccount, Workspace)


class SocialError(Exception):
    pass


# ================================================================ access

def is_social_admin(user):
    """Owners and partners (the people the BMS connector serves) manage every workspace."""
    if user is None or not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    from connector.auth import can_use_connector
    return can_use_connector(user)


def can_use_hub(user):
    return is_social_admin(user) or (
        user is not None and user.is_authenticated and Membership.objects.filter(user=user).exists())


def social_only(user):
    """True for a login whose only role is Social Hub member (a client's
    reviewer, a freelancer, Meta's app reviewer). Most BMS pages only check
    login, so the middleware keeps such a login inside /social/."""
    if user is None or not user.is_authenticated or user.is_staff or user.is_superuser:
        return False
    if not Membership.objects.filter(user=user).exists():
        return False
    if hasattr(user, 'team_profile') or hasattr(user, 'client_profile'):
        return False
    from academy.models import Student
    from employees.models import Employee
    return not (Employee.objects.filter(user=user, status='active').exists()
                or Student.objects.filter(user=user).exists())


def workspaces_for(user):
    qs = Workspace.objects.filter(is_active=True)
    if is_social_admin(user):
        return qs
    return qs.filter(memberships__user=user).distinct()


def role_for(user, workspace):
    if is_social_admin(user):
        return 'manager'
    m = Membership.objects.filter(user=user, workspace=workspace).first()
    return m.role if m else None


def require(user, workspace, level='editor'):
    role = role_for(user, workspace)
    if role is None or (level == 'manager' and role != 'manager'):
        raise PermissionDenied('You do not have access to this client.' if role is None else
                               'Only a manager can do this.')
    return role


# ================================================================ audit

def audit(workspace, action, summary='', *, user=None, via='web', actor='', **payload):
    return AuditLog.objects.create(
        workspace=workspace, user=user if (user and user.is_authenticated) else None,
        actor=actor or (user.get_full_name() or user.username if user and user.is_authenticated else ''),
        via=via, action=action, summary=summary[:300], payload=payload,
    )


# ================================================================ media

MEDIA_SALT = 'social-media'
MAX_IMAGE = 8 * 1024 * 1024
MAX_VIDEO = 512 * 1024 * 1024


def signed_media_url(asset):
    """An unguessable URL a platform can fetch for 48 hours (see views.media_file)."""
    token = signing.dumps(str(asset.pk), salt=MEDIA_SALT)
    base = getattr(settings, 'SOCIAL_PUBLIC_BASE_URL', '').rstrip('/')
    return f"{base}{reverse('social:media_file', args=[token])}"


def asset_from_token(token):
    try:
        pk = signing.loads(token, salt=MEDIA_SALT, max_age=48 * 3600)
    except signing.BadSignature:
        return None
    return MediaAsset.objects.filter(pk=pk).first()


def media_input(asset):
    return MediaInput(kind=asset.kind, url=signed_media_url(asset),
                      content_type=asset.content_type or 'application/octet-stream',
                      size=asset.size, name=asset.name or os.path.basename(asset.file.name),
                      open=lambda: _open_media(asset))


def _open_media(asset):
    """The file's bytes. On Railway the media volume is mounted on the web
    service only, so the worker falls back to fetching its own signed URL."""
    if asset.file.storage.exists(asset.file.name):
        return asset.file.open('rb')
    import requests
    try:
        r = requests.get(signed_media_url(asset), stream=True, timeout=120)
        r.raise_for_status()
    except requests.RequestException as exc:
        raise AdapterError(f'Could not read {asset.name or "the media file"}: {exc.__class__.__name__}',
                           retryable=True)
    r.raw.decode_content = True
    return r.raw


# Only formats the platforms accept. SVG is deliberately excluded: served from our
# domain it can carry script.
IMAGE_TYPES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
               '.gif': 'image/gif'}
VIDEO_TYPES = {'.mp4': 'video/mp4', '.mov': 'video/quicktime', '.m4v': 'video/x-m4v', '.webm': 'video/webm'}


def _kind_for(content_type, name):
    """(kind, content type) from the file extension; the browser's claim is not trusted."""
    ext = os.path.splitext(name or '')[1].lower()
    if ext in IMAGE_TYPES:
        return 'image', IMAGE_TYPES[ext]
    if ext in VIDEO_TYPES:
        return 'video', VIDEO_TYPES[ext]
    ct = (content_type or '').split(';')[0].strip().lower()
    for kind, table in (('image', IMAGE_TYPES), ('video', VIDEO_TYPES)):
        if ct in table.values():
            return kind, ct
    raise SocialError('Use a JPG, PNG, WebP or GIF image, or an MP4, MOV or WebM video.')


def _check_public_url(url):
    """Refuse URLs that point inside our own network (SSRF): only public http(s) hosts."""
    import ipaddress
    import socket
    from urllib.parse import urlsplit
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        raise SocialError('Give an http(s) link to the image or video.')
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == 'https' else 80))
    except OSError:
        raise SocialError('That link\'s address could not be found.')
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global or ip.is_multicast:
            raise SocialError('That link points to a private address and cannot be used.')


def save_media(user, workspace, uploaded, *, tags='', source='upload', via='web'):
    """Store an uploaded file (Django UploadedFile or ContentFile with .name)."""
    require(user, workspace)
    kind, ct = _kind_for(getattr(uploaded, 'content_type', ''), uploaded.name)
    limit = MAX_VIDEO if kind == 'video' else MAX_IMAGE
    if uploaded.size > limit:
        raise SocialError(f'That {kind} is larger than {limit // (1024 * 1024)} MB.')
    asset = MediaAsset(workspace=workspace, name=os.path.basename(uploaded.name)[:255], kind=kind,
                       content_type=ct, size=uploaded.size, tags=tags[:255], source=source,
                       uploaded_by=user if user and user.is_authenticated else None)
    # Random file names: the original name never appears in a URL.
    if kind == 'image':
        # The bytes must really be a raster image, whatever the name or type claims.
        from PIL import Image
        try:
            uploaded.seek(0)
            img = Image.open(uploaded)
            img.verify()
            if img.format not in ('JPEG', 'PNG', 'WEBP', 'GIF', 'MPO'):
                raise ValueError(img.format)
            asset.width, asset.height = img.size
        except Exception:
            raise SocialError('That file is not a valid JPG, PNG, WebP or GIF image.')
        uploaded.seek(0)
    else:
        head = uploaded.read(16)
        uploaded.seek(0)
        # MP4/MOV have 'ftyp' at byte 4; WebM starts with the EBML magic.
        if head[4:8] != b'ftyp' and not head.startswith(b'\x1a\x45\xdf\xa3'):
            raise SocialError('That file is not a valid MP4, MOV or WebM video.')
    ext = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp', 'image/gif': '.gif',
           'video/mp4': '.mp4', 'video/quicktime': '.mov', 'video/x-m4v': '.m4v', 'video/webm': '.webm'}[ct]
    asset.file.save(f'{uuid.uuid4().hex}{ext}', uploaded, save=False)
    asset.save()
    audit(workspace, 'media.upload', asset.name, user=user, via=via)
    return asset


def save_media_from_url(user, workspace, url, *, via='web'):
    import requests
    # Follow redirects by hand so every hop is checked, not just the first URL.
    for _ in range(5):
        _check_public_url(url)
        try:
            r = requests.get(url, stream=True, timeout=30, allow_redirects=False)
        except requests.RequestException:
            raise SocialError('Could not download that file.')
        if r.is_redirect and r.headers.get('location'):
            from urllib.parse import urljoin
            url = urljoin(url, r.headers['location'])
            r.close()
            continue
        break
    else:
        raise SocialError('That link redirects too many times.')
    if r.status_code != 200:
        raise SocialError(f'Downloading the file failed (HTTP {r.status_code}).')
    ct = r.headers.get('content-type', '').split(';')[0].strip()
    name = os.path.basename(url.split('?')[0]) or 'download'
    kind, ct = _kind_for(ct, name)
    limit = MAX_VIDEO if kind == 'video' else MAX_IMAGE
    data = bytearray()
    for chunk in r.iter_content(1024 * 256):
        data.extend(chunk)
        if len(data) > limit:
            raise SocialError(f'That {kind} is larger than {limit // (1024 * 1024)} MB.')
    f = ContentFile(bytes(data), name=name)
    f.content_type = ct
    return save_media(user, workspace, f, source='url', via=via)


# ================================================================ posts

def _accounts_for(workspace, account_ids):
    accounts = list(SocialAccount.objects.filter(workspace=workspace, pk__in=account_ids))
    if len(accounts) != len(set(map(str, account_ids))):
        raise SocialError('One of the accounts does not belong to this client.')
    return accounts


def problems_for(post):
    """{account: [problem, ...]} for every target that the platform would reject."""
    media = [media_input(a) for a in post.ordered_media()]
    out = {}
    for t in post.targets.select_related('account'):
        adapter = get_adapter(t.account.platform)
        extra = {'link': post.link} if t.account.platform == 'x' else {}  # X counts the link's 23 chars
        problems = adapter.validate(t.effective_text, media, title=post.title,
                                    first_comment=post.first_comment, **extra)
        if not t.account.healthy:
            problems.append(f'{t.account.name} needs reconnecting.')
        if problems:
            out[t.account] = problems
    return out


def _check_publishable(post):
    if not post.targets.exists():
        raise SocialError('Pick at least one account.')
    problems = problems_for(post)
    if problems:
        raise SocialError(' '.join(p for ps in problems.values() for p in ps))


def save_post(user, workspace, *, account_ids, text='', overrides=None, scheduled_at=None,
              first_comment='', title='', link='', media_ids=(), post=None, source='web'):
    """Create or edit a post and its per-account targets. Returns the Post.

    Editing a post that was approved or in review in a client-approval
    workspace sends it back to review: the client approved the old words.
    """
    require(user, workspace)
    if source == 'mcp':
        _mcp_rate_guard(workspace)
    if post is not None and not post.is_editable:
        raise SocialError('This post has already gone out and cannot be edited.')
    if scheduled_at and scheduled_at < timezone.now() - timedelta(minutes=1):
        raise SocialError('Pick a time in the future.')
    accounts = _accounts_for(workspace, account_ids)
    assets = list(MediaAsset.objects.filter(workspace=workspace, pk__in=media_ids))
    if len(assets) != len(set(map(str, media_ids))):
        raise SocialError('One of the media files does not belong to this client.')
    order = {str(i): n for n, i in enumerate(media_ids)}
    assets.sort(key=lambda a: order[str(a.pk)])
    overrides = {str(k): v for k, v in (overrides or {}).items()}

    with transaction.atomic():
        new = post is None
        if new:
            post = Post(workspace=workspace, created_by=user if user.is_authenticated else None,
                        source=source)
        was = post.status
        post.base_text, post.first_comment, post.title, post.link = text, first_comment, title, link
        post.scheduled_at = scheduled_at
        if not new and workspace.requires_approval and was == 'scheduled':
            post.status = 'review'
        elif not new and was == 'failed':
            post.status = 'draft'
        post.save()
        keep = {str(a.pk) for a in accounts}
        post.targets.exclude(account_id__in=keep).delete()
        for a in accounts:
            t, _ = PostTarget.objects.get_or_create(post=post, account=a)
            override = overrides.get(str(a.pk), '')
            t.text = '' if override.strip() == text.strip() else override
            if t.status == 'failed':
                t.status, t.attempts, t.error, t.next_attempt_at = 'pending', 0, '', None
            t.save()
        post.post_media.all().delete()
        PostMedia.objects.bulk_create([PostMedia(post=post, asset=a, position=i) for i, a in enumerate(assets)])
        if not new and was == 'scheduled' and post.status == 'review':
            Approval.objects.create(post=post, decision='submitted', user=user, via=source,
                                    comment='Edited after approval')
    audit(workspace, 'post.create' if new else 'post.edit', str(post), user=user, via=source,
          post=str(post.pk))
    return post


MCP_POSTS_PER_HOUR = 30


def _mcp_rate_guard(workspace):
    """Stop a runaway loop from flooding a client's queue."""
    recent = AuditLog.objects.filter(workspace=workspace, via='mcp', action__in=('post.create', 'post.edit'),
                                     created_at__gte=timezone.now() - timedelta(hours=1)).count()
    if recent >= MCP_POSTS_PER_HOUR:
        raise SocialError(f'Claude has written {recent} posts for {workspace.name} in the last hour. '
                          'Wait a while before drafting more.')


def submit(user, post, *, via='web', note=''):
    """Send for approval, or straight to the schedule where no approval is needed."""
    require(user, post.workspace)
    if post.status not in ('draft', 'changes', 'failed'):
        raise SocialError('Only a draft can be sent for approval.')
    _check_publishable(post)
    claude_queues = via == 'mcp' and getattr(settings, 'SOCIAL_MCP_AUTO_PUBLISH', False)
    if not post.workspace.requires_approval and (via != 'mcp' or claude_queues):
        return schedule(user, post, via=via)
    post.status = 'review'
    post.save(update_fields=['status', 'updated_at'])
    Approval.objects.create(post=post, decision='submitted', user=user, via=via, comment=note)
    audit(post.workspace, 'post.submit', str(post), user=user, via=via, post=str(post.pk))
    return post


def schedule(user, post, *, via='web'):
    """Queue a post where the workspace needs no client approval."""
    require(user, post.workspace)
    if post.workspace.requires_approval and post.status != 'scheduled':
        raise SocialError(f'{post.workspace.name} needs approval first.')
    if via == 'mcp' and not getattr(settings, 'SOCIAL_MCP_AUTO_PUBLISH', False):
        # Claude never queues a post to go out on its own.
        raise SocialError('Claude can draft and submit posts; a person schedules them.')
    _check_publishable(post)
    _queue(post)
    audit(post.workspace, 'post.schedule', str(post), user=user, via=via, post=str(post.pk))
    return post


def _queue(post):
    post.status = 'scheduled'
    if not post.scheduled_at:
        post.scheduled_at = timezone.now()
    post.save(update_fields=['status', 'scheduled_at', 'approved_at', 'approved_by_name', 'updated_at'])
    post.targets.exclude(status='published').update(status='pending', attempts=0, error='',
                                                    next_attempt_at=None, locked_at=None)


def approve(post, *, user=None, reviewer_name='', via='web', comment=''):
    """A manager (web) or the client (review link) approves a post in review."""
    if via != 'link':
        require(user, post.workspace, 'manager')
    if post.status != 'review':
        raise SocialError('This post is not waiting for approval.')
    _check_publishable(post)
    name = reviewer_name or (user.get_full_name() or user.username if user else '')
    post.approved_at, post.approved_by_name = timezone.now(), name
    _queue(post)
    Approval.objects.create(post=post, decision='approved', user=user, reviewer_name=name, via=via,
                            comment=comment)
    audit(post.workspace, 'post.approve', str(post), user=user, via=via, actor=name, post=str(post.pk))
    return post


def request_changes(post, *, user=None, reviewer_name='', via='web', comment=''):
    if via != 'link':
        require(user, post.workspace, 'manager')
    if post.status not in ('review', 'scheduled'):
        raise SocialError('Only a post in review or scheduled can be sent back.')
    if not comment.strip():
        raise SocialError('Say what should change.')
    name = reviewer_name or (user.get_full_name() or user.username if user else '')
    post.status = 'changes'
    post.save(update_fields=['status', 'updated_at'])
    Approval.objects.create(post=post, decision='changes', user=user, reviewer_name=name, via=via,
                            comment=comment)
    audit(post.workspace, 'post.changes', f'{post}: {comment}', user=user, via=via, actor=name,
          post=str(post.pk))
    return post


def reschedule(user, post, when, *, via='web'):
    """Move a post. An approved post in a client-approval workspace goes back to
    review, except when a manager moves it on the dashboard."""
    role = require(user, post.workspace)
    if not post.is_editable:
        raise SocialError('This post has already gone out.')
    if when < timezone.now() - timedelta(minutes=1):
        raise SocialError('Pick a time in the future.')
    post.scheduled_at = when
    back_to_review = (post.status == 'scheduled' and post.workspace.requires_approval
                      and (role != 'manager' or via == 'mcp'))
    if back_to_review:
        post.status = 'review'
        Approval.objects.create(post=post, decision='submitted', user=user, via=via,
                                comment='Moved to a new time')
    post.save(update_fields=['scheduled_at', 'status', 'updated_at'])
    audit(post.workspace, 'post.reschedule', f'{post} -> {timezone.localtime(when):%d %b %H:%M}',
          user=user, via=via, post=str(post.pk))
    return post


def delete_post(user, post, *, via='web'):
    require(user, post.workspace)
    if not post.is_editable:
        raise SocialError('A post that has gone out cannot be deleted here.')
    audit(post.workspace, 'post.delete', str(post), user=user, via=via)
    post.delete()


def retry(user, post, *, via='web'):
    require(user, post.workspace)
    if post.status not in ('failed', 'partial'):
        raise SocialError('Only a failed post can be retried.')
    for t in post.targets.select_related('account').filter(status='failed'):
        if not t.account.healthy:
            raise SocialError(f'Reconnect {t.account.name} first.')
    post.targets.filter(status='failed').update(status='pending', attempts=0, error='',
                                                next_attempt_at=None, locked_at=None)
    post.status = 'scheduled'
    if not post.scheduled_at or post.scheduled_at < timezone.now():
        post.scheduled_at = timezone.now()
    post.save(update_fields=['status', 'scheduled_at', 'updated_at'])
    audit(post.workspace, 'post.retry', str(post), user=user, via=via, post=str(post.pk))
    return post


def duplicate(user, post):
    require(user, post.workspace)
    copy = save_post(
        user, post.workspace, account_ids=[t.account_id for t in post.targets.all()],
        text=post.base_text, overrides={t.account_id: t.text for t in post.targets.all() if t.text},
        first_comment=post.first_comment, title=post.title, link=post.link,
        media_ids=[a.pk for a in post.ordered_media()],
        scheduled_at=(post.scheduled_at + timedelta(days=7)) if post.scheduled_at and
        post.scheduled_at + timedelta(days=7) > timezone.now() else None)
    return copy


# ================================================================ worker: publishing

STALE_LOCK = timedelta(minutes=15)
BACKOFF = (timedelta(minutes=5), timedelta(minutes=30), timedelta(hours=2))


def published_last_24h(account):
    return PostTarget.objects.filter(account=account, status='published',
                                     published_at__gte=timezone.now() - timedelta(hours=24)).count()


def publish_due(now=None, limit=50):
    """Publish every target whose time has come. Returns how many were attempted.

    A target is claimed with a conditional UPDATE (pending -> publishing), so
    two workers can never post the same thing. A target stuck in publishing
    is never retried automatically: the platform may have accepted it, and a
    second attempt would post twice. It is marked failed for a person to check.
    """
    now = now or timezone.now()
    stale = PostTarget.objects.filter(status='publishing', locked_at__lt=now - STALE_LOCK)
    for t in stale.select_related('post'):
        t.status = 'failed'
        t.error = 'Publishing did not finish. Check the platform before retrying, or it may post twice.'
        t.save(update_fields=['status', 'error'])
        _settle(t.post)

    due = (PostTarget.objects
           .filter(status='pending', post__status__in=('scheduled', 'publishing'),
                   post__scheduled_at__lte=now)
           .filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now))
           .select_related('post', 'account')
           .order_by('post__scheduled_at')[:limit])
    done = 0
    for t in due:
        claimed = PostTarget.objects.filter(pk=t.pk, status='pending').update(
            status='publishing', locked_at=now)
        if not claimed:
            continue
        t.refresh_from_db()
        _publish_target(t, now)
        done += 1
    return done


def _publish_target(t, now):
    post, account = t.post, t.account
    if post.status == 'scheduled':
        Post.objects.filter(pk=post.pk, status='scheduled').update(status='publishing')
        post.status = 'publishing'
    adapter = get_adapter(account.platform)
    try:
        if not account.healthy:
            raise AuthError(f'{account.name} needs reconnecting.')
        quota = adapter.quota_status(account, published_last_24h(account))
        if quota and quota[0] >= quota[1]:
            raise RateLimited(f'{account.name} has used {quota[0]} of {quota[1]} posts allowed in 24 hours.',
                              retry_after=3600)
        result = adapter.publish(
            account, t.effective_text, [media_input(a) for a in post.ordered_media()],
            title=post.title, link=post.link, first_comment=post.first_comment, options=t.options)
    except AuthError as exc:
        account.status, account.last_error = 'reconnect', exc.message
        account.save(update_fields=['status', 'last_error'])
        _fail(t, exc.message)
    except AdapterError as exc:
        t.attempts += 1
        if exc.retryable and t.attempts < PostTarget.MAX_ATTEMPTS:
            wait = timedelta(seconds=exc.retry_after) if isinstance(exc, RateLimited) else \
                BACKOFF[min(t.attempts - 1, len(BACKOFF) - 1)]
            t.status, t.error, t.next_attempt_at, t.locked_at = 'pending', exc.message, now + wait, None
            t.save(update_fields=['status', 'error', 'next_attempt_at', 'locked_at', 'attempts'])
        else:
            _fail(t, exc.message)
    except Exception as exc:  # a bug in an adapter must not stop the queue
        t.attempts += 1
        _fail(t, f'Unexpected error: {exc.__class__.__name__}: {exc}')
    else:
        t.status, t.external_id, t.external_url = 'published', result.external_id, result.url or ''
        t.published_at, t.error, t.locked_at = timezone.now(), '', None
        t.attempts += 1
        t.save()
        audit(post.workspace, 'post.published', f'{post} on {account.name}', via='worker',
              actor='Publisher', post=str(post.pk), url=t.external_url)
    _settle(post)


def _fail(t, message):
    t.status, t.error, t.locked_at = 'failed', message[:2000], None
    t.save(update_fields=['status', 'error', 'locked_at', 'attempts'])
    audit(t.post.workspace, 'post.failed', f'{t.post} on {t.account.name}: {message}'[:300],
          via='worker', actor='Publisher', post=str(t.post_id))


def _settle(post):
    states = set(post.targets.values_list('status', flat=True))
    if states & {'pending', 'publishing'}:
        status = 'publishing' if 'publishing' in states or 'published' in states else post.status
        if status == post.status:
            return
    elif states == {'published'}:
        status = 'published'
    elif 'published' in states:
        status = 'partial'
    else:
        status = 'failed'
    Post.objects.filter(pk=post.pk).update(status=status)
    post.status = status


# ================================================================ inbox

def ingest(account, items):
    """Store fetched or webhook-delivered inbox items. Returns how many were new."""
    new = 0
    for it in items:
        obj, created = InboxItem.objects.get_or_create(
            account=account, external_id=it.external_id,
            defaults=dict(kind=it.kind, thread_id=it.thread_id, author_name=it.author_name[:200],
                          author_id=it.author_id[:200], text=it.text, rating=it.rating,
                          permalink=it.permalink[:1000], raw=it.raw,
                          received_at=it.received_at or timezone.now()))
        new += created
    return new


def record_echo(account, echo):
    """A message sent from the WhatsApp Business app on the phone (coexistence). It shows in
    the hub as a sent reply on that customer's latest conversation, so the team sees it."""
    if not echo.get('id') or not echo.get('to'):
        return None
    item = account.inbox.filter(author_id=echo['to']).order_by('-received_at').first()
    if item is None or item.replies.filter(external_id=echo['id']).exists():
        return None
    reply = InboxReply.objects.create(item=item, text=echo.get('text') or '[message]', status='sent',
                                      source='phone', external_id=echo['id'],
                                      sent_at=echo.get('sent_at') or timezone.now())
    if item.status == 'open':
        item.status = 'done'
        item.save(update_fields=['status'])
    return reply


def sync_inbox(account):
    adapter = get_adapter(account.platform)
    if not adapter.caps.inbox or not account.healthy:
        return 0
    try:
        items = adapter.fetch_inbox(account, since=account.last_synced_at)
    except AuthError as exc:
        account.status, account.last_error = 'reconnect', exc.message
        account.save(update_fields=['status', 'last_error'])
        return 0
    n = ingest(account, items)
    account.last_synced_at = timezone.now()
    account.save(update_fields=['last_synced_at'])
    return n


def draft_reply(user, item, text, *, source='web'):
    require(user, item.account.workspace)
    if not text.strip():
        raise SocialError('The reply is empty.')
    reply = InboxReply.objects.create(item=item, text=text.strip(), source=source, created_by=user)
    audit(item.account.workspace, 'reply.draft', text[:120], user=user, via=source, item=str(item.pk))
    return reply


def send_reply(user, item, text, *, via='web'):
    """A person sends a reply. Claude cannot: it only drafts."""
    require(user, item.account.workspace)
    if via == 'mcp':
        raise SocialError('Claude drafts replies; a person sends them.')
    if not text.strip():
        raise SocialError('The reply is empty.')
    if not item.reply_window_open:
        raise SocialError('WhatsApp only allows a free reply within 24 hours of the customer\'s '
                          'last message. Send an approved template instead.')
    account = item.account
    reply = item.replies.filter(status='draft').order_by('-created_at').first() or \
        InboxReply(item=item, created_by=user)
    reply.text, reply.sent_by = text.strip(), user
    try:
        reply.external_id = get_adapter(account.platform).reply(account, item, reply.text) or ''
    except AuthError as exc:
        account.status, account.last_error = 'reconnect', exc.message
        account.save(update_fields=['status', 'last_error'])
        raise SocialError(exc.message)
    except AdapterError as exc:
        reply.status, reply.error = 'failed', exc.message
        reply.save()
        raise SocialError(exc.message)
    reply.status, reply.sent_at, reply.error = 'sent', timezone.now(), ''
    reply.save()
    item.status = 'done'
    item.save(update_fields=['status'])
    audit(account.workspace, 'reply.sent', f'To {item.author_name}: {reply.text[:100]}', user=user,
          via=via, item=str(item.pk))
    return reply


def set_item_status(user, item, status):
    require(user, item.account.workspace)
    item.status = status
    item.save(update_fields=['status'])


def assign_item(user, item, assignee):
    require(user, item.account.workspace)
    item.assigned_to = assignee
    item.save(update_fields=['assigned_to'])


# ================================================================ imported posts

IMPORT_DAYS = 90


def import_posts(account, since=None, limit=50):
    """Pull posts already on the account (made in the platform's app, or by us)
    into the hub as published posts, so the Posts page, calendar and analytics
    show the account's real history. Re-running updates counts and thumbnails
    (Instagram's CDN links expire) and never duplicates a post.
    Returns how many were new."""
    adapter = get_adapter(account.platform)
    if not account.healthy:
        return 0
    try:
        items = adapter.fetch_posts(account, since=since, limit=limit)
    except AuthError as exc:
        account.status, account.last_error = 'reconnect', exc.message
        account.save(update_fields=['status', 'last_error'])
        return 0
    new = 0
    for it in items:
        t = (PostTarget.objects.filter(account=account, external_id=it.external_id).select_related('post').first())
        opts = {'kind': it.kind, 'thumb': it.thumbnail_url[:2000]}
        if t is None:
            with transaction.atomic():
                post = Post.objects.create(
                    workspace=account.workspace, base_text=it.text, title=it.title[:100], status='published',
                    scheduled_at=it.published_at or timezone.now(), source='import')
                t = PostTarget.objects.create(
                    post=post, account=account, status='published', external_id=it.external_id[:300],
                    external_url=it.url[:1000], published_at=it.published_at or timezone.now(), options=opts)
            new += 1
        else:
            t.options = {**t.options, **opts}
            if it.url and not t.external_url:
                t.external_url = it.url[:1000]
            t.save(update_fields=['options', 'external_url'])
        for metric, value in it.metrics.items():
            PostMetric.objects.update_or_create(target=t, metric=metric,
                                                defaults={'value': int(value or 0), 'captured_at': timezone.now()})
    return new


def sync_account(account, *, first=False):
    """Inbox, posts and stats for one account; ``first`` imports the last 90 days."""
    since = timezone.now() - timedelta(days=IMPORT_DAYS) if first else None
    n_inbox = sync_inbox(account)
    n_posts = import_posts(account, since=since, limit=100 if first else 25)
    sync_insights(account, days=30 if first else 3)
    return n_inbox, n_posts


# ================================================================ analytics

METRICS = ('reach', 'impressions', 'engagement', 'followers', 'followers_gained', 'views', 'clicks')
#: Metrics that are a running total, so a period's value is the last day's, not the sum.
LEVEL_METRICS = ('followers',)


def sync_insights(account, days=3):
    adapter = get_adapter(account.platform)
    if not adapter.caps.insights or not account.healthy:
        return 0
    end = timezone.localdate()
    try:
        data = adapter.fetch_insights(account, end - timedelta(days=days), end)
    except AuthError as exc:
        account.status, account.last_error = 'reconnect', exc.message
        account.save(update_fields=['status', 'last_error'])
        return 0
    n = 0
    for day, metrics in data.items():
        for metric, value in metrics.items():
            MetricDaily.objects.update_or_create(account=account, date=day, metric=metric,
                                                 defaults={'value': int(value or 0)})
            n += 1
    return n


def sync_post_metrics(account, days=30):
    adapter = get_adapter(account.platform)
    since = timezone.now() - timedelta(days=days)
    n = 0
    for t in PostTarget.objects.filter(account=account, status='published', published_at__gte=since):
        try:
            data = adapter.fetch_post_metrics(account, t.external_id)
        except AdapterError:
            continue
        for metric, value in data.items():
            PostMetric.objects.update_or_create(target=t, metric=metric,
                                                defaults={'value': int(value or 0),
                                                          'captured_at': timezone.now()})
            n += 1
    return n


def analytics(accounts, start, end):
    """Totals, a daily series, per-platform reach and top posts for some accounts."""
    accounts = list(accounts)
    rows = MetricDaily.objects.filter(account__in=accounts, date__gte=start, date__lte=end)
    series = defaultdict(lambda: defaultdict(int))
    for r in rows.values('date', 'metric').annotate(v=Sum('value')):
        series[r['metric']][r['date']] = r['v']
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    totals = {}
    for m in METRICS:
        values = series.get(m, {})
        if m in LEVEL_METRICS:
            totals[m] = values[max(values)] if values else 0
        else:
            totals[m] = sum(values.values())
    by_platform = defaultdict(int)
    for r in rows.filter(metric='reach').values('account__platform').annotate(v=Sum('value')):
        by_platform[r['account__platform']] += r['v']
    top = (PostMetric.objects.filter(target__account__in=accounts, metric='engagement',
                                     target__published_at__date__gte=start)
           .select_related('target__post', 'target__account').order_by('-value')[:6])
    eng_rate = round(100 * totals['engagement'] / totals['reach'], 1) if totals['reach'] else 0
    return {
        'days': days,
        'series': {m: [series.get(m, {}).get(d, 0) for d in days] for m in METRICS},
        'totals': totals,
        'engagement_rate': eng_rate,
        'by_platform': dict(sorted(by_platform.items(), key=lambda kv: -kv[1])),
        'top_posts': list(top),
    }


SLOTS = (6, 9, 12, 15, 18, 21)
DAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')


def best_times(accounts, min_posts=5):
    """Average engagement per weekday x 3-hour slot from published posts.

    Returns None when there are too few posts to say anything honest.
    """
    rows = PostMetric.objects.filter(target__account__in=list(accounts), metric='engagement',
                                     target__published_at__isnull=False)
    rows = list(rows.values_list('target__published_at', 'value'))
    if len(rows) < min_posts:
        return None
    sums = defaultdict(lambda: [0, 0])
    for when, value in rows:
        local = timezone.localtime(when)
        slot = max([i for i, h in enumerate(SLOTS) if local.hour >= h] or [0])
        sums[(local.weekday(), slot)][0] += value
        sums[(local.weekday(), slot)][1] += 1
    avg = {k: s / n for k, (s, n) in sums.items()}
    top = max(avg.values())
    grid = [[round(avg.get((d, s), 0) / top, 2) if top else 0 for s in range(len(SLOTS))]
            for d in range(7)]
    best = sorted(avg, key=avg.get, reverse=True)[:3]
    return {'grid': grid, 'best': [{'day': DAYS[d], 'weekday': d, 'hour': SLOTS[s],
                                    'label': f'{DAYS[d]} {_hour(SLOTS[s])}-{_hour(SLOTS[s] + 3)}'}
                                   for d, s in best]}


def _hour(h):
    h %= 24
    return f'{h % 12 or 12}{"am" if h < 12 else "pm"}'


# ================================================================ accounts

def connect_candidates(user, workspace, platform, candidates, *, via='web'):
    """Save accounts picked after sign-in. Reconnecting updates the existing row."""
    require(user, workspace, 'manager')
    saved = []
    for c in candidates:
        acc, created = SocialAccount.objects.get_or_create(
            workspace=workspace, platform=platform, external_id=c.external_id,
            defaults={'name': c.name[:200]})
        acc.name, acc.handle, acc.avatar_url = c.name[:200], c.handle[:200], c.avatar_url[:1000]
        acc.token = c.token
        if c.refresh_token:
            acc.refresh_token = c.refresh_token
        acc.expires_at, acc.extra = c.expires_at, {**acc.extra, **c.extra}
        acc.status, acc.last_error, acc.connected_by = 'active', '', user
        acc.save()
        audit(workspace, 'account.connect' if created else 'account.reconnect', acc.name, user=user, via=via)
        saved.append(acc)
    return saved


def disconnect(user, account):
    require(user, account.workspace, 'manager')
    account.token = ''
    account.refresh_token = ''
    account.status = 'disconnected'
    account.save()
    audit(account.workspace, 'account.disconnect', account.name, user=user)


EXPIRY_WARNING = timedelta(days=7)


def refresh_tokens(now=None):
    """Renew tokens that can be renewed; flag the rest before they lapse."""
    now = now or timezone.now()
    changed = 0
    for acc in SocialAccount.objects.filter(status__in=('active', 'expiring')):
        adapter = get_adapter(acc.platform)
        try:
            if adapter.refresh(acc):
                acc.status, acc.last_error = 'active', ''
                acc.save()
                changed += 1
                continue
        except AuthError as exc:
            acc.status, acc.last_error = 'reconnect', exc.message
            acc.save(update_fields=['status', 'last_error'])
            changed += 1
            continue
        except AdapterError:
            continue
        if acc.expires_at and acc.expires_at <= now:
            acc.status = 'reconnect'
            acc.last_error = 'The sign-in expired.'
        elif acc.expires_at and acc.expires_at - now <= EXPIRY_WARNING:
            acc.status = 'expiring'
        else:
            continue
        acc.save(update_fields=['status', 'last_error'])
        changed += 1
    return changed


# ================================================================ calendar helpers

def posts_between(workspaces, start, end, platforms=None):
    qs = (Post.objects.filter(workspace__in=workspaces)
          .filter(Q(scheduled_at__gte=start, scheduled_at__lt=end) |
                  Q(scheduled_at__isnull=True, created_at__gte=start, created_at__lt=end))
          .select_related('workspace').prefetch_related('targets__account'))
    if platforms:
        qs = qs.filter(targets__account__platform__in=platforms).distinct()
    return qs


def attention(workspaces):
    """What needs a person: failed posts, posts waiting for approval, accounts to reconnect."""
    return {
        'failed': Post.objects.filter(workspace__in=workspaces, status__in=('failed', 'partial'))
        .select_related('workspace').prefetch_related('targets__account'),
        'review': Post.objects.filter(workspace__in=workspaces, status='review').count(),
        'accounts': SocialAccount.objects.filter(workspace__in=workspaces,
                                                 status__in=('expiring', 'reconnect'))
        .select_related('workspace'),
        'inbox': InboxItem.objects.filter(account__workspace__in=workspaces, status='open').count(),
    }
