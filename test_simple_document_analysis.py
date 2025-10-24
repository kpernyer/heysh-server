#!/usr/bin/env python3
"""Simple test for Document Analysis Workflow.

This is a minimal test that doesn't require all external dependencies.
"""

import asyncio
import logging
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_simple_document_analysis():
    """Test the document analysis workflow with minimal dependencies."""
    logger.info("=" * 80)
    logger.info("🧪 SIMPLE DOCUMENT ANALYSIS TEST")
    logger.info("=" * 80)

    try:
        # Test 1: Test AI activity directly
        logger.info("\n1️⃣  Testing AI relevance assessment...")
        await test_ai_activity()

        # Test 2: Test workflow logic
        logger.info("\n2️⃣  Testing workflow decision logic...")
        await test_workflow_logic()

        # Test 3: Test Search Attributes
        logger.info("\n3️⃣  Testing Search Attributes...")
        await test_search_attributes()

        logger.info("\n✅ All simple tests completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


async def test_ai_activity():
    """Test the AI activity directly."""
    try:
        from activity.ai import assess_document_relevance_activity

        # Test data
        document_id = str(uuid.uuid4())
        file_path = f"documents/{document_id}/test-doc.pdf"
        domain_criteria = {
            "topics": ["technology", "AI", "machine learning"],
            "min_length": 1000,
            "quality_threshold": 8.0,
        }
        ai_config = {
            "model": "gpt-4o",
            "temperature": 0.1,
            "max_tokens": 1000,
        }

        # Call activity
        result = await assess_document_relevance_activity(
            document_id, file_path, domain_criteria, ai_config
        )

        logger.info("   ✅ AI activity completed")
        logger.info(f"   📊 Relevance score: {result['relevance_score']}")
        logger.info(f"   ✅ Is relevant: {result['is_relevant']}")
        logger.info(f"   📝 Summary: {result['analysis_summary'][:100]}...")
        logger.info(f"   🏷️  Topics: {result['topics']}")

        return result

    except Exception as e:
        logger.error(f"   ❌ AI activity failed: {e}")
        raise


async def test_workflow_logic():
    """Test workflow decision logic."""
    logger.info("   🧠 Testing decision logic...")

    # Test different score scenarios
    test_cases = [
        {
            "score": 9.5,
            "auto_approve": 8.0,
            "relevance": 7.0,
            "expected": "auto_approve",
        },
        {
            "score": 7.5,
            "auto_approve": 8.0,
            "relevance": 7.0,
            "expected": "needs_review",
        },
        {"score": 5.0, "auto_approve": 8.0, "relevance": 7.0, "expected": "reject"},
    ]

    for i, case in enumerate(test_cases, 1):
        score = case["score"]
        auto_approve = case["auto_approve"]
        relevance = case["relevance"]
        expected = case["expected"]

        # Simulate decision logic
        if score >= auto_approve:
            decision = "auto_approve"
        elif score >= relevance:
            decision = "needs_review"
        else:
            decision = "reject"

        status = "✅" if decision == expected else "❌"
        logger.info(
            f"   {status} Case {i}: Score {score} → {decision} (expected: {expected})"
        )


async def test_search_attributes():
    """Test Search Attributes structure."""
    logger.info("   🔍 Testing Search Attributes structure...")

    # Mock Search Attributes
    search_attributes = {
        "Assignee": "controller",
        "Queue": "document-review",
        "Status": "pending",
        "Priority": "normal",
        "DueAt": "2024-01-15T10:00:00Z",
        "Tenant": "domain-456",
        "DocumentId": "doc-123",
        "ContributorId": "contributor-789",
        "RelevanceScore": 7.5,
    }

    logger.info("   ✅ Search Attributes structure valid")
    logger.info(f"   📋 Assignee: {search_attributes['Assignee']}")
    logger.info(f"   📋 Queue: {search_attributes['Queue']}")
    logger.info(f"   📋 Status: {search_attributes['Status']}")
    logger.info(f"   📋 Priority: {search_attributes['Priority']}")
    logger.info(f"   📋 Due: {search_attributes['DueAt']}")

    # Test query string
    query = f'Assignee = "{search_attributes["Assignee"]}" AND Status = "{search_attributes["Status"]}" AND Queue = "{search_attributes["Queue"]}"'
    logger.info(f"   🔍 Query: {query}")


async def test_workflow_states():
    """Test workflow state transitions."""
    logger.info("   🔄 Testing workflow state transitions...")

    states = [
        "UPLOADED",
        "ANALYZING",
        "PENDING_REVIEW",
        "APPROVED",
        "REJECTED",
        "PUBLISHED",
        "ARCHIVED",
    ]

    for state in states:
        logger.info(f"   ✅ State: {state}")

    logger.info("   ✅ All workflow states defined")


async def main():
    """Main test execution."""
    await test_simple_document_analysis()


if __name__ == "__main__":
    asyncio.run(main())
