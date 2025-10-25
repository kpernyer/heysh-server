"""WebSocket connection manager for real-time workflow signals."""

import json
from typing import Any, Dict, List

import structlog
from fastapi import WebSocket, WebSocketDisconnect

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections for real-time workflow signals."""

    def __init__(self):
        """Initialize connection manager."""
        # Map user_id -> list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Map connection -> user_id for cleanup
        self.connection_to_user: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept WebSocket connection and register user.

        Args:
            websocket: WebSocket connection
            user_id: Authenticated user ID

        """
        await websocket.accept()
        
        # Add to user's connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Track connection -> user mapping
        self.connection_to_user[websocket] = user_id
        
        logger.info(
            "WebSocket connected",
            user_id=user_id,
            total_connections=len(self.active_connections.get(user_id, [])),
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection and cleanup.

        Args:
            websocket: WebSocket connection to remove

        """
        user_id = self.connection_to_user.get(websocket)
        if not user_id:
            logger.warning("Disconnecting unknown WebSocket connection")
            return

        # Remove from user's connections
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
                # Clean up empty user entries
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            except ValueError:
                logger.warning("WebSocket not found in user connections", user_id=user_id)

        # Remove connection mapping
        self.connection_to_user.pop(websocket, None)

        logger.info(
            "WebSocket disconnected",
            user_id=user_id,
            remaining_connections=len(self.active_connections.get(user_id, [])),
        )

    async def send_to_user(self, user_id: str, signal: Dict[str, Any]) -> None:
        """Send signal to all connections for a specific user.

        Args:
            user_id: Target user ID
            signal: Signal data to send

        """
        if user_id not in self.active_connections:
            logger.debug("No active connections for user", user_id=user_id)
            return

        message = json.dumps(signal)
        failed_connections = []

        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(message)
                logger.debug("Signal sent to user", user_id=user_id, signal_type=signal.get("signal_type"))
            except Exception as e:
                logger.warning(
                    "Failed to send signal to connection",
                    user_id=user_id,
                    error=str(e),
                )
                failed_connections.append(connection)

        # Clean up failed connections
        for connection in failed_connections:
            await self.disconnect(connection)

    async def send_to_all(self, signal: Dict[str, Any]) -> None:
        """Send signal to all connected users.

        Args:
            signal: Signal data to send

        """
        message = json.dumps(signal)
        failed_connections = []

        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.warning(
                        "Failed to send broadcast signal",
                        user_id=user_id,
                        error=str(e),
                    )
                    failed_connections.append(connection)

        # Clean up failed connections
        for connection in failed_connections:
            await self.disconnect(connection)

    def get_connection_count(self, user_id: str | None = None) -> int:
        """Get total number of active connections.

        Args:
            user_id: Optional user ID to count connections for

        Returns:
            Number of active connections

        """
        if user_id:
            return len(self.active_connections.get(user_id, []))
        return sum(len(connections) for connections in self.active_connections.values())

    def get_connected_users(self) -> List[str]:
        """Get list of users with active connections.

        Returns:
            List of user IDs with active connections

        """
        return list(self.active_connections.keys())


# Global connection manager instance
connection_manager = ConnectionManager()
