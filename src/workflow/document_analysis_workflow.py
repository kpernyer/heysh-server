"""Document Analysis Workflow with Human-in-the-Loop.

This workflow implements the full vision:
1. Document upload to Supabase/MinIO
2. FörAnalys with LLM (later Ollama)
3. If relevant → Index in Weaviate + Neo4j
4. Send to Controller inbox for HITL review
5. Controller decision → Publish or Archive
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any

import structlog
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activity.ai import assess_document_relevance_activity
    from activity.document import (
        download_document_activity,
        extract_text_activity,
        generate_embeddings_activity,
    )
    from activity.search import index_weaviate_activity, update_neo4j_graph_activity
    from activity.supabase import update_document_metadata_activity

logger = structlog.get_logger()


class DocumentStatus(Enum):
    """Document processing status."""

    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class DocumentAnalysisInput:
    """Input for document analysis workflow."""

    document_id: str
    domain_id: str
    file_path: str
    contributor_id: str
    domain_criteria: dict[str, Any]
    auto_approve_threshold: float = 8.0
    relevance_threshold: float = 7.0


@workflow.defn(name="DocumentAnalysisWorkflow")
class DocumentAnalysisWorkflow:
    """Document analysis workflow with HITL controller review."""

    def __init__(self):
        """Initialize workflow state."""
        self.status = DocumentStatus.UPLOADED
        self.analysis_completed = False
        self.controller_decision = None
        self.relevance_score = None
        self.analysis_result = None

    @workflow.run
    async def run(self, input: DocumentAnalysisInput) -> dict[str, Any]:
        """Execute document analysis workflow."""
        workflow.logger.info(f"Starting document analysis: {input.document_id}")

        self.status = DocumentStatus.ANALYZING

        try:
            # Step 1: Download and extract document
            file_data = await workflow.execute_activity(
                download_document_activity,
                args=[input.file_path],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            extracted_data = await workflow.execute_activity(
                extract_text_activity,
                args=[file_data],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            # Step 2: FörAnalys - AI relevance assessment
            analysis_result = await workflow.execute_activity(
                assess_document_relevance_activity,
                args=[
                    input.document_id,
                    input.file_path,
                    input.domain_criteria,
                    {
                        "model": "gpt-4o",  # Later: Ollama model
                        "temperature": 0.1,
                        "max_tokens": 1000,
                    },
                ],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            self.analysis_result = analysis_result
            self.relevance_score = analysis_result.get("relevance_score", 0.0)

            # Step 3: Decision logic
            if self.relevance_score >= input.auto_approve_threshold:
                # Auto-approve: High quality document
                workflow.logger.info(
                    f"Auto-approving document: score={self.relevance_score}"
                )
                return await self._publish_document(
                    input, extracted_data, analysis_result
                )

            elif self.relevance_score >= input.relevance_threshold:
                # Send to Controller inbox for HITL review
                workflow.logger.info(
                    f"Sending to Controller inbox: score={self.relevance_score}"
                )
                return await self._send_to_controller_inbox(input, analysis_result)

            else:
                # Reject: Too low relevance
                workflow.logger.info(
                    f"Rejecting document: score={self.relevance_score}"
                )
                return await self._reject_document(input, analysis_result)

        except Exception as e:
            workflow.logger.error(f"Document analysis failed: {e}")
            self.status = DocumentStatus.ARCHIVED
            raise

    async def _publish_document(
        self, input: DocumentAnalysisInput, extracted_data: dict, analysis_result: dict
    ) -> dict[str, Any]:
        """Publish document directly (auto-approve)."""
        self.status = DocumentStatus.PUBLISHED

        # Generate embeddings
        embeddings = await workflow.execute_activity(
            generate_embeddings_activity,
            args=[extracted_data["text"], extracted_data.get("chunks", [])],
            task_queue="ai-processing-queue",
        )

        # Index in Weaviate
        weaviate_result = await workflow.execute_activity(
            index_weaviate_activity,
            args=[
                {
                    "document_id": input.document_id,
                    "domain_id": input.domain_id,
                    "text": extracted_data["text"],
                    "chunks": extracted_data.get("chunks", []),
                    "embeddings": embeddings,
                    "metadata": extracted_data.get("metadata", {}),
                }
            ],
            task_queue="storage-queue",
        )

        # Update Neo4j
        neo4j_result = await workflow.execute_activity(
            update_neo4j_graph_activity,
            args=[
                {
                    "document_id": input.document_id,
                    "domain_id": input.domain_id,
                    "entities": extracted_data.get("entities", []),
                    "topics": extracted_data.get("topics", []),
                    "metadata": extracted_data.get("metadata", {}),
                }
            ],
            task_queue="storage-queue",
        )

        # Update document status
        await workflow.execute_activity(
            update_document_metadata_activity,
            args=[
                input.document_id,
                {
                    "processing_status": "published",
                    "relevance_score": self.relevance_score,
                    "auto_approved": True,
                    "published_at": workflow.now().isoformat(),
                },
            ],
            task_queue="storage-queue",
        )

        return {
            "status": "published",
            "document_id": input.document_id,
            "relevance_score": self.relevance_score,
            "auto_approved": True,
            "weaviate_indexed": weaviate_result.get("success", False),
            "neo4j_updated": neo4j_result.get("success", False),
        }

    async def _send_to_controller_inbox(
        self, input: DocumentAnalysisInput, analysis_result: dict
    ) -> dict[str, Any]:
        """Send document to Controller inbox for HITL review."""
        self.status = DocumentStatus.PENDING_REVIEW

        # Upsert Search Attributes for Controller inbox
        await workflow.upsert_search_attributes(
            {
                "Assignee": "controller",  # All controllers can see this
                "Queue": "document-review",
                "Status": "pending",
                "Priority": "normal",
                "DueAt": (workflow.now() + timedelta(days=7)).isoformat(),
                "Tenant": input.domain_id,
                "DocumentId": input.document_id,
                "ContributorId": input.contributor_id,
                "RelevanceScore": self.relevance_score,
            }
        )

        # Update document status
        await workflow.execute_activity(
            update_document_metadata_activity,
            args=[
                input.document_id,
                {
                    "processing_status": "pending_review",
                    "relevance_score": self.relevance_score,
                    "controller_inbox": True,
                    "assigned_at": workflow.now().isoformat(),
                },
            ],
            task_queue="storage-queue",
        )

        # Wait for Controller decision (up to 7 days)
        await workflow.wait_condition(
            lambda: self.controller_decision is not None, timeout=timedelta(days=7)
        )

        # Apply Controller decision
        if self.controller_decision == "approve":
            return await self._publish_document(input, {}, analysis_result)
        else:
            return await self._reject_document(input, analysis_result)

    async def _reject_document(
        self, input: DocumentAnalysisInput, analysis_result: dict
    ) -> dict[str, Any]:
        """Reject document."""
        self.status = DocumentStatus.REJECTED

        await workflow.execute_activity(
            update_document_metadata_activity,
            args=[
                input.document_id,
                {
                    "processing_status": "rejected",
                    "relevance_score": self.relevance_score,
                    "rejection_reason": analysis_result.get(
                        "rejection_reason", "Low relevance"
                    ),
                    "rejected_at": workflow.now().isoformat(),
                },
            ],
            task_queue="storage-queue",
        )

        return {
            "status": "rejected",
            "document_id": input.document_id,
            "relevance_score": self.relevance_score,
            "reason": analysis_result.get("rejection_reason", "Low relevance"),
        }

    @workflow.signal
    async def controller_decision(
        self, decision: str, controller_id: str, feedback: str = ""
    ):
        """Controller submits decision."""
        workflow.logger.info(f"Controller decision: {decision} by {controller_id}")
        self.controller_decision = decision
        self.controller_id = controller_id
        self.analysis_completed = True

    @workflow.query
    def get_status(self) -> dict[str, Any]:
        """Get current workflow status."""
        return {
            "status": self.status.value,
            "relevance_score": self.relevance_score,
            "analysis_completed": self.analysis_completed,
            "controller_decision": self.controller_decision,
            "controller_id": self.controller_id,
        }
