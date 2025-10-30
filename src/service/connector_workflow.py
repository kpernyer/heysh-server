"""Workflow Service Connector - SCI-compliant workflow and inbox management.

Service Connector Interface (SCI) compliant API for managing workflow executions,
definitions, signals, and inbox items for human-in-the-loop (HITL) workflows.

Key SCI principles:
- Singular resource naming: /workflow/execution (not /workflows/executions)
- Hierarchical resources: /workflow/execution/{execution_id}/signal
- RESTful HTTP methods: GET, POST, PUT, DELETE
- snake_case path parameters: {execution_id}, {definition_id}
- Async operations return 202 Accepted with location header
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

import structlog
from fastapi import APIRouter, HTTPException, Query, status, Response
from pydantic import BaseModel, Field

from src.app.auth.dependencies import CurrentUserId
from src.app.clients.supabase import get_supabase_client
from src.service.models.workflow_model import WorkflowModel
from src.service.enhanced_signal_service import enhanced_signal_service

logger = structlog.get_logger()

router = APIRouter(prefix="/workflow", tags=["Workflow"])


# ==================== Models ====================


class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowType(str, Enum):
    """Type of workflow."""

    DATA_PROCESSING = "data_processing"
    DOCUMENT_ANALYSIS = "document_analysis"
    REVIEW_APPROVAL = "review_approval"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class WorkflowDefinition(BaseModel):
    """Workflow definition."""

    id: str
    name: str
    description: Optional[str] = None
    type: WorkflowType
    topic_id: str
    topic_name: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    version: int
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Workflow parameters schema"
    )
    steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="Workflow steps"
    )
    triggers: List[str] = Field(
        default_factory=list, description="Events that trigger this workflow"
    )
    permissions: Dict[str, List[str]] = Field(
        default_factory=dict, description="Permissions required for different actions"
    )


class WorkflowExecution(BaseModel):
    """A workflow execution instance."""

    id: str
    workflow_id: str
    workflow_name: str
    topic_id: str
    topic_name: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    started_by: str
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    current_step: Optional[str] = None
    progress_percentage: int = Field(0, ge=0, le=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StartExecutionRequest(BaseModel):
    """Request to start a workflow execution."""

    workflow_id: str
    input_parameters: Dict[str, Any] = Field(default_factory=dict)


class SendSignalRequest(BaseModel):
    """Request to send a signal to a workflow."""

    signal_name: str = Field(..., min_length=1)
    signal_data: Dict[str, Any] = Field(default_factory=dict)


class InboxItemType(str, Enum):
    """Type of inbox item."""

    APPROVAL_REQUEST = "approval_request"
    REVIEW_REQUEST = "review_request"
    NOTIFICATION = "notification"
    TASK_ASSIGNMENT = "task_assignment"
    MEMBERSHIP_REQUEST = "membership_request"
    WORKFLOW_SIGNAL = "workflow_signal"
    MENTION = "mention"
    SYSTEM_MESSAGE = "system_message"


class InboxItemPriority(str, Enum):
    """Priority of inbox item."""

    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class InboxItemStatus(str, Enum):
    """Status of inbox item."""

    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    ACTIONED = "actioned"


class InboxItem(BaseModel):
    """An item in the user's inbox."""

    id: str
    type: InboxItemType
    priority: InboxItemPriority
    status: InboxItemStatus
    title: str
    description: Optional[str] = None
    from_user_id: Optional[str] = None
    from_user_email: Optional[str] = None
    from_user_name: Optional[str] = None
    topic_id: Optional[str] = None
    topic_name: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_execution_id: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    action_required: bool = False
    actions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Available actions"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InboxStats(BaseModel):
    """Statistics about user's inbox."""

    total_count: int
    unread_count: int
    high_priority_count: int
    action_required_count: int
    by_type: Dict[str, int] = Field(default_factory=dict)
    oldest_unread: Optional[datetime] = None


# ==================== Workflow Definitions ====================


