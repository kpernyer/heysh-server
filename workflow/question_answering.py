"""Question answering workflow.

Orchestrates the Q&A pipeline:
1. Search relevant documents in Weaviate (vector search)
2. Find related documents in Neo4j (graph traversal)
3. Generate answer using LLM with context
4. Calculate confidence score
5. Flag for human review if confidence is low
6. Store answer in database
"""

from datetime import timedelta
from typing import Any

import structlog
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activity.llm import calculate_confidence_activity, generate_answer_activity
    from activity.search import (
        find_related_documents_activity,
        search_documents_activity,
    )
    from activity.supabase import (
        create_review_task_activity,
        store_question_activity,
        update_question_activity,
    )

logger = structlog.get_logger()


@workflow.defn
class QuestionAnsweringWorkflow:
    """Answer user questions using knowledge base."""

    @workflow.run
    async def run(
        self,
        question_id: str,
        question: str,
        domain_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Process a question and generate an answer.

        Args:
            question_id: UUID of the question
            question: The question text
            domain_id: UUID of the domain
            user_id: UUID of the user asking

        Returns:
            Dictionary with answer and metadata

        """
        workflow.logger.info(
            "Starting question answering",
            question_id=question_id,
            domain_id=domain_id,
        )

        try:
            # Step 1: Store question in database
            await workflow.execute_activity(
                store_question_activity,
                args=[
                    {
                        "id": question_id,
                        "question_text": question,
                        "domain_id": domain_id,
                        "asker_id": user_id,
                        "status": "processing",
                    }
                ],
                start_to_close_timeout=timedelta(minutes=1),
            )

            # Step 2: Vector search in Weaviate
            search_results = await workflow.execute_activity(
                search_documents_activity,
                args=[question, domain_id, 10],  # Top 10 results
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=workflow.RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3,
                ),
            )

            # Step 3: Graph traversal in Neo4j to find related documents
            doc_ids = [doc["document_id"] for doc in search_results]
            related_docs = await workflow.execute_activity(
                find_related_documents_activity,
                args=[doc_ids],
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=workflow.RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=20),
                    maximum_attempts=3,
                ),
            )

            # Combine search results with related documents
            all_context = search_results + related_docs

            # Step 4: Generate answer using LLM
            answer_data = await workflow.execute_activity(
                generate_answer_activity,
                args=[
                    {
                        "question": question,
                        "context": all_context,
                        "domain_id": domain_id,
                    }
                ],
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=workflow.RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=3,
                ),
            )

            # Step 5: Calculate confidence score
            confidence_score = await workflow.execute_activity(
                calculate_confidence_activity,
                args=[
                    {
                        "question": question,
                        "answer": answer_data["answer"],
                        "context": all_context,
                    }
                ],
                start_to_close_timeout=timedelta(minutes=1),
            )

            # Step 6: Determine if human review is needed
            needs_review = confidence_score < 0.7
            status = "needs_review" if needs_review else "answered"

            # Step 7: Update question with answer
            await workflow.execute_activity(
                update_question_activity,
                args=[
                    question_id,
                    {
                        "ai_answer": answer_data["answer"],
                        "confidence_score": confidence_score,
                        "needs_review": needs_review,
                        "status": status,
                        "answered_at": workflow.now().isoformat(),
                        "source_documents": doc_ids,
                    },
                ],
                start_to_close_timeout=timedelta(minutes=1),
            )

            # Step 8: Create review task if needed
            review_task_id = None
            if needs_review:
                review_task = await workflow.execute_activity(
                    create_review_task_activity,
                    args=[
                        {
                            "question_id": question_id,
                            "domain_id": domain_id,
                            "reason": "Low confidence score",
                            "priority": "high" if confidence_score < 0.5 else "medium",
                        }
                    ],
                    start_to_close_timeout=timedelta(minutes=1),
                )
                review_task_id = review_task["id"]

            workflow.logger.info(
                "Question answering completed",
                question_id=question_id,
                confidence=confidence_score,
                needs_review=needs_review,
            )

            return {
                "status": "completed",
                "question_id": question_id,
                "answer": answer_data["answer"],
                "confidence_score": confidence_score,
                "needs_review": needs_review,
                "review_task_id": review_task_id,
                "source_count": len(doc_ids),
            }

        except Exception as e:
            workflow.logger.error(
                "Question answering failed",
                question_id=question_id,
                error=str(e),
            )

            # Update question status to failed
            await workflow.execute_activity(
                update_question_activity,
                args=[
                    question_id,
                    {
                        "status": "failed",
                        "error_message": str(e),
                        "failed_at": workflow.now().isoformat(),
                    },
                ],
                start_to_close_timeout=timedelta(minutes=1),
            )

            raise
