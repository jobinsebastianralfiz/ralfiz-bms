"""Public offer letter - no login, reached only by the secret token.

The candidate reads the offer, confirms their college details if they are a
student, and accepts by typing their name (or declines). The copy is
downloadable only after HR approves the acceptance.
"""
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .agreement_views import _agreement_css, _client_ip, brand_letterhead, company_countersignature
from .offer_models import InternOffer

logger = logging.getLogger(__name__)

DOC = {'heading': 'Internship Offer Letter'}


def _get(token):
    return get_object_or_404(InternOffer.objects.select_related('enrolment'), token=token)


def letter_context(offer, for_pdf=False, show_company_sign=False):
    """For the mobile accept page, which renders the letter in the agreement layout."""
    return {
        'offer': offer,
        'doc': DOC,
        'for_pdf': for_pdf,
        'company': company_countersignature(for_pdf=for_pdf),
        'show_company_sign': show_company_sign,
        'inline_css': _agreement_css() if for_pdf else '',
    }


@require_http_methods(['GET', 'POST'])
def offer_view(request, token):
    offer = _get(token)
    if offer.status == InternOffer.STATUS_CANCELLED:
        return render(request, 'offers/closed.html', {'offer': offer, 'doc': DOC})
    if offer.status not in InternOffer.OPEN_STATUSES:
        return redirect('offer_done', token=token)
    if offer.is_expired:
        return render(request, 'offers/closed.html', {'offer': offer, 'doc': DOC, 'expired': True})

    errors, posted = {}, {}
    if request.method == 'POST':
        posted = request.POST.dict()
        decision = posted.get('decision')
        if decision == 'accept':
            errors = _accept(request, offer, posted)
        elif decision == 'decline':
            _decline(request, offer, posted)
        else:
            errors['decision'] = 'Please choose Accept or Decline.'
        if not errors:
            return redirect('offer_done', token=token)
    else:
        offer.mark_opened()
        posted = {
            'institution_name': offer.institution_name,
            'course': offer.course,
            'year_of_study': offer.year_of_study,
        }

    ctx = letter_context(offer)
    ctx.update({'errors': errors, 'posted': posted, 'years': InternOffer.YEAR_CHOICES,
                'today': timezone.localdate()})
    return render(request, 'offers/view.html', ctx, status=400 if errors else 200)


def _stamp(request, offer):
    offer.responded_at = timezone.now()
    offer.ip_address = _client_ip(request)
    offer.user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]


def _accept(request, offer, posted):
    errors = {}
    signed_name = (posted.get('signed_name') or '').strip()
    if not signed_name:
        errors['signed_name'] = 'Type your full name to accept.'
    if posted.get('agree') != 'on':
        errors['agree'] = 'Please confirm you accept the terms of this offer.'
    edu = {k: (posted.get(k) or '').strip()[:300] for k in ('institution_name', 'course', 'year_of_study')}
    if offer.is_student:
        if not edu['institution_name']:
            errors['institution_name'] = 'Enter your college or institution.'
        if not edu['course']:
            errors['course'] = 'Enter your course.'
        if edu['year_of_study'] and edu['year_of_study'] not in dict(InternOffer.YEAR_CHOICES):
            errors['year_of_study'] = 'Choose your year.'
    if errors:
        return errors

    if offer.is_student:
        offer.institution_name = edu['institution_name']
        offer.course = edu['course'][:200]
        offer.year_of_study = edu['year_of_study']
    offer.signed_name = signed_name[:200]
    offer.status = InternOffer.STATUS_ACCEPTED
    _stamp(request, offer)
    # Hash after the education details are in, so the fingerprint covers what
    # the candidate actually confirmed.
    offer.body_hash = offer.compute_body_hash()
    offer.save()
    return {}


def _decline(request, offer, posted):
    offer.status = InternOffer.STATUS_DECLINED
    offer.decline_reason = (posted.get('decline_reason') or '').strip()[:2000]
    _stamp(request, offer)
    offer.save()


def offer_done(request, token):
    offer = _get(token)
    if offer.status in InternOffer.OPEN_STATUSES:
        return redirect('offer_view', token=token)
    return render(request, 'offers/done.html', {'offer': offer, 'doc': DOC})


def letterhead_context(offer, for_pdf=False, pdf_url=''):
    """The letter on the blue company letterhead used by invoices and quotes."""
    return {
        'offer': offer,
        'letterhead': brand_letterhead(),
        'sign': company_countersignature(for_pdf=True),
        'for_pdf': for_pdf,
        'pdf_url': pdf_url,
    }


def render_offer_pdf(offer, base_url=None):
    """PDF bytes, or None when WeasyPrint cannot run."""
    try:
        from weasyprint import HTML
    except Exception as exc:  # ImportError, or OSError from the native libs
        logger.warning('WeasyPrint unavailable, serving HTML offer instead: %s', exc)
        return None
    html = render_to_string('offers/letterhead.html', letterhead_context(offer, for_pdf=True))
    try:
        return HTML(string=html, base_url=base_url).write_pdf()
    except Exception as exc:
        logger.exception('Failed to render offer PDF: %s', exc)
        return None


def offer_pdf_filename(offer):
    return f'Ralfiz-Offer-Letter-{offer.reference.replace("/", "-")}.pdf'


def offer_copy(request, token):
    offer = _get(token)
    if not offer.can_download:
        return redirect('offer_done', token=token)
    return render(request, 'offers/letterhead.html',
                  letterhead_context(offer, pdf_url=f'/offer/{offer.token}/copy.pdf'))


def offer_copy_pdf(request, token):
    offer = _get(token)
    if not offer.can_download:
        return redirect('offer_done', token=token)
    pdf = render_offer_pdf(offer, base_url=request.build_absolute_uri('/'))
    if pdf is None:
        return redirect('offer_copy', token=token)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{offer_pdf_filename(offer)}"'
    return response
