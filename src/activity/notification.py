"""Notification activities for Temporal workflows."""

from typing import Any, Dict
import structlog
from temporalio import activity

logger = structlog.get_logger()


@activity.defn
async def notify_user_activity(user_id: str, subject: str, message: str) -> Dict[str, Any]:
    """Notify a user about workflow events."""
    activity.logger.info(f"Notifying user {user_id}: {subject}")
    activity.logger.info(f"Message: {message}")
    
    # For now, just log the notification
    # In a real system, this would send email, Slack, etc.
    
    return {
        "success": True,
        "user_id": user_id,
        "subject": subject,
        "message": message,
        "timestamp": activity.now().isoformat()
    }
