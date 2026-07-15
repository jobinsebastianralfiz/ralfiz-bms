from datetime import date

from django.test import TestCase
from django.urls import reverse

from employees.models import Certificate


class CertificateBodyRenderTests(TestCase):
    def setUp(self):
        self.cert = Certificate(
            title='COURSE COMPLETION CERTIFICATE',
            certificate_type='course',
            salutation='Ms.',
            student_name='SABITHA P',
            gender='female',
            course_name='Mobile App Development using Flutter',
            start_date=date(2025, 5, 5),
            end_date=date(2025, 10, 28),
            mode='offline',
            date_of_issuance=date(2025, 11, 5),
            skills=['Flutter', 'Dart'],
        )

    def test_substitutes_known_placeholders(self):
        self.cert.body_text = 'This is to certify that {salutation} {student_name} from {course_name}.'
        self.assertIn('Ms. SABITHA P', self.cert.render_body_html())
        self.assertIn('Mobile App Development using Flutter', self.cert.render_body_html())

    def test_gendered_pronouns(self):
        self.cert.body_text = '{pronoun_cap} did well. We found {object_pronoun} sincere, {possessive} work good.'
        html = self.cert.render_body_html()
        self.assertIn('She did well. We found her sincere, her work good.', html)

    def test_position_uses_position_field_when_set(self):
        self.cert.position = 'Flutter Developer Intern'
        self.cert.body_text = 'engaged as a {position}.'
        self.assertIn('engaged as a Flutter Developer Intern.', self.cert.render_body_html())

    def test_position_falls_back_to_course_name_when_unset(self):
        """Existing bodies were written when {position} meant course_name."""
        self.cert.position = ''
        self.cert.body_text = 'engaged as a {position}.'
        self.assertIn('engaged as a Mobile App Development using Flutter.', self.cert.render_body_html())

    def test_position_empty_when_neither_set(self):
        self.cert.position = ''
        self.cert.course_name = ''
        self.cert.body_text = 'as a [{position}].'
        html = self.cert.render_body_html()
        self.assertIn('as a [].', html)
        self.assertNotIn('None', html)

    def test_register_number_placeholder(self):
        self.cert.register_number = 'BAI247966'
        self.cert.body_text = 'Reg. No.: {register_number}'
        self.assertIn('Reg. No.: BAI247966', self.cert.render_body_html())

    def test_register_number_blank_renders_empty(self):
        self.cert.register_number = ''
        self.cert.body_text = 'Reg. No.: [{register_number}]'
        html = self.cert.render_body_html()
        self.assertIn('Reg. No.: []', html)
        self.assertNotIn('None', html)

    def test_pronoun_object_and_possessive_aliases(self):
        self.cert.body_text = 'We found {pronoun_object} sincere and appreciate {pronoun_possessive} commitment.'
        html = self.cert.render_body_html()
        self.assertIn('We found her sincere and appreciate her commitment.', html)

    def test_unknown_placeholder_does_not_break_the_rest(self):
        """The bug: one bad name made .format() raise, falling back to a fully raw body."""
        self.cert.body_text = 'Certify that {student_name} as a {totally_unknown_thing} passed.'
        html = self.cert.render_body_html()
        self.assertIn('SABITHA P', html)
        self.assertIn('{totally_unknown_thing}', html)

    def test_dates_are_formatted_with_ordinal_suffix(self):
        self.cert.body_text = 'from {start_date} to {end_date}.'
        self.assertIn('from 5th May 2025 to 28th October 2025.', self.cert.render_body_html())

    def test_skills_render_as_bullet_list(self):
        self.cert.body_text = 'Skills:\n\n{skills}'
        html = self.cert.render_body_html()
        self.assertIn('<ul class="skills-list">', html)
        self.assertIn('<li>Flutter</li>', html)

    def test_skills_are_html_escaped(self):
        self.cert.skills = ['<script>alert(1)</script>']
        self.cert.body_text = '{skills}'
        self.assertNotIn('<script>', self.cert.render_body_html())

    def test_bold_markers_become_strong_tags(self):
        self.cert.body_text = 'Certify that **{student_name}** passed.'
        self.assertIn('<strong>SABITHA P</strong>', self.cert.render_body_html())

    def test_paragraphs_split_on_blank_lines(self):
        self.cert.body_text = 'First para.\n\nSecond para.'
        html = self.cert.render_body_html()
        self.assertIn('<p class="body-text">First para.</p>', html)
        self.assertIn('<p class="body-text">Second para.</p>', html)

    def test_paragraphs_split_on_crlf_blank_lines(self):
        """Browsers submit textarea line breaks as CRLF, so stored bodies use \\r\\n."""
        self.cert.body_text = 'First para.\r\n\r\nSecond para.'
        html = self.cert.render_body_html()
        self.assertEqual(html.count('<p class="body-text">'), 2)
        self.assertIn('<p class="body-text">First para.</p>', html)
        self.assertIn('<p class="body-text">Second para.</p>', html)

    def test_no_carriage_returns_leak_into_html(self):
        self.cert.body_text = 'Line one.\r\nLine two.\r\n\r\nNext para.'
        self.assertNotIn('\r', self.cert.render_body_html())

    def test_crlf_paragraph_around_skills_list(self):
        self.cert.body_text = 'Intro:\r\n\r\n{skills}\r\n\r\nOutro.'
        html = self.cert.render_body_html()
        self.assertIn('<p class="body-text">Intro:</p>', html)
        self.assertIn('<ul class="skills-list">', html)
        self.assertIn('<p class="body-text">Outro.</p>', html)

    def test_blank_optional_fields_render_empty_not_none(self):
        self.cert.college_name = ''
        self.cert.duration_days = None
        self.cert.body_text = 'College: [{college_name}] Days: [{duration_days}]'
        html = self.cert.render_body_html()
        self.assertIn('College: [] Days: []', html)
        self.assertNotIn('None', html)

    def test_malformed_braces_fall_back_to_raw_body(self):
        self.cert.body_text = 'Certify that {student_name} and an unclosed { brace.'
        self.assertIn('unclosed', self.cert.render_body_html())


