import base64
import json
import os
from datetime import timedelta
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ShopLicense, ShopLicenseLog
from .signing import new_key_pair

PRIVATE, PUBLIC = new_key_pair()


def verify(token):
    """What Shop Manager does: check the signature with the public key, then read the payload."""
    body_b64, sig_b64 = token.split('.')
    pad = lambda s: s + '=' * (-len(s) % 4)  # noqa: E731
    body = base64.urlsafe_b64decode(pad(body_b64))
    Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC)).verify(base64.urlsafe_b64decode(pad(sig_b64)), body)
    return json.loads(body)


@mock.patch.dict(os.environ, {'SHOPMANAGER_LICENSE_SIGNING_KEY': PRIVATE})
class ShopLicenceApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.lic = ShopLicense.objects.create(shop_name='4Z Watches', plan='software_website', yearly_fee=7500)

    def call(self, name='activate', key=None, domain='https://shop.4z.in/'):
        return self.client.post(reverse(f'shopmanager_licensing:{name}'),
                                json.dumps({'license_key': key or self.lic.license_key, 'domain': domain,
                                            'app_version': '1.0'}), content_type='application/json')

    def test_key_format_and_one_year_default(self):
        self.assertRegex(self.lic.license_key, r'^RS-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$')
        self.assertIn((self.lic.valid_until - self.lic.valid_from).days, (364, 365))

    def test_activation_binds_domain_and_signs(self):
        r = self.call()
        self.assertEqual(r.status_code, 200)
        p = verify(r.json()['token'])
        self.assertEqual((p['status'], p['domain'], p['on_expiry'], p['product']),
                         ('active', 'shop.4z.in', 'read_only', 'shopmanager'))
        self.lic.refresh_from_db()
        self.assertEqual((self.lic.api_domain, self.lic.app_version, self.lic.total_checks), ('shop.4z.in', '1.0', 1))

    def test_other_server_rejected(self):
        self.call()
        r = self.call('check', domain='shop.someone-else.com')
        self.assertEqual(r.status_code, 403)
        self.assertTrue(ShopLicenseLog.objects.filter(event='domain_mismatch').exists())

    def test_check_before_activation_rejected(self):
        self.assertEqual(self.call('check').status_code, 403)

    def test_unknown_key_and_bad_body(self):
        self.assertEqual(self.call(key='RS-0000-0000-0000').status_code, 404)
        r = self.client.post(reverse('shopmanager_licensing:check'), 'nope', content_type='application/json')
        self.assertEqual(r.status_code, 400)
        r = self.client.post(reverse('shopmanager_licensing:check'), '[1]', content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_states(self):
        today = timezone.localdate()
        self.lic.valid_until = today + timedelta(days=10)
        self.assertEqual(self.lic.state(), 'expiring')
        self.lic.valid_until = today - timedelta(days=3)
        self.assertEqual(self.lic.state(), 'grace')
        self.lic.valid_until = today - timedelta(days=30)
        self.assertEqual(self.lic.state(), 'expired')
        self.lic.status = 'suspended'
        self.assertEqual(self.lic.state(), 'suspended')

    def test_expired_and_suspended_still_get_signed_tokens(self):
        self.call()
        ShopLicense.objects.filter(pk=self.lic.pk).update(valid_until=timezone.localdate() - timedelta(days=30))
        r = self.call('check')
        self.assertFalse(r.json()['valid'])
        self.assertEqual(verify(r.json()['token'])['status'], 'expired')
        ShopLicense.objects.filter(pk=self.lic.pk).update(status='suspended', status_reason='Payment pending')
        p = verify(self.call('check').json()['token'])
        self.assertEqual((p['status'], p['reason']), ('suspended', 'Payment pending'))

    def test_renew_from_lapsed_starts_today(self):
        self.lic.valid_until = timezone.localdate() - timedelta(days=100)
        self.lic.status = 'expired'
        self.lic.renew()
        self.assertEqual(self.lic.status, 'active')
        self.assertGreaterEqual((self.lic.valid_until - timezone.localdate()).days, 363)

    def test_unconfigured_server_answers_503(self):
        with mock.patch.dict(os.environ, {'SHOPMANAGER_LICENSE_SIGNING_KEY': ''}):
            self.assertEqual(self.call().status_code, 503)


class ShopLicenceDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client.force_login(self.user)

    def test_create_renew_suspend(self):
        r = self.client.post(reverse('shop_license_create'), {
            'shop_name': 'Test Shop', 'plan': 'software', 'yearly_fee': '5500',
            'valid_from': '2026-01-15', 'on_expiry': 'lock', 'warn_days': '30', 'grace_period_days': '7'})
        lic = ShopLicense.objects.get()
        self.assertRedirects(r, reverse('shop_license_detail', args=[lic.pk]))
        self.assertEqual((str(lic.valid_until), lic.on_expiry), ('2027-01-14', 'lock'))
        self.assertEqual(self.client.get(reverse('shop_license_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('shop_license_detail', args=[lic.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('shop_license_create')).status_code, 200)

        self.client.post(reverse('shop_license_update', args=[lic.pk]), {'action': 'renew'})
        lic.refresh_from_db()
        self.assertEqual(str(lic.valid_until), '2028-01-14')

        self.client.post(reverse('shop_license_update', args=[lic.pk]),
                         {'action': 'change_status', 'new_status': 'suspended', 'reason': 'Payment pending'})
        lic.refresh_from_db()
        self.assertEqual((lic.status, lic.status_reason), ('suspended', 'Payment pending'))
        self.assertEqual(lic.logs.filter(event__in=['create', 'renew', 'suspend']).count(), 3)

    def test_login_required(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('shop_license_list')).status_code, 302)
