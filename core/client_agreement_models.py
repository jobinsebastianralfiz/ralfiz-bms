"""Client project agreements: one signable link per project, per version.

Same shape as the intern agreement (employees/agreement_models.py): the staff
member fills in the project terms, the request freezes them in `snapshot_json`,
and the client opens a private link to accept or ask for changes. Edits after
sending never rewrite what a client already accepted - a revision is a new
request that supersedes the old one.
"""
import hashlib
import json
import uuid
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from employees.agreement_models import default_expiry, generate_token, rupees_in_words


DEFAULT_MILESTONES = [
    ('Advance, on signing this agreement', 40),
    ('On delivery for testing (UAT)', 40),
    ('On go-live / final handover', 20),
]

# Standard clauses. Frozen into each request's snapshot at send time, so
# rewording these later never changes an agreement already sent.
STANDARD_CLAUSES = [
    {
        'title': 'Change Requests',
        'body': 'Work outside the scope and deliverables above is a change request. We will '
                'quote each change request in writing - cost and effect on the timeline - and '
                'start it only after you approve that quote.',
    },
    {
        'title': 'Client Responsibilities',
        'bullets': [
            'Provide content, branding, logins and other inputs on time',
            'Name one point of contact who can give feedback and approvals',
            'Review each delivery and share feedback within 5 working days',
            'Arrange third-party accounts and fees (domain, hosting, app stores, payment gateways, SMS/API) unless quoted by us',
        ],
        'callout': {
            'style': 'warn',
            'text': 'Delays in inputs or approvals move the delivery date by the same amount of time.',
        },
    },
    {
        'title': 'Ownership & Source Code',
        'body': 'On receipt of the full project fee, ownership of the custom work built for this '
                'project passes to you and the source code is handed over. Until then it remains '
                'the property of Ralfiz Technologies. Open-source libraries and our own reusable '
                'components stay under their own licences; you receive a licence to use them as '
                'part of this project.',
    },
    {
        'title': 'Confidentiality',
        'body': 'Both parties keep the other\'s business information, data and credentials '
                'confidential, and use them only for this project. We may list the project name '
                'and a screenshot in our portfolio unless you ask us not to.',
    },
    {
        'title': 'Termination',
        'body': 'Either party may end this agreement with 15 days\' written notice. You pay for '
                'the work completed up to the notice date; advances already paid are adjusted '
                'against that work and are otherwise non-refundable. Work paid for is handed over.',
    },
    {
        'title': 'Governing Law',
        'body': 'This agreement is governed by the laws of India. Any dispute that cannot be '
                'settled by discussion falls under the jurisdiction of the courts at Malappuram, '
                'Kerala.',
    },
]


def _money(amount):
    """'₹1,25,000' - Indian digit grouping, no paise unless there are some."""
    amount = Decimal(amount or 0).quantize(Decimal('0.01'))
    whole, _, paise = f'{amount:.2f}'.partition('.')
    sign = '-' if whole.startswith('-') else ''
    whole = whole.lstrip('-')
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ','.join(groups + [tail])
    return f'{sign}₹{whole}' + (f'.{paise}' if paise != '00' else '')


def parse_milestones(text, total):
    """'Advance | 40' lines into [{label, percent, amount}].

    A line with no percent gets an equal share of whatever is left, so a
    staff member can type labels alone and still get a valid schedule.
    """
    rows = []
    for line in (text or '').splitlines():
        if not line.strip():
            continue
        label, _, pct = line.partition('|')
        try:
            percent = Decimal(pct.strip().rstrip('%')) if pct.strip() else None
        except InvalidOperation:
            percent = None
        rows.append({'label': label.strip(), 'percent': percent})

    fixed = sum((r['percent'] for r in rows if r['percent'] is not None), Decimal('0'))
    loose = [r for r in rows if r['percent'] is None]
    if loose:
        share = max(Decimal('100') - fixed, Decimal('0')) / len(loose)
        for r in loose:
            r['percent'] = share.quantize(Decimal('0.01'))

    total = Decimal(total or 0)
    out = []
    for r in rows:
        amount = (total * r['percent'] / 100).quantize(Decimal('1'))
        out.append({
            'label': r['label'],
            'percent': f"{r['percent'].normalize():f}",
            'amount': str(amount),
            'amount_display': _money(amount),
        })
    return out


def milestones_total_percent(milestones):
    return sum((Decimal(m['percent']) for m in milestones), Decimal('0'))


def default_milestone_text():
    return '\n'.join(f'{label} | {pct}' for label, pct in DEFAULT_MILESTONES)


