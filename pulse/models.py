"""PULSE document store for RAG.

These are the first models the pulse app owns. They deliberately touch the
rest of the schema at exactly one point -- a FK to core.Project -- so the
business models stay unmodified (Phase 2 rule).

Embeddings live in `DocumentChunk.embedding` as a JSON list of floats. That
is the canonical copy and works on every database. On PostgreSQL a second,
denormalised `embedding_vector` pgvector column is added by migration 0002
purely as a search index; it is written by ingestion and read by the pgvector
store, and losing it costs performance, not data.
"""

import uuid

from django.conf import settings
from django.db import models


class Document(models.Model):
    """One ingested source: a file or a pasted note, tied to a project."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'core.Project',
        on_delete=models.CASCADE,
        related_name='pulse_documents',
    )
    title = models.CharField(max_length=255)
    #: Where the text came from -- a filename, a URL, or 'pasted text'.
    source = models.CharField(max_length=255, blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='pulse_documents',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    """A retrievable slice of a document, with its embedding."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    #: 0-based position within the document; the citation shows index + 1.
    index = models.PositiveIntegerField()
    text = models.TextField()
    #: JSON list of floats. Canonical storage; see module docstring.
    embedding = models.JSONField()

    class Meta:
        ordering = ('document', 'index')
        constraints = [
            models.UniqueConstraint(
                fields=('document', 'index'),
                name='pulse_chunk_unique_per_document',
            ),
        ]

    def __str__(self):
        return '%s #%d' % (self.document.title, self.index + 1)
