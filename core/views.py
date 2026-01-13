from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from .models import (
    Client, Project, Credential, Quote, QuoteItem, Invoice, InvoiceItem, Payment, CompanySettings,
    Expense, TeamMember, Task, TimeEntry, ActivityLog, Document
)
from django.contrib.contenttypes.models import ContentType


# ============== Authentication Views ==============

def login_view(request):
    if request.user.is_authenticated:
        # Check if user is a team member
        if hasattr(request.user, 'team_profile'):
            return redirect('team_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Redirect team members to their dashboard
            if hasattr(user, 'team_profile'):
                return redirect('team_dashboard')
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
    import json
    from dateutil.relativedelta import relativedelta

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

    # ============== Chart Data ==============

    # Monthly Revenue (Last 6 months)
    monthly_revenue_labels = []
    monthly_revenue_data = []
    today = timezone.now().date()

    for i in range(5, -1, -1):
        month_date = today - relativedelta(months=i)
        month_start = month_date.replace(day=1)
        if i > 0:
            month_end = (month_date + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
        else:
            month_end = today

        month_revenue = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_revenue_labels.append(month_date.strftime('%b %Y'))
        monthly_revenue_data.append(float(month_revenue))

    # Project Status Distribution
    project_status_data = {}
    for status_code, status_label in Project.STATUS_CHOICES:
        count = Project.objects.filter(status=status_code).count()
        if count > 0:
            project_status_data[status_label] = count

    # Invoice Status Distribution
    invoice_status_data = {}
    for status_code, status_label in Invoice.STATUS_CHOICES:
        count = Invoice.objects.filter(status=status_code).count()
        if count > 0:
            invoice_status_data[status_label] = count

    # Payment Method Distribution
    payment_method_data = {}
    for method_code, method_label in Payment.METHOD_CHOICES:
        total = Payment.objects.filter(payment_method=method_code).aggregate(
            total=Sum('amount')
        )['total'] or 0
        if total > 0:
            payment_method_data[method_label] = float(total)

    # Total revenue (all time)
    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'total_clients': total_clients,
        'active_projects': active_projects,
        'pending_count': pending_count,
        'pending_amount': pending_amount,
        'revenue_this_month': revenue_this_month,
        'total_revenue': total_revenue,
        'expiring_credentials': expiring_credentials,
        'overdue_invoices': overdue_invoices,
        'recent_payments': recent_payments,
        'recent_invoices': recent_invoices,
        # Chart data as JSON
        'monthly_revenue_labels': json.dumps(monthly_revenue_labels),
        'monthly_revenue_data': json.dumps(monthly_revenue_data),
        'project_status_labels': json.dumps(list(project_status_data.keys())),
        'project_status_data': json.dumps(list(project_status_data.values())),
        'invoice_status_labels': json.dumps(list(invoice_status_data.keys())),
        'invoice_status_data': json.dumps(list(invoice_status_data.values())),
        'payment_method_labels': json.dumps(list(payment_method_data.keys())),
        'payment_method_data': json.dumps(list(payment_method_data.values())),
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


# ============== Client Delete ==============

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        client_name = str(client)
        # Check for related records
        project_count = client.projects.count()
        invoice_count = client.invoices.count()
        quote_count = client.quotes.count()

        if project_count > 0 or invoice_count > 0 or quote_count > 0:
            messages.error(
                request,
                f'Cannot delete "{client_name}". It has {project_count} projects, '
                f'{invoice_count} invoices, and {quote_count} quotes associated with it.'
            )
            return redirect('client_detail', pk=pk)

        client.delete()
        messages.success(request, f'Client "{client_name}" deleted successfully.')
        return redirect('client_list')

    return render(request, 'clients/delete.html', {'client': client})


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

    # Get all payments for invoices related to this project
    payments = Payment.objects.filter(invoice__project=project).select_related('invoice').order_by('-payment_date')

    # Calculate financial stats
    from django.db.models import Sum
    from decimal import Decimal

    # Total project cost (use final_amount if set, otherwise estimated_budget)
    total_project_cost = project.final_amount or project.estimated_budget or Decimal('0')

    # Total invoiced amount for this project
    total_invoiced = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

    # Total amount received (sum of all payments)
    amount_received = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Pending amount = Total Project Cost - Amount Received
    pending_amount = total_project_cost - amount_received

    context = {
        'project': project,
        'credentials': credentials,
        'invoices': invoices,
        'quotes': quotes,
        'payments': payments,
        'total_project_cost': total_project_cost,
        'total_invoiced': total_invoiced,
        'amount_received': amount_received,
        'pending_amount': pending_amount,
    }
    return render(request, 'projects/detail.html', context)


@login_required
def project_create(request):
    clients = Client.objects.filter(is_active=True)
    team_members = TeamMember.objects.filter(is_active=True)

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
        # Assign team members
        selected_members = request.POST.getlist('team_members')
        if selected_members:
            project.team_members.set(selected_members)
        messages.success(request, f'Project "{project.name}" created successfully.')
        return redirect('project_detail', pk=project.pk)

    return render(request, 'projects/form.html', {
        'clients': clients,
        'team_members': team_members,
        'form_title': 'Add New Project',
        'status_choices': Project.STATUS_CHOICES,
        'type_choices': Project.TYPE_CHOICES,
    })


@login_required
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    clients = Client.objects.filter(is_active=True)
    team_members = TeamMember.objects.filter(is_active=True)

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

        # Update team members
        selected_members = request.POST.getlist('team_members')
        project.team_members.set(selected_members)

        messages.success(request, f'Project "{project.name}" updated successfully.')
        return redirect('project_detail', pk=project.pk)

    return render(request, 'projects/form.html', {
        'project': project,
        'clients': clients,
        'team_members': team_members,
        'form_title': 'Edit Project',
        'status_choices': Project.STATUS_CHOICES,
        'type_choices': Project.TYPE_CHOICES,
    })


# ============== Project Delete ==============

@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        project_name = project.name
        client_pk = project.client.pk

        # Check for related records
        credential_count = project.credentials.count()
        invoice_count = project.invoices.count()
        quote_count = project.quotes.count()

        if credential_count > 0 or invoice_count > 0 or quote_count > 0:
            messages.error(
                request,
                f'Cannot delete "{project_name}". It has {credential_count} credentials, '
                f'{invoice_count} invoices, and {quote_count} quotes associated with it.'
            )
            return redirect('project_detail', pk=pk)

        project.delete()
        messages.success(request, f'Project "{project_name}" deleted successfully.')
        return redirect('client_detail', pk=client_pk)

    return render(request, 'projects/delete.html', {'project': project})


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


# ============== Credential Delete ==============

@login_required
def credential_delete(request, pk):
    credential = get_object_or_404(Credential, pk=pk)

    if request.method == 'POST':
        credential_name = credential.name
        project_pk = credential.project.pk
        credential.delete()
        messages.success(request, f'Credential "{credential_name}" deleted successfully.')
        return redirect('project_detail', pk=project_pk)

    return render(request, 'credentials/delete.html', {'credential': credential})


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
        from decimal import Decimal, InvalidOperation

        # Safe tax_rate conversion - default to 0 if empty or invalid
        try:
            tax_rate_val = request.POST.get('tax_rate', '0')
            tax_rate = Decimal(tax_rate_val) if tax_rate_val else Decimal('0')
        except (InvalidOperation, ValueError):
            tax_rate = Decimal('0')

        # Safe discount conversion
        try:
            discount_val = request.POST.get('discount', '0')
            discount = Decimal(discount_val) if discount_val else Decimal('0')
        except (InvalidOperation, ValueError):
            discount = Decimal('0')

        quote = Quote.objects.create(
            client_id=request.POST.get('client'),
            project_id=request.POST.get('project') or None,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            issue_date=request.POST.get('issue_date') or timezone.now().date(),
            valid_until=request.POST.get('valid_until') or None,
            status=request.POST.get('status', 'draft'),
            discount=discount,
            tax_rate=tax_rate,
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
        from decimal import Decimal, InvalidOperation

        quote.client_id = request.POST.get('client')
        quote.project_id = request.POST.get('project') or None
        quote.title = request.POST.get('title')
        quote.description = request.POST.get('description', '')
        quote.issue_date = request.POST.get('issue_date')
        quote.valid_until = request.POST.get('valid_until') or None
        quote.status = request.POST.get('status', 'draft')

        # Safe decimal conversion - default to 0 if empty
        try:
            discount_val = request.POST.get('discount', '0')
            quote.discount = Decimal(discount_val) if discount_val else Decimal('0')
        except (InvalidOperation, ValueError):
            quote.discount = Decimal('0')

        try:
            tax_rate_val = request.POST.get('tax_rate', '0')
            quote.tax_rate = Decimal(tax_rate_val) if tax_rate_val else Decimal('0')
        except (InvalidOperation, ValueError):
            quote.tax_rate = Decimal('0')

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
    """Generate PDF for a quote"""
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from decimal import Decimal

    quote = get_object_or_404(
        Quote.objects.select_related('client', 'project').prefetch_related('items'),
        pk=pk
    )

    # Get company settings
    company = CompanySettings.get_settings()

    # Check if GST should be included
    with_gst = request.GET.get('gst', '0') == '1'
    download = request.GET.get('download', '0') == '1'

    # Calculate amounts
    taxable_amount = quote.subtotal - (quote.discount or Decimal('0'))
    # Use quote's tax_rate (0 means no tax), only default to 0 if None
    tax_rate = Decimal(str(quote.tax_rate)) if quote.tax_rate is not None else Decimal('0')

    cgst_amount = Decimal('0')
    sgst_amount = Decimal('0')
    tax_amount = Decimal('0')
    total = taxable_amount

    if with_gst:
        cgst_rate = tax_rate / 2
        sgst_rate = tax_rate / 2
        cgst_amount = taxable_amount * (cgst_rate / 100)
        sgst_amount = taxable_amount * (sgst_rate / 100)
        tax_amount = cgst_amount + sgst_amount
        total = taxable_amount + tax_amount

    context = {
        'quote': quote,
        'company': company,
        'with_gst': with_gst,
        'taxable_amount': taxable_amount,
        'tax_rate': tax_rate,
        'cgst_rate': tax_rate / 2 if with_gst else 0,
        'sgst_rate': tax_rate / 2 if with_gst else 0,
        'cgst_amount': cgst_amount,
        'sgst_amount': sgst_amount,
        'tax_amount': tax_amount,
        'total_with_gst': total,
    }

    # If download requested, generate PDF
    if download:
        try:
            from weasyprint import HTML, CSS
            from django.conf import settings
            import os

            html_string = render_to_string('quotes/pdf.html', context)

            # Create PDF
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf = html.write_pdf()

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="quote_{quote.quote_number}.pdf"'
            return response
        except ImportError:
            messages.warning(request, 'PDF generation requires WeasyPrint. Showing printable view instead.')

    return render(request, 'quotes/pdf.html', context)


# ============== Quote Delete ==============

@login_required
def quote_delete(request, pk):
    quote = get_object_or_404(Quote, pk=pk)

    if request.method == 'POST':
        quote_number = quote.quote_number
        # Check if quote has been converted to invoice
        if Invoice.objects.filter(quote=quote).exists():
            messages.error(
                request,
                f'Cannot delete "{quote_number}". It has been converted to an invoice.'
            )
            return redirect('quote_detail', pk=pk)

        quote.delete()
        messages.success(request, f'Quote "{quote_number}" deleted successfully.')
        return redirect('quote_list')

    return render(request, 'quotes/delete.html', {'quote': quote})


# ============== Quote Clone ==============

@login_required
def quote_clone(request, pk):
    """Clone an existing quote"""
    original_quote = get_object_or_404(
        Quote.objects.prefetch_related('items'),
        pk=pk
    )

    # Create new quote with copied data
    from decimal import Decimal

    today = timezone.now().date()
    valid_until = today + timedelta(days=30)

    new_quote = Quote.objects.create(
        client=original_quote.client,
        project=original_quote.project,
        title=f"Copy of {original_quote.title}",
        description=original_quote.description,
        status='draft',
        subtotal=original_quote.subtotal,
        discount=original_quote.discount,
        tax_rate=original_quote.tax_rate,
        tax_amount=original_quote.tax_amount,
        total_amount=original_quote.total_amount,
        issue_date=today,
        valid_until=valid_until,
        terms=original_quote.terms,
        notes=original_quote.notes,
    )

    # Clone all items
    for item in original_quote.items.all():
        QuoteItem.objects.create(
            quote=new_quote,
            description=item.description,
            details=item.details,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=item.amount,
            order=item.order,
        )

    messages.success(request, f'Quote cloned successfully. New quote: {new_quote.quote_number}')
    return redirect('quote_update', pk=new_quote.pk)


# ============== Quote to Invoice Conversion ==============

@login_required
def quote_convert(request, pk):
    """Convert a quote to an invoice"""
    quote = get_object_or_404(
        Quote.objects.select_related('client', 'project').prefetch_related('items'),
        pk=pk
    )

    # Check if already converted
    if Invoice.objects.filter(quote=quote).exists():
        existing_invoice = Invoice.objects.get(quote=quote)
        messages.warning(request, f'This quote has already been converted to invoice {existing_invoice.invoice_number}.')
        return redirect('invoice_detail', pk=existing_invoice.pk)

    from decimal import Decimal

    today = timezone.now().date()
    due_date = today + timedelta(days=15)

    # Create the invoice
    invoice = Invoice.objects.create(
        client=quote.client,
        project=quote.project,
        quote=quote,
        title=quote.title,
        description=quote.description,
        status='draft',
        subtotal=quote.subtotal,
        discount=quote.discount,
        tax_rate=quote.tax_rate,
        tax_amount=quote.tax_amount,
        total_amount=quote.total_amount,
        issue_date=today,
        due_date=due_date,
        terms=quote.terms,
        notes=quote.notes,
    )

    # Copy all items from quote to invoice
    for item in quote.items.all():
        InvoiceItem.objects.create(
            invoice=invoice,
            description=item.description,
            details=item.details,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item.amount,
            order=item.order,
        )

    # Update quote status to accepted if not already
    if quote.status not in ['accepted', 'rejected', 'expired']:
        quote.status = 'accepted'
        quote.save()

    messages.success(request, f'Quote converted to invoice {invoice.invoice_number} successfully.')
    return redirect('invoice_detail', pk=invoice.pk)


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

    # Always recalculate totals to ensure they match current items and tax rate
    if invoice.items.exists():
        invoice.calculate_totals()

    return render(request, 'invoices/detail.html', {'invoice': invoice})


@login_required
def invoice_create(request):
    clients = Client.objects.filter(is_active=True)
    projects = Project.objects.select_related('client').all()
    quotes = Quote.objects.filter(status='accepted')

    if request.method == 'POST':
        from decimal import Decimal, InvalidOperation

        # Safe tax_rate conversion - default to 0 if empty or invalid
        try:
            tax_rate_val = request.POST.get('tax_rate', '0')
            tax_rate = Decimal(tax_rate_val) if tax_rate_val else Decimal('0')
        except (InvalidOperation, ValueError):
            tax_rate = Decimal('0')

        # Safe discount conversion
        try:
            discount_val = request.POST.get('discount', '0')
            discount = Decimal(discount_val) if discount_val else Decimal('0')
        except (InvalidOperation, ValueError):
            discount = Decimal('0')

        invoice = Invoice.objects.create(
            client_id=request.POST.get('client'),
            project_id=request.POST.get('project') or None,
            quote_id=request.POST.get('quote') or None,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            issue_date=request.POST.get('issue_date') or timezone.now().date(),
            due_date=request.POST.get('due_date') or None,
            status=request.POST.get('status', 'draft'),
            discount=discount,
            tax_rate=tax_rate,
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
                    unit_price=unit_price
                )

        # Recalculate totals
        invoice.calculate_totals()

        messages.success(request, f'Invoice "{invoice.invoice_number}" created successfully.')
        return redirect('invoice_detail', pk=invoice.pk)

    # Get today's date and default due date (15 days from now)
    today = timezone.now().date()
    due_date_default = today + timezone.timedelta(days=15)

    # Get company settings for default terms
    company = CompanySettings.get_settings()

    return render(request, 'invoices/form.html', {
        'clients': clients,
        'projects': projects,
        'quotes': quotes,
        'company': company,
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
        from decimal import Decimal, InvalidOperation

        invoice.client_id = request.POST.get('client')
        invoice.project_id = request.POST.get('project') or None
        invoice.quote_id = request.POST.get('quote') or None
        invoice.title = request.POST.get('title')
        invoice.description = request.POST.get('description', '')
        invoice.issue_date = request.POST.get('issue_date') or timezone.now().date()
        invoice.due_date = request.POST.get('due_date') or None
        invoice.status = request.POST.get('status', 'draft')

        # Safe decimal conversion - default to 0 if empty
        try:
            discount_val = request.POST.get('discount', '0')
            invoice.discount = Decimal(discount_val) if discount_val else Decimal('0')
        except (InvalidOperation, ValueError):
            invoice.discount = Decimal('0')

        try:
            tax_rate_val = request.POST.get('tax_rate', '0')
            invoice.tax_rate = Decimal(tax_rate_val) if tax_rate_val else Decimal('0')
        except (InvalidOperation, ValueError):
            invoice.tax_rate = Decimal('0')

        invoice.notes = request.POST.get('notes', '')
        invoice.terms = request.POST.get('terms', '')
        invoice.save()

        # Delete existing items and recreate
        invoice.items.all().delete()

        # Process line items
        try:
            item_count = int(request.POST.get('item_count', 0) or 0)
        except ValueError:
            item_count = 0

        for i in range(1, item_count + 10):  # Check a few extra indices in case of gaps
            description = request.POST.get(f'item_description_{i}')
            if description:
                try:
                    qty_val = request.POST.get(f'item_quantity_{i}', '1') or '1'
                    quantity = Decimal(qty_val)
                except (InvalidOperation, ValueError):
                    quantity = Decimal('1')

                try:
                    price_val = request.POST.get(f'item_price_{i}', '0') or '0'
                    unit_price = Decimal(price_val)
                except (InvalidOperation, ValueError):
                    unit_price = Decimal('0')

                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price
                )

        # Recalculate totals
        invoice.calculate_totals()

        messages.success(request, f'Invoice "{invoice.invoice_number}" updated successfully.')
        return redirect('invoice_detail', pk=invoice.pk)

    # Get today's date and default due date (15 days from now) for form defaults
    today = timezone.now().date()
    due_date_default = today + timezone.timedelta(days=15)

    # Get company settings for default terms
    company = CompanySettings.get_settings()

    return render(request, 'invoices/form.html', {
        'invoice': invoice,
        'clients': clients,
        'projects': projects,
        'quotes': quotes,
        'company': company,
        'form_title': 'Edit Invoice',
        'status_choices': Invoice.STATUS_CHOICES,
        'today': today.isoformat(),
        'due_date_default': due_date_default.isoformat(),
    })


@login_required
def invoice_pdf(request, pk):
    """Generate PDF for an invoice"""
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from decimal import Decimal

    invoice = get_object_or_404(
        Invoice.objects.select_related('client', 'project').prefetch_related('items', 'payments'),
        pk=pk
    )

    # Get company settings
    company = CompanySettings.get_settings()

    # Check if GST should be included
    with_gst = request.GET.get('gst', '0') == '1'
    download = request.GET.get('download', '0') == '1'

    # Calculate amounts
    taxable_amount = invoice.subtotal - (invoice.discount or Decimal('0'))
    # Use invoice's tax_rate (0 means no tax), only default to 0 if None
    tax_rate = Decimal(str(invoice.tax_rate)) if invoice.tax_rate is not None else Decimal('0')

    cgst_amount = Decimal('0')
    sgst_amount = Decimal('0')
    tax_amount = Decimal('0')
    total = taxable_amount

    if with_gst:
        cgst_rate = tax_rate / 2
        sgst_rate = tax_rate / 2
        cgst_amount = taxable_amount * (cgst_rate / 100)
        sgst_amount = taxable_amount * (sgst_rate / 100)
        tax_amount = cgst_amount + sgst_amount
        total = taxable_amount + tax_amount

    # Calculate balance due
    balance_due = total - (invoice.amount_paid or Decimal('0'))

    context = {
        'invoice': invoice,
        'company': company,
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
    }

    # If download requested, generate PDF
    if download:
        try:
            from weasyprint import HTML, CSS

            html_string = render_to_string('invoices/pdf.html', context)

            # Create PDF
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf = html.write_pdf()

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
            return response
        except ImportError:
            messages.warning(request, 'PDF generation requires WeasyPrint. Showing printable view instead.')

    return render(request, 'invoices/pdf.html', context)


# ============== Invoice Delete ==============

@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        invoice_number = invoice.invoice_number
        # Check if invoice has payments
        payment_count = invoice.payments.count()

        if payment_count > 0:
            messages.error(
                request,
                f'Cannot delete "{invoice_number}". It has {payment_count} payment(s) recorded against it.'
            )
            return redirect('invoice_detail', pk=pk)

        invoice.delete()
        messages.success(request, f'Invoice "{invoice_number}" deleted successfully.')
        return redirect('invoice_list')

    return render(request, 'invoices/delete.html', {'invoice': invoice})


# ============== Invoice Clone ==============

@login_required
def invoice_clone(request, pk):
    """Clone an existing invoice"""
    original_invoice = get_object_or_404(
        Invoice.objects.prefetch_related('items'),
        pk=pk
    )

    from decimal import Decimal

    today = timezone.now().date()
    due_date = today + timedelta(days=15)

    new_invoice = Invoice.objects.create(
        client=original_invoice.client,
        project=original_invoice.project,
        title=f"Copy of {original_invoice.title}",
        description=original_invoice.description,
        status='draft',
        subtotal=original_invoice.subtotal,
        discount=original_invoice.discount,
        tax_rate=original_invoice.tax_rate,
        tax_amount=original_invoice.tax_amount,
        total_amount=original_invoice.total_amount,
        issue_date=today,
        due_date=due_date,
        terms=original_invoice.terms,
        notes=original_invoice.notes,
    )

    # Clone all items
    for item in original_invoice.items.all():
        InvoiceItem.objects.create(
            invoice=new_invoice,
            description=item.description,
            details=item.details,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item.total,
            order=item.order,
        )

    messages.success(request, f'Invoice cloned successfully. New invoice: {new_invoice.invoice_number}')
    return redirect('invoice_update', pk=new_invoice.pk)


# ============== Payments ==============

@login_required
def payment_list(request):
    import json
    from dateutil.relativedelta import relativedelta

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

    # ============== Stats & Chart Data ==============
    today = timezone.now().date()

    # Total payments
    total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0

    # This month
    first_day = today.replace(day=1)
    this_month = Payment.objects.filter(
        payment_date__gte=first_day
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Payment count
    payment_count = Payment.objects.count()

    # Monthly payments (last 6 months)
    monthly_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        month_date = today - relativedelta(months=i)
        month_start = month_date.replace(day=1)
        if i > 0:
            month_end = (month_date + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
        else:
            month_end = today

        month_total = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_labels.append(month_date.strftime('%b'))
        monthly_data.append(float(month_total))

    # Payment method distribution
    method_data = {}
    for method_code, method_label in Payment.METHOD_CHOICES:
        total = Payment.objects.filter(payment_method=method_code).aggregate(
            total=Sum('amount')
        )['total'] or 0
        if total > 0:
            method_data[method_label] = float(total)

    context = {
        'payments': payments.order_by('-payment_date'),
        'search': search,
        'method': method,
        'method_choices': Payment.METHOD_CHOICES,
        'total_payments': total_payments,
        'this_month': this_month,
        'payment_count': payment_count,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
        'method_labels': json.dumps(list(method_data.keys())),
        'method_data': json.dumps(list(method_data.values())),
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


@login_required
def payment_receipt(request, pk):
    """Generate receipt for a payment"""
    payment = get_object_or_404(
        Payment.objects.select_related('invoice', 'invoice__client'),
        pk=pk
    )

    # Get company settings
    company = CompanySettings.get_settings()

    # Generate receipt number based on payment
    receipt_number = f"REC{payment.payment_date.strftime('%Y%m%d')}{str(payment.pk)[:8].upper()}"

    context = {
        'payment': payment,
        'invoice': payment.invoice,
        'client': payment.invoice.client,
        'company': company,
        'receipt_number': receipt_number,
    }

    download = request.GET.get('download', '0') == '1'

    # If download requested, generate PDF
    if download:
        try:
            from weasyprint import HTML
            from django.template.loader import render_to_string

            html_string = render_to_string('payments/receipt.html', context)
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf = html.write_pdf()

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{receipt_number}.pdf"'
            return response
        except ImportError:
            messages.warning(request, 'PDF generation requires WeasyPrint. Showing printable view instead.')

    return render(request, 'payments/receipt.html', context)


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
        company.hsn_code = request.POST.get('hsn_code', '')
        company.bank_name = request.POST.get('bank_name', '')
        company.bank_account_number = request.POST.get('bank_account_number', '')
        company.bank_ifsc = request.POST.get('bank_ifsc', '')
        company.bank_branch = request.POST.get('bank_branch', '')
        company.upi_id = request.POST.get('upi_id', '')

        # Safe default_tax_rate conversion - default to 0 if empty
        from decimal import Decimal, InvalidOperation
        try:
            tax_rate_val = request.POST.get('default_tax_rate', '0')
            company.default_tax_rate = Decimal(tax_rate_val) if tax_rate_val else Decimal('0')
        except (InvalidOperation, ValueError):
            company.default_tax_rate = Decimal('0')

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
    import json
    from dateutil.relativedelta import relativedelta
    from collections import defaultdict

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

    # ============== Chart Data ==============
    today = timezone.now().date()

    # Monthly Revenue (Last 12 months)
    monthly_revenue_labels = []
    monthly_revenue_data = []
    monthly_invoiced_data = []

    for i in range(11, -1, -1):
        month_date = today - relativedelta(months=i)
        month_start = month_date.replace(day=1)
        if i > 0:
            month_end = (month_date + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
        else:
            month_end = today

        # Payments received
        month_revenue = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Invoices issued
        month_invoiced = Invoice.objects.filter(
            issue_date__gte=month_start,
            issue_date__lte=month_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        monthly_revenue_labels.append(month_date.strftime('%b'))
        monthly_revenue_data.append(float(month_revenue))
        monthly_invoiced_data.append(float(month_invoiced))

    # Revenue by Client (Top 5)
    client_revenue = defaultdict(float)
    for payment in Payment.objects.select_related('invoice__client').all():
        client_revenue[payment.invoice.client.name] += float(payment.amount)

    sorted_clients = sorted(client_revenue.items(), key=lambda x: x[1], reverse=True)[:5]
    client_labels = [c[0] for c in sorted_clients]
    client_data = [c[1] for c in sorted_clients]

    # Revenue by Project Type
    project_type_revenue = defaultdict(float)
    for payment in Payment.objects.select_related('invoice__project').all():
        if payment.invoice.project:
            project_type = payment.invoice.project.get_project_type_display()
        else:
            project_type = 'No Project'
        project_type_revenue[project_type] += float(payment.amount)

    project_type_labels = list(project_type_revenue.keys())
    project_type_data = list(project_type_revenue.values())

    # Quarterly Comparison
    quarterly_data = []
    quarterly_labels = []
    for q in range(3, -1, -1):
        quarter_start = today - relativedelta(months=q*3)
        quarter_end = quarter_start + relativedelta(months=3) - timedelta(days=1)
        q_start = quarter_start.replace(day=1)

        quarter_revenue = Payment.objects.filter(
            payment_date__gte=q_start,
            payment_date__lte=quarter_end
        ).aggregate(total=Sum('amount'))['total'] or 0

        quarterly_labels.append(f"Q{((quarter_start.month-1)//3)+1} {quarter_start.year}")
        quarterly_data.append(float(quarter_revenue))

    # Invoice collection rate
    total_invoiced = Invoice.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    collection_rate = (float(total_revenue) / float(total_invoiced) * 100) if total_invoiced else 0

    # Counts for summary
    total_invoices = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status='paid').count()
    total_projects = Project.objects.count()
    completed_projects = Project.objects.filter(status='completed').count()
    total_clients = Client.objects.filter(is_active=True).count()

    context = {
        'total_revenue': total_revenue,
        'this_month_revenue': this_month_revenue,
        'outstanding': outstanding,
        'collection_rate': collection_rate,
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'total_clients': total_clients,
        # Chart data
        'monthly_revenue_labels': json.dumps(monthly_revenue_labels),
        'monthly_revenue_data': json.dumps(monthly_revenue_data),
        'monthly_invoiced_data': json.dumps(monthly_invoiced_data),
        'client_labels': json.dumps(client_labels),
        'client_data': json.dumps(client_data),
        'project_type_labels': json.dumps(project_type_labels),
        'project_type_data': json.dumps(project_type_data),
        'quarterly_labels': json.dumps(quarterly_labels),
        'quarterly_data': json.dumps(quarterly_data),
    }
    return render(request, 'reports/index.html', context)


# ============== Global Search ==============

@login_required
def global_search(request):
    from django.http import JsonResponse

    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    results = []

    # Search Clients
    clients = Client.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query) |
        Q(company_name__icontains=query)
    ).filter(is_active=True)[:5]

    for client in clients:
        results.append({
            'type': 'client',
            'icon': 'fa-user',
            'title': client.name,
            'subtitle': client.company_name or client.email or '',
            'url': f'/clients/{client.pk}/'
        })

    # Search Projects
    projects = Project.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    ).select_related('client')[:5]

    for project in projects:
        results.append({
            'type': 'project',
            'icon': 'fa-folder-open',
            'title': project.name,
            'subtitle': project.client.name,
            'url': f'/projects/{project.pk}/'
        })

    # Search Invoices
    invoices = Invoice.objects.filter(
        Q(invoice_number__icontains=query) |
        Q(client__name__icontains=query)
    ).select_related('client')[:5]

    for invoice in invoices:
        results.append({
            'type': 'invoice',
            'icon': 'fa-file-invoice-dollar',
            'title': invoice.invoice_number,
            'subtitle': f'{invoice.client.name} - ₹{invoice.total_amount:,.0f}',
            'url': f'/invoices/{invoice.pk}/'
        })

    # Search Quotes
    quotes = Quote.objects.filter(
        Q(quote_number__icontains=query) |
        Q(client__name__icontains=query) |
        Q(title__icontains=query)
    ).select_related('client')[:5]

    for quote in quotes:
        results.append({
            'type': 'quote',
            'icon': 'fa-file-alt',
            'title': quote.quote_number,
            'subtitle': f'{quote.client.name} - {quote.title}',
            'url': f'/quotes/{quote.pk}/'
        })

    # Search Credentials
    credentials = Credential.objects.filter(
        Q(name__icontains=query) |
        Q(credential_type__icontains=query) |
        Q(project__name__icontains=query)
    ).select_related('project')[:5]

    for credential in credentials:
        results.append({
            'type': 'credential',
            'icon': 'fa-key',
            'title': credential.name,
            'subtitle': f'{credential.project.name} - {credential.get_credential_type_display()}',
            'url': f'/credentials/{credential.pk}/'
        })

    return JsonResponse({'results': results[:15]})


# ============== Excel Import ==============

@login_required
def client_import(request):
    """Import clients from Excel file"""
    from django.http import HttpResponse
    import openpyxl
    from io import BytesIO

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        try:
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active

            imported = 0
            skipped = 0
            errors = []

            # Skip header row
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not row[0]:  # Skip empty rows
                    continue

                name = str(row[0]).strip() if row[0] else ''
                email = str(row[1]).strip() if row[1] else ''
                phone = str(row[2]).strip() if row[2] else ''
                company_name = str(row[3]).strip() if len(row) > 3 and row[3] else ''
                address = str(row[4]).strip() if len(row) > 4 and row[4] else ''
                gst_number = str(row[5]).strip() if len(row) > 5 and row[5] else ''

                if not name:
                    errors.append(f'Row {row_num}: Name is required')
                    skipped += 1
                    continue

                # Check for duplicate email
                if email and Client.objects.filter(email=email).exists():
                    errors.append(f'Row {row_num}: Email {email} already exists')
                    skipped += 1
                    continue

                try:
                    Client.objects.create(
                        name=name,
                        email=email,
                        phone=phone,
                        company_name=company_name,
                        address=address,
                        gst_number=gst_number,
                    )
                    imported += 1
                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
                    skipped += 1

            if imported > 0:
                messages.success(request, f'Successfully imported {imported} client(s).')
            if skipped > 0:
                messages.warning(request, f'Skipped {skipped} row(s). Check errors below.')
            if errors:
                for error in errors[:5]:  # Show first 5 errors
                    messages.error(request, error)

        except Exception as e:
            messages.error(request, f'Error reading Excel file: {str(e)}')

        return redirect('client_list')

    # GET request - show import form or download template
    if request.GET.get('template') == '1':
        # Generate sample template
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Clients'

        # Header row
        headers = ['Name*', 'Email', 'Phone', 'Company Name', 'Address', 'GST Number']
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)

        # Sample row
        sample = ['John Doe', 'john@example.com', '+91 9876543210', 'ABC Corp', '123 Main St, City', 'GSTIN123456']
        for col, value in enumerate(sample, 1):
            ws.cell(row=2, column=col, value=value)

        # Save to response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=clients_template.xlsx'

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response.write(buffer.read())

        return response

    return render(request, 'clients/import.html')


@login_required
def project_import(request):
    """Import projects from Excel file"""
    from django.http import HttpResponse
    import openpyxl
    from io import BytesIO

    clients = Client.objects.filter(is_active=True)

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        try:
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active

            imported = 0
            skipped = 0
            errors = []

            # Skip header row
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not row[0]:  # Skip empty rows
                    continue

                name = str(row[0]).strip() if row[0] else ''
                client_name = str(row[1]).strip() if row[1] else ''
                project_type = str(row[2]).strip().lower() if len(row) > 2 and row[2] else 'other'
                status = str(row[3]).strip().lower() if len(row) > 3 and row[3] else 'planning'
                description = str(row[4]).strip() if len(row) > 4 and row[4] else ''

                if not name:
                    errors.append(f'Row {row_num}: Project name is required')
                    skipped += 1
                    continue

                if not client_name:
                    errors.append(f'Row {row_num}: Client name is required')
                    skipped += 1
                    continue

                # Find client
                client = Client.objects.filter(
                    Q(name__iexact=client_name) | Q(email__iexact=client_name)
                ).first()

                if not client:
                    errors.append(f'Row {row_num}: Client "{client_name}" not found')
                    skipped += 1
                    continue

                # Validate project_type
                valid_types = ['website', 'mobile_app', 'webapp', 'ecommerce', 'maintenance', 'other']
                if project_type not in valid_types:
                    project_type = 'other'

                # Validate status
                valid_statuses = ['planning', 'in_progress', 'on_hold', 'completed', 'cancelled']
                if status not in valid_statuses:
                    status = 'planning'

                try:
                    Project.objects.create(
                        name=name,
                        client=client,
                        project_type=project_type,
                        status=status,
                        description=description,
                    )
                    imported += 1
                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
                    skipped += 1

            if imported > 0:
                messages.success(request, f'Successfully imported {imported} project(s).')
            if skipped > 0:
                messages.warning(request, f'Skipped {skipped} row(s). Check errors below.')
            if errors:
                for error in errors[:5]:
                    messages.error(request, error)

        except Exception as e:
            messages.error(request, f'Error reading Excel file: {str(e)}')

        return redirect('project_list')

    # GET request - show import form or download template
    if request.GET.get('template') == '1':
        # Generate sample template
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Projects'

        # Header row
        headers = ['Project Name*', 'Client Name/Email*', 'Type', 'Status', 'Description']
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)

        # Sample row
        sample = ['Website Redesign', 'john@example.com', 'website', 'planning', 'Complete website redesign']
        for col, value in enumerate(sample, 1):
            ws.cell(row=2, column=col, value=value)

        # Add notes
        ws.cell(row=4, column=1, value='Notes:')
        ws.cell(row=5, column=1, value='Type: website, mobile_app, webapp, ecommerce, maintenance, other')
        ws.cell(row=6, column=1, value='Status: planning, in_progress, on_hold, completed, cancelled')

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=projects_template.xlsx'

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response.write(buffer.read())

        return response

    return render(request, 'projects/import.html', {'clients': clients})


# ============== User Profile ==============

@login_required
def profile_view(request):
    """View and edit user profile"""
    user = request.user

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    return render(request, 'profile/index.html', {'profile_user': user})


@login_required
def change_password(request):
    """Change user password"""
    from django.contrib.auth import update_session_auth_hash

    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('profile')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('profile')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('profile')

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Password changed successfully.')
        return redirect('profile')

    return redirect('profile')


# ============== Export to Excel ==============

@login_required
def export_clients(request):
    """Export clients to Excel"""
    from openpyxl import Workbook
    from django.http import HttpResponse

    wb = Workbook()
    ws = wb.active
    ws.title = "Clients"

    # Header
    headers = ['Company Name', 'Contact Name', 'Email', 'Phone', 'GST Number', 'Address', 'Created Date']
    ws.append(headers)

    # Data
    for client in Client.objects.all().order_by('company_name'):
        ws.append([
            client.company_name or '',
            client.name,
            client.email,
            client.phone or '',
            client.gst_number or '',
            client.address or '',
            client.created_at.strftime('%Y-%m-%d') if client.created_at else ''
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="clients_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response


@login_required
def export_projects(request):
    """Export projects to Excel"""
    from openpyxl import Workbook
    from django.http import HttpResponse

    wb = Workbook()
    ws = wb.active
    ws.title = "Projects"

    # Header
    headers = ['Project Name', 'Client', 'Status', 'Start Date', 'End Date', 'Budget', 'Description']
    ws.append(headers)

    # Data
    for project in Project.objects.select_related('client').all().order_by('-created_at'):
        ws.append([
            project.name,
            project.client.name if project.client else '',
            project.get_status_display(),
            project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
            project.end_date.strftime('%Y-%m-%d') if project.end_date else '',
            float(project.budget) if project.budget else 0,
            project.description or ''
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="projects_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response


@login_required
def export_invoices(request):
    """Export invoices to Excel"""
    from openpyxl import Workbook
    from django.http import HttpResponse

    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices"

    # Header
    headers = ['Invoice Number', 'Client', 'Project', 'Title', 'Issue Date', 'Due Date', 'Subtotal', 'Tax', 'Total', 'Paid', 'Balance', 'Status']
    ws.append(headers)

    # Data
    for invoice in Invoice.objects.select_related('client', 'project').all().order_by('-issue_date'):
        ws.append([
            invoice.invoice_number,
            invoice.client.name if invoice.client else '',
            invoice.project.name if invoice.project else '',
            invoice.title or '',
            invoice.issue_date.strftime('%Y-%m-%d') if invoice.issue_date else '',
            invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
            float(invoice.subtotal) if invoice.subtotal else 0,
            float(invoice.tax_amount) if invoice.tax_amount else 0,
            float(invoice.total_amount) if invoice.total_amount else 0,
            float(invoice.amount_paid) if invoice.amount_paid else 0,
            float(invoice.balance_due) if invoice.balance_due else 0,
            invoice.get_status_display()
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="invoices_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response


@login_required
def export_quotes(request):
    """Export quotes to Excel"""
    from openpyxl import Workbook
    from django.http import HttpResponse

    wb = Workbook()
    ws = wb.active
    ws.title = "Quotes"

    # Header
    headers = ['Quote Number', 'Client', 'Project', 'Title', 'Issue Date', 'Valid Until', 'Subtotal', 'Tax', 'Total', 'Status']
    ws.append(headers)

    # Data
    for quote in Quote.objects.select_related('client', 'project').all().order_by('-issue_date'):
        ws.append([
            quote.quote_number,
            quote.client.name if quote.client else '',
            quote.project.name if quote.project else '',
            quote.title or '',
            quote.issue_date.strftime('%Y-%m-%d') if quote.issue_date else '',
            quote.valid_until.strftime('%Y-%m-%d') if quote.valid_until else '',
            float(quote.subtotal) if quote.subtotal else 0,
            float(quote.tax_amount) if quote.tax_amount else 0,
            float(quote.total_amount) if quote.total_amount else 0,
            quote.get_status_display()
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="quotes_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response


# ============== Backup & Restore ==============

@login_required
def backup_view(request):
    """Backup management page"""
    import os

    # List existing backups
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backups = []

    if os.path.exists(backup_dir):
        for filename in sorted(os.listdir(backup_dir), reverse=True):
            if filename.endswith('.json'):
                filepath = os.path.join(backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created': timezone.datetime.fromtimestamp(stat.st_mtime)
                })

    return render(request, 'backup/index.html', {'backups': backups[:10]})


@login_required
def backup_download(request):
    """Create and download database backup"""
    import json
    import os
    from django.http import HttpResponse
    from django.core import serializers

    # Create backup data
    backup_data = {
        'created_at': timezone.now().isoformat(),
        'version': '1.0',
        'data': {}
    }

    # Export all models
    models_to_backup = [
        ('clients', Client),
        ('projects', Project),
        ('credentials', Credential),
        ('quotes', Quote),
        ('quote_items', QuoteItem),
        ('invoices', Invoice),
        ('invoice_items', InvoiceItem),
        ('payments', Payment),
        ('company_settings', CompanySettings),
    ]

    for name, model in models_to_backup:
        backup_data['data'][name] = json.loads(serializers.serialize('json', model.objects.all()))

    # Create backup file
    backup_json = json.dumps(backup_data, indent=2, default=str)

    # Save to backups folder
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    filename = f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(backup_dir, filename)

    with open(filepath, 'w') as f:
        f.write(backup_json)

    # Return as download
    response = HttpResponse(backup_json, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    messages.success(request, f'Backup created: {filename}')
    return response


@login_required
def backup_restore(request):
    """Restore database from backup"""
    import json
    from django.core import serializers
    from django.db import transaction

    if request.method != 'POST':
        return redirect('backup')

    backup_file = request.FILES.get('backup_file')
    if not backup_file:
        messages.error(request, 'Please select a backup file.')
        return redirect('backup')

    try:
        backup_data = json.load(backup_file)

        if 'data' not in backup_data:
            messages.error(request, 'Invalid backup file format.')
            return redirect('backup')

        with transaction.atomic():
            # Restore in order (respecting foreign keys)
            restore_order = [
                ('clients', Client),
                ('projects', Project),
                ('credentials', Credential),
                ('quotes', Quote),
                ('quote_items', QuoteItem),
                ('invoices', Invoice),
                ('invoice_items', InvoiceItem),
                ('payments', Payment),
                ('company_settings', CompanySettings),
            ]

            for name, model in restore_order:
                if name in backup_data['data']:
                    # Clear existing data
                    model.objects.all().delete()

                    # Restore from backup
                    for obj_data in backup_data['data'][name]:
                        for obj in serializers.deserialize('json', json.dumps([obj_data])):
                            obj.save()

        messages.success(request, 'Backup restored successfully.')
    except json.JSONDecodeError:
        messages.error(request, 'Invalid JSON file.')
    except Exception as e:
        messages.error(request, f'Restore failed: {str(e)}')

    return redirect('backup')


# ============== Expense Views ==============

@login_required
def expense_list(request):
    """List all expenses with filtering"""
    expenses = Expense.objects.select_related('project', 'project__client').all()

    # Filters
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    project_id = request.GET.get('project', '')

    if search:
        expenses = expenses.filter(
            Q(vendor__icontains=search) | Q(description__icontains=search)
        )
    if category:
        expenses = expenses.filter(category=category)
    if project_id:
        expenses = expenses.filter(project_id=project_id)

    # Calculate totals
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    billable_total = expenses.filter(is_billable=True).aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'expenses': expenses,
        'projects': Project.objects.filter(status__in=['in_progress', 'confirmed']),
        'category_choices': Expense.CATEGORY_CHOICES,
        'search': search,
        'selected_category': category,
        'selected_project': project_id,
        'total_expenses': total_expenses,
        'billable_total': billable_total,
    }
    return render(request, 'expenses/list.html', context)


@login_required
def expense_create(request):
    """Create a new expense"""
    if request.method == 'POST':
        expense = Expense(
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            date=request.POST.get('date') or timezone.now().date(),
            vendor=request.POST.get('vendor'),
            description=request.POST.get('description', ''),
            is_billable=request.POST.get('is_billable') == 'on',
            payment_method=request.POST.get('payment_method', 'bank_transfer'),
            notes=request.POST.get('notes', ''),
        )

        project_id = request.POST.get('project')
        if project_id:
            expense.project = Project.objects.get(pk=project_id)

        if request.FILES.get('receipt'):
            expense.receipt = request.FILES['receipt']

        expense.save()

        # Log activity
        log_activity(request, 'created', expense)

        messages.success(request, 'Expense created successfully.')
        return redirect('expense_list')

    context = {
        'projects': Project.objects.filter(status__in=['in_progress', 'confirmed']),
        'category_choices': Expense.CATEGORY_CHOICES,
        'payment_method_choices': Expense.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'expenses/form.html', context)


@login_required
def expense_update(request, pk):
    """Update an expense"""
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == 'POST':
        expense.category = request.POST.get('category')
        expense.amount = request.POST.get('amount')
        expense.date = request.POST.get('date')
        expense.vendor = request.POST.get('vendor')
        expense.description = request.POST.get('description', '')
        expense.is_billable = request.POST.get('is_billable') == 'on'
        expense.payment_method = request.POST.get('payment_method', 'bank_transfer')
        expense.notes = request.POST.get('notes', '')

        project_id = request.POST.get('project')
        expense.project = Project.objects.get(pk=project_id) if project_id else None

        if request.FILES.get('receipt'):
            expense.receipt = request.FILES['receipt']

        expense.save()

        log_activity(request, 'updated', expense)

        messages.success(request, 'Expense updated successfully.')
        return redirect('expense_list')

    context = {
        'expense': expense,
        'projects': Project.objects.filter(status__in=['in_progress', 'confirmed']),
        'category_choices': Expense.CATEGORY_CHOICES,
        'payment_method_choices': Expense.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'expenses/form.html', context)


@login_required
def expense_delete(request, pk):
    """Delete an expense"""
    expense = get_object_or_404(Expense, pk=pk)

    if request.method == 'POST':
        log_activity(request, 'deleted', expense)
        expense.delete()
        messages.success(request, 'Expense deleted successfully.')
        return redirect('expense_list')

    return render(request, 'expenses/delete.html', {'expense': expense})


# ============== Team Member Views ==============

@login_required
def team_dashboard(request):
    """Dashboard for team members showing their tasks and time entries"""
    # Get the team member profile for the current user
    team_member = getattr(request.user, 'team_profile', None)

    if not team_member:
        # If user is not a team member (admin), redirect to main dashboard
        return redirect('dashboard')

    from datetime import date, timedelta
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Get tasks assigned to this team member
    my_tasks = Task.objects.filter(assigned_to=team_member).select_related('project')
    tasks_todo = my_tasks.filter(status='todo').count()
    tasks_in_progress = my_tasks.filter(status='in_progress').count()
    tasks_review = my_tasks.filter(status='review').count()
    tasks_completed = my_tasks.filter(status='completed').count()

    # Recent tasks
    recent_tasks = my_tasks.exclude(status='completed').order_by('-updated_at')[:5]

    # Get time entries for this team member
    my_time_entries = TimeEntry.objects.filter(user=request.user)

    # Time logged this week
    week_entries = my_time_entries.filter(date__gte=week_start)
    hours_this_week = week_entries.aggregate(total=Sum('hours'))['total'] or 0

    # Time logged this month
    month_entries = my_time_entries.filter(date__gte=month_start)
    hours_this_month = month_entries.aggregate(total=Sum('hours'))['total'] or 0

    # Recent time entries
    recent_time_entries = my_time_entries.select_related('project', 'task').order_by('-date')[:5]

    # Projects assigned to me
    my_projects = team_member.assigned_projects.all()

    context = {
        'team_member': team_member,
        'tasks_todo': tasks_todo,
        'tasks_in_progress': tasks_in_progress,
        'tasks_review': tasks_review,
        'tasks_completed': tasks_completed,
        'recent_tasks': recent_tasks,
        'hours_this_week': hours_this_week,
        'hours_this_month': hours_this_month,
        'recent_time_entries': recent_time_entries,
        'my_projects': my_projects,
        'today': today,
    }
    return render(request, 'team/dashboard.html', context)


@login_required
def my_tasks(request):
    """View tasks assigned to the current team member"""
    team_member = getattr(request.user, 'team_profile', None)

    if not team_member:
        return redirect('task_list')

    tasks = Task.objects.filter(assigned_to=team_member).select_related('project')

    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')

    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)

    context = {
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'selected_status': status,
        'selected_priority': priority,
        'is_my_tasks': True,
    }
    return render(request, 'team/my_tasks.html', context)


@login_required
def my_time(request):
    """View time entries for the current user"""
    team_member = getattr(request.user, 'team_profile', None)

    if not team_member:
        return redirect('timeentry_list')

    entries = TimeEntry.objects.filter(user=request.user).select_related('project', 'task')

    from datetime import date, timedelta
    today = date.today()

    # Filter by date range
    date_filter = request.GET.get('date_filter', 'week')
    if date_filter == 'today':
        entries = entries.filter(date=today)
    elif date_filter == 'week':
        week_start = today - timedelta(days=today.weekday())
        entries = entries.filter(date__gte=week_start)
    elif date_filter == 'month':
        month_start = today.replace(day=1)
        entries = entries.filter(date__gte=month_start)

    total_hours = entries.aggregate(total=Sum('hours'))['total'] or 0

    context = {
        'entries': entries,
        'total_hours': total_hours,
        'date_filter': date_filter,
        'is_my_time': True,
    }
    return render(request, 'team/my_time.html', context)


@login_required
def team_list(request):
    """List all team members"""
    members = TeamMember.objects.all()

    search = request.GET.get('search', '')
    role = request.GET.get('role', '')

    if search:
        members = members.filter(Q(name__icontains=search) | Q(email__icontains=search))
    if role:
        members = members.filter(role=role)

    context = {
        'members': members,
        'role_choices': TeamMember.ROLE_CHOICES,
        'search': search,
        'selected_role': role,
    }
    return render(request, 'team/list.html', context)


@login_required
def team_detail(request, pk):
    """View team member details including assigned projects"""
    member = get_object_or_404(TeamMember, pk=pk)

    # Get assigned projects
    assigned_projects = member.assigned_projects.all()

    # Get tasks assigned to this member
    tasks = Task.objects.filter(assigned_to=member).select_related('project')
    tasks_todo = tasks.filter(status='todo').count()
    tasks_in_progress = tasks.filter(status='in_progress').count()
    tasks_review = tasks.filter(status='review').count()
    tasks_completed = tasks.filter(status='completed').count()
    recent_tasks = tasks.exclude(status='completed').order_by('-updated_at')[:5]

    # Get time entries if freelancer
    time_entries = []
    total_hours = 0
    if member.is_freelancer and member.user:
        time_entries = TimeEntry.objects.filter(user=member.user).select_related('project', 'task').order_by('-date')[:10]
        total_hours = TimeEntry.objects.filter(user=member.user).aggregate(total=Sum('hours'))['total'] or 0

    context = {
        'member': member,
        'assigned_projects': assigned_projects,
        'tasks_todo': tasks_todo,
        'tasks_in_progress': tasks_in_progress,
        'tasks_review': tasks_review,
        'tasks_completed': tasks_completed,
        'recent_tasks': recent_tasks,
        'time_entries': time_entries,
        'total_hours': total_hours,
    }
    return render(request, 'team/detail.html', context)


@login_required
def team_create(request):
    """Create a new team member with optional login account"""
    if request.method == 'POST':
        employment_type = request.POST.get('employment_type', 'permanent')

        member = TeamMember(
            name=request.POST.get('name'),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            role=request.POST.get('role', 'developer'),
            employment_type=employment_type,
            is_active=request.POST.get('is_active') == 'true',
            notes=request.POST.get('notes', ''),
        )

        # Set salary or hourly rate based on employment type
        if employment_type == 'freelancer':
            hourly_rate = request.POST.get('hourly_rate')
            if hourly_rate:
                member.hourly_rate = hourly_rate
        else:
            monthly_salary = request.POST.get('monthly_salary')
            if monthly_salary:
                member.monthly_salary = monthly_salary

        # Create user account if requested
        create_account = request.POST.get('create_account') == 'on'
        if create_account:
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')

            if username and password:
                # Check if username exists
                if User.objects.filter(username=username).exists():
                    messages.error(request, f'Username "{username}" already exists.')
                    context = {
                        'role_choices': TeamMember.ROLE_CHOICES,
                        'employment_type_choices': TeamMember.EMPLOYMENT_TYPE_CHOICES,
                        'form_data': request.POST,
                    }
                    return render(request, 'team/form.html', context)

                # Create user
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=member.email,
                    first_name=member.name.split()[0] if member.name else '',
                    last_name=' '.join(member.name.split()[1:]) if member.name and len(member.name.split()) > 1 else '',
                )
                member.user = user

        member.save()
        log_activity(request, 'created', member)

        if member.user:
            messages.success(request, f'Team member "{member.name}" added with login account.')
        else:
            messages.success(request, 'Team member added successfully.')
        return redirect('team_list')

    context = {
        'role_choices': TeamMember.ROLE_CHOICES,
        'employment_type_choices': TeamMember.EMPLOYMENT_TYPE_CHOICES,
    }
    return render(request, 'team/form.html', context)


@login_required
def team_update(request, pk):
    """Update a team member"""
    member = get_object_or_404(TeamMember, pk=pk)

    if request.method == 'POST':
        employment_type = request.POST.get('employment_type', 'permanent')

        member.name = request.POST.get('name')
        member.email = request.POST.get('email', '')
        member.phone = request.POST.get('phone', '')
        member.role = request.POST.get('role', 'developer')
        member.employment_type = employment_type
        member.is_active = request.POST.get('is_active') == 'true'
        member.notes = request.POST.get('notes', '')

        # Set salary or hourly rate based on employment type
        if employment_type == 'freelancer':
            hourly_rate = request.POST.get('hourly_rate')
            member.hourly_rate = hourly_rate if hourly_rate else None
            member.monthly_salary = None
        else:
            monthly_salary = request.POST.get('monthly_salary')
            member.monthly_salary = monthly_salary if monthly_salary else None
            member.hourly_rate = None

        member.save()
        log_activity(request, 'updated', member)
        messages.success(request, 'Team member updated successfully.')
        return redirect('team_list')

    context = {
        'member': member,
        'role_choices': TeamMember.ROLE_CHOICES,
        'employment_type_choices': TeamMember.EMPLOYMENT_TYPE_CHOICES,
    }
    return render(request, 'team/form.html', context)


@login_required
def team_delete(request, pk):
    """Delete a team member"""
    member = get_object_or_404(TeamMember, pk=pk)

    if request.method == 'POST':
        # Check if member has tasks assigned
        if member.tasks.exists():
            messages.error(request, 'Cannot delete team member with assigned tasks. Reassign or delete tasks first.')
            return redirect('team_list')

        log_activity(request, 'deleted', member)
        member.delete()
        messages.success(request, 'Team member deleted successfully.')
        return redirect('team_list')

    return render(request, 'team/delete.html', {'member': member})


# ============== Task Views ==============

@login_required
def task_list(request):
    """List all tasks (filtered for team members)"""
    tasks = Task.objects.select_related('project', 'project__client', 'assigned_to').all()

    # Team members only see their assigned tasks
    team_member = getattr(request.user, 'team_profile', None)
    if team_member:
        tasks = tasks.filter(assigned_to=team_member)

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    project_id = request.GET.get('project', '')
    priority = request.GET.get('priority', '')

    if search:
        tasks = tasks.filter(Q(title__icontains=search) | Q(description__icontains=search))
    if status:
        tasks = tasks.filter(status=status)
    if project_id:
        tasks = tasks.filter(project_id=project_id)
    if priority:
        tasks = tasks.filter(priority=priority)

    # Filter projects for team members
    if team_member:
        projects = Project.objects.filter(tasks__assigned_to=team_member).distinct()
    else:
        projects = Project.objects.filter(status__in=['in_progress', 'confirmed'])

    context = {
        'tasks': tasks,
        'projects': projects,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'search': search,
        'selected_status': status,
        'selected_project': project_id,
        'selected_priority': priority,
        'is_team_member': team_member is not None,
    }
    return render(request, 'tasks/list.html', context)


@login_required
def task_board(request):
    """Kanban board view (filtered for team members)"""
    project_id = request.GET.get('project', '')

    tasks = Task.objects.select_related('project', 'assigned_to').all()

    # Team members only see their assigned tasks
    team_member = getattr(request.user, 'team_profile', None)
    if team_member:
        tasks = tasks.filter(assigned_to=team_member)

    if project_id:
        tasks = tasks.filter(project_id=project_id)

    # Filter projects for team members
    if team_member:
        projects = Project.objects.filter(tasks__assigned_to=team_member).distinct()
    else:
        projects = Project.objects.filter(status__in=['in_progress', 'confirmed'])

    context = {
        'todo_tasks': tasks.filter(status='todo'),
        'in_progress_tasks': tasks.filter(status='in_progress'),
        'review_tasks': tasks.filter(status='review'),
        'completed_tasks': tasks.filter(status='completed'),
        'projects': projects,
        'selected_project': project_id,
        'is_team_member': team_member is not None,
    }
    return render(request, 'tasks/board.html', context)


@login_required
def task_detail(request, pk):
    """Task detail view"""
    task = get_object_or_404(Task.objects.select_related('project', 'assigned_to'), pk=pk)
    time_entries = task.time_entries.all()

    context = {
        'task': task,
        'time_entries': time_entries,
        'total_hours': time_entries.aggregate(total=Sum('hours'))['total'] or 0,
    }
    return render(request, 'tasks/detail.html', context)


@login_required
def task_create(request):
    """Create a new task"""
    if request.method == 'POST':
        task = Task(
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            status=request.POST.get('status', 'todo'),
            priority=request.POST.get('priority', 'medium'),
            notes=request.POST.get('notes', ''),
        )

        project_id = request.POST.get('project')
        if project_id:
            task.project = Project.objects.get(pk=project_id)

        assigned_to = request.POST.get('assigned_to')
        if assigned_to:
            task.assigned_to = TeamMember.objects.get(pk=assigned_to)

        due_date = request.POST.get('due_date')
        if due_date:
            task.due_date = due_date

        task.save()

        log_activity(request, 'created', task)

        messages.success(request, 'Task created successfully.')

        if request.GET.get('next') == 'board':
            return redirect('task_board')
        return redirect('task_list')

    context = {
        'projects': Project.objects.filter(status__in=['in_progress', 'confirmed']),
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'team_members': TeamMember.objects.filter(is_active=True),
    }
    return render(request, 'tasks/form.html', context)


@login_required
def task_update(request, pk):
    """Update a task"""
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.description = request.POST.get('description', '')
        task.status = request.POST.get('status', 'todo')
        task.priority = request.POST.get('priority', 'medium')
        task.notes = request.POST.get('notes', '')

        project_id = request.POST.get('project')
        task.project = Project.objects.get(pk=project_id) if project_id else None

        assigned_to = request.POST.get('assigned_to')
        task.assigned_to = TeamMember.objects.get(pk=assigned_to) if assigned_to else None

        due_date = request.POST.get('due_date')
        task.due_date = due_date if due_date else None

        # Set completed date if status changed to completed
        if task.status == 'completed' and not task.completed_date:
            task.completed_date = timezone.now().date()
        elif task.status != 'completed':
            task.completed_date = None

        task.save()

        log_activity(request, 'updated', task)

        messages.success(request, 'Task updated successfully.')
        return redirect('task_detail', pk=pk)

    context = {
        'task': task,
        'projects': Project.objects.filter(status__in=['in_progress', 'confirmed']),
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'team_members': TeamMember.objects.filter(is_active=True),
    }
    return render(request, 'tasks/form.html', context)


@login_required
def task_delete(request, pk):
    """Delete a task"""
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        log_activity(request, 'deleted', task)
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('task_list')

    return render(request, 'tasks/delete.html', {'task': task})


@login_required
def task_status_update(request, pk):
    """Update task status via AJAX or form submission"""
    from django.http import JsonResponse

    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk)
        new_status = request.POST.get('status')

        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            if new_status == 'completed':
                task.completed_date = timezone.now().date()
            else:
                task.completed_date = None
            task.save()

            log_activity(request, 'updated', task)

            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            # Regular form submission - redirect back
            messages.success(request, f'Task status updated to "{task.get_status_display()}".')
            return redirect('task_detail', pk=task.pk)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False})

    return redirect('task_detail', pk=pk)


# ============== Time Entry Views ==============

@login_required
def timeentry_list(request):
    """List all time entries (filtered for team members)"""
    entries = TimeEntry.objects.select_related('project', 'task', 'user').all()

    # Team members only see their own time entries
    team_member = getattr(request.user, 'team_profile', None)
    if team_member:
        entries = entries.filter(user=request.user)

    search = request.GET.get('search', '')
    project_id = request.GET.get('project', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if search:
        entries = entries.filter(description__icontains=search)
    if project_id:
        entries = entries.filter(project_id=project_id)
    if date_from:
        entries = entries.filter(date__gte=date_from)
    if date_to:
        entries = entries.filter(date__lte=date_to)

    total_hours = entries.aggregate(total=Sum('hours'))['total'] or 0
    billable_hours = entries.filter(is_billable=True).aggregate(total=Sum('hours'))['total'] or 0

    # Filter projects for team members
    if team_member:
        projects = Project.objects.filter(tasks__assigned_to=team_member).distinct()
    else:
        projects = Project.objects.filter(status__in=['in_progress', 'confirmed'])

    context = {
        'entries': entries,
        'projects': projects,
        'search': search,
        'selected_project': project_id,
        'date_from': date_from,
        'date_to': date_to,
        'total_hours': total_hours,
        'billable_hours': billable_hours,
        'is_team_member': team_member is not None,
    }
    return render(request, 'time/list.html', context)


@login_required
def timeentry_create(request):
    """Create a time entry"""
    if request.method == 'POST':
        entry = TimeEntry(
            description=request.POST.get('description'),
            hours=request.POST.get('hours'),
            date=request.POST.get('date') or timezone.now().date(),
            is_billable=request.POST.get('is_billable') == 'on',
            notes=request.POST.get('notes', ''),
            user=request.user,
        )

        project_id = request.POST.get('project')
        if project_id:
            entry.project = Project.objects.get(pk=project_id)

        task_id = request.POST.get('task')
        if task_id:
            entry.task = Task.objects.get(pk=task_id)

        hourly_rate = request.POST.get('hourly_rate')
        if hourly_rate:
            entry.hourly_rate = hourly_rate

        entry.save()

        log_activity(request, 'created', entry)

        messages.success(request, 'Time entry created successfully.')
        return redirect('timeentry_list')

    # For team members, only show their assigned projects
    team_member = getattr(request.user, 'team_profile', None)
    if team_member:
        projects = team_member.assigned_projects.filter(status__in=['in_progress', 'confirmed'])
        tasks = Task.objects.filter(assigned_to=team_member).exclude(status='completed')
    else:
        projects = Project.objects.filter(status__in=['in_progress', 'confirmed'])
        tasks = Task.objects.exclude(status='completed')

    context = {
        'projects': projects,
        'tasks': tasks,
    }
    return render(request, 'time/form.html', context)


@login_required
def timeentry_update(request, pk):
    """Update a time entry"""
    entry = get_object_or_404(TimeEntry, pk=pk)

    if request.method == 'POST':
        entry.description = request.POST.get('description')
        entry.hours = request.POST.get('hours')
        entry.date = request.POST.get('date')
        entry.is_billable = request.POST.get('is_billable') == 'on'
        entry.notes = request.POST.get('notes', '')

        project_id = request.POST.get('project')
        entry.project = Project.objects.get(pk=project_id) if project_id else None

        task_id = request.POST.get('task')
        entry.task = Task.objects.get(pk=task_id) if task_id else None

        hourly_rate = request.POST.get('hourly_rate')
        entry.hourly_rate = hourly_rate if hourly_rate else None

        entry.save()

        log_activity(request, 'updated', entry)

        messages.success(request, 'Time entry updated successfully.')
        return redirect('timeentry_list')

    context = {
        'entry': entry,
        'projects': Project.objects.filter(status__in=['in_progress', 'confirmed']),
        'tasks': Task.objects.exclude(status='completed'),
    }
    return render(request, 'time/form.html', context)


@login_required
def timeentry_delete(request, pk):
    """Delete a time entry"""
    entry = get_object_or_404(TimeEntry, pk=pk)

    if request.method == 'POST':
        log_activity(request, 'deleted', entry)
        entry.delete()
        messages.success(request, 'Time entry deleted successfully.')
        return redirect('timeentry_list')

    return render(request, 'time/delete.html', {'entry': entry})


# ============== Activity Log Views ==============

@login_required
def activity_log(request):
    """View activity log"""
    logs = ActivityLog.objects.select_related('user').all()

    action = request.GET.get('action', '')
    model = request.GET.get('model', '')

    if action:
        logs = logs.filter(action=action)
    if model:
        logs = logs.filter(model_name=model)

    # Get unique model names for filter
    model_names = ActivityLog.objects.values_list('model_name', flat=True).distinct()

    context = {
        'logs': logs[:100],  # Limit to 100 most recent
        'action_choices': ActivityLog.ACTION_CHOICES,
        'model_names': model_names,
        'selected_action': action,
        'selected_model': model,
    }
    return render(request, 'activity/list.html', context)


# ============== Document Views ==============

@login_required
def document_upload(request):
    """Upload a document attachment"""
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Please select a file.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        model_type = request.POST.get('model_type')
        object_id = request.POST.get('object_id')

        # Get content type
        model_map = {
            'client': Client,
            'project': Project,
            'invoice': Invoice,
            'quote': Quote,
        }

        if model_type not in model_map:
            messages.error(request, 'Invalid model type.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        model_class = model_map[model_type]
        content_type = ContentType.objects.get_for_model(model_class)

        document = Document(
            file=file,
            name=request.POST.get('name') or file.name,
            description=request.POST.get('description', ''),
            uploaded_by=request.user,
            content_type=content_type,
            object_id=object_id,
        )
        document.save()

        log_activity(request, 'created', document)

        messages.success(request, 'Document uploaded successfully.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('/')


@login_required
def document_download(request, pk):
    """Download a document"""
    from django.http import FileResponse

    document = get_object_or_404(Document, pk=pk)

    try:
        response = FileResponse(document.file.open('rb'), as_attachment=True, filename=document.name)
        return response
    except FileNotFoundError:
        messages.error(request, 'File not found.')
        return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def document_delete(request, pk):
    """Delete a document"""
    document = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        log_activity(request, 'deleted', document)
        document.file.delete()
        document.delete()
        messages.success(request, 'Document deleted successfully.')

    return redirect(request.META.get('HTTP_REFERER', '/'))


# ============== Email Views ==============

@login_required
def send_invoice_email(request, pk):
    """Send invoice via email"""
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string

    invoice = get_object_or_404(Invoice.objects.select_related('client'), pk=pk)
    company = CompanySettings.get_settings()

    if request.method == 'POST':
        to_email = request.POST.get('to_email', invoice.client.email)
        subject = request.POST.get('subject', f'Invoice {invoice.invoice_number} from {company.company_name}')
        message = request.POST.get('message', '')

        # Check if email settings are configured
        if not company.smtp_host or not company.smtp_user:
            messages.error(request, 'Email settings not configured. Please configure SMTP settings first.')
            return redirect('invoice_detail', pk=pk)

        try:
            # Configure email backend dynamically
            from django.core.mail import get_connection

            connection = get_connection(
                host=company.smtp_host,
                port=company.smtp_port,
                username=company.smtp_user,
                password=company.smtp_password,
                use_tls=company.smtp_use_tls,
            )

            # Generate PDF
            html_content = render_to_string('invoices/pdf.html', {
                'invoice': invoice,
                'company': company,
                'include_gst': True,
            })

            email = EmailMessage(
                subject=subject,
                body=message or f'Please find attached invoice {invoice.invoice_number}.',
                from_email=company.from_email or company.smtp_user,
                to=[to_email],
                connection=connection,
            )

            # Try to attach PDF if WeasyPrint is available
            try:
                from weasyprint import HTML
                pdf = HTML(string=html_content).write_pdf()
                email.attach(f'{invoice.invoice_number}.pdf', pdf, 'application/pdf')
            except ImportError:
                pass  # Send without attachment

            email.send()

            # Update invoice status
            if invoice.status == 'draft':
                invoice.status = 'sent'
                invoice.save()

            log_activity(request, 'sent', invoice)

            messages.success(request, f'Invoice sent to {to_email}')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')

        return redirect('invoice_detail', pk=pk)

    context = {
        'invoice': invoice,
        'company': company,
        'default_subject': f'Invoice {invoice.invoice_number} from {company.company_name}',
        'default_message': f'Dear {invoice.client.name},\n\nPlease find attached invoice {invoice.invoice_number} for {invoice.title}.\n\nAmount Due: ₹{invoice.balance_due}\nDue Date: {invoice.due_date.strftime("%d %b %Y") if invoice.due_date else "N/A"}\n\nThank you for your business.\n\nBest regards,\n{company.company_name}',
    }
    return render(request, 'emails/send_invoice.html', context)


@login_required
def send_quote_email(request, pk):
    """Send quote via email"""
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string

    quote = get_object_or_404(Quote.objects.select_related('client'), pk=pk)
    company = CompanySettings.get_settings()

    if request.method == 'POST':
        to_email = request.POST.get('to_email', quote.client.email)
        subject = request.POST.get('subject', f'Quote {quote.quote_number} from {company.company_name}')
        message = request.POST.get('message', '')

        if not company.smtp_host or not company.smtp_user:
            messages.error(request, 'Email settings not configured. Please configure SMTP settings first.')
            return redirect('quote_detail', pk=pk)

        try:
            from django.core.mail import get_connection

            connection = get_connection(
                host=company.smtp_host,
                port=company.smtp_port,
                username=company.smtp_user,
                password=company.smtp_password,
                use_tls=company.smtp_use_tls,
            )

            html_content = render_to_string('quotes/pdf.html', {
                'quote': quote,
                'company': company,
                'include_gst': True,
            })

            email = EmailMessage(
                subject=subject,
                body=message or f'Please find attached quote {quote.quote_number}.',
                from_email=company.from_email or company.smtp_user,
                to=[to_email],
                connection=connection,
            )

            try:
                from weasyprint import HTML
                pdf = HTML(string=html_content).write_pdf()
                email.attach(f'{quote.quote_number}.pdf', pdf, 'application/pdf')
            except ImportError:
                pass

            email.send()

            if quote.status == 'draft':
                quote.status = 'sent'
                quote.save()

            log_activity(request, 'sent', quote)

            messages.success(request, f'Quote sent to {to_email}')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')

        return redirect('quote_detail', pk=pk)

    context = {
        'quote': quote,
        'company': company,
        'default_subject': f'Quote {quote.quote_number} from {company.company_name}',
        'default_message': f'Dear {quote.client.name},\n\nPlease find attached quote {quote.quote_number} for {quote.title}.\n\nTotal Amount: ₹{quote.total_amount}\nValid Until: {quote.valid_until.strftime("%d %b %Y") if quote.valid_until else "N/A"}\n\nPlease let us know if you have any questions.\n\nBest regards,\n{company.company_name}',
    }
    return render(request, 'emails/send_quote.html', context)


# ============== Helper Functions ==============

def log_activity(request, action, instance):
    """Log an activity"""
    try:
        ActivityLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk),
            object_repr=str(instance)[:255],
            ip_address=get_client_ip(request),
        )
    except Exception:
        pass  # Don't fail if logging fails


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