DEFAULT_EXCLUSIONS = [
    'Domain registration and renewal',
    'Hosting / cloud server charges, unless taken from us below',
    'Third-party paid plugins, themes, APIs, SMS and payment-gateway fees',
    'Content writing, translation, photography and video',
    'Play Store / App Store developer account fees',
    'Support and changes after the warranty, unless covered by a maintenance plan or AMC',
]


def default_exclusions_text():
    return '\n'.join(DEFAULT_EXCLUSIONS)


CYCLES = {
    'monthly': ('/ month', 'Monthly'),
    'quarterly': ('/ quarter', 'Quarterly'),
    'half_yearly': ('/ 6 months', 'Half-yearly'),
    'yearly': ('/ year', 'Yearly'),
    'one_time': ('one-time', 'One-time'),
}

MODE_INCLUDED = 'included'  # part of the agreement, the client can't untick it
MODE_OPTIONAL = 'optional'  # the client chooses on the signing page


def _cycle(raw):
    raw = (raw or '').strip().lower().replace('-', '_').replace(' ', '_')
    aliases = {'month': 'monthly', 'year': 'yearly', 'annual': 'yearly', 'annually': 'yearly',
               'onetime': 'one_time', 'once': 'one_time', 'quarter': 'quarterly',
               'half_year': 'half_yearly', 'halfyearly': 'half_yearly'}
    raw = aliases.get(raw, raw)
    return raw if raw in CYCLES else 'monthly'


def _amount(raw):
    try:
        value = Decimal(str(raw).replace(',', '').replace('₹', '').strip())
    except (InvalidOperation, ValueError):
        return None
    return value if value >= 0 else None


def _service(key, group, name, amount, cycle, mode, description=''):
    suffix, label = CYCLES[cycle]
    return {
        'key': key, 'group': group, 'name': name, 'description': description,
        'amount': str(amount), 'amount_display': _money(amount),
        'cycle': cycle, 'cycle_suffix': suffix, 'cycle_label': label,
        'mode': mode if mode in (MODE_INCLUDED, MODE_OPTIONAL) else MODE_OPTIONAL,
    }


def build_services(form):
    """Recurring services from the staff form: (services, cloud_mode, errors).

    Monthly maintenance and AMC are single services. Cloud hosting is a list
    of plans the client picks one of - required means they must pick a plan,
    optional means they may also say no. Anything else goes in 'other
    services', one per line: Name | amount | cycle | included/optional.
    """
    services, errors = [], {}

    if form.get('maint_on'):
        amount = _amount(form.get('maint_amount'))
        if not amount:
            errors['maint'] = 'Enter the monthly maintenance charge.'
        else:
            services.append(_service(
                'maint', 'maintenance', 'Monthly Maintenance', amount, 'monthly',
                form.get('maint_mode'), (form.get('maint_note') or '').strip()
                or 'Bug fixes, minor content/text changes, security and software updates, '
                   'uptime monitoring and backups.'))

    cloud_mode = ''
    if form.get('cloud_on'):
        cloud_mode = 'required' if form.get('cloud_mode') == 'required' else 'optional'
        for i, line in enumerate(l for l in (form.get('cloud_plans') or '').splitlines() if l.strip()):
            parts = [p.strip() for p in line.split('|')]
            amount = _amount(parts[1]) if len(parts) > 1 else None
            if not parts[0] or amount is None:
                errors['cloud'] = f'Cloud plan line {i + 1} needs a name and a monthly price: Name | price | details'
                continue
            services.append(_service(f'cloud-{i + 1}', 'cloud', parts[0], amount, 'monthly',
                                     MODE_OPTIONAL, parts[2] if len(parts) > 2 else ''))
        if not any(s['group'] == 'cloud' for s in services) and 'cloud' not in errors:
            errors['cloud'] = 'Add at least one cloud plan, or switch cloud hosting off.'

    if form.get('amc_on'):
        amount = _amount(form.get('amc_amount'))
        if not amount:
            errors['amc'] = 'Enter the AMC amount.'
        else:
            services.append(_service(
                'amc', 'amc', 'Annual Maintenance Contract (AMC)', amount,
                _cycle(form.get('amc_cycle') or 'yearly'), form.get('amc_mode'),
                (form.get('amc_note') or '').strip()
                or 'Starts after the warranty ends. Covers support, bug fixes and updates for the '
                   'year; renewed yearly. A separate AMC agreement is issued.'))

    for i, line in enumerate(l for l in (form.get('other_services') or '').splitlines() if l.strip()):
        parts = [p.strip() for p in line.split('|')]
        amount = _amount(parts[1]) if len(parts) > 1 else None
        if not parts[0] or amount is None:
            errors['other'] = f'Other service line {i + 1} needs: Name | amount | cycle | included/optional'
            continue
        mode = MODE_INCLUDED if len(parts) > 3 and parts[3].lower().startswith('incl') else MODE_OPTIONAL
        services.append(_service(f'other-{i + 1}', 'other', parts[0], amount,
                                 _cycle(parts[2] if len(parts) > 2 else ''), mode))

    return services, cloud_mode, errors


