"""Shut out login accounts left behind by earlier employee deletions.

Deleting an employee used to preserve their User account, so people who had
left could still sign in to the app and the staff portal. The delete view now
revokes the login itself; this cleans up the ones deleted before that.

An account is an orphan only when it has no role left at all -- no employee,
team member, intern or client profile -- and is not staff or a superuser.

    python manage.py revoke_orphan_logins
    python manage.py revoke_orphan_logins --apply
    python manage.py revoke_orphan_logins --username fathima.hiba --apply
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

PROFILES = ('employee_profile', 'team_profile', 'intern_profile', 'client_profile')


class Command(BaseCommand):
    help = 'Deactivate login accounts that no longer belong to anyone in the organisation.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Write the changes. Without this the command only reports.')
        parser.add_argument('--username', action='append', default=[],
                            help='Revoke this account by name, whatever profiles it still has. '
                                 'Repeatable. Staff and superusers are still refused.')

    def handle(self, *args, **options):
        from core.views import revoke_login

        if options['username']:
            targets = []
            for username in options['username']:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    raise CommandError(f'No user named "{username}".')
                if user.is_superuser or user.is_staff:
                    raise CommandError(f'"{username}" is staff or a superuser; refusing.')
                targets.append(user)
        else:
            targets = [u for u in User.objects.filter(is_active=True, is_staff=False, is_superuser=False)
                       if not any(hasattr(u, name) for name in PROFILES)]

        targets = [u for u in targets if u.is_active]

        if not targets:
            self.stdout.write(self.style.SUCCESS('No active orphan logins found.'))
            return

        for user in targets:
            self.stdout.write(f'  {user.username}  ({user.get_full_name() or "no name"}, '
                              f'{user.email or "no email"}, last login {user.last_login or "never"})')

        self.stdout.write('')
        self.stdout.write(f'{len(targets)} account(s) can still sign in.')

        if not options['apply']:
            self.stdout.write(self.style.WARNING('Dry run - nothing written. Re-run with --apply.'))
            return

        with transaction.atomic():
            for user in targets:
                revoke_login(user)

        self.stdout.write(self.style.SUCCESS(f'Revoked {len(targets)} login(s).'))
