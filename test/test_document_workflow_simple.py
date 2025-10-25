#!/usr/bin/env python3
"""Simplified test for DocumentProcessingWorkflow - minimal dependencies."""

import asyncio
import logging
import os
import sys
import uuid
from datetime import timedelta
from typing import Any

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

# Configure logging
structlog.configure(processors=[structlog.dev.ConsoleRenderer(colors=True)])
logger = structlog.get_logger()


# =============================================================================
# MOCK ACTIVITIES - Direct implementations without imports
# =============================================================================


@activity.defn
async def download_document_activity(file_path: str) -> bytes:
    """Mock document download."""
    activity.logger.info(f"📥 Mock downloading: {file_path}")
    return b"PDF-1.4\nMock document content for testing\nThis is a test document."


@activity.defn
async def extract_text_activity(file_data: bytes) -> dict[str, Any]:
    """Mock text extraction."""
    activity.logger.info("📄 Mock extracting text from document")
    return {
        "text": "This is the extracted text from the document. It contains important information about AI and machine learning.",
        "chunks": [
            "This is the extracted text from the document.",
            "It contains important information about AI and machine learning.",
            "Chunk 3: Additional content for testing.",
            "Chunk 4: More test data.",
            "Chunk 5: Final chunk of test content.",
        ],
        "metadata": {"title": "Test Document", "author": "Test Author", "pages": 5},
        "entities": ["AI", "machine learning", "testing"],
        "topics": ["artificial intelligence", "software testing"],
    }


@activity.defn
async def generate_embeddings_activity(
    full_text: str, chunks: list[str]
) -> dict[str, list[float]]:
    """Mock embedding generation."""
    activity.logger.info(f"🧮 Mock generating embeddings for {len(chunks)} chunks")
    import random

    embeddings = [[random.random() for _ in range(1536)] for _ in chunks]
    return {"embeddings": embeddings}


@activity.defn
async def index_weaviate_activity(data: dict[str, Any]) -> dict[str, bool]:
    """Mock Weaviate indexing."""
    activity.logger.info(
        "🔍 Mock indexing in Weaviate",
        document_id=data.get("document_id"),
        chunks=len(data.get("chunks", [])),
    )
    await asyncio.sleep(0.5)
    return {"success": True}


@activity.defn
async def update_neo4j_graph_activity(data: dict[str, Any]) -> dict[str, bool]:
    """Mock Neo4j graph update."""
    activity.logger.info(
        "🕸️ Mock updating Neo4j graph",
        document_id=data.get("document_id"),
        entities=len(data.get("entities", [])),
    )
    await asyncio.sleep(0.3)
    return {"success": True}


@activity.defn
async def update_document_metadata_activity(
    document_id: str, metadata: dict[str, Any]
) -> None:
    """Mock Supabase metadata update."""
    activity.logger.info(
        "📊 Mock updating document metadata",
        document_id=document_id,
        status=metadata.get("processing_status"),
    )
    await asyncio.sleep(0.2)


# =============================================================================
# WORKFLOW DEFINITION - Simplified version
# =============================================================================


@workflow.defn
class DocumentProcessingWorkflow:
    """Process uploaded documents end-to-end."""

    @workflow.run
    async def run(
        self, document_id: str, domain_id: str, file_path: str
    ) -> dict[str, Any]:
        """Process a document through the full pipeline."""
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
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=1),
            )

            raise


# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================


