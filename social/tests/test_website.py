"""Website page: GA4 + Search Console through a service account, with Google simulated."""
import json
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from social.models import Membership, Workspace

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
SA = json.dumps({'client_email': 'reader@proj.iam.gserviceaccount.com', 'private_key': KEY})


def ga_reports():
    def r(rows):
        return {'rows': [{'dimensionValues': [{'value': d} for d in dims],
                          'metricValues': [{'value': str(v)} for v in vals]} for dims, vals in rows]}
    return {'reports': [
        r([(['date_range_0'], [120, 150, 400, 95]), (['date_range_1'], [100, 130, 300, 80])]),
        r([(['20261012'], [10]), (['20261013'], [14])]),
        r([(['/'], [200]), (['/services/'], [80])]),
        r([(['Organic Search'], [90]), (['Direct'], [60])]),
        r([(['generate_lead', 'date_range_0'], [4]), (['generate_lead', 'date_range_1'], [2])]),
    ]}


def fake_post(url, **kw):
    resp = mock.Mock(status_code=200)
    if 'oauth2' in url:
        resp.json.return_value = {'access_token': 'tok'}
    elif 'analyticsdata' in url:
        resp.json.return_value = ga_reports()
    elif kw['json'].get('dimensions') == ['query']:
        resp.json.return_value = {'rows': [{'keys': ['ralfiz technologies'], 'clicks': 12, 'impressions': 90,
                                            'position': 1.4}]}
    else:
        resp.json.return_value = {'rows': [{'clicks': 30, 'impressions': 900, 'ctr': 0.033, 'position': 8.2}]}
    return resp


@override_settings(GOOGLE_SERVICE_ACCOUNT_JSON=SA, WEBSITE_GA4_PROPERTY_ID='512345678',
                   WEBSITE_SEARCH_CONSOLE_SITE='sc-domain:ralfiz.com',
                   SOCIAL_TOKEN_KEY='ad-qsvn0nNwwkeZWx4ms_kfGauKcOxV6390X4U2rYAE=')
class WebsitePageTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_superuser('boss', 'b@x.com', 'pw')

    def test_report_numbers(self):
        from social import website as W
        with mock.patch('social.website.requests.post', side_effect=fake_post) as post:
            data = W.report(30)
        self.assertEqual(data['errors'], [])
        users, visits, views, leads = data['ga']['kpis']
        self.assertEqual((users['value'], users['change']), (120, 20.0))
        self.assertEqual((leads['value'], leads['change']), (4, 100.0))
        self.assertEqual(data['ga']['channels'][0], {'name': 'Organic Search', 'sessions': 90, 'pct': 60})
        self.assertEqual(data['gsc']['kpis'][0]['value'], 30)
        self.assertEqual(data['gsc']['queries'][0]['query'], 'ralfiz technologies')
        self.assertIn('sc-domain%3Aralfiz.com', [c.args[0] for c in post.call_args_list][-1])
        token_call = post.call_args_list[0]
        self.assertEqual(token_call.kwargs['data']['grant_type'], 'urn:ietf:params:oauth:grant-type:jwt-bearer')

    def test_no_access_gives_the_email_to_add(self):
        from social import website as W

        def denied(url, **kw):
            if 'oauth2' in url:
                return fake_post(url, **kw)
            return mock.Mock(status_code=403)
        with mock.patch('social.website.requests.post', side_effect=denied):
            data = W.report(7)
        self.assertTrue(any('reader@proj.iam.gserviceaccount.com' in e for e in data['errors']))

    def test_page_for_owner_and_hidden_from_client_logins(self):
        self.client.force_login(self.owner)
        with mock.patch('social.website.requests.post', side_effect=fake_post):
            page = self.client.get(reverse('social:website')).content.decode()
        self.assertIn('Contact-form leads', page)
        self.assertIn('What people search to find you', page)
        reviewer = User.objects.create_user('rev', 'r@x.com', 'pw')
        Membership.objects.create(user=reviewer, workspace=Workspace.objects.create(name='C'), role='manager')
        self.client.force_login(reviewer)
        self.assertEqual(self.client.get(reverse('social:website')).status_code, 403)

    @override_settings(GOOGLE_SERVICE_ACCOUNT_JSON='')
    def test_setup_steps_without_a_key(self):
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse('social:website')), 'service account')
