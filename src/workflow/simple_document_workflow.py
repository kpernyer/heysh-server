"""Simple Document Analysis Workflow without structlog dependencies."""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from temporalio import workflow
from temporalio.common import RetryPolicy

# Allow imports from activities
with workflow.unsafe.imports_passed_through():
    from activity.ai import assess_document_relevance_activity


class DocumentStatus(Enum):
    """Document processing status."""

    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    INDEXED = "indexed"


@dataclass
class DocumentInput:
    """Input for document analysis workflow."""

    document_id: str
    file_path: str
    domain_id: str
    contributor_id: str


@dataclass
class DocumentResult:
    """Result of document analysis workflow."""

    status: DocumentStatus
    relevance_score: float | None = None
    analysis_summary: str | None = None
    decision: str | None = None
    error: str | None = None


@workflow.defn(name="SimpleDocumentWorkflow")
class SimpleDocumentWorkflow:
    """Simple document analysis workflow with HITL controller review."""

    def __init__(self):
        """Initialize workflow state."""
        self.status = DocumentStatus.UPLOADED
        self.relevance_score: float | None = None
        self.analysis_summary: str | None = None
        self.controller_decision: str | None = None
        self.review_completed = False

    @workflow.run
    async def run(self, input_data: DocumentInput) -> DocumentResult:
        """Main workflow execution."""
        workflow.logger.info(f"Starting document analysis for {input_data.document_id}")

        try:
            # Step 1: Analyze document relevance
            self.status = DocumentStatus.ANALYZING
            workflow.logger.info("Analyzing document relevance...")

            # Set up domain criteria
            domain_criteria = {
                "topics": ["technology", "AI", "machine learning", "innovation"],
                "min_length": 500,
                "quality_threshold": 7.0,
            }
            ai_config = {
                "model": "gpt-4o",
                "temperature": 0.1,
            }

            # Execute AI analysis
            analysis_result = await workflow.execute_activity(
                assess_document_relevance_activity,
                args=[
                    input_data.document_id,
                    input_data.file_path,
                    domain_criteria,
                    ai_config,
                ],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(max_attempts=3),
            )

            self.relevance_score = analysis_result["relevance_score"]
            self.analysis_summary = analysis_result["analysis_summary"]

            workflow.logger.info(f"Analysis completed. Score: {self.relevance_score}")

            # Step 2: Decision logic
            if self.relevance_score >= 8.0:
                # Auto-approve high quality documents
                self.status = DocumentStatus.APPROVED
                self.controller_decision = "auto_approve"
                workflow.logger.info("Document auto-approved due to high quality")

            elif self.relevance_score >= 7.0:
                # Needs human review
                self.status = DocumentStatus.PENDING_REVIEW
                workflow.logger.info("Document needs human review")

                # Wait for controller decision (with timeout)
                try:
                    await workflow.wait_condition(
                        lambda: self.review_completed, timeout=timedelta(days=7)
                    )

                    if self.controller_decision == "approve":
                        self.status = DocumentStatus.APPROVED
                        workflow.logger.info("Document approved by controller")
                    else:
                        self.status = DocumentStatus.REJECTED
                        workflow.logger.info("Document rejected by controller")

                except TimeoutError:
                    self.status = DocumentStatus.REJECTED
                    self.controller_decision = "timeout"
                    workflow.logger.warning("Controller review timed out")

            else:
                # Reject low quality documents
                self.status = DocumentStatus.REJECTED
                self.controller_decision = "auto_reject"
                workflow.logger.info("Document auto-rejected due to low quality")

            # Step 3: Update Search Attributes for visibility
            await workflow.upsert_search_attributes(
                {
                    "Assignee": ["controller"],
                    "Queue": ["document-review"],
                    "Status": [self.status.value],
                    "Priority": ["normal"],
                    "DocumentId": [input_data.document_id],
                    "DomainId": [input_data.domain_id],
                    "ContributorId": [input_data.contributor_id],
                    "RelevanceScore": [self.relevance_score or 0.0],
                }
            )

            workflow.logger.info(f"Workflow completed with status: {self.status.value}")

            return DocumentResult(
                status=self.status,
                relevance_score=self.relevance_score,
                analysis_summary=self.analysis_summary,
                decision=self.controller_decision,
            )

        except Exception as e:
            self.status = DocumentStatus.REJECTED
            error_msg = f"Workflow failed: {e!s}"
            workflow.logger.error(error_msg)

            return DocumentResult(
                status=self.status,
                error=error_msg,
            )

    @workflow.signal
    async def submit_controller_decision(self, decision: str):
        """Signal for controller to submit decision."""
        workflow.logger.info(f"Controller submitted decision: {decision}")
        self.controller_decision = decision
        self.review_completed = True

    @workflow.query
    def get_status(self) -> DocumentResult:
        """Query current workflow status."""
        return DocumentResult(
            status=self.status,
            relevance_score=self.relevance_score,
            analysis_summary=self.analysis_summary,
            decision=self.controller_decision,
        )
