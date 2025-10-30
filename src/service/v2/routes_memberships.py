"""Memberships API routes - Manage user memberships across topics."""

from typing import Any, List, Optional
from enum import Enum

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.app.auth.dependencies import CurrentUserId
from src.app.clients.supabase import get_supabase_client

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v2/memberships", tags=["Memberships"])


# ==================== Models ====================

class MembershipStatus(str, Enum):
    """Status of a membership request."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class MembershipRole(str, Enum):
    """Roles within a topic."""
    OWNER = "owner"
    CONTROLLER = "controller"
    CONTRIBUTOR = "contributor"
    MEMBER = "member"


class Membership(BaseModel):
    """User's membership in a topic."""
    id: str
    topic_id: str
    topic_name: str
    topic_description: Optional[str]
    role: MembershipRole
    joined_at: str
    is_active: bool = True


class MembershipRequest(BaseModel):
    """Request to join a topic."""
    id: str
    topic_id: str
    topic_name: str
    user_id: str
    user_email: str
    user_name: Optional[str]
    status: MembershipStatus
    message: Optional[str] = Field(None, description="Request message from user")
    response_message: Optional[str] = Field(None, description="Response from topic owner/controller")
    requested_at: str
    responded_at: Optional[str]
    responded_by: Optional[str]


class CreateMembershipRequest(BaseModel):
    """Create a new membership request."""
    topic_id: str
    message: Optional[str] = Field(None, max_length=500, description="Optional message to topic owner")


class RespondToMembershipRequest(BaseModel):
    """Response to a membership request."""
    action: str = Field(..., pattern="^(accept|reject)$")
    response_message: Optional[str] = Field(None, max_length=500)
    role: Optional[MembershipRole] = Field(MembershipRole.MEMBER, description="Role to assign if accepting")


# ==================== User's Memberships ====================

@router.get("/", response_model=List[Membership])
async def list_my_memberships(
    user_id: CurrentUserId,
    active_only: bool = Query(True, description="Only show active memberships"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Membership]:
    """List current user's topic memberships."""
    try:
        supabase = get_supabase_client()

        # Get user's memberships with topic details
        query = supabase.table("domain_members").select(
            "*",
            "domains:domain_id(id, name, description)"
        ).eq("user_id", user_id)

        if active_only:
            query = query.eq("is_active", True)

        memberships_response = query.range(offset, offset + limit - 1).execute()

        memberships = []
        for membership_data in memberships_response.data:
            topic = membership_data.get("domains", {})
            membership = Membership(
                id=membership_data["id"],
                topic_id=membership_data["domain_id"],
                topic_name=topic.get("name", "Unknown"),
                topic_description=topic.get("description"),
                role=MembershipRole(membership_data["role"]),
                joined_at=membership_data["created_at"],
                is_active=membership_data.get("is_active", True)
            )
            memberships.append(membership)

        return memberships

    except Exception as e:
        logger.error("Failed to list memberships", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list memberships: {e}"
        )


# ==================== Membership Requests ====================

@router.post("/requests", response_model=MembershipRequest, status_code=status.HTTP_201_CREATED)
async def request_membership(
    request: CreateMembershipRequest,
    user_id: CurrentUserId,
) -> MembershipRequest:
    """Request membership to a topic.

    Creates a pending request that must be approved by topic owner/controller.
    """
    try:
        supabase = get_supabase_client()

        # Check if topic exists and get its info
        topic_response = supabase.table("domains").select(
            "id", "name", "is_public"
        ).eq("id", request.topic_id).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic not found: {request.topic_id}"
            )

        topic = topic_response.data[0]

        # Check if user is already a member
        existing_member = supabase.table("domain_members").select(
            "id"
        ).eq("domain_id", request.topic_id).eq("user_id", user_id).execute()

        if existing_member.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a member of this topic"
            )

        # Check for existing pending request
        existing_request = supabase.table("membership_requests").select(
            "id"
        ).eq("domain_id", request.topic_id).eq("user_id", user_id).eq(
            "status", MembershipStatus.PENDING.value
        ).execute()

        if existing_request.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a pending request for this topic"
            )

        # Get user profile
        user_profile = supabase.table("profiles").select(
            "email", "full_name"
        ).eq("id", user_id).execute()

        user_data = user_profile.data[0] if user_profile.data else {"email": "", "full_name": None}

        # Create membership request
        request_data = {
            "domain_id": request.topic_id,
            "user_id": user_id,
            "status": MembershipStatus.PENDING.value,
            "message": request.message,
        }

        create_response = supabase.table("membership_requests").insert(request_data).execute()

        if not create_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create membership request"
            )

        created_request = create_response.data[0]

        return MembershipRequest(
            id=created_request["id"],
            topic_id=created_request["domain_id"],
            topic_name=topic["name"],
            user_id=created_request["user_id"],
            user_email=user_data["email"],
            user_name=user_data.get("full_name"),
            status=MembershipStatus(created_request["status"]),
            message=created_request.get("message"),
            response_message=None,
            requested_at=created_request["created_at"],
            responded_at=None,
            responded_by=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to request membership", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request membership: {e}"
        )


