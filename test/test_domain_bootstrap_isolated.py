#!/usr/bin/env python3
"""Isolated Domain Bootstrap Workflow Test - No problematic imports."""

import asyncio
import logging
import os
import sys
from datetime import datetime
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from src.app.models.domain import BootstrapInput
from workflow.domain_bootstrap_workflow_isolated import DomainBootstrapWorkflowIsolated

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_domain_bootstrap_isolated():
    """Test the isolated domain bootstrap workflow."""
    logger.info("=" * 80)
    logger.info("🏗️  ISOLATED DOMAIN BOOTSTRAP WORKFLOW TEST")
    logger.info("=" * 80)
    
    try:
        # Connect to Temporal
        logger.info("1️⃣  Connecting to Temporal...")
        client = await Client.connect(
            "localhost:7233",
            namespace="default",
            data_converter=pydantic_data_converter
        )
        logger.info("   ✅ Connected to Temporal at localhost:7233")
        
        # Create domain bootstrap input
        logger.info("\n2️⃣  Creating domain bootstrap input...")
        domain_input = BootstrapInput(
            domain_id=uuid4(),
            owner_id=uuid4(),
            domain_name="Architect Isac Gustav Clason",
            domain_description="Swedish architect and pioneer of National Romanticism",
            initial_topics=["architecture", "swedish history", "national romanticism"],
            target_audience=["architecture students", "historians"],
            research_focus="Architectural heritage and cultural significance"
        )
        logger.info(f"   ✅ Domain input created: {domain_input.domain_name}")
        
        # Start the workflow
        logger.info("\n3️⃣  Starting Isolated Domain Bootstrap Workflow...")
        from slugify import slugify
        workflow_id_slug = slugify(domain_input.domain_name)
        
        handle = await client.start_workflow(
            DomainBootstrapWorkflowIsolated.run,
            args=[domain_input],
            id=f"domain-bootstrap-isolated-{workflow_id_slug}",
            task_queue="hey-sh-workflows",
        )
        logger.info(f"   ✅ Workflow started with ID: {handle.id}")
        
        # Wait for workflow to complete
        logger.info("\n4️⃣  Waiting for workflow to complete...")
        logger.info("   ⏳ This may take a few minutes for AI research...")
        
        try:
            result = await handle.result()
            logger.info("   ✅ Workflow completed successfully!")
            logger.info(f"   📊 Final result: {result}")
            
        except Exception as e:
            logger.error(f"   ❌ Workflow failed: {e}")
            raise
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 ISOLATED DOMAIN BOOTSTRAP WORKFLOW COMPLETED!")
        logger.info("=" * 80)
        logger.info("💡 Check your OpenRouter dashboard for actual API usage!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


async def main():
    """Main function."""
    await test_domain_bootstrap_isolated()


if __name__ == "__main__":
    asyncio.run(main())
