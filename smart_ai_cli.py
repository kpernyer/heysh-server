#!/usr/bin/env python3
"""Smart AI CLI with model selection based on quality tiers."""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from config.model_selection import ModelSelection, ModelTier, model_selection
from activity.ai_with_model_selection import AIRequest, call_ai_with_model_selection


class SmartAICLI:
    """Smart AI CLI with model selection."""
    
    def __init__(self):
        """Initialize Smart AI CLI."""
        self.model_selection = model_selection
    
    def show_help(self):
        """Show help information."""
        print("""
🤖 Smart AI CLI with Model Selection

USAGE:
    python smart_ai_cli.py <tier> <task> [options]

MODEL TIERS:
    --best-effort-quick      Fast, cheap, good enough
    --best-economic-value    Best balance of cost/quality (default)
    --best-deep-result       High quality, more expensive
    --ultra-fast            Fastest possible
    --ultra-cheap           Cheapest possible
    --ultra-quality         Highest quality possible

TASK TYPES:
    domain_research         Domain research and analysis
    code_review            Code review and analysis
    documentation          Documentation generation
    debugging              Debug and fix issues
    refactoring            Code refactoring
    testing                Test generation
    deployment             Deployment assistance

EXAMPLES:
    # Quick domain research (fast, cheap)
    python smart_ai_cli.py --best-effort-quick domain_research "Architect Isac Gustav Clason"
    
    # High-quality code analysis (expensive but thorough)
    python smart_ai_cli.py --best-deep-result code_review "def complex_function(): ..."
    
    # Ultra-fast quick question
    python smart_ai_cli.py --ultra-fast quick_question "What is Python?"
    
    # Ultra-cheap prototyping
    python smart_ai_cli.py --ultra-cheap prototyping "Create a simple API"
    
    # Ultra-quality research paper
    python smart_ai_cli.py --ultra-quality research_paper "Comprehensive analysis of AI ethics"

OPTIONS:
    --budget <amount>       Set budget limit (e.g., 0.01 for 1 cent)
    --interactive          Interactive mode
    --compare              Compare all tiers
    --help                 Show this help
        """)
    
    def show_tier_comparison(self):
        """Show comparison of all tiers."""
        print("\n📊 MODEL TIER COMPARISON")
        print("=" * 80)
        
        comparison = self.model_selection.get_tier_comparison()
        for tier, config in comparison.items():
            print(f"\n🔹 {tier.upper()}")
            print(f"   Model: {config['model']}")
            print(f"   Cost per 1K tokens: ${config['cost_per_1k']:.6f}")
            print(f"   Speed: {config['speed']}")
            print(f"   Quality: {config['quality']}")
            print(f"   Description: {config['description']}")
        
        print("\n" + "=" * 80)
    
    def show_task_recommendations(self):
        """Show task recommendations."""
        print("\n🎯 TASK RECOMMENDATIONS")
        print("=" * 50)
        
        for task, tier in self.model_selection.task_recommendations.items():
            config = self.model_selection.get_model_config(tier)
            print(f"{task:20} → {tier.value:20} ({config['model']})")
        
        print("\n" + "=" * 50)
    
    async def run_interactive_mode(self):
        """Run interactive mode."""
        print("\n🤖 Smart AI Interactive Mode")
        print("=" * 40)
        
        while True:
            try:
                print("\nAvailable commands:")
                print("1. Ask a question")
                print("2. Analyze code")
                print("3. Generate documentation")
                print("4. Domain research")
                print("5. Show tier comparison")
                print("6. Show task recommendations")
                print("7. Exit")
                
                choice = input("\nEnter your choice (1-7): ").strip()
                
                if choice == "1":
                    await self.interactive_question()
                elif choice == "2":
                    await self.interactive_code_analysis()
                elif choice == "3":
                    await self.interactive_documentation()
                elif choice == "4":
                    await self.interactive_domain_research()
                elif choice == "5":
                    self.show_tier_comparison()
                elif choice == "6":
                    self.show_task_recommendations()
                elif choice == "7":
                    print("Goodbye! 👋")
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    async def interactive_question(self):
        """Interactive question mode."""
        question = input("\nEnter your question: ").strip()
        if not question:
            return
        
        print("\nSelect model tier:")
        print("1. Best effort quick (fast, cheap)")
        print("2. Best economic value (balanced)")
        print("3. Best deep result (thorough)")
        print("4. Ultra fast (fastest)")
        print("5. Ultra cheap (cheapest)")
        print("6. Ultra quality (best)")
        
        tier_choice = input("Enter tier (1-6): ").strip()
        tier_map = {
            "1": ModelTier.BEST_EFFORT_QUICK,
            "2": ModelTier.BEST_ECONOMIC_VALUE,
            "3": ModelTier.BEST_DEEP_RESULT,
            "4": ModelTier.ULTRA_FAST,
            "5": ModelTier.ULTRA_CHEAP,
            "6": ModelTier.ULTRA_QUALITY
        }
        
        tier = tier_map.get(tier_choice, ModelTier.BEST_ECONOMIC_VALUE)
        
        await self.process_question(question, tier)
    
    async def interactive_code_analysis(self):
        """Interactive code analysis mode."""
        print("\nEnter your code (end with 'EOF' on a new line):")
        code_lines = []
        while True:
            line = input()
            if line.strip() == "EOF":
                break
            code_lines.append(line)
        
        code = "\n".join(code_lines)
        if not code.strip():
            print("No code provided.")
            return
        
        tier = ModelTier.BEST_ECONOMIC_VALUE  # Default for code analysis
        await self.process_code_analysis(code, tier)
    
    async def interactive_documentation(self):
        """Interactive documentation mode."""
        print("\nEnter your code (end with 'EOF' on a new line):")
        code_lines = []
        while True:
            line = input()
            if line.strip() == "EOF":
                break
            code_lines.append(line)
        
        code = "\n".join(code_lines)
        if not code.strip():
            print("No code provided.")
            return
        
        tier = ModelTier.BEST_ECONOMIC_VALUE  # Default for documentation
        await self.process_documentation(code, tier)
    
    async def interactive_domain_research(self):
        """Interactive domain research mode."""
        domain_name = input("\nEnter domain name: ").strip()
        if not domain_name:
            return
        
        domain_description = input("Enter domain description: ").strip()
        if not domain_description:
            domain_description = f"Research domain: {domain_name}"
        
        tier = ModelTier.BEST_DEEP_RESULT  # Default for domain research
        await self.process_domain_research(domain_name, domain_description, tier)
    
    async def process_question(self, question: str, tier: ModelTier):
        """Process a question with specified tier."""
        print(f"\n🤖 Processing question with {tier.value}...")
        
        request = AIRequest(
            prompt=question,
            tier=tier,
            task_type="quick_questions"
        )
        
        try:
            result = await call_ai_with_model_selection(request)
            print(f"\n📝 Answer:")
            print(result.get("content", result))
            print(f"\n💰 Cost: ${result.get('_metadata', {}).get('estimated_cost', 0):.6f}")
        except Exception as e:
            print(f"Error: {e}")
    
    async def process_code_analysis(self, code: str, tier: ModelTier):
        """Process code analysis with specified tier."""
        print(f"\n🔍 Analyzing code with {tier.value}...")
        
        request = AIRequest(
            prompt=f"Analyze this code:\n\n```python\n{code}\n```",
            tier=tier,
            task_type="code_review"
        )
        
        try:
            result = await call_ai_with_model_selection(request)
            print(f"\n📊 Analysis Results:")
            print(json.dumps(result, indent=2))
            print(f"\n💰 Cost: ${result.get('_metadata', {}).get('estimated_cost', 0):.6f}")
        except Exception as e:
            print(f"Error: {e}")
    
    async def process_documentation(self, code: str, tier: ModelTier):
        """Process documentation generation with specified tier."""
        print(f"\n📚 Generating documentation with {tier.value}...")
        
        request = AIRequest(
            prompt=f"Generate documentation for this code:\n\n```python\n{code}\n```",
            tier=tier,
            task_type="documentation"
        )
        
        try:
            result = await call_ai_with_model_selection(request)
            print(f"\n📖 Documentation:")
            print(json.dumps(result, indent=2))
            print(f"\n💰 Cost: ${result.get('_metadata', {}).get('estimated_cost', 0):.6f}")
        except Exception as e:
            print(f"Error: {e}")
    
    async def process_domain_research(self, domain_name: str, domain_description: str, tier: ModelTier):
        """Process domain research with specified tier."""
        print(f"\n🔬 Researching domain with {tier.value}...")
        
        request = AIRequest(
            prompt=f"""
            Perform comprehensive research for a new knowledge domain:
            Title: {domain_name}
            Description: {domain_description}
            
            Provide research results in JSON format with:
            - summary: Comprehensive summary
            - topics: List of key topics
            - key_figures: Important people
            - historical_context: Brief overview
            - technical_aspects: Key concepts
            - practical_applications: Real-world uses
            - potential_challenges: Difficulties
            - recommended_sources: List of sources
            - recommendations_for_kb: KB suggestions
            """,
            tier=tier,
            task_type="domain_research"
        )
        
        try:
            result = await call_ai_with_model_selection(request)
            print(f"\n📊 Research Results:")
            print(json.dumps(result, indent=2))
            print(f"\n💰 Cost: ${result.get('_metadata', {}).get('estimated_cost', 0):.6f}")
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage: python smart_ai_cli.py <command> [options]")
        print("Use --help for more information")
        return
    
    cli = SmartAICLI()
    
    if "--help" in sys.argv or "-h" in sys.argv:
        cli.show_help()
        return
    
    if "--compare" in sys.argv:
        cli.show_tier_comparison()
        return
    
    if "--interactive" in sys.argv:
        await cli.run_interactive_mode()
        return
    
    # Parse command line arguments
    tier = ModelTier.BEST_ECONOMIC_VALUE
    task = None
    prompt = None
    budget_limit = None
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith("--"):
            if arg == "--best-effort-quick":
                tier = ModelTier.BEST_EFFORT_QUICK
            elif arg == "--best-economic-value":
                tier = ModelTier.BEST_ECONOMIC_VALUE
            elif arg == "--best-deep-result":
                tier = ModelTier.BEST_DEEP_RESULT
            elif arg == "--ultra-fast":
                tier = ModelTier.ULTRA_FAST
            elif arg == "--ultra-cheap":
                tier = ModelTier.ULTRA_CHEAP
            elif arg == "--ultra-quality":
                tier = ModelTier.ULTRA_QUALITY
            elif arg == "--budget":
                if i + 1 < len(sys.argv):
                    budget_limit = float(sys.argv[i + 1])
        else:
            if not task:
                task = arg
            elif not prompt:
                prompt = arg
    
    if not task or not prompt:
        print("Error: Task and prompt are required")
        print("Use --help for more information")
        return
    
    # Process the request
    request = AIRequest(
        prompt=prompt,
        tier=tier,
        task_type=task,
        budget_limit=budget_limit
    )
    
    try:
        result = await call_ai_with_model_selection(request)
        print(f"\n📝 Result:")
        print(json.dumps(result, indent=2))
        print(f"\n💰 Cost: ${result.get('_metadata', {}).get('estimated_cost', 0):.6f}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
