"""Facebook Pages and Instagram (Business, linked to a Page) through the Graph API.

Both connect with Facebook Login: the user's long-lived token lists the Pages
they manage, and each Page's own token is stored. A Page token derived from a
long-lived user token does not expire, so nothing is ever refreshed; when the
user changes their password or removes the app, Graph answers error 190 and
the account is marked "Reconnect needed".

Graph quirks handled here:
- An expired token comes back as HTTP 400 with error code 190, not 401, and
  rate limits come back as 400/403 with codes 4/17/32/613, not 429. The
  ``_graph_error`` response hook turns those into AuthError / RateLimited
  before ``call()`` sees the status code.
- Instagram publishes in two steps (create a container, then publish it) and
  video containers process asynchronously, so they are polled.
"""
import json
import logging
import time
from datetime import datetime, time as dtime, timedelta, timezone as dt_timezone
from urllib.parse import urlencode

from django.conf import settings
from django.utils.dateparse import parse_datetime

from .base import (AccountCandidate, Adapter, AdapterError, AuthError, Capabilities, FetchedItem,
                   FetchedPost, NotSupported, PublishResult, RateLimited, call)

log = logging.getLogger(__name__)

GRAPH = 'https://graph.facebook.com'
#: Graph error codes meaning the token is dead (expired, revoked, password changed).
AUTH_CODES = {190, 102, 2500}
#: Graph throttling codes (app, user, page, and per-call limits).
RATE_CODES = {4, 17, 32, 613, 80001}
#: Transient server-side failures that are worth retrying.
TRANSIENT_CODES = {1, 2}


# ---------------------------------------------------------------- graph http

def _version():
    return getattr(settings, 'META_GRAPH_VERSION', '') or 'v23.0'


def graph_url(path):
    return f'{GRAPH}/{_version()}/{path.lstrip("/")}'


def _graph_error(r, *args, **kwargs):
    """requests response hook: map Graph's error codes, which hide behind HTTP 400."""
    if r.status_code < 400:
        return r
    try:
        err = r.json().get('error') or {}
    except (ValueError, AttributeError):
        return r
    if not isinstance(err, dict):
        return r
    code, message = err.get('code'), err.get('message') or 'Graph API error'
    if code in AUTH_CODES:
        raise AuthError(f'Meta rejected the token: {message}')
    if code in RATE_CODES:
        raise RateLimited(f'Meta rate limit: {message}')
    if code in TRANSIENT_CODES or err.get('is_transient'):
        raise AdapterError(f'Meta temporary error: {message}', retryable=True)
    return r


def graph(method, path, token='', *, platform='Meta', **kwargs):
    """One Graph API call; returns the decoded JSON body.

    The token goes in the Authorization header so it never lands in URLs or logs.
    """
    headers = dict(kwargs.pop('headers', None) or {})
    if token:
        headers['Authorization'] = f'Bearer {token}'
    r = call(method, graph_url(path), platform=platform, headers=headers,
             hooks={'response': _graph_error}, **kwargs)
    try:
        return r.json()
    except ValueError:
        return {}


def _parse_time(value):
    """Graph timestamps look like 2026-10-01T09:30:00+0000; webhooks use unix seconds."""
    if value in (None, ''):
        return None
    if isinstance(value, (int, float)) or str(value).isdigit():
        value = float(value)
        if value > 1e11:            # milliseconds (Messenger webhooks)
            value /= 1000
        return datetime.fromtimestamp(value, tz=dt_timezone.utc)
    return parse_datetime(str(value))


def _newer(when, since):
    return since is None or when is None or when > since


def _day_bounds(day):
    start = datetime.combine(day, dtime.min, tzinfo=dt_timezone.utc)
    return int(start.timestamp()), int((start + timedelta(days=1)).timestamp())


# ---------------------------------------------------------------- oauth (shared)

