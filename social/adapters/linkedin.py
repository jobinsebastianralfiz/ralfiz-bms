"""LinkedIn company pages, through the versioned Marketing API (/rest/).

Platform quirks worth knowing:

* Every /rest/ call needs ``LinkedIn-Version: YYYYMM`` and
  ``X-Restli-Protocol-Version: 2.0.0``. Versions are sunset about a year
  after release, so LINKEDIN_API_VERSION must be bumped regularly.
* Rest.li 2.0 wants URNs URL-encoded wherever they appear in a URL, but the
  structural ``( ) , :`` of a complex query value such as ``timeIntervals``
  must stay raw. ``requests``' ``params=`` would encode both, so query strings
  are built by hand here.
* Post ``commentary`` is "little text": ``| { } @ [ ] ( ) < > # \\ * _ ~``
  are markup and must be backslash-escaped to print literally.
* A new post's URN comes back only in the ``x-restli-id`` response header.
* Member access tokens last about 60 days. Refresh tokens are only issued to
  apps LinkedIn has approved for them; without one the user reconnects.
"""
from datetime import datetime, timedelta, timezone as dt_timezone
from urllib.parse import quote, urlencode

from django.conf import settings
from django.utils import timezone

from .base import (AccountCandidate, Adapter, AdapterError, Capabilities, FetchedItem,
                   PublishResult, call)

AUTH_URL = 'https://www.linkedin.com/oauth/v2/authorization'
TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
API = 'https://api.linkedin.com/rest'
SCOPES = 'w_organization_social r_organization_social rw_organization_admin'
REFRESH_WITHIN = timedelta(days=7)

_RESERVED = set('\\|{}@[]()<>#*_~')


def escape_little_text(text):
    """Backslash-escape LinkedIn "little" reserved characters so text prints as typed.

    Note this also turns a typed ``#tag`` into plain text rather than a
    hashtag link; that is the price of never misreading user text as markup.
    """
    return ''.join('\\' + ch if ch in _RESERVED else ch for ch in text or '')


def _enc(urn):
    return quote(urn, safe='')


def _ms(d):
    """Midnight UTC of a date, as epoch milliseconds."""
    return int(datetime(d.year, d.month, d.day, tzinfo=dt_timezone.utc).timestamp() * 1000)


def _day(ms):
    return datetime.fromtimestamp(ms / 1000, tz=dt_timezone.utc).date()


def _feed_url(urn):
    return f'https://www.linkedin.com/feed/update/{urn}/'


