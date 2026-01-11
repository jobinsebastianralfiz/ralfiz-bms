from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    Client, Project, Credential, Quote, QuoteItem, Invoice, InvoiceItem, Payment, CompanySettings
)


# ============== Authentication Views ==============

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# ============== Dashboard ==============

@login_required
def dashboard(request):
    # Get summary stats
    total_clients = Client.objects.filter(is_active=True).count()
    active_projects = Project.objects.exclude(status__in=['completed', 'cancelled']).count()

    # Pending invoices
    pending_invoices = Invoice.objects.exclude(status__in=['paid', 'cancelled'])
    pending_count = pending_invoices.count()
    pending_amount = pending_invoices.aggregate(
        total=Sum('total_amount') - Sum('amount_paid')
    )['total'] or 0

    # Revenue this month
    first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue_this_month = Payment.objects.filter(
        payment_date__gte=first_day_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Expiring credentials (next 30 days)
    expiring_soon = timezone.now().date() + timedelta(days=30)
    expiring_credentials = Credential.objects.filter(
        expiry_date__lte=expiring_soon,
        expiry_date__gte=timezone.now().date(),
        is_active=True
    ).select_related('project', 'project__client')[:5]

    # Overdue invoices
    overdue_invoices = Invoice.objects.filter(
        due_date__lt=timezone.now().date(),
        status__in=['sent', 'viewed', 'partial']
    ).select_related('client')[:5]

    # Recent payments
    recent_payments = Payment.objects.select_related(
        'invoice', 'invoice__client'
    ).order_by('-payment_date')[:5]

    # Recent invoices
    recent_invoices = Invoice.objects.select_related('client').order_by('-created_at')[:5]

    context = {
        'total_clients': total_clients,
        'active_projects': active_projects,
        'pending_count': pending_count,
        'pending_amount': pending_amount,
        'revenue_this_month': revenue_this_month,
        'expiring_credentials': expiring_credentials,
        'overdue_invoices': overdue_invoices,
        'recent_payments': recent_payments,
        'recent_invoices': recent_invoices,
    }
    return render(request, 'dashboard/index.html', context)


# ============== Clients ==============

@login_required
def client_list(request):
    clients = Client.objects.all()

    # Search
    search = request.GET.get('search', '')
    if search:
        clients = clients.filter(
            Q(name__icontains=search) |
            Q(company_name__icontains=search) |
            Q(email__icontains=search)
        )

    # Filter by priority
    priority = request.GET.get('priority', '')
    if priority:
        clients = clients.filter(priority=priority)

    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        clients = clients.filter(is_active=True)
    elif status == 'inactive':
        clients = clients.filter(is_active=False)

    context = {
        'clients': clients,
        'search': search,
        'priority': priority,
        'status': status,
    }
    return render(request, 'clients/list.html', context)


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    projects = client.projects.all()
    invoices = client.invoices.all()
    quotes = client.quotes.all()

    context = {
        'client': client,
        'projects': projects,
        'invoices': invoices,
        'quotes': quotes,
    }
    return render(request, 'clients/detail.html', context)


@login_required
def client_create(request):
    if request.method == 'POST':
        client = Client.objects.create(
            name=request.POST.get('name'),
            company_name=request.POST.get('company_name', ''),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            whatsapp=request.POST.get('whatsapp', ''),
            address=request.POST.get('address', ''),
            gst_number=request.POST.get('gst_number', ''),
            priority=request.POST.get('priority', 'medium'),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Client "{client}" created successfully.')
        return redirect('client_detail', pk=client.pk)

    return render(request, 'clients/form.html', {'form_title': 'Add New Client'})


@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        client.name = request.POST.get('name')
        client.company_name = request.POST.get('company_name', '')
        client.email = request.POST.get('email')
        client.phone = request.POST.get('phone', '')
        client.whatsapp = request.POST.get('whatsapp', '')
        client.address = request.POST.get('address', '')
        client.gst_number = request.POST.get('gst_number', '')
        client.priority = request.POST.get('priority', 'medium')
        client.notes = request.POST.get('notes', '')
        client.is_active = request.POST.get('is_active') == 'on'
        client.save()

        messages.success(request, f'Client "{client}" updated successfully.')
        return redirect('client_detail', pk=client.pk)

    return render(request, 'clients/form.html', {
        'client': client,
        'form_title': 'Edit Client'
    })


# ============== Projects ==============

@login_required
def project_list(request):
    projects = Project.objects.select_related('client').all()

    # Search
    search = request.GET.get('search', '')
    if search:
        projects = projects.filter(
            Q(name__icontains=search) |
            Q(client__name__icontains=search) |
            Q(client__company_name__icontains=search)
        )

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        projects = projects.filter(status=status)

    # Filter by type
    project_type = request.GET.get('type', '')
    if project_type:
        projects = projects.filter(project_type=project_type)

    context = {
        'projects': projects,
        'search': search,
        'status': status,
        'project_type': project_type,
        'status_choices': Project.STATUS_CHOICES,
        'type_choices': Project.TYPE_CHOICES,
    }
    return render(request, 'projects/list.html', context)


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project.objects.select_related('client'), pk=pk)
    credentials = project.credentials.all()
    invoices = project.invoices.all()
    quotes = project.quotes.all()

    context = {
        'project': project,
        'credentials': credentials,
        'invoices': invoices,
        'quotes': quotes,
    }
    return render(request, 'projects/detail.html', context)


@login_required
def project_create(request):
    clients = Client.objects.filter(is_active=True)

    if request.method == 'POST':
        project = Project.objects.create(
            client_id=request.POST.get('client'),
            name=request.POST.get('name'),
            project_type=request.POST.get('project_type', 'web_app'),
            description=request.POST.get('description', ''),
            status=request.POST.get('status', 'lead'),
            estimated_budget=request.POST.get('estimated_budget') or None,
            start_date=request.POST.get('start_date') or None,
            deadline=request.POST.get('deadline') or None,
            tech_stack=request.POST.get('tech_stack', ''),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Project "{project.name}" created successfully.')
        return redirect('project_detail', pk=project.pk)

    return render(request, 'projects/form.html', {
        'clients': clients,
        'form_title': 'Add New Project',
        'status_choices': Project.STATUS_CHOICES,
        'type_choices': Project.TYPE_CHOICES,
    })


@login_required
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    clients = Client.objects.filter(is_active=True)

    if request.method == 'POST':
        project.client_id = request.POST.get('client')
        project.name = request.POST.get('name')
        project.project_type = request.POST.get('project_type', 'web_app')
        project.description = request.POST.get('description', '')
        project.status = request.POST.get('status', 'lead')
        project.estimated_budget = request.POST.get('estimated_budget') or None
        project.final_amount = request.POST.get('final_amount') or None
        project.start_date = request.POST.get('start_date') or None
        project.deadline = request.POST.get('deadline') or None
        project.completed_date = request.POST.get('completed_date') or None
        project.tech_stack = request.POST.get('tech_stack', '')
        project.github_repo = request.POST.get('github_repo', '')
        project.live_url = request.POST.get('live_url', '')
        project.notes = request.POST.get('notes', '')
        project.save()

        messages.success(request, f'Project "{project.name}" updated successfully.')
        return redirect('project_detail', pk=project.pk)

    return render(request, 'projects/form.html', {
        'project': project,
        'clients': clients,
        'form_title': 'Edit Project',
        'status_choices': Project.STATUS_CHOICES,
        'type_choices': Project.TYPE_CHOICES,
    })


# ============== Credentials ==============

@login_required
def credential_list(request):
    credentials = Credential.objects.select_related('project', 'project__client').all()

    # Search
    search = request.GET.get('search', '')
    if search:
        credentials = credentials.filter(
            Q(name__icontains=search) |
            Q(provider__icontains=search) |
            Q(project__name__icontains=search)
        )

    # Filter by type
    cred_type = request.GET.get('type', '')
    if cred_type:
        credentials = credentials.filter(credential_type=cred_type)

    # Filter by expiry status
    expiry = request.GET.get('expiry', '')
    today = timezone.now().date()
    if expiry == 'expired':
        credentials = credentials.filter(expiry_date__lt=today)
    elif expiry == 'expiring':
        credentials = credentials.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=30)
        )

    context = {
        'credentials': credentials,
        'search': search,
        'cred_type': cred_type,
        'expiry': expiry,
        'type_choices': Credential.TYPE_CHOICES,
    }
    return render(request, 'credentials/list.html', context)


