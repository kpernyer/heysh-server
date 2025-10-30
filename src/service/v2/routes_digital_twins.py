"""Digital Twins API routes - Manage digital representations of users."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl

from src.app.auth.dependencies import CurrentUserId
from src.app.clients.supabase import get_supabase_client

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v2/digital-twins", tags=["Digital Twins"])


# ==================== Models ====================

class PresenceStatus(str, Enum):
    """User presence status."""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    DO_NOT_DISTURB = "do_not_disturb"
    OFFLINE = "offline"


class WorkStyle(str, Enum):
    """User's preferred work style."""
    DEEP_FOCUS = "deep_focus"
    COLLABORATIVE = "collaborative"
    BALANCED = "balanced"
    FLEXIBLE = "flexible"


class TimeZone(BaseModel):
    """User's timezone information."""
    name: str = Field(..., description="Timezone name (e.g., 'America/New_York')")
    offset: int = Field(..., description="UTC offset in minutes")
    is_dst: bool = Field(False, description="Is daylight saving time active")


class WorkingHours(BaseModel):
    """User's working hours."""
    start: str = Field(..., pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="Start time (HH:MM)")
    end: str = Field(..., pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="End time (HH:MM)")
    days: List[str] = Field(..., description="Working days (e.g., ['monday', 'tuesday', ...])")
    timezone: TimeZone


class CommunicationPreferences(BaseModel):
    """User's communication preferences."""
    preferred_channels: List[str] = Field(default_factory=list, description="Preferred communication channels")
    response_time_expectation: str = Field("within_24_hours", description="Expected response time")
    notification_settings: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email": True,
            "push": True,
            "sms": False,
            "in_app": True
        }
    )
    quiet_hours_enabled: bool = Field(False)
    quiet_hours_start: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")


class Expertise(BaseModel):
    """Area of expertise."""
    domain: str = Field(..., description="Domain of expertise")
    level: str = Field(..., pattern="^(beginner|intermediate|advanced|expert)$")
    years_experience: Optional[int] = Field(None, ge=0)
    certifications: List[str] = Field(default_factory=list)


class DigitalTwin(BaseModel):
    """Complete digital twin representation of a user."""
    # Basic Information
    user_id: str
    email: str
    full_name: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[HttpUrl]
    bio: Optional[str] = Field(None, max_length=500)

    # Professional Information
    title: Optional[str]
    department: Optional[str]
    organization: Optional[str]
    location: Optional[str]

    # Availability & Presence
    presence_status: PresenceStatus
    presence_message: Optional[str] = Field(None, max_length=200)
    last_seen: Optional[datetime]
    is_available: bool

    # Work Preferences
    work_style: Optional[WorkStyle]
    working_hours: Optional[WorkingHours]
    communication_preferences: CommunicationPreferences

    # Skills & Expertise
    skills: List[str] = Field(default_factory=list, max_items=50)
    expertise: List[Expertise] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

    # Collaboration Info
    current_projects: List[str] = Field(default_factory=list, description="Current project/topic IDs")
    collaboration_notes: Optional[str] = Field(None, max_length=1000, description="Notes for collaborators")

    # AI Assistant Settings
    ai_personality: str = Field("professional", description="AI personality type for interactions")
    ai_context: Dict[str, Any] = Field(default_factory=dict, description="Context for AI interactions")
    auto_respond_enabled: bool = Field(False, description="Enable AI auto-responses when unavailable")
    auto_response_rules: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    created_at: datetime
    updated_at: datetime
    version: int = Field(1, description="Digital twin version for tracking changes")


class DigitalTwinUpdate(BaseModel):
    """Update request for digital twin."""
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    bio: Optional[str] = Field(None, max_length=500)
    title: Optional[str] = None
    department: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    presence_status: Optional[PresenceStatus] = None
    presence_message: Optional[str] = Field(None, max_length=200)
    work_style: Optional[WorkStyle] = None
    working_hours: Optional[WorkingHours] = None
    communication_preferences: Optional[CommunicationPreferences] = None
    skills: Optional[List[str]] = Field(None, max_items=50)
    expertise: Optional[List[Expertise]] = None
    languages: Optional[List[str]] = None
    collaboration_notes: Optional[str] = Field(None, max_length=1000)
    ai_personality: Optional[str] = None
    auto_respond_enabled: Optional[bool] = None


class DigitalTwinSummary(BaseModel):
    """Summary view of a digital twin."""
    user_id: str
    email: str
    display_name: str
    avatar_url: Optional[HttpUrl]
    presence_status: PresenceStatus
    is_available: bool
    title: Optional[str]
    organization: Optional[str]


# ==================== Get My Digital Twin ====================

