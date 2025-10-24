#!/usr/bin/env python3
"""Standalone Domain Bootstrap Workflow Test - No problematic imports."""

import asyncio
import logging
import os
import sys
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from standalone_domain_bootstrap import BootstrapInput, StandaloneDomainBootstrapWorkflow

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_standalone_bootstrap():
    """Test the standalone domain bootstrap workflow."""
    logger.info("=" * 80)
    logger.info("🏗️  STANDALONE DOMAIN BOOTSTRAP WORKFLOW TEST")
    logger.info("=" * 80)
    
    try:
        # Connect to Temporal
        logger.info("1️⃣  Connecting to Temporal...")
        try:
            client = await Client.connect(
                "localhost:7233",
                namespace="default",
                data_converter=pydantic_data_converter
            )
            logger.info("   ✅ Connected to Temporal at localhost:7233")
        except ConnectionError as e:
            logger.error(f"   ❌ Failed to connect to Temporal: {e}")
            logger.error("   💡 Make sure Temporal server is running: just start-temporal")
            raise
        except Exception as e:
            logger.error(f"   ❌ Unexpected error connecting to Temporal: {e}")
            raise
        
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
        logger.info("\n3️⃣  Starting Standalone Domain Bootstrap Workflow...")
        from slugify import slugify
        workflow_id_slug = slugify(domain_input.domain_name)
        workflow_id = f"standalone-bootstrap-{workflow_id_slug}"
        
        try:
            handle = await client.start_workflow(
                StandaloneDomainBootstrapWorkflow.run,
                args=[domain_input],
                id=workflow_id,
                task_queue="hey-sh-workflows",
            )
            logger.info(f"   ✅ Workflow started with ID: {handle.id}")
        except Exception as e:
            logger.error(f"   ❌ Failed to start workflow: {e}")
            logger.error(f"   ❌ Error type: {type(e).__name__}")
            if "Workflow execution is already running" in str(e):
                logger.warning(f"   ⚠️  Workflow {workflow_id} is already running!")
                logger.info("   🔍 Checking existing workflow status...")
                
                # Get the existing workflow handle
                handle = client.get_workflow_handle(workflow_id)
                
                # Check if it's still running
                try:
                    description = await handle.describe()
                    logger.info(f"   📊 Existing workflow status: {description.status.name}")
                    
                    if description.status.name in ["RUNNING", "CONTINUE_AS_NEW"]:
                        logger.info("   ⏳ Workflow is still running - will wait for completion...")
                    else:
                        logger.info("   🔄 Workflow is not running - will start a new one...")
                        # Start a new workflow with a unique ID
                        import time
                        unique_id = f"{workflow_id}-{int(time.time())}"
                        handle = await client.start_workflow(
                            StandaloneDomainBootstrapWorkflow.run,
                            args=[domain_input],
                            id=unique_id,
                            task_queue="hey-sh-workflows",
                        )
                        logger.info(f"   ✅ New workflow started with ID: {handle.id}")
                except Exception as describe_error:
                    logger.warning(f"   ⚠️  Could not describe existing workflow: {describe_error}")
                    logger.info("   🔄 Starting a new workflow with unique ID...")
                    import time
                    unique_id = f"{workflow_id}-{int(time.time())}"
                    handle = await client.start_workflow(
                        StandaloneDomainBootstrapWorkflow.run,
                        args=[domain_input],
                        id=unique_id,
                        task_queue="hey-sh-workflows",
                    )
                    logger.info(f"   ✅ New workflow started with ID: {handle.id}")
            else:
                logger.error(f"   ❌ Failed to start workflow: {e}")
                raise
        
        # Wait for workflow to complete
        logger.info("\n4️⃣  Waiting for workflow to complete...")
        logger.info("   ⏳ This may take a few minutes for AI research...")
        logger.info("   💰 Real OpenRouter API calls are being made (check your dashboard for costs)")
        logger.info("")
        logger.info("   🚨 IMPORTANT: The workflow will wait for YOUR APPROVAL!")
        logger.info("   📋 In another terminal, run this command to approve:")
        logger.info(f"   python approve_domain_bootstrap.py {handle.id}")
        logger.info("   ⏰ Or wait 30 seconds for auto-approval (demo mode)")
        
        try:
            result = await handle.result()
            logger.info("   ✅ Workflow completed successfully!")
            logger.info(f"   📊 Final result: {result}")
            
            if result.success:
                logger.info("   🎉 Domain bootstrap completed successfully!")
                logger.info(f"   🏗️  Domain ID: {result.domain_id}")
                logger.info(f"   📈 Status: {result.status.value}")
                if result.domain_config:
                    logger.info("   ⚙️  Domain configuration generated")
                if result.research_results:
                    logger.info("   🔬 Research results available")
            else:
                logger.warning("   ⚠️  Workflow completed but with issues")
                logger.warning(f"   📝 Message: {result.message}")
                if result.error_message:
                    logger.warning(f"   ❌ Error: {result.error_message}")
            
        except Exception as e:
            logger.error(f"   ❌ Workflow failed: {e}")
            logger.info("   🔍 You can check the workflow status with:")
            logger.info(f"   temporal workflow show --workflow-id {handle.id}")
            raise
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 STANDALONE DOMAIN BOOTSTRAP WORKFLOW COMPLETED!")
        logger.info("=" * 80)
        logger.info("💡 Check your OpenRouter dashboard for actual API usage!")
        logger.info("=" * 80)
        
    except ConnectionError as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("💡 Make sure Temporal server is running: just start-temporal")
        logger.error("💡 Make sure worker is running: just start-domain-bootstrap-worker")
        raise
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        logger.error("💡 Make sure all dependencies are installed: uv pip install -r requirements.txt")
        raise
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error("💡 Check the logs above for more details")
        raise


async def main():
    """Main function."""
    await test_standalone_bootstrap()


if __name__ == "__main__":
    asyncio.run(main())
