"""WebSocket signal activities for Temporal workflows."""

from datetime import datetime, UTC
from typing import Any, Dict, Optional

import structlog
from temporalio import activity

from src.service.enhanced_signal_service import enhanced_signal_service

logger = structlog.get_logger()


@activity.defn
async def send_workflow_signal_activity(
    user_id: str,
    workflow_id: str,
    signal_type: str,
    data: Dict[str, Any],
    timestamp: Optional[str] = None,
) -> bool:
    """Send a workflow signal via WebSocket and persist to database.

    Args:
        user_id: Target user ID
        workflow_id: Workflow ID
        signal_type: Type of signal (status_update, completion, error, progress)
        data: Signal data payload
        timestamp: Optional timestamp (defaults to current time)

    Returns:
        True if signal was sent successfully

    """
    try:
        success = await enhanced_signal_service.send_and_persist_signal(
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type=signal_type,
            data=data,
            timestamp=timestamp,
        )

        logger.info(
            "Workflow signal sent",
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type=signal_type,
            success=success,
        )

        return success

    except Exception as e:
        logger.error(
            "Failed to send workflow signal",
            user_id=user_id,
            workflow_id=workflow_id,
            signal_type=signal_type,
            error=str(e),
        )
        return False


@activity.defn
async def send_status_update_activity(
    user_id: str,
    workflow_id: str,
    status: str,
    message: Optional[str] = None,
    progress: Optional[float] = None,
) -> bool:
    """Send a status update signal.

    Args:
        user_id: Target user ID
        workflow_id: Workflow ID
        status: Current status (started, processing, completed, failed)
        message: Optional status message
        progress: Optional progress percentage (0.0-1.0)

    Returns:
        True if signal was sent successfully

    """
    try:
        success = await enhanced_signal_service.send_status_update_with_persistence(
            user_id=user_id,
            workflow_id=workflow_id,
            status=status,
            message=message,
            progress=progress,
        )

        logger.info(
            "Status update sent",
            user_id=user_id,
            workflow_id=workflow_id,
            status=status,
            success=success,
        )

        return success

    except Exception as e:
        logger.error(
            "Failed to send status update",
            user_id=user_id,
            workflow_id=workflow_id,
            status=status,
            error=str(e),
        )
        return False


@activity.defn
async def send_completion_signal_activity(
    user_id: str,
    workflow_id: str,
    result: Dict[str, Any],
    message: Optional[str] = None,
) -> bool:
    """Send a workflow completion signal.

    Args:
        user_id: Target user ID
        workflow_id: Workflow ID
        result: Workflow result data
        message: Optional completion message

    Returns:
        True if signal was sent successfully

    """
    try:
        success = await enhanced_signal_service.send_completion_with_persistence(
            user_id=user_id,
            workflow_id=workflow_id,
            result=result,
            message=message,
        )

        logger.info(
            "Completion signal sent",
            user_id=user_id,
            workflow_id=workflow_id,
            success=success,
        )

        return success

    except Exception as e:
        logger.error(
            "Failed to send completion signal",
            user_id=user_id,
            workflow_id=workflow_id,
            error=str(e),
        )
        return False


@activity.defn
async def send_error_signal_activity(
    user_id: str,
    workflow_id: str,
    error: str,
    error_code: Optional[str] = None,
) -> bool:
    """Send an error signal.

    Args:
        user_id: Target user ID
        workflow_id: Workflow ID
        error: Error message
        error_code: Optional error code

    Returns:
        True if signal was sent successfully

    """
    try:
        success = await enhanced_signal_service.send_error_with_persistence(
            user_id=user_id,
            workflow_id=workflow_id,
            error=error,
            error_code=error_code,
        )

        logger.info(
            "Error signal sent",
            user_id=user_id,
            workflow_id=workflow_id,
            error=error,
            success=success,
        )

        return success

    except Exception as e:
        logger.error(
            "Failed to send error signal",
            user_id=user_id,
            workflow_id=workflow_id,
            error=str(e),
        )
        return False


@activity.defn
async def send_progress_signal_activity(
    user_id: str,
    workflow_id: str,
    progress: float,
    step: str,
    message: Optional[str] = None,
) -> bool:
    """Send a progress update signal.

    Args:
        user_id: Target user ID
        workflow_id: Workflow ID
        progress: Progress percentage (0.0-1.0)
        step: Current step description
        message: Optional progress message

    Returns:
        True if signal was sent successfully

    """
    try:
        success = await enhanced_signal_service.send_progress_with_persistence(
            user_id=user_id,
            workflow_id=workflow_id,
            progress=progress,
            step=step,
            message=message,
        )

        logger.info(
            "Progress signal sent",
            user_id=user_id,
            workflow_id=workflow_id,
            progress=progress,
            step=step,
            success=success,
        )

        return success

    except Exception as e:
        logger.error(
            "Failed to send progress signal",
            user_id=user_id,
            workflow_id=workflow_id,
            error=str(e),
        )
        return False
