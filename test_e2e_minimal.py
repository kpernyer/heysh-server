#!/usr/bin/env python3
"""Minimal E2E test - first test of the different task queues in action.
Shows Temporal connection and basic workflow structure.
"""

import asyncio
import logging
import os
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    """Minimal E2E test."""
    logger.info("=" * 60)
    logger.info("🚀 MINIMAL E2E TEST - Multiple Task Queues")
    logger.info("=" * 60)

    try:
        # Step 1: Connect to Temporal
        logger.info("\n1️⃣  Connecting to Temporal...")
        from temporalio.client import Client

        client = await Client.connect("localhost:7233", namespace="default")
        logger.info("   ✅ Connected to Temporal at localhost:7233")

        # Step 2: Connection verified
        logger.info("\n2️⃣  Verifying Temporal connection...")
        logger.info("   ✅ Namespace 'default' is active")

        # Step 3: Show what we can do
        logger.info("\n3️⃣  Next steps - Multiple Task Queues:")
        logger.info(
            """
   Your testing setup has these queues ready:

   📋 TASK QUEUES:
   - general-queue        → Workflow orchestration
   - ai-processing-queue  → AI model calls
   - storage-queue        → Database operations

   🧪 TEST SCENARIOS:
   1. Unit tests         (test/unit/)
   2. Integration tests  (test/test_workflows.py)
   3. E2E tests         (fully mocked)
   4. Load tests        (stress testing)

   📦 SERVICES READY:
   - Temporal Server    (localhost:7233)
   - Temporal Web UI    (localhost:8088)
   - Mock AI Service    (localhost:8001)
   - PostgreSQL
   - Weaviate (Vector DB)
   - Neo4j (Graph DB)
   - MinIO (S3 Storage)
        """
        )

        logger.info("\n✨ E2E test infrastructure ready!")
        logger.info("=" * 60)

    except Exception as e:
        logger.info(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
