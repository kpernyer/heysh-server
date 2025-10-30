"""Inbox API routes - Manage user inbox for HITL workflows."""

from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.app.auth.dependencies import CurrentUserId
from src.service.enhanced_signal_service import enhanced_signal_service

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v2/inbox", tags=["Inbox"])


# ==================== Models ====================

class InboxItemType(str, Enum):
    """Type of inbox item."""
    APPROVAL_REQUEST = "approval_request"
    REVIEW_REQUEST = "review_request"
    NOTIFICATION = "notification"
    TASK_ASSIGNMENT = "task_assignment"
    MEMBERSHIP_REQUEST = "membership_request"
    WORKFLOW_SIGNAL = "workflow_signal"
    MENTION = "mention"
    SYSTEM_MESSAGE = "system_message"


class InboxItemPriority(str, Enum):
    """Priority of inbox item."""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class InboxItemStatus(str, Enum):
    """Status of inbox item."""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    ACTIONED = "actioned"


class InboxItem(BaseModel):
    """An item in the user's inbox."""
    id: str
    type: InboxItemType
    priority: InboxItemPriority
    status: InboxItemStatus
    title: str
    description: Optional[str]
    from_user_id: Optional[str]
    from_user_email: Optional[str]
    from_user_name: Optional[str]
    topic_id: Optional[str]
    topic_name: Optional[str]
    workflow_id: Optional[str]
    workflow_execution_id: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]
    expires_at: Optional[datetime]
    action_required: bool = False
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Available actions")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InboxStats(BaseModel):
    """Statistics about user's inbox."""
    total_count: int
    unread_count: int
    high_priority_count: int
    action_required_count: int
    by_type: Dict[str, int]
    oldest_unread: Optional[datetime]


class MarkAsReadRequest(BaseModel):
    """Request to mark items as read."""
    item_ids: List[str] = Field(..., min_items=1, max_items=100)


class BulkActionRequest(BaseModel):
    """Request for bulk actions on inbox items."""
    item_ids: List[str] = Field(..., min_items=1, max_items=100)
    action: str = Field(..., pattern="^(archive|delete|mark_read|mark_unread)$")


# ==================== Get Inbox ====================