@login_required
def credential_detail(request, pk):
    credential = get_object_or_404(
        Credential.objects.select_related('project', 'project__client'),
        pk=pk
    )
    return render(request, 'credentials/detail.html', {'credential': credential})


@login_required
def credential_create(request):
    projects = Project.objects.select_related('client').all()

    if request.method == 'POST':
        credential = Credential.objects.create(
            project_id=request.POST.get('project'),
            name=request.POST.get('name'),
            credential_type=request.POST.get('credential_type', 'hosting'),
            provider=request.POST.get('provider', ''),
            username=request.POST.get('username', ''),
            password=request.POST.get('password', ''),
            url=request.POST.get('url', ''),
            expiry_date=request.POST.get('expiry_date') or None,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Credential "{credential.name}" created successfully.')
        return redirect('credential_detail', pk=credential.pk)

    return render(request, 'credentials/form.html', {
        'projects': projects,
        'form_title': 'Add New Credential',
        'type_choices': Credential.TYPE_CHOICES,
    })


@login_required
def credential_update(request, pk):
    credential = get_object_or_404(Credential, pk=pk)
    projects = Project.objects.select_related('client').all()

    if request.method == 'POST':
        credential.project_id = request.POST.get('project')
        credential.name = request.POST.get('name')
        credential.credential_type = request.POST.get('credential_type', 'hosting')
        credential.provider = request.POST.get('provider', '')
        credential.username = request.POST.get('username', '')
        credential.password = request.POST.get('password', '')
        credential.url = request.POST.get('url', '')
        credential.expiry_date = request.POST.get('expiry_date') or None
        credential.notes = request.POST.get('notes', '')
        credential.is_active = request.POST.get('is_active') == 'on'
        credential.save()

        messages.success(request, f'Credential "{credential.name}" updated successfully.')
        return redirect('credential_detail', pk=credential.pk)

    return render(request, 'credentials/form.html', {
        'credential': credential,
        'projects': projects,
        'form_title': 'Edit Credential',
        'type_choices': Credential.TYPE_CHOICES,
    })


@login_required
def credential_expiry(request):
    today = timezone.now().date()

    # Expired
    expired = Credential.objects.filter(
        expiry_date__lt=today, is_active=True
    ).select_related('project', 'project__client')

    # Expiring this week
    this_week = Credential.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=7),
        is_active=True
    ).select_related('project', 'project__client')

    # Expiring this month
    this_month = Credential.objects.filter(
        expiry_date__gt=today + timedelta(days=7),
        expiry_date__lte=today + timedelta(days=30),
        is_active=True
    ).select_related('project', 'project__client')

    context = {
        'expired': expired,
        'this_week': this_week,
        'this_month': this_month,
    }
    return render(request, 'credentials/expiry.html', context)


