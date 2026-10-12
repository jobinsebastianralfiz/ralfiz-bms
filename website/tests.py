from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from crm.models import Lead, LeadActivity


class LandingTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_visitors_get_the_landing_page(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'website/landing.html')
        self.assertContains(r, 'Book a free demo')
        self.assertContains(r, 'Ralfiz Social')
        self.assertContains(r, 'href="/staff/login/"')
        self.assertNotContains(r, 'href="/login/"')  # the admin sign-in is not advertised

    def test_staff_still_get_the_dashboard(self):
        self.client.force_login(User.objects.create_superuser('boss', 'b@x.com', 'pw'))
        r = self.client.get('/')
        self.assertTemplateNotUsed(r, 'website/landing.html')

    def test_demo_request_creates_a_website_lead(self):
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

    def test_needs_name_and_a_real_phone(self):
        self.client.post(reverse('book_demo'), {'name': '', 'phone': 'abc'})
        self.assertFalse(Lead.objects.exists())

    def test_honeypot_and_rate_limit(self):
        self.client.post(reverse('book_demo'), {'name': 'Bot', 'phone': '9999999999', 'website_url': 'http://spam'})
        self.assertFalse(Lead.objects.exists())
        for i in range(7):
            self.client.post(reverse('book_demo'), {'name': f'P{i}', 'phone': '9895000000'})
        self.assertEqual(Lead.objects.count(), 5)

    def test_unknown_interest_becomes_other(self):
        self.client.post(reverse('book_demo'), {'name': 'A', 'phone': '9895000001', 'interest': '<script>'})
        self.assertIn('Something else', Lead.objects.get().notes)
