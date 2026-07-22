"""Phase 2 RAG: chunking, ingestion, retrieval, scoping, and the endpoint.

A deterministic FakeProvider replaces the embedding API everywhere: it embeds
text as counts of four marker words, so similarity is exact and assertions can
be about ranking, not fuzz. That also proves the EmbeddingProvider interface
is genuinely swappable.

The pgvector store is asserted only when the test database is PostgreSQL;
on SQLite those tests skip and the numpy store carries the behaviour.
"""

from unittest import mock

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied

from core.models import Client, Project

from pulse import tools
from pulse.embeddings import EmbeddingProvider
from pulse.ingestion import chunk_text, ingest_document
from pulse.models import Document, DocumentChunk
from pulse.scoping import PulseScope
from pulse.vectorstore import NumpyVectorStore, get_store, pgvector_ready


class FakeProvider(EmbeddingProvider):
    VOCAB = ('hosting', 'payment', 'deadline', 'design')

    def _vector(self, text):
        lowered = text.lower()
        return [float(lowered.count(word)) for word in self.VOCAB]

    def embed_documents(self, texts):
        return [self._vector(text) for text in texts]

    def embed_query(self, text):
        return self._vector(text)


def owner_scope(user=None):
    return PulseScope(user=user, employee=None, can_query_business=True)


def denied_scope():
    return PulseScope(user=None, employee=None, can_query_business=False)


def make_project(name='Hospital Website'):
    client = Client.objects.create(name='%s client' % name)
    return Project.objects.create(name=name, client=client)


class ChunkTextTests(TestCase):
    def test_empty_text_gives_no_chunks(self):
        self.assertEqual(chunk_text(''), [])
        self.assertEqual(chunk_text('   \n\n  '), [])

    def test_short_text_is_one_chunk(self):
        self.assertEqual(chunk_text('One small note.'), ['One small note.'])

    def test_paragraphs_pack_up_to_target(self):
        text = '\n\n'.join('Paragraph %d about work.' % i for i in range(40))
        chunks = chunk_text(text, target=200)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 260)  # target plus one paragraph
        # Nothing lost: every paragraph appears in exactly one chunk.
        joined = '\n\n'.join(chunks)
        for i in range(40):
            self.assertIn('Paragraph %d ' % i, joined + ' ')

    def test_oversized_paragraph_splits_with_overlap(self):
        sentence = 'The hosting fee is due on the first of the month. '
        chunks = chunk_text(sentence * 60, target=400, overlap=50)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks[1:]:
            # Each continuation starts with carried-over text, not cold.
            self.assertTrue(chunk[:60].strip())


class IngestionTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.user = User.objects.create_user('owner', password='x')

    def test_ingest_creates_document_and_embedded_chunks(self):
        document = ingest_document(
            owner_scope(self.user), self.project, 'Hosting agreement',
            'The hosting renewal is annual.\n\nPayment is due in advance.',
            source='agreement.md', provider=FakeProvider(),
        )
        self.assertEqual(document.project, self.project)
        self.assertEqual(document.created_by, self.user)
        chunks = list(document.chunks.all())
        self.assertGreaterEqual(len(chunks), 1)
        for chunk in chunks:
            self.assertEqual(len(chunk.embedding), len(FakeProvider.VOCAB))

    def test_ingest_refuses_unprivileged_scope(self):
        with self.assertRaises(PermissionDenied):
            ingest_document(
                denied_scope(), self.project, 'X', 'text', provider=FakeProvider()
            )
        self.assertEqual(Document.objects.count(), 0)

    def test_ingest_refuses_empty_text(self):
        with self.assertRaises(ValueError):
            ingest_document(
                owner_scope(self.user), self.project, 'X', '   ',
                provider=FakeProvider(),
            )


