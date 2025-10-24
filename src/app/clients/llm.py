"""LLM client (OpenAI GPT)."""

import os
from functools import lru_cache
from typing import Any

from openai import AsyncOpenAI


class LLMClient:
    """LLM client for generating text with GPT."""

    def __init__(self, api_key: str) -> None:
        """Initialize LLM client."""
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Generate text completion.

        Args:
            prompt: User prompt
            system: System prompt
            model: Model name (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            Dictionary with answer and metadata

        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "answer": response.choices[0].message.content,
            "model": model,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Get LLM client (singleton).

    Returns:
        LLMClient instance

    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set")

    return LLMClient(api_key)