# ============== Quotes ==============

@login_required
def quote_list(request):
    quotes = Quote.objects.select_related('client', 'project').all()

    # Get stats counts
    all_quotes = Quote.objects.all()
    draft_count = all_quotes.filter(status='draft').count()
    sent_count = all_quotes.filter(status='sent').count()
    accepted_count = all_quotes.filter(status='accepted').count()
    rejected_count = all_quotes.filter(status='rejected').count()
    # Count quotes expiring within 7 days
    from datetime import timedelta
    expiring_date = timezone.now().date() + timedelta(days=7)
    expiring_count = all_quotes.filter(
        status__in=['sent', 'viewed'],
        valid_until__lte=expiring_date,
        valid_until__gte=timezone.now().date()
    ).count()

    search = request.GET.get('search', '')
    if search:
        quotes = quotes.filter(
            Q(quote_number__icontains=search) |
            Q(title__icontains=search) |
            Q(client__name__icontains=search)
        )

    status = request.GET.get('status', '')
    if status:
        quotes = quotes.filter(status=status)

    client_filter = request.GET.get('client', '')
    if client_filter:
        quotes = quotes.filter(client_id=client_filter)

    clients = Client.objects.filter(is_active=True)

    context = {
        'quotes': quotes,
        'search': search,
        'status': status,
        'status_choices': Quote.STATUS_CHOICES,
        'clients': clients,
        'selected_client': client_filter,
        'draft_count': draft_count,
        'sent_count': sent_count,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'expiring_count': expiring_count,
    }
    return render(request, 'quotes/list.html', context)


