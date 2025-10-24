"""Response schemas."""

from pydantic import BaseModel, Field


class WorkflowResponse(BaseModel):
    """Generic workflow response."""

    workflow_id: str = Field(..., description="Temporal workflow ID")
    status: str = Field(..., description="Workflow status")
    message: str = Field(..., description="Status message")


class QuestionResponse(BaseModel):
    """Question response."""

    question_id: str
    answer: str
    confidence_score: float
    needs_review: bool
    source_count: int


class DocumentResponse(BaseModel):
    """Document processing response."""

    document_id: str
    status: str
    text_length: int
    chunk_count: int
    weaviate_indexed: bool
    neo4j_updated: bool
