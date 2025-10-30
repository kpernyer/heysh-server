"""Main FastAPI application."""

import os
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from src.service.health import (
    run_liveness_check,
    run_readiness_check,
    run_startup_check,
)
from src.service.routes_auth import router as auth_router
from src.service.routes_config import router as config_router
from src.service.routes_data import router as data_router
from src.service.routes_inbox import router as inbox_router
from src.service.routes_membership import router as membership_router
from src.service.routes_users import router as users_router
from src.service.routes_workflows import router as workflows_router
from src.service.routes_workflows import set_temporal_client
from src.service.websocket_routes import router as websocket_router
from src.service.version import get_backend_info, get_api_version

# Import v2 routers
from src.service.v2 import (
    config_router as v2_config_router,
    digital_twins_router as v2_digital_twins_router,
    inbox_router as v2_inbox_router,
    knowledge_base_router as v2_knowledge_base_router,
    memberships_router as v2_memberships_router,
    topics_router as v2_topics_router,
    workflows_router as v2_workflows_router,
)

logger = structlog.get_logger()

# Global Temporal client
temporal_client: Client | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Lifespan context manager for startup/shutdown using hostname-based configuration."""
    from src.service.config import get_settings

    global temporal_client

    # Get configuration from Settings (hostname-based)
    settings = get_settings()
    temporal_address = settings.temporal_address
    temporal_namespace = settings.temporal_namespace
    temporal_api_key = settings.temporal_api_key

    logger.info("Connecting to Temporal", address=temporal_address, namespace=temporal_namespace)

    # Configure connection based on environment
    connect_config = {
        "namespace": temporal_namespace,
    }

    # Add TLS and API key for Temporal Cloud
    if temporal_api_key:
        from temporalio.client import TLSConfig

        connect_config["tls"] = TLSConfig()
        connect_config["api_key"] = temporal_api_key
        logger.info("Using Temporal Cloud with TLS and API key authentication")
    else:
        logger.info("Using local Temporal server (no TLS)")

    temporal_client = await Client.connect(
        temporal_address,
        data_converter=pydantic_data_converter,
        **connect_config,
    )
    logger.info("Connected to Temporal successfully")

    # Share Temporal client with workflows router
    set_temporal_client(temporal_client)

    yield

    # Shutdown
    # Note: Temporal client doesn't have a .close() method
    # It will be automatically cleaned up when the app shuts down
    logger.info("Shutting down Temporal client")


# Create FastAPI app
app = FastAPI(
    title="Hey.sh API v2",
    description="""
    RESTful API for knowledge collaboration and workflow orchestration.

    **Core Concepts:**
    - **Topics**: Knowledge collaboration spaces
    - **Memberships**: User participation with roles (Owner, Controller, Contributor, Member)
    - **Knowledge Base**: Document management and AI analysis
    - **Digital Twins**: User representations with presence and preferences
    - **Inbox**: Human-in-the-loop workflow notifications
    - **Workflows**: Read-only workflow status and history
    """,
    version=get_api_version(),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - hostname-based configuration
# Uses Settings.cors_origins which provides local/production URLs
from src.service.config import get_settings

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.lovableproject\.com",  # Allow all Lovable projects
    allow_origins=settings.cors_origins,  # Hostname-based: local or production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== API v1 Routes (Legacy - Hidden from Docs) ====================
# Keep v1 routes functional for backward compatibility but hide from documentation
app.include_router(auth_router, include_in_schema=False)
app.include_router(config_router, include_in_schema=False)
app.include_router(data_router, include_in_schema=False)
app.include_router(workflows_router, include_in_schema=False)
app.include_router(inbox_router, include_in_schema=False)
app.include_router(users_router, include_in_schema=False)
app.include_router(membership_router, include_in_schema=False)
app.include_router(websocket_router, include_in_schema=False)

# ==================== API v2 Routes ====================
# Clean RESTful API focused on domain concepts

# v2 Topics - Core domain concept
app.include_router(v2_topics_router)

# v2 Memberships - User memberships across topics
app.include_router(v2_memberships_router)

# v2 Knowledge Base - Document and knowledge management
app.include_router(v2_knowledge_base_router)

# v2 Inbox - HITL workflow signals
app.include_router(v2_inbox_router)

# v2 Digital Twins - User representations
app.include_router(v2_digital_twins_router)

# v2 Workflows - Read-only workflow information
app.include_router(v2_workflows_router)

# v2 Config - Configuration with content negotiation
app.include_router(v2_config_router)

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Meta"], summary="Health check")
async def health() -> dict[str, str]:
    """Simple health check endpoint - always returns healthy if API is responding."""
    return {"status": "healthy"}


@app.get("/api/v1/info", tags=["Meta"], summary="API version info", include_in_schema=False)
async def info() -> dict[str, Any]:
    """Get backend version, git commit, and build information."""
    return get_backend_info()


@app.get("/health/live", include_in_schema=False)
async def liveness_probe() -> dict:
    """Kubernetes liveness probe endpoint.
    Pod will be restarted if this fails.
    """
    result = await run_liveness_check(temporal_client)
    status_code = 200 if result["alive"] else 503
    return {"status_code": status_code, **result}


@app.get("/health/ready", include_in_schema=False)
async def readiness_probe() -> dict:
    """Kubernetes readiness probe endpoint.
    Pod will be removed from load balancer if this fails.
    """
    result = await run_readiness_check(temporal_client)
    status_code = 200 if result["ready"] else 503
    return {"status_code": status_code, **result}


@app.get("/health/startup", include_in_schema=False)
async def startup_probe() -> dict:
    """Kubernetes startup probe endpoint.
    Pod must pass this before readiness/liveness checks start.
    """
    result = await run_startup_check(temporal_client)
    status_code = 200 if result["started"] else 503
    return {"status_code": status_code, **result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.service.api:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
    )
