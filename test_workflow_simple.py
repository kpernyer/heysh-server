#!/usr/bin/env python3
"""Simple workflow test that works with Temporal."""

import asyncio
import logging
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_workflow_simple():
    """Test a simple workflow with Temporal."""
    logger.info("=" * 80)
    logger.info("🧪 SIMPLE WORKFLOW TEST")
    logger.info("=" * 80)

    try:
        # Step 1: Connect to Temporal
        logger.info("\n1️⃣  Connecting to Temporal...")
        from temporalio.client import Client

        client = await Client.connect("localhost:7233", namespace="default")
        logger.info("   ✅ Connected to Temporal")

        # Step 2: Test AI activity directly
        logger.info("\n2️⃣  Testing AI activity...")
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

        logger.info("\n✅ All tests completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


async def main():
    """Main test execution."""
    await test_workflow_simple()


if __name__ == "__main__":
    asyncio.run(main())
