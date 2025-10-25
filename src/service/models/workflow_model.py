"""Workflow model for managing workflow definitions and executions."""

from datetime import datetime
from typing import Any

import structlog

from src.service.models.base_model import BaseModel

logger = structlog.get_logger()


class WorkflowModel(BaseModel):
    """Model for workflow operations."""

    table_name = "workflows"

    @classmethod
    async def create_workflow(
        cls,
        name: str,
        domain_id: str,
        yaml_definition: dict[str, Any],
        description: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Create a new workflow definition.

        Args:
            name: Workflow name
            domain_id: Domain UUID
            yaml_definition: Workflow definition as dict
            description: Optional description
            created_by: User ID (optional)

        Returns:
            Created workflow data

        """
        data = {
            "name": name,
            "description": description,
            "domain_id": domain_id,
            "yaml_definition": yaml_definition,
            "is_active": True,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
        }
        return await cls.create(data)

    @classmethod
    async def get_by_domain(cls, domain_id: str) -> list[dict[str, Any]]:
        """Get all workflows in a domain."""
        return await cls.list_all({"domain_id": domain_id})

    @classmethod
    async def get_active_workflows(cls) -> list[dict[str, Any]]:
        """Get all active workflows."""
        return await cls.list_all({"is_active": True})

    @classmethod
    async def toggle_active(
        cls,
        workflow_id: str,
        is_active: bool,
    ) -> dict[str, Any]:
        """Enable or disable a workflow.

        Args:
            workflow_id: Workflow UUID
            is_active: True to enable, False to disable

        Returns:
            Updated workflow data

        """
        logger.info(
            "Toggling workflow active status",
            workflow_id=workflow_id,
            is_active=is_active,
        )
        return await cls.update(workflow_id, {"is_active": is_active})

    @classmethod
    async def record_execution(
        cls,
        workflow_id: str,
        execution_data: dict[str, Any],
    ) -> str | None:
        """Record a workflow execution (store in workflow_executions table).

        Args:
            workflow_id: Workflow UUID
            execution_data: Execution details (status, duration, results, etc.)

        Returns:
            Execution ID if successful, None otherwise

        """
        try:
            supabase = cls.get_client()

            data = {
                "workflow_id": workflow_id,
                "status": execution_data.get("status", "completed"),
                "duration_ms": execution_data.get("duration_ms"),
                "result": execution_data.get("result"),
                "error": execution_data.get("error"),
                "started_at": execution_data.get("started_at"),
                "completed_at": datetime.utcnow().isoformat(),
            }

            response = supabase.table("workflow_executions").insert(data).execute()

            logger.info(
                "Recorded workflow execution",
                workflow_id=workflow_id,
                execution_id=response.data[0].get("id"),
            )

            return response.data[0].get("id")

        except Exception as e:
            logger.error(
                "Failed to record workflow execution",
                workflow_id=workflow_id,
                error=str(e),
            )
            return None

    @classmethod
    async def get_execution_history(
        cls,
        workflow_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get recent execution history for a workflow.

        Args:
            workflow_id: Workflow UUID
            limit: Number of recent executions to return

        Returns:
            List of recent executions

        """
        try:
            supabase = cls.get_client()

            response = (
                supabase.table("workflow_executions")
                .select("*")
                .eq("workflow_id", workflow_id)
                .order("completed_at", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data
        except Exception as e:
            logger.error(
                "Failed to get execution history",
                workflow_id=workflow_id,
                error=str(e),
            )
            return []

    @classmethod
    async def get_execution_stats(cls, workflow_id: str) -> dict[str, Any]:
        """Get execution statistics for a workflow.

        Returns:
            Stats including total runs, success rate, avg duration

        """
        try:
            supabase = cls.get_client()

            response = (
                supabase.table("workflow_executions")
                .select("*")
                .eq("workflow_id", workflow_id)
                .execute()
            )

            executions = response.data
            total = len(executions)
            successful = len([e for e in executions if e["status"] == "completed"])

            durations = [e["duration_ms"] for e in executions if e["duration_ms"]]
            avg_duration = sum(durations) / len(durations) if durations else 0

            return {
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": total - successful,
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "average_duration_ms": avg_duration,
            }
        except Exception as e:
            logger.error(
                "Failed to get execution stats",
                workflow_id=workflow_id,
                error=str(e),
            )
            return {}
