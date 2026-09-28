import io
import json
import zipfile

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from employees.models import Employee

from .importer import run_import
from .models import (
    Enrollment, LabProgress, Lesson, Question, QuizAnswer, Student, TestAttempt, Track,
)
from .progress import lesson_statuses


def _quiet(*args, **kwargs):
    pass


class AcademyTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.counts = run_import(log=_quiet)
        cls.admin = User.objects.create_superuser('owner', 'o@example.com', 'pw')
        cls.user = User.objects.create_user('stu', password='pw', first_name='Asha')
        cls.student = Student.objects.create(user=cls.user, batch='Oct 2026')
        Enrollment.objects.create(student=cls.student, track_id='pl900')

    def login_student(self):
        self.client.login(username='stu', password='pw')

    def post_json(self, url, data):
        return self.client.post(url, json.dumps(data), content_type='application/json')


class ImportTests(AcademyTestBase):
    def test_counts_match_the_package(self):
        c = self.counts
        self.assertEqual((c['tracks'], c['domains'], c['lessons'], c['files'], c['questions']),
                         (4, 20, 76, 158, 292))

    def test_reimport_is_a_no_op_and_keeps_answers(self):
        q = Question.objects.filter(source='lesson').first()
        QuizAnswer.objects.create(user=self.user, question=q, last_choice=0)
        run_import(log=_quiet, force=True)
        self.assertEqual(Question.objects.count(), 292)
        self.assertTrue(QuizAnswer.objects.filter(question_id=q.pk).exists())

    def test_lesson_html_is_on_the_allow_list(self):
        for html in Lesson.objects.values_list('content_html', flat=True):
            self.assertNotIn('<script', html)
            self.assertNotIn('onclick', html)


