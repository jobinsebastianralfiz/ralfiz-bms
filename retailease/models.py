import uuid
import os
from django.db import models
from django.utils import timezone
from licensing.models import License, LicenseActivation


class Business(models.Model):
    """
    Represents a business using RetailEase Pro.
    Linked to a License for activation tracking.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name='businesses',
        help_text="The license this business is registered under"
    )

    # Business Information (synced from Flutter app)
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    business_type = models.CharField(max_length=50, blank=True)

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Address
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20, blank=True)

    # Tax Information
    gst_number = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=20, blank=True)

    # Settings
    currency_code = models.CharField(max_length=3, default='INR')
    currency_symbol = models.CharField(max_length=5, default='₹')
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY')

    # Logo (stored on server)
    logo = models.ImageField(upload_to='business_logos/', null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.license.customer_name})"


class Counter(models.Model):
    """
    Represents a POS counter/terminal for a business.
    Each counter is a separate LicenseActivation.
    """
    COUNTER_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='counters'
    )
    activation = models.OneToOneField(
        LicenseActivation,
        on_delete=models.CASCADE,
        related_name='counter',
        help_text="The license activation for this counter"
    )

    # Counter Details
    name = models.CharField(max_length=100, help_text="e.g., 'Counter 1', 'Main POS'")
    description = models.TextField(blank=True)

    # Device Information
    device_name = models.CharField(max_length=200, blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # desktop, tablet, etc.
    os_info = models.CharField(max_length=100, blank=True)
    app_version = models.CharField(max_length=20, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=COUNTER_STATUS_CHOICES, default='active')
    is_primary = models.BooleanField(default=False, help_text="Primary counter for the business")

    # Sync tracking
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_enabled = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Counter"
        verbose_name_plural = "Counters"
        ordering = ['business', 'name']

    def __str__(self):
        return f"{self.business.name} - {self.name}"


def backup_upload_path(instance, filename):
    """Generate upload path for backups: backups/<business_id>/<filename>"""
    return f"backups/{instance.business.id}/{filename}"


class Backup(models.Model):
    """
    Stores encrypted database backups for a business.
    """
    BACKUP_TYPE_CHOICES = [
        ('manual', 'Manual Backup'),
        ('auto', 'Automatic Backup'),
        ('pre_restore', 'Pre-Restore Backup'),
    ]

    BACKUP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('uploading', 'Uploading'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='backups'
    )
    counter = models.ForeignKey(
        Counter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backups',
        help_text="The counter that created this backup"
    )

    # Backup File
    file = models.FileField(upload_to=backup_upload_path)
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0, help_text="Size in bytes")
    checksum = models.CharField(max_length=64, blank=True, help_text="SHA-256 checksum")

    # Encryption
    is_encrypted = models.BooleanField(default=True)
    encryption_version = models.CharField(max_length=10, default='1.0')

    # Backup Metadata
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES, default='manual')
    status = models.CharField(max_length=20, choices=BACKUP_STATUS_CHOICES, default='pending')

    # App version info
    app_version = models.CharField(max_length=20, blank=True)
    db_version = models.IntegerField(default=1, help_text="Database schema version")

    # Data summary (for display without decryption)
    record_counts = models.JSONField(
        default=dict,
        blank=True,
        help_text="Summary of records: {'products': 100, 'invoices': 50, ...}"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Backup"
        verbose_name_plural = "Backups"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.business.name} - {self.filename}"

    def delete(self, *args, **kwargs):
        # Delete the file when the model is deleted
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class SyncLog(models.Model):
    """
    Tracks synchronization events between counters.
    Used for multi-counter sync functionality.
    """
    SYNC_TYPE_CHOICES = [
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync'),
        ('conflict_resolution', 'Conflict Resolution'),
    ]

    SYNC_STATUS_CHOICES = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]

    SYNC_DIRECTION_CHOICES = [
        ('upload', 'Upload (Counter → Server)'),
        ('download', 'Download (Server → Counter)'),
        ('bidirectional', 'Bidirectional'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='sync_logs'
    )
    counter = models.ForeignKey(
        Counter,
        on_delete=models.CASCADE,
        related_name='sync_logs'
    )

    # Sync Details
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES, default='incremental')
    sync_direction = models.CharField(max_length=20, choices=SYNC_DIRECTION_CHOICES, default='upload')
    status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='started')

    # Sync Statistics
    records_uploaded = models.IntegerField(default=0)
    records_downloaded = models.IntegerField(default=0)
    conflicts_detected = models.IntegerField(default=0)
    conflicts_resolved = models.IntegerField(default=0)

    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    # Details
    details = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Sync Log"
        verbose_name_plural = "Sync Logs"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.business.name} - {self.counter.name} - {self.sync_type} ({self.status})"

    def complete(self, status='completed', error_message=''):
        """Mark sync as complete"""
        self.status = status
        self.completed_at = timezone.now()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        if error_message:
            self.error_message = error_message
        self.save()


class APIToken(models.Model):
    """
    API authentication tokens for Flutter app.
    Simple token-based auth without requiring Django REST Framework's token auth.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name='api_tokens'
    )
    counter = models.ForeignKey(
        Counter,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='api_tokens'
    )

    # Token
    token = models.CharField(max_length=64, unique=True, db_index=True)

    # Metadata
    name = models.CharField(max_length=100, blank=True, help_text="Token name/description")
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.license.customer_name} - {self.name or 'Token'}"

    def is_valid(self):
        """Check if token is valid"""
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return self.license.is_valid()

    @classmethod
    def generate_token(cls):
        """Generate a secure random token"""
        import secrets
        return secrets.token_hex(32)

    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class AppConfig(models.Model):
    """
    Global application configuration that can be fetched by clients.
    Stores Google OAuth credentials and other settings that shouldn't be
    hardcoded in the Flutter app (avoiding rebuilds for each client).
    """
    # Singleton key
    key = models.CharField(max_length=50, unique=True, default='default')

    # Google OAuth Configuration
    google_client_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Google OAuth 2.0 Client ID for desktop apps"
    )
    google_client_id_ios = models.CharField(
        max_length=200,
        blank=True,
        help_text="Google OAuth 2.0 Client ID for iOS (if different)"
    )
    google_client_id_android = models.CharField(
        max_length=200,
        blank=True,
        help_text="Google OAuth 2.0 Client ID for Android (if different)"
    )
    google_reversed_client_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Reversed Client ID for iOS URL scheme"
    )

    # Feature Flags
    google_drive_enabled = models.BooleanField(
        default=True,
        help_text="Enable Google Drive backup feature"
    )
    server_backup_enabled = models.BooleanField(
        default=True,
        help_text="Enable Server backup feature"
    )
    local_backup_enabled = models.BooleanField(
        default=True,
        help_text="Enable Local backup feature"
    )

    # App Settings
    min_app_version = models.CharField(
        max_length=20,
        default='1.0.0',
        help_text="Minimum required app version"
    )
    latest_app_version = models.CharField(
        max_length=20,
        default='1.0.0',
        help_text="Latest available app version"
    )
    app_update_url = models.URLField(
        blank=True,
        help_text="URL to download app update"
    )
    force_update = models.BooleanField(
        default=False,
        help_text="Force users to update if below min_app_version"
    )

    # Maintenance Mode
    maintenance_mode = models.BooleanField(
        default=False,
        help_text="Enable maintenance mode (shows message to users)"
    )
    maintenance_message = models.TextField(
        blank=True,
        help_text="Message to show during maintenance"
    )

    # Support Information
    support_email = models.EmailField(default='support@ralfizdigital.in')
    support_phone = models.CharField(max_length=20, blank=True)
    support_whatsapp = models.CharField(max_length=20, blank=True)

    # Terms and Privacy URLs
    terms_url = models.URLField(blank=True)
    privacy_url = models.URLField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "App Configuration"
        verbose_name_plural = "App Configuration"

    def __str__(self):
        return f"App Config ({self.key})"

    @classmethod
    def get_config(cls):
        """Get the default config, creating if it doesn't exist"""
        config, _ = cls.objects.get_or_create(key='default')
        return config