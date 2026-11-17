"""Business Partner tools for the Claude connector (/mcp).

Joint projects run with a business partner (Saudi Arabia, money in SAR):
either a fixed amount for Ralfiz (plus AMC and server charges) or a profit
split. These tools read the same JointProject.money() figures the staff pages
and the partner portal show, and write payments, expenses and progress the
same way the staff forms do (INR converted at the rate given).

There is no API view for this app, so the tools use the ORM directly; the
connector itself is owner-only (connector.auth.can_use_connector).
"""
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.urls import reverse
from django.utils import timezone

from connector.dispatch import ToolError
from connector.tools import LIMIT, Tool, register, s_bool, s_date, s_int, s_num, s_str, s_uuid, to_decimal

from .models import CURRENCY_CHOICES, BusinessPartner, JointExpense, JointPayment, JointProject

CURRENCIES = [c for c, _ in CURRENCY_CHOICES]
KINDS = [k for k, _ in JointPayment.KIND_CHOICES]
PURPOSES = [k for k, _ in JointPayment.PURPOSE_CHOICES]
METHODS = [k for k, _ in JointPayment.METHOD_CHOICES]
STATUSES = [k for k, _ in JointProject.STATUS_CHOICES]
CENT = Decimal('0.01')


def _m(value):
    """Money as an exact string with two decimals."""
    return str(Decimal(value).quantize(CENT))


def _partner(partner_id):
    partner = BusinessPartner.objects.filter(pk=partner_id).first()
    if partner is None:
        raise ToolError('No business partner with that id. Use list_business_partners or search.')
    return partner


def _project(project_id):
    project = (JointProject.objects.select_related('partner')
               .prefetch_related('payments', 'expenses').filter(pk=project_id).first())
    if project is None:
        raise ToolError('No joint project with that id. Use get_business_partner or search.')
    return project


def _balance(cur, due_to_partner, fixed_only):
    """Who owes whom, in words. due_to_partner > 0 means Ralfiz owes the partner."""
    if due_to_partner > 0:
        return f'Ralfiz owes the partner {cur} {_m(due_to_partner)}' + (' (paid in advance)' if fixed_only else '')
    if due_to_partner < 0:
        return f'The partner owes Ralfiz {cur} {_m(-due_to_partner)}'
    return 'Settled: nobody owes anything'


def _staff_url(ctx, name, pk):
    return ctx.request.build_absolute_uri(reverse(name, args=[pk]))


def _project_summary(project):
    m = project.money()
    out = {
        'id': str(project.id),
        'title': project.title,
        'client': project.client_name,
        'status': project.get_status_display(),
        'progress_percent': project.progress,
        'deal': 'fixed amount for Ralfiz' if m['is_fixed'] else f'profit split {project.ratio_label}',
        'currency': project.currency,
        'balance': _balance(project.currency, m['due_to_partner'], m['is_fixed']),
    }
    if m['is_fixed']:
        out.update(agreed_amount=_m(m['fixed_agreed']), due_so_far=_m(m['fixed_due']),
                   paid_to_ralfiz=_m(m['fixed_paid']), still_to_pay=_m(m['fixed_balance']))
    else:
        out.update(contract_value=_m(m['contract_value']), received_from_client=_m(m['received']),
                   pending_from_client=_m(m['pending_from_client']), expenses=_m(m['expenses']),
                   profit=_m(m['profit']), partner_share=_m(m['partner_share']),
                   ralfiz_share=_m(m['ralfiz_share']))
    if project.deadline:
        out['deadline'] = project.deadline.isoformat()
    return out


def _converted(args, project, what):
    """(amount in project currency, paid currency, paid amount, rate) from the tool arguments."""
    cur = (args.get('currency') or project.currency).upper()
    if cur not in CURRENCIES:
        raise ToolError(f'currency must be one of {", ".join(CURRENCIES)}')
    paid = to_decimal(args['amount'], 'amount')
    if paid <= 0:
        raise ToolError('amount must be above zero')
    if cur == project.currency:
        return paid.quantize(CENT, ROUND_HALF_UP), cur, paid, Decimal('1')
    if args.get('exchange_rate') in (None, ''):
        raise ToolError(f'This {what} is in {cur} but the project is in {project.currency}: give exchange_rate '
                        f'({cur} per 1 {project.currency}, e.g. 23.45 INR per SAR). Ask the user for the rate '
                        f'they used; do not guess it.')
    rate = to_decimal(args['exchange_rate'], 'exchange_rate')
    if rate <= 0:
        raise ToolError('exchange_rate must be above zero')
    return (paid / rate).quantize(CENT, ROUND_HALF_UP), cur, paid, rate


