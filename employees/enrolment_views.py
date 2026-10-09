"""Public internship enrolment form - no login, reached only by the secret token."""

import re
from datetime import date
from pathlib import Path

from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from PIL import Image, UnidentifiedImageError

from .agreement_views import _client_ip
from .enrolment_models import OTHER_TRACK, EnrolmentSettings, InternEnrolment

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
DOCUMENT_EXTS = IMAGE_EXTS | {'.pdf'}

TEXT_FIELDS = ('full_name', 'phone', 'whatsapp', 'email', 'address', 'guardian_name',
               'guardian_phone', 'college_name', 'course', 'register_number', 'track_other', 'skills')
CHOICE_FIELDS = ('year_of_study', 'track', 'duration_months', 'work_mode')
DATE_FIELDS = ('date_of_birth', 'preferred_start_date')
REQUIRED = ('full_name', 'phone', 'email', 'date_of_birth', 'address', 'guardian_name',
            'guardian_phone', 'college_name', 'course', 'year_of_study', 'track',
            'preferred_start_date', 'duration_months', 'work_mode')
#: (field, allowed extensions, required)
UPLOADS = (('photo', IMAGE_EXTS, True), ('id_proof', DOCUMENT_EXTS, True),
           ('resume', DOCUMENT_EXTS, False), ('college_letter', DOCUMENT_EXTS, False))

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _digits(value):
    return ''.join(ch for ch in value if ch.isdigit())


def _choices(settings):
    """Options per choice field. Area, duration and work mode come from
    EnrolmentSettings; a field left with a single option is not asked at all
    (e.g. onsite only) and that option is filled in for the student."""
    return {
        'year_of_study': InternEnrolment.YEAR_CHOICES,
        'track': settings.track_choices(),
        'duration_months': settings.duration_choices(),
        'work_mode': settings.work_mode_choices(),
    }


def _fixed(choices):
    return {name: opts[0][0] for name, opts in choices.items() if len(opts) == 1}


#: The form, section by section: (name, label, input type, autocomplete, hint).
#: Required-ness comes from REQUIRED / UPLOADS so it is defined once.
SECTIONS = (
    ('About you', (
        ('full_name', 'Full name (as on your ID)', 'text', 'name', ''),
        ('date_of_birth', 'Date of birth', 'date', 'bday', ''),
        ('phone', 'Phone', 'tel', 'tel', ''),
        ('whatsapp', 'WhatsApp number', 'tel', 'tel', 'If different from your phone'),
        ('email', 'Email', 'email', 'email', ''),
        ('address', 'Home address', 'textarea', 'street-address', ''),
        ('guardian_name', 'Parent / guardian name', 'text', 'off', ''),
        ('guardian_phone', 'Parent / guardian phone', 'tel', 'off', 'For emergencies'),
    )),
    ('Your education', (
        ('college_name', 'College / institution', 'text', 'organization', ''),
        ('course', 'Course and branch', 'text', 'off', 'e.g. B.Tech Computer Science, BCA, MBA'),
        ('year_of_study', 'Current year', 'select', 'off', ''),
        ('register_number', 'University register number', 'text', 'off', ''),
    )),
    ('Your internship', (
        ('track', 'Area you want to intern in', 'select', 'off', ''),
        ('track_other', 'Which area?', 'text', 'off', 'Only if you chose Other'),
        ('preferred_start_date', 'Preferred start date', 'date', 'off', ''),
        ('duration_months', 'Duration', 'select', 'off', ''),
        ('work_mode', 'How you want to work', 'select', 'off', ''),
        ('skills', 'What do you already know?', 'textarea', 'off',
         'Languages, tools or courses you have done. Fine to leave blank if you are just starting.'),
    )),
)
UPLOAD_LABELS = {
    'photo': ('Photo of your face',
              'A clear, recent photo with your face fully visible, looking at the camera. '
              'JPG or PNG, up to 5 MB'),
    'id_proof': ('ID proof', 'Aadhaar, college ID or driving licence - PDF or photo, up to 5 MB'),
    'resume': ('Resume', 'PDF, up to 5 MB'),
    'college_letter': ('College letter / NOC', 'If your college gave you one'),
}


def _context(enrolment, errors=None, posted=None):
    errors = errors or {}
    settings = EnrolmentSettings.get()
    choices = _choices(settings)
    fixed = _fixed(choices)
    if posted is None:
        posted = {
            'full_name': enrolment.full_name or enrolment.invite_name,
            'phone': enrolment.phone or enrolment.invite_phone,
            'email': enrolment.email or enrolment.invite_email,
        }
    sections = []
    for title, fields in SECTIONS:
        rows = []
        for name, label, kind, autocomplete, hint in fields:
            if name in fixed or (name == 'track_other' and not settings.allow_other_track):
                continue
            rows.append({
                'name': name, 'label': label, 'type': kind, 'autocomplete': autocomplete,
                'hint': hint, 'value': posted.get(name, ''), 'error': errors.get(name, ''),
                'required': name in REQUIRED, 'choices': choices.get(name, ()),
                'wide': kind == 'textarea',
            })
        sections.append({'title': title, 'fields': rows})
    uploads = [{
        'name': name, 'label': UPLOAD_LABELS[name][0], 'hint': UPLOAD_LABELS[name][1],
        'required': required, 'error': errors.get(name, ''),
        'attached': bool(getattr(enrolment, name)),
        'accept': ','.join(sorted(exts)),
    } for name, exts, required in UPLOADS]
    return {
        'enrolment': enrolment,
        'sections': sections,
        'uploads': uploads,
        'errors': errors,
        'confirmed': bool(posted.get('confirm')),
        'other_track': OTHER_TRACK,
        'doc': {'heading': 'Internship Enrolment'},
    }


