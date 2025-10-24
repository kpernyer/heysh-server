#!/usr/bin/env python3
"""Test OpenRouter integration with real API calls."""

import asyncio
import json
import logging
import os
from typing import Any, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_openrouter_integration():
    """Test OpenRouter integration with real API calls."""
    logger.info("=" * 80)
    logger.info("🌐 OPENROUTER INTEGRATION TEST")
    logger.info("=" * 80)

    # Test 1: Enhanced domain research with OpenRouter
    logger.info("\n1️⃣  Testing OpenRouter domain research...")
    await test_openrouter_research()

    # Test 2: Continuous research with OpenRouter
    logger.info("\n2️⃣  Testing OpenRouter continuous research...")
    await test_openrouter_continuous_research()

    # Test 3: Deep question analysis with OpenRouter
    logger.info("\n3️⃣  Testing OpenRouter deep analysis...")
    await test_openrouter_deep_analysis()

    logger.info("\n✅ OpenRouter integration test completed!")
    logger.info("=" * 80)


async def test_openrouter_research():
    """Test OpenRouter domain research."""
    try:
        from activity.openai_enhanced import enhanced_domain_research_activity

        # Test research input for Architect Clason domain
        research_input = {
            "domain_name": "Architect Isac Gustav Clason",
            "domain_description": "Swedish architect and pioneer of National Romanticism",
            "initial_topics": ["architecture", "swedish history", "national romanticism"],
            "target_audience": ["architecture students", "historians", "preservation professionals"],
            "research_focus": "Architectural heritage and cultural significance",
            "research_depth": "comprehensive",
            "include_historical": True,
            "include_technical": True,
            "include_practical": True,
        }

        logger.info("🔍 Starting OpenRouter research...")
        result = await enhanced_domain_research_activity(research_input)

        logger.info("   ✅ OpenRouter research completed")
        logger.info(f"   📊 Summary: {result['summary'][:100]}...")
        logger.info(f"   🏷️  Topics: {result['topics'][:5]}")
        logger.info(f"   📚 Sources: {len(result['sources'])} sources")
        logger.info(f"   💡 Recommendations: {len(result['recommendations'])} recommendations")
        
        if 'insights' in result:
            logger.info(f"   🔍 Insights: {len(result['insights'])} insights")
            for insight in result['insights'][:3]:
                logger.info(f"      • {insight.get('insight', 'Insight')} (relevance: {insight.get('relevance', 0)})")

        return result

    except Exception as e:
        logger.error(f"   ❌ OpenRouter research failed: {e}")
        raise


async def test_openrouter_continuous_research():
    """Test OpenRouter continuous research."""
    try:
        from activity.openai_enhanced import continuous_research_activity

        # Mock current insights
        current_insights = [
            {
                "id": "insight_1",
                "insight": "Clason was a pioneer of National Romanticism",
                "category": "historical",
                "relevance": 0.9
            }
        ]

        logger.info("🔄 Starting OpenRouter continuous research...")
        result = await continuous_research_activity(
            "Architect Isac Gustav Clason",
            "Historical development",
            current_insights
        )

        logger.info("   ✅ OpenRouter continuous research completed")
        logger.info(f"   💡 New insights: {len(result.get('new_insights', []))}")
        logger.info(f"   ➕ Additional topics: {len(result.get('additional_topics', []))}")
        logger.info(f"   🔍 New gaps: {len(result.get('new_gaps', []))}")
        logger.info(f"   📈 Recommendations: {len(result.get('recommendations', []))}")

        return result

    except Exception as e:
        logger.error(f"   ❌ OpenRouter continuous research failed: {e}")
        raise


async def test_openrouter_deep_analysis():
    """Test OpenRouter deep analysis."""
    try:
        from activity.openai_enhanced import deep_question_analysis_activity

        # Test question
        question = "What are the fundamental principles of Architect Isac Gustav Clason's architectural style?"
        
        # Domain context
        domain_context = {
            "domain_name": "Architect Isac Gustav Clason",
            "domain_description": "Swedish architect and pioneer of National Romanticism",
            "research_summary": "Comprehensive research on Architect Isac Gustav Clason reveals a pioneering figure in Swedish National Romanticism.",
            "topics": ["architecture", "swedish history", "national romanticism", "cultural heritage"],
            "continuous_insights": [
                {
                    "insight": "Clason was a pioneer of National Romanticism",
                    "category": "historical",
                    "relevance": 0.9
                }
            ]
        }

        logger.info("🔍 Starting OpenRouter deep analysis...")
        result = await deep_question_analysis_activity(
            question,
            domain_context,
            "comprehensive"
        )

        logger.info("   ✅ OpenRouter deep analysis completed")
        logger.info(f"   📝 Answer: {result.get('answer', 'No answer')[:100]}...")
        logger.info(f"   🧠 Key concepts: {len(result.get('key_concepts', []))}")
        logger.info(f"   🔗 Relationships: {len(result.get('relationships', []))}")
        logger.info(f"   ❓ Related questions: {len(result.get('related_questions', []))}")
        logger.info(f"   💡 Actionable insights: {len(result.get('actionable_insights', []))}")
        logger.info(f"   📊 Confidence: {result.get('confidence', 0)}")

        return result

    except Exception as e:
        logger.error(f"   ❌ OpenRouter deep analysis failed: {e}")
        raise


async def test_openrouter_direct_api():
    """Test OpenRouter API directly."""
    try:
        from openai import AsyncOpenAI
        
        # Initialize OpenRouter client
        client = AsyncOpenAI(
            api_key=os.getenv("OPEN_ROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={"HTTP-Referer": "https://hey.sh"}
        )
        
        logger.info("🌐 Testing OpenRouter API directly...")
        
        # Test simple completion
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Architect Isac Gustav Clason known for? Please provide a brief answer."}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        content = response.choices[0].message.content
        logger.info("   ✅ OpenRouter API test successful")
        logger.info(f"   📝 Response: {content}")
        
        return content
        
    except Exception as e:
        logger.error(f"   ❌ OpenRouter API test failed: {e}")
        raise


async def main():
    """Main test execution."""
    await test_openrouter_integration()


if __name__ == "__main__":
    asyncio.run(main())
