"""Main Temporal worker process."""

import asyncio
import os

import structlog
import uvicorn
from fastapi import FastAPI, Response
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from activity import (
    apply_review_decision_activity,
    assign_review_activity,
    calculate_confidence_activity,
    create_review_task_activity,
    download_document_activity,
    extract_text_activity,
    find_related_documents_activity,
    generate_answer_activity,
    generate_embeddings_activity,
    index_weaviate_activity,
    notify_contributor_activity,
    search_documents_activity,
    store_question_activity,
    update_document_metadata_activity,
    update_neo4j_graph_activity,
    update_quality_score_activity,
    update_question_activity,
)
from activity.domain import (
    index_domain_activity,
    search_domains_activity,
)
from workflow import (
    DocumentProcessingWorkflow,
    QualityReviewWorkflow,
    QuestionAnsweringWorkflow,
)

logger = structlog.get_logger()

# Create a minimal FastAPI app for the health check
app = FastAPI()


@app.get("/health", status_code=200)
async def health_check():
    """Health check endpoint for Cloud Run."""
    return Response(status_code=200)


async def run_temporal_worker():
    """Start Temporal worker."""
    # Get configuration from environment
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "hey-sh-workflows")

    logger.info(
        "Starting Temporal worker",
        address=temporal_address,
        namespace=temporal_namespace,
        task_queue=task_queue,
    )

    # Configure connection based on environment
    connect_config = {
        "namespace": temporal_namespace,
    }

    # Add TLS and API key for Temporal Cloud
    if temporal_api_key:
        from temporalio.client import TLSConfig

        connect_config["tls"] = TLSConfig()
        connect_config["api_key"] = temporal_api_key
        logger.info("Using Temporal Cloud with TLS and API key authentication")
    else:
        logger.info("Using local Temporal server (no TLS)")

    # Connect to Temporal server
    client = await Client.connect(
        temporal_address,
        data_converter=pydantic_data_converter,
        **connect_config,
    )

    # Create worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            DocumentProcessingWorkflow,
            QuestionAnsweringWorkflow,
            QualityReviewWorkflow,
        ],
        activities=[
            # Document activities
            download_document_activity,
            extract_text_activity,
            generate_embeddings_activity,
            # Search activities
            search_documents_activity,
            find_related_documents_activity,
            index_weaviate_activity,
            update_neo4j_graph_activity,
            # LLM activities
            generate_answer_activity,
            calculate_confidence_activity,
            # Supabase activities
            store_question_activity,
            update_question_activity,
            update_document_metadata_activity,
            create_review_task_activity,
            assign_review_activity,
            apply_review_decision_activity,
            update_quality_score_activity,
            notify_contributor_activity,
            # Domain activities
            index_domain_activity,
            search_domains_activity,
        ],
    )

    logger.info("Worker started successfully. Waiting for tasks...")

    # Run the worker
    await worker.run()


async def run_web_server():
    """Start the health check web server."""
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting health check server on port {port}")
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Main entrypoint.

    If the PORT environment variable is set (indicating a Cloud Run environment),
    it runs the Temporal worker and the health check web server concurrently.
    Otherwise (for local development), it runs only the Temporal worker.
    """
    is_cloud_run = "PORT" in os.environ

    if is_cloud_run:
        logger.info(
            "Cloud Run environment detected. Starting worker and health check server."
        )
        await asyncio.gather(run_temporal_worker(), run_web_server())
    else:
        logger.info("Local environment detected. Starting worker only.")
        await run_temporal_worker()


if __name__ == "__main__":
    asyncio.run(main())
