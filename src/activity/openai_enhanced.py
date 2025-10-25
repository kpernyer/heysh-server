"""Enhanced OpenAI integration with OpenRouter support and continuous feedback."""

import json
import os
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

import structlog
from temporalio import activity

# Import cost-optimized configuration
from config.openrouter_config import openrouter_config

logger = structlog.get_logger()


@activity.defn
async def enhanced_domain_research_activity(research_input: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced domain research with OpenAI and continuous feedback.
    
    This activity performs comprehensive research using OpenAI with OpenRouter support,
    providing continuous feedback to the owner during the research process.
    
    Args:
        research_input: Dictionary containing domain information and research parameters
    
    Returns:
        Dictionary containing comprehensive research results
    """
    activity.logger.info(
        f"Starting enhanced domain research: {research_input['domain_name']}"
    )

    try:
        # Use OpenAI with OpenRouter for enhanced research
        research_result = await research_with_openai_enhanced(research_input)
        
        activity.logger.info(
            f"Enhanced domain research completed: {research_input['domain_name']}"
        )
        
        return research_result
        
    except Exception as e:
        activity.logger.error(
            f"Enhanced domain research failed: {research_input['domain_name']}, error={e!s}"
        )
        raise


@activity.defn
async def continuous_research_activity(
    domain_name: str, 
    research_focus: str, 
    current_insights: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Continuous research activity that builds on previous insights.
    
    This activity runs independently and continuously adds knowledge
    for the owner to consider during the onboarding process.
    
    Args:
        domain_name: Name of the domain
        research_focus: Specific research focus area
        current_insights: Current insights to build upon
    
    Returns:
        Dictionary containing new insights and knowledge
    """
    activity.logger.info(
        f"Starting continuous research: {domain_name} - {research_focus}"
    )

    try:
        # Use OpenAI for continuous research
        continuous_result = await continuous_research_with_openai(
            domain_name, research_focus, current_insights
        )
        
        activity.logger.info(
            f"Continuous research completed: {domain_name} - {research_focus}"
        )
        
        return continuous_result
        
    except Exception as e:
        activity.logger.error(
            f"Continuous research failed: {domain_name} - {research_focus}, error={e!s}"
        )
        raise


@activity.defn
async def deep_question_analysis_activity(
    question: str, 
    domain_context: Dict[str, Any], 
    research_depth: str = "comprehensive"
) -> Dict[str, Any]:
    """Deep analysis of a specific question using OpenAI.
    
    This activity provides deep analysis of the highest-ranked questions
    to give the owner more detailed insights.
    
    Args:
        question: The question to analyze deeply
        domain_context: Domain context and previous research
        research_depth: Depth of analysis (basic, comprehensive, expert)
    
    Returns:
        Dictionary containing deep analysis results
    """
    activity.logger.info(
        f"Starting deep question analysis: {question[:50]}..."
    )

    try:
        # Use OpenAI for deep question analysis
        analysis_result = await deep_analysis_with_openai(
            question, domain_context, research_depth
        )
        
        activity.logger.info(
            f"Deep question analysis completed: {question[:50]}..."
        )
        
        return analysis_result
        
    except Exception as e:
        activity.logger.error(
            f"Deep question analysis failed: {question[:50]}..., error={e!s}"
        )
        raise


async def research_with_openai_enhanced(research_input: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced research using OpenAI with OpenRouter support."""
    try:
        # Import OpenAI client
        try:
            from openai import AsyncOpenAI
        except ImportError:
            activity.logger.warning("OpenAI client not available, using mock research")
            return await mock_enhanced_research(research_input)
        
        # Get OpenAI API key (prefer OpenRouter if available)
        api_key = openrouter_config.api_key or os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            activity.logger.warning("No API key set, using mock research")
            return await mock_enhanced_research(research_input)
        
        # Initialize OpenAI client with cost-optimized configuration
        client_config = openrouter_config.get_client_config()
        client = AsyncOpenAI(**client_config)
        
        # Log cost optimization info
        if openrouter_config.is_cost_effective():
            activity.logger.info(f"Using cost-optimized model: {openrouter_config.model}")
        else:
            tips = openrouter_config.get_optimization_tips()
            if tips:
                activity.logger.warning(f"Cost optimization tips: {', '.join(tips)}")
        
        # Create enhanced research prompt
        research_prompt = create_enhanced_research_prompt(research_input)
        
        # Call OpenAI API with cost-optimized parameters
        model_config = openrouter_config.get_model_config()
        response = await client.chat.completions.create(
            model=model_config["model"],
            messages=[
                {"role": "system", "content": research_prompt["system"]},
                {"role": "user", "content": research_prompt["user"]}
            ],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"],
            stream=model_config["stream"]
        )
        
        # Process streaming response
        research_content = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                research_content += chunk.choices[0].delta.content
                # Send real-time feedback to owner
                await send_realtime_feedback(
                    research_input["domain_name"],
                    chunk.choices[0].delta.content
                )
        
        # Parse the complete response
        try:
            result = json.loads(research_content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', research_content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    activity.logger.warning("Failed to parse OpenAI response as JSON, using mock research")
                    return await mock_enhanced_research(research_input)
            else:
                activity.logger.warning("No JSON found in OpenAI response, using mock research")
                return await mock_enhanced_research(research_input)
        
        activity.logger.info(f"Enhanced OpenAI research completed for: {research_input['domain_name']}")
        return result
        
    except Exception as e:
        activity.logger.error(f"Enhanced OpenAI research failed: {e}, using mock research")
        return await mock_enhanced_research(research_input)


async def continuous_research_with_openai(
    domain_name: str, 
    research_focus: str, 
    current_insights: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Continuous research using OpenAI to build on existing insights."""
    try:
        # Import OpenAI client
        try:
            from openai import AsyncOpenAI
        except ImportError:
            activity.logger.warning("OpenAI client not available, using mock continuous research")
            return await mock_continuous_research(domain_name, research_focus)
        
        # Get OpenAI API key
        api_key = openrouter_config.api_key or os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            activity.logger.warning("No API key set, using mock continuous research")
            return await mock_continuous_research(domain_name, research_focus)
        
        # Initialize OpenAI client with cost-optimized configuration
        client_config = openrouter_config.get_client_config()
        client = AsyncOpenAI(**client_config)
        
        # Create continuous research prompt
        continuous_prompt = create_continuous_research_prompt(
            domain_name, research_focus, current_insights
        )
        
        # Call OpenAI API with cost-optimized parameters
        model_config = openrouter_config.get_model_config()
        response = await client.chat.completions.create(
            model=model_config["model"],
            messages=[
                {"role": "system", "content": continuous_prompt["system"]},
                {"role": "user", "content": continuous_prompt["user"]}
            ],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
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
                    activity.logger.warning("Failed to parse OpenAI response as JSON, using mock continuous research")
                    return await mock_continuous_research(domain_name, research_focus)
            else:
                activity.logger.warning("No JSON found in OpenAI response, using mock continuous research")
                return await mock_continuous_research(domain_name, research_focus)
        
        activity.logger.info(f"Continuous OpenAI research completed for: {domain_name}")
        return result
        
    except Exception as e:
        activity.logger.error(f"Continuous OpenAI research failed: {e}, using mock continuous research")
        return await mock_continuous_research(domain_name, research_focus)


async def deep_analysis_with_openai(
    question: str, 
    domain_context: Dict[str, Any], 
    research_depth: str
) -> Dict[str, Any]:
    """Deep analysis using OpenAI for high-ranked questions."""
    try:
        # Import OpenAI client
        try:
            from openai import AsyncOpenAI
        except ImportError:
            activity.logger.warning("OpenAI client not available, using mock deep analysis")
            return await mock_deep_analysis(question, domain_context)
        
        # Get OpenAI API key
        api_key = openrouter_config.api_key or os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            activity.logger.warning("No API key set, using mock deep analysis")
            return await mock_deep_analysis(question, domain_context)
        
        # Initialize OpenAI client with cost-optimized configuration
        client_config = openrouter_config.get_client_config()
        client = AsyncOpenAI(**client_config)
        
        # Create deep analysis prompt
        deep_prompt = create_deep_analysis_prompt(question, domain_context, research_depth)
        
        # Call OpenAI API with cost-optimized parameters
        model_config = openrouter_config.get_model_config()
        response = await client.chat.completions.create(
            model=model_config["model"],
            messages=[
                {"role": "system", "content": deep_prompt["system"]},
                {"role": "user", "content": deep_prompt["user"]}
            ],
            temperature=model_config["temperature"],
            max_tokens=model_config["max_tokens"]
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
                    activity.logger.warning("Failed to parse OpenAI response as JSON, using mock deep analysis")
                    return await mock_deep_analysis(question, domain_context)
            else:
                activity.logger.warning("No JSON found in OpenAI response, using mock deep analysis")
                return await mock_deep_analysis(question, domain_context)
        
        activity.logger.info(f"Deep OpenAI analysis completed for: {question[:50]}...")
        return result
        
    except Exception as e:
        activity.logger.error(f"Deep OpenAI analysis failed: {e}, using mock deep analysis")
        return await mock_deep_analysis(question, domain_context)


async def send_realtime_feedback(domain_name: str, content: str):
    """Send real-time feedback to the owner during research."""
    # This would integrate with your notification system
    # For now, we'll just log it
    activity.logger.info(f"Real-time feedback for {domain_name}: {content[:100]}...")


def create_enhanced_research_prompt(research_input: Dict[str, Any]) -> Dict[str, str]:
    """Create enhanced research prompt for OpenAI."""
    domain_name = research_input["domain_name"]
    domain_description = research_input["domain_description"]
    initial_topics = research_input.get("initial_topics", [])
    target_audience = research_input.get("target_audience", [])
    research_focus = research_input.get("research_focus", "")
    research_depth = research_input.get("research_depth", "comprehensive")
    
    system_prompt = f"""
You are an expert knowledge base architect specializing in comprehensive domain research.
Your task is to conduct deep, multi-faceted research on the domain "{domain_name}" to bootstrap a world-class knowledge base.

RESEARCH OBJECTIVES:
1. Discover all relevant topics and subtopics for this domain
2. Identify quality criteria for content assessment
3. Understand the knowledge landscape and gaps
4. Recommend knowledge base structure and organization
5. Identify key stakeholders and use cases
6. Provide actionable insights for knowledge base development

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
- Best practices and standards
- Educational resources and learning paths

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
    "research_steps": ["step1", "step2", "step3"],
    "insights": [
        {{
            "insight": "Key insight about the domain",
            "category": "technical|practical|historical|comparative",
            "relevance": 0.0-1.0,
            "actionable": true
        }}
    ]
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
- Include historical research: {research_input.get('include_historical', True)}
- Include technical research: {research_input.get('include_technical', True)}
- Include practical applications: {research_input.get('include_practical', True)}

Please provide a comprehensive research analysis in JSON format as specified in the system prompt.
"""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


def create_continuous_research_prompt(
    domain_name: str, 
    research_focus: str, 
    current_insights: List[Dict[str, Any]]
) -> Dict[str, str]:
    """Create continuous research prompt for OpenAI."""
    system_prompt = f"""
You are an expert research assistant specializing in continuous domain knowledge discovery.
Your task is to build upon existing insights for the domain "{domain_name}" and provide additional knowledge.

CONTINUOUS RESEARCH OBJECTIVES:
1. Build upon existing insights and knowledge
2. Discover new angles and perspectives
3. Identify additional knowledge gaps
4. Provide fresh insights and recommendations
5. Suggest new research directions

RESEARCH FOCUS: {research_focus}

Please provide your continuous research in JSON format with the following structure:
{{
    "new_insights": [
        {{
            "insight": "New insight about the domain",
            "category": "technical|practical|historical|comparative",
            "relevance": 0.0-1.0,
            "actionable": true,
            "builds_on": "existing_insight_id"
        }}
    ],
    "additional_topics": ["topic1", "topic2"],
    "new_gaps": ["gap1", "gap2"],
    "recommendations": ["recommendation1", "recommendation2"],
    "research_directions": ["direction1", "direction2"]
}}
"""

    user_prompt = f"""
Please conduct continuous research on the domain: {domain_name}

RESEARCH FOCUS: {research_focus}

CURRENT INSIGHTS:
{json.dumps(current_insights, indent=2) if current_insights else 'No existing insights'}

Please provide additional insights and knowledge in JSON format as specified in the system prompt.
"""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


def create_deep_analysis_prompt(
    question: str, 
    domain_context: Dict[str, Any], 
    research_depth: str
) -> Dict[str, str]:
    """Create deep analysis prompt for OpenAI."""
    system_prompt = f"""
You are an expert analyst specializing in deep domain knowledge analysis.
Your task is to provide comprehensive analysis of the question: "{question}"

DEEP ANALYSIS OBJECTIVES:
1. Provide comprehensive answer to the question
2. Include relevant context and background
3. Identify key concepts and relationships
4. Suggest related questions and topics
5. Provide actionable insights and recommendations

RESEARCH DEPTH: {research_depth.upper()}

Please provide your deep analysis in JSON format with the following structure:
{{
    "answer": "Comprehensive answer to the question",
    "context": "Relevant background and context",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "relationships": [
        {{
            "concept1": "concept1",
            "concept2": "concept2",
            "relationship": "relationship_type",
            "strength": 0.0-1.0
        }}
    ],
    "related_questions": ["question1", "question2", "question3"],
    "actionable_insights": ["insight1", "insight2"],
    "recommendations": ["recommendation1", "recommendation2"],
    "confidence": 0.0-1.0
}}
"""

    user_prompt = f"""
Please provide deep analysis for the question: {question}

DOMAIN CONTEXT:
{json.dumps(domain_context, indent=2)}

Please provide comprehensive analysis in JSON format as specified in the system prompt.
"""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


# Mock functions for when OpenAI is not available
async def mock_enhanced_research(research_input: Dict[str, Any]) -> Dict[str, Any]:
    """Mock enhanced research when OpenAI is not available."""
    domain_name = research_input["domain_name"]
    
    return {
        "summary": f"Enhanced mock research summary for {domain_name}. This domain shows significant potential for knowledge base development with multiple research areas and practical applications.",
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
        ],
        "insights": [
            {
                "insight": f"Key insight about {domain_name.lower()}",
                "category": "technical",
                "relevance": 0.8,
                "actionable": True
            }
        ]
    }


async def mock_continuous_research(domain_name: str, research_focus: str) -> Dict[str, Any]:
    """Mock continuous research when OpenAI is not available."""
    return {
        "new_insights": [
            {
                "insight": f"New insight about {domain_name.lower()}",
                "category": "practical",
                "relevance": 0.7,
                "actionable": True,
                "builds_on": "existing_insight_1"
            }
        ],
        "additional_topics": [f"{domain_name.lower()} advanced concepts"],
        "new_gaps": [f"Gap in {domain_name.lower()} research"],
        "recommendations": [f"Recommendation for {domain_name.lower()}"],
        "research_directions": [f"Research direction for {domain_name.lower()}"]
    }


async def mock_deep_analysis(question: str, domain_context: Dict[str, Any]) -> Dict[str, Any]:
    """Mock deep analysis when OpenAI is not available."""
    return {
        "answer": f"Mock comprehensive answer to: {question}",
        "context": "Mock relevant background and context",
        "key_concepts": ["concept1", "concept2", "concept3"],
        "relationships": [
            {
                "concept1": "concept1",
                "concept2": "concept2",
                "relationship": "related_to",
                "strength": 0.8
            }
        ],
        "related_questions": ["related question 1", "related question 2"],
        "actionable_insights": ["insight 1", "insight 2"],
        "recommendations": ["recommendation 1", "recommendation 2"],
        "confidence": 0.8
    }
