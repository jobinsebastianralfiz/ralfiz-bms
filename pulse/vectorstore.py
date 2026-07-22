"""Vector search over DocumentChunk, one implementation per database.

The interface is a single method: search(query_vector, k, project_id=None)
returning [(chunk, score)] best-first, where score is cosine similarity in
[-1, 1].

  * NumpyVectorStore -- reads the JSON embeddings and ranks in Python.
    Correct everywhere (it is also the fallback on PostgreSQL if pgvector
    could not be installed); costs O(chunks) per query, fine at this
    project's document scale.
  * PgVectorStore -- ranks in the database via the pgvector `<=>` cosine
    distance operator over the denormalised embedding_vector column that
    migration 0002 adds on PostgreSQL only.

get_store() picks at runtime by connection vendor + column availability, so
callers never branch.
"""

import logging

from django.db import connection

from .models import DocumentChunk

logger = logging.getLogger(__name__)


class NumpyVectorStore:
    """Cosine ranking in Python over the canonical JSON embeddings."""

    def search(self, query_vector, k=5, project_id=None):
        import numpy as np

        chunks = DocumentChunk.objects.select_related('document', 'document__project')
        if project_id is not None:
            chunks = chunks.filter(document__project_id=project_id)
        chunks = list(chunks)
        if not chunks:
            return []

        matrix = np.array([chunk.embedding for chunk in chunks], dtype=np.float32)
        query = np.array(query_vector, dtype=np.float32)

        norms = np.linalg.norm(matrix, axis=1) * (np.linalg.norm(query) or 1.0)
        norms[norms == 0] = 1.0
        scores = matrix @ query / norms

        order = np.argsort(scores)[::-1][:k]
        return [(chunks[i], float(scores[i])) for i in order]


class PgVectorStore:
    """Cosine ranking in PostgreSQL via pgvector. Falls back nowhere --
    get_store() only returns this when the column exists."""

    def search(self, query_vector, k=5, project_id=None):
        literal = '[' + ','.join(repr(float(v)) for v in query_vector) + ']'
        sql = (
            'SELECT c.id, 1 - (c.embedding_vector <=> %s::vector) AS score '
            'FROM pulse_documentchunk c '
            'JOIN pulse_document d ON d.id = c.document_id '
            'WHERE c.embedding_vector IS NOT NULL '
        )
        params = [literal]
        if project_id is not None:
            sql += 'AND d.project_id = %s '
            params.append(str(project_id))
        sql += 'ORDER BY c.embedding_vector <=> %s::vector LIMIT %s'
        params.extend([literal, k])

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        by_id = DocumentChunk.objects.select_related(
            'document', 'document__project'
        ).in_bulk([row[0] for row in rows])
        return [
            (by_id[chunk_id], float(score))
            for chunk_id, score in rows
            if chunk_id in by_id
        ]


def pgvector_ready():
    """True when we are on PostgreSQL and migration 0002 got the column in."""
    if connection.vendor != 'postgresql':
        return False
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'pulse_documentchunk' "
            "AND column_name = 'embedding_vector'"
        )
        return cursor.fetchone() is not None


def get_store():
    if pgvector_ready():
        return PgVectorStore()
    return NumpyVectorStore()


def write_pgvector(chunks):
    """Denormalise embeddings into the pgvector column after ingestion.

    No-op away from PostgreSQL. A failure here (say, a dimension mismatch
    with the column) logs and moves on -- the canonical JSON embedding is
    already saved and the numpy store still serves queries.
    """
    if not pgvector_ready():
        return
    try:
        with connection.cursor() as cursor:
            for chunk in chunks:
                literal = '[' + ','.join(repr(float(v)) for v in chunk.embedding) + ']'
                cursor.execute(
                    'UPDATE pulse_documentchunk SET embedding_vector = %s::vector '
                    'WHERE id = %s',
                    [literal, str(chunk.id)],
                )
    except Exception:
        logger.exception(
            'pgvector denormalisation failed; numpy search still works.'
        )
