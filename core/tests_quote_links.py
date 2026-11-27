from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Client, Quote, QuoteItem
from .quote_link_models import QuoteLink

PNG = ('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
       '+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')


class QuoteLinkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('ql_admin', 'q@example.com', 'pw')
        cls.client_obj = Client.objects.create(name='Arun Kumar', company_name='Arun Traders',
                                               phone='9876543210', email='arun@example.com')

    def setUp(self):
        self.quote = Quote.objects.create(
            client=self.client_obj, title='Shop billing app', valid_until=timezone.localdate() + timedelta(days=15),
            subtotal=Decimal('50000'), tax_rate=Decimal('18'), total_amount=Decimal('59000'),
            terms='Advance 50%.')
        QuoteItem.objects.create(quote=self.quote, description='Billing app', quantity=1,
                                 unit_price=Decimal('50000'), amount=Decimal('50000'))
        self.client.force_login(self.admin)

    def send(self, gst='1'):
        self.client.post(reverse('quote_send_link', args=[self.quote.pk]), {'with_gst': gst})
        return self.quote.links.first()

    def test_send_link_and_whatsapp_button(self):
        link = self.send()
        self.assertTrue(link.with_gst)
        page = self.client.get(reverse('quote_detail', args=[self.quote.pk]))
        self.assertContains(page, 'https://wa.me/919876543210?text=')
        self.assertContains(page, link.token)
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, 'sent')
        # A new link retires the old one.
        newer = self.send()
        link.refresh_from_db()
        self.assertEqual(link.status, 'cancelled')
        self.client.logout()
        self.assertContains(self.client.get(reverse('quote_public', args=[link.token])), 'no longer active')
        self.assertContains(self.client.get(reverse('quote_public', args=[newer.token])), 'Shop billing app')

    def test_client_views_and_accepts_without_login(self):
        link = self.send()
        self.client.logout()
        page = self.client.get(reverse('quote_public', args=[link.token]))
        self.assertContains(page, 'Accept &amp; sign quotation')
        self.assertContains(page, '59,000')                 # with GST total
        link.refresh_from_db()
        self.assertEqual(link.status, 'viewed')

        bad = self.client.post(reverse('quote_public', args=[link.token]), {'decision': 'accept', 'signer_name': 'Arun'})
        self.assertEqual(bad.status_code, 400)

        self.client.post(reverse('quote_public', args=[link.token]), {
            'decision': 'accept', 'signer_name': 'Arun Kumar', 'signer_designation': 'Owner',
            'signed_name': 'Arun Kumar', 'agreed': 'on', 'signature_data': PNG})
        link.refresh_from_db()
        self.quote.refresh_from_db()
        self.assertEqual(link.status, 'accepted')
        self.assertEqual(self.quote.status, 'accepted')
        self.assertTrue(link.signature_image)
        self.assertEqual(link.snapshot['total'], '59000.00')
        self.assertEqual(len(link.body_hash), 64)
        done = self.client.get(reverse('quote_public', args=[link.token]))
        self.assertContains(done, 'Thank you, Arun Kumar')
        self.assertContains(done, 'Download signed copy')
        # It can't be answered twice.
        self.client.post(reverse('quote_public', args=[link.token]), {
            'decision': 'changes', 'signer_name': 'X', 'change_notes': 'cheaper'})
        link.refresh_from_db()
        self.assertEqual(link.status, 'accepted')

        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('quote_detail', args=[self.quote.pk])), 'Accepted by Arun Kumar')

    def test_request_changes(self):
        link = self.send('0')
        self.client.logout()
        self.client.post(reverse('quote_public', args=[link.token]), {
            'decision': 'changes', 'signer_name': 'Arun', 'change_notes': 'Please add a mobile app'})
        link.refresh_from_db()
        self.assertEqual(link.status, 'changes')
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('quote_detail', args=[self.quote.pk])), 'Please add a mobile app')

    def test_expired_and_unknown(self):
        link = self.send()
        self.quote.valid_until = timezone.localdate() - timedelta(days=1)
        self.quote.save()
        self.client.logout()
        self.assertContains(self.client.get(reverse('quote_public', args=[link.token])), 'expired')
        self.assertEqual(self.client.get(reverse('quote_public', args=['nope'])).status_code, 404)

    def test_staff_login_confined_users_can_open_link(self):
        """Interns/clients logged in on the same phone are not bounced away."""
        from employees.middleware import OPEN_PREFIXES
        from client_portal.middleware import OPEN_PREFIXES as CP
        self.assertTrue(reverse('quote_public', args=['x']).startswith(OPEN_PREFIXES))
        self.assertTrue(reverse('quote_public', args=['x']).startswith(CP))


