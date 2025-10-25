#!/usr/bin/env python3
"""Test script for Document Analysis API endpoints.

This demonstrates how to use the REST API to:
1. Start document analysis workflows
2. Check workflow status
3. Submit Controller decisions
4. Query Controller inbox
"""

import asyncio
import logging
import uuid

import httpx

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000"


async def test_document_analysis_api():
    """Test the document analysis API endpoints."""
    logger.info("=" * 80)
    logger.info("🚀 DOCUMENT ANALYSIS API - REST ENDPOINTS TEST")
    logger.info("=" * 80)

    async with httpx.AsyncClient() as client:
        # Test 1: Start document analysis workflow
        logger.info("\n1️⃣  Starting document analysis workflow...")
        workflow_id = await start_document_analysis(client)

        # Test 2: Check workflow status
        logger.info("\n2️⃣  Checking workflow status...")
        await check_workflow_status(client, workflow_id)

        # Test 3: Submit Controller decision (if needed)
        logger.info("\n3️⃣  Submitting Controller decision...")
        await submit_controller_decision(client, workflow_id)

        # Test 4: Query Controller inbox
        logger.info("\n4️⃣  Querying Controller inbox...")
        await query_controller_inbox(client)

        logger.info("\n✅ All API tests completed!")


async def start_document_analysis(client: httpx.AsyncClient) -> str:
    """Start a document analysis workflow via API."""
    document_id = str(uuid.uuid4())

    request_data = {
        "document_id": document_id,
        "domain_id": str(uuid.uuid4()),
        "file_path": f"documents/{document_id}/test-document.pdf",
        "contributor_id": "contributor-123",
        "domain_criteria": {
            "topics": ["technology", "AI", "machine learning"],
            "min_length": 1000,
            "quality_threshold": 8.0,
        },
        "auto_approve_threshold": 8.0,
        "relevance_threshold": 7.0,
    }

    response = await client.post(
        f"{API_BASE_URL}/api/v1/analysis/documents", json=request_data, timeout=30.0
    )

    if response.status_code == 202:
        result = response.json()
        logger.info(f"   ✅ Workflow started: {result['workflow_id']}")
        logger.info(f"   📄 Document ID: {document_id}")
        logger.info(f"   📊 Status: {result['status']}")
        logger.info(f"   💬 Message: {result['message']}")
        return result["workflow_id"]
    else:
        logger.error(f"   ❌ Failed to start workflow: {response.status_code}")
        logger.error(f"   📄 Response: {response.text}")
        raise Exception(f"Failed to start workflow: {response.status_code}")


async def check_workflow_status(client: httpx.AsyncClient, workflow_id: str):
    """Check workflow status via API."""
    response = await client.get(
        f"{API_BASE_URL}/api/v1/analysis/workflows/{workflow_id}/status", timeout=10.0
    )

    if response.status_code == 200:
        result = response.json()
        logger.info("   ✅ Workflow status retrieved")
        logger.info(f"   📊 Status: {result['status']}")
        logger.info(f"   📈 Relevance score: {result.get('relevance_score', 'N/A')}")
        logger.info(
            f"   ✅ Analysis completed: {result.get('analysis_completed', False)}"
        )
        logger.info(
            f"   👤 Controller decision: {result.get('controller_decision', 'N/A')}"
        )
        logger.info(f"   🆔 Controller ID: {result.get('controller_id', 'N/A')}")
    else:
        logger.error(f"   ❌ Failed to get status: {response.status_code}")
        logger.error(f"   📄 Response: {response.text}")


async def submit_controller_decision(client: httpx.AsyncClient, workflow_id: str):
    """Submit Controller decision via API."""
    decision_data = {
        "decision": "approve",  # or "reject"
        "controller_id": "controller-456",
        "feedback": "Good content, approved for publication",
    }

    response = await client.post(
        f"{API_BASE_URL}/api/v1/analysis/workflows/{workflow_id}/controller-decision",
        json=decision_data,
        timeout=10.0,
    )

    if response.status_code == 200:
        result = response.json()
        logger.info("   ✅ Controller decision submitted")
        logger.info(f"   📊 Decision: {result['decision']}")
        logger.info(f"   👤 Controller: {result['controller_id']}")
        logger.info(f"   📊 Status: {result['status']}")
    else:
        logger.error(f"   ❌ Failed to submit decision: {response.status_code}")
        logger.error(f"   📄 Response: {response.text}")


