import uuid
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta


class Client(models.Model):
    """Client/Customer model"""
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_profile', help_text='Login account for client portal access')
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True, verbose_name='GST Number')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # RetailEase App Configuration (per-client)
    # Google OAuth Credentials
    google_client_id = models.CharField(
        max_length=200, blank=True,
        verbose_name='Google OAuth Client ID (Desktop)',
        help_text='OAuth 2.0 Client ID for Windows/Linux (Desktop type in Google Cloud Console)'
    )
    google_client_id_ios = models.CharField(
        max_length=200, blank=True,
        verbose_name='Google OAuth Client ID (iOS/macOS)',
        help_text='OAuth 2.0 Client ID for iOS & macOS (iOS type in Google Cloud Console)'
    )
    google_client_id_android = models.CharField(
        max_length=200, blank=True,
        verbose_name='Google OAuth Client ID (Android)'
    )
    google_reversed_client_id = models.CharField(
        max_length=200, blank=True,
        verbose_name='Reversed Client ID (for iOS/macOS)',
        help_text='e.g., com.googleusercontent.apps.xxxxx - Used for URL scheme callback'
    )
    google_client_secret = models.CharField(
        max_length=200, blank=True,
        verbose_name='Google OAuth Client Secret',
        help_text='Client Secret for Windows/Linux only (not needed for iOS/macOS/Android)'
    )

    # Backup Feature Flags
    retailease_google_drive_enabled = models.BooleanField(default=True, verbose_name='Google Drive Backup')
    retailease_server_backup_enabled = models.BooleanField(default=True, verbose_name='Server Backup')
    retailease_local_backup_enabled = models.BooleanField(default=True, verbose_name='Local Backup')

    # App Version Control
    retailease_min_version = models.CharField(max_length=20, default='1.0.0', verbose_name='Min App Version')
    retailease_latest_version = models.CharField(max_length=20, default='1.0.0', verbose_name='Latest App Version')
    retailease_update_url = models.URLField(blank=True, verbose_name='App Update URL')
    retailease_force_update = models.BooleanField(default=False, verbose_name='Force Update')

    # Maintenance Mode (per-client)
    retailease_maintenance_mode = models.BooleanField(default=False, verbose_name='Maintenance Mode')
    retailease_maintenance_message = models.TextField(blank=True, verbose_name='Maintenance Message')

    # Support Contact (per-client)
    retailease_support_email = models.EmailField(blank=True, verbose_name='Support Email')
    retailease_support_phone = models.CharField(max_length=20, blank=True, verbose_name='Support Phone')
    retailease_support_whatsapp = models.CharField(max_length=20, blank=True, verbose_name='Support WhatsApp')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.company_name if self.company_name else self.name

    @property
    def total_revenue(self):
        return self.invoices.filter(status='paid').aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0

    @property
    def pending_amount(self):
        from django.db.models import F
        return self.invoices.exclude(status__in=['paid', 'cancelled']).aggregate(
            total=models.Sum(F('total_amount') - F('amount_paid'))
        )['total'] or 0


class Project(models.Model):
    """Project model linked to client"""
    TYPE_CHOICES = [
        ('web_app', 'Web Application'),
        ('mobile_app', 'Mobile App'),
        ('full_stack', 'Full Stack'),
        ('api', 'API Development'),
        ('maintenance', 'Maintenance'),
        ('consulting', 'Consulting'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('lead', 'Lead'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    project_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='web_app')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    tech_stack = models.CharField(max_length=255, blank=True)
    github_repo = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    team_members = models.ManyToManyField('TeamMember', blank=True, related_name='assigned_projects')
    # Completion & AMC fields
    warranty_period = models.IntegerField(null=True, blank=True, help_text='Warranty period in months')
    completion_notes = models.TextField(blank=True)
    deliverables = models.TextField(blank=True, help_text='List of deliverables (one per line)')
    amc_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text='Agreed AMC amount')
    AMC_BILLING_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
    ]
    amc_billing_cycle = models.CharField(max_length=20, choices=AMC_BILLING_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.client}"

    @property
    def is_overdue(self):
        if self.deadline and self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.deadline
        return False


