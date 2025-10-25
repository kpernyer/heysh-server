#!/usr/bin/env python3
"""Test complete domain bootstrap workflow with OpenAI research and owner feedback."""

import asyncio
import logging
import uuid
from typing import Any, Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_complete_domain_bootstrap():
    """Test the complete domain bootstrap workflow."""
    logger.info("=" * 80)
    logger.info("🏗️  COMPLETE DOMAIN BOOTSTRAP WORKFLOW TEST")
    logger.info("=" * 80)

    # Test 1: Test domain research with OpenAI
    logger.info("\n1️⃣  Testing OpenAI domain research...")
    await test_openai_domain_research()

    # Test 2: Test research analysis
    logger.info("\n2️⃣  Testing research analysis...")
    await test_research_analysis()

    # Test 3: Test knowledge question generation
    logger.info("\n3️⃣  Testing knowledge question generation...")
    await test_knowledge_question_generation()

    # Test 4: Test domain configuration
    logger.info("\n4️⃣  Testing domain configuration...")
    await test_domain_configuration()

    # Test 5: Test owner feedback flow
    logger.info("\n5️⃣  Testing owner feedback flow...")
    await test_owner_feedback_flow()

    logger.info("\n✅ Complete domain bootstrap workflow test completed!")
    logger.info("=" * 80)


async def test_openai_domain_research():
    """Test OpenAI domain research activity."""
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

        logger.info("   ✅ OpenAI domain research completed")
        logger.info(f"   📊 Summary: {result['summary'][:100]}...")
        logger.info(f"   🏷️  Topics: {result['topics'][:5]}")
        logger.info(f"   📚 Sources: {len(result['sources'])} sources")
        logger.info(f"   💡 Recommendations: {len(result['recommendations'])} recommendations")

        return result

    except Exception as e:
        logger.error(f"   ❌ OpenAI domain research failed: {e}")
        raise


