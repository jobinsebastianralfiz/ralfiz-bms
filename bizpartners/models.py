"""Business partners: companies Ralfiz runs joint projects with.

Not the same thing as core.Partner, which is a capital partner (an owner of
Ralfiz). A business partner brings or shares a project, the profit is split
by an agreed ratio (50/50, 60/40...), and everything is kept in the
partner's currency (SAR by default), apart from the INR/GST books.

The money on a joint project is a small ledger:

    client pays Ralfiz        client pays partner
    Ralfiz pays partner       partner pays Ralfiz      (share settlements)
    expenses, paid by either side, come off the top before the split

From that, `JointProject.money()` works out each side's share and who owes
whom right now.
"""
import os
import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from core.fields import EncryptedTextField
from core.models import _private_storage

ZERO = Decimal('0')
HUNDRED = Decimal('100')

CURRENCY_CHOICES = [
    ('SAR', 'SAR - Saudi Riyal'),
    ('AED', 'AED - UAE Dirham'),
    ('QAR', 'QAR - Qatari Riyal'),
    ('KWD', 'KWD - Kuwaiti Dinar'),
    ('OMR', 'OMR - Omani Rial'),
    ('BHD', 'BHD - Bahraini Dinar'),
    ('USD', 'USD - US Dollar'),
    ('INR', 'INR - Indian Rupee'),
]

PERCENT = [MinValueValidator(ZERO), MaxValueValidator(HUNDRED)]


def _file_path(instance, filename):
    project_id = getattr(instance, 'project_id', None) or 'misc'
    kind = instance.__class__.__name__.lower()
    return f'bizpartners/{project_id}/{kind}/{uuid.uuid4().hex[:8]}_{os.path.basename(filename)}'


class BusinessPartner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='business_partner_profile',
        help_text='Login for the partner portal at /partner/.')
    name = models.CharField(max_length=255, help_text='Contact person')
    company_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, default='Saudi Arabia', blank=True)
    city = models.CharField(max_length=80, blank=True)
    address = models.TextField(blank=True)
    tax_number = models.CharField(max_length=40, blank=True, verbose_name='VAT / CR number')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='SAR')
    default_partner_share = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('50'), validators=PERCENT,
        verbose_name="Partner's default profit share %",
        help_text='Pre-filled on each new joint project. 50 = 50/50, 40 = Ralfiz 60 / partner 40.')
    notes = models.TextField(blank=True, help_text='Internal. The partner never sees this.')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', 'company_name', 'name']

    def __str__(self):
        return self.company_name or self.name

    @property
    def display_name(self):
        return self.company_name or self.name

    @property
    def default_ralfiz_share(self):
        return HUNDRED - self.default_partner_share

    def totals(self, projects=None):
        """Sum of money() across this partner's projects (cancelled ones left out)."""
        if projects is None:
            projects = self.projects.exclude(status='cancelled').prefetch_related('payments', 'expenses')
        keys = ('contract_value', 'received', 'pending_from_client', 'expenses', 'profit',
                'partner_share', 'ralfiz_share', 'paid_to_partner', 'paid_to_ralfiz',
                'due_to_partner', 'projected_partner_share',
                'fixed_agreed', 'fixed_due', 'fixed_paid', 'fixed_balance', 'amc_due', 'server_due',
                'split_contract_value')
        out = {k: ZERO for k in keys}
        out.update(projects=0, split_projects=0, fixed_projects=0)
        for p in projects:
            m = p.money()
            out['projects'] += 1
            out['fixed_projects' if m['is_fixed'] else 'split_projects'] += 1
            for k in keys:
                out[k] += m[k]
        out['only_fixed'] = bool(out['fixed_projects'] and not out['split_projects'])
        out['mixed'] = bool(out['fixed_projects'] and out['split_projects'])
        return out


