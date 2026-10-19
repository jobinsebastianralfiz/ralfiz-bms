import io
import tempfile

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from crm.models import Lead
from .models import DigitalCard
from .vcard import build_vcard


def _png():
    buf = io.BytesIO()
    Image.new('RGB', (600, 400), '#9B4DFF').save(buf, 'PNG')
    return SimpleUploadedFile('me.png', buf.getvalue(), content_type='image/png')


MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class PublicCardTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user('jobin', password='x', first_name='Jobin')
        self.card = DigitalCard.objects.create(
            slug='jobin', full_name='Jobin Sebastian', designation='Founder & CEO', phone='+91 98956 63498',
            email='jobin@ralfiz.com', website='https://ralfizdigital.in', owner=self.owner,
            linkedin='https://linkedin.com/in/jobin', services='Websites\nMobile apps\n\n')

    def test_page_shows_contact_buttons_and_counts_views(self):
        r = self.client.get('/card/jobin/')
        self.assertContains(r, 'Jobin Sebastian')
        self.assertContains(r, 'href="tel:+919895663498"')
        self.assertContains(r, 'https://wa.me/919895663498')
        self.assertContains(r, 'fa-linkedin-in')
        self.assertContains(r, '<span>Mobile apps</span>', html=False)
        self.assertContains(r, 'og:title')
        self.card.refresh_from_db()
        self.assertEqual(self.card.views, 1)

    def test_preview_does_not_count_and_can_be_framed(self):
        r = self.client.get('/card/jobin/?preview=1')
        self.assertEqual(r['X-Frame-Options'], 'SAMEORIGIN')
        self.card.refresh_from_db()
        self.assertEqual(self.card.views, 0)

    def test_turned_off_card_is_not_found(self):
        self.card.is_active = False
        self.card.save()
        self.assertEqual(self.client.get('/card/jobin/').status_code, 404)
        self.assertEqual(self.client.get('/card/jobin/contact.vcf').status_code, 404)

    def test_vcf_download(self):
        r = self.client.get('/card/jobin/contact.vcf')
        self.assertEqual(r['Content-Type'], 'text/vcard; charset=utf-8')
        body = r.content.decode()
        self.assertIn('FN:Jobin Sebastian', body)
        self.assertIn('N:Sebastian;Jobin;;;', body)
        self.assertIn('TITLE:Founder & CEO', body)
        self.assertIn('TEL;TYPE=CELL,VOICE:+919895663498', body)
        self.card.refresh_from_db()
        self.assertEqual(self.card.saves, 1)

    def test_vcard_lines_are_folded_and_photo_included(self):
        self.card.photo = _png()
        self.card.save()
        body = build_vcard(self.card, 'Ralfiz Technologies', 'https://x/card/jobin/')
        self.assertIn('PHOTO;ENCODING=b;TYPE=JPEG:', body)
        for line in body.split('\r\n'):
            self.assertLessEqual(len(line.encode()), 75)

    def test_qr_png(self):
        r = self.client.get('/card/jobin/qr.png')
        self.assertEqual(r['Content-Type'], 'image/png')
        self.assertTrue(r.content.startswith(b'\x89PNG'))

    def test_enquiry_becomes_lead_for_card_owner(self):
        r = self.client.post('/card/jobin/connect/', {'name': 'Asha', 'phone': '9876543210', 'business': 'Asha Bakes',
                                                     'message': 'Need a website'})
        self.assertRedirects(r, '/card/jobin/?sent=1#connect', fetch_redirect_response=False)
        lead = Lead.objects.get()
        self.assertEqual(lead.assigned_to, self.owner)
        self.assertEqual(lead.company_name, 'Asha Bakes')
        self.assertIn('Need a website', lead.notes)
        self.assertEqual(lead.activities.get().metadata['card'], 'jobin')
        self.card.refresh_from_db()
        self.assertEqual(self.card.enquiries, 1)

    def test_enquiry_rejects_bad_phone_and_honeypot(self):
        self.client.post('/card/jobin/connect/', {'name': 'Asha', 'phone': 'call me'})
        self.client.post('/card/jobin/connect/', {'name': 'Bot', 'phone': '9876543210', 'website_url': 'x'})
        self.assertFalse(Lead.objects.exists())

    def test_enquiry_rate_limited(self):
        for i in range(7):
            self.client.post('/card/jobin/connect/', {'name': f'P{i}', 'phone': '9876543210'})
        self.assertEqual(Lead.objects.count(), 5)

    def test_enquiry_form_can_be_turned_off(self):
        self.card.show_enquiry_form = False
        self.card.save()
        self.assertNotContains(self.client.get('/card/jobin/'), 'name="phone"')
        self.assertEqual(self.client.post('/card/jobin/connect/', {'name': 'A', 'phone': '9876543210'}).status_code, 404)


@override_settings(MEDIA_ROOT=MEDIA)
class OwnerScreenTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('boss', 'b@x.com', 'x')

    def test_login_required(self):
        r = self.client.get(reverse('cards:list'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('login', r['Location'])

    def test_create_makes_unique_slug_and_lands_on_share(self):
        DigitalCard.objects.create(slug='asha-k', full_name='Other', phone='1234567')
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('cards:create')), 'New digital visiting card')
        r = self.client.post(reverse('cards:create'), {
            'full_name': 'Asha K', 'phone': '9876543210', 'theme': 'daylight', 'photo': _png(),
            'show_enquiry_form': 'on', 'is_active': 'on'})
        card = DigitalCard.objects.get(full_name='Asha K')
        self.assertEqual(card.slug, 'asha-k-2')
        self.assertRedirects(r, reverse('cards:share', args=[card.pk]))
        share = self.client.get(reverse('cards:share', args=[card.pk]))
        self.assertContains(share, 'https://wa.me/?text=')
        self.assertContains(share, '/card/asha-k-2/')

    def test_taken_slug_rejected(self):
        DigitalCard.objects.create(slug='jobin', full_name='Jobin', phone='1234567')
        self.client.force_login(self.user)
        r = self.client.post(reverse('cards:create'), {'full_name': 'J2', 'phone': '1234567', 'slug': 'Jobin',
                                                       'theme': 'aurora'})
        self.assertContains(r, 'Another card already uses this link.')

    def test_list_edit_delete(self):
        card = DigitalCard.objects.create(slug='jobin', full_name='Jobin', phone='1234567')
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('cards:list')), '/card/jobin/')
        self.assertContains(self.client.get(reverse('cards:edit', args=[card.pk])), 'Edit card: Jobin')
        self.client.post(reverse('cards:delete', args=[card.pk]))
        self.assertFalse(DigitalCard.objects.exists())

    def test_sidebar_link(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('cards:list')), 'Visiting Cards')
