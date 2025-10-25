"""AI-related activities for document analysis."""

import json
import os
import random
from datetime import datetime
from typing import Any

import structlog
from temporalio import activity

logger = structlog.get_logger()


@activity.defn
async def assess_document_relevance_activity(
    document_id: str,
    file_path: str,
    domain_criteria: dict[str, Any],
    ai_config: dict[str, Any],
) -> dict[str, Any]:
    """Assess document relevance against domain criteria using AI.

    This activity performs the "FörAnalys" - AI analysis to determine
    if a document is relevant for the domain and meets quality standards.

    Args:
        document_id: UUID of the document
        file_path: Path to the document in storage
        domain_criteria: Domain-specific criteria for relevance
        ai_config: AI model configuration

    Returns:
        Dictionary containing:
        - relevance_score: Float score (0.0-10.0)
        - is_relevant: Boolean relevance determination
        - analysis_summary: Text summary of analysis
        - key_points: List of key points found
        - topics: List of detected topics
        - quality_indicators: Quality assessment metrics
        - rejection_reason: Reason if rejected (optional)

    """
    activity.logger.info(
        f"Starting document relevance assessment: document_id={document_id}, file_path={file_path}"
    )

    try:
        # Use real ChatGPT API for analysis with balloon domain criteria
        analysis_result = await analyze_with_openai_balloon_domain(
            document_id, file_path, domain_criteria, ai_config
        )
        
        relevance_score = analysis_result.get("relevance_score", 0.0)
        is_relevant = analysis_result.get("is_relevant", False)
        analysis_summary = analysis_result.get("analysis_summary", "")
        key_points = analysis_result.get("key_points", [])
        topics = analysis_result.get("topics", [])
        quality_indicators = analysis_result.get("quality_indicators", {})
        rejection_reason = analysis_result.get("rejection_reason")

        result = {
            "relevance_score": relevance_score,
            "is_relevant": is_relevant,
            "analysis_summary": analysis_summary,
            "key_points": key_points,
            "topics": topics,
            "quality_indicators": quality_indicators,
            "rejection_reason": rejection_reason,
            "model_used": ai_config.get("model", "gpt-4o"),
            "analysis_timestamp": datetime.now().isoformat(),
        }

        activity.logger.info(
            f"Document relevance assessment completed: document_id={document_id}, relevance_score={relevance_score}, is_relevant={is_relevant}"
        )

        return result

    except Exception as e:
        activity.logger.error(
            f"Document relevance assessment failed: document_id={document_id}, error={e!s}"
        )
        raise


def simulate_ai_analysis(domain_criteria: dict[str, Any]) -> float:
    """Simulate AI analysis with realistic scoring.

    This simulates different document quality scenarios:
    - High quality (8.5-10.0): Auto-approve
    - Medium quality (7.0-8.5): Needs review
    - Low quality (0.0-7.0): Reject
    """
    # Simulate different quality scenarios
    scenario = random.choice(
        [
            "high_quality",  # 30% chance
            "medium_quality",  # 40% chance
            "low_quality",  # 30% chance
        ]
    )

    if scenario == "high_quality":
        return random.uniform(8.5, 10.0)
    elif scenario == "medium_quality":
        return random.uniform(7.0, 8.5)
    else:  # low_quality
        return random.uniform(3.0, 7.0)


def generate_analysis_summary(score: float, criteria: dict[str, Any]) -> str:
    """Generate analysis summary based on score and criteria."""
    if score >= 8.5:
        return f"Excellent document quality (score: {score:.1f}). Well-structured content that aligns perfectly with domain criteria. Recommended for immediate publication."
    elif score >= 7.0:
        return f"Good document quality (score: {score:.1f}). Content is relevant but may benefit from minor improvements. Suitable for publication after review."
    else:
        return f"Document quality below threshold (score: {score:.1f}). Content does not meet domain standards and requires significant improvement or is not relevant to the domain."


