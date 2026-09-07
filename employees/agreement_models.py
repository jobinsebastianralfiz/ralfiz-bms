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
from decimal import Decimal
from urllib.parse import quote

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
        'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
        'Seventeen', 'Eighteen', 'Nineteen']
TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']


def _under_thousand(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return (TENS[n // 10] + (' ' + ONES[n % 10] if n % 10 else '')).strip()
    return (ONES[n // 100] + ' Hundred' + (' and ' + _under_thousand(n % 100) if n % 100 else '')).strip()


def rupees_in_words(amount):
    """Indian-numbering words for a whole-rupee amount, e.g. 'Rupees Seven
    Hundred and Fifty only'. Returns '' for zero/None, since a free internship
    has no fee to spell out."""
    try:
        rupees = int(Decimal(amount))
    except (TypeError, ValueError, ArithmeticError):
        return ''
    if rupees <= 0:
        return ''

    parts = []
    for divisor, label in ((10000000, 'Crore'), (100000, 'Lakh'), (1000, 'Thousand')):
        if rupees >= divisor:
            parts.append(f'{_under_thousand(rupees // divisor)} {label}')
            rupees %= divisor
    if rupees:
        parts.append(_under_thousand(rupees))
    return 'Rupees ' + ' '.join(parts) + ' only'


class _NotSet:
    """Sentinel: lets an explicit None mean 'free', not 'use the default'."""


NOT_SET = _NotSet()


MONEY_FEE = 'fee'          # the intern pays Ralfiz
MONEY_STIPEND = 'stipend'  # Ralfiz pays the intern
MONEY_NONE = 'none'        # neither direction

MONEY_MODE_CHOICES = [
    (MONEY_FEE, 'Intern pays a monthly fee'),
    (MONEY_STIPEND, 'We pay the intern a monthly stipend'),
    (MONEY_NONE, 'Free - no fee and no stipend'),
]

LEARNING_BULLETS = [
    'Guidance and mentorship for assigned work',
    'Work-related learning materials and resources',
    'Technical guidance to improve practical skills',
    'Support and direction while completing assigned tasks',
    'Learning resources relevant to the internship domain',
    'Practical exposure through assigned projects and activities',
]


def default_money_copy():
    """Wording for each money arrangement, so one agreement covers all three.

    An internship can run any of three ways and HR picks per person when
    sending, so the money direction cannot live in the template's prose. The
    block for the chosen mode replaces the section marked `show_fee`.
    """
    return {
        MONEY_FEE: {
            'section_title': 'Monthly Internship Fee',
            'section_body': 'The fee supports the structured learning and guidance provided '
                            'during the internship, including:',
            'bullets': list(LEARNING_BULLETS),
            'amount_note': 'payable monthly by the intern',
            'agreed_note': 'Agreed to the monthly internship fee of {amount}.',
            'confirm_suffix': 'and to pay the applicable {amount} monthly internship fee',
        },
        MONEY_STIPEND: {
            'section_title': 'Monthly Stipend',
            'section_body': 'A monthly stipend is payable to you for the duration of the '
                            'internship, subject to the conditions below:',
            'bullets': [
                'The stipend is paid monthly in arrears, for the days actually attended',
                'The stipend is a contribution towards the cost of attending and is not a salary or wage',
                'Payment is subject to satisfactory attendance and participation for the month',
                'Any deduction for unapproved absence will be communicated to you before it is applied',
                'The stipend may be revised at renewal, in writing',
            ],
            'amount_note': 'payable monthly by Ralfiz Technologies, for the days attended',
            'agreed_note': 'Accepted on a monthly stipend of {amount}.',
            'confirm_suffix': 'on the stated monthly stipend of {amount}',
        },
        MONEY_NONE: {
            'section_title': 'Learning Support & Guidance',
            'section_body': 'This internship carries no monthly fee and no stipend. The structured '
                            'learning and guidance provided during the internship includes:',
            'bullets': list(LEARNING_BULLETS),
            'amount_note': '',
            'agreed_note': 'This internship carries no monthly fee and no stipend.',
            'confirm_suffix': '',
        },
    }


def default_expiry():
    return timezone.now() + timedelta(days=14)


def generate_token():
    return secrets.token_urlsafe(32)


class AgreementTemplate(models.Model):
    """Master copy of an agreement. Body lives in JSON so HR can edit the
    wording and the fee without a deploy."""

    AGREEMENT_TYPE_CHOICES = [
        ('internship_continuation', 'Internship Continuation'),
        ('internship_new_joinee', 'Internship - New Joinee'),
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

    money_mode = models.CharField(
        max_length=10, choices=MONEY_MODE_CHOICES, default=MONEY_FEE,
        help_text='Default arrangement. HR can pick a different one per person when sending.')
    money_copy = models.JSONField(
        default=default_money_copy, blank=True,
        help_text='Wording for each money arrangement (fee / stipend / none). The block for the '
                  'chosen mode replaces the section marked show_fee.')
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                      help_text='Monthly internship fee, e.g. 750.00')
    fee_in_words = models.CharField(max_length=200, blank=True)
    fee_note = models.CharField(max_length=300, blank=True,
                                help_text='Small print under the fee, e.g. applicable for each month')

    confirmation_html = models.TextField(blank=True,
                                         help_text='Final confirmation callout, shown just above the form')
    confirmation_free_html = models.TextField(
        blank=True,
        help_text='Confirmation callout used when the internship carries no monthly fee. '
                  'Falls back to confirmation_html when blank.')
    continue_label = models.CharField(max_length=100, default='Continue my internship')
    decline_label = models.CharField(max_length=100, default='Discontinue my internship')

    # The signing page and the signed copy used to hardcode the continuation
    # wording. A new joiner is accepting an offer, not deciding whether to
    # carry on, so every visible phrase is template copy. The defaults are the
    # exact strings that were hardcoded, which keeps existing agreements
    # rendering byte for byte as before.
    decision_heading = models.CharField(
        max_length=120, default='Continuation Decision',
        help_text='Heading above the YES / NO buttons.')
    accept_statement = models.CharField(
        max_length=200, default='I wish to continue my internship',
        help_text='The YES line recorded in the signed copy.')
    decline_statement = models.CharField(
        max_length=200, default='I do not wish to continue my internship',
        help_text='The NO line recorded in the signed copy.')
    accept_sub = models.CharField(
        max_length=120, default='with Ralfiz Technologies',
        help_text='Small print under the YES button in the numbered decision section.')
    decline_sub = models.CharField(
        max_length=120, default='end participation in the program',
        help_text='Small print under the NO button in the numbered decision section.')
    accept_confirm_text = models.CharField(
        max_length=300,
        default='I confirm I have read and understood the terms, and I agree to continue my internship',
        help_text='Checkbox beside the signature. The money sentence is appended to it.')
    decline_heading = models.CharField(
        max_length=120, default='Discontinue Internship')
    decline_intro = models.TextField(
        default='You are about to inform Ralfiz Technologies that you do not wish to '
                'continue your internship.',
        help_text='Shown above the reason box on the decline panel.')
    decline_button_label = models.CharField(
        max_length=100, default='Confirm discontinuation')
    accepted_pill = models.CharField(
        max_length=60, default='Continuing',
        help_text='Outcome shown on the thank-you page when they say yes.')
    declined_pill = models.CharField(
        max_length=60, default='Discontinued',
        help_text='Outcome shown on the thank-you page when they say no.')
    done_accepted_html = models.TextField(
        default='Your confirmation to <strong>continue your internship</strong> with Ralfiz '
                'Technologies has been recorded. Our team will be in touch about the next steps.',
        help_text='Thank-you paragraph after they say yes.')
    done_declined_html = models.TextField(
        default='We have noted that you do not wish to continue your internship. Thank you for '
                'letting us know, and we wish you all the best.',
        help_text='Paragraph after they say no.')

    require_college_fields = models.BooleanField(
        default=True,
        help_text='Ask for College / Course / Domain. Interns yes; overridden off for non-interns.'
    )
    college_fields_optional = models.BooleanField(
        default=False,
        help_text='Ask for College and Course but let them be left blank. For agreements sent to '
                  'people who may not be studying. The internship domain is still required.'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name} ({self.version})"

    def resolve_fee(self, fee_override=NOT_SET):
        """The fee this agreement actually carries.

        `None` or 0 means a free internship; passing nothing falls back to the
        template's own fee.
        """
        fee = self.monthly_fee if fee_override is NOT_SET else fee_override
        if fee in (None, ''):
            return None
        try:
            fee = Decimal(fee)
        except (TypeError, ValueError, ArithmeticError):
            return None
        return fee if fee > 0 else None

    def resolve_money(self, fee_override=NOT_SET, money_mode=None):
        """The arrangement this agreement actually carries: (mode, amount).

        An amount of nothing always means a free internship, whichever mode was
        asked for - a stipend of zero is not a stipend.
        """
        amount = self.resolve_fee(fee_override)
        mode = money_mode or self.money_mode or MONEY_FEE
        if mode not in dict(MONEY_MODE_CHOICES):
            mode = MONEY_FEE
        if amount is None:
            return MONEY_NONE, None
        if mode == MONEY_NONE:
            return MONEY_NONE, None
        return mode, amount

    def money_block(self, mode):
        """Wording for one arrangement, falling back to the shipped defaults so
        a template saved before money_copy existed still renders."""
        copy = self.money_copy or {}
        block = dict(default_money_copy().get(mode, {}))
        block.update(copy.get(mode) or {})
        return block

    def build_snapshot(self, fee_override=NOT_SET, money_mode=None):
        """Freeze everything the signing page renders, for one arrangement.

        Interns are on different arrangements - some pay us a monthly fee, some
        are paid a stipend, some neither - so the money is resolved per request
        and its wording swapped here rather than being conditional in the
        templates.
        """
        mode, fee = self.resolve_money(fee_override, money_mode)
        is_free = fee is None
        money = '' if is_free else f'\u20b9{fee:.2f}'.rstrip('0').rstrip('.')
        block = self.money_block(mode)

        sections = []
        for section in (self.sections or []):
            section = dict(section)
            if is_free and section.get('bullets_free'):
                section['bullets'] = section['bullets_free']
            if section.get('show_fee'):
                # This section is written around the money. Swap in the wording
                # for whichever arrangement applies, and drop the amount when
                # there is none to show.
                section['title'] = block.get('section_title') or section['title']
                section['body'] = block.get('section_body') or section.get('body', '')
                if block.get('bullets'):
                    section['bullets'] = block['bullets']
                section['show_fee'] = not is_free
            for key in ('title_free', 'body_free', 'bullets_free'):
                section.pop(key, None)
            sections.append(section)

        if is_free:
            confirmation = self.confirmation_free_html or self.confirmation_html
        else:
            confirmation = self.confirmation_html

        return {
            'name': self.name,
            'version': self.version,
            'agreement_type': self.agreement_type,
            'heading': self.heading,
            'eyebrow': self.eyebrow,
            'intro_html': self.intro_html,
            'sections': sections,
            'monthly_fee': str(fee) if fee is not None else '',
            'is_free': is_free,
            'money_mode': mode,
            # Regenerated, never copied: a custom amount must not inherit the
            # template's words for a different number.
            'fee_in_words': rupees_in_words(fee) if fee is not None else '',
            'fee_note': (block.get('amount_note') or self.fee_note) if fee is not None else '',
            'confirmation_html': confirmation,
            'continue_label': self.continue_label,
            'decline_label': self.decline_label,
            'decision_heading': self.decision_heading,
            'accept_sub': self.accept_sub,
            'decline_sub': self.decline_sub,
            # The confirmation block follows the last numbered section, which
            # is not always nine.
            'confirmation_no': len(sections) + 1,
            'accept_statement': self.accept_statement,
            'decline_statement': self.decline_statement,
            'accept_confirm_text': self.accept_confirm_text,
            'decline_heading': self.decline_heading,
            'decline_intro': self.decline_intro,
            'decline_button_label': self.decline_button_label,
            'accepted_pill': self.accepted_pill,
            'declined_pill': self.declined_pill,
            'done_accepted_html': self.done_accepted_html,
            'done_declined_html': self.done_declined_html,
            # Resolved here, not in the page: the signed wording must name the
            # amount that was actually agreed, not the template's current one.
            'money_note': (block.get('agreed_note') or '').replace('{amount}', money),
            'money_confirm_line': (block.get('confirm_suffix') or '').replace('{amount}', money),
            'require_college_fields': self.require_college_fields,
            'college_fields_optional': self.college_fields_optional,
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
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
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
    snapshot_money_mode = models.CharField(
        max_length=10, choices=MONEY_MODE_CHOICES, default=MONEY_FEE,
        help_text='Which way the money went for this person: fee, stipend, or neither.')

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

    @property
    def college_fields_optional(self):
        """A new joiner may not be studying, so their college can be blank.

        The domain stays required either way - everyone interns in something.
        """
        return bool(self.snapshot_json.get('college_fields_optional', False))

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
