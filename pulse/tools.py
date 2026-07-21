"""Whitelisted read-only query functions -- the ONLY database path for PULSE.

Design rules, enforced by construction rather than by convention:

  * The model never composes SQL. It selects a function by name and supplies
    typed arguments; everything below is hand-written ORM.
  * Every function takes a resolved PulseScope as its first argument and calls
    require_business() before touching the ORM.
  * Reads only. Nothing here calls save(), delete(), update(), or create().
  * Returns plain JSON-safe primitives so the result can go straight into an
    API response and into the model's context without further massaging.

Field names here were verified against the real models. Two concepts the AI
might reasonably ask for do NOT exist in this schema and are deliberately not
faked:

  * "blocked" projects -- Project.status has no blocked value. The closest
    honest signals are status='on_hold' and an elapsed deadline, which is what
    get_projects_needing_attention reports.
  * "hot" leads -- Lead has no priority or score field. closing_probability
    exists but is hand-entered and defaults to 0, so it is reported as-is and
    never used as the sole definition of importance.
"""

import uuid
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from core.models import (
    AMCContract,
    Client,
    Credential,
    Expense,
    Invoice,
    Payment,
    Project,
    Quote,
    Task,
    TaskIssue,
)
from crm.models import Lead
from employees.models import Attendance, LeaveRequest

# --------------------------------------------------------------------------
# Status vocabularies.
#
# These are the interpretive decisions. They live as named constants precisely
# so that changing what the business means by "active" is a one-line edit here
# rather than a hunt through query bodies.
# --------------------------------------------------------------------------

#: Projects considered live work. Excludes the pre-sale funnel (lead,
#: proposal, negotiation) and anything finished or paused.
ACTIVE_PROJECT_STATUSES = ('confirmed', 'in_progress', 'review')

#: Projects that are finished one way or another; never "needing attention".
CLOSED_PROJECT_STATUSES = ('completed', 'cancelled')

#: Invoices that represent real money still owed. 'draft' is not yet a claim on
#: anyone; 'paid' and 'cancelled' are settled.
OPEN_INVOICE_STATUSES = ('sent', 'viewed', 'partial', 'overdue')

#: Leads that are out of the pipeline and should not surface as follow-ups.
CLOSED_LEAD_STATUSES = ('converted', 'lost', 'unqualified')

#: TaskIssue states that still need someone. TaskIssue is the only model in
#: this schema that records a blocker -- its own docstring calls it
#: "issues/bugs/blockers reported against a task" -- so it is what the command
#: centre's "Blockers" card counts.
OPEN_ISSUE_STATUSES = ('open', 'in_progress')

_MONEY = DecimalField(max_digits=14, decimal_places=2)


def _zero_money():
    return Value(Decimal('0.00'), output_field=_MONEY)


def _money(value) -> float:
    """Decimals are not JSON-serialisable; the API and the model both want floats."""
    return float(value or 0)


def _date(value):
    return value.isoformat() if value else None


def _inr(value) -> str:
    """Format with Indian digit grouping: 306950 -> '3,06,950'.

    Python has no locale-free way to do this and the rest of the UI already
    renders lakh-grouped amounts via Intl 'en-IN', so a server-rendered
    figure must match or the same number looks different in two places.
    """
    n = int(round(float(value or 0)))
    sign = '-' if n < 0 else ''
    digits = str(abs(n))
    if len(digits) <= 3:
        return sign + digits
    # Last three digits, then pairs, most-significant first.
    head, tail = digits[:-3], digits[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return sign + ','.join(parts + [tail])


def _parse_uuid(value, field_name='id'):
    """Parse a UUID primary key.

    Primary key types are NOT uniform across this project: core and employees
    models use UUIDField, but crm.Lead uses a plain BigAutoField integer. Use
    this for core/employees ids and _parse_int_pk for crm ids.
    """
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f'{field_name} must be a valid UUID, got: {value!r}')


def _parse_int_pk(value, field_name='id'):
    """Parse an integer primary key (crm models)."""
    try:
        parsed = int(str(value).strip())
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f'{field_name} must be an integer, got: {value!r}')
    if parsed < 1:
        raise ValueError(f'{field_name} must be a positive integer, got: {value!r}')
    return parsed


# --------------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------------


