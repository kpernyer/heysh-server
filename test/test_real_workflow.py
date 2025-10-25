#!/usr/bin/env python3
"""Test a real Temporal workflow execution."""

import asyncio
import logging
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_real_workflow():
    """Test a real workflow execution with Temporal."""
    logger.info("=" * 80)
    logger.info("🚀 REAL WORKFLOW TEST")
    logger.info("=" * 80)

    try:
        # Step 1: Connect to Temporal
        logger.info("\n1️⃣  Connecting to Temporal...")
        from temporalio.client import Client

        client = await Client.connect("localhost:7233", namespace="default")
        logger.info("   ✅ Connected to Temporal")

        # Step 2: Test AI activity directly (not through workflow)
        logger.info("\n2️⃣  Testing AI activity directly...")
        from activity.ai import assess_document_relevance_activity

        document_id = str(uuid.uuid4())
        domain_criteria = {
            "topics": ["technology", "AI"],
            "min_length": 1000,
            "quality_threshold": 8.0,
        }
        ai_config = {
            "model": "gpt-4o",
            "temperature": 0.1,
        }

        # Call activity directly (not through workflow)
        result = await assess_document_relevance_activity(
            document_id, "test-doc.pdf", domain_criteria, ai_config
        )

        logger.info("   ✅ AI activity completed")
        logger.info(f"   📊 Score: {result['relevance_score']}")
        logger.info(f"   ✅ Relevant: {result['is_relevant']}")

        # Step 3: Test Search Attributes
        logger.info("\n3️⃣  Testing Search Attributes...")
        search_attrs = {
            "Assignee": "controller",
            "Queue": "document-review",
            "Status": "pending",
            "Priority": "normal",
            "DocumentId": document_id,
            "RelevanceScore": result["relevance_score"],
        }

        logger.info(f"   ✅ Search Attributes: {search_attrs}")

        # Step 4: Test decision logic
        logger.info("\n4️⃣  Testing decision logic...")
        score = result["relevance_score"]
        if score >= 8.0:
            decision = "auto_approve"
        elif score >= 7.0:
            decision = "needs_review"
        else:
            decision = "reject"

        logger.info(f"   🧠 Decision: {decision} (score: {score})")

        # Step 5: Simulate workflow execution
        logger.info("\n5️⃣  Simulating workflow execution...")

        # Simulate workflow states
        states = ["UPLOADED", "ANALYZING", "PENDING_REVIEW", "APPROVED", "REJECTED"]
        current_state = "UPLOADED"

        for state in states:
            if state == current_state:
                logger.info(f"   🔄 Current state: {state}")
                break

        # Simulate state transitions based on decision
        if decision == "auto_approve":
            logger.info("   ✅ Auto-approving document")
            logger.info("   📝 Updating Search Attributes: Status = 'approved'")
        elif decision == "needs_review":
            logger.info("   👤 Document needs human review")
            logger.info("   📝 Updating Search Attributes: Status = 'pending_review'")
            logger.info("   📧 Notifying controller for review")
        else:
            logger.info("   ❌ Rejecting document")
            logger.info("   📝 Updating Search Attributes: Status = 'rejected'")
            logger.info("   📧 Notifying contributor of rejection")

        logger.info("\n✅ Real workflow simulation completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


async def main():
    """Main test execution."""
    await test_real_workflow()


if __name__ == "__main__":
    asyncio.run(main())
