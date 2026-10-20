"""vCard 3.0 for a DigitalCard: what "Save contact" downloads.

3.0 rather than 4.0 because iOS Contacts and most Android dialers import it
without asking which app to use. Lines are folded at 75 octets as the spec
requires; Outlook drops the photo otherwise.
"""
import base64
import io
import logging

log = logging.getLogger(__name__)


def _escape(value):
    return (value or '').replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')


def _fold(line):
    raw = line.encode('utf-8')
    if len(raw) <= 75:
        return line
    parts, chunk = [], b''
    for ch in line:
        b = ch.encode('utf-8')
        if len(chunk) + len(b) > (75 if not parts else 74):
            parts.append(chunk.decode('utf-8'))
            chunk = b''
        chunk += b
    parts.append(chunk.decode('utf-8'))
    return '\r\n '.join(parts)


def _photo_b64(card):
    """The card photo (a company card's logo first) as a small JPEG, base64. '' if there is none or it can't be read."""
    image = card.logo if card.is_company and card.logo else card.photo
    if not image:
        return ''
    try:
        from PIL import Image, ImageOps
        with image.open('rb') as fh:
            img = ImageOps.exif_transpose(Image.open(fh))
            if img.mode in ('RGBA', 'LA', 'P'):     # transparent logos go on white, not black
                img = img.convert('RGBA')
                bg = Image.new('RGB', img.size, 'white')
                bg.paste(img, mask=img.split()[-1])
                img = bg
            size = (320, 320)
            img = ImageOps.pad(img.convert('RGB'), size, color='white') if image == card.logo else ImageOps.fit(img.convert('RGB'), size)
        out = io.BytesIO()
        img.save(out, 'JPEG', quality=82)
        return base64.b64encode(out.getvalue()).decode()
    except Exception:
        log.warning('card %s: photo left out of the vCard', card.pk, exc_info=True)
        return ''


def build_vcard(card, company_name, card_url):
    lines = ['BEGIN:VCARD', 'VERSION:3.0']
    if card.is_company:
        # iOS and macOS list it under the company name, not as a person
        lines += ['N:;;;;', f'FN:{_escape(card.full_name)}', f'ORG:{_escape(card.full_name)}', 'X-ABShowAs:COMPANY']
    else:
        names = card.full_name.split()
        last, first = (names[-1], ' '.join(names[:-1])) if len(names) > 1 else ('', card.full_name)
        lines += [f'N:{_escape(last)};{_escape(first)};;;', f'FN:{_escape(card.full_name)}']
        if company_name:
            lines.append(f'ORG:{_escape(company_name)}')
        if card.designation:
            lines.append(f'TITLE:{_escape(card.designation)}')
    lines.append(f'TEL;TYPE=CELL,VOICE:{card.phone_link}')
    if card.whatsapp and card.whatsapp_number != ''.join(c for c in card.phone if c.isdigit()):
        lines.append(f'TEL;TYPE=CELL:+{card.whatsapp_number}')
    if card.email:
        lines.append(f'EMAIL;TYPE=INTERNET,WORK:{card.email}')
    if card.website:
        lines.append(f'URL;TYPE=WORK:{card.website}')
    for _label, _icon, url in card.socials:
        lines.append(f'URL:{url}')
    if card.address:
        lines.append(f'ADR;TYPE=WORK:;;{_escape(card.address)};;;;')
    note = card.bio + ('\n' if card.bio else '') + f'Digital card: {card_url}'
    lines.append(f'NOTE:{_escape(note)}')
    photo = _photo_b64(card)
    if photo:
        lines.append(f'PHOTO;ENCODING=b;TYPE=JPEG:{photo}')
    lines.append('END:VCARD')
    return '\r\n'.join(_fold(l) for l in lines) + '\r\n'