@router.get("/requests", response_model=List[MembershipRequest])
async def list_membership_requests(
    user_id: CurrentUserId,
    request_type: str = Query("my_requests", pattern="^(my_requests|pending_approvals)$"),
    status_filter: Optional[MembershipStatus] = Query(None),
    topic_id: Optional[str] = Query(None, description="Filter by topic"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[MembershipRequest]:
    """List membership requests.

    - my_requests: Requests created by the current user
    - pending_approvals: Requests waiting for approval in topics where user is owner/controller
    """
    try:
        supabase = get_supabase_client()

        if request_type == "my_requests":
            # Get user's own requests
            query = supabase.table("membership_requests").select(
                "*",
                "domains:domain_id(name)",
                "profiles:responded_by(email, full_name)"
            ).eq("user_id", user_id)

        else:  # pending_approvals
            # Get topics where user is owner/controller
            member_response = supabase.table("domain_members").select(
                "domain_id"
            ).eq("user_id", user_id).in_("role", ["owner", "controller"]).execute()

            topic_ids = [m["domain_id"] for m in member_response.data]

            if not topic_ids:
                return []  # No topics to manage

            # Get pending requests for those topics
            query = supabase.table("membership_requests").select(
                "*",
                "domains:domain_id(name)",
                "profiles:user_id(email, full_name)"
            ).in_("domain_id", topic_ids)

            # Default to pending for approvals view
            if not status_filter:
                status_filter = MembershipStatus.PENDING

        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter.value)

        if topic_id:
            query = query.eq("domain_id", topic_id)

        # Execute query with pagination
        requests_response = query.range(offset, offset + limit - 1).execute()

        # Transform to response model
        requests = []
        for request_data in requests_response.data:
            # Get user info (depends on request_type)
            if request_type == "my_requests":
                user_info = {"email": user_id, "full_name": None}  # Current user
                responder = request_data.get("profiles", {})
            else:
                user_info = request_data.get("profiles", {})
                responder = None

            membership_request = MembershipRequest(
                id=request_data["id"],
                topic_id=request_data["domain_id"],
                topic_name=request_data.get("domains", {}).get("name", "Unknown"),
                user_id=request_data["user_id"],
                user_email=user_info.get("email", ""),
                user_name=user_info.get("full_name"),
                status=MembershipStatus(request_data["status"]),
                message=request_data.get("message"),
                response_message=request_data.get("response_message"),
                requested_at=request_data["created_at"],
                responded_at=request_data.get("responded_at"),
                responded_by=responder.get("email") if responder else None
            )
            requests.append(membership_request)

        return requests

    except Exception as e:
        logger.error("Failed to list membership requests", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list membership requests: {e}"
        )


@router.put("/requests/{request_id}", response_model=MembershipRequest)
async def respond_to_membership_request(
    request_id: str,
    response: RespondToMembershipRequest,
    user_id: CurrentUserId,
) -> MembershipRequest:
    """Accept or reject a membership request.

    Only topic owner/controller can respond to requests.
    """
    try:
        supabase = get_supabase_client()

        # Get the request details
        request_response = supabase.table("membership_requests").select(
            "*",
            "domains:domain_id(id, name)"
        ).eq("id", request_id).execute()

        if not request_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request not found: {request_id}"
            )

        membership_request = request_response.data[0]
        topic = membership_request.get("domains", {})

        # Check if request is pending
        if membership_request["status"] != MembershipStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request is not pending, current status: {membership_request['status']}"
            )

        # Check user's permission in the topic
        permission_check = supabase.table("domain_members").select(
            "role"
        ).eq("domain_id", membership_request["domain_id"]).eq("user_id", user_id).execute()

        if not permission_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this topic"
            )

        user_role = permission_check.data[0]["role"]

        if user_role not in ["owner", "controller"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and controllers can respond to membership requests"
            )

        # Only owner can assign controller role
        if response.role == MembershipRole.CONTROLLER and user_role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can assign controller role"
            )

        # Update request status
        update_data = {
            "status": MembershipStatus.ACCEPTED.value if response.action == "accept" else MembershipStatus.REJECTED.value,
            "response_message": response.response_message,
            "responded_by": user_id,
            "responded_at": "now()"  # Database function
        }

        update_response = supabase.table("membership_requests").update(
            update_data
        ).eq("id", request_id).execute()

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update request"
            )

        updated_request = update_response.data[0]

        # If accepted, add user to topic
        if response.action == "accept":
            member_data = {
                "domain_id": membership_request["domain_id"],
                "user_id": membership_request["user_id"],
                "role": response.role.value if response.role else MembershipRole.MEMBER.value
            }

            supabase.table("domain_members").insert(member_data).execute()

        # Get user info for response
        user_info = supabase.table("profiles").select(
            "email", "full_name"
        ).eq("id", membership_request["user_id"]).execute()

        user_data = user_info.data[0] if user_info.data else {"email": "", "full_name": None}

        return MembershipRequest(
            id=updated_request["id"],
            topic_id=updated_request["domain_id"],
            topic_name=topic.get("name", "Unknown"),
            user_id=updated_request["user_id"],
            user_email=user_data["email"],
            user_name=user_data.get("full_name"),
            status=MembershipStatus(updated_request["status"]),
            message=updated_request.get("message"),
            response_message=updated_request.get("response_message"),
            requested_at=updated_request["created_at"],
            responded_at=updated_request.get("responded_at"),
            responded_by=user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to respond to membership request", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to respond to membership request: {e}"
        )