@login_required
def quote_detail(request, pk):
    quote = get_object_or_404(
        Quote.objects.select_related('client', 'project').prefetch_related('items'),
        pk=pk
    )
    return render(request, 'quotes/detail.html', {'quote': quote})


@login_required
def quote_create(request):
    clients = Client.objects.filter(is_active=True)
    projects = Project.objects.select_related('client').all()

    if request.method == 'POST':
        from decimal import Decimal

        quote = Quote.objects.create(
            client_id=request.POST.get('client'),
            project_id=request.POST.get('project') or None,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            issue_date=request.POST.get('issue_date') or timezone.now().date(),
            valid_until=request.POST.get('valid_until') or None,
            status=request.POST.get('status', 'draft'),
            discount=request.POST.get('discount', 0) or 0,
            tax_rate=request.POST.get('tax_rate', 18),
            notes=request.POST.get('notes', ''),
            terms=request.POST.get('terms', ''),
        )

        # Process line items
        item_count = int(request.POST.get('item_count', 0))
        for i in range(1, item_count + 10):  # Check extra indices for dynamically added items
            description = request.POST.get(f'item_description_{i}')
            if description:
                quantity = Decimal(request.POST.get(f'item_quantity_{i}', 1) or 1)
                unit_price = Decimal(request.POST.get(f'item_price_{i}', 0) or 0)
                QuoteItem.objects.create(
                    quote=quote,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=quantity * unit_price
                )

        # Recalculate totals
        quote.calculate_totals()

        messages.success(request, f'Quote "{quote.quote_number}" created successfully.')
        return redirect('quote_detail', pk=quote.pk)

    # Default dates
    from datetime import timedelta
    today = timezone.now().date()
    valid_until_default = today + timedelta(days=30)

    return render(request, 'quotes/form.html', {
        'clients': clients,
        'projects': projects,
        'form_title': 'Create New Quote',
        'status_choices': Quote.STATUS_CHOICES,
        'today': today.strftime('%Y-%m-%d'),
        'valid_until_default': valid_until_default.strftime('%Y-%m-%d'),
    })


@login_required
def quote_update(request, pk):
    quote = get_object_or_404(Quote.objects.prefetch_related('items'), pk=pk)
    clients = Client.objects.filter(is_active=True)
    projects = Project.objects.select_related('client').all()

    if request.method == 'POST':
        from decimal import Decimal

        quote.client_id = request.POST.get('client')
        quote.project_id = request.POST.get('project') or None
        quote.title = request.POST.get('title')
        quote.description = request.POST.get('description', '')
        quote.issue_date = request.POST.get('issue_date')
        quote.valid_until = request.POST.get('valid_until') or None
        quote.status = request.POST.get('status', 'draft')
        quote.discount = request.POST.get('discount', 0) or 0
        quote.tax_rate = request.POST.get('tax_rate', 18)
        quote.notes = request.POST.get('notes', '')
        quote.terms = request.POST.get('terms', '')
        quote.save()

        # Delete existing items and recreate
        quote.items.all().delete()

        # Process line items
        item_count = int(request.POST.get('item_count', 0))
        for i in range(1, item_count + 10):  # Check extra indices for dynamically added items
            description = request.POST.get(f'item_description_{i}')
            if description:
                quantity = Decimal(request.POST.get(f'item_quantity_{i}', 1) or 1)
                unit_price = Decimal(request.POST.get(f'item_price_{i}', 0) or 0)
                QuoteItem.objects.create(
                    quote=quote,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=quantity * unit_price
                )

        # Recalculate totals
        quote.calculate_totals()

        messages.success(request, f'Quote "{quote.quote_number}" updated successfully.')
        return redirect('quote_detail', pk=quote.pk)

    # Default dates
    from datetime import timedelta
    today = timezone.now().date()
    valid_until_default = today + timedelta(days=30)

    return render(request, 'quotes/form.html', {
        'quote': quote,
        'clients': clients,
        'projects': projects,
        'form_title': 'Edit Quote',
        'status_choices': Quote.STATUS_CHOICES,
        'today': today.strftime('%Y-%m-%d'),
        'valid_until_default': valid_until_default.strftime('%Y-%m-%d'),
    })


