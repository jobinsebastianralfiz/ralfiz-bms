"""Digital visiting cards: owner screens under /cards/, public card under /card/."""
import io
import logging
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from .forms import DigitalCardForm
from .models import DigitalCard
from .vcard import build_vcard

log = logging.getLogger(__name__)

PHONE_RE = re.compile(r'^\+?[\d\s\-()]{7,20}$')
MAX_PER_HOUR = 5        # enquiries from one IP
MAX_ALL_PER_HOUR = 60   # all visitors together: a flood cannot fill the CRM


def _company():
    from core.models import CompanySettings
    return CompanySettings.get_settings()


def _public_url(request, card):
    return request.build_absolute_uri(card.get_absolute_url())


def _active_card(slug):
    return get_object_or_404(DigitalCard, slug=slug, is_active=True)


# ---------------------------------------------------------------- public

@xframe_options_sameorigin   # the share page previews it in a phone frame
def public_card(request, slug):
    card = _active_card(slug)
    if not request.GET.get('preview'):
        DigitalCard.objects.filter(pk=card.pk).update(views=F('views') + 1)
    company = _company()
    return render(request, 'cards/public.html', {
        'card': card,
        'company': company,
        'company_name': card.company or company.company_name,
        'card_url': _public_url(request, card),
        'sent': request.GET.get('sent') == '1',
    })


def card_vcf(request, slug):
    card = _active_card(slug)
    DigitalCard.objects.filter(pk=card.pk).update(saves=F('saves') + 1)
    body = build_vcard(card, card.company or _company().company_name, _public_url(request, card))
    resp = HttpResponse(body, content_type='text/vcard; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="{card.slug}.vcf"'
    return resp


def card_qr(request, slug):
    """PNG QR of the card link. The quiet zone is in the image, so it scans
    even when placed on a coloured background."""
    import qrcode
    card = _active_card(slug)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=14, border=4)
    qr.add_data(_public_url(request, card))
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1F1D2E', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    resp = HttpResponse(buf.getvalue(), content_type='image/png')
    if request.GET.get('download'):
        resp['Content-Disposition'] = f'attachment; filename="{card.slug}-qr.png"'
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp


@require_POST
def card_enquiry(request, slug):
    """A visitor leaves their details: saved as a CRM lead, assigned to the card's owner."""
    from crm.models import Lead, LeadActivity
    from core.security import client_ip
    card = _active_card(slug)
    back = card.get_absolute_url()
    f = request.POST
    if not card.show_enquiry_form:
        raise Http404
    if f.get('website_url'):               # honeypot: people never see this field
        return redirect(back + '?sent=1#connect')
    name, phone = f.get('name', '').strip()[:200], f.get('phone', '').strip()[:20]
    email, business = f.get('email', '').strip()[:254], f.get('business', '').strip()[:200]
    message = f.get('message', '').strip()[:2000]
    if not name or not PHONE_RE.match(phone):
        messages.error(request, 'Please give your name and a phone number.')
        return redirect(back + '#connect')
    key = f'card-enquiries:{client_ip(request) or "unknown"}'
    count, total = cache.get(key, 0), cache.get('card-enquiries:all', 0)
    if count >= MAX_PER_HOUR or total >= MAX_ALL_PER_HOUR:
        return redirect(back + '?sent=1#connect')
    cache.set(key, count + 1, 3600)
    cache.set('card-enquiries:all', total + 1, 3600)

    notes = f'Shared their details on the digital visiting card of {card.full_name}.'
    if message:
        notes += f'\n\n{message}'
    with transaction.atomic():
        lead = Lead.objects.create(contact_person=name, company_name=business, phone=phone, email=email,
                                   source='referral', status='new', notes=notes, assigned_to=card.owner)
        LeadActivity.objects.create(lead=lead, activity_type='created',
                                    description=f'Came in through the digital card of {card.full_name}',
                                    metadata={'via': 'digital_card', 'card': card.slug})
        DigitalCard.objects.filter(pk=card.pk).update(enquiries=F('enquiries') + 1)
    _notify(card, lead)
    return redirect(back + '?sent=1#connect')


def _notify(card, lead):
    """Push to the card owner's phone, or to the owners when the card has none. Never blocks the visitor."""
    try:
        from employees.models import Employee
        from employees.utils import send_push_notification
        people = Employee.objects.filter(status='active')
        people = people.filter(user=card.owner) if card.owner else people.filter(role__in=('owner', 'partner'))
        for emp in people:
            send_push_notification(emp, 'New lead from your digital card',
                                   f'{lead.contact_person} ({lead.phone})',
                                   {'type': 'lead', 'lead_id': str(lead.pk)})
    except Exception:
        log.exception('card enquiry push failed')


# ---------------------------------------------------------------- owner

@login_required
def card_list(request):
    cards = DigitalCard.objects.select_related('owner')
    return render(request, 'cards/list.html', {'cards': cards})


@login_required
def card_create(request):
    initial = {}
    if not DigitalCard.objects.exists():
        company = _company()
        initial = {'phone': company.phone, 'email': company.email, 'address': company.address,
                   'website': 'https://ralfizdigital.in', 'owner': request.user.pk,
                   'full_name': request.user.get_full_name()}
    form = DigitalCardForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        card = form.save(commit=False)
        card.created_by = request.user
        card.save()
        messages.success(request, f'Card for {card.full_name} is live. Share it below.')
        return redirect('cards:share', pk=card.pk)
    return render(request, 'cards/form.html', {'form': form, 'card': None})


@login_required
def card_edit(request, pk):
    card = get_object_or_404(DigitalCard, pk=pk)
    form = DigitalCardForm(request.POST or None, request.FILES or None, instance=card)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Card updated.')
        return redirect('cards:share', pk=card.pk)
    return render(request, 'cards/form.html', {'form': form, 'card': card})


@login_required
def card_share(request, pk):
    card = get_object_or_404(DigitalCard, pk=pk)
    url = _public_url(request, card)
    company_name = card.company or _company().company_name
    message = (f'Hi, this is {card.full_name}'
               + (f', {card.designation}' if card.designation else '')
               + (f' at {company_name}' if company_name else '')
               + f'. Here is my digital visiting card. Tap to save my contact: {url}')
    return render(request, 'cards/share.html', {
        'card': card, 'card_url': url, 'share_message': message, 'company_name': company_name,
    })


@login_required
@require_POST
def card_delete(request, pk):
    card = get_object_or_404(DigitalCard, pk=pk)
    name = card.full_name
    card.delete()
    messages.success(request, f'Card for {name} deleted. Its link no longer works.')
    return redirect(reverse('cards:list'))
