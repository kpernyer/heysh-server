"""AI activities with intelligent model selection based on quality tiers."""

import json
import os
import re
from typing import Any, Dict, List, Optional

import structlog
from temporalio import activity

from config.model_selection import ModelSelection, ModelTier, model_selection

logger = structlog.get_logger()


class AIRequest:
    """AI request with model selection."""
    
    def __init__(
        self,
        prompt: str,
        tier: ModelTier = ModelTier.BEST_ECONOMIC_VALUE,
        task_type: Optional[str] = None,
        budget_limit: Optional[float] = None
    ):
        """Initialize AI request."""
        self.prompt = prompt
        self.tier = tier
        self.task_type = task_type
        self.budget_limit = budget_limit
        
        # Auto-select tier if task_type is provided
        if task_type and tier == ModelTier.BEST_ECONOMIC_VALUE:
            self.tier = model_selection.get_recommended_tier(task_type)
        
        # Auto-select tier if budget_limit is provided
        if budget_limit and tier == ModelTier.BEST_ECONOMIC_VALUE:
            quality_req = "good" if budget_limit < 0.01 else "excellent"
            self.tier = model_selection.get_optimal_tier(budget_limit, quality_req)
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration for this request."""
        return model_selection.get_model_config(self.tier)
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for this request."""
        return model_selection.estimate_cost(self.tier, tokens)


async def call_ai_with_model_selection(
    request: AIRequest,
    system_prompt: str = "You are a helpful AI assistant.",
    stream_callback: Optional[Any] = None
) -> Dict[str, Any]:
    """Call AI with intelligent model selection."""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise RuntimeError("OpenAI client not installed or available.")
    
    # Get model configuration
    model_config = request.get_model_config()
    client_config = model_selection.get_client_config(request.tier)
    request_config = model_selection.get_request_config(request.tier)
    
    # Initialize client
    client = AsyncOpenAI(**client_config)
    
    # Log model selection
    activity.logger.info(
        f"Using model tier: {request.tier.value} - Model: {model_config['model']} - Cost: ${model_config['cost_per_1k']:.6f}/1K - Quality: {model_config['quality']} - Speed: {model_config['speed']}"
    )
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.prompt}
    ]
    
    try:
        # Make API call
        response = await client.chat.completions.create(
            model=request_config["model"],
            messages=messages,
            temperature=request_config["temperature"],
            max_tokens=request_config["max_tokens"],
            stream=request_config["stream"]
        )
        
        # Process response
        if request_config["stream"]:
            full_content = ""
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content_part = chunk.choices[0].delta.content
                    full_content += content_part
                    if stream_callback:
                        await stream_callback(content_part)
            
            # Try to parse as JSON
            try:
                result = json.loads(full_content)
            except json.JSONDecodeError:
                # Extract JSON if response is not pure JSON
                json_match = re.search(r'\{.*\}', full_content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {"content": full_content, "raw_response": True}
        else:
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {"content": content, "raw_response": True}
        
        # Estimate cost
        estimated_tokens = len(json.dumps(result)) * 1.3
        estimated_cost = request.estimate_cost(int(estimated_tokens))
        
        # Add metadata
        result["_metadata"] = {
            "tier": request.tier.value,
            "model": model_config["model"],
            "estimated_tokens": int(estimated_tokens),
            "estimated_cost": estimated_cost,
            "quality": model_config["quality"],
            "speed": model_config["speed"]
        }
        
        activity.logger.info(
            f"AI request completed - Tier: {request.tier.value} - Cost: ${estimated_cost:.6f} - Quality: {model_config['quality']}"
        )
        
        return result
        
    except Exception as e:
        activity.logger.error(f"AI request failed: {e}")
        raise RuntimeError(f"AI request failed: {e}") from e


@activity.defn
async def smart_domain_research_activity(
    domain_name: str,
    domain_description: str,
    tier: str = "best-economic-value",
    task_type: str = "domain_research",
    budget_limit: Optional[float] = None
) -> Dict[str, Any]:
    """Smart domain research with model selection."""
    activity.logger.info(f"Starting smart domain research: {domain_name}")
    
    # Create AI request with model selection
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
        tier=ModelTier(tier),
        task_type=task_type,
        budget_limit=budget_limit
    )
    
    system_prompt = """You are an expert knowledge domain researcher. Provide comprehensive, structured research results in JSON format."""
    
    try:
        result = await call_ai_with_model_selection(request, system_prompt)
        activity.logger.info(f"Smart domain research completed: {domain_name}")
        return result
    except Exception as e:
        activity.logger.error(f"Smart domain research failed: {e}")
        # Fallback to mock research
        return await mock_smart_research(domain_name, domain_description)


