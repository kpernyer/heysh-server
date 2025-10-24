"""Health check endpoints for worker processes.

Exposes health information on HTTP server for Kubernetes probes.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

# Setup logging
logger = logging.getLogger(__name__)

from aiohttp import web


class WorkerHealthServer:
    """Simple health check HTTP server for workers."""

    def __init__(self, port: int = 8080):
        """Initialize the health server."""
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.temporal_client = None
        self.worker_started_at = None

    def setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_get("/health/live", self.handle_liveness)
        self.app.router.add_get("/health/ready", self.handle_readiness)
        self.app.router.add_get("/health/startup", self.handle_startup)

    async def handle_health(self, request):
        """Basic health check."""
        return web.json_response({"status": "healthy"})

    async def handle_startup(self, request):
        """Startup probe - check initialization."""
        worker_type = os.getenv("WORKER_TYPE", "unknown")
        task_queue = os.getenv("TASK_QUEUE", "unknown")

        issues = []

        # Check required environment variables
        required_vars = [
            "TEMPORAL_ADDRESS",
            "TEMPORAL_NAMESPACE",
            "WORKER_TYPE",
            "TASK_QUEUE",
        ]
        for var in required_vars:
            if not os.getenv(var):
                issues.append(f"Missing {var}")

        started = len(issues) == 0 and self.temporal_client is not None

        return web.json_response(
            {
                "started": started,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "system": {
                    "pod_name": os.getenv("POD_NAME", "unknown"),
                    "pod_namespace": os.getenv("POD_NAMESPACE", "default"),
                    "worker_type": worker_type,
                    "task_queue": task_queue,
                },
                "issues": issues,
            }
        )

    async def handle_readiness(self, request):
        """Readiness probe - can process tasks."""
        try:
            if not self.temporal_client:
                return web.json_response(
                    {"ready": False, "message": "Temporal client not initialized"},
                    status=503,
                )

            # Try to get worker task reachability (lightweight check)
            await asyncio.wait_for(
                self.temporal_client.get_worker_task_reachability(),
                timeout=3.0,
            )

            return web.json_response(
                {
                    "ready": True,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "message": "Connected to Temporal",
                }
            )
        except TimeoutError:
            return web.json_response(
                {
                    "ready": False,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "message": "Temporal connection timeout",
                },
                status=503,
            )
        except Exception as e:
            return web.json_response(
                {
                    "ready": False,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "message": f"Temporal connection failed: {e!s}",
                },
                status=503,
            )

    async def handle_liveness(self, request):
        """Liveness probe - minimal check."""
        try:
            if not self.temporal_client:
                return web.json_response(
                    {"alive": False, "message": "Temporal client not initialized"},
                    status=503,
                )

            # Minimal check - just verify connection exists
            await asyncio.wait_for(
                self.temporal_client.get_worker_task_reachability(),
                timeout=2.0,
            )

            return web.json_response(
                {
                    "alive": True,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
            )
        except Exception as e:
            return web.json_response(
                {
                    "alive": False,
                    "error": str(e),
                },
                status=503,
            )

    async def start(self, temporal_client: Any):
        """Start health check server."""
        self.temporal_client = temporal_client
        self.worker_started_at = datetime.utcnow()

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()

        logger.info(f"✅ Health check server started on port {self.port}")


async def start_health_server(temporal_client: Any, port: int = 8080):
    """Convenience function to start health server."""
    server = WorkerHealthServer(port)
    await server.start(temporal_client)
    return server