async def run_test():
    """Execute the DocumentProcessingWorkflow test."""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 DOCUMENT PROCESSING WORKFLOW - MULTI-QUEUE TEST")
    logger.info("=" * 80)

    try:
        # Step 1: Connect to Temporal
        logger.info("\n1️⃣  Connecting to Temporal...")
        client = await Client.connect("localhost:7233", namespace="default")
        logger.info("   ✅ Connected to Temporal at localhost:7233")

        # Step 2: Create workers for each queue
        logger.info("\n2️⃣  Starting workers on multiple queues...")

        # General queue worker (runs workflows)
        general_worker = Worker(
            client,
            task_queue="general-queue",
            workflows=[DocumentProcessingWorkflow],
            activities=[],  # Workflows only
        )

        # AI processing queue worker (AI-related activities)
        ai_worker = Worker(
            client,
            task_queue="ai-processing-queue",
            activities=[
                extract_text_activity,
                generate_embeddings_activity,
            ],
        )

        # Storage queue worker (storage-related activities)
        storage_worker = Worker(
            client,
            task_queue="storage-queue",
            activities=[
                download_document_activity,
                index_weaviate_activity,
                update_neo4j_graph_activity,
                update_document_metadata_activity,
            ],
        )

        logger.info("   ✅ Worker started on general-queue (workflows)")
        logger.info("   ✅ Worker started on ai-processing-queue (AI activities)")
        logger.info("   ✅ Worker started on storage-queue (storage activities)")

        # Step 3: Start all workers
        logger.info("\n3️⃣  Starting worker tasks...")
        worker_tasks = [
            asyncio.create_task(general_worker.run()),
            asyncio.create_task(ai_worker.run()),
            asyncio.create_task(storage_worker.run()),
        ]

        # Give workers time to start
        await asyncio.sleep(2)

        # Step 4: Execute the workflow
        logger.info("\n4️⃣  Triggering DocumentProcessingWorkflow...")

        document_id = str(uuid.uuid4())
        domain_id = str(uuid.uuid4())
        file_path = f"documents/{document_id}/test-document.pdf"

        logger.info(f"   📄 Document ID: {document_id}")
        logger.info(f"   🏢 Domain ID: {domain_id}")
        logger.info(f"   📁 File path: {file_path}")

        # Start the workflow
        handle = await client.start_workflow(
            DocumentProcessingWorkflow.run,
            args=[document_id, domain_id, file_path],
            id=f"doc-processing-test-{document_id}",
            task_queue="general-queue",  # Workflows run on general queue
        )

        logger.info(f"\n   ⏳ Workflow started with ID: {handle.id}")
        logger.info("   ⏳ Waiting for completion...\n")

        # Show progress
        logger.info("   📡 Activities executing on different queues:")

        # Wait for workflow to complete
        result = await handle.result()

        # Step 5: Display results
        logger.info("\n5️⃣  Workflow completed successfully! ✅")
        logger.info("\n" + "=" * 80)
        logger.info("📊 RESULTS:")
        logger.info("=" * 80)
        logger.info(f"   Status: {result['status']}")
        logger.info(f"   Document ID: {result['document_id']}")
        logger.info(f"   Domain ID: {result['domain_id']}")
        logger.info(f"   Text length: {result['text_length']} characters")
        logger.info(f"   Chunks processed: {result['chunk_count']}")
        logger.info(f"   Weaviate indexed: {result['weaviate_indexed']}")
        logger.info(f"   Neo4j updated: {result['neo4j_updated']}")

        logger.info("\n" + "=" * 80)
        logger.info("✨ MULTI-QUEUE WORKFLOW EXECUTION SUCCESSFUL!")
        logger.info("=" * 80)

        logger.info("\n📊 QUEUE DISTRIBUTION:")
        logger.info("   - general-queue: Workflow orchestration")
        logger.info("   - ai-processing-queue: Text extraction, embeddings")
        logger.info("   - storage-queue: Document download, DB updates")

        # Check Temporal Web UI
        logger.info("\n📌 View workflow execution details:")
        logger.info(
            f"   👉 Open http://localhost:8088/namespaces/default/workflows/{handle.id}"
        )
        logger.info(
            "   You'll see activities distributed across the different task queues!"
        )

        # Cancel workers
        logger.info("\n🛑 Shutting down workers...")
        for task in worker_tasks:
            task.cancel()

        await asyncio.gather(*worker_tasks, return_exceptions=True)

        logger.info("✅ Test completed successfully!")

    except Exception as e:
        logger.info(f"\n❌ Error during test execution: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Starting simplified DocumentProcessingWorkflow test...")
    asyncio.run(run_test())