class ClientAgreement(models.Model):
    """One signable agreement link for one project."""

    STATUS_PENDING = 'pending'
    STATUS_VIEWED = 'viewed'
    STATUS_ACCEPTED = 'accepted'
    STATUS_CHANGES = 'changes'
    STATUS_CANCELLED = 'cancelled'
    STATUS_SUPERSEDED = 'superseded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Sent'),
        (STATUS_VIEWED, 'Opened'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_CHANGES, 'Changes requested'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_SUPERSEDED, 'Superseded'),
    ]

    OPEN_STATUSES = (STATUS_PENDING, STATUS_VIEWED)
    RESPONDED_STATUSES = (STATUS_ACCEPTED, STATUS_CHANGES)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_token)
    reference = models.CharField(max_length=40, blank=True, db_index=True,
                                 help_text='e.g. RT/CA/26/0003')
    revision = models.PositiveIntegerField(default=1)

    project = models.ForeignKey('core.Project', on_delete=models.CASCADE,
                                related_name='client_agreements')
    snapshot_json = models.JSONField(default=dict, blank=True,
                                     help_text='Everything the client is shown, frozen at send time')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING,
                              db_index=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='client_agreements_sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)

    first_viewed_at = models.DateTimeField(null=True, blank=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    # ---- Response ----
    responded_at = models.DateTimeField(null=True, blank=True)
    signer_name = models.CharField(max_length=200, blank=True)
    signer_designation = models.CharField(max_length=200, blank=True)
    signer_company = models.CharField(max_length=255, blank=True)
    signer_email = models.EmailField(blank=True)
    signed_name = models.CharField(max_length=200, blank=True,
                                   help_text='Typed signature - the binding one')
    signature_image = models.ImageField(upload_to='client_agreements/signatures/',
                                        null=True, blank=True)
    agreed_to_terms = models.BooleanField(default=False)
    selected_services = models.JSONField(
        default=list, blank=True,
        help_text='Keys of the recurring services in force: included ones plus what the client chose')
    change_notes = models.TextField(blank=True, help_text='What the client asked to change')

    # ---- Evidence ----
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    body_hash = models.CharField(max_length=64, blank=True)

    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='supersedes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.reference} - {self.project.name} ({self.get_status_display()})'

    # ---- State ----
    @property
    def is_expired(self):
        return self.status in self.OPEN_STATUSES and timezone.now() > self.expires_at

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES and not self.is_expired

    @property
    def has_responded(self):
        return self.status in self.RESPONDED_STATUSES

    @property
    def status_label(self):
        return 'Expired' if self.is_expired else self.get_status_display()

    @property
    def status_css(self):
        """Inline badge colours from theme vars (the app has no .bg-info etc.)."""
        muted = 'background: var(--bg-hover); color: var(--text-muted);'
        if self.is_expired:
            return muted
        return {
            self.STATUS_PENDING: 'background: var(--info-bg); color: var(--info);',
            self.STATUS_VIEWED: 'background: var(--warning-bg); color: var(--warning);',
            self.STATUS_ACCEPTED: 'background: var(--success-bg); color: var(--success);',
            self.STATUS_CHANGES: 'background: var(--danger-bg); color: var(--danger);',
        }.get(self.status, muted)

    @property
    def chosen_services(self):
        keys = set(self.selected_services or [])
        return [s for s in self.snapshot_json.get('services', []) if s['key'] in keys]

    @property
    def chosen_monthly_total(self):
        total = sum((Decimal(s['amount']) for s in self.chosen_services if s['cycle'] == 'monthly'),
                    Decimal('0'))
        return _money(total) if total else ''

    # ---- Links ----
    def public_path(self):
        return f'/client-agreement/{self.token}/'

    def public_url(self, request=None):
        return request.build_absolute_uri(self.public_path()) if request else self.public_path()

    def whatsapp_url(self, request=None):
        client = self.project.client
        digits = ''.join(ch for ch in (client.whatsapp or client.phone or '') if ch.isdigit())
        if not digits:
            return ''
        if len(digits) == 10:
            digits = '91' + digits
        message = (
            f'Hi {client.name},\n\n'
            f'Please review the project agreement for "{self.project.name}" from Ralfiz '
            f'Technologies and accept it online:\n{self.public_url(request)}\n\n'
            'If anything needs changing, you can tell us from the same link. Thank you.'
        )
        return f'https://wa.me/{digits}?text={quote(message)}'

    def mailto_url(self, request=None):
        client = self.project.client
        if not client.email:
            return ''
        subject = f'Project agreement - {self.project.name} ({self.reference})'
        body = (f'Hi {client.name},\n\nPlease review and accept the project agreement for '
                f'"{self.project.name}":\n{self.public_url(request)}\n\nThank you,\nRalfiz Technologies')
        return f'mailto:{client.email}?subject={quote(subject)}&body={quote(body)}'

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
            prefix = f'RT/CA/{str(timezone.now().year)[-2:]}/'
            last = ClientAgreement.objects.filter(
                reference__startswith=prefix).order_by('-reference').first()
            nxt = 1
            if last:
                try:
                    nxt = int(last.reference.split('/')[-1]) + 1
                except ValueError:
                    nxt = 1
            self.reference = f'{prefix}{str(nxt).zfill(4)}'
        super().save(*args, **kwargs)


def build_snapshot(project, *, scope, deliverables, start_date, end_date, total,
                   milestones, warranty_months, support_note, extra_terms,
                   exclusions=(), services=(), cloud_mode=''):
    """Freeze the agreement for one project. Section numbers are assigned here
    so the page and the signed copy always number the same way."""
    client = project.client
    sections = []

    def add(title, **kw):
        sections.append({'no': len(sections) + 1, 'title': title, **kw})

    add('Scope of Work', body=scope or project.description or '')
    if deliverables:
        add('Deliverables', bullets=deliverables)
    if exclusions:
        add('Exclusions', body='The following are not part of this project fee:', bullets=list(exclusions))
    add('Timeline', kind='timeline',
        body='Dates assume inputs and approvals arrive on time (see Client Responsibilities).')
    add('Project Fee & Payment Schedule', kind='payment',
        body='Amounts are exclusive of GST, which is added at the applicable rate on each invoice. '
             'Each instalment is invoiced when its milestone is reached and is payable within '
             '7 days of the invoice.')
    if services:
        add('Recurring Services & Charges', kind='services',
            body='These are billed separately from the project fee, plus GST, from go-live (or from '
                 'the end of the warranty for AMC). Services marked Optional apply only if you '
                 'choose them when accepting. Either party may stop a monthly service with 30 '
                 'days\' written notice.'
                 + (' Cloud hosting: please choose one plan.' if cloud_mode == 'required' else ''))
    warranty_body = (f'We fix defects in the delivered work free of charge for {warranty_months} '
                     f'month{"s" if warranty_months != 1 else ""} after go-live. '
                     if warranty_months else 'No free warranty period applies to this project. ')
    add('Warranty & Support', body=warranty_body + (support_note or
        'New features, content changes and third-party outages are not defects. Ongoing support '
        'after the warranty is available under a separate Annual Maintenance Contract (AMC).'))
    for clause in STANDARD_CLAUSES:
        add(clause['title'], **{k: v for k, v in clause.items() if k != 'title'})
    if extra_terms:
        add('Additional Terms', bullets=extra_terms)

    total = Decimal(total or 0)
    return {
        'version': 'v1.0',
        'heading': 'Project Service Agreement',
        'eyebrow': 'CLIENT PROJECT AGREEMENT',
        'client_name': client.name,
        'client_company': client.company_name,
        'client_address': client.address,
        'client_gst': client.gst_number,
        'project_name': project.name,
        'project_type': project.get_project_type_display(),
        'tech_stack': project.tech_stack,
        'start_date': start_date.strftime('%d %b %Y') if start_date else 'On signing',
        'end_date': end_date.strftime('%d %b %Y') if end_date else 'To be agreed',
        'total': str(total),
        'total_display': _money(total),
        'total_in_words': rupees_in_words(total),
        'milestones': milestones,
        'warranty_months': warranty_months,
        'services': list(services),
        'cloud_mode': cloud_mode,
        'sections': sections,
        'confirmation_no': len(sections) + 1,
    }
