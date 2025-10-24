#!/usr/bin/env python3
"""Cost-effective OpenRouter development script with budget tracking."""

import asyncio
import json
import logging
import os
from typing import Any, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class CostTracker:
    """Track API costs for development."""
    
    def __init__(self):
        """Initialize cost tracker."""
        self.total_tokens = 0
        self.total_cost = 0.0
        self.cost_per_1k_tokens = {
            "gpt-4o": 0.03,
            "gpt-4o-mini": 0.00015,  # 200x cheaper!
            "gpt-3.5-turbo": 0.0015,
        }
        self.model = "gpt-4o-mini"  # Cost-effective model
    
    def add_usage(self, tokens: int, model: str = None):
        """Add token usage to cost tracking."""
        self.total_tokens += tokens
        model = model or self.model
        if model in self.cost_per_1k_tokens:
            cost = (tokens / 1000) * self.cost_per_1k_tokens[model]
            self.total_cost += cost
            logger.info(f"💰 Cost: ${cost:.6f} for {tokens} tokens ({model})")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "model": self.model,
            "cost_per_1k": self.cost_per_1k_tokens[self.model]
        }
    
    def print_summary(self):
        """Print cost summary."""
        summary = self.get_summary()
        logger.info("=" * 60)
        logger.info("💰 COST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total tokens used: {summary['total_tokens']:,}")
        logger.info(f"Total cost: ${summary['total_cost']:.6f}")
        logger.info(f"Model: {summary['model']}")
        logger.info(f"Cost per 1K tokens: ${summary['cost_per_1k']:.6f}")
        logger.info("=" * 60)


async def test_cost_effective_openrouter():
    """Test OpenRouter with cost optimization."""
    logger.info("=" * 80)
    logger.info("💰 COST-EFFECTIVE OPENROUTER DEVELOPMENT TEST")
    logger.info("=" * 80)
    
    # Initialize cost tracker
    cost_tracker = CostTracker()
    
    try:
        # Test 1: Enhanced domain research (cost-optimized)
        logger.info("\n1️⃣  Cost-Optimized Domain Research")
        logger.info("-" * 50)
        
        from activity.openai_enhanced import enhanced_domain_research_activity
        
        research_input = {
            "domain_name": "Architect Isac Gustav Clason",
            "domain_description": "Swedish architect and pioneer of National Romanticism",
            "initial_topics": ["architecture", "swedish history", "national romanticism"],
            "target_audience": ["architecture students", "historians"],
            "research_focus": "Architectural heritage and cultural significance",
            "research_depth": "comprehensive",
            "include_historical": True,
            "include_technical": True,
            "include_practical": True,
        }
        
        logger.info("🔍 Starting cost-optimized research...")
        result = await enhanced_domain_research_activity(research_input)
        
        # Estimate cost (approximate)
        estimated_tokens = len(json.dumps(result)) * 1.3  # Rough estimate
        cost_tracker.add_usage(int(estimated_tokens))
        
        logger.info("✅ Cost-optimized research completed")
        logger.info(f"📊 Summary: {result['summary'][:100]}...")
        logger.info(f"🏷️  Topics: {len(result['topics'])} topics")
        
        # Test 2: Continuous research (cost-optimized)
        logger.info("\n2️⃣  Cost-Optimized Continuous Research")
        logger.info("-" * 50)
        
        from activity.openai_enhanced import continuous_research_activity
        
        continuous_result = await continuous_research_activity(
            "Architect Isac Gustav Clason",
            "Historical development",
            []
        )
        
        # Estimate cost
        estimated_tokens = len(json.dumps(continuous_result)) * 1.3
        cost_tracker.add_usage(int(estimated_tokens))
        
        logger.info("✅ Cost-optimized continuous research completed")
        logger.info(f"💡 New insights: {len(continuous_result.get('new_insights', []))}")
        
        # Test 3: Deep analysis (cost-optimized)
        logger.info("\n3️⃣  Cost-Optimized Deep Analysis")
        logger.info("-" * 50)
        
        from activity.openai_enhanced import deep_question_analysis_activity
        
        question = "What are the fundamental principles of Architect Isac Gustav Clason's architectural style?"
        domain_context = {
            "domain_name": "Architect Isac Gustav Clason",
            "domain_description": "Swedish architect and pioneer of National Romanticism",
            "research_summary": result.get("summary", ""),
            "topics": result.get("topics", []),
            "continuous_insights": continuous_result.get("new_insights", [])
        }
        
        deep_analysis = await deep_question_analysis_activity(
            question,
            domain_context,
            "comprehensive"
        )
        
        # Estimate cost
        estimated_tokens = len(json.dumps(deep_analysis)) * 1.3
        cost_tracker.add_usage(int(estimated_tokens))
        
        logger.info("✅ Cost-optimized deep analysis completed")
        logger.info(f"📝 Answer: {deep_analysis.get('answer', '')[:100]}...")
        logger.info(f"📊 Confidence: {deep_analysis.get('confidence', 0)}")
        
        # Print cost summary
        cost_tracker.print_summary()
        
        # Cost comparison
        logger.info("\n💡 COST COMPARISON")
        logger.info("-" * 50)
        logger.info("Using gpt-4o-mini vs gpt-4o:")
        logger.info(f"  gpt-4o-mini: ${cost_tracker.total_cost:.6f}")
        gpt4o_cost = (cost_tracker.total_tokens / 1000) * 0.03
        logger.info(f"  gpt-4o:      ${gpt4o_cost:.6f}")
        savings = gpt4o_cost - cost_tracker.total_cost
        logger.info(f"  Savings:     ${savings:.6f} ({savings/gpt4o_cost*100:.1f}% cheaper)")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 COST-EFFECTIVE DEVELOPMENT TEST SUCCESSFUL!")
        logger.info("=" * 80)
        logger.info("💰 Your OpenRouter API key is optimized for budget development!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


async def test_budget_limits():
    """Test with budget limits to prevent overspending."""
    logger.info("\n🔒 BUDGET LIMIT TEST")
    logger.info("-" * 50)
    
    # Set budget limit (e.g., $0.01 for development)
    budget_limit = 0.01
    cost_tracker = CostTracker()
    
    logger.info(f"Budget limit: ${budget_limit}")
    
    # Simulate multiple API calls
    for i in range(5):
        # Simulate token usage
        tokens = 500  # Small requests
        cost_tracker.add_usage(tokens)
        
        if cost_tracker.total_cost > budget_limit:
            logger.warning(f"⚠️  Budget limit reached after {i+1} calls!")
            break
        
        logger.info(f"Call {i+1}: ${cost_tracker.total_cost:.6f} / ${budget_limit}")
    
    cost_tracker.print_summary()


async def main():
    """Main development test."""
    await test_cost_effective_openrouter()
    await test_budget_limits()


if __name__ == "__main__":
    asyncio.run(main())
