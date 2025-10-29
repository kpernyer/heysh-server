"""Weaviate client."""

import os
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

import weaviate
from weaviate.classes.init import Auth


class WeaviateClient:
    """Weaviate vector database client."""

    def __init__(self, url: str, api_key: str | None = None) -> None:
        """Initialize Weaviate client."""
        if api_key:
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=url,
                auth_credentials=Auth.api_key(api_key),
            )
        else:
            # Parse URL to extract host and port
            parsed = urlparse(url)
            host = parsed.hostname or "localhost"
            # Use port from URL, or default based on scheme (http=80, https=443, other=8080)
            if parsed.port:
                port = parsed.port
            elif parsed.scheme == "https":
                port = 443
            elif parsed.scheme == "http":
                port = 80
            else:
                port = 8080
            self.client = weaviate.connect_to_local(
                host=host, port=port, skip_init_checks=True
            )

    async def search(
        self,
        collection: str,
        query: str,
        filters: dict[str, Any],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Vector search for documents.

        Args:
            collection: Collection name
            query: Search query
            filters: Filter conditions
            limit: Max results

        Returns:
            List of matching documents

        """
        coll = self.client.collections.get(collection)

        # Build filter expression
        filter_expr = None
        if "domain_id" in filters:
            filter_expr = {
                "path": ["domain_id"],
                "operator": "Equal",
                "valueText": filters["domain_id"],
            }

        response = coll.query.near_text(
            query=query,
            limit=limit,
            return_metadata=["distance"],
            filters=filter_expr,
        )

        results = []
        for obj in response.objects:
            results.append(
                {
                    "document_id": obj.properties.get("document_id"),
                    "text": obj.properties.get("text"),
                    "distance": obj.metadata.distance if obj.metadata else None,
                    "properties": obj.properties,
                }
            )

        return results

    async def index_document(
        self,
        collection: str,
        document_id: str,
        domain_id: str,
        text: str,
        chunks: list[str],
        embeddings: dict[str, list[float]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Index document in Weaviate.

        Args:
            collection: Collection name
            document_id: Document ID
            domain_id: Domain ID
            text: Full text
            chunks: Text chunks
            embeddings: Embedding vectors
            metadata: Additional metadata

        Returns:
            Indexing result

        """
        coll = self.client.collections.get(collection)

        # Index each chunk
        for i, chunk in enumerate(chunks):
            properties = {
                "document_id": document_id,
                "domain_id": domain_id,
                "text": chunk,
                "chunk_index": i,
                **metadata,
            }

            vector = (
                embeddings["embeddings"][i]
                if i < len(embeddings["embeddings"])
                else None
            )

            coll.data.insert(
                properties=properties,
                vector=vector,
            )

        return {"success": True, "chunk_count": len(chunks)}


@lru_cache(maxsize=1)
def get_weaviate_client() -> WeaviateClient:
    """Get Weaviate client (singleton) using hostname-based configuration.

    Uses Settings class which provides hostname-based defaults (not localhost).

    Returns:
        WeaviateClient instance

    """
    from src.service.config import get_settings

    settings = get_settings()
    return WeaviateClient(settings.weaviate_url, settings.weaviate_api_key)