class LinkedInAdapter(Adapter):
    platform = 'linkedin'
    label = 'LinkedIn'
    caps = Capabilities(max_chars=3000, max_media=20, first_comment=True, inbox=('comment',))
    required_settings = ('LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET')

    # ------------------------------------------------------------ http
    def _headers(self, token, **extra):
        return {
            'Authorization': f'Bearer {token}',
            'LinkedIn-Version': str(getattr(settings, 'LINKEDIN_API_VERSION', '') or '202509'),
            'X-Restli-Protocol-Version': '2.0.0',
            **extra,
        }

    def _api(self, method, path, token, *, headers=None, **kwargs):
        """A /rest/ call. ``path`` already carries its hand-encoded query string."""
        return call(method, f'{API}{path}', platform=self.label,
                    headers=self._headers(token, **(headers or {})), **kwargs)

    def _token_request(self, data, auth_codes=(401,)):
        data = {**data, 'client_id': settings.LINKEDIN_CLIENT_ID,
                'client_secret': settings.LINKEDIN_CLIENT_SECRET}
        return call('POST', TOKEN_URL, platform=self.label, data=data, auth_codes=auth_codes).json()

    # ------------------------------------------------------------ connecting
    def authorize_url(self, state, redirect_uri, code_challenge=None):
        return AUTH_URL + '?' + urlencode({
            'response_type': 'code', 'client_id': settings.LINKEDIN_CLIENT_ID,
            'redirect_uri': redirect_uri, 'state': state, 'scope': SCOPES,
        }, quote_via=quote)

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        """One candidate per company page the member administers."""
        data = self._token_request({'grant_type': 'authorization_code', 'code': code,
                                    'redirect_uri': redirect_uri})
        token = data['access_token']
        expires_at = timezone.now() + timedelta(seconds=int(data.get('expires_in') or 5184000))
        acls = self._api('GET', '/organizationAcls?q=roleAssignee&role=ADMINISTRATOR'
                                '&state=APPROVED&count=100', token).json()
        candidates = []
        for acl in acls.get('elements', []):
            # 'organization' in current versions; older ones used 'organizationalTarget'.
            urn = acl.get('organization') or acl.get('organizationalTarget') or ''
            org_id = urn.rsplit(':', 1)[-1]
            if not org_id.isdigit():
                continue
            org = self._api('GET', f'/organizations/{org_id}', token).json()
            vanity = org.get('vanityName') or ''
            # The logo (logoV2) is a digitalmediaAsset URN, not a URL; resolving it
            # needs another call, so pages connect without an avatar.
            candidates.append(AccountCandidate(
                external_id=org_id,
                name=org.get('localizedName') or f'LinkedIn page {org_id}',
                handle=vanity,
                token=token,
                refresh_token=data.get('refresh_token') or '',
                expires_at=expires_at,
                extra={'urn': f'urn:li:organization:{org_id}'},
            ))
        return candidates

    def refresh(self, account):
        """Refresh only for partner apps that received a refresh token, within 7 days of expiry."""
        if not account.refresh_token:
            return False
        if account.expires_at and account.expires_at - timezone.now() > REFRESH_WITHIN:
            return False
        # Token endpoints answer a dead refresh token with 400 invalid_grant (RFC 6749 5.2).
        data = self._token_request({'grant_type': 'refresh_token',
                                    'refresh_token': account.refresh_token}, auth_codes=(400, 401))
        account.token = data['access_token']
        account.expires_at = timezone.now() + timedelta(seconds=int(data.get('expires_in') or 5184000))
        if data.get('refresh_token'):
            account.refresh_token = data['refresh_token']
        return True

    # ------------------------------------------------------------ publishing
    def _urn(self, account):
        return (account.extra or {}).get('urn') or f'urn:li:organization:{account.external_id}'

    def validate(self, text, media, title='', first_comment=''):
        problems = super().validate(text, media, title=title, first_comment=first_comment)
        if sum(m.kind == 'video' for m in media) > 1:
            problems.append('LinkedIn takes one video per post.')
        return problems

    def _read(self, m):
        with m.open() as f:
            return f.read()

    def _upload_image(self, account, m):
        token = account.token
        init = self._api('POST', '/images?action=initializeUpload', token, json={
            'initializeUploadRequest': {'owner': self._urn(account)}}).json()['value']
        call('PUT', init['uploadUrl'], platform=self.label, data=self._read(m),
             headers={'Authorization': f'Bearer {token}'})
        return init['image']

    def _upload_video(self, account, m):
        """initializeUpload, PUT each byte range, collect the ETags, finalizeUpload."""
        token = account.token
        data = self._read(m)
        init = self._api('POST', '/videos?action=initializeUpload', token, json={
            'initializeUploadRequest': {'owner': self._urn(account), 'fileSizeBytes': len(data),
                                        'uploadCaptions': False, 'uploadThumbnail': False}}).json()['value']
        etags = []
        for part in init['uploadInstructions']:
            r = call('PUT', part['uploadUrl'], platform=self.label,
                     data=data[part['firstByte']:part['lastByte'] + 1],
                     headers={'Authorization': f'Bearer {token}',
                              'Content-Type': 'application/octet-stream'})
            etags.append(r.headers.get('etag', ''))
        self._api('POST', '/videos?action=finalizeUpload', token, json={'finalizeUploadRequest': {
            'video': init['video'], 'uploadToken': init.get('uploadToken', ''),
            'uploadedPartIds': etags}})
        # The video then processes for a while; LinkedIn accepts the post meanwhile
        # and publishes it once processing ends (verify with large files).
        return init['video']

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        commentary = text or ''
        content = None
        if media:
            if media[0].kind == 'video':
                content = {'media': {'id': self._upload_video(account, media[0]), 'title': title or ''}}
            else:
                ids = [self._upload_image(account, m) for m in media]
                content = {'media': {'id': ids[0]}} if len(ids) == 1 else \
                    {'multiImage': {'images': [{'id': i, 'altText': ''} for i in ids]}}
            if link and link not in commentary:
                commentary = f'{commentary}\n\n{link}'.strip()
        elif link:
            # The Posts API does not scrape URLs: title (and optionally description
            # and a thumbnail image URN) must be supplied by us.
            content = {'article': {'source': link, 'title': title or link}}
        body = {
            'author': self._urn(account),
            'commentary': escape_little_text(commentary),
            'visibility': 'PUBLIC',
            'distribution': {'feedDistribution': 'MAIN_FEED', 'targetEntities': [],
                             'thirdPartyDistributionChannels': []},
            'lifecycleState': 'PUBLISHED',
            'isReshareDisabledByAuthor': False,
        }
        if content:
            body['content'] = content
        r = self._api('POST', '/posts', account.token, json=body)
        urn = r.headers.get('x-restli-id', '')
        if not urn:
            raise AdapterError('LinkedIn accepted the post but returned no id.')
        if first_comment:
            try:
                self._comment(account, urn, urn, first_comment)
            except AdapterError:
                pass  # the post is live; a missing first comment must not fail it
        return PublishResult(urn, _feed_url(urn))

    def delete(self, account, external_id):
        self._api('DELETE', f'/posts/{_enc(external_id)}', account.token,
                  headers={'X-RestLi-Method': 'DELETE'})
        return True

    def _comment(self, account, target, obj, text, parent=''):
        """Comment as the page. ``target`` is the URL entity (post, or parent comment URN)."""
        body = {'actor': self._urn(account), 'object': obj, 'message': {'text': text}}
        if parent:
            body['parentComment'] = parent
        r = self._api('POST', f'/socialActions/{_enc(target)}/comments', account.token, json=body)
        try:
            data = r.json()
        except ValueError:
            data = {}
        return data.get('commentUrn') or r.headers.get('x-restli-id', '')

    # ------------------------------------------------------------ inbox
    def fetch_inbox(self, account, since=None):
        """Comments by others on the page's 10 most recent posts."""
        token, org = account.token, self._urn(account)
        posts = self._api('GET', f'/posts?author={_enc(org)}&q=author&count=10&sortBy=LAST_MODIFIED',
                          token, headers={'X-RestLi-Method': 'FINDER'}).json().get('elements', [])
        items = []
        for post in posts:
            post_urn = post.get('id')
            if not post_urn:
                continue
            comments = self._api('GET', f'/socialActions/{_enc(post_urn)}/comments',
                                 token).json().get('elements', [])
            for c in comments:
                actor = c.get('actor', '')
                ms = (c.get('created') or {}).get('time')
                when = datetime.fromtimestamp(ms / 1000, tz=dt_timezone.utc) if ms else None
                if actor == org or (since and when and when <= since):
                    continue
                items.append(FetchedItem(
                    kind='comment',
                    external_id=c.get('commentUrn') or f'{post_urn}#{c.get("id")}',
                    text=(c.get('message') or {}).get('text', ''),
                    author_id=actor,
                    # Member names need profile permissions the page app does not hold.
                    author_name='LinkedIn member' if actor.startswith('urn:li:person') else '',
                    thread_id=post_urn,
                    permalink=_feed_url(post_urn),
                    received_at=when,
                    raw=c,
                ))
        return items

    def reply(self, account, item, text):
        """A nested reply: posted against the parent comment URN, with parentComment set."""
        obj = (item.raw or {}).get('object') or item.thread_id
        return self._comment(account, item.external_id, obj, text, parent=item.external_id)

    # ------------------------------------------------------------ analytics
    @staticmethod
    def _stats(s):
        out = {
            'impressions': int(s.get('impressionCount') or 0),
            'engagement': sum(int(s.get(k) or 0) for k in
                              ('likeCount', 'commentCount', 'shareCount', 'clickCount')),
            'clicks': int(s.get('clickCount') or 0),
        }
        if 'uniqueImpressionsCount' in s:  # absent from per-post statistics
            out['reach'] = int(s['uniqueImpressionsCount'] or 0)
        return out

    def fetch_insights(self, account, start, end):
        """Daily page totals. Share statistics only cover the last 12 months."""
        token, org = account.token, _enc(self._urn(account))
        interval = (f'timeIntervals=(timeRange:(start:{_ms(start)},end:{_ms(end + timedelta(days=1))}),'
                    'timeGranularityType:DAY)')
        out = {}
        shares = self._api('GET', f'/organizationalEntityShareStatistics?q=organizationalEntity'
                                  f'&organizationalEntity={org}&{interval}', token).json()
        for el in shares.get('elements', []):
            day = _day(el['timeRange']['start'])
            out.setdefault(day, {}).update(self._stats(el.get('totalShareStatistics') or {}))
        followers = self._api('GET', f'/organizationalEntityFollowerStatistics?q=organizationalEntity'
                                     f'&organizationalEntity={org}&{interval}', token).json()
        for el in followers.get('elements', []):
            day = _day(el['timeRange']['start'])
            g = el.get('followerGains') or {}
            out.setdefault(day, {})['followers_gained'] = \
                int(g.get('organicFollowerGain') or 0) + int(g.get('paidFollowerGain') or 0)
        return {d: m for d, m in out.items() if start <= d <= end}

    def fetch_post_metrics(self, account, external_id):
        """Lifetime stats for one post; LinkedIn has no time-bound stats per post."""
        if external_id.startswith('urn:li:share:'):
            param = 'shares'
        elif external_id.startswith('urn:li:ugcPost:'):
            param = 'ugcPosts'
        else:
            return {}
        data = self._api('GET', f'/organizationalEntityShareStatistics?q=organizationalEntity'
                                f'&organizationalEntity={_enc(self._urn(account))}'
                                f'&{param}=List({_enc(external_id)})', account.token).json()
        els = data.get('elements') or []
        # A post with no activity yet is simply left out of the response.
        return self._stats(els[0].get('totalShareStatistics') or {}) if els else {}
