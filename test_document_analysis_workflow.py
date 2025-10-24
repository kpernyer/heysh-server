#!/usr/bin/env python3
"""Test script for Document Analysis Workflow with HITL Controller Review.

This demonstrates the full workflow:
1. Document upload to Supabase/MinIO
2. FörAnalys with LLM
3. If relevant → Index in Weaviate + Neo4j
4. If needs review → Send to Controller inbox
5. Controller decision → Publish or Archive
"""

import asyncio
import logging
import os
import sys
import uuid

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from temporalio.client import Client
from temporalio.worker import Worker

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Configure structlog
structlog.configure(processors=[structlog.dev.ConsoleRenderer(colors=True)])
structlog_logger = structlog.get_logger()


async def test_document_analysis_workflow():
    """Test the complete document analysis workflow."""
    logger.info("=" * 80)
    logger.info("🚀 DOCUMENT ANALYSIS WORKFLOW - HITL CONTROLLER REVIEW")
    logger.info("=" * 80)

    try:
        # Step 1: Connect to Temporal
        logger.info("\n1️⃣  Connecting to Temporal...")
        client = await Client.connect("localhost:7233", namespace="default")
        logger.info("   ✅ Connected to Temporal at localhost:7233")

        # Step 2: Start workers
        logger.info("\n2️⃣  Starting workers...")

        # Import workflows and activities
        from activity.ai import assess_document_relevance_activity
        from activity.document import (
            download_document_activity,
            extract_text_activity,
            generate_embeddings_activity,
        )
        from activity.search import index_weaviate_activity, update_neo4j_graph_activity
        from activity.supabase import update_document_metadata_activity
        from workflow.document_analysis_workflow import (
            DocumentAnalysisWorkflow,
        )

        # Start workers for different queues
        workers = [
            Worker(
                client,
                task_queue="general-queue",
                workflows=[DocumentAnalysisWorkflow],
                activities=[],
            ),
            Worker(
                client,
                task_queue="ai-processing-queue",
                activities=[
                    extract_text_activity,
                    generate_embeddings_activity,
                    assess_document_relevance_activity,
                ],
            ),
            Worker(
                client,
                task_queue="storage-queue",
                activities=[
                    download_document_activity,
                    index_weaviate_activity,
                    update_neo4j_graph_activity,
                    update_document_metadata_activity,
                ],
            ),
        ]

        # Start all workers
        worker_tasks = [asyncio.create_task(worker.run()) for worker in workers]
        logger.info("   ✅ All workers started")

        # Step 3: Test scenarios
        logger.info("\n3️⃣  Testing different document scenarios...")

        # Scenario 1: High quality document (auto-approve)
        logger.info("\n📄 Scenario 1: High quality document (auto-approve)")
        await test_high_quality_document(client)

        # Scenario 2: Medium quality document (needs review)
        logger.info("\n📄 Scenario 2: Medium quality document (needs review)")
        await test_medium_quality_document(client)

        # Scenario 3: Low quality document (reject)
        logger.info("\n📄 Scenario 3: Low quality document (reject)")
        await test_low_quality_document(client)

        # Step 4: Test Controller inbox
        logger.info("\n4️⃣  Testing Controller inbox functionality...")
        await test_controller_inbox(client)

        logger.info("\n✅ All tests completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    finally:
        # Cleanup
        for task in worker_tasks:
            task.cancel()


async def test_high_quality_document(client: Client):
    """Test high quality document that gets auto-approved."""
    document_id = str(uuid.uuid4())
    domain_id = str(uuid.uuid4())

    input_data = DocumentAnalysisInput(
        document_id=document_id,
        domain_id=domain_id,
        file_path=f"documents/{document_id}/high-quality-doc.pdf",
        contributor_id="contributor-123",
        domain_criteria={
            "topics": ["technology", "AI", "machine learning"],
            "min_length": 1000,
            "quality_threshold": 8.0,
        },
        auto_approve_threshold=8.0,
        relevance_threshold=7.0,
    )

    # Start workflow
    handle = await client.start_workflow(
        "DocumentAnalysisWorkflow",
        args=[input_data],
        id=f"analysis-{document_id}",
        task_queue="general-queue",
    )

    logger.info(f"   📄 Started workflow: {handle.id}")
    logger.info(f"   📄 Document ID: {document_id}")

    # Wait for completion
    result = await handle.result()

    logger.info(f"   ✅ High quality document result: {result['status']}")
    logger.info(f"   📊 Relevance score: {result.get('relevance_score', 'N/A')}")
    logger.info(f"   🤖 Auto-approved: {result.get('auto_approved', False)}")


async def test_medium_quality_document(client: Client):
    """Test medium quality document that needs Controller review."""
    document_id = str(uuid.uuid4())
    domain_id = str(uuid.uuid4())

    input_data = DocumentAnalysisInput(
        document_id=document_id,
        domain_id=domain_id,
        file_path=f"documents/{document_id}/medium-quality-doc.pdf",
        contributor_id="contributor-456",
        domain_criteria={
            "topics": ["technology", "AI", "machine learning"],
            "min_length": 1000,
            "quality_threshold": 8.0,
        },
        auto_approve_threshold=8.0,
        relevance_threshold=7.0,
    )

    # Start workflow
    handle = await client.start_workflow(
        "DocumentAnalysisWorkflow",
        args=[input_data],
        id=f"analysis-{document_id}",
        task_queue="general-queue",
    )

    logger.info(f"   📄 Started workflow: {handle.id}")
    logger.info(f"   📄 Document ID: {document_id}")

    # Simulate Controller decision after a short delay
    await asyncio.sleep(2)

    # Submit Controller decision
    await handle.signal(
        "controller_decision",
        "approve",  # Controller approves
        "controller-789",
        "Good content, approved for publication",
    )

    # Wait for completion
    result = await handle.result()

    logger.info(f"   ✅ Medium quality document result: {result['status']}")
    logger.info(f"   📊 Relevance score: {result.get('relevance_score', 'N/A')}")
    logger.info(
        f"   👤 Controller decision: {result.get('controller_decision', 'N/A')}"
    )


async def test_low_quality_document(client: Client):
    """Test low quality document that gets rejected."""
    document_id = str(uuid.uuid4())
    domain_id = str(uuid.uuid4())

    input_data = DocumentAnalysisInput(
        document_id=document_id,
        domain_id=domain_id,
        file_path=f"documents/{document_id}/low-quality-doc.pdf",
        contributor_id="contributor-789",
        domain_criteria={
            "topics": ["technology", "AI", "machine learning"],
            "min_length": 1000,
            "quality_threshold": 8.0,
        },
        auto_approve_threshold=8.0,
        relevance_threshold=7.0,
    )

    # Start workflow
    handle = await client.start_workflow(
        "DocumentAnalysisWorkflow",
        args=[input_data],
        id=f"analysis-{document_id}",
        task_queue="general-queue",
    )

    logger.info(f"   📄 Started workflow: {handle.id}")
    logger.info(f"   📄 Document ID: {document_id}")

    # Wait for completion
    result = await handle.result()

    logger.info(f"   ✅ Low quality document result: {result['status']}")
    logger.info(f"   📊 Relevance score: {result.get('relevance_score', 'N/A')}")
    logger.info(f"   ❌ Rejection reason: {result.get('reason', 'N/A')}")


async def test_controller_inbox(client: Client):
    """Test Controller inbox functionality using Search Attributes."""
    logger.info("   📥 Testing Controller inbox...")

    # Query workflows assigned to controllers
    workflows = await client.list_workflows(
        query='Assignee = "controller" AND Status = "pending" AND Queue = "document-review"'
    )

    inbox_count = 0
    async for workflow in workflows:
        inbox_count += 1
        logger.info(f"   📋 Inbox item: {workflow.id}")
        logger.info(
            f"      Document ID: {workflow.search_attributes.get('DocumentId')}"
        )
        logger.info(
            f"      Contributor: {workflow.search_attributes.get('ContributorId')}"
        )
        logger.info(f"      Priority: {workflow.search_attributes.get('Priority')}")
        logger.info(f"      Due: {workflow.search_attributes.get('DueAt')}")

    logger.info(f"   📊 Total items in Controller inbox: {inbox_count}")


async def main():
    """Main test execution."""
    await test_document_analysis_workflow()


if __name__ == "__main__":
    asyncio.run(main())
