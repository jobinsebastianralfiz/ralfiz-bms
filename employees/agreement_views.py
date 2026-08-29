"""Public agreement signing - no login, reached only by the secret token."""
import base64
import binascii
import logging
import mimetypes

from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import AgreementRequest

logger = logging.getLogger(__name__)

MAX_SIGNATURE_BYTES = 2 * 1024 * 1024


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _get_request_or_404(token):
    # Tokens are secrets/opaque; never reveal whether one merely expired vs. never existed.
    return get_object_or_404(AgreementRequest.objects.select_related('employee__user'), token=token)


def _closed_response(request, agreement, template_name='agreements/closed.html', status=200):
    return render(request, template_name, {'agreement': agreement, 'doc': agreement.snapshot_json}, status=status)


def _decode_signature(data_url):
    """Turn a canvas data URL into a saveable PNG. Returns None when absent/invalid."""
    if not data_url or not data_url.startswith('data:image/png;base64,'):
        return None
    raw = data_url.split(',', 1)[1]
    try:
        decoded = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        return None
    if not decoded or len(decoded) > MAX_SIGNATURE_BYTES:
        return None
    if not decoded.startswith(b'\x89PNG\r\n\x1a\n'):
        return None
    return decoded


@require_http_methods(['GET', 'POST'])
def agreement_sign(request, token):
    agreement = _get_request_or_404(token)

    if agreement.status in (AgreementRequest.STATUS_CANCELLED, AgreementRequest.STATUS_SUPERSEDED):
        return _closed_response(request, agreement)
    if agreement.has_responded:
        return redirect('agreement_done', token=agreement.token)
    if agreement.is_expired:
        return _closed_response(request, agreement, 'agreements/expired.html')

    if request.method == 'POST':
        return _handle_submit(request, agreement)

    agreement.mark_viewed()
    return render(request, 'agreements/sign.html', _sign_context(agreement))


def _sign_context(agreement, errors=None, posted=None):
    employee = agreement.employee
    doc = agreement.snapshot_json or {}
    return {
        'agreement': agreement,
        'doc': doc,
        'employee': employee,
        'sections': doc.get('sections', []),
        'intro_lines': [line for line in (doc.get('intro_html') or '').split('\n') if line.strip()],
        'ask_college': agreement.asks_college_fields,
        'today': timezone.localdate(),
        'errors': errors or {},
        'posted': posted or {},
    }


def _handle_submit(request, agreement):
    decision = request.POST.get('decision', '')
    posted = request.POST.dict()
    errors = {}

    if decision not in ('continue', 'discontinue'):
        errors['decision'] = 'Please choose whether you wish to continue or discontinue.'
        return render(request, 'agreements/sign.html', _sign_context(agreement, errors, posted), status=400)

    if decision == 'continue':
        full_name = (request.POST.get('full_name') or '').strip()
        signed_name = (request.POST.get('signed_name') or '').strip()
        college = (request.POST.get('college_name') or '').strip()
        course = (request.POST.get('course_department') or '').strip()
        domain = (request.POST.get('internship_domain') or '').strip()
        agreed = request.POST.get('agreed_to_terms') == 'on'

        if not full_name:
            errors['full_name'] = 'Please enter your full name.'
        if not signed_name:
            errors['signed_name'] = 'Please type your name to sign.'
        if not agreed:
            errors['agreed_to_terms'] = 'Please confirm that you have read and accept the terms.'
        if agreement.asks_college_fields:
            if not college:
                errors['college_name'] = 'Please enter your college.'
            if not course:
                errors['course_department'] = 'Please enter your course or department.'
            if not domain:
                errors['internship_domain'] = 'Please enter your internship domain.'

        if errors:
            return render(request, 'agreements/sign.html', _sign_context(agreement, errors, posted), status=400)

        agreement.decision = 'continue'
        agreement.status = AgreementRequest.STATUS_ACCEPTED
        agreement.full_name = full_name
        agreement.signed_name = signed_name
        agreement.college_name = college
        agreement.course_department = course
        agreement.internship_domain = domain
        agreement.agreed_to_terms = True

        signature = _decode_signature(request.POST.get('signature_data', ''))
        if signature:
            agreement.signature_image.save(
                f'sig-{agreement.id}.png', ContentFile(signature), save=False,
            )
    else:
        agreement.decision = 'discontinue'
        agreement.status = AgreementRequest.STATUS_DECLINED
        agreement.decline_reason = (request.POST.get('decline_reason') or '').strip()
        agreement.full_name = (request.POST.get('full_name') or '').strip() or agreement.employee.full_name

    agreement.signed_date = timezone.localdate()
    agreement.responded_at = timezone.now()
    agreement.ip_address = _client_ip(request)
    agreement.user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]
    agreement.body_hash = agreement.compute_body_hash()
    agreement.save()

    return redirect('agreement_done', token=agreement.token)


