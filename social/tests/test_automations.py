"""Comment-to-DM: webhook comment -> keyword match -> private reply DM + public reply, Graph mocked."""
import hashlib
import hmac
import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import RequestFactory, override_settings
from django.utils import timezone

from social import automations as A
from social.models import Automation, AutomationRun, InboxItem, InboxReply, LeadCapture
from social.services import SocialError
from social.webhooks import meta_webhook

from .test_meta import SECRET, MetaTestCase, graph


def fb_comment(comment_id, text, who='U1', name='Anu', post='P1_1'):
    return {'object': 'page', 'entry': [{'id': 'P1', 'time': 1, 'changes': [
        {'field': 'feed', 'value': {'item': 'comment', 'verb': 'add', 'comment_id': comment_id,
                                    'post_id': post, 'message': text,
                                    'created_time': int(timezone.now().timestamp()),
                                    'from': {'id': who, 'name': name}}}]}]}


@override_settings(SOCIAL_PUBLIC_BASE_URL='https://ralfizdigital.in')
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
        slug = self.auto.link.slug
        self.assertEqual((button['text'], button['buttons'][0]['url'], button['buttons'][0]['title']),
                         ('Here is the skill', f'https://ralfizdigital.in/go/{slug}/?r={run.pk}', 'Download Skill'))
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


# ---------------------------------------------------------------- phase 2

def ig_comment(comment_id, text, who='IGU'):
    return {'object': 'instagram', 'entry': [{'id': 'IG1', 'changes': [
        {'field': 'comments', 'value': {'id': comment_id, 'text': text, 'media': {'id': 'MED1'},
                                        'from': {'id': who, 'username': 'fan'}}}]}]}


def _now_ms():
    return int(timezone.now().timestamp() * 1000)


def tap(entry_id, sender, payload, mid, obj='instagram'):
    return {'object': obj, 'entry': [{'id': entry_id, 'messaging': [
        {'sender': {'id': sender}, 'recipient': {'id': entry_id}, 'timestamp': _now_ms(),
         'postback': {'mid': mid, 'title': 'Send me the link', 'payload': payload}}]}]}


def ig_dm(sender, text, mid):
    return {'object': 'instagram', 'entry': [{'id': 'IG1', 'messaging': [
        {'sender': {'id': sender}, 'recipient': {'id': 'IG1'}, 'timestamp': _now_ms(),
         'message': {'mid': mid, 'text': text}}]}]}


def sent_message(fake, i):
    return json.loads(fake.calls[i][2]['data']['message'])


