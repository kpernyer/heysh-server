#!/usr/bin/env python3
"""Demo of the complete OpenRouter flow for domain onboarding."""

import asyncio
import json
import logging
import os
from typing import Any, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def demo_complete_openrouter_flow():
    """Demo the complete OpenRouter flow for domain onboarding."""
    logger.info("=" * 80)
    logger.info("🚀 COMPLETE OPENROUTER DOMAIN ONBOARDING DEMO")
    logger.info("=" * 80)

    # Step 1: Enhanced domain research
    logger.info("\n1️⃣  Enhanced Domain Research with OpenRouter")
    logger.info("-" * 50)
    
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

    from activity.openai_enhanced import enhanced_domain_research_activity
    research_result = await enhanced_domain_research_activity(research_input)
    
    logger.info("✅ Enhanced research completed")
    logger.info(f"📊 Summary: {research_result['summary'][:100]}...")
    logger.info(f"🏷️  Topics: {len(research_result['topics'])} topics discovered")
    logger.info(f"📚 Sources: {len(research_result['sources'])} sources")
    logger.info(f"💡 Insights: {len(research_result.get('insights', []))} insights")

    # Step 2: Continuous research
    logger.info("\n2️⃣  Continuous Research with OpenRouter")
    logger.info("-" * 50)
    
    from activity.openai_enhanced import continuous_research_activity
    continuous_result = await continuous_research_activity(
        "Architect Isac Gustav Clason",
        "Historical development",
        []
    )
    
    logger.info("✅ Continuous research completed")
    logger.info(f"💡 New insights: {len(continuous_result.get('new_insights', []))}")
    logger.info(f"➕ Additional topics: {len(continuous_result.get('additional_topics', []))}")

    # Step 3: Deep question analysis
    logger.info("\n3️⃣  Deep Question Analysis with OpenRouter")
    logger.info("-" * 50)
    
    question = "What are the fundamental principles of Architect Isac Gustav Clason's architectural style?"
    domain_context = {
        "domain_name": "Architect Isac Gustav Clason",
        "domain_description": "Swedish architect and pioneer of National Romanticism",
        "research_summary": research_result.get("summary", ""),
        "topics": research_result.get("topics", []),
        "continuous_insights": continuous_result.get("new_insights", [])
    }
    
    from activity.openai_enhanced import deep_question_analysis_activity
    deep_analysis = await deep_question_analysis_activity(
        question,
        domain_context,
        "comprehensive"
    )
    
    logger.info("✅ Deep analysis completed")
    logger.info(f"📝 Answer: {deep_analysis.get('answer', '')[:100]}...")
    logger.info(f"🧠 Key concepts: {len(deep_analysis.get('key_concepts', []))}")
    logger.info(f"📊 Confidence: {deep_analysis.get('confidence', 0)}")

    # Step 4: Generate example questions
    logger.info("\n4️⃣  Example Questions Generation")
    logger.info("-" * 50)
    
    # Mock questions for demo
    example_questions = [
        {
            "question": "What are the fundamental principles of Architect Isac Gustav Clason's architectural style?",
            "category": "technical",
            "difficulty": "beginner",
            "relevance_score": 0.9
        },
        {
            "question": "How did Isac Gustav Clason influence Swedish National Romanticism?",
            "category": "historical",
            "difficulty": "intermediate",
            "relevance_score": 0.85
        },
        {
            "question": "What are the key works of Architect Isac Gustav Clason?",
            "category": "practical",
            "difficulty": "beginner",
            "relevance_score": 0.8
        }
    ]
    
    logger.info("✅ Example questions generated")
    for i, q in enumerate(example_questions, 1):
        logger.info(f"   {i}. {q['question']} ({q['category']}, {q['difficulty']})")

    # Step 5: Owner feedback simulation
    logger.info("\n5️⃣  Owner Feedback Simulation")
    logger.info("-" * 50)
    
    owner_feedback = {
        "approved": True,
        "question_rankings": [
            {"question_id": 0, "ranking": 1, "relevance": "high"},
            {"question_id": 1, "ranking": 2, "relevance": "high"},
            {"question_id": 2, "ranking": 3, "relevance": "medium"}
        ],
        "additional_topics": ["urban development", "material science"],
        "remove_topics": [],
        "quality_requirements": {
            "quality_threshold": 8.0,
            "min_length": 1500
        }
    }
    
    logger.info("✅ Owner feedback collected")
    logger.info(f"   Approved: {owner_feedback['approved']}")
    logger.info(f"   Quality threshold: {owner_feedback['quality_requirements']['quality_threshold']}")
    logger.info(f"   Additional topics: {len(owner_feedback['additional_topics'])}")

    # Step 6: Final domain configuration
    logger.info("\n6️⃣  Final Domain Configuration")
    logger.info("-" * 50)
    
    final_config = {
        "domain_id": "architect-isac-gustav-clason",
        "title": "Architect Isac Gustav Clason",
        "description": "Swedish architect and pioneer of National Romanticism",
        "status": "active",
        "topics": research_result["topics"] + owner_feedback["additional_topics"],
        "quality_criteria": {
            "min_length": owner_feedback["quality_requirements"]["min_length"],
            "quality_threshold": owner_feedback["quality_requirements"]["quality_threshold"],
            "required_sections": ["abstract", "introduction", "conclusion", "references"],
            "technical_depth_required": True,
            "safety_considerations_required": True,
            "practical_applications_required": True
        },
        "search_attributes": {
            "domain_id": "architect-isac-gustav-clason",
            "domain_name": "Architect Isac Gustav Clason",
            "owner_id": "owner-123",
            "topics": research_result["topics"],
            "target_audience": ["architecture students", "historians", "preservation professionals"]
        },
        "bootstrap_prompt": research_result.get("bootstrap_prompt", ""),
        "research_steps": research_result.get("research_steps", []),
        "target_audience": ["architecture students", "historians", "preservation professionals"]
    }
    
    logger.info("✅ Final domain configuration generated")
    logger.info(f"   Domain ID: {final_config['domain_id']}")
    logger.info(f"   Topics: {len(final_config['topics'])} topics")
    logger.info(f"   Quality threshold: {final_config['quality_criteria']['quality_threshold']}")
    logger.info(f"   Min length: {final_config['quality_criteria']['min_length']} characters")

    # Save configuration
    config_file = f"domain_config_{final_config['domain_id']}.json"
    with open(config_file, "w") as f:
        json.dump(final_config, f, indent=2)
    
    logger.info(f"💾 Configuration saved to: {config_file}")

    logger.info("\n" + "=" * 80)
    logger.info("🎉 COMPLETE OPENROUTER DOMAIN ONBOARDING DEMO SUCCESSFUL!")
    logger.info("=" * 80)
    logger.info("🚀 Ready for Hey.sh webpage UX implementation!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_complete_openrouter_flow())
