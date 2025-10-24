"""Request schemas."""

from pydantic import BaseModel, Field


class UploadDocumentRequest(BaseModel):
    """Request to upload and process a document."""

    document_id: str = Field(..., description="UUID of the document")
    domain_id: str = Field(..., description="UUID of the domain")
    file_path: str = Field(..., description="Path to file in Supabase Storage")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "domain_id": "456e4567-e89b-12d3-a456-426614174001",
                "file_path": "domain-456/document-123.pdf",
            }
        }


class AskQuestionRequest(BaseModel):
    """Request to ask a question."""

    question_id: str = Field(..., description="UUID of the question")
    question: str = Field(..., description="Question text", min_length=10)
    domain_id: str = Field(..., description="UUID of the domain")
    user_id: str = Field(..., description="UUID of the user asking")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "789e4567-e89b-12d3-a456-426614174002",
                "question": "What is the process for deploying to production?",
                "domain_id": "456e4567-e89b-12d3-a456-426614174001",
                "user_id": "012e4567-e89b-12d3-a456-426614174003",
            }
        }


class SubmitReviewRequest(BaseModel):
    """Request to submit a review."""

    review_id: str = Field(..., description="UUID of the review")
    reviewable_type: str = Field(..., description="Type: 'document' or 'answer'")
    reviewable_id: str = Field(..., description="UUID of the item being reviewed")
    domain_id: str = Field(..., description="UUID of the domain")

    class Config:
        json_schema_extra = {
            "example": {
                "review_id": "345e4567-e89b-12d3-a456-426614174004",
                "reviewable_type": "document",
                "reviewable_id": "123e4567-e89b-12d3-a456-426614174000",
                "domain_id": "456e4567-e89b-12d3-a456-426614174001",
            }
        }


class WorkflowDataRequest(BaseModel):
    """Request to create or update a workflow."""

    name: str = Field(..., description="Workflow name")
    description: str | None = Field(None, description="Workflow description")
    domain_id: str = Field(..., description="UUID of the domain")
    yaml_definition: dict = Field(..., description="Workflow definition in YAML as dict")
    is_active: bool = Field(True, description="Whether workflow is active")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Document Processing",
                "description": "Process and index documents",
                "domain_id": "456e4567-e89b-12d3-a456-426614174001",
                "yaml_definition": {"version": "1.0", "steps": []},
                "is_active": True,
            }
        }


class DocumentDataRequest(BaseModel):
    """Request to create a document reference."""

    name: str = Field(..., description="Document name")
    domain_id: str = Field(..., description="UUID of the domain")
    file_path: str = Field(..., description="Path in Supabase Storage")
    file_type: str | None = Field(None, description="MIME type")
    size_bytes: int | None = Field(None, description="File size in bytes")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Architecture Guide",
                "domain_id": "456e4567-e89b-12d3-a456-426614174001",
                "file_path": "domain-456/docs/architecture.pdf",
                "file_type": "application/pdf",
                "size_bytes": 1024000,
            }
        }
