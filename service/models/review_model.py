"""Review model for managing review tasks and decisions."""

from datetime import datetime
from typing import Any

import structlog

from service.models.base_model import BaseModel

logger = structlog.get_logger()


class ReviewModel(BaseModel):
    """Model for review task operations."""

    table_name = "reviews"

    @classmethod
    async def create_review(
        cls,
        domain_id: str,
        reviewable_type: str,
        reviewable_id: str,
        reason: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Create a new review task.

        Args:
            domain_id: Domain UUID
            reviewable_type: Type of item being reviewed (document, answer, etc.)
            reviewable_id: UUID of the item being reviewed
            reason: Optional reason for review
            created_by: User ID who initiated review (optional)

        Returns:
            Created review data

        """
        data = {
            "domain_id": domain_id,
            "reviewable_type": reviewable_type,
            "reviewable_id": reviewable_id,
            "reason": reason,
            "status": "pending",
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
        }
        return await cls.create(data)

    @classmethod
    async def assign_to_reviewers(
        cls,
        review_id: str,
        reviewer_ids: list[str],
    ) -> dict[str, Any]:
        """Assign review to specific reviewers.

        Args:
            review_id: Review UUID
            reviewer_ids: List of reviewer user IDs

        Returns:
            Updated review data

        """
        logger.info(
            "Assigning review to reviewers",
            review_id=review_id,
            reviewer_count=len(reviewer_ids),
        )

        return await cls.update(
            review_id,
            {
                "assigned_to": reviewer_ids,
                "assigned_at": datetime.utcnow().isoformat(),
                "status": "assigned",
            },
        )

    @classmethod
    async def record_decision(
        cls,
        review_id: str,
        decision: str,
        reviewer_id: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Record a review decision (approve, reject, request changes, etc.).

        Args:
            review_id: Review UUID
            decision: Decision type (approve, reject, changes_requested, etc.)
            reviewer_id: User ID of reviewer
            comment: Optional comment from reviewer

        Returns:
            Updated review data

        """
        logger.info(
            "Recording review decision",
            review_id=review_id,
            decision=decision,
            reviewer_id=reviewer_id,
        )

        review = await cls.get_by_id(review_id)
        if not review:
            raise ValueError(f"Review not found: {review_id}")

        # Store decision history
        decisions = review.get("decisions") or []
        decisions.append(
            {
                "decision": decision,
                "reviewer_id": reviewer_id,
                "comment": comment,
                "decided_at": datetime.utcnow().isoformat(),
            }
        )

        # Update review status based on decision
        status_map = {
            "approve": "approved",
            "approved": "approved",
            "reject": "rejected",
            "rejected": "rejected",
            "changes_requested": "changes_requested",
        }
        new_status = status_map.get(decision, "pending")

        return await cls.update(
            review_id,
            {
                "decisions": decisions,
                "status": new_status,
                "decided_by": reviewer_id,
                "decided_at": datetime.utcnow().isoformat(),
            },
        )

    @classmethod
    async def get_pending_reviews(
        cls,
        domain_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all pending reviews, optionally filtered by domain."""
        filters = {"status": "pending"}
        if domain_id:
            filters["domain_id"] = domain_id

        return await cls.list_all(filters)

    @classmethod
    async def get_reviews_for_reviewer(
        cls,
        reviewer_id: str,
    ) -> list[dict[str, Any]]:
        """Get all reviews assigned to a specific reviewer.

        Args:
            reviewer_id: User ID of reviewer

        Returns:
            List of reviews

        """
        try:
            supabase = cls.get_client()

            # Query for reviews where reviewer_id is in assigned_to array
            response = (
                supabase.table(cls.table_name)
                .select("*")
                .contains("assigned_to", [reviewer_id])
                .eq("status", "assigned")
                .execute()
            )

            return response.data
        except Exception as e:
            logger.error(
                "Failed to get reviews for reviewer",
                reviewer_id=reviewer_id,
                error=str(e),
            )
            return []

    @classmethod
    async def get_review_history(
        cls,
        reviewable_type: str,
        reviewable_id: str,
    ) -> list[dict[str, Any]]:
        """Get all reviews for a specific item."""
        filters = {
            "reviewable_type": reviewable_type,
            "reviewable_id": reviewable_id,
        }
        return await cls.list_all(filters)

    @classmethod
    async def get_domain_review_stats(cls, domain_id: str) -> dict[str, Any]:
        """Get review statistics for a domain."""
        try:
            supabase = cls.get_client()

            response = (
                supabase.table(cls.table_name)
                .select("*")
                .eq("domain_id", domain_id)
                .execute()
            )

            reviews = response.data
            total = len(reviews)
            pending = len([r for r in reviews if r["status"] == "pending"])
            approved = len([r for r in reviews if r["status"] == "approved"])
            rejected = len([r for r in reviews if r["status"] == "rejected"])
            changes_requested = len(
                [r for r in reviews if r["status"] == "changes_requested"]
            )

            avg_decision_time = 0
            decided_reviews = [r for r in reviews if r.get("decided_at")]
            if decided_reviews:
                total_time = sum(
                    [
                        (
                            datetime.fromisoformat(r["decided_at"])
                            - datetime.fromisoformat(r["created_at"])
                        ).total_seconds()
                        for r in decided_reviews
                    ]
                )
                avg_decision_time = total_time / len(decided_reviews)

            return {
                "total_reviews": total,
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
                "changes_requested": changes_requested,
                "approval_rate": (approved / total * 100 if total > 0 else 0),
                "average_decision_time_seconds": avg_decision_time,
            }
        except Exception as e:
            logger.error(
                "Failed to get domain review stats",
                domain_id=domain_id,
                error=str(e),
            )
            return {}

    @classmethod
    async def close_review(
        cls,
        review_id: str,
        final_decision: str,
    ) -> dict[str, Any]:
        """Close a review and record final decision.

        Args:
            review_id: Review UUID
            final_decision: Final outcome (approved, rejected, etc.)

        Returns:
            Updated review data

        """
        logger.info(
            "Closing review",
            review_id=review_id,
            final_decision=final_decision,
        )

        return await cls.update(
            review_id,
            {
                "status": "closed",
                "final_decision": final_decision,
                "closed_at": datetime.utcnow().isoformat(),
            },
        )
