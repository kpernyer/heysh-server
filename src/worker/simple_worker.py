#!/usr/bin/env python3
"""Simple Temporal worker that only runs activities (no workflows)."""

import asyncio
import logging
import os

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def run_simple_worker():
    """Start a simple Temporal worker using hostname-based configuration."""
    from src.service.config import get_settings

    # Get configuration from Settings (hostname-based)
    settings = get_settings()
    temporal_address = settings.temporal_address
    temporal_namespace = settings.temporal_namespace
    temporal_api_key = settings.temporal_api_key
    task_queue = settings.temporal_task_queue

    logger.info(f"Starting simple Temporal worker: {temporal_address}")
    logger.info(f"Namespace: {temporal_namespace}, Task Queue: {task_queue}")

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

    # Import activities and workflows
    from activity.ai import (
        assess_document_relevance_activity,
        generate_document_summary_activity,
    )
    from workflow.simple_document_workflow import SimpleDocumentWorkflow

    # Create worker with workflow and activities
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[SimpleDocumentWorkflow],
        activities=[
            assess_document_relevance_activity,
            generate_document_summary_activity,
        ],
    )

    logger.info("Simple worker started successfully. Waiting for activities...")

    # Run the worker
    await worker.run()


async def main():
    """Main entrypoint."""
    logger.info("Starting simple Temporal worker...")
    await run_simple_worker()


if __name__ == "__main__":
    asyncio.run(main())
