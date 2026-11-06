"""HR screens for internship offer letters: write the offer, send the link,
approve the candidate's acceptance (which unlocks their download and opens
their enrolment link)."""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from employees.agreement_models import MONEY_MODE_CHOICES, MONEY_NONE
from employees.enrolment_models import WORK_MODE_CHOICES, EnrolmentSettings
from employees.models import Employee
from employees.offer_models import DEFAULT_TERMS, InternOffer, default_offer_expiry
from employees.offer_views import letter_context, offer_pdf_filename, render_offer_pdf

from .enrolment_web_views import enrolment_admin

TEXT_FIELDS = ('candidate_name', 'phone', 'email', 'position', 'department', 'work_mode',
               'money_mode', 'terms', 'institution_name', 'course', 'year_of_study')


@enrolment_admin
def offer_list(request):
    qs = InternOffer.objects.all()
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()
    now = timezone.now()
    if status_filter == 'expired':
        qs = qs.filter(status__in=InternOffer.OPEN_STATUSES, expires_at__lt=now)
    elif status_filter == 'open':
        qs = qs.filter(status__in=InternOffer.OPEN_STATUSES, expires_at__gte=now)
    elif status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(Q(candidate_name__icontains=search) | Q(phone__icontains=search)
                       | Q(position__icontains=search) | Q(institution_name__icontains=search)
                       | Q(reference__icontains=search))
    all_rows = InternOffer.objects.all()
    counters = {
        'waiting': all_rows.filter(status__in=InternOffer.OPEN_STATUSES, expires_at__gte=now).count(),
        'to_approve': all_rows.filter(status=InternOffer.STATUS_ACCEPTED).count(),
        'approved': all_rows.filter(status=InternOffer.STATUS_APPROVED).count(),
        'declined': all_rows.filter(status=InternOffer.STATUS_DECLINED).count(),
    }
    return render(request, 'hr/offer_list.html', {
        'offers': qs[:300], 'counters': counters, 'status_filter': status_filter,
        'search': search, 'statuses': InternOffer.STATUS_CHOICES,
    })


def _form_context(offer, posted, errors):
    settings = EnrolmentSettings.get()
    return {
        'offer': offer,
        'posted': posted,
        'errors': errors,
        'departments': Employee.DEPARTMENT_CHOICES,
        'work_modes': WORK_MODE_CHOICES,
        'money_modes': MONEY_MODE_CHOICES,
        'years': InternOffer.YEAR_CHOICES,
        'position_suggestions': [f"{t['label']} Intern" for t in settings.tracks],
        'durations': list(range(1, 13)),
    }


def _initial(offer):
    if offer is None:
        return {'work_mode': 'onsite', 'money_mode': MONEY_NONE, 'is_student': 'on',
                'terms': DEFAULT_TERMS, 'department': 'software',
                'start_date': timezone.localdate().isoformat(), 'duration_months': '3'}
    data = {name: getattr(offer, name) or '' for name in TEXT_FIELDS}
    data.update({
        'start_date': offer.start_date.isoformat() if offer.start_date else '',
        'duration_months': str(offer.duration_months or ''),
        'amount': '' if offer.amount is None else f'{offer.amount:.2f}'.rstrip('0').rstrip('.'),
        'is_student': 'on' if offer.is_student else '',
        'accept_days': '',
    })
    return data


def _clean(posted):
    """Validate the HR form. Returns (cleaned values, errors)."""
    errors, clean = {}, {}
    for name in TEXT_FIELDS:
        clean[name] = (posted.get(name) or '').strip()
    if not clean['candidate_name']:
        errors['candidate_name'] = "Enter the candidate's name."
    if not clean['position']:
        errors['position'] = 'Enter the position you are offering.'
    if not clean['phone'] and not clean['email']:
        errors['phone'] = 'Enter a phone number or an email so you can send the link.'
    if clean['department'] not in dict(Employee.DEPARTMENT_CHOICES):
        clean['department'] = ''
    if clean['work_mode'] not in dict(WORK_MODE_CHOICES):
        clean['work_mode'] = 'onsite'
    if clean['money_mode'] not in dict(MONEY_MODE_CHOICES):
        clean['money_mode'] = MONEY_NONE
    if clean['year_of_study'] not in dict(InternOffer.YEAR_CHOICES):
        clean['year_of_study'] = ''
    clean['is_student'] = bool(posted.get('is_student'))
    if not clean['is_student']:
        clean.update(institution_name='', course='', year_of_study='')

    try:
        clean['start_date'] = date.fromisoformat(posted.get('start_date') or '')
    except ValueError:
        errors['start_date'] = 'Choose the start date.'
    months = (posted.get('duration_months') or '').strip()
    clean['duration_months'] = int(months) if months.isdigit() and 1 <= int(months) <= 24 else None

    amount = (posted.get('amount') or '').replace(',', '').strip()
    clean['amount'] = None
    if clean['money_mode'] != MONEY_NONE:
        try:
            clean['amount'] = Decimal(amount)
            if clean['amount'] <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            errors['amount'] = 'Enter the monthly amount, or choose "Free".'
    return clean, errors


