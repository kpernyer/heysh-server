"""Isolated Domain Bootstrap Workflow - No problematic imports."""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Allow imports from src.app for activities
with workflow.unsafe.imports_passed_through():
    from src.app.models.domain import BootstrapInput, BootstrapResult, DomainStatus


class BootstrapStatus(Enum):
    """Bootstrap workflow status."""
    STARTED = "started"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    PENDING_OWNER_REVIEW = "pending_owner_review"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BootstrapState:
    """Bootstrap workflow state."""
    status: BootstrapStatus = BootstrapStatus.STARTED
    domain_config: Optional[Dict[str, Any]] = None
    research_results: Optional[Dict[str, Any]] = None
    analysis_results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    owner_feedback: Optional[Dict[str, Any]] = None


@workflow.defn(name="DomainBootstrapWorkflowIsolated")
class DomainBootstrapWorkflowIsolated:
    """
    Isolated Domain Bootstrap Workflow.
    
    This workflow orchestrates the bootstrapping of a new knowledge domain
    with AI research, analysis, and owner approval.
    """

    def __init__(self):
        self.state = BootstrapState()

    @workflow.run
    async def run(self, input: BootstrapInput) -> BootstrapResult:
        """Run the domain bootstrap workflow."""
        workflow.logger.info(f"Starting domain bootstrap for: {input.domain_name}")
        
        try:
            # Step 1: Domain Research
            self.state.status = BootstrapStatus.RESEARCHING
            workflow.logger.info("Starting domain research...")
            
            # Import activities here to avoid sandbox issues
            from activity.domain_research import research_domain_activity
            
            research_input = {
                "domain_name": input.domain_name,
                "domain_description": input.domain_description,
                "initial_topics": input.initial_topics,
                "target_audience": input.target_audience,
                "research_focus": input.research_focus,
                "research_depth": "comprehensive",
                "include_historical": True,
                "include_technical": True,
                "include_practical": True,
            }
            
            self.state.research_results = await workflow.execute_activity(
                research_domain_activity,
                args=[research_input],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            workflow.logger.info("Domain research completed.")

            # Step 2: Analysis
            self.state.status = BootstrapStatus.ANALYZING
            workflow.logger.info("Starting analysis...")
            
            from activity.domain_research import analyze_research_results_activity
            
            self.state.analysis_results = await workflow.execute_activity(
                analyze_research_results_activity,
                args=[input.domain_name, input.domain_description, self.state.research_results],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            workflow.logger.info("Analysis completed.")

            # Step 3: Generate Domain Config
            workflow.logger.info("Generating domain configuration...")
            
            from activity.domain_research import generate_domain_config_activity
            
            self.state.domain_config = await workflow.execute_activity(
                generate_domain_config_activity,
                args=[str(input.owner_id), input.domain_name, input.domain_description, self.state.analysis_results],
                task_queue="general-queue",
                start_to_close_timeout=timedelta(minutes=1),
            )
            workflow.logger.info("Domain configuration generated.")

            # Step 4: Wait for Owner Review
            self.state.status = BootstrapStatus.PENDING_OWNER_REVIEW
            workflow.logger.info("Waiting for owner review...")
            
            # Notify owner
            from activity.notification import notify_user_activity
            
            await workflow.execute_activity(
                notify_user_activity,
                args=[
                    str(input.owner_id),
                    f"Domain Review Required: {input.domain_name}",
                    f"Your domain '{input.domain_name}' is ready for review. Please provide your feedback.",
                ],
                task_queue="general-queue",
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Wait for owner decision (simplified - just wait 30 seconds for demo)
            await asyncio.sleep(30)
            
            # For demo purposes, auto-approve
            self.state.owner_feedback = {
                "approved": True,
                "comments": "Auto-approved for demo",
                "quality_rating": "excellent"
            }
            
            self.state.status = BootstrapStatus.COMPLETED
            workflow.logger.info("Domain bootstrap completed successfully.")

            return BootstrapResult(
                domain_id=input.domain_id,
                status=DomainStatus.ACTIVE,
                domain_config=self.state.domain_config,
                research_results=self.state.research_results,
                analysis_results=self.state.analysis_results,
                owner_feedback=self.state.owner_feedback,
                success=True,
                message="Domain bootstrap completed successfully"
            )

        except Exception as e:
            self.state.status = BootstrapStatus.FAILED
            self.state.error_message = str(e)
            workflow.logger.error(f"Domain bootstrap failed: {e}")
            
            return BootstrapResult(
                domain_id=input.domain_id,
                status=DomainStatus.REJECTED,
                error_message=str(e),
                success=False,
                message=f"Domain bootstrap failed: {e}"
            )

    @workflow.signal
    async def submit_owner_feedback(self, feedback: Dict[str, Any]):
        """Signal for owner to submit feedback."""
        workflow.logger.info(f"Owner feedback received: {feedback}")
        self.state.owner_feedback = feedback

    @workflow.query
    def get_bootstrap_status(self) -> Dict[str, Any]:
        """Query current bootstrap status."""
        return {
            "status": self.state.status.value,
            "domain_config": self.state.domain_config,
            "research_results": self.state.research_results,
            "analysis_results": self.state.analysis_results,
            "error_message": self.state.error_message,
            "owner_feedback": self.state.owner_feedback,
        }
