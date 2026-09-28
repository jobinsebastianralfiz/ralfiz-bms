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

from .models import RalfPOSLicense, RalfPOSLicenseLog
from .signing import new_key_pair

PRIVATE, PUBLIC = new_key_pair()


def verify(token):
    """What RalfPOS does: check the signature with the public key, then read the payload."""
    body_b64, sig_b64 = token.split('.')
    pad = lambda s: s + '=' * (-len(s) % 4)  # noqa: E731
    body = base64.urlsafe_b64decode(pad(body_b64))
    Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC)).verify(base64.urlsafe_b64decode(pad(sig_b64)), body)
    return json.loads(body)


@mock.patch.dict(os.environ, {'RALFPOS_LICENSE_SIGNING_KEY': PRIVATE})
class LicenceApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.lic = RalfPOSLicense.objects.create(shop_name='Karak Corner', country='UAE',
                                                 enabled_modules=['delivery'], max_counters=2)

    def call(self, name='activate', key=None, domain='https://pos.karak.ae/'):
        return self.client.post(reverse(f'ralfpos_licensing:{name}'),
                                json.dumps({'license_key': key or self.lic.license_key, 'domain': domain,
                                            'app_version': '2.0'}), content_type='application/json')

    def test_key_format_and_defaults(self):
        self.assertRegex(self.lic.license_key, r'^POS-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$')
        self.assertAlmostEqual((self.lic.valid_until - self.lic.valid_from).days, 365, delta=1)

    def test_activation_binds_domain_and_signs_modules(self):
        r = self.call()
        self.assertEqual(r.status_code, 200)
        payload = verify(r.json()['token'])
        self.assertEqual((payload['status'], payload['domain'], payload['modules'], payload['max_counters']),
                         ('active', 'pos.karak.ae', ['delivery'], 2))
        self.lic.refresh_from_db()
        self.assertEqual((self.lic.api_domain, self.lic.app_version, self.lic.total_checks), ('pos.karak.ae', '2.0', 1))

    def test_another_server_cannot_use_the_key(self):
        self.call()
        r = self.call('check', domain='pos.someone-else.com')
        self.assertEqual(r.status_code, 403)
        self.assertNotIn('token', r.json())
        self.assertTrue(RalfPOSLicenseLog.objects.filter(event='domain_mismatch').exists())

    def test_check_before_activation_is_refused(self):
        self.assertEqual(self.call('check').status_code, 403)

    def test_empty_module_list_means_no_add_ons(self):
        self.lic.enabled_modules = []
        self.lic.save()
        self.assertEqual(verify(self.call().json()['token'])['modules'], [])

    def test_expired_and_revoked_are_signed(self):
        self.call()
        self.lic.refresh_from_db()
        self.lic.valid_until = timezone.now() - timedelta(days=10)
        self.lic.save()
        r = self.call('check')
        self.assertFalse(r.json()['valid'])
        self.assertEqual(verify(r.json()['token'])['status'], 'expired')
        self.lic.refresh_from_db()
        self.assertEqual(self.lic.status, 'expired')
        self.lic.status = 'revoked'
        self.lic.save()
        self.assertEqual(verify(self.call('check').json()['token'])['status'], 'revoked')

    def test_grace_period_still_active(self):
        self.lic.valid_until = timezone.now() - timedelta(days=2)
        self.lic.save()
        self.assertEqual(verify(self.call().json()['token'])['status'], 'active')

    def test_tampered_token_fails(self):
        token = self.call().json()['token']
        body, sig = token.split('.')
        fake = base64.urlsafe_b64encode(json.dumps({'modules': ['delivery', 'tables']}).encode()).rstrip(b'=').decode()
        with self.assertRaises(Exception):
            verify(f'{fake}.{sig}')

    def test_unknown_key(self):
        self.assertEqual(self.call(key='POS-0000-0000-0000').status_code, 404)

    def test_rate_limit(self):
        with mock.patch('ralfpos_licensing.views.RATE_LIMIT', (3, 600)):
            codes = [self.call('check', domain='x').status_code for _ in range(4)]
        self.assertEqual(codes[-1], 429)


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('staff', password='pw-12345')
        self.client.force_login(self.user)

    def test_login_required(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('ralfpos_license_list')).status_code, 302)

    def test_create_with_add_ons_then_untick_all(self):
        r = self.client.post(reverse('ralfpos_license_create'), {
            'shop_name': 'Karak Corner', 'country': 'UAE', 'license_type': 'yearly', 'billing_cycle': 'yearly',
            'grace_period_days': '7', 'max_counters': '2', 'modules': ['delivery', 'kitchen', 'bogus'],
        })
        lic = RalfPOSLicense.objects.get()
        self.assertRedirects(r, reverse('ralfpos_license_detail', args=[lic.pk]))
        self.assertEqual(lic.enabled_modules, ['delivery', 'kitchen'])
        self.client.post(reverse('ralfpos_license_update', args=[lic.pk]), {'action': 'update_modules'})
        lic.refresh_from_db()
        self.assertEqual(lic.get_enabled_modules(), [])
        for page in ('ralfpos_license_list', ):
            self.assertContains(self.client.get(reverse(page)), 'Karak Corner')
        self.assertContains(self.client.get(reverse('ralfpos_license_detail', args=[lic.pk])), 'Basic app only')

    def test_extend_status_and_domain_reset(self):
        lic = RalfPOSLicense.objects.create(shop_name='S', api_domain='old.example.com')
        before = lic.valid_until
        url = reverse('ralfpos_license_update', args=[lic.pk])
        self.client.post(url, {'action': 'extend', 'extend_days': '30'})
        self.client.post(url, {'action': 'change_status', 'new_status': 'suspended'})
        self.client.post(url, {'action': 'reset_domain'})
        lic.refresh_from_db()
        self.assertEqual((lic.valid_until - before).days, 30)
        self.assertEqual((lic.status, lic.api_domain), ('suspended', ''))


class MisconfiguredServerTests(TestCase):
    @mock.patch.dict(os.environ, {'RALFPOS_LICENSE_SIGNING_KEY': ''})
    def test_missing_key_is_a_clear_503(self):
        lic = RalfPOSLicense.objects.create(shop_name='S')
        r = self.client.post(reverse('ralfpos_licensing:activate'), json.dumps({'license_key': lic.license_key, 'domain': 'a.b'}),
                             content_type='application/json')
        self.assertEqual(r.status_code, 503)
        self.assertIn('not configured', r.json()['error'])

    @mock.patch.dict(os.environ, {'RALFPOS_LICENSE_SIGNING_KEY': PRIVATE.rstrip('=')})
    def test_key_without_padding_works(self):
        lic = RalfPOSLicense.objects.create(shop_name='S')
        r = self.client.post(reverse('ralfpos_licensing:activate'), json.dumps({'license_key': lic.license_key, 'domain': 'a.b'}),
                             content_type='application/json')
        self.assertEqual(verify(r.json()['token'])['shop'], 'S')
