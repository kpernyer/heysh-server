"""Main FastAPI application."""

import os
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from src.service.graphql import schema
from src.service.graphql.resolvers import resolver
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
from src.service.version import get_backend_info

logger = structlog.get_logger()

# Global Temporal client
temporal_client: Client | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Lifespan context manager for startup/shutdown."""
    global temporal_client

    # Startup
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    temporal_api_key = os.getenv("TEMPORAL_API_KEY")

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

    # Initialize GraphQL resolver connections
    try:
        await resolver.init_connections()
        logger.info("GraphQL resolver connections initialized")
    except Exception as e:
        logger.warning(f"Some GraphQL connections failed to initialize: {e}")
        # Continue anyway - GraphQL will work with partial connections

    yield

    # Shutdown
    if temporal_client:
        await temporal_client.close()
        logger.info("Temporal client closed")

    try:
        await resolver.close_connections()
        logger.info("GraphQL resolver connections closed")
    except Exception as e:
        logger.warning(f"Error closing GraphQL connections: {e}")


# Create FastAPI app
app = FastAPI(
    title="Hey.sh Backend API",
    description="Backend orchestration layer for hey.sh knowledge platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
# Tillåter alla Lovable-projekt med regex pattern

cors_origins = [
    "http://localhost:5173",  # För lokal utveckling
    "http://localhost:3000",  # För annan lokal utveckling
    "http://hey.local",       # Hey.sh local development
    "http://www.hey.local",   # Hey.sh local development with www
    # Matcher alla subdomains på lovableproject.com
    r"https://.*\.lovableproject\.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.lovableproject\.com",  # Regex för alla Lovable-projekt
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://hey.local",
        "http://www.hey.local",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes (no auth required for some endpoints)
app.include_router(auth_router)

# Include configuration routes (no auth required)
app.include_router(config_router)

# Include data management routes (auth required)
app.include_router(data_router)

# Include workflow orchestration routes (auth required)
app.include_router(workflows_router)

# Include inbox routes (auth required)
app.include_router(inbox_router)

# Include user management routes (auth required)
app.include_router(users_router)

# Include membership routes (auth required)
app.include_router(membership_router)

# Include WebSocket routes
app.include_router(websocket_router)

# Create and mount GraphQL router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Hey.sh Backend API", "version": "0.1.0"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/v1/info")
async def get_backend_info() -> dict[str, Any]:
    """Get backend version and environment information."""
    return get_backend_info()


@app.get("/health/live")
async def liveness_probe() -> dict:
    """Kubernetes liveness probe endpoint.
    Pod will be restarted if this fails.
    """
    result = await run_liveness_check(temporal_client)
    status_code = 200 if result["alive"] else 503
    return {"status_code": status_code, **result}


@app.get("/health/ready")
async def readiness_probe() -> dict:
    """Kubernetes readiness probe endpoint.
    Pod will be removed from load balancer if this fails.
    """
    result = await run_readiness_check(temporal_client)
    status_code = 200 if result["ready"] else 503
    return {"status_code": status_code, **result}


@app.get("/health/startup")
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
