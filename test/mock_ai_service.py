"""Mock AI Service for testing workflows without real API calls."""

import asyncio
import logging
import os
import random
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock AI Service")


class AIRequest(BaseModel):
    model: str
    function_name: str
    inputs: dict[str, Any]
    config: dict[str, Any] = {}


class MockResponses:
    """Predefined responses for different AI functions."""

    @staticmethod
    def assess_relevance(inputs: dict[str, Any]) -> dict[str, Any]:
        """Mock relevance assessment."""
        # Get configurable score or random
        default_score = float(os.getenv("DEFAULT_RELEVANCE_SCORE", "7.5"))

        # Add some randomness for testing different paths
        if os.getenv("RANDOMIZE_SCORES", "false").lower() == "true":
            score = random.uniform(3.0, 9.5)
        else:
            score = default_score

        return {
            "relevance_score": score,
            "topics": ["technology", "AI", "workflows", "testing"],
            "entities": ["Temporal", "Document Processing", "Mock Entity"],
            "assessment_details": f"Mock assessment with score {score}",
        }

    @staticmethod
    def controller_review(inputs: dict[str, Any]) -> dict[str, Any]:
        """Mock controller review decision."""
        relevance_score = inputs.get("relevance_score", 5.0)

        # Simple logic: approve if score > 5
        approved = relevance_score > 5.0

        return {
            "approved": approved,
            "feedback": "Mock review completed",
            "rejection_reason": None if approved else "Score too low in mock review",
        }

    @staticmethod
    def generate_summary(inputs: dict[str, Any]) -> dict[str, Any]:
        """Mock summary generation."""
        return {
            "summary": "This is a mock summary of the document. It contains important information about testing workflows.",
            "key_points": [
                "Mock point 1: Document processing",
                "Mock point 2: Workflow testing",
                "Mock point 3: Quality assurance",
            ],
        }

    @staticmethod
    def extract_content(inputs: dict[str, Any]) -> dict[str, Any]:
        """Mock content extraction."""
        return {
            "extracted_text": "Mock extracted content from document. Lorem ipsum dolor sit amet...",
            "metadata": {
                "title": "Mock Document",
                "author": "Test Author",
                "pages": 10,
                "language": "en",
            },
            "chunks": [
                "Chunk 1: Introduction to testing",
                "Chunk 2: Main content about workflows",
                "Chunk 3: Conclusion and summary",
            ],
        }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mock-ai"}


@app.post("/api/v1/ai/execute")
async def execute_ai_function(request: AIRequest):
    """Mock AI execution endpoint.
    Routes to appropriate mock function based on function_name.
    """
    logger.info(f"Mock AI request: {request.function_name}")

    # Add configurable delay to simulate processing
    delay = float(os.getenv("DEFAULT_RESPONSE_DELAY", "0.5"))
    await asyncio.sleep(delay)

    # Route to appropriate mock function
    mock_responses = MockResponses()

    function_map = {
        "assess_relevance": mock_responses.assess_relevance,
        "controller_review": mock_responses.controller_review,
        "generate_summary": mock_responses.generate_summary,
        "extract_content": mock_responses.extract_content,
        "assess_document_quality": mock_responses.assess_relevance,
        "generate_personalized_welcome": mock_responses.generate_summary,
    }

    handler = function_map.get(request.function_name)

    if not handler:
        # Return generic response for unknown functions
        logger.warning(f"Unknown function: {request.function_name}")
        return {
            "result": f"Mock response for {request.function_name}",
            "success": True,
        }

    try:
        response = handler(request.inputs)
        return response
    except Exception as e:
        logger.error(f"Error in mock handler: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/embeddings")
async def generate_embeddings(texts: list[str]):
    """Mock embedding generation."""
    logger.info(f"Generating mock embeddings for {len(texts)} texts")

    # Return random embeddings
    embeddings = []
    for _ in texts:
        # Mock 1536-dimensional embedding (like OpenAI)
        embedding = [random.random() for _ in range(1536)]
        embeddings.append(embedding)

    return {"embeddings": embeddings}


@app.get("/api/v1/models")
async def list_models():
    """List available mock models."""
    return {
        "models": [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
