"""Login lockout (all login routes) and safe ?next= redirects."""
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from core.security import MAX_PER_IP, MAX_PER_USER


class LockoutTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_superuser('owner', 'o@x.com', 'right-pass-123')

    def fail(self, url='/login/', user='owner', **extra):
        return self.client.post(url, {'username': user, 'password': 'wrong'}, **extra)

    def test_bms_login_locks_after_repeated_failures(self):
        for _ in range(MAX_PER_USER):
            self.fail()
        r = self.client.post('/login/', {'username': 'owner', 'password': 'right-pass-123'}, follow=True)
        self.assertContains(r, 'Too many failed attempts')
        self.assertNotIn('_auth_user_id', self.client.session)  # even the right password is refused

    def test_lock_is_shared_by_admin_staff_portal_and_mobile_login(self):
        for _ in range(MAX_PER_USER):
            self.fail('/admin/login/')
        r = self.client.post('/admin/login/', {'username': 'owner', 'password': 'right-pass-123'})
        self.assertNotIn('_auth_user_id', self.client.session)
        r = self.client.post('/staff/login/', {'username': 'owner', 'password': 'right-pass-123'})
        self.assertNotIn('_auth_user_id', self.client.session)
        r = self.client.post('/api/employees/auth/login/', {'username': 'owner', 'password': 'right-pass-123'},
                             content_type='application/json')
        self.assertNotEqual(r.status_code, 200)

    def test_success_before_the_limit_clears_the_count(self):
        for _ in range(MAX_PER_USER - 1):
            self.fail()
        self.client.post('/login/', {'username': 'owner', 'password': 'right-pass-123'})
        self.assertIn('_auth_user_id', self.client.session)
        self.client.logout()
        for _ in range(MAX_PER_USER - 1):
            self.fail()
        self.client.post('/login/', {'username': 'owner', 'password': 'right-pass-123'})
        self.assertIn('_auth_user_id', self.client.session)

    def test_password_spraying_from_one_address_is_stopped(self):
        for i in range(MAX_PER_IP):
            self.fail(user=f'guess{i}', HTTP_X_FORWARDED_FOR='198.51.100.7')
        self.client.post('/login/', {'username': 'owner', 'password': 'right-pass-123'},
                         HTTP_X_FORWARDED_FOR='198.51.100.7')
        self.assertNotIn('_auth_user_id', self.client.session)
        # A spoofed first X-Forwarded-For entry does not dodge it.
        self.client.post('/login/', {'username': 'owner', 'password': 'right-pass-123'},
                         HTTP_X_FORWARDED_FOR='1.1.1.1, 198.51.100.7')
        self.assertNotIn('_auth_user_id', self.client.session)


class SafeNextTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_superuser('owner', 'o@x.com', 'right-pass-123')

    def login(self, next_url):
        return self.client.post(f'/login/?next={next_url}', {'username': 'owner', 'password': 'right-pass-123'})

    def test_offsite_next_is_ignored(self):
        for bad in ('https://evil.example/', '//evil.example/x', 'https:evil.example', '/\\evil.example'):
            r = self.login(bad)
            self.assertFalse(r['Location'].startswith(('http', '//', '/\\')), (bad, r['Location']))
            self.client.logout()

    def test_local_next_still_works(self):
        r = self.login('/social/')
        self.assertEqual(r['Location'], '/social/')
