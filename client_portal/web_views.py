"""Session-based web views for client portal frontend."""
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from core.models import Client, Project, Task, Invoice, Quote, Document, Credential
from .models import ProjectComment, ProjectUpdate, ClientNotification


def client_required(view_func):
    """Decorator: user must be logged in AND have a client profile."""
    @wraps(view_func)
    @login_required(login_url='client_portal:portal_login')
    def wrapper(request, *args, **kwargs):
        client = getattr(request.user, 'client_profile', None)
        if client is None:
            logout(request)
            messages.error(request, 'No client portal access for this account.')
            return redirect('client_portal:portal_login')
        if not client.is_active:
            logout(request)
            messages.error(request, 'Your account is inactive. Contact support.')
            return redirect('client_portal:portal_login')
        request.client = client
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_unread_count(client):
    return ClientNotification.objects.filter(client=client, is_read=False).count()


def _base_context(request, active_nav=''):
    client = request.client
    return {
        'client': client,
        'active_nav': active_nav,
        'unread_count': _get_unread_count(client),
    }


# ─── Auth ────────────────────────────────────────────────────────

def portal_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'client_profile'):
        return redirect('client_portal:portal_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, 'client_portal/login.html', {'error': 'Invalid username or password.'})

        client = getattr(user, 'client_profile', None)
        if client is None:
            return render(request, 'client_portal/login.html', {'error': 'No client portal access for this account.'})

        if not client.is_active:
            return render(request, 'client_portal/login.html', {'error': 'Your account is inactive. Contact support.'})

        login(request, user)
        next_url = request.GET.get('next', 'client_portal:portal_dashboard')
        return redirect(next_url)

    return render(request, 'client_portal/login.html')


def portal_logout(request):
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('client_portal:portal_login')


# ─── Dashboard ───────────────────────────────────────────────────

@client_required
def portal_dashboard(request):
    client = request.client
    projects = Project.objects.filter(client=client)

    active_statuses = ['confirmed', 'in_progress', 'review']
    active_projects = projects.filter(status__in=active_statuses)

    # Annotate active projects with progress info
    active_list = []
    for p in active_projects[:5]:
        tasks = p.tasks.all()
        total = tasks.count()
        completed = tasks.filter(status='completed').count()
        # Check for manual progress
        latest_update = p.updates.filter(
            progress_percentage__isnull=False, is_visible_to_client=True
        ).first()
        progress = latest_update.progress_percentage if latest_update else (int((completed / total) * 100) if total else 0)
        p.progress = progress
        p.task_total = total
        p.task_completed = completed
        active_list.append(p)

    all_invoices = Invoice.objects.filter(client=client).exclude(status='cancelled')
    pending_invoices = all_invoices.exclude(status='paid')[:5]
    total_invoiced = all_invoices.aggregate(t=Sum('total_amount'))['t'] or 0
    total_paid = all_invoices.aggregate(t=Sum('amount_paid'))['t'] or 0

    recent_updates = ProjectUpdate.objects.filter(
        project__client=client, is_visible_to_client=True
    )[:8]

    ctx = _base_context(request, 'dashboard')
    ctx.update({
        'stats': {
            'total_projects': projects.count(),
            'active_projects': active_projects.count(),
            'completed_projects': projects.filter(status='completed').count(),
            'pending_invoices': pending_invoices.count(),
            'balance_due': f'{float(total_invoiced - total_paid):,.0f}',
        },
        'active_projects': active_list,
        'pending_invoices': pending_invoices,
        'recent_updates': recent_updates,
    })
    return render(request, 'client_portal/dashboard.html', ctx)


# ─── Projects ────────────────────────────────────────────────────

@client_required
def portal_projects(request):
    client = request.client
    qs = Project.objects.filter(client=client)

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    project_list = []
    for p in qs:
        tasks = p.tasks.all()
        total = tasks.count()
        completed = tasks.filter(status='completed').count()
        latest_update = p.updates.filter(
            progress_percentage__isnull=False, is_visible_to_client=True
        ).first()
        p.progress = latest_update.progress_percentage if latest_update else (int((completed / total) * 100) if total else 0)
        p.task_total = total
        p.task_completed = completed
        project_list.append(p)

    ctx = _base_context(request, 'projects')
    ctx.update({
        'projects': project_list,
        'status_filter': status_filter,
    })
    return render(request, 'client_portal/projects.html', ctx)


@client_required
def portal_project_detail(request, project_id):
    client = request.client
    project = get_object_or_404(Project, id=project_id, client=client)

    tasks = project.tasks.prefetch_related('attachments').all()
    task_stats = {
        'total': tasks.count(),
        'todo': tasks.filter(status='todo').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'review': tasks.filter(status='review').count(),
        'completed': tasks.filter(status='completed').count(),
    }

    latest_update = project.updates.filter(
        progress_percentage__isnull=False, is_visible_to_client=True
    ).first()
    if latest_update:
        progress = latest_update.progress_percentage
    elif task_stats['total']:
        progress = int((task_stats['completed'] / task_stats['total']) * 100)
    else:
        progress = 0

    invoices = project.invoices.exclude(status='cancelled')
    total_invoiced = invoices.aggregate(t=Sum('total_amount'))['t'] or 0
    total_paid = invoices.aggregate(t=Sum('amount_paid'))['t'] or 0

    comments = ProjectComment.objects.filter(
        project=project, is_internal=False, parent__isnull=True
    ).select_related('author')

    # Attach visible replies to each comment
    for comment in comments:
        comment.visible_replies = comment.replies.filter(is_internal=False).select_related('author').order_by('created_at')

    updates = ProjectUpdate.objects.filter(
        project=project, is_visible_to_client=True
    )

    # Build unified Timeline: project updates + client-visible task comments + task activities
    from core.models import TaskComment, TaskActivity
    project_task_ids = list(tasks.values_list('id', flat=True))
    task_comments_tl = TaskComment.objects.filter(
        task_id__in=project_task_ids, is_visible_to_client=True, is_deleted=False
    ).select_related('author', 'task')
    task_activities_tl = TaskActivity.objects.filter(
        task_id__in=project_task_ids, is_visible_to_client=True,
        verb__in=['status_changed', 'issue_opened', 'issue_resolved', 'issue_status_changed']
    ).select_related('actor', 'task', 'related_issue')

    timeline_events = []
    for u in updates:
        timeline_events.append({
            'kind': 'update',
            'icon': {'milestone': 'flag-checkered', 'progress': 'chart-line', 'release': 'rocket', 'blocker': 'exclamation-triangle', 'info': 'info-circle'}.get(u.update_type, 'info-circle'),
            'color': {'milestone': '#0ea5a4', 'progress': '#6366f1', 'release': '#059669', 'blocker': '#dc2626', 'info': '#64748b'}.get(u.update_type, '#64748b'),
            'title': u.title,
            'body': u.description,
            'author': u.author,
            'type_label': u.get_update_type_display() if hasattr(u, 'get_update_type_display') else u.update_type,
            'progress_percentage': u.progress_percentage,
            'timestamp': u.created_at,
            'task': None,
        })
    for c in task_comments_tl:
        timeline_events.append({
            'kind': 'comment',
            'icon': 'comment',
            'color': '#6366f1',
            'title': f'Comment on {c.task.title}',
            'body': c.body,
            'author': c.author,
            'type_label': 'Update',
            'progress_percentage': None,
            'timestamp': c.created_at,
            'task': c.task,
        })
    for a in task_activities_tl:
        if a.verb == 'status_changed':
            title = f'{a.task.title}: {a.from_value} → {a.to_value}'
            icon, color = 'arrow-right', '#0ea5a4'
            label = 'Status'
        elif a.verb == 'issue_opened':
            title = f'Issue opened: {a.message or ""}'
            icon, color = 'exclamation-triangle', '#f59e0b'
            label = 'Issue'
        elif a.verb == 'issue_resolved':
            title = f'Issue resolved: {a.message or ""}'
            icon, color = 'check-circle', '#10b981'
            label = 'Resolved'
        else:
            title = f'Issue updated: {a.from_value} → {a.to_value}'
            icon, color = 'sync-alt', '#8b5cf6'
            label = 'Issue'
        timeline_events.append({
            'kind': 'activity',
            'icon': icon,
            'color': color,
            'title': title,
            'body': '',
            'author': a.actor,
            'type_label': label,
            'progress_percentage': None,
            'timestamp': a.created_at,
            'task': a.task,
        })
    timeline_events.sort(key=lambda e: e['timestamp'], reverse=True)

    ct = ContentType.objects.get_for_model(Project)
    documents = Document.objects.filter(content_type=ct, object_id=str(project.id))

    team_members = project.team_members.filter(is_active=True)

    credentials = Credential.objects.filter(
        project=project, client_visible=True, is_active=True
    ).order_by('credential_type', 'name')

    ctx = _base_context(request, 'projects')
    ctx.update({
        'project': project,
        'task_stats': task_stats,
        'tasks_todo': tasks.filter(status='todo'),
        'tasks_in_progress': tasks.filter(status='in_progress'),
        'tasks_review': tasks.filter(status='review'),
        'tasks_completed': tasks.filter(status='completed'),
        'progress': progress,
        'financial': {
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'balance_due': total_invoiced - total_paid,
        },
        'comments': comments,
        'updates': updates,
        'timeline_events': timeline_events,
        'documents': documents,
        'credentials': credentials,
        'team_members': team_members,
    })
    return render(request, 'client_portal/project_detail.html', ctx)


@client_required
def portal_add_comment(request, project_id):
    client = request.client
    project = get_object_or_404(Project, id=project_id, client=client)

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            ProjectComment.objects.create(
                project=project,
                author=request.user,
                message=message,
                is_internal=False,
            )
            messages.success(request, 'Comment posted.')
    return redirect(f"{request.META.get('HTTP_REFERER', '')}#comments")


# ─── Invoices ────────────────────────────────────────────────────

@client_required
def portal_invoices(request):
    client = request.client
    qs = Invoice.objects.filter(client=client)

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    all_invoices = Invoice.objects.filter(client=client).exclude(status='cancelled')
    total_paid = all_invoices.aggregate(t=Sum('amount_paid'))['t'] or 0
    total_invoiced = all_invoices.aggregate(t=Sum('total_amount'))['t'] or 0

    ctx = _base_context(request, 'invoices')
    ctx.update({
        'invoices': qs,
        'status_filter': status_filter,
        'total_paid': total_paid,
        'balance_due': total_invoiced - total_paid,
    })
    return render(request, 'client_portal/invoices.html', ctx)


@client_required
def portal_invoice_detail(request, invoice_id):
    client = request.client
    invoice = get_object_or_404(Invoice, id=invoice_id, client=client)

    # Auto-mark as viewed
    if invoice.status == 'sent':
        invoice.status = 'viewed'
        invoice.save(update_fields=['status'])

    ctx = _base_context(request, 'invoices')
    ctx['invoice'] = invoice
    return render(request, 'client_portal/invoice_detail.html', ctx)


# ─── Quotes ──────────────────────────────────────────────────────

@client_required
def portal_quotes(request):
    client = request.client
    ctx = _base_context(request, 'quotes')
    ctx['quotes'] = Quote.objects.filter(client=client)
    return render(request, 'client_portal/quotes.html', ctx)


@client_required
def portal_quote_detail(request, quote_id):
    client = request.client
    quote = get_object_or_404(Quote, id=quote_id, client=client)

    if quote.status == 'sent':
        quote.status = 'viewed'
        quote.save(update_fields=['status'])

    ctx = _base_context(request, 'quotes')
    ctx['quote'] = quote
    return render(request, 'client_portal/quote_detail.html', ctx)


@client_required
def portal_quote_respond(request, quote_id):
    client = request.client
    quote = get_object_or_404(Quote, id=quote_id, client=client)

    if request.method == 'POST' and quote.status in ('sent', 'viewed'):
        action = request.POST.get('action')
        if action in ('accept', 'reject'):
            quote.status = 'accepted' if action == 'accept' else 'rejected'
            notes = request.POST.get('notes', '').strip()
            if notes:
                quote.client_notes = notes
            quote.save()
            messages.success(request, f'Quote {action}ed successfully.')
    return redirect('client_portal:portal_quote_detail', quote_id=quote_id)


# ─── Notifications ───────────────────────────────────────────────

@client_required
def portal_notifications(request):
    client = request.client
    ctx = _base_context(request, 'notifications')
    ctx['notifications'] = ClientNotification.objects.filter(client=client)
    return render(request, 'client_portal/notifications.html', ctx)


@client_required
def portal_mark_all_read(request):
    if request.method == 'POST':
        ClientNotification.objects.filter(
            client=request.client, is_read=False
        ).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
    return redirect('client_portal:portal_notifications')


@client_required
def portal_mark_read(request, notification_id):
    if request.method == 'POST':
        try:
            notification = ClientNotification.objects.get(
                id=notification_id, client=request.client
            )
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        except ClientNotification.DoesNotExist:
            pass
    return redirect('client_portal:portal_notifications')


# ─── Profile ─────────────────────────────────────────────────────

@client_required
def portal_profile(request):
    client = request.client
    if request.method == 'POST':
        client.name = request.POST.get('name', client.name).strip()
        client.company_name = request.POST.get('company_name', '').strip()
        client.email = request.POST.get('email', client.email).strip()
        client.phone = request.POST.get('phone', '').strip()
        client.whatsapp = request.POST.get('whatsapp', '').strip()
        client.address = request.POST.get('address', '').strip()
        client.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('client_portal:portal_profile')

    ctx = _base_context(request, 'profile')
    return render(request, 'client_portal/profile.html', ctx)


@client_required
def portal_change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not request.user.check_password(old_password):
            ctx = _base_context(request, 'profile')
            ctx['error'] = 'Current password is incorrect.'
            return render(request, 'client_portal/change_password.html', ctx)

        if new_password != confirm_password:
            ctx = _base_context(request, 'profile')
            ctx['error'] = 'New passwords do not match.'
            return render(request, 'client_portal/change_password.html', ctx)

        if len(new_password) < 8:
            ctx = _base_context(request, 'profile')
            ctx['error'] = 'Password must be at least 8 characters.'
            return render(request, 'client_portal/change_password.html', ctx)

        request.user.set_password(new_password)
        request.user.save()
        messages.success(request, 'Password changed successfully. Please sign in again.')
        return redirect('client_portal:portal_login')

    ctx = _base_context(request, 'profile')
    return render(request, 'client_portal/change_password.html', ctx)
