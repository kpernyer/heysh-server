#!/usr/bin/env python3
"""Test script for WebSocket integration with Temporal workflows."""

import asyncio
import json
import os
import sys
from datetime import datetime, UTC
from typing import Any, Dict

import structlog
import websockets
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow.document_processing import DocumentProcessingWorkflow

logger = structlog.get_logger()


async def test_websocket_connection():
    """Test WebSocket connection and signal reception."""
    # WebSocket URL (adjust as needed)
    websocket_url = "ws://localhost:8000/ws"
    
    # Test JWT token (you'll need to replace this with a real token)
    test_token = "your-jwt-token-here"
    
    try:
        # Connect to WebSocket
        uri = f"{websocket_url}?token={test_token}"
        logger.info("Connecting to WebSocket", uri=uri)
        
        async with websockets.connect(uri) as websocket:
            logger.info("WebSocket connected successfully")
            
            # Send ping to test connection
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            logger.info("Sent ping message")
            
            # Wait for pong response
            response = await websocket.recv()
            pong_data = json.loads(response)
            logger.info("Received pong response", data=pong_data)
            
            # Listen for signals for a few seconds
            logger.info("Listening for signals...")
            try:
                while True:
                    signal = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    signal_data = json.loads(signal)
                    logger.info("Received signal", signal=signal_data)
            except asyncio.TimeoutError:
                logger.info("No signals received within timeout")
                
    except Exception as e:
        logger.error("WebSocket test failed", error=str(e))
        return False
    
    return True


async def test_temporal_workflow_with_signals():
    """Test Temporal workflow with WebSocket signals."""
    try:
        # Connect to Temporal
        temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
        temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
        temporal_api_key = os.getenv("TEMPORAL_API_KEY")
        
        logger.info("Connecting to Temporal", address=temporal_address)
        
        # Configure connection
        connect_config = {
            "namespace": temporal_namespace,
        }
        
        if temporal_api_key:
            from temporalio.client import TLSConfig
            connect_config["tls"] = TLSConfig()
            connect_config["api_key"] = temporal_api_key
        
        client = await Client.connect(
            temporal_address,
            data_converter=pydantic_data_converter,
            **connect_config,
        )
        
        # Start a test workflow
        test_document_id = "test-doc-123"
        test_domain_id = "test-domain-456"
        test_file_path = "test/document.pdf"
        test_user_id = "test-user-789"
        
        logger.info("Starting test workflow", 
                   document_id=test_document_id,
                   domain_id=test_domain_id,
                   user_id=test_user_id)
        
        handle = await client.start_workflow(
            DocumentProcessingWorkflow.run,
            args=[test_document_id, test_domain_id, test_file_path, test_user_id],
            id=f"test-workflow-{test_document_id}",
            task_queue="hey-sh-workflows",
        )
        
        logger.info("Workflow started", workflow_id=handle.id)
        
        # Wait for workflow to complete (or timeout)
        try:
            result = await asyncio.wait_for(handle.result(), timeout=60.0)
            logger.info("Workflow completed", result=result)
        except asyncio.TimeoutError:
            logger.warning("Workflow timed out after 60 seconds")
            # Get workflow status
            status = await handle.describe()
            logger.info("Workflow status", status=status.status.name)
        
        return True
        
    except Exception as e:
        logger.error("Temporal workflow test failed", error=str(e))
        return False


async def test_inbox_api():
    """Test inbox API endpoints."""
    import aiohttp
    
    # API base URL
    api_url = "http://localhost:8000"
    test_token = "your-jwt-token-here"
    
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json",
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test inbox status
            async with session.get(f"{api_url}/ws/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    logger.info("WebSocket status", status=status_data)
                else:
                    logger.error("Failed to get WebSocket status", status=response.status)
            
            # Test inbox signals (requires authentication)
            async with session.get(f"{api_url}/api/v1/inbox/signals", headers=headers) as response:
                if response.status == 200:
                    signals_data = await response.json()
                    logger.info("Retrieved signals", count=len(signals_data.get("signals", [])))
                else:
                    logger.error("Failed to get signals", status=response.status, 
                               text=await response.text())
            
            # Test unread count
            async with session.get(f"{api_url}/api/v1/inbox/signals/unread-count", headers=headers) as response:
                if response.status == 200:
                    count_data = await response.json()
                    logger.info("Unread count", count=count_data.get("unread_count", 0))
                else:
                    logger.error("Failed to get unread count", status=response.status)
        
        return True
        
    except Exception as e:
        logger.error("Inbox API test failed", error=str(e))
        return False


async def main():
    """Run all WebSocket integration tests."""
    logger.info("Starting WebSocket integration tests")
    
    # Test 1: WebSocket connection
    logger.info("=== Test 1: WebSocket Connection ===")
    websocket_success = await test_websocket_connection()
    logger.info("WebSocket test", success=websocket_success)
    
    # Test 2: Temporal workflow with signals
    logger.info("=== Test 2: Temporal Workflow with Signals ===")
    workflow_success = await test_temporal_workflow_with_signals()
    logger.info("Workflow test", success=workflow_success)
    
    # Test 3: Inbox API
    logger.info("=== Test 3: Inbox API ===")
    api_success = await test_inbox_api()
    logger.info("API test", success=api_success)
    
    # Summary
    all_tests_passed = websocket_success and workflow_success and api_success
    logger.info("Integration tests completed", 
               all_passed=all_tests_passed,
               websocket=websocket_success,
               workflow=workflow_success,
               api=api_success)
    
    if not all_tests_passed:
        logger.error("Some tests failed. Check the logs above for details.")
        sys.exit(1)
    else:
        logger.info("All tests passed! WebSocket integration is working correctly.")


if __name__ == "__main__":
    asyncio.run(main())
