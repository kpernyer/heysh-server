"""Supabase database activities."""

from typing import Any

import structlog
from temporalio import activity

from src.app.clients.supabase import get_supabase_client

logger = structlog.get_logger()


@activity.defn
async def update_document_metadata_activity(
    document_id: str, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Update document metadata in Supabase.

    Args:
        document_id: UUID of document
        metadata: Metadata to update

    Returns:
        Update result

    """
    activity.logger.info("Updating document metadata", document_id=document_id)

    supabase = get_supabase_client()
    result = (
        supabase.table("documents").update(metadata).eq("id", document_id).execute()
    )

    activity.logger.info("Document metadata updated")
    return {"success": True, "document_id": document_id}


@activity.defn
async def store_question_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Store a new question in the database.

    Args:
        data: Question data

    Returns:
        Stored question record

    """
    activity.logger.info("Storing question", question_id=data["id"])

    supabase = get_supabase_client()
    result = supabase.table("questions").insert(data).execute()

    activity.logger.info("Question stored successfully")
    return result.data[0] if result.data else {}


@activity.defn
async def update_question_activity(
    question_id: str, updates: dict[str, Any]
) -> dict[str, Any]:
    """Update question record.

    Args:
        question_id: UUID of question
        updates: Fields to update

    Returns:
        Updated question record

    """
    activity.logger.info("Updating question", question_id=question_id)

    supabase = get_supabase_client()
    result = supabase.table("questions").update(updates).eq("id", question_id).execute()

    activity.logger.info("Question updated successfully")
    return result.data[0] if result.data else {}


@activity.defn
async def create_review_task_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Create a review task for human reviewers.

    Args:
        data: Review task data

    Returns:
        Created review task

    """
    activity.logger.info("Creating review task", question_id=data.get("question_id"))

    supabase = get_supabase_client()
    result = supabase.table("review_tasks").insert(data).execute()

    activity.logger.info("Review task created")
    return result.data[0] if result.data else {}


@activity.defn
async def assign_review_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Assign review to an available admin/controller.

    Args:
        data: Review assignment data

    Returns:
        Assignment result with reviewer_id

    """
    activity.logger.info("Assigning review", review_id=data["review_id"])

    supabase = get_supabase_client()

    # Find available reviewer in the domain
    # Simple round-robin or priority-based assignment logic
    result = (
        supabase.table("domain_members")
        .select("user_id")
        .eq("domain_id", data["domain_id"])
        .in_("role", ["admin", "controller"])
        .limit(1)
        .execute()
    )

    reviewer_id = result.data[0]["user_id"] if result.data else None

    if not reviewer_id:
        raise ValueError("No available reviewer found in domain")

    # Create assignment record
    assignment = (
        supabase.table("review_assignments")
        .insert(
            {
                "review_id": data["review_id"],
                "reviewer_id": reviewer_id,
                "assigned_at": "now()",
            }
        )
        .execute()
    )

    activity.logger.info("Review assigned", reviewer_id=reviewer_id)
    return {"reviewer_id": reviewer_id}


@activity.defn
async def apply_review_decision_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Apply the decision made by a reviewer.

    Args:
        data: Review decision data

    Returns:
        Result of applying the decision

    """
    activity.logger.info("Applying review decision", review_id=data["review_id"])

    supabase = get_supabase_client()
    decision = data["decision"]

    # Update the reviewable item based on decision
    if decision.get("action") == "approve":
        # Mark as approved
        if data["reviewable_type"] == "document":
            supabase.table("documents").update(
                {
                    "review_status": "approved",
                    "reviewed_by": data["reviewer_id"],
                }
            ).eq("id", data["reviewable_id"]).execute()

    elif decision.get("action") == "reject":
        # Mark as rejected
        if data["reviewable_type"] == "document":
            supabase.table("documents").update(
                {
                    "review_status": "rejected",
                    "reviewed_by": data["reviewer_id"],
                }
            ).eq("id", data["reviewable_id"]).execute()

    elif decision.get("action") == "rollback":
        # Soft delete or archive
        if data["reviewable_type"] == "document":
            supabase.table("documents").update(
                {
                    "review_status": "rolled_back",
                    "reviewed_by": data["reviewer_id"],
                    "deleted_at": "now()",
                }
            ).eq("id", data["reviewable_id"]).execute()

    activity.logger.info("Review decision applied", action=decision.get("action"))
    return decision


@activity.defn
async def update_quality_score_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Update quality score for a document or contributor.

    Args:
        data: Quality score update data

    Returns:
        Updated score

    """
    activity.logger.info("Updating quality score", reviewable_id=data["reviewable_id"])

    supabase = get_supabase_client()

    # Adjust quality score based on review outcome
    score_delta = {
        "approve": 1.0,
        "reject": -2.0,
        "rollback": -5.0,
        "flag": -1.0,
    }.get(data["review_outcome"], 0.0)

    # Update document quality score
    supabase.rpc(
        "increment_quality_score",
        {
            "doc_id": data["reviewable_id"],
            "delta": score_delta,
        },
    ).execute()

    activity.logger.info("Quality score updated", delta=score_delta)
    return {"score_delta": score_delta}


@activity.defn
async def notify_contributor_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Notify contributor of review outcome.

    Args:
        data: Notification data

    Returns:
        Notification result

    """
    activity.logger.info("Notifying contributor", reviewable_id=data["reviewable_id"])

    supabase = get_supabase_client()

    # Create notification record
    notification = (
        supabase.table("notifications")
        .insert(
            {
                "reviewable_id": data["reviewable_id"],
                "reviewable_type": data["reviewable_type"],
                "message": f"Your {data['reviewable_type']} was {data['review_outcome']}",
                "notes": data.get("reviewer_notes"),
            }
        )
        .execute()
    )

    activity.logger.info("Contributor notified")
    return {"success": True}