async def query_controller_inbox(client: httpx.AsyncClient):
    """Query Controller inbox via API."""
    controller_id = "controller-456"

    response = await client.get(
        f"{API_BASE_URL}/api/v1/analysis/controller/inbox",
        params={"controller_id": controller_id},
        timeout=10.0,
    )

    if response.status_code == 200:
        result = response.json()
        logger.info("   ✅ Controller inbox retrieved")
        logger.info(f"   👤 Controller ID: {result['controller_id']}")
        logger.info(f"   📊 Pending count: {result['pending_count']}")
        logger.info("   📋 Items:")

        for item in result["items"]:
            logger.info(f"      📄 Document: {item['document_id']}")
            logger.info(f"      👤 Contributor: {item['contributor_id']}")
            logger.info(f"      📈 Score: {item['relevance_score']}")
            logger.info(f"      ⏰ Due: {item['due_at']}")
            logger.info(f"      🔥 Priority: {item['priority']}")
    else:
        logger.error(f"   ❌ Failed to get inbox: {response.status_code}")
        logger.error(f"   📄 Response: {response.text}")


async def test_multiple_scenarios():
    """Test multiple document analysis scenarios."""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 TESTING MULTIPLE DOCUMENT SCENARIOS")
    logger.info("=" * 80)

    async with httpx.AsyncClient() as client:
        # Scenario 1: High quality document (auto-approve)
        logger.info("\n📄 Scenario 1: High quality document")
        await test_scenario(client, "high-quality", 9.5)

        # Scenario 2: Medium quality document (needs review)
        logger.info("\n📄 Scenario 2: Medium quality document")
        await test_scenario(client, "medium-quality", 7.5)

        # Scenario 3: Low quality document (reject)
        logger.info("\n📄 Scenario 3: Low quality document")
        await test_scenario(client, "low-quality", 5.0)


async def test_scenario(
    client: httpx.AsyncClient, scenario_name: str, expected_score: float
):
    """Test a specific document analysis scenario."""
    document_id = str(uuid.uuid4())

    request_data = {
        "document_id": document_id,
        "domain_id": str(uuid.uuid4()),
        "file_path": f"documents/{document_id}/{scenario_name}.pdf",
        "contributor_id": f"contributor-{scenario_name}",
        "domain_criteria": {
            "topics": ["technology", "AI", "machine learning"],
            "min_length": 1000,
            "quality_threshold": 8.0,
        },
        "auto_approve_threshold": 8.0,
        "relevance_threshold": 7.0,
    }

    # Start workflow
    response = await client.post(
        f"{API_BASE_URL}/api/v1/analysis/documents", json=request_data, timeout=30.0
    )

    if response.status_code == 202:
        result = response.json()
        workflow_id = result["workflow_id"]
        logger.info(f"   ✅ {scenario_name} workflow started: {workflow_id}")

        # Wait a bit for processing
        await asyncio.sleep(2)

        # Check status
        status_response = await client.get(
            f"{API_BASE_URL}/api/v1/analysis/workflows/{workflow_id}/status",
            timeout=10.0,
        )

        if status_response.status_code == 200:
            status_result = status_response.json()
            logger.info(f"   📊 Status: {status_result['status']}")
            logger.info(f"   📈 Score: {status_result.get('relevance_score', 'N/A')}")

            # If needs review, submit decision
            if status_result["status"] == "pending_review":
                decision_data = {
                    "decision": "approve",
                    "controller_id": f"controller-{scenario_name}",
                    "feedback": f"Approved {scenario_name} document",
                }

                decision_response = await client.post(
                    f"{API_BASE_URL}/api/v1/analysis/workflows/{workflow_id}/controller-decision",
                    json=decision_data,
                    timeout=10.0,
                )

                if decision_response.status_code == 200:
                    logger.info(
                        f"   ✅ Controller decision submitted for {scenario_name}"
                    )
                else:
                    logger.error(f"   ❌ Failed to submit decision for {scenario_name}")
        else:
            logger.error(f"   ❌ Failed to get status for {scenario_name}")
    else:
        logger.error(f"   ❌ Failed to start {scenario_name} workflow")


async def main():
    """Main test execution."""
    try:
        await test_document_analysis_api()
        await test_multiple_scenarios()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