def agreement_done(request, token):
    agreement = _get_request_or_404(token)
    if not agreement.has_responded:
        return redirect('agreement_sign', token=agreement.token)
    return render(request, 'agreements/done.html', {
        'agreement': agreement,
        'doc': agreement.snapshot_json or {},
        'employee': agreement.employee,
    })


# ---------------------------------------------------------------------------
# Signed copy - the record the signer (and HR) can download afterwards.
# ---------------------------------------------------------------------------

def _agreement_css():
    """Stylesheet text for the PDF. Inlined so WeasyPrint never has to fetch
    the static file back over HTTP from the server rendering it."""
    from django.conf import settings
    from django.contrib.staticfiles import finders

    path = finders.find('css/agreement.css')
    if not path:
        path = settings.BASE_DIR / 'static' / 'css' / 'agreement.css'
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            return handle.read()
    except OSError:
        logger.warning('agreement.css not found for PDF rendering')
        return ''


def build_copy_context(agreement, request=None, for_pdf=False):
    """Context for the signed copy.

    WeasyPrint has no session, so for the PDF the signature is embedded as a
    data URI rather than linked by URL.
    """
    doc = agreement.snapshot_json or {}
    signature_src = ''
    if agreement.signature_image:
        if for_pdf:
            signature_src = _signature_data_uri(agreement)
        else:
            signature_src = agreement.signature_image.url

    return {
        'agreement': agreement,
        'doc': doc,
        'employee': agreement.employee,
        'sections': doc.get('sections', []),
        'intro_lines': [line for line in (doc.get('intro_html') or '').split('\n') if line.strip()],
        'ask_college': agreement.asks_college_fields,
        'signature_src': signature_src,
        'for_pdf': for_pdf,
        'inline_css': _agreement_css() if for_pdf else '',
        'pdf_url': f'/agreement/{agreement.token}/copy.pdf' if request else '',
    }


def _signature_data_uri(agreement):
    """Inline the signature so the PDF renderer needs no file access."""
    try:
        with agreement.signature_image.open('rb') as handle:
            raw = handle.read()
    except (OSError, ValueError):
        return ''
    mime = mimetypes.guess_type(agreement.signature_image.name)[0] or 'image/png'
    return f'data:{mime};base64,' + base64.b64encode(raw).decode()


def _pdf_filename(agreement):
    safe_ref = agreement.reference.replace('/', '-') or str(agreement.id)
    return f'Ralfiz-Agreement-{safe_ref}.pdf'


def render_agreement_pdf(agreement, base_url=None):
    """Render the signed copy to PDF bytes, or None when WeasyPrint can't run.

    WeasyPrint needs native pango/cairo libraries. They ship in the Docker
    image but are often missing on a dev machine, so callers fall back to the
    printable HTML instead of failing.
    """
    try:
        from weasyprint import HTML
    except Exception as exc:  # ImportError, or OSError from the native libs
        logger.warning('WeasyPrint unavailable, serving HTML copy instead: %s', exc)
        return None

    html = render_to_string('agreements/copy.html',
                            build_copy_context(agreement, for_pdf=True))
    try:
        return HTML(string=html, base_url=base_url).write_pdf()
    except Exception as exc:
        logger.exception('Failed to render agreement PDF: %s', exc)
        return None


def agreement_copy(request, token):
    """Printable signed copy at the signer's own link."""
    agreement = _get_request_or_404(token)
    if not agreement.has_responded:
        return redirect('agreement_sign', token=agreement.token)
    return render(request, 'agreements/copy.html',
                  build_copy_context(agreement, request=request))


def agreement_copy_pdf(request, token):
    """PDF download. Falls back to the printable page when PDF rendering is
    unavailable, so the signer always gets their copy."""
    agreement = _get_request_or_404(token)
    if not agreement.has_responded:
        return redirect('agreement_sign', token=agreement.token)

    pdf = render_agreement_pdf(agreement, base_url=request.build_absolute_uri('/'))
    if pdf is None:
        return redirect('agreement_copy', token=agreement.token)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{_pdf_filename(agreement)}"'
    return response