class Credential(models.Model):
    """Credential vault for storing project credentials"""
    TYPE_CHOICES = [
        ('server', 'Server / SSH'),
        ('domain', 'Domain'),
        ('hosting', 'Hosting'),
        ('database', 'Database'),
        ('email', 'Email Account'),
        ('api', 'API Key'),
        ('ssl', 'SSL Certificate'),
        ('cdn', 'CDN'),
        ('cloud', 'Cloud Service'),
        ('git', 'Git Repository'),
        ('payment', 'Payment Gateway'),
        ('social', 'Social Media'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='credentials')
    credential_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=100, blank=True)
    url = models.URLField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    ssh_key = models.TextField(blank=True)
    port = models.IntegerField(null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    renewal_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    client_visible = models.BooleanField(default=False, help_text='Share this credential with the client in their portal')
    last_renewed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['expiry_date', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_credential_type_display()})"

    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def is_expiring_soon(self):
        if self.expiry_date:
            return timezone.now().date() <= self.expiry_date <= timezone.now().date() + timedelta(days=30)
        return False

    @property
    def days_until_expiry(self):
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None


class AMCContract(models.Model):
    """Recurring service contract (AMC, content updates, hosting, etc.) linked to a project"""
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    CONTRACT_TYPE_CHOICES = [
        ('amc', 'AMC'),
        ('content_update', 'Content Update'),
        ('hosting', 'Hosting'),
        ('seo', 'SEO / Marketing'),
        ('support', 'Support Plan'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='amc_contracts')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, default='amc')
    annual_amount = models.DecimalField(max_digits=12, decimal_places=2)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='yearly')
    start_date = models.DateField()
    end_date = models.DateField()
    next_due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_due_date', '-created_at']

    def __str__(self):
        return f"{self.get_contract_type_display()} - {self.project.name} ({self.get_status_display()})"

    @property
    def is_overdue(self):
        return self.status == 'active' and self.next_due_date < timezone.now().date()

    @property
    def is_due_soon(self):
        today = timezone.now().date()
        return self.status == 'active' and today <= self.next_due_date <= today + timedelta(days=30)

    @property
    def days_until_due(self):
        delta = self.next_due_date - timezone.now().date()
        return delta.days

    @property
    def total_paid(self):
        from django.db.models import Sum
        return self.payments.aggregate(total=Sum('amount'))['total'] or 0

    def advance_due_date(self):
        """Advance next_due_date based on billing cycle after payment"""
        from dateutil.relativedelta import relativedelta
        cycle_map = {
            'monthly': relativedelta(months=1),
            'quarterly': relativedelta(months=3),
            'half_yearly': relativedelta(months=6),
            'yearly': relativedelta(years=1),
        }
        self.next_due_date = self.next_due_date + cycle_map[self.billing_cycle]
        if self.next_due_date > self.end_date:
            self.status = 'expired'
        self.save()


class AMCPayment(models.Model):
    """Tracks each AMC payment/renewal"""
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('cheque', 'Cheque'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amc = models.ForeignKey(AMCContract, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"AMC Payment ₹{self.amount} - {self.amc.project.name}"


class CredentialRenewal(models.Model):
    """Tracks credential renewal history"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credential = models.ForeignKey(Credential, on_delete=models.CASCADE, related_name='renewal_history')
    renewed_date = models.DateField(default=timezone.now)
    old_expiry = models.DateField(null=True, blank=True)
    new_expiry = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-renewed_date']

    def __str__(self):
        return f"Renewal of {self.credential.name} on {self.renewed_date}"


class Quote(models.Model):
    """Quotation model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote_number = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='quotes')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    issue_date = models.DateField(default=timezone.now)
    valid_until = models.DateField()

    # Timeline & Deliverables
    duration = models.CharField(max_length=100, blank=True, help_text='e.g., 4-6 weeks')
    start_date = models.DateField(null=True, blank=True)
    deliverables = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=50, default='50-50', blank=True)

    terms = models.TextField(blank=True)
    client_notes = models.TextField(blank=True, help_text='Notes visible to the client on the quote')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quote_number} - {self.client}"

    def save(self, *args, **kwargs):
        if not self.quote_number:
            settings = CompanySettings.get_settings()
            prefix = settings.quote_prefix
            matching_quotes = Quote.objects.filter(quote_number__startswith=prefix)
            max_number = 0
            for q in matching_quotes:
                try:
                    num = int(q.quote_number[len(prefix):])
                    if num > max_number:
                        max_number = num
                except (ValueError, IndexError):
                    continue
            new_number = max_number + 1 if max_number > 0 else settings.quote_starting_number
            self.quote_number = f'{prefix}{new_number}'
        super().save(*args, **kwargs)
        # When quote is accepted and linked to a project, set project budget
        if self.status == 'accepted' and self.project:
            self.project.estimated_budget = self.total_amount
            self.project.save(update_fields=['estimated_budget'])

    def calculate_totals(self):
        self.subtotal = sum(item.amount for item in self.items.all())
        taxable_amount = self.subtotal - self.discount
        self.tax_amount = taxable_amount * (self.tax_rate / 100)
        self.total_amount = taxable_amount + self.tax_amount
        self.save()

    @property
    def is_expired(self):
        if self.valid_until:
            return timezone.now().date() > self.valid_until
        return False

    @property
    def days_until_expiry(self):
        if self.valid_until:
            delta = self.valid_until - timezone.now().date()
            return delta.days
        return None

    @property
    def is_expiring_soon(self):
        """Returns True if quote expires within 7 days"""
        if self.valid_until and not self.is_expired:
            days = self.days_until_expiry
            return days is not None and days <= 7
        return False


