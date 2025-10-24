"""Integration tests for Document Contribution Workflow."""

import asyncio
import logging
import uuid
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

import pytest
from temporalio.client import Client
from temporalio.worker import Worker

from workflow.document_contribution_workflow import (
    DocumentContributionInput,
    DocumentContributionWorkflow,
    DocumentProcessingResult,
    DocumentStatus,
)


@dataclass
class TestConfig:
    """Test configuration."""

    temporal_address: str = "localhost:7233"
    namespace: str = "default"
    task_queue: str = "test-queue"
    use_mock_ai: bool = True


@pytest.fixture
async def temporal_client():
    """Create Temporal client for testing."""
    client = await Client.connect("localhost:7233", namespace="default")
    yield client
    # Cleanup if needed


@pytest.fixture
async def test_worker(temporal_client):
    """Create a test worker."""
    from activity.document_contribution_activities import (
        assess_document_relevance,
        get_next_controller,
        # ... other activities
        notify_stakeholders,
    )

    worker = Worker(
        temporal_client,
        task_queue="test-queue",
        workflows=[DocumentContributionWorkflow],
        activities=[
            assess_document_relevance,
            notify_stakeholders,
            get_next_controller,
        ],
    )

    async with worker:
        yield worker


class TestDocumentContributionWorkflow:
    """Test cases for Document Contribution Workflow."""

    @pytest.mark.asyncio
    async def test_auto_approve_high_score_document(self, temporal_client, test_worker):
        """Test that documents with high relevance scores are auto-approved."""
        # Prepare test input
        workflow_input = DocumentContributionInput(
            document_id=str(uuid.uuid4()),
            document_path="/test/document.pdf",
            contributor_id="contributor-123",
            domain_id="domain-456",
            domain_criteria={"topic": "AI", "quality": "high"},
            relevance_threshold=7.0,
            auto_approve_threshold=8.5,
            use_ai_controller=False,
        )

        # Start workflow
        handle = await temporal_client.start_workflow(
            DocumentContributionWorkflow.run,
            workflow_input,
            id=f"test-workflow-{uuid.uuid4()}",
            task_queue="test-queue",
        )

        # Wait for result
        result: DocumentProcessingResult = await handle.result()

        # Assertions
        assert result.success is True
        assert result.status == DocumentStatus.INDEXED
        assert result.relevance_score >= 8.5
        assert result.knowledge_base_url is not None

    @pytest.mark.asyncio
    async def test_auto_reject_low_score_document(self, temporal_client, test_worker):
        """Test that documents with low relevance scores are auto-rejected."""
        # Set environment to return low scores
        import os

        os.environ["DEFAULT_RELEVANCE_SCORE"] = "3.0"

        workflow_input = DocumentContributionInput(
            document_id=str(uuid.uuid4()),
            document_path="/test/low-quality.pdf",
            contributor_id="contributor-123",
            domain_id="domain-456",
            domain_criteria={"topic": "AI", "quality": "high"},
            relevance_threshold=7.0,
            auto_reject_threshold=4.0,
        )

        handle = await temporal_client.start_workflow(
            DocumentContributionWorkflow.run,
            workflow_input,
            id=f"test-workflow-{uuid.uuid4()}",
            task_queue="test-queue",
        )

        result = await handle.result()

        assert result.success is True
        assert result.status == DocumentStatus.REJECTED
        assert result.relevance_score < 4.0
        assert result.rejection_reason is not None

    @pytest.mark.asyncio
    async def test_human_controller_review_flow(self, temporal_client, test_worker):
        """Test human controller review process with signals."""
        # Set score for human review range
        import os

        os.environ["DEFAULT_RELEVANCE_SCORE"] = "6.0"

        workflow_input = DocumentContributionInput(
            document_id=str(uuid.uuid4()),
            document_path="/test/medium-quality.pdf",
            contributor_id="contributor-123",
            domain_id="domain-456",
            domain_criteria={"topic": "AI"},
            relevance_threshold=7.0,
            auto_approve_threshold=8.5,
            use_ai_controller=False,
            controller_pool=["controller-1", "controller-2"],
        )

        handle = await temporal_client.start_workflow(
            DocumentContributionWorkflow.run,
            workflow_input,
            id=f"test-workflow-{uuid.uuid4()}",
            task_queue="test-queue",
        )

        # Give workflow time to reach review state
        await asyncio.sleep(2)

        # Query workflow status
        status = await handle.query(DocumentContributionWorkflow.get_status)
        assert status["status"] == DocumentStatus.UNDER_REVIEW.value

        # Send review signal (approve)
        await handle.signal(
            DocumentContributionWorkflow.submit_review,
            {
                "approved": True,
                "feedback": "Good document",
                "tags": ["AI", "Testing"],
            },
        )

        # Wait for workflow to complete
        result = await handle.result()

        assert result.success is True
        assert result.status == DocumentStatus.INDEXED
        assert result.controller_id is not None

    @pytest.mark.asyncio
    async def test_ai_controller_review(self, temporal_client, test_worker):
        """Test AI controller review process."""
        import os

        os.environ["DEFAULT_RELEVANCE_SCORE"] = "6.0"

        workflow_input = DocumentContributionInput(
            document_id=str(uuid.uuid4()),
            document_path="/test/ai-review.pdf",
            contributor_id="contributor-123",
            domain_id="domain-456",
            domain_criteria={"topic": "AI"},
            relevance_threshold=7.0,
            use_ai_controller=True,  # Use AI controller
        )

        handle = await temporal_client.start_workflow(
            DocumentContributionWorkflow.run,
            workflow_input,
            id=f"test-workflow-{uuid.uuid4()}",
            task_queue="test-queue",
        )

        result = await handle.result()

        assert result.success is True
        assert result.controller_id == "ai-controller"
        # Result depends on mock AI response

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, temporal_client, test_worker):
        """Test workflow error handling."""
        # Input that will cause an error (invalid domain_id)
        workflow_input = DocumentContributionInput(
            document_id=str(uuid.uuid4()),
            document_path="/test/error.pdf",
            contributor_id="contributor-123",
            domain_id="",  # Invalid
            domain_criteria={},
        )

        handle = await temporal_client.start_workflow(
            DocumentContributionWorkflow.run,
            workflow_input,
            id=f"test-workflow-{uuid.uuid4()}",
            task_queue="test-queue",
        )

        result = await handle.result()

        assert result.success is False
        assert result.error is not None