def _day(args, key):
    return date.fromisoformat(args[key]) if args.get(key) else timezone.localdate()


# ---------------------------------------------------------------- read

def _list_partners(ctx, args):
    qs = BusinessPartner.objects.prefetch_related('projects__payments', 'projects__expenses').order_by('name')
    if not args.get('include_inactive'):
        qs = qs.filter(is_active=True)
    items = []
    for p in qs[:args.get('limit', 50)]:
        live = [j for j in p.projects.all() if j.status != 'cancelled']
        t = p.totals(live)
        items.append({
            'id': str(p.id), 'name': p.name, 'company': p.company_name, 'country': p.country,
            'currency': p.currency, 'projects': t['projects'], 'is_active': p.is_active,
            'has_portal_login': bool(p.user_id and p.user.is_active),
            'balance': _balance(p.currency, t['due_to_partner'], t['only_fixed']),
        })
    return {'count': len(items), 'items': items}


register(Tool(
    'list_business_partners', 'Business partners',
    'Business partners (companies Ralfiz runs joint projects with, mostly in Saudi Arabia) with '
    'how many joint projects each has and the overall balance: who owes whom, in the partner\'s '
    'currency (usually SAR). These are not the capital partners of Ralfiz.',
    _list_partners,
    {'include_inactive': s_bool('Also list partners marked inactive.'), 'limit': LIMIT},
))


def _get_partner(ctx, args):
    p = _partner(args['partner_id'])
    projects = list(p.projects.prefetch_related('payments', 'expenses').order_by('-created_at'))
    live = [j for j in projects if j.status != 'cancelled']
    t = p.totals(live)
    out = {
        'id': str(p.id), 'name': p.name, 'company': p.company_name, 'email': p.email, 'phone': p.phone,
        'whatsapp': p.whatsapp, 'country': p.country, 'city': p.city, 'currency': p.currency,
        'is_active': p.is_active, 'has_portal_login': bool(p.user_id and p.user.is_active),
        'portal_url': ctx.request.build_absolute_uri('/partner/'),
        'staff_page': _staff_url(ctx, 'bizpartners:detail', p.pk),
        'balance': _balance(p.currency, t['due_to_partner'], t['only_fixed']),
        'projects': [_project_summary(j) for j in projects],
    }
    if t['fixed_projects']:
        out['fixed_deals'] = {'due_so_far': _m(t['fixed_due']), 'paid_to_ralfiz': _m(t['fixed_paid']),
                              'still_to_pay': _m(t['fixed_balance'])}
    if t['split_projects']:
        out['split_deals'] = {'received_from_clients': _m(t['received']), 'expenses': _m(t['expenses']),
                              'profit': _m(t['profit']), 'partner_share': _m(t['partner_share']),
                              'ralfiz_share': _m(t['ralfiz_share'])}
    if p.notes:
        out['internal_notes'] = p.notes
    return out


register(Tool(
    'get_business_partner', 'Business partner details',
    'One business partner: contact details, portal login, every joint project with its deal and '
    'money, and the overall balance. Amounts are in the partner\'s currency (usually SAR).',
    _get_partner,
    {'partner_id': s_uuid('business partner')},
    required=('partner_id',),
))