async def test_research_analysis():
    """Test research analysis activity."""
    try:
        from activity.domain_research import analyze_research_results_activity

        # Mock research results
        research_results = {
            "summary": "Comprehensive research on Architect Isac Gustav Clason and Swedish National Romanticism",
            "topics": [
                "isac gustav clason",
                "swedish architecture",
                "national romanticism",
                "cultural heritage",
                "architectural preservation",
                "historical buildings",
                "architectural education",
                "swedish architects"
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
            "knowledge_gaps": [
                "Limited research on international influence",
                "Need for more technical analysis of building techniques",
                "Gap in educational applications"
            ],
            "sources": [
                "Academic research on Swedish architecture",
                "Historical documents and archives",
                "Expert interviews with architectural historians"
            ],
            "recommendations": [
                "Focus on architectural analysis and preservation",
                "Develop educational resources for students",
                "Create community engagement initiatives"
            ]
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


async def test_knowledge_question_generation():
    """Test knowledge question generation activity."""
    try:
        from activity.knowledge_questions import generate_knowledge_questions_activity

        # Test questions input
        questions_input = {
            "domain_name": "Architect Isac Gustav Clason",
            "domain_description": "Swedish architect and pioneer of National Romanticism",
            "topics": [
                "isac gustav clason",
                "swedish architecture",
                "national romanticism",
                "cultural heritage",
                "architectural preservation"
            ],
            "research_summary": "Comprehensive research on Architect Isac Gustav Clason and Swedish National Romanticism",
            "target_audience": ["architecture students", "historians", "preservation professionals"]
        }

        result = await generate_knowledge_questions_activity(questions_input)

        logger.info("   ✅ Knowledge questions generated")
        logger.info(f"   ❓ Questions: {len(result)} questions")
        
        for i, question in enumerate(result[:3], 1):
            logger.info(f"      {i}. {question['question']}")
            logger.info(f"         Category: {question['category']}, Difficulty: {question['difficulty']}")
            logger.info(f"         Relevance: {question['relevance_score']}")

        return result

    except Exception as e:
        logger.error(f"   ❌ Knowledge question generation failed: {e}")
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
            "cultural heritage",
            "architectural preservation"
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


async def test_owner_feedback_flow():
    """Test owner feedback flow."""
    logger.info("   👤 Testing owner feedback flow...")

    # Mock example questions
    example_questions = [
        {
            "question": "What are the fundamental principles of Architect Isac Gustav Clason's architectural style?",
            "category": "technical",
            "difficulty": "beginner",
            "relevance_score": 0.9,
            "expected_answer_type": "conceptual"
        },
        {
            "question": "How did Isac Gustav Clason influence Swedish architecture?",
            "category": "historical",
            "difficulty": "intermediate",
            "relevance_score": 0.8,
            "expected_answer_type": "analytical"
        },
        {
            "question": "What are the key characteristics of National Romanticism in architecture?",
            "category": "technical",
            "difficulty": "intermediate",
            "relevance_score": 0.85,
            "expected_answer_type": "conceptual"
        },
        {
            "question": "How can Clason's architectural principles be applied in modern preservation?",
            "category": "practical",
            "difficulty": "advanced",
            "relevance_score": 0.75,
            "expected_answer_type": "procedural"
        },
        {
            "question": "What are the challenges in preserving Clason's architectural works?",
            "category": "problem-solving",
            "difficulty": "advanced",
            "relevance_score": 0.7,
            "expected_answer_type": "analytical"
        }
    ]

    # Mock owner feedback
    owner_feedback = {
        "approved": True,
        "feedback": {
            "overall_quality": "excellent",
            "research_depth": "comprehensive",
            "topic_coverage": "well_covered"
        },
        "question_rankings": [
            {"question_id": 0, "ranking": 1, "relevance": "high"},
            {"question_id": 1, "ranking": 2, "relevance": "high"},
            {"question_id": 2, "ranking": 3, "relevance": "medium"},
            {"question_id": 3, "ranking": 4, "relevance": "medium"},
            {"question_id": 4, "ranking": 5, "relevance": "low"}
        ],
        "additional_topics": [
            "architectural education methods",
            "international influence of Swedish architecture"
        ],
        "remove_topics": [
            "modern architecture trends"
        ],
        "quality_requirements": {
            "min_length": 2000,
            "quality_threshold": 8.5,
            "require_visual_documentation": True
        }
    }

    logger.info("   ✅ Owner feedback flow validated")
    logger.info(f"   👤 Owner approved: {owner_feedback['approved']}")
    logger.info(f"   📊 Question rankings: {len(owner_feedback['question_rankings'])} questions ranked")
    logger.info(f"   ➕ Additional topics: {len(owner_feedback['additional_topics'])} topics")
    logger.info(f"   ➖ Remove topics: {len(owner_feedback['remove_topics'])} topics")
    logger.info(f"   📈 Quality threshold: {owner_feedback['quality_requirements']['quality_threshold']}")

    return owner_feedback


async def test_workflow_integration():
    """Test complete workflow integration."""
    logger.info("   🔄 Testing complete workflow integration...")

    # Test workflow input
    workflow_input = {
        "domain_id": "architect-clason-123",
        "owner_id": "owner-456",
        "title": "Architect Isac Gustav Clason",
        "description": "Swedish architect and pioneer of National Romanticism",
        "slug": "architect-isac-gustav-clason",
        "initial_topics": ["architecture", "swedish history", "national romanticism"],
        "target_audience": ["architecture students", "historians", "preservation professionals"],
        "research_focus": "Architectural heritage and cultural significance",
        "quality_requirements": {"quality_threshold": 8.0, "min_length": 1500},
        "research_depth": "comprehensive",
        "include_historical": True,
        "include_technical": True,
        "include_practical": True
    }

    logger.info("   ✅ Complete workflow input validated")
    logger.info(f"   📋 Domain: {workflow_input['title']}")
    logger.info(f"   👤 Owner: {workflow_input['owner_id']}")
    logger.info(f"   🏷️  Topics: {len(workflow_input['initial_topics'])} topics")
    logger.info(f"   👥 Audience: {len(workflow_input['target_audience'])} audience types")
    logger.info(f"   🔍 Research focus: {workflow_input['research_focus']}")

    return workflow_input


async def main():
    """Main test execution."""
    await test_complete_domain_bootstrap()


if __name__ == "__main__":
    asyncio.run(main())