def get_projects_needing_attention(scope):
    """Projects that are paused or past their deadline.

    This is the honest replacement for "blocked projects": the schema records
    no blocked state, so attention is defined as status='on_hold' OR a deadline
    that has passed while the project is still open.

    Note this re-implements Project.is_overdue as a queryset filter. That
    property is pure Python and cannot be used in .filter(); the logic is
    mirrored here (deadline elapsed, status not closed) and the two must be
    kept in step.
    """
    scope.require_business()
    today = timezone.localdate()

    qs = (
        Project.objects
        .exclude(status__in=CLOSED_PROJECT_STATUSES)
        .filter(Q(status='on_hold') | Q(deadline__lt=today))
        .select_related('client')
        .order_by('deadline', 'name')
    )

    results = []
    for project in qs:
        overdue = bool(project.deadline and project.deadline < today)
        results.append({
            'id': str(project.id),
            'name': project.name,
            'client': project.client.name if project.client else None,
            'status': project.status,
            'status_display': project.get_status_display(),
            'deadline': _date(project.deadline),
            'is_overdue': overdue,
            'days_overdue': (today - project.deadline).days if overdue else 0,
            'on_hold': project.status == 'on_hold',
            'reason': 'on hold' if project.status == 'on_hold' else 'past deadline',
        })
    return {'count': len(results), 'projects': results}


def count_projects_by_status(scope):
    """Every status and how many projects sit in it, including empty statuses."""
    scope.require_business()

    counted = dict(
        Project.objects.values_list('status').annotate(n=Count('id'))
    )
    breakdown = [
        {'status': value, 'label': label, 'count': counted.get(value, 0)}
        for value, label in Project.STATUS_CHOICES
    ]
    active = sum(
        row['count'] for row in breakdown
        if row['status'] in ACTIVE_PROJECT_STATUSES
    )
    return {
        'total': sum(row['count'] for row in breakdown),
        'active': active,
        'active_definition': list(ACTIVE_PROJECT_STATUSES),
        'breakdown': breakdown,
    }


def get_project_summary(scope, project_id):
    """One project in depth: client, team, task counts, money."""
    scope.require_business()
    pk = _parse_uuid(project_id, 'project_id')

    project = (
        Project.objects
        .select_related('client')
        .prefetch_related('team_members')
        .filter(pk=pk)
        .first()
    )
    if project is None:
        return {'found': False, 'project_id': str(pk)}

    task_counts = dict(
        Task.objects.filter(project=project)
        .values_list('status').annotate(n=Count('id'))
    )
    invoice_totals = Invoice.objects.filter(project=project).aggregate(
        billed=Coalesce(Sum('total_amount'), _zero_money()),
        collected=Coalesce(Sum('amount_paid'), _zero_money()),
    )
    open_issues = TaskIssue.objects.filter(
        task__project=project, status__in=OPEN_ISSUE_STATUSES
    ).count()
    critical_issues = TaskIssue.objects.filter(
        task__project=project,
        status__in=OPEN_ISSUE_STATUSES,
        severity__in=('high', 'critical'),
    ).count()
    today = timezone.localdate()

    return {
        'found': True,
        'id': str(project.id),
        'name': project.name,
        'client': project.client.name if project.client else None,
        'status': project.status,
        'status_display': project.get_status_display(),
        'project_type': project.project_type,
        'start_date': _date(project.start_date),
        'deadline': _date(project.deadline),
        'completed_date': _date(project.completed_date),
        'is_overdue': bool(
            project.deadline
            and project.deadline < today
            and project.status not in CLOSED_PROJECT_STATUSES
        ),
        'estimated_budget': _money(project.estimated_budget),
        'final_amount': _money(project.final_amount),
        'amount_billed': _money(invoice_totals['billed']),
        'amount_collected': _money(invoice_totals['collected']),
        'team': [
            {'id': str(m.id), 'name': m.name, 'role': m.role}
            for m in project.team_members.all()
        ],
        'tasks': {
            'total': sum(task_counts.values()),
            'open': sum(
                count for status, count in task_counts.items()
                if status != 'completed'
            ),
            'by_status': {
                value: task_counts.get(value, 0)
                for value, _label in Task.STATUS_CHOICES
            },
        },
        'issues': {
            'open': open_issues,
            'critical': critical_issues,
        },
    }