@router.get("/me", response_model=DigitalTwin)
async def get_my_digital_twin(
    user_id: CurrentUserId,
) -> DigitalTwin:
    """Get current user's digital twin."""
    try:
        supabase = get_supabase_client()

        # Get user profile
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()

        if not profile_response.data:
            # Create default digital twin
            default_twin = {
                "id": user_id,
                "email": "",  # Would be filled from auth
                "presence_status": PresenceStatus.OFFLINE.value,
                "is_available": False,
                "communication_preferences": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            supabase.table("profiles").insert(default_twin).execute()
            profile_data = default_twin
        else:
            profile_data = profile_response.data[0]

        # Get current projects (topics where user is member)
        member_response = supabase.table("domain_members").select(
            "domain_id"
        ).eq("user_id", user_id).execute()

        current_projects = [m["domain_id"] for m in member_response.data]

        # Build digital twin
        digital_twin = DigitalTwin(
            user_id=user_id,
            email=profile_data.get("email", ""),
            full_name=profile_data.get("full_name"),
            display_name=profile_data.get("display_name") or profile_data.get("full_name"),
            avatar_url=profile_data.get("avatar_url"),
            bio=profile_data.get("bio"),
            title=profile_data.get("title"),
            department=profile_data.get("department"),
            organization=profile_data.get("organization"),
            location=profile_data.get("location"),
            presence_status=PresenceStatus(profile_data.get("presence_status", "offline")),
            presence_message=profile_data.get("presence_message"),
            last_seen=datetime.fromisoformat(profile_data["last_seen"]) if profile_data.get("last_seen") else None,
            is_available=profile_data.get("is_available", False),
            work_style=WorkStyle(profile_data["work_style"]) if profile_data.get("work_style") else None,
            working_hours=profile_data.get("working_hours"),
            communication_preferences=CommunicationPreferences(**profile_data.get("communication_preferences", {})),
            skills=profile_data.get("skills", []),
            expertise=[Expertise(**e) for e in profile_data.get("expertise", [])],
            languages=profile_data.get("languages", []),
            current_projects=current_projects,
            collaboration_notes=profile_data.get("collaboration_notes"),
            ai_personality=profile_data.get("ai_personality", "professional"),
            ai_context=profile_data.get("ai_context", {}),
            auto_respond_enabled=profile_data.get("auto_respond_enabled", False),
            auto_response_rules=profile_data.get("auto_response_rules", []),
            created_at=datetime.fromisoformat(profile_data["created_at"]),
            updated_at=datetime.fromisoformat(profile_data["updated_at"]),
            version=profile_data.get("version", 1)
        )

        return digital_twin

    except Exception as e:
        logger.error("Failed to get digital twin", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get digital twin: {e}"
        )


# ==================== Update My Digital Twin ====================

@router.put("/me", response_model=DigitalTwin)
async def update_my_digital_twin(
    update: DigitalTwinUpdate,
    user_id: CurrentUserId,
) -> DigitalTwin:
    """Update current user's digital twin."""
    try:
        supabase = get_supabase_client()

        # Build update data
        update_data = {}
        for field, value in update.dict(exclude_unset=True).items():
            if value is not None:
                # Handle complex fields
                if field == "working_hours" and value:
                    update_data[field] = value.dict()
                elif field == "communication_preferences" and value:
                    update_data[field] = value.dict()
                elif field == "expertise" and value:
                    update_data[field] = [e.dict() for e in value]
                elif field == "presence_status" and value:
                    update_data[field] = value.value
                elif field == "work_style" and value:
                    update_data[field] = value.value
                else:
                    update_data[field] = value

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Add metadata
        update_data["updated_at"] = datetime.utcnow().isoformat()

        # If presence is updated, update last_seen
        if "presence_status" in update_data and update_data["presence_status"] != PresenceStatus.OFFLINE.value:
            update_data["last_seen"] = datetime.utcnow().isoformat()
            update_data["is_available"] = update_data["presence_status"] in [
                PresenceStatus.ONLINE.value,
                PresenceStatus.AWAY.value
            ]

        # Update profile
        update_response = supabase.table("profiles").update(
            update_data
        ).eq("id", user_id).execute()

        if not update_response.data:
            # Profile doesn't exist, create it
            update_data["id"] = user_id
            update_data["created_at"] = datetime.utcnow().isoformat()
            supabase.table("profiles").insert(update_data).execute()

        # Return updated digital twin
        return await get_my_digital_twin(user_id=user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update digital twin", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update digital twin: {e}"
        )


# ==================== Get User's Digital Twin ====================

@router.get("/{target_user_id}", response_model=DigitalTwin)
async def get_user_digital_twin(
    target_user_id: str,
    user_id: CurrentUserId,
) -> DigitalTwin:
    """Get another user's digital twin.

    Only returns information for users in shared topics.
    """
    try:
        supabase = get_supabase_client()

        # Check if users share any topics
        current_user_topics = supabase.table("domain_members").select(
            "domain_id"
        ).eq("user_id", user_id).execute()

        current_user_topic_ids = {m["domain_id"] for m in current_user_topics.data}

        target_user_topics = supabase.table("domain_members").select(
            "domain_id"
        ).eq("user_id", target_user_id).execute()

        target_user_topic_ids = {m["domain_id"] for m in target_user_topics.data}

        shared_topics = current_user_topic_ids.intersection(target_user_topic_ids)

        if not shared_topics:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't share any topics with this user"
            )

        # Get user profile
        profile_response = supabase.table("profiles").select("*").eq("id", target_user_id).execute()

        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {target_user_id}"
            )

        profile_data = profile_response.data[0]

        # Build digital twin (may filter some private information)
        digital_twin = DigitalTwin(
            user_id=target_user_id,
            email=profile_data.get("email", ""),
            full_name=profile_data.get("full_name"),
            display_name=profile_data.get("display_name") or profile_data.get("full_name"),
            avatar_url=profile_data.get("avatar_url"),
            bio=profile_data.get("bio"),
            title=profile_data.get("title"),
            department=profile_data.get("department"),
            organization=profile_data.get("organization"),
            location=profile_data.get("location"),
            presence_status=PresenceStatus(profile_data.get("presence_status", "offline")),
            presence_message=profile_data.get("presence_message"),
            last_seen=datetime.fromisoformat(profile_data["last_seen"]) if profile_data.get("last_seen") else None,
            is_available=profile_data.get("is_available", False),
            work_style=WorkStyle(profile_data["work_style"]) if profile_data.get("work_style") else None,
            working_hours=profile_data.get("working_hours"),
            communication_preferences=CommunicationPreferences(**profile_data.get("communication_preferences", {})),
            skills=profile_data.get("skills", []),
            expertise=[Expertise(**e) for e in profile_data.get("expertise", [])],
            languages=profile_data.get("languages", []),
            current_projects=list(shared_topics),  # Only show shared projects
            collaboration_notes=profile_data.get("collaboration_notes"),
            ai_personality=profile_data.get("ai_personality", "professional"),
            ai_context={},  # Don't share AI context
            auto_respond_enabled=profile_data.get("auto_respond_enabled", False),
            auto_response_rules=[],  # Don't share rules
            created_at=datetime.fromisoformat(profile_data["created_at"]),
            updated_at=datetime.fromisoformat(profile_data["updated_at"]),
            version=profile_data.get("version", 1)
        )

        return digital_twin

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user digital twin", target_user_id=target_user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user digital twin: {e}"
        )


