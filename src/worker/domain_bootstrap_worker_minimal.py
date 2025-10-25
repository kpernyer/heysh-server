#!/usr/bin/env python3
"""Minimal Domain Bootstrap Worker - No problematic imports."""

import asyncio
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def run_domain_bootstrap_worker():
    """Run the domain bootstrap worker."""
    logger.info("🚀 Starting Minimal Domain Bootstrap Worker...")
    
    try:
        # Connect to Temporal
        client = await Client.connect(
            "localhost:7233",
            namespace="default",
            data_converter=pydantic_data_converter
        )
        logger.info("✅ Connected to Temporal at localhost:7233")
        
        # Import activities and workflows here to avoid sandbox issues
        from activity.domain_research import (
            analyze_research_results_activity,
            generate_domain_config_activity,
            research_domain_activity,
        )
        from activity.notification import notify_user_activity
        from workflow.domain_bootstrap_workflow import DomainBootstrapWorkflow
        
        # Create worker
        worker = Worker(
            client,
            task_queue="hey-sh-workflows",
            workflows=[DomainBootstrapWorkflow],
            activities=[
                research_domain_activity,
                analyze_research_results_activity,
                generate_domain_config_activity,
                notify_user_activity,
            ],
        )
        
        logger.info("🔄 Starting worker on task queue: hey-sh-workflows")
        logger.info("📋 Registered workflows: DomainBootstrapWorkflow")
        logger.info("🔧 Registered activities: domain research, analysis, config generation, notifications")
        logger.info("⏳ Worker running... (Press Ctrl+C to stop)")
        
        # Run worker
        await worker.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Worker failed: {e}")
        raise


async def main():
    """Main function."""
    await run_domain_bootstrap_worker()


if __name__ == "__main__":
    asyncio.run(main())