class CertificateFormWiringTests(TestCase):
    """The new fields must survive the real create/edit views, not just the model."""

    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user('hr', password='pw')
        self.client.force_login(self.user)

    def _post_data(self, **overrides):
        data = {
            'certificate_type': 'inter',
            'title': 'INTERNSHIP CERTIFICATE',
            'salutation': 'Mr.',
            'student_name': 'Mohammed Amal P',
            'register_number': 'BAI247966',
            'gender': 'male',
            'college_name': '',
            'course_name': '',
            'position': 'Python Developer Intern',
            'start_date': '2026-06-01',
            'end_date': '2026-07-17',
            'mode': 'offline',
            'skills': 'Python Programming\nDjango Framework',
            'body_text': 'Certify {student_name} (Reg. No.: {register_number}) as a {position}.',
            'wish_text': 'We wish {pronoun} success in {possessive} future.',
            'date_of_issuance': '2026-07-17',
        }
        data.update(overrides)
        return data

    def test_create_view_saves_register_number_and_position(self):
        resp = self.client.post(reverse('certificate_create'), self._post_data())
        self.assertEqual(resp.status_code, 302)
        cert = Certificate.objects.get()
        self.assertEqual(cert.register_number, 'BAI247966')
        self.assertEqual(cert.position, 'Python Developer Intern')

    def test_edit_view_updates_register_number_and_position(self):
        self.client.post(reverse('certificate_create'), self._post_data())
        cert = Certificate.objects.get()
        self.client.post(
            reverse('certificate_detail', args=[cert.pk]),
            self._post_data(register_number='XYZ999', position='Flutter Intern'),
        )
        cert.refresh_from_db()
        self.assertEqual(cert.register_number, 'XYZ999')
        self.assertEqual(cert.position, 'Flutter Intern')

    def test_created_certificate_renders_both_new_placeholders(self):
        self.client.post(reverse('certificate_create'), self._post_data())
        html = Certificate.objects.get().render_body_html()
        self.assertIn('Reg. No.: BAI247966', html)
        self.assertIn('as a Python Developer Intern.', html)
        self.assertNotIn('{register_number}', html)


class CertificateWishTextTests(TestCase):
    def setUp(self):
        self.cert = Certificate(
            student_name='SABITHA P',
            gender='female',
            date_of_issuance=date(2025, 11, 5),
        )

    def test_wish_text_uses_object_pronoun_and_possessive(self):
        self.cert.wish_text = 'We wish {pronoun} success in {possessive} future.'
        self.assertEqual(self.cert.render_wish_text(), 'We wish her success in her future.')

    def test_wish_text_unknown_placeholder_does_not_break_render(self):
        self.cert.wish_text = 'We wish {pronoun} success, {bogus}.'
        self.assertEqual(self.cert.render_wish_text(), 'We wish her success, {bogus}.')
