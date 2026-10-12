"""YouTube and Google Business Profile, both signed in through Google OAuth.

One Google sign-in (offline access, so we get a refresh token) gives an
access token that lives about an hour. Every API method first calls
``_ensure_fresh`` so a worker never uses an expired token; ``refresh`` is
also what ``services.refresh_tokens`` calls on its schedule.

Business Profile is split across several Google services (checked against
developers.google.com/my-business, October 2026):

- mybusinessaccountmanagement v1: the accounts a user can manage
- mybusinessbusinessinformation v1: the locations of an account
- mybusiness v4 (legacy, still the only home of): localPosts and reviews;
  its paths are ``accounts/{a}/locations/{l}/...``, so we keep both names
- businessprofileperformance v1: daily impressions, clicks, calls

Note: a new Google Cloud project gets a quota of 0 on the Business Profile
APIs until Google approves its access request.

Comment and review text written by outsiders is stored as data only; it is
never interpreted.
"""
import re
from datetime import date, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .base import (AccountCandidate, Adapter, AdapterError, AuthError, Capabilities, FetchedItem,
                   FetchedPost, PublishResult, RateLimited, call)

AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
REFRESH_MARGIN = timedelta(minutes=10)
MAX_PAGES = 5


def _ts(value):
    """RFC 3339 -> aware datetime. Google sends up to 9 fractional digits; Python takes 6."""
    if not value:
        return None
    return parse_datetime(re.sub(r'(\.\d{6})\d+', r'\1', value))


