"""Quote payment terms (free text) and the logo embedded into PDFs."""
import base64
import io

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Client, CompanySettings, Quote


def png_bytes(colour=(90, 110, 250)):
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (24, 24), colour).save(buf, 'PNG')
    return buf.getvalue()


SVG_WITH_DOCTYPE = (
    b'<?xml version="1.0" standalone="no"?>\n'
    b'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
    b'"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
    b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
    b'<rect width="10" height="10" fill="red"/></svg>'
)


class PaymentTermsDisplayTests(TestCase):
    """payment_terms stores a code; templates must never print it raw."""

    def setUp(self):
        self.client_obj = Client.objects.create(name='Acme Ltd')

    def _quote(self, **kwargs):
        return Quote.objects.create(
            quote_number=f'Q-{Quote.objects.count() + 1:04d}',
            client=self.client_obj,
            title='Website build',
            valid_until=timezone.localdate(),
            **kwargs,
        )

    def test_preset_codes_render_as_readable_labels(self):
        cases = {
            '50-50': '50% Advance, 50% on Completion',
            '30-30-40': '30% Advance, 30% Mid-project, 40% on Completion',
            '100-advance': '100% Advance',
            '100-completion': '100% on Completion',
        }
        for code, label in cases.items():
            with self.subTest(code=code):
                q = self._quote(payment_terms=code)
                self.assertEqual(q.payment_terms_display, label)

    def test_custom_terms_are_used_verbatim(self):
        text = '40% on signing, 30% at design sign-off, 30% on handover'
        q = self._quote(payment_terms='custom', payment_terms_custom=text)
        self.assertEqual(q.payment_terms_display, text)

    def test_custom_terms_keep_their_line_breaks(self):
        text = 'Milestone 1 - 40%\nMilestone 2 - 30%\nHandover - 30%'
        q = self._quote(payment_terms='custom', payment_terms_custom=text)
        self.assertEqual(q.payment_terms_display, text)
        self.assertIn('\n', q.payment_terms_display)

    def test_custom_selected_but_left_blank_shows_nothing(self):
        """Better an absent section than the literal word 'custom'."""
        q = self._quote(payment_terms='custom', payment_terms_custom='   ')
        self.assertEqual(q.payment_terms_display, '')

    def test_unknown_code_falls_back_to_itself(self):
        q = self._quote(payment_terms='legacy-code')
        self.assertEqual(q.payment_terms_display, 'legacy-code')


class QuoteFormPaymentTermsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('boss', password='pw-12345', is_staff=True)
        self.client.login(username='boss', password='pw-12345')
        self.client_obj = Client.objects.create(name='Acme Ltd')

    def test_form_offers_a_custom_terms_box(self):
        res = self.client.get(reverse('quote_create'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'name="payment_terms_custom"')
        self.assertContains(res, 'id="payment_terms_custom_group"')

    def test_creating_a_quote_stores_the_custom_terms(self):
        res = self.client.post(reverse('quote_create'), {
            'client': str(self.client_obj.id),
            'title': 'Bespoke build',
            'valid_until': timezone.localdate().isoformat(),
            'payment_terms': 'custom',
            'payment_terms_custom': '60% upfront, 40% on delivery',
            'item_count': '1',
            'item_description_1': 'Design',
            'item_quantity_1': '1',
            'item_price_1': '1000',
        })
        self.assertIn(res.status_code, (302, 200))
        q = Quote.objects.filter(title='Bespoke build').first()
        self.assertIsNotNone(q, 'quote was not created')
        self.assertEqual(q.payment_terms, 'custom')
        self.assertEqual(q.payment_terms_custom, '60% upfront, 40% on delivery')
        self.assertEqual(q.payment_terms_display, '60% upfront, 40% on delivery')

    def test_editing_a_quote_updates_the_custom_terms(self):
        q = Quote.objects.create(
            quote_number='Q-9001', client=self.client_obj, title='Edit me',
            valid_until=timezone.localdate(),
            payment_terms='custom', payment_terms_custom='old text')
        self.client.post(reverse('quote_update', args=[q.pk]), {
            'client': str(self.client_obj.id),
            'title': 'Edit me',
            'issue_date': timezone.localdate().isoformat(),
            'valid_until': timezone.localdate().isoformat(),
            'payment_terms': 'custom',
            'payment_terms_custom': 'new text',
            'item_count': '1',
            'item_description_1': 'Design',
            'item_quantity_1': '1',
            'item_price_1': '1000',
        })
        q.refresh_from_db()
        self.assertEqual(q.payment_terms_custom, 'new text')

    def test_pdf_prints_the_payment_terms(self):
        """The default T&C says 'Payment terms as agreed above', so the PDF
        has to actually show them."""
        q = Quote.objects.create(
            quote_number='Q-9002', client=self.client_obj, title='PDF me',
            valid_until=timezone.localdate(), subtotal=Decimal('1000'),
            payment_terms='custom',
            payment_terms_custom='45% upfront, 55% on handover')
        html = render_to_string('quotes/pdf.html', {
            'quote': q, 'company': CompanySettings.get_settings(),
            'items': q.items.all(),
        })
        self.assertIn('Payment Terms', html)
        self.assertIn('45% upfront, 55% on handover', html)

    def test_pdf_omits_the_section_when_there_are_no_terms(self):
        q = Quote.objects.create(
            quote_number='Q-9003', client=self.client_obj, title='No terms',
            valid_until=timezone.localdate(), subtotal=Decimal('10'),
            payment_terms='custom', payment_terms_custom='')
        html = render_to_string('quotes/pdf.html', {
            'quote': q, 'company': CompanySettings.get_settings(),
            'items': q.items.all(),
        })
        self.assertNotIn('>Payment Terms<', html)


class CompanyLogoDataUriTests(TestCase):
    """The PDF logo must not depend on WeasyPrint fetching /media/ over HTTP."""

    def _settings_with_logo(self, name, content):
        c = CompanySettings.get_settings()
        c.logo.save(name, ContentFile(content), save=True)
        return c

    def tearDown(self):
        c = CompanySettings.get_settings()
        if c.logo:
            c.logo.delete(save=True)

    def test_png_logo_becomes_a_data_uri(self):
        c = self._settings_with_logo('logo.png', png_bytes())
        uri = c.logo_data_uri
        self.assertTrue(uri.startswith('data:image/png;base64,'))
        decoded = base64.b64decode(uri.split(',', 1)[1])
        self.assertEqual(decoded[:8], b'\x89PNG\r\n\x1a\n')

    def test_svg_logo_becomes_a_data_uri(self):
        c = self._settings_with_logo('logo.svg', SVG_WITH_DOCTYPE)
        self.assertTrue(c.logo_data_uri.startswith('data:image/svg+xml;base64,'))

    def test_svg_doctype_is_stripped(self):
        """A DOCTYPE sends the renderer to w3.org for the DTD, which stalls."""
        c = self._settings_with_logo('logo2.svg', SVG_WITH_DOCTYPE)
        decoded = base64.b64decode(c.logo_data_uri.split(',', 1)[1])
        self.assertNotIn(b'DOCTYPE', decoded)
        self.assertNotIn(b'<?xml', decoded)
        self.assertIn(b'<svg', decoded)

    def test_no_logo_yields_empty_string(self):
        c = CompanySettings(company_name='X')
        self.assertEqual(c.logo_data_uri, '')

    def test_missing_file_yields_empty_string(self):
        """Recorded in the database but absent from the media volume --
        exactly the production state that lost the logo."""
        c = CompanySettings(company_name='X', logo='company/not-here.png')
        self.assertEqual(c.logo_data_uri, '')

    def test_unsupported_extension_yields_empty_string(self):
        c = CompanySettings(company_name='X', logo='company/notes.txt')
        self.assertEqual(c.logo_data_uri, '')

    def test_quote_pdf_embeds_the_logo(self):
        company = self._settings_with_logo('logo.png', png_bytes())
        client_obj = Client.objects.create(name='Acme Ltd')
        q = Quote.objects.create(
            quote_number='Q-9100', client=client_obj, title='Logo test',
            valid_until=timezone.localdate(), subtotal=Decimal('100'))
        html = render_to_string('quotes/pdf.html', {
            'quote': q, 'company': company, 'items': q.items.all()})
        self.assertIn('src="data:image/png;base64,', html)
        # and must not fall back to a URL WeasyPrint would have to fetch
        self.assertNotIn('src="/media/', html)

    def test_pdfs_fall_back_to_the_letter_mark_without_a_logo(self):
        company = CompanySettings.get_settings()
        client_obj = Client.objects.create(name='Acme Ltd')
        q = Quote.objects.create(
            quote_number='Q-9101', client=client_obj, title='No logo',
            valid_until=timezone.localdate(), subtotal=Decimal('100'))
        html = render_to_string('quotes/pdf.html', {
            'quote': q, 'company': company, 'items': q.items.all()})
        self.assertNotIn('src="data:', html)
        self.assertIn('logo-icon', html)