class QuoteItem(models.Model):
    """Line items for quotes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=500)
    details = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """Invoice model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    GST_FILING_STATUS_CHOICES = [
        ('pending', 'Pending GST filing'),
        ('filed', 'Filed in GSTR'),
        ('not_applicable', 'GST not applicable'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    gst_filing_status = models.CharField(
        max_length=20, choices=GST_FILING_STATUS_CHOICES, default='pending',
        help_text='Tracks whether this invoice has been included in a GSTR filing.'
    )
    gst_filed_at = models.DateTimeField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    terms = models.TextField(blank=True)
    client_notes = models.TextField(blank=True, help_text='Notes visible to the client on the invoice')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.client}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            settings = CompanySettings.get_settings()
            prefix = settings.invoice_prefix
            # Find the highest invoice number with the same prefix
            matching_invoices = Invoice.objects.filter(invoice_number__startswith=prefix)
            max_number = 0
            for inv in matching_invoices:
                try:
                    num = int(inv.invoice_number[len(prefix):])
                    if num > max_number:
                        max_number = num
                except (ValueError, IndexError):
                    continue
            if max_number > 0:
                new_number = max_number + 1
            else:
                # Use starting number from settings
                new_number = settings.invoice_starting_number
            self.invoice_number = f'{prefix}{new_number}'
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['paid', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False

    @property
    def days_until_due(self):
        if self.due_date:
            delta = self.due_date - timezone.now().date()
            return delta.days
        return 0

    @property
    def cgst_amount(self):
        """Calculate CGST (half of total tax)"""
        from decimal import Decimal
        return (self.tax_amount or Decimal('0')) / 2

    @property
    def sgst_amount(self):
        """Calculate SGST (half of total tax)"""
        from decimal import Decimal
        return (self.tax_amount or Decimal('0')) / 2

    @property
    def half_tax_rate(self):
        """Half of tax rate for CGST/SGST display"""
        from decimal import Decimal
        tax_rate = self.tax_rate if self.tax_rate is not None else Decimal('0')
        return tax_rate / 2

    def calculate_totals(self):
        from decimal import Decimal
        self.subtotal = sum(item.amount for item in self.items.all()) or Decimal('0')
        taxable_amount = self.subtotal - (self.discount or Decimal('0'))
        # Use tax_rate as-is (0 means no tax), only default to 0 if None
        tax_rate = self.tax_rate if self.tax_rate is not None else Decimal('0')
        self.tax_amount = taxable_amount * (tax_rate / 100)
        self.total_amount = taxable_amount + self.tax_amount
        self.save()

    def update_payment_status(self):
        if self.amount_paid >= self.total_amount:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        elif self.is_overdue:
            self.status = 'overdue'
        self.save()


class InvoiceItem(models.Model):
    """Line items for invoices"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=500)
    details = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment tracking model"""
    METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='bank_transfer')
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment of ₹{self.amount} for {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._recompute_invoice_totals()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        total_paid = invoice.payments.aggregate(total=models.Sum('amount'))['total'] or 0
        invoice.amount_paid = total_paid
        invoice.update_payment_status()

    def _recompute_invoice_totals(self):
        total_paid = self.invoice.payments.aggregate(total=models.Sum('amount'))['total'] or 0
        self.invoice.amount_paid = total_paid
        self.invoice.update_payment_status()


class CompanySettings(models.Model):
    """Singleton model for company settings"""
    company_name = models.CharField(max_length=255, default='Ralfiz Technologies')
    tagline = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True, verbose_name='GST Number')
    pan_number = models.CharField(max_length=20, blank=True, verbose_name='PAN Number')
    hsn_code = models.CharField(max_length=20, blank=True, verbose_name='HSN/SAC Code', help_text='HSN code for goods or SAC code for services')
    logo = models.FileField(upload_to='company/', blank=True, help_text='Accepts PNG, JPG, or SVG files')

    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc = models.CharField(max_length=20, blank=True, verbose_name='IFSC Code')
    bank_branch = models.CharField(max_length=100, blank=True)
    upi_id = models.CharField(max_length=100, blank=True, verbose_name='UPI ID')

    # Default settings
    invoice_prefix = models.CharField(max_length=10, default='INVRT', help_text='Prefix for invoice numbers (e.g., INVRT)')
    invoice_starting_number = models.IntegerField(default=201, help_text='Starting number for invoices (used when no invoices exist)')
    quote_prefix = models.CharField(max_length=10, default='QT')
    quote_starting_number = models.IntegerField(default=1, help_text='Starting number for quotes (used when no quotes exist with the current prefix)')
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    default_quote_validity_days = models.IntegerField(default=30, help_text='Default number of days a quote is valid')
    default_payment_terms = models.CharField(max_length=50, default='50-50', blank=True, help_text='Default payment terms for quotes')
    invoice_terms = models.TextField(blank=True)
    quote_terms = models.TextField(blank=True)

    # Email Settings
    smtp_host = models.CharField(max_length=255, blank=True, verbose_name='SMTP Host')
    smtp_port = models.IntegerField(default=587, verbose_name='SMTP Port')
    smtp_user = models.CharField(max_length=255, blank=True, verbose_name='SMTP Username')
    smtp_password = models.CharField(max_length=255, blank=True, verbose_name='SMTP Password')
    smtp_use_tls = models.BooleanField(default=True, verbose_name='Use TLS')
    from_email = models.EmailField(blank=True, verbose_name='From Email')

    # ============================================
    # RetailEase App Configuration
    # ============================================
    # Google OAuth for backup
    google_client_id = models.CharField(
        max_length=200, blank=True,
        verbose_name='Google OAuth Client ID (Desktop)',
        help_text='OAuth 2.0 Client ID for Windows/Linux (Desktop type in Google Cloud Console)'
    )
    google_client_id_ios = models.CharField(
        max_length=200, blank=True,
        verbose_name='Google OAuth Client ID (iOS/macOS)',
        help_text='OAuth 2.0 Client ID for iOS & macOS (iOS type in Google Cloud Console)'
    )
    google_client_id_android = models.CharField(
        max_length=200, blank=True,
        verbose_name='Google OAuth Client ID (Android)',
        help_text='OAuth 2.0 Client ID for Android (Android type in Google Cloud Console)'
    )
    google_reversed_client_id = models.CharField(
        max_length=200, blank=True,
        verbose_name='Reversed Client ID (for iOS/macOS)',
        help_text='e.g., com.googleusercontent.apps.xxxxx - Used for URL scheme callback'
    )

    # RetailEase Feature Flags
    retailease_google_drive_enabled = models.BooleanField(default=True, verbose_name='Google Drive Backup')
    retailease_server_backup_enabled = models.BooleanField(default=True, verbose_name='Server Backup')
    retailease_local_backup_enabled = models.BooleanField(default=True, verbose_name='Local Backup')

    # RetailEase App Version
    retailease_min_version = models.CharField(max_length=20, default='1.0.0', verbose_name='Min App Version')
    retailease_latest_version = models.CharField(max_length=20, default='1.0.0', verbose_name='Latest App Version')
    retailease_update_url = models.URLField(blank=True, verbose_name='App Update URL')
    retailease_force_update = models.BooleanField(default=False, verbose_name='Force Update')

    # Maintenance Mode
    retailease_maintenance_mode = models.BooleanField(default=False, verbose_name='Maintenance Mode')
    retailease_maintenance_message = models.TextField(blank=True, verbose_name='Maintenance Message')

    # Support
    retailease_support_email = models.EmailField(default='support@ralfizdigital.in', verbose_name='Support Email')
    retailease_support_phone = models.CharField(max_length=20, blank=True, verbose_name='Support Phone')
    retailease_support_whatsapp = models.CharField(max_length=20, blank=True, verbose_name='Support WhatsApp')

    # ============================================
    # InterioDesk App Configuration
    # ============================================
    interiodesk_min_version = models.CharField(max_length=20, default='1.0.0', verbose_name='InterioDesk Min Version')
    interiodesk_latest_version = models.CharField(max_length=20, default='1.0.0', verbose_name='InterioDesk Latest Version')
    interiodesk_update_url_macos = models.URLField(blank=True, verbose_name='InterioDesk Update URL (macOS)')
    interiodesk_update_url_windows = models.URLField(blank=True, verbose_name='InterioDesk Update URL (Windows)')
    interiodesk_file_macos = models.FileField(upload_to='interiodesk/releases/', blank=True, verbose_name='InterioDesk macOS Installer (.dmg)')
    interiodesk_file_windows = models.FileField(upload_to='interiodesk/releases/', blank=True, verbose_name='InterioDesk Windows Installer (.exe)')
    interiodesk_force_update = models.BooleanField(default=False, verbose_name='InterioDesk Force Update')
    interiodesk_maintenance_mode = models.BooleanField(default=False, verbose_name='InterioDesk Maintenance Mode')
    interiodesk_maintenance_message = models.TextField(blank=True, verbose_name='InterioDesk Maintenance Message')
    interiodesk_release_notes = models.TextField(blank=True, verbose_name='InterioDesk Release Notes')

    class Meta:
        verbose_name = 'Company Settings'
        verbose_name_plural = 'Company Settings'

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Expense(models.Model):
    """Expense tracking model"""
    CATEGORY_CHOICES = [
        ('travel', 'Travel'),
        ('software', 'Software & Subscriptions'),
        ('hardware', 'Hardware & Equipment'),
        ('office', 'Office Supplies'),
        ('marketing', 'Marketing & Advertising'),
        ('professional', 'Professional Services'),
        ('utilities', 'Utilities'),
        ('meals', 'Meals & Entertainment'),
        ('other', 'Other'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    vendor = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    is_billable = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.vendor} - ₹{self.amount} ({self.get_category_display()})"


class OpeningBalance(models.Model):
    """Opening cash balances snapshot at the start of a financial year (or any cutover).

    Multiple rows allowed so each FY's opening position is preserved.
    The 'current' opening balance is the most recent row by as_of_date.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=50, help_text='e.g. "FY 2026-27"')
    as_of_date = models.DateField(help_text='Balances are effective from this date')
    cash_in_hand = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cash_in_account = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    accounts_receivable = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text='Total outstanding from clients carried into this FY (preserved when invoices are wiped).'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-as_of_date', '-created_at']

    def __str__(self):
        return f"{self.label} ({self.as_of_date})"

    @classmethod
    def current(cls):
        return cls.objects.order_by('-as_of_date', '-created_at').first()


class BankAccount(models.Model):
    """A money bucket: cash on hand or a bank account.

    Each Payment / Expense / InternalTransfer attributes to one of these.
    There must be exactly one is_cash row and exactly one is_primary_bank
    row at any time (enforced in save()); these are the defaults used to
    place legacy Payment.payment_method / Expense.payment_method values.
    """
    ACCOUNT_TYPE_CHOICES = [
        ('cash', 'Cash on Hand'),
        ('bank', 'Bank Account'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text='e.g. "Primary Current Account", "Joint Savings"')
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='bank')
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=40, blank=True)
    ifsc = models.CharField(max_length=20, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    upi_id = models.CharField(max_length=100, blank=True)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    opening_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_primary_bank = models.BooleanField(default=False, help_text='Default bucket for non-cash Payment/Expense methods. Exactly one.')
    is_cash = models.BooleanField(default=False, help_text='Default bucket for cash Payment/Expense. Exactly one.')
    display_order = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_primary_bank:
            BankAccount.objects.exclude(pk=self.pk).filter(is_primary_bank=True).update(is_primary_bank=False)
        if self.is_cash:
            BankAccount.objects.exclude(pk=self.pk).filter(is_cash=True).update(is_cash=False)
        super().save(*args, **kwargs)

    @property
    def account_number_last4(self):
        return self.account_number[-4:] if self.account_number else ''

    def resolved_payment_methods(self):
        """Which Payment.payment_method values land in this account."""
        if self.is_cash:
            return ['cash']
        if self.is_primary_bank:
            return ['bank_transfer', 'upi', 'card', 'paypal', 'cheque']
        return []

    def resolved_expense_methods(self):
        """Which Expense.payment_method values flow out of this account."""
        if self.is_cash:
            return ['cash']
        if self.is_primary_bank:
            return ['bank_transfer', 'upi', 'card']
        return []


class InternalTransfer(models.Model):
    """Movement of money between two of our own BankAccounts.

    NOT income or expense - the company's total assets are unchanged;
    only the distribution across accounts shifts. Reported separately
    from P&L for transparency.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='transfers_out')
    to_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='transfers_in')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now, help_text='Transfer date. May be future-dated for scheduled transfers.')
    reference = models.CharField(max_length=100, blank=True, help_text='UPI ref / cheque no / transaction id')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='internal_transfers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(from_account=models.F('to_account')),
                name='internaltransfer_from_to_distinct'
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='internaltransfer_amount_positive'
            ),
        ]

    def __str__(self):
        return f"{self.from_account} → {self.to_account} ₹{self.amount} ({self.date})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.from_account_id and self.to_account_id and self.from_account_id == self.to_account_id:
            raise ValidationError('Source and destination accounts must be different.')
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be greater than zero.'})