def get_team_for_project(scope, project_id):
    """Who is assigned to a project."""
    scope.require_business()
    pk = _parse_uuid(project_id, 'project_id')

    project = Project.objects.prefetch_related('team_members').filter(pk=pk).first()
    if project is None:
        return {'found': False, 'project_id': str(pk)}

    return {
        'found': True,
        'project': project.name,
        'team': [
            {
                'id': str(m.id),
                'name': m.name,
                'role': m.role,
                'employment_type': m.employment_type,
                'is_active': m.is_active,
            }
            for m in project.team_members.all()
        ],
    }


# --------------------------------------------------------------------------
# Money
# --------------------------------------------------------------------------


def get_overdue_invoices(scope):
    """Invoices past their due date with a balance still outstanding."""
    scope.require_business()
    today = timezone.localdate()

    qs = (
        Invoice.objects
        .filter(status__in=OPEN_INVOICE_STATUSES, due_date__lt=today)
        .annotate(balance=F('total_amount') - F('amount_paid'))
        .filter(balance__gt=0)
        .select_related('client', 'project')
        .order_by('due_date')
    )

    invoices = [
        {
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'client': inv.client.name if inv.client else None,
            'project': inv.project.name if inv.project else None,
            'status': inv.status,
            'total_amount': _money(inv.total_amount),
            'amount_paid': _money(inv.amount_paid),
            'balance': _money(inv.balance),
            'due_date': _date(inv.due_date),
            'days_overdue': (today - inv.due_date).days,
        }
        for inv in qs
    ]
    return {
        'count': len(invoices),
        'total_outstanding': round(sum(i['balance'] for i in invoices), 2),
        'invoices': invoices,
    }


def get_outstanding_receivables(scope):
    """Total unpaid balance across all open invoices, split by overdue status."""
    scope.require_business()
    today = timezone.localdate()

    base = (
        Invoice.objects
        .filter(status__in=OPEN_INVOICE_STATUSES)
        .annotate(balance=F('total_amount') - F('amount_paid'))
        .filter(balance__gt=0)
    )
    totals = base.aggregate(
        outstanding=Coalesce(Sum('balance'), _zero_money()),
        invoice_count=Count('id'),
    )
    overdue = base.filter(due_date__lt=today).aggregate(
        outstanding=Coalesce(Sum('balance'), _zero_money()),
        invoice_count=Count('id'),
    )

    return {
        'total_outstanding': _money(totals['outstanding']),
        'open_invoice_count': totals['invoice_count'],
        'overdue_outstanding': _money(overdue['outstanding']),
        'overdue_invoice_count': overdue['invoice_count'],
    }


# --------------------------------------------------------------------------
# Leads
# --------------------------------------------------------------------------


def get_leads_needing_followup(scope, limit=25):
    """Open leads whose follow-up date has arrived or passed.

    This is the honest reading of "hot leads". The schema has no priority or
    score field, so importance is defined by a follow-up date the business
    already committed to. closing_probability is reported alongside for
    context but is not used to filter, because it defaults to 0 and is
    frequently left unset.
    """
    scope.require_business()
    today = timezone.localdate()
    limit = max(1, min(int(limit), 100))

    qs = (
        Lead.objects
        .exclude(status__in=CLOSED_LEAD_STATUSES)
        .filter(next_follow_up_date__lte=today)
        .select_related('assigned_to')
        .order_by('next_follow_up_date', '-closing_probability')[:limit]
    )

    leads = [
        {
            'id': str(lead.id),
            'contact_person': lead.contact_person,
            'company_name': lead.company_name,
            'phone': lead.phone,
            'status': lead.status,
            'status_display': lead.get_status_display(),
            'source': lead.source,
            'assigned_to': (
                lead.assigned_to.get_full_name() or lead.assigned_to.get_username()
            ) if lead.assigned_to else None,
            'next_follow_up_date': _date(lead.next_follow_up_date),
            'days_overdue': (today - lead.next_follow_up_date).days,
            'closing_probability': lead.closing_probability,
        }
        for lead in qs
    ]
    return {'count': len(leads), 'leads': leads}


