"""Collaboration Service Connector - SCI Compliant.

Topics and memberships for knowledge collaboration.
"""

from typing import Any, List, Optional

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.app.auth.dependencies import CurrentUserId
from src.app.clients.supabase import get_supabase_client

logger = structlog.get_logger()

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])


# ==================== Models ====================

class TopicBase(BaseModel):
    """Base model for Topic."""
    name: str = Field(..., description="Topic name")
    description: Optional[str] = Field(None, description="Topic description")
    is_public: bool = Field(False, description="Whether topic is publicly accessible")


class TopicCreate(TopicBase):
    """Request model for creating a topic."""
    pass


class TopicUpdate(BaseModel):
    """Request model for updating a topic."""
    name: Optional[str] = Field(None, description="Topic name")
    description: Optional[str] = Field(None, description="Topic description")
    is_public: Optional[bool] = Field(None, description="Public accessibility")


class Topic(TopicBase):
    """Response model for a topic."""
    id: str
    owner_id: str
    created_at: str
    updated_at: str
    member_count: int = Field(0, description="Number of members")
    knowledge_item_count: int = Field(0, description="Number of knowledge items")


class MembershipBase(BaseModel):
    """Base model for Membership."""
    role: str = Field(..., pattern="^(owner|controller|contributor|member)$")


class MembershipCreate(BaseModel):
    """Request model for adding a member."""
    user_email: str = Field(..., description="Email of user to add")
    role: str = Field("member", pattern="^(contributor|controller|member)$")


class MembershipUpdate(BaseModel):
    """Request model for updating membership."""
    role: str = Field(..., pattern="^(contributor|controller|member)$")


class Membership(MembershipBase):
    """Response model for membership."""
    id: str
    topic_id: str
    user_id: str
    user_email: str
    user_full_name: Optional[str]
    joined_at: str


# ==================== Topic Resources ====================

@router.get("/topic", response_model=List[Topic])
async def list_topics(
    user_id: CurrentUserId,
    include_public: bool = Query(True, description="Include public topics"),
    my_topics_only: bool = Query(False, description="Only show topics I'm a member of"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Topic]:
    """List topics accessible to the user.

    Returns topics where user is a member, plus public topics if requested.
    """
    try:
        supabase = get_supabase_client()

        # Build query based on filters
        if my_topics_only:
            # Get topics where user is a member
            member_response = supabase.table("domain_members").select(
                "domain_id"
            ).eq("user_id", user_id).execute()

            topic_ids = [m["domain_id"] for m in member_response.data]

            topics_response = supabase.table("domains").select(
                "*",
                "domain_members(count)"
            ).in_("id", topic_ids).range(offset, offset + limit - 1).execute()

        else:
            # Get all accessible topics (member or public)
            if include_public:
                # Complex query: user's topics OR public topics
                topics_response = supabase.table("domains").select(
                    "*",
                    "domain_members(count)"
                ).or_(
                    f"is_public.eq.true,domain_members.user_id.eq.{user_id}"
                ).range(offset, offset + limit - 1).execute()
            else:
                # Only user's topics
                topics_response = supabase.table("domains").select(
                    "*",
                    "domain_members(count)"
                ).eq("domain_members.user_id", user_id).range(
                    offset, offset + limit - 1
                ).execute()

        # Transform to Topic model
        topics = []
        for topic_data in topics_response.data:
            topic = Topic(
                id=topic_data["id"],
                name=topic_data["name"],
                description=topic_data.get("description"),
                is_public=topic_data.get("is_public", False),
                owner_id=topic_data["owner_id"],
                created_at=topic_data["created_at"],
                updated_at=topic_data["updated_at"],
                member_count=len(topic_data.get("domain_members", [])),
                knowledge_item_count=0  # TODO: Add document count
            )
            topics.append(topic)

        return topics

    except Exception as e:
        logger.error("Failed to list topics", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list topics: {e}"
        )


@router.post("/topic", response_model=Topic, status_code=status.HTTP_201_CREATED)
async def create_topic(
    request: TopicCreate,
    user_id: CurrentUserId,
) -> Topic:
    """Create a new topic.

    Creator becomes the owner of the topic.
    """
    try:
        supabase = get_supabase_client()

        # Create the topic (domain in current schema)
        topic_data = {
            "name": request.name,
            "description": request.description,
            "is_public": request.is_public,
            "owner_id": user_id,
        }

        topic_response = supabase.table("domains").insert(topic_data).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create topic"
            )

        created_topic = topic_response.data[0]

        # Add creator as owner member
        member_data = {
            "domain_id": created_topic["id"],
            "user_id": user_id,
            "role": "owner",
        }

        supabase.table("domain_members").insert(member_data).execute()

        return Topic(
            id=created_topic["id"],
            name=created_topic["name"],
            description=created_topic.get("description"),
            is_public=created_topic.get("is_public", False),
            owner_id=created_topic["owner_id"],
            created_at=created_topic["created_at"],
            updated_at=created_topic["updated_at"],
            member_count=1,  # Just the owner
            knowledge_item_count=0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create topic", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create topic: {e}"
        )


