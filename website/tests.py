from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from crm.models import Lead, LeadActivity


FEED = {'projects': [
    {'title': 'Novrik Technologies – Corporate Website', 'summary': 'A premium corporate website.',
     'image': 'https://ralfiz.com/images/projects/n.png', 'url': 'https://novriktech.com/',
     'detail': 'https://ralfiz.com/projects/novrik/', 'categories': ['Canada'], 'featured': True},
    {'title': 'Van Sales ERP', 'summary': 'x ' * 200, 'image': '', 'url': '',
     'detail': 'https://ralfiz.com/projects/van-sales/', 'categories': ['ERP System'], 'featured': False},
]}


def feed_response(data=FEED, status=200):
    r = mock.Mock(status_code=status, json=mock.Mock(return_value=data))
    r.raise_for_status = mock.Mock() if status == 200 else mock.Mock(side_effect=Exception('down'))
    return r


@mock.patch('requests.get', return_value=feed_response())
class LandingTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_visitors_get_the_landing_page(self, _get):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'website/landing.html')
        self.assertContains(r, 'Book a free demo')
        self.assertContains(r, 'Ralfiz Social')
        self.assertContains(r, 'href="/staff/login/"')
        self.assertNotContains(r, 'href="/login/"')  # the admin sign-in is not advertised

    def test_staff_still_get_the_dashboard(self, _get):
        self.client.force_login(User.objects.create_superuser('boss', 'b@x.com', 'pw'))
        r = self.client.get('/')
        self.assertTemplateNotUsed(r, 'website/landing.html')

    def test_demo_request_creates_a_website_lead(self, _get):
        r = self.client.post(reverse('book_demo'), {
            'name': 'Suresh', 'phone': '+91 98470 12345', 'business': 'Demo Café', 'email': 's@cafe.in',
            'interest': 'ralfiz_social', 'message': 'We post daily on Instagram.'})
        self.assertRedirects(r, '/?sent=1#demo', fetch_redirect_response=False)
        lead = Lead.objects.get()
        self.assertEqual((lead.source, lead.status, lead.company_name), ('website', 'new', 'Demo Café'))
        self.assertIn('Ralfiz Social', lead.notes)
        self.assertIn('We post daily', lead.notes)
        self.assertTrue(LeadActivity.objects.filter(lead=lead, activity_type='created').exists())
        self.assertContains(self.client.get('/?sent=1'), 'We have your request')

    def test_needs_name_and_a_real_phone(self, _get):
        self.client.post(reverse('book_demo'), {'name': '', 'phone': 'abc'})
        self.assertFalse(Lead.objects.exists())

    def test_honeypot_and_rate_limit(self, _get):
        self.client.post(reverse('book_demo'), {'name': 'Bot', 'phone': '9999999999', 'website_url': 'http://spam'})
        self.assertFalse(Lead.objects.exists())
        for i in range(7):
            self.client.post(reverse('book_demo'), {'name': f'P{i}', 'phone': '9895000000'})
        self.assertEqual(Lead.objects.count(), 5)

    def test_unknown_interest_becomes_other(self, _get):
        self.client.post(reverse('book_demo'), {'name': 'A', 'phone': '9895000001', 'interest': '<script>'})
        self.assertIn('Something else', Lead.objects.get().notes)

    def test_portfolio_comes_from_the_ralfiz_com_feed(self, get):
        r = self.client.get('/')
        self.assertContains(r, 'Novrik Technologies')
        self.assertContains(r, 'Corporate Website')            # the part after the dash becomes the tag
        self.assertContains(r, 'https://ralfiz.com/images/projects/n.png')
        self.assertContains(r, 'href="https://ralfiz.com/projects/van-sales/"')  # no live URL: link the detail page
        self.client.get('/')
        self.assertEqual(get.call_count, 1)                    # cached between requests

    def test_portfolio_falls_back_when_the_feed_is_down(self, get):
        get.return_value = feed_response(status=500)
        r = self.client.get('/')
        self.assertContains(r, 'iRAD 2027')                    # built-in list

    def test_spoofed_forwarded_for_does_not_reset_the_limit(self, _get):
        for i in range(7):
            self.client.post(reverse('book_demo'), {'name': f'P{i}', 'phone': '9895000000'},
                             HTTP_X_FORWARDED_FOR=f'1.2.3.{i}, 203.0.113.9')
        self.assertEqual(Lead.objects.count(), 5)

    def test_feed_links_must_be_http(self, get):
        get.return_value = feed_response({'projects': [
            {'title': 'Evil', 'summary': 's', 'image': 'javascript:alert(1)', 'url': 'javascript:alert(1)',
             'detail': 'https://ralfiz.com/projects/evil/', 'categories': [], 'featured': False}]})
        r = self.client.get('/')
        self.assertNotContains(r, 'javascript:alert')
        self.assertContains(r, 'href="https://ralfiz.com/projects/evil/"')