@router.get("/", response_model=List[InboxItem])
async def get_inbox(
    user_id: CurrentUserId,
    status: Optional[InboxItemStatus] = Query(None),
    type_filter: Optional[InboxItemType] = Query(None, alias="type"),
    priority: Optional[InboxItemPriority] = Query(None),
    topic_id: Optional[str] = Query(None),
    action_required: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[InboxItem]:
    """Get user's inbox items.

    Returns items sorted by priority and creation time.
    """
    try:
        # Use the existing signal service for workflow signals
        signals = await enhanced_signal_service.get_user_inbox(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=(status == InboxItemStatus.UNREAD) if status else False,
        )

        # Transform signals to inbox items
        inbox_items = []
        for signal in signals.get("signals", []):
            # Map signal to inbox item
            inbox_item = InboxItem(
                id=signal["id"],
                type=InboxItemType.WORKFLOW_SIGNAL,
                priority=InboxItemPriority.NORMAL,
                status=InboxItemStatus.UNREAD if signal.get("is_unread") else InboxItemStatus.READ,
                title=signal.get("signal_type", "Workflow Signal"),
                description=signal.get("data", {}).get("message"),
                from_user_id=signal.get("from_user_id"),
                from_user_email=None,  # Would need to look up
                from_user_name=None,
                topic_id=signal.get("domain_id"),
                topic_name=signal.get("domain_name"),
                workflow_id=signal.get("workflow_id"),
                workflow_execution_id=signal.get("workflow_execution_id"),
                created_at=datetime.fromisoformat(signal["created_at"]),
                read_at=datetime.fromisoformat(signal["read_at"]) if signal.get("read_at") else None,
                expires_at=datetime.fromisoformat(signal["expires_at"]) if signal.get("expires_at") else None,
                action_required=signal.get("action_required", False),
                actions=signal.get("available_actions", []),
                metadata=signal.get("data", {})
            )

            # Apply filters
            if type_filter and inbox_item.type != type_filter:
                continue
            if priority and inbox_item.priority != priority:
                continue
            if topic_id and inbox_item.topic_id != topic_id:
                continue
            if action_required is not None and inbox_item.action_required != action_required:
                continue

            inbox_items.append(inbox_item)

        return inbox_items

    except Exception as e:
        logger.error("Failed to get inbox", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inbox: {e}"
        )


# ==================== Get Inbox Stats ====================

@router.get("/stats", response_model=InboxStats)
async def get_inbox_stats(
    user_id: CurrentUserId,
) -> InboxStats:
    """Get statistics about user's inbox."""
    try:
        # Get unread count from signal service
        unread_count = await enhanced_signal_service.get_unread_count(user_id)

        # Get full inbox for detailed stats
        all_signals = await enhanced_signal_service.get_user_inbox(
            user_id=user_id,
            limit=1000,  # Get all for stats
            offset=0,
        )

        signals = all_signals.get("signals", [])

        # Calculate stats
        total_count = len(signals)
        high_priority_count = 0
        action_required_count = 0
        by_type = {}
        oldest_unread = None

        for signal in signals:
            # Count by type
            signal_type = signal.get("signal_type", "unknown")
            by_type[signal_type] = by_type.get(signal_type, 0) + 1

            # Count action required
            if signal.get("action_required"):
                action_required_count += 1

            # Track oldest unread
            if signal.get("is_unread"):
                created_at = datetime.fromisoformat(signal["created_at"])
                if oldest_unread is None or created_at < oldest_unread:
                    oldest_unread = created_at

        return InboxStats(
            total_count=total_count,
            unread_count=unread_count,
            high_priority_count=high_priority_count,
            action_required_count=action_required_count,
            by_type=by_type,
            oldest_unread=oldest_unread
        )

    except Exception as e:
        logger.error("Failed to get inbox stats", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inbox stats: {e}"
        )


# ==================== Get Unread Count ====================

@router.get("/unread-count", response_model=Dict[str, int])
async def get_unread_count(
    user_id: CurrentUserId,
) -> Dict[str, int]:
    """Get count of unread inbox items."""
    try:
        unread_count = await enhanced_signal_service.get_unread_count(user_id)
        return {"unread_count": unread_count}

    except Exception as e:
        logger.error("Failed to get unread count", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {e}"
        )


# ==================== Mark as Read ====================

@router.put("/{item_id}/read", response_model=Dict[str, str])
async def mark_item_as_read(
    item_id: str,
    user_id: CurrentUserId,
) -> Dict[str, str]:
    """Mark a single inbox item as read."""
    try:
        # Mark signal as read
        await enhanced_signal_service.mark_signal_read(
            signal_id=item_id,
            user_id=user_id
        )

        return {"status": "success", "message": f"Item {item_id} marked as read"}

    except Exception as e:
        logger.error("Failed to mark item as read", item_id=item_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark item as read: {e}"
        )


# ==================== Bulk Mark as Read ====================

@router.post("/mark-read", response_model=Dict[str, Any])
async def bulk_mark_as_read(
    request: MarkAsReadRequest,
    user_id: CurrentUserId,
) -> Dict[str, Any]:
    """Mark multiple inbox items as read."""
    try:
        success_count = 0
        failed_items = []

        for item_id in request.item_ids:
            try:
                await enhanced_signal_service.mark_signal_read(
                    signal_id=item_id,
                    user_id=user_id
                )
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to mark item {item_id} as read: {e}")
                failed_items.append(item_id)

        return {
            "status": "success" if success_count > 0 else "failed",
            "marked_count": success_count,
            "failed_items": failed_items,
            "message": f"Marked {success_count} items as read"
        }

    except Exception as e:
        logger.error("Failed to bulk mark as read", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk mark as read: {e}"
        )


# ==================== Archive Item ====================

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_inbox_item(
    item_id: str,
    user_id: CurrentUserId,
) -> None:
    """Archive (soft delete) an inbox item."""
    try:
        # Archive the signal
        await enhanced_signal_service.archive_signal(
            signal_id=item_id,
            user_id=user_id
        )

    except Exception as e:
        logger.error("Failed to archive item", item_id=item_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive item: {e}"
        )


# ==================== Bulk Actions ====================

@router.post("/bulk-action", response_model=Dict[str, Any])
async def bulk_inbox_action(
    request: BulkActionRequest,
    user_id: CurrentUserId,
) -> Dict[str, Any]:
    """Perform bulk actions on inbox items."""
    try:
        success_count = 0
        failed_items = []

        for item_id in request.item_ids:
            try:
                if request.action == "archive" or request.action == "delete":
                    await enhanced_signal_service.archive_signal(
                        signal_id=item_id,
                        user_id=user_id
                    )
                elif request.action == "mark_read":
                    await enhanced_signal_service.mark_signal_read(
                        signal_id=item_id,
                        user_id=user_id
                    )
                elif request.action == "mark_unread":
                    await enhanced_signal_service.mark_signal_unread(
                        signal_id=item_id,
                        user_id=user_id
                    )

                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to {request.action} item {item_id}: {e}")
                failed_items.append(item_id)

        return {
            "status": "success" if success_count > 0 else "failed",
            "action": request.action,
            "processed_count": success_count,
            "failed_items": failed_items,
            "message": f"Successfully processed {success_count} items"
        }

    except Exception as e:
        logger.error("Failed to perform bulk action", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk action: {e}"
        )