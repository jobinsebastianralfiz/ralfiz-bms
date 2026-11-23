"""Session-based web views for client portal frontend."""
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from core.models import Client, Project, ProjectLink, Task, Invoice, Quote, Document, Credential
from core.task_board import board_columns, project_progress
from .models import ProjectComment, ProjectUpdate, ClientNotification, SupportMessage


STAFF_PORTAL_MESSAGE = ('That is a staff account. The client portal only opens with the client\'s own '
                        'login - create or reset it in the Client Portal panel on the client\'s page.')


def _is_staff_login(user):
    return bool(user.is_staff or user.is_superuser
                or getattr(user, 'team_profile', None) or getattr(user, 'employee_profile', None))


def client_required(view_func):
    """Decorator: user must be logged in AND have a client profile."""
    @wraps(view_func)
    @login_required(login_url='client_portal:portal_login')
    def wrapper(request, *args, **kwargs):
        client = getattr(request.user, 'client_profile', None)
        if client is None:
            if _is_staff_login(request.user):
                # Keep the staff session; the portal is only for client logins.
                messages.info(request, STAFF_PORTAL_MESSAGE)
                return redirect('dashboard')
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
    from core.models import CompanySettings
    client = request.client
    company = CompanySettings.get_settings()
    return {
        'client': client,
        'active_nav': active_nav,
        'unread_count': _get_unread_count(client),
        'chat_unread': SupportMessage.objects.filter(client=client, from_client=False, read_at__isnull=True).count(),
        'company_name': company.company_name,
        'company_email': company.email,
    }


# ─── Auth ────────────────────────────────────────────────────────

def _login_context(**extra):
    from core.models import CompanySettings
    company = CompanySettings.get_settings()
    return {'company_name': company.company_name, 'company_email': company.email, **extra}


def _portal_username(login_name):
    """Clients may sign in with their email address as well as their username."""
    if '@' not in login_name:
        return login_name
    client = Client.objects.filter(email__iexact=login_name, user__isnull=False).select_related('user').first()
    return client.user.username if client else login_name


