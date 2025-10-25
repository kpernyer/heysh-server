"""API routes for domain bootstrap workflow."""

import os
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from temporalio.client import Client, WorkflowHandle
from workflow.domain_bootstrap_workflow import (
    BootstrapWorkflowInput,
    DomainBootstrapWorkflow,
)

router = APIRouter()
logger = structlog.get_logger()

# Global Temporal client instance
temporal_client: Optional[Client] = None


def set_temporal_client(client: Client | None) -> None:
    """Set the Temporal client instance."""
    global temporal_client
    temporal_client = client


class CreateDomainRequest(BaseModel):
    """Request to create a new domain."""
    domain_name: str
    domain_description: str
    initial_topics: List[str] = []
    target_audience: List[str] = []
    research_focus: Optional[str] = None
    quality_requirements: Dict[str, Any] = {}
    research_depth: str = "comprehensive"
    include_historical: bool = True
    include_technical: bool = True
    include_practical: bool = True


class WorkflowResponse(BaseModel):
    """Response for workflow operations."""
    workflow_id: str
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None


class BootstrapStatusResponse(BaseModel):
    """Response for bootstrap status."""
    workflow_id: str
    status: str
    research_results: Optional[Dict[str, Any]] = None
    analysis_results: Optional[Dict[str, Any]] = None
    domain_config: Optional[Dict[str, Any]] = None
    owner_approved: bool = False
    error_message: Optional[str] = None


class OwnerDecisionRequest(BaseModel):
    """Request for owner decision on domain configuration."""
    decision: str  # "approve" or "reject"
    reason: Optional[str] = None


@router.post("/domains", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_domain(request: CreateDomainRequest) -> WorkflowResponse:
    """
    Create a new domain and start bootstrap workflow.
    
    This endpoint initiates the domain bootstrap workflow which will:
    1. Research the domain using AI
    2. Analyze research results
    3. Generate domain configuration
    4. Wait for owner approval
    5. Complete domain setup
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    logger.info(
        "Creating new domain",
        domain_name=request.domain_name,
        owner_id="owner_placeholder",  # TODO: Get from authentication
    )

    try:
        # Generate domain ID (in real implementation, this would come from database)
        import uuid
        domain_id = str(uuid.uuid4())
        owner_id = "owner_placeholder"  # TODO: Get from authentication

        # Create bootstrap workflow input
        workflow_input = BootstrapWorkflowInput(
            domain_id=domain_id,
            owner_id=owner_id,
            domain_name=request.domain_name,
            domain_description=request.domain_description,
            initial_topics=request.initial_topics,
            target_audience=request.target_audience,
            research_focus=request.research_focus,
            quality_requirements=request.quality_requirements,
            research_depth=request.research_depth,
            include_historical=request.include_historical,
            include_technical=request.include_technical,
            include_practical=request.include_practical,
        )

        # Start bootstrap workflow
        handle = await temporal_client.start_workflow(
            DomainBootstrapWorkflow.run,
            args=[workflow_input],
            id=f"domain-bootstrap-{domain_id}",
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "hey-sh-workflows"),
            # Set initial Search Attributes for visibility
            search_attributes={
                "Assignee": [owner_id],
                "Queue": ["domain-bootstrap"],
                "Status": ["started"],
                "Priority": ["high"],
                "DomainId": [domain_id],
                "DomainName": [request.domain_name],
                "OwnerId": [owner_id],
                "CreatedAt": [Client.now().isoformat()],
            },
        )

        logger.info(
            "Domain bootstrap workflow started",
            workflow_id=handle.id,
            domain_id=domain_id,
            domain_name=request.domain_name,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            message="Domain bootstrap workflow initiated. Research and analysis will begin shortly.",
        )

    except Exception as e:
        logger.error("Failed to create domain", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create domain: {e!s}",
        ) from e


@router.get("/domains/{workflow_id}/status", response_model=BootstrapStatusResponse)
async def get_bootstrap_status(workflow_id: str) -> BootstrapStatusResponse:
    """Get the current status of a domain bootstrap workflow."""
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    try:
        handle: WorkflowHandle[DomainBootstrapWorkflow] = temporal_client.get_workflow_handle(
            workflow_id
        )
        
        # Query the workflow for its current state
        status_result = await handle.query(DomainBootstrapWorkflow.get_bootstrap_status)
        workflow_description = await handle.describe()

        return BootstrapStatusResponse(
            workflow_id=workflow_id,
            status=workflow_description.status.name,
            research_results=status_result.get("research_results"),
            analysis_results=status_result.get("analysis_results"),
            domain_config=status_result.get("domain_config"),
            owner_approved=status_result.get("owner_approved", False),
            error_message=status_result.get("error_message"),
        )

    except Exception as e:
        logger.error("Failed to get bootstrap status", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found or failed to query: {e!s}",
        ) from e


@router.post("/domains/{workflow_id}/owner-decision", status_code=status.HTTP_200_OK)
async def submit_owner_decision(
    workflow_id: str, decision_request: OwnerDecisionRequest
):
    """
    Submit owner decision (approve/reject) for domain configuration.
    
    This endpoint allows the domain owner to approve or reject the
    domain configuration generated by the bootstrap workflow.
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    try:
        handle: WorkflowHandle[DomainBootstrapWorkflow] = temporal_client.get_workflow_handle(
            workflow_id
        )

        if decision_request.decision == "approve":
            await handle.signal(DomainBootstrapWorkflow.approve_domain_config)
            logger.info("Owner approved domain configuration", workflow_id=workflow_id)
        elif decision_request.decision == "reject":
            reason = decision_request.reason or "No reason provided"
            await handle.signal(DomainBootstrapWorkflow.reject_domain_config, reason)
            logger.info("Owner rejected domain configuration", workflow_id=workflow_id, reason=reason)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decision must be 'approve' or 'reject'",
            )

        return {"message": "Owner decision submitted successfully"}

    except Exception as e:
        logger.error("Failed to submit owner decision", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit decision: {e!s}",
        ) from e


@router.get("/domains/owner/inbox", response_model=List[Dict[str, Any]])
async def get_owner_inbox(
    owner_id: str = "owner_placeholder",
    status_filter: str = "pending_owner_review",
    queue_filter: str = "domain-bootstrap",
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Get a list of domain bootstrap workflows pending owner review.
    
    This acts as the 'inbox' for domain owners to review and approve
    domain configurations generated by the bootstrap workflow.
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    try:
        # Construct the query using Search Attributes
        query = (
            f'Assignee = "{owner_id}" AND Status = "{status_filter}" AND Queue = "{queue_filter}"'
        )
        logger.info("Querying owner inbox", query=query)

        # Use Temporal's Visibility API to list workflow executions
        executions = await temporal_client.list_workflows(
            query, page_size=limit, query_offset=offset
        )

        inbox_items = []
        for exec_info in executions.executions:
            search_attributes = {
                k: v.value for k, v in exec_info.search_attributes.items()
            }
            inbox_items.append(
                {
                    "workflow_id": exec_info.id,
                    "run_id": exec_info.run_id,
                    "start_time": exec_info.start_time.isoformat(),
                    "search_attributes": search_attributes,
                    "status": search_attributes.get("Status", "UNKNOWN"),
                    "domain_id": search_attributes.get("DomainId"),
                    "domain_name": search_attributes.get("DomainName"),
                    "owner_id": search_attributes.get("OwnerId"),
                    "due_at": search_attributes.get("DueAt"),
                }
            )

        return inbox_items

    except Exception as e:
        logger.error("Failed to query owner inbox", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inbox: {e!s}",
        ) from e
