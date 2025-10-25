#!/usr/bin/env python3
"""Test a simple Temporal workflow without Search Attributes."""

import asyncio
import logging
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_simple_workflow():
    """Test a simple Temporal workflow execution."""
    logger.info("=" * 80)
    logger.info("🚀 SIMPLE TEMPORAL WORKFLOW TEST")
    logger.info("=" * 80)

    try:
        # Step 1: Connect to Temporal
        logger.info("\n1️⃣  Connecting to Temporal...")
        from temporalio.client import Client

        client = await Client.connect("localhost:7233", namespace="default")
        logger.info("   ✅ Connected to Temporal")

        # Step 2: Start a simple workflow
        logger.info("\n2️⃣  Starting simple Temporal workflow...")
        from workflow.simple_document_workflow import (
            DocumentInput,
            SimpleDocumentWorkflow,
        )

        # Create test document input
        document_id = str(uuid.uuid4())
        workflow_input = DocumentInput(
            document_id=document_id,
            file_path="test-documents/balloon-article-1.txt",
            domain_id="balloon-domain-123",
            contributor_id="contributor-456",
        )

        # Start the workflow (without Search Attributes)
        handle = await client.start_workflow(
            SimpleDocumentWorkflow.run,
            args=[workflow_input],
            id=f"document-analysis-{document_id}",
            task_queue="hey-sh-workflows",
        )

        logger.info(f"   ✅ Workflow started: {handle.id}")
        logger.info(f"   📋 Document ID: {document_id}")
        logger.info(f"   📄 Document: {workflow_input.file_path}")

        # Step 3: Wait for workflow to complete
        logger.info("\n3️⃣  Waiting for workflow to complete...")
        try:
            # Use asyncio.wait_for for timeout
            result = await asyncio.wait_for(handle.result(), timeout=120)  # 2 minutes
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

        logger.info("\n✅ Simple workflow test completed!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


async def main():
    """Main test execution."""
    await test_simple_workflow()


if __name__ == "__main__":
    asyncio.run(main())
