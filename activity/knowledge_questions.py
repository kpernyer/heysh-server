"""Knowledge question generation activities."""

import json
import os
from typing import Any, Dict, List

import structlog
from temporalio import activity

logger = structlog.get_logger()


@activity.defn
async def generate_knowledge_questions_activity(questions_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate example questions that the knowledge base can answer.
    
    This activity uses OpenAI to generate relevant questions based on the domain research
    and analysis results. These questions will be presented to the owner for feedback.
    
    Args:
        questions_input: Dictionary containing:
            - domain_name: Name of the domain
            - domain_description: Description of the domain
            - topics: List of discovered topics
            - research_summary: Summary of research results
            - target_audience: Target audience for the domain
    
    Returns:
        List of dictionaries containing:
        - question: The example question
        - category: Category of the question
        - difficulty: Difficulty level (beginner, intermediate, advanced)
        - relevance_score: Relevance score (0.0-1.0)
        - expected_answer_type: Type of answer expected
    """
    activity.logger.info(
        f"Generating knowledge questions for: {questions_input['domain_name']}"
    )

    try:
        # Use OpenAI to generate example questions
        questions_result = await generate_questions_with_openai(questions_input)
        
        activity.logger.info(
            f"Knowledge questions generated: {questions_input['domain_name']}"
        )
        
        return questions_result
        
    except Exception as e:
        activity.logger.error(
            f"Knowledge questions generation failed: {questions_input['domain_name']}, error={e!s}"
        )
        raise


async def generate_questions_with_openai(questions_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate example questions using OpenAI API."""
    try:
        # Import OpenAI client
        try:
            from openai import AsyncOpenAI
        except ImportError:
            activity.logger.warning("OpenAI client not available, using mock questions")
            return await mock_knowledge_questions(questions_input)
        
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            activity.logger.warning("OPENAI_API_KEY not set, using mock questions")
            return await mock_knowledge_questions(questions_input)
        
        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=api_key)
        
        # Create questions generation prompt
        questions_prompt = create_questions_prompt(questions_input)
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": questions_prompt["system"]},
                {"role": "user", "content": questions_prompt["user"]}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse response
        content = response.choices[0].message.content
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    activity.logger.warning("Failed to parse OpenAI response as JSON, using mock questions")
                    return await mock_knowledge_questions(questions_input)
            else:
                activity.logger.warning("No JSON found in OpenAI response, using mock questions")
                return await mock_knowledge_questions(questions_input)
        
        activity.logger.info(f"OpenAI questions generated for: {questions_input['domain_name']}")
        return result
        
    except Exception as e:
        activity.logger.error(f"OpenAI questions generation failed: {e}, using mock questions")
        return await mock_knowledge_questions(questions_input)


def create_questions_prompt(questions_input: Dict[str, Any]) -> Dict[str, str]:
    """Create prompt for generating example questions."""
    domain_name = questions_input["domain_name"]
    domain_description = questions_input["domain_description"]
    topics = questions_input.get("topics", [])
    research_summary = questions_input.get("research_summary", "")
    target_audience = questions_input.get("target_audience", [])
    
    system_prompt = f"""
You are an expert knowledge base architect specializing in generating relevant questions for domain-specific knowledge bases.
Your task is to generate example questions that demonstrate the knowledge base's capabilities for the domain "{domain_name}".

QUESTION GENERATION OBJECTIVES:
1. Create questions that showcase the knowledge base's expertise
2. Cover different difficulty levels (beginner, intermediate, advanced)
3. Address different aspects of the domain (technical, practical, historical, etc.)
4. Be specific and actionable
5. Demonstrate the value of the knowledge base

QUESTION CATEGORIES TO COVER:
- Technical questions about domain-specific concepts
- Practical questions about applications and use cases
- Historical questions about development and evolution
- Comparative questions about different approaches
- Problem-solving questions about common challenges

TARGET AUDIENCE: {', '.join(target_audience) if target_audience else 'General audience'}

Please generate 8-10 example questions in JSON format with the following structure:
[
    {{
        "question": "Specific question about the domain",
        "category": "technical|practical|historical|comparative|problem-solving",
        "difficulty": "beginner|intermediate|advanced",
        "relevance_score": 0.0-1.0,
        "expected_answer_type": "factual|analytical|procedural|conceptual",
        "key_topics": ["topic1", "topic2"],
        "target_audience": ["audience1", "audience2"]
    }}
]
"""

    user_prompt = f"""
Please generate example questions for the domain: {domain_name}

DOMAIN DESCRIPTION:
{domain_description}

DISCOVERED TOPICS:
{', '.join(topics) if topics else 'Topics being analyzed'}

RESEARCH SUMMARY:
{research_summary if research_summary else 'Research in progress'}

TARGET AUDIENCE:
{', '.join(target_audience) if target_audience else 'General audience'}

Please generate 8-10 example questions that demonstrate the knowledge base's capabilities for this domain.
Make sure the questions are:
1. Specific and actionable
2. Cover different difficulty levels
3. Address different aspects of the domain
4. Demonstrate the value of the knowledge base
5. Are relevant to the target audience

Provide your response in JSON format as specified in the system prompt.
"""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


