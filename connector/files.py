"""Short-lived download links for invoice and quote PDFs.

Tool results are text, so the connector cannot hand Claude the PDF bytes.
Instead get_invoice_pdf / get_quote_pdf return a signed link to this view,
which renders the PDF through the same owner API view the mobile app uses.
The link names the user it was minted for and is re-checked on download, so
it stops working when that person loses owner access, and it expires after
PDF_LINK_MAX_AGE seconds.
"""

from django.contrib.auth.models import User
from django.core import signing
from django.http import HttpResponse
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from employees.views import OwnerInvoicePDFView, OwnerQuotePDFView

from .auth import can_use_connector

PDF_LINK_MAX_AGE = 60 * 60
SALT = 'connector.pdf'

VIEWS = {
    'invoice': OwnerInvoicePDFView,
    'quote': OwnerQuotePDFView,
}


def pdf_link(request, user, kind, object_id, with_gst):
    token = signing.dumps({'k': kind, 'id': str(object_id), 'u': user.pk, 'g': bool(with_gst)},
                          salt=SALT, compress=True)
    return request.build_absolute_uri(reverse('connector_pdf', kwargs={'token': token}))


def pdf_download(request, token):
    try:
        claim = signing.loads(token, salt=SALT, max_age=PDF_LINK_MAX_AGE)
    except signing.SignatureExpired:
        return HttpResponse('This download link has expired. Ask Claude for a new one.',
                            status=410, content_type='text/plain')
    except signing.BadSignature:
        return HttpResponse('Invalid download link.', status=404, content_type='text/plain')

    view = VIEWS.get(claim.get('k'))
    user = User.objects.filter(pk=claim.get('u')).first()
    if view is None or not can_use_connector(user):
        return HttpResponse('This download link is no longer valid.', status=403,
                            content_type='text/plain')

    inner = APIRequestFactory().get('/', {'gst': '1' if claim.get('g') else '0'},
                                    HTTP_HOST=request.get_host(), secure=request.is_secure())
    force_authenticate(inner, user=user)
    response = view.as_view()(inner, pk=claim['id'])
    if response.status_code >= 400:
        detail = getattr(response, 'data', None) or {}
        message = detail.get('error') if isinstance(detail, dict) else None
        return HttpResponse(message or 'Could not create the PDF.', status=response.status_code,
                            content_type='text/plain')
    return response
