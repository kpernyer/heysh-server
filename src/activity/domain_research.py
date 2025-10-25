"""Domain research activities for bootstrap workflow."""

import json
import os
from datetime import datetime
from typing import Any, Dict, List

import structlog
from temporalio import activity

logger = structlog.get_logger()


@activity.defn
async def research_domain_activity(research_input: Dict[str, Any]) -> Dict[str, Any]:
    """Research a domain using AI to discover topics, criteria, and knowledge base structure.
    
    This activity performs comprehensive research on a domain to bootstrap a knowledge base.
    It uses OpenAI to research the domain and discover relevant topics, quality criteria,
    and knowledge base structure.
    
    Args:
        research_input: Dictionary containing:
            - domain_name: Name of the domain
            - domain_description: Description of the domain
            - initial_topics: Initial topics provided by owner
            - target_audience: Target audience for the domain
            - research_focus: Specific research focus areas
            - research_depth: Research depth (basic, comprehensive, expert)
            - include_historical: Include historical research
            - include_technical: Include technical research
            - include_practical: Include practical applications
    
    Returns:
        Dictionary containing:
        - summary: Research summary
        - topics: Discovered topics
        - quality_criteria: Quality assessment criteria
        - knowledge_gaps: Identified knowledge gaps
        - sources: Research sources used
        - recommendations: Recommendations for domain setup
    """
    activity.logger.info(
        f"Starting domain research: {research_input['domain_name']}"
    )

    try:
        # Use OpenAI for comprehensive domain research
        research_result = await research_with_openai(research_input)
        
        activity.logger.info(
            f"Domain research completed: {research_input['domain_name']}"
        )
        
        return research_result
        
    except Exception as e:
        activity.logger.error(
            f"Domain research failed: {research_input['domain_name']}, error={e!s}"
        )
        raise


@activity.defn
async def analyze_research_results_activity(
    research_results: Dict[str, Any], 
    domain_name: str
) -> Dict[str, Any]:
    """Analyze research results to generate domain configuration.
    
    This activity analyzes the research results and generates domain-specific
    configuration including topics, quality criteria, and search attributes.
    
    Args:
        research_results: Results from domain research
        domain_name: Name of the domain
    
    Returns:
        Dictionary containing:
        - topics: Final topic list for domain
        - quality_criteria: Quality assessment criteria
        - search_attributes: Search attributes for workflows
        - bootstrap_prompt: Custom bootstrap prompt
        - research_steps: Research steps for domain
        - recommendations: Setup recommendations
    """
    activity.logger.info(f"Analyzing research results for: {domain_name}")

    try:
        # Use OpenAI to analyze research results
        analysis_result = await analyze_with_openai(research_results, domain_name)
        
        activity.logger.info(f"Research analysis completed: {domain_name}")
        
        return analysis_result
        
    except Exception as e:
        activity.logger.error(
            f"Research analysis failed: {domain_name}, error={e!s}"
        )
        raise


async def research_with_openai(research_input: Dict[str, Any]) -> Dict[str, Any]:
    """Research domain using OpenAI API."""
    try:
        # Import OpenAI client
        try:
            from openai import AsyncOpenAI
        except ImportError:
            activity.logger.warning("OpenAI client not available, using mock research")
            return await mock_domain_research(research_input)
        
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            activity.logger.warning("OPENAI_API_KEY not set, using mock research")
            return await mock_domain_research(research_input)
        
        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=api_key)
        
        # Create comprehensive research prompt
        research_prompt = create_research_prompt(research_input)
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": research_prompt["system"]},
                {"role": "user", "content": research_prompt["user"]}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        # Parse response
        content = response.choices[0].message.content
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    activity.logger.warning("Failed to parse OpenAI response as JSON, using mock research")
                    return await mock_domain_research(research_input)
            else:
                activity.logger.warning("No JSON found in OpenAI response, using mock research")
                return await mock_domain_research(research_input)
        
        activity.logger.info(f"OpenAI domain research completed for: {research_input['domain_name']}")
        return result
        
    except Exception as e:
        activity.logger.error(f"OpenAI domain research failed: {e}, using mock research")
        return await mock_domain_research(research_input)