def portal_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'client_profile'):
        return redirect('client_portal:portal_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=_portal_username(username), password=password)

        if user is None:
            return render(request, 'client_portal/login.html', _login_context(error='Invalid username or password.', username=username))

        client = getattr(user, 'client_profile', None)
        if client is None:
            error = STAFF_PORTAL_MESSAGE if _is_staff_login(user) else 'No client portal access for this account.'
            return render(request, 'client_portal/login.html', _login_context(error=error, username=username))

        if not client.is_active:
            return render(request, 'client_portal/login.html', _login_context(error='Your account is inactive. Contact support.', username=username))

        login(request, user)
        if not request.POST.get('remember'):
            request.session.set_expiry(0)  # ends when the browser closes
        from core.security import safe_next
        return redirect(safe_next(request, request.GET.get('next'), 'client_portal:portal_dashboard'))

    return render(request, 'client_portal/login.html', _login_context())


def portal_logout(request):
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('client_portal:portal_login')


# ─── Dashboard ───────────────────────────────────────────────────

CARD_TONES = ('plum', 'teal', 'coral')
TITLES = {'dr', 'mr', 'mrs', 'ms', 'miss', 'prof', 'er', 'adv', 'sri', 'smt', 'shri'}


def _first_name(name):
    """'Dr. Priya Menon' -> 'Priya': the first word that is not a title."""
    words = (name or '').split()
    for w in words:
        if w.rstrip('.').lower() not in TITLES:
            return w
    return words[0] if words else 'there'


def _calendar_days(events, reverse=False, limit=6):
    """Group {'date', ...} events into [{'date', 'events'}] days, soonest (or newest) first."""
    days = {}
    for e in events:
        days.setdefault(e['date'], []).append(e)
    ordered = sorted(days.items(), key=lambda kv: kv[0], reverse=reverse)[:limit]
    return [{'date': d, 'events': evs} for d, evs in ordered]


@client_required
def portal_dashboard(request):
    from datetime import timedelta
    from django.utils import timezone
    from core.models import AMCContract, Payment
    from core.signoff_models import ProjectSignoff
    client = request.client
    projects = Project.objects.filter(client=client)
    today = timezone.localdate()

    active_statuses = ['confirmed', 'in_progress', 'review']
    live = list(projects.exclude(status='cancelled').order_by('-updated_at'))
    # Running projects first, then the rest, newest first within each.
    live.sort(key=lambda p: (p.status not in active_statuses, p.status == 'completed'))
    for i, p in enumerate(live):
        tasks = p.tasks.exclude(status='backlog')
        p.task_total = tasks.count()
        p.task_completed = tasks.filter(status='completed').count()
        p.progress = project_progress(p)
        p.overdue = bool(p.deadline and p.deadline < today and p.status in active_statuses)
        p.tone = CARD_TONES[i % len(CARD_TONES)]
    cards = live[:3]

    all_invoices = Invoice.all_objects.filter(client=client).exclude(status__in=['cancelled', 'draft'])
    pending_invoices = list(all_invoices.exclude(status='paid').order_by('due_date', 'issue_date'))
    total_invoiced = all_invoices.aggregate(t=Sum('total_amount'))['t'] or 0
    total_paid = all_invoices.aggregate(t=Sum('amount_paid'))['t'] or 0
    for i, inv in enumerate(pending_invoices):
        inv.is_late = bool(inv.due_date and inv.due_date < today)
        inv.tone = CARD_TONES[i % len(CARD_TONES)]
    paid_invoices = list(all_invoices.filter(status='paid').order_by('-issue_date')[:3])
    for i, inv in enumerate(paid_invoices):
        inv.tone = CARD_TONES[(i + len(pending_invoices)) % len(CARD_TONES)]
    balance = total_invoiced - total_paid

    # Calendar: what is coming up, and what was paid lately.
    tone_of = {p.pk: p.tone for p in live}
    upcoming = []
    for p in live:
        if p.deadline and p.status in active_statuses and p.deadline >= today:
            upcoming.append({'date': p.deadline, 'when': 'Due', 'what': 'Project deadline', 'title': p.name, 'tone': p.tone})
    for inv in pending_invoices:
        if inv.due_date:
            upcoming.append({'date': inv.due_date, 'amount': inv.balance_due,
                             'what': f'Invoice {inv.invoice_number}' + (' (overdue)' if inv.is_late else ''),
                             'title': inv.title, 'tone': 'coral'})
    for amc in AMCContract.objects.filter(project__client=client, status='active').select_related('project'):
        upcoming.append({'date': amc.next_due_date, 'when': 'AMC',
                         'what': 'AMC renewal' if amc.included_in_project else f'{amc.get_contract_type_display()} payment',
                         'title': amc.project.name, 'tone': tone_of.get(amc.project_id, 'plum')})
    for s in ProjectSignoff.objects.filter(project__client=client, status__in=ProjectSignoff.OPEN_STATUSES).select_related('project'):
        if not s.is_expired:
            upcoming.append({'date': timezone.localtime(s.expires_at).date(), 'when': 'Sign',
                             'what': 'Sign-off waiting for you', 'title': s.title, 'tone': tone_of.get(s.project_id, 'teal')})
    upcoming = _calendar_days(upcoming)

    recent_pays = [
        {'date': pay.payment_date, 'amount': pay.amount, 'what': f'Paid · {pay.invoice.invoice_number}',
         'title': pay.invoice.title, 'tone': CARD_TONES[i % len(CARD_TONES)]}
        for i, pay in enumerate(Payment.all_objects.filter(invoice__client=client)
                                .exclude(invoice__status='cancelled')
                                .select_related('invoice').order_by('-payment_date', '-created_at')[:6])
    ]
    recent = _calendar_days(recent_pays, reverse=True, limit=4)

    # Free card slots: money at a glance, then an invitation to start something new.
    fillers = []
    if len(cards) < 3 and total_invoiced:
        pct = int(total_paid * 100 / total_invoiced) if total_invoiced else 0
        fillers.append({'kind': 'paid', 'tone': CARD_TONES[len(cards) % 3], 'amount': total_paid,
                        'of': total_invoiced, 'pct': min(pct, 100)})
    if len(cards) + len(fillers) < 3:
        fillers.append({'kind': 'new'})

    ctx = _base_context(request, 'dashboard')
    ctx.update({
        'today': today,
        'first_name': _first_name(client.name),
        'cards': cards,
        'fillers': fillers,
        'projects': live,
        'stats': {
            'total_projects': len(live),
            'active_projects': sum(1 for p in live if p.status in active_statuses),
            'overdue_projects': sum(1 for p in live if p.overdue),
            'pending_invoices': len(pending_invoices),
        },
        'balance': balance,
        'total_paid': total_paid,
        'pending_invoices': pending_invoices[:5],
        'paid_invoices': paid_invoices,
        'upcoming': upcoming,
        'recent': recent,
        'open_signoffs': sum(len([e for e in d['events'] if e.get('when') == 'Sign']) for d in upcoming),
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
        tasks = p.tasks.exclude(status='backlog')
        total = tasks.count()
        completed = tasks.filter(status='completed').count()
        p.progress = project_progress(p)
        p.task_total = total
        p.task_completed = completed
        project_list.append(p)

    ctx = _base_context(request, 'projects')
    ctx.update({
        'projects': project_list,
        'status_filter': status_filter,
    })
    return render(request, 'client_portal/projects.html', ctx)


def _portal_board_columns(project):
    """Task board columns for the client, counting only what the client may see."""
    tasks = project.tasks.exclude(status='backlog').select_related('assigned_to').annotate(
        comment_total=Count('comments', filter=Q(comments__is_deleted=False, comments__is_visible_to_client=True), distinct=True),
        attachment_total=Count('attachments', distinct=True),
        open_issue_total=Count('issues', filter=Q(issues__is_visible_to_client=True, issues__status__in=['open', 'in_progress']), distinct=True),
    )
    return board_columns(tasks)[1]


@client_required
def portal_project_detail(request, project_id):
    client = request.client
    project = get_object_or_404(Project, id=project_id, client=client)

    tasks = project.tasks.exclude(status='backlog').prefetch_related('attachments')
    task_stats = {
        'total': tasks.count(),
        'todo': tasks.filter(status='todo').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'review': tasks.filter(status='review').count(),
        'completed': tasks.filter(status='completed').count(),
    }

    progress = project_progress(project)

    invoices = project.invoices(manager='all_objects').exclude(status='cancelled')
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

    from core.signoff_models import ProjectSignoff
    amc_contracts = project.amc_contracts.exclude(status='cancelled').prefetch_related('payments')
    signoffs = project.signoffs.exclude(
        status__in=[ProjectSignoff.STATUS_CANCELLED, ProjectSignoff.STATUS_SUPERSEDED]).order_by('-sent_at')

    ctx = _base_context(request, 'projects')
    ctx.update({
        'project': project,
        'project_invoices': invoices.order_by('-issue_date'),
        'amc_contracts': amc_contracts,
        'signoffs': signoffs,
        'project_links': project.links.filter(visible_to_client=True),
        'task_stats': task_stats,
        'board_columns': _portal_board_columns(project),
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
    qs = Invoice.all_objects.filter(client=client)

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    all_invoices = Invoice.all_objects.filter(client=client).exclude(status='cancelled')
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
    invoice = get_object_or_404(Invoice.all_objects, id=invoice_id, client=client)

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
            ctx = _base_context(request, 'password')
            ctx['error'] = 'Current password is incorrect.'
            return render(request, 'client_portal/change_password.html', ctx)

        if new_password != confirm_password:
            ctx = _base_context(request, 'password')
            ctx['error'] = 'New passwords do not match.'
            return render(request, 'client_portal/change_password.html', ctx)

        if len(new_password) < 8:
            ctx = _base_context(request, 'password')
            ctx['error'] = 'Password must be at least 8 characters.'
            return render(request, 'client_portal/change_password.html', ctx)

        request.user.set_password(new_password)
        request.user.save()
        messages.success(request, 'Password changed successfully. Please sign in again.')
        return redirect('client_portal:portal_login')

    ctx = _base_context(request, 'password')
    return render(request, 'client_portal/change_password.html', ctx)


# ─── Files, messages, search ─────────────────────────────────────

@client_required
def portal_files(request):
    """Every document shared on the client's projects."""
    from django.contrib.contenttypes.models import ContentType
    client = request.client
    projects = {str(p.pk): p for p in Project.objects.filter(client=client)}
    docs = list(Document.objects.filter(
        content_type=ContentType.objects.get_for_model(Project), object_id__in=list(projects)))
    for d in docs:
        d.project = projects.get(d.object_id)
    ctx = _base_context(request, 'files')
    ctx['documents'] = docs
    ctx['links'] = ProjectLink.objects.filter(project__client=client, visible_to_client=True).select_related('project')
    return render(request, 'client_portal/files.html', ctx)


@client_required
def portal_messages(request):
    """Project discussions, newest first, across all of the client's projects."""
    client = request.client
    threads = ProjectComment.objects.filter(
        project__client=client, is_internal=False, parent__isnull=True,
    ).select_related('author', 'project').order_by('-created_at')[:50]
    for t in threads:
        t.visible_replies = t.replies.filter(is_internal=False).count()
    ctx = _base_context(request, 'messages')
    ctx['threads'] = threads
    ctx['projects'] = Project.objects.filter(client=client).order_by('name')
    return render(request, 'client_portal/messages.html', ctx)


@client_required
def portal_search(request):
    client = request.client
    q = request.GET.get('q', '').strip()[:100]
    results = {'projects': [], 'invoices': [], 'quotes': []}
    if q:
        results['projects'] = Project.objects.filter(client=client).filter(
            Q(name__icontains=q) | Q(description__icontains=q))[:20]
        results['invoices'] = Invoice.all_objects.filter(client=client).exclude(status='cancelled').filter(
            Q(invoice_number__icontains=q) | Q(title__icontains=q))[:20]
        results['quotes'] = Quote.objects.filter(client=client).filter(
            Q(quote_number__icontains=q) | Q(title__icontains=q))[:20]
    ctx = _base_context(request, '')
    ctx.update({'q': q, 'results': results,
                'result_count': sum(len(v) for v in results.values())})
    return render(request, 'client_portal/search.html', ctx)


@client_required
def portal_amc_agreement(request, amc_id):
    """The client's own AMC agreement, as a printable page or PDF."""
    from core.models import AMCContract
    from core.views import _amc_agreement_context
    amc = get_object_or_404(AMCContract.objects.select_related('project__client'),
                            pk=amc_id, project__client=request.client)
    if not amc.agreement_no:
        amc.save(update_fields=['agreement_no'])
    if request.GET.get('download') == '1':
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        try:
            from weasyprint import HTML
            html = render_to_string('amc/agreement.html', _amc_agreement_context(amc, for_pdf=True))
            pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Portal AMC agreement PDF failed for %s', amc.pk)
        else:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{amc.reference.replace("/", "-")}.pdf"'
            return response
    ctx = _amc_agreement_context(amc)
    ctx['portal_view'] = True
    return render(request, 'amc/agreement.html', ctx)
