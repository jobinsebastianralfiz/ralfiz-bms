"""Create (or reset) a Social-Hub-only login for a platform's app reviewer.

    python manage.py social_review_login                # meta_reviewer, new password
    python manage.py social_review_login --disable      # turn it off after the review

The login manages one empty test workspace and nothing else: the
SocialConfinementMiddleware keeps it out of every BMS page.
"""
import secrets

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from social.models import Membership, Workspace

WORKSPACE = 'App Review Test Client'


class Command(BaseCommand):
    help = "Create or reset a Social-Hub-only login for Meta/Google/LinkedIn app reviewers."

    def add_arguments(self, parser):
        parser.add_argument('--username', default='meta_reviewer')
        parser.add_argument('--disable', action='store_true', help='Deactivate the login.')

    def handle(self, *args, username, disable, **opts):
        if disable:
            n = User.objects.filter(username=username).update(is_active=False)
            self.stdout.write(f'{username}: {"deactivated" if n else "not found"}.')
            return
        user, created = User.objects.get_or_create(username=username, defaults={'first_name': 'App Reviewer'})
        if not created and (user.is_staff or user.is_superuser):
            self.stderr.write(f'{username} is a staff account; pick another --username.')
            return
        password = secrets.token_urlsafe(12)
        user.set_password(password)
        user.is_active = True
        user.save()
        ws, _ = Workspace.objects.get_or_create(name=WORKSPACE, defaults={'requires_approval': False,
                                                                          'color': '#3D8BFF'})
        Membership.objects.update_or_create(user=user, workspace=ws, defaults={'role': 'manager'})
        self.stdout.write(f'Workspace: {ws.name}\nUsername: {username}\nPassword: {password}')
