"""Document processing activities."""

from typing import Any

import structlog
from temporalio import activity

from src.app.clients.supabase import get_supabase_client
from src.app.utils.embeddings import generate_text_embeddings
from src.app.utils.text_extraction import extract_text_from_file

logger = structlog.get_logger()


@activity.defn
async def download_document_activity(file_path: str) -> bytes:
    """Download document from Supabase Storage.

    Args:
        file_path: Path to file in Supabase Storage

    Returns:
        File content as bytes

    """
    activity.logger.info("Downloading document", file_path=file_path)

    supabase = get_supabase_client()
    response = supabase.storage.from_("documents").download(file_path)

    activity.logger.info("Document downloaded successfully", size=len(response))
    return response


@activity.defn
async def extract_text_activity(file_data: bytes) -> dict[str, Any]:
    """Extract text content from document.

    Args:
        file_data: Raw file content

    Returns:
        Dictionary containing:
        - text: Full extracted text
        - chunks: List of text chunks for embedding
        - metadata: Extracted metadata (title, author, etc.)
        - entities: Named entities found in text
        - topics: Detected topics

    """
    activity.logger.info("Extracting text from document")

    result = await extract_text_from_file(file_data)

    activity.logger.info(
        "Text extracted successfully",
        text_length=len(result["text"]),
        chunk_count=len(result.get("chunks", [])),
    )

    return result


@activity.defn
async def generate_embeddings_activity(
    full_text: str, chunks: list[str]
) -> dict[str, list[float]]:
    """Generate embeddings for document text.

    Args:
        full_text: Complete document text
        chunks: List of text chunks

    Returns:
        Dictionary mapping chunk indices to embedding vectors

    """
    activity.logger.info("Generating embeddings", chunk_count=len(chunks))

    embeddings = await generate_text_embeddings(chunks)

    activity.logger.info("Embeddings generated successfully", count=len(embeddings))

    return {"embeddings": embeddings}
