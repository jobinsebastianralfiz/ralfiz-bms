"""Rewrite certificate bodies so the recipient's name prints large.

Dry run by default - it shows every before/after and changes nothing until
you pass --apply.

    python manage.py promote_certificate_names
    python manage.py promote_certificate_names --apply
    python manage.py promote_certificate_names --certificates --apply
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from employees.certificate_body_rewrite import name_still_in_body, rewrite_body
from employees.models import Certificate, CertificateTemplate


class Command(BaseCommand):
    help = "Strip the opening 'This is to certify that {student_name}' clause from certificate bodies."

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Write the changes. Without this the command only reports.')
        parser.add_argument('--certificates', action='store_true',
                            help='Also rewrite already-issued certificates, not just templates.')
        parser.add_argument('--include-published', action='store_true',
                            help='With --certificates, also rewrite published certificates '
                                 '(by default only drafts are touched).')

    def handle(self, *args, **options):
        apply_changes = options['apply']
        rows = [('CertificateTemplate', t) for t in CertificateTemplate.objects.order_by('certificate_type', 'name')]

        if options['certificates']:
            certs = Certificate.objects.order_by('-created_at')
            if not options['include_published']:
                certs = certs.filter(status='draft')
            rows += [('Certificate', c) for c in certs]

        if not rows:
            self.stdout.write(self.style.WARNING('No certificate templates found.'))
            return

        changed, skipped, warned = [], [], []

        for kind, obj in rows:
            label = f'{kind} · {obj}'
            new_body = rewrite_body(obj.body_text)
            if new_body == obj.body_text:
                skipped.append(label)
                continue

            self.stdout.write('')
            self.stdout.write(self.style.MIGRATE_HEADING(label))
            self.stdout.write(self.style.ERROR('  - ' + _first_line(obj.body_text)))
            self.stdout.write(self.style.SUCCESS('  + ' + _first_line(new_body)))

            if name_still_in_body(new_body):
                warned.append(label)
                self.stdout.write(self.style.WARNING(
                    '    {student_name} still appears later in this body, so the large '
                    'name will stay hidden. Remove it by hand.'))

            changed.append((obj, new_body))

        self.stdout.write('')
        self.stdout.write(f'{len(changed)} to rewrite, {len(skipped)} already fine or not safe to touch.')
        for label in skipped:
            self.stdout.write(f'  unchanged: {label}')

        if warned:
            self.stdout.write(self.style.WARNING(
                f'{len(warned)} still mention the name later in the body.'))

        if not changed:
            return

        if not apply_changes:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Dry run - nothing written. Re-run with --apply.'))
            return

        with transaction.atomic():
            for obj, new_body in changed:
                obj.body_text = new_body
                obj.save(update_fields=['body_text'])

        self.stdout.write(self.style.SUCCESS(f'Rewrote {len(changed)} bodies.'))


def _first_line(body):
    line = (body or '').replace('\r\n', '\n').split('\n')[0].strip()
    return line if len(line) <= 160 else line[:157] + '...'