@login_required
def quote_pdf(request, pk):
    """Generate PDF for a quote - shows printable view"""
    quote = get_object_or_404(
        Quote.objects.select_related('client', 'project').prefetch_related('items'),
        pk=pk
    )

    # Check if GST should be included
    with_gst = request.GET.get('gst', '0') == '1'

    # Calculate amounts
    from decimal import Decimal
    taxable_amount = quote.subtotal - (quote.discount or Decimal('0'))
    tax_rate = Decimal(str(quote.tax_rate or 18))

    cgst_amount = Decimal('0')
    sgst_amount = Decimal('0')
    tax_amount = Decimal('0')
    total = taxable_amount

    if with_gst:
        # Split tax rate into CGST and SGST (half each)
        cgst_rate = tax_rate / 2
        sgst_rate = tax_rate / 2
        cgst_amount = taxable_amount * (cgst_rate / 100)
        sgst_amount = taxable_amount * (sgst_rate / 100)
        tax_amount = cgst_amount + sgst_amount
        total = taxable_amount + tax_amount

    return render(request, 'quotes/pdf.html', {
        'quote': quote,
        'with_gst': with_gst,
        'taxable_amount': taxable_amount,
        'tax_rate': tax_rate,
        'cgst_rate': tax_rate / 2 if with_gst else 0,
        'sgst_rate': tax_rate / 2 if with_gst else 0,
        'cgst_amount': cgst_amount,
        'sgst_amount': sgst_amount,
        'tax_amount': tax_amount,
        'total_with_gst': total,
    })


# ============== Invoices ==============

@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('client', 'project').all()

    search = request.GET.get('search', '')
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(title__icontains=search) |
            Q(client__name__icontains=search)
        )

    status = request.GET.get('status', '')
    if status:
        invoices = invoices.filter(status=status)

    context = {
        'invoices': invoices,
        'search': search,
        'status': status,
        'status_choices': Invoice.STATUS_CHOICES,
    }
    return render(request, 'invoices/list.html', context)


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('client', 'project').prefetch_related('items', 'payments'),
        pk=pk
    )
    return render(request, 'invoices/detail.html', {'invoice': invoice})


