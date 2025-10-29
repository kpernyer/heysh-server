"""Temporal workflow orchestration routes."""

import os
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from temporalio.client import Client

from src.app.schemas.requests import (
    AskQuestionRequest,
    CreateTopicRequest,
    SubmitReviewRequest,
    UploadDocumentRequest,
)
from src.app.schemas.responses import (
    WorkflowResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["workflows"])

# Global reference to Temporal client (set by api.py during app startup)
temporal_client: Client | None = None


def set_temporal_client(client: Client | None) -> None:
    """Set the global Temporal client reference."""
    global temporal_client
    temporal_client = client


@router.post(
    "/documents", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_document(request: UploadDocumentRequest) -> WorkflowResponse:
    """Trigger document processing workflow.

    This endpoint starts a Temporal workflow to:
    1. Download document from Supabase Storage
    2. Extract text and metadata
    3. Generate embeddings
    4. Index in Weaviate
    5. Update Neo4j knowledge graph
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    logger.info(
        "Starting document processing workflow",
        document_id=request.document_id,
        topic_id=request.topic_id,
    )

    try:
        handle = await temporal_client.start_workflow(
            "DocumentProcessingWorkflow",
            args=[request.document_id, request.topic_id, request.file_path],
            id=f"doc-{request.document_id}",
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "hey-sh-workflows"),
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="processing",
            message="Document processing started",
        )

    except Exception as e:
        logger.error("Failed to start document workflow", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {e!s}",
        ) from e


@router.post(
    "/questions", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED
)
async def ask_question(request: AskQuestionRequest) -> WorkflowResponse:
    """Trigger question answering workflow.

    This endpoint starts a Temporal workflow to:
    1. Search relevant documents (Weaviate)
    2. Find related documents (Neo4j)
    3. Generate answer using LLM
    4. Calculate confidence score
    5. Create review task if confidence is low
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    logger.info(
        "Starting question answering workflow",
        question_id=request.question_id,
        topic_id=request.topic_id,
    )

    try:
        handle = await temporal_client.start_workflow(
            "QuestionAnsweringWorkflow",
            args=[
                request.question_id,
                request.question,
                request.topic_id,
                request.user_id,
            ],
            id=f"question-{request.question_id}",
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "hey-sh-workflows"),
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="processing",
            message="Question answering started",
        )

    except Exception as e:
        logger.error("Failed to start question workflow", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {e!s}",
        ) from e


@router.post(
    "/reviews", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED
)
async def submit_review(request: SubmitReviewRequest) -> WorkflowResponse:
    """Trigger quality review workflow.

    This endpoint starts a Temporal workflow to:
    1. Assign review to topic admin/controller
    2. Wait for review decision
    3. Apply decision (approve/reject/rollback)
    4. Update quality scores
    5. Notify contributor
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    logger.info(
        "Starting quality review workflow",
        review_id=request.review_id,
        reviewable_type=request.reviewable_type,
    )

    try:
        handle = await temporal_client.start_workflow(
            "QualityReviewWorkflow",
            args=[
                request.review_id,
                request.reviewable_type,
                request.reviewable_id,
                request.topic_id,
            ],
            id=f"review-{request.review_id}",
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "hey-sh-workflows"),
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="processing",
            message="Quality review started",
        )

    except Exception as e:
        logger.error("Failed to start review workflow", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {e!s}",
        ) from e


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> dict[str, Any]:
    """Get execution status of a Temporal workflow."""
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    try:
        handle = temporal_client.get_workflow_handle(workflow_id)
        result = await handle.describe()

        return {
            "workflow_id": workflow_id,
            "status": result.status.name,
            "type": result.workflow_type,
        }

    except Exception as e:
        logger.error("Failed to get workflow status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        ) from e


@router.post("/topics", status_code=status.HTTP_201_CREATED)
async def create_topic(request: CreateTopicRequest) -> dict[str, Any]:
    """Create a new topic and index it in Weaviate and Neo4j.

    Requires:
        - topic_id: Unique topic identifier
        - name: Topic name
        - description: Topic description (optional)
        - created_by: User ID who created the topic
    """
    logger.info("Creating topic", topic_id=request.topic_id)

    # Import activities directly for synchronous execution
    from activity.domain import index_domain_activity

    try:
        # Prepare topic data
        topic_data = {
            "topic_id": request.topic_id,
            "name": request.name,
            "description": request.description,
            "created_by": request.created_by,
        }

        # Index topic immediately (could be made async with workflow)
        result = await index_domain_activity(topic_data)

        return {
            "topic_id": request.topic_id,
            "name": request.name,
            "description": request.description,
            "created_by": request.created_by,
            "status": "indexed",
            "message": "Topic created and indexed successfully",
        }

    except Exception as e:
        logger.error("Failed to create topic", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create topic: {e!s}",
        ) from e
