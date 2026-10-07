"""The connector's tool catalogue.

Most tools are a thin description over one existing owner/admin/CRM API view
(see dispatch.call_view). Only `search` and `list_work_assignments` query the
ORM directly, because no existing endpoint answers them.

Choice lists are read from the models at import time so they cannot drift from
what the views accept.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Callable

from django.db.models import Q

from core.models import AMCContract, Client, DailyTask, Expense, Invoice, Project, Quote, TeamMember
from crm.models import Demo, FollowUp, Lead
from employees.models import Employee, Notification, WorkAssignment

from .dispatch import ToolError, call_view, redact, shape


def _choices(model, field_name):
    return [value for value, _ in model._meta.get_field(field_name).choices]


# ---------------------------------------------------------------- schemas

def s_str(description, enum=None, fmt=None):
    schema = {'type': 'string', 'description': description}
    if enum:
        schema['enum'] = list(enum)
    if fmt:
        schema['format'] = fmt
    return schema


def s_int(description, minimum=None, maximum=None):
    schema = {'type': 'integer', 'description': description}
    if minimum is not None:
        schema['minimum'] = minimum
    if maximum is not None:
        schema['maximum'] = maximum
    return schema


def s_bool(description):
    return {'type': 'boolean', 'description': description}


def s_uuid(what):
    return s_str(f'UUID of the {what}. Use `search` to find it from a name.', fmt='uuid')


def s_date(description):
    return s_str(f'{description} Format YYYY-MM-DD.', fmt='date')


LIMIT = s_int('Maximum items to return (default 50).', 1, 500)


# ---------------------------------------------------------------- registry

@dataclass
class Tool:
    name: str
    title: str
    description: str
    run: Callable
    params: dict = field(default_factory=dict)
    required: tuple = ()
    write: bool = False
    destructive: bool = False
    endpoint: tuple = ()  # (method, url name) for tools that wrap an API view

    def definition(self):
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'inputSchema': {
                'type': 'object',
                'properties': self.params,
                'required': list(self.required),
                'additionalProperties': False,
            },
            'annotations': {
                'title': self.title,
                'readOnlyHint': not self.write,
                'destructiveHint': self.destructive,
                'idempotentHint': not self.write,
                'openWorldHint': False,
            },
        }


TOOLS = {}


def register(tool):
    assert tool.name not in TOOLS, tool.name
    TOOLS[tool.name] = tool
    return tool


def _arg_pairs(spec):
    """'name' -> ('name', 'name'); ('arg', 'key') stays as is."""
    return [(item, item) if isinstance(item, str) else item for item in spec]


def view_tool(name, title, description, method, url_name, *, path=None, query=(), body=(),
              params=None, required=(), write=False, destructive=False,
              default_limit=None, item_fields=None):
    """Register a tool that calls one existing API view."""
    path = path or {}
    params = dict(params or {})
    if default_limit is not None:
        params['limit'] = LIMIT

    def run(ctx, args):
        kwargs = {kwarg: args[arg] for kwarg, arg in path.items()}
        q = {key: args.get(arg) for arg, key in _arg_pairs(query)}
        b = {key: args[arg] for arg, key in _arg_pairs(body) if arg in args}
        data = call_view(ctx, method, url_name, kwargs=kwargs, query=q, data=b)
        if default_limit is not None or item_fields:
            data = shape(data, args.get('limit', default_limit), item_fields)
        return data

    return register(Tool(name, title, description, run, params, tuple(required), write, destructive,
                         endpoint=(method, url_name)))


# ---------------------------------------------------------------- validation

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
UUID_RE = re.compile(r'^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$')
DATETIME_RE = re.compile(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}')


def validate_arguments(tool, args):
    """Check arguments against the tool's schema before any view runs.

    The views validate too, but several of them turn a malformed date or UUID
    into a 500. Catching it here gives Claude a message it can correct.
    """
    if args is None:
        args = {}
    if not isinstance(args, dict):
        raise ToolError('arguments must be an object')
    unknown = set(args) - set(tool.params)
    if unknown:
        raise ToolError(f'Unknown argument(s): {", ".join(sorted(unknown))}')
    missing = [name for name in tool.required if args.get(name) in (None, '')]
    if missing:
        raise ToolError(f'Missing required argument(s): {", ".join(missing)}')

    clean = {}
    for name, value in args.items():
        if value is None:
            continue
        schema = tool.params[name]
        kind = schema.get('type')
        if kind == 'integer':
            if isinstance(value, bool) or not isinstance(value, int):
                if isinstance(value, str) and value.strip().lstrip('-').isdigit():
                    value = int(value)
                else:
                    raise ToolError(f'{name} must be an integer')
            if 'minimum' in schema and value < schema['minimum']:
                raise ToolError(f'{name} must be at least {schema["minimum"]}')
            if 'maximum' in schema and value > schema['maximum']:
                raise ToolError(f'{name} must be at most {schema["maximum"]}')
        elif kind == 'boolean':
            if not isinstance(value, bool):
                raise ToolError(f'{name} must be true or false')
        elif kind == 'string':
            if not isinstance(value, str):
                value = str(value)
            value = value.strip()
            if 'enum' in schema and value not in schema['enum']:
                raise ToolError(f'{name} must be one of: {", ".join(schema["enum"])}')
            fmt = schema.get('format')
            if fmt == 'date' and value and not DATE_RE.match(value):
                raise ToolError(f'{name} must be a date in YYYY-MM-DD format')
            if fmt == 'uuid' and value and not UUID_RE.match(value):
                raise ToolError(f'{name} must be a UUID; use `search` to look it up by name')
            if fmt == 'date-time' and value and not DATETIME_RE.match(value):
                raise ToolError(f'{name} must be a date-time like 2026-10-08T15:30')
        elif kind == 'array':
            if not isinstance(value, list):
                raise ToolError(f'{name} must be a list')
        clean[name] = value
    return clean


def run_tool(ctx, name, args):
    tool = TOOLS.get(name)
    if tool is None:
        raise KeyError(name)
    clean = validate_arguments(tool, args)
    return redact(tool.run(ctx, clean))


# ======================================================================
# Overview
# ======================================================================

SEARCH_PER_TYPE = 8


def _search(ctx, args):
    term = args['query']
    if len(term) < 2:
        raise ToolError('query must be at least 2 characters')
    kinds = args.get('types') or list(SEARCH_TYPES)
    out = {}

    if 'clients' in kinds:
        out['clients'] = [
            {'id': str(c.id), 'name': c.name, 'company': c.company_name, 'phone': c.phone,
             'email': c.email, 'is_active': c.is_active}
            for c in Client.objects.filter(
                Q(name__icontains=term) | Q(company_name__icontains=term)
                | Q(email__icontains=term) | Q(phone__icontains=term)
            ).order_by('name')[:SEARCH_PER_TYPE]
        ]
    if 'projects' in kinds:
        out['projects'] = [
            {'id': str(p.id), 'name': p.name, 'client': p.client.name if p.client_id else '',
             'status': p.status}
            for p in Project.objects.select_related('client').filter(
                Q(name__icontains=term) | Q(client__name__icontains=term)
                | Q(client__company_name__icontains=term)
            ).order_by('-created_at')[:SEARCH_PER_TYPE]
        ]
    if 'leads' in kinds:
        out['leads'] = [
            {'id': l.id, 'contact_person': l.contact_person, 'company': l.company_name,
             'phone': l.phone, 'status': l.status}
            for l in Lead.objects.filter(
                Q(contact_person__icontains=term) | Q(company_name__icontains=term)
                | Q(phone__icontains=term) | Q(email__icontains=term)
            ).order_by('-created_at')[:SEARCH_PER_TYPE]
        ]
    if 'employees' in kinds:
        out['employees'] = [
            {'id': str(e.id), 'name': e.full_name, 'employee_id': e.employee_id,
             'role': e.role, 'designation': e.designation, 'status': e.status}
            for e in Employee.objects.select_related('user').filter(
                Q(user__first_name__icontains=term) | Q(user__last_name__icontains=term)
                | Q(user__username__icontains=term) | Q(employee_id__icontains=term)
                | Q(phone__icontains=term)
            ).order_by('user__first_name')[:SEARCH_PER_TYPE]
        ]
    if 'team_members' in kinds:
        out['team_members'] = [
            {'id': str(t.id), 'name': t.name, 'role': t.role, 'is_active': t.is_active}
            for t in TeamMember.objects.filter(name__icontains=term).order_by('name')[:SEARCH_PER_TYPE]
        ]
    if 'invoices' in kinds:
        # Invoice.objects is the GST-series manager; the no-GST ledger stays out.
        out['invoices'] = [
            {'id': str(i.id), 'invoice_number': i.invoice_number, 'title': i.title,
             'client': i.client.name if i.client_id else '', 'status': i.status,
             'total_amount': str(i.total_amount), 'amount_paid': str(i.amount_paid)}
            for i in Invoice.objects.select_related('client').filter(
                Q(invoice_number__icontains=term) | Q(title__icontains=term)
                | Q(client__name__icontains=term)
            ).order_by('-issue_date')[:SEARCH_PER_TYPE]
        ]
    if 'quotes' in kinds:
        out['quotes'] = [
            {'id': str(q.id), 'quote_number': q.quote_number, 'title': q.title,
             'client': q.client.name if q.client_id else '',
             'lead_id': q.lead_id, 'status': q.status, 'total_amount': str(q.total_amount)}
            for q in Quote.objects.select_related('client').filter(
                Q(quote_number__icontains=term) | Q(title__icontains=term)
                | Q(client__name__icontains=term) | Q(lead__company_name__icontains=term)
                | Q(lead__contact_person__icontains=term)
            ).order_by('-issue_date')[:SEARCH_PER_TYPE]
        ]
    return out


SEARCH_TYPES = ('clients', 'projects', 'leads', 'employees', 'team_members', 'invoices', 'quotes')

register(Tool(
    'search', 'Search the BMS',
    'Find clients, projects, leads, employees, team members, invoices and quotes by name, '
    'company, phone, email or number. Call this FIRST whenever the user names something '
    'instead of giving an ID, then pass the returned id to the detail tool. Leads have '
    'integer ids; everything else uses UUIDs.',
    _search,
    {
        'query': s_str('Text to look for, e.g. "ajith", "INRT-14", "9846".'),
        'types': {'type': 'array', 'items': {'type': 'string', 'enum': list(SEARCH_TYPES)},
                  'description': 'Limit the search to these record types. Omit to search all.'},
    },
    required=('query',),
))

view_tool(
    'get_dashboard', 'Business dashboard',
    'Headline numbers for the whole business: clients, active projects, revenue (total and '
    'this month), outstanding receivables, expenses and upcoming dues. Call for "how is the '
    'business doing", "revenue this month", or as a starting overview.',
    'get', 'employees:owner_dashboard',
)

view_tool(
    'get_financial_report', 'Financial report',
    'Twelve-month revenue, expense and profit trends with category breakdowns. Call for '
    'month-by-month comparisons, profit, or "how did we do last quarter".',
    'get', 'employees:owner_financial_report',
)

view_tool(
    'get_dues', 'Dues and renewals',
    'Everything coming due: unpaid invoices, AMC payments, and domain/SSL/hosting renewals, '
    'grouped by urgency. Call for "what do we need to collect or pay soon".',
    'get', 'employees:owner_dues',
)


# ======================================================================
# Clients & projects
# ======================================================================

view_tool(
    'list_clients', 'List clients',
    'All clients with their project counts and billing totals. Optional text search.',
    'get', 'employees:owner_clients', query=('search',),
    params={'search': s_str('Filter by client name, company or email.')},
    default_limit=50,
)

view_tool(
    'get_client', 'Client details',
    'One client in full: contact details, projects, invoices, payments and outstanding balance.',
    'get', 'employees:owner_client_detail', path={'pk': 'client_id'},
    params={'client_id': s_uuid('client')}, required=('client_id',),
)

PROJECT_STATUSES = _choices(Project, 'status')

view_tool(
    'list_projects', 'List projects',
    'Projects with client, status, budget and deadline. Filter by status or text.',
    'get', 'employees:owner_projects', query=('search', 'status'),
    params={
        'search': s_str('Filter by project or client name.'),
        'status': s_str('Only projects in this status.', PROJECT_STATUSES),
    },
    default_limit=50,
)

view_tool(
    'get_project', 'Project details',
    'One project in full: client, status, team, tasks, invoices, payments, renewals and AMC. '
    'Stored passwords and keys are never returned.',
    'get', 'employees:owner_project_detail', path={'pk': 'project_id'},
    params={'project_id': s_uuid('project')}, required=('project_id',),
)

view_tool(
    'get_project_board', 'Project board',
    'Projects grouped into status columns, like the kanban board in the app. Call for '
    '"what is in progress", "what is in review", or a pipeline view of delivery.',
    'get', 'employees:owner_project_board', query=('search',),
    params={'search': s_str('Filter by project or client name.')},
)

view_tool(
    'update_project_status', 'Change project status',
    'Move a project to a new status. Setting "completed" also stamps the completion date.',
    'post', 'employees:owner_project_status', path={'pk': 'project_id'}, body=('status',),
    params={
        'project_id': s_uuid('project'),
        'status': s_str('New status.', PROJECT_STATUSES),
    },
    required=('project_id', 'status'), write=True,
)


# ======================================================================
# Money (read)
# ======================================================================

view_tool(
    'list_invoices', 'List invoices',
    'GST invoices with client, totals, amount paid and status. Filter by status, client, '
    'GST filing status or text. Call for overdue invoices, unpaid invoices, or invoices for '
    'a client.',
    'get', 'employees:owner_invoices', query=('search', 'status', 'client_id', 'gst_filing_status'),
    params={
        'search': s_str('Filter by invoice number, title or client name.'),
        'status': s_str('Only invoices in this status.', _choices(Invoice, 'status')),
        'client_id': s_uuid('client'),
        'gst_filing_status': s_str('Only invoices with this GST filing state.',
                                   _choices(Invoice, 'gst_filing_status')),
    },
    default_limit=50,
)

view_tool(
    'get_invoice', 'Invoice details',
    'One invoice in full: line items, tax, payments received and balance due.',
    'get', 'employees:owner_invoice_detail', path={'pk': 'invoice_id'},
    params={'invoice_id': s_uuid('invoice')}, required=('invoice_id',),
)

view_tool(
    'list_quotes', 'List quotes',
    'Quotes with client or lead, totals and status. Filter by status, client or lead.',
    'get', 'employees:owner_quotes', query=('status', 'client_id', 'lead_id'),
    params={
        'status': s_str('Only quotes in this status.', _choices(Quote, 'status')),
        'client_id': s_uuid('client'),
        'lead_id': s_int('Numeric lead id.'),
    },
    default_limit=50,
)

view_tool(
    'get_quote', 'Quote details',
    'One quote in full: line items, totals, validity, payment terms and deliverables.',
    'get', 'employees:owner_quote_detail', path={'pk': 'quote_id'},
    params={'quote_id': s_uuid('quote')}, required=('quote_id',),
)

view_tool(
    'list_expenses', 'List expenses',
    'Business expenses with category, vendor and amount. Filter by date range, category or '
    'project.',
    'get', 'employees:owner_expenses', query=('start_date', 'end_date', 'category', 'project_id'),
    params={
        'start_date': s_date('From this date.'),
        'end_date': s_date('Up to this date.'),
        'category': s_str('Only this category.', _choices(Expense, 'category')),
        'project_id': s_uuid('project'),
    },
    default_limit=100,
)

view_tool(
    'list_bank_accounts', 'Bank accounts',
    'Bank and cash accounts with their current balances.',
    'get', 'employees:owner_accounts', query=('include_inactive',),
    params={'include_inactive': s_bool('Also list closed accounts.')},
)

view_tool(
    'list_transfers', 'Internal transfers',
    'Money moved between the business\'s own accounts. Filter by account or future-dated.',
    'get', 'employees:owner_transfers', query=(('account_id', 'account'), 'pending', 'limit'),
    params={
        'account_id': s_uuid('bank account'),
        'pending': s_bool('Only transfers dated in the future.'),
        'limit': LIMIT,
    },
)

view_tool(
    'list_amc_contracts', 'AMC contracts',
    'Annual maintenance, hosting, SEO and support contracts with amounts and next due dates.',
    'get', 'employees:owner_amc_list', query=('status', ('contract_type', 'type')),
    params={
        'status': s_str('Only contracts in this status.', _choices(AMCContract, 'status')),
        'contract_type': s_str('Only this contract type.', _choices(AMCContract, 'contract_type')),
    },
    default_limit=100,
)

view_tool(
    'get_amc_contract', 'AMC contract details',
    'One AMC contract in full with its payment history.',
    'get', 'employees:owner_amc_detail', path={'pk': 'amc_id'},
    params={'amc_id': s_uuid('AMC contract')}, required=('amc_id',),
)

view_tool(
    'list_expiring_renewals', 'Expiring renewals',
    'Domains, SSL certificates, hosting and other credentials that have expired or expire '
    'within 30 days, with renewal cost. Names and dates only -- never passwords.',
    'get', 'employees:owner_credentials_expiring',
)


# ======================================================================
# CRM
# ======================================================================

LEAD_STATUSES = _choices(Lead, 'status')
LEAD_FIELDS = ('id', 'contact_person', 'company_name', 'phone', 'email', 'status', 'source',
               'assigned_to_name', 'next_follow_up_date', 'closing_probability', 'client_name',
               'last_activity', 'created_at')

view_tool(
    'get_crm_dashboard', 'CRM dashboard',
    'Sales pipeline overview: lead counts by status, recent leads, upcoming demos and '
    'follow-ups.',
    'get', 'employees:crm_dashboard',
)

view_tool(
    'list_leads', 'List leads',
    'Sales leads with contact, status, source, owner and next follow-up date. Filter by '
    'status or source. Use get_lead for notes and history.',
    'get', 'employees:crm_leads', query=('status', 'source'),
    params={
        'status': s_str('Only leads in this status.', LEAD_STATUSES),
        'source': s_str('Only leads from this source.', _choices(Lead, 'source')),
    },
    default_limit=50, item_fields=LEAD_FIELDS,
)

view_tool(
    'get_lead', 'Lead details',
    'One lead in full: contact, status, notes, reference links, quotes and follow-ups.',
    'get', 'employees:crm_lead_detail', path={'pk': 'lead_id'},
    params={'lead_id': s_int('Numeric lead id.')}, required=('lead_id',),
)

view_tool(
    'get_lead_timeline', 'Lead timeline',
    'Everything that has happened on a lead in date order: status changes, notes, '
    'follow-ups and demos.',
    'get', 'employees:crm_lead_timeline', path={'lead_id': 'lead_id'},
    params={'lead_id': s_int('Numeric lead id.')}, required=('lead_id',),
)

view_tool(
    'list_upcoming_followups', 'Upcoming follow-ups',
    'Scheduled lead follow-ups split into today, overdue and upcoming. Call for "who should '
    'I call today" or "which follow-ups did we miss".',
    'get', 'employees:crm_upcoming_follow_ups',
)

view_tool(
    'list_demos', 'Product demos',
    'Scheduled and past product demos with their lead and outcome.',
    'get', 'employees:crm_demos', query=('status',),
    params={'status': s_str('Only demos in this status.', _choices(Demo, 'status'))},
    default_limit=50,
)


def _create_lead(ctx, args):
    if not args.get('allow_duplicate') and (args.get('phone') or args.get('email')):
        dup = call_view(ctx, 'post', 'employees:crm_lead_check_duplicate',
                        data={'phone': args.get('phone'), 'email': args.get('email')})
        if dup.get('has_duplicates'):
            existing = [{k: d.get(k) for k in ('id', 'contact_person', 'company_name', 'phone',
                                                'email', 'status')} for d in dup['duplicates']]
            raise ToolError(
                'A lead with this phone or email already exists: '
                f'{existing}. Update that lead instead, or call again with '
                'allow_duplicate=true if this really is a different lead.'
            )
    body = {k: v for k, v in args.items() if k != 'allow_duplicate'}
    return call_view(ctx, 'post', 'employees:crm_leads', data=body)


register(Tool(
    'create_lead', 'Create lead',
    'Add a new sales lead. Checks for an existing lead with the same phone or email first.',
    _create_lead,
    {
        'contact_person': s_str('Name of the person.'),
        'company_name': s_str('Company or business name.'),
        'phone': s_str('Phone number.'),
        'email': s_str('Email address.'),
        'source': s_str('Where the lead came from.', _choices(Lead, 'source')),
        'status': s_str('Starting status (default "new").', LEAD_STATUSES),
        'next_follow_up_date': s_date('When to follow up next.'),
        'closing_probability': s_int('Chance of closing, 0-100.', 0, 100),
        'notes': s_str('Background notes.'),
        'allow_duplicate': s_bool('Create even if a lead with this phone/email exists.'),
    },
    required=('contact_person',), write=True,
))

view_tool(
    'update_lead_status', 'Change lead status',
    'Move a lead to a new pipeline status. "lost" needs a lost_reason. Converted leads '
    'cannot be changed.',
    'post', 'employees:crm_lead_status', path={'pk': 'lead_id'},
    body=('status', 'lost_reason', 'next_follow_up_date', 'closing_probability'),
    params={
        'lead_id': s_int('Numeric lead id.'),
        'status': s_str('New status.', LEAD_STATUSES),
        'lost_reason': s_str('Why the lead was lost (when status is "lost").',
                             _choices(Lead, 'lost_reason')),
        'next_follow_up_date': s_date('When to follow up next.'),
        'closing_probability': s_int('Chance of closing, 0-100.', 0, 100),
    },
    required=('lead_id', 'status'), write=True,
)

view_tool(
    'add_lead_note', 'Add lead note',
    'Add a note to a lead, e.g. what was discussed on a call.',
    'post', 'employees:crm_lead_notes', path={'pk': 'lead_id'}, body=('note',),
    params={'lead_id': s_int('Numeric lead id.'), 'note': s_str('The note text.')},
    required=('lead_id', 'note'), write=True,
)

view_tool(
    'schedule_followup', 'Schedule follow-up',
    'Schedule a call, meeting, visit or message with a lead. Also sets the lead\'s next '
    'follow-up date.',
    'post', 'employees:crm_lead_follow_ups', path={'lead_id': 'lead_id'},
    body=('follow_up_type', 'scheduled_date', 'notes'),
    params={
        'lead_id': s_int('Numeric lead id.'),
        'follow_up_type': s_str('Kind of follow-up.', _choices(FollowUp, 'follow_up_type')),
        'scheduled_date': s_str('When, as YYYY-MM-DDTHH:MM in India time.', fmt='date-time'),
        'notes': s_str('What the follow-up is about.'),
    },
    required=('lead_id', 'follow_up_type', 'scheduled_date'), write=True,
)

view_tool(
    'update_followup', 'Update follow-up',
    'Mark a follow-up completed or missed, record its outcome, or reschedule it. Follow-up '
    'ids come from get_lead or list_upcoming_followups.',
    'patch', 'employees:crm_follow_up_detail', path={'follow_up_id': 'follow_up_id'},
    body=('status', 'outcome', 'scheduled_date', 'notes'),
    params={
        'follow_up_id': s_int('Numeric follow-up id.'),
        'status': s_str('New status.', _choices(FollowUp, 'status')),
        'outcome': s_str('What happened.'),
        'scheduled_date': s_str('New time when rescheduling, YYYY-MM-DDTHH:MM.', fmt='date-time'),
        'notes': s_str('Updated notes.'),
    },
    required=('follow_up_id',), write=True,
)


# ======================================================================
# People
# ======================================================================

view_tool(
    'list_employees', 'List employees',
    'Employees and interns with role, department, designation and status.',
    'get', 'employees:owner_employees', query=('search', 'role', 'department', 'status'),
    params={
        'search': s_str('Filter by name or employee id.'),
        'role': s_str('Only this role.', _choices(Employee, 'role')),
        'department': s_str('Only this department.', _choices(Employee, 'department')),
        'status': s_str('Only this status.', _choices(Employee, 'status')),
    },
    default_limit=100,
)

view_tool(
    'get_employee', 'Employee details',
    'One employee in full: profile, recent attendance, leave balances and current work.',
    'get', 'employees:owner_employee_detail', path={'pk': 'employee_id'},
    params={'employee_id': s_uuid('employee')}, required=('employee_id',),
)

view_tool(
    'get_attendance', 'Attendance',
    'Per-employee attendance records (check-in/out times, late, remote) for a date range. '
    'Defaults to this month so far. For a single day pass the same start and end date.',
    'get', 'employees:owner_attendance', query=('start_date', 'end_date', 'employee_id'),
    params={
        'start_date': s_date('From this date (default: 1st of this month).'),
        'end_date': s_date('Up to this date (default: today).'),
        'employee_id': s_uuid('employee'),
    },
)

view_tool(
    'get_attendance_report', 'Monthly attendance report',
    'Attendance summary for one month: present, absent and late counts per person.',
    'get', 'employees:admin_attendance_report', query=('month', 'year', 'employee_id'),
    params={
        'month': s_int('Month number 1-12 (default: this month).', 1, 12),
        'year': s_int('Year (default: this year).', 2020, 2100),
        'employee_id': s_uuid('employee'),
    },
)

view_tool(
    'list_pending_leave_requests', 'Pending leave requests',
    'Leave requests waiting for approval, with dates, type and reason.',
    'get', 'employees:admin_leaves',
    default_limit=100,
)

view_tool(
    'review_leave_request', 'Approve or reject leave',
    'Approve or reject a pending leave request. The employee gets a notification.',
    'post', 'employees:admin_leave_review', path={'pk': 'leave_request_id'},
    body=('action', 'notes'),
    params={
        'leave_request_id': s_uuid('leave request (from list_pending_leave_requests)'),
        'action': s_str('Decision.', ['approve', 'reject']),
        'notes': s_str('Note to the employee.'),
    },
    required=('leave_request_id', 'action'), write=True,
)


def _list_work_assignments(ctx, args):
    from employees.serializers import WorkAssignmentSerializer

    qs = WorkAssignment.objects.prefetch_related('assigned_to__user').select_related(
        'project', 'assigned_by').order_by('-created_at')
    if args.get('status'):
        qs = qs.filter(status=args['status'])
    else:
        qs = qs.exclude(status__in=('completed', 'cancelled'))
    if args.get('employee_id'):
        qs = qs.filter(assigned_to=args['employee_id'])
    if args.get('overdue_only'):
        qs = qs.filter(due_date__lt=date.today()).exclude(status__in=('completed', 'cancelled'))
    limit = args.get('limit', 50)
    total = qs.count()
    items = WorkAssignmentSerializer(qs[:limit], many=True).data
    for item in items:
        item.pop('updates', None)
    return {'count': total, 'returned': len(items), 'items': items}


register(Tool(
    'list_work_assignments', 'Work assignments',
    'Work assigned to employees and interns. By default only open work (not completed or '
    'cancelled).',
    _list_work_assignments,
    {
        'status': s_str('Only this status.', _choices(WorkAssignment, 'status')),
        'employee_id': s_uuid('employee'),
        'overdue_only': s_bool('Only open work past its due date.'),
        'limit': LIMIT,
    },
))

view_tool(
    'assign_work', 'Assign work',
    'Assign a piece of work to one or more employees or interns. Each gets a notification.',
    'post', 'employees:admin_work_assign',
    body=('employee_ids', 'title', 'description', 'priority', 'due_date', 'project_id'),
    params={
        'employee_ids': {'type': 'array', 'items': s_uuid('employee'),
                         'description': 'Employee UUIDs to assign to.'},
        'title': s_str('Short title.'),
        'description': s_str('What needs doing.'),
        'priority': s_str('Priority (default medium).', _choices(WorkAssignment, 'priority')),
        'due_date': s_date('Due date.'),
        'project_id': s_uuid('project'),
    },
    required=('employee_ids', 'title'), write=True,
)

view_tool(
    'list_team_members', 'Team members',
    'Delivery team members (developers, designers...). Daily tasks are assigned to these ids, '
    'not employee ids.',
    'get', 'employees:owner_team_members',
)

DAILY_TASK_STATUSES = _choices(DailyTask, 'status')

view_tool(
    'list_daily_tasks', 'Daily tasks',
    'The day\'s task list. Viewing today also shows unfinished tasks carried over from '
    'earlier days.',
    'get', 'employees:owner_daily_tasks', query=('date', 'assigned_to', 'status'),
    params={
        'date': s_date('Day to show (default today).'),
        'assigned_to': s_uuid('team member (from list_team_members)'),
        'status': s_str('Only this status.', DAILY_TASK_STATUSES),
    },
)

view_tool(
    'add_daily_task', 'Add daily task',
    'Add a task to a day\'s task list.',
    'post', 'employees:owner_daily_tasks',
    body=('title', 'description', 'date', 'priority', 'assigned_to', ('project_id', 'project')),
    params={
        'title': s_str('Task title.'),
        'description': s_str('Details.'),
        'date': s_date('Day (default today).'),
        'priority': s_str('Priority (default medium).', _choices(DailyTask, 'priority')),
        'assigned_to': s_uuid('team member (from list_team_members)'),
        'project_id': s_uuid('project'),
    },
    required=('title',), write=True,
)

view_tool(
    'update_daily_task', 'Update daily task',
    'Change a daily task\'s status, title, priority, assignee or date.',
    'patch', 'employees:owner_daily_task_detail', path={'pk': 'task_id'},
    body=('status', 'title', 'description', 'priority', 'assigned_to', 'date'),
    params={
        'task_id': s_uuid('daily task'),
        'status': s_str('New status.', DAILY_TASK_STATUSES),
        'title': s_str('New title.'),
        'description': s_str('New details.'),
        'priority': s_str('New priority.', _choices(DailyTask, 'priority')),
        'assigned_to': s_uuid('team member'),
        'date': s_date('Move to this day.'),
    },
    required=('task_id',), write=True,
)

view_tool(
    'list_daily_reports', 'Daily status reports',
    'What each person did, learned and was blocked on, newest first. Filter by date range, '
    'employee, or only reports that flag a blocker.',
    'get', 'employees:admin_daily_reports',
    query=(('start_date', 'start'), ('end_date', 'end'), ('employee_id', 'employee'),
           'blockers', 'page'),
    params={
        'start_date': s_date('From this date.'),
        'end_date': s_date('Up to this date.'),
        'employee_id': s_uuid('employee'),
        'blockers': s_bool('Only reports that mention a blocker.'),
        'page': s_int('Page number for older reports.', 1),
    },
)

view_tool(
    'list_missing_daily_reports', 'Missing daily reports',
    'Active staff who have not filed a daily report for a day.',
    'get', 'employees:admin_daily_reports_missing', query=('date',),
    params={'date': s_date('Day to check (default today).')},
)

view_tool(
    'send_notification', 'Send staff notification',
    'Send a push notification to one employee, or to every active employee when employee_id '
    'is omitted.',
    'post', 'employees:admin_send_notification',
    body=('title', 'body', 'employee_id', ('notification_type', 'type')),
    params={
        'title': s_str('Notification title.'),
        'body': s_str('Message text.'),
        'employee_id': s_uuid('employee; omit to message everyone'),
        'notification_type': s_str('Category (default general).',
                                   _choices(Notification, 'notification_type')),
    },
    required=('title', 'body'), write=True,
)
