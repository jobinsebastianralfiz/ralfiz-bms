"""LinkedIn and X adapters against a faked HTTP layer (no network)."""
import io
import json
from datetime import date, timedelta
from unittest import mock
from urllib.parse import parse_qs, urlparse

import requests
from django.test import SimpleTestCase, override_settings
from django.utils import timezone
from requests.structures import CaseInsensitiveDict

from social.adapters.base import AdapterError, AuthError, MediaInput, RateLimited
from social.adapters.linkedin import LinkedInAdapter, escape_little_text
from social.adapters.x import XAdapter, weighted_length

KEYS = dict(LINKEDIN_CLIENT_ID='li-id', LINKEDIN_CLIENT_SECRET='li-secret', LINKEDIN_API_VERSION='202609',
            X_CLIENT_ID='x-id', X_CLIENT_SECRET='x-secret', SOCIAL_X_READS=False)


def resp(status=200, body=None, headers=None):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(body).encode() if body is not None else b''
    r.headers = CaseInsensitiveDict(headers or {})
    return r


class FakeHTTP:
    """Patches requests.request; answers by (method, url substring), in registration order."""

    def __init__(self, test):
        self.routes, self.calls = [], []
        patcher = mock.patch('social.adapters.base.requests.request', side_effect=self._request)
        patcher.start()
        test.addCleanup(patcher.stop)

    def on(self, method, fragment, *responses):
        self.routes.append([method, fragment, list(responses)])
        return self

    def _request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        for m, frag, queue in self.routes:
            if m == method and frag in url and queue:
                r = queue.pop(0) if len(queue) > 1 else queue[0]
                for hook in (kwargs.get('hooks') or {}).get('response', []):
                    hook(r)
                return r
        raise AssertionError(f'unexpected request {method} {url}')

    def find(self, method, fragment):
        return [c for c in self.calls if c[0] == method and fragment in c[1]]


class FakeAccount:
    def __init__(self, **kw):
        self.token, self.refresh_token = 'tok', ''
        self.expires_at = timezone.now() + timedelta(days=30)
        self.external_id, self.handle, self.extra = '123', '', {}
        self.__dict__.update(kw)
        self.save = mock.Mock()


def media(kind='image', data=b'img', content_type='image/jpeg', name='a.jpg'):
    return MediaInput(kind=kind, url='https://example.com/' + name, content_type=content_type,
                      size=len(data), name=name, open=lambda: io.BytesIO(data))


