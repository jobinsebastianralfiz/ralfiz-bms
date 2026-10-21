"""Comment-to-DM: webhook comment -> keyword match -> private reply DM + public reply, Graph mocked."""
import hashlib
import hmac
import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import RequestFactory
from django.utils import timezone

from social import automations as A
from social.models import Automation, AutomationRun, InboxItem, InboxReply
from social.services import SocialError
from social.webhooks import meta_webhook

from .test_meta import SECRET, MetaTestCase, graph


def fb_comment(comment_id, text, who='U1', name='Anu', post='P1_1'):
    return {'object': 'page', 'entry': [{'id': 'P1', 'time': 1, 'changes': [
        {'field': 'feed', 'value': {'item': 'comment', 'verb': 'add', 'comment_id': comment_id,
                                    'post_id': post, 'message': text,
                                    'created_time': int(timezone.now().timestamp()),
                                    'from': {'id': who, 'name': name}}}]}]}


class AutomationTestCase(MetaTestCase):
    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_superuser('owner', 'o@x.in', 'pw')
        self.fb = self.account('facebook', 'P1', page_id='P1')
        self.ig = self.account('instagram', 'IG1', page_id='P1', handle='@acme')
        self.auto = Automation.objects.create(
            workspace=self.ws, account=self.fb, name='Skill reel', keywords=['skill'],
            public_replies=['Sent to your DMs 📩'], dm_text='Here is the skill',
            button_label='Download Skill', button_url='https://ralfizdigital.in/s/seo')

    def deliver(self, payload):
        body = json.dumps(payload).encode()
        sig = 'sha256=' + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
        req = RequestFactory().post('/social/webhooks/meta/', body, content_type='application/json',
                                    HTTP_X_HUB_SIGNATURE_256=sig)
        self.assertEqual(meta_webhook(req).status_code, 200)


class EndToEndTests(AutomationTestCase):
    def test_facebook_comment_gets_dm_and_public_reply(self):
        self.deliver(fb_comment('C1', 'SKILL please 🔥'))
        run = AutomationRun.objects.get()
        self.assertEqual((run.status, run.commenter_id, run.item.external_id), ('queued', 'U1', 'C1'))

        fake, patch = graph({'recipient_id': 'U1', 'message_id': 'mid.1'}, {'id': 'C1_r'})
        with patch:
            self.assertEqual(A.run_due(), 1)
        self.assertEqual(fake.paths(), [('POST', '/P1/messages'), ('POST', '/C1/comments')])
        sent = fake.calls[0][2]['data']
        self.assertEqual(json.loads(sent['recipient']), {'comment_id': 'C1'})
        button = json.loads(sent['message'])['attachment']['payload']
        self.assertEqual((button['text'], button['buttons'][0]['url'], button['buttons'][0]['title']),
                         ('Here is the skill', 'https://ralfizdigital.in/s/seo', 'Download Skill'))
        self.assertEqual(fake.calls[1][2]['data'], {'message': 'Sent to your DMs 📩'})

        run.refresh_from_db()
        self.assertEqual((run.status, run.dm_id, run.reply_id, run.error), ('sent', 'mid.1', 'C1_r', ''))
        item = InboxItem.objects.get(external_id='C1')
        self.assertEqual(item.status, 'done')
        self.assertEqual(InboxReply.objects.get(item=item).source, 'auto')

    def test_instagram_comment_goes_through_linked_page(self):
        Automation.objects.create(workspace=self.ws, account=self.ig, name='IG', keywords=['seo'],
                                  dm_text='Link inside')
        self.deliver({'object': 'instagram', 'entry': [{'id': 'IG1', 'changes': [
            {'field': 'comments', 'value': {'id': 'IC1', 'text': 'seo', 'media': {'id': 'MED1'},
                                            'from': {'id': 'IGU', 'username': 'fan'}}}]}]})
        fake, patch = graph({'message_id': 'mid.2'})
        with patch:
            A.run_due()
        self.assertEqual(fake.paths(), [('POST', '/P1/messages')])     # no public replies set
        self.assertEqual(json.loads(fake.calls[0][2]['data']['message']), {'text': 'Link inside'})
        self.assertEqual(AutomationRun.objects.get().status, 'sent')

    def test_webhook_twice_queues_once(self):
        self.deliver(fb_comment('C1', 'skill'))
        self.deliver(fb_comment('C1', 'skill'))
        self.assertEqual(AutomationRun.objects.count(), 1)

    def test_same_person_twice_on_one_post_gets_one_dm(self):
        self.deliver(fb_comment('C1', 'skill'))
        self.deliver(fb_comment('C2', 'skill again'))
        fake, patch = graph({'message_id': 'm1'}, {'id': 'r1'})
        with patch:
            self.assertEqual(A.run_due(), 1)
        self.assertEqual(sorted(AutomationRun.objects.values_list('status', flat=True)), ['sent', 'skipped'])


