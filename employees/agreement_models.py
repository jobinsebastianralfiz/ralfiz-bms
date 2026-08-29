"""Agreement e-signing: an editable master template, and one signable request
per person.

The request snapshots the template body at send time, so later edits to the
wording or the fee never rewrite what somebody already signed.
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


def default_expiry():
    return timezone.now() + timedelta(days=14)


def generate_token():
    return secrets.token_urlsafe(32)


class AgreementTemplate(models.Model):
    """Master copy of an agreement. Body lives in JSON so HR can edit the
    wording and the fee without a deploy."""

    AGREEMENT_TYPE_CHOICES = [
        ('internship_continuation', 'Internship Continuation'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=20, default='v1.0')
    agreement_type = models.CharField(max_length=30, choices=AGREEMENT_TYPE_CHOICES,
                                      default='internship_continuation')

    heading = models.CharField(max_length=200, default='Internship Continuation & Learning Agreement',
                               help_text='Large title at the top of the document')
    eyebrow = models.CharField(max_length=100, blank=True, default='INTERNSHIP CONTINUATION CONFIRMATION',
                               help_text='Small label above the title')
    intro_html = models.TextField(blank=True, help_text='Opening paragraphs, one per line')

    sections = models.JSONField(
        default=list, blank=True,
        help_text='[{"no": 1, "title": "...", "body": "...", "bullets": [...], '
                  '"callout": {"style": "info|warn|dark", "text": "..."}}]'
    )

    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                      help_text='Monthly internship fee, e.g. 750.00')
    fee_in_words = models.CharField(max_length=200, blank=True)
    fee_note = models.CharField(max_length=300, blank=True,
                                help_text='Small print under the fee, e.g. applicable for each month')

    confirmation_html = models.TextField(blank=True,
                                         help_text='Final confirmation callout, shown just above the form')
    continue_label = models.CharField(max_length=100, default='Continue my internship')
    decline_label = models.CharField(max_length=100, default='Discontinue my internship')

    require_college_fields = models.BooleanField(
        default=True,
        help_text='Ask for College / Course / Domain. Interns yes; overridden off for non-interns.'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name} ({self.version})"

    def build_snapshot(self):
        """Freeze everything the signing page renders."""
        return {
            'name': self.name,
            'version': self.version,
            'agreement_type': self.agreement_type,
            'heading': self.heading,
            'eyebrow': self.eyebrow,
            'intro_html': self.intro_html,
            'sections': self.sections,
            'monthly_fee': str(self.monthly_fee) if self.monthly_fee is not None else '',
            'fee_in_words': self.fee_in_words,
            'fee_note': self.fee_note,
            'confirmation_html': self.confirmation_html,
            'continue_label': self.continue_label,
            'decline_label': self.decline_label,
            'require_college_fields': self.require_college_fields,
        }


class AgreementRequest(models.Model):
    """One signable link for one person."""

    STATUS_PENDING = 'pending'
    STATUS_VIEWED = 'viewed'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_CANCELLED = 'cancelled'
    STATUS_SUPERSEDED = 'superseded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Sent'),
        (STATUS_VIEWED, 'Opened'),
        (STATUS_ACCEPTED, 'Continuing'),
        (STATUS_DECLINED, 'Discontinued'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_SUPERSEDED, 'Superseded'),
    ]

    DECISION_CHOICES = [
        ('continue', 'Continue'),
        ('discontinue', 'Discontinue'),
    ]

    OPEN_STATUSES = (STATUS_PENDING, STATUS_VIEWED)
    RESPONDED_STATUSES = (STATUS_ACCEPTED, STATUS_DECLINED)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_token,
                             help_text='Secret in the public URL')
    reference = models.CharField(max_length=40, blank=True, db_index=True,
                                 help_text='Human-readable ref, e.g. RT/AGR/26/0007')

    employee = models.ForeignKey('employees.Employee', on_delete=models.PROTECT,
                                 related_name='agreement_requests')
    template = models.ForeignKey(AgreementTemplate, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='requests')

    # Frozen copy of what this person is shown.
    snapshot_json = models.JSONField(default=dict, blank=True)
    snapshot_version = models.CharField(max_length=20, blank=True)
    snapshot_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    batch = models.UUIDField(null=True, blank=True, db_index=True,
                             help_text='Groups links generated in one send')

    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='agreements_sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)

    first_viewed_at = models.DateTimeField(null=True, blank=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    # ---- Response ----
    decision = models.CharField(max_length=12, choices=DECISION_CHOICES, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    full_name = models.CharField(max_length=200, blank=True)
    college_name = models.CharField(max_length=300, blank=True)
    course_department = models.CharField(max_length=200, blank=True)
    internship_domain = models.CharField(max_length=200, blank=True)

    signed_name = models.CharField(max_length=200, blank=True,
                                   help_text='Typed signature - this is the binding one')
    signature_image = models.ImageField(upload_to='agreements/signatures/', null=True, blank=True,
                                        help_text='Optional drawn signature')
    signed_date = models.DateField(null=True, blank=True)
    agreed_to_terms = models.BooleanField(default=False)
    decline_reason = models.TextField(blank=True)

    # ---- Evidence ----
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    body_hash = models.CharField(max_length=64, blank=True,
                                 help_text='SHA-256 of the snapshot the signer agreed to')

    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='supersedes')
    hr_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['batch']),
        ]

    def __str__(self):
        return f"{self.reference or self.token[:8]} - {self.employee.full_name} ({self.get_status_display()})"

    # ---- State ----
    @property
    def is_expired(self):
        return self.status in self.OPEN_STATUSES and timezone.now() > self.expires_at

    @property
    def is_open(self):
        """Can still be signed right now."""
        return self.status in self.OPEN_STATUSES and not self.is_expired

    @property
    def has_responded(self):
        return self.status in self.RESPONDED_STATUSES

    @property
    def effective_status(self):
        """Status for display; expiry is computed, never stored eagerly."""
        return 'expired' if self.is_expired else self.status

    @property
    def status_label(self):
        if self.is_expired:
            return 'Expired'
        return self.get_status_display()

    @property
    def status_css(self):
        """Inline badge colours. The app's CSS has no .bg-info/.bg-secondary,
        so colour these from theme vars rather than adding a stylesheet rule
        that whitenoise would serve stale."""
        muted = 'background: var(--bg-hover); color: var(--text-muted);'
        if self.is_expired:
            return muted
        return {
            self.STATUS_PENDING: 'background: var(--info-bg); color: var(--info);',
            self.STATUS_VIEWED: 'background: var(--warning-bg); color: var(--warning);',
            self.STATUS_ACCEPTED: 'background: var(--success-bg); color: var(--success);',
            self.STATUS_DECLINED: 'background: var(--danger-bg); color: var(--danger);',
        }.get(self.status, muted)

    @property
    def asks_college_fields(self):
        """Interns get College / Course / Domain; staff don't."""
        if not self.snapshot_json.get('require_college_fields', True):
            return False
        return self.employee.employment_type == 'intern' or self.employee.role == 'intern'

    # ---- Links ----
    def public_path(self):
        return f"/agreement/{self.token}/"

    def public_url(self, request=None):
        path = self.public_path()
        return request.build_absolute_uri(path) if request else path

    def whatsapp_url(self, request=None):
        """wa.me deep link with a prefilled message. Empty when no phone on file."""
        digits = ''.join(ch for ch in (self.employee.phone or '') if ch.isdigit())
        if not digits:
            return ''
        if len(digits) == 10:
            digits = '91' + digits
        heading = self.snapshot_json.get('heading') or 'Internship Continuation Agreement'
        message = (
            f"Hi {self.employee.full_name},\n\n"
            f"Please read the {heading} from Ralfiz Technologies and confirm "
            f"whether you wish to continue:\n{self.public_url(request)}\n\n"
            "The link is personal to you. Thank you."
        )
        return f"https://wa.me/{digits}?text={quote(message)}"

    # ---- Transitions ----
    def mark_viewed(self):
        now = timezone.now()
        if self.first_viewed_at is None:
            self.first_viewed_at = now
        self.last_viewed_at = now
        self.view_count += 1
        fields = ['first_viewed_at', 'last_viewed_at', 'view_count', 'updated_at']
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_VIEWED
            fields.append('status')
        self.save(update_fields=fields)

    def compute_body_hash(self):
        payload = json.dumps(self.snapshot_json, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        if not self.reference:
            year = str(timezone.now().year)[-2:]
            prefix = f"RT/AGR/{year}/"
            last = AgreementRequest.objects.filter(
                reference__startswith=prefix
            ).order_by('-reference').first()
            nxt = 1
            if last:
                try:
                    nxt = int(last.reference.split('/')[-1]) + 1
                except ValueError:
                    nxt = 1
            self.reference = f"{prefix}{str(nxt).zfill(4)}"
        super().save(*args, **kwargs)
