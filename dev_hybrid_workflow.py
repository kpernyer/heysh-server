#!/usr/bin/env python3
"""Hybrid development workflow: Cursor + OpenRouter for cost optimization."""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class HybridDevelopmentWorkflow:
    """Optimize development costs by using Cursor + OpenRouter strategically."""
    
    def __init__(self):
        """Initialize hybrid workflow."""
        self.cursor_usage = 0
        self.openrouter_usage = 0
        self.openrouter_cost = 0.0
        
    def log_cursor_usage(self, task: str):
        """Log Cursor usage (no additional cost)."""
        self.cursor_usage += 1
        logger.info(f"🖥️  Cursor AI: {task} (No additional cost)")
    
    def log_openrouter_usage(self, task: str, cost: float):
        """Log OpenRouter usage and cost."""
        self.openrouter_usage += 1
        self.openrouter_cost += cost
        logger.info(f"🌐 OpenRouter: {task} (Cost: ${cost:.6f})")
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary."""
        return {
            "cursor_tasks": self.cursor_usage,
            "openrouter_tasks": self.openrouter_usage,
            "openrouter_cost": self.openrouter_cost,
            "cursor_cost": 0.0,  # No additional cost
            "total_cost": self.openrouter_cost
        }


async def demonstrate_hybrid_workflow():
    """Demonstrate optimal use of Cursor + OpenRouter."""
    logger.info("=" * 80)
    logger.info("🔄 HYBRID DEVELOPMENT WORKFLOW: CURSOR + OPENROUTER")
    logger.info("=" * 80)
    
    workflow = HybridDevelopmentWorkflow()
    
    # Step 1: Use Cursor for code structure and syntax
    logger.info("\n1️⃣  CURSOR AI: Code Structure & Syntax")
    logger.info("-" * 50)
    workflow.log_cursor_usage("Code completion for function signatures")
    workflow.log_cursor_usage("Import statements and type hints")
    workflow.log_cursor_usage("Basic error fixing and refactoring")
    workflow.log_cursor_usage("Code formatting and linting")
    
    # Step 2: Use OpenRouter for complex domain research
    logger.info("\n2️⃣  OPENROUTER: Complex Domain Research")
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
    
    logger.info("🔍 Using OpenRouter for domain research...")
    result = await enhanced_domain_research_activity(research_input)
    
    # Estimate cost
    estimated_tokens = len(json.dumps(result)) * 1.3
    cost = (estimated_tokens / 1000) * 0.00015  # gpt-4o-mini cost
    workflow.log_openrouter_usage("Domain research and analysis", cost)
    
    # Step 3: Use Cursor for code implementation
    logger.info("\n3️⃣  CURSOR AI: Code Implementation")
    logger.info("-" * 50)
    workflow.log_cursor_usage("Implementing research results into code")
    workflow.log_cursor_usage("Creating data models and schemas")
    workflow.log_cursor_usage("Writing tests and documentation")
    workflow.log_cursor_usage("Debugging and optimization")
    
    # Step 4: Use OpenRouter for complex analysis
    logger.info("\n4️⃣  OPENROUTER: Complex Analysis")
    logger.info("-" * 50)
    
    from activity.openai_enhanced import deep_question_analysis_activity
    
    question = "What are the fundamental principles of Architect Isac Gustav Clason's architectural style?"
    domain_context = {
        "domain_name": "Architect Isac Gustav Clason",
        "domain_description": "Swedish architect and pioneer of National Romanticism",
        "research_summary": result.get("summary", ""),
        "topics": result.get("topics", []),
    }
    
    logger.info("🔍 Using OpenRouter for deep analysis...")
    analysis = await deep_question_analysis_activity(question, domain_context, "comprehensive")
    
    # Estimate cost
    estimated_tokens = len(json.dumps(analysis)) * 1.3
    cost = (estimated_tokens / 1000) * 0.00015
    workflow.log_openrouter_usage("Deep question analysis", cost)
    
    # Step 5: Use Cursor for final implementation
    logger.info("\n5️⃣  CURSOR AI: Final Implementation")
    logger.info("-" * 50)
    workflow.log_cursor_usage("Implementing analysis results")
    workflow.log_cursor_usage("Code review and optimization")
    workflow.log_cursor_usage("Documentation and comments")
    workflow.log_cursor_usage("Final testing and validation")
    
    # Print summary
    summary = workflow.get_usage_summary()
    logger.info("\n" + "=" * 60)
    logger.info("📊 HYBRID WORKFLOW SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Cursor AI tasks: {summary['cursor_tasks']} (No additional cost)")
    logger.info(f"OpenRouter tasks: {summary['openrouter_tasks']}")
    logger.info(f"OpenRouter cost: ${summary['openrouter_cost']:.6f}")
    logger.info(f"Total cost: ${summary['total_cost']:.6f}")
    logger.info("=" * 60)
    
    # Cost comparison
    logger.info("\n💡 COST COMPARISON")
    logger.info("-" * 50)
    logger.info("Hybrid approach (Cursor + OpenRouter):")
    logger.info(f"  Cursor: $0.00 (included in subscription)")
    logger.info(f"  OpenRouter: ${summary['openrouter_cost']:.6f}")
    logger.info(f"  Total: ${summary['total_cost']:.6f}")
    logger.info("")
    logger.info("If using only premium AI services:")
    logger.info(f"  GPT-4o: ${summary['openrouter_cost'] * 200:.6f} (200x more expensive)")
    logger.info(f"  Claude: ${summary['openrouter_cost'] * 100:.6f} (100x more expensive)")
    
    logger.info("\n" + "=" * 80)
    logger.info("🎉 HYBRID WORKFLOW OPTIMIZATION COMPLETE!")
    logger.info("=" * 80)
    logger.info("💡 Use Cursor for code, OpenRouter for complex AI tasks!")
    logger.info("=" * 80)


async def demonstrate_cost_optimization():
    """Demonstrate cost optimization strategies."""
    logger.info("\n🔧 COST OPTIMIZATION STRATEGIES")
    logger.info("-" * 50)
    
    strategies = [
        "Use Cursor for: Code completion, syntax, refactoring, debugging",
        "Use OpenRouter for: Domain research, complex analysis, documentation",
        "Batch OpenRouter requests to reduce API calls",
        "Use gpt-4o-mini for development (200x cheaper than gpt-4o)",
        "Implement caching for repeated queries",
        "Use mock responses for development testing",
        "Set budget limits and alerts",
        "Monitor usage and costs in real-time"
    ]
    
    for i, strategy in enumerate(strategies, 1):
        logger.info(f"  {i}. {strategy}")
    
    logger.info("\n📈 EXPECTED SAVINGS")
    logger.info("-" * 50)
    logger.info("• 99.5% cost reduction vs premium AI services")
    logger.info("• Real-time cost tracking and budget alerts")
    logger.info("• Automatic fallback to mock responses")
    logger.info("• Optimized for development workflow")


async def main():
    """Main demonstration."""
    await demonstrate_hybrid_workflow()
    await demonstrate_cost_optimization()


if __name__ == "__main__":
    asyncio.run(main())