@router.get("/definition", response_model=List[WorkflowDefinition])
async def list_workflow_definitions(
    user_id: CurrentUserId,
    topic_id: Optional[str] = Query(None, description="Filter by topic"),
    workflow_type: Optional[WorkflowType] = Query(None, description="Filter by type"),
    active_only: bool = Query(True, description="Only show active workflows"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[WorkflowDefinition]:
    """List available workflow definitions.

    **Access Control:**
    - Only shows workflows from topics the user has access to
    """
    try:
        supabase = get_supabase_client()

        # Get user's accessible topics
        member_response = supabase.table("domain_members").select("domain_id", "role").eq(
            "user_id", user_id
        ).execute()

        user_topics = {m["domain_id"]: m["role"] for m in member_response.data}

        # Also get public topics
        public_topics = supabase.table("domains").select("id").eq(
            "is_public", True
        ).execute()

        for topic in public_topics.data:
            if topic["id"] not in user_topics:
                user_topics[topic["id"]] = "viewer"  # Read-only access

        if not user_topics:
            return []  # No accessible topics

        # Filter by specific topic if requested
        if topic_id:
            if topic_id not in user_topics:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this topic",
                )
            topic_filter = [topic_id]
        else:
            topic_filter = list(user_topics.keys())

        # Get workflows using the model
        all_workflows = []
        for tid in topic_filter:
            workflows = await WorkflowModel.get_by_domain(tid)
            all_workflows.extend(workflows)

        # Transform to response model
        workflow_definitions = []
        for workflow_data in all_workflows:
            # Apply filters
            if active_only and not workflow_data.get("is_active", True):
                continue

            if workflow_type and workflow_data.get("type") != workflow_type.value:
                continue

            # Get topic name
            topic_response = supabase.table("domains").select("name").eq(
                "id", workflow_data["domain_id"]
            ).execute()

            topic_name = (
                topic_response.data[0]["name"] if topic_response.data else "Unknown"
            )

            definition = WorkflowDefinition(
                id=workflow_data["id"],
                name=workflow_data["name"],
                description=workflow_data.get("description"),
                type=WorkflowType(workflow_data.get("type", "custom")),
                topic_id=workflow_data["domain_id"],
                topic_name=topic_name,
                created_by=workflow_data.get("created_by", "system"),
                created_at=datetime.fromisoformat(workflow_data["created_at"]),
                updated_at=datetime.fromisoformat(workflow_data["updated_at"]),
                is_active=workflow_data.get("is_active", True),
                version=workflow_data.get("version", 1),
                parameters=workflow_data.get("yaml_definition", {}).get("parameters", {}),
                steps=workflow_data.get("yaml_definition", {}).get("steps", []),
                triggers=workflow_data.get("yaml_definition", {}).get("triggers", []),
                permissions=workflow_data.get("permissions", {}),
            )
            workflow_definitions.append(definition)

        # Apply pagination
        start = offset
        end = offset + limit
        return workflow_definitions[start:end]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list workflow definitions", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflow definitions: {e}",
        )


@router.get("/definition/{definition_id}", response_model=WorkflowDefinition)
async def get_workflow_definition(
    definition_id: str,
    user_id: CurrentUserId,
) -> WorkflowDefinition:
    """Get detailed information about a specific workflow definition.

    **Access Control:**
    - User must have access to the workflow's topic
    """
    try:
        # Get workflow
        workflow_data = await WorkflowModel.get_by_id(definition_id)

        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow definition not found: {definition_id}",
            )

        # Check access
        supabase = get_supabase_client()

        # Check if user has access to the topic
        topic_response = supabase.table("domains").select("id", "name", "is_public").eq(
            "id", workflow_data["domain_id"]
        ).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated topic not found",
            )

        topic = topic_response.data[0]
        is_public = topic.get("is_public", False)

        if not is_public:
            # Check membership
            member_check = supabase.table("domain_members").select("id").eq(
                "domain_id", workflow_data["domain_id"]
            ).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this workflow",
                )

        # Build response
        definition = WorkflowDefinition(
            id=workflow_data["id"],
            name=workflow_data["name"],
            description=workflow_data.get("description"),
            type=WorkflowType(workflow_data.get("type", "custom")),
            topic_id=workflow_data["domain_id"],
            topic_name=topic["name"],
            created_by=workflow_data.get("created_by", "system"),
            created_at=datetime.fromisoformat(workflow_data["created_at"]),
            updated_at=datetime.fromisoformat(workflow_data["updated_at"]),
            is_active=workflow_data.get("is_active", True),
            version=workflow_data.get("version", 1),
            parameters=workflow_data.get("yaml_definition", {}).get("parameters", {}),
            steps=workflow_data.get("yaml_definition", {}).get("steps", []),
            triggers=workflow_data.get("yaml_definition", {}).get("triggers", []),
            permissions=workflow_data.get("permissions", {}),
        )

        return definition

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get workflow definition", definition_id=definition_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow definition: {e}",
        )


