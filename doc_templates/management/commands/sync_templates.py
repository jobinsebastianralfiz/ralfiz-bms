from django.core.management.base import BaseCommand

from doc_templates.builtin import sync
from doc_templates.models import Template


class Command(BaseCommand):
    help = "Add new built-in templates. --force also resets existing ones (undoing admin edits to them)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, force=False, **options):
        created, updated = sync(Template, force=force)
        self.stdout.write(f"{created} created, {updated} updated.")