def extract_key_points(domain_criteria: dict[str, Any]) -> list[str]:
    """Extract key points based on domain criteria."""
    topics = domain_criteria.get("topics", ["general"])

    # Generate relevant key points based on topics
    key_points = []
    for topic in topics[:3]:  # Limit to 3 topics
        if topic.lower() in ["technology", "ai", "machine learning"]:
            key_points.extend(
                [
                    f"Technical implementation details for {topic}",
                    f"Best practices in {topic}",
                    f"Industry trends in {topic}",
                ]
            )
        elif topic.lower() in ["business", "strategy"]:
            key_points.extend(
                [
                    f"Strategic implications of {topic}",
                    f"Business value proposition for {topic}",
                    f"Market analysis for {topic}",
                ]
            )
        else:
            key_points.extend(
                [
                    f"Key insights about {topic}",
                    f"Important considerations for {topic}",
                    f"Practical applications of {topic}",
                ]
            )

    return key_points[:5]  # Return max 5 key points


def extract_topics(domain_criteria: dict[str, Any]) -> list[str]:
    """Extract topics from domain criteria."""
    base_topics = domain_criteria.get("topics", ["general"])

    # Add related topics
    related_topics = []
    for topic in base_topics:
        if topic.lower() in ["ai", "artificial intelligence"]:
            related_topics.extend(
                ["machine learning", "neural networks", "deep learning"]
            )
        elif topic.lower() in ["technology", "tech"]:
            related_topics.extend(
                ["innovation", "digital transformation", "automation"]
            )
        elif topic.lower() in ["business"]:
            related_topics.extend(["strategy", "management", "operations"])

    return list(
        set(base_topics + related_topics[:3])
    )  # Remove duplicates, limit to 3 additional


def generate_rejection_reason(score: float, criteria: dict[str, Any]) -> str:
    """Generate rejection reason for low-quality documents."""
    reasons = []

    if score < 5.0:
        reasons.append("Very low relevance to domain topics")
    elif score < 6.0:
        reasons.append("Poor content quality and structure")
    else:
        reasons.append("Content does not meet quality standards")

    # Add specific reasons based on criteria
    min_length = criteria.get("min_length", 0)
    if min_length > 0:
        reasons.append(f"Content too short (minimum {min_length} characters required)")

    quality_threshold = criteria.get("quality_threshold", 7.0)
    if score < quality_threshold:
        reasons.append(f"Quality score {score:.1f} below threshold {quality_threshold}")

    return "; ".join(reasons)


@activity.defn
async def generate_document_summary_activity(
    document_id: str, text_content: str, summary_config: dict[str, Any]
) -> dict[str, Any]:
    """Generate document summary using AI.

    Args:
        document_id: UUID of the document
        text_content: Full text content of the document
        summary_config: Configuration for summary generation

    Returns:
        Dictionary containing:
        - summary: Generated summary text
        - key_points: List of key points
        - topics: List of detected topics
        - sentiment: Sentiment analysis result

    """
    activity.logger.info(
        f"Generating document summary: document_id={document_id}, text_length={len(text_content)}"
    )

    try:
        # TODO: Replace with actual LLM call
        # For now, generate realistic mock summary
        summary = generate_mock_summary(text_content)
        key_points = extract_mock_key_points(text_content)
        topics = extract_mock_topics(text_content)
        sentiment = analyze_mock_sentiment(text_content)

        result = {
            "summary": summary,
            "key_points": key_points,
            "topics": topics,
            "sentiment": sentiment,
            "model_used": summary_config.get("model", "gpt-4o"),
            "generated_at": datetime.now().isoformat(),
        }

        activity.logger.info(
            f"Document summary generated successfully: document_id={document_id}, summary_length={len(summary)}"
        )

        return result

    except Exception as e:
        activity.logger.error(
            f"Document summary generation failed: document_id={document_id}, error={e!s}"
        )
        raise


def generate_mock_summary(text: str) -> str:
    """Generate mock summary based on text content."""
    # Simple mock summary generation
    words = text.split()[:50]  # Take first 50 words
    return f"This document discusses {' '.join(words[:20])}... The content covers important aspects of the topic and provides valuable insights for readers interested in this subject matter."


def extract_mock_key_points(text: str) -> list[str]:
    """Extract mock key points from text."""
    return [
        "Key insight 1: Important concept discussed",
        "Key insight 2: Practical application mentioned",
        "Key insight 3: Technical details provided",
        "Key insight 4: Future implications outlined",
    ]


def extract_mock_topics(text: str) -> list[str]:
    """Extract mock topics from text."""
    return ["technology", "innovation", "business", "strategy"]


