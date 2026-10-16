from django.test import TestCase

# Create your tests here.


class ClientConfinementTests(TestCase):
    """A client login must stay inside the portal."""

    def setUp(self):
        from django.contrib.auth.models import User
        from core.models import Client as BizClient
        self.user = User.objects.create_user('acme_login', password='pw-12345')
        BizClient.objects.create(name='Acme', email='acme@example.com', user=self.user)

    def test_business_pages_redirect_to_portal(self):
        self.client.force_login(self.user)
        for url in ['/', '/invoices/', '/clients/', '/projects/', '/tasks/board/']:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertEqual(r['Location'], '/portal/', url)

    def test_portal_and_other_api_paths(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/portal/').status_code, 200)
        self.assertEqual(self.client.get('/api/employees/').status_code, 403)

    def test_staff_with_client_profile_not_confined(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        self.assertNotEqual(self.client.get('/invoices/').get('Location'), '/portal/')


class StaffVisitingPortalTests(TestCase):
    def test_staff_session_is_kept_and_redirected_to_bms(self):
        from django.contrib.auth.models import User
        admin = User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        self.client.force_login(admin)
        r = self.client.get('/portal/')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], '/')
        self.assertEqual(int(self.client.session['_auth_user_id']), admin.pk)

    def test_staff_credentials_on_portal_login_get_a_clear_message(self):
        from django.contrib.auth.models import User
        User.objects.create_superuser('boss', 'boss@example.com', 'pw-12345')
        r = self.client.post('/portal/login/', {'username': 'boss', 'password': 'pw-12345'})
        self.assertContains(r, 'That is a staff account')


class PortalLoginTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from core.models import Client as BizClient
        self.user = User.objects.create_user('acme_login', password='pw-12345')
        BizClient.objects.create(name='Acme', email='Owner@Acme.example', user=self.user)

    def test_sign_in_with_email(self):
        r = self.client.post('/portal/login/', {'username': 'owner@acme.example', 'password': 'pw-12345', 'remember': '1'})
        self.assertRedirects(r, '/portal/', fetch_redirect_response=False)
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_without_remember_me_session_ends_with_browser(self):
        self.client.post('/portal/login/', {'username': 'acme_login', 'password': 'pw-12345'})
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_wrong_password_keeps_username(self):
        r = self.client.post('/portal/login/', {'username': 'acme_login', 'password': 'nope'})
        self.assertContains(r, 'Invalid username or password.')
        self.assertContains(r, 'value="acme_login"')
