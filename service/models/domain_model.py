"""Domain model for managing domains and their metadata."""

from datetime import datetime
from typing import Any

import structlog

from service.models.base_model import BaseModel

logger = structlog.get_logger()


class DomainModel(BaseModel):
    """Model for domain operations."""

    table_name = "domains"

    @classmethod
    async def create_domain(
        cls,
        name: str,
        description: str | None = None,
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new domain.

        Args:
            name: Domain name
            description: Optional description
            created_by: User ID (optional)
            metadata: Optional metadata

        Returns:
            Created domain data

        """
        data = {
            "name": name,
            "description": description,
            "created_by": created_by,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat(),
        }
        return await cls.create(data)

    @classmethod
    async def record_indexing(
        cls,
        domain_id: str,
        weaviate_indexed: bool = False,
        neo4j_indexed: bool = False,
    ) -> dict[str, Any]:
        """Record that domain was indexed in Weaviate and/or Neo4j.

        Args:
            domain_id: Domain UUID
            weaviate_indexed: Whether indexed in Weaviate
            neo4j_indexed: Whether indexed in Neo4j

        Returns:
            Updated domain data

        """
        metadata_key = "indexing_status"

        data = {
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Get current domain to preserve metadata
        domain = await cls.get_by_id(domain_id)
        if domain:
            current_metadata = domain.get("metadata") or {}
            current_metadata[metadata_key] = {
                "weaviate": weaviate_indexed,
                "neo4j": neo4j_indexed,
                "indexed_at": datetime.utcnow().isoformat(),
            }
            data["metadata"] = current_metadata

        logger.info(
            "Recording domain indexing",
            domain_id=domain_id,
            weaviate=weaviate_indexed,
            neo4j=neo4j_indexed,
        )

        return await cls.update(domain_id, data)

    @classmethod
    async def get_user_domains(
        cls,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """Get all domains created by a user."""
        return await cls.list_all({"created_by": user_id})

    @classmethod
    async def update_stats(
        cls,
        domain_id: str,
        document_count: int | None = None,
        member_count: int | None = None,
    ) -> dict[str, Any]:
        """Update domain statistics.

        Args:
            domain_id: Domain UUID
            document_count: Number of documents
            member_count: Number of members

        Returns:
            Updated domain data

        """
        domain = await cls.get_by_id(domain_id)
        if not domain:
            raise ValueError(f"Domain not found: {domain_id}")

        stats = domain.get("stats") or {}

        if document_count is not None:
            stats["document_count"] = document_count

        if member_count is not None:
            stats["member_count"] = member_count

        stats["last_updated"] = datetime.utcnow().isoformat()

        return await cls.update(domain_id, {"stats": stats})

    @classmethod
    async def record_indexing_error(
        cls,
        domain_id: str,
        error_message: str,
    ) -> dict[str, Any]:
        """Record that domain indexing failed.

        Args:
            domain_id: Domain UUID
            error_message: Error description

        Returns:
            Updated domain data

        """
        logger.error(
            "Domain indexing failed",
            domain_id=domain_id,
            error=error_message,
        )

        domain = await cls.get_by_id(domain_id)
        if domain:
            metadata = domain.get("metadata") or {}
            metadata["indexing_error"] = {
                "error": error_message,
                "error_at": datetime.utcnow().isoformat(),
            }
            return await cls.update(domain_id, {"metadata": metadata})

        return {}

    @classmethod
    async def get_domains_needing_indexing(cls) -> list[dict[str, Any]]:
        """Get domains that haven't been indexed yet.

        Returns:
            List of domains needing indexing

        """
        try:
            supabase = cls.get_client()

            # This is a simple check - in production, you might want more sophisticated logic
            response = supabase.table(cls.table_name).select("*").execute()

            domains_needing_indexing = []
            for domain in response.data:
                metadata = domain.get("metadata") or {}
                indexing_status = metadata.get("indexing_status", {})

                if not indexing_status.get("weaviate") or not indexing_status.get(
                    "neo4j"
                ):
                    domains_needing_indexing.append(domain)

            return domains_needing_indexing

        except Exception as e:
            logger.error(
                "Failed to get domains needing indexing",
                error=str(e),
            )
            return []