@login_required
def invoice_create(request):
    clients = Client.objects.filter(is_active=True)
    projects = Project.objects.select_related('client').all()
    quotes = Quote.objects.filter(status='accepted')

    if request.method == 'POST':
        from decimal import Decimal

        invoice = Invoice.objects.create(
            client_id=request.POST.get('client'),
            project_id=request.POST.get('project') or None,
            quote_id=request.POST.get('quote') or None,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            issue_date=request.POST.get('issue_date') or timezone.now().date(),
            due_date=request.POST.get('due_date') or None,
            status=request.POST.get('status', 'draft'),
            discount=Decimal(request.POST.get('discount', 0) or 0),
            tax_rate=request.POST.get('tax_rate', 18),
            notes=request.POST.get('notes', ''),
            terms=request.POST.get('terms', ''),
        )

        # Process line items
        item_count = int(request.POST.get('item_count', 0))
        for i in range(1, item_count + 10):  # Check a few extra indices in case of gaps
            description = request.POST.get(f'item_description_{i}')
            if description:
                quantity = Decimal(request.POST.get(f'item_quantity_{i}', 1) or 1)
                unit_price = Decimal(request.POST.get(f'item_price_{i}', 0) or 0)
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    total=quantity * unit_price
                )

        # Recalculate totals
        invoice.calculate_totals()

        messages.success(request, f'Invoice "{invoice.invoice_number}" created successfully.')
        return redirect('invoice_detail', pk=invoice.pk)

    # Get today's date and default due date (15 days from now)
    today = timezone.now().date()
    due_date_default = today + timezone.timedelta(days=15)

    return render(request, 'invoices/form.html', {
        'clients': clients,
        'projects': projects,
        'quotes': quotes,
        'form_title': 'Create New Invoice',
        'status_choices': Invoice.STATUS_CHOICES,
        'today': today.isoformat(),
        'due_date_default': due_date_default.isoformat(),
    })


@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice.objects.prefetch_related('items'), pk=pk)
    clients = Client.objects.filter(is_active=True)
    projects = Project.objects.select_related('client').all()
    quotes = Quote.objects.filter(status='accepted')

    if request.method == 'POST':
        from decimal import Decimal

        invoice.client_id = request.POST.get('client')
        invoice.project_id = request.POST.get('project') or None
        invoice.quote_id = request.POST.get('quote') or None
        invoice.title = request.POST.get('title')
        invoice.description = request.POST.get('description', '')
        invoice.issue_date = request.POST.get('issue_date')
        invoice.due_date = request.POST.get('due_date') or None
        invoice.status = request.POST.get('status', 'draft')
        invoice.discount = Decimal(request.POST.get('discount', 0) or 0)
        invoice.tax_rate = request.POST.get('tax_rate', 18)
        invoice.notes = request.POST.get('notes', '')
        invoice.terms = request.POST.get('terms', '')
        invoice.save()

        # Delete existing items and recreate
        invoice.items.all().delete()

        # Process line items
        item_count = int(request.POST.get('item_count', 0))
        for i in range(1, item_count + 10):  # Check a few extra indices in case of gaps
            description = request.POST.get(f'item_description_{i}')
            if description:
                quantity = Decimal(request.POST.get(f'item_quantity_{i}', 1) or 1)
                unit_price = Decimal(request.POST.get(f'item_price_{i}', 0) or 0)
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    total=quantity * unit_price
                )

        # Recalculate totals
        invoice.calculate_totals()

        messages.success(request, f'Invoice "{invoice.invoice_number}" updated successfully.')
        return redirect('invoice_detail', pk=invoice.pk)

    return render(request, 'invoices/form.html', {
        'invoice': invoice,
        'clients': clients,
        'projects': projects,
        'quotes': quotes,
        'form_title': 'Edit Invoice',
        'status_choices': Invoice.STATUS_CHOICES,
    })


@login_required
def invoice_pdf(request, pk):
    """Generate PDF for an invoice - shows printable view"""
    invoice = get_object_or_404(
        Invoice.objects.select_related('client', 'project').prefetch_related('items', 'payments'),
        pk=pk
    )

    # Check if GST should be included
    with_gst = request.GET.get('gst', '0') == '1'

    # Calculate amounts
    from decimal import Decimal
    taxable_amount = invoice.subtotal - (invoice.discount or Decimal('0'))
    tax_rate = Decimal(str(invoice.tax_rate or 18))

    cgst_amount = Decimal('0')
    sgst_amount = Decimal('0')
    tax_amount = Decimal('0')
    total = taxable_amount

    if with_gst:
        # Split tax rate into CGST and SGST (half each)
        cgst_rate = tax_rate / 2
        sgst_rate = tax_rate / 2
        cgst_amount = taxable_amount * (cgst_rate / 100)
        sgst_amount = taxable_amount * (sgst_rate / 100)
        tax_amount = cgst_amount + sgst_amount
        total = taxable_amount + tax_amount

    # Calculate balance due
    balance_due = total - (invoice.amount_paid or Decimal('0'))

    return render(request, 'invoices/pdf.html', {
        'invoice': invoice,
        'with_gst': with_gst,
        'taxable_amount': taxable_amount,
        'tax_rate': tax_rate,
        'cgst_rate': tax_rate / 2 if with_gst else 0,
        'sgst_rate': tax_rate / 2 if with_gst else 0,
        'cgst_amount': cgst_amount,
        'sgst_amount': sgst_amount,
        'tax_amount': tax_amount,
        'total_with_gst': total,
        'balance_due': balance_due,
    })


