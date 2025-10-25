"""Signal model for persisting WebSocket signals in the inbox system."""

from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

import structlog
from src.service.models.base_model import BaseModel

logger = structlog.get_logger()


class SignalModel(BaseModel):
    """Model for managing workflow signals in the inbox system."""

    table_name = "workflow_signals"

    @classmethod
    async def create_signal(
        cls,
        user_id: str,
        workflow_id: str,
        signal_type: str,
        data: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any] | None:
        """Create a new signal record.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            signal_type: Type of signal
            data: Signal data payload
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Created signal record or None if failed

        """
        if timestamp is None:
            timestamp = datetime.now(UTC).isoformat()

        signal_data = {
            "user_id": user_id,
            "workflow_id": workflow_id,
            "signal_type": signal_type,
            "data": data,
            "timestamp": timestamp,
            "read": False,
            "created_at": datetime.now(UTC).isoformat(),
        }

        return await cls.create(signal_data)

    @classmethod
    async def get_user_signals(
        cls,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        signal_type: Optional[str] = None,
        workflow_id: Optional[str] = None,
        unread_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get signals for a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of signals to return
            offset: Number of signals to skip
            signal_type: Optional signal type filter
            workflow_id: Optional workflow ID filter
            unread_only: Only return unread signals

        Returns:
            List of signal records

        """
        try:
            supabase = cls.get_client()
            query = (
                supabase.table(cls.table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
            )

            if signal_type:
                query = query.eq("signal_type", signal_type)
            if workflow_id:
                query = query.eq("workflow_id", workflow_id)
            if unread_only:
                query = query.eq("read", False)

            response = query.execute()
            logger.info(
                "Retrieved user signals",
                user_id=user_id,
                count=len(response.data),
                filters={
                    "signal_type": signal_type,
                    "workflow_id": workflow_id,
                    "unread_only": unread_only,
                },
            )
            return response.data

        except Exception as e:
            logger.error("Failed to get user signals", user_id=user_id, error=str(e))
            return []

    @classmethod
    async def mark_as_read(
        cls,
        signal_id: str,
        user_id: str,
    ) -> bool:
        """Mark a signal as read.

        Args:
            signal_id: Signal ID
            user_id: User ID (for security)

        Returns:
            True if successful, False otherwise

        """
        try:
            supabase = cls.get_client()
            response = (
                supabase.table(cls.table_name)
                .update({"read": True, "read_at": datetime.now(UTC).isoformat()})
                .eq("id", signal_id)
                .eq("user_id", user_id)
                .execute()
            )

            success = len(response.data) > 0
            if success:
                logger.info("Signal marked as read", signal_id=signal_id, user_id=user_id)
            else:
                logger.warning("Signal not found or not owned by user", signal_id=signal_id, user_id=user_id)

            return success

        except Exception as e:
            logger.error("Failed to mark signal as read", signal_id=signal_id, user_id=user_id, error=str(e))
            return False

    @classmethod
    async def mark_all_as_read(
        cls,
        user_id: str,
        workflow_id: Optional[str] = None,
    ) -> int:
        """Mark all signals as read for a user.

        Args:
            user_id: User ID
            workflow_id: Optional workflow ID filter

        Returns:
            Number of signals marked as read

        """
        try:
            supabase = cls.get_client()
            query = (
                supabase.table(cls.table_name)
                .update({"read": True, "read_at": datetime.now(UTC).isoformat()})
                .eq("user_id", user_id)
                .eq("read", False)
            )

            if workflow_id:
                query = query.eq("workflow_id", workflow_id)

            response = query.execute()
            count = len(response.data)
            
            logger.info(
                "Marked signals as read",
                user_id=user_id,
                workflow_id=workflow_id,
                count=count,
            )
            return count

        except Exception as e:
            logger.error("Failed to mark signals as read", user_id=user_id, error=str(e))
            return 0

    @classmethod
    async def get_unread_count(cls, user_id: str) -> int:
        """Get count of unread signals for a user.

        Args:
            user_id: User ID

        Returns:
            Number of unread signals

        """
        try:
            supabase = cls.get_client()
            response = (
                supabase.table(cls.table_name)
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("read", False)
                .execute()
            )

            count = response.count or 0
            logger.debug("Retrieved unread count", user_id=user_id, count=count)
            return count

        except Exception as e:
            logger.error("Failed to get unread count", user_id=user_id, error=str(e))
            return 0

    @classmethod
    async def delete_old_signals(
        cls,
        days_old: int = 30,
    ) -> int:
        """Delete signals older than specified days.

        Args:
            days_old: Delete signals older than this many days

        Returns:
            Number of signals deleted

        """
        try:
            cutoff_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)

            supabase = cls.get_client()
            response = (
                supabase.table(cls.table_name)
                .delete()
                .lt("created_at", cutoff_date.isoformat())
                .execute()
            )

            count = len(response.data)
            logger.info("Deleted old signals", days_old=days_old, count=count)
            return count

        except Exception as e:
            logger.error("Failed to delete old signals", days_old=days_old, error=str(e))
            return 0
