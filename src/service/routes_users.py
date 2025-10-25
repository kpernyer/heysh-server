"""User management routes."""

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException, Query, status

from src.app.auth.dependencies import CurrentUserId
from src.app.auth.models import UserModel
from src.app.clients.supabase import get_supabase_client

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    current_user_id: CurrentUserId,
) -> Dict[str, Any]:
    """Get user profile by user ID.
    
    Args:
        user_id: Target user ID
        current_user_id: Current authenticated user ID
        
    Returns:
        User profile information
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        # For now, users can only access their own profile
        # TODO: Add role-based access control for admin users
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Can only view own profile"
            )
        
        user = await UserModel.get_user_by_id(user_id)
        
        if not user:
            logger.warning("User not found", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user["id"],
            "email": user["email"],
            "role": user.get("role", "contributor"),
            "domain_id": user.get("domain_id"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
            "profile": {
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "avatar_url": user.get("avatar_url"),
                "bio": user.get("bio"),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user profile", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.get("/{user_id}/domains")
async def get_user_domains(
    user_id: str,
    current_user_id: CurrentUserId,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of domains to return"),
    offset: int = Query(0, ge=0, description="Number of domains to skip"),
) -> Dict[str, Any]:
    """Get domains owned by or where user is a member.
    
    Args:
        user_id: Target user ID
        current_user_id: Current authenticated user ID
        limit: Maximum number of domains to return
        offset: Number of domains to skip
        
    Returns:
        List of domains with user's role
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        # For now, users can only access their own domains
        # TODO: Add role-based access control for admin users
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Can only view own domains"
            )
        
        supabase = get_supabase_client()
        
        # Get domains where user is owner
        owned_response = supabase.table("domains").select("*").eq("owner_id", user_id).execute()
        
        # Get domains where user is a member (through domain_members table)
        memberships_response = supabase.table("domain_members").select(
            "domain_id, role, domains(*)"
        ).eq("user_id", user_id).execute()
        
        owned_domains = owned_response.data or []
        member_domains = []
        
        for membership in memberships_response.data or []:
            if membership.get("domains"):
                domain = membership["domains"]
                domain["user_role"] = membership.get("role", "member")
                member_domains.append(domain)
        
        # Combine and deduplicate (in case user is both owner and member)
        all_domains = owned_domains + member_domains
        unique_domains = {}
        
        for domain in all_domains:
            domain_id = domain["id"]
            if domain_id not in unique_domains:
                unique_domains[domain_id] = domain
            else:
                # If user is both owner and member, prioritize owner role
                if domain.get("user_role") != "owner":
                    unique_domains[domain_id]["user_role"] = "owner"
        
        domains_list = list(unique_domains.values())
        
        # Apply pagination
        total_count = len(domains_list)
        paginated_domains = domains_list[offset:offset + limit]
        
        return {
            "domains": paginated_domains,
            "total_count": total_count,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user domains", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user domains"
        )


@router.get("/{user_id}/membership-requests")
async def get_user_membership_requests(
    user_id: str,
    current_user_id: CurrentUserId,
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of requests to return"),
    offset: int = Query(0, ge=0, description="Number of requests to skip"),
) -> Dict[str, Any]:
    """Get membership requests for a user.
    
    Args:
        user_id: Target user ID
        current_user_id: Current authenticated user ID
        status_filter: Optional status filter
        limit: Maximum number of requests to return
        offset: Number of requests to skip
        
    Returns:
        List of membership requests
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        # For now, users can only access their own membership requests
        # TODO: Add role-based access control for admin users
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Can only view own membership requests"
            )
        
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table("membership_requests").select(
            "*, domains(name, description), users(email, first_name, last_name)"
        ).eq("user_id", user_id)
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        
        return {
            "membership_requests": response.data or [],
            "total_count": len(response.data or []),
            "filters": {
                "status": status_filter
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user membership requests", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user membership requests"
        )