# ==================== Workflow Executions ====================


@router.get("/execution", response_model=List[WorkflowExecution])
async def list_workflow_executions(
    user_id: CurrentUserId,
    workflow_id: Optional[str] = Query(None, description="Filter by workflow"),
    topic_id: Optional[str] = Query(None, description="Filter by topic"),
    status_filter: Optional[WorkflowStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    started_after: Optional[datetime] = Query(None),
    started_before: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[WorkflowExecution]:
    """List workflow executions.

    **Access Control:**
    - Only shows executions from topics the user has access to
    """
    try:
        supabase = get_supabase_client()

        # Get user's accessible topics
        member_response = supabase.table("domain_members").select("domain_id").eq(
            "user_id", user_id
        ).execute()

        user_topic_ids = [m["domain_id"] for m in member_response.data]

        # Also get public topics
        public_topics = supabase.table("domains").select("id").eq(
            "is_public", True
        ).execute()

        public_topic_ids = [t["id"] for t in public_topics.data]

        # Combine accessible topics
        accessible_topic_ids = list(set(user_topic_ids + public_topic_ids))

        if not accessible_topic_ids:
            return []

        # Build query
        query = supabase.table("workflow_executions").select("*")

        # Filter by workflow if specified
        if workflow_id:
            # Verify access to workflow first
            workflow_data = await WorkflowModel.get_by_id(workflow_id)
            if not workflow_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workflow not found: {workflow_id}",
                )
            if workflow_data["domain_id"] not in accessible_topic_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this workflow",
                )
            query = query.eq("workflow_id", workflow_id)

        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter.value)

        if started_after:
            query = query.gte("started_at", started_after.isoformat())

        if started_before:
            query = query.lte("started_at", started_before.isoformat())

        # Execute with pagination
        executions_response = query.order("started_at", desc=True).range(
            offset, offset + limit - 1
        ).execute()

        # Transform to response model
        executions = []
        for exec_data in executions_response.data:
            # Get workflow details
            workflow_data = await WorkflowModel.get_by_id(exec_data["workflow_id"])
            if not workflow_data:
                continue  # Skip if workflow not found

            # Check if user has access to this execution's topic
            if workflow_data["domain_id"] not in accessible_topic_ids:
                continue  # Skip if no access

            # Get topic name
            topic_response = supabase.table("domains").select("name").eq(
                "id", workflow_data["domain_id"]
            ).execute()
            topic_name = (
                topic_response.data[0]["name"] if topic_response.data else "Unknown"
            )

            execution = WorkflowExecution(
                id=exec_data["id"],
                workflow_id=exec_data["workflow_id"],
                workflow_name=workflow_data["name"],
                topic_id=workflow_data["domain_id"],
                topic_name=topic_name,
                status=WorkflowStatus(exec_data["status"]),
                started_at=datetime.fromisoformat(exec_data["started_at"]),
                completed_at=datetime.fromisoformat(exec_data["completed_at"])
                if exec_data.get("completed_at")
                else None,
                started_by=exec_data["started_by"],
                error_message=exec_data.get("error_message"),
                result=exec_data.get("result"),
                current_step=exec_data.get("current_step"),
                progress_percentage=exec_data.get("progress_percentage", 0),
                metadata=exec_data.get("metadata", {}),
            )
            executions.append(execution)

        return executions

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list workflow executions", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflow executions: {e}",
        )


