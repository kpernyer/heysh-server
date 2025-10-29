"""Request schemas."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UploadDocumentRequest(BaseModel):
    """Request to upload and process a document."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic_id": "456e4567-e89b-12d3-a456-426614174001",
                "file_path": "topic-456/document-123.pdf",
            }
        }
    )

    document_id: str = Field(..., description="UUID of the document")
    topic_id: str = Field(..., description="UUID of the topic")
    file_path: str = Field(..., description="Path to file in Supabase Storage")


class AskQuestionRequest(BaseModel):
    """Request to ask a question."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "789e4567-e89b-12d3-a456-426614174002",
                "question": "What is the process for deploying to production?",
                "topic_id": "456e4567-e89b-12d3-a456-426614174001",
                "user_id": "012e4567-e89b-12d3-a456-426614174003",
            }
        }
    )

    question_id: str = Field(..., description="UUID of the question")
    question: str = Field(..., description="Question text", min_length=10)
    topic_id: str = Field(..., description="UUID of the topic")
    user_id: str = Field(..., description="UUID of the user asking")


class SubmitReviewRequest(BaseModel):
    """Request to submit a review."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "review_id": "345e4567-e89b-12d3-a456-426614174004",
                "reviewable_type": "document",
                "reviewable_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic_id": "456e4567-e89b-12d3-a456-426614174001",
            }
        }
    )

    review_id: str = Field(..., description="UUID of the review")
    reviewable_type: str = Field(..., description="Type: 'document' or 'answer'")
    reviewable_id: str = Field(..., description="UUID of the item being reviewed")
    topic_id: str = Field(..., description="UUID of the topic")


class WorkflowDataRequest(BaseModel):
    """Request to create or update a workflow."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Document Processing",
                "description": "Process and index documents",
                "topic_id": "456e4567-e89b-12d3-a456-426614174001",
                "yaml_definition": {"version": "1.0", "steps": []},
                "is_active": True,
            }
        }
    )

    name: str = Field(..., description="Workflow name")
    description: str | None = Field(None, description="Workflow description")
    topic_id: str = Field(..., description="UUID of the topic")
    yaml_definition: dict = Field(..., description="Workflow definition in YAML as dict")
    is_active: bool = Field(True, description="Whether workflow is active")


class DocumentDataRequest(BaseModel):
    """Request to create a document reference."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Architecture Guide",
                "topic_id": "456e4567-e89b-12d3-a456-426614174001",
                "file_path": "topic-456/docs/architecture.pdf",
                "file_type": "application/pdf",
                "size_bytes": 1024000,
            }
        }
    )

    name: str = Field(..., description="Document name")
    topic_id: str = Field(..., description="UUID of the topic")
    file_path: str = Field(..., description="Path in Supabase Storage")
    file_type: str | None = Field(None, description="MIME type")
    size_bytes: int | None = Field(None, description="File size in bytes")


class CreateTopicRequest(BaseModel):
    """Request to create a new topic."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic_id": "topic-123",
                "name": "Machine Learning",
                "description": "A topic about machine learning and AI",
                "created_by": "user-456",
            }
        }
    )

    topic_id: str = Field(..., description="Unique topic identifier")
    name: str = Field(..., description="Topic name")
    description: Optional[str] = Field(None, description="Topic description")
    created_by: str = Field(..., description="User ID who created the topic")
