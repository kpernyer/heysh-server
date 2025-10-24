"""Document Contribution Workflow with multi-queue architecture.

Handles document uploads, AI relevance testing, human review, and knowledge base updates.
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

# Import activities
with workflow.unsafe.imports_passed_through():
    from activity.ai_agent_activities import execute_ai_agent_activity
    from activity.document_contribution_activities import (
        archive_rejected_document,
        assess_document_relevance,
        generate_summary_for_notification,
        get_next_controller,
        index_to_weaviate,
        notify_stakeholders,
        update_neo4j_graph,
    )


# Global Workflow Configuration
class WorkflowConfig:
    """Global configuration for workflow constants and defaults."""

    # AI Model Configuration
    DEFAULT_AI_MODEL = "claude-3-haiku-20240307"  # Latest Haiku model
    CONTROLLER_AI_MODEL = "claude-3-haiku-20240307"
    SUMMARY_AI_MODEL = "claude-3-haiku-20240307"

    # AI Parameters
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_MAX_TOKENS = 2000
    CONTROLLER_MAX_TOKENS = 1000
    SUMMARY_MAX_TOKENS = 500

    # Scoring Thresholds
    DEFAULT_RELEVANCE_THRESHOLD = 7.0
    DEFAULT_AUTO_APPROVE_THRESHOLD = 8.5
    DEFAULT_AUTO_REJECT_THRESHOLD = 4.0

    # Timeout Configuration
    AI_ACTIVITY_TIMEOUT = timedelta(minutes=5)
    STORAGE_ACTIVITY_TIMEOUT = timedelta(minutes=2)
    GENERAL_ACTIVITY_TIMEOUT = timedelta(minutes=1)
    HUMAN_REVIEW_TIMEOUT = timedelta(days=7)

    # Retry Configuration
    DEFAULT_MAX_ATTEMPTS = 3
    DEFAULT_INITIAL_INTERVAL = timedelta(seconds=2)
    DEFAULT_BACKOFF_COEFFICIENT = 2.0
    DEFAULT_MAX_INTERVAL = timedelta(seconds=30)

    # Queue Names
    AI_PROCESSING_QUEUE = "ai-processing-queue"
    STORAGE_QUEUE = "storage-queue"
    GENERAL_QUEUE = "general-queue"

    # System Prompts
    CONTROLLER_SYSTEM_PROMPT = """You are a document controller reviewing for quality and relevance.
    Evaluate documents based on provided criteria and make approval decisions.
    Be strict but fair in your assessments."""

    RELEVANCE_SYSTEM_PROMPT = """You are an expert document analyzer assessing relevance to domain criteria.
    Score documents from 0-10 based on how well they match the specified domain requirements."""

    SUMMARY_SYSTEM_PROMPT = """You are a concise document summarizer.
    Create brief, informative summaries suitable for notifications."""


class DocumentStatus(Enum):
    """Document processing status enumeration."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    INDEXED = "indexed"


@dataclass
class DocumentContributionInput:
    """Input parameters for document contribution workflow."""

    document_id: str
    document_path: str
    contributor_id: str
    domain_id: str
    domain_criteria: dict[str, Any]
    relevance_threshold: float = WorkflowConfig.DEFAULT_RELEVANCE_THRESHOLD
    auto_approve_threshold: float = WorkflowConfig.DEFAULT_AUTO_APPROVE_THRESHOLD
    auto_reject_threshold: float = WorkflowConfig.DEFAULT_AUTO_REJECT_THRESHOLD
    use_ai_controller: bool = False
    controller_pool: list[str] = None  # List of controller IDs for round-robin
    ai_model_override: str = None  # Override default AI model if needed


@dataclass
class DocumentProcessingResult:
    """Result of document processing workflow."""

    success: bool
    status: DocumentStatus
    document_id: str
    relevance_score: float | None = None
    controller_id: str | None = None
    rejection_reason: str | None = None
    knowledge_base_url: str | None = None
    summary: str | None = None
    topics: list[str] | None = None
    error: str | None = None