def _get_project(ctx, args):
    project = _project(args['project_id'])
    m = project.money()
    out = _project_summary(project)
    out['partner'] = {'id': str(project.partner_id), 'name': project.partner.display_name}
    out['staff_page'] = _staff_url(ctx, 'bizpartners:project', project.pk)
    if m['is_fixed']:
        out['charges'] = [{'item': 'Project (agreed amount)', 'due_so_far': _m(m['fixed_agreed']),
                           'paid_for_it': _m(m['fixed_agreed_paid'])}] + [
            {'item': line['label'], 'terms': f"{project.currency} {_m(line['amount'])} {line['cycle_label'].lower()}",
             'starts': line['start'].isoformat() if line['start'] else None,
             'periods_due': line['periods'], 'due_so_far': _m(line['due']), 'paid_for_it': _m(line['paid']),
             'next_charge': line['next'].isoformat() if line['next'] else None}
            for line in m['recurring']]
    else:
        out['partner_share_percent'] = str(project.partner_share_percent)
    out['payments'] = [{
        'id': str(p.id), 'date': p.payment_date.isoformat(), 'who_paid_whom': p.get_kind_display(),
        'for': p.get_purpose_display(), 'amount': _m(p.amount), 'method': p.get_method_display(),
        'reference': p.reference,
        **({'paid_as': f'{p.paid_currency} {_m(p.paid_amount)} at {p.exchange_rate}'} if p.is_converted else {}),
    } for p in project.payments.order_by('-payment_date', '-created_at')]
    out['expenses'] = [{
        'id': str(e.id), 'date': e.expense_date.isoformat(), 'description': e.description,
        'paid_by': e.get_paid_by_display(), 'amount': _m(e.amount),
        **({'paid_as': f'{e.paid_currency} {_m(e.paid_amount)} at {e.exchange_rate}'} if e.is_converted else {}),
    } for e in project.expenses.order_by('-expense_date')]
    out['quotes'] = [{'number': q.quote_number, 'title': q.title, 'amount': _m(q.amount),
                      'status': q.get_status_display(), 'date': q.quote_date.isoformat()}
                     for q in project.quotes.order_by('-quote_date')]
    if project.notes:
        out['notes_shown_to_partner'] = project.notes
    if project.internal_notes:
        out['internal_notes'] = project.internal_notes
    return out


register(Tool(
    'get_joint_project', 'Joint project details',
    'One joint project with a business partner: the deal (fixed amount for Ralfiz, or profit split), '
    'what is charged and due so far (agreed amount, AMC and server charges), every payment (with the '
    'original INR amount and rate when converted), expenses, quotes and the balance.',
    _get_project,
    {'project_id': s_uuid('joint project')},
    required=('project_id',),
))


# ---------------------------------------------------------------- write

def _record_payment(ctx, args):
    project = _project(args['project_id'])
    amount, cur, paid, rate = _converted(args, project, 'payment')
    kind = args.get('kind') or ('partner_to_ralfiz' if project.is_fixed else 'client_to_ralfiz')
    pay = JointPayment.objects.create(
        project=project, kind=kind, purpose=args.get('purpose') or 'development',
        amount=amount, paid_currency=cur, paid_amount=paid, exchange_rate=rate,
        payment_date=_day(args, 'payment_date'), method=args.get('method') or 'bank_transfer',
        reference=args.get('reference', ''), notes=args.get('notes', ''))
    project = _project(project.pk)
    return {
        'recorded': {'id': str(pay.id), 'who_paid_whom': pay.get_kind_display(), 'for': pay.get_purpose_display(),
                     'amount': f'{project.currency} {_m(pay.amount)}', 'date': pay.payment_date.isoformat(),
                     **({'paid_as': f'{cur} {_m(paid)} at {rate} {cur} per {project.currency}'}
                        if cur != project.currency else {})},
        'project': _project_summary(project),
        'note': 'Remove or correct it on staff_page if this was wrong; it cannot be deleted from here.',
        'staff_page': _staff_url(ctx, 'bizpartners:project', project.pk),
    }


register(Tool(
    'record_joint_payment', 'Record joint project payment',
    'Record money moving on a joint project. kind: partner_to_ralfiz (the partner paid Ralfiz, the '
    'usual one on a fixed deal), client_to_ralfiz, client_to_partner, or ralfiz_to_partner. purpose: '
    'development (the agreed amount), amc, server or other. Give amount in the currency it was paid '
    'in; if that is not the project currency (e.g. INR on a SAR project) exchange_rate is required '
    '(INR per 1 SAR) and the SAR value is worked out from it. The partner sees this payment in their '
    'portal. Read back the project, who paid whom, amount, currency, rate and date and get a yes first.',
    _record_payment,
    {
        'project_id': s_uuid('joint project'),
        'amount': s_num('Amount actually paid, in `currency`.', exclusive_minimum=0),
        'currency': s_str('Currency it was paid in (default: the project currency, usually SAR).', enum=CURRENCIES),
        'exchange_rate': s_num('Units of `currency` per 1 of the project currency, e.g. 23.5 INR per SAR. '
                               'Required when currency differs from the project.', exclusive_minimum=0),
        'kind': s_str('Who paid whom (default partner_to_ralfiz on fixed deals, client_to_ralfiz on '
                      'split deals).', enum=KINDS),
        'purpose': s_str('What the payment is for (default development).', enum=PURPOSES),
        'payment_date': s_date('Date paid (default today).'),
        'method': s_str('Payment method (default bank_transfer).', enum=METHODS),
        'reference': s_str('Transaction or cheque number.'),
        'notes': s_str('Short note.'),
    },
    required=('project_id', 'amount'), write=True,
))