class AccessTests(AcademyTestBase):
    def test_student_login_lands_in_academy(self):
        r = self.client.post(reverse('academy:login'), {'username': 'stu', 'password': 'pw'})
        self.assertRedirects(r, reverse('academy:home'))

    def test_keep_me_signed_in(self):
        self.client.post(reverse('academy:login'), {'username': 'stu', 'password': 'pw'})
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.client.logout()
        self.client.post(reverse('academy:login'), {'username': 'stu', 'password': 'pw', 'remember': '1'})
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), 30 * 24 * 60 * 60)

    def test_main_login_sends_students_to_academy(self):
        r = self.client.post(reverse('login'), {'username': 'stu', 'password': 'pw'})
        self.assertRedirects(r, reverse('academy:home'))

    def test_student_cannot_open_the_business_dashboard(self):
        self.login_student()
        r = self.client.get('/')
        self.assertRedirects(r, reverse('academy:home'))
        r = self.client.get(reverse('invoice_list'))
        self.assertRedirects(r, reverse('academy:home'))
        self.assertEqual(self.client.get('/api/pulse/ask/').status_code, 403)

    def test_student_cannot_open_academy_admin(self):
        self.login_student()
        r = self.client.get(reverse('academy:manage_students'), follow=True)
        self.assertEqual(r.redirect_chain[-1][0], reverse('academy:home'))

    def test_other_roles_are_untouched(self):
        self.client.login(username='owner', password='pw')
        self.assertEqual(self.client.get('/').status_code, 200)
        emp_user = User.objects.create_user('intern1', password='pw')
        Student.objects.create(user=emp_user)
        Employee.objects.create(user=emp_user, employee_id='E-1', employment_type='intern',
                                role='intern', status='active')
        # An intern who is also a student keeps the staff portal.
        self.client.login(username='intern1', password='pw')
        self.assertEqual(self.client.get('/staff/').status_code, 200)

    def test_inactive_student_is_refused(self):
        Student.objects.filter(pk=self.student.pk).update(status='inactive')
        r = self.client.post(reverse('academy:login'), {'username': 'stu', 'password': 'pw'})
        self.assertContains(r, 'no active Academy access')

    def test_not_enrolled_track_is_hidden(self):
        self.login_student()
        lesson = Lesson.objects.filter(track_id='ab400').first()
        self.assertEqual(self.client.get(reverse('academy:track', args=['ab400'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('academy:lesson', args=[lesson.id])).status_code, 404)
        f = lesson.lesson_files.exclude(file__id__startswith='hd/').first().file
        self.assertEqual(self.client.get(reverse('academy:file', args=[f.id])).status_code, 404)

    def test_owner_previews_every_track(self):
        self.client.login(username='owner', password='pw')
        self.assertEqual(self.client.get(reverse('academy:track', args=['ab400'])).status_code, 200)


class LearningTests(AcademyTestBase):
    def setUp(self):
        self.login_student()
        self.lesson = Lesson.objects.filter(track_id='pl900').exclude(lab_steps=[]).first()
        self.questions = list(Question.objects.filter(lesson=self.lesson, source='lesson'))

    def test_lessons_run_in_course_order(self):
        nums = list(Lesson.objects.filter(track_id='pl900').values_list('num', flat=True))
        self.assertEqual(nums[:4], ['0.1', '1.1', '1.2', '2.1'])

    def test_dashboard_and_pages_render(self):
        for name, args in [('academy:home', []), ('academy:track', ['pl900']),
                           ('academy:lesson', [self.lesson.id]), ('academy:test_start', ['pl900']),
                           ('academy:profile', []), ('academy:courses', []),
                           ('academy:assessments', []), ('academy:certificates', [])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)

    def test_every_lesson_renders(self):
        self.client.logout()
        self.client.login(username='owner', password='pw')
        for lesson in Lesson.objects.all():
            r = self.client.get(reverse('academy:lesson', args=[lesson.id]))
            self.assertEqual(r.status_code, 200, lesson.id)

    def test_profile_edit_and_password_change(self):
        url = reverse('academy:profile')
        r = self.client.post(url, {'action': 'info', 'first_name': 'Asha', 'last_name': 'Menon',
                                   'email': 'asha@example.com', 'phone': '98470'})
        self.assertRedirects(r, url)
        self.user.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual((self.user.last_name, self.user.email, self.student.phone),
                         ('Menon', 'asha@example.com', '98470'))
        # A weak password is refused and the old one keeps working.
        r = self.client.post(url, {'action': 'password', 'old_password': 'pw',
                                   'new_password1': '12345678', 'new_password2': '12345678'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['pw_form'].errors)
        r = self.client.post(url, {'action': 'password', 'old_password': 'pw',
                                   'new_password1': 'Lab-Steps-2026', 'new_password2': 'Lab-Steps-2026'})
        self.assertRedirects(r, url)
        self.client.logout()
        self.assertTrue(self.client.login(username='stu', password='Lab-Steps-2026'))

    def test_answer_key_is_not_on_the_page_before_answering(self):
        r = self.client.get(reverse('academy:lesson', args=[self.lesson.id]))
        html = r.content.decode()
        self.assertNotIn('data-answer', html)
        for q in self.questions:
            self.assertNotIn(q.explanation, html)

    def test_answer_is_graded_on_the_server(self):
        q = self.questions[0]
        wrong = (q.answer + 1) % len(q.options)
        r = self.post_json(reverse('academy:api_answer', args=[q.id]), {'choice': wrong})
        self.assertEqual(r.json()['correct'], False)
        self.assertEqual(r.json()['answer'], q.answer)
        r = self.post_json(reverse('academy:api_answer', args=[q.id]), {'choice': q.answer})
        self.assertTrue(r.json()['correct'])
        a = QuizAnswer.objects.get(user=self.user, question=q)
        self.assertEqual((a.attempts, a.ever_correct), (2, True))

    def test_lesson_becomes_done_after_lab_and_quiz(self):
        st = lambda: lesson_statuses(self.user, [self.lesson])[self.lesson.id]['status']
        self.assertEqual(st(), 'not_started')
        self.post_json(reverse('academy:api_lab', args=[self.lesson.id]), {'ticked_steps': [0]})
        self.assertEqual(st(), 'in_progress')
        all_steps = list(range(len(self.lesson.lab_steps))) + [99, 'x']
        r = self.post_json(reverse('academy:api_lab', args=[self.lesson.id]), {'ticked_steps': all_steps})
        self.assertEqual(r.json()['ticked_steps'], list(range(len(self.lesson.lab_steps))))
        for q in self.questions:
            self.post_json(reverse('academy:api_answer', args=[q.id]), {'choice': q.answer})
        self.assertEqual(st(), 'done')

    def test_practice_test_flow(self):
        r = self.client.post(reverse('academy:test_start', args=['pl900']), {'size': '30'})
        attempt = TestAttempt.objects.get(user=self.user)
        self.assertRedirects(r, reverse('academy:test_take', args=[attempt.id]))
        self.assertEqual(len(set(attempt.question_ids)), 30)
        page = self.client.get(reverse('academy:test_take', args=[attempt.id])).content.decode()
        self.assertNotIn('Correct.', page)

        qs = Question.objects.in_bulk(attempt.question_ids)
        answers = {str(i): qs[qid].answer for i, qid in enumerate(attempt.question_ids[:21])}
        self.post_json(reverse('academy:api_test_save', args=[attempt.id]), {'answers': answers})
        self.client.post(reverse('academy:test_submit', args=[attempt.id]))
        attempt.refresh_from_db()
        self.assertEqual(attempt.correct_count, 21)
        self.assertEqual(attempt.score, 700)
        self.assertTrue(attempt.passed)
        r = self.client.get(reverse('academy:test_result', args=[attempt.id]))
        self.assertContains(r, '700')

    def test_full_mock_needs_fifty_questions(self):
        self.client.post(reverse('academy:test_start', args=['pl900']), {'size': '50'})
        self.assertEqual(TestAttempt.objects.get(user=self.user).size, 50)

    def test_other_users_attempt_is_404(self):
        other = TestAttempt.objects.create(user=self.admin, track_id='pl900', question_ids=[])
        r = self.client.get(reverse('academy:test_take', args=[other.id]))
        self.assertEqual(r.status_code, 404)

    def test_downloads_are_attachments_and_zip_has_lab_md(self):
        f = self.lesson.lesson_files.first().file
        r = self.client.get(reverse('academy:file', args=[f.id]))
        self.assertIn('attachment', r['Content-Disposition'])
        r = self.client.get(reverse('academy:lesson_zip', args=[self.lesson.id]))
        names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
        self.assertIn('LAB.md', names)
        self.assertEqual(len(names), self.lesson.lesson_files.count() + 1)


class ManageTests(AcademyTestBase):
    def setUp(self):
        self.client.login(username='owner', password='pw')

    def test_create_student_with_tracks(self):
        r = self.client.post(reverse('academy:manage_student_new'), {
            'first_name': 'Ravi', 'username': 'ravi', 'batch': 'Nov', 'tracks': ['pl900', 'pl300'],
        })
        s = Student.objects.get(user__username='ravi')
        self.assertRedirects(r, reverse('academy:manage_student_detail', args=[s.pk]),
                             fetch_redirect_response=False)
        self.assertEqual(set(s.enrollments.values_list('track_id', flat=True)), {'pl900', 'pl300'})
        page = self.client.get(reverse('academy:manage_student_detail', args=[s.pk]))
        self.assertContains(page, 'shown once')
        # The generated password works on the student login.
        pw = page.context['new_password']
        self.client.logout()
        self.assertTrue(self.client.login(username='ravi', password=pw))

    def test_pages_render(self):
        for name, args in [('academy:manage_home', []), ('academy:manage_students', []),
                           ('academy:manage_student_new', []), ('academy:manage_progress', []),
                           ('academy:manage_student_detail', [self.student.pk]),
                           ('academy:manage_student_edit', [self.student.pk])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)

    def test_progress_csv(self):
        r = self.client.get(reverse('academy:manage_progress') + '?track=pl900&export=csv')
        self.assertEqual(r['Content-Type'], 'text/csv')
        self.assertIn('Asha', r.content.decode())

    def test_non_admin_is_refused(self):
        u = User.objects.create_user('team', password='pw')
        self.client.login(username='team', password='pw')
        r = self.client.get(reverse('academy:manage_students'))
        self.assertRedirects(r, reverse('dashboard'), fetch_redirect_response=False)

    def test_accounts_page_shows_student_role(self):
        r = self.client.get(reverse('account_list') + '?role=Student')
        self.assertContains(r, 'stu')


class LockAndPerkTests(AcademyTestBase):
    def setUp(self):
        self.login_student()
        self.lessons = list(Lesson.objects.filter(track_id='pl900'))

    def finish(self, lesson):
        LabProgress.objects.update_or_create(
            user=self.user, lesson=lesson,
            defaults={'ticked_steps': list(range(len(lesson.lab_steps)))})
        for q in Question.objects.filter(lesson=lesson, source='lesson'):
            QuizAnswer.objects.update_or_create(user=self.user, question=q,
                                                defaults={'last_choice': q.answer, 'ever_correct': True,
                                                          'attempts': 1})

    def test_lessons_unlock_in_order(self):
        first, second = self.lessons[0], self.lessons[1]
        r = self.client.get(reverse('academy:lesson', args=[second.id]))
        self.assertRedirects(r, reverse('academy:track', args=['pl900']))
        # The first lesson's page offers no link into the locked one.
        page = self.client.get(reverse('academy:lesson', args=[first.id]))
        self.assertNotContains(page, 'href="%s"' % reverse('academy:lesson', args=[second.id]))
        r = self.post_json(reverse('academy:api_lab', args=[second.id]), {'ticked_steps': [0]})
        self.assertEqual(r.status_code, 403)
        self.finish(first)
        self.assertEqual(self.client.get(reverse('academy:lesson', args=[second.id])).status_code, 200)

    def test_started_lesson_stays_open(self):
        third = self.lessons[2]
        LabProgress.objects.create(user=self.user, lesson=third, ticked_steps=[0])
        self.assertEqual(self.client.get(reverse('academy:lesson', args=[third.id])).status_code, 200)

    def test_course_waits_for_prerequisite(self):
        Enrollment.objects.create(student=self.student, track_id='ab410')
        first = Lesson.objects.filter(track_id='ab410').first()
        r = self.client.get(reverse('academy:lesson', args=[first.id]))
        self.assertRedirects(r, reverse('academy:track', args=['ab410']))
        r = self.client.post(reverse('academy:test_start', args=['ab410']), {'size': '30'})
        self.assertRedirects(r, reverse('academy:track', args=['ab410']))
        self.assertContains(self.client.get(reverse('academy:track', args=['ab410'])), 'This course is locked')
        # Finish PL-900: every lesson plus a passing practice test.
        for lesson in self.lessons:
            self.finish(lesson)
        TestAttempt.objects.create(user=self.user, track_id='pl900', question_ids=[1], score=800,
                                   correct_count=1, submitted_at='2026-09-27T10:00:00Z')
        self.assertEqual(self.client.get(reverse('academy:lesson', args=[first.id])).status_code, 200)

    def test_started_course_stays_open(self):
        Enrollment.objects.create(student=self.student, track_id='pl300')
        TestAttempt.objects.create(user=self.user, track_id='pl300', question_ids=[])
        first = Lesson.objects.filter(track_id='pl300').first()
        self.assertEqual(self.client.get(reverse('academy:lesson', args=[first.id])).status_code, 200)

    def test_prerequisite_not_enrolled_does_not_block(self):
        Enrollment.objects.filter(student=self.student).delete()
        Enrollment.objects.create(student=self.student, track_id='ab410')
        first = Lesson.objects.filter(track_id='ab410').first()
        self.assertEqual(self.client.get(reverse('academy:lesson', args=[first.id])).status_code, 200)

    def test_trainer_unlock_all(self):
        Student.objects.filter(pk=self.student.pk).update(unlock_all=True)
        self.assertEqual(self.client.get(reverse('academy:lesson', args=[self.lessons[5].id])).status_code, 200)

    def test_xp_badge_and_streak(self):
        first = self.lessons[0]
        r = self.post_json(reverse('academy:api_lab', args=[first.id]), {'ticked_steps': [0]}).json()
        self.assertEqual(r['perks']['xp_gain'], 5)
        self.assertEqual(r['perks']['streak'], 1)
        self.assertEqual([b['name'] for b in r['perks']['new_badges']], ['First step'])
        # Announced once only.
        r = self.post_json(reverse('academy:api_lab', args=[first.id]), {'ticked_steps': [0, 1]}).json()
        self.assertEqual(r['perks']['new_badges'], [])
        q = Question.objects.filter(lesson=first, source='lesson').first()
        r = self.post_json(reverse('academy:api_answer', args=[q.id]), {'choice': q.answer}).json()
        self.assertEqual(r['perks']['xp_gain'], 10)
        self.assertContains(self.client.get(reverse('academy:profile')), 'Achievements')


class PublicCatalogTests(AcademyTestBase):
    def test_pages_are_public(self):
        for url in [reverse('academy:catalog'), reverse('academy:catalog_course', args=['pl300']),
                    reverse('academy:catalog_lesson', args=['pl300', 'b1']), '/robots.txt',
                    reverse('academy:sitemap')]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_only_free_lessons_are_public(self):
        self.assertEqual(self.client.get(reverse('academy:catalog_lesson', args=['pl300', 'b7'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('academy:catalog_lesson', args=['pl900', 'b1'])).status_code, 404)

    def test_no_quiz_answers_or_files_leak(self):
        lesson = Lesson.objects.get(pk='b1')
        html = self.client.get(reverse('academy:catalog_lesson', args=['pl300', 'b1'])).content.decode()
        for q in Question.objects.filter(lesson=lesson):
            self.assertNotIn(q.explanation, html)
        for lf in lesson.lesson_files.select_related('file'):
            if len(lf.file.content) > 40:
                self.assertNotIn(lf.file.content[:40], html)
        self.assertNotIn('/academy/files/', html)

    def test_sitemap_lists_free_lessons(self):
        xml = self.client.get(reverse('academy:sitemap')).content.decode()
        self.assertIn('/academy/catalog/pl300/b1/', xml)
        self.assertNotIn('/academy/catalog/pl300/b7/', xml)

    def test_try_a_sample_question(self):
        from .public_views import sample_question
        q = sample_question(Track.objects.get(pk='pl900'))
        r = self.post_json(reverse('academy:catalog_try', args=[q.id]), {'choice': q.answer})
        self.assertEqual(r.json()['correct'], True)
        self.assertContains(self.client.get(reverse('academy:catalog')), q.question)
        # Questions outside the free lessons are never graded publicly.
        locked = Question.objects.filter(lesson_id='b7', source='lesson').first()
        r = self.post_json(reverse('academy:catalog_try', args=[locked.id]), {'choice': 0})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.client.get(reverse('academy:catalog_try', args=[q.id])).status_code, 405)

    def test_urls_use_https_behind_proxy(self):
        xml = self.client.get(reverse('academy:sitemap'), HTTP_X_FORWARDED_PROTO='https').content.decode()
        self.assertIn('<loc>https://', xml)
        self.assertIn('Sitemap: https://', self.client.get('/robots.txt', HTTP_X_FORWARDED_PROTO='https').content.decode())

    def test_student_can_browse_catalog(self):
        self.login_student()
        r = self.client.get(reverse('academy:catalog'))
        self.assertContains(r, 'My dashboard')


class VideoTests(AcademyTestBase):
    def test_link_parsing(self):
        from .video import embed
        yt = embed('https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=5')
        self.assertEqual(yt['src'].split('?')[0], 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ')
        self.assertEqual(embed('https://youtu.be/dQw4w9WgXcQ')['kind'], 'iframe')
        self.assertEqual(embed('https://vimeo.com/76979871')['src'], 'https://player.vimeo.com/video/76979871')
        self.assertEqual(embed('https://cdn.example.com/l.mp4')['kind'], 'file')
        self.assertIsNone(embed('http://cdn.example.com/l.mp4'))
        self.assertIsNone(embed('https://example.com/page'))

    def test_admin_saves_links_and_rejects_bad_ones(self):
        self.client.login(username='owner', password='pw')
        url = reverse('academy:manage_videos') + '?track=pl900'
        self.assertEqual(self.client.get(url).status_code, 200)
        r = self.client.post(reverse('academy:manage_videos'),
                             {'track': 'pl900', 'video_l1-1': 'https://youtu.be/dQw4w9WgXcQ'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Lesson.objects.get(pk='l1-1').video_url, 'https://youtu.be/dQw4w9WgXcQ')
        r = self.client.post(reverse('academy:manage_videos'),
                             {'track': 'pl900', 'video_l0-1': 'https://example.com/page'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Lesson.objects.get(pk='l0-1').video_url, '')

    def test_player_shows_and_reimport_keeps_link(self):
        Lesson.objects.filter(pk='l0-1').update(video_url='https://youtu.be/dQw4w9WgXcQ')
        self.assertContains(self.client.get(reverse('academy:catalog_lesson', args=['pl900', 'l0-1'])),
                            'youtube-nocookie.com/embed/dQw4w9WgXcQ')
        self.login_student()
        self.assertContains(self.client.get(reverse('academy:lesson', args=['l0-1'])), 'Watch the lesson')
        run_import(log=_quiet, force=True)
        self.assertEqual(Lesson.objects.get(pk='l0-1').video_url, 'https://youtu.be/dQw4w9WgXcQ')
