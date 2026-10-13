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
        r([(['20261012'], [10, 30]), (['20261013'], [14, 41])]),
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
    elif kw['json'].get('dimensions') == ['date']:
        resp.json.return_value = {'rows': [{'keys': ['2026-10-05'], 'clicks': 3, 'impressions': 70}]}
    elif kw['json'].get('dimensions') == ['page']:
        resp.json.return_value = {'rows': [{'keys': ['https://ralfiz.com/'], 'clicks': 20, 'impressions': 500}]}
    elif kw['json'].get('dimensions') == ['query'] and kw['json'].get('rowLimit') == 200:
        resp.json.return_value = {'rows': [
            {'keys': ['ralfiz technologies'], 'clicks': 12, 'impressions': 90, 'ctr': 0.13, 'position': 1.4},
            {'keys': ['software company kerala'], 'clicks': 1, 'impressions': 140, 'ctr': 0.007, 'position': 7.8},
            {'keys': ['ralfiz'], 'clicks': 0, 'impressions': 40, 'ctr': 0.0, 'position': 2.0}]}
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


@override_settings(GOOGLE_SERVICE_ACCOUNT_JSON=SA, WEBSITE_GA4_PROPERTY_ID='512345678',
                   WEBSITE_SEARCH_CONSOLE_SITE='sc-domain:ralfiz.com', ANTHROPIC_API_KEY='k',
                   SOCIAL_TOKEN_KEY='ad-qsvn0nNwwkeZWx4ms_kfGauKcOxV6390X4U2rYAE=')
class WebsiteChartsAndTipsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client.force_login(User.objects.create_superuser('boss2', 'b2@x.com', 'pw'))

    def test_opportunities_low_ctr_and_tips(self):
        from social import website as W
        with mock.patch('social.website.requests.post', side_effect=fake_post):
            data = W.report(30)
        self.assertEqual([o['query'] for o in data['gsc']['opportunities']], ['software company kerala'])
        self.assertEqual([o['query'] for o in data['gsc']['low_ctr']], ['ralfiz'])
        titles = [t[1] for t in W.tips(data)]
        self.assertIn('You are #7.8 for "software company kerala"', titles)
        self.assertIn('Rewrite the Google title for "ralfiz"', titles)
        self.assertIn('No visits from social media yet', titles)
        self.assertIn('"software company kerala" #7.8 shown 140', W.summary_text(data, 30))

    def test_page_has_chart_donut_and_ai_ideas(self):
        claude = mock.MagicMock()
        claude.beta.messages.create.return_value = mock.Mock(stop_reason='end_turn', content=[mock.Mock(
            type='text', text='1. **Write a Kerala pricing page**: Target "software company kerala".\n2. **Fix <b>titles</b>**: x')])
        with mock.patch('social.website.requests.post', side_effect=fake_post):
            page = self.client.get(reverse('social:website')).content.decode()
            self.assertIn('id="wSvg"', page)
            self.assertIn('conic-gradient(', page)
            self.assertIn('Almost on top', page)
            with mock.patch('social.ai._client', return_value=claude):
                self.client.post(reverse('social:website') + '?days=30', {'action': 'ideas'})
            page = self.client.get(reverse('social:website')).content.decode()
        self.assertIn('<b>Write a Kerala pricing page</b>', page)
        self.assertIn('&lt;b&gt;titles&lt;/b&gt;', page)   # AI text is escaped


class OldCacheTests(TestCase):
    def test_a_report_cached_by_older_code_is_not_reused(self):
        from social import website as W
        cache.set('social:website:30', {'ga': {'kpis': []}, 'gsc': None, 'errors': []})   # old key and shape
        with override_settings(GOOGLE_SERVICE_ACCOUNT_JSON=SA, WEBSITE_GA4_PROPERTY_ID='1',
                               WEBSITE_SEARCH_CONSOLE_SITE='sc-domain:x.com'), \
                mock.patch('social.website.requests.post', side_effect=fake_post):
            self.assertIn('labels', W.report(30)['ga'])


@override_settings(GOOGLE_SERVICE_ACCOUNT_JSON=SA, WEBSITE_GA4_PROPERTY_ID='1', WEBSITE_SEARCH_CONSOLE_SITE='sc-domain:x.com',
                   GOOGLE_MAPS_API_KEY='maps-key', WEBSITE_PLACE_ID='', WEBSITE_PLACE_QUERY='Ralfiz Technologies Perinthalmanna',
                   SOCIAL_TOKEN_KEY='ad-qsvn0nNwwkeZWx4ms_kfGauKcOxV6390X4U2rYAE=')
class GoogleReviewsTests(TestCase):
    def setUp(self):
        cache.clear()

    def places(self, method, url, **kw):
        resp = mock.Mock(status_code=200)
        self.calls.append((method, url, kw['headers']['X-Goog-FieldMask']))
        if url.endswith('places:searchText'):
            resp.json.return_value = {'places': [{'id': 'PLACE1'}]}
        else:
            resp.json.return_value = {
                'displayName': {'text': 'Ralfiz Technologies'}, 'rating': 4.9, 'userRatingCount': 37,
                'googleMapsUri': 'https://maps.google.com/?cid=1',
                'reviews': [
                    {'rating': 5, 'publishTime': '2026-09-01T00:00:00Z', 'relativePublishTimeDescription': 'a month ago',
                     'text': {'text': 'Great team'}, 'authorAttribution': {'displayName': 'Asha'}},
                    {'rating': 4, 'publishTime': '2026-10-01T00:00:00Z', 'relativePublishTimeDescription': '2 weeks ago',
                     'originalText': {'text': 'നല്ല സേവനം <script>x</script>'}, 'authorAttribution': {'displayName': 'Rahul'}},
                ]}
        return resp

    def test_finds_place_once_and_shows_newest_first(self):
        from social import website as W
        self.calls = []
        with mock.patch('social.website.requests.request', side_effect=self.places):
            data = W.google_reviews()
            W.google_reviews()                       # cached: no new calls
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.calls[1][1], 'https://places.googleapis.com/v1/places/PLACE1')
        self.assertIn('reviews', self.calls[1][2])
        self.assertEqual((data['rating'], data['count']), (4.9, 37))
        self.assertEqual([r['author'] for r in data['reviews']], ['Rahul', 'Asha'])
        self.assertEqual(data['reviews'][0]['text'], 'നല്ല സേവനം <script>x</script>')

    def test_card_on_the_page_is_escaped(self):
        self.calls = []
        self.client.force_login(User.objects.create_superuser('boss3', 'b3@x.com', 'pw'))
        with mock.patch('social.website.requests.request', side_effect=self.places), \
                mock.patch('social.website.requests.post', side_effect=fake_post):
            page = self.client.get(reverse('social:website')).content.decode()
        self.assertIn('Google reviews', page)
        self.assertIn('4.9', page)
        self.assertIn('&lt;script&gt;x&lt;/script&gt;', page)
        self.assertNotIn('<script>x</script>', page)
