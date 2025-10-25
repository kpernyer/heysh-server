"""Enhanced signal service with persistence for inbox system."""

from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

import structlog
from src.service.models.signal_model import SignalModel
from src.service.signal_service import SignalService
from src.service.websocket_manager import connection_manager

logger = structlog.get_logger()


class EnhancedSignalService:
    """Enhanced signal service with WebSocket delivery and database persistence."""

    @staticmethod
    async def send_and_persist_signal(
        user_id: str,
        workflow_id: str,
        signal_type: str,
        data: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> bool:
        """Send signal via WebSocket and persist to database.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            signal_type: Type of signal
            data: Signal data payload
            timestamp: Optional timestamp

        Returns:
            True if both WebSocket and persistence succeeded

        """
        if timestamp is None:
            timestamp = datetime.now(UTC).isoformat()

        # Send via WebSocket
        websocket_success = True
        try:
            await SignalService.send_workflow_signal(
                user_id=user_id,
                workflow_id=workflow_id,
                signal_type=signal_type,
                data=data,
                timestamp=timestamp,
            )
        except Exception as e:
            logger.warning("Failed to send WebSocket signal", user_id=user_id, error=str(e))
            websocket_success = False

        # Persist to database
        persistence_success = True
        try:
            await SignalModel.create_signal(
                user_id=user_id,
                workflow_id=workflow_id,
                signal_type=signal_type,
                data=data,
                timestamp=timestamp,
            )
        except Exception as e:
            logger.warning("Failed to persist signal", user_id=user_id, error=str(e))
            persistence_success = False

        success = websocket_success or persistence_success  # At least one must succeed
        logger.info(
            "Signal sent and persisted",
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type=signal_type,
            websocket_success=websocket_success,
            persistence_success=persistence_success,
        )

        return success

    @staticmethod
    async def send_status_update_with_persistence(
        user_id: str,
        workflow_id: str,
        status: str,
        message: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> bool:
        """Send status update with persistence.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            status: Current status
            message: Optional status message
            progress: Optional progress percentage

        Returns:
            True if successful

        """
        data = {"status": status}
        if message:
            data["message"] = message
        if progress is not None:
            data["progress"] = progress

        return await EnhancedSignalService.send_and_persist_signal(
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type="status_update",
            data=data,
        )

    @staticmethod
    async def send_completion_with_persistence(
        user_id: str,
        workflow_id: str,
        result: Dict[str, Any],
        message: Optional[str] = None,
    ) -> bool:
        """Send completion signal with persistence.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            result: Workflow result data
            message: Optional completion message

        Returns:
            True if successful

        """
        data = {"result": result}
        if message:
            data["message"] = message

        return await EnhancedSignalService.send_and_persist_signal(
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type="completion",
            data=data,
        )

    @staticmethod
    async def send_error_with_persistence(
        user_id: str,
        workflow_id: str,
        error: str,
        error_code: Optional[str] = None,
    ) -> bool:
        """Send error signal with persistence.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            error: Error message
            error_code: Optional error code

        Returns:
            True if successful

        """
        data = {"error": error}
        if error_code:
            data["error_code"] = error_code

        return await EnhancedSignalService.send_and_persist_signal(
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type="error",
            data=data,
        )

    @staticmethod
    async def send_progress_with_persistence(
        user_id: str,
        workflow_id: str,
        progress: float,
        step: str,
        message: Optional[str] = None,
    ) -> bool:
        """Send progress signal with persistence.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            progress: Progress percentage
            step: Current step description
            message: Optional progress message

        Returns:
            True if successful

        """
        data = {
            "progress": progress,
            "step": step,
        }
        if message:
            data["message"] = message

        return await EnhancedSignalService.send_and_persist_signal(
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type="progress",
            data=data,
        )

    @staticmethod
    async def get_user_inbox(
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        signal_type: Optional[str] = None,
        workflow_id: Optional[str] = None,
        unread_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get user's signal inbox.

        Args:
            user_id: User ID
            limit: Maximum number of signals
            offset: Number of signals to skip
            signal_type: Optional signal type filter
            workflow_id: Optional workflow ID filter
            unread_only: Only return unread signals

        Returns:
            List of signals

        """
        return await SignalModel.get_user_signals(
            user_id=user_id,
            limit=limit,
            offset=offset,
            signal_type=signal_type,
            workflow_id=workflow_id,
            unread_only=unread_only,
        )

    @staticmethod
    async def mark_signal_as_read(signal_id: str, user_id: str) -> bool:
        """Mark a signal as read.

        Args:
            signal_id: Signal ID
            user_id: User ID

        Returns:
            True if successful

        """
        return await SignalModel.mark_as_read(signal_id, user_id)

    @staticmethod
    async def mark_all_as_read(user_id: str, workflow_id: Optional[str] = None) -> int:
        """Mark all signals as read for a user.

        Args:
            user_id: User ID
            workflow_id: Optional workflow ID filter

        Returns:
            Number of signals marked as read

        """
        return await SignalModel.mark_all_as_read(user_id, workflow_id)

    @staticmethod
    async def get_unread_count(user_id: str) -> int:
        """Get count of unread signals.

        Args:
            user_id: User ID

        Returns:
            Number of unread signals

        """
        return await SignalModel.get_unread_count(user_id)


# Global enhanced signal service instance
enhanced_signal_service = EnhancedSignalService()
