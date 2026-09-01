"""Tests for the staff portal (/staff/) used by interns and employees."""
import pathlib
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Attendance, Employee, InternAssessment, LeaveRequest, LeaveType,
    Notification, OfficeConfig, Payroll, ScheduledClass, WorkAssignment,
)


class StaffPortalTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'intern-pass-123'

        cls.intern_user = User.objects.create_user(
            username='portal_intern', password=cls.password,
            first_name='Asha', last_name='Nair', email='asha@example.com')
        cls.intern = Employee.objects.create(
            user=cls.intern_user, employee_id='EMPT01',
            employment_type='intern', role='intern', department='marketing',
            intern_type='digital', status='active')

        cls.employee_user = User.objects.create_user(
            username='portal_employee', password=cls.password, first_name='Ravi')
        cls.employee = Employee.objects.create(
            user=cls.employee_user, employee_id='EMPT02',
            employment_type='fulltime', role='employee', status='active')

        cls.outsider = User.objects.create_user(username='portal_outsider', password=cls.password)

        cls.inactive_user = User.objects.create_user(username='portal_inactive', password=cls.password)
        cls.inactive = Employee.objects.create(
            user=cls.inactive_user, employee_id='EMPT03',
            employment_type='intern', role='intern', status='terminated')

    def login_intern(self):
        self.assertTrue(self.client.login(username='portal_intern', password=self.password))


