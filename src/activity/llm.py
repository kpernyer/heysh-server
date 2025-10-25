"""LLM-related activities."""

from typing import Any

import structlog
from temporalio import activity

from src.app.clients.llm import get_llm_client
from src.app.utils.prompts import load_prompt, render_prompt

logger = structlog.get_logger()


@activity.defn
async def generate_answer_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Generate answer to question using LLM.

    Args:
        data: Contains question, context, and domain_id

    Returns:
        Dictionary with generated answer and metadata

    """
    activity.logger.info("Generating answer with LLM", question=data["question"][:50])

    llm = get_llm_client()

    # Load and render the Q&A prompt
    prompt_template = load_prompt("api-calling/question-answering.v1.prompt.yaml")
    rendered_prompt = render_prompt(
        prompt_template,
        {
            "question": data["question"],
            "context": data["context"],
            "domain_id": data["domain_id"],
        },
    )

    # Generate answer
    response = await llm.generate(
        prompt=rendered_prompt["user"],
        system=rendered_prompt.get("system", ""),
        model=rendered_prompt.get("model", "gpt-4o"),
        temperature=rendered_prompt.get("temperature", 0.3),
        max_tokens=rendered_prompt.get("max_tokens", 2000),
    )

    activity.logger.info(
        "Answer generated successfully", length=len(response["answer"])
    )

    return {
        "answer": response["answer"],
        "model": response["model"],
        "usage": response.get("usage", {}),
    }


@activity.defn
async def calculate_confidence_activity(data: dict[str, Any]) -> float:
    """Calculate confidence score for an answer.

    Args:
        data: Contains question, answer, and context

    Returns:
        Confidence score between 0 and 1

    """
    activity.logger.info("Calculating confidence score")

    llm = get_llm_client()

    # Use LLM to self-assess confidence
    confidence_prompt = f"""
    Given the following question and answer, assess the confidence level of the answer
    based on the provided context. Return a score between 0.0 and 1.0.

    Question: {data["question"]}
    Answer: {data["answer"]}

    Context available: {len(data["context"])} documents

    Respond with only a single number between 0.0 and 1.0, representing the confidence score.
    """

    response = await llm.generate(
        prompt=confidence_prompt,
        model="gpt-4o-mini",
        temperature=0.0,
        max_tokens=10,
    )

    # Parse confidence score from response
    try:
        confidence = float(response["answer"].strip())
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
    except ValueError:
        activity.logger.warning("Failed to parse confidence score, using default 0.5")
        confidence = 0.5

    activity.logger.info("Confidence calculated", score=confidence)
    return confidence