class QuoteAddonTests(TestCase):
    """Optional add-ons: not in the total, picked by the client on the link,
    and only picked ones are billed when the quote becomes an invoice."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('qa_admin', 'qa@example.com', 'pw')
        cls.client_obj = Client.objects.create(name='Jabir', company_name='Jabir Homes', phone='9876500000')

    def setUp(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('quote_create'), {
            'client': self.client_obj.pk, 'title': 'Property website', 'valid_until': (timezone.localdate() + timedelta(days=15)).isoformat(),
            'tax_rate': '18', 'discount': '0', 'payment_terms': '50-50', 'status': 'draft', 'item_count': '3',
            'item_description_1': 'Property website', 'item_details_1': 'mobile-friendly, map search',
            'item_quantity_1': '1', 'item_price_1': '45000',
            'item_description_2': 'Website AI chat', 'item_optional_2': '1', 'item_quantity_2': '1', 'item_price_2': '6000',
            'item_description_3': 'AI voice agent', 'item_optional_3': '1', 'item_quantity_3': '1', 'item_price_3': '10000',
        })
        self.quote = Quote.objects.get(title='Property website')

    def test_form_saves_details_and_addons_outside_total(self):
        items = list(self.quote.items.all())
        self.assertEqual([i.is_optional for i in items], [False, True, True])
        self.assertEqual(items[0].details, 'mobile-friendly, map search')
        self.assertEqual(self.quote.subtotal, Decimal('45000'))
        self.assertEqual(self.quote.total_amount, Decimal('53100'))

    def test_pdf_preview_shows_addons_and_words(self):
        page = self.client.get(reverse('quote_pdf', args=[self.quote.pk]) + '?gst=1')
        self.assertContains(page, 'Optional add-ons')
        self.assertContains(page, 'Core package + both add-ons')
        self.assertContains(page, '71,980.00')                      # 61,000 + 18%
        self.assertContains(page, 'Rupees Fifty Three Thousand One Hundred only')

    def test_client_picks_addon_and_invoice_bills_it(self):
        self.client.post(reverse('quote_send_link', args=[self.quote.pk]), {'with_gst': '1'})
        link = self.quote.links.first()
        chat = self.quote.items.get(description='Website AI chat')
        self.client.logout()
        self.assertContains(self.client.get(reverse('quote_public', args=[link.token])), 'Add-ons you want')
        self.client.post(reverse('quote_public', args=[link.token]), {
            'decision': 'accept', 'signer_name': 'Jabir', 'signed_name': 'Jabir', 'agreed': 'on',
            'addons': [str(chat.pk), 'not-an-addon']})
        link.refresh_from_db()
        self.assertEqual(link.snapshot['chosen_addons'], [str(chat.pk)])
        self.assertEqual(link.snapshot['accepted_total'], '60180.00')   # 53,100 + 7,080
        self.assertContains(self.client.get(reverse('quote_public', args=[link.token])), '60,180.00')

        self.client.force_login(self.admin)
        self.client.get(reverse('quote_convert', args=[self.quote.pk]))
        from .models import Invoice
        inv = Invoice.all_objects.get(quote=self.quote)
        self.assertEqual(sorted(i.description for i in inv.items.all()), ['Property website', 'Website AI chat'])
        self.assertEqual(inv.subtotal, Decimal('51000'))
