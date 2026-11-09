"""
Shop Manager Licensing: a yearly licence for each shop that runs the Ralfiz Shop Manager
(the GST billing / stock / accounts web app, e.g. shop.ralfiz.com). This is separate from RetailEase.

Each shop starts on its own date and renews yearly. Every answer to a shop is a signed token
(signing.py), so the shop can trust its cached licence while it can't reach this server, and
can't fake one.
"""

import secrets
import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


def _today():
    return timezone.localdate()


def _plus_year(d):
    try:
        return d.replace(year=d.year + 1)
    except ValueError:  # 29 Feb
        return d + timedelta(days=365)


class ShopLicense(models.Model):
    PLAN_CHOICES = [
        ('software', 'Software (₹5,500 / year)'),
        ('software_website', 'Software + public website (₹7,500 / year)'),
        ('custom', 'Custom'),
    ]
    PLAN_FEES = {'software': 5500, 'software_website': 7500}

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
    ]

    ON_EXPIRY_CHOICES = [
        ('warn', 'Keep working, show a warning'),
        ('read_only', 'Read-only (can view, cannot bill)'),
        ('lock', 'Lock the software'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey('core.Client', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='shop_licenses', help_text='Link to Ralfiz client record')

    # Shop
    shop_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255, blank=True)
    shop_phone = models.CharField(max_length=30, blank=True)
    shop_email = models.EmailField(blank=True)
    shop_address = models.TextField(blank=True)

    # Key & installation
    license_key = models.CharField(max_length=64, unique=True, db_index=True,
                                   help_text='RS-XXXX-XXXX-XXXX')
    api_domain = models.CharField(max_length=255, blank=True, default='',
                                  help_text="The shop's web address. Empty until first activation, then bound.")

    # Plan & validity
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='software')
    yearly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    status_reason = models.CharField(max_length=255, blank=True, help_text='Shown to the shop when suspended')
    valid_from = models.DateField(default=_today)
    valid_until = models.DateField(blank=True)
    on_expiry = models.CharField(max_length=20, choices=ON_EXPIRY_CHOICES, default='read_only')
    warn_days = models.PositiveIntegerField(default=30, help_text='Start warning this many days before expiry')
    grace_period_days = models.PositiveIntegerField(default=7)
    last_renewed_at = models.DateTimeField(null=True, blank=True)
    renewal_count = models.PositiveIntegerField(default=0)

    # Tracking
    app_version = models.CharField(max_length=40, blank=True)
    last_check_at = models.DateTimeField(null=True, blank=True)
    last_check_ip = models.GenericIPAddressField(null=True, blank=True)
    total_checks = models.PositiveIntegerField(default=0)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Shop Manager License'
        verbose_name_plural = 'Shop Manager Licenses'

    def __str__(self):
        return f"{self.shop_name} — {self.license_key} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.license_key:
            self.license_key = self.generate_license_key()
        if not self.valid_until:
            self.valid_until = _plus_year(self.valid_from or _today()) - timedelta(days=1)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_license_key():
        while True:
            key = 'RS-' + '-'.join(secrets.token_hex(2).upper() for _ in range(3))
            if not ShopLicense.objects.filter(license_key=key).exists():
                return key

    # ── State ────────────────────────────────────────────
    def days_remaining(self, on=None):
        return (self.valid_until - (on or _today())).days

    def grace_until(self):
        return self.valid_until + timedelta(days=self.grace_period_days)

    def state(self, on=None):
        """active / expiring / grace / expired / suspended / revoked"""
        if self.status in ('suspended', 'revoked'):
            return self.status
        day = on or _today()
        if day < self.valid_from:
            return 'active'
        if day <= self.valid_until:
            return 'expiring' if self.days_remaining(day) <= self.warn_days else 'active'
        if day <= self.grace_until():
            return 'grace'
        return 'expired'

    def renew(self, days=None, who=''):
        """Add a year (or `days`) from the current end date, or from today if it has already lapsed."""
        start = max(self.valid_until, _today() - timedelta(days=1))
        self.valid_until = start + timedelta(days=days) if days else _plus_year(start)
        self.status = 'active'
        self.status_reason = ''
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

    def record_check(self, ip_address=None, app_version=''):
        self.last_check_at = timezone.now()
        self.last_check_ip = ip_address
        self.total_checks += 1
        fields = ['last_check_at', 'last_check_ip', 'total_checks']
        if app_version:
            self.app_version = app_version[:40]
            fields.append('app_version')
        self.save(update_fields=fields)


class ShopLicenseLog(models.Model):
    EVENT_CHOICES = [
        ('create', 'Create'), ('activate', 'Activate'), ('check', 'Check'), ('renew', 'Renew'),
        ('update', 'Update'), ('suspend', 'Suspend'), ('reactivate', 'Reactivate'), ('expire', 'Expire'),
        ('revoke', 'Revoke'), ('domain_mismatch', 'Domain Mismatch'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(ShopLicense, on_delete=models.CASCADE, related_name='logs')
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
