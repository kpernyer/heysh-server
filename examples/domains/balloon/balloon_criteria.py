"""Balloon knowledge base criteria and domain-specific configurations."""

from typing import Dict, List, Any


class BalloonKnowledgeCriteria:
    """Knowledge base criteria for hot air balloon domain."""
    
    # Core topics that define balloon knowledge
    CORE_TOPICS = [
        "hot air balloon",
        "balloon flight",
        "balloon navigation", 
        "balloon safety",
        "balloon weather",
        "balloon tourism",
        "balloon economics",
        "balloon history",
        "balloon science",
        "balloon technology",
        "balloon piloting",
        "balloon maintenance",
        "balloon regulations",
        "balloon equipment",
        "balloon materials",
        "balloon physics",
        "balloon meteorology",
        "balloon engineering",
        "balloon design",
        "balloon operations"
    ]
    
    # Quality assessment criteria
    QUALITY_CRITERIA = {
        "min_length": 1000,
        "quality_threshold": 7.0,
        "required_sections": [
            "abstract", "introduction", "conclusion", "references"
        ],
        "technical_depth_required": True,
        "safety_considerations_required": True,
        "practical_applications_required": True
    }
    
    # Relevance scoring weights
    RELEVANCE_WEIGHTS = {
        "topic_relevance": 0.3,
        "technical_accuracy": 0.25,
        "safety_focus": 0.2,
        "practical_value": 0.15,
        "completeness": 0.1
    }
    
    # Balloon-specific quality indicators
    BALLOON_QUALITY_INDICATORS = [
        "safety_protocols",
        "weather_considerations", 
        "navigation_techniques",
        "equipment_specifications",
        "regulatory_compliance",
        "pilot_training",
        "emergency_procedures",
        "maintenance_requirements",
        "economic_impact",
        "environmental_considerations"
    ]


def get_balloon_domain_criteria() -> Dict[str, Any]:
    """Get comprehensive domain criteria for balloon knowledge base."""
    return {
        "topics": BalloonKnowledgeCriteria.CORE_TOPICS,
        "quality_criteria": BalloonKnowledgeCriteria.QUALITY_CRITERIA,
        "relevance_weights": BalloonKnowledgeCriteria.RELEVANCE_WEIGHTS,
        "quality_indicators": BalloonKnowledgeCriteria.BALLOON_QUALITY_INDICATORS,
        "domain_name": "Hot Air Balloon Knowledge Base",
        "domain_description": "Comprehensive knowledge base for hot air balloon operations, safety, technology, and applications",
        "target_audience": [
            "balloon pilots",
            "aviation professionals", 
            "tourism operators",
            "safety inspectors",
            "researchers",
            "students"
        ]
    }


def get_balloon_analysis_prompt() -> str:
    """Get the specialized prompt for balloon document analysis."""
    return """
You are an expert analyst specializing in hot air balloon knowledge and operations. 
Your task is to analyze documents for relevance to the hot air balloon domain.

DOMAIN FOCUS: Hot Air Balloon Knowledge Base
- Balloon operations and piloting
- Safety protocols and procedures  
- Weather and navigation systems
- Tourism and economic impact
- Historical and scientific aspects
- Technology and equipment
- Regulations and compliance

ANALYSIS CRITERIA:
1. TOPIC RELEVANCE (30%): How directly does this relate to hot air balloons?
2. TECHNICAL ACCURACY (25%): Are technical details correct and detailed?
3. SAFETY FOCUS (20%): Does it address safety considerations?
4. PRACTICAL VALUE (15%): Will this help balloon operations?
5. COMPLETENESS (10%): Is the information comprehensive?

SCORING SCALE: 0.0 - 10.0
- 8.0-10.0: Excellent, auto-approve
- 7.0-7.9: Good, needs human review  
- 0.0-6.9: Poor, auto-reject

REQUIRED SECTIONS: abstract, introduction, conclusion, references
MINIMUM LENGTH: 1000 characters

Analyze the document and provide:
1. Relevance score (0.0-10.0)
2. Is relevant (true/false)
3. Analysis summary (2-3 sentences)
4. Key points (3-5 bullet points)
5. Topics identified (list of relevant topics)
6. Quality indicators (safety, technical, practical aspects)
7. Rejection reason (if score < 7.0)
"""


def get_balloon_learning_context() -> str:
    """Get context for building balloon knowledge base."""
    return """
KNOWLEDGE BASE CONTEXT:
This system is building a comprehensive knowledge base for hot air balloon operations.
The knowledge base will be used to:

1. EVALUATE NEW CONTRIBUTIONS: Assess if new documents add value to balloon knowledge
2. MAINTAIN QUALITY STANDARDS: Ensure all content meets safety and technical standards  
3. SUPPORT DECISION MAKING: Help operators make informed decisions
4. EDUCATE STAKEHOLDERS: Provide learning resources for pilots, operators, and enthusiasts

CURRENT KNOWLEDGE AREAS:
- Historical development of balloon technology
- Modern navigation and weather systems  
- Economic impact of balloon tourism
- Safety protocols and regulations
- Technical specifications and maintenance
- Environmental considerations

TARGET KNOWLEDGE GAPS:
- Advanced weather prediction for balloon operations
- International regulatory harmonization
- Sustainable tourism practices
- Emergency response procedures
- Technology integration opportunities
"""