@override_settings(**KEYS)
class LinkedInTests(SimpleTestCase):
    def setUp(self):
        self.a = LinkedInAdapter()
        self.http = FakeHTTP(self)
        self.acc = FakeAccount(external_id='42', extra={'urn': 'urn:li:organization:42'})

    def test_escape_little_text(self):
        self.assertEqual(escape_little_text('Hi (all) @team #1 a_b *x* ~y~ [z] {w} <v> | \\'),
                         'Hi \\(all\\) \\@team \\#1 a\\_b \\*x\\* \\~y\\~ \\[z\\] \\{w\\} \\<v\\> \\| \\\\')
        self.assertEqual(escape_little_text('plain, text. 100%!'), 'plain, text. 100%!')
        self.assertEqual(escape_little_text(''), '')

    def test_authorize_url(self):
        url = self.a.authorize_url('st8', 'https://hub/cb')
        q = parse_qs(urlparse(url).query)
        self.assertTrue(url.startswith('https://www.linkedin.com/oauth/v2/authorization?'))
        self.assertEqual(q['scope'], ['w_organization_social r_organization_social rw_organization_admin'])
        self.assertEqual(q['state'], ['st8'])
        self.assertEqual(q['client_id'], ['li-id'])

    def test_exchange_code_lists_admin_orgs(self):
        self.http.on('POST', '/oauth/v2/accessToken',
                     resp(body={'access_token': 'AT', 'expires_in': 5184000, 'refresh_token': 'RT'}))
        self.http.on('GET', '/organizationAcls', resp(body={'elements': [
            {'organization': 'urn:li:organization:42', 'role': 'ADMINISTRATOR', 'state': 'APPROVED'}]}))
        self.http.on('GET', '/organizations/42', resp(body={'localizedName': 'Ralfiz', 'vanityName': 'ralfiz'}))
        [c] = self.a.exchange_code('code', 'https://hub/cb')
        self.assertEqual((c.external_id, c.name, c.token, c.refresh_token), ('42', 'Ralfiz', 'AT', 'RT'))
        self.assertEqual(c.extra, {'urn': 'urn:li:organization:42'})
        self.assertGreater(c.expires_at, timezone.now() + timedelta(days=59))
        _, url, kw = self.http.find('GET', '/organizationAcls')[0]
        self.assertIn('q=roleAssignee&role=ADMINISTRATOR&state=APPROVED', url)
        self.assertEqual(kw['headers']['LinkedIn-Version'], '202609')
        self.assertEqual(kw['headers']['X-Restli-Protocol-Version'], '2.0.0')

    def _post_ok(self, urn='urn:li:share:999'):
        self.http.on('POST', '/rest/posts', resp(201, headers={'x-restli-id': urn}))

    def _post_body(self):
        return self.http.find('POST', '/rest/posts')[0][2]['json']

    def test_text_post_escapes_and_returns_header_urn(self):
        self._post_ok()
        r = self.a.publish(self.acc, 'Launch (today) #news', [])
        self.assertEqual(r.external_id, 'urn:li:share:999')
        self.assertEqual(r.url, 'https://www.linkedin.com/feed/update/urn:li:share:999/')
        body = self._post_body()
        self.assertEqual(body['commentary'], 'Launch \\(today\\) \\#news')
        self.assertEqual(body['author'], 'urn:li:organization:42')
        self.assertEqual((body['visibility'], body['lifecycleState']), ('PUBLIC', 'PUBLISHED'))
        self.assertEqual(body['distribution']['feedDistribution'], 'MAIN_FEED')
        self.assertNotIn('content', body)

    def test_single_image(self):
        self.http.on('POST', '/images?action=initializeUpload', resp(body={'value': {
            'uploadUrl': 'https://upload.example/img1', 'image': 'urn:li:image:A'}}))
        self.http.on('PUT', 'upload.example', resp(201))
        self._post_ok()
        self.a.publish(self.acc, 'pic', [media()])
        self.assertEqual(self.http.find('PUT', 'upload.example')[0][2]['data'], b'img')
        self.assertEqual(self._post_body()['content'], {'media': {'id': 'urn:li:image:A'}})

    def test_multi_image(self):
        self.http.on('POST', '/images?action=initializeUpload',
                     resp(body={'value': {'uploadUrl': 'https://upload.example/1', 'image': 'urn:li:image:A'}}),
                     resp(body={'value': {'uploadUrl': 'https://upload.example/2', 'image': 'urn:li:image:B'}}))
        self.http.on('PUT', 'upload.example', resp(201))
        self._post_ok()
        self.a.publish(self.acc, 'pics', [media(), media()])
        images = self._post_body()['content']['multiImage']['images']
        self.assertEqual([i['id'] for i in images], ['urn:li:image:A', 'urn:li:image:B'])

    def test_video_parts_and_finalize(self):
        data = b'0123456789'
        self.http.on('POST', '/videos?action=initializeUpload', resp(body={'value': {
            'video': 'urn:li:video:V', 'uploadToken': 'UT', 'uploadInstructions': [
                {'uploadUrl': 'https://upload.example/p1', 'firstByte': 0, 'lastByte': 4},
                {'uploadUrl': 'https://upload.example/p2', 'firstByte': 5, 'lastByte': 9}]}}))
        self.http.on('PUT', '/p1', resp(200, headers={'etag': 'e1'}))
        self.http.on('PUT', '/p2', resp(200, headers={'etag': 'e2'}))
        self.http.on('POST', '/videos?action=finalizeUpload', resp(200))
        self._post_ok('urn:li:ugcPost:7')
        self.a.publish(self.acc, 'vid', [media('video', data, 'video/mp4', 'v.mp4')])
        self.assertEqual(self.http.find('PUT', '/p2')[0][2]['data'], b'56789')
        fin = self.http.find('POST', 'finalizeUpload')[0][2]['json']['finalizeUploadRequest']
        self.assertEqual(fin, {'video': 'urn:li:video:V', 'uploadToken': 'UT', 'uploadedPartIds': ['e1', 'e2']})
        self.assertEqual(self._post_body()['content']['media']['id'], 'urn:li:video:V')

    def test_article_link_and_first_comment_failure_is_ignored(self):
        self._post_ok()
        self.http.on('POST', '/socialActions/', resp(500, {'message': 'boom'}))
        r = self.a.publish(self.acc, 'read this', [], link='https://ralfiz.in/blog', first_comment='More below')
        self.assertEqual(r.external_id, 'urn:li:share:999')
        self.assertEqual(self._post_body()['content']['article']['source'], 'https://ralfiz.in/blog')
        _, url, kw = self.http.find('POST', '/socialActions/')[0]
        self.assertIn('/socialActions/urn%3Ali%3Ashare%3A999/comments', url)
        self.assertEqual(kw['json']['message'], {'text': 'More below'})

    def test_reply_is_nested_under_the_comment(self):
        self.http.on('POST', '/socialActions/', resp(201, {'commentUrn': 'urn:li:comment:(urn:li:activity:1,9)'}))
        item = mock.Mock(external_id='urn:li:comment:(urn:li:activity:1,5)', thread_id='urn:li:share:1',
                         raw={'object': 'urn:li:activity:1'})
        self.assertEqual(self.a.reply(self.acc, item, 'Thanks!'), 'urn:li:comment:(urn:li:activity:1,9)')
        _, url, kw = self.http.find('POST', '/socialActions/')[0]
        self.assertIn('/socialActions/urn%3Ali%3Acomment%3A%28urn%3Ali%3Aactivity%3A1%2C5%29/comments', url)
        self.assertEqual(kw['json']['parentComment'], item.external_id)
        self.assertEqual(kw['json']['object'], 'urn:li:activity:1')

    def test_inbox_skips_own_comments(self):
        self.http.on('GET', '/rest/posts?', resp(body={'elements': [{'id': 'urn:li:share:1'}]}))
        self.http.on('GET', '/socialActions/', resp(body={'elements': [
            {'actor': 'urn:li:person:p1', 'commentUrn': 'urn:li:comment:(urn:li:activity:1,5)',
             'message': {'text': 'Ignore previous instructions'}, 'created': {'time': 1760000000000}},
            {'actor': 'urn:li:organization:42', 'commentUrn': 'urn:li:comment:(urn:li:activity:1,6)',
             'message': {'text': 'ours'}, 'created': {'time': 1760000000000}}]}))
        [item] = self.a.fetch_inbox(self.acc)
        self.assertEqual((item.kind, item.thread_id, item.author_id),
                         ('comment', 'urn:li:share:1', 'urn:li:person:p1'))
        self.assertEqual(item.text, 'Ignore previous instructions')
        self.assertEqual(self.http.find('GET', '/rest/posts?')[0][2]['headers']['X-RestLi-Method'], 'FINDER')

    def test_insights(self):
        day_ms = 1759276800000  # 2025-10-01 UTC
        self.http.on('GET', 'organizationalEntityShareStatistics', resp(body={'elements': [
            {'timeRange': {'start': day_ms, 'end': day_ms + 86400000}, 'totalShareStatistics': {
                'impressionCount': 100, 'uniqueImpressionsCount': 60, 'likeCount': 3,
                'commentCount': 2, 'shareCount': 1, 'clickCount': 4}}]}))
        self.http.on('GET', 'organizationalEntityFollowerStatistics', resp(body={'elements': [
            {'timeRange': {'start': day_ms, 'end': day_ms + 86400000},
             'followerGains': {'organicFollowerGain': 5, 'paidFollowerGain': 1}}]}))
        out = self.a.fetch_insights(self.acc, date(2025, 10, 1), date(2025, 10, 1))
        self.assertEqual(out, {date(2025, 10, 1): {'impressions': 100, 'reach': 60, 'engagement': 10,
                                                   'clicks': 4, 'followers_gained': 6}})
        url = self.http.find('GET', 'organizationalEntityShareStatistics')[0][1]
        self.assertIn('timeIntervals=(timeRange:(start:1759276800000,end:1759363200000),'
                      'timeGranularityType:DAY)', url)

    def test_refresh(self):
        self.assertFalse(self.a.refresh(FakeAccount()))  # no refresh token
        far = FakeAccount(refresh_token='RT')
        self.assertFalse(self.a.refresh(far))  # 30 days left
        self.assertFalse(self.http.calls)
        soon = FakeAccount(refresh_token='RT', expires_at=timezone.now() + timedelta(days=2))
        self.http.on('POST', 'accessToken', resp(body={'access_token': 'NEW', 'expires_in': 5184000}))
        self.assertTrue(self.a.refresh(soon))
        self.assertEqual((soon.token, soon.refresh_token), ('NEW', 'RT'))

    def test_refresh_invalid_grant_is_auth_error(self):
        acc = FakeAccount(refresh_token='RT', expires_at=timezone.now())
        self.http.on('POST', 'accessToken', resp(400, {'error': 'invalid_grant'}))
        with self.assertRaises(AuthError):
            self.a.refresh(acc)


