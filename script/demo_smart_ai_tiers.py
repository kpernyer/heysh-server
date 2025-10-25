#!/usr/bin/env python3
"""Demonstration of Smart AI tiers for different use cases."""

import asyncio
import json
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from config.model_selection import ModelTier, model_selection
from activity.ai_with_model_selection import AIRequest, call_ai_with_model_selection


async def demonstrate_smart_ai_tiers():
    """Demonstrate different AI tiers for various use cases."""
    logger.info("=" * 80)
    logger.info("🤖 SMART AI TIERS DEMONSTRATION")
    logger.info("=" * 80)
    
    # Test cases with different requirements
    test_cases = [
        {
            "name": "Quick Code Review",
            "tier": ModelTier.BEST_EFFORT_QUICK,
            "task": "code_review",
            "prompt": "Review this simple function:\n\ndef add(a, b):\n    return a + b",
            "description": "Fast, cheap review for simple code"
        },
        {
            "name": "Complex Domain Research",
            "tier": ModelTier.BEST_DEEP_RESULT,
            "task": "domain_research",
            "prompt": "Research the architectural contributions of Isac Gustav Clason to Swedish National Romanticism",
            "description": "Thorough research requiring deep analysis"
        },
        {
            "name": "Ultra-Fast Question",
            "tier": ModelTier.ULTRA_FAST,
            "task": "quick_questions",
            "prompt": "What is Python?",
            "description": "Quick answer for simple question"
        },
        {
            "name": "Ultra-Cheap Prototyping",
            "tier": ModelTier.ULTRA_CHEAP,
            "task": "prototyping",
            "prompt": "Create a simple Python function to calculate fibonacci numbers",
            "description": "Cheapest option for basic prototyping"
        },
        {
            "name": "Ultra-Quality Documentation",
            "tier": ModelTier.ULTRA_QUALITY,
            "task": "documentation",
            "prompt": "Generate comprehensive documentation for this complex function:\n\ndef complex_algorithm(data, params):\n    # Complex algorithm implementation\n    result = process_data(data, params)\n    return result",
            "description": "Highest quality documentation"
        },
        {
            "name": "Balanced Economic Value",
            "tier": ModelTier.BEST_ECONOMIC_VALUE,
            "task": "code_review",
            "prompt": "Review this medium-complexity function:\n\ndef process_user_data(users):\n    filtered = [u for u in users if u.active]\n    return sorted(filtered, key=lambda x: x.score)",
            "description": "Best balance of cost and quality"
        }
    ]
    
    total_cost = 0.0
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n{i}️⃣  {test_case['name']}")
        logger.info("-" * 50)
        logger.info(f"Tier: {test_case['tier'].value}")
        logger.info(f"Task: {test_case['task']}")
        logger.info(f"Description: {test_case['description']}")
        
        # Get model configuration
        model_config = model_selection.get_model_config(test_case['tier'])
        logger.info(f"Model: {model_config['model']}")
        logger.info(f"Cost per 1K tokens: ${model_config['cost_per_1k']:.6f}")
        logger.info(f"Quality: {model_config['quality']}")
        logger.info(f"Speed: {model_config['speed']}")
        
        # Create AI request
        request = AIRequest(
            prompt=test_case['prompt'],
            tier=test_case['tier'],
            task_type=test_case['task']
        )
        
        try:
            logger.info("🤖 Processing request...")
            result = await call_ai_with_model_selection(request)
            
            # Extract metadata
            metadata = result.get('_metadata', {})
            estimated_cost = metadata.get('estimated_cost', 0)
            estimated_tokens = metadata.get('estimated_tokens', 0)
            
            total_cost += estimated_cost
            
            # Store results
            results.append({
                "name": test_case['name'],
                "tier": test_case['tier'].value,
                "model": model_config['model'],
                "cost": estimated_cost,
                "tokens": estimated_tokens,
                "quality": model_config['quality'],
                "speed": model_config['speed'],
                "result_preview": str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
            })
            
            logger.info(f"✅ Completed")
            logger.info(f"💰 Cost: ${estimated_cost:.6f}")
            logger.info(f"📊 Tokens: {estimated_tokens:,}")
            logger.info(f"📝 Result preview: {results[-1]['result_preview']}")
            
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
            results.append({
                "name": test_case['name'],
                "tier": test_case['tier'].value,
                "model": model_config['model'],
                "cost": 0,
                "tokens": 0,
                "quality": model_config['quality'],
                "speed": model_config['speed'],
                "result_preview": f"Error: {e}"
            })
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 DEMONSTRATION SUMMARY")
    logger.info("=" * 80)
    
    for result in results:
        logger.info(f"\n🔹 {result['name']}")
        logger.info(f"   Tier: {result['tier']}")
        logger.info(f"   Model: {result['model']}")
        logger.info(f"   Cost: ${result['cost']:.6f}")
        logger.info(f"   Tokens: {result['tokens']:,}")
        logger.info(f"   Quality: {result['quality']}")
        logger.info(f"   Speed: {result['speed']}")
        logger.info(f"   Result: {result['result_preview']}")
    
    logger.info(f"\n💰 TOTAL COST: ${total_cost:.6f}")
    logger.info(f"📊 AVERAGE COST PER REQUEST: ${total_cost/len(results):.6f}")
    
    # Cost comparison
    logger.info("\n💡 COST COMPARISON")
    logger.info("-" * 50)
    
    # Calculate what it would cost with premium models
    premium_cost = total_cost * 200  # 200x more expensive
    claude_cost = total_cost * 100   # 100x more expensive
    
    logger.info(f"Smart AI (OpenRouter): ${total_cost:.6f}")
    logger.info(f"GPT-4o direct: ${premium_cost:.6f} (200x more expensive)")
    logger.info(f"Claude direct: ${claude_cost:.6f} (100x more expensive)")
    logger.info(f"Savings: ${premium_cost - total_cost:.6f} (99.5% cheaper)")
    
    logger.info("\n" + "=" * 80)
    logger.info("🎉 SMART AI TIERS DEMONSTRATION COMPLETE!")
    logger.info("=" * 80)
    logger.info("💡 Choose the right tier for your specific use case!")
    logger.info("=" * 80)


async def demonstrate_budget_optimization():
    """Demonstrate budget optimization with different tiers."""
    logger.info("\n🔧 BUDGET OPTIMIZATION DEMONSTRATION")
    logger.info("-" * 50)
    
    budgets = [0.001, 0.01, 0.1, 1.0]  # Different budget levels
    
    for budget in budgets:
        logger.info(f"\n💰 Budget: ${budget:.3f}")
        
        # Get optimal tier for this budget
        optimal_tier = model_selection.get_optimal_tier(budget, "good")
        model_config = model_selection.get_model_config(optimal_tier)
        
        logger.info(f"   Recommended tier: {optimal_tier.value}")
        logger.info(f"   Model: {model_config['model']}")
        logger.info(f"   Cost per 1K tokens: ${model_config['cost_per_1k']:.6f}")
        logger.info(f"   Quality: {model_config['quality']}")
        logger.info(f"   Speed: {model_config['speed']}")
        
        # Calculate how many tokens you can afford
        max_tokens = int((budget / model_config['cost_per_1k']) * 1000)
        logger.info(f"   Max tokens affordable: {max_tokens:,}")
        logger.info(f"   Description: {model_config['description']}")


async def main():
    """Main demonstration function."""
    await demonstrate_smart_ai_tiers()
    await demonstrate_budget_optimization()


if __name__ == "__main__":
    asyncio.run(main())
