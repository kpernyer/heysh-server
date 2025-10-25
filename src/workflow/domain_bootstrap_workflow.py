"""Domain Bootstrap Workflow for initializing new knowledge domains."""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from temporalio import workflow
from temporalio.common import RetryPolicy

# Allow imports from src.app for activities
with workflow.unsafe.imports_passed_through():
    from activity.domain_research import research_domain_activity, analyze_research_results_activity
    from activity.notification import notify_user_activity
    from src.app.models.domain import BootstrapInput, BootstrapResult, DomainStatus

logger = structlog.get_logger()


class BootstrapStatus(Enum):
    """Bootstrap workflow status."""
    STARTED = "started"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    PENDING_OWNER_REVIEW = "pending_owner_review"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BootstrapWorkflowInput:
    """Input for bootstrap workflow."""
    domain_id: str
    owner_id: str
    domain_name: str
    domain_description: str
    initial_topics: List[str]
    target_audience: List[str]
    research_focus: Optional[str] = None
    quality_requirements: Dict[str, Any] = None
    research_depth: str = "comprehensive"
    include_historical: bool = True
    include_technical: bool = True
    include_practical: bool = True


@workflow.defn(name="DomainBootstrapWorkflow")
class DomainBootstrapWorkflow:
    """
    Bootstrap workflow for initializing new knowledge domains.
    
    This workflow:
    1. Researches the domain using AI
    2. Analyzes research results
    3. Creates domain configuration
    4. Waits for owner approval
    5. Completes domain setup
    """

    def __init__(self):
        """Initialize the bootstrap workflow."""
        self.status: BootstrapStatus = BootstrapStatus.STARTED
        self.research_results: Optional[Dict[str, Any]] = None
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.domain_config: Optional[Dict[str, Any]] = None
        self.owner_approved: bool = False
        self.error_message: Optional[str] = None

    @workflow.run
    async def run(self, input: BootstrapWorkflowInput) -> BootstrapResult:
        """Execute the domain bootstrap workflow."""
        workflow.logger.info(
            "Starting DomainBootstrapWorkflow",
            domain_id=input.domain_id,
            domain_name=input.domain_name,
            owner_id=input.owner_id,
        )
        
        self.status = BootstrapStatus.STARTED

        try:
            # Step 1: Create initial domain record
            await workflow.execute_activity(
                create_domain_activity,
                args=[input.domain_id, input.owner_id, input.domain_name, input.domain_description],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=2),
            )

            # Step 2: Research domain using AI
            self.status = BootstrapStatus.RESEARCHING
            workflow.logger.info("Starting domain research", domain_id=input.domain_id)
            
            research_input = {
                "domain_name": input.domain_name,
                "domain_description": input.domain_description,
                "initial_topics": input.initial_topics,
                "target_audience": input.target_audience,
                "research_focus": input.research_focus,
                "research_depth": input.research_depth,
                "include_historical": input.include_historical,
                "include_technical": input.include_technical,
                "include_practical": input.include_practical,
            }
            
            self.research_results = await workflow.execute_activity(
                research_domain_activity,
                args=[research_input],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=15),
            )

            # Step 3: Analyze research results
            self.status = BootstrapStatus.ANALYZING
            workflow.logger.info("Analyzing research results", domain_id=input.domain_id)
            
            self.analysis_results = await workflow.execute_activity(
                analyze_research_results_activity,
                args=[self.research_results, input.domain_name],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=10),
            )

            # Step 4: Generate domain configuration
            self.domain_config = self._generate_domain_config(input, self.analysis_results)
            
            # Step 5: Update domain with research results
            await workflow.execute_activity(
                update_domain_activity,
                args=[input.domain_id, self.domain_config],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=2),
            )

            # Step 6: Notify owner for review
            self.status = BootstrapStatus.PENDING_OWNER_REVIEW
            workflow.logger.info("Requesting owner review", domain_id=input.domain_id)
            
            await workflow.execute_activity(
                notify_user_activity,
                args=[
                    input.owner_id,
                    "Domain Bootstrap Complete - Review Required",
                    f"Your domain '{input.domain_name}' has been researched and analyzed. Please review the results and approve to complete the setup.",
                ],
                task_queue="general-queue",
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Upsert Search Attributes for HITL inbox
            await workflow.upsert_search_attributes(
                assignee=[input.owner_id],
                queue=["domain-bootstrap"],
                status=[BootstrapStatus.PENDING_OWNER_REVIEW.value],
                priority=["high"],
                domain_id=[input.domain_id],
                domain_name=[input.domain_name],
                owner_id=[input.owner_id],
                due_at=[(workflow.now() + timedelta(days=3)).isoformat()],
            )

            # Step 7: Wait for owner approval (with timeout)
            try:
                await workflow.wait_condition(
                    lambda: self.owner_approved, 
                    timeout=timedelta(days=7)
                )
                
                if self.owner_approved:
                    self.status = BootstrapStatus.COMPLETED
                    workflow.logger.info("Domain bootstrap completed", domain_id=input.domain_id)
                    
                    # Final domain update
                    await workflow.execute_activity(
                        update_domain_activity,
                        args=[input.domain_id, {"status": DomainStatus.ACTIVE.value}],
                        task_queue="storage-queue",
                        start_to_close_timeout=timedelta(minutes=1),
                    )
                    
                    # Notify owner of completion
                    await workflow.execute_activity(
                        notify_user_activity,
                        args=[
                            input.owner_id,
                            "Domain Bootstrap Complete",
                            f"Your domain '{input.domain_name}' is now active and ready for contributions.",
                        ],
                        task_queue="general-queue",
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                else:
                    self.status = BootstrapStatus.FAILED
                    self.error_message = "Owner did not approve the domain configuration"
                    
            except asyncio.TimeoutError:
                self.status = BootstrapStatus.FAILED
                self.error_message = "Owner review timed out"
                workflow.logger.warning("Owner review timed out", domain_id=input.domain_id)

        except Exception as e:
            self.status = BootstrapStatus.FAILED
            self.error_message = str(e)
            workflow.logger.error(
                f"Domain bootstrap workflow failed: domain_id={input.domain_id}, error={e!s}"
            )
            raise

        # Final Search Attributes update
        await workflow.upsert_search_attributes(
            status=[self.status.value],
            error_message=[self.error_message or ""],
            owner_approved=[self.owner_approved],
        )

        return BootstrapResult(
            domain_id=input.domain_id,
            status=self.status.value,
            research_summary=self.research_results.get("summary", "") if self.research_results else "",
            discovered_topics=self.analysis_results.get("topics", []) if self.analysis_results else [],
            quality_criteria=self.domain_config.get("quality_criteria", {}) if self.domain_config else {},
            search_attributes=self.domain_config.get("search_attributes", {}) if self.domain_config else {},
            research_sources=self.research_results.get("sources", []) if self.research_results else [],
            recommendations=self.analysis_results.get("recommendations", []) if self.analysis_results else [],
        )

    @workflow.signal
    async def approve_domain_config(self):
        """Signal for owner to approve domain configuration."""
        workflow.logger.info("Owner approved domain configuration")
        self.owner_approved = True

    @workflow.signal
    async def reject_domain_config(self, reason: str):
        """Signal for owner to reject domain configuration."""
        workflow.logger.info(f"Owner rejected domain configuration: {reason}")
        self.owner_approved = False
        self.error_message = f"Rejected by owner: {reason}"

    @workflow.query
    def get_bootstrap_status(self) -> Dict[str, Any]:
        """Query current bootstrap status."""
        return {
            "status": self.status.value,
            "research_results": self.research_results,
            "analysis_results": self.analysis_results,
            "domain_config": self.domain_config,
            "owner_approved": self.owner_approved,
            "error_message": self.error_message,
        }

    def _generate_domain_config(
        self, 
        input: BootstrapWorkflowInput, 
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate domain configuration from analysis results."""
        return {
            "topics": analysis_results.get("topics", input.initial_topics),
            "quality_criteria": {
                "min_length": 1000,
                "quality_threshold": 7.0,
                "required_sections": ["abstract", "introduction", "conclusion", "references"],
                "technical_depth_required": True,
                "safety_considerations_required": True,
                "practical_applications_required": True,
            },
            "search_attributes": {
                "domain_id": input.domain_id,
                "domain_name": input.domain_name,
                "owner_id": input.owner_id,
                "topics": analysis_results.get("topics", []),
                "target_audience": input.target_audience,
            },
            "bootstrap_prompt": analysis_results.get("bootstrap_prompt", ""),
            "research_steps": analysis_results.get("research_steps", []),
            "target_audience": input.target_audience,
        }