def get_lead_pipeline_summary(scope):
    """Lead counts across every pipeline stage."""
    scope.require_business()

    counted = dict(Lead.objects.values_list('status').annotate(n=Count('id')))
    breakdown = [
        {'status': value, 'label': label, 'count': counted.get(value, 0)}
        for value, label in Lead.STATUS_CHOICES
    ]
    open_count = sum(
        row['count'] for row in breakdown
        if row['status'] not in CLOSED_LEAD_STATUSES
    )
    return {
        'total': sum(row['count'] for row in breakdown),
        'open': open_count,
        'breakdown': breakdown,
    }


def get_lead_quotes(scope, lead_id):
    """Structured quotes raised against a lead.

    A lead has two unrelated quote concepts: structured core.Quote rows
    (lead.quotes) and uploaded files (lead.quote_attachments). By decision this
    reports the structured ones only.
    """
    scope.require_business()
    pk = _parse_int_pk(lead_id, 'lead_id')

    lead = Lead.objects.filter(pk=pk).first()
    if lead is None:
        return {'found': False, 'lead_id': str(pk)}

    quotes = (
        Quote.objects.filter(lead=lead)
        .select_related('project')
        .order_by('-issue_date')
    )
    return {
        'found': True,
        'lead': lead.contact_person,
        'company_name': lead.company_name,
        'quotes': [
            {
                'id': str(q.id),
                'quote_number': q.quote_number,
                'title': q.title,
                'status': q.status,
                'status_display': q.get_status_display(),
                'total_amount': _money(q.total_amount),
                'issue_date': _date(q.issue_date),
                'valid_until': _date(q.valid_until),
                'project': q.project.name if q.project else None,
            }
            for q in quotes
        ],
    }


# --------------------------------------------------------------------------
# People
# --------------------------------------------------------------------------


def get_pending_leave_requests(scope):
    """Leave requests awaiting a decision."""
    scope.require_business()

    qs = (
        LeaveRequest.objects
        .filter(status='pending')
        .select_related('employee', 'employee__user', 'leave_type')
        .order_by('start_date')
    )
    requests = [
        {
            'id': str(req.id),
            'employee': req.employee.full_name,
            'employee_id': req.employee.employee_id,
            'leave_type': req.leave_type.name if req.leave_type else None,
            'start_date': _date(req.start_date),
            'end_date': _date(req.end_date),
            'total_days': req.total_days,
            'reason': req.reason,
        }
        for req in qs
    ]
    return {'count': len(requests), 'requests': requests}


def get_attendance_summary(scope, date=None):
    """Who was present, absent, late or remote on a given day (default today)."""
    scope.require_business()

    if date:
        from datetime import date as _d
        try:
            target = _d.fromisoformat(str(date))
        except ValueError:
            raise ValueError(f'date must be ISO format YYYY-MM-DD, got: {date!r}')
    else:
        target = timezone.localdate()

    counted = dict(
        Attendance.objects.filter(date=target)
        .values_list('status').annotate(n=Count('id'))
    )
    records = (
        Attendance.objects.filter(date=target)
        .select_related('employee')
        .order_by('employee__employee_id')
    )
    return {
        'date': target.isoformat(),
        'by_status': {
            value: counted.get(value, 0)
            for value, _label in Attendance.STATUS_CHOICES
        },
        'total_records': sum(counted.values()),
        'employees': [
            {
                'employee': rec.employee.full_name,
                'status': rec.status,
                'check_in': rec.check_in.isoformat() if rec.check_in else None,
                'check_out': rec.check_out.isoformat() if rec.check_out else None,
                'worked_hours': _money(rec.worked_hours),
            }
            for rec in records
        ],
    }


# --------------------------------------------------------------------------
# Portfolio graph
# --------------------------------------------------------------------------

#: Node colour by project status, using the jewel tones from the design spec.
#: Meaning is encoded in hue -- this is not decoration.
STATUS_HUE = {
    'lead': '#7cc4e8',          # cyan   -- not yet won
    'proposal': '#7cc4e8',
    'negotiation': '#a78bd6',   # violet -- in play
    'confirmed': '#a78bd6',
    'in_progress': '#2fd4d4',   # teal   -- live work
    'review': '#2fd4d4',
    'completed': '#4edea3',     # green  -- done
    'on_hold': '#e08aa0',       # rose   -- needs a human
    'cancelled': '#6b7d86',     # grey   -- inert
}

