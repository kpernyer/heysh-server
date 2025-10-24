"""Smoke tests for staging environment.
Quick tests to verify basic functionality after deployment.
"""

import asyncio
import logging
import sys
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from temporalio.client import Client

from workflow.document_contribution_workflow import (
    DocumentContributionInput,
    DocumentContributionWorkflow,
)


async def test_temporal_connection():
    """Test connection to Temporal."""
    logger.info("🔌 Testing Temporal connection...")
    try:
        client = await Client.connect("localhost:7233", namespace="staging")
        logger.info("  ✅ Connected to Temporal")
        return client
    except Exception as e:
        logger.error(f"  ❌ Failed to connect to Temporal: {e}")
        return None


async def test_workflow_execution(client):
    """Test basic workflow execution."""
    logger.info("🔄 Testing workflow execution...")

    workflow_input = DocumentContributionInput(
        document_id=str(uuid.uuid4()),
        document_path="/smoke-test/document.pdf",
        contributor_id="smoke-test-contributor",
        domain_id="smoke-test-domain",
        domain_criteria={"test": "smoke"},
        auto_approve_threshold=8.5,
        relevance_threshold=7.0,
    )

    try:
        handle = await client.start_workflow(
            DocumentContributionWorkflow.run,
            workflow_input,
            id=f"smoke-test-{uuid.uuid4()}",
            task_queue="general-queue",
        )

        # Wait for workflow to complete (with timeout)
        result = await asyncio.wait_for(handle.result(), timeout=30)

        if result.success:
            logger.info(f"  ✅ Workflow completed successfully: {result.status}")
        else:
            logger.info(f"  ⚠️ Workflow completed with error: {result.error}")

        return True

    except TimeoutError:
        logger.info("  ❌ Workflow execution timeout")
        return False
    except Exception as e:
        logger.info(f"  ❌ Workflow execution failed: {e}")
        return False


async def test_worker_health():
    """Test worker health endpoints."""
    logger.info("🏥 Testing worker health...")

    import aiohttp

    workers = [
        ("AI Worker", "http://ai-processing-worker:8080/health"),
        ("Storage Worker", "http://storage-worker:8080/health"),
        ("General Worker", "http://general-worker:8080/health"),
    ]

    async with aiohttp.ClientSession() as session:
        for name, url in workers:
            try:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        logger.info(f"  ✅ {name} is healthy")
                    else:
                        logger.info(f"  ⚠️ {name} returned status {resp.status}")
            except Exception as e:
                logger.info(f"  ❌ {name} health check failed: {e}")


async def test_database_connections():
    """Test database connections."""
    logger.info("🗄️ Testing database connections...")

    # Test Neo4j
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            "bolt://neo4j:7687", auth=("neo4j", "testpassword")
        )
        with driver.session() as session:
            session.run("RETURN 1")
            logger.info("  ✅ Neo4j connection successful")
    except Exception as e:
        logger.info(f"  ❌ Neo4j connection failed: {e}")

    # Test Weaviate
    try:
        import weaviate

        client = weaviate.Client("http://weaviate:8080")
        client.schema.get()
        logger.info("  ✅ Weaviate connection successful")
    except Exception as e:
        logger.info(f"  ❌ Weaviate connection failed: {e}")


async def main():
    """Run all smoke tests."""
    logger.info("🧪 Running Staging Smoke Tests")
    logger.info("=" * 50)

    all_passed = True

    # Test Temporal connection
    client = await test_temporal_connection()
    if not client:
        all_passed = False
    else:
        # Test workflow execution
        if not await test_workflow_execution(client):
            all_passed = False

    # Test worker health
    await test_worker_health()

    # Test database connections
    await test_database_connections()

    logger.info("=" * 50)

    if all_passed:
        logger.info("✅ All smoke tests passed!")
        sys.exit(0)
    else:
        logger.info("❌ Some smoke tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
