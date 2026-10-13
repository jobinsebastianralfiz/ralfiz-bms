"""Facebook, Instagram and WhatsApp adapters plus the Meta webhook, with HTTP mocked."""
import hashlib
import hmac
import json
from datetime import date
from unittest import mock
from urllib.parse import parse_qs, urlparse

import requests
from cryptography.fernet import Fernet
from django.test import TestCase, override_settings

from social.adapters.base import AdapterError, AuthError, MediaInput, NotSupported
from social.adapters.meta import FacebookAdapter, InstagramAdapter
from social.adapters.whatsapp import WhatsAppAdapter
from social.models import InboxItem, SocialAccount, Workspace

SECRET = 'app-secret'
META = dict(META_APP_ID='123', META_APP_SECRET=SECRET, META_GRAPH_VERSION='v23.0',
            META_WEBHOOK_VERIFY_TOKEN='verify-me', SOCIAL_TOKEN_KEY=Fernet.generate_key().decode())


def _response(status, body):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(body).encode()
    r.headers['Content-Type'] = 'application/json'
    return r


class FakeGraph:
    """Stands in for requests.request: answers in order and runs response hooks like requests does."""

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def __call__(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        answer = self.answers.pop(0)
        status, body = answer if isinstance(answer, tuple) else (200, answer)
        return requests.hooks.dispatch_hook('response', kwargs.get('hooks'), _response(status, body))

    def paths(self):
        return [(m, urlparse(u).path.replace('/v23.0', '', 1)) for m, u, _ in self.calls]


def graph(*answers):
    fake = FakeGraph(*answers)
    return fake, mock.patch('social.adapters.base.requests.request', side_effect=fake)


def image(n=1):
    return MediaInput('image', f'https://cdn.test/{n}.jpg', 'image/jpeg', 100, f'{n}.jpg')


def video():
    return MediaInput('video', 'https://cdn.test/v.mp4', 'video/mp4', 1000, 'v.mp4')


@override_settings(**META)
class MetaTestCase(TestCase):
    def setUp(self):
        self.ws = Workspace.objects.create(name='Acme')

    def account(self, platform, external_id, handle='', **extra):
        acc = SocialAccount(workspace=self.ws, platform=platform, external_id=external_id,
                            name=platform, handle=handle, extra=extra)
        acc.token = 'page-token'
        acc.save()
        return acc


class OAuthTests(MetaTestCase):
    def test_authorize_url(self):
        url = urlparse(FacebookAdapter().authorize_url('st8', 'https://app.test/cb'))
        q = parse_qs(url.query)
        self.assertEqual((url.netloc, url.path), ('www.facebook.com', '/v23.0/dialog/oauth'))
        self.assertEqual((q['client_id'], q['state'], q['redirect_uri']), (['123'], ['st8'], ['https://app.test/cb']))
        self.assertIn('pages_manage_posts', q['scope'][0])
        self.assertNotIn('instagram_basic', q['scope'][0])
        ig = parse_qs(urlparse(InstagramAdapter().authorize_url('s', 'https://app.test/cb')).query)
        self.assertIn('instagram_content_publish', ig['scope'][0])
        self.assertIn('pages_show_list', ig['scope'][0])

    def _pages(self):
        return ({'access_token': 'short'}, {'access_token': 'long'}, {'data': [
            {'id': 'P1', 'name': 'Acme Page', 'access_token': 'pt1',
             'picture': {'data': {'url': 'https://pic/1'}},
             'instagram_business_account': {'id': 'IG1', 'username': 'acme', 'profile_picture_url': 'https://ig/1'}},
            {'id': 'P2', 'name': 'Other Page', 'access_token': 'pt2'},
        ]})

    def test_facebook_exchange_code(self):
        fake, patch = graph(*self._pages())
        with patch:
            cands = FacebookAdapter().exchange_code('code', 'https://app.test/cb')
        self.assertEqual([(c.external_id, c.token, c.expires_at) for c in cands],
                         [('P1', 'pt1', None), ('P2', 'pt2', None)])
        self.assertEqual(cands[0].avatar_url, 'https://pic/1')
        self.assertEqual(cands[0].extra, {'page_id': 'P1'})
        swap = fake.calls[1][2]['params']
        self.assertEqual((swap['grant_type'], swap['fb_exchange_token']), ('fb_exchange_token', 'short'))
        self.assertEqual(fake.calls[2][2]['headers']['Authorization'], 'Bearer long')

    def test_instagram_exchange_code_only_linked_pages(self):
        fake, patch = graph(*self._pages())
        with patch:
            cands = InstagramAdapter().exchange_code('code', 'https://app.test/cb')
        self.assertEqual(len(cands), 1)
        c = cands[0]
        self.assertEqual((c.external_id, c.handle, c.token, c.extra), ('IG1', '@acme', 'pt1', {'page_id': 'P1'}))


class FacebookPublishTests(MetaTestCase):
    def setUp(self):
        super().setUp()
        self.acc = self.account('facebook', 'P1', page_id='P1')
        self.fb = FacebookAdapter()

    def test_text_and_link(self):
        fake, patch = graph({'id': 'P1_9'})
        with patch:
            res = self.fb.publish(self.acc, 'Hello', [], link='https://acme.test')
        self.assertEqual(fake.paths(), [('POST', '/P1/feed')])
        self.assertEqual(fake.calls[0][2]['data'], {'message': 'Hello', 'link': 'https://acme.test'})
        self.assertEqual((res.external_id, res.url), ('P1_9', 'https://www.facebook.com/P1_9'))

    def test_single_photo_with_first_comment_failure(self):
        fake, patch = graph({'id': 'PH1', 'post_id': 'P1_7'}, (400, {'error': {'code': 100, 'message': 'nope'}}))
        with patch:
            res = self.fb.publish(self.acc, 'Pic', [image()], first_comment='#tags')
        self.assertEqual(fake.paths(), [('POST', '/P1/photos'), ('POST', '/P1_7/comments')])
        self.assertEqual(fake.calls[0][2]['data']['url'], 'https://cdn.test/1.jpg')
        self.assertEqual(res.external_id, 'P1_7')

    def test_multi_photo(self):
        fake, patch = graph({'id': 'A'}, {'id': 'B'}, {'id': 'P1_8'})
        with patch:
            res = self.fb.publish(self.acc, 'Two', [image(1), image(2)])
        self.assertEqual(fake.paths(), [('POST', '/P1/photos'), ('POST', '/P1/photos'), ('POST', '/P1/feed')])
        self.assertEqual(fake.calls[0][2]['data']['published'], 'false')
        feed = fake.calls[2][2]['data']
        self.assertEqual(json.loads(feed['attached_media[1]']), {'media_fbid': 'B'})
        self.assertEqual(res.external_id, 'P1_8')

    def test_video(self):
        fake, patch = graph({'id': 'V1'})
        with patch:
            self.fb.publish(self.acc, 'Watch', [video()])
        self.assertEqual(fake.paths(), [('POST', '/P1/videos')])
        self.assertEqual(fake.calls[0][2]['data']['file_url'], 'https://cdn.test/v.mp4')

    def test_error_190_is_auth_error(self):
        fake, patch = graph((400, {'error': {'code': 190, 'type': 'OAuthException', 'message': 'Session expired'}}))
        with patch, self.assertRaises(AuthError):
            self.fb.publish(self.acc, 'Hi', [])

    def test_500_is_retryable(self):
        fake, patch = graph((500, {'error': {'message': 'boom'}}))
        with patch, self.assertRaises(AdapterError) as ctx:
            self.fb.publish(self.acc, 'Hi', [])
        self.assertTrue(ctx.exception.retryable)
        self.assertNotIsInstance(ctx.exception, AuthError)

    def test_plain_400_is_not_auth(self):
        fake, patch = graph((400, {'error': {'code': 100, 'message': 'Invalid parameter'}}))
        with patch, self.assertRaises(AdapterError) as ctx:
            self.fb.publish(self.acc, 'Hi', [])
        self.assertNotIsInstance(ctx.exception, AuthError)
        self.assertFalse(ctx.exception.retryable)

    def test_inbox_skips_page_and_reply(self):
        fake, patch = graph(
            {'data': [{'id': 'P1_1', 'comments': {'data': [
                {'id': 'C1', 'message': 'Price?', 'from': {'id': 'U1', 'name': 'Anu'},
                 'created_time': '2026-10-01T10:00:00+0000'},
                {'id': 'C2', 'message': 'Thanks', 'from': {'id': 'P1'}, 'created_time': '2026-10-01T10:05:00+0000'},
            ]}}]},
            {'data': [{'id': 'T1', 'updated_time': '2026-10-01T11:00:00+0000', 'messages': {'data': [
                {'id': 'M1', 'message': 'Open today?', 'from': {'id': 'PSID9', 'name': 'Raj'},
                 'created_time': '2026-10-01T11:00:00+0000'},
                {'id': 'M2', 'message': 'Yes', 'from': {'id': 'P1'}, 'created_time': '2026-10-01T11:01:00+0000'},
            ]}}]})
        with patch:
            items = self.fb.fetch_inbox(self.acc)
        self.assertEqual([(i.kind, i.external_id, i.thread_id, i.author_id) for i in items],
                         [('comment', 'C1', 'P1_1', 'U1'), ('dm', 'M1', 'T1', 'PSID9')])
        dm = InboxItem(account=self.acc, kind='dm', external_id='M1', author_id='PSID9')
        fake, patch = graph({'recipient_id': 'PSID9', 'message_id': 'mid.1'})
        with patch:
            self.assertEqual(self.fb.reply(self.acc, dm, 'Yes!'), 'mid.1')
        sent = fake.calls[0][2]['data']
        self.assertEqual((json.loads(sent['recipient']), sent['messaging_type']), ({'id': 'PSID9'}, 'RESPONSE'))

    def test_insights_maps_metrics(self):
        fake, patch = graph({'data': [
            {'name': 'page_total_media_view_unique',
             'values': [{'value': 40, 'end_time': '2026-10-02T07:00:00+0000'}]},
            {'name': 'page_follows', 'values': [{'value': 900, 'end_time': '2026-10-02T07:00:00+0000'}]},
        ]})
        with patch:
            out = self.fb.fetch_insights(self.acc, date(2026, 10, 1), date(2026, 10, 1))
        self.assertEqual(out, {date(2026, 10, 1): {'reach': 40, 'followers': 900}})


@mock.patch('social.adapters.meta.time.sleep')
class InstagramPublishTests(MetaTestCase):
    def setUp(self):
        super().setUp()
        self.acc = self.account('instagram', 'IG1', page_id='P1')
        self.ig = InstagramAdapter()

    def test_single_image(self, sleep):
        fake, patch = graph({'id': 'CT1'}, {'status_code': 'FINISHED'}, {'id': 'MED1'},
                            {'permalink': 'https://instagram.com/p/x'})
        with patch:
            res = self.ig.publish(self.acc, 'Caption', [image()])
        self.assertEqual(fake.paths(), [('POST', '/IG1/media'), ('GET', '/CT1'),
                                        ('POST', '/IG1/media_publish'), ('GET', '/MED1')])
        self.assertEqual(fake.calls[0][2]['data'], {'image_url': 'https://cdn.test/1.jpg', 'caption': 'Caption'})
        self.assertEqual(fake.calls[2][2]['data'], {'creation_id': 'CT1'})
        self.assertEqual((res.external_id, res.url), ('MED1', 'https://instagram.com/p/x'))

    def test_carousel(self, sleep):
        fake, patch = graph({'id': 'K1'}, {'id': 'K2'}, {'status_code': 'FINISHED'}, {'status_code': 'FINISHED'},
                            {'id': 'CAR'}, {'status_code': 'FINISHED'}, {'id': 'MED2'}, {'permalink': ''})
        with patch:
            res = self.ig.publish(self.acc, 'Two', [image(1), image(2)])
        self.assertEqual(fake.calls[0][2]['data']['is_carousel_item'], 'true')
        parent = fake.calls[4][2]['data']
        self.assertEqual((parent['media_type'], parent['children']), ('CAROUSEL', 'K1,K2'))
        self.assertEqual(res.external_id, 'MED2')

    def test_video_polls_until_finished(self, sleep):
        fake, patch = graph({'id': 'CT'}, {'status_code': 'IN_PROGRESS'}, {'status_code': 'IN_PROGRESS'},
                            {'status_code': 'FINISHED'}, {'id': 'REEL'}, {'id': 'CM'}, {'permalink': ''})
        with patch:
            res = self.ig.publish(self.acc, 'Reel', [video()], first_comment='#reels')
        self.assertEqual(fake.calls[0][2]['data']['media_type'], 'REELS')
        self.assertEqual(fake.calls[0][2]['data']['video_url'], 'https://cdn.test/v.mp4')
        self.assertEqual(sleep.call_count, 2)
        self.assertIn(('POST', '/REEL/comments'), fake.paths())
        self.assertEqual(res.external_id, 'REEL')

    def test_video_still_processing_is_retryable(self, sleep):
        tries = InstagramAdapter.POLL_TRIES
        fake, patch = graph({'id': 'CT'}, *[{'status_code': 'IN_PROGRESS'}] * tries)
        with patch, self.assertRaises(AdapterError) as ctx:
            self.ig.publish(self.acc, 'Reel', [video()])
        self.assertTrue(ctx.exception.retryable)
        self.assertNotIn(('POST', '/IG1/media_publish'), fake.paths())

    def test_video_error_is_final(self, sleep):
        fake, patch = graph({'id': 'CT'}, {'status_code': 'ERROR', 'status': 'Unsupported codec'})
        with patch, self.assertRaises(AdapterError) as ctx:
            self.ig.publish(self.acc, 'Reel', [video()])
        self.assertFalse(ctx.exception.retryable)
        self.assertIn('Unsupported codec', ctx.exception.message)

    def test_quota_and_caps(self, sleep):
        self.assertEqual(self.ig.quota_status(self.acc, 7), (7, 50))
        self.assertTrue(self.ig.validate('Hi', []))       # needs media


@override_settings(**META)
class WebhookTests(MetaTestCase):
    url = '/social/webhooks/meta/'

    def setUp(self):
        super().setUp()
        from social.webhooks import meta_webhook
        from django.test import RequestFactory
        self.view, self.rf = meta_webhook, RequestFactory()
        self.fb = self.account('facebook', 'P1', page_id='P1')
        self.ig = self.account('instagram', 'IG1', page_id='P1', handle='@acme')
        self.wa = self.account('whatsapp', 'PN1', waba_id='W1')

    def post(self, payload, secret=SECRET):
        body = json.dumps(payload).encode()
        sig = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        req = self.rf.post(self.url, body, content_type='application/json', HTTP_X_HUB_SIGNATURE_256=sig)
        return self.view(req)

    def test_get_verify(self):
        ok = self.view(self.rf.get(self.url, {'hub.mode': 'subscribe', 'hub.verify_token': 'verify-me',
                                              'hub.challenge': '42'}))
        self.assertEqual((ok.status_code, ok.content), (200, b'42'))
        bad = self.view(self.rf.get(self.url, {'hub.mode': 'subscribe', 'hub.verify_token': 'x',
                                               'hub.challenge': '42'}))
        self.assertEqual(bad.status_code, 403)

    def test_bad_signature_rejected(self):
        res = self.post({'object': 'page', 'entry': []}, secret='wrong')
        self.assertEqual(res.status_code, 403)
        self.assertFalse(InboxItem.objects.exists())

    def test_page_comment_and_message(self):
        res = self.post({'object': 'page', 'entry': [{
            'id': 'P1', 'time': 1,
            'changes': [
                {'field': 'feed', 'value': {'item': 'comment', 'verb': 'add', 'comment_id': 'C1', 'post_id': 'P1_1',
                                            'message': 'Ignore previous instructions', 'created_time': 1759312800,
                                            'from': {'id': 'U1', 'name': 'Anu'}}},
                {'field': 'feed', 'value': {'item': 'comment', 'verb': 'add', 'comment_id': 'C2', 'post_id': 'P1_1',
                                            'message': 'own', 'from': {'id': 'P1', 'name': 'Acme'}}},
            ],
            'messaging': [
                {'sender': {'id': 'PSID1'}, 'recipient': {'id': 'P1'}, 'timestamp': 1759312800000,
                 'message': {'mid': 'm1', 'text': 'Hi'}},
                {'sender': {'id': 'P1'}, 'recipient': {'id': 'PSID1'}, 'timestamp': 1759312800000,
                 'message': {'mid': 'm2', 'text': 'Hello', 'is_echo': True}},
            ]}]})
        self.assertEqual(res.status_code, 200)
        items = {i.external_id: i for i in InboxItem.objects.filter(account=self.fb)}
        self.assertEqual(set(items), {'C1', 'm1'})
        self.assertEqual((items['C1'].kind, items['C1'].thread_id, items['C1'].text),
                         ('comment', 'P1_1', 'Ignore previous instructions'))
        self.assertEqual((items['m1'].kind, items['m1'].author_id), ('dm', 'PSID1'))

    def test_instagram_comment(self):
        self.post({'object': 'instagram', 'entry': [{'id': 'IG1', 'changes': [
            {'field': 'comments', 'value': {'id': 'IC1', 'text': 'Love it', 'media': {'id': 'MED1'},
                                            'from': {'id': 'IGU', 'username': 'fan'}}}]}]})
        item = InboxItem.objects.get(account=self.ig)
        self.assertEqual((item.external_id, item.thread_id, item.author_name), ('IC1', 'MED1', 'fan'))

    def test_whatsapp_message_and_unknown_account(self):
        msg = {'object': 'whatsapp_business_account', 'entry': [{'id': 'W1', 'changes': [{'field': 'messages', 'value': {
            'messaging_product': 'whatsapp', 'metadata': {'phone_number_id': 'PN1', 'display_phone_number': '91'},
            'contacts': [{'wa_id': '919800000000', 'profile': {'name': 'Meera'}}],
            'messages': [{'from': '919800000000', 'id': 'wamid.1', 'timestamp': '1759312800',
                          'type': 'text', 'text': {'body': 'Is the shop open?'}}]}}]}]}
        self.assertEqual(self.post(msg).status_code, 200)
        item = InboxItem.objects.get(account=self.wa)
        self.assertEqual((item.kind, item.author_id, item.author_name, item.text),
                         ('dm', '919800000000', 'Meera', 'Is the shop open?'))
        msg['entry'][0]['changes'][0]['value']['metadata']['phone_number_id'] = 'UNKNOWN'
        self.assertEqual(self.post(msg).status_code, 200)
        self.assertEqual(InboxItem.objects.count(), 1)


class WhatsAppTests(MetaTestCase):
    def test_manual_connect(self):
        fake, patch = graph({'verified_name': 'Acme Store', 'display_phone_number': '+91 98000 00000', 'id': 'PN1'},
                            {'success': True}, {'data': {'expires_at': 0}})
        with patch:
            [c] = WhatsAppAdapter().manual_connect(
                {'phone_number_id': 'PN1', 'waba_id': 'W1', 'access_token': 'sys-token'})
        self.assertEqual((c.external_id, c.name, c.token, c.extra), ('PN1', 'Acme Store', 'sys-token', {'waba_id': 'W1'}))
        self.assertIsNone(c.expires_at)                     # a System User token never expires
        self.assertEqual(fake.paths(), [('GET', '/PN1'), ('POST', '/W1/subscribed_apps'), ('GET', '/debug_token')])
        self.assertEqual(fake.calls[0][2]['headers']['Authorization'], 'Bearer sys-token')

    def test_manual_connect_bad_token(self):
        fake, patch = graph((401, {'error': {'code': 190, 'message': 'Invalid OAuth access token'}}))
        with patch, self.assertRaises(AuthError):
            WhatsAppAdapter().manual_connect({'phone_number_id': 'PN1', 'waba_id': 'W1', 'access_token': 'x'})
        with self.assertRaises(AdapterError):
            WhatsAppAdapter().manual_connect({'phone_number_id': 'PN1'})

    def test_reply_and_no_publish(self):
        acc = self.account('whatsapp', 'PN1', waba_id='W1')
        item = InboxItem(account=acc, kind='dm', external_id='wamid.1', author_id='919800000000')
        fake, patch = graph({'messages': [{'id': 'wamid.OUT'}]})
        with patch:
            self.assertEqual(WhatsAppAdapter().reply(acc, item, 'Yes, till 9pm'), 'wamid.OUT')
        self.assertEqual(fake.paths(), [('POST', '/PN1/messages')])
        body = fake.calls[0][2]['json']
        self.assertEqual((body['to'], body['type'], body['text']['body']), ('919800000000', 'text', 'Yes, till 9pm'))
        self.assertTrue(WhatsAppAdapter().validate('Hi', []))
        with self.assertRaises(NotSupported):
            WhatsAppAdapter().publish(acc, 'Hi', [])