class GoogleOAuthAdapter(Adapter):
    """Google's OAuth 2.0 web-server flow, shared by YouTube and Business Profile."""
    required_settings = ('GOOGLE_OAUTH_CLIENT_ID', 'GOOGLE_OAUTH_CLIENT_SECRET')
    uses_pkce = True
    scopes = ()

    # -- connecting
    def authorize_url(self, state, redirect_uri, code_challenge=None):
        params = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'state': state,
            # offline + consent: Google only returns a refresh token when the
            # consent screen is shown, so ask every time.
            'access_type': 'offline',
            'prompt': 'consent',
            'include_granted_scopes': 'true',
        }
        if code_challenge:
            params.update(code_challenge=code_challenge, code_challenge_method='S256')
        return f'{AUTH_URL}?{urlencode(params)}'

    def _token_request(self, data, auth_codes=(401,)):
        data = {**data, 'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET}
        tok = call('POST', TOKEN_URL, platform=self.label, data=data, auth_codes=auth_codes).json()
        expires = tok.get('expires_in')
        return tok, (timezone.now() + timedelta(seconds=int(expires)) if expires else None)

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        data = {'code': code, 'redirect_uri': redirect_uri, 'grant_type': 'authorization_code'}
        if code_verifier:
            data['code_verifier'] = code_verifier
        tok, expires_at = self._token_request(data)
        candidates = self._candidates(tok['access_token'])
        for c in candidates:
            c.token, c.refresh_token, c.expires_at = tok['access_token'], tok.get('refresh_token', ''), expires_at
        return candidates

    def _candidates(self, token):
        raise NotImplementedError

    def refresh(self, account):
        """Renew the access token when it is within 10 minutes of expiry (or unknown).

        A revoked or expired refresh token comes back as 400 ``invalid_grant``
        (Google also uses 400 for refresh tokens of apps left in "Testing",
        which die after 7 days), so 400 and 401 both mean "reconnect".
        """
        if not account.refresh_token:
            return False
        if account.expires_at and account.expires_at - timezone.now() > REFRESH_MARGIN:
            return False
        tok, expires_at = self._token_request(
            {'grant_type': 'refresh_token', 'refresh_token': account.refresh_token},
            auth_codes=(400, 401))
        account.token = tok['access_token']
        account.expires_at = expires_at
        if tok.get('refresh_token'):  # Google normally keeps the old one
            account.refresh_token = tok['refresh_token']
        return True

    def _ensure_fresh(self, account):
        if self.refresh(account) and not account._state.adding:
            account.save(update_fields=['token_encrypted', 'refresh_token_encrypted', 'expires_at'])

    def _api(self, method, url, account=None, token=None, **kwargs):
        """An authorised call. Pass ``account`` (refreshed first) or a bare ``token``."""
        if account is not None:
            self._ensure_fresh(account)
            token = account.token
        headers = {'Authorization': f'Bearer {token}', **kwargs.pop('headers', {})}
        return call(method, url, platform=self.label, headers=headers, **kwargs)


# ================================================================ YouTube

YT = 'https://www.googleapis.com/youtube/v3'
YT_UPLOAD = 'https://www.googleapis.com/upload/youtube/v3/videos'
YT_ANALYTICS = 'https://youtubeanalytics.googleapis.com/v2/reports'
QUOTA_RETRY = 4 * 3600  # the daily quota resets at midnight Pacific time


class YouTubeAdapter(GoogleOAuthAdapter):
    """Uploads videos, answers comments, reads channel analytics.

    An upload costs ~1,600 of the default 10,000 daily quota units, so a
    project can upload about six videos a day before Google approves more.
    Videos uploaded by an unaudited API project are locked to private; the
    project must pass Google's audit for public uploads to stay public.
    """
    platform = 'youtube'
    label = 'YouTube'
    scopes = (
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube.force-ssl',
        'https://www.googleapis.com/auth/yt-analytics.readonly',
        'https://www.googleapis.com/auth/youtube.readonly',
    )
    caps = Capabilities(max_chars=5000, text_only=False, images=False, video=True, max_media=1,
                        requires_media=True, title=True, link=False, inbox=('comment',))

    def _api(self, method, url, account=None, token=None, **kwargs):
        """Quota exhaustion is a 403 (reason quotaExceeded): retry in a few hours, not fail."""
        try:
            return super()._api(method, url, account, token, **kwargs)
        except AuthError:
            raise
        except AdapterError as exc:
            # call() keeps only error.message; Google's says "...exceeded your quota".
            if ' 403:' in exc.message and 'quota' in exc.message.lower():
                raise RateLimited(f'YouTube daily quota used up: {exc.message}', retry_after=QUOTA_RETRY)
            raise

    def _candidates(self, token):
        data = self._api('GET', f'{YT}/channels', token=token,
                         params={'part': 'snippet', 'mine': 'true'}).json()
        out = []
        for ch in data.get('items', []):
            sn = ch.get('snippet', {})
            out.append(AccountCandidate(
                external_id=ch['id'], name=sn.get('title', ch['id']), handle=sn.get('customUrl', ''),
                avatar_url=sn.get('thumbnails', {}).get('default', {}).get('url', '')))
        return out

    # -- publishing
    @staticmethod
    def _title(title, text):
        return (title or (text or '').strip().split('\n', 1)[0]).strip()[:100]

    def validate(self, text, media, title='', first_comment=''):
        problems = [p for p in super().validate(text, media, title, first_comment)
                    if 'needs an image or video' not in p]
        if not media:
            problems.append('YouTube needs a video.')
        if len(title or '') > 100:
            problems.append(f'YouTube titles allow 100 characters; this is {len(title)}.')
        if not self._title(title, text):
            problems.append('YouTube needs a title.')
        return problems

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        """Resumable upload: POST the metadata, then PUT the bytes to the session URL."""
        videos = [m for m in media if m.kind == 'video']
        if len(videos) != 1:
            raise AdapterError('YouTube needs exactly one video.')
        video = videos[0]
        if not video.open:
            raise AdapterError('The video file cannot be read for upload.')
        # YouTube rejects '<' and '>' in titles and descriptions.
        clean = lambda s: (s or '').replace('<', '‹').replace('>', '›')
        meta = {
            'snippet': {'title': clean(self._title(title, text)), 'description': clean(text)[:5000]},
            'status': {'privacyStatus': (options or {}).get('privacy', 'public'),
                       'selfDeclaredMadeForKids': False},
        }
        r = self._api('POST', YT_UPLOAD, account, json=meta,
                      params={'uploadType': 'resumable', 'part': 'snippet,status'},
                      headers={'X-Upload-Content-Type': video.content_type,
                               'X-Upload-Content-Length': str(video.size)})
        session = r.headers.get('Location')
        if not session:
            raise AdapterError('YouTube did not start the upload.', retryable=True)
        with video.open() as fh:
            data = self._api('PUT', session, account, data=fh, timeout=(30, 900),
                             headers={'Content-Type': video.content_type,
                                      'Content-Length': str(video.size)}).json()
        return PublishResult(data['id'], f'https://youtu.be/{data["id"]}')

    def delete(self, account, external_id):
        self._api('DELETE', f'{YT}/videos', account, params={'id': external_id})
        return True

    # -- inbox
    def fetch_inbox(self, account, since=None):
        """Top-level comments on the channel's videos, newest first, down to ``since``."""
        items, page = [], None
        for _ in range(MAX_PAGES):
            params = {'part': 'snippet', 'allThreadsRelatedToChannelId': account.external_id,
                      'order': 'time', 'maxResults': 100, 'textFormat': 'plainText'}
            if page:
                params['pageToken'] = page
            data = self._api('GET', f'{YT}/commentThreads', account, params=params).json()
            for th in data.get('items', []):
                video_id = th['snippet'].get('videoId', '')
                top = th['snippet']['topLevelComment']
                sn = top['snippet']
                received = _ts(sn.get('publishedAt'))
                if since and received and received <= since:
                    return items
                items.append(FetchedItem(
                    kind='comment', external_id=top['id'], text=sn.get('textOriginal') or sn.get('textDisplay', ''),
                    author_name=sn.get('authorDisplayName', ''),
                    author_id=sn.get('authorChannelId', {}).get('value', ''),
                    thread_id=video_id, received_at=received,
                    permalink=f'https://www.youtube.com/watch?v={video_id}&lc={top["id"]}' if video_id else '',
                    raw=th))
            page = data.get('nextPageToken')
            if not page:
                break
        return items

    def reply(self, account, item, text):
        data = self._api('POST', f'{YT}/comments', account, params={'part': 'snippet'},
                         json={'snippet': {'parentId': item.external_id, 'textOriginal': text}}).json()
        return data.get('id', '')

    # -- analytics
    def fetch_insights(self, account, start, end):
        """Channel totals per day. YouTube Analytics lags by about two days.

        subscribersGained - subscribersLost is a daily change, so it is stored
        as 'followers_gained' ('followers' is a level, summed differently).
        """
        data = self._api('GET', YT_ANALYTICS, account, params={
            'ids': 'channel==MINE', 'startDate': start.isoformat(), 'endDate': end.isoformat(),
            'dimensions': 'day', 'sort': 'day',
            'metrics': 'views,likes,comments,shares,subscribersGained,subscribersLost',
        }).json()
        cols = [h['name'] for h in data.get('columnHeaders', [])]
        out = {}
        for row in data.get('rows') or []:
            r = dict(zip(cols, row))
            out[date.fromisoformat(r['day'])] = {
                'views': int(r.get('views', 0)),
                'engagement': int(r.get('likes', 0)) + int(r.get('comments', 0)) + int(r.get('shares', 0)),
                'followers_gained': int(r.get('subscribersGained', 0)) - int(r.get('subscribersLost', 0)),
            }
        return out

    def fetch_post_metrics(self, account, external_id):
        data = self._api('GET', f'{YT}/videos', account,
                         params={'part': 'statistics', 'id': external_id}).json()
        if not data.get('items'):
            return {}
        st = data['items'][0].get('statistics', {})
        return {'reach': int(st.get('viewCount', 0)),
                'engagement': int(st.get('likeCount', 0)) + int(st.get('commentCount', 0))}



    def fetch_posts(self, account, since=None, limit=50):
        """The channel's uploads with their view, like and comment counts (3 quota units)."""
        ch = self._api('GET', f'{YT}/channels', account,
                       params={'part': 'contentDetails', 'id': account.external_id}).json()
        uploads = ((((ch.get('items') or [{}])[0].get('contentDetails') or {}).get('relatedPlaylists') or {})
                   .get('uploads'))
        if not uploads:
            return []
        items = self._api('GET', f'{YT}/playlistItems', account, params={
            'part': 'contentDetails', 'playlistId': uploads, 'maxResults': min(limit, 50)}).json().get('items', [])
        ids = [i['contentDetails']['videoId'] for i in items if (i.get('contentDetails') or {}).get('videoId')]
        if not ids:
            return []
        videos = self._api('GET', f'{YT}/videos', account, params={
            'part': 'snippet,statistics', 'id': ','.join(ids)}).json().get('items', [])
        out = []
        for v in sorted(videos, key=lambda v: v['snippet'].get('publishedAt', ''), reverse=True):
            sn, st = v.get('snippet') or {}, v.get('statistics') or {}
            when = _ts(sn.get('publishedAt'))
            if since and when and when <= since:
                break
            likes, comments = int(st.get('likeCount', 0)), int(st.get('commentCount', 0))
            thumbs = sn.get('thumbnails') or {}
            out.append(FetchedPost(
                external_id=v['id'], title=sn.get('title', ''), text=sn.get('description', ''), published_at=when,
                url=f'https://youtu.be/{v["id"]}', kind='video',
                thumbnail_url=(thumbs.get('high') or thumbs.get('medium') or thumbs.get('default') or {}).get('url', ''),
                metrics={'views': int(st.get('viewCount', 0)), 'likes': likes, 'comments': comments,
                         'engagement': likes + comments}))
        return out


# ================================================================ Business Profile

GBP_ACCOUNTS = 'https://mybusinessaccountmanagement.googleapis.com/v1/accounts'
GBP_INFO = 'https://mybusinessbusinessinformation.googleapis.com/v1'
GBP_V4 = 'https://mybusiness.googleapis.com/v4'
GBP_PERF = 'https://businessprofileperformance.googleapis.com/v1'
STARS = {'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5}
IMPRESSIONS = ('BUSINESS_IMPRESSIONS_DESKTOP_MAPS', 'BUSINESS_IMPRESSIONS_DESKTOP_SEARCH',
               'BUSINESS_IMPRESSIONS_MOBILE_MAPS', 'BUSINESS_IMPRESSIONS_MOBILE_SEARCH')
CLICKS = ('WEBSITE_CLICKS', 'CALL_CLICKS', 'BUSINESS_DIRECTION_REQUESTS')


class GoogleBusinessAdapter(GoogleOAuthAdapter):
    """One connected account per Business Profile location.

    ``external_id`` is the bare location id; ``extra`` keeps
    ``account_name`` ('accounts/1') and ``location_name`` ('locations/2')
    because the v4 posts and reviews paths need both. Reviews and posts only
    work on verified locations.
    """
    platform = 'google_business'
    label = 'Google Business'
    scopes = ('https://www.googleapis.com/auth/business.manage',)
    caps = Capabilities(max_chars=1500, text_only=True, images=True, video=False, max_media=1,
                        inbox=('review',))

    def _candidates(self, token):
        out = []
        for acct in self._pages(GBP_ACCOUNTS, 'accounts', token=token):
            for loc in self._pages(f'{GBP_INFO}/{acct["name"]}/locations', 'locations', token=token,
                                   params={'readMask': 'name,title,storefrontAddress,metadata',
                                           'pageSize': 100}):
                addr = loc.get('storefrontAddress', {})
                out.append(AccountCandidate(
                    external_id=loc['name'].split('/')[-1], name=loc.get('title', loc['name']),
                    handle=addr.get('locality', ''),
                    extra={'account_name': acct['name'], 'location_name': loc['name'],
                           'maps_uri': loc.get('metadata', {}).get('mapsUri', '')}))
        return out

    def _pages(self, url, key, account=None, token=None, params=None):
        params, results = dict(params or {}), []
        for _ in range(MAX_PAGES):
            data = self._api('GET', url, account, token, params=params).json()
            results += data.get(key, [])
            if not data.get('nextPageToken'):
                break
            params['pageToken'] = data['nextPageToken']
        return results

    @staticmethod
    def _v4(account):
        return f'{GBP_V4}/{account.extra["account_name"]}/{account.extra["location_name"]}'

    # -- publishing
    def validate(self, text, media, title='', first_comment=''):
        problems = super().validate(text, media, title, first_comment)
        if not (text or '').strip() and media:
            problems.append('Google Business posts need text.')
        return problems

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        """A STANDARD "What's new" local post. Google fetches the photo from its URL."""
        body = {'languageCode': 'en', 'summary': (text or '')[:1500], 'topicType': 'STANDARD'}
        if link:
            body['callToAction'] = {'actionType': 'LEARN_MORE', 'url': link}
        photos = [m for m in media if m.kind == 'image'][:1]
        if photos:
            body['media'] = [{'mediaFormat': 'PHOTO', 'sourceUrl': photos[0].url}]
        data = self._api('POST', f'{self._v4(account)}/localPosts', account, json=body).json()
        return PublishResult(data['name'], data.get('searchUrl', ''))

    def delete(self, account, external_id):
        self._api('DELETE', f'{GBP_V4}/{external_id}', account)
        return True

    # -- inbox
    def fetch_inbox(self, account, since=None):
        """Reviews still waiting for an owner reply, newest-updated first."""
        items, page = [], None
        for _ in range(MAX_PAGES):
            params = {'pageSize': 50, 'orderBy': 'updateTime desc'}
            if page:
                params['pageToken'] = page
            data = self._api('GET', f'{self._v4(account)}/reviews', account, params=params).json()
            for rv in data.get('reviews', []):
                updated = _ts(rv.get('updateTime') or rv.get('createTime'))
                if since and updated and updated <= since:
                    return items
                if rv.get('reviewReply'):
                    continue
                items.append(FetchedItem(
                    kind='review', external_id=rv['reviewId'], text=rv.get('comment', ''),
                    author_name=rv.get('reviewer', {}).get('displayName', ''),
                    rating=STARS.get(rv.get('starRating')), thread_id=rv.get('name', ''),
                    permalink=account.extra.get('maps_uri', ''),
                    received_at=_ts(rv.get('createTime')), raw=rv))
            page = data.get('nextPageToken')
            if not page:
                break
        return items

    def reply(self, account, item, text):
        """PUT creates or replaces the owner's single reply to a review."""
        path = f'{self._v4(account)}/reviews/{item.external_id}/reply'
        self._api('PUT', path, account, json={'comment': text})
        return f'{item.external_id}/reply'

    # -- analytics
    def fetch_insights(self, account, start, end):
        """Daily impressions (Search + Maps, desktop + mobile) and actions.

        'clicks' = website clicks + calls + direction requests. Impressions
        are what Google's own dashboard calls profile views, so no separate
        'views' is reported. Days with no activity are omitted by Google.
        """
        params = [('dailyMetrics', m) for m in IMPRESSIONS + CLICKS]
        for prefix, d in (('dailyRange.start_date', start), ('dailyRange.end_date', end)):
            params += [(f'{prefix}.year', d.year), (f'{prefix}.month', d.month), (f'{prefix}.day', d.day)]
        loc = account.extra.get('location_name') or f'locations/{account.external_id}'
        data = self._api('GET', f'{GBP_PERF}/{loc}:fetchMultiDailyMetricsTimeSeries',
                         account, params=params).json()
        out = {}
        for group in data.get('multiDailyMetricTimeSeries', []):
            for series in group.get('dailyMetricTimeSeries', []):
                metric = series.get('dailyMetric')
                name = 'impressions' if metric in IMPRESSIONS else 'clicks' if metric in CLICKS else None
                if not name:
                    continue
                for dv in series.get('timeSeries', {}).get('datedValues', []):
                    d = dv['date']
                    day = out.setdefault(date(d['year'], d['month'], d['day']),
                                         {'impressions': 0, 'clicks': 0})
                    day[name] += int(dv.get('value', 0))  # int64 arrives as a string
        return out
