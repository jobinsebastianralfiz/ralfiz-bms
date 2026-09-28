"""
RalfPOS Licensing — yearly licence per shop installation, with add-on modules.

Copied from the EduFlow licensing app, with two differences:
- An empty module list means NO add-ons (EduFlow treats empty as all modules).
  Add-ons are paid extras that only Ralfiz can switch on.
- Every answer to a shop is a token signed with Ed25519 (see signing.py), so the
  shop's RalfPOS can trust its cached licence while offline and cannot fake one.
"""

import uuid
import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone


class RalfPOSLicense(models.Model):
    """A licence issued to one shop's RalfPOS installation."""

    LICENSE_TYPE_CHOICES = [
        ('trial', 'Trial (30 days)'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
    ]

    BILLING_CYCLE_CHOICES = LICENSE_TYPE_CHOICES[1:]

    # Paid add-ons on top of the basic app (counter billing, back office, reports).
    MODULE_CHOICES = [
        ('delivery', 'Delivery / phone orders'),
        ('kitchen', 'Kitchen display & KOT'),
        ('tables', 'Table management'),
        ('einvoice_sa', 'E-invoicing — Saudi (ZATCA)'),
        ('einvoice_ae', 'E-invoicing — UAE'),
    ]

    DURATIONS = {
        'trial': 30, 'monthly': 30, 'quarterly': 90, 'half_yearly': 180, 'yearly': 365, 'lifetime': 36500,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ─── Client Link ──────────────────────────────────
    client = models.ForeignKey(
        'core.Client', on_delete=models.CASCADE,
        related_name='ralfpos_licenses', null=True, blank=True,
        help_text='Link to Ralfiz client record',
    )

    # ─── Shop Identity ────────────────────────────────
    shop_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255, blank=True)
    shop_email = models.EmailField(blank=True)
    shop_phone = models.CharField(max_length=30, blank=True)
    shop_address = models.TextField(blank=True)
    country = models.CharField(max_length=40, blank=True, help_text='e.g. India, UAE, Saudi Arabia')

    # ─── Licence Key & Domain ─────────────────────────
    license_key = models.CharField(
        max_length=64, unique=True, db_index=True,
        help_text='Unique licence key (POS-XXXX-XXXX-XXXX)',
    )
    api_domain = models.CharField(
        max_length=255, blank=True, default='',
        help_text="The shop's RalfPOS address. Empty until the first activation, then bound.",
    )

    # ─── Licence Config ───────────────────────────────
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPE_CHOICES, default='yearly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='yearly')
    grace_period_days = models.PositiveIntegerField(default=7)

    # ─── Validity ─────────────────────────────────────
    issued_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    last_renewed_at = models.DateTimeField(null=True, blank=True)
    renewal_count = models.PositiveIntegerField(default=0)

    # ─── Add-ons & Limits ─────────────────────────────
    enabled_modules = models.JSONField(
        default=list, blank=True,
        help_text='Add-on module keys this shop has paid for. Empty = basic app only.',
    )
    max_counters = models.PositiveIntegerField(default=0, help_text='0 = unlimited')

    # ─── Deployment Info ──────────────────────────────
    server_ip = models.GenericIPAddressField(null=True, blank=True)
    app_version = models.CharField(max_length=40, blank=True)
    deployment_notes = models.TextField(blank=True)

    # ─── Tracking ─────────────────────────────────────
    last_check_at = models.DateTimeField(null=True, blank=True)
    last_check_ip = models.GenericIPAddressField(null=True, blank=True)
    total_checks = models.PositiveIntegerField(default=0)

    # ─── Meta ─────────────────────────────────────────
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'RalfPOS License'
        verbose_name_plural = 'RalfPOS Licenses'

    def __str__(self):
        return f"{self.shop_name} — {self.license_key} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.license_key:
            self.license_key = self.generate_license_key()
        if not self.valid_until:
            base = self.valid_from or timezone.now()
            self.valid_until = base + timedelta(days=self.DURATIONS.get(self.license_type, 365))
        super().save(*args, **kwargs)

    @staticmethod
    def generate_license_key():
        while True:
            parts = [secrets.token_hex(2).upper() for _ in range(3)]
            key = f"POS-{parts[0]}-{parts[1]}-{parts[2]}"
            if not RalfPOSLicense.objects.filter(license_key=key).exists():
                return key

    def is_valid(self):
        return self.status == 'active' and self.valid_from <= timezone.now() <= self.valid_until

    def is_in_grace_period(self):
        if self.status != 'active':
            return False
        now = timezone.now()
        return self.valid_until < now <= self.valid_until + timedelta(days=self.grace_period_days)

    def days_remaining(self):
        return (self.valid_until - timezone.now()).days

    def renew(self, extend_days=None):
        if extend_days:
            self.valid_until += timedelta(days=extend_days)
        else:
            days = self.DURATIONS.get(self.billing_cycle, 365)
            self.valid_until = max(self.valid_until, timezone.now()) + timedelta(days=days)
        self.status = 'active'
        self.renewal_count += 1
        self.last_renewed_at = timezone.now()
        self.save()

    @staticmethod
    def normalize_domain(d):
        d = (d or '').lower().strip().rstrip('/')
        for prefix in ('https://', 'http://'):
            if d.startswith(prefix):
                d = d[len(prefix):]
        return d.split('/')[0]

    def validate_domain(self, domain):
        return self.normalize_domain(domain) == self.normalize_domain(self.api_domain)

    def get_enabled_modules(self):
        """Only known add-ons, in a stable order. Empty means the basic app only."""
        chosen = set(self.enabled_modules or [])
        return [key for key, _ in self.MODULE_CHOICES if key in chosen]

    def record_check(self, ip_address=None, app_version=''):
        self.last_check_at = timezone.now()
        self.last_check_ip = ip_address
        self.total_checks += 1
        fields = ['last_check_at', 'last_check_ip', 'total_checks']
        if app_version:
            self.app_version = app_version[:40]
            fields.append('app_version')
        self.save(update_fields=fields)


class RalfPOSLicenseLog(models.Model):
    EVENT_CHOICES = [
        ('activate', 'Activate'),
        ('check', 'Check'),
        ('renew', 'Renew'),
        ('expire', 'Expire'),
        ('revoke', 'Revoke'),
        ('suspend', 'Suspend'),
        ('reactivate', 'Reactivate'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('domain_mismatch', 'Domain Mismatch'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(RalfPOSLicense, on_delete=models.CASCADE, related_name='logs')
    event = models.CharField(max_length=30, choices=EVENT_CHOICES)
    status = models.CharField(max_length=20)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    domain = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.license.shop_name} — {self.event} ({self.status})"