@require_http_methods(['GET', 'POST'])
def enrolment_form(request, token):
    enrolment = get_object_or_404(InternEnrolment, token=token)
    if enrolment.status in (InternEnrolment.STATUS_SUBMITTED, InternEnrolment.STATUS_APPROVED,
                            InternEnrolment.STATUS_REJECTED):
        return redirect('enrolment_done', token=token)
    if enrolment.status == InternEnrolment.STATUS_CANCELLED:
        return render(request, 'enrolment/closed.html', {'doc': {'heading': 'Internship Enrolment'}})
    if enrolment.is_expired:
        return render(request, 'enrolment/expired.html', {'doc': {'heading': 'Internship Enrolment'}})

    if request.method == 'POST':
        return _submit(request, enrolment)
    enrolment.mark_opened()
    return render(request, 'enrolment/form.html', _context(enrolment))


def _submit(request, enrolment):
    posted = {k: (request.POST.get(k) or '').strip() for k in
              TEXT_FIELDS + CHOICE_FIELDS + DATE_FIELDS + ('confirm',)}
    choices = _choices(EnrolmentSettings.get())
    posted.update(_fixed(choices))
    errors = {}

    for name in REQUIRED:
        if not posted[name]:
            errors[name] = 'This is required.'
    for name, options in choices.items():
        if posted[name] and posted[name] not in dict(options):
            errors[name] = 'Choose one of the options.'
    if posted['track'] == OTHER_TRACK and not posted['track_other']:
        errors['track_other'] = 'Tell us which area.'
    for name in ('phone', 'whatsapp', 'guardian_phone'):
        if posted[name] and not 10 <= len(_digits(posted[name])) <= 13:
            errors[name] = 'Enter a valid phone number.'
    if posted['email'] and not EMAIL_RE.match(posted['email']):
        errors['email'] = 'Enter a valid email address.'

    dates = {}
    for name in DATE_FIELDS:
        if posted[name] and name not in errors:
            try:
                dates[name] = date.fromisoformat(posted[name])
            except ValueError:
                errors[name] = 'Enter a valid date.'
    dob = dates.get('date_of_birth')
    if dob and not (date(1950, 1, 1) <= dob <= timezone.localdate()):
        errors['date_of_birth'] = 'Enter your real date of birth.'
    if not request.POST.get('confirm'):
        errors['confirm'] = 'Please confirm your details are correct.'

    # Valid files are kept even when something else is wrong, so a student
    # fixing a typo does not have to attach everything again.
    for name, exts, required in UPLOADS:
        upload = request.FILES.get(name)
        if upload is None:
            if required and not getattr(enrolment, name):
                errors[name] = 'Please attach this file.'
            continue
        problem = _check_upload(upload, exts)
        if problem:
            errors[name] = problem
            continue
        old = getattr(enrolment, name)
        if old:
            old.delete(save=False)
        getattr(enrolment, name).save(upload.name, upload, save=False)
        enrolment.save(update_fields=[name, 'updated_at'])

    if errors:
        return render(request, 'enrolment/form.html', _context(enrolment, errors, posted), status=400)

    for name in TEXT_FIELDS + CHOICE_FIELDS:
        setattr(enrolment, name, posted[name])
    if posted['track'] == OTHER_TRACK:
        enrolment.track = 'Other'
    else:
        enrolment.track_other = ''
    enrolment.date_of_birth = dates['date_of_birth']
    enrolment.preferred_start_date = dates['preferred_start_date']
    enrolment.status = InternEnrolment.STATUS_SUBMITTED
    enrolment.submitted_at = timezone.now()
    enrolment.ip_address = _client_ip(request)
    enrolment.user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]
    enrolment.save()
    return redirect('enrolment_done', token=enrolment.token)


def _check_upload(upload, exts):
    if Path(upload.name).suffix.lower() not in exts:
        allowed = ', '.join(sorted(e.lstrip('.').upper() for e in exts))
        return f'Upload a {allowed} file.'
    if upload.size > MAX_UPLOAD_BYTES:
        return 'This file is larger than 5 MB.'
    if Path(upload.name).suffix.lower() in IMAGE_EXTS:
        try:
            Image.open(upload).verify()
        except (UnidentifiedImageError, OSError, SyntaxError):
            return 'This image could not be read. Try another photo.'
        finally:
            upload.seek(0)
    elif upload.read(5) != b'%PDF-':
        upload.seek(0)
        return 'This PDF could not be read.'
    upload.seek(0)
    return None


def enrolment_done(request, token):
    enrolment = get_object_or_404(InternEnrolment, token=token)
    if enrolment.status in InternEnrolment.OPEN_STATUSES:
        return redirect('enrolment_form', token=token)
    return render(request, 'enrolment/done.html',
                  {'enrolment': enrolment, 'doc': {'heading': 'Internship Enrolment'}})