class JointProject(models.Model):
    STATUS_CHOICES = [
        ('lead', 'Lead'),
        ('quoted', 'Quoted'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('review', 'Review / Testing'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    ACTIVE = ('confirmed', 'in_progress', 'review')
    DEAL_CHOICES = [
        ('fixed', 'Fixed amount for Ralfiz'),
        ('split', 'Profit split'),
    ]
    CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half-yearly'),
        ('yearly', 'Yearly'),
    ]
    CYCLE_MONTHS = {'monthly': 1, 'quarterly': 3, 'half_yearly': 6, 'yearly': 12}

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner = models.ForeignKey(BusinessPartner, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255, blank=True, help_text='End client the work is for.')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    progress = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)],
                                                help_text='0-100, shown to the partner.')
    deal_type = models.CharField(
        max_length=10, choices=DEAL_CHOICES, default='split', verbose_name='How Ralfiz earns',
        help_text='Fixed: the partner pays Ralfiz an agreed amount, whatever they charge the client. '
                  'Split: client money minus expenses is shared by the percentages.')
    contract_value = models.DecimalField(
        max_digits=14, decimal_places=2, default=ZERO, verbose_name='Amount',
        help_text="Fixed deal: Ralfiz's agreed amount. Split deal: what the end client pays in total.")
    # Recurring charges, fixed deals only. Amount 0 = not opted.
    amc_amount = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO, verbose_name='AMC amount',
                                     help_text='Per cycle. Leave 0 if there is no AMC.')
    amc_cycle = models.CharField(max_length=12, choices=CYCLE_CHOICES, default='yearly', verbose_name='AMC cycle')
    amc_start_date = models.DateField(null=True, blank=True, verbose_name='AMC starts',
                                      help_text='The first AMC period starts (and is due) on this date.')
    server_amount = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO,
                                        verbose_name='Server charges',
                                        help_text='Per cycle. Leave 0 if they did not opt for our server.')
    server_cycle = models.CharField(max_length=12, choices=CYCLE_CHOICES, default='yearly',
                                    verbose_name='Server cycle')
    server_start_date = models.DateField(null=True, blank=True, verbose_name='Server starts')
    recurring_end_date = models.DateField(null=True, blank=True, verbose_name='AMC / server end',
                                          help_text='Optional. No new periods fall due after this date.')
    partner_share_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('50'), validators=PERCENT,
        verbose_name="Partner's profit share %")
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    linked_project = models.ForeignKey(
        'core.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='joint_ventures',
        help_text='Optional: the internal BMS project where the team does the work.')
    repo_url = models.URLField(blank=True, verbose_name='Code repository (GitHub)',
                               help_text='Link to the code, e.g. https://github.com/ralfiz/nous-web. The partner sees it.')
    live_url = models.URLField(blank=True, verbose_name='Live site / app link', help_text='The partner sees it.')
    notes = models.TextField(blank=True, help_text='Shown to the partner.')
    internal_notes = models.TextField(blank=True, help_text='Internal. The partner never sees this.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def currency(self):
        return self.partner.currency

    @property
    def open_issue_count(self):
        return self.issues.filter(is_done=False).count()

    @property
    def ralfiz_share_percent(self):
        return HUNDRED - self.partner_share_percent

    @property
    def ratio_label(self):
        def fmt(d):
            return f'{d.normalize():f}'
        return f'{fmt(self.ralfiz_share_percent)} / {fmt(self.partner_share_percent)}'

    @property
    def is_overdue(self):
        return bool(self.deadline and self.status not in ('completed', 'cancelled')
                    and timezone.localdate() > self.deadline)

    @property
    def is_fixed(self):
        return self.deal_type == 'fixed'

    @property
    def is_confirmed(self):
        """Lead and Quoted projects are not agreed yet, so nothing is owed on them."""
        return self.status not in ('lead', 'quoted')

    def periods_due(self, start, cycle, today=None):
        """How many billing periods have started by today (each is due when it starts)."""
        today = today or timezone.localdate()
        if self.recurring_end_date and self.recurring_end_date < today:
            today = self.recurring_end_date
        if not start or today < start:
            return 0
        months = (today.year - start.year) * 12 + today.month - start.month - (1 if today.day < start.day else 0)
        return months // self.CYCLE_MONTHS.get(cycle, 12) + 1

    @staticmethod
    def add_months(d, months):
        import calendar
        y, m = divmod(d.month - 1 + months, 12)
        y, m = d.year + y, m + 1
        return d.replace(year=y, month=m, day=min(d.day, calendar.monthrange(y, m)[1]))

    def next_charge_date(self, start, cycle, today=None):
        """When the next AMC/server period starts (and falls due), or None if it has ended."""
        today = today or timezone.localdate()
        if not start:
            return None
        n = self.periods_due(start, cycle, today)
        nxt = self.add_months(start, n * self.CYCLE_MONTHS.get(cycle, 12))
        if self.recurring_end_date and nxt > self.recurring_end_date:
            return None
        return nxt

    def recurring_lines(self):
        """AMC and server charges due so far, one dict each (only the opted ones)."""
        lines = []
        for key, label, amount, cycle, start in (
                ('amc', 'AMC', self.amc_amount, self.amc_cycle, self.amc_start_date),
                ('server', 'Server charges', self.server_amount, self.server_cycle, self.server_start_date)):
            if amount and amount > 0:
                n = self.periods_due(start, cycle)
                lines.append({'key': key, 'label': label, 'amount': amount, 'cycle': cycle,
                              'cycle_label': dict(self.CYCLE_CHOICES).get(cycle, cycle), 'start': start,
                              'periods': n, 'due': amount * n, 'next': self.next_charge_date(start, cycle)})
        return lines

    def _fixed_money(self, pays_by_purpose, pays):
        lines = self.recurring_lines()
        amc_due = sum((l['due'] for l in lines if l['key'] == 'amc'), ZERO)
        server_due = sum((l['due'] for l in lines if l['key'] == 'server'), ZERO)
        # Money that reached Ralfiz, from the partner or straight from the client.
        paid = pays['partner_to_ralfiz'] + pays['client_to_ralfiz'] - pays['ralfiz_to_partner']
        if not self.is_confirmed:
            amc_due = server_due = ZERO
            for l in lines:
                l['due'] = ZERO
        due = (self.contract_value if self.is_confirmed else ZERO) + amc_due + server_due
        for l in lines:
            l['paid'] = pays_by_purpose.get(l['key'], ZERO)
        out = {k: ZERO for k in (
            'received', 'received_by_ralfiz', 'received_by_partner', 'pending_from_client', 'expenses',
            'expenses_ralfiz', 'expenses_partner', 'profit', 'partner_share', 'ralfiz_share',
            'paid_to_partner', 'paid_to_ralfiz', 'projected_profit', 'projected_partner_share',
            'projected_ralfiz_share')}
        out.update({
            'is_fixed': True,
            'is_confirmed': self.is_confirmed,
            'contract_value': self.contract_value,
            'split_contract_value': ZERO,
            'fixed_agreed': self.contract_value,
            'fixed_agreed_paid': pays_by_purpose.get('development', ZERO) + pays_by_purpose.get('other', ZERO),
            'amc_due': amc_due,
            'server_due': server_due,
            'recurring_due': amc_due + server_due,
            'fixed_due': due,
            'fixed_paid': paid,
            'fixed_balance': due - paid,
            'due_to_partner': paid - due,
            'recurring': lines,
            'collected_percent': int(min(paid / due * 100, 100)) if due > 0 else 0,
        })
        return out

    def money(self):
        """Each side's share and who owes whom, from what has actually come in.

        Profit = client money received - expenses. Each side gets its share of
        that profit plus back whatever it spent on expenses. Compare that with
        what each side is holding (what the client paid it, adjusted by the
        settlements between us) and the difference is the balance:
        due_to_partner > 0 means Ralfiz owes the partner, < 0 the other way.
        """
        pays = {k: ZERO for k, _ in JointPayment.KIND_CHOICES}
        by_purpose = {}
        for pay in self.payments.all():
            pays[pay.kind] += pay.amount
            sign = -1 if pay.kind == 'ralfiz_to_partner' else (0 if pay.kind == 'client_to_partner' else 1)
            by_purpose[pay.purpose] = by_purpose.get(pay.purpose, ZERO) + sign * pay.amount
        if self.is_fixed:
            return self._fixed_money(by_purpose, pays)
        exp_ralfiz = exp_partner = ZERO
        for e in self.expenses.all():
            if e.paid_by == 'partner':
                exp_partner += e.amount
            else:
                exp_ralfiz += e.amount

        pct = self.partner_share_percent / HUNDRED
        received = pays['client_to_ralfiz'] + pays['client_to_partner']
        expenses = exp_ralfiz + exp_partner
        profit = received - expenses
        partner_share = (profit * pct).quantize(Decimal('0.01'))
        ralfiz_share = profit - partner_share
        partner_entitled = partner_share + exp_partner
        partner_holds = pays['client_to_partner'] + pays['ralfiz_to_partner'] - pays['partner_to_ralfiz']
        projected_profit = self.contract_value - expenses
        return {
            'is_fixed': False,
            'is_confirmed': self.is_confirmed,
            'fixed_agreed': ZERO, 'fixed_due': ZERO, 'fixed_paid': ZERO, 'fixed_balance': ZERO,
            'amc_due': ZERO, 'server_due': ZERO, 'recurring': [], 'split_contract_value': self.contract_value,
            'contract_value': self.contract_value,
            'received': received,
            'received_by_ralfiz': pays['client_to_ralfiz'],
            'received_by_partner': pays['client_to_partner'],
            'pending_from_client': max(self.contract_value - received, ZERO) if self.is_confirmed else ZERO,
            'expenses': expenses,
            'expenses_ralfiz': exp_ralfiz,
            'expenses_partner': exp_partner,
            'profit': profit,
            'partner_share': partner_share,
            'ralfiz_share': ralfiz_share,
            'paid_to_partner': pays['ralfiz_to_partner'],
            'paid_to_ralfiz': pays['partner_to_ralfiz'],
            'due_to_partner': partner_entitled - partner_holds,
            'projected_profit': projected_profit,
            'projected_partner_share': (projected_profit * pct).quantize(Decimal('0.01')),
            'projected_ralfiz_share': projected_profit - (projected_profit * pct).quantize(Decimal('0.01')),
            'collected_percent': int(min(received / self.contract_value * 100, 100)) if self.contract_value else 0,
        }


class JointQuote(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to client'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(JointProject, on_delete=models.CASCADE, related_name='quotes')
    quote_number = models.CharField(max_length=30, blank=True)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    quote_date = models.DateField(default=timezone.localdate)
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    details = models.TextField(blank=True, help_text='Scope, line items, terms.')
    file = models.FileField(upload_to=_file_path, storage=_private_storage, max_length=300, blank=True,
                            help_text='Optional PDF of the quote.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-quote_date', '-created_at']

    def __str__(self):
        return self.quote_number or self.title

    def save(self, *args, **kwargs):
        if not self.quote_number:
            n = JointQuote.objects.count() + 1
            while JointQuote.objects.filter(quote_number=f'JQ-{n:04d}').exists():
                n += 1
            self.quote_number = f'JQ-{n:04d}'
        super().save(*args, **kwargs)
        self._move_project_status()

    def _move_project_status(self):
        """Sending a quote marks a Lead project Quoted; an accepted quote confirms it.

        Only moves forward from Lead/Quoted, so a project already running is never pulled back.
        """
        project = self.project
        target = {'sent': 'quoted', 'accepted': 'confirmed'}.get(self.status)
        if not target or project.status not in ('lead', 'quoted') or project.status == target:
            return
        if target == 'quoted' and project.status != 'lead':
            return
        project.status = target
        project.save(update_fields=['status', 'updated_at'])


class ConvertedAmount(models.Model):
    """Money paid in one currency, booked in the project's currency.

    A client in India pays in INR, but the project and the split are in SAR.
    We keep what was actually paid (paid_amount in paid_currency) and the rate
    used, and `amount` holds the converted value in the project's currency,
    which is what every total and the profit split use.
    """
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))],
                                 help_text="In the project's currency (converted).")
    paid_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, blank=True,
                                     help_text='Currency the money actually moved in.')
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True,
        help_text="How many of the paid currency make 1 of the project's currency, e.g. 23.45 (INR per SAR).")

    class Meta:
        abstract = True

    @property
    def is_converted(self):
        return bool(self.paid_currency and self.paid_amount is not None
                    and self.paid_currency != self.project.currency)


