"""Topic model for knowledge base topics."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TopicStatus(Enum):
    """Topic status enumeration."""
    BOOTSTRAPPING = "bootstrapping"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


class TopicRole(Enum):
    """Topic role enumeration."""
    OWNER = "owner"
    CONTRIBUTOR = "contributor"
    CONTROLLER = "controller"
    MEMBER = "member"


class Topic(BaseModel):
    """Topic model for knowledge base topics."""

    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Topic name")
    description: str = Field(..., description="Topic description")
    owner_id: UUID = Field(..., description="Owner user ID")
    status: TopicStatus = Field(default=TopicStatus.BOOTSTRAPPING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Topic configuration
    subtopics: List[str] = Field(default_factory=list, description="Core subtopics for this topic")
    quality_criteria: Dict[str, Any] = Field(default_factory=dict, description="Quality assessment criteria")
    search_attributes: Dict[str, Any] = Field(default_factory=dict, description="Search attributes for workflows")

    # Bootstrap configuration
    bootstrap_prompt: Optional[str] = Field(None, description="Custom bootstrap research prompt")
    research_steps: List[str] = Field(default_factory=list, description="Research steps for bootstrapping")
    target_audience: List[str] = Field(default_factory=list, description="Target audience for this topic")

    # Knowledge base metrics
    document_count: int = Field(default=0, description="Number of documents in topic")
    contributor_count: int = Field(default=0, description="Number of contributors")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")


class TopicMember(BaseModel):
    """Topic member model."""

    model_config = ConfigDict(use_enum_values=True)

    topic_id: UUID = Field(..., description="Topic ID")
    user_id: UUID = Field(..., description="User ID")
    role: TopicRole = Field(..., description="User role in topic")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    permissions: List[str] = Field(default_factory=list, description="User permissions")


class BootstrapInput(BaseModel):
    """Input for topic bootstrap workflow."""

    topic_id: UUID = Field(..., description="Topic ID")
    owner_id: UUID = Field(..., description="Owner user ID")
    topic_name: str = Field(..., description="Topic name")
    topic_description: str = Field(..., description="Topic description")
    initial_subtopics: List[str] = Field(default_factory=list, description="Initial subtopics provided by owner")
    target_audience: List[str] = Field(default_factory=list, description="Target audience")
    research_focus: Optional[str] = Field(None, description="Specific research focus areas")
    quality_requirements: Dict[str, Any] = Field(default_factory=dict, description="Quality requirements")

    # Bootstrap configuration
    research_depth: str = Field(default="comprehensive", description="Research depth: basic, comprehensive, expert")
    include_historical: bool = Field(default=True, description="Include historical research")
    include_technical: bool = Field(default=True, description="Include technical research")
    include_practical: bool = Field(default=True, description="Include practical applications")


class BootstrapResult(BaseModel):
    """Result of topic bootstrap workflow."""

    topic_id: UUID = Field(..., description="Topic ID")
    status: str = Field(..., description="Bootstrap status")
    research_summary: str = Field(..., description="Research summary")
    discovered_subtopics: List[str] = Field(default_factory=list, description="Discovered subtopics")
    quality_criteria: Dict[str, Any] = Field(default_factory=dict, description="Generated quality criteria")
    search_attributes: Dict[str, Any] = Field(default_factory=dict, description="Generated search attributes")
    research_sources: List[str] = Field(default_factory=list, description="Research sources used")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for topic")
    completed_at: datetime = Field(default_factory=datetime.utcnow)
