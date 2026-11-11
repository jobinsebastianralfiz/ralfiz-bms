"""Intern XP wallet: a ledger of XP earned for approved work, paid out as money.

Every change to a wallet is an XPEntry row. The balance is the sum of the
approved rows and is never stored, so it can't drift. Rows are not edited once
decided: a mistake is fixed with a correcting row.
"""
import uuid
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q


class XPSettings(models.Model):
    """One row: the rupee rate, default XP per source and the optional cap."""
    rate_paise = models.PositiveIntegerField(default=50, help_text='Paise paid per XP. 50 = 2 XP for ₹1.')
    xp_low = models.PositiveIntegerField(default=50, help_text='Work assignment, Low priority')
    xp_medium = models.PositiveIntegerField(default=100, help_text='Work assignment, Medium priority')
    xp_high = models.PositiveIntegerField(default=200, help_text='Work assignment, High priority')
    xp_urgent = models.PositiveIntegerField(default=300, help_text='Work assignment, Urgent priority')
    xp_per_assessment_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.00'),
                                                    help_text='XP per % scored in a graded assessment')
    xp_lead_converted = models.PositiveIntegerField(default=500, help_text='A lead the intern added becomes a client')
    monthly_cap = models.PositiveIntegerField(default=0, help_text='Most XP one person can earn in a month. 0 = no cap.')
    include_employees = models.BooleanField(default=True,
                                            help_text='Employees have wallets too. Off = interns only.')
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'XP settings'
        verbose_name_plural = 'XP settings'

    def __str__(self):
        return f'{self.xp_per_rupee} XP = ₹1'

    @classmethod
    def current(cls):
        obj = cls.objects.order_by('pk').first()
        return obj or cls.objects.create()

    @property
    def xp_per_rupee(self):
        if not self.rate_paise:
            return 0
        value = Decimal(100) / Decimal(self.rate_paise)
        return value.quantize(Decimal('0.01')).normalize()

    def priority_xp(self, priority):
        return {'low': self.xp_low, 'medium': self.xp_medium, 'high': self.xp_high,
                'urgent': self.xp_urgent}.get(priority, self.xp_medium)


def xp_to_rupees(xp, rate_paise):
    return (Decimal(xp) * Decimal(rate_paise) / Decimal(100)).quantize(Decimal('0.01'))


class XPPayout(models.Model):
    """One cash-out: XP leaves the wallet as money, on a payslip or paid separately."""
    METHOD_CHOICES = [('payslip', 'Added to payslip'), ('upi', 'UPI'), ('bank', 'Bank transfer'), ('cash', 'Cash')]
    STATUS_CHOICES = [('paid', 'Paid'), ('undone', 'Undone')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='xp_payouts')
    xp = models.PositiveIntegerField()
    rate_paise = models.PositiveIntegerField(help_text='Frozen at the rate in force when paid')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    payroll = models.ForeignKey('employees.Payroll', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='xp_payouts')
    reference = models.CharField(max_length=120, blank=True, help_text='UPI / bank reference')
    paid_on = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='paid')
    undo_reason = models.CharField(max_length=255, blank=True)
    undone_at = models.DateTimeField(null=True, blank=True)
    undone_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'XP payout'

    def __str__(self):
        return f'{self.employee} · {self.xp} XP · ₹{self.amount}'

    @property
    def is_active(self):
        return self.status == 'paid'


class XPEntry(models.Model):
    """One row in a wallet's ledger."""
    KIND_CHOICES = [('earned', 'Earned'), ('adjustment', 'Adjustment'), ('payout', 'Paid out'),
                    ('reversal', 'Reversal')]
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
    SOURCE_CHOICES = [('work', 'Work assignment'), ('uat', 'UAT plan'), ('assessment', 'Assessment'),
                      ('lead', 'CRM lead'), ('manual', 'Manual'), ('payout', 'Payout')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='xp_entries')
    xp = models.IntegerField(help_text='+ adds to the wallet, − takes away')
    kind = models.CharField(max_length=12, choices=KIND_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    source_kind = models.CharField(max_length=12, choices=SOURCE_CHOICES, default='manual')
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    source = GenericForeignKey('content_type', 'object_id')
    title = models.CharField(max_length=255, help_text='What it was for, as the intern sees it')
    suggested_xp = models.IntegerField(null=True, blank=True, help_text='What the rules suggested')
    note = models.TextField(blank=True, help_text='Reason for a change, rejection or adjustment')
    closed_by_system = models.BooleanField(default=False,
                                           help_text='Rejected automatically because the work was reopened')
    decided_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    decided_at = models.DateTimeField(null=True, blank=True)
    rate_paise = models.PositiveIntegerField(null=True, blank=True, help_text='Frozen on payout rows')
    payout = models.ForeignKey(XPPayout, on_delete=models.PROTECT, null=True, blank=True, related_name='entries')
    reverses = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='reversals')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'XP entry'
        verbose_name_plural = 'XP entries'
        constraints = [
            # The same piece of work can't pay the same person twice.
            models.UniqueConstraint(fields=['employee', 'content_type', 'object_id'],
                                    condition=Q(kind='earned'), name='xp_one_earning_per_source'),
        ]
        indexes = [models.Index(fields=['employee', 'status'])]

    def __str__(self):
        return f'{self.employee} {self.xp:+d} XP · {self.title}'

    @property
    def abs_xp(self):
        return abs(self.xp)

    @property
    def display_status(self):
        if self.kind == 'payout':
            return 'Paid'
        return self.get_status_display()

    @property
    def status_css(self):
        return {'Pending': 'warn', 'Approved': 'ok', 'Rejected': 'danger', 'Paid': 'info'}[self.display_status]