async def analyze_with_openai(research_results: Dict[str, Any], domain_name: str) -> Dict[str, Any]:
    """Analyze research results using OpenAI API."""
    try:
        # Import OpenAI client
        try:
            from openai import AsyncOpenAI
        except ImportError:
            activity.logger.warning("OpenAI client not available, using mock analysis")
            return await mock_research_analysis(research_results, domain_name)
        
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            activity.logger.warning("OPENAI_API_KEY not set, using mock analysis")
            return await mock_research_analysis(research_results, domain_name)
        
        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=api_key)
        
        # Create analysis prompt
        analysis_prompt = create_analysis_prompt(research_results, domain_name)
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": analysis_prompt["system"]},
                {"role": "user", "content": analysis_prompt["user"]}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        # Parse response
        content = response.choices[0].message.content
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    activity.logger.warning("Failed to parse OpenAI response as JSON, using mock analysis")
                    return await mock_research_analysis(research_results, domain_name)
            else:
                activity.logger.warning("No JSON found in OpenAI response, using mock analysis")
                return await mock_research_analysis(research_results, domain_name)
        
        activity.logger.info(f"OpenAI research analysis completed for: {domain_name}")
        return result
        
    except Exception as e:
        activity.logger.error(f"OpenAI research analysis failed: {e}, using mock analysis")
        return await mock_research_analysis(research_results, domain_name)


@activity.defn
async def generate_domain_config_activity(
    owner_id: str, title: str, description: str, analysis_results: Dict[str, Any]
) -> Dict[str, Any]:
    """Generates the final DomainConfig object from analysis results."""
    activity.logger.info(f"Generating domain configuration for: {title}")
    
    try:
        from src.app.models.domain import DomainConfig, DomainStatus
        from slugify import slugify
        
        domain_id = slugify(title)
        final_topics = analysis_results.get("final_topics", [])
        quality_criteria = analysis_results.get("quality_criteria", {})
        bootstrap_prompt = analysis_results.get("bootstrap_prompt", "")
        search_attributes_suggestions = analysis_results.get("search_attributes_suggestions", {})
        
        # Default acceptance criteria based on quality_criteria
        acceptance_criteria = {
            "min_relevance_score": quality_criteria.get("quality_threshold", 7.0),
            "min_length": quality_criteria.get("min_length", 500),
            "required_sections": quality_criteria.get("required_sections", []),
            "weighted_quality_indicators": quality_criteria.get("weighted_indicators", {}),
        }
        
        # Convert search attributes to list of strings if not already
        processed_search_attributes = {}
        for k, v in search_attributes_suggestions.items():
            if isinstance(v, list):
                processed_search_attributes[k] = [str(item) for item in v]
            else:
                processed_search_attributes[k] = [str(v)]
        
        domain_config = DomainConfig(
            domain_id=domain_id,
            title=title,
            description=description,
            status=DomainStatus.PENDING_OWNER_REVIEW,
            owner_id=owner_id,
            topics=final_topics,
            quality_criteria=quality_criteria,
            bootstrap_prompt=bootstrap_prompt,
            acceptance_criteria=acceptance_criteria,
            search_attributes=processed_search_attributes,
        )
        
        activity.logger.info(f"Domain configuration generated for: {domain_id}")
        return domain_config.dict()
        
    except Exception as e:
        activity.logger.error(f"Failed to generate domain config: {e}")
        # Return a basic config as fallback
        from src.app.models.domain import DomainConfig, DomainStatus
        from slugify import slugify
        
        domain_id = slugify(title)
        return DomainConfig(
            domain_id=domain_id,
            title=title,
            description=description,
            status=DomainStatus.PENDING_OWNER_REVIEW,
            owner_id=owner_id,
            topics=[title.lower()],
            quality_criteria={"quality_threshold": 7.0, "min_length": 500},
            bootstrap_prompt=f"Research and analyze {title} domain",
            acceptance_criteria={"min_relevance_score": 7.0},
            search_attributes={},
        ).dict()


