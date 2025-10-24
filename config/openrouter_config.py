"""OpenRouter configuration for cost-effective development."""

import os
from typing import Dict, Any


class OpenRouterConfig:
    """Configuration for OpenRouter API usage with cost optimization."""
    
    def __init__(self):
        """Initialize OpenRouter configuration."""
        self.api_key = os.getenv("OPEN_ROUTER_API_KEY", "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")
        self.base_url = "https://openrouter.ai/api/v1"
        self.http_referer = "https://hey.sh"
        
        # Cost optimization settings
        self.model = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")  # Much cheaper than gpt-4o
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "1000"))  # Limit tokens
        self.temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.1"))  # Lower temperature
        
        # Development mode settings
        self.dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"
        self.mock_fallback = os.getenv("MOCK_AI_FALLBACK", "true").lower() == "true"
        
        # Cost tracking
        self.cost_per_1k_tokens = {
            "gpt-4o": 0.03,  # $0.03 per 1K tokens
            "gpt-4o-mini": 0.00015,  # $0.00015 per 1K tokens (200x cheaper!)
            "gpt-3.5-turbo": 0.0015,  # $0.0015 per 1K tokens
        }
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get OpenAI client configuration for OpenRouter."""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "default_headers": {
                "HTTP-Referer": self.http_referer
            }
        }
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration optimized for cost."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True  # Enable streaming for real-time feedback
        }
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for given number of tokens."""
        if self.model in self.cost_per_1k_tokens:
            return (tokens / 1000) * self.cost_per_1k_tokens[self.model]
        return 0.0
    
    def is_cost_effective(self) -> bool:
        """Check if current configuration is cost-effective."""
        return self.model == "gpt-4o-mini" and self.max_tokens <= 1000
    
    def get_optimization_tips(self) -> list[str]:
        """Get tips for cost optimization."""
        tips = []
        
        if self.model != "gpt-4o-mini":
            tips.append("Switch to gpt-4o-mini for 200x cost reduction")
        
        if self.max_tokens > 1000:
            tips.append("Reduce max_tokens to 1000 for development")
        
        if self.temperature > 0.1:
            tips.append("Lower temperature to 0.1 for more focused responses")
        
        if not self.mock_fallback:
            tips.append("Enable mock_fallback for development")
        
        return tips


# Global configuration instance
openrouter_config = OpenRouterConfig()
