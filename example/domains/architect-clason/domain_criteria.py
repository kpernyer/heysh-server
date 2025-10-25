"""Architect Isac Gustav Clason domain criteria and configurations."""

from typing import Dict, List, Any


class ArchitectClasonKnowledgeCriteria:
    """Knowledge base criteria for Architect Isac Gustav Clason domain."""
    
    # Core topics that define Architect Clason knowledge
    CORE_TOPICS = [
        "isac gustav clason",
        "architect clason",
        "swedish architecture",
        "national romanticism",
        "art nouveau",
        "nordic architecture",
        "stockholm architecture",
        "historical buildings",
        "architectural heritage",
        "cultural buildings",
        "public architecture",
        "institutional buildings",
        "architectural education",
        "architectural history",
        "swedish architects",
        "19th century architecture",
        "20th century architecture",
        "architectural movements",
        "building techniques",
        "architectural preservation"
    ]
    
    # Quality assessment criteria
    QUALITY_CRITERIA = {
        "min_length": 1500,
        "quality_threshold": 8.0,
        "required_sections": [
            "abstract", "introduction", "historical_context", "analysis", "conclusion", "references"
        ],
        "technical_depth_required": True,
        "historical_accuracy_required": True,
        "architectural_analysis_required": True,
        "cultural_context_required": True
    }
    
    # Relevance scoring weights
    RELEVANCE_WEIGHTS = {
        "topic_relevance": 0.35,
        "historical_accuracy": 0.25,
        "architectural_analysis": 0.20,
        "cultural_context": 0.15,
        "completeness": 0.05
    }
    
    # Architect Clason-specific quality indicators
    ARCHITECT_QUALITY_INDICATORS = [
        "historical_accuracy",
        "architectural_analysis",
        "cultural_context",
        "building_techniques",
        "design_principles",
        "influence_analysis",
        "preservation_status",
        "educational_value",
        "research_quality",
        "visual_documentation"
    ]


def get_architect_clason_domain_criteria() -> Dict[str, Any]:
    """Get comprehensive domain criteria for Architect Isac Gustav Clason knowledge base."""
    return {
        "topics": ArchitectClasonKnowledgeCriteria.CORE_TOPICS,
        "quality_criteria": ArchitectClasonKnowledgeCriteria.QUALITY_CRITERIA,
        "relevance_weights": ArchitectClasonKnowledgeCriteria.RELEVANCE_WEIGHTS,
        "quality_indicators": ArchitectClasonKnowledgeCriteria.ARCHITECT_QUALITY_INDICATORS,
        "domain_name": "Architect Isac Gustav Clason Knowledge Base",
        "domain_description": "Comprehensive knowledge base for Architect Isac Gustav Clason, Swedish architecture, and National Romanticism",
        "target_audience": [
            "architecture students",
            "architectural historians",
            "preservation professionals",
            "cultural heritage researchers",
            "architecture enthusiasts",
            "museum professionals"
        ]
    }


def get_architect_clason_analysis_prompt() -> str:
    """Get the specialized prompt for Architect Clason document analysis."""
    return """
You are an expert analyst specializing in architectural history and Swedish architecture.
Your task is to analyze documents for relevance to Architect Isac Gustav Clason and Swedish architectural heritage.

DOMAIN FOCUS: Architect Isac Gustav Clason Knowledge Base
- Isac Gustav Clason's life and work
- Swedish architecture and National Romanticism
- Historical buildings and architectural heritage
- Cultural and institutional architecture
- Architectural education and history
- Building techniques and preservation

ANALYSIS CRITERIA:
1. TOPIC RELEVANCE (35%): How directly does this relate to Architect Clason or Swedish architecture?
2. HISTORICAL ACCURACY (25%): Are historical details correct and well-researched?
3. ARCHITECTURAL ANALYSIS (20%): Does it provide architectural analysis and insights?
4. CULTURAL CONTEXT (15%): Does it address cultural and historical context?
5. COMPLETENESS (5%): Is the information comprehensive and well-structured?

SCORING SCALE: 0.0 - 10.0
- 8.5-10.0: Excellent, auto-approve
- 7.0-8.4: Good, needs human review  
- 0.0-6.9: Poor, auto-reject

REQUIRED SECTIONS: abstract, introduction, historical_context, analysis, conclusion, references
MINIMUM LENGTH: 1500 characters

Analyze the document and provide:
1. Relevance score (0.0-10.0)
2. Is relevant (true/false)
3. Analysis summary (2-3 sentences)
4. Key points (3-5 bullet points)
5. Topics identified (list of relevant topics)
6. Quality indicators (historical, architectural, cultural aspects)
7. Rejection reason (if score < 7.0)
"""


def get_architect_clason_learning_context() -> str:
    """Get context for building Architect Clason knowledge base."""
    return """
KNOWLEDGE BASE CONTEXT:
This system is building a comprehensive knowledge base for Architect Isac Gustav Clason and Swedish architectural heritage.
The knowledge base will be used to:

1. PRESERVE ARCHITECTURAL HERITAGE: Document and analyze Clason's work and influence
2. EDUCATE STAKEHOLDERS: Provide learning resources for students and professionals
3. SUPPORT RESEARCH: Enable academic and professional research
4. PROMOTE CULTURAL AWARENESS: Increase understanding of Swedish architectural history

CURRENT KNOWLEDGE AREAS:
- Isac Gustav Clason's life and architectural career
- National Romanticism in Swedish architecture
- Historical buildings and their significance
- Architectural techniques and methods
- Cultural and institutional architecture
- Preservation and restoration practices

TARGET KNOWLEDGE GAPS:
- Detailed analysis of Clason's design principles
- Influence on subsequent Swedish architects
- International recognition and impact
- Technical aspects of his building methods
- Cultural significance of his works
- Educational applications of his architecture
"""
