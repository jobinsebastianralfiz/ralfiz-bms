"""Tests for agreement e-signing: the public link, and the HR screens."""
import base64
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from employees.models import AgreementRequest, AgreementTemplate, Employee

# Smallest valid PNG, used as a stand-in for a drawn signature.
PNG_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)
SIGNATURE_DATA_URL = 'data:image/png;base64,' + base64.b64encode(PNG_BYTES).decode()


class AgreementTestBase(TestCase):
    def setUp(self):
        self.template = AgreementTemplate.objects.create(
            name='Internship Continuation & Learning Agreement',
            version='v1.0',
            heading='Internship Continuation & Learning Agreement',
            intro_html='Dear Intern,\nPlease confirm.',
            sections=[
                {'no': 1, 'title': 'Internship Continuation', 'body': 'I confirm:'},
                {'no': 2, 'title': 'Monthly Internship Fee', 'show_fee': True,
                 'body': 'The fee supports guidance, including:',
                 'bullets': ['Mentorship'],
                 'title_free': 'Learning Support & Guidance',
                 'body_free': 'This internship carries no monthly fee.'},
                {'no': 9, 'title': 'Completion & Continuation',
                 'bullets': ['Regular attendance', 'Timely payment of the applicable monthly fee'],
                 'bullets_free': ['Regular attendance']},
            ],
            monthly_fee=Decimal('750.00'),
            fee_in_words='Rupees Seven Hundred and Fifty only',
            confirmation_html='By selecting Continue, I agree to pay the monthly fee.',
            confirmation_free_html='By selecting Continue, I agree to the terms.',
        )
        self.intern = self._make_employee('intern1', 'EMP900', 'intern', phone='9895663498')
        self.staff = self._make_employee('staff1', 'EMP901', 'fulltime')

    def _make_employee(self, username, emp_id, employment_type, phone=''):
        user = User.objects.create_user(username, first_name='Test', last_name=username)
        return Employee.objects.create(
            user=user, employee_id=emp_id, employment_type=employment_type,
            role='intern' if employment_type == 'intern' else 'employee',
            phone=phone, status='active',
        )

    def _make_request(self, employee=None, **kwargs):
        employee = employee or self.intern
        return AgreementRequest.objects.create(
            employee=employee,
            template=self.template,
            snapshot_json=self.template.build_snapshot(),
            snapshot_version=self.template.version,
            snapshot_fee=self.template.monthly_fee,
            **kwargs
        )

    def _continue_payload(self, **overrides):
        payload = {
            'decision': 'continue',
            'full_name': 'Test Intern',
            'college_name': 'MES College',
            'course_department': 'BCA',
            'internship_domain': 'Digital Marketing',
            'signed_name': 'Test Intern',
            'agreed_to_terms': 'on',
        }
        payload.update(overrides)
        return payload


