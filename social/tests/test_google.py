"""YouTube and Google Business adapters, with every HTTP call mocked."""
import io
from datetime import date, datetime, timedelta, timezone as dt_timezone
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from cryptography.fernet import Fernet
from django.test import TestCase, override_settings
from django.utils import timezone

from social.adapters.base import AuthError, MediaInput, RateLimited
from social.adapters.google import GoogleBusinessAdapter, YouTubeAdapter
from social.models import InboxItem, SocialAccount, Workspace

KEY = Fernet.generate_key().decode()


def resp(status=200, data=None, headers=None):
    r = MagicMock(status_code=status, headers=headers or {}, text='')
    r.json.return_value = data if data is not None else {}
    return r


@override_settings(SOCIAL_TOKEN_KEY=KEY, GOOGLE_OAUTH_CLIENT_ID='cid',
                   GOOGLE_OAUTH_CLIENT_SECRET='secret')
class GoogleTestCase(TestCase):
    platform = 'youtube'

    def setUp(self):
        self.ws = Workspace.objects.create(name='Acme')
        self.acc = SocialAccount(workspace=self.ws, platform=self.platform, external_id='UC1', name='Acme',
                                 expires_at=timezone.now() + timedelta(hours=1),
                                 extra={'account_name': 'accounts/1', 'location_name': 'locations/2'})
        self.acc.token, self.acc.refresh_token = 'tok', 'rtok'
        self.acc.save()
        patcher = patch('social.adapters.base.requests.request')
        self.req = patcher.start()
        self.addCleanup(patcher.stop)

    def calls(self):
        return [(c.args[0], c.args[1], c.kwargs) for c in self.req.call_args_list]


