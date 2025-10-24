"""Domain model for knowledge base domains."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainStatus(Enum):
    """Domain status enumeration."""
    BOOTSTRAPPING = "bootstrapping"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


class DomainRole(Enum):
    """Domain role enumeration."""
    OWNER = "owner"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


class Domain(BaseModel):
    """Domain model for knowledge base domains."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Domain name")
    description: str = Field(..., description="Domain description")
    owner_id: UUID = Field(..., description="Owner user ID")
    status: DomainStatus = Field(default=DomainStatus.BOOTSTRAPPING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Domain configuration
    topics: List[str] = Field(default_factory=list, description="Core topics for this domain")
    quality_criteria: Dict[str, Any] = Field(default_factory=dict, description="Quality assessment criteria")
    search_attributes: Dict[str, Any] = Field(default_factory=dict, description="Search attributes for workflows")
    
    # Bootstrap configuration
    bootstrap_prompt: Optional[str] = Field(None, description="Custom bootstrap research prompt")
    research_steps: List[str] = Field(default_factory=list, description="Research steps for bootstrapping")
    target_audience: List[str] = Field(default_factory=list, description="Target audience for this domain")
    
    # Knowledge base metrics
    document_count: int = Field(default=0, description="Number of documents in domain")
    contributor_count: int = Field(default=0, description="Number of contributors")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class DomainMember(BaseModel):
    """Domain member model."""
    
    domain_id: UUID = Field(..., description="Domain ID")
    user_id: UUID = Field(..., description="User ID")
    role: DomainRole = Field(..., description="User role in domain")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class BootstrapInput(BaseModel):
    """Input for domain bootstrap workflow."""
    
    domain_id: UUID = Field(..., description="Domain ID")
    owner_id: UUID = Field(..., description="Owner user ID")
    domain_name: str = Field(..., description="Domain name")
    domain_description: str = Field(..., description="Domain description")
    initial_topics: List[str] = Field(default_factory=list, description="Initial topics provided by owner")
    target_audience: List[str] = Field(default_factory=list, description="Target audience")
    research_focus: Optional[str] = Field(None, description="Specific research focus areas")
    quality_requirements: Dict[str, Any] = Field(default_factory=dict, description="Quality requirements")
    
    # Bootstrap configuration
    research_depth: str = Field(default="comprehensive", description="Research depth: basic, comprehensive, expert")
    include_historical: bool = Field(default=True, description="Include historical research")
    include_technical: bool = Field(default=True, description="Include technical research")
    include_practical: bool = Field(default=True, description="Include practical applications")


class BootstrapResult(BaseModel):
    """Result of domain bootstrap workflow."""
    
    domain_id: UUID = Field(..., description="Domain ID")
    status: str = Field(..., description="Bootstrap status")
    research_summary: str = Field(..., description="Research summary")
    discovered_topics: List[str] = Field(default_factory=list, description="Discovered topics")
    quality_criteria: Dict[str, Any] = Field(default_factory=dict, description="Generated quality criteria")
    search_attributes: Dict[str, Any] = Field(default_factory=dict, description="Generated search attributes")
    research_sources: List[str] = Field(default_factory=list, description="Research sources used")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for domain")
    completed_at: datetime = Field(default_factory=datetime.utcnow)
