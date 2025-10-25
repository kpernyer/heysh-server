"""Membership management routes."""

from typing import Any, Dict, Optional

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.app.auth.dependencies import CurrentUserId
from src.app.clients.supabase import get_supabase_client

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/membership-requests", tags=["membership"])


class CreateMembershipRequestRequest(BaseModel):
    """Request model for creating a membership request."""
    domain_id: str
    message: Optional[str] = None


class MembershipRequestResponse(BaseModel):
    """Response model for membership request."""
    id: str
    user_id: str
    domain_id: str
    status: str
    message: Optional[str] = None
    created_at: str
    updated_at: str


@router.post("/", response_model=MembershipRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_membership_request(
    request: CreateMembershipRequestRequest,
    user_id: CurrentUserId,
) -> MembershipRequestResponse:
    """Create a new membership request for a domain.
    
    Args:
        request: Membership request data
        user_id: Current authenticated user ID
        
    Returns:
        Created membership request
        
    Raises:
        HTTPException: If domain not found or request already exists
    """
    try:
        supabase = get_supabase_client()
        
        # Check if domain exists
        domain_response = supabase.table("domains").select("id, name").eq("id", request.domain_id).execute()
        
        if not domain_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain not found"
            )
        
        # Check if user is already a member
        existing_member_response = supabase.table("domain_members").select("id").eq("user_id", user_id).eq("domain_id", request.domain_id).execute()
        
        if existing_member_response.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this domain"
            )
        
        # Check if there's already a pending request
        existing_request_response = supabase.table("membership_requests").select("id").eq("user_id", user_id).eq("domain_id", request.domain_id).eq("status", "pending").execute()
        
        if existing_request_response.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending membership request already exists for this domain"
            )
        
        # Create the membership request
        membership_request_data = {
            "user_id": user_id,
            "domain_id": request.domain_id,
            "status": "pending",
            "message": request.message
        }
        
        response = supabase.table("membership_requests").insert(membership_request_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create membership request"
            )
        
        created_request = response.data[0]
        
        logger.info(
            "Membership request created",
            user_id=user_id,
            domain_id=request.domain_id,
            request_id=created_request["id"]
        )
        
        return MembershipRequestResponse(
            id=created_request["id"],
            user_id=created_request["user_id"],
            domain_id=created_request["domain_id"],
            status=created_request["status"],
            message=created_request.get("message"),
            created_at=created_request["created_at"],
            updated_at=created_request["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create membership request", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create membership request"
        )
