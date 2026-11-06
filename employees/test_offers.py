"""Internship offer letters: HR writes the offer -> candidate accepts -> HR
approves -> candidate downloads the letter and moves on to enrolment."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from employees.models import Employee, InternOffer


def offer_data(**overrides):
    data = {
        'candidate_name': 'Anjali Menon', 'phone': '9876543210', 'email': '',
        'position': 'Flutter Developer Intern', 'department': 'software',
        'start_date': '2026-12-01', 'duration_months': '3', 'work_mode': 'onsite',
        'money_mode': 'stipend', 'amount': '3000', 'terms': 'Be on time.\nKeep secrets.',
        'is_student': 'on', 'institution_name': 'MES College', 'course': 'BCA',
        'year_of_study': '3', 'accept_days': '14',
    }
    data.update(overrides)
    return data


class OfferTests(TestCase):
    def setUp(self):
        self.hr = User.objects.create_superuser('boss', 'boss@example.com', 'pw-123456')
        self.client.force_login(self.hr)

    def create(self, **overrides):
        response = self.client.post(reverse('offer_new'), offer_data(**overrides))
        offer = InternOffer.objects.order_by('-created_at').first()
        self.assertRedirects(response, reverse('offer_detail', args=[offer.pk]))
        return offer

    def accept(self, offer, **overrides):
        data = {'decision': 'accept', 'signed_name': 'Anjali Menon', 'agree': 'on',
                'institution_name': 'MES College', 'course': 'BCA', 'year_of_study': '3'}
        data.update(overrides)
        return self.client.post(reverse('offer_view', args=[offer.token]), data)

    # ---- HR side ----
    def test_create_offer_sets_reference_and_fields(self):
        offer = self.create()
        self.assertTrue(offer.reference.startswith('RT/OFR/'))
        self.assertEqual(offer.position, 'Flutter Developer Intern')
        self.assertEqual(offer.institution_name, 'MES College')
        self.assertEqual(offer.duration_months, 3)
        self.assertEqual(str(offer.amount), '3000.00')
        self.assertIn('Stipend of', offer.money_label)
        page = self.client.get(reverse('offer_detail', args=[offer.pk]))
        self.assertContains(page, 'wa.me/919876543210')

    def test_paid_offer_needs_amount_and_free_ignores_it(self):
        response = self.client.post(reverse('offer_new'), offer_data(amount=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(InternOffer.objects.exists())
        offer = self.create(money_mode='none', amount='999')
        self.assertIsNone(offer.amount)
        self.assertEqual(offer.money_label, 'No fee and no stipend')

    def test_non_student_drops_college(self):
        offer = self.create(is_student='')
        self.assertFalse(offer.is_student)
        self.assertEqual(offer.institution_name, '')

    def test_interns_cannot_reach_hr_pages(self):
        user = User.objects.create_user('intern1', password='pw-123456')
        Employee.objects.create(user=user, employee_id='EMP900', employment_type='intern',
                                role='intern', joining_date=timezone.localdate())
        self.client.force_login(user)
        response = self.client.get(reverse('offer_list'))
        self.assertIn(response.status_code, (302, 403))

    # ---- Candidate side ----
    def test_candidate_sees_letter_without_login(self):
        offer = self.create()
        self.client.logout()
        page = self.client.get(reverse('offer_view', args=[offer.token]))
        self.assertContains(page, 'Offer of internship as Flutter Developer Intern')
        self.assertContains(page, 'MES College')
        offer.refresh_from_db()
        self.assertEqual(offer.status, InternOffer.STATUS_OPENED)

    def test_student_must_give_college_to_accept(self):
        offer = self.create(institution_name='', course='')
        self.client.logout()
        response = self.accept(offer, institution_name='', course='')
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Enter your college', status_code=400)
        offer.refresh_from_db()
        self.assertIn(offer.status, InternOffer.OPEN_STATUSES)

    def test_accept_then_approve_unlocks_download_and_enrolment(self):
        offer = self.create(institution_name='')
        self.client.logout()
        response = self.accept(offer, institution_name='Govt Polytechnic', course='Diploma CS')
        self.assertRedirects(response, reverse('offer_done', args=[offer.token]))
        offer.refresh_from_db()
        self.assertEqual(offer.status, InternOffer.STATUS_ACCEPTED)
        self.assertEqual(offer.institution_name, 'Govt Polytechnic')
        self.assertEqual(len(offer.body_hash), 64)

        # Not downloadable until HR approves.
        copy = self.client.get(reverse('offer_copy', args=[offer.token]))
        self.assertRedirects(copy, reverse('offer_done', args=[offer.token]))
        self.assertContains(self.client.get(reverse('offer_done', args=[offer.token])),
                            'awaiting approval')

        self.client.force_login(self.hr)
        self.client.post(reverse('offer_approve', args=[offer.pk]), {'create_enrolment': 'on'})
        offer.refresh_from_db()
        self.assertEqual(offer.status, InternOffer.STATUS_APPROVED)
        enrolment = offer.enrolment
        self.assertEqual(enrolment.college_name, 'Govt Polytechnic')
        self.assertEqual(enrolment.preferred_start_date.isoformat(), '2026-12-01')
        self.assertEqual(enrolment.invite_phone, '9876543210')
        detail = self.client.get(reverse('offer_detail', args=[offer.pk]))
        self.assertContains(detail, 'Send letter')

        self.client.logout()
        done = self.client.get(reverse('offer_done', args=[offer.token]))
        self.assertContains(done, 'Download offer letter')
        self.assertContains(done, enrolment.public_path())
        copy = self.client.get(reverse('offer_copy', args=[offer.token]))
        self.assertContains(copy, 'Accepted by the candidate')
        self.assertContains(copy, offer.body_hash)
        # The enrolment form arrives with the college already filled in.
        form = self.client.get(enrolment.public_path())
        self.assertContains(form, 'value="Govt Polytechnic"')

    def test_non_student_accepts_without_college(self):
        offer = self.create(is_student='')
        self.client.logout()
        response = self.accept(offer, institution_name='', course='')
        self.assertRedirects(response, reverse('offer_done', args=[offer.token]))

    def test_accept_needs_signature_and_tick(self):
        offer = self.create()
        self.client.logout()
        response = self.accept(offer, signed_name='', agree='')
        self.assertEqual(response.status_code, 400)

    def test_decline_records_reason(self):
        offer = self.create()
        self.client.logout()
        self.client.post(reverse('offer_view', args=[offer.token]),
                         {'decision': 'decline', 'decline_reason': 'Got another offer'})
        offer.refresh_from_db()
        self.assertEqual(offer.status, InternOffer.STATUS_DECLINED)
        self.assertEqual(offer.decline_reason, 'Got another offer')
        self.client.force_login(self.hr)
        response = self.client.post(reverse('offer_approve', args=[offer.pk]))
        offer.refresh_from_db()
        self.assertEqual(offer.status, InternOffer.STATUS_DECLINED)

    def test_expired_and_withdrawn_links_do_not_open(self):
        offer = self.create()
        InternOffer.objects.filter(pk=offer.pk).update(expires_at=timezone.now() - timedelta(days=1))
        self.client.logout()
        self.assertContains(self.client.get(reverse('offer_view', args=[offer.token])), 'expired')
        self.client.force_login(self.hr)
        self.client.post(reverse('offer_cancel', args=[offer.pk]))
        self.client.logout()
        self.assertContains(self.client.get(reverse('offer_view', args=[offer.token])), 'withdrawn')

    def test_cannot_edit_after_answer(self):
        offer = self.create()
        self.client.logout()
        self.accept(offer)
        self.client.force_login(self.hr)
        response = self.client.post(reverse('offer_edit', args=[offer.pk]), offer_data(position='CEO'))
        self.assertRedirects(response, reverse('offer_detail', args=[offer.pk]))
        offer.refresh_from_db()
        self.assertEqual(offer.position, 'Flutter Developer Intern')

    def test_end_date(self):
        offer = self.create(start_date='2026-11-30', duration_months='3')
        self.assertEqual(offer.end_date.isoformat(), '2027-02-27')