def _add_expense(ctx, args):
    project = _project(args['project_id'])
    amount, cur, paid, rate = _converted(args, project, 'expense')
    exp = JointExpense.objects.create(
        project=project, description=args['description'], amount=amount, paid_currency=cur, paid_amount=paid,
        exchange_rate=rate, paid_by=args.get('paid_by') or 'ralfiz', expense_date=_day(args, 'expense_date'))
    project = _project(project.pk)
    out = {
        'recorded': {'id': str(exp.id), 'description': exp.description, 'paid_by': exp.get_paid_by_display(),
                     'amount': f'{project.currency} {_m(exp.amount)}', 'date': exp.expense_date.isoformat(),
                     **({'paid_as': f'{cur} {_m(paid)} at {rate} {cur} per {project.currency}'}
                        if cur != project.currency else {})},
        'project': _project_summary(project),
        'staff_page': _staff_url(ctx, 'bizpartners:project', project.pk),
    }
    if project.is_fixed:
        out['note'] = ('This is a fixed-amount deal, so expenses do not change what the partner owes Ralfiz; '
                       'it is kept for the record only.')
    return out


register(Tool(
    'add_joint_expense', 'Add joint project expense',
    'Record an expense on a joint project (server, domain, freelancer, ads...), and who paid it '
    '(ralfiz or partner). On a profit-split project expenses come out of the profit before it is '
    'shared, and whoever paid gets it back. On a fixed-amount project it is for the record only. '
    'INR needs exchange_rate, as with record_joint_payment. Confirm with the user first.',
    _add_expense,
    {
        'project_id': s_uuid('joint project'),
        'description': s_str('What it was for, e.g. "Hosting for 1 year".'),
        'amount': s_num('Amount, in `currency`.', exclusive_minimum=0),
        'currency': s_str('Currency it was paid in (default: the project currency).', enum=CURRENCIES),
        'exchange_rate': s_num('Units of `currency` per 1 of the project currency. Required when '
                               'currency differs from the project.', exclusive_minimum=0),
        'paid_by': s_str('Who paid (default ralfiz).', enum=['ralfiz', 'partner']),
        'expense_date': s_date('Date (default today).'),
    },
    required=('project_id', 'description', 'amount'), write=True,
))


def _update_project(ctx, args):
    project = _project(args['project_id'])
    changed = []
    if args.get('status'):
        project.status = args['status']
        changed.append('status')
        if project.status == 'completed' and not project.completed_date:
            project.completed_date = timezone.localdate()
            changed.append('completed_date')
            if 'progress' not in args:
                project.progress = 100
                changed.append('progress')
    if args.get('progress') is not None:
        project.progress = args['progress']
        changed.append('progress')
    if args.get('deadline'):
        project.deadline = date.fromisoformat(args['deadline'])
        changed.append('deadline')
    if args.get('note_to_partner'):
        project.notes = args['note_to_partner']
        changed.append('notes')
    if not changed:
        raise ToolError('Nothing to change: give status, progress, deadline or note_to_partner.')
    project.save(update_fields=sorted(set(changed)) + ['updated_at'])
    return {'updated': sorted(set(changed)), 'project': _project_summary(project),
            'staff_page': _staff_url(ctx, 'bizpartners:project', project.pk)}


register(Tool(
    'update_joint_project', 'Update joint project',
    'Change a joint project\'s status, progress percent, deadline, or the note the partner sees in '
    'their portal. Marking it completed sets progress to 100 unless progress is given. The partner '
    'sees these changes.',
    _update_project,
    {
        'project_id': s_uuid('joint project'),
        'status': s_str('New status.', enum=STATUSES),
        'progress': s_int('Percent done, 0-100.', 0, 100),
        'deadline': s_date('New delivery deadline.'),
        'note_to_partner': s_str('Replaces the note shown to the partner on this project.'),
    },
    required=('project_id',), write=True,
))
