"""Inbox API routes for managing workflow signals."""

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.app.auth.dependencies import CurrentUserId
from src.service.enhanced_signal_service import enhanced_signal_service

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/inbox", tags=["inbox"])


@router.get("/signals")
async def get_user_signals(
    user_id: CurrentUserId,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of signals to return"),
    offset: int = Query(0, ge=0, description="Number of signals to skip"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    unread_only: bool = Query(False, description="Only return unread signals"),
) -> Dict[str, Any]:
    """Get user's signal inbox.

    Args:
        user_id: Current authenticated user ID
        limit: Maximum number of signals to return
        offset: Number of signals to skip
        signal_type: Optional signal type filter
        workflow_id: Optional workflow ID filter
        unread_only: Only return unread signals

    Returns:
        User's signals with metadata

    """
    try:
        signals = await enhanced_signal_service.get_user_inbox(
            user_id=user_id,
            limit=limit,
            offset=offset,
            signal_type=signal_type,
            workflow_id=workflow_id,
            unread_only=unread_only,
        )

        unread_count = await enhanced_signal_service.get_unread_count(user_id)

        return {
            "signals": signals,
            "total_count": len(signals),
            "unread_count": unread_count,
            "filters": {
                "signal_type": signal_type,
                "workflow_id": workflow_id,
                "unread_only": unread_only,
            },
            "pagination": {
                "limit": limit,
                "offset": offset,
            },
        }

    except Exception as e:
        logger.error("Failed to get user signals", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve signals",
        )


@router.get("/signals/unread-count")
async def get_unread_count(user_id: CurrentUserId) -> Dict[str, int]:
    """Get count of unread signals for the current user.

    Args:
        user_id: Current authenticated user ID

    Returns:
        Unread signal count

    """
    try:
        count = await enhanced_signal_service.get_unread_count(user_id)
        return {"unread_count": count}

    except Exception as e:
        logger.error("Failed to get unread count", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count",
        )


@router.post("/signals/{signal_id}/read")
async def mark_signal_as_read(
    signal_id: str,
    user_id: CurrentUserId,
) -> Dict[str, Any]:
    """Mark a specific signal as read.

    Args:
        signal_id: Signal ID to mark as read
        user_id: Current authenticated user ID

    Returns:
        Success status

    """
    try:
        success = await enhanced_signal_service.mark_signal_as_read(signal_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found or not owned by user",
            )

        return {"success": True, "signal_id": signal_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to mark signal as read", signal_id=signal_id, user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark signal as read",
        )


@router.post("/signals/mark-all-read")
async def mark_all_signals_as_read(
    user_id: CurrentUserId,
    workflow_id: Optional[str] = Query(None, description="Optional workflow ID filter"),
) -> Dict[str, Any]:
    """Mark all signals as read for the current user.

    Args:
        user_id: Current authenticated user ID
        workflow_id: Optional workflow ID filter

    Returns:
        Number of signals marked as read

    """
    try:
        count = await enhanced_signal_service.mark_all_as_read(user_id, workflow_id)
        
        return {
            "success": True,
            "marked_count": count,
            "workflow_id": workflow_id,
        }

    except Exception as e:
        logger.error("Failed to mark all signals as read", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark signals as read",
        )


@router.get("/signals/workflow/{workflow_id}")
async def get_workflow_signals(
    workflow_id: str,
    user_id: CurrentUserId,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """Get all signals for a specific workflow.

    Args:
        workflow_id: Workflow ID
        user_id: Current authenticated user ID
        limit: Maximum number of signals
        offset: Number of signals to skip

    Returns:
        Workflow signals

    """
    try:
        signals = await enhanced_signal_service.get_user_inbox(
            user_id=user_id,
            limit=limit,
            offset=offset,
            workflow_id=workflow_id,
        )

        return {
            "workflow_id": workflow_id,
            "signals": signals,
            "total_count": len(signals),
            "pagination": {
                "limit": limit,
                "offset": offset,
            },
        }

    except Exception as e:
        logger.error("Failed to get workflow signals", workflow_id=workflow_id, user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow signals",
        )