async def mock_knowledge_questions(questions_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Mock knowledge questions when OpenAI is not available."""
    domain_name = questions_input["domain_name"]
    topics = questions_input.get("topics", [])
    target_audience = questions_input.get("target_audience", [])
    
    return [
        {
            "question": f"What are the fundamental principles of {domain_name.lower()}?",
            "category": "technical",
            "difficulty": "beginner",
            "relevance_score": 0.9,
            "expected_answer_type": "conceptual",
            "key_topics": topics[:2] if topics else [domain_name.lower()],
            "target_audience": target_audience[:2] if target_audience else ["general"]
        },
        {
            "question": f"How has {domain_name.lower()} evolved over time?",
            "category": "historical",
            "difficulty": "intermediate",
            "relevance_score": 0.8,
            "expected_answer_type": "analytical",
            "key_topics": topics[:2] if topics else [domain_name.lower()],
            "target_audience": target_audience[:2] if target_audience else ["general"]
        },
        {
            "question": f"What are the best practices for {domain_name.lower()}?",
            "category": "practical",
            "difficulty": "intermediate",
            "relevance_score": 0.85,
            "expected_answer_type": "procedural",
            "key_topics": topics[:2] if topics else [domain_name.lower()],
            "target_audience": target_audience[:2] if target_audience else ["general"]
        },
        {
            "question": f"What are the common challenges in {domain_name.lower()}?",
            "category": "problem-solving",
            "difficulty": "advanced",
            "relevance_score": 0.75,
            "expected_answer_type": "analytical",
            "key_topics": topics[:2] if topics else [domain_name.lower()],
            "target_audience": target_audience[:2] if target_audience else ["general"]
        },
        {
            "question": f"How does {domain_name.lower()} compare to similar domains?",
            "category": "comparative",
            "difficulty": "advanced",
            "relevance_score": 0.7,
            "expected_answer_type": "analytical",
            "key_topics": topics[:2] if topics else [domain_name.lower()],
            "target_audience": target_audience[:2] if target_audience else ["general"]
        },
        {
            "question": f"What are the key metrics for evaluating {domain_name.lower()}?",
            "category": "technical",
            "difficulty": "intermediate",
            "relevance_score": 0.8,
            "expected_answer_type": "factual",
            "key_topics": topics[:2] if topics else [domain_name.lower()],
            "target_audience": target_audience[:2] if target_audience else ["general"]
        },
        {
            "question": f"What are the emerging trends in {domain_name.lower()}?",
            "category": "practical",
            "difficulty": "advanced",
            "relevance_score": 0.75,
            "expected_answer_type": "analytical",
            "key_topics": topics[:2] if topics else [domain_name.lower()],
            "target_audience": target_audience[:2] if target_audience else ["general"]
        },
        {
            "question": f"How can {domain_name.lower()} be applied in real-world scenarios?",
            "category": "practical",
            "difficulty": "intermediate",
            "relevance_score": 0.85,
            "expected_answer_type": "procedural",
            "key_topics": topics[:2] if topics else [domain_name.lower()],
            "target_audience": target_audience[:2] if target_audience else ["general"]
        }
    ]