class FYResetEvent(models.Model):
    """Audit record of every Financial Year reset (data wipe).

    Captures who ran the reset, when, what was wiped, and the financial
    position at that moment so the action is traceable after the
    underlying invoices/payments/expenses are gone.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ran_at = models.DateTimeField(auto_now_add=True)
    ran_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fy_resets'
    )
    invoices_wiped = models.IntegerField(default=0)
    payments_wiped = models.IntegerField(default=0)
    expenses_wiped = models.IntegerField(default=0)
    leads_wiped = models.IntegerField(default=0)
    outstanding_receivables = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text='Sum of unpaid invoice balance_due at the moment of reset.'
    )
    opening_balance = models.ForeignKey(
        OpeningBalance, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='resets',
        help_text='Opening balance active when the reset ran (carries receivables forward).'
    )
    invoice_prefix_after = models.CharField(max_length=10, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-ran_at']

    def __str__(self):
        return f"FY reset on {self.ran_at:%d %b %Y %H:%M} by {self.ran_by or 'unknown'}"


class TeamMember(models.Model):
    """Team member model for task assignment"""
    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('project_manager', 'Project Manager'),
        ('qa', 'QA Engineer'),
        ('devops', 'DevOps'),
        ('digital_marketing', 'Digital Marketing'),
        ('growth_outreach', 'Growth and Outreach Executive'),
        ('other', 'Other'),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('freelancer', 'Freelancer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='team_profile')
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='permanent')
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text='For permanent employees')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='For freelancers')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

    @property
    def is_freelancer(self):
        return self.employment_type == 'freelancer'

    @property
    def is_team_member(self):
        """Check if this user is a team member (not admin)"""
        return self.user is not None and not self.user.is_superuser


class Task(models.Model):
    """Task management model"""
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('completed', 'Completed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(TeamMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['completed']:
            return timezone.now().date() > self.due_date
        return False

    @property
    def client_visible_comment_count(self):
        return self.comments.filter(is_visible_to_client=True, is_deleted=False).count()

    @property
    def open_issue_count(self):
        return self.issues.filter(status__in=['open', 'in_progress']).count()

    @property
    def client_visible_issue_count(self):
        return self.issues.filter(is_visible_to_client=True).count()


class TaskAttachment(models.Model):
    """File/image attachments for tasks"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    name = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='task_attachments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name or self.file.name

    @property
    def file_extension(self):
        return self.file.name.split('.')[-1].lower() if self.file else ''

    @property
    def is_image(self):
        return self.file_extension in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'svg')


