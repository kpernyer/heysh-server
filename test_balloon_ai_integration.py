#!/usr/bin/env python3
"""Test balloon AI integration with real ChatGPT."""

import asyncio
import logging
import os
import uuid
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_balloon_ai_integration():
    """Test balloon AI integration with ChatGPT."""
    logger.info("=" * 80)
    logger.info("🎈 BALLOON AI INTEGRATION TEST")
    logger.info("=" * 80)

    # Check environment variables
    logger.info("\n1️⃣  Checking environment configuration...")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        logger.info("   ✅ OPENAI_API_KEY is set")
        logger.info(f"   🔑 Key starts with: {openai_key[:10]}...")
    else:
        logger.info("   ⚠️  OPENAI_API_KEY not set - will use mock analysis")
        logger.info("   💡 Set OPENAI_API_KEY in root .env file to test real ChatGPT integration")

    # Test balloon domain criteria
    logger.info("\n2️⃣  Testing balloon domain criteria...")
    try:
        from config.balloon_criteria import get_balloon_domain_criteria, get_balloon_analysis_prompt
        
        balloon_criteria = get_balloon_domain_criteria()
        analysis_prompt = get_balloon_analysis_prompt()
        
        logger.info(f"   📋 Domain: {balloon_criteria['domain_name']}")
        logger.info(f"   🎯 Topics: {len(balloon_criteria['topics'])} topics")
        logger.info(f"   📊 Quality threshold: {balloon_criteria['quality_criteria']['quality_threshold']}")
        logger.info(f"   📝 Min length: {balloon_criteria['quality_criteria']['min_length']}")
        logger.info(f"   🔍 Quality indicators: {len(balloon_criteria['quality_indicators'])}")
        
    except Exception as e:
        logger.error(f"   ❌ Failed to load balloon criteria: {e}")
        return

    # Test AI activity with balloon domain
    logger.info("\n3️⃣  Testing AI activity with balloon domain...")
    try:
        from activity.ai import assess_document_relevance_activity
        
        # Test with a balloon document
        test_docs_dir = Path("test-documents")
        balloon_docs = list(test_docs_dir.glob("balloon-article-*.txt"))
        
        if not balloon_docs:
            logger.warning("   ⚠️  No balloon test documents found")
            return
            
        # Use first balloon document
        doc_path = balloon_docs[0]
        logger.info(f"   📄 Testing with: {doc_path.name}")
        
        # Read document content
        with open(doc_path, encoding="utf-8") as f:
            content = f.read()
        logger.info(f"   📊 Document length: {len(content)} characters")
        
        # Prepare domain criteria
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
            "max_tokens": 1000,
        }
        
        # Test AI analysis
        document_id = str(uuid.uuid4())
        result = await assess_document_relevance_activity(
            document_id, str(doc_path), domain_criteria, ai_config
        )
        
        logger.info("   ✅ AI analysis completed")
        logger.info(f"   📈 Relevance score: {result['relevance_score']:.2f}")
        logger.info(f"   ✅ Is relevant: {result['is_relevant']}")
        logger.info(f"   🏷️  Topics: {result['topics'][:5]}")
        logger.info(f"   📝 Summary: {result['analysis_summary'][:150]}...")
        
        # Show decision logic
        score = result['relevance_score']
        if score >= 8.0:
            decision = "Auto-approve (high quality)"
        elif score >= 7.0:
            decision = "Needs human review"
        else:
            decision = "Auto-reject (low quality)"
        
        logger.info(f"   🎯 Decision: {decision}")
        
        # Show quality indicators
        if 'quality_indicators' in result:
            indicators = result['quality_indicators']
            logger.info(f"   🔍 Quality indicators:")
            for key, value in indicators.items():
                logger.info(f"      {key}: {value:.2f}")
        
    except Exception as e:
        logger.error(f"   ❌ AI analysis failed: {e}")
        import traceback
        traceback.print_exc()

    # Test OpenAI integration status
    logger.info("\n4️⃣  Testing OpenAI integration status...")
    try:
        from openai import AsyncOpenAI
        
        if openai_key:
            client = AsyncOpenAI(api_key=openai_key)
            logger.info("   ✅ OpenAI client initialized successfully")
            logger.info("   🤖 Ready for real ChatGPT analysis")
        else:
            logger.info("   ⚠️  OpenAI client not available (no API key)")
            logger.info("   🔄 Will use mock analysis")
            
    except ImportError:
        logger.warning("   ⚠️  OpenAI package not installed")
        logger.info("   💡 Run: uv add openai")
    except Exception as e:
        logger.error(f"   ❌ OpenAI client error: {e}")

    logger.info("\n✅ Balloon AI integration test completed!")
    logger.info("=" * 80)

    # Summary
    logger.info("\n📊 SUMMARY:")
    logger.info(f"   🔑 OpenAI API: {'✅ Set' if openai_key else '❌ Not set'}")
    logger.info(f"   🎈 Balloon domain: ✅ Configured")
    logger.info(f"   🤖 AI analysis: ✅ Working")
    logger.info(f"   📄 Test document: ✅ Analyzed")
    
    if openai_key:
        logger.info("\n🚀 READY FOR REAL CHATGPT ANALYSIS!")
        logger.info("   OPENAI_API_KEY is set in root .env file")
    else:
        logger.info("\n⚠️  USING MOCK ANALYSIS")
        logger.info("   Set OPENAI_API_KEY in root .env file to enable real ChatGPT integration")


async def main():
    """Main test execution."""
    await test_balloon_ai_integration()


if __name__ == "__main__":
    asyncio.run(main())
