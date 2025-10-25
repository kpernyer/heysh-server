#!/usr/bin/env python3
"""Standalone Domain Bootstrap Worker - No problematic imports."""

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


async def run_standalone_worker():
    """Run the standalone domain bootstrap worker."""
    logger.info("🚀 Starting Standalone Domain Bootstrap Worker...")
    
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
        
        # Add missing activities that might be called by other workflows
        try:
            from activity.supabase import update_document_metadata_activity
            logger.info("✅ Loaded update_document_metadata_activity")
        except ImportError as e:
            logger.warning(f"⚠️  Could not load update_document_metadata_activity: {e}")
            # Create a mock activity to prevent crashes
            async def update_document_metadata_activity(*args, **kwargs):
                logger.warning("⚠️  update_document_metadata_activity called but not implemented")
                return {"status": "not_implemented", "message": "Activity not available in standalone worker"}
        
        from standalone_domain_bootstrap import StandaloneDomainBootstrapWorkflow
        
        # Create worker
        worker = Worker(
            client,
            task_queue="hey-sh-workflows",
            workflows=[StandaloneDomainBootstrapWorkflow],
            activities=[
                research_domain_activity,
                analyze_research_results_activity,
                generate_domain_config_activity,
                notify_user_activity,
                update_document_metadata_activity,  # Add missing activity
            ],
        )
        
        logger.info("🔄 Starting worker on task queue: hey-sh-workflows")
        logger.info("📋 Registered workflows: StandaloneDomainBootstrapWorkflow")
        logger.info("🔧 Registered activities: domain research, analysis, config generation, notifications, document metadata")
        logger.info("⏳ Worker running... (Press Ctrl+C to stop)")
        
        # Run worker with better error handling
        try:
            await worker.run()
        except Exception as e:
            logger.error(f"❌ Worker execution failed: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            logger.error(f"❌ Error details: {str(e)}")
            raise
        
    except KeyboardInterrupt:
        logger.info("🛑 Worker stopped by user")
    except ConnectionError as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("💡 Make sure Temporal server is running: just start-temporal")
        raise
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        logger.error("💡 Make sure all dependencies are installed: uv pip install -r requirements.txt")
        raise
    except Exception as e:
        logger.error(f"❌ Worker failed: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error("💡 Check the logs above for more details")
        raise


async def main():
    """Main function."""
    await run_standalone_worker()


if __name__ == "__main__":
    asyncio.run(main())