class TaskComment(models.Model):
    """Threaded comments on tasks (Jira-style)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='task_comments')
    body = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    attachment = models.FileField(upload_to='task_comment_attachments/', blank=True, null=True)
    is_visible_to_client = models.BooleanField(default=False, help_text='If true, this comment appears in the client portal.')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author} on {self.task_id}'


class TaskIssue(models.Model):
    """Issues/bugs/blockers reported against a task."""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='issues')
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_task_issues')
    assignee = models.ForeignKey(TeamMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_task_issues')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_visible_to_client = models.BooleanField(default=False)
    resolution = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.severity}] {self.title}'

    @property
    def is_open(self):
        return self.status in ('open', 'in_progress')


class TaskActivity(models.Model):
    """Immutable activity log for a task (status changes, comments, issues)."""
    VERB_CHOICES = [
        ('created', 'Task Created'),
        ('status_changed', 'Status Changed'),
        ('priority_changed', 'Priority Changed'),
        ('assigned', 'Assigned'),
        ('commented', 'Commented'),
        ('issue_opened', 'Issue Opened'),
        ('issue_status_changed', 'Issue Status Changed'),
        ('issue_resolved', 'Issue Resolved'),
        ('attachment_added', 'Attachment Added'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='task_activities')
    verb = models.CharField(max_length=32, choices=VERB_CHOICES)
    from_value = models.CharField(max_length=255, blank=True)
    to_value = models.CharField(max_length=255, blank=True)
    message = models.CharField(max_length=500, blank=True)
    is_visible_to_client = models.BooleanField(default=False)
    related_comment = models.ForeignKey(TaskComment, on_delete=models.SET_NULL, null=True, blank=True)
    related_issue = models.ForeignKey(TaskIssue, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Task activities'

    def __str__(self):
        return f'{self.verb} on {self.task_id}'


class TimeEntry(models.Model):
    """Time tracking model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='time_entries')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='time_entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_entries')
    description = models.TextField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField(default=timezone.now)
    is_billable = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Time entries'

    def __str__(self):
        return f"{self.project.name} - {self.hours}h on {self.date}"

    @property
    def total_amount(self):
        if self.hourly_rate:
            return self.hours * self.hourly_rate
        return 0


