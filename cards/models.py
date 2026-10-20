"""Digital visiting cards: a public page per person, shared by link or QR.

The page at /card/<slug>/ shows the person's contact buttons, saves them to
the visitor's phone as a vCard, and takes the visitor's own details back as
a CRM lead.
"""
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class DigitalCard(models.Model):
    THEME_CHOICES = [
        ('daylight', 'Daylight (light, soft)'),
        ('aurora', 'Midnight (dark, soft)'),
        ('executive', 'Executive (printed business card look)'),
        ('editorial', 'Editorial (white and black, magazine look)'),
        ('showcase', 'Showcase (dark blue, wide profile page on desktop)'),
    ]
    TYPE_CHOICES = [
        ('person', 'Person (one team member)'),
        ('company', 'Company (the business itself)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=60, unique=True, verbose_name='Card link',
                            help_text='The link: ralfizdigital.in/card/<this>/. Letters, numbers and dashes.')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='digital_cards', verbose_name='Leads go to',
                              help_text='Enquiries from this card are assigned to this login in Leads.')

    card_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='person', verbose_name='Card for',
                                 help_text='A company card puts the business name and logo first; Save contact saves it as a company.')
    full_name = models.CharField(max_length=120, verbose_name='Name', help_text='Person card: your name. Company card: the company name.')
    designation = models.CharField(max_length=120, blank=True, verbose_name='Designation / tagline',
                                   help_text='Person: e.g. Founder & CEO. Company: a tagline, e.g. Rise to the Next Level.')
    company = models.CharField(max_length=120, blank=True, help_text='Left blank, the company name from Settings is used.')
    bio = models.TextField(max_length=400, blank=True, help_text='Two or three lines about you or what you do.')
    photo = models.ImageField(upload_to='cards/', blank=True, help_text='Square photo works best. Company card: an office or team photo.')
    logo = models.ImageField(upload_to='cards/', blank=True, help_text='Left blank, the logo from Settings is used. Upload one for a client company.')

    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True, verbose_name='WhatsApp', help_text='Left blank, the phone number is used.')
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    map_url = models.URLField(blank=True, verbose_name='Google Maps link')
    google_review_url = models.URLField(blank=True, verbose_name='Google review link',
                                        help_text='From Google Business Profile: "Ask for reviews" → copy link (g.page/r/…/review).')

    linkedin = models.URLField(blank=True, verbose_name='LinkedIn')
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True, verbose_name='X (Twitter)')
    youtube = models.URLField(blank=True, verbose_name='YouTube')
    github = models.URLField(blank=True, verbose_name='GitHub')

    services = models.TextField(blank=True, verbose_name='Services / what you do', help_text='One per line, shown as chips on the card.')
    highlights = models.TextField(blank=True, help_text='One per line as figure | label, e.g. "100+ | Projects delivered". Shown by the Showcase theme.')
    company_about = models.TextField(max_length=800, blank=True, verbose_name='About the company',
                                     help_text='A short paragraph about the business. Shown by the Showcase theme.')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='daylight')
    show_enquiry_form = models.BooleanField(default=True, verbose_name='Show "Share your details" form', help_text='Let visitors send you their details.')
    is_active = models.BooleanField(default=True, verbose_name='Card is live', help_text='Turned off, the link shows "card not found".')

    views = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0)
    enquiries = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse('cards:public', args=[self.slug])

    @property
    def is_company(self):
        return self.card_type == 'company'

    @property
    def highlight_list(self):
        """(figure, label) pairs from the highlights lines; a line without | is all label."""
        out = []
        for line in self.highlights.splitlines():
            if line.strip():
                figure, _, label = line.partition('|')
                out.append((figure.strip(), label.strip()) if label else ('', figure.strip()))
        return out

    @property
    def service_tiles(self):
        """(name, Font Awesome class) per service, the icon guessed from its words."""
        icons = [(('web', 'site'), 'fas fa-globe'), (('app', 'mobile', 'android', 'ios', 'flutter'), 'fas fa-mobile-screen'),
                 (('erp', 'software', 'crm', 'pos', 'billing', 'system'), 'fas fa-gear'),
                 (('social', 'instagram', 'facebook'), 'fas fa-bullhorn'), (('marketing', 'seo', 'ads'), 'fas fa-chart-simple'),
                 (('ai', 'automation', 'bot', 'data'), 'fas fa-microchip'), (('design', 'brand', 'logo', 'ui'), 'fas fa-pen-nib'),
                 (('host', 'cloud', 'server', 'domain'), 'fas fa-cloud'), (('train', 'course', 'intern', 'academy'), 'fas fa-graduation-cap')]
        tiles = []
        for name in self.service_list:
            words = name.lower().replace('&', ' ').replace('/', ' ').split()
            icon = next((cls for keys, cls in icons if any(w.startswith(k) for w in words for k in keys)), 'fas fa-circle-check')
            tiles.append((name, icon))
        return tiles

    @property
    def whatsapp_number(self):
        return ''.join(c for c in (self.whatsapp or self.phone) if c.isdigit())

    @property
    def phone_link(self):
        return ''.join(c for c in self.phone if c.isdigit() or c == '+')

    @property
    def initials(self):
        return ''.join(w[0] for w in self.full_name.split()[:2]).upper()

    @property
    def name_parts(self):
        """(first, last) for the two-line name; last is '' for a single word."""
        words = self.full_name.split()
        return (' '.join(words[:-1]), words[-1]) if len(words) > 1 else (self.full_name, '')

    @property
    def handle(self):
        """Short handle for the side of the editorial card: @instagram, else the website domain."""
        if self.instagram:
            name = self.instagram.rstrip('/').split('/')[-1].split('?')[0]
            if name:
                return '@' + name.lstrip('@')
        if self.website:
            return self.website.split('//')[-1].split('/')[0].removeprefix('www.')
        return ''

    @property
    def address_line(self):
        """The address as one flowing line, so it wraps to the column instead of the typed line breaks."""
        return ', '.join(l.strip().rstrip(',') for l in self.address.splitlines() if l.strip())

    @property
    def service_list(self):
        return [s.strip() for s in self.services.splitlines() if s.strip()]

    @property
    def socials(self):
        """(label, Font Awesome class, url) for each social link that is set."""
        links = [
            ('LinkedIn', 'fab fa-linkedin-in', self.linkedin),
            ('Instagram', 'fab fa-instagram', self.instagram),
            ('Facebook', 'fab fa-facebook-f', self.facebook),
            ('X', 'fab fa-x-twitter', self.twitter),
            ('YouTube', 'fab fa-youtube', self.youtube),
            ('GitHub', 'fab fa-github', self.github),
        ]
        return [link for link in links if link[2]]

    @classmethod
    def unique_slug(cls, name, exclude_pk=None):
        base = slugify(name)[:50] or 'card'
        slug, n = base, 2
        qs = cls.objects.exclude(pk=exclude_pk) if exclude_pk else cls.objects.all()
        while qs.filter(slug=slug).exists():
            slug, n = f'{base}-{n}', n + 1
        return slug
