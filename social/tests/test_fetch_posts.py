"""Parsing of each platform's post list into FetchedPost (HTTP mocked)."""
from datetime import datetime, timezone as tz
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from social.adapters.google import YouTubeAdapter
from social.adapters.meta import FacebookAdapter, InstagramAdapter


def account(**kw):
    return SimpleNamespace(token='tok', external_id='123', extra={'page_id': 'PAGE'}, **kw)


class FacebookPostsTests(SimpleTestCase):
    def test_parses_posts_reels_and_counts(self):
        data = {'data': [
            {'id': 'PAGE_2', 'message': 'Reel!', 'created_time': '2026-10-10T10:00:00+0000',
             'permalink_url': 'https://www.facebook.com/reel/99', 'full_picture': 'https://x/a.jpg',
             'attachments': {'data': [{'media_type': 'video'}]},
             'reactions': {'summary': {'total_count': 5}}, 'comments': {'summary': {'total_count': 2}},
             'shares': {'count': 1}},
            {'id': 'PAGE_1', 'message': 'Old', 'created_time': '2026-09-01T10:00:00+0000',
             'permalink_url': 'https://www.facebook.com/p/1', 'attachments': {'data': [{'media_type': 'album'}]}},
        ]}
        with mock.patch('social.adapters.meta.graph', return_value=data) as g:
            out = FacebookAdapter().fetch_posts(account(), since=datetime(2026, 9, 15, tzinfo=tz.utc))
        self.assertEqual(g.call_args[0][1], 'PAGE/published_posts')
        self.assertEqual(len(out), 1)  # the September post is older than since
        p = out[0]
        self.assertEqual((p.kind, p.text, p.thumbnail_url), ('reel', 'Reel!', 'https://x/a.jpg'))
        self.assertEqual(p.metrics, {'likes': 5, 'comments': 2, 'shares': 1, 'engagement': 8})


class InstagramPostsTests(SimpleTestCase):
    def test_kinds_and_thumbnails(self):
        data = {'data': [
            {'id': '1', 'caption': 'r', 'media_type': 'VIDEO', 'media_product_type': 'REELS',
             'thumbnail_url': 'https://cdn/t.jpg', 'media_url': 'https://cdn/v.mp4', 'permalink': 'https://ig/r',
             'timestamp': '2026-10-11T08:00:00+0000', 'like_count': 40, 'comments_count': 3},
            {'id': '2', 'media_type': 'CAROUSEL_ALBUM', 'media_product_type': 'FEED', 'media_url': 'https://cdn/c.jpg',
             'timestamp': '2026-10-09T08:00:00+0000'},
            {'id': '3', 'media_type': 'IMAGE', 'media_product_type': 'FEED', 'media_url': 'https://cdn/i.jpg',
             'timestamp': '2026-10-08T08:00:00+0000', 'like_count': 1},
        ]}
        with mock.patch('social.adapters.meta.graph', return_value=data) as g:
            out = InstagramAdapter().fetch_posts(account())
        self.assertEqual(g.call_args[0][1], '123/media')
        self.assertEqual([p.kind for p in out], ['reel', 'carousel', 'post'])
        self.assertEqual(out[0].thumbnail_url, 'https://cdn/t.jpg')   # video: the still, not the mp4
        self.assertEqual(out[1].thumbnail_url, 'https://cdn/c.jpg')
        self.assertEqual(out[0].metrics['engagement'], 43)
        self.assertEqual(out[1].text, '')


class YouTubePostsTests(SimpleTestCase):
    def test_uploads_with_stats(self):
        responses = [
            {'items': [{'contentDetails': {'relatedPlaylists': {'uploads': 'UU123'}}}]},
            {'items': [{'contentDetails': {'videoId': 'a'}}, {'contentDetails': {'videoId': 'b'}}]},
            {'items': [
                {'id': 'a', 'snippet': {'title': 'Ep 1', 'publishedAt': '2026-10-01T10:00:00.123456789Z',
                                        'thumbnails': {'high': {'url': 'https://i.ytimg.com/a.jpg'}}},
                 'statistics': {'viewCount': '900', 'likeCount': '30', 'commentCount': '4'}},
                {'id': 'b', 'snippet': {'title': 'Ep 2', 'publishedAt': '2026-10-08T10:00:00Z'},
                 'statistics': {'viewCount': '100'}},
            ]},
        ]
        fake = mock.Mock(side_effect=[mock.Mock(json=mock.Mock(return_value=r)) for r in responses])
        with mock.patch.object(YouTubeAdapter, '_api', fake):
            out = YouTubeAdapter().fetch_posts(account())
        self.assertEqual([p.title for p in out], ['Ep 2', 'Ep 1'])  # newest first
        self.assertEqual(out[1].url, 'https://youtu.be/a')
        self.assertEqual(out[1].metrics, {'views': 900, 'likes': 30, 'comments': 4, 'engagement': 34})
        self.assertEqual(out[0].thumbnail_url, '')
