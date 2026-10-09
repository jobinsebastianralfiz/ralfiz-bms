"""Internship enrolment: HR link -> student form -> HR approve into an intern."""

import io
import shutil
import tempfile
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from employees.models import Employee, InternEnrolment

TMP_MEDIA = tempfile.mkdtemp(prefix='enrol-test-')


def png(name='photo.png'):
    buf = io.BytesIO()
    Image.new('RGB', (40, 50), (30, 90, 200)).save(buf, 'PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


def pdf(name='id.pdf'):
    return SimpleUploadedFile(name, b'%PDF-1.4\n%fake\n', content_type='application/pdf')


def form_data(**overrides):
    data = {
        'full_name': 'Anjali Menon', 'phone': '9876543210', 'whatsapp': '', 'email': 'anjali@example.com',
        'date_of_birth': '2004-05-17', 'address': 'Kozhikode, Kerala', 'guardian_name': 'Ravi Menon',
        'guardian_phone': '9876500000', 'college_name': 'MES College', 'course': 'BCA',
        'year_of_study': '3', 'register_number': 'MES21BCA07', 'track': 'development',
        'track_other': '', 'preferred_start_date': '2026-11-02', 'duration_months': '3',
        'work_mode': 'onsite', 'skills': 'Python basics', 'confirm': '1',
    }
    data.update(overrides)
    return data


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class EnrolmentTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.hr = User.objects.create_superuser('boss', 'boss@example.com', 'pw-123456')
        self.client.force_login(self.hr)
        response = self.client.post(reverse('enrolment_send'),
                                    {'name': 'Anjali', 'phone': '9876543210', 'email': ''})
        self.enrolment = InternEnrolment.objects.get()
        self.assertRedirects(response, reverse('enrolment_detail', args=[self.enrolment.pk]))
        self.url = reverse('enrolment_form', args=[self.enrolment.token])
        self.client.logout()

    def submit(self, **overrides):
        data = form_data(**overrides)
        data.setdefault('photo', png())
        data.setdefault('id_proof', pdf())
        return self.client.post(self.url, {k: v for k, v in data.items() if v is not None})

    # ---------------------------------------------------------- student side

    def test_form_opens_prefilled_and_marks_opened(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Internship Enrolment')
        self.assertContains(response, 'value="9876543210"')
        self.enrolment.refresh_from_db()
        self.assertEqual(self.enrolment.status, 'opened')

    def test_full_submission(self):
        response = self.submit()
        self.assertRedirects(response, reverse('enrolment_done', args=[self.enrolment.token]))
        e = InternEnrolment.objects.get()
        self.assertEqual((e.status, e.full_name, e.date_of_birth, e.track),
                         ('submitted', 'Anjali Menon', date(2004, 5, 17), 'development'))
        self.assertTrue(e.photo.name.startswith(f'enrolments/{e.pk}/photo'))
        # The link now shows the thank-you page, and cannot be resubmitted.
        self.assertRedirects(self.client.get(self.url), reverse('enrolment_done', args=[e.token]))
        self.client.post(self.url, form_data(full_name='Someone else'))
        e.refresh_from_db()
        self.assertEqual(e.full_name, 'Anjali Menon')

    def test_errors_keep_valid_uploads(self):
        response = self.submit(email='not-an-email', guardian_phone='12')
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Enter a valid email address.', status_code=400)
        self.assertContains(response, 'Attached. Choose a file only to replace it.', status_code=400)
        # Second try without re-attaching anything goes through.
        response = self.client.post(self.url, form_data())
        self.assertRedirects(response, reverse('enrolment_done', args=[self.enrolment.token]))

    def test_required_documents_and_file_checks(self):
        response = self.client.post(self.url, form_data())
        self.assertContains(response, 'Please attach this file.', count=2, status_code=400)
        response = self.submit(photo=SimpleUploadedFile('p.png', b'not an image'))
        self.assertContains(response, 'could not be read', status_code=400)
        response = self.submit(id_proof=SimpleUploadedFile('id.exe', b'MZ'))
        self.assertContains(response, 'Upload a', status_code=400)

    def test_other_track_needs_a_name(self):
        response = self.submit(track='other')
        self.assertContains(response, 'Tell us which area.', status_code=400)

    def test_expired_and_cancelled_links(self):
        InternEnrolment.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        self.assertContains(self.client.get(self.url), 'This link has expired')
        InternEnrolment.objects.update(status='cancelled')
        self.assertContains(self.client.get(self.url), 'no longer active')
        self.assertEqual(self.client.get('/enrol/not-a-token/').status_code, 404)

    # ---------------------------------------------------------- privacy

    def test_documents_are_private(self):
        self.submit()
        e = InternEnrolment.objects.get()
        for path in (f'/media/private/{e.id_proof.name}', f'/media/./private/{e.id_proof.name}',
                     f'/media/x/../private/{e.id_proof.name}'):
            self.assertEqual(self.client.get(path).status_code, 404, path)

        file_url = reverse('enrolment_file', args=[e.pk, 'id_proof'])
        self.assertEqual(self.client.get(file_url).status_code, 302)  # to login

        intern = User.objects.create_user('meera', password='pw-123456')
        Employee.objects.create(user=intern, employee_id='EMP900', employment_type='intern', role='intern')
        self.client.force_login(intern)
        self.assertEqual(self.client.get(file_url).status_code, 403)
        self.assertEqual(self.client.get(reverse('enrolment_list')).status_code, 403)

        self.client.force_login(self.hr)
        response = self.client.get(file_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4\n%fake\n')

    # ---------------------------------------------------------- HR side

    def test_approve_creates_intern_with_login(self):
        self.submit()
        e = InternEnrolment.objects.get()
        self.client.force_login(self.hr)
        detail = self.client.get(reverse('enrolment_detail', args=[e.pk]))
        self.assertContains(detail, 'value="anjali"')  # suggested username
        self.assertContains(detail, 'Software Development Intern')

        response = self.client.post(reverse('enrolment_approve', args=[e.pk]), {
            'username': 'anjali', 'joining_date': '2026-11-02', 'department': 'engineering',
            'designation': 'Software Development Intern'})
        # Not followed: following would use up the once-only password display.
        self.assertRedirects(response, reverse('enrolment_detail', args=[e.pk]),
                             fetch_redirect_response=False)

        e.refresh_from_db()
        emp = e.employee
        self.assertEqual((e.status, emp.role, emp.employment_type, emp.department),
                         ('approved', 'intern', 'intern', 'engineering'))
        self.assertEqual((emp.user.first_name, emp.user.last_name, emp.phone, emp.emergency_contact),
                         ('Anjali', 'Menon', '9876543210', '9876500000'))
        self.assertEqual(emp.joining_date, date(2026, 11, 2))
        self.assertIn('MES College', emp.notes)
        self.assertTrue(emp.profile_photo)

        # Password shown once, and it works for the staff portal.
        page = self.client.get(reverse('enrolment_detail', args=[e.pk]))
        password = page.context['login']['password']
        self.assertContains(page, 'shown only once')
        self.assertNotContains(self.client.get(reverse('enrolment_detail', args=[e.pk])), 'shown only once')
        self.client.logout()
        self.assertTrue(self.client.login(username='anjali', password=password))

    def test_approve_refuses_taken_username_and_double_approval(self):
        self.submit()
        e = InternEnrolment.objects.get()
        self.client.force_login(self.hr)
        approve = reverse('enrolment_approve', args=[e.pk])
        self.client.post(approve, {'username': 'boss', 'joining_date': '2026-11-02'})
        e.refresh_from_db()
        self.assertEqual(e.status, 'submitted')
        self.assertFalse(Employee.objects.filter(role='intern').exists())

        self.client.post(approve, {'username': 'anjali', 'joining_date': '2026-11-02'})
        self.client.post(approve, {'username': 'anjali2', 'joining_date': '2026-11-02'})
        self.assertEqual(Employee.objects.filter(role='intern').count(), 1)

    def test_next_employee_id_ignores_other_formats(self):
        for eid in ('EMP009', 'EMP010', 'SMOKE-OWNER', 'EMPX'):
            user = User.objects.create_user(f'u-{eid}')
            Employee.objects.create(user=user, employee_id=eid, employment_type='fulltime')
        self.assertEqual(Employee.next_employee_id(), 'EMP011')

    def test_reject(self):
        self.submit()
        e = InternEnrolment.objects.get()
        self.client.force_login(self.hr)
        self.client.post(reverse('enrolment_reject', args=[e.pk]), {'reason': 'Batch full'})
        e.refresh_from_db()
        self.assertEqual((e.status, e.rejection_reason), ('rejected', 'Batch full'))
        self.client.logout()
        self.assertContains(self.client.get(reverse('enrolment_done', args=[e.token])),
                            'Thank you for applying')

    def test_list_and_counters(self):
        self.submit()
        self.client.force_login(self.hr)
        response = self.client.get(reverse('enrolment_list'))
        self.assertEqual(response.context['counters']['to_review'], 1)
        self.assertContains(response, 'MES College')
