"""Qdrant implementation of :class:`VectorRepository`.

Uses the ``qdrant-client`` async API to store and search vector
embeddings.  Collections are created on first upsert if they do not
already exist.
"""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from app.core.config import Settings
from app.core.logging import get_logger
from app.storage.contracts import VectorRepository, VectorSearchResult

logger = get_logger("storage.qdrant")

# Default vector size — matches sentence-transformers/all-MiniLM-L6-v2.
_DEFAULT_VECTOR_SIZE = 384


class QdrantVectorRepository(VectorRepository):
    """Concrete vector repository backed by Qdrant."""

    def __init__(self, client: AsyncQdrantClient, vector_size: int = _DEFAULT_VECTOR_SIZE) -> None:
        self._client = client
        self._vector_size = vector_size
        self._ensured_collections: set[str] = set()

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    @classmethod
    async def create(cls, settings: Settings) -> "QdrantVectorRepository":
        """Construct a repository with an open Qdrant client."""
        client = AsyncQdrantClient(url=settings.qdrant_url)
        logger.info("Connected to Qdrant", extra={"data": {"url": settings.qdrant_url}})
        return cls(client)

    async def close(self) -> None:
        """Close the underlying client."""
        await self._client.close()
        logger.info("Qdrant client closed")

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    async def _ensure_collection(self, collection: str) -> None:
        """Create the collection if it does not yet exist."""
        if collection in self._ensured_collections:
            return

        collections = await self._client.get_collections()
        existing = {c.name for c in collections.collections}
        if collection not in existing:
            await self._client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=self._vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection", extra={"data": {"collection": collection}})

        self._ensured_collections.add(collection)

    # ------------------------------------------------------------------
    # Repository interface
    # ------------------------------------------------------------------

    async def upsert(
        self,
        collection: str,
        id: str,
        vector: list[float],
        payload: dict[str, object],
    ) -> None:
        """Insert or update a single vector point."""
        await self._ensure_collection(collection)
        await self._client.upsert(
            collection_name=collection,
            points=[
                PointStruct(
                    id=id,
                    vector=vector,
                    payload=payload,
                ),
            ],
        )

    async def search(
        self,
        collection: str,
        vector: list[float],
        *,
        limit: int = 10,
        score_threshold: float = 0.0,
    ) -> list[VectorSearchResult]:
        """Return nearest neighbours above the score threshold."""
        await self._ensure_collection(collection)
        results = await self._client.search(
            collection_name=collection,
            query_vector=vector,
            limit=limit,
            score_threshold=score_threshold,
        )
        return [
            VectorSearchResult(
                id=str(hit.id),
                score=hit.score,
                payload=dict(hit.payload) if hit.payload else {},
            )
            for hit in results
        ]