#: Reserved for the node the user has selected. The design spec allows gold on
#: exactly one thing at a time, so it must not also encode a data condition --
#: four simultaneously-overdue clients would drown the selection signal.
SELECTION_HUE = '#e8c07a'

#: Rose doubles as the attention colour on both clients and projects.
ATTENTION_HUE = '#e08aa0'


def find_entity(scope, name):
    """Resolve a client or project NAME to its IDs.

    Users ask about things by name; every detail tool wants an ID. This is
    the bridge: a case-insensitive substring search over client names,
    client companies and project names. Capped small on purpose -- it is a
    lookup, not a browse.
    """
    scope.require_business()
    query = (name or '').strip()
    if len(query) < 2:
        raise ValueError('Give at least two characters of the name to search for.')

    clients = list(
        Client.objects
        .filter(Q(name__icontains=query) | Q(company_name__icontains=query),
                is_active=True)
        .order_by('name')[:8]
    )
    projects = list(
        Project.objects
        .filter(name__icontains=query)
        .select_related('client')
        .order_by('name')[:8]
    )

    return {
        'query': query,
        'clients': [
            {'id': str(c.id), 'name': c.name, 'company': c.company_name}
            for c in clients
        ],
        'projects': [
            {
                'id': str(p.id),
                'name': p.name,
                'status': p.status,
                'status_display': p.get_status_display(),
                'client': p.client.name if p.client else None,
                'client_id': str(p.client_id) if p.client_id else None,
            }
            for p in projects
        ],
    }


def get_portfolio_graph(scope):
    """The whole business as a graph: clients orbiting the core, projects orbiting clients.

    Shape is deliberately generic (nodes + edges + a core) so the renderer
    does not need to know about Clients or Projects specifically.

    Every number here is real. Clients with no projects are still returned --
    an empty orbit is information, not something to hide.
    """
    scope.require_business()
    today = timezone.localdate()

    clients = list(
        Client.objects.filter(is_active=True)
        .prefetch_related('projects')
        .order_by('name')
    )

    # Per-project money drives the satellites.
    invoice_by_project = {
        row['project_id']: row
        for row in Invoice.objects.values('project_id').annotate(
            billed=Coalesce(Sum('total_amount'), _zero_money()),
            collected=Coalesce(Sum('amount_paid'), _zero_money()),
        )
    }

    # Client totals are summed from the CLIENT, not from their projects.
    # Rolling up per-project figures silently drops any invoice raised against
    # a client without a project attached -- real money that would vanish from
    # both the node total and everyone's percentage share.
    invoice_by_client = {
        row['client_id']: row
        for row in Invoice.objects.values('client_id').annotate(
            billed=Coalesce(Sum('total_amount'), _zero_money()),
            collected=Coalesce(Sum('amount_paid'), _zero_money()),
        )
    }

    nodes, edges = [], []
    total_projects = 0
    total_billed = Decimal('0.00')

    for client in clients:
        projects = list(client.projects.all())
        live = [p for p in projects if p.status in ACTIVE_PROJECT_STATUSES]

        client_money = invoice_by_client.get(client.id, {})
        client_billed = client_money.get('billed') or Decimal('0.00')
        client_collected = client_money.get('collected') or Decimal('0.00')

        satellites = []
        for project in projects:
            money = invoice_by_project.get(project.id, {})
            billed = money.get('billed') or Decimal('0.00')
            overdue = bool(
                project.deadline
                and project.deadline < today
                and project.status not in CLOSED_PROJECT_STATUSES
            )
            satellites.append({
                'id': f'project:{project.id}',
                'label': project.name,
                'status': project.status,
                'status_display': project.get_status_display(),
                'hue': STATUS_HUE.get(project.status, '#7c94a0'),
                'billed': _money(billed),
                'deadline': _date(project.deadline),
                'needs_attention': bool(overdue or project.status == 'on_hold'),
                'tag': (today - project.deadline).days if overdue else None,
            })
            edges.append({'from': f'client:{client.id}', 'to': f'project:{project.id}'})

        total_projects += len(projects)
        total_billed += client_billed

        nodes.append({
            'id': f'client:{client.id}',
            'label': client.name,
            'company': client.company_name,
            'kind': 'client',
            'priority': client.priority,
            # A client's hue comes from its most urgent live project, so
            # colour on the graph means "where is the heat".
            'hue': (
                ATTENTION_HUE if any(s['needs_attention'] for s in satellites)
                else (STATUS_HUE.get(live[0].status, '#7c94a0') if live else '#4a5c66')
            ),
            'needs_attention': any(s['needs_attention'] for s in satellites),
            'project_count': len(projects),
            'active_count': len(live),
            'billed': _money(client_billed),
            'collected': _money(client_collected),
            # The number that actually matters: billed is not the same as owed.
            'outstanding': _money(client_billed - client_collected),
            'satellites': satellites,
        })
        edges.append({'from': 'core', 'to': f'client:{client.id}'})

    # Share of billing, so each node can carry a percentage like the reference.
    for node in nodes:
        node['share'] = (
            round(node['billed'] / float(total_billed) * 100)
            if total_billed else 0
        )

    return {
        'core': {
            'id': 'core',
            'label': 'Ralfiz',
            'client_count': len(nodes),
            'project_count': total_projects,
            'billed': _money(total_billed),
            'billed_display': _inr(total_billed),
        },
        'nodes': nodes,
        'edges': edges,
        'legend': [
            {'label': 'Live work', 'hue': '#2fd4d4'},
            {'label': 'In play', 'hue': '#a78bd6'},
            {'label': 'Prospect', 'hue': '#7cc4e8'},
            {'label': 'Needs a human', 'hue': ATTENTION_HUE},
            {'label': 'Delivered', 'hue': '#4edea3'},
            {'label': 'No projects', 'hue': '#4a5c66'},
        ],
    }