class MatchingTests(AutomationTestCase):
    def test_contains_needs_the_whole_word(self):
        self.assertTrue(A.matches(self.auto, 'Send me the Skill!'))
        self.assertFalse(A.matches(self.auto, 'skills are great'))

    def test_exact(self):
        self.auto.match_type = 'exact'
        self.assertTrue(A.matches(self.auto, '  Skill 🔥 '))
        self.assertFalse(A.matches(self.auto, 'skill please'))

    def test_skips_other_posts_off_and_old_comments(self):
        self.auto.post_id = 'P1_9'
        self.auto.save()
        self.deliver(fb_comment('C1', 'skill'))                         # different post
        self.auto.post_id, self.auto.is_active = '', False
        self.auto.save()
        self.deliver(fb_comment('C2', 'skill'))                         # switched off
        self.auto.is_active = True
        self.auto.save()
        old = fb_comment('C3', 'skill')
        old['entry'][0]['changes'][0]['value']['created_time'] = int(
            (self.auto.created_at - timedelta(hours=1)).timestamp())
        self.deliver(old)                                               # before the automation
        self.deliver(fb_comment('C4', 'nothing to see'))                # no keyword
        self.assertFalse(AutomationRun.objects.exists())
        self.assertEqual(InboxItem.objects.count(), 4)                  # still in the inbox


class FailureTests(AutomationTestCase):
    def setUp(self):
        super().setUp()
        self.deliver(fb_comment('C1', 'skill'))
        self.run = AutomationRun.objects.get()

    def test_temporary_error_retries_then_fails(self):
        for attempt in range(1, AutomationRun.MAX_ATTEMPTS + 1):
            AutomationRun.objects.filter(pk=self.run.pk).update(next_attempt_at=timezone.now())
            fake, patch = graph((500, {'error': {'message': 'down', 'code': 2}}))
            with patch:
                A.run_due()
            self.run.refresh_from_db()
            self.assertEqual(self.run.attempts, attempt)
        self.assertEqual(self.run.status, 'failed')
        self.assertIn('down', self.run.error)

    def test_dead_token_marks_account(self):
        fake, patch = graph((400, {'error': {'message': 'expired', 'code': 190}}))
        with patch:
            A.run_due()
        self.run.refresh_from_db()
        self.fb.refresh_from_db()
        self.assertEqual((self.run.status, self.fb.status), ('failed', 'reconnect'))

    def test_public_reply_failure_keeps_dm_sent(self):
        fake, patch = graph({'message_id': 'm1'}, (400, {'error': {'message': 'nope', 'code': 100}}))
        with patch:
            self.assertEqual(A.run_due(), 1)
        self.run.refresh_from_db()
        self.assertEqual(self.run.status, 'sent')
        self.assertIn('public reply failed', self.run.error)

    def test_stale_lock_is_not_retried(self):
        AutomationRun.objects.filter(pk=self.run.pk).update(
            status='sending', locked_at=timezone.now() - timedelta(hours=1))
        fake, patch = graph()
        with patch:
            A.run_due()
        self.run.refresh_from_db()
        self.assertEqual((self.run.status, fake.calls), ('failed', []))

    def test_hourly_limit_defers(self):
        AutomationRun.objects.bulk_create([AutomationRun(
            automation=self.auto, item=InboxItem.objects.create(account=self.fb, kind='comment',
                                                                external_id=f'X{i}'),
            status='sent', sent_at=timezone.now()) for i in range(A.HOURLY_LIMIT)])
        fake, patch = graph()
        with patch:
            self.assertEqual(A.run_due(), 0)
        self.run.refresh_from_db()
        self.assertEqual((self.run.status, self.run.attempts), ('queued', 0))
        self.assertGreater(self.run.next_attempt_at, timezone.now())


class PageTests(AutomationTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)

    def test_page_lists_and_creates(self):
        res = self.client.get('/social/automations/')
        self.assertContains(res, 'Skill reel')
        res = self.client.post('/social/automations/', {
            'account': self.ig.pk, 'keywords': 'SEO, audit', 'dm_text': 'Your audit',
            'public_replies': 'Check DMs\nSent 📩', 'match_type': 'exact', 'is_active': 'on',
            'ends_at': '2030-01-31'})
        self.assertRedirects(res, '/social/automations/', fetch_redirect_response=False)
        a = Automation.objects.get(account=self.ig)
        self.assertEqual((a.keywords, a.public_replies, a.match_type, a.name),
                         (['SEO', 'audit'], ['Check DMs', 'Sent 📩'], 'exact', 'SEO automation'))
        self.assertEqual(timezone.localtime(a.ends_at).date().isoformat(), '2030-01-31')

    def test_toggle(self):
        self.client.post('/social/automations/', {'action': 'toggle', 'id': self.auto.pk})
        self.auto.refresh_from_db()
        self.assertFalse(self.auto.is_active)

    def test_validation(self):
        base = {'keywords': 'x', 'dm_text': 'hi'}
        for bad in ({'keywords': ''}, {'dm_text': ''}, {'button_label': 'Go'},
                    {'button_label': 'Go', 'button_url': 'http://insecure.in'}, {'dm_text': 'x' * 641}):
            with self.assertRaises(SocialError):
                A.save_automation(self.owner, self.ws, {'account': self.fb.pk, **base, **bad})
        with self.assertRaises(SocialError):
            A.save_automation(self.owner, self.ws, {'account': self.account('linkedin', 'L1').pk, **base})