class OAuthTests(GoogleTestCase):
    def test_authorize_url_scopes(self):
        q = parse_qs(urlparse(YouTubeAdapter().authorize_url('st', 'https://x/cb', 'chal')).query)
        self.assertEqual(q['access_type'], ['offline'])
        self.assertEqual(q['prompt'], ['consent'])
        self.assertEqual(q['include_granted_scopes'], ['true'])
        self.assertEqual(q['code_challenge_method'], ['S256'])
        scopes = q['scope'][0].split()
        for s in ('youtube.upload', 'youtube.force-ssl', 'yt-analytics.readonly', 'youtube.readonly'):
            self.assertIn(f'https://www.googleapis.com/auth/{s}', scopes)
        q = parse_qs(urlparse(GoogleBusinessAdapter().authorize_url('st', 'https://x/cb')).query)
        self.assertEqual(q['scope'], ['https://www.googleapis.com/auth/business.manage'])

    def test_exchange_code_youtube(self):
        self.req.side_effect = [
            resp(data={'access_token': 'A', 'refresh_token': 'R', 'expires_in': 3599}),
            resp(data={'items': [{'id': 'UC9', 'snippet': {
                'title': 'Acme TV', 'customUrl': '@acmetv',
                'thumbnails': {'default': {'url': 'https://img/t.jpg'}}}}]}),
        ]
        [c] = YouTubeAdapter().exchange_code('code', 'https://x/cb', 'ver')
        self.assertEqual((c.external_id, c.name, c.handle, c.avatar_url), ('UC9', 'Acme TV', '@acmetv', 'https://img/t.jpg'))
        self.assertEqual((c.token, c.refresh_token), ('A', 'R'))
        self.assertAlmostEqual((c.expires_at - timezone.now()).total_seconds(), 3599, delta=5)
        token_call = self.calls()[0]
        self.assertEqual(token_call[1], 'https://oauth2.googleapis.com/token')
        self.assertEqual(token_call[2]['data']['code_verifier'], 'ver')
        self.assertEqual(self.calls()[1][2]['headers']['Authorization'], 'Bearer A')

    def test_exchange_code_business(self):
        self.req.side_effect = [
            resp(data={'access_token': 'A', 'refresh_token': 'R', 'expires_in': 3600}),
            resp(data={'accounts': [{'name': 'accounts/11'}]}),
            resp(data={'locations': [
                {'name': 'locations/21', 'title': 'Acme Kochi', 'storefrontAddress': {'locality': 'Kochi'}},
                {'name': 'locations/22', 'title': 'Acme Thrissur'}]}),
        ]
        cands = GoogleBusinessAdapter().exchange_code('code', 'https://x/cb')
        self.assertEqual([c.external_id for c in cands], ['21', '22'])
        self.assertEqual(cands[0].extra['account_name'], 'accounts/11')
        self.assertEqual(cands[0].extra['location_name'], 'locations/21')
        self.assertEqual(cands[0].handle, 'Kochi')
        self.assertTrue(all(c.refresh_token == 'R' for c in cands))
        loc_call = self.calls()[2]
        self.assertIn('/v1/accounts/11/locations', loc_call[1])
        self.assertIn('readMask', loc_call[2]['params'])

    def test_refresh_success(self):
        self.acc.expires_at = timezone.now() + timedelta(minutes=5)
        self.req.return_value = resp(data={'access_token': 'NEW', 'expires_in': 3600})
        self.assertTrue(YouTubeAdapter().refresh(self.acc))
        self.assertEqual(self.acc.token, 'NEW')
        self.assertEqual(self.acc.refresh_token, 'rtok')
        self.assertGreater(self.acc.expires_at, timezone.now() + timedelta(minutes=50))
        self.assertEqual(self.calls()[0][2]['data']['grant_type'], 'refresh_token')

    def test_refresh_not_needed(self):
        self.assertFalse(YouTubeAdapter().refresh(self.acc))
        self.req.assert_not_called()

    def test_refresh_invalid_grant(self):
        self.acc.expires_at = None
        self.req.return_value = resp(400, {'error': 'invalid_grant',
                                           'error_description': 'Token has been expired or revoked.'})
        with self.assertRaises(AuthError):
            YouTubeAdapter().refresh(self.acc)

    def test_api_call_refreshes_and_saves_first(self):
        self.acc.expires_at = timezone.now() - timedelta(minutes=1)
        self.acc.save()
        self.req.side_effect = [resp(data={'access_token': 'NEW', 'expires_in': 3600}),
                                resp(data={'items': [{'statistics': {'viewCount': '5'}}]})]
        YouTubeAdapter().fetch_post_metrics(self.acc, 'v1')
        self.assertEqual(self.calls()[1][2]['headers']['Authorization'], 'Bearer NEW')
        self.acc.refresh_from_db()
        self.assertEqual(self.acc.token, 'NEW')