def create_research_prompt(research_input: Dict[str, Any]) -> Dict[str, str]:
    """Create comprehensive research prompt for domain bootstrap."""
    domain_name = research_input["domain_name"]
    domain_description = research_input["domain_description"]
    initial_topics = research_input.get("initial_topics", [])
    target_audience = research_input.get("target_audience", [])
    research_focus = research_input.get("research_focus", "")
    research_depth = research_input.get("research_depth", "comprehensive")
    include_historical = research_input.get("include_historical", True)
    include_technical = research_input.get("include_technical", True)
    include_practical = research_input.get("include_practical", True)
    
    system_prompt = f"""
You are an expert knowledge base architect specializing in domain research and knowledge base design.
Your task is to conduct comprehensive research on the domain "{domain_name}" to bootstrap a knowledge base.

RESEARCH OBJECTIVES:
1. Discover all relevant topics and subtopics for this domain
2. Identify quality criteria for content assessment
3. Understand the knowledge landscape and gaps
4. Recommend knowledge base structure and organization
5. Identify key stakeholders and use cases

RESEARCH DEPTH: {research_depth.upper()}
- Basic: Core topics and basic quality criteria
- Comprehensive: Detailed topic mapping, quality criteria, and knowledge gaps
- Expert: Complete domain analysis with advanced insights and recommendations

RESEARCH AREAS TO COVER:
- Historical development and evolution
- Technical aspects and methodologies
- Practical applications and use cases
- Current trends and future directions
- Key stakeholders and communities
- Knowledge gaps and opportunities

TARGET AUDIENCE: {', '.join(target_audience) if target_audience else 'General audience'}

Please provide your research in JSON format with the following structure:
{{
    "summary": "Comprehensive research summary",
    "topics": ["topic1", "topic2", "topic3"],
    "quality_criteria": {{
        "min_length": 1000,
        "quality_threshold": 7.0,
        "required_sections": ["abstract", "introduction", "conclusion", "references"],
        "technical_depth_required": true,
        "safety_considerations_required": true,
        "practical_applications_required": true
    }},
    "knowledge_gaps": ["gap1", "gap2", "gap3"],
    "sources": ["source1", "source2", "source3"],
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
    "bootstrap_prompt": "Custom prompt for this domain",
    "research_steps": ["step1", "step2", "step3"]
}}
"""

    user_prompt = f"""
Please conduct comprehensive research on the domain: {domain_name}

DOMAIN DESCRIPTION:
{domain_description}

INITIAL TOPICS PROVIDED:
{', '.join(initial_topics) if initial_topics else 'None provided'}

RESEARCH FOCUS:
{research_focus if research_focus else 'General domain research'}

RESEARCH REQUIREMENTS:
- Include historical research: {include_historical}
- Include technical research: {include_technical}
- Include practical applications: {include_practical}

Please provide a comprehensive research analysis in JSON format as specified in the system prompt.
"""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