@router.post(
    "/execution",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Dict[str, str],
)
async def start_workflow_execution(
    request: StartExecutionRequest,
    user_id: CurrentUserId,
    response: Response,
) -> Dict[str, str]:
    """Start a new workflow execution.

    **Returns:**
    - 202 Accepted (async operation)
    - Location header with URL to check execution status

    **Access Control:**
    - User must have access to the workflow's topic
    - User must have appropriate role (contributor or higher)
    """
    try:
        # Get workflow
        workflow_data = await WorkflowModel.get_by_id(request.workflow_id)

        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {request.workflow_id}",
            )

        # Check access
        supabase = get_supabase_client()

        member_response = supabase.table("domain_members").select("role").eq(
            "domain_id", workflow_data["domain_id"]
        ).eq("user_id", user_id).execute()

        if not member_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this topic",
            )

        user_role = member_response.data[0]["role"]

        if user_role == "member":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members cannot start workflows. Contributor role or higher required.",
            )

        # TODO: Start actual workflow execution via Temporal
        # For now, create a placeholder execution ID
        execution_id = f"exec-{request.workflow_id}-{int(datetime.now().timestamp())}"

        # Set Location header (SCI compliance)
        response.headers["Location"] = f"/workflow/execution/{execution_id}"

        return {
            "status": "accepted",
            "message": "Workflow execution started",
            "execution_id": execution_id,
            "workflow_id": request.workflow_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start workflow execution", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow execution: {e}",
        )


@router.get("/execution/{execution_id}", response_model=WorkflowExecution)
async def get_workflow_execution(
    execution_id: str,
    user_id: CurrentUserId,
) -> WorkflowExecution:
    """Get details of a specific workflow execution.

    **Access Control:**
    - User must have access to the execution's topic
    """
    try:
        supabase = get_supabase_client()

        # Get execution
        execution_response = supabase.table("workflow_executions").select("*").eq(
            "id", execution_id
        ).execute()

        if not execution_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution not found: {execution_id}",
            )

        exec_data = execution_response.data[0]

        # Get workflow to check access
        workflow_data = await WorkflowModel.get_by_id(exec_data["workflow_id"])

        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated workflow not found",
            )

        # Check topic access
        topic_response = supabase.table("domains").select("id", "name", "is_public").eq(
            "id", workflow_data["domain_id"]
        ).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated topic not found",
            )

        topic = topic_response.data[0]
        is_public = topic.get("is_public", False)

        if not is_public:
            member_check = supabase.table("domain_members").select("id").eq(
                "domain_id", workflow_data["domain_id"]
            ).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this execution",
                )

        execution = WorkflowExecution(
            id=exec_data["id"],
            workflow_id=exec_data["workflow_id"],
            workflow_name=workflow_data["name"],
            topic_id=workflow_data["domain_id"],
            topic_name=topic["name"],
            status=WorkflowStatus(exec_data["status"]),
            started_at=datetime.fromisoformat(exec_data["started_at"]),
            completed_at=datetime.fromisoformat(exec_data["completed_at"])
            if exec_data.get("completed_at")
            else None,
            started_by=exec_data["started_by"],
            error_message=exec_data.get("error_message"),
            result=exec_data.get("result"),
            current_step=exec_data.get("current_step"),
            progress_percentage=exec_data.get("progress_percentage", 0),
            metadata=exec_data.get("metadata", {}),
        )

        return execution

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get workflow execution", execution_id=execution_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow execution: {e}",
        )


