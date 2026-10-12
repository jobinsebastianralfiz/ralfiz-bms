"""The public face of ralfizdigital.in: the landing page and the demo form.

Visitors who are not signed in get the landing page at '/'; signed-in staff
keep getting the BMS dashboard there, as before. A demo request becomes a CRM
Lead (source: website) so it shows up in Leads like any other enquiry.
"""
import logging
import re

from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

log = logging.getLogger(__name__)

INTERESTS = [
    ('ralfiz_social', 'Ralfiz Social (social media hub)'),
    ('website', 'Business website'),
    ('pkg_starter', 'Website · Starter package'),
    ('pkg_business', 'Website · Business package'),
    ('pkg_professional', 'Website · Professional package'),
    ('pkg_enterprise', 'Website · Enterprise package'),
    ('web_app', 'Custom web application'),
    ('mobile_app', 'Mobile app'),
    ('custom_software', 'Custom business software'),
    ('marketing', 'Digital marketing & social media management'),
    ('ralfpos', 'RalfPOS'),
    ('retailease', 'RetailEase'),
    ('gympro', 'GymPro'),
    ('eduflow', 'EduFlow'),
    ('interiodesk', 'InterioDesk'),
    ('academy', 'Academy course or internship'),
    ('other', 'Something else'),
]
WHATSAPP = '919895663498'

# From Ralfiz_Portfolio (2026). img = screenshot in static/website/img/pf/; url None = login-only system.
PORTFOLIO = [
    {'name': 'Vistgrow', 'url': 'https://vistgrow.com', 'img': 'vistgrow-com', 'tag': 'Agency website',
     'desc': 'Website for a Kerala digital marketing and branding agency.', 'recent': True},
    {'name': 'Backbone India', 'url': 'https://backboneindia.com', 'img': 'backboneindia-com', 'tag': 'Corporate website',
     'desc': 'E-commerce consultancy helping brands grow on India\'s major marketplaces.', 'recent': True},
    {'name': 'Novrik Technologies', 'url': 'https://novriktech.com', 'img': 'novriktech-com', 'tag': 'Corporate website',
     'desc': 'Corporate site for a Canadian software development company.', 'recent': True},
    {'name': 'iRAD 2027', 'url': 'https://irad2027.org', 'img': 'irad2027-org', 'tag': 'Conference platform',
     'desc': 'Registrations, payments and delegate logistics for an international conference.'},
    {'name': 'CUSAT · ACARR', 'url': 'https://acarr.cusat.ac.in', 'img': 'acarr-cusat-ac-in', 'tag': 'University website',
     'desc': 'Advanced Centre for Atmospheric Radar Research, Cochin University.'},
    {'name': 'CUSAT · DPO', 'url': 'https://dpo.cusat.ac.in', 'img': 'dpo-cusat-ac-in', 'tag': 'University portal',
     'desc': 'Official web portal for a Cochin University of Science and Technology office.'},
    {'name': 'Lecule Pharma', 'url': 'https://leculepharma.com', 'img': 'leculepharma-com', 'tag': 'Corporate website',
     'desc': 'Corporate website and product catalogue for a pharmaceutical company.'},
    {'name': 'Sunnok', 'url': 'https://sunnok.in', 'img': 'sunnok-in', 'tag': 'Corporate website',
     'desc': 'Brand website with automated CI/CD deployment.'},
    {'name': 'ICFHR-TECH of India', 'url': 'https://icfhrtechofindia.com', 'img': 'icfhrtechofindia-com', 'tag': 'Education portal',
     'desc': 'Educational support services for institutes, colleges and universities.'},
    {'name': 'Maicafe', 'url': 'https://apps.apple.com/us/app/maicafe/id6770197831', 'img': '', 'tag': 'iOS & Android app',
     'desc': 'Café ordering app with coupons and profiles, live on the App Store and Google Play, plus the brand website.',
     'icon': 'fa-mug-hot', 'color': '#FF7A3D'},
    {'name': 'Gateway Tours', 'url': 'https://gatewaytours.ae', 'img': '', 'tag': 'UAE · Travel website',
     'desc': 'Website for a UAE travel and visa services company.', 'icon': 'fa-plane-departure', 'color': '#3D8BFF'},
    {'name': 'Lyceum Academy', 'url': 'https://lyceumacademy.info', 'img': '', 'tag': 'Education website',
     'desc': 'Website for an education and training academy.', 'icon': 'fa-book-open', 'color': '#9B4DFF'},
    {'name': 'Zoco Toys ERP', 'url': None, 'img': '', 'tag': 'ERP system',
     'desc': 'ERP for a toy distribution business: stock, orders and billing.', 'icon': 'fa-boxes-stacked', 'color': '#FF2E88'},
    {'name': 'Logitech Express', 'url': None, 'img': '', 'tag': 'Business system',
     'desc': 'Business management system for a logistics company.', 'icon': 'fa-truck-fast', 'color': '#3EF0A0'},
]