class _MetaAdapter(Adapter):
    required_settings = ('META_APP_ID', 'META_APP_SECRET')
    scopes = ()

    def authorize_url(self, state, redirect_uri, code_challenge=None):
        """Facebook Login dialog. If META_LOGIN_CONFIG_ID is set (a Facebook Login for
        Business configuration), it is sent instead of the scope list."""
        params = {'client_id': settings.META_APP_ID, 'redirect_uri': redirect_uri,
                  'state': state, 'response_type': 'code'}
        config_id = getattr(settings, 'META_LOGIN_CONFIG_ID', '')
        if config_id:
            params['config_id'] = config_id
        else:
            params['scope'] = ','.join(self.scopes)
        return f'https://www.facebook.com/{_version()}/dialog/oauth?{urlencode(params)}'

    def _pages(self, code, redirect_uri):
        """code -> short-lived user token -> long-lived user token -> managed Pages."""
        creds = {'client_id': settings.META_APP_ID, 'client_secret': settings.META_APP_SECRET}
        short = graph('GET', 'oauth/access_token', platform=self.label,
                      params={**creds, 'redirect_uri': redirect_uri, 'code': code})
        long = graph('GET', 'oauth/access_token', platform=self.label,
                     params={**creds, 'grant_type': 'fb_exchange_token',
                             'fb_exchange_token': short['access_token']})
        user_token = long.get('access_token') or short['access_token']
        fields = ('id,name,access_token,picture{url},'
                  'instagram_business_account{id,username,name,profile_picture_url}')
        pages, path, params = [], 'me/accounts', {'fields': fields, 'limit': 100}
        for _ in range(10):                      # follow paging, bounded
            data = graph('GET', path, user_token, platform=self.label, params=params)
            pages += data.get('data', [])
            after = (data.get('paging') or {}).get('cursors', {}).get('after')
            if not after or not (data.get('paging') or {}).get('next'):
                break
            params = {**params, 'after': after}
        return pages

    def refresh(self, account):
        """Page tokens from a long-lived user token never expire; a dead one raises AuthError."""
        return False

    def _page_id(self, account):
        return account.extra.get('page_id') or account.external_id

    def _send_message(self, account, recipient_id, text):
        """Messenger Send API (also used for Instagram DMs, through the linked Page)."""
        data = graph('POST', f'{self._page_id(account)}/messages', account.token, platform=self.label,
                     data={'recipient': json.dumps({'id': recipient_id}),
                           'messaging_type': 'RESPONSE',
                           'message': json.dumps({'text': text})})
        return data.get('message_id', '')

    @staticmethod
    def _message(text, buttons=None):
        """Plain text, or a button template. A button is {'title', 'url'} or {'title', 'payload'}."""
        if not buttons:
            return {'text': text}
        return {'attachment': {'type': 'template', 'payload': {
            'template_type': 'button', 'text': text,
            'buttons': [{'type': 'web_url', 'url': b['url'], 'title': b['title']} if b.get('url')
                        else {'type': 'postback', 'payload': b['payload'], 'title': b['title']}
                        for b in buttons]}}}

    def private_reply(self, account, comment_id, text, buttons=None):
        """Messenger private reply: addressed to the comment, allowed once per comment and only
        for about seven days after it. Works for Instagram comments through the linked Page."""
        data = graph('POST', f'{self._page_id(account)}/messages', account.token, platform=self.label,
                     data={'recipient': json.dumps({'comment_id': comment_id}),
                           'message': json.dumps(self._message(text, buttons))})
        return data.get('message_id', '')

    def send_dm(self, account, user_id, text, buttons=None):
        """A message inside the 24-hour window the person opened by writing or tapping a button."""
        data = graph('POST', f'{self._page_id(account)}/messages', account.token, platform=self.label,
                     data={'recipient': json.dumps({'id': user_id}), 'messaging_type': 'RESPONSE',
                           'message': json.dumps(self._message(text, buttons))})
        return data.get('message_id', '')

    def user_profile(self, account, user_id):
        """Name and, on Instagram, whether they follow the account. Only answers for people who
        have messaged the account or tapped one of its buttons."""
        if self.platform == 'instagram':
            data = graph('GET', user_id, account.token, platform=self.label,
                         params={'fields': 'name,username,is_user_follow_business'})
            return {'name': data.get('name', ''), 'username': data.get('username', ''),
                    'is_follower': data.get('is_user_follow_business')}
        data = graph('GET', user_id, account.token, platform=self.label, params={'fields': 'name'})
        return {'name': data.get('name', ''), 'username': '', 'is_follower': None}

    def _conversations(self, account, since, platform=None):
        """Recent DMs from the Page's conversations; the business's own messages are skipped."""
        params = {'fields': 'id,updated_time,messages.limit(10){id,message,from,created_time}',
                  'limit': 25}
        if platform:
            params['platform'] = platform
        own = {self._page_id(account), account.external_id}
        data = graph('GET', f'{self._page_id(account)}/conversations', account.token,
                     platform=self.label, params=params)
        items = []
        for conv in data.get('data', []):
            if not _newer(_parse_time(conv.get('updated_time')), since):
                continue
            for m in (conv.get('messages') or {}).get('data', []):
                sender = m.get('from') or {}
                when = _parse_time(m.get('created_time'))
                if sender.get('id') in own or not _newer(when, since):
                    continue
                items.append(FetchedItem(
                    kind='dm', external_id=m['id'], text=m.get('message') or '[attachment]',
                    author_name=sender.get('name') or sender.get('username') or '',
                    author_id=sender.get('id', ''), thread_id=conv['id'], received_at=when, raw=m))
        return items


