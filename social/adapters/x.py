"""X (Twitter), through API v2 with OAuth 2.0 user tokens (PKCE).

Platform quirks worth knowing:

* Access tokens live about 2 hours. ``offline.access`` gives a refresh token
  that rotates: every refresh returns a new one and the old one dies, so the
  new one must be stored straight away.
* The app is a confidential client, so the token endpoint takes HTTP Basic
  auth (client id + secret) as well as the PKCE ``code_verifier``.
* Media goes through the v2 upload endpoints (``media.write`` scope): a single
  request for images, and initialize / append / finalize (+ STATUS polling)
  for video. The v1.1 ``command=INIT`` style must not be used for writes.
* On pay-per-use access every read is billed, so the inbox and post metrics
  only run when SOCIAL_X_READS is on. Posting and replying are writes.
* A 429 carries ``x-rate-limit-reset`` (epoch seconds) instead of Retry-After.
* Every URL counts as 23 characters (t.co wrapping), whatever its length.
"""
import re
import time
from datetime import timedelta, timezone as dt_timezone
from urllib.parse import quote, urlencode

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .base import (AccountCandidate, Adapter, AdapterError, Capabilities, FetchedItem,
                   PublishResult, RateLimited, call)

AUTH_URL = 'https://x.com/i/oauth2/authorize'
API = 'https://api.x.com/2'
TOKEN_URL = f'{API}/oauth2/token'
SCOPES = 'tweet.read tweet.write users.read offline.access media.write'
REFRESH_WITHIN = timedelta(minutes=10)
CHUNK = 4 * 1024 * 1024        # append segments must stay at or under 5 MB
PROCESSING_TIMEOUT = 120       # seconds to wait for video processing
URL_RE = re.compile(r'https?://\S+')
URL_LENGTH = 23


def weighted_length(text):
    """Characters as X counts them, with every URL as 23.

    X also weights some scripts (CJK, emoji) as 2; that is not modelled here,
    so text in those scripts may pass this check and still be rejected.
    """
    text = text or ''
    urls = URL_RE.findall(text)
    return len(URL_RE.sub('', text)) + URL_LENGTH * len(urls)


def _with_link(text, link):
    """X has no separate link field: the link is appended to the text."""
    text = text or ''
    if link and link not in text:
        return f'{text}\n{link}'.strip()
    return text