class StaffPortalAccessTests(StaffPortalTestBase):
    def test_login_page_renders_anonymously(self):
        res = self.client.get(reverse('staff:login'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Staff sign in')

    def test_intern_can_sign_in(self):
        res = self.client.post(reverse('staff:login'), {
            'username': 'portal_intern', 'password': self.password})
        self.assertRedirects(res, reverse('staff:dashboard'))

    def test_bad_password_is_rejected(self):
        res = self.client.post(reverse('staff:login'), {
            'username': 'portal_intern', 'password': 'wrong'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Invalid username or password')

    def test_user_without_employee_profile_is_refused(self):
        res = self.client.post(reverse('staff:login'), {
            'username': 'portal_outsider', 'password': self.password})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'no active staff profile')

    def test_terminated_employee_is_refused(self):
        res = self.client.post(reverse('staff:login'), {
            'username': 'portal_inactive', 'password': self.password})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'no active staff profile')

    def test_anonymous_is_redirected_to_staff_login(self):
        res = self.client.get(reverse('staff:dashboard'))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('staff:login'), res.url)

    def test_logout_returns_to_login(self):
        self.login_intern()
        res = self.client.get(reverse('staff:logout'))
        self.assertRedirects(res, reverse('staff:login'))


class StaffPortalPageTests(StaffPortalTestBase):
    """Every page must render for a freshly-created intern with no data yet."""

    def setUp(self):
        self.login_intern()

    def test_all_pages_render_with_no_data(self):
        for name in ['dashboard', 'attendance', 'attendance_history', 'leave',
                     'work_list', 'class_list', 'assessment_list', 'payslip_list',
                     'notification_list', 'profile', 'lead_list']:
            with self.subTest(page=name):
                res = self.client.get(reverse('staff:' + name))
                self.assertEqual(res.status_code, 200, f'{name} did not render')

    def test_dashboard_shows_not_checked_in(self):
        res = self.client.get(reverse('staff:dashboard'))
        self.assertContains(res, 'Not checked in')

    def test_attendance_warns_when_face_not_registered(self):
        res = self.client.get(reverse('staff:attendance'))
        self.assertContains(res, 'Register your face first')
        # The check-in button must be disabled until a face exists.
        self.assertContains(res, 'id="sfCheckIn" disabled')

    def test_attendance_warns_when_no_office_qr_configured(self):
        res = self.client.get(reverse('staff:attendance'))
        self.assertContains(res, 'No office QR is configured')

    def test_attendance_shows_checked_in_state(self):
        Attendance.objects.create(
            employee=self.intern, date=timezone.localdate(),
            check_in=timezone.now(), status='present', verification_method='face_qr',
            face_verified=True, qr_verified=True)
        res = self.client.get(reverse('staff:attendance'))
        self.assertContains(res, "You're checked in")
        self.assertContains(res, 'id="sfCheckOut"')

    def test_history_filters_by_month(self):
        Attendance.objects.create(
            employee=self.intern, date=date(2026, 3, 14),
            check_in=timezone.now(), status='present', worked_hours=Decimal('7.50'))
        res = self.client.get(reverse('staff:attendance_history'), {'year': 2026, 'month': 3})
        self.assertContains(res, 'March 2026')
        self.assertContains(res, '7.50')

    def test_history_survives_a_junk_month(self):
        res = self.client.get(reverse('staff:attendance_history'), {'month': '99', 'year': 'abc'})
        self.assertEqual(res.status_code, 200)

    def test_leave_balance_counts_approved_days_only(self):
        lt = LeaveType.objects.create(name='Casual', days_allowed=12)
        LeaveRequest.objects.create(
            employee=self.intern, leave_type=lt, start_date=date(timezone.now().year, 5, 1),
            end_date=date(timezone.now().year, 5, 3), reason='Family', status='approved')
        LeaveRequest.objects.create(
            employee=self.intern, leave_type=lt, start_date=date(timezone.now().year, 6, 1),
            end_date=date(timezone.now().year, 6, 9), reason='Trip', status='pending')
        res = self.client.get(reverse('staff:leave'))
        balance = res.context['balances'][0]
        self.assertEqual(balance['used'], 3)        # only the approved 3 days
        self.assertEqual(balance['remaining'], 9)

    def test_payslips_hide_drafts(self):
        Payroll.objects.create(employee=self.intern, month=4, year=2026,
                               base_salary=Decimal('9000'), net_pay=Decimal('9000'), status='draft')
        Payroll.objects.create(employee=self.intern, month=5, year=2026,
                               base_salary=Decimal('9000'), net_pay=Decimal('8500'), status='paid')
        res = self.client.get(reverse('staff:payslip_list'))
        self.assertContains(res, 'May 2026')
        self.assertNotContains(res, 'April 2026')

    def test_assessment_average_uses_graded_only(self):
        InternAssessment.objects.create(employee=self.intern, title='Aptitude 1',
                                        max_score=Decimal('100'), scored=Decimal('80'))
        InternAssessment.objects.create(employee=self.intern, title='Aptitude 2',
                                        max_score=Decimal('100'), scored=Decimal('60'))
        InternAssessment.objects.create(employee=self.intern, title='Ungraded',
                                        max_score=Decimal('100'))
        res = self.client.get(reverse('staff:assessment_list'))
        self.assertEqual(res.context['average'], 70.0)
        self.assertEqual(res.context['graded_count'], 2)

    def test_classes_include_all_intern_broadcasts(self):
        broadcast = ScheduledClass.objects.create(
            title='SEO Basics', date=timezone.localdate() + timedelta(days=2),
            start_time='10:00', end_time='11:00')
        res = self.client.get(reverse('staff:class_list'))
        self.assertContains(res, 'SEO Basics')
        res = self.client.get(reverse('staff:class_detail', args=[broadcast.pk]))
        self.assertEqual(res.status_code, 200)

    def test_intern_only_nav_hidden_from_employees(self):
        self.client.logout()
        self.client.login(username='portal_employee', password=self.password)
        res = self.client.get(reverse('staff:dashboard'))
        self.assertNotContains(res, reverse('staff:assessment_list'))
        self.assertContains(res, reverse('staff:payslip_list'))


class StaffPortalIsolationTests(StaffPortalTestBase):
    """An intern must never see another person's records."""

    def setUp(self):
        self.login_intern()

    def test_work_of_another_employee_is_404(self):
        other = WorkAssignment.objects.create(title='Not yours')
        other.assigned_to.add(self.employee)
        res = self.client.get(reverse('staff:work_detail', args=[other.pk]))
        self.assertEqual(res.status_code, 404)

    def test_work_list_excludes_other_employees(self):
        mine = WorkAssignment.objects.create(title='Mine to do')
        mine.assigned_to.add(self.intern)
        theirs = WorkAssignment.objects.create(title='Theirs to do')
        theirs.assigned_to.add(self.employee)
        res = self.client.get(reverse('staff:work_list'))
        self.assertContains(res, 'Mine to do')
        self.assertNotContains(res, 'Theirs to do')

    def test_payslip_of_another_employee_is_404(self):
        other = Payroll.objects.create(employee=self.employee, month=5, year=2026,
                                       net_pay=Decimal('1000'), status='paid')
        res = self.client.get(reverse('staff:payslip_detail', args=[other.pk]))
        self.assertEqual(res.status_code, 404)

    def test_assessments_exclude_other_employees(self):
        InternAssessment.objects.create(employee=self.employee, title='Their test',
                                        max_score=Decimal('50'))
        res = self.client.get(reverse('staff:assessment_list'))
        self.assertNotContains(res, 'Their test')

    def test_class_not_assigned_to_this_intern_is_404(self):
        private = ScheduledClass.objects.create(
            title='Private session', date=timezone.localdate(),
            start_time='10:00', end_time='11:00')
        private.interns.add(self.employee)
        res = self.client.get(reverse('staff:class_detail', args=[private.pk]))
        self.assertEqual(res.status_code, 404)

    def test_leads_of_another_user_are_not_listed(self):
        from crm.models import Lead
        Lead.objects.create(contact_person='Their Lead', phone='9000000001',
                            assigned_to=self.employee_user)
        mine = Lead.objects.create(contact_person='My Lead', phone='9000000002',
                                   assigned_to=self.intern_user)
        res = self.client.get(reverse('staff:lead_list'))
        self.assertContains(res, 'My Lead')
        self.assertNotContains(res, 'Their Lead')
        self.assertEqual(self.client.get(reverse('staff:lead_detail', args=[mine.pk])).status_code, 200)

    def test_lead_of_another_user_is_404(self):
        from crm.models import Lead
        theirs = Lead.objects.create(contact_person='Their Lead', phone='9000000003',
                                     assigned_to=self.employee_user)
        res = self.client.get(reverse('staff:lead_detail', args=[theirs.pk]))
        self.assertEqual(res.status_code, 404)


class StaffPortalApiBridgeTests(StaffPortalTestBase):
    """The portal posts writes to the existing DRF endpoints via session auth.

    These prove that path actually works from a browser session, since that is
    the whole reason the portal does not re-implement the business rules.
    """

    def setUp(self):
        self.login_intern()

    def test_session_auth_reaches_the_attendance_api(self):
        res = self.client.post('/api/employees/attendance/check-in/', {
            'verification_method': 'face_qr', 'qr_code': 'nope'})
        # Rejected on the rules, NOT on authentication -- that is the point.
        self.assertNotIn(res.status_code, (401, 403))
        self.assertEqual(res.status_code, 400)

    def test_session_auth_can_create_a_leave_request(self):
        lt = LeaveType.objects.create(name='Sick', days_allowed=6)
        res = self.client.post('/api/employees/leave/requests/', {
            'leave_type': str(lt.id),
            'start_date': '2026-09-10',
            'end_date': '2026-09-11',
            'reason': 'Fever',
        })
        self.assertEqual(res.status_code, 201, res.content)
        self.assertTrue(LeaveRequest.objects.filter(employee=self.intern, reason='Fever').exists())

    def test_anonymous_cannot_reach_the_attendance_api(self):
        self.client.logout()
        res = self.client.post('/api/employees/attendance/check-in/', {'qr_code': 'x'})
        self.assertIn(res.status_code, (401, 403))


class StaffPortalPwaTests(StaffPortalTestBase):
    def test_manifest_is_served_with_the_right_type_and_scope(self):
        res = self.client.get(reverse('staff:manifest'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/manifest+json')
        import json
        data = json.loads(res.content)
        self.assertEqual(data['scope'], '/staff/')
        self.assertEqual(data['start_url'], '/staff/')
        self.assertEqual(data['display'], 'standalone')
        self.assertEqual(len(data['icons']), 4)

    def test_service_worker_is_scoped_to_the_portal(self):
        res = self.client.get(reverse('staff:service_worker'))
        self.assertEqual(res.status_code, 200)
        self.assertIn('javascript', res['Content-Type'])
        self.assertEqual(res['Service-Worker-Allowed'], '/staff/')

    def test_service_worker_never_caches_the_api(self):
        body = self.client.get(reverse('staff:service_worker')).content.decode()
        self.assertIn("pathname.startsWith('/api/')", body)
        self.assertIn("req.method !== 'GET'", body)

    def test_manifest_declares_a_maskable_icon(self):
        import json
        data = json.loads(self.client.get(reverse('staff:manifest')).content)
        purposes = [i.get('purpose') for i in data['icons']]
        self.assertIn('maskable', purposes,
                      'Android crops non-maskable icons and can clip the logo')
        self.assertEqual(data['background_color'], '#ffffff')

    def test_icon_files_exist_and_are_the_right_shape(self):
        from PIL import Image
        static = pathlib.Path(__file__).resolve().parent.parent / 'static' / 'staff'
        expected = {
            'icon-192.png': (192, 192),
            'icon-512.png': (512, 512),
            'icon-1024.png': (1024, 1024),
            'icon-maskable-512.png': (512, 512),
            'icon-180.png': (180, 180),
        }
        for name, size in expected.items():
            with self.subTest(icon=name):
                path = static / name
                self.assertTrue(path.exists(), f'{name} is missing')
                im = Image.open(path)
                self.assertEqual(im.size, size)

    def test_ios_and_maskable_icons_are_opaque(self):
        """iOS paints alpha as black and Android crops, so these must be flat."""
        from PIL import Image
        static = pathlib.Path(__file__).resolve().parent.parent / 'static' / 'staff'
        for name in ['icon-180.png', 'icon-maskable-512.png']:
            with self.subTest(icon=name):
                im = Image.open(static / name)
                self.assertNotIn('A', im.getbands(),
                                 f'{name} must not carry an alpha channel')

    def test_offline_page_renders_without_login(self):
        res = self.client.get(reverse('staff:offline'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "You're offline")

    def test_login_page_offers_the_install_flow(self):
        res = self.client.get(reverse('staff:login'))
        self.assertContains(res, 'Add to Home Screen')
        self.assertContains(res, 'apple-touch-icon')
        # The hint must be a real control wired to the install helper.
        self.assertContains(res, 'id="sfInstallOpen"')
        self.assertContains(res, 'js/staff.js')


class StaffPortalInstallPromptTests(StaffPortalTestBase):
    """Add-to-home-screen must be discoverable, dismissible and always reachable."""

    def setUp(self):
        self.login_intern()

    def test_banner_is_present_but_hidden_until_js_decides(self):
        res = self.client.get(reverse('staff:dashboard'))
        self.assertContains(res, 'id="sfInstallBanner"')
        # Hidden server-side; staff.js unhides it only when install is possible
        # and the user has not dismissed it.
        self.assertContains(res, '<div class="sf-install" id="sfInstallBanner" hidden>')

    def test_banner_has_both_a_show_me_and_a_dismiss_control(self):
        res = self.client.get(reverse('staff:dashboard'))
        self.assertContains(res, 'id="sfInstallOpen"')
        self.assertContains(res, 'id="sfInstallDismiss"')

    def test_menu_entry_survives_dismissing_the_banner(self):
        """Dismissing the banner is remembered, so the More sheet is the way back."""
        res = self.client.get(reverse('staff:dashboard'))
        self.assertContains(res, 'id="sfInstallEntry"')
        self.assertContains(res, 'Add to Home Screen')

    def test_every_page_carries_the_install_entry(self):
        for name in ['dashboard', 'attendance', 'leave', 'work_list', 'profile']:
            with self.subTest(page=name):
                res = self.client.get(reverse('staff:' + name))
                self.assertContains(res, 'id="sfInstallEntry"')

    def test_profile_offers_the_install_flow(self):
        res = self.client.get(reverse('staff:profile'))
        self.assertContains(res, 'id="sfInstallOpen"')

    def test_install_button_is_bound_before_the_banner_check(self):
        """Regression: the login page has an install button but no banner.

        initInstall() early-returns when there is no banner, so binding the
        button after that check left it dead on the login page -- the first
        screen every intern sees. Order matters here.
        """
        js = (pathlib.Path(__file__).resolve().parent.parent
              / 'static' / 'js' / 'staff.js').read_text()
        bind_at = js.index("open.addEventListener('click', SF.showInstallHelp)")
        bail_at = js.index('if (!banner) return;')
        self.assertLess(bind_at, bail_at,
                        'the install button must be bound before initInstall() '
                        'bails out on pages that have no banner')

    def test_install_help_covers_ios_and_android(self):
        js = (pathlib.Path(__file__).resolve().parent.parent
              / 'static' / 'js' / 'staff.js').read_text()
        self.assertIn('isIOS()', js)
        self.assertIn('/android/i.test(navigator.userAgent)', js)
        # Both platforms warn about in-app browsers, which cannot install.
        self.assertIn('Open in Safari', js)
        self.assertIn('Open in browser', js)

    def test_static_assets_are_version_stamped_together(self):
        """Unhashed statics need a ?v bump or phones serve a stale app."""
        res = self.client.get(reverse('staff:dashboard')).content.decode()
        self.assertIn('css/staff.css?v=5', res)
        self.assertIn('js/staff.js?v=5', res)


class StaffPortalThemeTests(StaffPortalTestBase):
    """Staff asked for a light portal; dark stays available behind a toggle."""

    def setUp(self):
        self.login_intern()

    def test_pages_default_to_light(self):
        for name in ['dashboard', 'attendance', 'profile']:
            with self.subTest(page=name):
                res = self.client.get(reverse('staff:' + name))
                self.assertContains(res, '<html lang="en" data-theme="light">')

    def test_login_page_defaults_to_light(self):
        self.client.logout()
        res = self.client.get(reverse('staff:login'))
        self.assertContains(res, '<html lang="en" data-theme="light">')
        self.assertContains(res, '<meta name="theme-color" content="#ffffff">')

    def test_theme_is_applied_before_first_paint(self):
        """Reading the stored theme after paint would flash the wrong colours."""
        res = self.client.get(reverse('staff:dashboard')).content.decode()
        pre_paint = res.index("localStorage.getItem('sf-theme')")
        stylesheet = res.index('css/staff.css')
        self.assertLess(pre_paint, stylesheet)

    def test_theme_toggle_is_offered(self):
        res = self.client.get(reverse('staff:dashboard'))
        self.assertContains(res, 'id="sfThemeToggle"')
        self.assertContains(res, 'Switch to dark')

    def test_stylesheet_defines_both_palettes(self):
        css = (pathlib.Path(__file__).resolve().parent.parent
               / 'static' / 'css' / 'staff.css').read_text()
        self.assertIn(':root {', css)
        self.assertIn('[data-theme="dark"] {', css)
        # No stray hardcoded colours from the old teal palette.
        for ghost in ['#2fd4d4', '#04191b', '#1c8f9a']:
            self.assertNotIn(ghost, css, f'{ghost} survives the theme rewrite')


class MainLoginRoutingTests(StaffPortalTestBase):
    """The main site login must send interns/employees to the portal, and
    must not steal owners, team members or admins away from the admin site."""

    def test_intern_lands_on_the_staff_portal(self):
        res = self.client.post(reverse('login'), {
            'username': 'portal_intern', 'password': self.password})
        self.assertRedirects(res, reverse('staff:dashboard'))

    def test_employee_lands_on_the_staff_portal(self):
        res = self.client.post(reverse('login'), {
            'username': 'portal_employee', 'password': self.password})
        self.assertRedirects(res, reverse('staff:dashboard'))

    def test_owner_still_lands_on_the_admin_dashboard(self):
        owner_user = User.objects.create_user(username='portal_owner', password=self.password)
        Employee.objects.create(user=owner_user, employee_id='EMPT04',
                                employment_type='fulltime', role='owner', status='active')
        res = self.client.post(reverse('login'), {
            'username': 'portal_owner', 'password': self.password})
        self.assertRedirects(res, reverse('dashboard'), fetch_redirect_response=False)

    def test_django_staff_user_still_lands_on_the_admin_dashboard(self):
        staff_user = User.objects.create_user(username='portal_admin', password=self.password,
                                              is_staff=True)
        Employee.objects.create(user=staff_user, employee_id='EMPT05',
                                employment_type='fulltime', role='employee', status='active')
        res = self.client.post(reverse('login'), {
            'username': 'portal_admin', 'password': self.password})
        self.assertRedirects(res, reverse('dashboard'), fetch_redirect_response=False)

    def test_explicit_next_is_still_honoured(self):
        res = self.client.post(
            reverse('login') + '?next=' + reverse('staff:profile'),
            {'username': 'portal_intern', 'password': self.password})
        self.assertRedirects(res, reverse('staff:profile'))
