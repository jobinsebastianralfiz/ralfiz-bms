"""Shared certificate PDF rendering.

Both the HR web view (`core.views.certificate_pdf`) and the mobile API
(`employees.views.CertificatePDFView`) render the same document, so the
context and the WeasyPrint call live here rather than being duplicated.
"""

import base64
from io import BytesIO

from django.conf import settings
from django.template.loader import render_to_string


def _asset_uris():
    """file:// URIs for the print assets.

    WeasyPrint is handed a bare HTML string with no base URL, so every
    reference has to be absolute.
    """
    static_dir = settings.BASE_DIR / 'static' / 'certificates'
    return {
        'header_logo': (static_dir / 'headerlogo.png').as_uri(),
        # Keyed-out variants for tinted stock; see build_certificate_assets.
        'header_logo_alpha': (static_dir / 'headerlogo_alpha.png').as_uri(),
        'footer_logo_alpha': (static_dir / 'footer_right_logo_alpha.png').as_uri(),
        'signature': (static_dir / 'jobin_signature.png').as_uri(),
        'seal': (static_dir / 'seal.png').as_uri(),
        'footer_logo': (static_dir / 'footer_right_logo.png').as_uri(),
        'bottom_graphics': (static_dir / 'bottom_graphics.png').as_uri(),
        # Fonts are bundled because the Railway image ships no system fonts.
        'font_dir': (static_dir / 'fonts').as_uri(),
        # The navy design: WeasyPrint has no filter or blur, so the gradient
        # field and the white knockouts are pre-rendered.
        'certificate_bg': (static_dir / 'certificate_bg.png').as_uri(),
        'header_logo_white': (static_dir / 'headerlogo_white.png').as_uri(),
        'rt_mark_white': (static_dir / 'rt_mark_white.png').as_uri(),
        'signature_white': (static_dir / 'jobin_signature_white.png').as_uri(),
        'seal_white': (static_dir / 'seal_white.png').as_uri(),
    }


def _qr_base64(verify_url):
    import qrcode

    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(verify_url)
    qr.make(fit=True)
    buffer = BytesIO()
    qr.make_image(fill_color='black', back_color='white').save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


def _recipient_subtitle(certificate):
    parts = []
    if certificate.register_number:
        parts.append(f'Register No. {certificate.register_number}')
    if certificate.college_name:
        parts.append(certificate.college_name)
    return ' · '.join(parts)


def split_title(title):
    """Split a stored title into the design's two lines.

    The artboard sets a large CERTIFICATE over a letterspaced "OF INTERNSHIP".
    Titles are stored as one field, so "INTERNSHIP CERTIFICATE" becomes
    ("CERTIFICATE", "OF INTERNSHIP") and "CERTIFICATE OF MERIT" becomes
    ("CERTIFICATE", "OF MERIT"). A title with no such word is left whole.
    """
    import re

    raw = (title or '').strip()
    if not raw:
        return 'CERTIFICATE', ''

    words = raw.upper().split()
    if 'CERTIFICATE' not in words:
        return raw.upper(), ''

    rest = ' '.join(w for w in words if w != 'CERTIFICATE').strip()
    if not rest:
        return 'CERTIFICATE', ''
    if not rest.startswith('OF '):
        rest = f'OF {rest}'
    return 'CERTIFICATE', re.sub(r'\s+', ' ', rest)


def _density(rendered_body, skills, show_recipient_name):
    """How tightly to set the prose so the certificate stays on one page.

    Bodies are admin-authored, so the amount of copy swings widely between
    three lines and three paragraphs plus a skills list. Estimate how much
    vertical space the content wants and pick a type scale to match.
    """
    import re

    text = re.sub(r'<[^>]+>', ' ', rendered_body)
    length = len(' '.join(text.split()))
    # A skill costs a whole line even when it is two words.
    length += 45 * len(skills or [])
    # The presented-to / name / rule / college block is worth a paragraph.
    if show_recipient_name:
        length += 300
    if length < 520:
        return 'roomy'
    if length < 980:
        return 'normal'
    if length < 1450:
        return 'dense'
    return 'packed'


def build_context(certificate, request=None):
    """Everything `employees/certificate_pdf.html` needs."""
    path = f'/api/employees/certificates/verify/{certificate.verification_id}/'
    if request is not None:
        verify_url = request.build_absolute_uri(path)
        verify_host = request.get_host().split(':')[0]
    else:
        verify_url = f'https://ralfizdigital.in{path}'
        verify_host = 'ralfizdigital.in'

    rendered_body = certificate.render_body_html()

    # The design leads with the recipient's name set large. Older bodies
    # open with "This is to certify that Mr. X ...", so only promote the
    # name when the body has not already spent it.
    name = (certificate.student_name or '').strip()
    show_recipient_name = bool(name) and name.lower() not in rendered_body.lower()

    title_main, title_sub = split_title(certificate.title)

    context = {
        'cert': certificate,
        'title_main': title_main,
        'title_sub': title_sub,
        'qr_base64': _qr_base64(verify_url),
        'verify_url': verify_url,
        'verify_host': verify_host,
        'rendered_body': rendered_body,
        'wish_text': certificate.render_wish_text(),
        'date_of_issuance_fmt': certificate.date_of_issuance.strftime('%d %B %Y'),
        'show_recipient_name': show_recipient_name,
        # The navy design always prints the name in its pill, so the block
        # always costs vertical space regardless of what the body says.
        'density': _density(rendered_body, certificate.skills, True),
        'recipient_sub': _recipient_subtitle(certificate),
    }
    context.update(_asset_uris())
    return context


def render_pdf(certificate, request=None):
    """Return the certificate as PDF bytes."""
    import weasyprint

    html = render_to_string('employees/certificate_pdf.html', build_context(certificate, request))
    return weasyprint.HTML(string=html).write_pdf()


def pdf_filename(certificate):
    student = certificate.student_name.replace(' ', '_')
    number = certificate.certificate_number.replace('/', '_')
    return f'Certificate_{student}_{number}.pdf'