@router.get("/topic/{topic_id}", response_model=Topic)
async def get_topic(
    topic_id: str,
    user_id: CurrentUserId,
) -> Topic:
    """Get a specific topic by ID.

    User must be a member or topic must be public.
    """
    try:
        supabase = get_supabase_client()

        # Get topic with member count
        topic_response = supabase.table("domains").select(
            "*",
            "domain_members(count)"
        ).eq("id", topic_id).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic not found: {topic_id}"
            )

        topic_data = topic_response.data[0]

        # Check access: user must be member or topic must be public
        if not topic_data.get("is_public", False):
            member_check = supabase.table("domain_members").select(
                "id"
            ).eq("domain_id", topic_id).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Topic not found"
                )

        return Topic(
            id=topic_data["id"],
            name=topic_data["name"],
            description=topic_data.get("description"),
            is_public=topic_data.get("is_public", False),
            owner_id=topic_data["owner_id"],
            created_at=topic_data["created_at"],
            updated_at=topic_data["updated_at"],
            member_count=len(topic_data.get("domain_members", [])),
            knowledge_item_count=0  # TODO: Add document count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get topic", topic_id=topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get topic: {e}"
        )


@router.put("/topic/{topic_id}", response_model=Topic)
async def update_topic(
    topic_id: str,
    request: TopicUpdate,
    user_id: CurrentUserId,
) -> Topic:
    """Update a topic.

    User must be owner or controller of the topic.
    """
    try:
        supabase = get_supabase_client()

        # Check user's role in the topic
        member_response = supabase.table("domain_members").select(
            "role"
        ).eq("domain_id", topic_id).eq("user_id", user_id).execute()

        if not member_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )

        user_role = member_response.data[0]["role"]

        # Only owner and controller can update
        if user_role not in ["owner", "controller"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and controllers can update topics"
            )

        # Build update data
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.is_public is not None:
            # Only owner can change public status
            if user_role != "owner":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only owner can change public status"
                )
            update_data["is_public"] = request.is_public

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Update the topic
        update_response = supabase.table("domains").update(
            update_data
        ).eq("id", topic_id).execute()

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic not found: {topic_id}"
            )

        updated_topic = update_response.data[0]

        # Get member count
        member_count_response = supabase.table("domain_members").select(
            "count"
        ).eq("domain_id", topic_id).execute()

        return Topic(
            id=updated_topic["id"],
            name=updated_topic["name"],
            description=updated_topic.get("description"),
            is_public=updated_topic.get("is_public", False),
            owner_id=updated_topic["owner_id"],
            created_at=updated_topic["created_at"],
            updated_at=updated_topic["updated_at"],
            member_count=member_count_response.count if member_count_response else 0,
            knowledge_item_count=0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update topic", topic_id=topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update topic: {e}"
        )