# ============== Payments ==============

@login_required
def payment_list(request):
    payments = Payment.objects.select_related('invoice', 'invoice__client').all()

    search = request.GET.get('search', '')
    if search:
        payments = payments.filter(
            Q(invoice__invoice_number__icontains=search) |
            Q(transaction_id__icontains=search) |
            Q(invoice__client__name__icontains=search)
        )

    method = request.GET.get('method', '')
    if method:
        payments = payments.filter(payment_method=method)

    context = {
        'payments': payments,
        'search': search,
        'method': method,
        'method_choices': Payment.METHOD_CHOICES,
    }
    return render(request, 'payments/list.html', context)


@login_required
def payment_create(request):
    invoices = Invoice.objects.exclude(status__in=['paid', 'cancelled']).select_related('client')

    if request.method == 'POST':
        payment = Payment.objects.create(
            invoice_id=request.POST.get('invoice'),
            amount=request.POST.get('amount'),
            payment_date=request.POST.get('payment_date') or timezone.now().date(),
            payment_method=request.POST.get('payment_method', 'bank_transfer'),
            transaction_id=request.POST.get('transaction_id', ''),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Payment of ₹{payment.amount} recorded successfully.')
        return redirect('invoice_detail', pk=payment.invoice.pk)

    return render(request, 'payments/form.html', {
        'invoices': invoices,
        'form_title': 'Record New Payment',
        'method_choices': Payment.METHOD_CHOICES,
    })


# ============== Settings & Reports ==============

@login_required
def settings_view(request):
    company = CompanySettings.get_settings()

    if request.method == 'POST':
        company.company_name = request.POST.get('company_name', '')
        company.tagline = request.POST.get('tagline', '')
        company.email = request.POST.get('email', '')
        company.phone = request.POST.get('phone', '')
        company.address = request.POST.get('address', '')
        company.gst_number = request.POST.get('gst_number', '')
        company.pan_number = request.POST.get('pan_number', '')
        company.bank_name = request.POST.get('bank_name', '')
        company.bank_account_number = request.POST.get('bank_account_number', '')
        company.bank_ifsc = request.POST.get('bank_ifsc', '')
        company.bank_branch = request.POST.get('bank_branch', '')
        company.upi_id = request.POST.get('upi_id', '')
        company.default_tax_rate = request.POST.get('default_tax_rate', 18)
        company.invoice_terms = request.POST.get('invoice_terms', '')
        company.quote_terms = request.POST.get('quote_terms', '')

        if request.FILES.get('logo'):
            company.logo = request.FILES.get('logo')

        company.save()
        messages.success(request, 'Settings updated successfully.')
        return redirect('settings')

    return render(request, 'settings/index.html', {'company': company})


@login_required
def reports_view(request):
    # Revenue stats
    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0

    # This month
    first_day = timezone.now().replace(day=1)
    this_month_revenue = Payment.objects.filter(
        payment_date__gte=first_day
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Outstanding
    outstanding = Invoice.objects.exclude(
        status__in=['paid', 'cancelled']
    ).aggregate(
        total=Sum('total_amount') - Sum('amount_paid')
    )['total'] or 0

    context = {
        'total_revenue': total_revenue,
        'this_month_revenue': this_month_revenue,
        'outstanding': outstanding,
    }
    return render(request, 'reports/index.html', context)