@router.post(
    "/execution/{execution_id}/signal",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Dict[str, str],
)
async def send_workflow_signal(
    execution_id: str,
    request: SendSignalRequest,
    user_id: CurrentUserId,
    response: Response,
) -> Dict[str, str]:
    """Send a signal to a running workflow execution.

    Signals are used for human-in-the-loop interactions, approvals, and dynamic
    workflow control.

    **Returns:**
    - 202 Accepted (async operation)

    **Access Control:**
    - User must have access to the execution's topic
    """
    try:
        # Get execution and verify access (same as get_workflow_execution)
        supabase = get_supabase_client()

        execution_response = supabase.table("workflow_executions").select("*").eq(
            "id", execution_id
        ).execute()

        if not execution_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution not found: {execution_id}",
            )

        exec_data = execution_response.data[0]

        # Get workflow to check access
        workflow_data = await WorkflowModel.get_by_id(exec_data["workflow_id"])

        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated workflow not found",
            )

        # Check topic access
        topic_response = supabase.table("domains").select("is_public").eq(
            "id", workflow_data["domain_id"]
        ).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated topic not found",
            )

        is_public = topic_response.data[0].get("is_public", False)

        if not is_public:
            member_check = supabase.table("domain_members").select("id").eq(
                "domain_id", workflow_data["domain_id"]
            ).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to send signals to this execution",
                )

        # TODO: Send actual signal to Temporal workflow
        # For now, return placeholder response

        return {
            "status": "accepted",
            "message": f"Signal '{request.signal_name}' sent to execution",
            "execution_id": execution_id,
            "signal_name": request.signal_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send workflow signal", execution_id=execution_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send workflow signal: {e}",
        )


@router.delete("/execution/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_workflow_execution(
    execution_id: str,
    user_id: CurrentUserId,
) -> None:
    """Cancel a running workflow execution.

    **Access Control:**
    - User must be the starter, admin, or owner of the topic
    """
    try:
        supabase = get_supabase_client()

        # Get execution
        execution_response = supabase.table("workflow_executions").select("*").eq(
            "id", execution_id
        ).execute()

        if not execution_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution not found: {execution_id}",
            )

        exec_data = execution_response.data[0]

        # Get workflow
        workflow_data = await WorkflowModel.get_by_id(exec_data["workflow_id"])

        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated workflow not found",
            )

        # Check if user is the starter
        if exec_data["started_by"] != user_id:
            # Check if user is admin or owner
            member_check = supabase.table("domain_members").select("role").eq(
                "domain_id", workflow_data["domain_id"]
            ).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this execution",
                )

            user_role = member_check.data[0]["role"]
            if user_role not in ["admin", "owner"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only execution starter, admin, or owner can cancel execution",
                )

        # TODO: Cancel actual Temporal workflow
        # For now, just update status
        supabase.table("workflow_executions").update(
            {"status": WorkflowStatus.CANCELLED.value}
        ).eq("id", execution_id).execute()

        logger.info("Workflow execution cancelled", execution_id=execution_id, user_id=user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to cancel workflow execution", execution_id=execution_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel workflow execution: {e}",
        )


# ==================== Inbox (Human-in-the-Loop) ====================


