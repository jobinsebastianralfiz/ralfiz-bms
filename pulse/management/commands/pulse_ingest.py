"""Ingest a text file into the PULSE document store from the shell.

Usage:
    python manage.py pulse_ingest path/to/notes.md --project "Hospital Website"
    python manage.py pulse_ingest spec.txt --project 7b0c... --title "API spec"

--project accepts a project UUID or a (unique) name fragment. The command
runs as the first superuser unless --user is given, and goes through the same
scope gate as the API.
"""

from pathlib import Path

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from core.models import Project
from pulse.embeddings import EmbeddingConfigurationError
from pulse.ingestion import TEXT_EXTENSIONS, ingest_document
from pulse.scoping import resolve_scope


class Command(BaseCommand):
    help = 'Chunk, embed and store a plain-text document for PULSE search.'

    def add_arguments(self, parser):
        parser.add_argument('path', help='Text file to ingest (%s)'
                                         % ', '.join(TEXT_EXTENSIONS))
        parser.add_argument('--project', required=True,
                            help='Project UUID or unique name fragment.')
        parser.add_argument('--title', default='',
                            help='Document title. Defaults to the file name.')
        parser.add_argument('--user', default='',
                            help='Username to ingest as. Defaults to the first superuser.')

    def _resolve_project(self, ref):
        try:
            project = Project.objects.filter(id=ref).first()
        except (ValueError, ValidationError):
            project = None
        if project:
            return project
        matches = list(Project.objects.filter(name__icontains=ref)[:3])
        if not matches:
            raise CommandError('No project matches %r.' % ref)
        if len(matches) > 1:
            raise CommandError(
                'Ambiguous project %r: %s' % (ref, ', '.join(p.name for p in matches))
            )
        return matches[0]

    def handle(self, *args, **options):
        path = Path(options['path'])
        if not path.exists():
            raise CommandError('No such file: %s' % path)
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            raise CommandError('Only plain-text files are supported: %s'
                               % ', '.join(TEXT_EXTENSIONS))

        if options['user']:
            user = User.objects.filter(username=options['user']).first()
            if user is None:
                raise CommandError('No user %r.' % options['user'])
        else:
            user = User.objects.filter(is_superuser=True).order_by('date_joined').first()
            if user is None:
                raise CommandError('No superuser to ingest as; pass --user.')

        project = self._resolve_project(options['project'])
        title = options['title'] or path.stem

        try:
            document = ingest_document(
                resolve_scope(user),
                project,
                title,
                path.read_text(encoding='utf-8', errors='replace'),
                source=path.name,
            )
        except EmbeddingConfigurationError as exc:
            raise CommandError(str(exc))
        except ValueError as exc:
            raise CommandError(str(exc))

        self.stdout.write(self.style.SUCCESS(
            'Ingested %r into %s: %d chunks (document %s)'
            % (title, project.name, document.chunks.count(), document.id)
        ))
