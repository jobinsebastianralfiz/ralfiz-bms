"""The Claude API key saved in Settings > AI: owner only, checked, encrypted, never shown."""
from unittest import mock

import anthropic
from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse

from core.ai_keys import anthropic_api_key
from core.models import CompanySettings

KEY = 'sk-ant-api03-' + 'x' * 40 + 'WXYZ'


@override_settings(ANTHROPIC_API_KEY='sk-ant-env-key-from-railway-000000000')
class AIKeyTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client.force_login(self.owner)

    def save(self, key=KEY, ok=True):
        with mock.patch('anthropic.Anthropic') as cls:
            if not ok:
                cls.return_value.models.list.side_effect = anthropic.AuthenticationError(
                    'bad', response=mock.Mock(status_code=401), body=None)
            return self.client.post(reverse('settings_ai_key'), {'api_key': key}), cls

    def test_falls_back_to_environment(self):
        self.assertEqual(anthropic_api_key(), 'sk-ant-env-key-from-railway-000000000')

    def test_owner_saves_key_encrypted_and_it_is_used(self):
        _, cls = self.save()
        cls.assert_called_once()
        self.assertEqual(cls.call_args.kwargs['api_key'], KEY)
        self.assertEqual(anthropic_api_key(), KEY)
        with connection.cursor() as c:
            c.execute('SELECT anthropic_api_key FROM core_companysettings WHERE id = 1')
            raw = c.fetchone()[0]
        self.assertTrue(raw.startswith('enc1:'))
        self.assertNotIn('WXYZ', raw)
        page = self.client.get(reverse('settings'))
        self.assertContains(page, 'Saved here')
        self.assertNotContains(page, KEY)
        self.assertContains(page, 'sk-ant-…WXYZ')

    def test_rejected_key_not_saved(self):
        r, _ = self.save(ok=False)
        self.assertEqual(CompanySettings.get_settings().anthropic_api_key, '')
        self.assertIn('rejected', [str(m) for m in r.wsgi_request._messages][0])

    def test_not_a_key(self):
        self.save(key='hello')
        self.assertEqual(CompanySettings.get_settings().anthropic_api_key, '')

    def test_remove_falls_back(self):
        self.save()
        self.client.post(reverse('settings_ai_key'), {'remove': '1'})
        self.assertEqual(anthropic_api_key(), 'sk-ant-env-key-from-railway-000000000')

    def test_staff_who_are_not_owner_cannot_change_or_see_it(self):
        staff = User.objects.create_user('hr', password='pw-12345', is_staff=True)
        self.client.force_login(staff)
        self.save()
        self.assertEqual(CompanySettings.get_settings().anthropic_api_key, '')
        self.assertNotContains(self.client.get(reverse('settings')), 'id="ai-panel"')

    def test_main_settings_save_keeps_the_key(self):
        self.save()
        self.client.post(reverse('settings'), {'company_name': 'Ralfiz Technologies', 'invoice_prefix': 'INVRT',
                                               'non_gst_invoice_prefix': 'NG'})
        self.assertEqual(anthropic_api_key(), KEY)