# ==================== Search Digital Twins ====================

@router.get("/", response_model=List[DigitalTwinSummary])
async def search_digital_twins(
    user_id: CurrentUserId,
    topic_id: Optional[str] = Query(None, description="Filter by topic membership"),
    skill: Optional[str] = Query(None, description="Filter by skill"),
    available_only: bool = Query(False, description="Only show available users"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[DigitalTwinSummary]:
    """Search for digital twins of users in your network."""
    try:
        supabase = get_supabase_client()

        # Get current user's topics to define "network"
        user_topics = supabase.table("domain_members").select(
            "domain_id"
        ).eq("user_id", user_id).execute()

        user_topic_ids = [m["domain_id"] for m in user_topics.data]

        if not user_topic_ids:
            return []  # No network

        # Find users in the network
        query = supabase.table("domain_members").select(
            "user_id",
            "profiles:user_id(*)"
        )

        if topic_id:
            query = query.eq("domain_id", topic_id)
        else:
            query = query.in_("domain_id", user_topic_ids)

        # Get unique users
        members_response = query.execute()

        # Deduplicate and filter
        seen_users = set()
        twins = []

        for member in members_response.data:
            if member["user_id"] in seen_users:
                continue

            seen_users.add(member["user_id"])
            profile = member.get("profiles", {})

            if not profile:
                continue

            # Apply filters
            if available_only and not profile.get("is_available", False):
                continue

            if skill and skill.lower() not in [s.lower() for s in profile.get("skills", [])]:
                continue

            # Create summary
            twin_summary = DigitalTwinSummary(
                user_id=member["user_id"],
                email=profile.get("email", ""),
                display_name=profile.get("display_name") or profile.get("full_name") or "Unknown",
                avatar_url=profile.get("avatar_url"),
                presence_status=PresenceStatus(profile.get("presence_status", "offline")),
                is_available=profile.get("is_available", False),
                title=profile.get("title"),
                organization=profile.get("organization")
            )
            twins.append(twin_summary)

        # Apply pagination
        start = offset
        end = offset + limit
        return twins[start:end]

    except Exception as e:
        logger.error("Failed to search digital twins", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search digital twins: {e}"
        )