class JointPayment(ConvertedAmount):
    KIND_CHOICES = [
        ('client_to_ralfiz', 'Client paid Ralfiz'),
        ('client_to_partner', 'Client paid partner'),
        ('ralfiz_to_partner', 'Ralfiz paid partner'),
        ('partner_to_ralfiz', 'Partner paid Ralfiz'),
    ]
    METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('stc_pay', 'STC Pay'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(JointProject, on_delete=models.CASCADE, related_name='payments')
    PURPOSE_CHOICES = [
        ('development', 'Project / development'),
        ('amc', 'AMC'),
        ('server', 'Server charges'),
        ('other', 'Other'),
    ]
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='client_to_ralfiz')
    purpose = models.CharField(max_length=12, choices=PURPOSE_CHOICES, default='development',
                               verbose_name='Payment for')
    payment_date = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='bank_transfer')
    reference = models.CharField(max_length=120, blank=True, help_text='Transaction / cheque number')
    notes = models.CharField(max_length=255, blank=True)
    receipt = models.FileField(upload_to=_file_path, storage=_private_storage, max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f'{self.get_kind_display()} {self.amount}'

    @property
    def is_client_payment(self):
        return self.kind.startswith('client_')


class JointExpense(ConvertedAmount):
    PAID_BY_CHOICES = [('ralfiz', 'Ralfiz'), ('partner', 'Partner')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(JointProject, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255)
    expense_date = models.DateField(default=timezone.localdate)
    paid_by = models.CharField(max_length=10, choices=PAID_BY_CHOICES, default='ralfiz')
    receipt = models.FileField(upload_to=_file_path, storage=_private_storage, max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return self.description


class JointUpdate(models.Model):
    """A progress note on a joint project, shown to the partner."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(JointProject, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    from_partner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message[:60]



class JointCredential(models.Model):
    """A login for a joint project (server, domain, hosting, admin panel...).

    Password and notes are encrypted at rest like core.Credential. Shared ones
    show in the partner's portal on the project page.
    """
    KIND_CHOICES = [
        ('server', 'Server / SSH'),
        ('domain', 'Domain'),
        ('hosting', 'Hosting / cPanel'),
        ('database', 'Database'),
        ('admin', 'Admin panel / app login'),
        ('email', 'Email account'),
        ('git', 'Git / GitHub access'),
        ('store', 'App Store / Play Console'),
        ('api', 'API key / service'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(JointProject, on_delete=models.CASCADE, related_name='credentials')
    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default='server', verbose_name='Type')
    name = models.CharField(max_length=255, help_text='e.g. "Hostinger VPS" or "nous.sa domain (GoDaddy)".')
    url = models.CharField(max_length=500, blank=True, verbose_name='URL / host / IP',
                           help_text='Login page, server IP or host name.')
    username = models.CharField(max_length=255, blank=True)
    password = EncryptedTextField(blank=True)
    notes = EncryptedTextField(blank=True, help_text='Port, SSH key, PIN, renewal date... Stored encrypted.')
    shared_with_partner = models.BooleanField(default=True, help_text='Show it in the partner portal.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['kind', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_kind_display()})'


class JointIssue(models.Model):
    """One row of a joint project's issue list: feedback the partner follows,
    laid out like the Excel tracker. Done / Not Done only. Not the task board."""
    SOURCE_CHOICES = [
        ('client', 'Client feedback'),
        ('partner', 'Partner'),
        ('ralfiz', 'Ralfiz'),
        ('review', 'Review'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(JointProject, on_delete=models.CASCADE, related_name='issues')
    number = models.PositiveIntegerField(help_text='Running number per project, shown as #12.')
    page = models.CharField(max_length=80, blank=True)
    section = models.CharField(max_length=120, blank=True)
    title = models.CharField(max_length=500, verbose_name='Issue')
    action = models.TextField(blank=True, verbose_name='Action required')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='client')
    notes = models.TextField(blank=True, help_text='Decision or note. The partner sees it.')
    is_done = models.BooleanField(default=False)
    done_at = models.DateTimeField(null=True, blank=True)
    done_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['number']
        constraints = [models.UniqueConstraint(fields=['project', 'number'], name='joint_issue_unique_number')]

    def __str__(self):
        return f'#{self.number} {self.title[:60]}'

    @property
    def status_label(self):
        return 'Done' if self.is_done else 'Not Done'

    def set_done(self, done, user=None):
        self.is_done = bool(done)
        if self.is_done:
            if not self.done_at:
                self.done_at, self.done_by = timezone.now(), user
        else:
            self.done_at = self.done_by = None

    @staticmethod
    def sync_progress(project):
        """With an issue list, the project's "% done" is the share of issues Done.
        Without one, the progress typed on the project form stays."""
        qs = JointIssue.objects.filter(project_id=project.pk)
        total = qs.count()
        if not total:
            return project.progress
        pct = round(qs.filter(is_done=True).count() * 100 / total)
        if pct != project.progress:
            JointProject.objects.filter(pk=project.pk).update(progress=pct)
            project.progress = pct
        return pct

    @classmethod
    def next_number(cls, project):
        top = cls.objects.filter(project=project).aggregate(m=models.Max('number'))['m']
        return (top or 0) + 1

    @classmethod
    def add_many(cls, project, items, source='client', user=None):
        """Create issues from dicts (page, section, title, action, notes, is_done, source, undated).
        Rows without a title are skipped. Locks the project row so two saves at once
        never take the same numbers."""
        from django.db import transaction
        sources = dict(cls.SOURCE_CHOICES)
        created = []
        with transaction.atomic():
            JointProject.objects.select_for_update().filter(pk=project.pk).first()
            n = cls.next_number(project)
            for it in items:
                title = (it.get('title') or '').strip()[:500]
                if not title:
                    continue
                issue = cls(project=project, number=n, title=title, created_by=user,
                            page=(it.get('page') or '').strip()[:80],
                            section=(it.get('section') or '').strip()[:120],
                            action=(it.get('action') or '').strip(),
                            notes=(it.get('notes') or '').strip(),
                            source=it.get('source') if it.get('source') in sources else
                            (source if source in sources else 'client'))
                issue.set_done(it.get('is_done'), user)
                if it.get('undated'):  # imported as Done: we don't know when or by whom
                    issue.done_at = issue.done_by = None
                issue.save()
                created.append(issue)
                n += 1
            if created:
                cls.sync_progress(project)
        return created


def joint_issue_image_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
        ext = '.png'
    return f'joint_issues/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{ext}'


class JointIssueImage(models.Model):
    """A screenshot or photo attached to an issue. Both the partner and staff see it."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(JointIssue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=joint_issue_image_path, max_length=200)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Picture for #{self.issue.number}'



@receiver(post_delete, sender=JointIssueImage)
def _drop_issue_image_file(sender, instance, **kwargs):
    """Remove the file too, also when the issue or project is deleted."""
    if instance.image.name:
        instance.image.storage.delete(instance.image.name)