@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_membership_request(
    request_id: str,
    user_id: CurrentUserId,
) -> None:
    """Cancel a pending membership request.

    Only the requester can cancel their own request.
    """
    try:
        supabase = get_supabase_client()

        # Get the request
        request_response = supabase.table("membership_requests").select(
            "user_id", "status"
        ).eq("id", request_id).execute()

        if not request_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request not found: {request_id}"
            )

        membership_request = request_response.data[0]

        # Check ownership
        if membership_request["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own requests"
            )

        # Check status
        if membership_request["status"] != MembershipStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending requests can be cancelled"
            )

        # Update to cancelled
        supabase.table("membership_requests").update(
            {"status": MembershipStatus.CANCELLED.value}
        ).eq("id", request_id).execute()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel membership request", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel membership request: {e}"
        )


# ==================== Leave Topic ====================

@router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_topic(
    membership_id: str,
    user_id: CurrentUserId,
) -> None:
    """Leave a topic (remove own membership).

    Cannot leave if you are the owner - must transfer ownership first.
    """
    try:
        supabase = get_supabase_client()

        # Get membership details
        membership_response = supabase.table("domain_members").select(
            "user_id", "role", "domain_id"
        ).eq("id", membership_id).execute()

        if not membership_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Membership not found: {membership_id}"
            )

        membership = membership_response.data[0]

        # Check ownership
        if membership["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only remove your own membership"
            )

        # Cannot leave if owner
        if membership["role"] == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owners cannot leave topics. Transfer ownership first."
            )

        # Remove membership
        supabase.table("domain_members").delete().eq("id", membership_id).execute()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to leave topic", membership_id=membership_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to leave topic: {e}"
        )