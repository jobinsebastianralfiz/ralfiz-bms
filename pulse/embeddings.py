"""Embedding providers for PULSE document search.

Anthropic has no embeddings endpoint, so this is a separate provider behind a
small interface. The default is Voyage AI over plain HTTPS (no SDK to pin);
swapping providers means writing one subclass and pointing get_provider() at
it. Tests inject their own provider, so nothing here is imported at
module-load time by the rest of the app.
"""

import logging
from abc import ABC, abstractmethod

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

VOYAGE_URL = 'https://api.voyageai.com/v1/embeddings'


class EmbeddingConfigurationError(RuntimeError):
    """Raised when document search is used without a configured provider."""


class EmbeddingProvider(ABC):
    """Turn text into vectors. Documents and queries embed differently on
    providers that support asymmetric retrieval, hence two methods."""

    @abstractmethod
    def embed_documents(self, texts):
        """list[str] -> list[list[float]], same order as the input."""

    @abstractmethod
    def embed_query(self, text):
        """str -> list[float]."""


class VoyageEmbeddingProvider(EmbeddingProvider):
    """Voyage AI REST API. Model comes from settings.PULSE_EMBEDDING_MODEL."""

    #: Voyage caps batch size; 128 is safely under every model's limit.
    BATCH = 128

    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def _post(self, texts, input_type):
        response = requests.post(
            VOYAGE_URL,
            json={'input': texts, 'model': self.model, 'input_type': input_type},
            headers={'Authorization': 'Bearer %s' % self.api_key},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        # Voyage returns data in input order, but sort by index anyway --
        # the contract matters more than the current behaviour.
        rows = sorted(payload['data'], key=lambda row: row['index'])
        return [row['embedding'] for row in rows]

    def embed_documents(self, texts):
        vectors = []
        for start in range(0, len(texts), self.BATCH):
            vectors.extend(self._post(texts[start:start + self.BATCH], 'document'))
        return vectors

    def embed_query(self, text):
        return self._post([text], 'query')[0]


def get_provider():
    """The configured provider, or a clear error naming the missing key."""
    api_key = getattr(settings, 'VOYAGE_API_KEY', '')
    if not api_key:
        raise EmbeddingConfigurationError(
            'VOYAGE_API_KEY is not set. PULSE document search cannot embed '
            'text until an embedding provider is configured.'
        )
    model = getattr(settings, 'PULSE_EMBEDDING_MODEL', 'voyage-4')
    return VoyageEmbeddingProvider(api_key=api_key, model=model)
