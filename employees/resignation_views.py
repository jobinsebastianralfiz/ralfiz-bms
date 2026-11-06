"""Public resignation form and the two letters - no login, reached by the token.

The person picks a reason, explains it, proposes a last working day and signs
by typing their name. Once HR approves, the same link hands over the signed
resignation and the relieving letter, both on the company letterhead.
"""
import logging
from datetime import date

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .agreement_views import _client_ip, brand_letterhead, company_countersignature
from .resignation_models import ResignationRequest

logger = logging.getLogger(__name__)

DOC = {'heading': 'Resignation Letter'}
KINDS = {'letter': 'RESIGNATION', 'relieving': 'RELIEVING LETTER'}


def _get(token):
    return get_object_or_404(ResignationRequest.objects.select_related('employee__user'), token=token)


@require_http_methods(['GET', 'POST'])
def resignation_form(request, token):
    res = _get(token)
    if res.status == ResignationRequest.STATUS_CANCELLED:
        return render(request, 'resignations/closed.html', {'res': res, 'doc': DOC})
    if res.status not in ResignationRequest.OPEN_STATUSES:
        return redirect('resignation_done', token=token)
    if res.is_expired:
        return render(request, 'resignations/closed.html', {'res': res, 'doc': DOC, 'expired': True})

    errors, posted = {}, {}
    if request.method == 'POST':
        posted = request.POST.dict()
        errors = _submit(request, res, posted)
        if not errors:
            return redirect('resignation_done', token=token)
    else:
        res.mark_opened()
    return render(request, 'resignations/form.html', {
        'res': res, 'doc': DOC, 'employee': res.employee, 'errors': errors, 'posted': posted,
        'reasons': ResignationRequest.REASON_CHOICES, 'today': timezone.localdate(),
    }, status=400 if errors else 200)


def _submit(request, res, posted):
    errors = {}
    category = posted.get('reason_category', '')
    reason = (posted.get('reason') or '').strip()
    signed_name = (posted.get('signed_name') or '').strip()
    if category not in dict(ResignationRequest.REASON_CHOICES):
        errors['reason_category'] = 'Choose the main reason.'
    if len(reason) < 10:
        errors['reason'] = 'Tell us a little more about why you are leaving.'
    try:
        lwd = date.fromisoformat(posted.get('last_working_day') or '')
        if lwd < res.employee.joining_date:
            errors['last_working_day'] = 'This is before your joining date.'
    except ValueError:
        lwd = None
        errors['last_working_day'] = 'Choose your last working day.'
    if not signed_name:
        errors['signed_name'] = 'Type your full name to sign.'
    if posted.get('agree') != 'on':
        errors['agree'] = 'Please confirm the declaration.'
    if errors:
        return errors

    res.reason_category = category
    res.reason = reason[:3000]
    res.last_working_day = lwd
    res.signed_name = signed_name[:200]
    res.status = ResignationRequest.STATUS_SUBMITTED
    res.submitted_at = timezone.now()
    res.ip_address = _client_ip(request)
    res.user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]
    res.body_hash = res.compute_body_hash()
    res.save()
    return {}


def resignation_done(request, token):
    res = _get(token)
    if res.status in ResignationRequest.OPEN_STATUSES:
        return redirect('resignation_form', token=token)
    return render(request, 'resignations/done.html', {'res': res, 'doc': DOC})


# ---------------------------------------------------------------------------
# The letters, on the blue letterhead
# ---------------------------------------------------------------------------

def letter_context(res, kind, for_pdf=False, pdf_url=''):
    return {
        'res': res,
        'employee': res.employee,
        'kind': kind,
        'doc_title': KINDS[kind],
        'letterhead': brand_letterhead(),
        'sign': company_countersignature(for_pdf=True),
        'for_pdf': for_pdf,
        'pdf_url': pdf_url,
    }


def render_resignation_pdf(res, kind, base_url=None):
    try:
        from weasyprint import HTML
    except Exception as exc:  # ImportError, or OSError from the native libs
        logger.warning('WeasyPrint unavailable, serving HTML letter instead: %s', exc)
        return None
    html = render_to_string('resignations/letterhead.html', letter_context(res, kind, for_pdf=True))
    try:
        return HTML(string=html, base_url=base_url).write_pdf()
    except Exception as exc:
        logger.exception('Failed to render resignation PDF: %s', exc)
        return None


def pdf_filename(res, kind):
    label = 'Relieving-Letter' if kind == 'relieving' else 'Resignation'
    return f'Ralfiz-{label}-{res.reference.replace("/", "-")}.pdf'


def pdf_response(res, kind, request, disposition='attachment'):
    pdf = render_resignation_pdf(res, kind, base_url=request.build_absolute_uri('/'))
    if pdf is None:
        return None
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'{disposition}; filename="{pdf_filename(res, kind)}"'
    return response


def resignation_document(request, token, kind):
    res = _get(token)
    if not res.can_download:
        return redirect('resignation_done', token=token)
    return render(request, 'resignations/letterhead.html',
                  letter_context(res, kind, pdf_url=f'/resign/{res.token}/{kind}.pdf'))


def resignation_document_pdf(request, token, kind):
    res = _get(token)
    if not res.can_download:
        return redirect('resignation_done', token=token)
    return pdf_response(res, kind, request) or redirect(f'/resign/{res.token}/{kind}/')