# From Ralfiz-Website-Packages-2026 (prices exclude 18% GST, domain, hosting and AMC).
PACKAGES = [
    {'name': 'Starter', 'for': 'Shops, freelancers, small service businesses', 'price': '25,000', 'pages': '5', 'langs': '1',
     'days': '10–12 days', 'support': '1 month support',
     'features': ['Unlimited services & gallery', 'Admin dashboard', 'Enquiry form + WhatsApp button',
                  'Google Map & click-to-call', 'Basic on-page SEO', 'Cookie banner & legal pages', 'SSL setup']},
    {'name': 'Business', 'for': 'Clinics, institutes, agencies, growing SMEs', 'price': '40,000', 'pages': '8', 'langs': '2',
     'days': '15–20 days', 'support': '2 months support', 'popular': True,
     'features': ['Everything in Starter', 'Unlimited blog, testimonials, FAQs', 'Accessibility toolbar',
                  'Google Analytics & Business Profile', 'Speed optimisation', 'Enquiries saved to dashboard',
                  '3 revision rounds']},
    {'name': 'Professional', 'for': 'Established companies & GCC businesses', 'price': '65,000', 'pages': '12',
     'langs': '2 incl. Arabic', 'days': '25–35 days', 'support': '3 months support',
     'features': ['Everything in Business', 'Unlimited team, projects, careers, branches', 'KSA & GCC compliance pack',
                  'WCAG 2.1 AA accessibility', 'Arabic RTL layout', 'Advanced SEO & schema', 'Premium animations']},
    {'name': 'Enterprise', 'for': 'Portals, bookings, multi-branch, integrations', 'price': '1,00,000', 'from': True,
     'pages': '∞', 'langs': '3+', 'days': 'As per scope', 'support': '3 months support',
     'features': ['Everything in Professional', 'Custom modules: booking, catalogue, portal',
                  'Payment, CRM, ERP & WhatsApp API', 'Multi-branch support', 'Dedicated project manager',
                  'Scoped after a requirement call']},
]
WEBAPPS = [
    {'name': 'Web App MVP', 'for': 'Booking system, lead tracker, internal tool', 'price': '1,50,000', 'time': '4–8 weeks',
     'features': ['Login & user roles', 'Dashboard & reports', '3–5 core modules', 'Custom admin panel']},
    {'name': 'Business Application', 'for': 'ERP, CRM, LMS, clinic or multi-branch management, customer portal',
     'price': '3,00,000', 'time': '2–4 months', 'featured': True,
     'features': ['6–12 modules', 'Role-based access', 'Advanced reports & exports', 'Payment, SMS & WhatsApp integrations']},
    {'name': 'SaaS Platform', 'for': 'Multi-tenant subscription product, white-label platform', 'price': '6,00,000',
     'time': '4–6 months', 'features': ['Tenant management', 'Subscriptions & billing', 'Super-admin console', 'Public APIs']},
]
AMC = [
    {'name': 'Basic', 'price': '6,000', 'note': 'Recommended for Starter',
     'features': ['2 hrs content updates / month', 'Monthly backup', 'Security patches', '48-hour response']},
    {'name': 'Standard', 'price': '12,000', 'note': 'Recommended for Business', 'featured': True,
     'features': ['5 hrs content updates / month', 'Weekly backup', 'Uptime monitoring', '24-hour response']},
    {'name': 'Premium', 'price': '24,000', 'note': 'Professional & Enterprise',
     'features': ['10 hrs content updates / month', 'Daily backup', 'Monthly SEO health report', 'Same-day response']},
]
PHONE_RE = re.compile(r'^\+?[\d\s\-()]{7,20}$')
MAX_PER_HOUR = 5
PROJECTS_FEED = 'https://ralfiz.com/projects/feed.json'
FEED_CACHE = 'website:portfolio-feed'
FEED_TTL = 30 * 60
SPLIT = re.compile(r'\s+[–—-]\s+')