class YouTubeTests(GoogleTestCase):
    def video(self):
        return MediaInput(kind='video', url='https://x/v.mp4', content_type='video/mp4', size=4,
                          name='v.mp4', open=lambda: io.BytesIO(b'abcd'))

    def test_validate(self):
        a = YouTubeAdapter()
        self.assertIn('YouTube needs a video.', a.validate('hi', []))
        self.assertTrue(any('100 characters' in p for p in a.validate('hi', [self.video()], title='x' * 101)))
        self.assertEqual(a.validate('First line\nmore', [self.video()]), [])

    def test_resumable_upload(self):
        self.req.side_effect = [resp(headers={'Location': 'https://upload/session1'}),
                                resp(data={'id': 'vid1'})]
        result = YouTubeAdapter().publish(self.acc, 'My first video\nLong description', [self.video()])
        self.assertEqual((result.external_id, result.url), ('vid1', 'https://youtu.be/vid1'))
        (m1, u1, k1), (m2, u2, k2) = self.calls()
        self.assertEqual(m1, 'POST')
        self.assertIn('upload/youtube/v3/videos', u1)
        self.assertEqual(k1['params'], {'uploadType': 'resumable', 'part': 'snippet,status'})
        self.assertEqual(k1['json']['snippet']['title'], 'My first video')
        self.assertEqual(k1['json']['status'], {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False})
        self.assertEqual((m2, u2), ('PUT', 'https://upload/session1'))
        self.assertTrue(hasattr(k2['data'], 'read'))

    def test_quota_exceeded_is_rate_limited(self):
        self.req.return_value = resp(403, {'error': {
            'code': 403, 'message': 'The request cannot be completed because you have exceeded your quota.',
            'errors': [{'reason': 'quotaExceeded'}]}})
        with self.assertRaises(RateLimited) as ctx:
            YouTubeAdapter().publish(self.acc, 'Title', [self.video()])
        self.assertGreaterEqual(ctx.exception.retry_after, 3600)

    def test_comments_fetch_stops_at_since(self):
        def thread(cid, when):
            return {'id': 't' + cid, 'snippet': {'videoId': 'vid1', 'topLevelComment': {'id': cid, 'snippet': {
                'textOriginal': f'comment {cid}', 'authorDisplayName': 'Anu',
                'authorChannelId': {'value': 'UCa'}, 'publishedAt': when}}}}
        self.req.return_value = resp(data={'items': [
            thread('c2', '2026-10-10T10:00:00Z'), thread('c1', '2026-10-01T10:00:00.123456789Z')]})
        since = datetime(2026, 10, 5, tzinfo=dt_timezone.utc)
        items = YouTubeAdapter().fetch_inbox(self.acc, since=since)
        self.assertEqual([i.external_id for i in items], ['c2'])
        i = items[0]
        self.assertEqual((i.kind, i.thread_id, i.author_name, i.text), ('comment', 'vid1', 'Anu', 'comment c2'))
        self.assertIn('watch?v=vid1', i.permalink)
        self.assertEqual(i.received_at.day, 10)
        self.assertEqual(self.calls()[0][2]['params']['allThreadsRelatedToChannelId'], 'UC1')

    def test_reply(self):
        item = InboxItem.objects.create(account=self.acc, kind='comment', external_id='c2', thread_id='vid1')
        self.req.return_value = resp(data={'id': 'r1'})
        self.assertEqual(YouTubeAdapter().reply(self.acc, item, 'Thanks!'), 'r1')
        method, url, kw = self.calls()[0]
        self.assertTrue(url.endswith('/youtube/v3/comments'))
        self.assertEqual(kw['json'], {'snippet': {'parentId': 'c2', 'textOriginal': 'Thanks!'}})

    def test_insights_mapping(self):
        self.req.return_value = resp(data={
            'columnHeaders': [{'name': n} for n in
                              ('day', 'views', 'likes', 'comments', 'shares', 'subscribersGained', 'subscribersLost')],
            'rows': [['2026-10-01', 100, 5, 2, 1, 4, 1]]})
        out = YouTubeAdapter().fetch_insights(self.acc, date(2026, 10, 1), date(2026, 10, 1))
        self.assertEqual(out, {date(2026, 10, 1): {'views': 100, 'engagement': 8, 'followers_gained': 3}})
        self.assertEqual(self.calls()[0][2]['params']['ids'], 'channel==MINE')

    def test_post_metrics(self):
        self.req.return_value = resp(data={'items': [{'statistics': {
            'viewCount': '120', 'likeCount': '7', 'commentCount': '3'}}]})
        self.assertEqual(YouTubeAdapter().fetch_post_metrics(self.acc, 'v1'), {'reach': 120, 'engagement': 10})