class XAdapter(Adapter):
    platform = 'x'
    label = 'X'
    caps = Capabilities(max_chars=280, max_media=4, inbox=('mention',))
    required_settings = ('X_CLIENT_ID', 'X_CLIENT_SECRET')
    uses_pkce = True

    # ------------------------------------------------------------ http
    def _call(self, method, url, token=None, **kwargs):
        """call() plus X's rate-limit header, read through a requests response hook."""
        seen = {}
        kwargs['hooks'] = {'response': [lambda r, *a, **k: seen.__setitem__('r', r)]}
        if token:
            kwargs.setdefault('headers', {})['Authorization'] = f'Bearer {token}'
        try:
            return call(method, url, platform=self.label, **kwargs)
        except RateLimited as exc:
            reset = getattr(seen.get('r'), 'headers', {}).get('x-rate-limit-reset', '')
            if str(reset).isdigit():
                raise RateLimited(exc.message, retry_after=max(int(reset) - int(time.time()), 1))
            raise

    def _token_request(self, data, auth_codes=(401,)):
        return self._call('POST', TOKEN_URL, data={**data, 'client_id': settings.X_CLIENT_ID},
                          auth=(settings.X_CLIENT_ID, settings.X_CLIENT_SECRET),
                          auth_codes=auth_codes).json()

    def _reads_on(self):
        return bool(getattr(settings, 'SOCIAL_X_READS', False))

    # ------------------------------------------------------------ connecting
    def authorize_url(self, state, redirect_uri, code_challenge=None):
        return AUTH_URL + '?' + urlencode({
            'response_type': 'code', 'client_id': settings.X_CLIENT_ID,
            'redirect_uri': redirect_uri, 'scope': SCOPES, 'state': state,
            'code_challenge': code_challenge or '', 'code_challenge_method': 'S256',
        }, quote_via=quote)

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        data = self._token_request({'grant_type': 'authorization_code', 'code': code,
                                    'redirect_uri': redirect_uri, 'code_verifier': code_verifier or ''})
        token = data['access_token']
        me = self._call('GET', f'{API}/users/me?user.fields=profile_image_url', token).json()['data']
        return [AccountCandidate(
            external_id=str(me['id']),
            name=me.get('name') or me.get('username', ''),
            handle=f"@{me.get('username', '')}",
            avatar_url=me.get('profile_image_url', ''),
            token=token,
            refresh_token=data.get('refresh_token', ''),
            expires_at=timezone.now() + timedelta(seconds=int(data.get('expires_in') or 7200)),
        )]

    def refresh(self, account):
        """Renew within 10 minutes of expiry, storing the rotated refresh token."""
        if not account.refresh_token:
            return False
        if account.expires_at and account.expires_at - timezone.now() > REFRESH_WITHIN:
            return False
        # A used or revoked refresh token gets 400 invalid_grant: reconnect needed.
        data = self._token_request({'grant_type': 'refresh_token',
                                    'refresh_token': account.refresh_token}, auth_codes=(400, 401))
        account.token = data['access_token']
        account.expires_at = timezone.now() + timedelta(seconds=int(data.get('expires_in') or 7200))
        if data.get('refresh_token'):
            account.refresh_token = data['refresh_token']
        return True

    def _ensure_fresh(self, account):
        """Refresh before acting; save at once, since the old refresh token is now dead."""
        if self.refresh(account):
            account.save(update_fields=['token_encrypted', 'refresh_token_encrypted', 'expires_at'])

    # ------------------------------------------------------------ publishing
    def validate(self, text, media, title='', first_comment='', link=''):
        problems = super().validate(text, media, title=title, first_comment=first_comment)
        problems = [p for p in problems if 'characters' not in p]
        n = weighted_length(_with_link(text, link))
        if n > self.caps.max_chars:
            problems.append(f'X allows {self.caps.max_chars} characters (links count as 23); this is {n}.')
        if any(m.kind == 'video' for m in media) and len(media) > 1:
            problems.append('X takes up to 4 images or 1 video.')
        return problems

    def _upload_image(self, token, m):
        with m.open() as f:
            data = f.read()
        category = 'tweet_gif' if m.content_type == 'image/gif' else 'tweet_image'
        r = self._call('POST', f'{API}/media/upload', token, data={'media_category': category},
                       files={'media': (m.name, data, m.content_type)})
        return r.json()['data']['id']

    def _upload_video(self, token, m):
        """initialize, append 4 MB segments, finalize, then poll STATUS while processing."""
        init = self._call('POST', f'{API}/media/upload/initialize', token, json={
            'media_type': m.content_type, 'total_bytes': m.size, 'media_category': 'tweet_video',
        }).json()['data']
        media_id = init['id']
        with m.open() as f:
            index = 0
            while True:
                chunk = f.read(CHUNK)
                if not chunk:
                    break
                self._call('POST', f'{API}/media/upload/{media_id}/append', token,
                           data={'segment_index': index}, files={'media': ('chunk', chunk)})
                index += 1
        info = self._call('POST', f'{API}/media/upload/{media_id}/finalize',
                          token).json()['data'].get('processing_info')
        waited = 0
        while info and info.get('state') not in ('succeeded', None):
            if info.get('state') == 'failed':
                err = (info.get('error') or {}).get('message', 'processing failed')
                raise AdapterError(f'X could not process the video: {err}')
            if waited >= PROCESSING_TIMEOUT:
                raise AdapterError('X is still processing the video.', retryable=True)
            wait = max(1, min(int(info.get('check_after_secs') or 5), PROCESSING_TIMEOUT - waited))
            time.sleep(wait)
            waited += wait
            info = self._call('GET', f'{API}/media/upload?command=STATUS&media_id={media_id}',
                              token).json()['data'].get('processing_info')
        return media_id

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        self._ensure_fresh(account)
        token = account.token
        body = {'text': _with_link(text, link)}
        if media:
            if media[0].kind == 'video':
                ids = [self._upload_video(token, media[0])]
            else:
                ids = [self._upload_image(token, m) for m in media[:4]]
            body['media'] = {'media_ids': ids}
        tweet_id = self._call('POST', f'{API}/tweets', token, json=body).json()['data']['id']
        handle = (account.handle or '').lstrip('@') or 'i'
        return PublishResult(tweet_id, f'https://x.com/{handle}/status/{tweet_id}')

    def delete(self, account, external_id):
        self._ensure_fresh(account)
        self._call('DELETE', f'{API}/tweets/{external_id}', account.token)
        return True

    # ------------------------------------------------------------ inbox
    def fetch_inbox(self, account, since=None):
        """Mentions since the last sync. Off (no calls) unless SOCIAL_X_READS."""
        if not self._reads_on():
            return []
        self._ensure_fresh(account)
        params = {'expansions': 'author_id', 'tweet.fields': 'created_at,conversation_id',
                  'user.fields': 'username,name', 'max_results': 50}
        if since:
            params['start_time'] = since.astimezone(dt_timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        data = self._call('GET', f'{API}/users/{account.external_id}/mentions', account.token,
                          params=params).json()
        users = {u['id']: u for u in (data.get('includes') or {}).get('users', [])}
        items = []
        for t in data.get('data') or []:
            u = users.get(t.get('author_id'), {})
            username = u.get('username', '')
            items.append(FetchedItem(
                kind='mention',
                external_id=t['id'],
                text=t.get('text', ''),
                author_id=t.get('author_id', ''),
                author_name=f'@{username}' if username else u.get('name', ''),
                thread_id=t.get('conversation_id', ''),
                permalink=f'https://x.com/{username or "i"}/status/{t["id"]}',
                received_at=parse_datetime(t['created_at']) if t.get('created_at') else None,
                raw=t,
            ))
        return items

    def reply(self, account, item, text):
        """A write, so allowed whatever SOCIAL_X_READS says."""
        self._ensure_fresh(account)
        r = self._call('POST', f'{API}/tweets', account.token,
                       json={'text': text, 'reply': {'in_reply_to_tweet_id': item.external_id}})
        return r.json()['data']['id']

    # ------------------------------------------------------------ analytics
    def fetch_insights(self, account, start, end):
        """X v2 has no account-level daily metrics on pay-per-use access."""
        return {}

    def fetch_post_metrics(self, account, external_id):
        if not self._reads_on():
            return {}
        self._ensure_fresh(account)
        m = self._call('GET', f'{API}/tweets/{external_id}?tweet.fields=public_metrics',
                       account.token).json()['data'].get('public_metrics') or {}
        return {
            'reach': int(m.get('impression_count') or 0),
            'engagement': sum(int(m.get(k) or 0) for k in
                              ('like_count', 'reply_count', 'retweet_count', 'quote_count')),
        }