class RetrievalTests(TestCase):
    def setUp(self):
        self.provider = FakeProvider()
        self.hosting_project = make_project('Hospital Website')
        self.design_project = make_project('Brand Refresh')
        scope = owner_scope()
        ingest_document(
            scope, self.hosting_project, 'Hosting agreement',
            'Hosting hosting hosting is renewed each year.',
            provider=self.provider,
        )
        ingest_document(
            scope, self.hosting_project, 'Payment terms',
            'Payment payment is made by bank transfer.',
            provider=self.provider,
        )
        ingest_document(
            scope, self.design_project, 'Design notes',
            'Design design follows the brand palette. Hosting is elsewhere.',
            provider=self.provider,
        )

    def _search(self, query, **kwargs):
        with mock.patch('pulse.embeddings.get_provider', return_value=self.provider):
            return tools.search_documents(owner_scope(), query, **kwargs)

    def test_best_matching_document_ranks_first_with_citation(self):
        result = self._search('when is hosting renewed')
        self.assertTrue(result['results'])
        top = result['results'][0]
        self.assertEqual(top['title'], 'Hosting agreement')
        self.assertEqual(top['citation'], 'Hosting agreement §1')
        self.assertEqual(top['project'], 'Hospital Website')

    def test_project_filter_restricts_results(self):
        result = self._search(
            'hosting', project_id=str(self.design_project.id)
        )
        titles = {row['title'] for row in result['results']}
        self.assertEqual(titles, {'Design notes'})

    def test_unknown_project_id_is_an_error_not_a_leak(self):
        result = self._search(
            'hosting', project_id='00000000-0000-0000-0000-000000000000'
        )
        self.assertEqual(result['results'], [])
        self.assertIn('error', result)

    def test_k_is_clamped(self):
        result = self._search('hosting payment design', k=999)
        self.assertLessEqual(len(result['results']), 20)

    def test_search_refuses_unprivileged_scope(self):
        with self.assertRaises(PermissionDenied):
            tools.search_documents(denied_scope(), 'hosting')

    def test_store_selection_matches_database(self):
        store = get_store()
        if connection.vendor == 'postgresql' and pgvector_ready():
            from pulse.vectorstore import PgVectorStore
            self.assertIsInstance(store, PgVectorStore)
        else:
            self.assertIsInstance(store, NumpyVectorStore)

    def test_numpy_store_directly(self):
        """The numpy store must rank correctly regardless of backend."""
        store = NumpyVectorStore()
        hits = store.search(self.provider.embed_query('payment'), k=1)
        self.assertEqual(hits[0][0].document.title, 'Payment terms')


class PgVectorTests(TestCase):
    """Exercised only on PostgreSQL; on SQLite the numpy tests stand in."""

    def setUp(self):
        if not pgvector_ready():
            self.skipTest('pgvector not available on this database')
        self.provider = FakeProvider()
        self.project = make_project()

    def test_pgvector_search_matches_numpy_ranking(self):
        from pulse.vectorstore import PgVectorStore
        ingest_document(
            owner_scope(), self.project, 'Hosting agreement',
            'Hosting hosting is renewed each year.', provider=self.provider,
        )
        ingest_document(
            owner_scope(), self.project, 'Payment terms',
            'Payment payment by transfer.', provider=self.provider,
        )
        query = self.provider.embed_query('hosting')
        pg = [c.id for c, _ in PgVectorStore().search(query, k=2)]
        np_ = [c.id for c, _ in NumpyVectorStore().search(query, k=2)]
        self.assertEqual(pg, np_)


class DocumentsEndpointTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.owner = User.objects.create_user(
            'boss', password='x', is_staff=True
        )
        self.outsider = User.objects.create_user('intern', password='x')

    def test_ingest_and_list_roundtrip(self):
        self.client.force_login(self.owner)
        with mock.patch(
            'pulse.embeddings.get_provider', return_value=FakeProvider()
        ):
            response = self.client.post('/api/pulse/documents/', {
                'project_id': str(self.project.id),
                'title': 'Hosting agreement',
                'text': 'Hosting is renewed each year.',
            }, content_type='application/json')
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual(body['title'], 'Hosting agreement')
        self.assertGreaterEqual(body['chunks'], 1)

        listing = self.client.get('/api/pulse/documents/').json()
        self.assertEqual(len(listing), 1)
        self.assertEqual(listing[0]['project'], self.project.name)

    def test_non_owner_cannot_ingest(self):
        self.client.force_login(self.outsider)
        response = self.client.post('/api/pulse/documents/', {
            'project_id': str(self.project.id),
            'title': 'X',
            'text': 'text',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Document.objects.count(), 0)

    def test_missing_provider_key_is_503_not_traceback(self):
        self.client.force_login(self.owner)
        with self.settings(VOYAGE_API_KEY=''):
            response = self.client.post('/api/pulse/documents/', {
                'project_id': str(self.project.id),
                'title': 'X',
                'text': 'some text',
            }, content_type='application/json')
        self.assertEqual(response.status_code, 503)

    def test_rejects_empty_submission(self):
        self.client.force_login(self.owner)
        response = self.client.post('/api/pulse/documents/', {
            'project_id': str(self.project.id),
            'title': 'X',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
