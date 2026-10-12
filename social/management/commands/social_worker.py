"""Publish due posts and keep accounts in sync.

Run as its own Railway service:  python manage.py social_worker
Or from cron once a minute:      python manage.py social_worker --once

Every minute it publishes what is due. Inboxes sync every 10 minutes,
metrics and token checks every 6 hours. Webhooks (Meta) deliver comments
and messages in between.
"""
import logging
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from social import services
from social.models import SocialAccount

log = logging.getLogger('social.worker')

PUBLISH_EVERY = 60
INBOX_EVERY = 10 * 60
METRICS_EVERY = 6 * 3600


class Command(BaseCommand):
    help = 'Publish scheduled social posts and sync inboxes, metrics and tokens.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true', help='Run every job once and exit.')

    def handle(self, *args, once=False, **options):
        last = {'inbox': 0.0, 'metrics': 0.0}
        while True:
            close_old_connections()
            now = time.monotonic()
            self.safely('publish', services.publish_due)
            if once or now - last['inbox'] >= INBOX_EVERY:
                last['inbox'] = now
                self.each_account('inbox', services.sync_inbox)
            if once or now - last['metrics'] >= METRICS_EVERY:
                last['metrics'] = now
                self.safely('tokens', services.refresh_tokens)
                self.each_account('insights', services.sync_insights)
                self.each_account('post metrics', services.sync_post_metrics)
            if once:
                return
            time.sleep(max(1, PUBLISH_EVERY - (time.monotonic() - now)))

    def safely(self, name, fn, *args):
        try:
            result = fn(*args)
            if result:
                self.stdout.write(f'{timezone.localtime():%H:%M:%S} {name}: {result}')
            return result
        except Exception:  # keep the loop alive; one bad job must not stop publishing
            log.exception('social worker job %s failed', name)

    def each_account(self, name, fn):
        for acc in SocialAccount.objects.filter(status__in=('active', 'expiring')):
            self.safely(f'{name} {acc.name}', fn, acc)