@activity.defn
async def smart_code_analysis_activity(
    code: str,
    analysis_type: str = "code_review",
    tier: str = "best-economic-value",
    budget_limit: Optional[float] = None
) -> Dict[str, Any]:
    """Smart code analysis with model selection."""
    activity.logger.info(f"Starting smart code analysis: {analysis_type}")
    
    # Create AI request with model selection
    request = AIRequest(
        prompt=f"""
        Analyze the following code for {analysis_type}:
        
        ```python
        {code}
        ```
        
        Provide analysis in JSON format with:
        - issues: List of issues found
        - suggestions: Improvement suggestions
        - quality_score: Overall quality (0-10)
        - complexity: Complexity assessment
        - maintainability: Maintainability score
        - performance: Performance considerations
        - security: Security concerns
        - best_practices: Best practice violations
        """,
        tier=ModelTier(tier),
        task_type=analysis_type,
        budget_limit=budget_limit
    )
    
    system_prompt = """You are an expert code reviewer and software engineer. Provide detailed, actionable analysis in JSON format."""
    
    try:
        result = await call_ai_with_model_selection(request, system_prompt)
        activity.logger.info(f"Smart code analysis completed: {analysis_type}")
        return result
    except Exception as e:
        activity.logger.error(f"Smart code analysis failed: {e}")
        # Fallback to mock analysis
        return await mock_smart_code_analysis(code, analysis_type)


@activity.defn
async def smart_documentation_activity(
    code: str,
    doc_type: str = "documentation",
    tier: str = "best-economic-value",
    budget_limit: Optional[float] = None
) -> Dict[str, Any]:
    """Smart documentation generation with model selection."""
    activity.logger.info(f"Starting smart documentation: {doc_type}")
    
    # Create AI request with model selection
    request = AIRequest(
        prompt=f"""
        Generate {doc_type} for the following code:
        
        ```python
        {code}
        ```
        
        Provide documentation in JSON format with:
        - docstring: Function/class docstring
        - comments: Inline comments
        - examples: Usage examples
        - parameters: Parameter descriptions
        - returns: Return value descriptions
        - raises: Exception descriptions
        - notes: Additional notes
        """,
        tier=ModelTier(tier),
        task_type="documentation",
        budget_limit=budget_limit
    )
    
    system_prompt = """You are an expert technical writer. Generate clear, comprehensive documentation in JSON format."""
    
    try:
        result = await call_ai_with_model_selection(request, system_prompt)
        activity.logger.info(f"Smart documentation completed: {doc_type}")
        return result
    except Exception as e:
        activity.logger.error(f"Smart documentation failed: {e}")
        # Fallback to mock documentation
        return await mock_smart_documentation(code, doc_type)


# Mock functions for fallback
async def mock_smart_research(domain_name: str, domain_description: str) -> Dict[str, Any]:
    """Mock smart research fallback."""
    activity.logger.warning("Using mock smart research")
    return {
        "summary": f"Mock research summary for {domain_name}",
        "topics": [f"{domain_name} fundamentals", f"{domain_name} applications"],
        "key_figures": [f"Figure A in {domain_name}"],
        "historical_context": f"Brief historical overview of {domain_name}",
        "technical_aspects": f"Key technical concepts related to {domain_name}",
        "practical_applications": f"Practical applications of {domain_name}",
        "potential_challenges": f"Potential challenges in {domain_name}",
        "recommended_sources": [f"https://example.com/{domain_name}-source"],
        "recommendations_for_kb": [f"Focus on {domain_name} fundamentals"],
        "_metadata": {
            "tier": "mock",
            "model": "mock",
            "estimated_tokens": 100,
            "estimated_cost": 0.0,
            "quality": "mock",
            "speed": "instant"
        }
    }


async def mock_smart_code_analysis(code: str, analysis_type: str) -> Dict[str, Any]:
    """Mock smart code analysis fallback."""
    activity.logger.warning("Using mock smart code analysis")
    return {
        "issues": ["Mock issue 1", "Mock issue 2"],
        "suggestions": ["Mock suggestion 1", "Mock suggestion 2"],
        "quality_score": 7.5,
        "complexity": "medium",
        "maintainability": "good",
        "performance": "acceptable",
        "security": "no major concerns",
        "best_practices": ["Follow PEP 8", "Add type hints"],
        "_metadata": {
            "tier": "mock",
            "model": "mock",
            "estimated_tokens": 50,
            "estimated_cost": 0.0,
            "quality": "mock",
            "speed": "instant"
        }
    }


async def mock_smart_documentation(code: str, doc_type: str) -> Dict[str, Any]:
    """Mock smart documentation fallback."""
    activity.logger.warning("Using mock smart documentation")
    return {
        "docstring": f"Mock {doc_type} for the provided code",
        "comments": ["Mock comment 1", "Mock comment 2"],
        "examples": ["Mock example 1", "Mock example 2"],
        "parameters": {"param1": "Mock parameter description"},
        "returns": "Mock return description",
        "raises": ["MockException: Mock exception description"],
        "notes": ["Mock note 1", "Mock note 2"],
        "_metadata": {
            "tier": "mock",
            "model": "mock",
            "estimated_tokens": 75,
            "estimated_cost": 0.0,
            "quality": "mock",
            "speed": "instant"
        }
    }
