"""The intern bootcamp (Academy course `django`) opened from the staff portal."""
import json
from pathlib import Path

from django.test import TestCase
from django.urls import reverse

from academy.models import Domain, Enrollment, LabProgress, Lesson, Student, Track

from .tests_portal import StaffPortalTestBase


def make_track():
    track = Track.objects.create(
        id='django', code='Django', name='Python & Django Backend Bootcamp', level='Intern bootcamp',
        status='Live', outline_date='Nov 2026', order_hint='', blurb='Five days.', tool='Python',
        guide_url='https://docs.djangoproject.com/', note='', category='development')
    d1 = Domain.objects.create(id='djd1', track=track, name='Day 1', weight='Day 1', sort_order=0)
    Lesson.objects.create(id='dj1', track=track, domain=d1, num='1.1', title='Python traps',
                          minutes=60, lab_steps=['a', 'b'], sort_order=0)
    Lesson.objects.create(id='dj2', track=track, domain=d1, num='1.2', title='Decorators',
                          minutes=60, lab_steps=['a'], sort_order=1)
    return track


class BootcampPortalTests(StaffPortalTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.track = make_track()

    def test_intern_dashboard_shows_the_course_card(self):
        self.login_intern()
        res = self.client.get(reverse('staff:dashboard'))
        self.assertContains(res, 'Your Bootcamp')
        self.assertContains(res, 'Python &amp; Django Backend Bootcamp')
        self.assertContains(res, f"{reverse('staff:bootcamp')}?lesson=dj1")
        self.assertContains(res, 'Next: 1.1 Python traps')

    def test_employee_dashboard_has_no_course_card(self):
        self.client.login(username='portal_employee', password=self.password)
        res = self.client.get(reverse('staff:dashboard'))
        self.assertNotContains(res, 'Your Bootcamp')
        self.assertEqual(self.client.get(reverse('staff:bootcamp')).status_code, 404)

    def test_card_hidden_when_course_not_imported(self):
        Track.objects.filter(pk='django').update(is_published=False)
        self.login_intern()
        self.assertNotContains(self.client.get(reverse('staff:dashboard')), 'Your Bootcamp')
        res = self.client.get(reverse('staff:bootcamp'))
        self.assertRedirects(res, reverse('staff:dashboard'))
        self.assertFalse(Student.objects.filter(user=self.intern_user).exists())

    def test_first_open_enrols_and_lands_on_the_course(self):
        self.login_intern()
        res = self.client.get(reverse('staff:bootcamp'))
        self.assertRedirects(res, reverse('academy:track', args=['django']), fetch_redirect_response=False)
        student = Student.objects.get(user=self.intern_user)
        self.assertTrue(Enrollment.objects.filter(student=student, track_id='django').exists())
        # Opening it again doesn't duplicate anything.
        self.client.get(reverse('staff:bootcamp'))
        self.assertEqual(Enrollment.objects.filter(student=student).count(), 1)

    def test_lesson_link_opens_that_lesson_and_ignores_others(self):
        self.login_intern()
        res = self.client.get(reverse('staff:bootcamp') + '?lesson=dj1')
        self.assertRedirects(res, reverse('academy:lesson', args=['dj1']), fetch_redirect_response=False)
        res = self.client.get(reverse('staff:bootcamp') + '?lesson=pl1')
        self.assertRedirects(res, reverse('academy:track', args=['django']), fetch_redirect_response=False)

    def test_enrolled_intern_reaches_the_course_and_keeps_portal_access(self):
        self.login_intern()
        self.client.get(reverse('staff:bootcamp'))
        res = self.client.get(reverse('academy:track', args=['django']))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Back to staff portal')
        # Visible way back in the top bar and the phone bottom bar, not only in the name menu.
        self.assertContains(res, '<span>Staff portal</span>', html=False)
        self.assertContains(res, f'href="{reverse("staff:dashboard")}"', count=4)
        # A Student profile must not confine the intern to /academy/.
        self.assertEqual(self.client.get(reverse('staff:dashboard')).status_code, 200)

    def test_bootcamp_lessons_are_all_open(self):
        # Mentor-led: an intern can open lesson 2 without finishing lesson 1.
        self.login_intern()
        self.client.get(reverse('staff:bootcamp'))
        res = self.client.get(reverse('academy:lesson', args=['dj2']))
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'data-unlock-pager')
        res = self.client.get(reverse('academy:track', args=['django']))
        self.assertNotContains(res, 'Finish 1.1')

    def test_card_shows_progress(self):
        LabProgress.objects.create(user=self.intern_user, lesson_id='dj1', ticked_steps=[0, 1])
        self.login_intern()
        res = self.client.get(reverse('staff:dashboard'))
        self.assertContains(res, '1 of 2 lessons done')
        self.assertContains(res, 'Continue')
        self.assertContains(res, 'Next: 1.2 Decorators')

    def test_hr_switched_off_academy_access_is_respected(self):
        Student.objects.create(user=self.intern_user, status='inactive')
        self.login_intern()
        res = self.client.get(reverse('staff:bootcamp'))
        self.assertRedirects(res, reverse('staff:dashboard'))
        self.assertFalse(Enrollment.objects.exists())


class BootcampContentTests(TestCase):
    """The packaged course JSON is consistent with its lab files."""

    def test_package_shape(self):
        content = Path(__file__).resolve().parent.parent / 'academy' / 'content'
        track = json.loads((content / 'django.json').read_text(encoding='utf-8'))
        index = json.loads((content / 'files-index.json').read_text(encoding='utf-8'))
        lessons = [l for d in track['domains'] for l in d['lessons']]
        self.assertEqual((len(track["domains"]), len(lessons)), (7, 16))
        self.assertGreaterEqual(sum(len(l['quiz']) for l in lessons), 30)  # enough for a 30-question test
        for lesson in lessons:
            self.assertTrue(lesson['lab']['steps'], lesson['id'])
            for fid in lesson['lab']['files']:
                self.assertIn(fid, index)
                self.assertTrue((content / 'exercise-files' / fid).exists(), fid)
        self.assertIn('django/bookit/manage.py', track['data'])
