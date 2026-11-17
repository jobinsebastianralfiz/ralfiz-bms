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
from django.utils import timezone

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
                'due_to_partner', 'projected_partner_share')
        out = {k: ZERO for k in keys}
        count = 0
        for p in projects:
            m = p.money()
            count += 1
            for k in keys:
                out[k] += m[k]
        out['projects'] = count
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner = models.ForeignKey(BusinessPartner, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255, blank=True, help_text='End client the work is for.')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    progress = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)],
                                                help_text='0-100, shown to the partner.')
    contract_value = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO,
                                         help_text='What the end client pays in total.')
    partner_share_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('50'), validators=PERCENT,
        verbose_name="Partner's profit share %")
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    linked_project = models.ForeignKey(
        'core.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='joint_ventures',
        help_text='Optional: the internal BMS project where the team does the work.')
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

    def money(self):
        """Each side's share and who owes whom, from what has actually come in.

        Profit = client money received - expenses. Each side gets its share of
        that profit plus back whatever it spent on expenses. Compare that with
        what each side is holding (what the client paid it, adjusted by the
        settlements between us) and the difference is the balance:
        due_to_partner > 0 means Ralfiz owes the partner, < 0 the other way.
        """
        pays = {k: ZERO for k, _ in JointPayment.KIND_CHOICES}
        for pay in self.payments.all():
            pays[pay.kind] += pay.amount
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
            'contract_value': self.contract_value,
            'received': received,
            'received_by_ralfiz': pays['client_to_ralfiz'],
            'received_by_partner': pays['client_to_partner'],
            'pending_from_client': max(self.contract_value - received, ZERO),
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


class JointPayment(models.Model):
    KIND_CHOICES = [
        ('client_to_ralfiz', 'Client paid Ralfiz'),
        ('client_to_partner', 'Client paid partner'),
        ('ralfiz_to_partner', 'Ralfiz paid partner (share)'),
        ('partner_to_ralfiz', 'Partner paid Ralfiz (share)'),
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
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='client_to_ralfiz')
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
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


class JointExpense(models.Model):
    PAID_BY_CHOICES = [('ralfiz', 'Ralfiz'), ('partner', 'Partner')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(JointProject, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
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

