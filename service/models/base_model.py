"""Base model class with common Supabase operations."""

from typing import Any

import structlog
from supabase import Client

from src.app.clients.supabase import get_supabase_client

logger = structlog.get_logger()


class BaseModel:
    """Base class for all data models."""

    table_name: str = ""

    @classmethod
    def get_client(cls) -> Client:
        """Get Supabase client."""
        return get_supabase_client()

    @classmethod
    async def get_by_id(cls, item_id: str) -> dict[str, Any] | None:
        """Get item by ID."""
        try:
            supabase = cls.get_client()
            response = (
                supabase.table(cls.table_name)
                .select("*")
                .eq("id", item_id)
                .single()
                .execute()
            )
            logger.info(f"Retrieved {cls.table_name}", item_id=item_id)
            return response.data
        except Exception as e:
            logger.error(
                f"Failed to get {cls.table_name}",
                item_id=item_id,
                error=str(e),
            )
            return None

    @classmethod
    async def list_all(
        cls, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """List all items, optionally with filters."""
        try:
            supabase = cls.get_client()
            query = supabase.table(cls.table_name).select("*")

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = query.execute()
            logger.info(f"Listed {cls.table_name}", count=len(response.data))
            return response.data
        except Exception as e:
            logger.error(f"Failed to list {cls.table_name}", error=str(e))
            return []

    @classmethod
    async def create(cls, data: dict[str, Any]) -> dict[str, Any] | None:
        """Create new item."""
        try:
            supabase = cls.get_client()
            response = supabase.table(cls.table_name).insert(data).execute()
            logger.info(f"Created {cls.table_name}", item_id=response.data[0].get("id"))
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create {cls.table_name}", error=str(e))
            raise

    @classmethod
    async def update(cls, item_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update item."""
        try:
            supabase = cls.get_client()
            response = (
                supabase.table(cls.table_name).update(data).eq("id", item_id).execute()
            )
            if not response.data:
                logger.warning(f"{cls.table_name} not found", item_id=item_id)
                return None
            logger.info(f"Updated {cls.table_name}", item_id=item_id)
            return response.data[0]
        except Exception as e:
            logger.error(
                f"Failed to update {cls.table_name}",
                item_id=item_id,
                error=str(e),
            )
            raise

    @classmethod
    async def delete(cls, item_id: str) -> bool:
        """Delete item."""
        try:
            supabase = cls.get_client()
            response = (
                supabase.table(cls.table_name).delete().eq("id", item_id).execute()
            )
            if not response.data:
                logger.warning(f"{cls.table_name} not found", item_id=item_id)
                return False
            logger.info(f"Deleted {cls.table_name}", item_id=item_id)
            return True
        except Exception as e:
            logger.error(
                f"Failed to delete {cls.table_name}",
                item_id=item_id,
                error=str(e),
            )
            raise