def portfolio():
    """Projects from ralfiz.com's admin (cached 30 min); the built-in list if the feed is down.

    Add, edit or reorder projects in the ralfiz.com admin and they appear here.
    """
    cached = cache.get(FEED_CACHE)
    if cached is not None:
        return cached
    try:
        import requests
        r = requests.get(PROJECTS_FEED, timeout=6)
        r.raise_for_status()
        items = []
        for p in r.json().get('projects', []):
            title = p.get('title', '').strip()
            parts = SPLIT.split(title, maxsplit=1)
            cats = p.get('categories') or []
            items.append({
                'name': parts[0], 'tag': parts[1] if len(parts) > 1 else (cats[0] if cats else 'Project'),
                'desc': (p.get('summary') or '')[:160].rsplit(' ', 1)[0] + ('…' if len(p.get('summary') or '') > 160 else ''),
                'url': _http(p.get('url')) or _http(p.get('detail')), 'image': _http(p.get('image')),
                'recent': bool(p.get('featured')), 'detail': p.get('detail', ''),
            })
        if not items:
            raise ValueError('empty feed')
        cache.set(FEED_CACHE, items, FEED_TTL)
        return items
    except Exception:
        log.warning('portfolio feed unavailable, using the built-in list', exc_info=True)
        cache.set(FEED_CACHE, PORTFOLIO, 5 * 60)   # retry in 5 minutes
        return PORTFOLIO


def root(request):
    """'/' : the BMS dashboard for staff, the landing page for everyone else."""
    if request.user.is_authenticated:
        from core.views import home_dashboard
        return home_dashboard(request)
    return landing(request)


def landing(request):
    from core.models import Client, CompanySettings
    company = CompanySettings.get_settings()
    clients = Client.objects.filter(is_active=True).count()
    return render(request, 'website/landing.html', {
        'company': company,
        'clients_label': f'{clients // 10 * 10}+' if clients >= 20 else str(clients),
        'interests': INTERESTS, 'portfolio': portfolio(), 'packages': PACKAGES, 'webapps': WEBAPPS, 'amc': AMC,
        'picked': request.GET.get('interest', ''),
        'whatsapp': WHATSAPP,
        'sent': request.GET.get('sent') == '1',
    })


MAX_ALL_PER_HOUR = 60   # all visitors together: a flood cannot fill the CRM


def _client_ip(request):
    from core.security import client_ip
    return client_ip(request) or 'unknown'


def _http(url):
    return url if isinstance(url, str) and url.lower().startswith(('https://', 'http://')) else ''


