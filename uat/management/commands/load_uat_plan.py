import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from employees.models import Employee
from uat import services
from uat.models import UATCase, UATPlan, UATResult
from uat.web_views import load_cases


class Command(BaseCommand):
    help = ('Create a UAT plan from a JSON file and assign it. Example:\n'
            '  manage.py load_uat_plan uat/data/shop_manager_uat.json --due 2026-11-13 '
            '--owner "Intern 1=EMP014" --owner "Intern 2=EMP015" --owner "Intern 3=EMP016" --notify')

    def add_arguments(self, parser):
        parser.add_argument('path')
        parser.add_argument('--owner', action='append', default=[],
                            help='"<owner label in the file>=<EMP id>[,<EMP id>]"; testers of that section')
        parser.add_argument('--due', help='Finish-by date, YYYY-MM-DD')
        parser.add_argument('--notify', action='store_true', help='Send each tester a notification')
        parser.add_argument('--replace', action='store_true',
                            help='Rebuild an existing plan with the same name. Results already marked are kept '
                                 'for tests whose code is still in the file.')

    @transaction.atomic
    def handle(self, path, owner, due, notify, replace, **_):
        data = json.loads(Path(path).read_text())
        owner_map, everyone = {}, []
        for spec in owner:
            label, _, ids = spec.partition('=')
            emps = list(Employee.objects.filter(employee_id__in=[i.strip() for i in ids.split(',') if i.strip()]))
            if not emps:
                raise CommandError(f'No employees found for {spec!r}')
            owner_map[label.strip()] = emps
            everyone += [e for e in emps if e not in everyone]
        existing = UATPlan.objects.filter(name=data['name'])
        kept, old_due = [], None
        if existing.exists():
            if not replace:
                raise CommandError(f'A plan called {data["name"]!r} already exists (use --replace).')
            kept = [(r.case.code, r) for r in UATResult.objects.filter(case__section__plan__in=existing)
                    .select_related('case')]
            old_due = existing.first().due_date
            existing.delete()
        plan = UATPlan.objects.create(name=data['name'], product=data.get('product', ''),
                                      site_url=data.get('site_url', ''), instructions=data.get('instructions', ''),
                                      due_date=due or old_due)
        plan.testers.set(everyone)
        load_cases(plan, data, owner_map)
        restored = self._restore(plan, kept)
        if notify:
            services.notify_assigned(plan, everyone)
        self.stdout.write(f'{plan.name}: {plan.cases().count()} tests in {plan.sections.count()} sections, '
                          f'testers: {", ".join(e.full_name for e in everyone) or "none"} (id {plan.pk})')
        if kept:
            self.stdout.write(f'Kept {restored} of {len(kept)} earlier results.')

    @staticmethod
    def _restore(plan, kept):
        cases = {c.code: c for c in UATCase.objects.filter(section__plan=plan)}
        new = []
        for code, r in kept:
            if code in cases:
                r.pk, r.id, r.case = None, None, cases[code]
                new.append(r)
        UATResult.objects.bulk_create(new)
        return len(new)