@router.delete("/topic/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: str,
    user_id: CurrentUserId,
) -> None:
    """Delete a topic.

    Only the owner can delete a topic.
    """
    try:
        supabase = get_supabase_client()

        # Check if user is owner
        topic_response = supabase.table("domains").select(
            "owner_id"
        ).eq("id", topic_id).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )

        if topic_response.data[0]["owner_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can delete a topic"
            )

        # Delete the topic (cascade will handle members, documents, etc.)
        supabase.table("domains").delete().eq("id", topic_id).execute()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete topic", topic_id=topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete topic: {e}"
        )


# ==================== Membership Resources (Hierarchical) ====================

@router.get("/topic/{topic_id}/membership", response_model=List[Membership])
async def list_topic_memberships(
    topic_id: str,
    user_id: CurrentUserId,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Membership]:
    """List memberships of a topic.

    User must be a member or topic must be public.
    """
    try:
        supabase = get_supabase_client()

        # Check access
        topic_response = supabase.table("domains").select(
            "is_public"
        ).eq("id", topic_id).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )

        is_public = topic_response.data[0].get("is_public", False)

        if not is_public:
            # Check if user is member
            member_check = supabase.table("domain_members").select(
                "id"
            ).eq("domain_id", topic_id).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Topic not found"
                )

        # Get members with user details
        members_response = supabase.table("domain_members").select(
            "*",
            "profiles:user_id(email, full_name)"
        ).eq("domain_id", topic_id).range(offset, offset + limit - 1).execute()

        memberships = []
        for member_data in members_response.data:
            profile = member_data.get("profiles", {})
            membership = Membership(
                id=member_data["id"],
                topic_id=member_data["domain_id"],
                user_id=member_data["user_id"],
                user_email=profile.get("email", ""),
                user_full_name=profile.get("full_name"),
                role=member_data["role"],
                joined_at=member_data["created_at"]
            )
            memberships.append(membership)

        return memberships

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list topic memberships", topic_id=topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list topic memberships: {e}"
        )


