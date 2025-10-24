"""Document processing workflow.

Orchestrates the entire document processing pipeline:
1. Download document from Supabase Storage
2. Extract text content
3. Generate embeddings
4. Index in Weaviate
5. Update Neo4j knowledge graph
6. Update document metadata in Supabase
"""

from datetime import timedelta
from typing import Any

import structlog
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activity.document import (
        download_document_activity,
        extract_text_activity,
        generate_embeddings_activity,
    )
    from activity.search import index_weaviate_activity, update_neo4j_graph_activity
    from activity.supabase import update_document_metadata_activity

logger = structlog.get_logger()


@workflow.defn
class DocumentProcessingWorkflow:
    """Process uploaded documents end-to-end."""

    @workflow.run
    async def run(
        self, document_id: str, domain_id: str, file_path: str
    ) -> dict[str, Any]:
        """Process a document through the full pipeline.

        Args:
            document_id: UUID of the document in Supabase
            domain_id: UUID of the domain the document belongs to
            file_path: Path to the file in Supabase Storage

        Returns:
            Dictionary with processing results and metadata

        """
        workflow.logger.info(
            f"Starting document processing: document_id={document_id}, domain_id={domain_id}"
        )

        try:
            # Step 1: Download document from Supabase Storage
            file_data = await workflow.execute_activity(
                download_document_activity,
                args=[file_path],
                task_queue="storage-queue",  # Route to storage queue
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3,
                ),
            )

            # Step 2: Extract text content
            extracted_data = await workflow.execute_activity(
                extract_text_activity,
                args=[file_data],
                task_queue="ai-processing-queue",  # Route to AI queue
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=3,
                ),
            )

            # Step 3: Generate embeddings for text chunks
            embeddings = await workflow.execute_activity(
                generate_embeddings_activity,
                args=[extracted_data["text"], extracted_data.get("chunks", [])],
                task_queue="ai-processing-queue",  # Route to AI queue
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=3,
                ),
            )

            # Step 4: Index in Weaviate for vector search
            weaviate_result = await workflow.execute_activity(
                index_weaviate_activity,
                args=[
                    {
                        "document_id": document_id,
                        "domain_id": domain_id,
                        "text": extracted_data["text"],
                        "chunks": extracted_data.get("chunks", []),
                        "embeddings": embeddings,
                        "metadata": extracted_data.get("metadata", {}),
                    }
                ],
                task_queue="storage-queue",  # Route to storage queue
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=5,
                ),
            )

            # Step 5: Update Neo4j knowledge graph
            neo4j_result = await workflow.execute_activity(
                update_neo4j_graph_activity,
                args=[
                    {
                        "document_id": document_id,
                        "domain_id": domain_id,
                        "entities": extracted_data.get("entities", []),
                        "topics": extracted_data.get("topics", []),
                        "metadata": extracted_data.get("metadata", {}),
                    }
                ],
                task_queue="storage-queue",  # Route to storage queue
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=5,
                ),
            )

            # Step 6: Update document metadata in Supabase
            await workflow.execute_activity(
                update_document_metadata_activity,
                args=[
                    document_id,
                    {
                        "processing_status": "completed",
                        "processed_at": workflow.now().isoformat(),
                        "text_length": len(extracted_data["text"]),
                        "chunk_count": len(extracted_data.get("chunks", [])),
                        "topics": extracted_data.get("topics", []),
                        "entities": extracted_data.get("entities", []),
                    },
                ],
                task_queue="storage-queue",  # Route to storage queue
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=5,
                ),
            )

            workflow.logger.info(
                "Document processing completed successfully",
                document_id=document_id,
            )

            return {
                "status": "completed",
                "document_id": document_id,
                "domain_id": domain_id,
                "text_length": len(extracted_data["text"]),
                "chunk_count": len(extracted_data.get("chunks", [])),
                "weaviate_indexed": weaviate_result.get("success", False),
                "neo4j_updated": neo4j_result.get("success", False),
            }

        except Exception as e:
            workflow.logger.error(
                f"Document processing failed: document_id={document_id}, error={e!s}"
            )

            # Update document status to failed
            await workflow.execute_activity(
                update_document_metadata_activity,
                args=[
                    document_id,
                    {
                        "processing_status": "failed",
                        "error_message": str(e),
                        "failed_at": workflow.now().isoformat(),
                    },
                ],
                task_queue="storage-queue",  # Route to storage queue
                start_to_close_timeout=timedelta(minutes=1),
            )

            raise