#: How far ahead renewals surface. Beyond this they are not yet actionable
#: and would only crowd out the things that are.
RENEWAL_HORIZON_DAYS = 90


def get_dues_and_renewals(scope, horizon_days=RENEWAL_HORIZON_DAYS, limit=40):
    """Credentials expiring and AMC contracts falling due, soonest first.

    Two different models with one thing in common -- a date somebody has to act
    on -- merged into a single ordered list. Anything already overdue always
    sorts first, however far past.

    Credentials have no client FK; they reach a client through their project,
    which is nullable. A credential with no project still appears, because an
    unattached domain expiring is exactly the kind of thing that gets missed.
    """
    scope.require_business()
    today = timezone.localdate()
    cutoff = today + timedelta(days=int(horizon_days))
    items = []

    credentials = (
        Credential.objects
        .filter(is_active=True, expiry_date__isnull=False, expiry_date__lte=cutoff)
        .select_related('project', 'project__client')
        .order_by('expiry_date')
    )
    for cred in credentials:
        days = (cred.expiry_date - today).days
        items.append({
            'id': str(cred.id),
            'kind': 'credential',
            'kind_label': cred.get_credential_type_display(),
            'label': cred.name,
            'provider': cred.provider or '',
            'client': (
                cred.project.client.name
                if cred.project and cred.project.client else None
            ),
            'project': cred.project.name if cred.project else None,
            'due_date': _date(cred.expiry_date),
            'days': days,
            'overdue': days < 0,
            # Positive magnitude, so templates never have to strip a sign.
            'days_abs': abs(days),
            'amount': _money(cred.renewal_cost),
            'auto_renew': cred.auto_renew,
        })

    contracts = (
        AMCContract.objects
        .filter(status='active', next_due_date__isnull=False, next_due_date__lte=cutoff)
        .select_related('project', 'project__client')
        .order_by('next_due_date')
    )
    for amc in contracts:
        days = (amc.next_due_date - today).days
        items.append({
            'id': str(amc.id),
            'kind': 'amc',
            'kind_label': amc.get_contract_type_display(),
            'label': amc.project.name if amc.project else 'AMC contract',
            'provider': amc.get_billing_cycle_display(),
            'client': (
                amc.project.client.name
                if amc.project and amc.project.client else None
            ),
            'project': amc.project.name if amc.project else None,
            'due_date': _date(amc.next_due_date),
            'days': days,
            'overdue': days < 0,
            # Positive magnitude, so templates never have to strip a sign.
            'days_abs': abs(days),
            'amount': _money(amc.annual_amount),
            'auto_renew': amc.auto_renew,
        })

    items.sort(key=lambda i: i['days'])
    overdue = [i for i in items if i['overdue']]

    return {
        'count': len(items),
        'overdue_count': len(overdue),
        'horizon_days': int(horizon_days),
        'total_cost': round(sum(i['amount'] for i in items), 2),
        'items': items[:int(limit)],
    }


