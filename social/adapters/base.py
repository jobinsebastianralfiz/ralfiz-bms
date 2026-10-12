"""The one interface every platform implements.

The dashboard, the MCP tools and the worker only ever talk to an Adapter;
nothing outside social/adapters/ calls a platform API directly. Adapters are
stateless: every call gets the SocialAccount (with its decrypted token) it
acts for, and returns plain dataclasses the service layer stores.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

import requests

TIMEOUT = 30


# ---------------------------------------------------------------- errors

class AdapterError(Exception):
    """A platform call failed. ``retryable`` failures are tried again later."""

    def __init__(self, message, retryable=False):
        super().__init__(message)
        self.message = message
        self.retryable = retryable


class AuthError(AdapterError):
    """The token is expired or revoked: the account needs reconnecting."""


class RateLimited(AdapterError):
    def __init__(self, message, retry_after=900):
        super().__init__(message, retryable=True)
        self.retry_after = retry_after


class NotSupported(AdapterError):
    pass


# ---------------------------------------------------------------- data

@dataclass
class Capabilities:
    max_chars: int = 2200
    text_only: bool = True          # a post may have no media
    images: bool = True
    video: bool = True
    max_media: int = 1
    requires_media: bool = False
    first_comment: bool = False
    title: bool = False             # YouTube
    link: bool = True
    inbox: tuple = ()               # kinds this platform feeds into the inbox
    reply: bool = True
    insights: bool = True


@dataclass
class AccountCandidate:
    """An account found after sign-in, before the user picks which to connect."""
    external_id: str
    name: str
    handle: str = ''
    avatar_url: str = ''
    token: str = ''
    refresh_token: str = ''
    expires_at: Optional[datetime] = None
    extra: dict = field(default_factory=dict)


@dataclass
class MediaInput:
    kind: str                # image or video
    url: str                 # public, signed URL the platform can fetch
    content_type: str
    size: int
    name: str
    open: object = None      # callable returning a binary file object, for byte uploads


@dataclass
class PublishResult:
    external_id: str
    url: str = ''


@dataclass
class FetchedItem:
    kind: str                # comment, dm, review, mention
    external_id: str
    text: str
    author_name: str = ''
    author_id: str = ''
    thread_id: str = ''
    rating: Optional[int] = None
    permalink: str = ''
    received_at: Optional[datetime] = None
    raw: dict = field(default_factory=dict)


@dataclass
class FetchedPost:
    """A post already on the account (made in the platform's own app or by us)."""
    external_id: str
    text: str = ''
    published_at: Optional[datetime] = None
    url: str = ''
    kind: str = 'post'              # post, reel, video, carousel, story
    thumbnail_url: str = ''
    title: str = ''
    metrics: dict = field(default_factory=dict)   # likes, comments, shares, views, engagement


# ---------------------------------------------------------------- adapter

class Adapter:
    platform = ''
    label = ''
    caps = Capabilities()
    #: 'oauth' -> /social/connect/<platform>/ redirects to the platform;
    #: 'manual' -> a form asks for ids and a token (WhatsApp Cloud API).
    connect_mode = 'oauth'
    uses_pkce = False
    #: Settings that must be set before this platform can be connected.
    required_settings = ()

    # -- connecting
    def is_configured(self):
        from django.conf import settings
        return all(getattr(settings, name, '') for name in self.required_settings)

    def authorize_url(self, state, redirect_uri, code_challenge=None):
        raise NotSupported(f'{self.label} does not connect through OAuth.')

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        """Return the AccountCandidates the signed-in user can manage."""
        raise NotSupported(f'{self.label} does not connect through OAuth.')

    def manual_connect(self, data):
        """For connect_mode 'manual': validate the form data, return AccountCandidates."""
        raise NotSupported(f'{self.label} connects through OAuth.')

    def refresh(self, account):
        """Renew the token if it can be renewed. Return True if the account changed."""
        return False

    # -- publishing
    def validate(self, text, media, title='', first_comment=''):
        """Problems that would make the platform reject this post, in plain words."""
        c, problems = self.caps, []
        if len(text or '') > c.max_chars:
            problems.append(f'{self.label} allows {c.max_chars:,} characters; this is {len(text):,}.')
        if c.requires_media and not media:
            problems.append(f'{self.label} needs an image or video.')
        if not media and not (text or '').strip():
            problems.append(f'{self.label} post is empty.')
        if len(media) > c.max_media:
            problems.append(f'{self.label} takes at most {c.max_media} media file(s).')
        kinds = {m.kind for m in media}
        if 'video' in kinds and not c.video:
            problems.append(f'{self.label} does not take video here.')
        if 'image' in kinds and not c.images:
            problems.append(f'{self.label} needs a video, not an image.')
        if len(kinds) > 1:
            problems.append(f'{self.label}: use either images or one video, not both.')
        return problems

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        raise NotImplementedError

    def delete(self, account, external_id):
        raise NotSupported(f'{self.label} posts cannot be deleted from here.')

    # -- inbox
    def fetch_inbox(self, account, since=None):
        return []

    def reply(self, account, item, text):
        """Send a reply to an InboxItem. Return the reply's external id."""
        raise NotSupported(f'Replies are not supported on {self.label}.')

    # -- analytics
    def fetch_insights(self, account, start: date, end: date):
        """{date: {metric: value}} for each day in [start, end]."""
        return {}

    def fetch_post_metrics(self, account, external_id):
        return {}

    def fetch_posts(self, account, since=None, limit=50):
        """Recent posts on the account, newest first, stopping at ``since``."""
        return []

    def quota_status(self, account, published_last_24h):
        """(used, limit) for platforms that cap posts, else None."""
        return None


# ---------------------------------------------------------------- http

def call(method, url, *, platform='', auth_codes=(401,), **kwargs):
    """requests.request with a timeout and platform errors mapped to AdapterError."""
    kwargs.setdefault('timeout', TIMEOUT)
    try:
        r = requests.request(method, url, **kwargs)
    except requests.RequestException as exc:
        raise AdapterError(f'Could not reach {platform or url}: {exc.__class__.__name__}', retryable=True)
    if r.status_code < 400:
        return r
    message = _error_text(r)
    if r.status_code in auth_codes:
        raise AuthError(f'{platform} rejected the token: {message}')
    if r.status_code == 429:
        retry = r.headers.get('retry-after')
        raise RateLimited(f'{platform} rate limit: {message}',
                          retry_after=int(retry) if retry and retry.isdigit() else 900)
    raise AdapterError(f'{platform} error {r.status_code}: {message}', retryable=r.status_code >= 500)


def _error_text(r):
    try:
        data = r.json()
    except ValueError:
        return (r.text or '')[:300]
    err = data.get('error') if isinstance(data, dict) else None
    if isinstance(err, dict):
        return err.get('message') or err.get('error_user_msg') or str(err)[:300]
    if isinstance(err, str):
        return data.get('error_description') or err
    if isinstance(data, dict):
        if data.get('detail'):
            return str(data['detail'])
        if data.get('message'):
            return str(data['message'])
        if data.get('errors'):
            return str(data['errors'])[:300]
    return str(data)[:300]