class ActivityLog(models.Model):
    """Activity log for tracking all system changes"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('viewed', 'Viewed'),
        ('sent', 'Sent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=255)
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Activity logs'

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} at {self.timestamp}"


class Document(models.Model):
    """Document attachments for clients, projects, invoices, quotes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='documents/')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')

    # Generic foreign key to attach to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def file_extension(self):
        return self.file.name.split('.')[-1].lower() if self.file else ''

    @property
    def file_size(self):
        try:
            return self.file.size
        except:
            return 0


class ProjectType(models.Model):
    """Configurable project types for client feature-request forms (Website, E-commerce, etc.)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=255, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class ProjectFeature(models.Model):
    """Feature options grouped under a ProjectType."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_type = models.ForeignKey(ProjectType, on_delete=models.CASCADE, related_name='features')
    label = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['project_type', 'sort_order', 'label']
        unique_together = ['project_type', 'label']

    def __str__(self):
        return f"{self.project_type.name} - {self.label}"


def _gen_otp():
    import secrets
    return f"{secrets.randbelow(1000000):06d}"


class FeatureRequestLink(models.Model):
    """Shareable link for a client to select project features. OTP-gated, single-use."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='feature_request_links')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False,
                             help_text='Opaque token used in the shareable URL')
    otp = models.CharField(max_length=6, default=_gen_otp,
                           help_text='6-digit OTP shown to the admin; shared manually with the client')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='created_feature_request_links')
    created_at = models.DateTimeField(auto_now_add=True)

    # Submission state
    submitted_at = models.DateTimeField(null=True, blank=True)
    selected_project_type = models.ForeignKey(ProjectType, on_delete=models.SET_NULL, null=True, blank=True,
                                              related_name='+')
    selected_features = models.ManyToManyField(ProjectFeature, blank=True, related_name='submissions')
    client_notes = models.TextField(blank=True, help_text='Free-form notes from the client')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client} - {'submitted' if self.is_submitted else 'pending'}"

    @property
    def is_submitted(self):
        return self.submitted_at is not None
