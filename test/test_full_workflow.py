#!/usr/bin/env python3
"""Test a full Temporal workflow execution with real documents."""

import asyncio
import logging
import uuid
from datetime import timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_full_workflow():
    """Test a full Temporal workflow with real document processing."""
    logger.info("=" * 80)
    logger.info("🚀 FULL TEMPORAL WORKFLOW TEST")
    logger.info("=" * 80)

    try:
        # Step 1: Connect to Temporal
        logger.info("\n1️⃣  Connecting to Temporal...")
        from temporalio.client import Client

        client = await Client.connect("localhost:7233", namespace="default")
        logger.info("   ✅ Connected to Temporal")

        # Step 2: Start a real workflow
        logger.info("\n2️⃣  Starting real Temporal workflow...")
        from workflow.simple_document_workflow import (
            DocumentInput,
            SimpleDocumentWorkflow,
        )

        # Create test document input
        document_id = str(uuid.uuid4())
        workflow_input = DocumentInput(
            document_id=document_id,
            file_path="test-documents/balloon-article.pdf",
            domain_id="balloon-domain-123",
            contributor_id="contributor-456",
        )

        # Start the workflow
        handle = await client.start_workflow(
            SimpleDocumentWorkflow.run,
            args=[workflow_input],
            id=f"document-analysis-{document_id}",
            task_queue="hey-sh-workflows",
            # Set initial Search Attributes
            search_attributes={
                "Assignee": ["unassigned"],
                "Queue": ["document-analysis"],
                "Status": ["uploaded"],
                "Priority": ["normal"],
                "DocumentId": [document_id],
                "DomainId": [workflow_input.domain_id],
                "ContributorId": [workflow_input.contributor_id],
            },
        )

        logger.info(f"   ✅ Workflow started: {handle.id}")
        logger.info(f"   📋 Document ID: {document_id}")

        # Step 3: Wait for workflow to complete (with timeout)
        logger.info("\n3️⃣  Waiting for workflow to complete...")
        try:
            result = await handle.result(timeout=timedelta(minutes=2))
            logger.info("   ✅ Workflow completed successfully!")
            logger.info(f"   📊 Status: {result.status.value}")
            logger.info(f"   📈 Score: {result.relevance_score}")
            logger.info(f"   🧠 Decision: {result.decision}")
            if result.analysis_summary:
                logger.info(f"   📝 Summary: {result.analysis_summary[:100]}...")

        except TimeoutError:
            logger.warning("   ⏰ Workflow timed out, checking status...")
            # Query current status
            status = await handle.query(SimpleDocumentWorkflow.get_status)
            logger.info(f"   📊 Current status: {status.status.value}")
            logger.info(f"   📈 Current score: {status.relevance_score}")

        # Step 4: Test controller decision (if pending review)
        logger.info("\n4️⃣  Testing controller interaction...")
        try:
            status = await handle.query(SimpleDocumentWorkflow.get_status)
            if status.status.value == "pending_review":
                logger.info("   👤 Document needs human review")
                logger.info("   📝 Submitting controller decision...")

                # Submit controller decision
                await handle.signal(
                    SimpleDocumentWorkflow.submit_controller_decision, "approve"
                )
                logger.info("   ✅ Controller decision submitted: approve")

                # Wait a bit for the workflow to process
                await asyncio.sleep(2)

                # Check final status
                final_status = await handle.query(SimpleDocumentWorkflow.get_status)
                logger.info(f"   📊 Final status: {final_status.status.value}")
            else:
                logger.info(
                    f"   📊 Document status: {status.status.value} (no human review needed)"
                )

        except Exception as e:
            logger.warning(f"   ⚠️  Could not test controller interaction: {e}")

        logger.info("\n✅ Full workflow test completed!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


async def main():
    """Main test execution."""
    await test_full_workflow()


if __name__ == "__main__":
    asyncio.run(main())
