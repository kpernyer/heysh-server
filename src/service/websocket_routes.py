"""WebSocket routes for real-time workflow signals."""

import json
from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse

from src.app.auth.dependencies import get_current_user
from src.app.auth.utils import extract_token_from_header, verify_supabase_jwt
from src.service.websocket_manager import connection_manager

logger = structlog.get_logger()

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication"),
):
    """WebSocket endpoint for real-time workflow signals.

    Args:
        websocket: WebSocket connection
        token: JWT token from query parameter

    """
    try:
        # Validate JWT token
        payload = verify_supabase_jwt(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token: missing user ID")
            return

        # Connect to WebSocket
        await connection_manager.connect(websocket, user_id)
        
        logger.info("WebSocket connection established", user_id=user_id)

        try:
            # Keep connection alive and handle incoming messages
            while True:
                # Wait for messages from client (ping/pong, etc.)
                data = await websocket.receive_text()
                
                # Handle client messages (optional - for ping/pong)
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    logger.debug("Received non-JSON message from client", user_id=user_id)
                    
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected by client", user_id=user_id)
        except Exception as e:
            logger.error("WebSocket error", user_id=user_id, error=str(e))
        finally:
            await connection_manager.disconnect(websocket)

    except Exception as e:
        logger.error("WebSocket connection failed", error=str(e))
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication failed")
        except Exception:
            pass


@router.get("/ws/status")
async def websocket_status() -> Dict[str, Any]:
    """Get WebSocket connection status.

    Returns:
        Status information about WebSocket connections

    """
    return {
        "total_connections": connection_manager.get_connection_count(),
        "connected_users": connection_manager.get_connected_users(),
        "user_connection_counts": {
            user_id: connection_manager.get_connection_count(user_id)
            for user_id in connection_manager.get_connected_users()
        },
    }


@router.post("/ws/send-test")
async def send_test_signal(
    user_id: str,
    signal_type: str = "test",
    message: str = "Test signal from API",
) -> Dict[str, Any]:
    """Send a test signal to a specific user (for testing purposes).

    Args:
        user_id: Target user ID
        signal_type: Type of signal to send
        message: Test message content

    Returns:
        Result of the send operation

    """
    signal = {
        "signal_type": signal_type,
        "workflow_id": "test-workflow",
        "data": {"message": message, "timestamp": "2024-01-01T00:00:00Z"},
        "timestamp": "2024-01-01T00:00:00Z",
    }

    await connection_manager.send_to_user(user_id, signal)
    
    return {
        "success": True,
        "user_id": user_id,
        "signal": signal,
        "connections": connection_manager.get_connection_count(user_id),
    }
