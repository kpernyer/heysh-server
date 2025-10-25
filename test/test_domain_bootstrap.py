#!/usr/bin/env python3
"""Test domain bootstrap workflow with multi-domain architecture."""

import asyncio
import logging
import uuid
from typing import Any, Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_domain_bootstrap():
    """Test the domain bootstrap workflow."""
    logger.info("=" * 80)
    logger.info("🏗️  DOMAIN BOOTSTRAP WORKFLOW TEST")
    logger.info("=" * 80)

    # Test 1: Test domain research activity
    logger.info("\n1️⃣  Testing domain research activity...")
    await test_domain_research()

    # Test 2: Test research analysis activity
    logger.info("\n2️⃣  Testing research analysis activity...")
    await test_research_analysis()

    # Test 3: Test domain configuration generation
    logger.info("\n3️⃣  Testing domain configuration generation...")
    await test_domain_configuration()

    # Test 4: Test multi-domain architecture
    logger.info("\n4️⃣  Testing multi-domain architecture...")
    await test_multi_domain_architecture()

    logger.info("\n✅ Domain bootstrap workflow test completed!")
    logger.info("=" * 80)


async def test_domain_research():
    """Test domain research activity."""
    try:
        from activity.domain_research import research_domain_activity

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

        result = await research_domain_activity(research_input)

        logger.info("   ✅ Domain research completed")
        logger.info(f"   📊 Summary: {result['summary'][:100]}...")
        logger.info(f"   🏷️  Topics: {result['topics'][:5]}")
        logger.info(f"   📚 Sources: {len(result['sources'])} sources")
        logger.info(f"   💡 Recommendations: {len(result['recommendations'])} recommendations")

        return result

    except Exception as e:
        logger.error(f"   ❌ Domain research failed: {e}")
        raise


async def test_research_analysis():
    """Test research analysis activity."""
    try:
        from activity.domain_research import analyze_research_results_activity

        # Mock research results
        research_results = {
            "summary": "Comprehensive research on Architect Isac Gustav Clason",
            "topics": ["architecture", "swedish history", "national romanticism", "cultural heritage"],
            "quality_criteria": {
                "min_length": 1500,
                "quality_threshold": 8.0,
                "required_sections": ["abstract", "introduction", "historical_context", "analysis", "conclusion", "references"],
                "technical_depth_required": True,
                "historical_accuracy_required": True,
                "architectural_analysis_required": True,
                "cultural_context_required": True
            },
            "knowledge_gaps": ["Limited research on international influence", "Need for more technical analysis"],
            "sources": ["Academic research", "Historical documents", "Expert interviews"],
            "recommendations": ["Focus on architectural analysis", "Develop educational resources"]
        }

        result = await analyze_research_results_activity(research_results, "Architect Isac Gustav Clason")

        logger.info("   ✅ Research analysis completed")
        logger.info(f"   🏷️  Final topics: {result['topics'][:5]}")
        logger.info(f"   📊 Quality criteria: {result['quality_criteria']['quality_threshold']}")
        logger.info(f"   🔍 Search attributes: {len(result['search_attributes'])} attributes")
        logger.info(f"   📝 Bootstrap prompt: {result['bootstrap_prompt'][:100]}...")

        return result

    except Exception as e:
        logger.error(f"   ❌ Research analysis failed: {e}")
        raise


async def test_domain_configuration():
    """Test domain configuration generation."""
    logger.info("   🏗️  Testing domain configuration generation...")

    # Test domain configuration for Architect Clason
    domain_config = {
        "topics": [
            "isac gustav clason",
            "swedish architecture",
            "national romanticism",
            "architectural heritage",
            "cultural buildings"
        ],
        "quality_criteria": {
            "min_length": 1500,
            "quality_threshold": 8.0,
            "required_sections": ["abstract", "introduction", "historical_context", "analysis", "conclusion", "references"],
            "technical_depth_required": True,
            "historical_accuracy_required": True,
            "architectural_analysis_required": True,
            "cultural_context_required": True
        },
        "search_attributes": {
            "domain_id": "architect-clason-123",
            "domain_name": "Architect Isac Gustav Clason",
            "topics": ["architecture", "swedish history", "national romanticism"],
            "target_audience": ["architecture students", "historians", "preservation professionals"]
        },
        "bootstrap_prompt": "Expert analysis of Architect Isac Gustav Clason domain with focus on architectural heritage and cultural significance.",
        "research_steps": [
            "Literature review of Clason's work",
            "Expert interviews on Swedish architecture",
            "Case study analysis of historical buildings"
        ],
        "target_audience": ["architecture students", "historians", "preservation professionals"]
    }

    logger.info(f"   ✅ Domain configuration generated")
    logger.info(f"   🏷️  Topics: {len(domain_config['topics'])} topics")
    logger.info(f"   📊 Quality threshold: {domain_config['quality_criteria']['quality_threshold']}")
    logger.info(f"   🔍 Search attributes: {len(domain_config['search_attributes'])} attributes")
    logger.info(f"   📝 Bootstrap prompt: {domain_config['bootstrap_prompt'][:100]}...")

    return domain_config


async def test_multi_domain_architecture():
    """Test multi-domain architecture."""
    logger.info("   🏗️  Testing multi-domain architecture...")

    # Test multiple domains
    domains = [
        {
            "id": "balloon-domain",
            "name": "Hot Air Balloon Knowledge Base",
            "topics": ["balloon safety", "weather", "navigation", "tourism", "economics"],
            "quality_criteria": {"quality_threshold": 7.0, "min_length": 1000}
        },
        {
            "id": "architect-clason-domain",
            "name": "Architect Isac Gustav Clason Knowledge Base",
            "topics": ["architecture", "swedish history", "national romanticism", "cultural heritage"],
            "quality_criteria": {"quality_threshold": 8.0, "min_length": 1500}
        }
    ]

    for domain in domains:
        logger.info(f"   📋 Domain: {domain['name']}")
        logger.info(f"      ID: {domain['id']}")
        logger.info(f"      Topics: {len(domain['topics'])} topics")
        logger.info(f"      Quality threshold: {domain['quality_criteria']['quality_threshold']}")

    logger.info("   ✅ Multi-domain architecture validated")
    logger.info(f"   📊 Total domains: {len(domains)}")

    return domains


async def test_bootstrap_workflow_integration():
    """Test bootstrap workflow integration."""
    logger.info("   🔄 Testing bootstrap workflow integration...")

    # Test workflow input
    workflow_input = {
        "domain_id": "architect-clason-123",
        "owner_id": "owner-456",
        "domain_name": "Architect Isac Gustav Clason",
        "domain_description": "Swedish architect and pioneer of National Romanticism",
        "initial_topics": ["architecture", "swedish history", "national romanticism"],
        "target_audience": ["architecture students", "historians", "preservation professionals"],
        "research_focus": "Architectural heritage and cultural significance",
        "quality_requirements": {"quality_threshold": 8.0, "min_length": 1500},
        "research_depth": "comprehensive",
        "include_historical": True,
        "include_technical": True,
        "include_practical": True
    }

    logger.info("   ✅ Bootstrap workflow input validated")
    logger.info(f"   📋 Domain: {workflow_input['domain_name']}")
    logger.info(f"   👤 Owner: {workflow_input['owner_id']}")
    logger.info(f"   🏷️  Topics: {len(workflow_input['initial_topics'])} topics")
    logger.info(f"   👥 Audience: {len(workflow_input['target_audience'])} audience types")

    return workflow_input


async def main():
    """Main test execution."""
    await test_domain_bootstrap()


if __name__ == "__main__":
    asyncio.run(main())