@router.get("/inbox", response_model=List[InboxItem])
async def get_user_inbox(
    user_id: CurrentUserId,
    status_filter: Optional[InboxItemStatus] = Query(None, alias="status"),
    type_filter: Optional[InboxItemType] = Query(None, alias="type"),
    priority: Optional[InboxItemPriority] = Query(None),
    topic_id: Optional[str] = Query(None),
    action_required: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[InboxItem]:
    """Get user's inbox items for human-in-the-loop workflows.

    Returns items sorted by priority and creation time.

    **Access Control:**
    - Only returns items for the authenticated user
    """
    try:
        # Use the existing signal service for workflow signals
        signals = await enhanced_signal_service.get_user_inbox(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=(status_filter == InboxItemStatus.UNREAD) if status_filter else False,
        )

        # Transform signals to inbox items
        inbox_items = []
        for signal in signals.get("signals", []):
            # Map signal to inbox item
            inbox_item = InboxItem(
                id=signal["id"],
                type=InboxItemType.WORKFLOW_SIGNAL,
                priority=InboxItemPriority.NORMAL,
                status=InboxItemStatus.UNREAD
                if signal.get("is_unread")
                else InboxItemStatus.READ,
                title=signal.get("signal_type", "Workflow Signal"),
                description=signal.get("data", {}).get("message"),
                from_user_id=signal.get("from_user_id"),
                from_user_email=None,  # Would need to look up
                from_user_name=None,
                topic_id=signal.get("domain_id"),
                topic_name=signal.get("domain_name"),
                workflow_id=signal.get("workflow_id"),
                workflow_execution_id=signal.get("workflow_execution_id"),
                created_at=datetime.fromisoformat(signal["created_at"]),
                read_at=datetime.fromisoformat(signal["read_at"])
                if signal.get("read_at")
                else None,
                expires_at=datetime.fromisoformat(signal["expires_at"])
                if signal.get("expires_at")
                else None,
                action_required=signal.get("action_required", False),
                actions=signal.get("available_actions", []),
                metadata=signal.get("data", {}),
            )

            # Apply filters
            if type_filter and inbox_item.type != type_filter:
                continue
            if priority and inbox_item.priority != priority:
                continue
            if topic_id and inbox_item.topic_id != topic_id:
                continue
            if action_required is not None and inbox_item.action_required != action_required:
                continue

            inbox_items.append(inbox_item)

        return inbox_items

    except Exception as e:
        logger.error("Failed to get inbox", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inbox: {e}",
        )


@router.get("/inbox/stats", response_model=InboxStats)
async def get_inbox_statistics(
    user_id: CurrentUserId,
) -> InboxStats:
    """Get statistics about user's inbox."""
    try:
        # Get unread count from signal service
        unread_count = await enhanced_signal_service.get_unread_count(user_id)

        # Get full inbox for detailed stats
        all_signals = await enhanced_signal_service.get_user_inbox(
            user_id=user_id,
            limit=1000,  # Get all for stats
            offset=0,
        )

        signals = all_signals.get("signals", [])

        # Calculate stats
        total_count = len(signals)
        high_priority_count = 0
        action_required_count = 0
        by_type = {}
        oldest_unread = None

        for signal in signals:
            # Count by type
            signal_type = signal.get("signal_type", "unknown")
            by_type[signal_type] = by_type.get(signal_type, 0) + 1

            # Count action required
            if signal.get("action_required"):
                action_required_count += 1

            # Track oldest unread
            if signal.get("is_unread"):
                created_at = datetime.fromisoformat(signal["created_at"])
                if oldest_unread is None or created_at < oldest_unread:
                    oldest_unread = created_at

        return InboxStats(
            total_count=total_count,
            unread_count=unread_count,
            high_priority_count=high_priority_count,
            action_required_count=action_required_count,
            by_type=by_type,
            oldest_unread=oldest_unread,
        )

    except Exception as e:
        logger.error("Failed to get inbox stats", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inbox stats: {e}",
        )


@router.put("/inbox/{item_id}/read", response_model=Dict[str, str])
async def mark_inbox_item_read(
    item_id: str,
    user_id: CurrentUserId,
) -> Dict[str, str]:
    """Mark an inbox item as read."""
    try:
        # Mark signal as read
        await enhanced_signal_service.mark_signal_read(signal_id=item_id, user_id=user_id)

        return {"status": "success", "message": f"Item {item_id} marked as read"}

    except Exception as e:
        logger.error("Failed to mark item as read", item_id=item_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark item as read: {e}",
        )


@router.delete("/inbox/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_inbox_item(
    item_id: str,
    user_id: CurrentUserId,
) -> None:
    """Archive (soft delete) an inbox item."""
    try:
        # Archive the signal
        await enhanced_signal_service.archive_signal(signal_id=item_id, user_id=user_id)

    except Exception as e:
        logger.error("Failed to archive item", item_id=item_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive item: {e}",
        )
