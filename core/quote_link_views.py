"""Send a quote to the client as a link (WhatsApp / email). The client views
it, downloads the PDF, and accepts it with their name and signature, which
keeps the accepted quote as an agreement. Or they ask for changes."""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from employees.agreement_views import _client_ip, _decode_signature, _file_data_uri, company_countersignature

from .models import Quote
from .quote_link_models import QuoteLink

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------

@login_required
@require_POST
def quote_send_link(request, pk):
    """Make a fresh link for the client. Older unanswered links stop working,
    so the client only ever has the latest version."""
    quote = get_object_or_404(Quote, pk=pk)
    quote.links.filter(status__in=QuoteLink.OPEN_STATUSES).update(status=QuoteLink.STATUS_CANCELLED)
    link = QuoteLink.objects.create(quote=quote, with_gst=request.POST.get('with_gst') == '1',
                                    created_by=request.user)
    quote.status = 'sent'
    quote.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Link ready. Tap "Send on WhatsApp" to share it with the client.')
    return redirect(f"{redirect('quote_detail', pk=pk).url}?link={link.pk}#send")


@login_required
@require_POST
def quote_link_cancel(request, pk):
    link = get_object_or_404(QuoteLink, pk=pk)
    if link.is_open:
        link.status = QuoteLink.STATUS_CANCELLED
        link.save(update_fields=['status'])
        messages.success(request, 'Link cancelled. The client can no longer open it.')
    return redirect('quote_detail', pk=link.quote_id)


@login_required
def quote_link_signed_pdf(request, pk):
    link = get_object_or_404(QuoteLink, pk=pk, status=QuoteLink.STATUS_ACCEPTED)
    return _signed_pdf_response(request, link)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _context(link, for_pdf=False):
    from .views import quote_pdf_context
    ctx = quote_pdf_context(link.quote, link.with_gst)
    ctx.update({'public': True, 'link': link})
    if link.status == QuoteLink.STATUS_ACCEPTED:
        ctx['acceptance'] = {
            'link': link,
            'signature_src': (_file_data_uri(link.signature_image) if for_pdf else
                              (link.signature_image.url if link.signature_image else '')),
            'company': company_countersignature(for_pdf=for_pdf),
        }
    return ctx


def _render_pdf(request, link):
    from weasyprint import HTML
    from django.conf import settings
    ctx = _context(link, for_pdf=True)
    ctx['font_dir'] = (settings.BASE_DIR / 'static' / 'certificates' / 'fonts').as_uri()
    html = render_to_string('quotes/pdf.html', ctx)
    return HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()


def _pdf_response(pdf, filename):
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _signed_pdf_response(request, link):
    name = f'quote_{link.quote.quote_number}_accepted.pdf'.replace('/', '-')
    if link.signed_pdf:
        try:
            with link.signed_pdf.open('rb') as fh:
                return _pdf_response(fh.read(), name)
        except (OSError, ValueError):
            logger.warning('Signed quote PDF missing for %s; rebuilding', link.pk)
    try:
        return _pdf_response(_render_pdf(request, link), name)
    except Exception:
        logger.exception('Could not build signed quote PDF for %s', link.pk)
        return render(request, 'quotes/pdf.html', _context(link))


# ---------------------------------------------------------------------------
# Public: no login, reached only by the secret token
# ---------------------------------------------------------------------------

def _link_or_404(token):
    return get_object_or_404(
        QuoteLink.objects.select_related('quote__client', 'quote__lead').prefetch_related('quote__items'),
        token=token)


@require_http_methods(['GET', 'POST'])
def quote_public(request, token):
    link = _link_or_404(token)
    quote = link.quote
    base = {**_context(link), 'today': timezone.localdate()}

    if link.status == QuoteLink.STATUS_CANCELLED:
        return render(request, 'quotes/public_closed.html', base)
    if link.status in QuoteLink.RESPONDED_STATUSES:
        return render(request, 'quotes/public_done.html', base)
    if link.is_expired:
        return render(request, 'quotes/public_closed.html', {**base, 'expired': True})

    if request.method == 'GET':
        link.mark_viewed()
        return render(request, 'quotes/public.html', {**base, 'errors': {}, 'posted': {}, 'posted_addons': []})

    posted = request.POST.dict()
    decision = posted.get('decision')
    errors = {}
    if not posted.get('signer_name', '').strip():
        errors['signer_name'] = 'Please enter your name.'
    if decision == 'accept':
        if not posted.get('signed_name', '').strip():
            errors['signed_name'] = 'Please type your name to sign.'
        if posted.get('agreed') != 'on':
            errors['agreed'] = 'Please confirm that you accept this quotation.'
    elif decision == 'changes':
        if not posted.get('change_notes', '').strip():
            errors['change_notes'] = 'Please tell us what you would like changed.'
    else:
        errors['decision'] = 'Please choose to accept or request changes.'
    if errors:
        return render(request, 'quotes/public.html', {**base, 'errors': errors, 'posted': posted,
                                                      'posted_addons': request.POST.getlist('addons')}, status=400)

    link.signer_name = posted['signer_name'].strip()[:150]
    link.signer_designation = posted.get('signer_designation', '').strip()[:150]
    link.signer_company = posted.get('signer_company', '').strip()[:200]
    link.signer_email = posted.get('signer_email', '').strip()[:254] if '@' in posted.get('signer_email', '') else ''
    link.responded_at = timezone.now()
    link.ip_address = _client_ip(request)
    link.user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]
    if decision == 'accept':
        link.status = QuoteLink.STATUS_ACCEPTED
        link.signed_name = posted['signed_name'].strip()[:150]
        signature = _decode_signature(posted.get('signature_data', ''))
        if signature:
            link.signature_image.save(f'sig-{link.id}.png', ContentFile(signature), save=False)
        addon_ids = {str(i.pk) for i in quote.items.all() if i.is_optional}
        chosen = [v for v in request.POST.getlist('addons') if v in addon_ids]
        link.snapshot = link.build_snapshot(base, chosen)
        link.body_hash = link.hash_snapshot(link.snapshot)
        link.save()
        quote.status = 'accepted'
        quote.save(update_fields=['status', 'updated_at'])
        # Freeze the signed copy now, so later edits to the quote never change
        # what the client accepted.
        try:
            link.signed_pdf.save(f'{quote.quote_number}-accepted.pdf'.replace('/', '-'),
                                 ContentFile(_render_pdf(request, link)), save=True)
        except Exception:
            logger.exception('Could not freeze signed PDF for quote link %s', link.pk)
    else:
        link.status = QuoteLink.STATUS_CHANGES
        link.change_notes = posted['change_notes'].strip()[:5000]
        link.save()
    return redirect('quote_public', token=token)


def quote_public_pdf(request, token):
    """The quote as a PDF; once accepted, the signed copy."""
    link = _link_or_404(token)
    if link.status == QuoteLink.STATUS_CANCELLED:
        raise Http404
    if link.status == QuoteLink.STATUS_ACCEPTED:
        return _signed_pdf_response(request, link)
    try:
        return _pdf_response(_render_pdf(request, link),
                             f'quote_{link.quote.quote_number}.pdf'.replace('/', '-'))
    except Exception:
        logger.exception('Could not build quote PDF for link %s', link.pk)
        return render(request, 'quotes/pdf.html', _context(link))

