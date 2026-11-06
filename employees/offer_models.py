"""Internship offer letters, sent before enrolment.

HR fills in the position, dates and money, and the candidate (who has no login
or Employee record yet) gets a personal link to read and accept the offer. HR
then approves the acceptance, which unlocks the countersigned copy for the
candidate to download and, optionally, creates their enrolment link so the
same person moves straight on to the enrolment form.
"""
import calendar
import hashlib
import json
import secrets
import uuid
from datetime import timedelta
from decimal import Decimal
from urllib.parse import quote

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .agreement_models import MONEY_MODE_CHOICES, MONEY_NONE, MONEY_STIPEND, rupees_in_words
from .enrolment_models import WORK_MODE_CHOICES, InternEnrolment, duration_label

DEFAULT_TERMS = '\n'.join((
    'This internship is a learning programme and is not an offer of employment.',
    'You will follow office timings and mark your attendance every working day through the '
    'Ralfiz staff portal.',
    'Leave must be applied for through the staff portal and approved in advance.',
    'You will keep all client, project and company information confidential, during and after '
    'the internship.',
    'Work you create during the internship belongs to Ralfiz Technologies and its clients.',
    'An internship certificate is issued on successful completion, subject to attendance and '
    'performance.',
    'Ralfiz Technologies may end the internship early for misconduct or repeated unapproved '
    'absence.',
    'This offer is subject to you completing the enrolment form with a valid ID proof.',
))


def default_offer_expiry():
    return timezone.now() + timedelta(days=14)


def generate_offer_token():
    return secrets.token_urlsafe(32)


def _wa_digits(phone):
    digits = ''.join(ch for ch in (phone or '') if ch.isdigit())
    return '91' + digits if len(digits) == 10 else digits