# ---------------------------------------------------------------- facebook

class FacebookAdapter(_MetaAdapter):
    platform = 'facebook'
    label = 'Facebook'
    caps = Capabilities(max_chars=63206, max_media=10, first_comment=True, inbox=('comment', 'dm'))
    scopes = ('pages_show_list', 'pages_read_engagement', 'pages_manage_posts',
              'pages_manage_engagement', 'pages_read_user_content', 'read_insights',
              'pages_messaging', 'business_management')

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        return [AccountCandidate(
            external_id=p['id'], name=p.get('name', p['id']), token=p['access_token'],
            avatar_url=((p.get('picture') or {}).get('data') or {}).get('url', ''),
            expires_at=None, extra={'page_id': p['id']},
        ) for p in self._pages(code, redirect_uri) if p.get('access_token')]

    def validate(self, text, media, title='', first_comment=''):
        problems = super().validate(text, media, title=title, first_comment=first_comment)
        if sum(m.kind == 'video' for m in media) > 1:
            problems.append('Facebook takes one video per post.')
        return problems

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        page, tok, label = self._page_id(account), account.token, self.label
        if media and link:
            text = f'{text}\n\n{link}'.strip()     # only /feed takes a link preview
        if not media:
            data = {'message': text}
            if link:
                data['link'] = link
            post_id = graph('POST', f'{page}/feed', tok, platform=label, data=data)['id']
        elif media[0].kind == 'video':
            post_id = graph('POST', f'{page}/videos', tok, platform=label,
                            data={'file_url': media[0].url, 'description': text,
                                  **({'title': title} if title else {})})['id']
        elif len(media) == 1:
            r = graph('POST', f'{page}/photos', tok, platform=label,
                      data={'url': media[0].url, 'caption': text})
            post_id = r.get('post_id') or r['id']
        else:
            # Multi-photo: upload each photo unpublished, then one feed post attaching them all.
            data = {'message': text}
            for i, m in enumerate(media):
                photo = graph('POST', f'{page}/photos', tok, platform=label,
                              data={'url': m.url, 'published': 'false'})
                data[f'attached_media[{i}]'] = json.dumps({'media_fbid': photo['id']})
            post_id = graph('POST', f'{page}/feed', tok, platform=label, data=data)['id']
        if first_comment:
            try:
                graph('POST', f'{post_id}/comments', tok, platform=label, data={'message': first_comment})
            except AdapterError as exc:     # the post is live; a missing comment must not fail it
                log.warning('Facebook first comment on %s failed: %s', post_id, exc.message)
        return PublishResult(post_id, f'https://www.facebook.com/{post_id}')

    def delete(self, account, external_id):
        graph('DELETE', external_id, account.token, platform=self.label)
        return True

    def fetch_inbox(self, account, since=None):
        """Comments on the 15 most recent Page posts, plus Messenger conversations.

        ``from`` on comments needs pages_read_user_content; without it the author is blank.
        """
        page = self._page_id(account)
        data = graph('GET', f'{page}/posts', account.token, platform=self.label, params={
            'fields': 'id,permalink_url,comments.order(reverse_chronological).limit(50)'
                      '{id,message,from,created_time,permalink_url}',
            'limit': 15})
        items = []
        for post in data.get('data', []):
            for c in (post.get('comments') or {}).get('data', []):
                who, when = c.get('from') or {}, _parse_time(c.get('created_time'))
                if who.get('id') == page or not _newer(when, since):
                    continue
                items.append(FetchedItem(
                    kind='comment', external_id=c['id'], text=c.get('message', ''),
                    author_name=who.get('name', ''), author_id=who.get('id', ''), thread_id=post['id'],
                    permalink=c.get('permalink_url') or post.get('permalink_url') or '',
                    received_at=when, raw=c))
        return items + self._conversations(account, since)

    def reply(self, account, item, text):
        if item.kind == 'dm':
            return self._send_message(account, item.author_id, text)
        return graph('POST', f'{item.external_id}/comments', account.token, platform=self.label,
                     data={'message': text}).get('id', '')

    #: Graph metric -> our metric. page_impressions* were deprecated in 2025;
    #: the "media view" metrics replaced them. page_follows replaced page_fans.
    PAGE_METRICS = {
        'page_total_media_view_unique': 'reach',
        'page_media_view': 'views',
        'page_post_engagements': 'engagement',
        'page_follows': 'followers',
    }

    def fetch_insights(self, account, start, end):
        page, out = self._page_id(account), {}
        params = {'period': 'day', 'since': start.isoformat(),
                  'until': (end + timedelta(days=1)).isoformat()}
        try:
            series = [graph('GET', f'{page}/insights', account.token, platform=self.label,
                            params={**params, 'metric': ','.join(self.PAGE_METRICS)})]
        except (AuthError, RateLimited):
            raise
        except AdapterError:
            # One renamed/deprecated metric fails the whole request: fetch one by one, skip bad ones.
            series = []
            for metric in self.PAGE_METRICS:
                try:
                    series.append(graph('GET', f'{page}/insights', account.token, platform=self.label,
                                        params={**params, 'metric': metric}))
                except (AuthError, RateLimited):
                    raise
                except AdapterError as exc:
                    log.info('Facebook metric %s unavailable: %s', metric, exc.message)
        for data in series:
            for row in data.get('data', []):
                ours = self.PAGE_METRICS.get(row.get('name'))
                for v in row.get('values', []):
                    when = _parse_time(v.get('end_time'))
                    # end_time is the end of the day the value covers (midnight Pacific).
                    day = (when - timedelta(days=1)).date() if when else None
                    if ours and day and start <= day <= end and isinstance(v.get('value'), (int, float)):
                        out.setdefault(day, {})[ours] = int(v['value'])
        return out

    def fetch_post_metrics(self, account, external_id):
        tok, out = account.token, {}
        post = graph('GET', external_id, tok, platform=self.label, params={
            'fields': 'reactions.summary(total_count).limit(0),comments.summary(total_count).limit(0),shares'})
        out['engagement'] = (((post.get('reactions') or {}).get('summary') or {}).get('total_count', 0)
                             + ((post.get('comments') or {}).get('summary') or {}).get('total_count', 0)
                             + (post.get('shares') or {}).get('count', 0))
        names = {'post_total_media_view_unique': 'reach', 'post_media_view': 'views', 'post_clicks': 'clicks'}
        try:
            data = graph('GET', f'{external_id}/insights', tok, platform=self.label,
                         params={'metric': ','.join(names)})
        except (AuthError, RateLimited):
            raise
        except AdapterError:
            return out          # e.g. video ids, or a metric renamed again
        for row in data.get('data', []):
            values = row.get('values') or [{}]
            if row.get('name') in names and isinstance(values[0].get('value'), (int, float)):
                out[names[row['name']]] = int(values[0]['value'])
        return out

    def fetch_posts(self, account, since=None, limit=50):
        """The Page's own posts, including ones made in Facebook itself.

        Counts come from the post's fields (reactions, comments, shares) in the
        same call; reach and views arrive later through fetch_post_metrics.
        """
        data = graph('GET', f'{self._page_id(account)}/published_posts', account.token, platform=self.label,
                     params={'fields': 'id,message,created_time,permalink_url,full_picture,status_type,'
                                       'attachments{media_type,type},'
                                       'reactions.summary(total_count).limit(0),'
                                       'comments.summary(total_count).limit(0),shares',
                             'limit': min(limit, 100)})
        out = []
        for p in data.get('data', []):
            when = _parse_time(p.get('created_time'))
            if not _newer(when, since):
                break
            att = ((p.get('attachments') or {}).get('data') or [{}])[0]
            media_type, url = (att.get('media_type') or '').lower(), p.get('permalink_url') or ''
            kind = ('reel' if '/reel/' in url else 'video' if media_type == 'video'
                    else 'carousel' if media_type == 'album' else 'post')
            likes = ((p.get('reactions') or {}).get('summary') or {}).get('total_count', 0)
            comments = ((p.get('comments') or {}).get('summary') or {}).get('total_count', 0)
            shares = (p.get('shares') or {}).get('count', 0)
            out.append(FetchedPost(external_id=p['id'], text=p.get('message', ''), published_at=when, url=url,
                                   kind=kind, thumbnail_url=p.get('full_picture', ''),
                                   metrics={'likes': likes, 'comments': comments, 'shares': shares,
                                            'engagement': likes + comments + shares}))
        return out


