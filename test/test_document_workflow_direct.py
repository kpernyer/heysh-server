#!/usr/bin/env python3
"""Direct execution test for DocumentProcessingWorkflow.
Tests multiple task queues working together.
"""

import asyncio
import os
import sys
import uuid
from typing import Any

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

# Import the workflow
from workflow.document_processing import DocumentProcessingWorkflow

# Configure logging
structlog.configure(processors=[structlog.dev.ConsoleRenderer(colors=True)])
logger = structlog.get_logger()


# =============================================================================
# MOCK IMPLEMENTATIONS - Simple versions to run without full infrastructure
# =============================================================================


class MockSupabaseClient:
    """Mock Supabase client for testing."""

    class Storage:
        def __init__(self):
            self.buckets = {}

        def from_(self, bucket_name: str):
            return self

        def download(self, file_path: str) -> bytes:
            """Return mock file content."""
            logger.info(f"📥 Mock downloading: {file_path}")
            # Return fake PDF content
            return (
                b"PDF-1.4\nMock document content for testing\nThis is a test document."
            )

    def __init__(self):
        self.storage = self.Storage()


async def mock_extract_text_from_file(file_data: bytes) -> dict[str, Any]:
    """Mock text extraction."""
    logger.info("📄 Mock extracting text from document")

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


async def mock_generate_text_embeddings(chunks: list[str]) -> list[list[float]]:
    """Mock embedding generation."""
    logger.info(f"🧮 Mock generating embeddings for {len(chunks)} chunks")

    # Return fake embeddings (1536 dimensions like OpenAI)
    import random

    embeddings = []
    for _chunk in chunks:
        # Generate random vector
        embedding = [random.random() for _ in range(1536)]
        embeddings.append(embedding)

    return embeddings


# Mock module structure
class MockSupabaseModule:
    @staticmethod
    def get_supabase_client():
        return MockSupabaseClient()


class MockTextExtractionModule:
    extract_text_from_file = staticmethod(mock_extract_text_from_file)


class MockEmbeddingsModule:
    generate_text_embeddings = staticmethod(mock_generate_text_embeddings)


class MockLLMClient:
    """Mock LLM client for testing."""

    async def generate(self, *args, **kwargs):
        return {"answer": "Mock LLM response"}


class MockLLMModule:
    @staticmethod
    def get_llm_client():
        return MockLLMClient()


# Mock OpenAI module to avoid import errors
class MockOpenAI:
    class AsyncOpenAI:
        pass


# Mock YAML module
class MockYAML:
    @staticmethod
    def safe_load(*args, **kwargs):
        return {}


# Mock prompts module
class MockPromptsModule:
    @staticmethod
    def load_prompt(name):
        return "Mock prompt template"

    @staticmethod
    def render_prompt(template, **kwargs):
        return "Rendered mock prompt"


# =============================================================================
# IMPORT ACTIVITIES AND WORKFLOWS
# =============================================================================

# First, inject our mocks into sys.modules before importing
sys.modules["yaml"] = MockYAML
sys.modules["openai"] = MockOpenAI
sys.modules["src.app.clients.llm"] = MockLLMModule
sys.modules["src.app.clients.supabase"] = MockSupabaseModule
sys.modules["src.app.utils.text_extraction"] = MockTextExtractionModule
sys.modules["src.app.utils.embeddings"] = MockEmbeddingsModule
sys.modules["src.app.utils.prompts"] = MockPromptsModule

# Now import the activities
# Import or create mock versions of search activities
from activity.document import (
    download_document_activity,
    extract_text_activity,
    generate_embeddings_activity,
)


@activity.defn
async def index_weaviate_activity(data: dict[str, Any]) -> dict[str, bool]:
    """Mock Weaviate indexing."""
    logger.info(
        "🔍 Mock indexing in Weaviate",
        document_id=data.get("document_id"),
        chunks=len(data.get("chunks", [])),
    )
    await asyncio.sleep(0.5)  # Simulate work
    return {"success": True}


@activity.defn
async def update_neo4j_graph_activity(data: dict[str, Any]) -> dict[str, bool]:
    """Mock Neo4j graph update."""
    logger.info(
        "🕸️ Mock updating Neo4j graph",
        document_id=data.get("document_id"),
        entities=len(data.get("entities", [])),
    )
    await asyncio.sleep(0.3)  # Simulate work
    return {"success": True}


@activity.defn
async def update_document_metadata_activity(
    document_id: str, metadata: dict[str, Any]
) -> None:
    """Mock Supabase metadata update."""
    logger.info(
        "📊 Mock updating document metadata",
        document_id=document_id,
        status=metadata.get("processing_status"),
    )
    await asyncio.sleep(0.2)  # Simulate work


# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================


async def run_test():
    """Execute the DocumentProcessingWorkflow test."""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 DOCUMENT PROCESSING WORKFLOW - DIRECT EXECUTION TEST")
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
        logger.info("✨ WORKFLOW EXECUTION SUCCESSFUL!")
        logger.info("=" * 80)

        # Check Temporal Web UI
        logger.info("\n📌 View workflow execution details:")
        logger.info(
            f"   👉 Open http://localhost:8088/namespaces/default/workflows/{handle.id}"
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
    logger.info("Starting DocumentProcessingWorkflow test...")
    asyncio.run(run_test())