class OpenerTests(AutomationTestCase):
    def setUp(self):
        super().setUp()
        self.gated = Automation.objects.create(
            workspace=self.ws, account=self.ig, name='SEO reel', keywords=['seo'], dm_text='Want the skill?',
            delivery='opener', follow_gate=True, button_label='Download', button_url='https://x.in/seo.zip',
            followup_text='Did it work?', followup_hours=6)
        self.deliver(ig_comment('IC1', 'SEO'))
        fake, patch = graph({'message_id': 'm1'})
        with patch:
            A.run_due()
        self.run = AutomationRun.objects.get(automation=self.gated)
        opener = sent_message(fake, 0)['attachment']['payload']['buttons'][0]
        self.assertEqual(opener, {'type': 'postback', 'payload': f'AUTO:{self.run.pk}', 'title': A.DEFAULT_OPENER})

    def test_follow_gate_then_link_then_followup(self):
        fake, patch = graph({'name': 'Fan', 'username': 'fan', 'is_user_follow_business': False},
                            {'message_id': 'm2'})
        with patch:
            self.deliver(tap('IG1', 'IGSID', f'AUTO:{self.run.pk}', 'pb1'))
        self.assertEqual(fake.paths(), [('GET', '/IGSID'), ('POST', '/P1/messages')])
        ask = sent_message(fake, 1)['attachment']['payload']
        self.assertEqual((ask['text'], ask['buttons'][0]['title']), (A.DEFAULT_GATE_TEXT, A.GATE_AGAIN))
        self.assertEqual(json.loads(fake.calls[1][2]['data']['recipient']), {'id': 'IGSID'})
        self.run.refresh_from_db()
        self.assertEqual((self.run.was_follower, self.run.link_sent_at), (False, None))

        fake, patch = graph()                                           # Meta redelivers the same tap
        with patch:
            self.deliver(tap('IG1', 'IGSID', f'AUTO:{self.run.pk}', 'pb1'))
        self.assertEqual(fake.calls, [])

        fake, patch = graph({'name': 'Fan', 'username': 'fan', 'is_user_follow_business': True},
                            {'message_id': 'm3'})
        with patch:
            self.deliver(tap('IG1', 'IGSID', f'AUTO:{self.run.pk}', 'pb2'))
        link = sent_message(fake, 1)['attachment']['payload']
        self.assertEqual(link['text'], A.DEFAULT_LINK_TEXT)
        self.assertIn(f'/go/{self.gated.link.slug}/?r={self.run.pk}', link['buttons'][0]['url'])
        self.run.refresh_from_db()
        self.assertTrue(self.run.follow_gained)
        self.assertEqual((self.run.contact.messaging_id, self.run.contact.is_follower), ('IGSID', True))
        self.assertEqual(A.stats([self.gated])[self.gated.pk]['follows'], 1)

        fake, patch = graph()
        with patch:
            self.assertEqual(A.run_due(now=timezone.now() + timedelta(hours=5)), 0)
        fake, patch = graph({'message_id': 'm4'})
        with patch:
            self.assertEqual(A.run_due(now=timezone.now() + timedelta(hours=7)), 1)
        self.assertEqual(sent_message(fake, 0), {'text': 'Did it work?'})
        fake, patch = graph()
        with patch:
            self.assertEqual(A.run_due(now=timezone.now() + timedelta(hours=8)), 0)

    def test_follow_check_failure_still_sends_link(self):
        fake, patch = graph((400, {'error': {'message': 'no permission', 'code': 100}}), {'message_id': 'm2'})
        with patch:
            self.deliver(tap('IG1', 'IGSID', f'AUTO:{self.run.pk}', 'pb1'))
        self.run.refresh_from_db()
        self.assertIsNotNone(self.run.link_sent_at)
        self.assertIsNone(self.run.was_follower)

    def test_tap_for_someone_elses_account_is_ignored(self):
        fake, patch = graph()
        with patch:
            self.deliver(tap('P1', 'PSID', f'AUTO:{self.run.pk}', 'pb1', obj='page'))
            self.deliver(tap('IG1', 'IGSID', 'SOMETHING_ELSE', 'pb2'))
        self.assertEqual(fake.calls, [])

    def test_facebook_opener_without_gate_sends_link_at_once(self):
        self.auto.delivery = 'opener'
        self.auto.save()
        self.deliver(fb_comment('C1', 'skill'))
        fake, patch = graph({'message_id': 'm1'}, {'id': 'r1'})
        with patch:
            A.run_due()
        run = AutomationRun.objects.get(automation=self.auto)
        fake, patch = graph({'message_id': 'm2'})
        with patch:
            self.deliver(tap('P1', 'PSID9', f'AUTO:{run.pk}', 'pb1', obj='page'))
        self.assertEqual(fake.paths(), [('POST', '/P1/messages')])
        run.refresh_from_db()
        self.assertEqual((run.contact.platform_user_id, run.contact.messaging_id), ('U1', 'PSID9'))


class LinkTests(AutomationTestCase):
    def setUp(self):
        super().setUp()
        self.deliver(fb_comment('C1', 'skill'))
        fake, patch = graph({'message_id': 'm1'}, {'id': 'r1'})
        with patch:
            A.run_due()
        self.run = AutomationRun.objects.get()
        self.slug = self.auto.link.slug

    def test_click_counts_and_redirects_with_utm(self):
        res = self.client.get(f'/go/{self.slug}/?r={self.run.pk}', HTTP_USER_AGENT='Mozilla/5.0 Instagram')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res['Location'], 'https://ralfizdigital.in/s/seo?utm_source=facebook'
                                          '&utm_medium=social_dm&utm_campaign=skill-reel')
        click = self.auto.link.clicks.get()
        self.assertEqual((click.run, click.platform), (self.run, 'facebook'))
        self.client.get(f'/go/{self.slug}/', HTTP_USER_AGENT='facebookexternalhit/1.1')
        self.assertEqual(self.auto.link.clicks.count(), 1)
        self.assertEqual(A.stats([self.auto])[self.auto.pk]['clicks'], 1)
        self.assertEqual(self.client.get('/go/nope/').status_code, 404)

    def test_existing_utm_kept_and_target_follows_edits(self):
        self.auto.button_url = 'https://x.in/p?utm_source=reel'
        self.auto.save()
        A.link_for(self.auto)
        res = self.client.get(f'/go/{self.slug}/')
        self.assertTrue(res['Location'].startswith('https://x.in/p?utm_source=reel&utm_medium=social_dm'))