@router.post("/topic/{topic_id}/membership", response_model=Membership, status_code=status.HTTP_201_CREATED)
async def add_topic_membership(
    topic_id: str,
    request: MembershipCreate,
    user_id: CurrentUserId,
) -> Membership:
    """Add a member to a topic.

    User must be owner or controller to add members.
    """
    try:
        supabase = get_supabase_client()

        # Check user's role
        member_response = supabase.table("domain_members").select(
            "role"
        ).eq("domain_id", topic_id).eq("user_id", user_id).execute()

        if not member_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )

        user_role = member_response.data[0]["role"]

        # Only owner and controller can add members
        if user_role not in ["owner", "controller"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and controllers can add members"
            )

        # Only owner can add controllers
        if request.role == "controller" and user_role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can add controllers"
            )

        # Find user by email
        user_response = supabase.table("profiles").select(
            "id", "email", "full_name"
        ).eq("email", request.user_email).execute()

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found with email: {request.user_email}"
            )

        new_member_profile = user_response.data[0]
        new_member_id = new_member_profile["id"]

        # Check if already a member
        existing_member = supabase.table("domain_members").select(
            "id"
        ).eq("domain_id", topic_id).eq("user_id", new_member_id).execute()

        if existing_member.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this topic"
            )

        # Add member
        member_data = {
            "domain_id": topic_id,
            "user_id": new_member_id,
            "role": request.role,
        }

        add_response = supabase.table("domain_members").insert(member_data).execute()

        if not add_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add member"
            )

        added_member = add_response.data[0]

        return Membership(
            id=added_member["id"],
            topic_id=added_member["domain_id"],
            user_id=added_member["user_id"],
            user_email=new_member_profile["email"],
            user_full_name=new_member_profile.get("full_name"),
            role=added_member["role"],
            joined_at=added_member["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add topic membership", topic_id=topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add topic membership: {e}"
        )


@router.put("/topic/{topic_id}/membership/{membership_id}", response_model=Membership)
async def update_membership_role(
    topic_id: str,
    membership_id: str,
    request: MembershipUpdate,
    user_id: CurrentUserId,
) -> Membership:
    """Update a membership's role.

    Only owner can change roles.
    """
    try:
        supabase = get_supabase_client()

        # Check if user is owner
        owner_check = supabase.table("domain_members").select(
            "role"
        ).eq("domain_id", topic_id).eq("user_id", user_id).execute()

        if not owner_check.data or owner_check.data[0]["role"] != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can change member roles"
            )

        # Can't change owner's role
        member_to_update = supabase.table("domain_members").select(
            "role", "user_id", "domain_id"
        ).eq("id", membership_id).execute()

        if not member_to_update.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found"
            )

        if member_to_update.data[0]["domain_id"] != topic_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found in this topic"
            )

        if member_to_update.data[0]["role"] == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change owner's role"
            )

        # Update role
        update_response = supabase.table("domain_members").update(
            {"role": request.role}
        ).eq("id", membership_id).execute()

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update membership role"
            )

        updated_member = update_response.data[0]

        # Get user profile
        profile_response = supabase.table("profiles").select(
            "email", "full_name"
        ).eq("id", updated_member["user_id"]).execute()

        profile = profile_response.data[0] if profile_response.data else {}

        return Membership(
            id=updated_member["id"],
            topic_id=updated_member["domain_id"],
            user_id=updated_member["user_id"],
            user_email=profile.get("email", ""),
            user_full_name=profile.get("full_name"),
            role=updated_member["role"],
            joined_at=updated_member["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update membership", topic_id=topic_id, membership_id=membership_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update membership role: {e}"
        )


@router.delete("/topic/{topic_id}/membership/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_topic_membership(
    topic_id: str,
    membership_id: str,
    user_id: CurrentUserId,
) -> None:
    """Remove a member from a topic.

    Owner and controller can remove members (except owner).
    Members can remove themselves.
    """
    try:
        supabase = get_supabase_client()

        # Get current user's membership
        current_user_member = supabase.table("domain_members").select(
            "id", "role"
        ).eq("domain_id", topic_id).eq("user_id", user_id).execute()

        if not current_user_member.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )

        current_user_role = current_user_member.data[0]["role"]
        current_user_membership_id = current_user_member.data[0]["id"]

        # Get target membership
        target_member = supabase.table("domain_members").select(
            "role", "user_id", "domain_id"
        ).eq("id", membership_id).execute()

        if not target_member.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found"
            )

        if target_member.data[0]["domain_id"] != topic_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Membership not found in this topic"
            )

        target_role = target_member.data[0]["role"]

        # Can't remove owner
        if target_role == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the owner from a topic"
            )

        # Check permissions
        if membership_id == current_user_membership_id:
            # User removing themselves - always allowed
            pass
        elif current_user_role in ["owner", "controller"]:
            # Owner/controller can remove others
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to remove this member"
            )

        # Remove member
        supabase.table("domain_members").delete().eq("id", membership_id).execute()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove membership", topic_id=topic_id, membership_id=membership_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove membership: {e}"
        )


# ==================== User's Memberships (Top-level) ====================

@router.get("/membership", response_model=List[Membership])
async def list_user_memberships(
    user_id: CurrentUserId,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Membership]:
    """List all memberships for the current user.

    Returns all topics where the user is a member.
    """
    try:
        supabase = get_supabase_client()

        # Get user's memberships
        memberships_response = supabase.table("domain_members").select(
            "*",
            "domains!inner(name)"
        ).eq("user_id", user_id).range(offset, offset + limit - 1).execute()

        # Get user profile
        profile_response = supabase.table("profiles").select(
            "email", "full_name"
        ).eq("id", user_id).execute()

        profile = profile_response.data[0] if profile_response.data else {}

        memberships = []
        for member_data in memberships_response.data:
            membership = Membership(
                id=member_data["id"],
                topic_id=member_data["domain_id"],
                user_id=member_data["user_id"],
                user_email=profile.get("email", ""),
                user_full_name=profile.get("full_name"),
                role=member_data["role"],
                joined_at=member_data["created_at"]
            )
            memberships.append(membership)

        return memberships

    except Exception as e:
        logger.error("Failed to list user memberships", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list user memberships: {e}"
        )
