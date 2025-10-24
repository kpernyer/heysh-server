"""Model selection system with quality tiers for different use cases."""

import os
from enum import Enum
from typing import Dict, Any, Optional


class ModelTier(str, Enum):
    """Model quality tiers for different use cases."""
    BEST_EFFORT_QUICK = "best-effort-quick"      # Fast, cheap, good enough
    BEST_ECONOMIC_VALUE = "best-economic-value"  # Best balance of cost/quality
    BEST_DEEP_RESULT = "best-deep-result"        # Highest quality, more expensive
    ULTRA_FAST = "ultra-fast"                    # Fastest possible
    ULTRA_CHEAP = "ultra-cheap"                  # Cheapest possible
    ULTRA_QUALITY = "ultra-quality"              # Highest quality possible


class ModelSelection:
    """Model selection system with quality tiers."""
    
    def __init__(self):
        """Initialize model selection system."""
        self.api_key = os.getenv("OPEN_ROUTER_API_KEY", "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")
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Model configurations for different tiers
        self.model_configs = {
            ModelTier.BEST_EFFORT_QUICK: {
                "model": "gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 1000,
                "cost_per_1k": 0.00015,
                "speed": "fast",
                "quality": "good",
                "description": "Fast, cheap, good enough for most tasks"
            },
            ModelTier.BEST_ECONOMIC_VALUE: {
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "max_tokens": 1500,
                "cost_per_1k": 0.00015,
                "speed": "fast",
                "quality": "very_good",
                "description": "Best balance of cost and quality"
            },
            ModelTier.BEST_DEEP_RESULT: {
                "model": "gpt-4o",
                "temperature": 0.1,
                "max_tokens": 4000,
                "cost_per_1k": 0.03,
                "speed": "medium",
                "quality": "excellent",
                "description": "High quality results for complex tasks"
            },
            ModelTier.ULTRA_FAST: {
                "model": "gpt-3.5-turbo",
                "temperature": 0.1,
                "max_tokens": 500,
                "cost_per_1k": 0.0015,
                "speed": "ultra_fast",
                "quality": "basic",
                "description": "Fastest possible response"
            },
            ModelTier.ULTRA_CHEAP: {
                "model": "gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 500,
                "cost_per_1k": 0.00015,
                "speed": "fast",
                "quality": "good",
                "description": "Cheapest possible option"
            },
            ModelTier.ULTRA_QUALITY: {
                "model": "gpt-4o",
                "temperature": 0.05,
                "max_tokens": 8000,
                "cost_per_1k": 0.03,
                "speed": "slow",
                "quality": "exceptional",
                "description": "Highest quality possible"
            }
        }
        
        # Task-specific recommendations
        self.task_recommendations = {
            "code_completion": ModelTier.BEST_EFFORT_QUICK,
            "code_review": ModelTier.BEST_ECONOMIC_VALUE,
            "debugging": ModelTier.BEST_EFFORT_QUICK,
            "refactoring": ModelTier.BEST_ECONOMIC_VALUE,
            "documentation": ModelTier.BEST_ECONOMIC_VALUE,
            "domain_research": ModelTier.BEST_DEEP_RESULT,
            "complex_analysis": ModelTier.BEST_DEEP_RESULT,
            "quick_questions": ModelTier.ULTRA_FAST,
            "prototyping": ModelTier.ULTRA_CHEAP,
            "production_code": ModelTier.BEST_ECONOMIC_VALUE,
            "research_paper": ModelTier.ULTRA_QUALITY,
            "creative_writing": ModelTier.BEST_DEEP_RESULT,
            "data_analysis": ModelTier.BEST_ECONOMIC_VALUE,
            "testing": ModelTier.BEST_EFFORT_QUICK,
            "deployment": ModelTier.BEST_ECONOMIC_VALUE
        }
    
    def get_model_config(self, tier: ModelTier) -> Dict[str, Any]:
        """Get model configuration for a specific tier."""
        return self.model_configs.get(tier, self.model_configs[ModelTier.BEST_ECONOMIC_VALUE])
    
    def get_recommended_tier(self, task: str) -> ModelTier:
        """Get recommended tier for a specific task."""
        return self.task_recommendations.get(task, ModelTier.BEST_ECONOMIC_VALUE)
    
    def estimate_cost(self, tier: ModelTier, tokens: int) -> float:
        """Estimate cost for given tier and token count."""
        config = self.get_model_config(tier)
        return (tokens / 1000) * config["cost_per_1k"]
    
    def get_tier_comparison(self) -> Dict[str, Any]:
        """Get comparison of all tiers."""
        comparison = {}
        for tier, config in self.model_configs.items():
            comparison[tier.value] = {
                "model": config["model"],
                "cost_per_1k": config["cost_per_1k"],
                "speed": config["speed"],
                "quality": config["quality"],
                "description": config["description"]
            }
        return comparison
    
    def get_optimal_tier(self, budget: float, quality_requirement: str = "good") -> ModelTier:
        """Get optimal tier based on budget and quality requirements."""
        if budget < 0.001:  # Very low budget
            return ModelTier.ULTRA_CHEAP
        elif budget < 0.01:  # Low budget
            return ModelTier.BEST_EFFORT_QUICK
        elif budget < 0.1:  # Medium budget
            return ModelTier.BEST_ECONOMIC_VALUE
        elif quality_requirement == "exceptional":
            return ModelTier.ULTRA_QUALITY
        else:
            return ModelTier.BEST_DEEP_RESULT
    
    def get_client_config(self, tier: ModelTier) -> Dict[str, Any]:
        """Get OpenAI client configuration for a specific tier."""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "default_headers": {
                "HTTP-Referer": "https://hey.sh"
            }
        }
    
    def get_request_config(self, tier: ModelTier) -> Dict[str, Any]:
        """Get request configuration for a specific tier."""
        config = self.get_model_config(tier)
        return {
            "model": config["model"],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"],
            "stream": True
        }


# Global model selection instance
model_selection = ModelSelection()
