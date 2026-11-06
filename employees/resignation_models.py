"""Resignations: the leaver signs a resignation letter with their reason, HR
approves it, and the leaver can then download their signed resignation and a
relieving letter.

A request starts either from HR (who sends a personal link, like the
agreement and offer links) or from the person in the staff portal. Both end
on the same public form, so the person never needs to be signed in to sign.
"""
import hashlib
import json
import secrets
import uuid
from datetime import timedelta
from urllib.parse import quote

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def default_resignation_expiry():
    return timezone.now() + timedelta(days=14)


def generate_resignation_token():
    return secrets.token_urlsafe(32)


class ResignationRequest(models.Model):
    STATUS_SENT = 'sent'
    STATUS_OPENED = 'opened'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_SENT, 'Link sent'),
        (STATUS_OPENED, 'Opened'),
        (STATUS_SUBMITTED, 'To approve'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Not accepted'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    OPEN_STATUSES = (STATUS_SENT, STATUS_OPENED)
    ACTIVE_STATUSES = OPEN_STATUSES + (STATUS_SUBMITTED,)

    SOURCE_CHOICES = [('hr', 'Sent by HR'), ('self', 'Started by the person')]

    REASON_CHOICES = [
        ('internship_complete', 'Internship period completed'),
        ('higher_studies', 'Higher studies / exams'),
        ('new_job', 'Joining another job'),
        ('personal', 'Personal or family reasons'),
        ('health', 'Health reasons'),
        ('relocation', 'Relocating'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_resignation_token)
    reference = models.CharField(max_length=40, blank=True, db_index=True, help_text='e.g. RT/RES/26/0001')
    employee = models.ForeignKey('employees.Employee', on_delete=models.PROTECT, related_name='resignations')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_SENT, db_index=True)
    source = models.CharField(max_length=6, choices=SOURCE_CHOICES, default='hr')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='resignations_sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_resignation_expiry)
    first_opened_at = models.DateTimeField(null=True, blank=True)

    # ---- Filled in by the person leaving ----
    reason_category = models.CharField(max_length=24, choices=REASON_CHOICES, blank=True)
    reason = models.TextField(blank=True)
    last_working_day = models.DateField(null=True, blank=True, help_text='Requested by the person')
    signed_name = models.CharField(max_length=200, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    body_hash = models.CharField(max_length=64, blank=True)

    # ---- HR decision ----
    relieving_date = models.DateField(null=True, blank=True, help_text='Final last working day')
    relieving_note = models.TextField(blank=True, help_text='Optional paragraph printed on the relieving letter')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='resignations_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    hr_notes = models.TextField(blank=True)

    # ---- Thank-you card, sent after approval ----
    thanks_note = models.TextField(blank=True, help_text='Personal message on the thank-you card')
    thanks_sent_at = models.DateTimeField(null=True, blank=True)

    # ---- Internship certificate, issued from the existing certificate system ----
    certificate = models.OneToOneField('employees.Certificate', on_delete=models.SET_NULL, null=True,
                                       blank=True, related_name='resignation')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.reference} - {self.employee.full_name} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.reference:
            prefix = f'RT/RES/{str(timezone.now().year)[-2:]}/'
            last = (ResignationRequest.objects.filter(reference__startswith=prefix)
                    .order_by('-reference').values_list('reference', flat=True).first())
            try:
                nxt = int(last.rsplit('/', 1)[-1]) + 1 if last else 1
            except ValueError:
                nxt = 1
            self.reference = f'{prefix}{nxt:04d}'
        super().save(*args, **kwargs)

    # ---- State ----
    @property
    def is_expired(self):
        return self.status in self.OPEN_STATUSES and timezone.now() > self.expires_at

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES and not self.is_expired

    @property
    def can_download(self):
        return self.status == self.STATUS_APPROVED

    @property
    def status_label(self):
        return 'Expired' if self.is_expired else self.get_status_display()

    @property
    def status_css(self):
        if self.is_expired:
            return 'background: var(--warning-bg); color: var(--warning);'
        return {
            self.STATUS_SENT: 'background: var(--info-bg); color: var(--info);',
            self.STATUS_OPENED: 'background: var(--info-bg); color: var(--info);',
            self.STATUS_SUBMITTED: 'background: var(--warning-bg); color: var(--warning);',
            self.STATUS_APPROVED: 'background: var(--success-bg); color: var(--success);',
            self.STATUS_REJECTED: 'background: var(--danger-bg); color: var(--danger);',
        }.get(self.status, 'background: var(--bg-hover); color: var(--text-muted);')

    @property
    def is_intern(self):
        return self.employee.employment_type == 'intern' or self.employee.role == 'intern'

    @property
    def name(self):
        return self.signed_name or self.employee.full_name

    @property
    def first_name(self):
        return (self.name or '').split(' ')[0] or 'there'

    @property
    def role_title(self):
        return self.employee.designation or ('Intern' if self.is_intern else 'Employee')

    @property
    def reason_line(self):
        label = self.get_reason_category_display() if self.reason_category else ''
        if label and self.reason:
            return f'{label}. {self.reason}'
        return label or self.reason

    @property
    def final_date(self):
        return self.relieving_date or self.last_working_day

    @property
    def tenure_label(self):
        """'4 months', '1 year 2 months', '3 weeks' - joining date to relieving date."""
        start, end = self.employee.joining_date, self.final_date
        if not start or not end or end < start:
            return ''
        months = (end.year - start.year) * 12 + end.month - start.month - (end.day < start.day)
        if months < 1:
            weeks = (end - start).days // 7
            return f'{weeks} week{"s" if weeks != 1 else ""}' if weeks else ''
        years, months = divmod(months, 12)
        parts = []
        if years:
            parts.append(f'{years} year{"s" if years != 1 else ""}')
        if months:
            parts.append(f'{months} month{"s" if months != 1 else ""}')
        return ' '.join(parts)

    @property
    def default_thanks_note(self):
        return (f'Thank you for everything you brought to Ralfiz, {self.first_name}: your effort, your ideas '
                'and your good company. It has been a real pleasure having you on the team. We are proud of '
                'what you learned and built here, and we cannot wait to see where you go next.')

    @property
    def thanks_text(self):
        return self.thanks_note or self.default_thanks_note

    # ---- Evidence ----
    def compute_body_hash(self):
        payload = json.dumps({
            'reference': self.reference,
            'employee_id': self.employee.employee_id,
            'name': self.signed_name,
            'reason_category': self.reason_category,
            'reason': self.reason,
            'last_working_day': self.last_working_day.isoformat() if self.last_working_day else '',
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    # ---- Transitions ----
    def mark_opened(self):
        if self.first_opened_at is None:
            self.first_opened_at = timezone.now()
            if self.status == self.STATUS_SENT:
                self.status = self.STATUS_OPENED
            self.save(update_fields=['first_opened_at', 'status', 'updated_at'])

    def approve(self, by, relieving_date=None, note='', deactivate=False):
        if self.status != self.STATUS_SUBMITTED:
            raise ValueError('Only a signed resignation can be approved.')
        from django.db import transaction
        with transaction.atomic():
            self.status = self.STATUS_APPROVED
            self.relieving_date = relieving_date or self.last_working_day
            self.relieving_note = (note or '').strip()
            self.approved_by = by
            self.approved_at = timezone.now()
            self.save()
            if deactivate:
                emp = self.employee
                emp.status = 'inactive'
                emp.save(update_fields=['status'])
                if emp.user_id and not emp.user.is_superuser:
                    emp.user.is_active = False
                    emp.user.save(update_fields=['is_active'])

    def reject(self, by, reason=''):
        if self.status != self.STATUS_SUBMITTED:
            raise ValueError('Only a signed resignation can be declined.')
        self.status = self.STATUS_REJECTED
        self.rejection_reason = (reason or '').strip()
        self.approved_by = by
        self.approved_at = timezone.now()
        self.save()

    @property
    def has_certificate(self):
        return bool(self.certificate_id) and self.certificate.status == 'published'

    def _enrolment(self):
        try:
            return self.employee.enrolment
        except Exception:  # RelatedObjectDoesNotExist: joined before enrolment links existed
            return None

    @property
    def certificate_college(self):
        """Best guess at their college: enrolment form first, then the offer letter."""
        enrolment = self._enrolment()
        if enrolment is None:
            return ''
        if enrolment.college_name:
            return enrolment.college_name
        offer = getattr(enrolment, 'offer', None)
        return getattr(offer, 'institution_name', '') or ''

    @property
    def default_salutation(self):
        return {'female': 'Ms.', 'male': 'Mr.'}.get(self.employee.gender, '')

    def issue_certificate(self, template, salutation, by, college_name=None):
        """Fill a certificate from the person's records and publish it.

        Uses the chosen certificate template's wording, so HR keeps editing
        the text in one place (Certificates > Templates).
        """
        if self.has_certificate:
            return self.certificate
        if self.status != self.STATUS_APPROVED:
            raise ValueError('Approve the resignation before issuing the certificate.')
        from .models import Certificate

        emp = self.employee
        enrolment = self._enrolment()
        start, end = emp.joining_date, self.final_date
        cert = Certificate(
            template=template,
            certificate_type=template.certificate_type,
            title=template.title,
            salutation=salutation,
            gender='female' if salutation in ('Ms.', 'Mrs.') else 'male',
            student_name=emp.full_name,
            register_number=getattr(enrolment, 'register_number', '') or '',
            college_name=(self.certificate_college if college_name is None else college_name.strip())[:300],
            course_name=(getattr(enrolment, 'track', '') or getattr(enrolment, 'track_other', '') or ''),
            position=self.role_title,
            start_date=start,
            end_date=end,
            duration_days=(end - start).days + 1 if start and end else None,
            mode={'onsite': 'offline', 'remote': 'online', 'hybrid': 'hybrid'}.get(emp.work_mode, 'offline'),
            body_text=template.body_text,
            wish_text=template.wish_text,
            date_of_issuance=timezone.localdate(),
            issued_by=by,
            status='published',
        )
        cert.save()
        if not emp.gender:
            # HR just told us; keep it for next time.
            emp.gender = cert.gender
            emp.save(update_fields=['gender'])
        self.certificate = cert
        self.save(update_fields=['certificate', 'updated_at'])
        return cert

    # ---- Links ----
    def public_path(self):
        return f'/resign/{self.token}/'

    def public_url(self, request=None):
        return request.build_absolute_uri(self.public_path()) if request else self.public_path()

    def thanks_path(self):
        return f'/resign/{self.token}/thanks/'

    def thanks_whatsapp_url(self, request=None):
        if not self.can_download:
            return ''
        link = request.build_absolute_uri(self.thanks_path()) if request else self.thanks_path()
        return self._wa(
            f'Hi {self.first_name} 💙\n\n'
            'A little thank-you card from all of us at Ralfiz Technologies:\n'
            f'{link}\n\n'
            'Our office doors are always open. Drop by any time!'
        )

    def _wa(self, message):
        digits = self.employee.whatsapp_number
        return f'https://wa.me/{digits}?text={quote(message)}' if digits else ''

    def whatsapp_url(self, request=None):
        return self._wa(
            f'Hi {self.first_name},\n\n'
            'Please fill in and sign your resignation letter from Ralfiz Technologies here:\n'
            f'{self.public_url(request)}\n\nThe link is personal to you. Thank you.'
        )

    def approved_whatsapp_url(self, request=None):
        if not self.can_download:
            return ''

        def link(path):
            return request.build_absolute_uri(path) if request else path

        certificate = (f'🎓 Internship certificate:\n{link(f"/resign/{self.token}/certificate.pdf")}\n\n'
                       if self.has_certificate else '')
        return self._wa(
            f'Hi {self.first_name},\n\n'
            'Your resignation has been accepted. Your relieving date is '
            f'*{self.final_date:%d %b %Y}*.\n\n'
            f'📄 Relieving letter:\n{link(f"/resign/{self.token}/relieving.pdf")}\n\n'
            f'📝 Your signed resignation:\n{link(f"/resign/{self.token}/letter.pdf")}\n\n'
            f'{certificate}'
            'Thank you for your time with us, and all the best for what comes next!\n'
            'Team Ralfiz Technologies'
        )