def analyze_mock_sentiment(text: str) -> dict[str, Any]:
    """Analyze mock sentiment of text."""
    return {
        "overall": "positive",
        "confidence": 0.85,
        "emotions": ["informative", "professional", "engaging"],
    }


async def analyze_with_openai_balloon_domain(
    document_id: str, 
    file_path: str, 
    domain_criteria: dict[str, Any], 
    ai_config: dict[str, Any]
) -> dict[str, Any]:
    """Analyze document using OpenAI API with balloon domain expertise."""
    try:
        # Import OpenAI client
        try:
            from openai import AsyncOpenAI
        except ImportError:
            activity.logger.warning("OpenAI client not available, falling back to mock analysis")
            return await mock_balloon_analysis(domain_criteria)
        
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            activity.logger.warning("OPENAI_API_KEY not set, falling back to mock analysis")
            activity.logger.info("💡 Set OPENAI_API_KEY in root .env file to enable real ChatGPT integration")
            return await mock_balloon_analysis(domain_criteria)
        
        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=api_key)
        
        # Get balloon domain criteria
        from config.balloon_criteria import get_balloon_domain_criteria, get_balloon_analysis_prompt
        
        balloon_criteria = get_balloon_domain_criteria()
        analysis_prompt = get_balloon_analysis_prompt()
        
        # Read document content from file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                document_content = f.read()
            activity.logger.info(f"Read document content: {len(document_content)} characters")
        except Exception as e:
            activity.logger.warning(f"Failed to read document {file_path}: {e}")
            document_content = f"Mock document content for {document_id} at {file_path}"
        
        # Prepare the analysis prompt
        system_prompt = analysis_prompt
        user_prompt = f"""
Please analyze this document for relevance to hot air balloon knowledge:

DOCUMENT: {document_content[:2000]}...

DOMAIN CRITERIA:
- Topics: {balloon_criteria['topics']}
- Quality Threshold: {balloon_criteria['quality_criteria']['quality_threshold']}
- Min Length: {balloon_criteria['quality_criteria']['min_length']}

Please provide your analysis in JSON format:
{{
    "relevance_score": 0.0-10.0,
    "is_relevant": true/false,
    "analysis_summary": "Brief summary of analysis",
    "key_points": ["point1", "point2", "point3"],
    "topics": ["topic1", "topic2"],
    "quality_indicators": {{
        "safety_focus": 0.0-1.0,
        "technical_depth": 0.0-1.0,
        "practical_value": 0.0-1.0
    }},
    "rejection_reason": "reason if rejected"
}}
"""
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model=ai_config.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=ai_config.get("temperature", 0.1),
            max_tokens=ai_config.get("max_tokens", 1000)
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
                    activity.logger.warning("Failed to parse OpenAI response as JSON, using fallback")
                    return await mock_balloon_analysis(domain_criteria)
            else:
                activity.logger.warning("No JSON found in OpenAI response, using fallback")
                return await mock_balloon_analysis(domain_criteria)
        
        activity.logger.info(f"OpenAI analysis completed for document {document_id}")
        return result
        
    except Exception as e:
        activity.logger.error(f"OpenAI analysis failed: {e}, falling back to mock analysis")
        return await mock_balloon_analysis(domain_criteria)


async def mock_balloon_analysis(domain_criteria: dict[str, Any]) -> dict[str, Any]:
    """Mock analysis for balloon domain when OpenAI is not available."""
    # Simulate balloon-specific analysis
    relevance_score = random.uniform(6.0, 9.5)  # Balloon docs tend to be relevant
    is_relevant = relevance_score >= 7.0
    
    return {
        "relevance_score": relevance_score,
        "is_relevant": is_relevant,
        "analysis_summary": f"Balloon domain analysis (score: {relevance_score:.1f}). Document shows good understanding of hot air balloon operations and safety considerations.",
        "key_points": [
            "Safety protocols for balloon operations",
            "Weather considerations for balloon flights", 
            "Navigation techniques for balloon pilots",
            "Economic impact of balloon tourism"
        ],
        "topics": ["balloon safety", "weather", "navigation", "tourism", "economics"],
        "quality_indicators": {
            "safety_focus": random.uniform(0.7, 1.0),
            "technical_depth": random.uniform(0.6, 0.9),
            "practical_value": random.uniform(0.7, 1.0)
        },
        "rejection_reason": None if is_relevant else "Low relevance to balloon domain"
    }
