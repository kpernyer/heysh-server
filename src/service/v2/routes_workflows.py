"""Workflows API routes - Read-only access to workflow information."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.app.auth.dependencies import CurrentUserId
from src.app.clients.supabase import get_supabase_client
from src.service.models.workflow_model import WorkflowModel

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v2/workflows", tags=["Workflows"])


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
    description: Optional[str]
    type: WorkflowType
    topic_id: str
    topic_name: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    version: int
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters schema")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Workflow steps")
    triggers: List[str] = Field(default_factory=list, description="Events that trigger this workflow")
    permissions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Permissions required for different actions"
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
    completed_at: Optional[datetime]
    started_by: str
    error_message: Optional[str]
    result: Optional[Dict[str, Any]]
    current_step: Optional[str]
    progress_percentage: int = Field(0, ge=0, le=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStatistics(BaseModel):
    """Statistics for a workflow."""
    workflow_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration_seconds: Optional[float]
    last_execution_at: Optional[datetime]
    success_rate: float = Field(0.0, ge=0.0, le=1.0)


class WorkflowStep(BaseModel):
    """A step in workflow execution."""
    id: str
    execution_id: str
    step_name: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error: Optional[str]
    duration_ms: Optional[int]


# ==================== List Workflows ====================

@router.get("/", response_model=List[WorkflowDefinition])
async def list_workflows(
    user_id: CurrentUserId,
    topic_id: Optional[str] = Query(None, description="Filter by topic"),
    workflow_type: Optional[WorkflowType] = Query(None, description="Filter by type"),
    active_only: bool = Query(True, description="Only show active workflows"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[WorkflowDefinition]:
    """List available workflow definitions.

    Only shows workflows from topics the user has access to.
    """
    try:
        supabase = get_supabase_client()

        # Get user's accessible topics
        member_response = supabase.table("domain_members").select(
            "domain_id", "role"
        ).eq("user_id", user_id).execute()

        user_topics = {m["domain_id"]: m["role"] for m in member_response.data}

        # Also get public topics
        public_topics = supabase.table("domains").select(
            "id"
        ).eq("is_public", True).execute()

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
                    detail="You don't have access to this topic"
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

            topic_name = topic_response.data[0]["name"] if topic_response.data else "Unknown"

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
                permissions=workflow_data.get("permissions", {})
            )
            workflow_definitions.append(definition)

        # Apply pagination
        start = offset
        end = offset + limit
        return workflow_definitions[start:end]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list workflows", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflows: {e}"
        )


# ==================== Get Workflow Details ====================

@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow_details(
    workflow_id: str,
    user_id: CurrentUserId,
) -> WorkflowDefinition:
    """Get detailed information about a specific workflow.

    User must have access to the workflow's topic.
    """
    try:
        # Get workflow
        workflow_data = await WorkflowModel.get_by_id(workflow_id)

        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}"
            )

        # Check access
        supabase = get_supabase_client()

        # Check if user has access to the topic
        topic_response = supabase.table("domains").select(
            "id", "name", "is_public"
        ).eq("id", workflow_data["domain_id"]).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated topic not found"
            )

        topic = topic_response.data[0]
        is_public = topic.get("is_public", False)

        if not is_public:
            # Check membership
            member_check = supabase.table("domain_members").select(
                "id"
            ).eq("domain_id", workflow_data["domain_id"]).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this workflow"
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
            permissions=workflow_data.get("permissions", {})
        )

        return definition

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow details", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow details: {e}"
        )


# ==================== Get Workflow Executions ====================

@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecution])
async def get_workflow_executions(
    workflow_id: str,
    user_id: CurrentUserId,
    status_filter: Optional[WorkflowStatus] = Query(None),
    started_after: Optional[datetime] = Query(None),
    started_before: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[WorkflowExecution]:
    """Get execution history for a workflow.

    User must have access to the workflow's topic.
    """
    try:
        # First verify access to the workflow
        workflow_data = await WorkflowModel.get_by_id(workflow_id)

        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}"
            )

        supabase = get_supabase_client()

        # Check topic access
        topic_response = supabase.table("domains").select(
            "id", "name", "is_public"
        ).eq("id", workflow_data["domain_id"]).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated topic not found"
            )

        topic = topic_response.data[0]
        is_public = topic.get("is_public", False)

        if not is_public:
            member_check = supabase.table("domain_members").select(
                "id"
            ).eq("domain_id", workflow_data["domain_id"]).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this workflow"
                )

        # Get executions (assuming workflow_executions table)
        query = supabase.table("workflow_executions").select("*").eq(
            "workflow_id", workflow_id
        )

        # Apply filters
        if status_filter:
            query = query.eq("status", status_filter.value)

        if started_after:
            query = query.gte("started_at", started_after.isoformat())

        if started_before:
            query = query.lte("started_at", started_before.isoformat())

        # Order by start time descending and apply pagination
        executions_response = query.order("started_at", desc=True).range(
            offset, offset + limit - 1
        ).execute()

        # Transform to response model
        executions = []
        for exec_data in executions_response.data:
            execution = WorkflowExecution(
                id=exec_data["id"],
                workflow_id=exec_data["workflow_id"],
                workflow_name=workflow_data["name"],
                topic_id=workflow_data["domain_id"],
                topic_name=topic["name"],
                status=WorkflowStatus(exec_data["status"]),
                started_at=datetime.fromisoformat(exec_data["started_at"]),
                completed_at=datetime.fromisoformat(exec_data["completed_at"]) if exec_data.get("completed_at") else None,
                started_by=exec_data["started_by"],
                error_message=exec_data.get("error_message"),
                result=exec_data.get("result"),
                current_step=exec_data.get("current_step"),
                progress_percentage=exec_data.get("progress_percentage", 0),
                metadata=exec_data.get("metadata", {})
            )
            executions.append(execution)

        return executions

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow executions", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow executions: {e}"
        )


# ==================== Get Workflow Status ====================

@router.get("/{workflow_id}/status", response_model=Dict[str, Any])
async def get_workflow_status(
    workflow_id: str,
    user_id: CurrentUserId,
) -> Dict[str, Any]:
    """Get current status and statistics for a workflow."""
    try:
        # Verify access (same as above)
        workflow_data = await WorkflowModel.get_by_id(workflow_id)

        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}"
            )

        supabase = get_supabase_client()

        # Check topic access
        topic_response = supabase.table("domains").select(
            "id", "is_public"
        ).eq("id", workflow_data["domain_id"]).execute()

        if not topic_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated topic not found"
            )

        is_public = topic_response.data[0].get("is_public", False)

        if not is_public:
            member_check = supabase.table("domain_members").select(
                "id"
            ).eq("domain_id", workflow_data["domain_id"]).eq("user_id", user_id).execute()

            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this workflow"
                )

        # Get statistics (assuming workflow_executions table)
        all_executions = supabase.table("workflow_executions").select(
            "status", "started_at", "completed_at"
        ).eq("workflow_id", workflow_id).execute()

        # Calculate statistics
        total_executions = len(all_executions.data)
        successful_executions = sum(
            1 for e in all_executions.data if e["status"] == WorkflowStatus.COMPLETED.value
        )
        failed_executions = sum(
            1 for e in all_executions.data if e["status"] == WorkflowStatus.FAILED.value
        )
        running_executions = sum(
            1 for e in all_executions.data if e["status"] == WorkflowStatus.RUNNING.value
        )

        # Calculate average duration
        durations = []
        for exec_data in all_executions.data:
            if exec_data.get("completed_at") and exec_data.get("started_at"):
                start = datetime.fromisoformat(exec_data["started_at"])
                end = datetime.fromisoformat(exec_data["completed_at"])
                duration = (end - start).total_seconds()
                durations.append(duration)

        average_duration = sum(durations) / len(durations) if durations else None

        # Get last execution time
        last_execution_at = None
        if all_executions.data:
            last_execution_at = max(
                datetime.fromisoformat(e["started_at"]) for e in all_executions.data
            )

        success_rate = successful_executions / total_executions if total_executions > 0 else 0.0

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow_data["name"],
            "is_active": workflow_data.get("is_active", True),
            "statistics": {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "running_executions": running_executions,
                "average_duration_seconds": average_duration,
                "last_execution_at": last_execution_at.isoformat() if last_execution_at else None,
                "success_rate": success_rate
            },
            "current_status": "running" if running_executions > 0 else "idle"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow status", workflow_id=workflow_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {e}"
        )