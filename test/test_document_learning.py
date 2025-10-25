#!/usr/bin/env python3
"""Test document learning system with balloon articles."""

import asyncio
import logging
import uuid
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_document_learning():
    """Test the document learning system with balloon articles."""
    logger.info("=" * 80)
    logger.info("🎈 DOCUMENT LEARNING SYSTEM TEST")
    logger.info("=" * 80)

    # Step 1: Check test documents
    logger.info("\n1️⃣  Checking test documents...")
    test_docs_dir = Path("test-documents")
    if not test_docs_dir.exists():
        logger.error("   ❌ Test documents directory not found")
        return

    balloon_docs = list(test_docs_dir.glob("balloon-article-*.txt"))
    logger.info(f"   📄 Found {len(balloon_docs)} balloon documents:")
    for doc in balloon_docs:
        logger.info(f"      - {doc.name}")

    # Step 2: Test AI analysis on each document
    logger.info("\n2️⃣  Testing AI analysis on balloon documents...")
    from activity.ai import assess_document_relevance_activity

    # Use balloon domain criteria
    from config.balloon_criteria import get_balloon_domain_criteria
    balloon_criteria = get_balloon_domain_criteria()
    
    domain_criteria = {
        "topics": balloon_criteria["topics"],
        "min_length": balloon_criteria["quality_criteria"]["min_length"],
        "quality_threshold": balloon_criteria["quality_criteria"]["quality_threshold"],
        "required_sections": balloon_criteria["quality_criteria"]["required_sections"],
        "quality_indicators": balloon_criteria["quality_indicators"],
    }
    ai_config = {
        "model": "gpt-4o",
        "temperature": 0.1,
    }

    results = []
    for i, doc_path in enumerate(balloon_docs, 1):
        logger.info(f"\n   📄 Analyzing document {i}: {doc_path.name}")

        # Read document content
        try:
            with open(doc_path, encoding="utf-8") as f:
                content = f.read()
            logger.info(f"      📊 Document length: {len(content)} characters")
        except Exception as e:
            logger.error(f"      ❌ Failed to read document: {e}")
            continue

        # Analyze document
        try:
            document_id = str(uuid.uuid4())
            result = await assess_document_relevance_activity(
                document_id, str(doc_path), domain_criteria, ai_config
            )

            logger.info("      ✅ Analysis completed")
            logger.info(f"      📈 Relevance score: {result['relevance_score']:.2f}")
            logger.info(f"      ✅ Is relevant: {result['is_relevant']}")
            logger.info(
                f"      🏷️  Topics: {result['topics'][:3]}..."
            )  # Show first 3 topics
            logger.info(f"      📝 Summary: {result['analysis_summary'][:100]}...")

            results.append(
                {
                    "document": doc_path.name,
                    "score": result["relevance_score"],
                    "relevant": result["is_relevant"],
                    "topics": result["topics"],
                    "summary": result["analysis_summary"],
                }
            )

        except Exception as e:
            logger.error(f"      ❌ Analysis failed: {e}")

    # Step 3: Analyze learning patterns
    logger.info("\n3️⃣  Analyzing learning patterns...")
    if results:
        avg_score = sum(r["score"] for r in results) / len(results)
        relevant_count = sum(1 for r in results if r["relevant"])

        logger.info(f"   📊 Average relevance score: {avg_score:.2f}")
        logger.info(f"   ✅ Relevant documents: {relevant_count}/{len(results)}")

        # Show decision logic
        logger.info("\n   🧠 Decision logic analysis:")
        for result in results:
            score = result["score"]
            if score >= 8.0:
                decision = "Auto-approve (high quality)"
            elif score >= 7.0:
                decision = "Needs human review"
            else:
                decision = "Auto-reject (low quality)"

            logger.info(f"      {result['document']}: {score:.2f} → {decision}")

    # Step 4: Test system learning
    logger.info("\n4️⃣  Testing system learning capabilities...")

    # Simulate learning from multiple documents
    all_topics = set()
    for result in results:
        all_topics.update(result["topics"])

    logger.info(f"   🧠 System learned about topics: {list(all_topics)[:10]}...")
    logger.info(f"   📚 Total topics identified: {len(all_topics)}")

    # Simulate knowledge base updates
    logger.info("\n   📝 Simulating knowledge base updates...")
    for result in results:
        if result["relevant"]:
            logger.info(f"      ✅ {result['document']} → Added to knowledge base")
            logger.info(f"         Topics: {result['topics'][:5]}")
        else:
            logger.info(f"      ❌ {result['document']} → Rejected (low relevance)")

    # Step 5: Test HITL controller simulation
    logger.info("\n5️⃣  Testing Human-in-the-Loop controller simulation...")

    pending_review = [r for r in results if 7.0 <= r["score"] < 8.0]
    if pending_review:
        logger.info(f"   👤 {len(pending_review)} documents need human review:")
        for result in pending_review:
            logger.info(f"      - {result['document']} (score: {result['score']:.2f})")

        logger.info("\n   🎯 Controller decisions:")
        for result in pending_review:
            # Simulate controller decision
            decision = "approve" if result["score"] > 7.5 else "reject"
            logger.info(f"      {result['document']}: {decision}")
    else:
        logger.info("   ✅ No documents need human review")

    logger.info("\n✅ Document learning system test completed!")
    logger.info("=" * 80)

    # Summary
    logger.info("\n📊 SUMMARY:")
    logger.info(f"   📄 Documents analyzed: {len(results)}")
    logger.info(f"   📈 Average score: {avg_score:.2f}")
    logger.info(f"   ✅ Relevant: {relevant_count}")
    logger.info(f"   🧠 Topics learned: {len(all_topics)}")
    logger.info(f"   👤 Human review needed: {len(pending_review)}")


async def main():
    """Main test execution."""
    await test_document_learning()


if __name__ == "__main__":
    asyncio.run(main())
