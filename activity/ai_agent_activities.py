"""AI Agent activities for Temporal workflows
These activities execute AI agent tasks defined in workflow YAML
"""

import asyncio
from typing import Any

import anthropic
import openai
from temporalio import activity


class AIAgentError(Exception):
    """Raised when AI agent execution fails"""

    pass


@activity.defn(name="ai-agent.execute")
async def execute_ai_agent_activity(
    actor_config: dict[str, Any], function_name: str, inputs: dict[str, Any]
) -> dict[str, Any]:
    """Generic AI agent activity executor

    Args:
        actor_config: AI agent configuration (model, system_prompt, etc.)
        function_name: The function to execute
        inputs: Input parameters

    Returns:
        Dictionary with outputs from AI agent

    """
    activity.logger.info(
        f"Executing AI agent activity: {function_name} with model {actor_config.get('model')}"
    )

    model = actor_config.get("model")
    system_prompt = actor_config.get("system_prompt", "")
    temperature = actor_config.get("temperature", 0.7)
    max_tokens = actor_config.get("max_tokens", 2000)

    # Route to appropriate AI provider
    if model.startswith("claude"):
        return await _execute_claude(
            model, system_prompt, temperature, max_tokens, function_name, inputs
        )
    elif model.startswith("gpt"):
        return await _execute_openai(
            model, system_prompt, temperature, max_tokens, function_name, inputs
        )
    else:
        raise AIAgentError(f"Unsupported AI model: {model}")


async def _execute_claude(
    model: str,
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    function_name: str,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Execute using Anthropic Claude"""
    client = anthropic.AsyncAnthropic()

    # Build user prompt from function name and inputs
    user_prompt = _build_prompt(function_name, inputs)

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else None,
            messages=[{"role": "user", "content": user_prompt}],
        )

        result_text = response.content[0].text

        # Parse result based on function name
        return _parse_result(function_name, result_text, inputs)

    except Exception as e:
        raise AIAgentError(f"Claude execution failed: {e}")


async def _execute_openai(
    model: str,
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    function_name: str,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Execute using OpenAI GPT"""
    client = openai.AsyncOpenAI()

    user_prompt = _build_prompt(function_name, inputs)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        result_text = response.choices[0].message.content

        return _parse_result(function_name, result_text, inputs)

    except Exception as e:
        raise AIAgentError(f"OpenAI execution failed: {e}")


def _build_prompt(function_name: str, inputs: dict[str, Any]) -> str:
    """Build prompt based on function name and inputs"""
    # Map function names to prompt templates
    prompts = {
        "extract_document_content": """
Extract the following information from this document:

Document: {document_text}

Please extract:
1. Full text content
2. Metadata (title, author, date if available)
3. Key sections and structure

Return in a structured format.
""",
        "summarize_content": """
Summarize the following content concisely:

{extracted_text}

Provide:
1. A brief summary (max {max_length} words)
2. Key points as a list
""",
        "assess_document_quality": """
Assess the quality of this document:

Document: {document_text}
Summary: {summary}

Evaluate:
1. Quality score (0-10)
2. Compliance status (compliant/non-compliant/needs-review)
3. List any issues found

Consider domain policies: {domain_policies}
""",
        "generate_personalized_welcome": """
Generate a personalized welcome message for:

Customer Data: {customer_data}
Industry: {industry}

Create:
1. Welcome email content (warm, professional)
2. Onboarding plan with suggested steps
""",
        "validate_customer_data": """
Validate this customer data:

{customer_data}

Check for:
1. Valid email format
2. Required fields present
3. Data consistency
4. Potential enrichment opportunities

Return validation status and enriched data.
""",
    }

    template = prompts.get(
        function_name,
        f"Execute the function '{function_name}' with these inputs:\n{{inputs}}",
    )

    # Format template with inputs
    try:
        return template.format(**inputs, inputs=inputs)
    except KeyError:
        # If formatting fails, use generic template
        inputs_str = "\n".join([f"- {k}: {v}" for k, v in inputs.items()])
        return f"Execute {function_name}:\n{inputs_str}"


def _parse_result(
    function_name: str, result_text: str, inputs: dict[str, Any]
) -> dict[str, Any]:
    """Parse AI result into structured outputs
    This is simplified - in production, you'd use structured outputs or JSON parsing
    """
    # For now, return simple structured output
    # In production, you'd parse the AI response more carefully

    if function_name == "extract_document_content":
        return {
            "extracted_text": result_text,
            "metadata": {"title": "Extracted Document"},
            "image_urls": [],
        }

    elif function_name == "summarize_content":
        # Split into summary and key points (simplified)
        return {
            "summary": result_text[:500],
            "key_points": [
                result_text[i : i + 100] for i in range(0, len(result_text), 100)
            ][:3],
        }

    elif function_name == "assess_document_quality":
        return {
            "quality_score": 7.5,  # Would parse from AI response
            "compliance_status": "compliant",
            "issues": [],
        }

    elif function_name == "generate_personalized_welcome":
        return {
            "welcome_email": result_text[:1000],
            "onboarding_plan": {"steps": ["Step 1", "Step 2", "Step 3"]},
        }

    elif function_name == "validate_customer_data":
        return {
            "valid": True,
            "validation_errors": [],
            "enriched_data": inputs.get("customer_data", {}),
        }

    else:
        # Generic output
        return {"result": result_text, "success": True}


# Specific activity implementations for common functions


@activity.defn(name="extract_document_content")
async def extract_document_content(
    document_id: str, extract_images: bool = False
) -> dict[str, Any]:
    """Extract content from a document"""
    # Placeholder - would integrate with actual document storage
    activity.logger.info(f"Extracting content from document {document_id}")

    # Simulate extraction
    await asyncio.sleep(1)

    return {
        "extracted_text": f"Content of document {document_id}",
        "metadata": {"title": "Sample Document", "author": "Unknown"},
        "image_urls": [] if not extract_images else ["https://example.com/img1.png"],
    }


@activity.defn(name="publish_to_knowledge_base")
async def publish_to_knowledge_base(
    document_id: str, tags: list = None
) -> dict[str, Any]:
    """Publish document to knowledge base"""
    activity.logger.info(f"Publishing document {document_id} to knowledge base")

    await asyncio.sleep(0.5)

    return {
        "published_url": f"https://kb.example.com/docs/{document_id}",
        "indexed": True,
    }


@activity.defn(name="archive_rejected_document")
async def archive_rejected_document(
    document_id: str, reason: str = None
) -> dict[str, Any]:
    """Archive a rejected document"""
    activity.logger.info(f"Archiving document {document_id}, reason: {reason}")

    await asyncio.sleep(0.3)

    return {"archived": True}


@activity.defn(name="notify_user")
async def notify_user(
    user_id: str, status: str, feedback: str = None
) -> dict[str, Any]:
    """Send notification to user"""
    activity.logger.info(f"Notifying user {user_id} about status: {status}")

    await asyncio.sleep(0.2)

    return {"notification_sent": True}
