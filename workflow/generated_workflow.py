"""Generated Temporal workflow from YAML definition.

This demonstrates how to dynamically generate workflows from YAML.
"""

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities
with workflow.unsafe.imports_passed_through():
    from activity.ai_agent_activities import (
        archive_rejected_document,
        execute_ai_agent_activity,
        extract_document_content,
        notify_user,
        publish_to_knowledge_base,
    )


@workflow.defn(name="document-review-workflow")
class DocumentReviewWorkflow:
    """Generated from document-review.workflow.yaml.

    AI-powered document review with human approval workflow.
    """

    def __init__(self):
        """Initialize the document review workflow."""
        self.review_completed = False
        self.review_result = None

    @workflow.run
    async def run(self, document_id: str, user_id: str) -> dict[str, Any]:
        """Execute the document review workflow."""
        workflow.logger.info(f"Starting document review workflow for {document_id}")

        # Step 1: Extract content
        try:
            extract_result = await workflow.execute_activity(
                extract_document_content,
                args=[document_id, False],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    backoff_coefficient=2.0,
                    maximum_interval=timedelta(seconds=30),
                ),
            )

            extracted_text = extract_result["extracted_text"]
            _metadata = extract_result["metadata"]

        except Exception as e:
            workflow.logger.error(f"Failed to extract content: {e}")
            await self._notify_failure(user_id, f"Extraction failed: {e}")
            return {"success": False, "error": str(e)}

        # Step 2: Summarize content
        try:
            # Call AI agent to summarize
            summarize_result = await workflow.execute_activity(
                execute_ai_agent_activity,
                args=[
                    {
                        "model": "claude-3-5-sonnet",
                        "system_prompt": "You are an expert document analyzer.",
                        "temperature": 0.3,
                        "max_tokens": 2000,
                    },
                    "summarize_content",
                    {"extracted_text": extracted_text, "max_length": 500},
                ],
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )

            summary = summarize_result["summary"]
            _key_points = summarize_result.get("key_points", [])

        except Exception as e:
            workflow.logger.error(f"Failed to summarize: {e}")
            await self._notify_failure(user_id, f"Summarization failed: {e}")
            return {"success": False, "error": str(e)}

        # Step 3: Assess quality
        try:
            quality_result = await workflow.execute_activity(
                execute_ai_agent_activity,
                args=[
                    {
                        "model": "gpt-4",
                        "system_prompt": "Assess document quality and compliance.",
                        "temperature": 0.1,
                    },
                    "assess_document_quality",
                    {
                        "document_text": extracted_text,
                        "summary": summary,
                        "domain_policies": {},
                    },
                ],
                start_to_close_timeout=timedelta(minutes=2),
            )

            quality_score = quality_result["quality_score"]
            compliance_status = quality_result["compliance_status"]
            _issues = quality_result.get("issues", [])

        except Exception as e:
            workflow.logger.error(f"Failed quality assessment: {e}")
            await self._notify_failure(user_id, f"Quality check failed: {e}")
            return {"success": False, "error": str(e)}

        # Decision logic based on quality
        if quality_score >= 7 and compliance_status == "compliant":
            # Auto-approve high quality documents
            workflow.logger.info(f"Auto-approving document with score {quality_score}")
            result = await self._publish_document(document_id, [])
            await self._notify_success(user_id, "approved", result)
            return {
                "success": True,
                "status": "approved",
                "quality_score": quality_score,
            }

        elif quality_score < 4 or compliance_status == "non-compliant":
            # Auto-reject low quality documents
            workflow.logger.info(f"Auto-rejecting document with score {quality_score}")
            await self._archive_document(document_id, "Low quality or non-compliant")
            await self._notify_failure(
                user_id, f"Rejected: quality score {quality_score}, {compliance_status}"
            )
            return {
                "success": True,
                "status": "rejected",
                "quality_score": quality_score,
            }

        else:
            # Requires human review
            workflow.logger.info(
                f"Document requires human review (score: {quality_score})"
            )

            # Wait for human review (via signal)
            await workflow.wait_condition(
                lambda: self.review_completed, timeout=timedelta(days=7)
            )

            if self.review_result and self.review_result.get("approved"):
                result = await self._publish_document(
                    document_id, self.review_result.get("tags", [])
                )
                await self._notify_success(user_id, "approved_after_review", result)
                return {
                    "success": True,
                    "status": "approved",
                    "quality_score": quality_score,
                    "human_reviewed": True,
                }
            else:
                await self._archive_document(
                    document_id,
                    self.review_result.get("feedback", "Rejected by reviewer"),
                )
                await self._notify_failure(user_id, "Rejected by human reviewer")
                return {
                    "success": True,
                    "status": "rejected",
                    "quality_score": quality_score,
                    "human_reviewed": True,
                }

    @workflow.signal
    async def submit_review(self, review_data: dict[str, Any]):
        """Signal to submit human review result."""
        self.review_result = review_data
        self.review_completed = True

    @workflow.query
    def get_status(self) -> dict[str, Any]:
        """Query current workflow status."""
        return {
            "review_completed": self.review_completed,
            "review_result": self.review_result,
        }

    async def _publish_document(self, document_id: str, tags: list) -> dict[str, Any]:
        """Publish document to knowledge base."""
        return await workflow.execute_activity(
            publish_to_knowledge_base,
            args=[document_id, tags],
            start_to_close_timeout=timedelta(minutes=2),
        )

    async def _archive_document(self, document_id: str, reason: str):
        """Archive rejected document."""
        await workflow.execute_activity(
            archive_rejected_document,
            args=[document_id, reason],
            start_to_close_timeout=timedelta(minutes=1),
        )

    async def _notify_success(self, user_id: str, status: str, result: dict[str, Any]):
        """Notify user of success."""
        await workflow.execute_activity(
            notify_user,
            args=[
                user_id,
                status,
                f"Document published: {result.get('published_url')}",
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )

    async def _notify_failure(self, user_id: str, feedback: str):
        """Notify user of failure."""
        await workflow.execute_activity(
            notify_user,
            args=[user_id, "failed", feedback],
            start_to_close_timeout=timedelta(seconds=30),
        )
