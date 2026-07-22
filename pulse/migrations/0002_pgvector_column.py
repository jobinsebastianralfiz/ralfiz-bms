"""PostgreSQL-only: pgvector search column over DocumentChunk.

On SQLite (dev) this migration is a recorded no-op -- the numpy store ranks
the canonical JSON embeddings instead. On PostgreSQL it enables the pgvector
extension, adds the denormalised embedding_vector column, and indexes it for
cosine search.

Prod note (Railway): the database user must be allowed to CREATE EXTENSION
vector. Railway's Postgres images ship pgvector; if the CREATE EXTENSION
call is ever refused, this migration logs and completes, and PULSE document
search keeps working through the numpy store -- slower, not broken.

The vector dimension comes from settings.PULSE_EMBEDDING_DIM and must match
the embedding model's output (voyage models: 1024). Changing models to a
different dimension means dropping and re-adding the column and re-ingesting.
"""

import logging

from django.conf import settings
from django.db import migrations

logger = logging.getLogger(__name__)


def add_pgvector(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    dim = int(getattr(settings, 'PULSE_EMBEDDING_DIM', 1024))
    try:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute('CREATE EXTENSION IF NOT EXISTS vector')
            cursor.execute(
                'ALTER TABLE pulse_documentchunk '
                'ADD COLUMN IF NOT EXISTS embedding_vector vector(%d)' % dim
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS pulse_chunk_embedding_hnsw '
                'ON pulse_documentchunk '
                'USING hnsw (embedding_vector vector_cosine_ops)'
            )
    except Exception:
        logger.exception(
            'pgvector setup failed; PULSE document search will use the '
            'numpy store on this database.'
        )


def drop_pgvector(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            'ALTER TABLE pulse_documentchunk DROP COLUMN IF EXISTS embedding_vector'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('pulse', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_pgvector, drop_pgvector),
    ]