@enrolment_admin
def offer_form(request, pk=None):
    offer = get_object_or_404(InternOffer, pk=pk) if pk else None
    if offer and not offer.is_editable:
        messages.error(request, 'The candidate has already answered this offer, so it can no longer be changed.')
        return redirect('offer_detail', pk=offer.pk)

    errors = {}
    posted = _initial(offer)
    if request.method == 'POST':
        posted = request.POST.dict()
        clean, errors = _clean(request.POST)
        if not errors:
            offer = offer or InternOffer(created_by=request.user)
            for name, value in clean.items():
                setattr(offer, name, value)
            days = (request.POST.get('accept_days') or '').strip()
            if days.isdigit() and 1 <= int(days) <= 60:
                offer.expires_at = timezone.now() + timedelta(days=int(days))
            offer.save()
            messages.success(request, f'Offer {offer.reference} saved. Send it on WhatsApp or copy the link.')
            return redirect('offer_detail', pk=offer.pk)
    return render(request, 'hr/offer_form.html', _form_context(offer, posted, errors))


@enrolment_admin
def offer_detail(request, pk):
    offer = get_object_or_404(InternOffer.objects.select_related('enrolment', 'created_by', 'approved_by'), pk=pk)
    return render(request, 'hr/offer_detail.html', {
        'offer': offer,
        'url': offer.public_url(request),
        'whatsapp': offer.whatsapp_url(request),
        'approved_whatsapp': offer.approved_whatsapp_url(request),
    })


@enrolment_admin
def offer_preview(request, pk):
    """The letter as the candidate sees it; signed and stamped once approved."""
    offer = get_object_or_404(InternOffer, pk=pk)
    ctx = letter_context(offer, show_company_sign=offer.can_download)
    return render(request, 'offers/copy.html', ctx)


@enrolment_admin
def offer_pdf(request, pk):
    offer = get_object_or_404(InternOffer, pk=pk)
    pdf = render_offer_pdf(offer, base_url=request.build_absolute_uri('/'),
                           show_company_sign=offer.can_download)
    if pdf is None:
        return redirect('offer_preview', pk=pk)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{offer_pdf_filename(offer)}"'
    return response


@enrolment_admin
@require_POST
def offer_approve(request, pk):
    offer = get_object_or_404(InternOffer, pk=pk)
    try:
        offer.approve(request.user, create_enrolment=bool(request.POST.get('create_enrolment')))
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, 'Offer approved. The candidate can now download their offer letter.'
                         + (' Their enrolment link is ready too.' if offer.enrolment_id else ''))
    return redirect('offer_detail', pk=pk)


@enrolment_admin
@require_POST
def offer_create_enrolment(request, pk):
    offer = get_object_or_404(InternOffer, pk=pk)
    if offer.status == InternOffer.STATUS_APPROVED and not offer.enrolment_id:
        offer.enrolment = offer.build_enrolment(request.user)
        offer.save(update_fields=['enrolment', 'updated_at'])
        messages.success(request, 'Enrolment link created.')
    return redirect('offer_detail', pk=pk)


@enrolment_admin
@require_POST
def offer_cancel(request, pk):
    offer = get_object_or_404(InternOffer, pk=pk)
    if offer.status in InternOffer.OPEN_STATUSES + (InternOffer.STATUS_ACCEPTED,):
        offer.status = InternOffer.STATUS_CANCELLED
        offer.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Offer withdrawn. The link no longer opens.')
    else:
        messages.error(request, 'This offer can no longer be withdrawn.')
    return redirect('offer_detail', pk=pk)


@enrolment_admin
@require_POST
def offer_extend(request, pk):
    offer = get_object_or_404(InternOffer, pk=pk)
    if offer.status in InternOffer.OPEN_STATUSES:
        offer.expires_at = default_offer_expiry()
        offer.save(update_fields=['expires_at', 'updated_at'])
        messages.success(request, 'Respond-by date moved 14 days out. The same link works.')
    return redirect('offer_detail', pk=pk)