@override_settings(**KEYS)
class XTests(SimpleTestCase):
    def setUp(self):
        self.a = XAdapter()
        self.http = FakeHTTP(self)
        self.acc = FakeAccount(external_id='777', handle='@ralfiz')

    def test_authorize_url_uses_pkce(self):
        url = self.a.authorize_url('st8', 'https://hub/cb', code_challenge='CH')
        self.assertTrue(url.startswith('https://x.com/i/oauth2/authorize?'))
        q = parse_qs(urlparse(url).query)
        self.assertEqual(q['code_challenge'], ['CH'])
        self.assertEqual(q['code_challenge_method'], ['S256'])
        self.assertEqual(q['scope'], ['tweet.read tweet.write users.read offline.access media.write'])
        self.assertTrue(self.a.uses_pkce)

    def test_exchange_code(self):
        self.http.on('POST', '/2/oauth2/token',
                     resp(body={'access_token': 'AT', 'refresh_token': 'RT', 'expires_in': 7200}))
        self.http.on('GET', '/2/users/me', resp(body={'data': {
            'id': '777', 'name': 'Ralfiz', 'username': 'ralfiz', 'profile_image_url': 'https://img'}}))
        [c] = self.a.exchange_code('code', 'https://hub/cb', code_verifier='VER')
        self.assertEqual((c.external_id, c.handle, c.token, c.refresh_token, c.avatar_url),
                         ('777', '@ralfiz', 'AT', 'RT', 'https://img'))
        self.assertLess(c.expires_at, timezone.now() + timedelta(hours=3))
        kw = self.http.find('POST', '/2/oauth2/token')[0][2]
        self.assertEqual(kw['auth'], ('x-id', 'x-secret'))
        self.assertEqual(kw['data']['code_verifier'], 'VER')
        self.assertEqual(self.http.find('GET', '/2/users/me')[0][2]['headers']['Authorization'], 'Bearer AT')

    def test_image_publish(self):
        self.http.on('POST', '/2/media/upload', resp(body={'data': {'id': 'M1'}}))
        self.http.on('POST', '/2/tweets', resp(201, {'data': {'id': 'T1'}}))
        r = self.a.publish(self.acc, 'hello', [media()], link='https://ralfiz.in')
        self.assertEqual((r.external_id, r.url), ('T1', 'https://x.com/ralfiz/status/T1'))
        body = self.http.find('POST', '/2/tweets')[0][2]['json']
        self.assertEqual(body, {'text': 'hello\nhttps://ralfiz.in', 'media': {'media_ids': ['M1']}})
        up = self.http.find('POST', '/2/media/upload')[0][2]
        self.assertEqual(up['data'], {'media_category': 'tweet_image'})

    @mock.patch('social.adapters.x.CHUNK', 4)
    @mock.patch('social.adapters.x.time.sleep')
    def test_video_chunked_and_polled(self, sleep):
        self.http.on('POST', '/media/upload/initialize', resp(body={'data': {'id': 'V1'}}))
        self.http.on('POST', '/media/upload/V1/append', resp(204))
        self.http.on('POST', '/media/upload/V1/finalize', resp(body={'data': {
            'id': 'V1', 'processing_info': {'state': 'pending', 'check_after_secs': 2}}}))
        self.http.on('GET', 'command=STATUS', resp(body={'data': {'processing_info': {
            'state': 'in_progress', 'check_after_secs': 3}}}),
            resp(body={'data': {'processing_info': {'state': 'succeeded'}}}))
        self.http.on('POST', '/2/tweets', resp(201, {'data': {'id': 'T2'}}))
        self.a.publish(self.acc, 'clip', [media('video', b'0123456789', 'video/mp4', 'v.mp4')])
        init = self.http.find('POST', '/initialize')[0][2]['json']
        self.assertEqual(init, {'media_type': 'video/mp4', 'total_bytes': 10, 'media_category': 'tweet_video'})
        appends = self.http.find('POST', '/append')
        self.assertEqual([c[2]['data']['segment_index'] for c in appends], [0, 1, 2])
        self.assertEqual(len(self.http.find('GET', 'command=STATUS')), 2)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 3])
        self.assertEqual(self.http.find('POST', '/2/tweets')[0][2]['json']['media'], {'media_ids': ['V1']})

    @mock.patch('social.adapters.x.time.sleep')
    def test_video_processing_timeout_is_retryable(self, sleep):
        self.http.on('POST', '/initialize', resp(body={'data': {'id': 'V1'}}))
        self.http.on('POST', '/append', resp(204))
        self.http.on('POST', '/finalize', resp(body={'data': {'processing_info': {
            'state': 'in_progress', 'check_after_secs': 60}}}))
        self.http.on('GET', 'command=STATUS', resp(body={'data': {'processing_info': {
            'state': 'in_progress', 'check_after_secs': 60}}}))
        with self.assertRaises(AdapterError) as cm:
            self.a.publish(self.acc, 'clip', [media('video', b'xx', 'video/mp4', 'v.mp4')])
        self.assertTrue(cm.exception.retryable)
        self.assertFalse(self.http.find('POST', '/2/tweets'))

    def test_refresh_rotates_and_ensure_fresh_saves(self):
        acc = FakeAccount(external_id='777', handle='@r', refresh_token='OLD',
                          expires_at=timezone.now() + timedelta(minutes=5))
        self.http.on('POST', '/2/oauth2/token',
                     resp(body={'access_token': 'NEW', 'refresh_token': 'NEWRT', 'expires_in': 7200}))
        self.http.on('POST', '/2/tweets', resp(201, {'data': {'id': 'T3'}}))
        self.a.publish(acc, 'hi', [])
        self.assertEqual((acc.token, acc.refresh_token), ('NEW', 'NEWRT'))
        acc.save.assert_called_once()
        self.assertEqual(self.http.find('POST', '/2/tweets')[0][2]['headers']['Authorization'], 'Bearer NEW')
        self.assertEqual(self.http.find('POST', '/2/oauth2/token')[0][2]['data']['refresh_token'], 'OLD')

    def test_refresh_not_needed(self):
        self.assertFalse(self.a.refresh(FakeAccount(refresh_token='RT')))
        self.assertFalse(self.http.calls)

    def test_invalid_grant_is_auth_error(self):
        acc = FakeAccount(refresh_token='RT', expires_at=timezone.now())
        self.http.on('POST', '/2/oauth2/token', resp(400, {'error': 'invalid_request',
                                                           'error_description': 'Value passed for the token was invalid.'}))
        with self.assertRaises(AuthError):
            self.a.refresh(acc)

    def test_reads_off_makes_no_calls(self):
        self.assertEqual(self.a.fetch_inbox(self.acc), [])
        self.assertEqual(self.a.fetch_post_metrics(self.acc, 'T1'), {})
        self.assertEqual(self.a.fetch_insights(self.acc, date(2026, 1, 1), date(2026, 1, 2)), {})
        self.assertFalse(self.http.calls)

    @override_settings(SOCIAL_X_READS=True)
    def test_reads_on_mentions_and_metrics(self):
        self.http.on('GET', '/users/777/mentions', resp(body={
            'data': [{'id': 'T9', 'text': '@ralfiz hi', 'author_id': 'U1', 'conversation_id': 'C1',
                      'created_at': '2026-10-01T10:00:00.000Z'}],
            'includes': {'users': [{'id': 'U1', 'username': 'anj', 'name': 'Anjali'}]}}))
        self.http.on('GET', '/tweets/T1', resp(body={'data': {'public_metrics': {
            'impression_count': 500, 'like_count': 5, 'reply_count': 2, 'retweet_count': 1,
            'quote_count': 1, 'bookmark_count': 9}}}))
        since = timezone.now() - timedelta(hours=1)
        [m] = self.a.fetch_inbox(self.acc, since=since)
        self.assertEqual((m.kind, m.external_id, m.author_name, m.thread_id), ('mention', 'T9', '@anj', 'C1'))
        params = self.http.find('GET', '/mentions')[0][2]['params']
        self.assertTrue(params['start_time'].endswith('Z'))
        self.assertEqual(params['expansions'], 'author_id')
        self.assertEqual(self.a.fetch_post_metrics(self.acc, 'T1'), {'reach': 500, 'engagement': 9})

    def test_reply_works_with_reads_off(self):
        self.http.on('POST', '/2/tweets', resp(201, {'data': {'id': 'R1'}}))
        item = mock.Mock(external_id='T9')
        self.assertEqual(self.a.reply(self.acc, item, 'Thanks'), 'R1')
        self.assertEqual(self.http.find('POST', '/2/tweets')[0][2]['json'],
                         {'text': 'Thanks', 'reply': {'in_reply_to_tweet_id': 'T9'}})

    @mock.patch('social.adapters.x.time.time', return_value=1000)
    def test_429_uses_rate_limit_reset(self, _):
        self.http.on('POST', '/2/tweets', resp(429, {'title': 'Too Many Requests'},
                                               headers={'x-rate-limit-reset': '1600'}))
        with self.assertRaises(RateLimited) as cm:
            self.a.publish(self.acc, 'hi', [])
        self.assertEqual(cm.exception.retry_after, 600)
        self.assertTrue(cm.exception.retryable)

    def test_validate_counts_links_as_23(self):
        long_url = 'https://example.com/' + 'a' * 200
        self.assertEqual(weighted_length(f'hi {long_url}'), 3 + 23)
        self.assertEqual(self.a.validate('x' * 250, [], link=long_url), [])  # 250 + 1 + 23 = 274
        self.assertTrue(self.a.validate('x' * 260, [], link=long_url))     # 284
        self.assertTrue(self.a.validate('x' * 281, []))
        self.assertTrue(self.a.validate('hi', [media('video', b'v', 'video/mp4'), media()]))
