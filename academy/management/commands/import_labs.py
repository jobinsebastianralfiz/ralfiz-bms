import shutil
import tempfile
import zipfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from academy.importer import DEFAULT_PACKAGE_DIR, ImportFailed, run_import


class Command(BaseCommand):
    help = ('Import the Ralfiz Academy Labs content package (a directory or the .zip). '
            'Defaults to the copy bundled in academy/content. Safe to re-run.')

    def add_arguments(self, parser):
        parser.add_argument('package', nargs='?', default=str(DEFAULT_PACKAGE_DIR))
        parser.add_argument('--content-version', default='2026-09')
        parser.add_argument('--force', action='store_true', help='Import even if unchanged.')
        parser.add_argument('--dry-run', action='store_true', help='Validate and count, then roll back.')

    def handle(self, *args, **opts):
        package = Path(opts['package'])
        tmp = None
        try:
            if package.suffix == '.zip':
                tmp = tempfile.mkdtemp(prefix='labs-')
                with zipfile.ZipFile(package) as z:
                    z.extractall(tmp)
                package = Path(tmp)
            run_import(package, content_version=opts['content_version'], force=opts['force'],
                       dry_run=opts['dry_run'], log=self.stdout.write)
        except ImportFailed as e:
            raise CommandError(str(e))
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)