@require_POST
def book_demo(request):
    """Save a demo request as a CRM lead. Honeypot + per-IP limit keep bots out."""
    from crm.models import Lead, LeadActivity
    f = request.POST
    back = reverse('dashboard') + '#demo'
    if f.get('website_url'):              # honeypot: people never see this field
        return redirect(reverse('dashboard') + '?sent=1#demo')
    name, phone = f.get('name', '').strip()[:200], f.get('phone', '').strip()[:20]
    email, business = f.get('email', '').strip()[:254], f.get('business', '').strip()[:200]
    interest = f.get('interest', 'other')
    labels = dict(INTERESTS)
    if interest not in labels:
        interest = 'other'
    if not name or not PHONE_RE.match(phone):
        messages.error(request, 'Please give your name and a phone number we can call.')
        return redirect(back)
    key = f'demo-requests:{_client_ip(request)}'
    count, total = cache.get(key, 0), cache.get('demo-requests:all', 0)
    if count >= MAX_PER_HOUR or total >= MAX_ALL_PER_HOUR:
        messages.error(request, 'We already have your request. We will call you soon.')
        return redirect(back)
    cache.set(key, count + 1, 3600)
    cache.set('demo-requests:all', total + 1, 3600)

    message = f.get('message', '').strip()[:2000]
    notes = f'Website demo request: {labels[interest]}'
    if message:
        notes += f'\n\n{message}'
    with transaction.atomic():
        lead = Lead.objects.create(contact_person=name, company_name=business, phone=phone, email=email,
                                   source='website', status='new', notes=notes)
        LeadActivity.objects.create(lead=lead, activity_type='created',
                                    description=f'Demo requested on ralfizdigital.in: {labels[interest]}',
                                    metadata={'interest': interest, 'via': 'website'})
    _notify_owners(lead, labels[interest])
    return redirect(reverse('dashboard') + '?sent=1#demo')


def _notify_owners(lead, interest):
    """Push to owners' phones (the BMS mobile app). Never blocks the visitor."""
    try:
        from employees.models import Employee
        from employees.utils import send_push_notification
        for emp in Employee.objects.filter(status='active', role__in=('owner', 'partner')):
            send_push_notification(emp, 'New demo request',
                                   f'{lead.contact_person} ({lead.phone}): {interest}',
                                   {'type': 'lead', 'lead_id': str(lead.pk)})
    except Exception:
        log.exception('demo request push failed')


VIDEO_DIR = 'website/video'
RANGE_RE = re.compile(r'bytes=(\d*)-(\d*)$')


def video(request, name):
    """Serve a landing-page video with HTTP Range support.

    Safari and iOS only play <video> from servers that answer Range requests
    with 206; whitenoise answers 200 with the whole file, so the clip would
    never start on an iPhone. Only files that exist in static/website/video/
    can be served (the name is matched against the folder listing).
    """
    import os
    from django.conf import settings
    from django.contrib.staticfiles import finders
    from django.http import FileResponse, Http404, HttpResponse
    folder = finders.find(VIDEO_DIR) or os.path.join(settings.STATIC_ROOT, VIDEO_DIR)
    if not folder or name not in os.listdir(folder) or not name.endswith('.mp4'):
        raise Http404
    path = os.path.join(folder, name)
    size = os.path.getsize(path)
    m = RANGE_RE.match(request.headers.get('Range', '').strip())
    if m and (m.group(1) or m.group(2)):
        if m.group(1):
            start = int(m.group(1))
            end = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
        else:  # suffix range: the last N bytes
            start, end = max(0, size - int(m.group(2))), size - 1
        if start > end or start >= size:
            resp = HttpResponse(status=416)
            resp['Content-Range'] = f'bytes */{size}'
            return resp
        with open(path, 'rb') as fh:
            fh.seek(start)
            body = fh.read(end - start + 1)
        resp = HttpResponse(body, status=206, content_type='video/mp4')
        resp['Content-Range'] = f'bytes {start}-{end}/{size}'
    else:
        resp = FileResponse(open(path, 'rb'), content_type='video/mp4')
    resp['Accept-Ranges'] = 'bytes'
    resp['Cache-Control'] = 'public, max-age=604800'
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp
