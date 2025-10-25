"""Signal service for sending WebSocket signals from Temporal workflows."""

from datetime import datetime, UTC
from typing import Any, Dict, Optional

import structlog
from src.service.websocket_manager import connection_manager

logger = structlog.get_logger()


class SignalService:
    """Service for sending WebSocket signals to frontend clients."""

    @staticmethod
    async def send_workflow_signal(
        user_id: str,
        workflow_id: str,
        signal_type: str,
        data: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> None:
        """Send a workflow signal to a specific user.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            signal_type: Type of signal (status_update, completion, error, progress)
            data: Signal data payload
            timestamp: Optional timestamp (defaults to current time)

        """
        if timestamp is None:
            timestamp = datetime.now(UTC).isoformat()

        signal = {
            "signal_type": signal_type,
            "workflow_id": workflow_id,
            "data": data,
            "timestamp": timestamp,
        }

        await connection_manager.send_to_user(user_id, signal)
        
        logger.info(
            "Workflow signal sent",
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type=signal_type,
        )

    @staticmethod
    async def send_status_update(
        user_id: str,
        workflow_id: str,
        status: str,
        message: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> None:
        """Send a status update signal.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            status: Current status (started, processing, completed, failed)
            message: Optional status message
            progress: Optional progress percentage (0.0-1.0)

        """
        data = {"status": status}
        if message:
            data["message"] = message
        if progress is not None:
            data["progress"] = progress

        await SignalService.send_workflow_signal(
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type="status_update",
            data=data,
        )

    @staticmethod
    async def send_completion_signal(
        user_id: str,
        workflow_id: str,
        result: Dict[str, Any],
        message: Optional[str] = None,
    ) -> None:
        """Send a workflow completion signal.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            result: Workflow result data
            message: Optional completion message

        """
        data = {"result": result}
        if message:
            data["message"] = message

        await SignalService.send_workflow_signal(
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type="completion",
            data=data,
        )

    @staticmethod
    async def send_error_signal(
        user_id: str,
        workflow_id: str,
        error: str,
        error_code: Optional[str] = None,
    ) -> None:
        """Send an error signal.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            error: Error message
            error_code: Optional error code

        """
        data = {"error": error}
        if error_code:
            data["error_code"] = error_code

        await SignalService.send_workflow_signal(
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type="error",
            data=data,
        )

    @staticmethod
    async def send_progress_signal(
        user_id: str,
        workflow_id: str,
        progress: float,
        step: str,
        message: Optional[str] = None,
    ) -> None:
        """Send a progress update signal.

        Args:
            user_id: Target user ID
            workflow_id: Workflow ID
            progress: Progress percentage (0.0-1.0)
            step: Current step description
            message: Optional progress message

        """
        data = {
            "progress": progress,
            "step": step,
        }
        if message:
            data["message"] = message

        await SignalService.send_workflow_signal(
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type="progress",
            data=data,
        )


# Global signal service instance
signal_service = SignalService()
