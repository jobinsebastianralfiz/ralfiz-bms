"""Turn text into stored, embedded document chunks.

Chunking is paragraph-aware: paragraphs are packed into chunks of roughly
TARGET_CHARS, and a paragraph that is itself oversized is split on sentence
boundaries with OVERLAP_CHARS carried between pieces so no fact is stranded
on a cut line. Plain characters, not tokens -- at this scale the precision of
a tokenizer buys nothing.
"""

import re

from django.db import transaction

from .models import Document, DocumentChunk
from .vectorstore import write_pgvector

TARGET_CHARS = 1200
OVERLAP_CHARS = 150

#: Files the ingest endpoint/command will read as text.
TEXT_EXTENSIONS = ('.txt', '.md', '.markdown', '.rst', '.csv', '.log')


def chunk_text(text, target=TARGET_CHARS, overlap=OVERLAP_CHARS):
    """Split text into chunk strings. Empty input gives an empty list."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

    pieces = []
    for paragraph in paragraphs:
        if len(paragraph) <= target:
            pieces.append(paragraph)
            continue
        # Oversized paragraph: walk it in sentence steps with overlap.
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        current = ''
        for sentence in sentences:
            if current and len(current) + len(sentence) + 1 > target:
                pieces.append(current)
                current = current[-overlap:] + ' ' + sentence if overlap else sentence
            else:
                current = (current + ' ' + sentence).strip()
        if current:
            pieces.append(current)

    # Pack whole paragraphs together up to the target size.
    chunks = []
    current = ''
    for piece in pieces:
        if current and len(current) + len(piece) + 2 > target:
            chunks.append(current)
            current = piece
        else:
            current = (current + '\n\n' + piece).strip()
    if current:
        chunks.append(current)
    return chunks


@transaction.atomic
def ingest_document(scope, project, title, text, source='', provider=None):
    """Chunk, embed and store one document. Returns the Document.

    The scope gate is the same one every PULSE tool uses; ingestion writes,
    so it is unconditionally owner/partner-only.
    """
    scope.require_business()

    if provider is None:
        from .embeddings import get_provider
        provider = get_provider()

    texts = chunk_text(text)
    if not texts:
        raise ValueError('The document is empty; nothing to ingest.')

    vectors = provider.embed_documents(texts)

    document = Document.objects.create(
        project=project,
        title=title,
        source=source,
        created_by=scope.user,
    )
    chunks = DocumentChunk.objects.bulk_create([
        DocumentChunk(document=document, index=i, text=t, embedding=v)
        for i, (t, v) in enumerate(zip(texts, vectors))
    ])
    write_pgvector(chunks)
    return document
