import uuid
from django.db import models
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
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    issue_date = models.DateField(default=timezone.now)
    valid_until = models.DateField()
    terms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quote_number} - {self.client}"

    def save(self, *args, **kwargs):
        if not self.quote_number:
            year = timezone.now().year
            last_quote = Quote.objects.filter(quote_number__startswith=f'QT{year}').order_by('-quote_number').first()
            if last_quote:
                last_number = int(last_quote.quote_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.quote_number = f'QT{year}{new_number:04d}'
        super().save(*args, **kwargs)

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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    terms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.client}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(invoice_number__startswith=f'INV{year}').order_by('-invoice_number').first()
            if last_invoice:
                last_number = int(last_invoice.invoice_number[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.invoice_number = f'INV{year}{new_number:04d}'
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['paid', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False

    def calculate_totals(self):
        self.subtotal = sum(item.amount for item in self.items.all())
        taxable_amount = self.subtotal - self.discount
        self.tax_amount = taxable_amount * (self.tax_rate / 100)
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
        # Update invoice amount_paid
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
    logo = models.ImageField(upload_to='company/', blank=True)

    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc = models.CharField(max_length=20, blank=True, verbose_name='IFSC Code')
    bank_branch = models.CharField(max_length=100, blank=True)
    upi_id = models.CharField(max_length=100, blank=True, verbose_name='UPI ID')

    # Default settings
    invoice_prefix = models.CharField(max_length=10, default='INV')
    quote_prefix = models.CharField(max_length=10, default='QT')
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    invoice_terms = models.TextField(blank=True)
    quote_terms = models.TextField(blank=True)

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