# ---------------------------------------------------------------- instagram

class InstagramAdapter(_MetaAdapter):
    """Instagram professional accounts linked to a Facebook Page (Facebook Login flavour).

    The account's external_id is the IG user id; extra['page_id'] is the linked Page,
    whose token is stored and which carries Instagram DMs.
    """
    platform = 'instagram'
    label = 'Instagram'
    caps = Capabilities(requires_media=True, max_chars=2200, max_media=10, text_only=False,
                        first_comment=True, link=False, inbox=('comment', 'dm'))
    scopes = FacebookAdapter.scopes + (
        'instagram_basic', 'instagram_content_publish', 'instagram_manage_comments',
        'instagram_manage_insights', 'instagram_manage_messages')
    #: Container polling: ~120 s in all. Meta suggests polling up to 5 minutes;
    #: a still-processing video is retried later with a fresh container.
    POLL_TRIES = 24
    POLL_SECONDS = 5
    DAILY_LIMIT = 50    # verify with GET /{ig}/content_publishing_limit (docs also say 100)

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        out = []
        for p in self._pages(code, redirect_uri):
            ig = p.get('instagram_business_account')
            if not ig or not p.get('access_token'):
                continue
            username = ig.get('username', '')
            out.append(AccountCandidate(
                external_id=ig['id'], name=ig.get('name') or username or p.get('name', ig['id']),
                handle=f'@{username}' if username else '', avatar_url=ig.get('profile_picture_url', ''),
                token=p['access_token'], expires_at=None, extra={'page_id': p['id']}))
        return out

    def quota_status(self, account, published_last_24h):
        return (published_last_24h, self.DAILY_LIMIT)

    def _container(self, account, **data):
        return graph('POST', f'{account.external_id}/media', account.token, platform=self.label,
                     data=data)['id']

    def _wait(self, account, container_id):
        """Wait until a container is FINISHED. Video processing takes a while."""
        for attempt in range(self.POLL_TRIES):
            data = graph('GET', container_id, account.token, platform=self.label,
                         params={'fields': 'status_code,status'})
            code = data.get('status_code')
            if code in ('FINISHED', 'PUBLISHED'):
                return
            if code in ('ERROR', 'EXPIRED'):
                raise AdapterError(f'Instagram could not process the media: {data.get("status") or code}')
            time.sleep(self.POLL_SECONDS)
        raise AdapterError('Instagram is still processing the video; will try again.', retryable=True)

    def _child(self, account, m):
        if m.kind == 'video':
            return self._container(account, media_type='VIDEO', video_url=m.url, is_carousel_item='true')
        return self._container(account, image_url=m.url, is_carousel_item='true')

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        if not media:
            raise AdapterError('Instagram needs an image or video.')
        if len(media) > 1:
            children = [self._child(account, m) for m in media]
            for child in children:
                self._wait(account, child)
            container = self._container(account, media_type='CAROUSEL', caption=text,
                                        children=','.join(children))
        elif media[0].kind == 'video':
            container = self._container(account, media_type='REELS', video_url=media[0].url, caption=text)
        else:
            container = self._container(account, image_url=media[0].url, caption=text)
        self._wait(account, container)
        media_id = graph('POST', f'{account.external_id}/media_publish', account.token, platform=self.label,
                         data={'creation_id': container})['id']
        if first_comment:
            try:
                graph('POST', f'{media_id}/comments', account.token, platform=self.label,
                      data={'message': first_comment})
            except AdapterError as exc:
                log.warning('Instagram first comment on %s failed: %s', media_id, exc.message)
        try:
            permalink = graph('GET', media_id, account.token, platform=self.label,
                              params={'fields': 'permalink'}).get('permalink', '')
        except AdapterError:
            permalink = ''
        return PublishResult(media_id, permalink)

    def fetch_inbox(self, account, since=None):
        """Comments on the 15 most recent media, plus DMs via the linked Page."""
        handle = account.handle.lstrip('@')
        data = graph('GET', f'{account.external_id}/media', account.token, platform=self.label, params={
            'fields': 'id,permalink,timestamp,comments.limit(50){id,text,username,from,timestamp}',
            'limit': 15})
        items = []
        for media in data.get('data', []):
            for c in (media.get('comments') or {}).get('data', []):
                who = c.get('from') or {}
                username = c.get('username') or who.get('username', '')
                when = _parse_time(c.get('timestamp'))
                if who.get('id') == account.external_id or (handle and username == handle) \
                        or not _newer(when, since):
                    continue
                items.append(FetchedItem(
                    kind='comment', external_id=c['id'], text=c.get('text', ''), author_name=username,
                    author_id=who.get('id', ''), thread_id=media['id'],
                    permalink=media.get('permalink', ''), received_at=when, raw=c))
        if account.extra.get('page_id'):
            items += self._conversations(account, since, platform='instagram')
        return items

    def reply(self, account, item, text):
        if item.kind == 'dm':
            return self._send_message(account, item.author_id, text)
        return graph('POST', f'{item.external_id}/replies', account.token, platform=self.label,
                     data={'message': text}).get('id', '')

    #: Instagram "impressions" is gone (v22+); "views" replaced it. total_value metrics
    #: give one number per since/until window, so each day is asked for separately.
    DAY_METRICS = {'reach': 'reach', 'views': 'views', 'total_interactions': 'engagement'}

    def fetch_insights(self, account, start, end):
        out, day, now = {}, start, int(datetime.now(dt_timezone.utc).timestamp())
        while day <= end:
            since, until = _day_bounds(day)
            if since >= now:
                break
            data = graph('GET', f'{account.external_id}/insights', account.token, platform=self.label,
                         params={'metric': ','.join(self.DAY_METRICS), 'metric_type': 'total_value',
                                 'period': 'day', 'since': since, 'until': min(until, now)})
            for row in data.get('data', []):
                value = (row.get('total_value') or {}).get('value')
                if row.get('name') in self.DAY_METRICS and isinstance(value, (int, float)):
                    out.setdefault(day, {})[self.DAY_METRICS[row['name']]] = int(value)
            day += timedelta(days=1)
        # The follower count is a current snapshot, recorded against the last day.
        profile = graph('GET', account.external_id, account.token, platform=self.label,
                        params={'fields': 'followers_count'})
        if isinstance(profile.get('followers_count'), int):
            out.setdefault(end, {})['followers'] = profile['followers_count']
        return out

    def fetch_post_metrics(self, account, external_id):
        names = {'reach': 'reach', 'total_interactions': 'engagement', 'views': 'views'}
        data = graph('GET', f'{external_id}/insights', account.token, platform=self.label,
                     params={'metric': ','.join(names)})
        out = {}
        for row in data.get('data', []):
            values = row.get('values') or [{}]
            value = values[0].get('value', (row.get('total_value') or {}).get('value'))
            if row.get('name') in names and isinstance(value, (int, float)):
                out[names[row['name']]] = int(value)
        return out

    def fetch_posts(self, account, since=None, limit=50):
        """Feed posts, Reels, carousels and live Stories on the account."""
        data = graph('GET', f'{account.external_id}/media', account.token, platform=self.label,
                     params={'fields': 'id,caption,media_type,media_product_type,media_url,thumbnail_url,'
                                       'permalink,timestamp,like_count,comments_count',
                             'limit': min(limit, 100)})
        out = []
        for m in data.get('data', []):
            when = _parse_time(m.get('timestamp'))
            if not _newer(when, since):
                break
            product, media_type = m.get('media_product_type', ''), m.get('media_type', '')
            kind = ('reel' if product == 'REELS' else 'story' if product == 'STORY'
                    else 'carousel' if media_type == 'CAROUSEL_ALBUM' else 'video' if media_type == 'VIDEO'
                    else 'post')
            likes, comments = m.get('like_count') or 0, m.get('comments_count') or 0
            out.append(FetchedPost(external_id=m['id'], text=m.get('caption', ''), published_at=when,
                                   url=m.get('permalink', ''), kind=kind,
                                   thumbnail_url=m.get('thumbnail_url') or m.get('media_url', ''),
                                   metrics={'likes': likes, 'comments': comments, 'engagement': likes + comments}))
        return out

    def delete(self, account, external_id):
        raise NotSupported('Instagram posts cannot be deleted through the API; delete it in the app.')
