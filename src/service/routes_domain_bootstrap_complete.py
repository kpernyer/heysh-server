"""API routes for complete domain bootstrap workflow with OpenAI research and owner feedback."""

import os
import uuid
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from temporalio.client import Client, WorkflowHandle
from workflow.domain_bootstrap_complete_workflow import (
    DomainBootstrapInput,
    DomainBootstrapCompleteWorkflow,
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
    """Request to create a new domain with complete bootstrap."""
    title: str
    description: str
    slug: Optional[str] = None
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
    example_questions: List[Dict[str, Any]] = []
    owner_feedback: Optional[Dict[str, Any]] = None
    owner_approved: bool = False
    error_message: Optional[str] = None


class OwnerFeedbackRequest(BaseModel):
    """Request for owner feedback on domain configuration."""
    approved: bool
    feedback: Dict[str, Any]
    question_rankings: List[Dict[str, Any]] = []
    additional_topics: List[str] = []
    remove_topics: List[str] = []
    quality_requirements: Dict[str, Any] = {}


@router.post("/domains", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_domain_complete(request: CreateDomainRequest) -> WorkflowResponse:
    """
    Create a new domain with complete bootstrap workflow.
    
    This endpoint initiates the complete domain bootstrap workflow which will:
    1. Research the domain using OpenAI
    2. Analyze research results
    3. Index knowledge in Weaviate
    4. Update Neo4j knowledge graph
    5. Generate example questions
    6. Wait for owner feedback
    7. Complete domain setup
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    logger.info(
        "Creating new domain with complete bootstrap",
        title=request.title,
        owner_id="owner_placeholder",  # TODO: Get from authentication
    )

    try:
        # Generate domain ID and slug
        domain_id = str(uuid.uuid4())
        slug = request.slug or request.title.lower().replace(" ", "-").replace("_", "-")
        owner_id = "owner_placeholder"  # TODO: Get from authentication

        # Create bootstrap workflow input
        workflow_input = DomainBootstrapInput(
            domain_id=domain_id,
            owner_id=owner_id,
            title=request.title,
            description=request.description,
            slug=slug,
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
            DomainBootstrapCompleteWorkflow.run,
            args=[workflow_input],
            id=f"domain-bootstrap-complete-{domain_id}",
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "hey-sh-workflows"),
            # Set initial Search Attributes for visibility
            search_attributes={
                "Assignee": [owner_id],
                "Queue": ["domain-bootstrap-complete"],
                "Status": ["started"],
                "Priority": ["high"],
                "DomainId": [domain_id],
                "DomainName": [request.title],
                "OwnerId": [owner_id],
                "CreatedAt": [Client.now().isoformat()],
            },
        )

        logger.info(
            "Domain bootstrap complete workflow started",
            workflow_id=handle.id,
            domain_id=domain_id,
            title=request.title,
        )

        return WorkflowResponse(
            workflow_id=handle.id,
            status="started",
            message=f"Domain '{request.title}' bootstrap workflow initiated. OpenAI research, vector indexing, and knowledge graph updates will begin shortly.",
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
        handle: WorkflowHandle[DomainBootstrapCompleteWorkflow] = temporal_client.get_workflow_handle(
            workflow_id
        )
        
        # Query the workflow for its current state
        status_result = await handle.query(DomainBootstrapCompleteWorkflow.get_bootstrap_status)
        workflow_description = await handle.describe()

        return BootstrapStatusResponse(
            workflow_id=workflow_id,
            status=workflow_description.status.name,
            research_results=status_result.get("research_results"),
            analysis_results=status_result.get("analysis_results"),
            domain_config=status_result.get("domain_config"),
            example_questions=status_result.get("example_questions", []),
            owner_feedback=status_result.get("owner_feedback"),
            owner_approved=status_result.get("owner_approved", False),
            error_message=status_result.get("error_message"),
        )

    except Exception as e:
        logger.error("Failed to get bootstrap status", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found or failed to query: {e!s}",
        ) from e


@router.post("/domains/{workflow_id}/owner-feedback", status_code=status.HTTP_200_OK)
async def submit_owner_feedback(
    workflow_id: str, feedback_request: OwnerFeedbackRequest
):
    """
    Submit owner feedback on domain configuration and example questions.
    
    This endpoint allows the domain owner to provide feedback on:
    - Domain configuration
    - Example questions ranking
    - Additional topics to cover
    - Topics to remove
    - Quality requirements
    """
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    try:
        handle: WorkflowHandle[DomainBootstrapCompleteWorkflow] = temporal_client.get_workflow_handle(
            workflow_id
        )

        # Prepare feedback data
        feedback_data = {
            "approved": feedback_request.approved,
            "feedback": feedback_request.feedback,
            "question_rankings": feedback_request.question_rankings,
            "additional_topics": feedback_request.additional_topics,
            "remove_topics": feedback_request.remove_topics,
            "quality_requirements": feedback_request.quality_requirements,
        }

        # Submit feedback to workflow
        await handle.signal(DomainBootstrapCompleteWorkflow.submit_owner_feedback, feedback_data)

        logger.info(
            "Owner feedback submitted",
            workflow_id=workflow_id,
            approved=feedback_request.approved,
        )

        return {"message": "Owner feedback submitted successfully"}

    except Exception as e:
        logger.error("Failed to submit owner feedback", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {e!s}",
        ) from e


@router.get("/domains/owner/inbox", response_model=List[Dict[str, Any]])
async def get_owner_inbox(
    owner_id: str = "owner_placeholder",
    status_filter: str = "pending_owner_feedback",
    queue_filter: str = "domain-bootstrap-complete",
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Get a list of domain bootstrap workflows pending owner feedback.
    
    This acts as the 'inbox' for domain owners to review and provide feedback
    on domain configurations and example questions generated by the bootstrap workflow.
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


@router.get("/domains/{workflow_id}/example-questions", response_model=List[Dict[str, Any]])
async def get_example_questions(workflow_id: str) -> List[Dict[str, Any]]:
    """Get example questions generated for a domain bootstrap workflow."""
    if not temporal_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Temporal client not initialized",
        )

    try:
        handle: WorkflowHandle[DomainBootstrapCompleteWorkflow] = temporal_client.get_workflow_handle(
            workflow_id
        )
        
        # Query the workflow for example questions
        status_result = await handle.query(DomainBootstrapCompleteWorkflow.get_bootstrap_status)
        example_questions = status_result.get("example_questions", [])

        return example_questions

    except Exception as e:
        logger.error("Failed to get example questions", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to get example questions: {e!s}",
        ) from e