class PublicSigningTests(AgreementTestBase):
    def test_opening_the_link_marks_it_viewed(self):
        agreement = self._make_request()
        response = self.client.get(agreement.public_path())

        agreement.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(agreement.status, AgreementRequest.STATUS_VIEWED)
        self.assertEqual(agreement.view_count, 1)
        self.assertIsNotNone(agreement.first_viewed_at)

    def test_page_renders_the_snapshot_not_the_live_template(self):
        agreement = self._make_request()
        self.template.monthly_fee = Decimal('9999.00')
        self.template.save()

        body = self.client.get(agreement.public_path()).content.decode()
        self.assertIn('750', body)
        self.assertNotIn('9999', body)

    def test_continue_records_the_decision(self):
        agreement = self._make_request()
        self.client.post(agreement.public_path(), self._continue_payload())

        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementRequest.STATUS_ACCEPTED)
        self.assertEqual(agreement.decision, 'continue')
        self.assertEqual(agreement.college_name, 'MES College')
        self.assertTrue(agreement.agreed_to_terms)
        self.assertTrue(agreement.body_hash)
        self.assertIsNotNone(agreement.responded_at)

    def test_drawn_signature_is_stored(self):
        agreement = self._make_request()
        self.client.post(agreement.public_path(),
                         self._continue_payload(signature_data=SIGNATURE_DATA_URL))

        agreement.refresh_from_db()
        self.assertTrue(agreement.signature_image)

    def test_corrupt_signature_is_dropped_but_submission_succeeds(self):
        """A bad canvas payload must never cost someone their submission."""
        agreement = self._make_request()
        self.client.post(agreement.public_path(),
                         self._continue_payload(signature_data='data:image/png;base64,!!not-base64'))

        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementRequest.STATUS_ACCEPTED)
        self.assertFalse(agreement.signature_image)

    def test_non_png_signature_payload_is_rejected(self):
        agreement = self._make_request()
        gif = 'data:image/png;base64,' + base64.b64encode(b'GIF89a-not-a-png').decode()
        self.client.post(agreement.public_path(), self._continue_payload(signature_data=gif))

        agreement.refresh_from_db()
        self.assertFalse(agreement.signature_image)

    def test_missing_required_fields_re_renders_with_errors(self):
        agreement = self._make_request()
        response = self.client.post(agreement.public_path(),
                                    self._continue_payload(signed_name='', agreed_to_terms=''))

        agreement.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(agreement.status, AgreementRequest.STATUS_ACCEPTED)

    def test_intern_must_supply_college_fields(self):
        agreement = self._make_request()
        response = self.client.post(agreement.public_path(),
                                    self._continue_payload(college_name=''))

        agreement.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(agreement.status, AgreementRequest.STATUS_ACCEPTED)

    def test_staff_do_not_need_college_fields(self):
        agreement = self._make_request(employee=self.staff)
        self.assertFalse(agreement.asks_college_fields)

        self.client.post(agreement.public_path(), {
            'decision': 'continue', 'full_name': 'Staff Person',
            'signed_name': 'Staff Person', 'agreed_to_terms': 'on',
        })

        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementRequest.STATUS_ACCEPTED)

    def test_discontinue_records_the_reason(self):
        agreement = self._make_request()
        self.client.post(agreement.public_path(),
                         {'decision': 'discontinue', 'decline_reason': 'Exams'})

        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementRequest.STATUS_DECLINED)
        self.assertEqual(agreement.decline_reason, 'Exams')

    def test_a_decision_cannot_be_changed(self):
        agreement = self._make_request()
        self.client.post(agreement.public_path(), self._continue_payload())
        self.client.post(agreement.public_path(), {'decision': 'discontinue'})

        agreement.refresh_from_db()
        self.assertEqual(agreement.decision, 'continue')

    def test_revisiting_after_signing_shows_the_receipt(self):
        agreement = self._make_request()
        self.client.post(agreement.public_path(), self._continue_payload())

        response = self.client.get(agreement.public_path(), follow=True)
        self.assertContains(response, agreement.reference)
        self.assertNotContains(response, 'Continuation Decision')

    def test_expired_link_cannot_be_signed(self):
        agreement = self._make_request(expires_at=timezone.now() - timedelta(days=1))
        self.assertTrue(agreement.is_expired)

        response = self.client.get(agreement.public_path())
        self.assertContains(response, 'expired')

        self.client.post(agreement.public_path(), self._continue_payload())
        agreement.refresh_from_db()
        self.assertNotEqual(agreement.status, AgreementRequest.STATUS_ACCEPTED)

    def test_cancelled_link_cannot_be_signed(self):
        agreement = self._make_request(status=AgreementRequest.STATUS_CANCELLED)

        self.client.post(agreement.public_path(), self._continue_payload())
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementRequest.STATUS_CANCELLED)

    def test_unknown_token_is_404(self):
        self.assertEqual(self.client.get('/agreement/nope/').status_code, 404)

    def test_whatsapp_link_adds_country_code(self):
        agreement = self._make_request()
        self.assertTrue(agreement.whatsapp_url().startswith('https://wa.me/919895663498'))

    def test_whatsapp_link_is_empty_without_a_phone(self):
        agreement = self._make_request(employee=self.staff)
        self.assertEqual(agreement.whatsapp_url(), '')

    def test_references_are_sequential(self):
        first = self._make_request()
        second = self._make_request()
        self.assertNotEqual(first.reference, second.reference)
        self.assertTrue(second.reference.startswith('RT/AGR/'))


