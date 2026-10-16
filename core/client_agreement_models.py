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
        'body': 'Any work outside the Services and Deliverables described in this Agreement is a '
                'change request. The Service Provider shall quote each change request in writing, '
                'stating its cost and its effect on the timeline, and shall not be obliged to begin '
                'any change request until the Client has approved that quote in writing.',
    },
    {
        'title': 'Client Responsibilities',
        'body': 'The Client shall:',
        'bullets': [
            'provide content, branding, access credentials and all other inputs reasonably required, in a timely manner;',
            'appoint one point of contact with authority to give feedback and approvals on its behalf;',
            'review each delivery and give written feedback within five (5) working days, failing which that delivery shall be deemed accepted; and',
            'procure and pay for all third-party accounts and fees (including domain, hosting, app store, payment gateway, SMS and API charges), unless these are expressly quoted by the Service Provider.',
        ],
        'callout': {
            'style': 'warn',
            'text': 'Any delay by the Client in providing inputs or approvals shall extend the delivery '
                    'date by at least the period of that delay.',
        },
    },
    {
        'title': 'Intellectual Property & Source Code',
        'body': 'On receipt of the Project Fee in full, ownership of the custom work created '
                'specifically for the Project shall pass to the Client and the source code shall be '
                'handed over. Until then, all such work remains the property of the Service Provider. '
                'Open-source software and the Service Provider\'s pre-existing or reusable components '
                'remain subject to their own licences, and the Client is granted a non-exclusive, '
                'perpetual licence to use them as part of the Project.',
    },
    {
        'title': 'Confidentiality',
        'body': 'Each Party shall keep confidential all business information, data and credentials '
                'disclosed to it by the other Party, and shall use them solely for the purposes of '
                'this Agreement. This obligation survives the termination of this Agreement. The '
                'Service Provider may refer to the Project name and display screenshots of it in its '
                'portfolio, unless the Client objects in writing.',
    },
    {
        'title': 'Limitation of Liability',
        'body': 'The total liability of the Service Provider arising out of or in connection with '
                'this Agreement shall not exceed the fees actually paid by the Client under this '
                'Agreement. Neither Party shall be liable to the other for any indirect, incidental '
                'or consequential loss, including loss of profit, revenue, data or business.',
    },
    {
        'title': 'Force Majeure',
        'body': 'Neither Party shall be liable for any delay or failure to perform its obligations '
                'caused by events beyond its reasonable control, including natural disasters, '
                'epidemics, government action, power or network failures and outages of third-party '
                'services. The affected obligations are suspended for the duration of such event.',
    },
    {
        'title': 'Termination',
        'body': 'Either Party may terminate this Agreement by giving fifteen (15) days\' written notice '
                'to the other. On termination, the Client shall pay for all work completed up to the '
                'date of termination. Advances already paid shall be adjusted against that work and '
                'are otherwise non-refundable. Work that has been paid for shall be handed over to '
                'the Client.',
    },
    {
        'title': 'Governing Law & Jurisdiction',
        'body': 'This Agreement shall be governed by and construed in accordance with the laws of '
                'India. The Parties shall first attempt to resolve any dispute through good-faith '
                'discussion. Any dispute not so resolved shall be subject to the exclusive '
                'jurisdiction of the courts at Malappuram, Kerala.',
    },
    {
        'title': 'General',
        'bullets': [
            'Entire agreement: this Agreement constitutes the entire agreement between the Parties regarding the Project and supersedes all prior proposals, quotations and discussions.',
            'Amendment: no change to this Agreement is valid unless agreed in writing by both Parties.',
            'Independent parties: the Service Provider acts as an independent contractor. Nothing in this Agreement creates a partnership, agency or employment relationship.',
            'Assignment: neither Party may assign this Agreement without the prior written consent of the other Party.',
            'Severability: if any provision is held invalid or unenforceable, the remaining provisions continue in full force.',
            'Notices: notices under this Agreement may be given by email to the addresses the Parties have provided to each other.',
        ],
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
MODE_IN_FEE = 'in_fee'  # staff form only: covered by the project fee, stored as included at no charge


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


def _price(raw):
    """'1999', '₹1,999', '$20' or '20 USD' -> (amount, currency).

    Cloud hosting runs on Railway, which bills in US dollars, so a price may
    be in USD; everything else defaults to rupees."""
    raw = str(raw or '').strip()
    currency = 'USD' if ('$' in raw or 'usd' in raw.lower()) else 'INR'
    amount = _amount(raw.replace('$', '').lower().replace('usd', ''))
    return amount, currency


def _usd(amount):
    return f'${amount:,.2f}'.replace('.00', '')


def _display(amount, currency):
    return _usd(amount) if currency == 'USD' else _money(amount)


DEFAULT_CLOUD_PLANS = (
    'Railway Standard | $20 | Managed cloud hosting on Railway, SSL, automatic deploys\n'
    'Railway Premium | $30 | More compute and memory for higher traffic, SSL, automatic deploys'
)

DEFAULT_CLOUD_NOTE = (
    'Hosting is on Railway. The plan price is the base monthly charge; extra usage beyond the '
    'plan (compute, memory, bandwidth, storage) is billed at actuals as per the Railway invoice. '
    'US dollar amounts are billed in rupees at the exchange rate on the invoice date.'
)


def default_own_hosting_text(tech_stack=''):
    """Minimum hosting the client must provide if they skip our cloud plans.
    One requirement per line; the tech stack line comes from the project."""
    lines = [
        'A Linux server (VPS or cloud instance) with SSH/root access - shared hosting such as cPanel is not supported',
    ]
    if (tech_stack or '').strip():
        lines.append(f'Support for the technology used in this project: {" ".join(tech_stack.split())}')
    lines += [
        'A database server as required by the project, with regular backups',
        'Domain DNS access and an SSL certificate',
        'At least 2 GB RAM and enough resources for the expected traffic',
    ]
    return '\n'.join(lines)


OWN_HOSTING_TERMS = (
    'If the Client chooses not to take a cloud hosting plan from the Service Provider, the Client '
    'shall, before go-live, provide hosting that meets all of the hosting requirements listed in '
    'this Agreement and give the '
    'Service Provider the access needed to deploy the Project. The Service Provider is not responsible '
    'for any failure, downtime, security issue, loss of data or delay caused by hosting that does not '
    'meet these requirements, or by the Client\'s hosting provider. Any additional work this causes, '
    'including configuration, troubleshooting, migration or rework of the Project to suit that '
    'hosting, is a change request and shall be charged separately. The timeline shall be extended '
    'by any delay in the hosting being made available.'
)


def _service(key, group, name, amount, cycle, mode, description='', currency='INR'):
    suffix, label = CYCLES[cycle]
    return {
        'key': key, 'group': group, 'name': name, 'description': description,
        'amount': str(amount), 'amount_display': _display(amount, currency), 'currency': currency,
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
            amount, currency = _price(parts[1]) if len(parts) > 1 else (None, 'INR')
            if not parts[0] or amount is None:
                errors['cloud'] = f'Cloud plan line {i + 1} needs a name and a monthly price: Name | price | details'
                continue
            services.append(_service(f'cloud-{i + 1}', 'cloud', parts[0], amount, 'monthly',
                                     MODE_OPTIONAL, parts[2] if len(parts) > 2 else '', currency))
        if not any(s['group'] == 'cloud' for s in services) and 'cloud' not in errors:
            errors['cloud'] = 'Add at least one cloud plan, or switch cloud hosting off.'

    if form.get('content_on') and form.get('content_mode') == MODE_IN_FEE:
        service = _service(
            'content', 'content', 'Initial Content Upload', Decimal('0'), 'one_time', MODE_INCLUDED,
            (form.get('content_note') or '').strip()
            or 'We load the content you provide - text, images, products and prices - into '
               'the website/app before go-live. Writing or creating new content is not included.')
        service.update(amount_display='Included in the project fee', cycle_suffix='', in_project_fee=True)
        services.append(service)
    elif form.get('content_on'):
        amount = _amount(form.get('content_amount'))
        unit = (form.get('content_unit') or '').strip()
        if not amount:
            errors['content'] = 'Enter the content upload price.'
        else:
            service = _service(
                'content', 'content', 'Initial Content Upload', amount, 'one_time',
                form.get('content_mode'), (form.get('content_note') or '').strip()
                or 'We load the content you provide - text, images, products and prices - into '
                   'the website/app before go-live. Writing or creating new content is not included.')
            if unit:  # priced per item, e.g. per product or per page
                service['cycle_suffix'] = f'per {unit.removeprefix("per ").strip()}'
            services.append(service)

    # AMC is compulsory: every agreement carries it, so there is no on/off switch.
    amount = _amount(form.get('amc_amount'))
    if not amount:
        errors['amc'] = 'Enter the AMC amount - AMC is part of every agreement.'
    else:
        services.append(_service(
            'amc', 'amc', 'Annual Maintenance Contract (AMC)', amount,
            _cycle(form.get('amc_cycle') or 'yearly'), MODE_INCLUDED,
            (form.get('amc_note') or '').strip()
            or 'Starts after the warranty ends. Covers support, bug fixes and updates for the '
               'year; renewed yearly. A separate AMC agreement is issued.'))

    for i, line in enumerate(l for l in (form.get('other_services') or '').splitlines() if l.strip()):
        parts = [p.strip() for p in line.split('|')]
        amount, currency = _price(parts[1]) if len(parts) > 1 else (None, 'INR')
        if not parts[0] or amount is None:
            errors['other'] = f'Other service line {i + 1} needs: Name | amount | cycle | included/optional'
            continue
        mode = MODE_INCLUDED if len(parts) > 3 and parts[3].lower().startswith('incl') else MODE_OPTIONAL
        services.append(_service(f'other-{i + 1}', 'other', parts[0], amount,
                                 _cycle(parts[2] if len(parts) > 2 else ''), mode, '', currency))

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
        """'₹2,500 + $20' - rupee and dollar services are totalled apart."""
        totals = {}
        for s in self.chosen_services:
            if s['cycle'] == 'monthly':
                cur = s.get('currency', 'INR')
                totals[cur] = totals.get(cur, Decimal('0')) + Decimal(s['amount'])
        return ' + '.join(_display(totals[c], c) for c in ('INR', 'USD') if totals.get(c))

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
                   exclusions=(), services=(), cloud_mode='', cloud_note='', late_interest=None,
                   own_hosting=()):
    """Freeze the agreement for one project. Section numbers are assigned here
    so the page and the signed copy always number the same way. The wording
    (preamble, clauses, acceptance) is frozen too, so rewording the template
    later never changes what a client already accepted."""
    from core.models import CompanySettings

    client = project.client
    company = CompanySettings.get_settings()
    provider_name = company.company_name or 'Ralfiz Technologies'
    provider_address = ' '.join((company.address or 'KIMS Avenue, Perinthalmanna, Kerala, India').split())
    client_party = client.company_name or client.name
    client_address = ' '.join((client.address or '').split())
    total = Decimal(total or 0)
    has_cloud = any(sv['group'] == 'cloud' for sv in services)
    own_hosting_list = [l for l in own_hosting if l.strip()] if has_cloud and cloud_mode != 'required' else []
    sections = []

    def add(title, **kw):
        sections.append({'no': len(sections) + 1, 'title': title, **kw})

    add('Scope of Work', body='The Service Provider shall carry out the following work for the '
        'Project (the "Services"):\n\n' + (scope or project.description or ''))
    if deliverables:
        add('Deliverables', body='The Service Provider shall deliver the following (the "Deliverables"):',
            bullets=deliverables)
    if exclusions:
        add('Exclusions', body='The following are excluded from the Services and the Project Fee and, '
            'where required, shall be arranged and paid for by the Client:', bullets=list(exclusions))
    add('Timeline', kind='timeline',
        body='The Service Provider shall use reasonable efforts to deliver the Project by the target '
             'delivery date. The timeline is conditional on the Client meeting its obligations under '
             'the clause titled Client Responsibilities.')
    add('Project Fee & Payment Schedule', kind='payment',
        body=f'In consideration of the Services, the Client shall pay the Service Provider a total '
             f'project fee of {_money(total)} ({rupees_in_words(total)}) (the "Project Fee"), exclusive '
             f'of Goods and Services Tax (GST), which shall be charged at the applicable rate. The '
             f'Project Fee shall be invoiced in instalments as each milestone below is reached, and '
             f'each invoice is payable within seven (7) days of its date.'
             + (f' Any amount not paid by its due date, including amounts due for recurring services, '
                f'shall carry interest at {late_interest.normalize():f}% per month on the overdue amount, '
                f'from the due date until the date of payment in full.' if late_interest else '')
             + ' The Service Provider may suspend work on the Project while any invoice remains overdue, '
               'and the timeline shall be extended accordingly.')
    if services:
        add('Additional Services & Charges', kind='services',
            body='The following services are charged separately from the Project Fee, plus GST, unless '
                 'stated to be included in the Project Fee. One-time services are invoiced on delivery. '
                 'Recurring services are invoiced from go-live or, for the Annual Maintenance Contract '
                 '(AMC), from the end of the Warranty Period. Services marked Optional apply only if the '
                 'Client selects them at acceptance; services marked Part of agreement are binding. '
                 'Either Party may discontinue a monthly service by giving thirty (30) days\' written notice.'
                 + (' The Client shall select one cloud hosting plan.' if cloud_mode == 'required' else ''))
    months = f'{warranty_months} month{"s" if warranty_months != 1 else ""}'
    warranty_body = (f'The Service Provider warrants that the Deliverables shall be free from material '
                     f'defects for a period of {months} from go-live (the "Warranty Period"), and shall '
                     f'remedy any such defect reported in writing during the Warranty Period at no '
                     f'additional charge. '
                     if warranty_months else 'No free warranty period applies to this Project. ')
    add('Warranty & Support', body=warranty_body + (support_note or
        'New features, changes to content or requirements, and failures of third-party services are '
        'not defects. Support after the Warranty Period is provided under the Annual Maintenance '
        'Contract (AMC).'))
    for clause in STANDARD_CLAUSES:
        add(clause['title'], **{k: v for k, v in clause.items() if k != 'title'})
    if extra_terms:
        add('Additional Terms', bullets=extra_terms)

    issued = timezone.localdate().strftime('%d %B %Y')
    preamble = (
        f'This Project Service Agreement (the "Agreement") is made on {issued} between '
        f'{provider_name}, {provider_address} (the "Service Provider"), and {client_party}'
        + (f', {client_address}' if client_address else '')
        + ' (the "Client"). The Service Provider and the Client are each a "Party" and together '
          'the "Parties".'
    )
    recital = (f'The Client wishes to engage the Service Provider for {project.name} (the "Project"), '
               f'and the Service Provider agrees to carry out the Project on the terms set out below.')
    acceptance = (
        f'By accepting this Agreement electronically, {client_party} confirms that it has read and '
        f'understood this Agreement and agrees to be bound by its terms, including the Project Fee of '
        f'{_money(total)} plus GST payable as per the payment schedule'
        + (', the services marked Part of agreement and any optional services selected at acceptance'
           if services else '')
        + '. Under the Information Technology Act, 2000, this electronic acceptance has the same legal '
          'effect as a handwritten signature.'
    )

    return {
        'version': 'v1.0',
        'heading': 'Project Service Agreement',
        'eyebrow': 'CLIENT PROJECT AGREEMENT',
        'preamble': preamble,
        'recital': recital,
        'acceptance': acceptance,
        'provider_name': provider_name,
        'provider_address': provider_address,
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
        'late_interest': f'{late_interest.normalize():f}' if late_interest else '',
        'cloud_mode': cloud_mode,
        'cloud_note': cloud_note if any(sv['group'] == 'cloud' for sv in services) else '',
        # Only when the client may skip our plans: what their own hosting must meet.
        'own_hosting': own_hosting_list,
        'own_hosting_terms': OWN_HOSTING_TERMS if own_hosting_list else '',
        'sections': sections,
        'confirmation_no': len(sections) + 1,
    }
