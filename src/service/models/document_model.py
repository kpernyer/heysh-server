"""Document model for managing document data."""

from datetime import datetime
from typing import Any

import structlog

from src.service.models.base_model import BaseModel

logger = structlog.get_logger()


class DocumentModel(BaseModel):
    """Model for document operations."""

    table_name = "documents"

    @classmethod
    async def create_document(
        cls,
        name: str,
        domain_id: str,
        file_path: str,
        file_type: str | None = None,
        size_bytes: int | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Create a new document.

        Args:
            name: Document name
            domain_id: Domain UUID
            file_path: Path in Supabase Storage
            file_type: MIME type (optional)
            size_bytes: File size (optional)
            created_by: User ID (optional)

        Returns:
            Created document data

        """
        data = {
            "name": name,
            "domain_id": domain_id,
            "file_path": file_path,
            "file_type": file_type,
            "size_bytes": size_bytes,
            "status": "pending",  # Will be updated by workflow
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
        }
        return await cls.create(data)

    @classmethod
    async def update_status(
        cls,
        document_id: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update document status (called by workflows).

        Args:
            document_id: Document UUID
            status: New status (pending, indexed, failed, etc.)
            metadata: Optional metadata to store

        Returns:
            Updated document data

        """
        data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if metadata:
            data["metadata"] = metadata

        logger.info(
            "Updating document status",
            document_id=document_id,
            status=status,
        )

        return await cls.update(document_id, data)

    @classmethod
    async def get_by_domain(cls, domain_id: str) -> list[dict[str, Any]]:
        """Get all documents in a domain."""
        return await cls.list_all({"domain_id": domain_id})

    @classmethod
    async def get_by_status(cls, status: str) -> list[dict[str, Any]]:
        """Get all documents with specific status."""
        return await cls.list_all({"status": status})

    @classmethod
    async def add_metadata(
        cls,
        document_id: str,
        metadata_key: str,
        metadata_value: Any,
    ) -> dict[str, Any]:
        """Add or update metadata for a document.

        Args:
            document_id: Document UUID
            metadata_key: Key in metadata JSON
            metadata_value: Value to store

        Returns:
            Updated document data

        """
        doc = await cls.get_by_id(document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        current_metadata = doc.get("metadata") or {}
        current_metadata[metadata_key] = metadata_value

        return await cls.update(document_id, {"metadata": current_metadata})

    @classmethod
    async def record_processing_error(
        cls,
        document_id: str,
        error_message: str,
    ) -> dict[str, Any]:
        """Record that document processing failed.

        Args:
            document_id: Document UUID
            error_message: Error description

        Returns:
            Updated document data

        """
        logger.error(
            "Document processing failed",
            document_id=document_id,
            error=error_message,
        )

        return await cls.update_status(
            document_id,
            "failed",
            {"error": error_message},
        )

    @classmethod
    async def record_processing_success(
        cls,
        document_id: str,
        weaviate_id: str | None = None,
        neo4j_updated: bool = False,
        embeddings_count: int | None = None,
    ) -> dict[str, Any]:
        """Record successful document processing.

        Args:
            document_id: Document UUID
            weaviate_id: ID in Weaviate (optional)
            neo4j_updated: Whether Neo4j was updated
            embeddings_count: Number of embeddings generated

        Returns:
            Updated document data

        """
        logger.info(
            "Document processing succeeded",
            document_id=document_id,
            weaviate_id=weaviate_id,
            neo4j_updated=neo4j_updated,
        )

        metadata = {
            "weaviate_id": weaviate_id,
            "neo4j_updated": neo4j_updated,
            "embeddings_count": embeddings_count,
            "processed_at": datetime.utcnow().isoformat(),
        }

        return await cls.update_status(
            document_id,
            "indexed",
            metadata,
        )
