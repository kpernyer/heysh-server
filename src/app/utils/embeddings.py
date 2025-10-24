"""Embedding generation utilities."""

import os

from openai import AsyncOpenAI


async def generate_text_embeddings(chunks: list[str]) -> list[list[float]]:
    """Generate embeddings for text chunks.

    Args:
        chunks: List of text chunks

    Returns:
        List of embedding vectors

    """
    if not chunks:
        return []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set")

    client = AsyncOpenAI(api_key=api_key)

    # Generate embeddings using OpenAI
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=chunks,
    )

    embeddings = [item.embedding for item in response.data]
    return embeddings


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding for a single text string.

    Args:
        text: Text string to embed

    Returns:
        Embedding vector

    """
    embeddings = await generate_text_embeddings([text])
    return embeddings[0] if embeddings else []