@workflow.defn(name="DocumentContributionWorkflow")
class DocumentContributionWorkflow:
    """Main workflow for document contributions with human-in-the-loop.

    Flow:
    1. Document upload from contributor
    2. AI relevance assessment
    3. Controller review (human or AI) if needed
    4. Knowledge base indexing if approved
    5. Notifications to stakeholders
    """

    def __init__(self):
        """Initialize the document state."""
        self.status = DocumentStatus.UPLOADED
        self.review_completed = False
        self.review_result = None
        self.relevance_score = None
        self.controller_id = None
        self.config = WorkflowConfig()

    @workflow.run
    async def run(self, input: DocumentContributionInput) -> DocumentProcessingResult:
        """Execute the document contribution workflow."""
        workflow.logger.info(
            "Starting document contribution workflow",
            document_id=input.document_id,
            domain_id=input.domain_id,
            contributor_id=input.contributor_id,
        )

        self.status = DocumentStatus.PROCESSING

        try:
            # Step 1: Assess document relevance against domain criteria
            relevance_result = await workflow.execute_activity(
                assess_document_relevance,
                args=[
                    input.document_id,
                    input.document_path,
                    input.domain_criteria,
                    {
                        "model": input.ai_model_override
                        or self.config.DEFAULT_AI_MODEL,
                        "system_prompt": self.config.RELEVANCE_SYSTEM_PROMPT,
                        "temperature": self.config.DEFAULT_TEMPERATURE,
                        "max_tokens": self.config.DEFAULT_MAX_TOKENS,
                    },
                ],
                start_to_close_timeout=self.config.AI_ACTIVITY_TIMEOUT,
                retry_policy=RetryPolicy(
                    maximum_attempts=self.config.DEFAULT_MAX_ATTEMPTS,
                    initial_interval=self.config.DEFAULT_INITIAL_INTERVAL,
                    backoff_coefficient=self.config.DEFAULT_BACKOFF_COEFFICIENT,
                    maximum_interval=self.config.DEFAULT_MAX_INTERVAL,
                ),
                task_queue=self.config.AI_PROCESSING_QUEUE,
            )

            self.relevance_score = relevance_result["relevance_score"]
            topics = relevance_result.get("topics", [])
            entities = relevance_result.get("entities", [])

            workflow.logger.info(
                "Relevance assessment complete",
                score=self.relevance_score,
                topics=topics,
            )

            # Step 2: Decision logic based on relevance score
            if self.relevance_score >= input.auto_approve_threshold:
                # Auto-approve high relevance documents
                workflow.logger.info(
                    f"Auto-approving document with score {self.relevance_score}"
                )
                approved = True

            elif self.relevance_score < input.auto_reject_threshold:
                # Auto-reject very low relevance documents
                workflow.logger.info(
                    f"Auto-rejecting document with low score {self.relevance_score}"
                )
                approved = False
                self.review_result = {
                    "approved": False,
                    "rejection_reason": f"Relevance score {self.relevance_score} below threshold",
                }

            elif self.relevance_score < input.relevance_threshold:
                # Send to controller for review
                workflow.logger.info(
                    f"Document needs review (score: {self.relevance_score})"
                )

                if input.use_ai_controller:
                    # Use AI as controller
                    approved = await self._ai_controller_review(
                        input.document_id,
                        input.document_path,
                        self.relevance_score,
                        input.domain_criteria,
                        input.ai_model_override,
                    )
                else:
                    # Round-robin to human controller
                    approved = await self._human_controller_review(
                        input.document_id,
                        input.document_path,
                        self.relevance_score,
                        input.controller_pool,
                        input.contributor_id,
                    )
            else:
                # Mid-range score - default approve
                approved = True

            # Step 3: Handle approval/rejection
            if approved:
                self.status = DocumentStatus.APPROVED

                # Index to knowledge bases
                kb_result = await self._index_to_knowledge_bases(
                    input.document_id,
                    input.document_path,
                    topics,
                    entities,
                    input.domain_id,
                )

                # Generate summary for notification
                summary = await self._generate_summary(
                    input.document_id,
                    input.document_path,
                    input.ai_model_override,
                )

                # Notify stakeholders
                await self._notify_stakeholders(
                    input.contributor_id,
                    input.domain_id,
                    "approved",
                    summary,
                    kb_result.get("knowledge_base_url"),
                )

                self.status = DocumentStatus.INDEXED

                return DocumentProcessingResult(
                    success=True,
                    status=self.status,
                    document_id=input.document_id,
                    relevance_score=self.relevance_score,
                    controller_id=self.controller_id,
                    knowledge_base_url=kb_result.get("knowledge_base_url"),
                    summary=summary,
                    topics=topics,
                )
            else:
                # Document rejected
                self.status = DocumentStatus.REJECTED

                # Archive rejected document
                await workflow.execute_activity(
                    archive_rejected_document,
                    args=[
                        input.document_id,
                        self.review_result.get(
                            "rejection_reason", "Did not meet criteria"
                        ),
                    ],
                    start_to_close_timeout=self.config.STORAGE_ACTIVITY_TIMEOUT,
                    task_queue=self.config.STORAGE_QUEUE,
                )

                # Notify contributor
                await self._notify_stakeholders(
                    input.contributor_id,
                    input.domain_id,
                    "rejected",
                    self.review_result.get("rejection_reason"),
                    None,
                )

                return DocumentProcessingResult(
                    success=True,
                    status=self.status,
                    document_id=input.document_id,
                    relevance_score=self.relevance_score,
                    controller_id=self.controller_id,
                    rejection_reason=self.review_result.get("rejection_reason"),
                )

        except ActivityError as e:
            workflow.logger.error(f"Activity failed: {e}")
            return DocumentProcessingResult(
                success=False,
                status=self.status,
                document_id=input.document_id,
                error=str(e),
            )
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {e}")
            return DocumentProcessingResult(
                success=False,
                status=self.status,
                document_id=input.document_id,
                error=str(e),
            )

    async def _ai_controller_review(
        self,
        document_id: str,
        document_path: str,
        relevance_score: float,
        domain_criteria: dict[str, Any],
        ai_model_override: str | None = None,
    ) -> bool:
        """Use AI agent as controller for review."""
        review_result = await workflow.execute_activity(
            execute_ai_agent_activity,
            args=[
                {
                    "model": ai_model_override or self.config.CONTROLLER_AI_MODEL,
                    "system_prompt": self.config.CONTROLLER_SYSTEM_PROMPT,
                    "temperature": self.config.DEFAULT_TEMPERATURE,
                    "max_tokens": self.config.CONTROLLER_MAX_TOKENS,
                },
                "controller_review",
                {
                    "document_id": document_id,
                    "document_path": document_path,
                    "relevance_score": relevance_score,
                    "domain_criteria": domain_criteria,
                },
            ],
            start_to_close_timeout=self.config.AI_ACTIVITY_TIMEOUT,
            task_queue=self.config.AI_PROCESSING_QUEUE,
        )

        self.controller_id = "ai-controller"
        self.review_result = review_result
        return review_result.get("approved", False)

    async def _human_controller_review(
        self,
        document_id: str,
        document_path: str,
        relevance_score: float,
        controller_pool: list[str],
        contributor_id: str,
    ) -> bool:
        """Assign to human controller for review."""
        self.status = DocumentStatus.UNDER_REVIEW

        # Get next controller (round-robin)
        controller = await workflow.execute_activity(
            get_next_controller,
            args=[controller_pool, contributor_id],
            start_to_close_timeout=self.config.GENERAL_ACTIVITY_TIMEOUT,
            task_queue=self.config.GENERAL_QUEUE,
        )

        self.controller_id = controller["controller_id"]

        workflow.logger.info(f"Assigned to controller {self.controller_id} for review")

        # Wait for human review signal (with timeout)
        try:
            await workflow.wait_condition(
                lambda: self.review_completed,
                timeout=self.config.HUMAN_REVIEW_TIMEOUT,
            )
        except TimeoutError:
            workflow.logger.warning("Review timeout - auto-rejecting")
            self.review_result = {
                "approved": False,
                "rejection_reason": "Review timeout",
            }
            return False

        return self.review_result.get("approved", False)

    async def _index_to_knowledge_bases(
        self,
        document_id: str,
        document_path: str,
        topics: list[str],
        entities: list[str],
        domain_id: str,
    ) -> dict[str, Any]:
        """Index document to Weaviate and Neo4j."""
        # Parallel indexing to both knowledge bases
        weaviate_task = workflow.execute_activity(
            index_to_weaviate,
            args=[document_id, document_path, topics, entities, domain_id],
            start_to_close_timeout=self.config.AI_ACTIVITY_TIMEOUT,
            task_queue=self.config.STORAGE_QUEUE,
        )

        neo4j_task = workflow.execute_activity(
            update_neo4j_graph,
            args=[document_id, topics, entities, domain_id],
            start_to_close_timeout=self.config.AI_ACTIVITY_TIMEOUT,
            task_queue=self.config.STORAGE_QUEUE,
        )

        # Wait for both to complete
        weaviate_result = await weaviate_task
        neo4j_result = await neo4j_task

        return {
            "knowledge_base_url": weaviate_result.get("url"),
            "graph_updated": neo4j_result.get("success"),
        }

    async def _generate_summary(
        self,
        document_id: str,
        document_path: str,
        ai_model_override: str | None = None,
    ) -> str:
        """Generate summary for notifications."""
        summary_result = await workflow.execute_activity(
            generate_summary_for_notification,
            args=[
                document_id,
                document_path,
                {
                    "model": ai_model_override or self.config.SUMMARY_AI_MODEL,
                    "system_prompt": self.config.SUMMARY_SYSTEM_PROMPT,
                    "temperature": self.config.DEFAULT_TEMPERATURE,
                    "max_tokens": self.config.SUMMARY_MAX_TOKENS,
                },
            ],
            start_to_close_timeout=self.config.AI_ACTIVITY_TIMEOUT,
            task_queue=self.config.AI_PROCESSING_QUEUE,
        )

        return summary_result.get("summary", "")

    async def _notify_stakeholders(
        self,
        contributor_id: str,
        domain_id: str,
        status: str,
        message: str,
        knowledge_base_url: str | None,
    ):
        """Notify contributor and domain owner."""
        await workflow.execute_activity(
            notify_stakeholders,
            args=[
                {
                    "contributor_id": contributor_id,
                    "domain_id": domain_id,
                    "status": status,
                    "message": message,
                    "knowledge_base_url": knowledge_base_url,
                }
            ],
            start_to_close_timeout=self.config.GENERAL_ACTIVITY_TIMEOUT,
            task_queue=self.config.GENERAL_QUEUE,
        )

    @workflow.signal
    async def submit_review(self, review_data: dict[str, Any]):
        """Signal to submit human controller review."""
        self.review_result = review_data
        self.review_completed = True
        workflow.logger.info(
            "Review submitted",
            approved=review_data.get("approved"),
            controller_id=self.controller_id,
        )

    @workflow.query
    def get_status(self) -> dict[str, Any]:
        """Query current workflow status."""
        return {
            "status": self.status.value,
            "relevance_score": self.relevance_score,
            "controller_id": self.controller_id,
            "review_completed": self.review_completed,
            "review_result": self.review_result,
        }
