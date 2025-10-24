"""API routes for document analysis workflow."""

import os
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from temporalio.client import Client

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/analysis", tags=["document-analysis"])

# Global Temporal client
temporal_client: Client | None = None


def set_temporal_client(client: Client | None) -> None:
    """Set the Temporal client."""
    global temporal_client
    temporal_client = client


class DocumentAnalysisRequest(BaseModel):
    """Request to start document analysis."""

    document_id: str
    domain_id: str
    file_path: str
    contributor_id: str
    domain_criteria: dict[str, Any]
    auto_approve_threshold: float = 8.0
    relevance_threshold: float = 7.0


class WorkflowResponse(BaseModel):
    """Response from workflow start."""

    workflow_id: str
    status: str
    message: str


class ControllerDecisionRequest(BaseModel):
    """Controller decision request."""

    decision: str  # "approve" or "reject"
    controller_id: str
    feedback: str = ""


@router.post(
    "/documents", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED
)
async def start_document_analysis(request: DocumentAnalysisRequest) -> WorkflowResponse:
    """Start document analysis workflow with HITL controller review.

    This endpoint:
    1. Downloads document from Supabase Storage
    2. Performs FörAnalys with LLM (later Ollama)
    3. If relevant → Indexes in Weaviate + Neo4j
    4. If needs review → Sends to Controller inbox
    5. Waits for Controller decision
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    logger.info(
        "Starting document analysis workflow",
        document_id=request.document_id,
        domain_id=request.domain_id,
        contributor_id=request.contributor_id,
    )

    try:
        handle = await temporal_client.start_workflow(
            "DocumentAnalysisWorkflow",
            args=[request],
            id=f"analysis-{request.document_id}",
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "hey-sh-workflows"),
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="analyzing",
            message="Document analysis started",
        )

    except Exception as e:
        logger.error("Failed to start analysis workflow", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {e!s}",
        ) from e


@router.get("/workflows/{workflow_id}/status")
async def get_analysis_status(workflow_id: str) -> dict[str, Any]:
    """Get analysis workflow status."""
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    try:
        handle = temporal_client.get_workflow_handle(workflow_id)
        result = await handle.query("get_status")

        return {
            "workflow_id": workflow_id,
            "status": result["status"],
            "relevance_score": result.get("relevance_score"),
            "analysis_completed": result.get("analysis_completed", False),
            "controller_decision": result.get("controller_decision"),
            "controller_id": result.get("controller_id"),
        }

    except Exception as e:
        logger.error("Failed to get analysis status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        ) from e


@router.post("/workflows/{workflow_id}/controller-decision")
async def submit_controller_decision(
    workflow_id: str, request: ControllerDecisionRequest
) -> dict[str, Any]:
    """Submit Controller decision for document review.

    This is the HITL (Human-in-the-Loop) endpoint where Controllers
    approve or reject documents that need manual review.
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    if request.decision not in ["approve", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approve' or 'reject'",
        )

    try:
        handle = temporal_client.get_workflow_handle(workflow_id)
        await handle.signal(
            "controller_decision",
            request.decision,
            request.controller_id,
            request.feedback,
        )

        logger.info(
            "Controller decision submitted",
            workflow_id=workflow_id,
            decision=request.decision,
            controller_id=request.controller_id,
        )

        return {
            "workflow_id": workflow_id,
            "status": "decision_submitted",
            "decision": request.decision,
            "controller_id": request.controller_id,
        }

    except Exception as e:
        logger.error("Failed to submit controller decision", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit decision: {e!s}",
        ) from e


@router.get("/controller/inbox")
async def get_controller_inbox(controller_id: str) -> dict[str, Any]:
    """Get Controller inbox using Temporal Search Attributes.

    This uses Temporal's Visibility API to query workflows
    assigned to the Controller for review.
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    try:
        # Query workflows using Search Attributes
        # This creates the "inbox" functionality
        workflows = await temporal_client.list_workflows(
            query=f'Assignee = "{controller_id}" AND Status = "pending" AND Queue = "document-review"'
        )

        inbox_items = []
        async for workflow in workflows:
            # Get workflow details
            handle = temporal_client.get_workflow_handle(workflow.id)
            status_info = await handle.query("get_status")

            inbox_items.append(
                {
                    "workflow_id": workflow.id,
                    "document_id": workflow.search_attributes.get("DocumentId"),
                    "contributor_id": workflow.search_attributes.get("ContributorId"),
                    "relevance_score": status_info.get("relevance_score"),
                    "assigned_at": workflow.start_time.isoformat(),
                    "due_at": workflow.search_attributes.get("DueAt"),
                    "priority": workflow.search_attributes.get("Priority"),
                }
            )

        return {
            "controller_id": controller_id,
            "pending_count": len(inbox_items),
            "items": inbox_items,
        }

    except Exception as e:
        logger.error("Failed to get controller inbox", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inbox: {e!s}",
        ) from e
