#!/usr/bin/env python3
"""Domain Bootstrap Approval Script - Human-in-the-Loop Control."""

import asyncio
import logging
import sys
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.insert(0, '/Users/kpernyer/repo/hey-sh-workflow/backend')

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from standalone_domain_bootstrap import StandaloneDomainBootstrapWorkflow

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def approve_domain_bootstrap(workflow_id: str):
    """Approve a domain bootstrap workflow."""
    logger.info("=" * 80)
    logger.info("🎯 DOMAIN BOOTSTRAP APPROVAL")
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
        
        # Get workflow handle
        logger.info(f"\n2️⃣  Getting workflow handle for: {workflow_id}")
        handle = client.get_workflow_handle(workflow_id)
        
        # Check workflow status
        logger.info("\n3️⃣  Checking workflow status...")
        try:
            description = await handle.describe()
            logger.info(f"   📊 Workflow status: {description.status.name}")
            
            if description.status.name not in ["RUNNING", "CONTINUE_AS_NEW"]:
                logger.warning(f"   ⚠️  Workflow is not running (status: {description.status.name})")
                logger.info("   💡 The workflow may have already completed or failed")
                return
                
        except Exception as e:
            logger.error(f"   ❌ Could not get workflow status: {e}")
            return
        
        # Get current bootstrap status
        logger.info("\n4️⃣  Getting current bootstrap status...")
        try:
            status = await handle.query(StandaloneDomainBootstrapWorkflow.get_bootstrap_status)
            logger.info(f"   📋 Current status: {status.get('status', 'unknown')}")
            
            if status.get('domain_config'):
                logger.info("   ⚙️  Domain configuration is ready for review")
                logger.info(f"   🏗️  Domain: {status['domain_config'].get('title', 'Unknown')}")
                logger.info(f"   📝 Description: {status['domain_config'].get('description', 'No description')}")
            
            if status.get('research_results'):
                logger.info("   🔬 Research results are available")
                
        except Exception as e:
            logger.warning(f"   ⚠️  Could not get bootstrap status: {e}")
        
        # Submit approval
        logger.info("\n5️⃣  Submitting approval...")
        approval_feedback = {
            "approved": True,
            "comments": "Approved by human reviewer",
            "quality_rating": "excellent",
            "overall_quality": "excellent",
            "research_depth": "comprehensive",
            "additional_topics": [],
            "remove_topics": [],
            "quality_threshold": 8.0,
            "question_rankings": {
                "What are the fundamental principles?": 5,
                "How did Clason influence architecture?": 4,
                "What are the key architectural features?": 3
            }
        }
        
        await handle.signal(StandaloneDomainBootstrapWorkflow.submit_owner_feedback, approval_feedback)
        logger.info("   ✅ Approval submitted successfully!")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 DOMAIN BOOTSTRAP APPROVED!")
        logger.info("=" * 80)
        logger.info("💡 The workflow will now complete with your approval")
        logger.info("=" * 80)
        
    except ConnectionError as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("💡 Make sure Temporal server is running: just start-temporal")
        raise
    except Exception as e:
        logger.error(f"❌ Approval failed: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error("💡 Check the logs above for more details")
        raise


async def main():
    """Main function."""
    if len(sys.argv) != 2:
        logger.error("Usage: python approve_domain_bootstrap.py <workflow_id>")
        logger.error("Example: python approve_domain_bootstrap.py standalone-bootstrap-architect-isac-gustav-clason")
        sys.exit(1)
    
    workflow_id = sys.argv[1]
    
    try:
        await approve_domain_bootstrap(workflow_id)
    except Exception as e:
        logger.error(f"❌ Main function failed: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