class HRScreenTests(AgreementTestBase):
    def setUp(self):
        super().setUp()
        self.hr = User.objects.create_superuser('hr', 'hr@example.com', 'pw')
        self.client.force_login(self.hr)

    def test_screens_require_login(self):
        self.client.logout()
        for url in ['/hr/agreements/', '/hr/agreements/send/']:
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_send_generates_one_link_per_person(self):
        response = self.client.post('/hr/agreements/send/', {
            'template': str(self.template.id), 'expiry_days': '30',
            'employees': [str(self.intern.id), str(self.staff.id)],
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AgreementRequest.objects.count(), 2)
        created = AgreementRequest.objects.first()
        self.assertEqual(created.sent_by, self.hr)
        self.assertEqual(created.snapshot_fee, self.template.monthly_fee)

    def test_sending_again_supersedes_an_open_link(self):
        old = self._make_request()
        self.client.post('/hr/agreements/send/', {
            'template': str(self.template.id), 'employees': [str(self.intern.id)],
        })

        old.refresh_from_db()
        self.assertEqual(old.status, AgreementRequest.STATUS_SUPERSEDED)

    def test_sending_again_does_not_disturb_a_signed_record(self):
        signed = self._make_request()
        self.client.post(signed.public_path(), self._continue_payload())

        self.client.post('/hr/agreements/send/', {
            'template': str(self.template.id), 'employees': [str(self.intern.id)],
        })

        signed.refresh_from_db()
        self.assertEqual(signed.status, AgreementRequest.STATUS_ACCEPTED)

    def test_send_with_no_selection_creates_nothing(self):
        self.client.post('/hr/agreements/send/', {'template': str(self.template.id),
                                                  'employees': []}, follow=True)
        self.assertEqual(AgreementRequest.objects.count(), 0)

    def test_cancel_closes_an_open_link(self):
        agreement = self._make_request()
        self.client.post(f'/hr/agreements/{agreement.pk}/cancel/')

        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementRequest.STATUS_CANCELLED)

    def test_cancel_is_refused_once_signed(self):
        agreement = self._make_request()
        self.client.post(agreement.public_path(), self._continue_payload())

        self.client.post(f'/hr/agreements/{agreement.pk}/cancel/')
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementRequest.STATUS_ACCEPTED)

    def test_resend_keeps_the_signed_record(self):
        agreement = self._make_request()
        self.client.post(agreement.public_path(), self._continue_payload())

        self.client.post(f'/hr/agreements/{agreement.pk}/resend/')

        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementRequest.STATUS_ACCEPTED)
        self.assertEqual(AgreementRequest.objects.filter(employee=self.intern).count(), 2)

    def test_detail_renders_without_a_sender(self):
        """Records created outside the HR screen have no sent_by."""
        agreement = self._make_request()
        response = self.client.get(f'/hr/agreements/{agreement.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_counters(self):
        accepted = self._make_request()
        self.client.post(accepted.public_path(), self._continue_payload())
        declined = self._make_request()
        self.client.post(declined.public_path(), {'decision': 'discontinue'})
        self._make_request(expires_at=timezone.now() - timedelta(days=1))
        self._make_request()

        counters = self.client.get('/hr/agreements/').context['counters']
        self.assertEqual(counters['accepted'], 1)
        self.assertEqual(counters['declined'], 1)
        self.assertEqual(counters['expired'], 1)
        self.assertEqual(counters['awaiting'], 1)

    def test_list_filters_and_search(self):
        agreement = self._make_request()
        for query in ['?status=open', '?status=accepted', '?status=expired',
                      f'?q={agreement.employee.employee_id}']:
            self.assertEqual(self.client.get(f'/hr/agreements/{query}').status_code, 200)


class SignedCopyTests(AgreementTestBase):
    def _sign(self, **overrides):
        agreement = self._make_request()
        self.client.post(agreement.public_path(), self._continue_payload(**overrides))
        agreement.refresh_from_db()
        return agreement

    def test_copy_is_only_available_after_signing(self):
        agreement = self._make_request()
        response = self.client.get(f'/agreement/{agreement.token}/copy/', follow=True)
        self.assertContains(response, 'Continuation Decision')

    def test_copy_shows_the_completed_form(self):
        agreement = self._sign()
        response = self.client.get(f'/agreement/{agreement.token}/copy/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, agreement.reference)
        self.assertContains(response, 'MES College')
        self.assertContains(response, 'Electronic signature record')
        self.assertContains(response, agreement.body_hash)

    def test_copy_shows_the_decline_decision(self):
        agreement = self._make_request()
        self.client.post(agreement.public_path(),
                         {'decision': 'discontinue', 'decline_reason': 'Exams'})

        response = self.client.get(f'/agreement/{agreement.token}/copy/')
        self.assertContains(response, 'discontinued')
        self.assertContains(response, 'Exams')

    def test_copy_renders_the_snapshot_not_the_live_template(self):
        agreement = self._sign()
        self.template.monthly_fee = Decimal('4242.00')
        self.template.save()

        body = self.client.get(f'/agreement/{agreement.token}/copy/').content.decode()
        self.assertIn('750', body)
        self.assertNotIn('4242', body)

    def test_receipt_links_to_the_copy(self):
        agreement = self._sign()
        response = self.client.get(f'/agreement/{agreement.token}/done/')
        self.assertContains(response, f'/agreement/{agreement.token}/copy.pdf')

    def test_pdf_context_inlines_css_and_signature(self):
        """The PDF renderer has no HTTP session, so both must be embedded."""
        from employees.agreement_views import build_copy_context

        agreement = self._sign(signature_data=SIGNATURE_DATA_URL)
        context = build_copy_context(agreement, for_pdf=True)

        self.assertTrue(context['inline_css'])
        self.assertTrue(context['signature_src'].startswith('data:image/'))

    def test_html_copy_links_css_rather_than_inlining_it(self):
        agreement = self._sign()
        body = self.client.get(f'/agreement/{agreement.token}/copy/').content.decode()
        self.assertIn('css/agreement.css', body)

    def test_pdf_falls_back_to_html_when_rendering_is_unavailable(self):
        """A dev box without pango must still hand over the copy, not a 500."""
        from unittest import mock

        agreement = self._sign()
        with mock.patch('employees.agreement_views.render_agreement_pdf', return_value=None):
            response = self.client.get(f'/agreement/{agreement.token}/copy.pdf')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/copy/', response['Location'])

    def test_pdf_is_served_when_rendering_succeeds(self):
        from unittest import mock

        agreement = self._sign()
        with mock.patch('employees.agreement_views.render_agreement_pdf',
                        return_value=b'%PDF-1.7 fake'):
            response = self.client.get(f'/agreement/{agreement.token}/copy.pdf')

        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertIn('.pdf', response['Content-Disposition'])

    def test_pdf_filename_has_no_slashes(self):
        from employees.agreement_views import _pdf_filename

        agreement = self._sign()
        self.assertNotIn('/', _pdf_filename(agreement))

    def test_template_has_no_multiline_django_comments(self):
        """Multi-line {# #} comments render as visible page text."""
        import glob
        import re

        for path in glob.glob('templates/agreements/*.html'):
            source = open(path).read()
            for match in re.finditer(r'\{#', source):
                rest = source[match.start():]
                close, newline = rest.find('#}'), rest.find('\n')
                self.assertFalse(close == -1 or (newline != -1 and newline < close),
                                 f'multi-line {{# #}} comment in {path}')


class HRSignedCopyTests(AgreementTestBase):
    def setUp(self):
        super().setUp()
        self.hr = User.objects.create_superuser('hr2', 'hr2@example.com', 'pw')
        self.client.force_login(self.hr)

    def test_hr_pdf_requires_a_signed_record(self):
        agreement = self._make_request()
        response = self.client.get(f'/hr/agreements/{agreement.pk}/pdf/')
        self.assertEqual(response.status_code, 302)

    def test_hr_pdf_serves_the_document(self):
        from unittest import mock

        agreement = self._make_request()
        self.client.post(agreement.public_path(), self._continue_payload())

        with mock.patch('employees.agreement_views.render_agreement_pdf',
                        return_value=b'%PDF-1.7 fake'):
            response = self.client.get(f'/hr/agreements/{agreement.pk}/pdf/')

        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_hr_pdf_requires_login(self):
        self.client.logout()
        agreement = self._make_request()
        response = self.client.get(f'/hr/agreements/{agreement.pk}/pdf/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])


class FeeConfigurationTests(AgreementTestBase):
    """Interns are on different arrangements - some pay monthly, some are free."""

    def _make_with_fee(self, fee):
        return AgreementRequest.objects.create(
            employee=self.intern, template=self.template,
            snapshot_json=self.template.build_snapshot(fee_override=fee),
            snapshot_version=self.template.version,
            snapshot_fee=self.template.resolve_fee(fee),
        )

    def test_default_fee_comes_from_the_template(self):
        snapshot = self.template.build_snapshot()
        self.assertEqual(snapshot['monthly_fee'], '750.00')
        self.assertFalse(snapshot['is_free'])

    def test_custom_fee_regenerates_the_words(self):
        """A custom amount must never inherit the words for a different number."""
        snapshot = self.template.build_snapshot(fee_override=Decimal('500'))
        self.assertEqual(snapshot['monthly_fee'], '500')
        self.assertEqual(snapshot['fee_in_words'], 'Rupees Five Hundred only')
        self.assertNotIn('Seven Hundred', snapshot['fee_in_words'])

    def test_zero_and_none_both_mean_free(self):
        for value in (0, Decimal('0'), None, ''):
            snapshot = self.template.build_snapshot(fee_override=value)
            self.assertTrue(snapshot['is_free'], value)
            self.assertEqual(snapshot['monthly_fee'], '')
            self.assertEqual(snapshot['fee_in_words'], '')

    def test_free_swaps_the_fee_section_wording(self):
        snapshot = self.template.build_snapshot(fee_override=0)
        section = [s for s in snapshot['sections'] if s['no'] == 2][0]

        self.assertEqual(section['title'], 'Learning Support & Guidance')
        self.assertIn('no monthly fee', section['body'])
        self.assertFalse(section['show_fee'])

    def test_free_drops_the_fee_payment_condition(self):
        snapshot = self.template.build_snapshot(fee_override=0)
        section = [s for s in snapshot['sections'] if s['no'] == 9][0]
        self.assertNotIn('Timely payment of the applicable monthly fee', section['bullets'])

    def test_paid_keeps_the_fee_payment_condition(self):
        snapshot = self.template.build_snapshot()
        section = [s for s in snapshot['sections'] if s['no'] == 9][0]
        self.assertIn('Timely payment of the applicable monthly fee', section['bullets'])

    def test_free_uses_the_fee_free_confirmation(self):
        self.assertIn('agree to the terms',
                      self.template.build_snapshot(fee_override=0)['confirmation_html'])
        self.assertIn('pay the monthly fee',
                      self.template.build_snapshot()['confirmation_html'])

    def test_snapshot_never_leaks_the_free_variant_keys(self):
        for snapshot in (self.template.build_snapshot(), self.template.build_snapshot(fee_override=0)):
            for section in snapshot['sections']:
                for key in ('title_free', 'body_free', 'bullets_free'):
                    self.assertNotIn(key, section)

    def test_free_agreement_page_shows_no_fee(self):
        agreement = self._make_with_fee(0)
        body = self.client.get(agreement.public_path()).content.decode()

        self.assertIn('Learning Support', body)
        self.assertNotIn('750', body)
        self.assertNotIn('/ month', body)

    def test_paid_agreement_page_shows_the_fee(self):
        agreement = self._make_with_fee(Decimal('750'))
        body = self.client.get(agreement.public_path()).content.decode()
        self.assertIn('750', body)

    def test_free_signed_copy_says_no_fee(self):
        agreement = self._make_with_fee(0)
        self.client.post(agreement.public_path(), self._continue_payload())

        body = self.client.get(f'/agreement/{agreement.token}/copy/').content.decode()
        self.assertIn('no monthly fee', body)
        self.assertNotIn('750', body)

    def test_free_internship_does_not_break_the_template_default(self):
        """Sending someone a free agreement must not change the template."""
        self.template.build_snapshot(fee_override=0)
        self.template.refresh_from_db()
        self.assertEqual(self.template.monthly_fee, Decimal('750.00'))


class SendFeeTests(AgreementTestBase):
    def setUp(self):
        super().setUp()
        self.hr = User.objects.create_superuser('hr3', 'hr3@example.com', 'pw')
        self.client.force_login(self.hr)

    def _send(self, **extra):
        payload = {'template': str(self.template.id),
                   'employees': [str(self.intern.id), str(self.staff.id)]}
        payload.update(extra)
        return self.client.post('/hr/agreements/send/', payload)

    def test_batch_default_fee_applies_to_everyone(self):
        self._send(default_fee='500')
        for agreement in AgreementRequest.objects.all():
            self.assertEqual(agreement.snapshot_fee, Decimal('500'))

    def test_per_person_fee_overrides_the_batch_default(self):
        self._send(**{'default_fee': '750', f'fee_{self.intern.id}': '0'})

        free = AgreementRequest.objects.get(employee=self.intern)
        paid = AgreementRequest.objects.get(employee=self.staff)
        self.assertIsNone(free.snapshot_fee)
        self.assertTrue(free.snapshot_json['is_free'])
        self.assertEqual(paid.snapshot_fee, Decimal('750'))
        self.assertFalse(paid.snapshot_json['is_free'])

    def test_blank_fee_falls_back_to_the_template(self):
        self._send(default_fee='')
        for agreement in AgreementRequest.objects.all():
            self.assertEqual(agreement.snapshot_fee, Decimal('750.00'))

    def test_junk_fee_falls_back_rather_than_erroring(self):
        response = self._send(default_fee='abc')
        self.assertEqual(response.status_code, 302)
        for agreement in AgreementRequest.objects.all():
            self.assertEqual(agreement.snapshot_fee, Decimal('750.00'))

    def test_resend_keeps_the_persons_existing_fee(self):
        self._send(**{f'fee_{self.intern.id}': '0'})
        original = AgreementRequest.objects.get(employee=self.intern)

        self.client.post(f'/hr/agreements/{original.pk}/resend/')

        newest = AgreementRequest.objects.filter(employee=self.intern).order_by('-sent_at').first()
        self.assertNotEqual(newest.pk, original.pk)
        self.assertIsNone(newest.snapshot_fee)
        self.assertTrue(newest.snapshot_json['is_free'])

    def test_send_screen_offers_a_fee_box_per_person(self):
        body = self.client.get('/hr/agreements/send/?type=all').content.decode()
        self.assertIn(f'fee_{self.intern.id}', body)
        self.assertIn('name="default_fee"', body)


class CountersignatureTests(AgreementTestBase):
    """The "For Ralfiz Technologies" block on the signed copy."""

    def _sign(self):
        agreement = self._make_request()
        self.client.post(agreement.public_path(), self._continue_payload())
        agreement.refresh_from_db()
        return agreement

    def test_falls_back_to_the_bundled_certificate_assets(self):
        """So the block is never blank, even before anything is uploaded."""
        from employees.agreement_views import company_countersignature

        block = company_countersignature(for_pdf=False)
        self.assertIn('jobin_signature', block['signature_src'])
        self.assertIn('seal', block['seal_src'])

    def test_uploaded_signature_and_seal_win(self):
        from django.core.files.base import ContentFile

        from core.models import CompanySettings
        from employees.agreement_views import company_countersignature

        company = CompanySettings.get_settings()
        company.authorized_signature.save('sig.png', ContentFile(PNG_BYTES), save=False)
        company.company_seal.save('seal.png', ContentFile(PNG_BYTES), save=False)
        company.signatory_name = 'Jobin Sebastian'
        company.save()

        block = company_countersignature(for_pdf=False)
        self.assertIn('sig', block['signature_src'])
        self.assertEqual(block['signatory_name'], 'Jobin Sebastian')

    def test_pdf_embeds_the_images_rather_than_linking_them(self):
        from employees.agreement_views import company_countersignature

        block = company_countersignature(for_pdf=True)
        self.assertTrue(block['signature_src'].startswith('data:image/'))
        self.assertTrue(block['seal_src'].startswith('data:image/'))

    def test_signed_copy_shows_the_company_block(self):
        agreement = self._sign()
        response = self.client.get(f'/agreement/{agreement.token}/copy/')

        self.assertContains(response, 'For Ralfiz Technologies')
        self.assertContains(response, 'Authorized Representative')
        self.assertContains(response, 'Company seal')

    def test_missing_asset_degrades_to_an_empty_string(self):
        """A broken path must not blow up the signed copy."""
        from employees.agreement_views import _static_data_uri

        self.assertEqual(_static_data_uri('certificates/does-not-exist.png'), '')

class NewJoineeAgreementTests(TestCase):
    """A new joiner accepts an offer; they are not deciding whether to carry on."""

    def setUp(self):
        from django.core.management import call_command
        call_command('seed_new_joinee_agreement', verbosity=0)
        self.template = AgreementTemplate.objects.get(agreement_type='internship_new_joinee')

    def test_it_covers_every_area_the_document_has_to_state(self):
        titles = ' '.join(s['title'] for s in self.template.sections)
        for area in ['Internship Offer', 'Period & Renewal', 'Stipend',
                     'Company Policy', 'Confidentiality', 'Job Offer']:
            self.assertIn(area, titles, f'missing a section for {area}')

    def test_it_does_not_promise_employment(self):
        """A promise of a job would bind the company; the wording must stay conditional."""
        offer = next(s for s in self.template.sections if 'Job Offer' in s['title'])
        body = ' '.join(offer['bullets']) + ' ' + offer.get('footnote', '')
        self.assertIn('may be considered', body)
        self.assertIn('does not by itself create', body)
        self.assertNotIn('will be offered', body)

    def test_the_decision_wording_is_about_accepting_not_continuing(self):
        doc = self.template.build_snapshot()
        self.assertEqual(doc['decision_heading'], 'Internship Offer Decision')
        self.assertNotIn('continue', doc['accept_statement'].lower())
        self.assertNotIn('continue', doc['continue_label'].lower())

    def test_a_stipend_is_worded_as_paid_to_the_intern(self):
        doc = self.template.build_snapshot(fee_override=Decimal('8000'))
        self.assertEqual(doc['money_note'], 'Accepted on a monthly stipend of \u20b98000.')
        self.assertIn('stipend', doc['money_confirm_line'])

    def test_no_stipend_swaps_the_section_the_way_the_fee_one_does(self):
        doc = self.template.build_snapshot(fee_override=None, money_mode='stipend')
        section = next(s for s in doc['sections'] if s['no'] == 3)
        self.assertEqual(section['title'], 'Learning Support & Guidance')
        self.assertFalse(section.get('show_fee'))
        self.assertEqual(doc['money_note'],
                         'This internship carries no monthly fee and no stipend.')

    def test_seeding_twice_does_not_duplicate_or_clobber_hr_edits(self):
        from django.core.management import call_command
        self.template.heading = 'Edited by HR'
        self.template.save()
        call_command('seed_new_joinee_agreement', verbosity=0)
        self.template.refresh_from_db()
        self.assertEqual(self.template.heading, 'Edited by HR')
        self.assertEqual(
            AgreementTemplate.objects.filter(agreement_type='internship_new_joinee').count(), 1)

    def test_force_overwrites_when_asked(self):
        from django.core.management import call_command
        self.template.heading = 'Edited by HR'
        self.template.save()
        call_command('seed_new_joinee_agreement', '--force', verbosity=0)
        self.template.refresh_from_db()
        self.assertEqual(self.template.heading, 'Internship Agreement')

    def test_the_confirmation_block_follows_the_last_section(self):
        """It was pinned at 10 for the nine-section continuation agreement."""
        doc = self.template.build_snapshot()
        self.assertEqual(doc['confirmation_no'], len(doc['sections']) + 1)
        self.assertEqual(doc['confirmation_no'], 12)

    def test_the_decision_sublabels_do_not_talk_about_ending_participation(self):
        """A new joiner has not started, so they cannot 'end participation'."""
        doc = self.template.build_snapshot()
        self.assertNotIn('end participation', doc['decline_sub'])
        self.assertEqual(doc['accept_sub'], 'join Ralfiz Technologies as an intern')


class ContinuationWordingUnchangedTests(TestCase):
    """The continuation agreement must read exactly as it did before the
    decision wording became template copy."""

    def test_the_defaults_are_the_strings_that_used_to_be_hardcoded(self):
        t = AgreementTemplate(name='x', version='v1')
        self.assertEqual(t.decision_heading, 'Continuation Decision')
        self.assertEqual(t.accept_statement, 'I wish to continue my internship')
        self.assertEqual(t.decline_statement, 'I do not wish to continue my internship')
        self.assertEqual(t.decline_heading, 'Discontinue Internship')
        self.assertEqual(t.decline_button_label, 'Confirm discontinuation')

    def test_the_continuation_confirmation_is_still_numbered_ten(self):
        from django.core.management import call_command
        call_command('seed_internship_agreement', verbosity=0)
        t = AgreementTemplate.objects.get(agreement_type='internship_continuation')
        doc = t.build_snapshot()
        self.assertEqual(len(doc['sections']), 9)
        self.assertEqual(doc['confirmation_no'], 10)
        self.assertEqual(doc['accept_sub'], 'with Ralfiz Technologies')
        self.assertEqual(doc['decline_sub'], 'end participation in the program')


class MoneyArrangementTests(TestCase):
    """An internship runs one of three ways, and HR picks per person."""

    def setUp(self):
        from django.core.management import call_command
        call_command('seed_internship_agreement', '--force', verbosity=0)
        call_command('seed_new_joinee_agreement', '--force', verbosity=0)
        self.cont = AgreementTemplate.objects.get(agreement_type='internship_continuation')
        self.new = AgreementTemplate.objects.get(agreement_type='internship_new_joinee')

    def _money_section(self, doc):
        return next(s for s in doc['sections']
                    if s['title'] in ('Monthly Internship Fee', 'Monthly Stipend',
                                      'Learning Support & Guidance'))

    def test_either_template_can_carry_a_fee(self):
        for t in (self.cont, self.new):
            doc = t.build_snapshot(fee_override=Decimal('750'), money_mode='fee')
            self.assertEqual(self._money_section(doc)['title'], 'Monthly Internship Fee')
            self.assertIn('pay', doc['money_confirm_line'])
            self.assertEqual(doc['money_mode'], 'fee')

    def test_either_template_can_carry_a_stipend(self):
        for t in (self.cont, self.new):
            doc = t.build_snapshot(fee_override=Decimal('8000'), money_mode='stipend')
            self.assertEqual(self._money_section(doc)['title'], 'Monthly Stipend')
            self.assertIn('stipend', doc['money_confirm_line'])
            self.assertEqual(doc['money_mode'], 'stipend')

    def test_either_template_can_be_free(self):
        for t in (self.cont, self.new):
            doc = t.build_snapshot(fee_override=None, money_mode='none')
            self.assertEqual(self._money_section(doc)['title'], 'Learning Support & Guidance')
            self.assertEqual(doc['money_confirm_line'], '')
            self.assertEqual(doc['money_mode'], 'none')

    def test_a_stipend_of_zero_is_not_a_stipend(self):
        """An amount of nothing means free, whichever direction was picked."""
        for mode in ('fee', 'stipend'):
            doc = self.new.build_snapshot(fee_override=Decimal('0'), money_mode=mode)
            self.assertEqual(doc['money_mode'], 'none')
            self.assertTrue(doc['is_free'])
            self.assertEqual(doc['monthly_fee'], '')

    def test_the_amount_note_says_who_pays(self):
        fee = self.new.build_snapshot(fee_override=Decimal('750'), money_mode='fee')
        stipend = self.new.build_snapshot(fee_override=Decimal('8000'), money_mode='stipend')
        self.assertIn('by the intern', fee['fee_note'])
        self.assertIn('by Ralfiz Technologies', stipend['fee_note'])

    def test_an_unknown_mode_falls_back_rather_than_breaking_the_link(self):
        doc = self.new.build_snapshot(fee_override=Decimal('750'), money_mode='nonsense')
        self.assertEqual(doc['money_mode'], 'fee')

    def test_a_template_saved_before_money_copy_existed_still_renders(self):
        self.new.money_copy = {}
        self.new.save()
        doc = self.new.build_snapshot(fee_override=Decimal('8000'), money_mode='stipend')
        self.assertEqual(self._money_section(doc)['title'], 'Monthly Stipend')


class SendWithMixedArrangementsTests(TestCase):
    """One send, three people, three different money arrangements."""

    def setUp(self):
        from django.core.management import call_command
        call_command('seed_new_joinee_agreement', '--force', verbosity=0)
        self.template = AgreementTemplate.objects.get(agreement_type='internship_new_joinee')
        self.hr = User.objects.create_superuser('hr_mixed', 'hr@example.com', 'pw')
        self.people = []
        for i, name in enumerate(['payer', 'earner', 'freebie']):
            u = User.objects.create_user(f'mix_{name}', f'{name}@example.com', 'pw')
            self.people.append(Employee.objects.create(
                user=u, employee_id=f'MIX{i}', designation='Intern',
                employment_type='intern', status='active'))
        self.client.force_login(self.hr)

    def test_each_person_gets_the_arrangement_they_were_given(self):
        payer, earner, freebie = self.people
        resp = self.client.post(reverse('agreement_send'), {
            'employees': [str(p.id) for p in self.people],
            'template': str(self.template.id),
            'expiry_days': '14',
            'default_money_mode': 'stipend',
            'default_fee': '8000',
            f'money_mode_{payer.id}': 'fee',
            f'fee_{payer.id}': '750',
            f'money_mode_{freebie.id}': 'none',
            f'fee_{freebie.id}': '0',
        })
        self.assertEqual(resp.status_code, 302)

        got = {r.employee_id: r for r in AgreementRequest.objects.all()}
        self.assertEqual(len(got), 3)

        self.assertEqual(got[payer.id].snapshot_money_mode, 'fee')
        self.assertEqual(got[payer.id].snapshot_fee, Decimal('750'))
        self.assertIn('pay', got[payer.id].snapshot_json['money_confirm_line'])

        # This one took the batch default rather than a box of its own.
        self.assertEqual(got[earner.id].snapshot_money_mode, 'stipend')
        self.assertEqual(got[earner.id].snapshot_fee, Decimal('8000'))
        self.assertIn('stipend', got[earner.id].snapshot_json['money_confirm_line'])

        self.assertEqual(got[freebie.id].snapshot_money_mode, 'none')
        self.assertIsNone(got[freebie.id].snapshot_fee)
        self.assertEqual(got[freebie.id].snapshot_json['money_confirm_line'], '')

    def test_the_three_arrangements_do_not_share_one_snapshot(self):
        """Snapshots are cached per arrangement; caching on amount alone would
        hand a stipend signer the fee wording."""
        payer, earner, _ = self.people
        self.client.post(reverse('agreement_send'), {
            'employees': [str(payer.id), str(earner.id)],
            'template': str(self.template.id),
            'default_money_mode': 'fee',
            'default_fee': '750',
            f'money_mode_{earner.id}': 'stipend',
            f'fee_{earner.id}': '750',
        })
        got = {r.employee_id: r for r in AgreementRequest.objects.all()}
        self.assertEqual(got[payer.id].snapshot_fee, got[earner.id].snapshot_fee)
        self.assertNotEqual(got[payer.id].snapshot_json['money_note'],
                            got[earner.id].snapshot_json['money_note'])