def create_analysis_prompt(research_results: Dict[str, Any], domain_name: str) -> Dict[str, str]:
    """Create analysis prompt for research results."""
    system_prompt = f"""
You are an expert knowledge base architect analyzing research results for the domain "{domain_name}".
Your task is to analyze the research results and generate domain-specific configuration.

ANALYSIS OBJECTIVES:
1. Synthesize research findings into actionable domain configuration
2. Generate quality criteria specific to this domain
3. Create search attributes for workflow management
4. Develop custom bootstrap prompt for this domain
5. Recommend research steps and methodology

Please provide your analysis in JSON format with the following structure:
{{
    "topics": ["final_topic1", "final_topic2", "final_topic3"],
    "quality_criteria": {{
        "min_length": 1000,
        "quality_threshold": 7.0,
        "required_sections": ["abstract", "introduction", "conclusion", "references"],
        "technical_depth_required": true,
        "safety_considerations_required": true,
        "practical_applications_required": true
    }},
    "search_attributes": {{
        "domain_id": "domain_id_placeholder",
        "domain_name": "{domain_name}",
        "topics": ["topic1", "topic2"],
        "target_audience": ["audience1", "audience2"]
    }},
    "bootstrap_prompt": "Custom bootstrap prompt for this domain",
    "research_steps": ["step1", "step2", "step3"],
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"]
}}
"""

    user_prompt = f"""
Please analyze the following research results for the domain "{domain_name}":

RESEARCH RESULTS:
{json.dumps(research_results, indent=2)}

Please provide your analysis in JSON format as specified in the system prompt.
"""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


async def mock_domain_research(research_input: Dict[str, Any]) -> Dict[str, Any]:
    """Mock domain research when OpenAI is not available."""
    domain_name = research_input["domain_name"]
    
    return {
        "summary": f"Mock research summary for {domain_name}. This domain shows significant potential for knowledge base development with multiple research areas and practical applications.",
        "topics": [
            f"{domain_name.lower()} fundamentals",
            f"{domain_name.lower()} applications",
            f"{domain_name.lower()} best practices",
            f"{domain_name.lower()} case studies",
            f"{domain_name.lower()} future trends"
        ],
        "quality_criteria": {
            "min_length": 1000,
            "quality_threshold": 7.0,
            "required_sections": ["abstract", "introduction", "conclusion", "references"],
            "technical_depth_required": True,
            "safety_considerations_required": True,
            "practical_applications_required": True
        },
        "knowledge_gaps": [
            f"Limited research on {domain_name.lower()} in emerging markets",
            f"Need for more practical {domain_name.lower()} applications",
            f"Gap in {domain_name.lower()} education and training"
        ],
        "sources": [
            f"Academic research on {domain_name.lower()}",
            f"Industry reports on {domain_name.lower()}",
            f"Expert interviews on {domain_name.lower()}"
        ],
        "recommendations": [
            f"Focus on practical {domain_name.lower()} applications",
            f"Develop {domain_name.lower()} education resources",
            f"Create {domain_name.lower()} community engagement"
        ],
        "bootstrap_prompt": f"Expert analysis of {domain_name.lower()} domain with focus on practical applications and best practices.",
        "research_steps": [
            f"Literature review of {domain_name.lower()}",
            f"Expert interviews on {domain_name.lower()}",
            f"Case study analysis of {domain_name.lower()}"
        ]
    }


async def mock_research_analysis(research_results: Dict[str, Any], domain_name: str) -> Dict[str, Any]:
    """Mock research analysis when OpenAI is not available."""
    return {
        "topics": research_results.get("topics", [f"{domain_name.lower()} basics"]),
        "quality_criteria": research_results.get("quality_criteria", {
            "min_length": 1000,
            "quality_threshold": 7.0,
            "required_sections": ["abstract", "introduction", "conclusion", "references"],
            "technical_depth_required": True,
            "safety_considerations_required": True,
            "practical_applications_required": True
        }),
        "search_attributes": {
            "domain_id": "domain_id_placeholder",
            "domain_name": domain_name,
            "topics": research_results.get("topics", []),
            "target_audience": ["professionals", "students", "researchers"]
        },
        "bootstrap_prompt": f"Expert analysis of {domain_name.lower()} domain with focus on practical applications and best practices.",
        "research_steps": research_results.get("research_steps", [
            f"Literature review of {domain_name.lower()}",
            f"Expert interviews on {domain_name.lower()}",
            f"Case study analysis of {domain_name.lower()}"
        ]),
        "recommendations": research_results.get("recommendations", [
            f"Focus on practical {domain_name.lower()} applications",
            f"Develop {domain_name.lower()} education resources",
            f"Create {domain_name.lower()} community engagement"
        ])
    }