def get_dashboard_metrics(scope):
    """The headline numbers: money in, money owed, pipeline, delivery.

    Six figures chosen because each one can change what you do today. Every
    one is a real aggregate; none are derived from another.
    """
    scope.require_business()
    today = timezone.localdate()
    month_start = today.replace(day=1)

    income_month = Payment.objects.filter(
        payment_date__gte=month_start
    ).aggregate(s=Coalesce(Sum('amount'), _zero_money()))['s']

    expenses_month = Expense.objects.filter(
        date__gte=month_start
    ).aggregate(s=Coalesce(Sum('amount'), _zero_money()))['s']

    open_invoices = (
        Invoice.objects.filter(status__in=OPEN_INVOICE_STATUSES)
        .annotate(balance=F('total_amount') - F('amount_paid'))
        .filter(balance__gt=0)
    )
    outstanding = open_invoices.aggregate(
        s=Coalesce(Sum('balance'), _zero_money())
    )['s']
    overdue_count = open_invoices.filter(due_date__lt=today).count()

    open_leads = Lead.objects.exclude(status__in=CLOSED_LEAD_STATUSES).count()
    due_followups = Lead.objects.exclude(
        status__in=CLOSED_LEAD_STATUSES
    ).filter(next_follow_up_date__lte=today).count()

    active_projects = Project.objects.filter(
        status__in=ACTIVE_PROJECT_STATUSES
    ).count()
    attention_projects = (
        Project.objects.exclude(status__in=CLOSED_PROJECT_STATUSES)
        .filter(Q(status='on_hold') | Q(deadline__lt=today))
        .count()
    )

    def plural(n, one, many):
        return '%d %s' % (n, one if n == 1 else many)

    spent = _money(expenses_month)

    return [
        {
            'key': 'income',
            'label': 'Income this month',
            'value': _money(income_month),
            'display': '₹' + _inr(income_month),
            'format': 'money',
            'note': ('against ₹%s spent' % _inr(spent)) if spent else 'nothing spent yet',
            'href': '/payments/',
        },
        {
            'key': 'outstanding',
            'label': 'Owed to us',
            'value': _money(outstanding),
            'display': '₹' + _inr(outstanding),
            'format': 'money',
            'note': (plural(overdue_count, 'invoice overdue', 'invoices overdue')
                     if overdue_count else 'none overdue'),
            'alert': overdue_count > 0,
            'href': '/invoices/',
        },
        {
            'key': 'leads',
            'label': 'Open leads',
            'value': open_leads,
            'display': str(open_leads),
            'format': 'count',
            'note': ('%d need chasing' % due_followups) if due_followups else 'all up to date',
            'alert': due_followups > 0,
            'href': '/crm/leads/',
        },
        {
            'key': 'projects',
            'label': 'Active projects',
            'value': active_projects,
            'display': str(active_projects),
            'format': 'count',
            'note': (plural(attention_projects, 'needs a human', 'need a human')
                     if attention_projects else 'all on track'),
            'alert': attention_projects > 0,
            'href': '/projects/',
        },
    ]


# --------------------------------------------------------------------------
# The registry. The supervisor may call these and nothing else.
# --------------------------------------------------------------------------

TOOL_REGISTRY = {
    'find_entity': find_entity,
    'get_projects_needing_attention': get_projects_needing_attention,
    'count_projects_by_status': count_projects_by_status,
    'get_project_summary': get_project_summary,
    'get_team_for_project': get_team_for_project,
    'get_overdue_invoices': get_overdue_invoices,
    'get_outstanding_receivables': get_outstanding_receivables,
    'get_leads_needing_followup': get_leads_needing_followup,
    'get_lead_pipeline_summary': get_lead_pipeline_summary,
    'get_lead_quotes': get_lead_quotes,
    'get_pending_leave_requests': get_pending_leave_requests,
    'get_attendance_summary': get_attendance_summary,
    'get_dues_and_renewals': get_dues_and_renewals,
}
