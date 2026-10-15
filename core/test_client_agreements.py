from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.client_agreement_models import ClientAgreement, _money, parse_milestones
from core.models import Client, Project


class MilestoneParsingTests(TestCase):
    def test_amounts_follow_percentages(self):
        rows = parse_milestones('Advance | 40\nUAT | 40\nGo-live | 20', Decimal('125000'))
        self.assertEqual([r['amount'] for r in rows], ['50000', '50000', '25000'])
        self.assertEqual(rows[0]['amount_display'], '₹50,000')

    def test_lines_without_percent_share_the_rest(self):
        rows = parse_milestones('Advance | 50\nPhase 2\nPhase 3', Decimal('1000'))
        self.assertEqual([r['percent'] for r in rows], ['50', '25', '25'])

    def test_indian_grouping(self):
        self.assertEqual(_money(Decimal('306950')), '₹3,06,950')
        self.assertEqual(_money(Decimal('12500000.5')), '₹1,25,00,000.50')


class ClientAgreementFlowTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.client_rec = Client.objects.create(name='Anil Kumar', company_name='Anil Traders',
                                                email='anil@example.com', phone='9876543210')
        self.project = Project.objects.create(
            client=self.client_rec, name='Billing App', description='A billing web app.',
            deliverables='Admin panel\nBilling module', final_amount=Decimal('125000'),
            start_date=date(2026, 10, 20), deadline=date(2026, 12, 20), warranty_period=3)
        self.client.force_login(self.staff)

    def _create(self, **overrides):
        data = {
            'scope': 'Build the billing app.', 'deliverables': 'Admin panel\nBilling module',
            'start_date': '2026-10-20', 'end_date': '2026-12-20', 'total': '125000',
            'milestones': 'Advance | 40\nUAT | 40\nGo-live | 20', 'warranty_months': '3',
            'support_note': '', 'extra_terms': '', 'expiry_days': '14',
        }
        data.update(overrides)
        return self.client.post(reverse('client_agreement_new', args=[self.project.pk]), data)

    def test_form_prefills_from_project(self):
        res = self.client.get(reverse('client_agreement_new', args=[self.project.pk]))
        self.assertContains(res, 'A billing web app.')
        self.assertContains(res, '125000')

    def test_create_freezes_snapshot(self):
        res = self._create()
        agreement = ClientAgreement.objects.get()
        self.assertRedirects(res, reverse('client_agreement_detail', args=[agreement.pk]))
        self.assertTrue(agreement.reference.startswith('RT/CA/'))
        self.assertEqual(agreement.snapshot_json['total_display'], '₹1,25,000')
        self.assertEqual(len(agreement.snapshot_json['milestones']), 3)
        self.assertIn('wa.me/919876543210', agreement.whatsapp_url())

    def test_milestones_must_total_100(self):
        res = self._create(milestones='Advance | 40\nUAT | 40')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'must add up to 100%')
        self.assertFalse(ClientAgreement.objects.exists())

    def test_client_accepts_without_login(self):
        self._create()
        agreement = ClientAgreement.objects.get()
        self.client.logout()
        url = agreement.public_path()
        res = self.client.get(url)
        self.assertContains(res, 'Project Service Agreement')
        self.assertContains(res, '₹50,000')
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, ClientAgreement.STATUS_VIEWED)

        res = self.client.post(url, {'decision': 'accept', 'signer_name': 'Anil Kumar',
                                     'signed_name': 'Anil Kumar', 'agreed_to_terms': 'on'})
        self.assertRedirects(res, f'{url}done/')
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, ClientAgreement.STATUS_ACCEPTED)
        self.assertEqual(len(agreement.body_hash), 64)
        # Answered links can't be re-signed; they go to the receipt.
        self.assertRedirects(self.client.get(url), f'{url}done/')
        self.assertContains(self.client.get(f'{url}copy/'), 'Accepted &amp; signed')

    def test_accept_requires_signature_and_consent(self):
        self._create()
        agreement = ClientAgreement.objects.get()
        res = self.client.post(agreement.public_path(), {'decision': 'accept', 'signer_name': 'A'})
        self.assertEqual(res.status_code, 400)
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, ClientAgreement.STATUS_PENDING)

    def test_change_request_then_revision_supersedes(self):
        self._create()
        first = ClientAgreement.objects.get()
        self.client.post(first.public_path(), {'decision': 'changes', 'signer_name': 'Anil',
                                               'change_notes': 'Split the advance in two.'})
        first.refresh_from_db()
        self.assertEqual(first.status, ClientAgreement.STATUS_CHANGES)

        res = self.client.get(reverse('client_agreement_new', args=[self.project.pk]))
        self.assertContains(res, 'Split the advance in two.')
        self._create(milestones='Advance 1 | 20\nAdvance 2 | 20\nUAT | 40\nGo-live | 20')
        second = ClientAgreement.objects.exclude(pk=first.pk).get()
        first.refresh_from_db()
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.snapshot_json['version'], 'v2.0')
        self.assertEqual(first.status, ClientAgreement.STATUS_SUPERSEDED)
        self.assertContains(self.client.get(first.public_path()), 'A newer version was sent')

    def test_expired_and_cancelled_links_close(self):
        self._create()
        agreement = ClientAgreement.objects.get()
        agreement.expires_at = timezone.now() - timedelta(days=1)
        agreement.save()
        self.assertContains(self.client.get(agreement.public_path()), 'This link has expired')

        agreement.expires_at = timezone.now() + timedelta(days=1)
        agreement.save()
        self.client.post(reverse('client_agreement_cancel', args=[agreement.pk]))
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, ClientAgreement.STATUS_CANCELLED)
        self.assertContains(self.client.get(agreement.public_path()), 'no longer active')

    def test_project_page_links_to_agreement(self):
        res = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(res, reverse('client_agreement_new', args=[self.project.pk]))
        self._create()
        agreement = ClientAgreement.objects.get()
        res = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(res, reverse('client_agreement_detail', args=[agreement.pk]))

    def test_staff_pages_need_login(self):
        self.client.logout()
        res = self.client.get(reverse('client_agreement_new', args=[self.project.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertIn('login', res['Location'])


class ClientAgreementServicesTests(ClientAgreementFlowTests):
    """Exclusions and recurring services (maintenance, cloud, AMC, other)."""

    SERVICES = {
        'exclusions': 'Domain registration\nContent writing',
        'maint_on': 'on', 'maint_amount': '2500', 'maint_mode': 'optional',
        'cloud_on': 'on', 'cloud_mode': 'required',
        'cloud_plans': 'Basic | 999 | 2 GB RAM\nStandard | 1,999 | 4 GB RAM',
        'amc_on': 'on', 'amc_amount': '15000', 'amc_cycle': 'yearly', 'amc_mode': 'included',
        'other_services': 'SEO package | 5000 | monthly | optional',
    }

    def test_snapshot_carries_exclusions_and_services(self):
        self._create(**self.SERVICES)
        doc = ClientAgreement.objects.get().snapshot_json
        titles = [s['title'] for s in doc['sections']]
        self.assertIn('Exclusions', titles)
        self.assertIn('Recurring Services & Charges', titles)
        self.assertEqual([s['key'] for s in doc['services']],
                         ['maint', 'cloud-1', 'cloud-2', 'amc', 'other-1'])
        self.assertEqual(doc['services'][2]['amount_display'], '₹1,999')
        self.assertEqual(doc['cloud_mode'], 'required')

    def test_bad_service_lines_are_rejected(self):
        res = self._create(maint_on='on', maint_amount='', cloud_on='on', cloud_plans='Basic')
        self.assertContains(res, 'Enter the monthly maintenance charge.')
        self.assertContains(res, 'needs a name and a monthly price')
        self.assertFalse(ClientAgreement.objects.exists())

    def test_client_choices_are_recorded(self):
        self._create(**self.SERVICES)
        agreement = ClientAgreement.objects.get()
        self.client.logout()
        url = agreement.public_path()
        self.assertContains(self.client.get(url), 'Add Monthly Maintenance')
        base = {'decision': 'accept', 'signer_name': 'Anil', 'signed_name': 'Anil',
                'agreed_to_terms': 'on', 'svc': ['maint']}
        # Cloud is required here, so accepting without a plan is refused.
        res = self.client.post(url, base)
        self.assertContains(res, 'Please choose a cloud hosting plan.', status_code=400)

        self.client.post(url, {**base, 'cloud_plan': 'cloud-2', 'svc': ['maint', 'amc', 'bogus']})
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, ClientAgreement.STATUS_ACCEPTED)
        # AMC is included regardless; the unknown key is dropped; SEO wasn't picked.
        self.assertEqual(agreement.selected_services, ['amc', 'maint', 'cloud-2'])
        self.assertEqual(agreement.chosen_monthly_total, '₹4,499')
        self.assertContains(self.client.get(f'{url}done/'), 'Standard')

    def test_optional_cloud_can_be_declined(self):
        self._create(**{**self.SERVICES, 'cloud_mode': 'optional'})
        agreement = ClientAgreement.objects.get()
        self.client.post(agreement.public_path(), {
            'decision': 'accept', 'signer_name': 'A', 'signed_name': 'A',
            'agreed_to_terms': 'on', 'cloud_plan': ''})
        agreement.refresh_from_db()
        self.assertEqual(agreement.selected_services, ['amc'])