class InternOffer(models.Model):
    STATUS_SENT = 'sent'
    STATUS_OPENED = 'opened'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_APPROVED = 'approved'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_SENT, 'Sent'),
        (STATUS_OPENED, 'Opened'),
        (STATUS_ACCEPTED, 'Accepted - to approve'),
        (STATUS_DECLINED, 'Declined'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    OPEN_STATUSES = (STATUS_SENT, STATUS_OPENED)

    YEAR_CHOICES = InternEnrolment.YEAR_CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_offer_token)
    reference = models.CharField(max_length=40, blank=True, db_index=True,
                                 help_text='e.g. RT/OFR/26/0001')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_SENT,
                              db_index=True)

    # ---- Candidate ----
    candidate_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # ---- The offer ----
    position = models.CharField(max_length=200, help_text='e.g. Flutter Developer Intern')
    department = models.CharField(max_length=20, blank=True,
                                  help_text='Employee department key, used when they enrol')
    start_date = models.DateField()
    duration_months = models.PositiveSmallIntegerField(null=True, blank=True)
    work_mode = models.CharField(max_length=10, choices=WORK_MODE_CHOICES, default='onsite')
    money_mode = models.CharField(max_length=10, choices=MONEY_MODE_CHOICES, default=MONEY_NONE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                 help_text='Monthly fee or stipend')
    terms = models.TextField(default=DEFAULT_TERMS, blank=True, help_text='One term per line')

    # ---- Education (HR may prefill; the candidate confirms when accepting) ----
    is_student = models.BooleanField(default=True)
    institution_name = models.CharField(max_length=300, blank=True)
    course = models.CharField(max_length=200, blank=True)
    year_of_study = models.CharField(max_length=10, choices=YEAR_CHOICES, blank=True)

    # ---- Link ----
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='offers_sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_offer_expiry)
    first_opened_at = models.DateTimeField(null=True, blank=True)

    # ---- Response ----
    responded_at = models.DateTimeField(null=True, blank=True)
    signed_name = models.CharField(max_length=200, blank=True)
    decline_reason = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    body_hash = models.CharField(max_length=64, blank=True,
                                 help_text='SHA-256 of the offer the candidate accepted')

    # ---- Approval ----
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='offers_approved')
    enrolment = models.OneToOneField(InternEnrolment, on_delete=models.SET_NULL, null=True,
                                     blank=True, related_name='offer')
    hr_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.reference} - {self.candidate_name} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.reference:
            prefix = f'RT/OFR/{str(timezone.now().year)[-2:]}/'
            last = (InternOffer.objects.filter(reference__startswith=prefix)
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
    def is_editable(self):
        """HR may fix the offer until the candidate has answered it."""
        return self.status in self.OPEN_STATUSES

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
            self.STATUS_ACCEPTED: 'background: var(--warning-bg); color: var(--warning);',
            self.STATUS_APPROVED: 'background: var(--success-bg); color: var(--success);',
            self.STATUS_DECLINED: 'background: var(--danger-bg); color: var(--danger);',
        }.get(self.status, 'background: var(--bg-hover); color: var(--text-muted);')

    @property
    def first_name(self):
        return (self.candidate_name or '').split(' ')[0] or 'there'

    @property
    def department_label(self):
        from .models import Employee
        return dict(Employee.DEPARTMENT_CHOICES).get(self.department, '')

    @property
    def duration_label(self):
        return duration_label(self.duration_months)

    @property
    def end_date(self):
        """Last day of the internship: start + N months - 1 day."""
        if not (self.start_date and self.duration_months):
            return None
        month = self.start_date.month - 1 + self.duration_months
        year = self.start_date.year + month // 12
        month = month % 12 + 1
        day = min(self.start_date.day, calendar.monthrange(year, month)[1])
        return self.start_date.replace(year=year, month=month, day=day) - timedelta(days=1)

    @property
    def money_amount(self):
        if self.money_mode == MONEY_NONE or not self.amount or self.amount <= 0:
            return None
        return Decimal(self.amount)

    @property
    def money_label(self):
        """One line for the key-details grid."""
        amount = self.money_amount
        if amount is None:
            return 'No fee and no stipend'
        rupees = f'₹{amount:,.2f}'.rstrip('0').rstrip('.')
        if self.money_mode == MONEY_STIPEND:
            return f'Stipend of {rupees} per month'
        return f'Internship fee of {rupees} per month'

    @property
    def money_words(self):
        return rupees_in_words(self.money_amount) if self.money_amount else ''

    @property
    def money_sentence(self):
        """The sentence in the letter body."""
        amount = self.money_amount
        if amount is None:
            return 'This internship carries no fee and no stipend.'
        rupees = f'₹{amount:,.2f}'.rstrip('0').rstrip('.')
        words = self.money_words
        if self.money_mode == MONEY_STIPEND:
            return (f'You will receive a monthly stipend of {rupees} ({words}), paid in arrears '
                    'for the days you attend.')
        return (f'A monthly internship fee of {rupees} ({words}) is payable by you, towards '
                'the structured training and mentoring provided.')

    @property
    def term_lines(self):
        return [line.strip() for line in (self.terms or '').splitlines() if line.strip()]

    @property
    def education_line(self):
        if not self.is_student:
            return ''
        bits = [self.course, self.get_year_of_study_display() if self.year_of_study else '',
                self.institution_name]
        return ', '.join(b for b in bits if b)

    # ---- Evidence ----
    def content_snapshot(self):
        """Everything the candidate is agreeing to, for the fingerprint."""
        return {
            'reference': self.reference,
            'candidate_name': self.candidate_name,
            'position': self.position,
            'start_date': self.start_date.isoformat() if self.start_date else '',
            'duration_months': self.duration_months,
            'work_mode': self.work_mode,
            'money_mode': self.money_mode,
            'amount': str(self.money_amount or ''),
            'terms': self.term_lines,
            'is_student': self.is_student,
            'institution_name': self.institution_name,
            'course': self.course,
            'year_of_study': self.year_of_study,
        }

    def compute_body_hash(self):
        payload = json.dumps(self.content_snapshot(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    # ---- Transitions ----
    def mark_opened(self):
        if self.first_opened_at is None:
            self.first_opened_at = timezone.now()
            if self.status == self.STATUS_SENT:
                self.status = self.STATUS_OPENED
            self.save(update_fields=['first_opened_at', 'status', 'updated_at'])

    def approve(self, by, create_enrolment=True):
        """HR countersigns an accepted offer; optionally opens their enrolment link."""
        from django.db import transaction

        if self.status != self.STATUS_ACCEPTED:
            raise ValueError('Only an accepted offer can be approved.')
        with transaction.atomic():
            self.status = self.STATUS_APPROVED
            self.approved_by = by
            self.approved_at = timezone.now()
            if create_enrolment and not self.enrolment_id:
                self.enrolment = self.build_enrolment(by)
            self.save()

    def build_enrolment(self, by):
        """An enrolment link with what the offer already knows filled in."""
        from .enrolment_models import EnrolmentSettings

        settings = EnrolmentSettings.get()
        track = ''
        matches = [t['label'] for t in settings.tracks if t.get('department') == self.department]
        if len(matches) == 1:
            track = matches[0]
        durations = {str(n) for n in settings.durations}
        return InternEnrolment.objects.create(
            invite_name=self.signed_name or self.candidate_name,
            invite_phone=self.phone,
            invite_email=self.email,
            created_by=by,
            college_name=self.institution_name if self.is_student else '',
            course=self.course if self.is_student else '',
            year_of_study=self.year_of_study if self.is_student else '',
            track=track,
            preferred_start_date=self.start_date,
            duration_months=(str(self.duration_months)
                             if str(self.duration_months) in durations else ''),
            work_mode=self.work_mode if self.work_mode in settings.work_modes else '',
        )

    # ---- Links ----
    def public_path(self):
        return f'/offer/{self.token}/'

    def public_url(self, request=None):
        return request.build_absolute_uri(self.public_path()) if request else self.public_path()

    def whatsapp_url(self, request=None):
        """Invite to read and accept. Empty when no phone."""
        digits = _wa_digits(self.phone)
        if not digits:
            return ''
        message = (
            f'Hi {self.first_name},\n\n'
            f'Congratulations! Ralfiz Technologies is pleased to offer you an internship as '
            f'*{self.position}*.\n\n'
            f'Please read your offer letter and accept it here:\n{self.public_url(request)}\n\n'
            f'Kindly respond by {timezone.localtime(self.expires_at):%d %b %Y}. '
            'The link is personal to you.'
        )
        return f'https://wa.me/{digits}?text={quote(message)}'

    def approved_whatsapp_url(self, request=None):
        """After approval: the offer letter download and the enrolment link."""
        digits = _wa_digits(self.phone)
        if not digits or not self.can_download:
            return ''

        def link(path):
            return request.build_absolute_uri(path) if request else path

        lines = [
            f'Hi {self.first_name},\n',
            f'Your internship offer as *{self.position}* at Ralfiz Technologies is confirmed. 🎉\n',
            f'📄 Download your offer letter:\n{link(f"/offer/{self.token}/copy.pdf")}\n',
        ]
        if self.enrolment_id and self.enrolment.is_open:
            lines.append('📝 Next, please fill in your enrolment form (keep a photo and ID proof '
                         f'ready):\n{self.enrolment.public_url(request)}\n')
        lines.append('Welcome aboard!\nTeam Ralfiz Technologies')
        return f'https://wa.me/{digits}?text={quote(chr(10).join(lines))}'
