"""GraphQL types for the knowledge database"""

from datetime import datetime
from enum import Enum

import strawberry


@strawberry.enum
class DocumentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@strawberry.enum
class WorkflowStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    CANCELED = "canceled"


@strawberry.type
class Domain:
    """Knowledge domain type"""

    domain_id: str
    name: str
    description: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    entity_count: int = 0
    relationship_count: int = 0


@strawberry.type
class Document:
    """Document in the knowledge base"""

    document_id: str
    domain_id: str
    title: str
    content: str | None = None
    status: DocumentStatus
    file_path: str | None = None
    mime_type: str | None = None
    created_at: datetime
    updated_at: datetime
    metadata: str | None = None  # JSON string
    embedding_count: int = 0


@strawberry.type
class Entity:
    """Knowledge graph entity"""

    entity_id: str
    domain_id: str
    name: str
    entity_type: str
    properties: str | None = None  # JSON string
    created_at: datetime
    updated_at: datetime


@strawberry.type
class Relationship:
    """Relationship between entities"""

    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    properties: str | None = None  # JSON string
    confidence: float = 1.0
    created_at: datetime


@strawberry.type
class SearchResult:
    """Search result from vector or graph search"""

    domain_id: str
    domain_name: str
    description: str | None = None
    score: float
    source: str  # "vector" or "graph"
    highlights: list[str] = strawberry.field(default_factory=list)


@strawberry.type
class SearchResponse:
    """Complete search response with results from both vector and graph"""

    query: str
    vector_results: list[SearchResult] = strawberry.field(default_factory=list)
    graph_results: list[SearchResult] = strawberry.field(default_factory=list)
    total_results: int = 0
    search_time_ms: float = 0.0


@strawberry.type
class Question:
    """Question asked in a domain"""

    question_id: str
    domain_id: str
    question: str
    answer: str | None = None
    context: list[str] | None = None
    confidence: float = 0.0
    asked_by: str
    created_at: datetime


@strawberry.type
class WorkflowInfo:
    """Workflow execution information"""

    workflow_id: str
    workflow_type: str
    status: WorkflowStatus
    input_data: str | None = None  # JSON string
    output_data: str | None = None  # JSON string
    error: str | None = None
    started_at: datetime
    completed_at: datetime | None = None


@strawberry.type
class DomainStats:
    """Statistics for a domain"""

    domain_id: str
    total_documents: int
    total_entities: int
    total_relationships: int
    total_questions: int
    avg_confidence: float
    last_activity: datetime
    top_entity_types: list[str] = strawberry.field(default_factory=list)
    top_relationship_types: list[str] = strawberry.field(default_factory=list)


@strawberry.type
class KnowledgeGraphNode:
    """Node in the knowledge graph visualization"""

    id: str
    label: str
    type: str
    properties: str | None = None  # JSON string
    connections: int = 0


@strawberry.type
class KnowledgeGraphEdge:
    """Edge in the knowledge graph visualization"""

    source: str
    target: str
    type: str
    label: str
    properties: str | None = None  # JSON string


@strawberry.type
class KnowledgeGraph:
    """Complete knowledge graph for visualization"""

    domain_id: str
    nodes: list[KnowledgeGraphNode] = strawberry.field(default_factory=list)
    edges: list[KnowledgeGraphEdge] = strawberry.field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0


# Input types for mutations
@strawberry.input
class CreateDomainInput:
    name: str
    description: str | None = None
    created_by: str


@strawberry.input
class UploadDocumentInput:
    domain_id: str
    file_path: str
    title: str | None = None
    user_id: str


@strawberry.input
class AskQuestionInput:
    domain_id: str
    question: str
    user_id: str
    use_context: bool = True