class GoogleBusinessTests(GoogleTestCase):
    platform = 'google_business'
    V4 = 'https://mybusiness.googleapis.com/v4/accounts/1/locations/2'

    def test_local_post_with_photo(self):
        self.req.return_value = resp(data={'name': 'accounts/1/locations/2/localPosts/p1',
                                           'searchUrl': 'https://local.google.com/p1'})
        photo = MediaInput(kind='image', url='https://cdn/x.jpg', content_type='image/jpeg', size=10, name='x.jpg')
        r = GoogleBusinessAdapter().publish(self.acc, 'Diwali offer', [photo], link='https://acme.in')
        self.assertEqual((r.external_id, r.url), ('accounts/1/locations/2/localPosts/p1', 'https://local.google.com/p1'))
        method, url, kw = self.calls()[0]
        self.assertEqual((method, url), ('POST', f'{self.V4}/localPosts'))
        self.assertEqual(kw['json'], {
            'languageCode': 'en', 'summary': 'Diwali offer', 'topicType': 'STANDARD',
            'callToAction': {'actionType': 'LEARN_MORE', 'url': 'https://acme.in'},
            'media': [{'mediaFormat': 'PHOTO', 'sourceUrl': 'https://cdn/x.jpg'}]})

    def test_reviews_fetch_maps_stars_and_skips_replied(self):
        self.req.return_value = resp(data={'reviews': [
            {'reviewId': 'r1', 'name': 'accounts/1/locations/2/reviews/r1', 'starRating': 'FOUR',
             'comment': 'Good', 'reviewer': {'displayName': 'Rahul'},
             'createTime': '2026-10-09T08:00:00.5Z', 'updateTime': '2026-10-09T08:00:00.5Z'},
            {'reviewId': 'r2', 'starRating': 'FIVE', 'comment': 'Great',
             'createTime': '2026-10-08T08:00:00Z', 'updateTime': '2026-10-08T08:00:00Z',
             'reviewReply': {'comment': 'Thanks'}},
            {'reviewId': 'r3', 'starRating': 'ONE', 'reviewer': {'displayName': 'Sneha'},
             'createTime': '2026-10-07T08:00:00Z'},
        ]})
        items = GoogleBusinessAdapter().fetch_inbox(self.acc)
        self.assertEqual([(i.external_id, i.rating) for i in items], [('r1', 4), ('r3', 1)])
        self.assertEqual((items[0].kind, items[0].author_name, items[0].text), ('review', 'Rahul', 'Good'))
        self.assertEqual(items[0].received_at.day, 9)
        self.assertEqual(self.calls()[0][1], f'{self.V4}/reviews')

    def test_review_reply(self):
        item = InboxItem.objects.create(account=self.acc, kind='review', external_id='r1')
        self.req.return_value = resp(data={'comment': 'Thank you'})
        GoogleBusinessAdapter().reply(self.acc, item, 'Thank you')
        method, url, kw = self.calls()[0]
        self.assertEqual((method, url), ('PUT', f'{self.V4}/reviews/r1/reply'))
        self.assertEqual(kw['json'], {'comment': 'Thank you'})

    def test_insights_mapping(self):
        def series(metric, *values):
            return {'dailyMetric': metric, 'timeSeries': {'datedValues': [
                {'date': {'year': 2026, 'month': 10, 'day': d}, **({'value': v} if v is not None else {})}
                for d, v in values]}}
        self.req.return_value = resp(data={'multiDailyMetricTimeSeries': [{'dailyMetricTimeSeries': [
            series('BUSINESS_IMPRESSIONS_MOBILE_MAPS', (1, '10'), (2, None)),
            series('BUSINESS_IMPRESSIONS_DESKTOP_SEARCH', (1, '5')),
            series('WEBSITE_CLICKS', (1, '2')),
            series('CALL_CLICKS', (1, '1')),
            series('BUSINESS_DIRECTION_REQUESTS', (2, '3')),
        ]}]})
        out = GoogleBusinessAdapter().fetch_insights(self.acc, date(2026, 10, 1), date(2026, 10, 2))
        self.assertEqual(out, {date(2026, 10, 1): {'impressions': 15, 'clicks': 3},
                               date(2026, 10, 2): {'impressions': 0, 'clicks': 3}})
        method, url, kw = self.calls()[0]
        self.assertTrue(url.endswith('/v1/locations/2:fetchMultiDailyMetricsTimeSeries'))
        self.assertIn(('dailyMetrics', 'CALL_CLICKS'), kw['params'])
        self.assertIn(('dailyRange.start_date.day', 1), kw['params'])