class LeadFormTests(AutomationTestCase):
    def setUp(self):
        super().setUp()
        Automation.objects.create(workspace=self.ws, account=self.ig, name='SEO reel', keywords=['seo'],
                                  dm_text='Here you go', lead_keyword='WEBSITE')
        self.deliver(ig_comment('IC1', 'seo', who='IGU'))
        fake, patch = graph({'message_id': 'm1'})
        with patch:
            A.run_due()

    def say(self, text, mid, *answers):
        fake, patch = graph(*answers)
        with patch:
            self.deliver(ig_dm('IGU', text, mid))
        return [sent_message(fake, i)['text'] for i in range(len(fake.calls))]

    def test_three_questions_make_a_crm_lead(self):
        from crm.models import Lead
        ok = {'message_id': 'x'}
        self.assertEqual(self.say('website please', 'd1', ok), [A.LEAD_ASK['name']])
        self.assertEqual(self.say('Anu Joseph', 'd2', ok), [A.LEAD_ASK['business']])
        self.assertEqual(self.say('Anu Bakes', 'd3', ok), [A.LEAD_ASK['phone']])
        self.assertEqual(self.say('soon', 'd4', ok), [A.LEAD_BAD_PHONE])
        self.assertEqual(self.say('+91 98765 43210', 'd5', ok), ['Thanks Anu! Our team will WhatsApp you soon.'])
        lead = Lead.objects.get()
        self.assertEqual((lead.contact_person, lead.company_name, lead.phone, lead.source),
                         ('Anu Joseph', 'Anu Bakes', '+91 98765 43210', 'instagram'))
        self.assertIn('SEO reel', lead.notes)
        self.assertEqual(lead.activities.count(), 1)
        self.assertEqual(self.say('thanks', 'd6'), [])                  # form finished: no more bot
        self.assertEqual(InboxItem.objects.get(external_id='d5').status, 'done')

    def test_strangers_and_client_workspaces(self):
        from core.models import Client
        from crm.models import Lead
        fake, patch = graph()
        with patch:
            self.deliver(ig_dm('SOMEONE', 'website', 'd1'))
        self.assertEqual(fake.calls, [])
        self.ws.client = Client.objects.create(name='Acme Bakery')
        self.ws.save()
        ok = {'message_id': 'x'}
        for i, text in enumerate(['WEBSITE', 'Anu', 'Anu Bakes', '9876543210']):
            self.say(text, f'c{i}', ok)
        self.assertFalse(Lead.objects.exists())
        self.assertEqual(LeadCapture.objects.get().step, 'done')


class Phase2SaveTests(AutomationTestCase):
    def test_validation(self):
        base = {'account': self.fb.pk, 'keywords': 'x', 'dm_text': 'hi'}
        for bad in ({'delivery': 'opener', 'follow_gate': True},                     # Facebook
                    {'followup_text': 'later'},                                       # needs opener
                    {'delivery': 'opener', 'button_label': 'Go', 'button_url': 'https://x.in',
                     'followup_text': 'later', 'followup_hours': 30},
                    {'delivery': 'opener'},                                           # nothing to send
                    {'opener_label': 'x' * 21}):
            with self.assertRaises(SocialError, msg=bad):
                A.save_automation(self.owner, self.ws, {**base, **bad})
        a = A.save_automation(self.owner, self.ws, {
            **base, 'account': self.ig.pk, 'delivery': 'opener', 'follow_gate': True,
            'button_label': 'Get it', 'button_url': 'https://x.in/f', 'followup_text': 'Hi', 'followup_hours': '3'})
        self.assertEqual((a.follow_gate, a.followup_hours, a.link.target_url), (True, 3, 'https://x.in/f'))

    def test_page_shows_new_numbers(self):
        self.client.force_login(self.owner)
        self.auto.lead_keyword = 'WEBSITE'
        self.auto.save()
        res = self.client.get('/social/automations/')
        self.assertContains(res, 'link clicks')
        self.assertContains(res, 'leads</span>')
