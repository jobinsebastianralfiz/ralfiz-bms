from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Client
from .models import SupportMessage


class SupportChatTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('agc', 'design@agc.example', 'pw-1')
        self.cl = Client.objects.create(name='AGC', email='design@agc.example', user=self.user)
        self.staff = User.objects.create_superuser('boss', 'b@example.com', 'pw')

    def test_client_sends_staff_replies_both_see_history(self):
        self.client.force_login(self.user)
        page = self.client.get(reverse('client_portal:portal_dashboard'))
        self.assertContains(page, 'id="scFab"')
        r = self.client.post(reverse('client_portal:portal_chat_send'), {'body': 'Hello, site is down?'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(SupportMessage.objects.get().from_client, True)

        self.client.force_login(self.staff)
        a = self.client.get(reverse('support_chat:alerts'), {'after': (timezone.now() - timedelta(minutes=1)).isoformat()}).json()
        self.assertEqual(a['unread'], 1)
        self.assertEqual(a['items'][0]['client'], 'AGC')
        inbox = self.client.get(reverse('support_chat:inbox'))
        self.assertContains(inbox, 'Hello, site is down?')
        feed = self.client.get(reverse('support_chat:poll', args=[self.cl.pk]), {'open': '1'}).json()
        self.assertEqual(len(feed['messages']), 1)
        self.assertEqual(self.client.get(reverse('support_chat:alerts')).json()['unread'], 0)
        self.client.post(reverse('support_chat:send', args=[self.cl.pk]), {'body': 'Checking now.'})

        self.client.force_login(self.user)
        feed = self.client.get(reverse('client_portal:portal_chat_poll')).json()
        self.assertEqual([m['body'] for m in feed['messages']], ['Hello, site is down?', 'Checking now.'])
        self.assertEqual(feed['unread'], 1)
        after = feed['messages'][0]['at']
        newer = self.client.get(reverse('client_portal:portal_chat_poll'), {'after': after, 'open': '1'}).json()
        self.assertEqual([m['body'] for m in newer['messages']], ['Checking now.'])
        self.assertEqual(newer['unread'], 0)

    def test_empty_message_rejected_and_clients_cannot_reach_staff_inbox(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('client_portal:portal_chat_send'), {'body': '  '}).status_code, 400)
        self.assertNotEqual(self.client.get(reverse('support_chat:inbox')).status_code, 200)
        other_u = User.objects.create_user('o', 'o@x.com', 'pw')
        other = Client.objects.create(name='Other', email='o@x.com', user=other_u)
        SupportMessage.objects.create(client=other, from_client=False, body='private to Other')
        feed = self.client.get(reverse('client_portal:portal_chat_poll')).json()
        self.assertEqual(feed['messages'], [])

    def test_fresh_browser_does_not_chime_old_messages(self):
        SupportMessage.objects.create(client=self.cl, body='old one')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('support_chat:alerts')).json()['items'], [])