class TestMultiQueueIntegration:
    """Test multi-queue worker setup."""

    @pytest.mark.asyncio
    async def test_activity_routing_to_correct_queue(self, temporal_client):
        """Test that activities are routed to correct queues."""
        # This would require setting up workers on different queues
        # and verifying activities execute on the right workers

        # Start workers for each queue
        Worker(
            temporal_client,
            task_queue="ai-processing-queue",
            activities=[],  # AI activities
        )

        Worker(
            temporal_client,
            task_queue="storage-queue",
            activities=[],  # Storage activities
        )

        Worker(
            temporal_client,
            task_queue="general-queue",
            workflows=[DocumentContributionWorkflow],
            activities=[],  # General activities
        )

        # Test workflow execution across queues
        # ... implementation

    @pytest.mark.asyncio
    async def test_queue_failure_resilience(self, temporal_client):
        """Test system resilience when one queue is down."""
        # Test that workflow handles activity failures gracefully
        pass


@pytest.mark.asyncio
async def test_end_to_end_document_flow():
    """End-to-end test of complete document processing flow."""
    client = await Client.connect("localhost:7233")

    # 1. Upload document
    document_id = str(uuid.uuid4())

    # 2. Start workflow
    handle = await client.start_workflow(
        DocumentContributionWorkflow.run,
        DocumentContributionInput(
            document_id=document_id,
            document_path=f"/documents/{document_id}.pdf",
            contributor_id="test-contributor",
            domain_id="test-domain",
            domain_criteria={"topic": "testing"},
        ),
        id=f"e2e-test-{document_id}",
        task_queue="general-queue",
    )

    # 3. Wait for completion
    result = await handle.result()

    # 4. Verify results
    assert result.success is True

    # 5. Verify side effects (indexing, notifications, etc.)
    # Check Weaviate
    # Check Neo4j
    # Check notifications

    logger.info(f"✅ E2E Test passed: Document {document_id} processed successfully")
