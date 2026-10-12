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
    ('website', 'Website or web app'),
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
PHONE_RE = re.compile(r'^\+?[\d\s\-()]{7,20}$')
MAX_PER_HOUR = 5


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
        'interests': INTERESTS,
        'picked': request.GET.get('interest', ''),
        'whatsapp': WHATSAPP,
        'sent': request.GET.get('sent') == '1',
    })


def _client_ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (fwd.split(',')[0].strip() if fwd else request.META.get('REMOTE_ADDR', '')) or 'unknown'


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
    count = cache.get(key, 0)
    if count >= MAX_PER_HOUR:
        messages.error(request, 'We already have your request. We will call you soon.')
        return redirect(back)
    cache.set(key, count + 1, 3600)

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
