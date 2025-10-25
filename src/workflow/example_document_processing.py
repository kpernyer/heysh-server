"""Example: Document Processing Workflow using Models.

This demonstrates how Temporal workflows use the data models to:
1. Receive document for processing
2. Download from Supabase Storage
3. Process and generate embeddings
4. Update Supabase with results
5. Record execution stats
"""

from datetime import datetime

import structlog
from temporalio import workflow

from src.service.models import DocumentModel, WorkflowModel

logger = structlog.get_logger()


@workflow.defn
class DocumentProcessingWorkflow:
    """Example workflow that processes a document.

    Steps:
    1. Update document status to 'processing'
    2. Download document from storage
    3. Extract text and generate embeddings
    4. Index in Weaviate and Neo4j (via activities)
    5. Update document status to 'indexed'
    6. Record workflow execution
    """

    @workflow.run
    async def run(
        self,
        document_id: str,
        domain_id: str,
        file_path: str,
    ) -> dict[str, any]:
        """Main workflow execution.

        Args:
            document_id: Document UUID
            domain_id: Domain UUID
            file_path: Path in Supabase Storage

        Returns:
            Result dict with processing outcome

        """
        workflow_id = workflow.info().workflow_id
        start_time = datetime.utcnow()

        try:
            logger.info(
                "Document processing workflow started",
                workflow_id=workflow_id,
                document_id=document_id,
            )

            # Step 1: Update document status to processing
            await DocumentModel.update_status(document_id, "processing")

            # Step 2: Call activity to download and process
            # (In real implementation, these would be Temporal activities)
            result = await self._process_document(
                document_id=document_id,
                domain_id=domain_id,
                file_path=file_path,
            )

            # Step 3: Record successful processing
            await DocumentModel.record_processing_success(
                document_id=document_id,
                weaviate_id=result.get("weaviate_id"),
                neo4j_updated=result.get("neo4j_updated", False),
                embeddings_count=result.get("embeddings_count"),
            )

            # Step 4: Record workflow execution
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await WorkflowModel.record_execution(
                workflow_id=workflow_id,
                execution_data={
                    "status": "completed",
                    "duration_ms": duration_ms,
                    "result": result,
                    "started_at": start_time.isoformat(),
                },
            )

            logger.info(
                "Document processing completed",
                workflow_id=workflow_id,
                document_id=document_id,
                duration_ms=duration_ms,
            )

            return {
                "document_id": document_id,
                "status": "success",
                "result": result,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(
                "Document processing failed",
                workflow_id=workflow_id,
                document_id=document_id,
                error=str(e),
            )

            # Record failure
            await DocumentModel.record_processing_error(
                document_id=document_id,
                error_message=str(e),
            )

            # Record workflow execution failure
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await WorkflowModel.record_execution(
                workflow_id=workflow_id,
                execution_data={
                    "status": "failed",
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "started_at": start_time.isoformat(),
                },
            )

            raise

    async def _process_document(
        self,
        document_id: str,
        domain_id: str,
        file_path: str,
    ) -> dict[str, any]:
        """Process document (simplified for example).

        In real implementation, these would be @activity.defn functions.

        Returns:
            Processing result with IDs and metadata

        """
        logger.info(
            "Processing document",
            document_id=document_id,
            file_path=file_path,
        )

        # Simulate processing steps
        # In real implementation:
        # 1. Download from Supabase Storage
        # 2. Extract text
        # 3. Generate embeddings via LLM
        # 4. Index in Weaviate (get weaviate_id)
        # 5. Update Neo4j graph

        return {
            "weaviate_id": f"weaviate-{document_id}",
            "neo4j_updated": True,
            "embeddings_count": 100,
            "text_length": 5000,
        }


# ==================== Usage Example ====================


async def example_usage():
    """Example of how to use the models in your workflows.

    This shows the integration pattern:
    1. Models handle Supabase operations
    2. Workflows orchestrate the process
    3. APIs expose the endpoints
    """
    # Create a document
    document = await DocumentModel.create_document(
        name="architecture.pdf",
        domain_id="domain-123",
        file_path="domain-123/docs/architecture.pdf",
        file_type="application/pdf",
        size_bytes=1024000,
    )
    logger.info(f"Document created: {document['id']}")

    # Create a workflow
    workflow = await WorkflowModel.create_workflow(
        name="Document Processing",
        domain_id="domain-123",
        yaml_definition={
            "version": "1.0",
            "steps": [
                {"step": "download", "onSuccess": "extract"},
                {"step": "extract", "onSuccess": "embed"},
                {"step": "embed", "onSuccess": "index"},
            ],
        },
    )
    logger.info(f"Workflow created: {workflow['id']}")

    # Record a workflow execution
    execution_id = await WorkflowModel.record_execution(
        workflow_id=workflow["id"],
        execution_data={
            "status": "completed",
            "duration_ms": 5000,
            "result": {"documents_processed": 1},
        },
    )
    logger.info(f"Execution recorded: {execution_id}")

    # Get workflow stats
    stats = await WorkflowModel.get_execution_stats(workflow["id"])
    logger.info(f"Workflow stats: {stats}")

    # Update document status
    updated_doc = await DocumentModel.update_status(
        document["id"],
        "indexed",
        {"weaviate_id": "vec-123", "neo4j_updated": True},
    )
    logger.info(f"Document updated: {updated_doc['status']}")
